"""TFM's background scenes — the animated fields drawn behind the file panes.

Every scene TFM offers is a fragment shader, evaluated per pixel on the GPU. That
is a deliberate consolidation: scenes used to come in two kinds, and the CPU kind
(line segments stroked by the backend) lost on every axis that mattered. Density
cost CPU time per segment, the whole scene was stroked in a single color, and —
the one that decided it — a segment scene was drawn *inside* the UI's render pass,
so animating it repainted the entire UI every frame no matter how little it drew.
A shader owns a layer behind the UI, which the backend advances without touching a
UI pixel, so an idle TFM with a background costs a fraction of what it used to.

**Writing one.** A scene is a single fragment function named ``puikit_bg_fragment``.
PuiKit prepends its prelude — the uniform struct and a fullscreen vertex stage — so
the source here is just that function::

    fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                       constant BackgroundUniforms &u [[buffer(0)]])

``u`` carries ``resolution`` (pixels), ``time`` (seconds, already scaled by the
theme's speed), ``opacity``, and the theme's ``ink``/``backdrop`` as RGBA — so a
shader stays on-palette without knowing anything about TFM's theme system. The
source is compiled when the theme is applied; one that fails to compile draws
nothing and logs the compiler error, so a typo costs a blank background.

**Every scene ships twice.** Shader source is the one genuinely backend-specific
part of a background: macOS compiles Metal Shading Language, Windows compiles HLSL,
and they are different languages. So each scene is a pair named for its dialect —
``<SCENE>_MSL`` and ``<SCENE>_HLSL`` — holding the same maths, and the registry at
the bottom pairs them. No compiler checks one against the other, so tuning one and
forgetting the twin is the standing hazard here; ``test_background_shaders.py``
compares the two sets of constants to catch exactly that.

**The per-pixel inversion.** A CPU scene walks its objects and draws them. A shader
is asked, for one pixel at a time, "what covers you?" — so every scene here needs a
way to answer that without visiting everything. The recurring device is a *grid*: an
object's identity comes from hashing its cell index, so a pixel can compute which
cells could possibly reach it and consult only those. The wave visits particle cells
across depth layers, the rain its own column and two neighbours, the starfield cells
along a depth ray, the constellation a 5x5 block of nodes. Where a scene needs
per-object randomness it hashes the cell index rather than calling anything
time-varying, so an object keeps a fixed identity across frames and all motion comes
from ``time``.
"""

from __future__ import annotations

#: A flowing sheet of particles — a wave surface rendered as a point cloud.
#:
#: Structure: the surface is a sum of travelling sine trains, sampled at a stack of
#: depth layers. Each layer is a row of particles whose lateral spacing is measured
#: in *world* units, so perspective packs the far rows tighter on screen and the
#: sheet reads as receding. For each pixel the shader visits the few particle cells
#: that could overlap it, at each layer, and accumulates a soft splat — which is
#: how a per-pixel program draws what is conceptually a particle system.
#:
#: The colour is the part the CPU renderer could never do: hue shifts along the
#: sheet and toward the crests, so the wave runs cool in its troughs and pales to
#: near-white where it peaks, in the spirit of the reference. It is anchored on the
#: theme's ``ink`` so it still belongs to the palette rather than ignoring it.
WAVE_MSL = """
// --- tunables ---------------------------------------------------------------
// LAYERS x 3 cells is the per-pixel iteration count and the dominant cost, so it
// is kept as low as the look allows; everything inside that loop is deliberately
// transcendental-free except the surface itself.
constant int   LAYERS      = 12;     // depth rows sampled per pixel
constant float Z_NEAR      = 1.5;    // nearest / furthest sheet depth
constant float Z_FAR       = 5.2;
constant float CAM_H       = 0.62;   // camera height above the sheet
constant float HORIZON     = 0.36;   // sheet's vanishing line, fraction of height
constant float FOCAL       = 0.85;   // focal length in view-height units
constant float PPU         = 44.0;   // particles per world unit, across the sheet
constant float DOT         = 0.0034; // particle radius in view-height units
constant float SPRAY       = 0.34;   // how far a lofted particle rises
constant float GAIN        = 1.5;    // overall brightness of the accumulation

// Particle jitter and brightness must be fixed per particle, so they come from its
// (cell, layer) index rather than anything time-varying -- otherwise every particle
// would reshuffle each frame. These are the arithmetic-only variety on purpose:
// the usual fract(sin(n)*43758.0) idiom costs a transcendental, and at 48 cells per
// pixel that alone was a third of the frame.
static inline float hash11(float n) {
    n = fract(n * 0.1031);
    n *= n + 33.33;
    n *= n + n;
    return fract(n);
}
static inline float2 hash21(float2 p) {
    float3 v = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return fract((v.xx + v.yz) * v.zy);
}

// The surface: three travelling sine trains at unrelated angles and wavelengths,
// which fold into each other instead of reading as corrugation.
static inline float surface(float x, float z, float t) {
    return 0.32 * sin(1.30 * x + 0.55 * z + 0.55 * t)
         + 0.18 * sin(-0.85 * x + 1.30 * z + 0.41 * t)
         + 0.10 * sin(2.40 * x - 0.90 * z + 0.72 * t);
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    float2 uv = pos.xy / u.resolution;
    float aspect = u.resolution.x / u.resolution.y;
    // Work in view-height units so the sheet keeps its proportions in any window.
    float px = (uv.x - 0.5) * aspect;
    float t = u.time;

    float density = 0.0;   // accumulated particle coverage
    float crest = 0.0;     // height of whatever contributed most, for colouring

    for (int i = 0; i < LAYERS; ++i) {
        float fi = (float(i) + 0.5) / float(LAYERS);
        // Even steps in 1/z are even steps on screen; stepping z directly would
        // pile the far half of the sheet onto a single line.
        float z = 1.0 / mix(1.0 / Z_NEAR, 1.0 / Z_FAR, fi);
        float layerFade = 1.0 - 0.55 * fi;

        // This pixel's position on the sheet, in world units at this depth.
        float wx = px * z / FOCAL;
        float cell = floor(wx * PPU);

        // Visit the neighbouring cells too: a particle whose centre is in the next
        // cell can still overlap this pixel, and skipping them leaves seams.
        for (int c = -1; c <= 1; ++c) {
            float id = cell + float(c);
            float2 rnd = hash21(float2(id, float(i)));
            float pwx = (id + 0.5 + (rnd.x - 0.5) * 0.9) / PPU;

            float loft = rnd.y * rnd.y * rnd.y;   // most on the surface, a few high
            float h = surface(pwx, z, t);
            float py = h + loft * SPRAY;

            // Project the particle: x back to screen, y through the camera.
            float sx = FOCAL * pwx / z;
            float sy = HORIZON + FOCAL * (CAM_H - py) / z;

            float2 d = float2(px - sx, uv.y - sy);
            float r = DOT * (1.0 + 2.2 / z);      // nearer particles are larger
            // Polynomial falloff rather than a gaussian: exp() at 48 cells per
            // pixel is expensive, and squaring a clamped (1 - d^2/r^2) gives the
            // same soft round dot with a finite support the compiler can skip.
            float q = max(0.0, 1.0 - dot(d, d) / (r * r));
            float splat = q * q;

            float bright = layerFade * (1.0 - 0.7 * loft) * (0.55 + 0.45 * hash11(id + float(i) * 37.0));
            density += splat * bright;
            crest = max(crest, splat * (0.5 + 0.5 * h / 0.6));
        }
    }

    density = 1.0 - exp(-density * GAIN);   // saturating, so dense areas read solid

    // Colour: sweep the hue along the sheet and lift it toward white at the
    // crests. The two ends are the theme ink pushed apart in opposite directions
    // rather than fixed colours, so the gradient tracks whatever palette is
    // active while still spanning the violet-to-cyan range of the reference.
    float3 violet = u.ink.rgb * float3(1.00, 0.42, 1.30);
    float3 cyan   = u.ink.rgb * float3(0.34, 1.10, 1.18);
    float sweep = 0.5 + 0.5 * sin(uv.x * 3.1 + t * 0.25);
    float3 tint = mix(violet, cyan, sweep);
    // Crests catch the light and pale out, which is what separates the leading
    // edge of the sheet from the mass behind it.
    float3 rgb = mix(tint, float3(1.0), clamp(crest * 1.9, 0.0, 1.0) * 0.7);

    rgb = mix(u.backdrop.rgb, rgb, clamp(density, 0.0, 1.0) * u.opacity);
    return float4(rgb, 1.0);
}
"""

#: The HLSL translation of :data:`WAVE_MSL` for puikit's Direct3D 11 (Windows) backend.
#:
#: A shader is the one genuinely backend-specific part of a background: Metal Shading
#: Language and HLSL are different languages, so a cross-platform scene ships the
#: same math in both and each backend compiles the dialect it speaks (macOS reads
#: ``source``, Windows reads ``source_hlsl`` — see puikit ``Shader``). This is a
#: line-for-line port of the wave above; only the dialect differs (``fract``→``frac``,
#: ``mix``→``lerp``, the ``constant`` qualifiers become ``static const``, and the
#: uniforms are read from the ``BackgroundUniforms`` cbuffer as globals rather than a
#: ``[[buffer(0)]]`` parameter). Keep the two in sync when tuning the scene.
WAVE_HLSL = """
// --- tunables (see WAVE_MSL for the rationale of each) -------------------
static const int   LAYERS  = 12;
static const float Z_NEAR  = 1.5;
static const float Z_FAR   = 5.2;
static const float CAM_H   = 0.62;
static const float HORIZON = 0.36;
static const float FOCAL   = 0.85;
static const float PPU     = 44.0;
static const float DOT     = 0.0034;
static const float SPRAY   = 0.34;
static const float GAIN    = 1.5;

float hash11(float n) {
    n = frac(n * 0.1031);
    n *= n + 33.33;
    n *= n + n;
    return frac(n);
}
float2 hash21(float2 p) {
    float3 v = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return frac((v.xx + v.yz) * v.zy);
}
float surface(float x, float z, float t) {
    return 0.32 * sin(1.30 * x + 0.55 * z + 0.55 * t)
         + 0.18 * sin(-0.85 * x + 1.30 * z + 0.41 * t)
         + 0.10 * sin(2.40 * x - 0.90 * z + 0.72 * t);
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float2 uv = pos.xy / resolution;
    float aspect = resolution.x / resolution.y;
    float px = (uv.x - 0.5) * aspect;
    float t = time;

    float density = 0.0;
    float crest = 0.0;

    for (int i = 0; i < LAYERS; ++i) {
        float fi = (float(i) + 0.5) / float(LAYERS);
        float z = 1.0 / lerp(1.0 / Z_NEAR, 1.0 / Z_FAR, fi);
        float layerFade = 1.0 - 0.55 * fi;

        float wx = px * z / FOCAL;
        float cell = floor(wx * PPU);

        for (int c = -1; c <= 1; ++c) {
            float id = cell + float(c);
            float2 rnd = hash21(float2(id, float(i)));
            float pwx = (id + 0.5 + (rnd.x - 0.5) * 0.9) / PPU;

            float loft = rnd.y * rnd.y * rnd.y;
            float h = surface(pwx, z, t);
            float py = h + loft * SPRAY;

            float sx = FOCAL * pwx / z;
            float sy = HORIZON + FOCAL * (CAM_H - py) / z;

            float2 d = float2(px - sx, uv.y - sy);
            float r = DOT * (1.0 + 2.2 / z);
            float q = max(0.0, 1.0 - dot(d, d) / (r * r));
            float splat = q * q;

            float bright = layerFade * (1.0 - 0.7 * loft) * (0.55 + 0.45 * hash11(id + float(i) * 37.0));
            density += splat * bright;
            crest = max(crest, splat * (0.5 + 0.5 * h / 0.6));
        }
    }

    density = 1.0 - exp(-density * GAIN);

    float3 violet = ink.rgb * float3(1.00, 0.42, 1.30);
    float3 cyan   = ink.rgb * float3(0.34, 1.10, 1.18);
    float sweep = 0.5 + 0.5 * sin(uv.x * 3.1 + t * 0.25);
    float3 tint = lerp(violet, cyan, sweep);
    float3 rgb = lerp(tint, float3(1.0, 1.0, 1.0), clamp(crest * 1.9, 0.0, 1.0) * 0.7);

    rgb = lerp(backdrop.rgb, rgb, clamp(density, 0.0, 1.0) * opacity);
    return float4(rgb, 1.0);
}
"""

#: Falling phosphor streaks — the terminal rain.
#:
#: Structure: the screen is divided into columns whose count follows the window
#: width, so the fall keeps its density at any size. Each column draws its streaks
#: at a fixed x, so a pixel only has to consider its own column and its two
#: neighbours (a streak near a column edge bleeds across one) — three cells,
#: regardless of how many columns the window holds. Within a column, a streak is a
#: span of length ``streakLen`` hanging *above* its head, and a pixel's place along
#: that span is one subtraction; there is no per-drop geometry to walk.
#:
#: ``rnd`` is the exact uint32 avalanche of ``_rand`` in the segment module this
#: scene replaces, so column placement, speed, length and brightness come out
#: identical — the rain falls in the same places, it is only painted differently.
#:
#: Two things the CPU renderer could not do. The tail is a continuous curve rather
#: than the 7 discrete alpha steps a stack of sub-segments had to quantise it into;
#: and the head pales toward white while the tail keeps the theme ink, which is the
#: hot-phosphor tip a single-colour stroke has no way to express.
RAIN_MSL = """
// --- tunables ---------------------------------------------------------------
constant float COLUMN_PX  = 26.0;   // nominal column width; the count follows width
constant float RATE       = 0.16;   // fraction of a full fall per second
constant int   DROPS      = 2;      // streaks per column, offset in phase
constant float LEN_MIN    = 0.10;   // streak length as a fraction of view height
constant float LEN_RANGE  = 0.22;
constant float WIDTH_PX   = 1.3;    // streak width in pixels
constant float TAIL_GAMMA = 1.7;    // >1 keeps the head crisp and the tail long
constant float HEAD_GLOW  = 0.55;   // how far the head pales toward white

// The integer avalanche hash from the segment scene, verbatim: the salt picks an
// independent draw for the same column, so placement and speed are uncorrelated.
// Integer ops are exact in both dialects, which is what makes the two renderers
// agree on where the rain falls.
static inline float rnd(uint index, uint salt) {
    uint x = index * 0x9E3779B1u + salt * 0x85EBCA77u;
    x ^= x >> 15;
    x *= 0x2C1B3C6Du;
    x ^= x >> 12;
    x *= 0x297A2D39u;
    x ^= x >> 15;
    return float(x) * (1.0 / 4294967296.0);
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    float H = u.resolution.y;
    float columns = max(6.0, floor(u.resolution.x / COLUMN_PX));
    float colW = u.resolution.x / columns;

    float density = 0.0;   // accumulated streak coverage at this pixel
    float hot = 0.0;       // proximity to the brightest head, for the glow

    float c0 = floor(pos.x / colW);
    for (int n = -1; n <= 1; ++n) {
        float cf = c0 + float(n);
        uint ci = uint(int(cf));

        // Jitter x within the column so the fall is not a perfect comb.
        float x = (cf + 0.15 + rnd(ci, 1) * 0.7) * colW;
        float dx = abs(pos.x - x);
        // Nothing in this column can reach this pixel: skip its drops entirely.
        // Most pixels take this exit for all three columns, which is what keeps
        // the scene cheap at native resolution.
        if (dx > WIDTH_PX * 1.6) { continue; }

        float fall      = 0.55 + rnd(ci, 2);              // per-column speed
        float streakLen = (LEN_MIN + LEN_RANGE * rnd(ci, 3)) * H;
        float bright    = 0.45 + rnd(ci, 6) * 0.55;       // some columns stay faint
        // Antialiased across the streak's width — a hard test would shimmer as the
        // column's sub-pixel x drifts with the window size.
        float prof = 1.0 - smoothstep(WIDTH_PX * 0.5, WIDTH_PX * 1.6, dx);

        for (int d = 0; d < DROPS; ++d) {
            float phase = rnd(ci, 4u + uint(d));
            // Travel 0->1 walks the head from just above the view to the bottom
            // edge, so a streak enters already fully formed.
            float travel = fract(u.time * RATE * fall + phase);
            float hy = travel * (H + streakLen) - streakLen;
            // Place this pixel along the streak: 0 at the head, 1 at the tail end.
            float k = (hy - pos.y) / streakLen;
            if (k < 0.0 || k > 1.0) { continue; }
            float a = pow(1.0 - k, TAIL_GAMMA) * bright * prof;
            density += a;
            hot = max(hot, a * (1.0 - k));
        }
    }

    float3 rgb = mix(u.ink.rgb, float3(1.0), clamp(hot, 0.0, 1.0) * HEAD_GLOW);
    rgb = mix(u.backdrop.rgb, rgb, clamp(density, 0.0, 1.0) * u.opacity);
    return float4(rgb, 1.0);
}
"""

#: The HLSL translation of :data:`RAIN_MSL` (see :data:`WAVE_HLSL` for why a scene ships
#: both). Line-for-line; only the dialect differs — ``fract``/``mix`` become
#: ``frac``/``lerp``, ``constant`` becomes ``static const``, the uniforms are cbuffer
#: globals, and the hash constants are typed ``uint`` so the literals do not land in
#: a signed int. Keep the two in sync when tuning the scene.
RAIN_HLSL = """
// --- tunables (see RAIN_MSL for the rationale of each) -------------------
static const float COLUMN_PX  = 26.0;
static const float RATE       = 0.16;
static const int   DROPS      = 2;
static const float LEN_MIN    = 0.10;
static const float LEN_RANGE  = 0.22;
static const float WIDTH_PX   = 1.3;
static const float TAIL_GAMMA = 1.7;
static const float HEAD_GLOW  = 0.55;

static const uint HASH_K1 = 0x9E3779B1;
static const uint HASH_K2 = 0x85EBCA77;
static const uint HASH_K3 = 0x2C1B3C6D;
static const uint HASH_K4 = 0x297A2D39;

float rnd(uint index, uint salt) {
    uint x = index * HASH_K1 + salt * HASH_K2;
    x ^= x >> 15;
    x *= HASH_K3;
    x ^= x >> 12;
    x *= HASH_K4;
    x ^= x >> 15;
    return float(x) * (1.0 / 4294967296.0);
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float H = resolution.y;
    float columns = max(6.0, floor(resolution.x / COLUMN_PX));
    float colW = resolution.x / columns;

    float density = 0.0;
    float hot = 0.0;

    float c0 = floor(pos.x / colW);
    for (int n = -1; n <= 1; ++n) {
        float cf = c0 + float(n);
        uint ci = uint(int(cf));

        float x = (cf + 0.15 + rnd(ci, 1) * 0.7) * colW;
        float dx = abs(pos.x - x);
        if (dx > WIDTH_PX * 1.6) { continue; }

        float fall      = 0.55 + rnd(ci, 2);
        float streakLen = (LEN_MIN + LEN_RANGE * rnd(ci, 3)) * H;
        float bright    = 0.45 + rnd(ci, 6) * 0.55;
        float prof = 1.0 - smoothstep(WIDTH_PX * 0.5, WIDTH_PX * 1.6, dx);

        for (int d = 0; d < DROPS; ++d) {
            float phase = rnd(ci, 4 + (uint)d);
            float travel = frac(time * RATE * fall + phase);
            float hy = travel * (H + streakLen) - streakLen;
            float k = (hy - pos.y) / streakLen;
            if (k < 0.0 || k > 1.0) { continue; }
            float a = pow(1.0 - k, TAIL_GAMMA) * bright * prof;
            density += a;
            hot = max(hot, a * (1.0 - k));
        }
    }

    float3 rgb = lerp(ink.rgb, float3(1.0, 1.0, 1.0), clamp(hot, 0.0, 1.0) * HEAD_GLOW);
    rgb = lerp(backdrop.rgb, rgb, clamp(density, 0.0, 1.0) * opacity);
    return float4(rgb, 1.0);
}
"""

#: Stars streaming toward the viewer, drawn as radial motion streaks.
#:
#: Structure: stars sit on a bounded plane in front of the camera and travel only in
#: depth; the perspective divide sweeps them outward from the centre and accelerates
#: them as they near. The plane is *bounded* — that is what gives the field a
#: vanishing point, since a far layer covers only the middle of the view and opens
#: outward as it approaches.
#:
#: The per-pixel inversion is the interesting part. A star at plane position ``s`` and
#: depth ``z`` lands at ``s/z`` in normalised coordinates, so a pixel can run that
#: backwards: at an assumed depth, ``s = n * z`` names the exact cell that could
#: cover it. Depth is sampled in layers — each layer a full grid of stars sharing one
#: depth, the layers evenly offset in phase so some are always near and some far. A
#: layer recycles when its depth wraps, which is invisible because the fade-in has it
#: at zero alpha exactly there.
#:
#: A streak spans a range of depths, so the covering star lies somewhere along the
#: pixel's ray between the plane radius of its head and that of its tail. For any
#: *on-screen* pixel that span works out to well under one cell, so sampling the two
#: ends brackets it — which is why this costs two lookups per layer and not a search.
STARFIELD_MSL = """
// --- tunables ---------------------------------------------------------------
constant int   LAYERS   = 10;     // depth samples; each is a full grid of stars
constant float Z_FAR    = 2.6;    // spawn depth. Above 1 so the far plane lands
                                  // inside the view rather than already filling it
constant float Z_NEAR   = 0.16;   // closest approach; the divide blows up at 0
constant float RATE     = 0.12;   // fraction of the depth range crossed per second
constant float TAIL     = 0.055;  // streak length, in depth -- constant in depth is
                                  // what makes the drawn streak lengthen as it nears
constant float FADE_IN  = 0.55;   // fraction of the travel spent fading in
constant float DENSITY  = 3.0;    // star cells per unit of plane
constant float DOT_PX   = 1.15;   // streak half-width, in pixels
constant float NEAR_GLOW = 0.6;   // how far the nearest stars pale toward white

static inline float hash11(float n) {
    n = fract(n * 0.1031);
    n *= n + 33.33;
    n *= n + n;
    return fract(n);
}
static inline float2 hash21(float2 p) {
    float3 v = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return fract((v.xx + v.yz) * v.zy);
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    float2 halfRes = u.resolution * 0.5;
    float2 P = pos.xy - halfRes;      // pixels from the centre
    float2 n = P / halfRes;           // normalised: +-1 at the view edges
    float span = Z_FAR - Z_NEAR;

    float density = 0.0;
    float near = 0.0;                 // depth of the closest contributor, for glow

    for (int i = 0; i < LAYERS; ++i) {
        // Layers evenly offset in phase, so the field always holds stars at every
        // stage of the journey rather than pulsing in unison.
        float travel = fract(u.time * RATE + float(i) / float(LAYERS));
        float alpha = min(1.0, travel / FADE_IN);
        if (alpha <= 0.0) { continue; }
        float z = Z_FAR - travel * span;
        float zt = min(Z_FAR, z + TAIL);

        // Bracket the ray: the covering star's plane radius lies between what its
        // head would need and what its tail would.
        for (int e = 0; e < 2; ++e) {
            float2 s = n * (e == 0 ? z : zt);
            float2 cell = floor(s * DENSITY);
            float2 j = hash21(cell + float2(float(i) * 17.0, float(i) * 31.0));
            float2 star = (cell + j) / DENSITY;
            if (abs(star.x) > 1.0 || abs(star.y) > 1.0) { continue; }

            float2 A = star * halfRes;    // the star's ray, in pixels
            float L = length(A);
            if (L < 1e-4) { continue; }
            float2 dir = A / L;
            // Point-to-segment: the streak runs from the tail (further, so nearer
            // the centre) out to the head.
            float along = clamp(dot(P, dir), L / zt, L / z);
            float d = length(P - dir * along);
            float q = max(0.0, 1.0 - d / DOT_PX);
            float splat = q * q;
            float bright = 0.55 + 0.45 * hash11(cell.x * 73.0 + cell.y * 149.0 + float(i));
            // max, not sum: the two bracket samples usually find the same star, and
            // adding them would double it.
            density = max(density, splat * alpha * bright);
            near = max(near, splat * (1.0 - z / Z_FAR));
        }
    }

    float3 rgb = mix(u.ink.rgb, float3(1.0), clamp(near, 0.0, 1.0) * NEAR_GLOW);
    rgb = mix(u.backdrop.rgb, rgb, clamp(density, 0.0, 1.0) * u.opacity);
    return float4(rgb, 1.0);
}
"""

#: The HLSL translation of :data:`STARFIELD_MSL`. Line-for-line; only the dialect
#: differs. Keep the two in sync when tuning the scene.
STARFIELD_HLSL = """
// --- tunables (see STARFIELD_MSL for the rationale of each) ------------------
static const int   LAYERS    = 10;
static const float Z_FAR     = 2.6;
static const float Z_NEAR    = 0.16;
static const float RATE      = 0.12;
static const float TAIL      = 0.055;
static const float FADE_IN   = 0.55;
static const float DENSITY   = 3.0;
static const float DOT_PX    = 1.15;
static const float NEAR_GLOW = 0.6;

float hash11(float n) {
    n = frac(n * 0.1031);
    n *= n + 33.33;
    n *= n + n;
    return frac(n);
}
float2 hash21(float2 p) {
    float3 v = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return frac((v.xx + v.yz) * v.zy);
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float2 halfRes = resolution * 0.5;
    float2 P = pos.xy - halfRes;
    float2 n = P / halfRes;
    float span = Z_FAR - Z_NEAR;

    float density = 0.0;
    float near = 0.0;

    for (int i = 0; i < LAYERS; ++i) {
        float travel = frac(time * RATE + float(i) / float(LAYERS));
        float alpha = min(1.0, travel / FADE_IN);
        if (alpha <= 0.0) { continue; }
        float z = Z_FAR - travel * span;
        float zt = min(Z_FAR, z + TAIL);

        for (int e = 0; e < 2; ++e) {
            float2 s = n * (e == 0 ? z : zt);
            float2 cell = floor(s * DENSITY);
            float2 j = hash21(cell + float2(float(i) * 17.0, float(i) * 31.0));
            float2 star = (cell + j) / DENSITY;
            if (abs(star.x) > 1.0 || abs(star.y) > 1.0) { continue; }

            float2 A = star * halfRes;
            float L = length(A);
            if (L < 1e-4) { continue; }
            float2 dir = A / L;
            float along = clamp(dot(P, dir), L / zt, L / z);
            float d = length(P - dir * along);
            float q = max(0.0, 1.0 - d / DOT_PX);
            float splat = q * q;
            float bright = 0.55 + 0.45 * hash11(cell.x * 73.0 + cell.y * 149.0 + float(i));
            density = max(density, splat * alpha * bright);
            near = max(near, splat * (1.0 - z / Z_FAR));
        }
    }

    float3 rgb = lerp(ink.rgb, float3(1.0, 1.0, 1.0), clamp(near, 0.0, 1.0) * NEAR_GLOW);
    rgb = lerp(backdrop.rgb, rgb, clamp(density, 0.0, 1.0) * opacity);
    return float4(rgb, 1.0);
}
"""

#: A rectangular grid corridor with the camera flying through it.
#:
#: This scene is genuinely 3D, and it is the one the per-pixel form suits *better*
#: than segments did. The CPU version placed world points on the four walls, pushed
#: them through a moving camera and stroked the resulting polyline; here the same
#: transform is simply run backwards. Each pixel recovers its own view ray, meets
#: the corridor analytically — the corridor is a box around the camera, so exactly
#: one of the four walls is hit — and asks the grid at that point how close the
#: nearest line is. No geometry is generated at all.
#:
#: What that buys, beyond cost: line width is filtered by the screen-space
#: derivative, so a rail stays a crisp constant width all the way to the vanishing
#: point instead of aliasing into a dotted crawl, and where the grid finally packs
#: tighter than a pixel it fades out rather than boiling into a wash. The camera
#: sway, ring spacing and depth fade are the segment scene's, unchanged.
GRID_MSL = """
// --- tunables ---------------------------------------------------------------
constant float RING_SPACING = 0.5;   // world distance between rings
constant float Z_NEAR       = 0.28;  // depth window actually drawn. NEAR is close
constant float Z_FAR        = 9.0;   // on purpose; FAR is where the fade reaches 0
constant float HALF_H       = 1.0;   // corridor half-height; half-width follows aspect
constant float FORWARD      = 0.35;  // world units travelled per second
constant float FADE_GAMMA   = 1.2;   // >1 holds the near/middle bright
constant float RAILS_V      = 5.0;   // rails up the side walls
constant float RAILS_H_MAX  = 12.0;  // cap on floor/ceiling rails in a wide window
constant float CAM_DRIFT_X  = 0.30;  // sway amplitudes, world units and radians
constant float CAM_DRIFT_Y  = 0.18;
constant float CAM_YAW      = 0.10;
constant float CAM_PITCH    = 0.07;
constant float RATE_X       = 0.037; // sway rates, cycles/sec. Mutually
constant float RATE_Y       = 0.029; // incommensurate -- periods of ~27, 34, 43
constant float RATE_YAW     = 0.023; // and 53s -- so the motion never reads as
constant float RATE_PITCH   = 0.019; // a loop
constant float LINE_PX      = 1.1;   // grid line width, in pixels
constant float NEAR_GLOW    = 0.35;  // how far near geometry pales toward white
constant float TAU          = 6.283185307;

// A grid line as coverage rather than a hit test. `p` is a coordinate that reaches
// an integer on every line, so the distance to the nearest one is |p - round(p)|.
// fwidth gives how far p moves per pixel, which is what converts a width in pixels
// into the right threshold *and* antialiases the edge -- the whole reason a line
// stays crisp into the distance here. Past the point where one pixel spans a whole
// period the grid can no longer be resolved, so it fades out instead of turning
// into a solid wash.
static inline float grid_line(float p) {
    float w = max(fwidth(p), 1e-5);
    float halfWidth = LINE_PX * 0.5 * w;
    float d = abs(p - round(p));
    float m = 1.0 - smoothstep(halfWidth, halfWidth + w, d);
    return m * (1.0 - smoothstep(0.25, 0.6, w));
}

static inline float depth_fade(float depth) {
    float f = (Z_FAR - depth) / (Z_FAR - Z_NEAR);
    return pow(clamp(f, 0.0, 1.0), FADE_GAMMA);
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    float2 halfRes = u.resolution * 0.5;
    float focal = halfRes.y;
    float halfH = HALF_H;
    float halfW = HALF_H * (u.resolution.x / u.resolution.y);
    float t = u.time;

    float camX  = CAM_DRIFT_X * sin(t * RATE_X * TAU);
    float camY  = CAM_DRIFT_Y * sin(t * RATE_Y * TAU + 1.7);
    float yaw   = CAM_YAW * sin(t * RATE_YAW * TAU + 0.6);
    float pitch = CAM_PITCH * sin(t * RATE_PITCH * TAU + 2.4);
    float camZ  = t * FORWARD;

    // This pixel's view ray, rotated back onto the world axes: the inverse of the
    // yaw-then-pitch the scene is viewed through.
    float2 P = pos.xy - halfRes;
    float cy = cos(yaw), sy = sin(yaw);
    float cp = cos(pitch), sp = sin(pitch);
    float rx = P.x / focal, ry = P.y / focal;
    float z1 = -ry * sp + cp;
    float dy =  ry * cp + sp;
    float dx =  rx * cy + z1 * sy;
    float dz = -rx * sy + z1 * cy;

    // Meet the nearest wall. Everything below stays branch-free of the derivative
    // calls: fwidth is undefined under non-uniform control flow, and the corridor
    // corners are exactly where neighbouring pixels would disagree.
    float tx = 1e9, ty = 1e9;
    if (abs(dx) > 1e-6) { tx = ((dx > 0.0 ? halfW : -halfW) - camX) / dx; }
    if (abs(dy) > 1e-6) { ty = ((dy > 0.0 ? halfH : -halfH) - camY) / dy; }
    bool sideWall = tx < ty;
    float s = clamp(min(tx, ty), 0.0, 1e6);
    float depth = s * dz;

    float visible = (dz > 1e-4 && depth >= Z_NEAR && depth <= Z_FAR) ? 1.0 : 0.0;

    // Rings sit at fixed world z, so relative to the moving camera their parameter
    // is depth/spacing offset by how far through a cell the camera has travelled --
    // which makes the recycling seamless by construction.
    float ring = depth / RING_SPACING + fract(camZ / RING_SPACING);

    // Rails: floor/ceiling carry lanes across the width, the side walls up the
    // height. The count follows the corridor's aspect so cells stay roughly square.
    float railsH = max(2.0, min(RAILS_H_MAX, round(RAILS_V * halfW / halfH)));
    float wx = camX + s * dx;
    float wy = camY + s * dy;
    // Both walls' rails are evaluated for every pixel and only *then* selected.
    // Putting the grid_line calls inside the branch instead makes their fwidth
    // conditional, and the corridor corners -- the one place neighbouring pixels
    // disagree about which wall they hit -- come out as dashed lines.
    float mSide = grid_line((wy + halfH) / (2.0 * halfH / RAILS_V));
    float mFloor = grid_line((wx + halfW) / (2.0 * halfW / railsH));
    float mRail = sideWall ? mSide : mFloor;

    float lit = max(grid_line(ring), mRail) * depth_fade(depth) * visible;

    float3 rgb = mix(u.ink.rgb, float3(1.0),
                     clamp(1.0 - depth / Z_FAR, 0.0, 1.0) * NEAR_GLOW);
    rgb = mix(u.backdrop.rgb, rgb, clamp(lit, 0.0, 1.0) * u.opacity);
    return float4(rgb, 1.0);
}
"""

#: The HLSL translation of :data:`GRID_MSL`. Line-for-line; only the dialect differs.
#: Keep the two in sync when tuning the scene.
GRID_HLSL = """
// --- tunables (see GRID_MSL for the rationale of each) -----------------------
static const float RING_SPACING = 0.5;
static const float Z_NEAR       = 0.28;
static const float Z_FAR        = 9.0;
static const float HALF_H       = 1.0;
static const float FORWARD      = 0.35;
static const float FADE_GAMMA   = 1.2;
static const float RAILS_V      = 5.0;
static const float RAILS_H_MAX  = 12.0;
static const float CAM_DRIFT_X  = 0.30;
static const float CAM_DRIFT_Y  = 0.18;
static const float CAM_YAW      = 0.10;
static const float CAM_PITCH    = 0.07;
static const float RATE_X       = 0.037;
static const float RATE_Y       = 0.029;
static const float RATE_YAW     = 0.023;
static const float RATE_PITCH   = 0.019;
static const float LINE_PX      = 1.1;
static const float NEAR_GLOW    = 0.35;
static const float TAU          = 6.283185307;

float grid_line(float p) {
    float w = max(fwidth(p), 1e-5);
    float halfWidth = LINE_PX * 0.5 * w;
    float d = abs(p - round(p));
    float m = 1.0 - smoothstep(halfWidth, halfWidth + w, d);
    return m * (1.0 - smoothstep(0.25, 0.6, w));
}

float depth_fade(float depth) {
    float f = (Z_FAR - depth) / (Z_FAR - Z_NEAR);
    return pow(saturate(f), FADE_GAMMA);
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float2 halfRes = resolution * 0.5;
    float focal = halfRes.y;
    float halfH = HALF_H;
    float halfW = HALF_H * (resolution.x / resolution.y);
    float t = time;

    float camX  = CAM_DRIFT_X * sin(t * RATE_X * TAU);
    float camY  = CAM_DRIFT_Y * sin(t * RATE_Y * TAU + 1.7);
    float yaw   = CAM_YAW * sin(t * RATE_YAW * TAU + 0.6);
    float pitch = CAM_PITCH * sin(t * RATE_PITCH * TAU + 2.4);
    float camZ  = t * FORWARD;

    float2 P = pos.xy - halfRes;
    float cy = cos(yaw), sy = sin(yaw);
    float cp = cos(pitch), sp = sin(pitch);
    float rx = P.x / focal, ry = P.y / focal;
    float z1 = -ry * sp + cp;
    float dy =  ry * cp + sp;
    float dx =  rx * cy + z1 * sy;
    float dz = -rx * sy + z1 * cy;

    float tx = 1e9, ty = 1e9;
    if (abs(dx) > 1e-6) { tx = ((dx > 0.0 ? halfW : -halfW) - camX) / dx; }
    if (abs(dy) > 1e-6) { ty = ((dy > 0.0 ? halfH : -halfH) - camY) / dy; }
    bool sideWall = tx < ty;
    float s = clamp(min(tx, ty), 0.0, 1e6);
    float depth = s * dz;

    float visible = (dz > 1e-4 && depth >= Z_NEAR && depth <= Z_FAR) ? 1.0 : 0.0;

    float ring = depth / RING_SPACING + frac(camZ / RING_SPACING);

    float railsH = max(2.0, min(RAILS_H_MAX, round(RAILS_V * halfW / halfH)));
    float wx = camX + s * dx;
    float wy = camY + s * dy;
    // See the MSL twin: evaluating both before the select keeps fwidth uniform.
    float mSide = grid_line((wy + halfH) / (2.0 * halfH / RAILS_V));
    float mFloor = grid_line((wx + halfW) / (2.0 * halfW / railsH));
    float mRail = sideWall ? mSide : mFloor;

    float lit = max(grid_line(ring), mRail) * depth_fade(depth) * visible;

    float3 rgb = lerp(ink.rgb, float3(1.0, 1.0, 1.0),
                      saturate(1.0 - depth / Z_FAR) * NEAR_GLOW);
    rgb = lerp(backdrop.rgb, rgb, saturate(lit) * opacity);
    return float4(rgb, 1.0);
}
"""

#: Drifting nodes linked to their near neighbours, edges fading with distance.
#:
#: This is the scene that fought the per-pixel form hardest, and the one place the
#: port is a *reinterpretation* rather than a translation. Its identity is global
#: nearest-neighbour topology — which pairs are linked depends on where every node
#: is — and that is exactly what a shader, asked about one pixel at a time, cannot
#: survey. So the field is rebuilt on a grid: one node per cell, its position and
#: motion hashed from the cell index.
#:
#: The cell is sized so the link radius spans a little over one cell
#: (:data:`LINK_CELLS`). That ratio is load-bearing in both directions. Too large and
#: every node links to everything nearby; too small — a cell *equal* to the link
#: radius, the obvious first choice — and a regular grid puts every neighbour at
#: almost exactly the link distance, where the distance falloff sends the edge to
#: zero alpha and the net renders as bare dots. At 1.4 cells a typical neighbour sits
#: at ~0.7 of the radius, so edges are actually visible and the orbits below spread
#: the rest across the falloff.
#:
#: That ratio also bounds the search: an edge reaches at most 1.4 cells, so for any
#: pixel an edge crosses, both endpoints lie within a link of it and therefore inside
#: the 5x5 block around it. Cells whose nearest corner is already out of range are
#: rejected before their node is even evaluated, so the usual cost is far below the
#: 25 that bound allows.
#:
#: What changed, deliberately. The CPU scene drifted nodes in straight lines that
#: wrapped at the view border; a wrapping node cannot stay in the cell that owns it,
#: and the cell is how a pixel finds it. So a node orbits inside its own cell
#: instead — a circle at constant angular speed, with its own radius, rate and
#: handedness. That directly answers the objection the original raised against
#: sinusoidal paths: a sine dwells at its turning points and piles nodes up, while a
#: circle traversed at constant speed has no turning points and is uniform in time.
#: The character survives (a calm net, drifting, edges dissolving as nodes part);
#: what is gone is a node crossing the entire window over half a minute.
CONSTELLATION_MSL = """
// --- tunables ---------------------------------------------------------------
constant float CELL_FRACTION = 0.16;  // cell size as a fraction of the short side;
                                      // this is what sets how many nodes there are
constant float LINK_CELLS    = 1.4;   // link radius, in cells -- see the note above
constant float DRIFT_RATE    = 0.035; // orbit rate, cycles/sec
constant float EDGE_FADE     = 0.10;  // border fade width, fraction of the view
constant float ORBIT_MIN     = 0.15;  // orbit radius range, in cells. Varying it is
constant float ORBIT_RANGE   = 0.30;  // what stops the cells reading as a lattice
constant float NODE_PX       = 1.7;   // node dot radius, pixels
constant float LINE_PX       = 1.0;   // edge half-width, pixels
constant float EDGE_ALPHA    = 0.5;   // edges stay clearly secondary to the nodes
constant float NODE_ALPHA    = 0.85;
constant float NODE_GLOW     = 0.45;  // how far a node core pales toward white
constant float NEAR_SPAN     = 0.5;   // distance, in cells, at which an edge is at
                                      // full strength -- see the falloff note below
constant float TAU           = 6.283185307;

static inline float2 hash21(float2 p) {
    float3 v = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return fract((v.xx + v.yz) * v.zy);
}

// Fade to nothing at the view border, so the net dissolves into the edges of the
// window instead of being cut off by them.
static inline float border_fade(float a) {
    return clamp(min(a, 1.0 - a) / EDGE_FADE, 0.0, 1.0);
}

// A node stays inside the cell that owns it -- that is what lets a pixel find it by
// index at all. A circle at constant angular speed, so the motion is uniform in
// time and never dwells; radius, rate and handedness all come from the cell.
static inline float2 node_at(float2 cell, float cellPx, float t) {
    float2 h = hash21(cell);
    float2 g = hash21(cell + 37.0);
    float radius = ORBIT_MIN + ORBIT_RANGE * h.x;
    float rate = DRIFT_RATE * (0.6 + 0.8 * h.y);
    float spin = (g.x < 0.5) ? -1.0 : 1.0;
    float ang = spin * t * TAU * rate + g.y * TAU;
    return (cell + 0.5 + float2(cos(ang), sin(ang)) * radius) * cellPx;
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    float cellPx = CELL_FRACTION * min(u.resolution.x, u.resolution.y);
    float link = LINK_CELLS * cellPx;
    float2 base = floor(pos.xy / cellPx);

    float2 nodes[25];
    float  fades[25];
    int k = 0;
    for (int oy = -2; oy <= 2; ++oy) {
        for (int ox = -2; ox <= 2; ++ox) {
            float2 cell = base + float2(float(ox), float(oy));
            // Reject on the cell's bounds before evaluating its node: the corners of
            // the 5x5 are always out of range, and this skips their trig entirely.
            float2 lo = cell * cellPx;
            float2 far = max(max(lo - pos.xy, pos.xy - (lo + cellPx)), float2(0.0));
            if (dot(far, far) > link * link) {
                nodes[k] = float2(0.0);
                fades[k] = 0.0;
                k++;
                continue;
            }
            float2 p = node_at(cell, cellPx, u.time);
            nodes[k] = p;
            float2 nrm = p / u.resolution;
            fades[k] = border_fade(nrm.x) * border_fade(nrm.y);
            k++;
        }
    }

    float lit = 0.0;   // coverage at this pixel
    float hot = 0.0;   // node cores only, for the glow

    for (int a = 0; a < 25; ++a) {
        float fa = fades[a];
        if (fa <= 0.0) { continue; }
        float2 pa = nodes[a];
        float da = length(pos.xy - pa);
        // Only a node within one link of this pixel can put an edge across it: a
        // pixel on an edge lies between its ends, so it is within `len` of both.
        // The inner loop runs over every other node (not just b > a), which is what
        // keeps this prune from dropping an edge whose far end is out of range.
        if (da >= link) { continue; }

        float q = max(0.0, 1.0 - da / NODE_PX);
        float dot_ = q * q * fa;
        hot = max(hot, dot_);
        lit = max(lit, dot_ * NODE_ALPHA);

        for (int b = 0; b < 25; ++b) {
            if (b == a) { continue; }
            float fb = fades[b];
            if (fb <= 0.0) { continue; }
            float2 e = nodes[b] - pa;
            float len = length(e);
            if (len >= link || len < 1e-4) { continue; }
            float2 dir = e / len;
            float along = clamp(dot(pos.xy - pa, dir), 0.0, len);
            float d = length(pos.xy - pa - dir * along);
            float m = max(0.0, 1.0 - d / LINE_PX);
            if (m <= 0.0) { continue; }
            // Falloff measured against the *cell spacing*, not the link radius. The
            // CPU scene scattered its nodes at random, so plenty of pairs sat well
            // inside the radius and a falloff over the full radius gave a usable
            // spread. On a grid every neighbour is about one cell away, so that same
            // falloff drops them all to the same near-zero alpha and the net renders
            // as bare dots. Anchoring full strength at half a cell restores the range.
            float f = clamp((link - len) / (link - cellPx * NEAR_SPAN), 0.0, 1.0);
            lit = max(lit, m * m * f * EDGE_ALPHA * fa * fb);
        }
    }

    float3 rgb = mix(u.ink.rgb, float3(1.0), clamp(hot, 0.0, 1.0) * NODE_GLOW);
    rgb = mix(u.backdrop.rgb, rgb, clamp(lit, 0.0, 1.0) * u.opacity);
    return float4(rgb, 1.0);
}
"""

#: The HLSL translation of :data:`CONSTELLATION_MSL`. Line-for-line; only the dialect
#: differs. Keep the two in sync when tuning the scene.
CONSTELLATION_HLSL = """
// --- tunables (see CONSTELLATION_MSL for the rationale of each) --------------
static const float CELL_FRACTION = 0.16;
static const float LINK_CELLS    = 1.4;
static const float DRIFT_RATE    = 0.035;
static const float EDGE_FADE     = 0.10;
static const float ORBIT_MIN     = 0.15;
static const float ORBIT_RANGE   = 0.30;
static const float NODE_PX       = 1.7;
static const float LINE_PX       = 1.0;
static const float EDGE_ALPHA    = 0.5;
static const float NODE_ALPHA    = 0.85;
static const float NODE_GLOW     = 0.45;
static const float NEAR_SPAN     = 0.5;
static const float TAU           = 6.283185307;

float2 hash21(float2 p) {
    float3 v = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return frac((v.xx + v.yz) * v.zy);
}

float border_fade(float a) {
    return saturate(min(a, 1.0 - a) / EDGE_FADE);
}

float2 node_at(float2 cell, float cellPx, float t) {
    float2 h = hash21(cell);
    float2 g = hash21(cell + 37.0);
    float radius = ORBIT_MIN + ORBIT_RANGE * h.x;
    float rate = DRIFT_RATE * (0.6 + 0.8 * h.y);
    float spin = (g.x < 0.5) ? -1.0 : 1.0;
    float ang = spin * t * TAU * rate + g.y * TAU;
    return (cell + 0.5 + float2(cos(ang), sin(ang)) * radius) * cellPx;
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float cellPx = CELL_FRACTION * min(resolution.x, resolution.y);
    float link = LINK_CELLS * cellPx;
    float2 base = floor(pos.xy / cellPx);

    float2 nodes[25];
    float  fades[25];
    int k = 0;
    for (int oy = -2; oy <= 2; ++oy) {
        for (int ox = -2; ox <= 2; ++ox) {
            float2 cell = base + float2(float(ox), float(oy));
            float2 lo = cell * cellPx;
            float2 far = max(max(lo - pos.xy, pos.xy - (lo + cellPx)), float2(0.0, 0.0));
            if (dot(far, far) > link * link) {
                nodes[k] = float2(0.0, 0.0);
                fades[k] = 0.0;
                k++;
                continue;
            }
            float2 p = node_at(cell, cellPx, time);
            nodes[k] = p;
            float2 nrm = p / resolution;
            fades[k] = border_fade(nrm.x) * border_fade(nrm.y);
            k++;
        }
    }

    float lit = 0.0;
    float hot = 0.0;

    for (int a = 0; a < 25; ++a) {
        float fa = fades[a];
        if (fa <= 0.0) { continue; }
        float2 pa = nodes[a];
        float da = length(pos.xy - pa);
        if (da >= link) { continue; }

        float q = max(0.0, 1.0 - da / NODE_PX);
        float dotv = q * q * fa;
        hot = max(hot, dotv);
        lit = max(lit, dotv * NODE_ALPHA);

        for (int b = 0; b < 25; ++b) {
            if (b == a) { continue; }
            float fb = fades[b];
            if (fb <= 0.0) { continue; }
            float2 e = nodes[b] - pa;
            float len = length(e);
            if (len >= link || len < 1e-4) { continue; }
            float2 dir = e / len;
            float along = clamp(dot(pos.xy - pa, dir), 0.0, len);
            float d = length(pos.xy - pa - dir * along);
            float m = max(0.0, 1.0 - d / LINE_PX);
            if (m <= 0.0) { continue; }
            float f = saturate((link - len) / (link - cellPx * NEAR_SPAN));
            lit = max(lit, m * m * f * EDGE_ALPHA * fa * fb);
        }
    }

    float3 rgb = lerp(ink.rgb, float3(1.0, 1.0, 1.0), saturate(hot) * NODE_GLOW);
    rgb = lerp(backdrop.rgb, rgb, saturate(lit) * opacity);
    return float4(rgb, 1.0);
}
"""

#: Every scene TFM offers, by the name a theme's ``animation`` key uses, paired with
#: the puikit ``Shader`` fields that belong to the scene rather than to the theme.
#: ``_resolve_background`` in ``tfm.py`` resolves a theme's ``animation`` name here
#: and nowhere else: a name absent from this dict yields no background at all, so a
#: typo in a theme costs the scene rather than startup.
#:
#: ``resolution_scale`` is per scene because only the scene knows how much sharpness
#: it can give up. The wave is diffuse grain — indistinguishable at half resolution
#: and four times cheaper there, which is what keeps it affordable on a Retina
#: display. Every other scene here is thin bright lines, where halving the scale and
#: upscaling would trade away the crispness that is the point of drawing them.
SHADER_KINDS: dict[str, dict] = {
    "wave": {"source": WAVE_MSL, "source_hlsl": WAVE_HLSL, "resolution_scale": 0.5},
    # Rain renders at full resolution: it is thin bright lines, and at half scale the
    # upscale makes them crawl and shimmer. It can afford to — a pixel tests three
    # columns and most exit before touching a drop.
    "rain": {"source": RAIN_MSL, "source_hlsl": RAIN_HLSL},
    # Also full resolution: streaks are thin and near-white at the head, and halving
    # the scale turns them into crawling smudges.
    "starfield": {"source": STARFIELD_MSL, "source_hlsl": STARFIELD_HLSL},
    # The corridor is all thin straight lines, and its whole gain over the segment
    # version is derivative-filtered width. Rendering at half scale and upscaling
    # would throw exactly that away.
    "grid": {"source": GRID_MSL, "source_hlsl": GRID_HLSL},
    # Dots and hairline edges, so again full resolution.
    "constellation": {"source": CONSTELLATION_MSL, "source_hlsl": CONSTELLATION_HLSL},
}
