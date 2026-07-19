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
cells could possibly reach it and consult only those. The rain visits its own column
and two neighbours, the starfield cells along a depth ray, the constellation a 5x5
block of nodes. The wave takes the idea furthest: it *texture-maps* its cells rather
than walking them, sampling a procedural dot field in the sheet's own plane, which
decouples its particle count from its per-pixel cost entirely. Where a scene needs
per-object randomness it hashes the cell index rather than calling anything
time-varying, so an object keeps a fixed identity across frames and all motion comes
from ``time``. The earth is the exception that shows what the device is *for*: it
holds a single object, so a pixel can simply ask whether it is inside the disc and
solve the sphere in closed form — no grid needed, because nothing has to be searched
for.
"""

from __future__ import annotations

#: A flowing sheet of particles — a wave surface rendered as a point cloud.
#:
#: Structure: the surface is a sum of travelling sine trains, sampled at a stack of
#: depth layers. Rather than *placing* particles, each layer **texture-maps** them:
#: a procedural dot field is sampled in the sheet's own (x, z) plane, and the layer
#: keeps whatever dots sit at the height that projects onto this pixel. That
#: inversion is what makes the particle count free — density is the texture's
#: frequency, not a loop bound — and it is why this scene draws several times the
#: particles of the cell-walking version it replaces at slightly *less* cost.
#:
#: There is no texture *asset*: puikit's background shaders take uniforms and bind
#: no images (see puikit ``SHADER_PRELUDE``), so the dot field is generated in
#: place. That is the better trade anyway — a procedural field is infinite, tiles
#: without a seam, and can be sampled at any frequency, so nothing has to be
#: uploaded or kept resident to make the sheet denser.
#:
#: Three octaves of that field are sampled per layer, each **rotating** in the
#: plane at its own slow rate. Rotation is what turns a fixed lattice into drifting
#: particles, and because the rates are mutually incommensurate the octaves never
#: re-align — the sheet churns instead of sliding, and never visibly repeats.
#:
#: The colour is the part the CPU renderer could never do: hue shifts along the
#: sheet and toward the crests, so the wave runs cool in its troughs and pales to
#: near-white where it peaks, in the spirit of the reference. It is anchored on the
#: theme's ``ink`` so it still belongs to the palette rather than ignoring it.
WAVE_MSL = """
// --- tunables ---------------------------------------------------------------
// LAYERS x 3 octaves is the per-pixel iteration count and the dominant cost. Each
// octave is a single texture lookup -- the neighbouring-cell visits the previous
// version needed are gone (see `splat`), which is what buys the extra octaves and
// the doubled layer count. Everything in the loop is transcendental-free except
// the surface and the per-octave rotation.
constant int   LAYERS      = 24;     // depth slabs sampled per pixel
constant float Z_NEAR      = 1.5;    // nearest / furthest sheet depth
constant float Z_FAR       = 5.2;
constant float CAM_H       = 0.62;   // camera height above the sheet
constant float HORIZON     = 0.36;   // sheet's vanishing line, fraction of height
constant float FOCAL       = 0.85;   // focal length in view-height units
constant float FREQ        = 24.0;   // texture cells per world unit
constant float DOT_FRAC    = 0.18;   // dot radius as a fraction of a cell
constant float SPRAY       = 0.34;   // how far a lofted particle rises
constant float GAIN        = 10.0;   // overall brightness of the accumulation
constant float THICK       = 1.0;    // band half-thickness, in dot radii

// Particle jitter, loft and brightness must be fixed per particle, so they come
// from its cell index rather than anything time-varying -- otherwise every particle
// would reshuffle each frame. This is the arithmetic-only variety on purpose: the
// usual fract(sin(n)*43758.0) idiom costs a transcendental, and at 72 lookups per
// pixel that alone would be a third of the frame.
static inline float3 hash33(float2 p) {
    float3 v = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return fract((v.xxy + v.yzz) * v.zyx);
}

// The surface: three travelling sine trains at unrelated angles and wavelengths,
// which fold into each other instead of reading as corrugation.
static inline float surface(float x, float z, float t) {
    return 0.32 * sin(1.30 * x + 0.55 * z + 0.55 * t)
         + 0.18 * sin(-0.85 * x + 1.30 * z + 0.41 * t)
         + 0.10 * sin(2.40 * x - 0.90 * z + 0.72 * t);
}

// One octave of the particle texture. Rotates the plane by `ang`, lands in a cell,
// and measures the distance to that cell's jittered dot; `dy` is how far this pixel
// sits above the sheet, so the dot only registers if its height projects here.
// Returns the density contribution in .x and coverage in .y (for crest colouring).
static inline float2 splat(float2 p, float freq, float ang, float lodPix, float dy) {
    float s = sin(ang), c = cos(ang);
    float2 q = float2(c * p.x - s * p.y, s * p.x + c * p.y) * freq;
    float2 cell = floor(q);
    float2 f = q - cell;
    float3 rnd = hash33(cell);
    // Jitter is bounded so the dot cannot cross a cell edge. That is the whole
    // trick: one lookup is then *exact*, with none of the neighbouring-cell visits
    // the placed-particle version needed to avoid seams -- and it only holds while
    // the dots stay small, so finer dots make this scene cheaper, not dearer.
    float2 center = float2(0.5) + (rnd.xy - 0.5) * 0.62;
    float d = length(f - center);
    // Widen the dot to the pixel footprint once the cell goes subpixel, so distant
    // layers dissolve toward their average instead of aliasing into crawling noise.
    float r = max(DOT_FRAC, lodPix * freq);
    float cov = max(0.0, 1.0 - d / r);
    cov = cov * cov * (DOT_FRAC / r);      // conserve energy as it widens
    // Half-thickness comes from *this* octave's radius, so a dot is as tall as it
    // is wide at every frequency. Deriving it from one shared frequency instead
    // stretches the finer octaves into vertical dashes.
    float rw = r / freq * THICK;
    float loft = rnd.z * rnd.z * rnd.z;    // most on the sheet, a few lofted high
    float band = max(0.0, 1.0 - abs(dy - loft * SPRAY) / rw);
    // A second, independent value out of the same hash. Without it every dot peaks
    // at one brightness and the sheet reads as uniform grain rather than particles.
    float bright = (0.55 + 0.45 * fract(rnd.z * 13.7)) * (1.0 - 0.7 * loft);
    return float2(cov * band * band * bright, cov * band);
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

        // The projection, run backwards. Instead of placing a particle and asking
        // where it lands, ask what this pixel is looking at: at this depth the ray
        // crosses the sheet at wx, and only a particle at height py projects here.
        float wx = px * z / FOCAL;
        float py = CAM_H - (uv.y - HORIZON) * z / FOCAL;
        float h = surface(wx, z, t);

        // One pixel's width in world units at this depth, for the LOD widening.
        float lodPix = (z / FOCAL) / u.resolution.y;

        // Three octaves at unrelated frequencies, each rotating at its own rate.
        float2 p = float2(wx, z);
        float dy = py - h;
        float2 a = splat(p, FREQ,         0.050 * t,         lodPix, dy);
        float2 b = splat(p, FREQ * 1.70, -0.037 * t + 2.1,   lodPix, dy);
        float2 c = splat(p, FREQ * 2.60,  0.021 * t + 4.7,   lodPix, dy);

        density += (a.x * 1.00 + b.x * 0.80 + c.x * 0.60) * layerFade;
        crest = max(crest, (a.y + b.y) * (0.5 + 0.5 * h / 0.6));
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
static const int   LAYERS   = 24;
static const float Z_NEAR   = 1.5;
static const float Z_FAR    = 5.2;
static const float CAM_H    = 0.62;
static const float HORIZON  = 0.36;
static const float FOCAL    = 0.85;
static const float FREQ     = 24.0;
static const float DOT_FRAC = 0.18;
static const float SPRAY    = 0.34;
static const float GAIN     = 10.0;
static const float THICK    = 1.0;

float3 hash33(float2 p) {
    float3 v = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return frac((v.xxy + v.yzz) * v.zyx);
}
float surface(float x, float z, float t) {
    return 0.32 * sin(1.30 * x + 0.55 * z + 0.55 * t)
         + 0.18 * sin(-0.85 * x + 1.30 * z + 0.41 * t)
         + 0.10 * sin(2.40 * x - 0.90 * z + 0.72 * t);
}

// One octave of the particle texture -- see the MSL twin for what each step is for.
float2 splat(float2 p, float freq, float ang, float lodPix, float dy) {
    float s = sin(ang), c = cos(ang);
    float2 q = float2(c * p.x - s * p.y, s * p.x + c * p.y) * freq;
    float2 cell = floor(q);
    float2 f = q - cell;
    float3 rnd = hash33(cell);
    float2 center = float2(0.5, 0.5) + (rnd.xy - 0.5) * 0.62;
    float d = length(f - center);
    float r = max(DOT_FRAC, lodPix * freq);
    float cov = max(0.0, 1.0 - d / r);
    cov = cov * cov * (DOT_FRAC / r);
    float rw = r / freq * THICK;
    float loft = rnd.z * rnd.z * rnd.z;
    float band = max(0.0, 1.0 - abs(dy - loft * SPRAY) / rw);
    float bright = (0.55 + 0.45 * frac(rnd.z * 13.7)) * (1.0 - 0.7 * loft);
    return float2(cov * band * band * bright, cov * band);
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
        float py = CAM_H - (uv.y - HORIZON) * z / FOCAL;
        float h = surface(wx, z, t);

        float lodPix = (z / FOCAL) / resolution.y;

        float2 p = float2(wx, z);
        float dy = py - h;
        float2 a = splat(p, FREQ,         0.050 * t,         lodPix, dy);
        float2 b = splat(p, FREQ * 1.70, -0.037 * t + 2.1,   lodPix, dy);
        float2 c = splat(p, FREQ * 2.60,  0.021 * t + 4.7,   lodPix, dy);

        density += (a.x * 1.00 + b.x * 0.80 + c.x * 0.60) * layerFade;
        crest = max(crest, (a.y + b.y) * (0.5 + 0.5 * h / 0.6));
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
            // Travel 0->1 walks the head from a streak's length above the view to
            // a streak's length below it, so the streak both enters already fully
            // formed and stays until its tail has cleared the bottom edge. Stopping
            // the head at H would wrap the drop while the tail still covered the
            // last streakLen of the screen, and the drop would blink out early.
            float travel = fract(u.time * RATE * fall + phase);
            float hy = travel * (H + 2.0 * streakLen) - streakLen;
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
            float hy = travel * (H + 2.0 * streakLen) - streakLen;
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
constant float BRIGHTNESS   = 0.5;   // how far a lit line gets toward full ink
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
    rgb = mix(u.backdrop.rgb, rgb, clamp(lit, 0.0, 1.0) * BRIGHTNESS * u.opacity);
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
static const float BRIGHTNESS   = 0.5;
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
    rgb = lerp(backdrop.rgb, rgb, saturate(lit) * BRIGHTNESS * opacity);
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

#: Horizontal data traffic — layered tracks of dashes streaming past the viewer.
#:
#: The look this chases is a telemetry wall seen side-on: rows of bright segments of
#: many lengths sliding by at different rates, faint tick marks standing between
#: them, the whole field clumping into busy and quiet regions. Where :data:`RAIN_MSL`
#: falls, this *travels* — the two are the same idea rotated, but the differences
#: that matter are the ones a rotation does not give you: parallax layers, a
#: leading-edge hot head, and the vertical connectors.
#:
#: Structure: each layer is a stack of rows, and a row is a lane of dashes. A pixel
#: finds its row by division and its dash by another, so it consults exactly one cell
#: per layer — no neighbour visits at all, because a dash is contained in its cell by
#: construction (the cell *is* the dash's slot; only its length varies). That is the
#: cheapest form the grid device takes anywhere in this module, which is what pays
#: for running several layers.
#:
#: Layers recede by a constant factor in pitch, cell length, speed and brightness, so
#: the far ones read as distance rather than as clutter. Every row flows the same
#: direction and differs only in rate: counter-flowing rows read as noise, while a
#: shared direction reads as travel.
#:
#: **Time is folded, not accumulated.** A lane's offset grows without bound, and
#: feeding ``x + t*speed`` straight into the cell hash would lose the fractional part
#: to float32 after a long uptime — the dashes would start to jitter on a machine
#: left running for days. So the offset is split into its integer cell count and its
#: fraction: the fraction positions the pixel inside a cell, the integer only
#: *identifies* which cell (wrapped at :data:`_DS_WRAP` cells, ~10^5 px of travel, so
#: the hash input stays exact). The field repeats after that, which is unobservable
#: and the whole point.
DATASTREAM_MSL = """
// --- tunables ---------------------------------------------------------------
constant int   LAYERS      = 3;     // depth stack; each is a full field of rows
constant float ROW_PX      = 13.0;  // row pitch of the nearest layer, pixels
constant float CELL_PX     = 240.0; // dash slot length of the nearest layer
constant float RATE        = 58.0;  // nearest layer's drift, pixels/second
constant float LINE_PX     = 1.5;   // dash thickness, pixels
constant float DASH_MIN    = 0.06;  // dash length as a fraction of its slot. Skewed
constant float DASH_RANGE  = 0.90;  // short (see DASH_SKEW) so the long ones are rare
constant float DASH_SKEW   = 2.0;   // and read as the exception rather than the rule
constant float HEAD_PX     = 14.0;  // hot leading edge, pixels -- a length, not a
                                    // fraction, so a long streak is not all head
constant float DENSITY     = 0.55;  // fraction of slots that carry a dash
constant float LAYER_STEP  = 0.62;  // each further layer's pitch/speed factor
constant float LAYER_DIM   = 0.60;  // ...and its brightness factor
constant float SPEED_MIN   = 0.35;  // per-row rate spread, x the layer's rate
constant float SPEED_RANGE = 1.30;
constant float TAIL_FLOOR  = 0.42;  // how far a dash dims from head to tail
constant float HEAD_GLOW   = 0.70;  // how far a leading edge pales toward white
constant float TICK_SHARE  = 0.30;  // share of dashes that also stand a tick
constant float TICK_PX     = 1.4;   // tick width, pixels
constant float TICK_FRAC   = 0.92;  // tick height, as a fraction of the row pitch
constant float TICK_ALPHA  = 0.85;
constant float WASH_X      = 2.6;   // the drifting density wash: spatial frequency
constant float WASH_Y      = 1.7;   // in each axis, and how fast it moves
constant float WASH_RATE   = 0.11;
constant float WASH_FLOOR  = 0.55;  // density multiplier at the quietest
constant float WASH_RANGE  = 0.60;
constant float AA_PX       = 0.8;   // edge softening, pixels
constant float CELL_WRAP   = 4096.0;// see the note on folding time, above

// The arithmetic-only hash used throughout this module: no transcendentals, and
// exact for the integer-valued inputs it is given here.
static inline float3 hash33(float2 p) {
    float3 v = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return fract((v.xxy + v.yzz) * v.zyx);
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    float t = u.time;
    float2 uv = pos.xy / u.resolution;

    // Busy and quiet regions drifting across the field. Modulating the *density*
    // threshold rather than the brightness is what makes it read as traffic
    // thinning out instead of the whole field dimming.
    float wash = 0.5 + 0.5 * sin(uv.x * WASH_X + t * WASH_RATE)
                           * sin(uv.y * WASH_Y - t * WASH_RATE * 0.77);
    float dens = DENSITY * (WASH_FLOOR + WASH_RANGE * wash);

    float lit = 0.0;   // coverage at this pixel
    float far = 0.0;   // the share of it owed to the receding layers, for the hue
    float hot = 0.0;   // proximity to a leading edge, for the white head

    float scale = 1.0;
    float dim = 1.0;
    for (int i = 0; i < LAYERS; ++i) {
        float rowH = ROW_PX * scale;
        float cellW = CELL_PX * scale;
        // Floors: the far layers must not thin below what a pixel can draw, or they
        // stop being distance and become a grey haze over the file list.
        float halfT = max(0.55, LINE_PX * 0.5 * scale);
        float tickHalf = rowH * TICK_FRAC * 0.5;

        float row = floor(pos.y / rowH);
        float dy = abs(pos.y - (row + 0.5) * rowH);
        // Most pixels sit in a row's gap. Rejecting on the tallest thing the row can
        // hold skips the rest of the layer for them.
        if (dy <= tickHalf + AA_PX) {
            float3 r = hash33(float2(row, float(i) * 91.0));
            float speed = RATE * scale * (SPEED_MIN + SPEED_RANGE * r.x);

            // Fold time: the fraction places this pixel in its slot, the integer
            // only names the slot (see the module note).
            float shift = t * speed / cellW;
            float shiftI = floor(shift);
            float uX = pos.x / cellW + (shift - shiftI);
            float cell = floor(uX);
            float f = uX - cell;
            float cid = fmod(cell + shiftI, CELL_WRAP);

            float3 c = hash33(float2(cid, row + float(i) * 313.0));
            if (c.x <= dens) {
                // Skewed short: most slots carry a stub, a few carry a streak most
                // of the slot long. A flat distribution gives every dash roughly the
                // same length, which reads as a dashed rule rather than as traffic.
                float dash = DASH_MIN + DASH_RANGE * pow(c.y, DASH_SKEW);
                float aa = AA_PX / cellW;          // the AA width, in slot units
                float bright = (0.45 + 0.55 * c.z) * dim;

                // The lane slides left, so f = 0 is the dash's leading edge.
                float covY = 1.0 - smoothstep(halfT, halfT + AA_PX, dy);
                float covX = smoothstep(0.0, aa, f)
                           * (1.0 - smoothstep(dash - aa, dash, f));
                float k = f / dash;                // 0 at the head, 1 at the tail
                float a = covX * covY * bright * mix(1.0, TAIL_FLOOR, k * k);
                lit = max(lit, a);
                far = max(far, a * (1.0 - dim));
                // The head is a fixed number of pixels, not a fraction of the dash:
                // a motion streak's hot tip is the same size however long the streak
                // is, and scaling it with the length makes the long ones glow end to
                // end instead of leading with a bright point.
                hot = max(hot, a * (1.0 - smoothstep(0.0, HEAD_PX, f * cellW)));

                // A vertical connector standing at the *trailing* end of some dashes
                // -- the circuit-trace tick. At the trailing end rather than the
                // leading one so it reads as a terminator: it carries the dash's
                // untapered brightness, so against the faded tail it stands out,
                // whereas at the head it would merge into the hot leading edge.
                // Confined to its own row on purpose: a tick spanning several rows
                // would have to be found by pixels in rows that do not own it, and
                // the one-cell lookup is what makes this scene cheap.
                if (c.x < TICK_SHARE * dens) {
                    float m = 1.0 - smoothstep(TICK_PX * 0.5, TICK_PX * 0.5 + AA_PX,
                                               abs(f - dash) * cellW);
                    float covT = 1.0 - smoothstep(tickHalf, tickHalf + AA_PX, dy);
                    lit = max(lit, m * covT * bright * TICK_ALPHA);
                }
            }
        }
        scale *= LAYER_STEP;
        dim *= LAYER_DIM;
    }

    // Colour: the near tracks carry the theme ink; the far ones recede toward a
    // cooler, bluer cast of it, and a leading edge pales toward white. Both ends are
    // the ink pushed rather than fixed colours, so the field stays on-palette.
    float3 nearInk = u.ink.rgb;
    float3 farInk = u.ink.rgb * float3(0.42, 0.80, 1.15);
    float3 rgb = mix(nearInk, farInk, clamp(far / max(lit, 1e-4), 0.0, 1.0));
    rgb = mix(rgb, float3(1.0), clamp(hot, 0.0, 1.0) * HEAD_GLOW);

    rgb = mix(u.backdrop.rgb, rgb, clamp(lit, 0.0, 1.0) * u.opacity);
    return float4(rgb, 1.0);
}
"""

#: The HLSL translation of :data:`DATASTREAM_MSL` (see :data:`WAVE_HLSL` for why a
#: scene ships both). Line-for-line; only the dialect differs — ``fract``/``mix``
#: become ``frac``/``lerp``, ``constant`` becomes ``static const``, and the uniforms
#: are cbuffer globals. Keep the two in sync when tuning the scene.
DATASTREAM_HLSL = """
// --- tunables (see DATASTREAM_MSL for the rationale of each) -----------------
static const int   LAYERS      = 3;
static const float ROW_PX      = 13.0;
static const float CELL_PX     = 240.0;
static const float RATE        = 58.0;
static const float LINE_PX     = 1.5;
static const float DASH_MIN    = 0.06;
static const float DASH_RANGE  = 0.90;
static const float DASH_SKEW   = 2.0;
static const float HEAD_PX     = 14.0;
static const float DENSITY     = 0.55;
static const float LAYER_STEP  = 0.62;
static const float LAYER_DIM   = 0.60;
static const float SPEED_MIN   = 0.35;
static const float SPEED_RANGE = 1.30;
static const float TAIL_FLOOR  = 0.42;
static const float HEAD_GLOW   = 0.70;
static const float TICK_SHARE  = 0.30;
static const float TICK_PX     = 1.4;
static const float TICK_FRAC   = 0.92;
static const float TICK_ALPHA  = 0.85;
static const float WASH_X      = 2.6;
static const float WASH_Y      = 1.7;
static const float WASH_RATE   = 0.11;
static const float WASH_FLOOR  = 0.55;
static const float WASH_RANGE  = 0.60;
static const float AA_PX       = 0.8;
static const float CELL_WRAP   = 4096.0;

float3 hash33(float2 p) {
    float3 v = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return frac((v.xxy + v.yzz) * v.zyx);
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float t = time;
    float2 uv = pos.xy / resolution;

    float wash = 0.5 + 0.5 * sin(uv.x * WASH_X + t * WASH_RATE)
                           * sin(uv.y * WASH_Y - t * WASH_RATE * 0.77);
    float dens = DENSITY * (WASH_FLOOR + WASH_RANGE * wash);

    float lit = 0.0;
    float far = 0.0;
    float hot = 0.0;

    float scale = 1.0;
    float dim = 1.0;
    for (int i = 0; i < LAYERS; ++i) {
        float rowH = ROW_PX * scale;
        float cellW = CELL_PX * scale;
        float halfT = max(0.55, LINE_PX * 0.5 * scale);
        float tickHalf = rowH * TICK_FRAC * 0.5;

        float row = floor(pos.y / rowH);
        float dy = abs(pos.y - (row + 0.5) * rowH);
        if (dy <= tickHalf + AA_PX) {
            float3 r = hash33(float2(row, float(i) * 91.0));
            float speed = RATE * scale * (SPEED_MIN + SPEED_RANGE * r.x);

            float shift = t * speed / cellW;
            float shiftI = floor(shift);
            float uX = pos.x / cellW + (shift - shiftI);
            float cell = floor(uX);
            float f = uX - cell;
            float cid = fmod(cell + shiftI, CELL_WRAP);

            float3 c = hash33(float2(cid, row + float(i) * 313.0));
            if (c.x <= dens) {
                float dash = DASH_MIN + DASH_RANGE * pow(c.y, DASH_SKEW);
                float aa = AA_PX / cellW;
                float bright = (0.45 + 0.55 * c.z) * dim;

                float covY = 1.0 - smoothstep(halfT, halfT + AA_PX, dy);
                float covX = smoothstep(0.0, aa, f)
                           * (1.0 - smoothstep(dash - aa, dash, f));
                float k = f / dash;
                float a = covX * covY * bright * lerp(1.0, TAIL_FLOOR, k * k);
                lit = max(lit, a);
                far = max(far, a * (1.0 - dim));
                hot = max(hot, a * (1.0 - smoothstep(0.0, HEAD_PX, f * cellW)));

                // See the MSL twin: the tick stands at the dash's trailing end.
                if (c.x < TICK_SHARE * dens) {
                    float m = 1.0 - smoothstep(TICK_PX * 0.5, TICK_PX * 0.5 + AA_PX,
                                               abs(f - dash) * cellW);
                    float covT = 1.0 - smoothstep(tickHalf, tickHalf + AA_PX, dy);
                    lit = max(lit, m * covT * bright * TICK_ALPHA);
                }
            }
        }
        scale *= LAYER_STEP;
        dim *= LAYER_DIM;
    }

    float3 nearInk = ink.rgb;
    float3 farInk = ink.rgb * float3(0.42, 0.80, 1.15);
    float3 rgb = lerp(nearInk, farInk, saturate(far / max(lit, 1e-4)));
    rgb = lerp(rgb, float3(1.0, 1.0, 1.0), saturate(hot) * HEAD_GLOW);

    rgb = lerp(backdrop.rgb, rgb, saturate(lit) * opacity);
    return float4(rgb, 1.0);
}
"""

#: A depth of holographic panels drifting toward the viewer — the data-wall look.
#:
#: Structure: a stack of planes at increasing depth, each tiled into cells, each cell
#: hosting one **panel** — a small flat HUD of rules, blocks and pseudo-text. A plane
#: sweeps from far to near and recycles, so panels grow and slide outward as they
#: approach and pass. This is :data:`STARFIELD_MSL`'s depth machinery carrying a
#: *drawing* instead of a dot, and it inherits that scene's key property: a panel's
#: identity comes from its position on the plane, which never moves, so approaching
#: it magnifies it rather than morphing it.
#:
#: A panel draws one of six things — typed pseudo-text, a bar chart, a line chart,
#: progress bars, a ring gauge, or a wireframe mesh — picked by a hash and read off a
#: threshold chain, so only the winning branch costs anything. Text is much the
#: commonest; the charts are punctuation.
#:
#: **Why the content is procedural blocks and not text.** A background shader is
#: handed uniforms and binds no textures — there is no font to sample, and glyph
#: rasterisation in a fragment function would cost more than the whole rest of the
#: scene. So a row of "text" is a run of blocks with text's *rhythm*: varied widths,
#: short gaps, a common baseline. At the size panels actually occupy that is what the
#: reference reads as anyway; the legibility was never there to lose.
#:
#: What it does need is text's **order**. A row types out left to right, holds, then
#: retypes with fresh content, with the mark under the head burning brighter — the
#: caret. Re-rolling every slot at once (what this did first) costs nothing less and
#: reads as noise: writing order is most of what identifies a row as writing.
#:
#: **Three nested grids, one lookup each.** Cell → panel, panel → row, row → block:
#: a pixel divides its way down to exactly one block and hashes it. Nothing is
#: iterated but the depth planes, which is what lets the field be this dense.
#:
#: **Speed.** Panels creep toward the viewer and the ambient field drifts at a few
#: pixels a second, which between them make a scene that barely appears to move. The
#: *fast layer* — barcode bursts, dashes and dots running along horizontal lanes — is
#: the one element with real pace, and it is what keeps the whole thing from reading
#: as a still image under a slow zoom.
#:
#: **The concentration lines** raking outward from the vanishing point are the
#: datastream's dash-in-a-slot wrapped around the centre — a pixel finds its angular
#: sector and its slot along the ray and consults one cell, so the whole field costs
#: about what one more depth plane would. They earn their place by selling the motion
#: the panels only imply: panels *grow*, but nothing about them streaks.
#:
#: **Resolution-aware fade.** Depth means far panels pack their rows tighter than a
#: pixel can resolve, and drawing them anyway turns the far field into crawling
#: noise. Each panel measures a pixel against its own row pitch — computed
#: analytically from the depth, since ``fwidth`` is undefined under the non-uniform
#: branching this scene is built from — and fades out where it can no longer be read.
#: That is also what bounds the cost of the far planes rather than the plane count.
#:
#: **The warm accent.** The reference punctuates its cyan with amber, and a shader
#: gets exactly one theme colour (``ink``). The accent is therefore the ink with red
#: and blue swapped: on the cyan this scene is written for that lands on amber
#: exactly, and on any other palette it stays a hue derived from the theme rather
#: than a colour imported from outside it.
HOLOGRAM_MSL = """
// --- tunables ---------------------------------------------------------------
constant int   LAYERS      = 12;    // depth planes; each a full grid of panels
constant float Z_FAR       = 3.0;   // spawn depth / closest approach. The divide
constant float Z_NEAR      = 0.45;  // blows up as Z_NEAR reaches 0
constant float RATE        = 0.015;  // fraction of the depth range crossed per second
constant float FADE_IN     = 0.30;  // fraction of the travel spent fading in
constant float FADE_OUT    = 0.18;  // ...and fading out as it sweeps past. Long,
                                    // because a plane at Z_NEAR is wider than the
                                    // window: a panel has to be gone before it
                                    // becomes the whole screen and pops out
constant float GRID        = 3.20;  // panel cells per unit of plane
constant float PANEL_KEEP  = 0.38;  // share of cells that host a panel at all
constant float PANEL_W_MIN = 0.40;  // panel size as a fraction of its cell
constant float PANEL_W_RNG = 0.50;
constant float PANEL_H_MIN = 0.22;
constant float PANEL_H_RNG = 0.42;

// What a panel *is*. Cumulative thresholds on one hash, read off in a comparison
// chain, so a panel draws one kind and only the winning branch costs anything.
constant float K_TEXT      = 0.660;  // typed pseudo-text (the commonest)
constant float K_BARS      = 0.725;  // bar chart
constant float K_LINE      = 0.765;  // line chart
constant float K_PROG      = 0.875;  // progress bars
constant float K_PIE       = 0.915;  // ring gauge -- the rest are wireframe

// Text panels
constant float ROWS        = 9.0;   // content rows per panel
constant float SEG_MIN     = 8.0;   // character slots per row
constant float SEG_RNG     = 16.0;
constant float ROW_FILL    = 0.60;  // share of slots carrying a mark
constant float BLOCK_H     = 0.32;  // mark height, as a fraction of the row
constant float BLOCK_MIN   = 0.15;  // mark width, as a fraction of its slot
constant float BLOCK_RNG   = 0.55;
constant float RULE_SHARE  = 0.20;  // share of rows drawn as a full-width hairline
constant float RULE_H      = 0.09;
constant float TYPE_RATE   = 0.16;  // type-hold-retype cycles per second
constant float TYPE_FRAC   = 0.34;  // fraction of that cycle spent typing
constant float CURSOR_LIFT = 0.60;  // extra brightness on the mark at the head

// Bar charts
constant float BAR_N_MIN   = 5.0;   // bars per panel
constant float BAR_N_RNG   = 9.0;
constant float BAR_W       = 0.42;  // bar width, as a fraction of its slot
constant float BAR_MIN     = 0.12;  // bar height range, as a fraction of the panel
constant float BAR_RNG     = 0.80;
constant float BAR_RATE    = 0.22;  // re-rolls per second

// Line charts
constant float LINE_PTS    = 8.0;   // vertices across the panel
constant float LINE_W      = 0.022;  // trace thickness, in panel-local units
constant float LINE_RATE   = 0.18;
constant float LINE_LO     = 0.12;  // the band the trace stays inside
constant float LINE_SPAN   = 0.76;
constant float LINE_FILL   = 0.10;  // brightness of the wash under the trace

// Progress bars
constant float PROG_ROWS   = 4.0;
constant float PROG_H      = 0.34;  // bar height, as a fraction of its row
constant float PROG_RATE   = 0.12;
constant float PROG_TRACK  = 0.32;  // brightness of the unfilled track
constant float PROG_LO     = 0.08;  // fill range, so a bar is never quite empty/full
constant float PROG_SPAN   = 0.86;

// Ring gauges
constant float PIE_R       = 0.24;  // radius, as a fraction of the panel's short side
constant float PIE_W       = 0.06;  // ring thickness, as a fraction of the radius
constant float PIE_RATE    = 0.09;
constant float PIE_TRACK   = 0.50;  // brightness of the unswept ring

// Wireframes
constant float WIRE_NX     = 6.0;   // mesh divisions
constant float WIRE_NY     = 4.0;
constant float WIRE_DIAG   = 0.50;  // share that also carry diagonals
constant float WIRE_ALPHA  = 0.50;

// Panel chrome and shading
constant float FRAME_SHARE = 0.45;  // share of panels carrying an outline
constant float FRAME_ALPHA = 0.55;
constant float WARM_SHARE  = 0.14;  // share of marks struck in the warm accent
constant float NEAR_GLOW   = 0.55;  // how far the nearest panels pale toward white
constant float DEPTH_DIM   = 0.52;  // brightness of the furthest plane vs the nearest.
                                    // Without this the field reads flat: every plane
                                    // draws at the same strength, so the eye gets the
                                    // *scale* cue and no aerial one, and a big near
                                    // panel looks like a big panel rather than a
                                    // close one
constant float RESOLVE     = 0.85;  // fade a panel out past this many pixels per row

// Concentration lines -- the radial speed streaks
constant float CONC_SECTORS = 220.0; // angular slots around the vanishing point
constant float CONC_COUNT   = 4.0;   // how many of them carry a streak. A pixel only
                                     // ever sees its own sector, so this cannot be a
                                     // hard cap -- it is the *expected* number, set by
                                     // keeping a COUNT/SECTORS share of the draws
constant float CONC_CELL    = 0.34;  // streak slot length, as a fraction of the radius
constant float CONC_DASH    = 0.55;  // dash length within its slot
constant float CONC_RATE    = 0.20;  // outward drift, fraction of the radius/second
constant float CONC_PX      = 2.6;   // streak width, pixels
constant float CONC_ALPHA   = 0.95;
constant float CONC_IN      = 0.16;  // radius (fraction) the streaks start at
constant float CONC_RAMP    = 0.26;  // ...and how far they take to reach full strength
constant float CONC_HEAD    = 0.60;  // how far a leading edge pales toward white

constant float LIFE_RATE   = 0.167; // panel appear-hold-vanish cycles per second.
                                    // Deliberately independent of RATE: see the note
                                    // in the loop on why the two had to come apart
constant float LIFE_IN     = 0.12;  // fraction of a life spent fading up
constant float LIFE_OUT    = 0.18;  // ...and fading out

// The ambient field: soft out-of-focus dots, rings and strokes drifting in *screen*
// space, with no part in the depth sweep. Everything else here flies at the viewer,
// which gives the scene one motion and one only; this layer drifts across it instead,
// so there is something in frame that is simply there rather than arriving.
constant float AMB_CELL_PX  = 170.0; // ambient cell size, pixels
constant float AMB_KEEP     = 0.55;  // share of cells carrying an object
constant float AMB_MAX_R    = 70.0;  // bound on an object's reach: the jitter below is
                                     // clamped so nothing leaves its own cell, which
                                     // is what keeps this to one lookup per pixel
constant float AMB_DRIFT_X  = 5.0;   // field drift, pixels/second
constant float AMB_DRIFT_Y  = -3.0;
constant float AMB_ORBIT    = 0.05;  // per-object orbit, turns/second
constant float AMB_ORBIT_R  = 9.0;   // ...and its radius, pixels
constant float AMB_K_DOT    = 0.60;  // kind mix: dot / stroke
constant float AMB_DOT_R    = 40.0;
constant float AMB_DOT_A    = 0.45;
constant float AMB_LINE_L   = 80.0;
constant float AMB_LINE_W   = 1.4;
constant float AMB_LINE_A   = 0.30;
constant float AMB_SOFT     = 7.0;   // edge softness, pixels -- these read as
                                     // out-of-focus, so the falloff is wide

// The fast layer: bright dashes and dots running along horizontal lanes, far quicker
// than anything else here. The ambient field drifts at a few pixels a second and the
// panels creep toward the viewer; this is the only element with real speed, and it is
// what stops the scene reading as a still image with a slow zoom.
constant float FAST_LANE_PX = 38.0;  // lane pitch, pixels
constant float FAST_KEEP    = 0.42;  // share of lanes carrying traffic
constant float FAST_CELL_PX = 150.0; // slot length along a lane, pixels
constant float FAST_FILL    = 0.55;  // share of slots carrying an object
constant float FAST_RATE    = 260.0; // lane speed, pixels/second
constant float FAST_DASH    = 0.16;  // dash length, as a fraction of its slot
constant float FAST_LINE_W  = 1.3;   // dash thickness, pixels
constant float FAST_DOT_R   = 2.6;   // dot radius, pixels
constant float FAST_TICK_H  = 15.0;  // upright tick height, pixels (before variance)
constant float FAST_TICK_W  = 1.6;   // ...and its width
constant float FAST_BURST   = 0.30;  // a tick object is a *burst* of bars, spanning
constant float FAST_TICK_N  = 8.0;   // this fraction of its slot, this many bars
constant float FAST_TICK_FILL = 0.70;// ...of which this share are actually drawn
constant float FAST_DOT_MIX = 0.30;  // kind mix, cumulative: dot / upright tick /
constant float FAST_TICK_MIX = 0.66; // horizontal dash
constant float FAST_REACH   = 17.0;  // the tallest a lane's contents can reach, for
                                     // the early-out. A tick varies up to 2x its
                                     // nominal height, so this is not FAST_TICK_H
constant float FAST_ALPHA   = 0.85;
constant float FAST_HEAD    = 0.70;  // how far a dash's leading edge pales to white
constant float FAST_WRAP    = 4096.0;

constant float CYCLE_WRAP   = 512.0; // keeps the hash inputs exact -- see the note on
constant float CONC_WRAP    = 4096.0;// folding time in DATASTREAM_MSL
constant float TAU          = 6.283185307;

static inline float3 hash33(float2 p) {
    float3 v = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return fract((v.xxy + v.yzz) * v.zyx);
}

// A value that re-rolls on a fixed beat and eases between draws, so charts move
// rather than jump. Returns the eased value; `gen` is the draw it is heading to.
static inline float stepped(float2 seed, float beat, float phase) {
    float ct = beat + phase;
    float gen = floor(ct);
    float a = hash33(seed + float2(gen * 53.0, 0.0)).x;
    float b = hash33(seed + float2((gen + 1.0) * 53.0, 0.0)).x;
    return mix(a, b, smoothstep(0.0, 1.0, fract(ct)));
}

// The ambient field: one soft object per screen-space cell, drifting as a whole and
// orbiting within its cell. The jitter is clamped so an object cannot leave the cell
// that owns it, which is what lets a pixel consult exactly one cell -- the same
// bounded-jitter trick the wave uses, and the reason this layer is nearly free.
//
// Nothing here takes part in the depth sweep. That is the point: every other element
// flies at the viewer, so the scene had exactly one kind of motion, and a layer that
// merely drifts across it reads as depth of field rather than as more traffic.
static inline float ambient_field(float2 p, float t) {
    float2 q = p + float2(t * AMB_DRIFT_X, t * AMB_DRIFT_Y);
    float2 cell = floor(q / AMB_CELL_PX);
    float2 f = q - cell * AMB_CELL_PX;
    float3 h = hash33(cell + 91.0);
    if (h.x > AMB_KEEP) { return 0.0; }

    float3 g = hash33(cell * 1.7 + 13.0);
    float span = AMB_CELL_PX - 2.0 * AMB_MAX_R;
    float2 c = float2(AMB_CELL_PX * 0.5) + (g.xy - 0.5) * span;
    float ang = t * AMB_ORBIT * TAU * (0.6 + 0.8 * g.z) + h.z * TAU;
    c += float2(cos(ang), sin(ang)) * AMB_ORBIT_R;

    float2 d2 = f - c;
    float d = length(d2);
    if (h.y < AMB_K_DOT) {
        // A squared falloff, not a smoothstep-bounded disc: an out-of-focus
        // highlight has no edge. (Cubed, the first try, collapses the visible core
        // to a point -- the dots read as dust rather than as lights.)
        float r = AMB_DOT_R * (0.5 + 0.9 * g.x);
        float k = max(0.0, 1.0 - d / r);
        return k * k * AMB_DOT_A;
    }
    float a2 = g.z * TAU;
    float2 dir = float2(cos(a2), sin(a2));
    float half_len = AMB_LINE_L * 0.5 * (0.5 + 0.9 * g.x);
    float along = clamp(dot(d2, dir), -half_len, half_len);
    return (1.0 - smoothstep(AMB_LINE_W, AMB_LINE_W + AMB_SOFT,
                             length(d2 - dir * along))) * AMB_LINE_A;
}

// Bright traffic running along horizontal lanes: short dashes with a hot leading
// edge, and dots riding the same slots. Folded like the datastream's lanes -- the
// fraction places the pixel in its slot, the integer only names it -- so a pixel
// consults exactly one cell however long the app has been running.
//
// Returns coverage in .x and how much of it is leading edge in .y.
static inline float2 fast_field(float2 pos, float t) {
    float lane = floor(pos.y / FAST_LANE_PX);
    float dy = abs(pos.y - (lane + 0.5) * FAST_LANE_PX);
    // Everything in a lane hugs its centre line, so most pixels leave immediately.
    if (dy > FAST_REACH) { return float2(0.0); }

    float3 lh = hash33(float2(lane, 71.0));
    if (lh.x > FAST_KEEP) { return float2(0.0); }

    float speed = FAST_RATE * (0.6 + 0.8 * lh.y);
    float shift = t * speed / FAST_CELL_PX;
    float shiftI = floor(shift);
    float uu = pos.x / FAST_CELL_PX + (shift - shiftI);
    float slot = floor(uu);
    float fx = uu - slot;
    float3 sh = hash33(float2(fmod(slot - shiftI, FAST_WRAP), lane));
    if (sh.x > FAST_FILL) { return float2(0.0); }

    if (sh.y < FAST_DOT_MIX) {
        float d = length(float2(fx * FAST_CELL_PX, dy));
        return float2((1.0 - smoothstep(FAST_DOT_R, FAST_DOT_R + 1.2, d))
                      * FAST_ALPHA, 0.0);
    }
    if (sh.y < FAST_TICK_MIX) {
        // A burst of upright bars -- the barcode the reference runs along its bands.
        // A single bar per slot (the first try) scatters into isolated tally marks;
        // it is the *cluster* that reads as a packet of data going past. Heights vary
        // widely on purpose too: a run of equal bars reads as a ruler.
        if (fx > FAST_BURST) { return float2(0.0); }
        float gx = fx / FAST_BURST * FAST_TICK_N;
        float bar = floor(gx);
        float gf = gx - bar;
        float3 th = hash33(float2(bar + slot * 17.0, lane + 5.0));
        if (th.x > FAST_TICK_FILL) { return float2(0.0); }
        float half_h = FAST_TICK_H * (0.35 + 1.1 * th.y);
        float pitch = FAST_BURST * FAST_CELL_PX / FAST_TICK_N;   // bar spacing, px
        float covX = 1.0 - smoothstep(FAST_TICK_W * 0.5, FAST_TICK_W * 0.5 + 1.0,
                                      gf * pitch);
        float covY = 1.0 - smoothstep(half_h, half_h + 1.0, dy);
        return float2(covX * covY * FAST_ALPHA, 0.0);
    }
    float dash = FAST_DASH * (0.4 + 1.2 * sh.z);
    float aa = 1.0 / FAST_CELL_PX;
    float covX = smoothstep(0.0, aa, fx) * (1.0 - smoothstep(dash - aa, dash, fx));
    float covY = 1.0 - smoothstep(FAST_LINE_W * 0.5, FAST_LINE_W * 0.5 + 1.0, dy);
    float a = covX * covY * FAST_ALPHA;
    return float2(a, a * (1.0 - smoothstep(0.0, dash * 0.35, fx)));
}

// One panel's contents, in panel-local coordinates (0..1 on each axis). Returns
// coverage in .x and how much of it is struck in the warm accent in .y.
//
// `pixCell` is one screen pixel expressed in *cell* units -- the panel's own axes
// are anisotropic (it is pw x panelH of a cell), so each branch converts as it needs
// to. Everything is antialiased against that rather than against fwidth: the caller
// reaches this under heavily non-uniform branching, where a derivative is undefined.
static inline float2 panel_content(float lx, float ly, float pixCell,
                                   float pw, float panelH, float2 salt,
                                   float kind, float kvar, float t) {
    float pixX = pixCell / pw;          // one pixel, in panel-local x
    float pixY = pixCell / panelH;      // ...and y
    float a = 0.0;
    float acc = 0.0;

    if (kind < K_TEXT) {
        // --- typed pseudo-text ------------------------------------------------
        float ry = ly * ROWS;
        float row = floor(ry);
        float fy = ry - row;
        float aaY = pixY * ROWS;
        float3 rh = hash33(salt + float2(row * 7.0, 3.0));
        if (rh.x < RULE_SHARE) {
            a = 1.0 - smoothstep(RULE_H * 0.5, RULE_H * 0.5 + aaY, abs(fy - 0.5));
        } else {
            float segs = floor(SEG_MIN + SEG_RNG * rh.y);
            float sx = lx * segs;
            float seg = floor(sx);
            float fx = sx - seg;
            // A row types out left to right, holds, then retypes with fresh content.
            // Re-rolling every slot at once (what this did before) is what made the
            // marks read as noise rather than as characters: text has a writing
            // *order*, and the order is most of what identifies it as text.
            float ct = t * TYPE_RATE + rh.z * 7.0;
            float gen = floor(ct);
            float head = clamp(fract(ct) / TYPE_FRAC, 0.0, 1.0) * segs;
            if (seg < head) {
                float3 sh = hash33(float2(seg + gen * 131.0, salt.y + row));
                if (sh.x < ROW_FILL) {
                    float bw = BLOCK_MIN + BLOCK_RNG * sh.y;
                    float covX = 1.0 - smoothstep(bw - pixX * segs, bw, fx);
                    float covY = 1.0 - smoothstep(BLOCK_H * 0.5,
                                                  BLOCK_H * 0.5 + aaY, abs(fy - 0.5));
                    a = covX * covY;
                    // The mark under the head burns brighter for a slot or so -- the
                    // caret, and the cue that reads as "this is being written now".
                    a *= 1.0 + CURSOR_LIFT * (1.0 - smoothstep(0.0, 1.5, head - seg));
                    acc = (sh.z > 1.0 - WARM_SHARE) ? a : 0.0;
                }
            }
        }
    } else if (kind < K_BARS) {
        // --- bar chart --------------------------------------------------------
        float bars = floor(BAR_N_MIN + BAR_N_RNG * kvar);
        float bx = lx * bars;
        float bar = floor(bx);
        float fx = bx - bar;
        float h = BAR_MIN + BAR_RNG * stepped(salt + float2(bar, 0.0),
                                              t * BAR_RATE, kvar * 5.0);
        float covX = 1.0 - smoothstep(BAR_W - pixX * bars, BAR_W, fx);
        // ly runs downward, so a bar standing on the floor is (1 - ly) < h.
        float covY = 1.0 - smoothstep(h - pixY, h, 1.0 - ly);
        a = covX * covY;
        a = max(a, 1.0 - smoothstep(pixY * 0.5, pixY * 1.5, 1.0 - ly));   // baseline
    } else if (kind < K_LINE) {
        // --- line chart -------------------------------------------------------
        float px = lx * LINE_PTS;
        float ip = floor(px);
        float fp = px - ip;
        float y0 = LINE_LO + LINE_SPAN * stepped(salt + float2(ip, 0.0),
                                                 t * LINE_RATE, kvar * 3.0);
        float y1 = LINE_LO + LINE_SPAN * stepped(salt + float2(ip + 1.0, 0.0),
                                                 t * LINE_RATE, kvar * 3.0);
        float yl = mix(y0, y1, fp);
        // Perpendicular distance, not vertical: without the slope correction a steep
        // leg of the trace draws several times thicker than a flat one.
        float slope = (y1 - y0) * LINE_PTS;
        float d = abs(ly - yl) / sqrt(1.0 + slope * slope);
        a = 1.0 - smoothstep(LINE_W * 0.5, LINE_W * 0.5 + pixY, d);
        a = max(a, (ly > yl) ? LINE_FILL : 0.0);      // the wash under the trace
    } else if (kind < K_PROG) {
        // --- progress bars ----------------------------------------------------
        float ry = ly * PROG_ROWS;
        float row = floor(ry);
        float fy = ry - row;
        float aaY = pixY * PROG_ROWS;
        float3 rh = hash33(salt + float2(row * 11.0, 17.0));
        float band = 1.0 - smoothstep(PROG_H * 0.5, PROG_H * 0.5 + aaY, abs(fy - 0.5));
        float p = PROG_LO + PROG_SPAN * stepped(salt + float2(row * 3.0, 9.0),
                                                t * PROG_RATE, rh.z * 4.0);
        float fill = band * (1.0 - smoothstep(p - pixX, p, lx));
        a = max(band * PROG_TRACK, fill);
        acc = (rh.y > 1.0 - WARM_SHARE) ? fill : 0.0;
    } else if (kind < K_PIE) {
        // --- ring gauge -------------------------------------------------------
        // Back into cell units, where the axes are isotropic again -- drawn in
        // panel-local units a circle would come out as an ellipse.
        float2 q = float2((lx - 0.5) * pw, (ly - 0.5) * panelH);
        float R = PIE_R * min(pw, panelH);
        float r = length(q);
        float ring = 1.0 - smoothstep(R * PIE_W, R * PIE_W + pixCell, abs(r - R));
        float band = 1.0 - smoothstep(R * PIE_W * 2.4, R * PIE_W * 2.4 + pixCell,
                                      abs(r - R));
        float sweep = stepped(salt + float2(31.0, 0.0), t * PIE_RATE, kvar * 6.0);
        float ang = atan2(q.y, q.x) / TAU + 0.5;
        float arc = (ang < sweep) ? band : 0.0;
        a = max(ring * PIE_TRACK, arc);
        acc = arc;
    } else {
        // --- wireframe --------------------------------------------------------
        float u = lx * WIRE_NX;
        float v = ly * WIRE_NY;
        float wu = pixX * WIRE_NX;
        float wv = pixY * WIRE_NY;
        a = max(1.0 - smoothstep(0.5 * wu, 1.5 * wu, abs(u - round(u))),
                1.0 - smoothstep(0.5 * wv, 1.5 * wv, abs(v - round(v))));
        if (kvar < WIRE_DIAG) {
            float d = u + v;
            float wd = wu + wv;
            a = max(a, 1.0 - smoothstep(0.5 * wd, 1.5 * wd, abs(d - round(d))));
        }
        a *= WIRE_ALPHA;
    }
    return float2(a, acc);
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    float2 halfRes = u.resolution * 0.5;
    // View-height units in both axes, so a panel stays square whatever the window
    // aspect. (The starfield normalises per-axis instead and lets its field stretch;
    // a stretching *drawing* would read as a mistake where a stretching dot does not.)
    float2 P = pos.xy - halfRes;
    float2 n = P / halfRes.y;
    float t = u.time;

    float lit = 0.0;    // coverage at this pixel
    float warm = 0.0;   // the share of it struck in the accent, for the hue
    float hot = 0.0;    // nearness of whatever covered it, for the white lift

    for (int i = 0; i < LAYERS; ++i) {
        // Planes evenly offset in phase, so the field always holds panels at every
        // stage of the approach rather than pulsing in unison.
        float raw = t * RATE + float(i) / float(LAYERS);
        float travel = fract(raw);
        float cycle = fmod(floor(raw), CYCLE_WRAP);   // re-rolls a plane's content
        // Even steps in 1/z are even steps *on screen* (the same reason the wave
        // stacks its slabs this way). Stepping z linearly instead spends almost every
        // plane in the far half, where 1/z barely moves -- which is why the field
        // came out as one size of panel repeated rather than a depth of them. This
        // spreads the planes evenly across apparent scale, so a big near panel, a
        // mid one and the far haze are all on screen at once.
        float z = 1.0 / mix(1.0 / Z_FAR, 1.0 / Z_NEAR, travel);
        float alpha = min(1.0, travel / FADE_IN)
                    * (1.0 - smoothstep(1.0 - FADE_OUT, 1.0, travel));
        if (alpha <= 0.002) { continue; }

        // Run the projection backwards: at this depth the ray crosses the plane
        // here, so this is the only cell that can cover this pixel.
        float2 s = n * z;
        float2 cell = floor(s * GRID);
        float2 f = s * GRID - cell;

        // Each panel lives and dies on its own clock, much shorter than its plane's
        // traversal: it fades up, holds, fades out, and the cell is redrawn with a
        // fresh one. Decoupling the two is the whole point -- the plane's sweep used
        // to serve as the panel lifetime as well, so slowing the flight would have
        // made every panel linger proportionally longer. Now the flight can be slow
        // and the field still turns over quickly.
        float3 lh = hash33(cell * 0.61 + float2(float(i) * 3.0, 7.0));
        float lifeT = t * LIFE_RATE + lh.x * 11.0;
        float lifeGen = fmod(floor(lifeT), CYCLE_WRAP);
        float lifePh = fract(lifeT);
        float life = smoothstep(0.0, LIFE_IN, lifePh)
                   * (1.0 - smoothstep(1.0 - LIFE_OUT, 1.0, lifePh));
        if (life <= 0.002) { continue; }

        // ``lifeGen`` rides in every panel hash below, so a cell that comes back
        // comes back as a different panel rather than as the same one blinking.
        float3 ph = hash33(cell + float2(cycle * 13.0 + float(i) * 57.0 + lifeGen * 29.0,
                                         cycle * 7.0 - float(i) * 23.0 + lifeGen * 41.0));
        if (ph.x > PANEL_KEEP) { continue; }     // this cell is empty space

        float3 qh = hash33(cell * 1.37 + float2(float(i) * 11.0,
                                                cycle * 3.0 + lifeGen * 17.0));
        float pw = PANEL_W_MIN + PANEL_W_RNG * ph.y;
        float panelH = PANEL_H_MIN + PANEL_H_RNG * ph.z;
        float lx = (f.x - (1.0 - pw) * qh.x) / pw;   // panel-local, 0..1
        float ly = (f.y - (1.0 - panelH) * qh.y) / panelH;
        if (lx < 0.0 || lx > 1.0 || ly < 0.0 || ly > 1.0) { continue; }

        // One pixel, in cell units. Derived from the depth rather than from fwidth:
        // the branching above is non-uniform, which makes a derivative undefined,
        // and every antialiasing width downstream depends on this.
        float pixCell = z * GRID / halfRes.y;
        // Past the point where a pixel spans a good part of a row, the panel cannot
        // be read at all; fading it out is what keeps the far field from boiling.
        float resolve = 1.0 - smoothstep(RESOLVE * 0.5, RESOLVE,
                                         (pixCell / panelH) * ROWS);
        if (resolve <= 0.0) { continue; }

        // ``travel``, not z: with the 1/z stepping above it is travel that is linear
        // in apparent scale, so it is the measure that makes the aerial cue agree
        // with the size cue.
        float depth = 1.0 - travel;                         // 0 near, 1 far
        float bright = (0.3 + 0.7 * ph.y) * alpha * life * resolve
                     * mix(1.0, DEPTH_DIM, depth);

        float2 r = panel_content(lx, ly, pixCell, pw, panelH,
                                 float2(cell.x * 13.0 + float(i),
                                        cell.y * 29.0 + cycle + lifeGen * 7.0),
                                 qh.z, fract(qh.y * 11.7), t);
        float a = r.x;

        // A hairline outline on some panels, which is most of what makes a cluster
        // of marks read as a *panel* rather than as loose debris.
        if (fract(qh.x * 7.3) < FRAME_SHARE) {
            float edge = min(min(lx, 1.0 - lx) * pw,
                             min(ly, 1.0 - ly) * panelH) / pixCell;
            a = max(a, (1.0 - smoothstep(0.6, 1.6, edge)) * FRAME_ALPHA);
        }

        a *= bright;
        lit = max(lit, a);
        warm = max(warm, r.y * bright);
        hot = max(hot, a * (1.0 - z / Z_FAR));
    }

    // --- concentration lines --------------------------------------------------
    // Radial speed streaks raking outward from the vanishing point. This is the
    // datastream's dash-in-a-slot wrapped around the centre: a pixel finds its
    // angular sector and its slot along the ray and consults exactly one cell, so a
    // whole field of them costs about what one more panel plane would. They sell the
    // forward motion the panels only imply -- the panels grow, but nothing *streaks*.
    float rad = length(P);
    float rn = rad / length(halfRes);          // 0 at the centre, 1 at the corner
    if (rn > CONC_IN && rad > 1.0) {
        float ang = atan2(P.y, P.x) / TAU + 0.5;
        // Wrapped, or the slot at ang = 1 would be a different draw from the one at
        // ang = 0 and the field would carry a seam straight out along -x.
        float sector = fmod(floor(ang * CONC_SECTORS), CONC_SECTORS);
        float3 ch = hash33(float2(sector, 4.0));
        if (ch.x * CONC_SECTORS < CONC_COUNT) {
            // Folded like the datastream's lanes: the fraction places the pixel in
            // its slot, the integer only names it.
            float shift = t * CONC_RATE * (0.5 + 1.2 * ch.y) / CONC_CELL;
            float shiftI = floor(shift);
            float uu = rn / CONC_CELL - (shift - shiftI);
            float slot = floor(uu);
            float fu = uu - slot;
            float3 dh = hash33(float2(fmod(slot - shiftI, CONC_WRAP), sector));
            if (dh.x < 0.75) {
                float dash = CONC_DASH * (0.35 + 0.9 * dh.y);
                // Constant width in pixels, so the angular half-width has to shrink
                // as the radius grows -- otherwise a streak fans out into a wedge.
                float dPx = abs(fract(ang * CONC_SECTORS) - 0.5) / CONC_SECTORS * TAU * rad;
                float covA = 1.0 - smoothstep(CONC_PX * 0.5, CONC_PX * 0.5 + 1.0, dPx);
                float covR = smoothstep(0.0, 0.02, fu)
                           * (1.0 - smoothstep(dash - 0.02, dash, fu));
                float fade = smoothstep(CONC_IN, CONC_IN + CONC_RAMP, rn);
                float a = covA * covR * fade * CONC_ALPHA * (0.5 + 0.5 * dh.z);
                lit = max(lit, a);
                hot = max(hot, a * (1.0 - smoothstep(0.0, 0.3, fu)) * CONC_HEAD);
            }
        }
    }

    // The ambient layer sits under the rest: dim, soft and cool, never warm or hot.
    lit = max(lit, ambient_field(pos.xy, t));

    // The fast layer, on top: this is the element that actually moves.
    float2 fastR = fast_field(pos.xy, t);
    lit = max(lit, fastR.x);
    hot = max(hot, fastR.y * FAST_HEAD);

    // The accent is the ink with red and blue swapped -- amber out of this scene's
    // cyan, and a theme-derived hue out of anything else (see the module note).
    float3 rgb = mix(u.ink.rgb, u.ink.zyx, clamp(warm / max(lit, 1e-4), 0.0, 1.0));
    rgb = mix(rgb, float3(1.0), clamp(hot, 0.0, 1.0) * NEAR_GLOW);

    rgb = mix(u.backdrop.rgb, rgb, clamp(lit, 0.0, 1.0) * u.opacity);
    return float4(rgb, 1.0);
}
"""

#: The HLSL translation of :data:`HOLOGRAM_MSL` (see :data:`WAVE_HLSL` for why a scene
#: ships both). Line-for-line; only the dialect differs. Keep the two in sync.
HOLOGRAM_HLSL = """
// --- tunables (see HOLOGRAM_MSL for the rationale of each) -------------------
static const int   LAYERS      = 12;    // depth planes; each a full grid of panels
static const float Z_FAR       = 3.0;   // spawn depth / closest approach. The divide
static const float Z_NEAR      = 0.45;  // blows up as Z_NEAR reaches 0
static const float RATE        = 0.015;  // fraction of the depth range crossed per second
static const float FADE_IN     = 0.30;  // fraction of the travel spent fading in
static const float FADE_OUT    = 0.18;  // ...and fading out as it sweeps past. Long,
                                    // because a plane at Z_NEAR is wider than the
                                    // window: a panel has to be gone before it
                                    // becomes the whole screen and pops out
static const float GRID        = 3.20;  // panel cells per unit of plane
static const float PANEL_KEEP  = 0.38;  // share of cells that host a panel at all
static const float PANEL_W_MIN = 0.40;  // panel size as a fraction of its cell
static const float PANEL_W_RNG = 0.50;
static const float PANEL_H_MIN = 0.22;
static const float PANEL_H_RNG = 0.42;

// What a panel *is*. Cumulative thresholds on one hash, read off in a comparison
// chain, so a panel draws one kind and only the winning branch costs anything.
static const float K_TEXT      = 0.660;  // typed pseudo-text (the commonest)
static const float K_BARS      = 0.725;  // bar chart
static const float K_LINE      = 0.765;  // line chart
static const float K_PROG      = 0.875;  // progress bars
static const float K_PIE       = 0.915;  // ring gauge -- the rest are wireframe

// Text panels
static const float ROWS        = 9.0;   // content rows per panel
static const float SEG_MIN     = 8.0;   // character slots per row
static const float SEG_RNG     = 16.0;
static const float ROW_FILL    = 0.60;  // share of slots carrying a mark
static const float BLOCK_H     = 0.32;  // mark height, as a fraction of the row
static const float BLOCK_MIN   = 0.15;  // mark width, as a fraction of its slot
static const float BLOCK_RNG   = 0.55;
static const float RULE_SHARE  = 0.20;  // share of rows drawn as a full-width hairline
static const float RULE_H      = 0.09;
static const float TYPE_RATE   = 0.16;  // type-hold-retype cycles per second
static const float TYPE_FRAC   = 0.34;  // fraction of that cycle spent typing
static const float CURSOR_LIFT = 0.60;  // extra brightness on the mark at the head

// Bar charts
static const float BAR_N_MIN   = 5.0;   // bars per panel
static const float BAR_N_RNG   = 9.0;
static const float BAR_W       = 0.42;  // bar width, as a fraction of its slot
static const float BAR_MIN     = 0.12;  // bar height range, as a fraction of the panel
static const float BAR_RNG     = 0.80;
static const float BAR_RATE    = 0.22;  // re-rolls per second

// Line charts
static const float LINE_PTS    = 8.0;   // vertices across the panel
static const float LINE_W      = 0.022;  // trace thickness, in panel-local units
static const float LINE_RATE   = 0.18;
static const float LINE_LO     = 0.12;  // the band the trace stays inside
static const float LINE_SPAN   = 0.76;
static const float LINE_FILL   = 0.10;  // brightness of the wash under the trace

// Progress bars
static const float PROG_ROWS   = 4.0;
static const float PROG_H      = 0.34;  // bar height, as a fraction of its row
static const float PROG_RATE   = 0.12;
static const float PROG_TRACK  = 0.32;  // brightness of the unfilled track
static const float PROG_LO     = 0.08;  // fill range, so a bar is never quite empty/full
static const float PROG_SPAN   = 0.86;

// Ring gauges
static const float PIE_R       = 0.24;  // radius, as a fraction of the panel's short side
static const float PIE_W       = 0.06;  // ring thickness, as a fraction of the radius
static const float PIE_RATE    = 0.09;
static const float PIE_TRACK   = 0.50;  // brightness of the unswept ring

// Wireframes
static const float WIRE_NX     = 6.0;   // mesh divisions
static const float WIRE_NY     = 4.0;
static const float WIRE_DIAG   = 0.50;  // share that also carry diagonals
static const float WIRE_ALPHA  = 0.50;

// Panel chrome and shading
static const float FRAME_SHARE = 0.45;  // share of panels carrying an outline
static const float FRAME_ALPHA = 0.55;
static const float WARM_SHARE  = 0.14;  // share of marks struck in the warm accent
static const float NEAR_GLOW   = 0.55;  // how far the nearest panels pale toward white
static const float DEPTH_DIM   = 0.52;  // brightness of the furthest plane vs the nearest.
                                    // Without this the field reads flat: every plane
                                    // draws at the same strength, so the eye gets the
                                    // *scale* cue and no aerial one, and a big near
                                    // panel looks like a big panel rather than a
                                    // close one
static const float RESOLVE     = 0.85;  // fade a panel out past this many pixels per row

// Concentration lines -- the radial speed streaks
static const float CONC_SECTORS = 220.0; // angular slots around the vanishing point
static const float CONC_COUNT   = 4.0;   // how many of them carry a streak. A pixel only
                                     // ever sees its own sector, so this cannot be a
                                     // hard cap -- it is the *expected* number, set by
                                     // keeping a COUNT/SECTORS share of the draws
static const float CONC_CELL    = 0.34;  // streak slot length, as a fraction of the radius
static const float CONC_DASH    = 0.55;  // dash length within its slot
static const float CONC_RATE    = 0.20;  // outward drift, fraction of the radius/second
static const float CONC_PX      = 2.6;   // streak width, pixels
static const float CONC_ALPHA   = 0.95;
static const float CONC_IN      = 0.16;  // radius (fraction) the streaks start at
static const float CONC_RAMP    = 0.26;  // ...and how far they take to reach full strength
static const float CONC_HEAD    = 0.60;  // how far a leading edge pales toward white

static const float LIFE_RATE   = 0.167; // panel appear-hold-vanish cycles per second.
                                    // (see HOLOGRAM_MSL for the rationale)
static const float LIFE_IN     = 0.12;  // fraction of a life spent fading up
static const float LIFE_OUT    = 0.18;  // ...and fading out

// The ambient field -- see the MSL twin.
static const float AMB_CELL_PX  = 170.0; // ambient cell size, pixels
static const float AMB_KEEP     = 0.55;  // share of cells carrying an object
static const float AMB_MAX_R    = 70.0;  // bound on an object's reach: the jitter below is
static const float AMB_DRIFT_X  = 5.0;   // field drift, pixels/second
static const float AMB_DRIFT_Y  = -3.0;
static const float AMB_ORBIT    = 0.05;  // per-object orbit, turns/second
static const float AMB_ORBIT_R  = 9.0;   // ...and its radius, pixels
static const float AMB_K_DOT    = 0.60;  // kind mix: dot / stroke
static const float AMB_DOT_R    = 40.0;
static const float AMB_DOT_A    = 0.45;
static const float AMB_LINE_L   = 80.0;
static const float AMB_LINE_W   = 1.4;
static const float AMB_LINE_A   = 0.30;
static const float AMB_SOFT     = 7.0;   // edge softness, pixels -- these read as

// The fast layer -- see the MSL twin.
static const float FAST_LANE_PX = 38.0;  // lane pitch, pixels
static const float FAST_KEEP    = 0.42;  // share of lanes carrying traffic
static const float FAST_CELL_PX = 150.0; // slot length along a lane, pixels
static const float FAST_FILL    = 0.55;  // share of slots carrying an object
static const float FAST_RATE    = 260.0; // lane speed, pixels/second
static const float FAST_DASH    = 0.16;  // dash length, as a fraction of its slot
static const float FAST_LINE_W  = 1.3;   // dash thickness, pixels
static const float FAST_DOT_R   = 2.6;   // dot radius, pixels
static const float FAST_TICK_H  = 15.0;  // upright tick height, pixels (before variance)
static const float FAST_TICK_W  = 1.6;   // ...and its width
static const float FAST_BURST   = 0.30;  // a tick object is a *burst* of bars, spanning
static const float FAST_TICK_N  = 8.0;   // this fraction of its slot, this many bars
static const float FAST_TICK_FILL = 0.70;// ...of which this share are actually drawn
static const float FAST_DOT_MIX = 0.30;  // kind mix, cumulative: dot / upright tick /
static const float FAST_TICK_MIX = 0.66; // horizontal dash
static const float FAST_REACH   = 17.0;  // the tallest a lane's contents can reach, for
                                     // the early-out. A tick varies up to 2x its
                                     // nominal height, so this is not FAST_TICK_H
static const float FAST_ALPHA   = 0.85;
static const float FAST_HEAD    = 0.70;  // how far a dash's leading edge pales to white
static const float FAST_WRAP    = 4096.0;

static const float CYCLE_WRAP   = 512.0; // keeps the hash inputs exact -- see the note on
static const float CONC_WRAP    = 4096.0;// folding time in DATASTREAM_MSL
static const float TAU          = 6.283185307;

float3 hash33(float2 p) {
    float3 v = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
    v += dot(v, v.yzx + 33.33);
    return frac((v.xxy + v.yzz) * v.zyx);
}

// A value that re-rolls on a fixed beat and eases between draws, so charts move
// rather than jump. Returns the eased value; `gen` is the draw it is heading to.
float stepped(float2 seed, float beat, float phase) {
    float ct = beat + phase;
    float gen = floor(ct);
    float a = hash33(seed + float2(gen * 53.0, 0.0)).x;
    float b = hash33(seed + float2((gen + 1.0) * 53.0, 0.0)).x;
    return lerp(a, b, smoothstep(0.0, 1.0, frac(ct)));
}

// The ambient field: one soft object per screen-space cell, drifting as a whole and
// orbiting within its cell. The jitter is clamped so an object cannot leave the cell
// that owns it, which is what lets a pixel consult exactly one cell -- the same
// bounded-jitter trick the wave uses, and the reason this layer is nearly free.
//
// Nothing here takes part in the depth sweep. That is the point: every other element
// flies at the viewer, so the scene had exactly one kind of motion, and a layer that
// merely drifts across it reads as depth of field rather than as more traffic.
float ambient_field(float2 p, float t) {
    float2 q = p + float2(t * AMB_DRIFT_X, t * AMB_DRIFT_Y);
    float2 cell = floor(q / AMB_CELL_PX);
    float2 f = q - cell * AMB_CELL_PX;
    float3 h = hash33(cell + 91.0);
    if (h.x > AMB_KEEP) { return 0.0; }

    float3 g = hash33(cell * 1.7 + 13.0);
    float span = AMB_CELL_PX - 2.0 * AMB_MAX_R;
    float2 c = float2(AMB_CELL_PX * 0.5) + (g.xy - 0.5) * span;
    float ang = t * AMB_ORBIT * TAU * (0.6 + 0.8 * g.z) + h.z * TAU;
    c += float2(cos(ang), sin(ang)) * AMB_ORBIT_R;

    float2 d2 = f - c;
    float d = length(d2);
    if (h.y < AMB_K_DOT) {
        // A squared falloff, not a smoothstep-bounded disc: an out-of-focus
        // highlight has no edge. (Cubed, the first try, collapses the visible core
        // to a point -- the dots read as dust rather than as lights.)
        float r = AMB_DOT_R * (0.5 + 0.9 * g.x);
        float k = max(0.0, 1.0 - d / r);
        return k * k * AMB_DOT_A;
    }
    float a2 = g.z * TAU;
    float2 dir = float2(cos(a2), sin(a2));
    float half_len = AMB_LINE_L * 0.5 * (0.5 + 0.9 * g.x);
    float along = clamp(dot(d2, dir), -half_len, half_len);
    return (1.0 - smoothstep(AMB_LINE_W, AMB_LINE_W + AMB_SOFT,
                             length(d2 - dir * along))) * AMB_LINE_A;
}

// Bright traffic running along horizontal lanes: short dashes with a hot leading
// edge, and dots riding the same slots. Folded like the datastream's lanes -- the
// fraction places the pixel in its slot, the integer only names it -- so a pixel
// consults exactly one cell however long the app has been running.
//
// Returns coverage in .x and how much of it is leading edge in .y.
static inline float2 fast_field(float2 pos, float t) {
    float lane = floor(pos.y / FAST_LANE_PX);
    float dy = abs(pos.y - (lane + 0.5) * FAST_LANE_PX);
    // Everything in a lane hugs its centre line, so most pixels leave immediately.
    if (dy > FAST_REACH) { return float2(0.0, 0.0); }

    float3 lh = hash33(float2(lane, 71.0));
    if (lh.x > FAST_KEEP) { return float2(0.0, 0.0); }

    float speed = FAST_RATE * (0.6 + 0.8 * lh.y);
    float shift = t * speed / FAST_CELL_PX;
    float shiftI = floor(shift);
    float uu = pos.x / FAST_CELL_PX + (shift - shiftI);
    float slot = floor(uu);
    float fx = uu - slot;
    float3 sh = hash33(float2(fmod(slot - shiftI, FAST_WRAP), lane));
    if (sh.x > FAST_FILL) { return float2(0.0, 0.0); }

    if (sh.y < FAST_DOT_MIX) {
        float d = length(float2(fx * FAST_CELL_PX, dy));
        return float2((1.0 - smoothstep(FAST_DOT_R, FAST_DOT_R + 1.2, d))
                      * FAST_ALPHA, 0.0);
    }
    if (sh.y < FAST_TICK_MIX) {
        // A burst of upright bars -- the barcode the reference runs along its bands.
        // A single bar per slot (the first try) scatters into isolated tally marks;
        // it is the *cluster* that reads as a packet of data going past. Heights vary
        // widely on purpose too: a run of equal bars reads as a ruler.
        if (fx > FAST_BURST) { return float2(0.0, 0.0); }
        float gx = fx / FAST_BURST * FAST_TICK_N;
        float bar = floor(gx);
        float gf = gx - bar;
        float3 th = hash33(float2(bar + slot * 17.0, lane + 5.0));
        if (th.x > FAST_TICK_FILL) { return float2(0.0, 0.0); }
        float half_h = FAST_TICK_H * (0.35 + 1.1 * th.y);
        float pitch = FAST_BURST * FAST_CELL_PX / FAST_TICK_N;   // bar spacing, px
        float covX = 1.0 - smoothstep(FAST_TICK_W * 0.5, FAST_TICK_W * 0.5 + 1.0,
                                      gf * pitch);
        float covY = 1.0 - smoothstep(half_h, half_h + 1.0, dy);
        return float2(covX * covY * FAST_ALPHA, 0.0);
    }
    float dash = FAST_DASH * (0.4 + 1.2 * sh.z);
    float aa = 1.0 / FAST_CELL_PX;
    float covX = smoothstep(0.0, aa, fx) * (1.0 - smoothstep(dash - aa, dash, fx));
    float covY = 1.0 - smoothstep(FAST_LINE_W * 0.5, FAST_LINE_W * 0.5 + 1.0, dy);
    float a = covX * covY * FAST_ALPHA;
    return float2(a, a * (1.0 - smoothstep(0.0, dash * 0.35, fx)));
}

// One panel's contents, in panel-local coordinates (0..1 on each axis). Returns
// coverage in .x and how much of it is struck in the warm accent in .y.
//
// `pixCell` is one screen pixel expressed in *cell* units -- the panel's own axes
// are anisotropic (it is pw x panelH of a cell), so each branch converts as it needs
// to. Everything is antialiased against that rather than against fwidth: the caller
// reaches this under heavily non-uniform branching, where a derivative is undefined.
float2 panel_content(float lx, float ly, float pixCell,
                                   float pw, float panelH, float2 salt,
                                   float kind, float kvar, float t) {
    float pixX = pixCell / pw;          // one pixel, in panel-local x
    float pixY = pixCell / panelH;      // ...and y
    float a = 0.0;
    float acc = 0.0;

    if (kind < K_TEXT) {
        // --- typed pseudo-text ------------------------------------------------
        float ry = ly * ROWS;
        float row = floor(ry);
        float fy = ry - row;
        float aaY = pixY * ROWS;
        float3 rh = hash33(salt + float2(row * 7.0, 3.0));
        if (rh.x < RULE_SHARE) {
            a = 1.0 - smoothstep(RULE_H * 0.5, RULE_H * 0.5 + aaY, abs(fy - 0.5));
        } else {
            float segs = floor(SEG_MIN + SEG_RNG * rh.y);
            float sx = lx * segs;
            float seg = floor(sx);
            float fx = sx - seg;
            // A row types out left to right, holds, then retypes with fresh content.
            // Re-rolling every slot at once (what this did before) is what made the
            // marks read as noise rather than as characters: text has a writing
            // *order*, and the order is most of what identifies it as text.
            float ct = t * TYPE_RATE + rh.z * 7.0;
            float gen = floor(ct);
            float head = clamp(frac(ct) / TYPE_FRAC, 0.0, 1.0) * segs;
            if (seg < head) {
                float3 sh = hash33(float2(seg + gen * 131.0, salt.y + row));
                if (sh.x < ROW_FILL) {
                    float bw = BLOCK_MIN + BLOCK_RNG * sh.y;
                    float covX = 1.0 - smoothstep(bw - pixX * segs, bw, fx);
                    float covY = 1.0 - smoothstep(BLOCK_H * 0.5,
                                                  BLOCK_H * 0.5 + aaY, abs(fy - 0.5));
                    a = covX * covY;
                    // The mark under the head burns brighter for a slot or so -- the
                    // caret, and the cue that reads as "this is being written now".
                    a *= 1.0 + CURSOR_LIFT * (1.0 - smoothstep(0.0, 1.5, head - seg));
                    acc = (sh.z > 1.0 - WARM_SHARE) ? a : 0.0;
                }
            }
        }
    } else if (kind < K_BARS) {
        // --- bar chart --------------------------------------------------------
        float bars = floor(BAR_N_MIN + BAR_N_RNG * kvar);
        float bx = lx * bars;
        float bar = floor(bx);
        float fx = bx - bar;
        float h = BAR_MIN + BAR_RNG * stepped(salt + float2(bar, 0.0),
                                              t * BAR_RATE, kvar * 5.0);
        float covX = 1.0 - smoothstep(BAR_W - pixX * bars, BAR_W, fx);
        // ly runs downward, so a bar standing on the floor is (1 - ly) < h.
        float covY = 1.0 - smoothstep(h - pixY, h, 1.0 - ly);
        a = covX * covY;
        a = max(a, 1.0 - smoothstep(pixY * 0.5, pixY * 1.5, 1.0 - ly));   // baseline
    } else if (kind < K_LINE) {
        // --- line chart -------------------------------------------------------
        float px = lx * LINE_PTS;
        float ip = floor(px);
        float fp = px - ip;
        float y0 = LINE_LO + LINE_SPAN * stepped(salt + float2(ip, 0.0),
                                                 t * LINE_RATE, kvar * 3.0);
        float y1 = LINE_LO + LINE_SPAN * stepped(salt + float2(ip + 1.0, 0.0),
                                                 t * LINE_RATE, kvar * 3.0);
        float yl = lerp(y0, y1, fp);
        // Perpendicular distance, not vertical: without the slope correction a steep
        // leg of the trace draws several times thicker than a flat one.
        float slope = (y1 - y0) * LINE_PTS;
        float d = abs(ly - yl) / sqrt(1.0 + slope * slope);
        a = 1.0 - smoothstep(LINE_W * 0.5, LINE_W * 0.5 + pixY, d);
        a = max(a, (ly > yl) ? LINE_FILL : 0.0);      // the wash under the trace
    } else if (kind < K_PROG) {
        // --- progress bars ----------------------------------------------------
        float ry = ly * PROG_ROWS;
        float row = floor(ry);
        float fy = ry - row;
        float aaY = pixY * PROG_ROWS;
        float3 rh = hash33(salt + float2(row * 11.0, 17.0));
        float band = 1.0 - smoothstep(PROG_H * 0.5, PROG_H * 0.5 + aaY, abs(fy - 0.5));
        float p = PROG_LO + PROG_SPAN * stepped(salt + float2(row * 3.0, 9.0),
                                                t * PROG_RATE, rh.z * 4.0);
        float fill = band * (1.0 - smoothstep(p - pixX, p, lx));
        a = max(band * PROG_TRACK, fill);
        acc = (rh.y > 1.0 - WARM_SHARE) ? fill : 0.0;
    } else if (kind < K_PIE) {
        // --- ring gauge -------------------------------------------------------
        // Back into cell units, where the axes are isotropic again -- drawn in
        // panel-local units a circle would come out as an ellipse.
        float2 q = float2((lx - 0.5) * pw, (ly - 0.5) * panelH);
        float R = PIE_R * min(pw, panelH);
        float r = length(q);
        float ring = 1.0 - smoothstep(R * PIE_W, R * PIE_W + pixCell, abs(r - R));
        float band = 1.0 - smoothstep(R * PIE_W * 2.4, R * PIE_W * 2.4 + pixCell,
                                      abs(r - R));
        float sweep = stepped(salt + float2(31.0, 0.0), t * PIE_RATE, kvar * 6.0);
        float ang = atan2(q.y, q.x) / TAU + 0.5;
        float arc = (ang < sweep) ? band : 0.0;
        a = max(ring * PIE_TRACK, arc);
        acc = arc;
    } else {
        // --- wireframe --------------------------------------------------------
        float u = lx * WIRE_NX;
        float v = ly * WIRE_NY;
        float wu = pixX * WIRE_NX;
        float wv = pixY * WIRE_NY;
        a = max(1.0 - smoothstep(0.5 * wu, 1.5 * wu, abs(u - round(u))),
                1.0 - smoothstep(0.5 * wv, 1.5 * wv, abs(v - round(v))));
        if (kvar < WIRE_DIAG) {
            float d = u + v;
            float wd = wu + wv;
            a = max(a, 1.0 - smoothstep(0.5 * wd, 1.5 * wd, abs(d - round(d))));
        }
        a *= WIRE_ALPHA;
    }
    return float2(a, acc);
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float2 halfRes = resolution * 0.5;
    // View-height units in both axes, so a panel stays square whatever the window
    // aspect. (The starfield normalises per-axis instead and lets its field stretch;
    // a stretching *drawing* would read as a mistake where a stretching dot does not.)
    float2 P = pos.xy - halfRes;
    float2 n = P / halfRes.y;
    float t = time;

    float lit = 0.0;    // coverage at this pixel
    float warm = 0.0;   // the share of it struck in the accent, for the hue
    float hot = 0.0;    // nearness of whatever covered it, for the white lift

    for (int i = 0; i < LAYERS; ++i) {
        // Planes evenly offset in phase, so the field always holds panels at every
        // stage of the approach rather than pulsing in unison.
        float raw = t * RATE + float(i) / float(LAYERS);
        float travel = frac(raw);
        float cycle = fmod(floor(raw), CYCLE_WRAP);   // re-rolls a plane's content
        // Even steps in 1/z are even steps *on screen* (the same reason the wave
        // stacks its slabs this way). Stepping z linearly instead spends almost every
        // plane in the far half, where 1/z barely moves -- which is why the field
        // came out as one size of panel repeated rather than a depth of them. This
        // spreads the planes evenly across apparent scale, so a big near panel, a
        // mid one and the far haze are all on screen at once.
        float z = 1.0 / lerp(1.0 / Z_FAR, 1.0 / Z_NEAR, travel);
        float alpha = min(1.0, travel / FADE_IN)
                    * (1.0 - smoothstep(1.0 - FADE_OUT, 1.0, travel));
        if (alpha <= 0.002) { continue; }

        // Run the projection backwards: at this depth the ray crosses the plane
        // here, so this is the only cell that can cover this pixel.
        float2 s = n * z;
        float2 cell = floor(s * GRID);
        float2 f = s * GRID - cell;

        // Each panel lives and dies on its own clock, much shorter than its plane's
        // traversal: it fades up, holds, fades out, and the cell is redrawn with a
        // fresh one. Decoupling the two is the whole point -- the plane's sweep used
        // to serve as the panel lifetime as well, so slowing the flight would have
        // made every panel linger proportionally longer. Now the flight can be slow
        // and the field still turns over quickly.
        float3 lh = hash33(cell * 0.61 + float2(float(i) * 3.0, 7.0));
        float lifeT = t * LIFE_RATE + lh.x * 11.0;
        float lifeGen = fmod(floor(lifeT), CYCLE_WRAP);
        float lifePh = frac(lifeT);
        float life = smoothstep(0.0, LIFE_IN, lifePh)
                   * (1.0 - smoothstep(1.0 - LIFE_OUT, 1.0, lifePh));
        if (life <= 0.002) { continue; }

        // ``lifeGen`` rides in every panel hash below, so a cell that comes back
        // comes back as a different panel rather than as the same one blinking.
        float3 ph = hash33(cell + float2(cycle * 13.0 + float(i) * 57.0 + lifeGen * 29.0,
                                         cycle * 7.0 - float(i) * 23.0 + lifeGen * 41.0));
        if (ph.x > PANEL_KEEP) { continue; }     // this cell is empty space

        float3 qh = hash33(cell * 1.37 + float2(float(i) * 11.0,
                                                cycle * 3.0 + lifeGen * 17.0));
        float pw = PANEL_W_MIN + PANEL_W_RNG * ph.y;
        float panelH = PANEL_H_MIN + PANEL_H_RNG * ph.z;
        float lx = (f.x - (1.0 - pw) * qh.x) / pw;   // panel-local, 0..1
        float ly = (f.y - (1.0 - panelH) * qh.y) / panelH;
        if (lx < 0.0 || lx > 1.0 || ly < 0.0 || ly > 1.0) { continue; }

        // One pixel, in cell units. Derived from the depth rather than from fwidth:
        // the branching above is non-uniform, which makes a derivative undefined,
        // and every antialiasing width downstream depends on this.
        float pixCell = z * GRID / halfRes.y;
        // Past the point where a pixel spans a good part of a row, the panel cannot
        // be read at all; fading it out is what keeps the far field from boiling.
        float resolve = 1.0 - smoothstep(RESOLVE * 0.5, RESOLVE,
                                         (pixCell / panelH) * ROWS);
        if (resolve <= 0.0) { continue; }

        // ``travel``, not z: with the 1/z stepping above it is travel that is linear
        // in apparent scale, so it is the measure that makes the aerial cue agree
        // with the size cue.
        float depth = 1.0 - travel;                         // 0 near, 1 far
        float bright = (0.3 + 0.7 * ph.y) * alpha * life * resolve
                     * lerp(1.0, DEPTH_DIM, depth);

        float2 r = panel_content(lx, ly, pixCell, pw, panelH,
                                 float2(cell.x * 13.0 + float(i),
                                        cell.y * 29.0 + cycle + lifeGen * 7.0),
                                 qh.z, frac(qh.y * 11.7), t);
        float a = r.x;

        // A hairline outline on some panels, which is most of what makes a cluster
        // of marks read as a *panel* rather than as loose debris.
        if (frac(qh.x * 7.3) < FRAME_SHARE) {
            float edge = min(min(lx, 1.0 - lx) * pw,
                             min(ly, 1.0 - ly) * panelH) / pixCell;
            a = max(a, (1.0 - smoothstep(0.6, 1.6, edge)) * FRAME_ALPHA);
        }

        a *= bright;
        lit = max(lit, a);
        warm = max(warm, r.y * bright);
        hot = max(hot, a * (1.0 - z / Z_FAR));
    }

    // --- concentration lines --------------------------------------------------
    // Radial speed streaks raking outward from the vanishing point. This is the
    // datastream's dash-in-a-slot wrapped around the centre: a pixel finds its
    // angular sector and its slot along the ray and consults exactly one cell, so a
    // whole field of them costs about what one more panel plane would. They sell the
    // forward motion the panels only imply -- the panels grow, but nothing *streaks*.
    float rad = length(P);
    float rn = rad / length(halfRes);          // 0 at the centre, 1 at the corner
    if (rn > CONC_IN && rad > 1.0) {
        float ang = atan2(P.y, P.x) / TAU + 0.5;
        // Wrapped, or the slot at ang = 1 would be a different draw from the one at
        // ang = 0 and the field would carry a seam straight out along -x.
        float sector = fmod(floor(ang * CONC_SECTORS), CONC_SECTORS);
        float3 ch = hash33(float2(sector, 4.0));
        if (ch.x * CONC_SECTORS < CONC_COUNT) {
            // Folded like the datastream's lanes: the fraction places the pixel in
            // its slot, the integer only names it.
            float shift = t * CONC_RATE * (0.5 + 1.2 * ch.y) / CONC_CELL;
            float shiftI = floor(shift);
            float uu = rn / CONC_CELL - (shift - shiftI);
            float slot = floor(uu);
            float fu = uu - slot;
            float3 dh = hash33(float2(fmod(slot - shiftI, CONC_WRAP), sector));
            if (dh.x < 0.75) {
                float dash = CONC_DASH * (0.35 + 0.9 * dh.y);
                // Constant width in pixels, so the angular half-width has to shrink
                // as the radius grows -- otherwise a streak fans out into a wedge.
                float dPx = abs(frac(ang * CONC_SECTORS) - 0.5) / CONC_SECTORS * TAU * rad;
                float covA = 1.0 - smoothstep(CONC_PX * 0.5, CONC_PX * 0.5 + 1.0, dPx);
                float covR = smoothstep(0.0, 0.02, fu)
                           * (1.0 - smoothstep(dash - 0.02, dash, fu));
                float fade = smoothstep(CONC_IN, CONC_IN + CONC_RAMP, rn);
                float a = covA * covR * fade * CONC_ALPHA * (0.5 + 0.5 * dh.z);
                lit = max(lit, a);
                hot = max(hot, a * (1.0 - smoothstep(0.0, 0.3, fu)) * CONC_HEAD);
            }
        }
    }

    // The ambient layer sits under the rest: dim, soft and cool, never warm or hot.
    lit = max(lit, ambient_field(pos.xy, t));

    // The fast layer, on top: this is the element that actually moves.
    float2 fastR = fast_field(pos.xy, t);
    lit = max(lit, fastR.x);
    hot = max(hot, fastR.y * FAST_HEAD);

    // The accent is the ink with red and blue swapped -- amber out of this scene's
    // cyan, and a theme-derived hue out of anything else (see the module note).
    float3 rgb = lerp(ink.rgb, ink.zyx, clamp(warm / max(lit, 1e-4), 0.0, 1.0));
    rgb = lerp(rgb, float3(1.0, 1.0, 1.0), clamp(hot, 0.0, 1.0) * NEAR_GLOW);

    rgb = lerp(backdrop.rgb, rgb, clamp(lit, 0.0, 1.0) * opacity);
    return float4(rgb, 1.0);
}
"""

#: Earth from orbit — the blue marble turning in the dark.
#:
#: **The one scene that needs no grid.** Every other background here answers "what
#: covers this pixel?" by hashing cell indices, because its objects are scattered and
#: a pixel cannot afford to visit them all. This scene has a single object, and a
#: sphere answers the question in closed form: under an orthographic projection a
#: pixel is on the planet exactly when it lies inside the disc, and the surface normal
#: there is ``(x, y, sqrt(1 - x² - y²))``. That normal *is* the scene — it gives the
#: point to sample the continents at, the angle to the sun, and the grazing angle that
#: lights the atmosphere at the limb.
#:
#: **Sampled, not textured.** There is no map asset — puikit's background shaders bind
#: no images — so land is a threshold on 3D value-noise fBm evaluated at the un-spun
#: surface point. Sampling in three dimensions rather than off a lat/lon image is what
#: keeps the poles free of the pinch a wrapped texture would show, and the coastlines
#: get their shape from a **domain warp**: the field is displaced by a second, coarser
#: field before the sea-level threshold, which turns noise blobs into landmasses with
#: capes and inlets. That warp field is then reused as the *climate*, choosing between
#: two land tones — free, because it has already been evaluated.
#:
#: **Two materials, not one albedo.** The reference photographs separate land from sea
#: less by colour than by how each handles light, so they are lit differently here.
#: The sea is the only surface with a specular: a two-lobe highlight (a tight core in a
#: broad haze, which is what a wind-roughened surface does to a sun) plus a Fresnel
#: term that turns it mirror-like at grazing angles, so the water picks up the sky
#: toward the limb. The land takes neither, and gets instead what the sea has no
#: equivalent of — a high-frequency terrain field that swings its albedo, and relief
#: shading from a second sample of that field taken a step toward the sun, so slopes
#: facing away from it fall into shadow. Matte and textured against glossy and smooth
#: is the whole difference, and it survives being composited at a third of full
#: strength behind a file list.
#:
#: **The clouds live on their own shell**, at a radius slightly above the ground.
#: That single change buys both of the things a flat cloud layer cannot do. The ray
#: hits that shell at a different point than it hits the ground, by more and more as
#: it nears the limb, so the deck *parallaxes* over the continents as the planet turns.
#: And the shadow a cloud casts is cast by a *different* cloud than the one overhead —
#: the one the sun's ray meets on the way in — which is found by stepping from the
#: ground point toward the sun, and stretches out as the sun sinks, so the shadows
#: lengthen toward the terminator.
#:
#: **The atmosphere is where the sunrise comes from.** Both the shell outside the disc
#: and the rim inside it are coloured by the sun's *elevation at that point of the
#: sky* rather than by a fixed tint: overhead sun gives the blue band, and as the
#: elevation falls to zero the band runs through gold — the long slant path that
#: reddens a sunrise, which from orbit is a ring rather than an event. Where that gold
#: band meets the limb it blooms into a wider, whiter flare, the moment the sun is
#: about to clear the horizon. The band also survives a little past the geometric
#: terminator, because air that high is still in sunlight when the ground below is not.
EARTH_MSL = """
// --- geometry ---------------------------------------------------------------
constant float RADIUS      = 0.30;  // globe radius, as a fraction of the short side
constant float CENTRE_X    = 0.68;  // globe centre, as a fraction of the width ...
constant float CENTRE_Y    = 0.40;  // ... and of the height
constant float SPIN        = 0.015; // turns per second
constant float TILT        = 0.41;  // axial tilt, in radians (23.4 degrees)
constant float TAU         = 6.28318530718;

// --- terrain ----------------------------------------------------------------
constant int   LAND_OCT    = 5;     // fBm octaves for the continents
constant int   WARP_OCT    = 2;     // ... for the field that displaces them
constant int   CLOUD_OCT   = 4;     // ... for the cloud deck and its shadow
constant int   DETAIL_OCT  = 2;     // ... for the terrain the land is textured with
constant float LAND_FREQ   = 2.2;   // continent scale, in cells per unit sphere
constant float WARP        = 0.75;  // how far the warp field displaces the sample
constant float SEA         = 0.55;  // fBm level separating water from land. Above the
                                    // 0.5 mean on purpose: it is what sets the land
                                    // fraction, and Earth's is under a third
constant float COAST       = 0.035; // width of the shoreline blend
constant float SHELF       = 0.13;  // fBm below sea level where the deep ocean starts
constant float ICE_LAT     = 0.80;  // |sin(latitude)| where the polar caps begin

// --- land material: matte, textured, relief-shaded --------------------------
constant float DETAIL_FREQ = 9.0;   // terrain scale -- far finer than the continents
constant float DETAIL_AMT  = 0.45;  // how far that field swings the land's albedo
constant float BUMP        = 3.0;   // relief shading strength
constant float BUMP_STEP   = 0.014; // how far toward the sun the second sample sits

// --- sea material: dark, glossy, the only specular in the scene -------------
// The ink pushed apart through fixed channel scales (the trick the wave uses), which
// keeps the water blue whatever the ink's own luminance is. Deliberately dark: from
// orbit the sunlit ocean is nearly navy everywhere except where the sun is mirrored
// in it, and it is that near-black water the clouds and continents read against.
constant float DEEP_R      = 0.05;
constant float DEEP_G      = 0.14;
constant float DEEP_B      = 0.34;
constant float SHAL_R      = 0.12;
constant float SHAL_G      = 0.33;
constant float SHAL_B      = 0.64;
constant float GLINT_TIGHT = 220.0; // the specular's core ...
constant float GLINT_BROAD = 14.0;  // ... inside the haze a roughened sea spreads it
constant float GLINT_CORE  = 0.65;  // how the two lobes divide the highlight
constant float GLINT       = 0.7;   // overall strength of the sun's mirror
constant float SEA_FRESNEL = 0.35;   // how mirror-like the water goes at the limb

// --- clouds: a shell above the ground ---------------------------------------
constant float CLOUD_ALT   = 0.028; // shell height, in ground radii. Exaggerated
                                    // ~18x over the real troposphere, which is what
                                    // makes the parallax and the shadows legible
constant float CLOUD_FREQ  = 3.1;
constant float CLOUD_LEVEL = 0.52;  // fBm level above which cloud covers the ground
constant float CLOUD_SOFT  = 0.20;  // width of a cloud's edge
constant float CLOUD_MAX   = 0.80;  // how opaque the thickest cloud gets
constant float CLOUD_DRIFT = 0.004; // extra turns per second, relative to the ground
constant float SHADOW_MAX  = 0.55;  // how far a cloud darkens the ground beneath
constant float SHADOW_LEN  = 1.6;   // shadow throw, in cloud-shell heights
constant float SHADOW_MIN  = 0.35;  // floor on the sun's height, so the shadow
                                    // lengthens toward the terminator without the
                                    // 1/cos blowing up as it crosses

// --- light ------------------------------------------------------------------
constant float LIGHT_X     = -0.72; // direction to the sun, in view space. Well off
constant float LIGHT_Y     = 0.28;  // the view axis, so the terminator crosses the
constant float LIGHT_Z     = 0.42;  // disc instead of hiding behind the limb
constant float TERM_SOFT   = 0.18;  // half-width of the day/night terminator
constant float NIGHT       = 0.06;  // how much daylight colour survives the dark side

// --- atmosphere -------------------------------------------------------------
constant float ATM_ALT     = 0.055; // shell height, in ground radii
constant float ATM_OUT     = 0.9;  // brightness of the band outside the disc
constant float ATM_POW     = 1.5;   // how tightly that band hugs the limb
constant float SKY_R       = 0.45;  // the daylight sky: the ink pushed to a
constant float SKY_G       = 0.72;  // saturated blue through fixed channel
constant float SKY_B       = 1.00;  // scales, then barely lifted toward white
constant float SKY_MIX     = 0.12;  // -- a wash toward white reads as grey plastic
constant float DUSK_G      = 0.66;  // the sunrise colour: the warm ink, its green and
constant float DUSK_B      = 0.30;  // blue pulled down until it is a true orange
constant float DUSK_LO     = 0.02;  // sun elevation where the band is fully gold ...
constant float DUSK_HI     = 0.42;  // ... and where it has become the blue sky
constant float ATM_WRAP    = 0.30;  // how far past the terminator the air stays lit
constant float SUNRISE     = 0.5;   // the flare where the gold band meets the limb
constant float SUNRISE_W   = 0.16;  // its angular width, in sun elevation
constant float SUNRISE_SPD = 2.5;   // its reach outward, in atmosphere heights
constant float RIM         = 1.0;   // atmosphere brightness at the limb, inside it
constant float RIM_POW     = 2.4;   // how tightly that hugs the edge

// --- city lights & stars ----------------------------------------------------
constant float CITY_FREQ   = 45.0;  // city-light clumps per unit sphere
constant float CITY_LEVEL  = 0.74;  // noise level a clump must clear to be lit
constant float CITY_SOFT   = 0.06;
constant float POP_LO      = 0.44;  // where the climate field starts to be settled
constant float POP_HI      = 0.60;  // ... and where it is fully so
constant float CITY_BRIGHT = 0.55;
constant float STAR_CELLS  = 30.0;  // star cells across the short side
constant float STAR_RARE   = 0.86;  // fraction of those cells left empty
constant float STAR_PX     = 1.1;   // star half-width, in pixels
constant float TWINKLE     = 1.7;   // twinkle rate, in radians per second

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
static inline float hash13(float3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.zyx + 31.32);
    return fract((p.x + p.y) * p.z);
}

// Value noise on the lattice: eight corner hashes, smoothstep-weighted. Sampled in
// 3D rather than on a wrapped 2D map, which is what lets the field be continuous
// across the poles instead of pinching there.
static inline float vnoise(float3 x) {
    float3 i = floor(x);
    float3 f = x - i;
    f = f * f * (3.0 - 2.0 * f);
    float n000 = hash13(i);
    float n100 = hash13(i + float3(1.0, 0.0, 0.0));
    float n010 = hash13(i + float3(0.0, 1.0, 0.0));
    float n110 = hash13(i + float3(1.0, 1.0, 0.0));
    float n001 = hash13(i + float3(0.0, 0.0, 1.0));
    float n101 = hash13(i + float3(1.0, 0.0, 1.0));
    float n011 = hash13(i + float3(0.0, 1.0, 1.0));
    float n111 = hash13(i + float3(1.0, 1.0, 1.0));
    return mix(mix(mix(n000, n100, f.x), mix(n010, n110, f.x), f.y),
               mix(mix(n001, n101, f.x), mix(n011, n111, f.x), f.y), f.z);
}

static inline float fbm(float3 p, int octaves) {
    float sum = 0.0;
    float amp = 0.5;
    float norm = 0.0;
    for (int i = 0; i < octaves; ++i) {
        sum += amp * vnoise(p);
        norm += amp;
        // Non-integral step, plus an offset, so successive octaves never sit on the
        // same lattice and the sum keeps no trace of the grid it was built on.
        p = p * 2.03 + 19.7;
        amp *= 0.5;
    }
    return sum / norm;
}

static inline float3 spin_y(float3 p, float a) {
    float s = sin(a), c = cos(a);
    return float3(c * p.x + s * p.z, p.y, c * p.z - s * p.x);
}
static inline float3 tilt_x(float3 p, float a) {
    float s = sin(a), c = cos(a);
    return float3(p.x, c * p.y - s * p.z, s * p.y + c * p.z);
}

fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]]) {
    // Normalised by the SHORT side so the globe stays a circle in any window, and
    // scaled by the radius so `r` reads 1.0 exactly at the limb.
    float S = min(u.resolution.x, u.resolution.y);
    float2 centre = u.resolution * float2(CENTRE_X, CENTRE_Y);
    float2 q = (pos.xy - centre) / (S * RADIUS);
    q.y = -q.y;                     // pixel y runs down; the scene works in y-up
    float r = length(q);

    float3 L = normalize(float3(LIGHT_X, LIGHT_Y, LIGHT_Z));
    float3 warm = u.ink.zyx;        // ink with red and blue swapped -- sand out of blue
    float3 sky = mix(u.ink.rgb * float3(SKY_R, SKY_G, SKY_B), float3(1.0), SKY_MIX);
    float3 dusk = warm * float3(1.0, DUSK_G, DUSK_B);
    float3 rgb = u.backdrop.rgb;
    float spin = -u.time * SPIN * TAU;
    float atmR = 1.0 + ATM_ALT;

    if (r > 1.0) {
        // Stars, one cell in eight or so, each a fixed point that only breathes. A
        // pixel consults its own cell and no other: a star is smaller than a cell,
        // so it can never reach across the boundary.
        float2 g = pos.xy / S * STAR_CELLS;
        float2 cell = floor(g);
        float pick = hash11(cell.x * 51.7 + cell.y * 97.3);
        if (pick > STAR_RARE) {
            float2 j = hash21(cell + 3.7);
            float d = length(g - cell - j) * S / STAR_CELLS;   // back into pixels
            float core = max(0.0, 1.0 - d / STAR_PX);
            float mag = (pick - STAR_RARE) / (1.0 - STAR_RARE);
            float tw = 0.7 + 0.3 * sin(u.time * TWINKLE + pick * 40.0);
            rgb = mix(rgb, mix(u.ink.rgb, float3(1.0), 0.5), core * core * mag * tw);
        }
    }

    float aa = 1.5 / (S * RADIUS);            // a pixel and a half, in limb units

    // The atmosphere, seen past the edge of the globe. It starts just INSIDE the
    // limb rather than at it: the disc fades out across its antialias band, and if
    // the air only began where the ground ended, that band would fade to empty space
    // and leave a dark hairline tracing the whole planet.
    if (r > 1.0 - aa) {
        // Its brightness is the ray's
        // chord through the shell -- longest at the limb, zero where the shell ends
        // -- and its COLOUR is the sun's elevation at that point of the sky: blue
        // overhead, gold as it sinks to the horizon. That is the sunrise, and from
        // orbit it is a ring rather than a moment.
        float2 dir = q / max(r, 1e-4);
        float elev = dot(float3(dir, 0.0), L);
        float3 tint = mix(dusk, sky, smoothstep(DUSK_LO, DUSK_HI, elev));
        // Air this high is still in sunlight after the ground below it is not, so the
        // band reaches past the geometric terminator rather than ending on it.
        float lit_air = smoothstep(-ATM_WRAP, ATM_WRAP * 0.35, elev);
        float chord = min(1.0, sqrt(max(0.0, atmR * atmR - r * r))
                             / sqrt(max(1e-4, atmR * atmR - 1.0)));
        float band = pow(chord, ATM_POW) * ATM_OUT;
        // Where the gold band meets the limb it blooms: wider than the band, and
        // whitening at its core -- the sun about to clear the horizon.
        float flare = exp(-(r - 1.0) / (ATM_ALT * SUNRISE_SPD)) * SUNRISE
                    * exp(-elev * elev / (2.0 * SUNRISE_W * SUNRISE_W));
        float cover = clamp((band + flare) * lit_air, 0.0, 1.0);
        rgb = mix(rgb, mix(tint, float3(1.0), clamp(flare, 0.0, 1.0) * 0.5), cover);
    }

    float disc = 1.0 - smoothstep(1.0 - aa, 1.0, r);
    if (disc > 0.0) {
        // The sphere, in closed form. Orthographic, so x and y are the normal's own
        // x and y and the rest follows from the unit length.
        float3 N = float3(q, sqrt(max(0.0, 1.0 - min(r * r, 1.0))));

        // Into planet space: undo the axial tilt, then the spin. The noise field is
        // fixed to the ground, so it is the ground that turns under a fixed sun. The
        // sun makes the same trip, because the shadows are cast in this frame.
        float3 P = spin_y(tilt_x(N, -TILT), spin);
        float3 Lp = spin_y(tilt_x(L, -TILT), spin);

        float w = fbm(P * (LAND_FREQ * 0.6) + 11.0, WARP_OCT);
        float h = fbm(P * LAND_FREQ + (w - 0.5) * WARP, LAND_OCT);
        float land = smoothstep(SEA, SEA + COAST, h);
        float lam = dot(N, L);
        float day = smoothstep(-TERM_SOFT, TERM_SOFT, lam);

        // --- the cloud shell. The ray meets it at a different point than it meets
        // the ground, by more and more toward the limb: that difference IS the
        // parallax, and it costs one extra square root.
        float cloudR = 1.0 + CLOUD_ALT;
        float3 Nc = float3(q, sqrt(max(0.0, cloudR * cloudR - r * r))) / cloudR;
        float drift = -u.time * CLOUD_DRIFT * TAU;
        float cf = fbm(spin_y(spin_y(tilt_x(Nc, -TILT), spin), drift) * CLOUD_FREQ + 43.0,
                       CLOUD_OCT);
        float cloud = smoothstep(CLOUD_LEVEL, CLOUD_LEVEL + CLOUD_SOFT, cf) * CLOUD_MAX;

        // The shadow on this ground point is cast by whichever cloud the sun's ray
        // met on the way in -- a different one from the cloud overhead. Stepping
        // toward the sun and dividing by its height is what makes shadows stretch as
        // it sinks; the floor on that height keeps the stretch finite at the
        // terminator, where the true 1/cos would run away.
        float3 Ps = normalize(P + Lp * (CLOUD_ALT * SHADOW_LEN
                                        / max(dot(P, Lp), SHADOW_MIN)));
        float sf = fbm(spin_y(Ps, drift) * CLOUD_FREQ + 43.0, CLOUD_OCT);
        float shadow = smoothstep(CLOUD_LEVEL, CLOUD_LEVEL + CLOUD_SOFT, sf) * SHADOW_MAX;

        // --- the sea: dark, and the only surface here with a specular.
        float3 deep = u.ink.rgb * float3(DEEP_R, DEEP_G, DEEP_B);
        float3 shallow = u.ink.rgb * float3(SHAL_R, SHAL_G, SHAL_B);
        float3 sea = mix(deep, shallow, smoothstep(SEA - SHELF, SEA, h));

        // --- the land: matte, and textured at a scale the sea has no equivalent of.
        // The second sample is taken a step toward the sun: where the terrain rises
        // that way the slope faces away from it, so the difference between the two
        // IS the relief shading, with no derivative and no normal map.
        float d0 = fbm(P * DETAIL_FREQ, DETAIL_OCT);
        float d1 = fbm((P + Lp * BUMP_STEP) * DETAIL_FREQ, DETAIL_OCT);
        float3 ground = mix(u.ink.yzx * 0.42, warm * 0.66, smoothstep(0.42, 0.66, w));
        ground *= 1.0 - DETAIL_AMT * 0.5 + DETAIL_AMT * d0;
        float relief = clamp(1.0 - (d1 - d0) * BUMP, 0.35, 1.7);

        float3 surf = mix(sea, ground, land);
        // Polar caps, their edge broken up by the terrain field so they do not close
        // as two clean circles of latitude.
        float ice = smoothstep(ICE_LAT, ICE_LAT + 0.16, abs(P.y) + (h - 0.5) * 0.22);
        surf = mix(surf, mix(u.ink.rgb, float3(1.0), 0.55), ice);

        // Diffuse. The relief belongs to the land alone -- water has no slopes -- and
        // the cloud shadows fall on both.
        float shade = day * mix(1.0, relief, land) * (1.0 - shadow);
        float3 lit = surf * (NIGHT + (1.0 - NIGHT) * shade);

        // The sun mirrored in the water: a tight core inside the broad haze that a
        // wind-roughened surface spreads it into.
        float3 H = normalize(L + float3(0.0, 0.0, 1.0));
        float ndh = max(dot(N, H), 0.0);
        float water = (1.0 - land) * (1.0 - cloud) * (1.0 - ice) * day;
        float glint = (pow(ndh, GLINT_TIGHT) * GLINT_CORE
                       + pow(ndh, GLINT_BROAD) * (1.0 - GLINT_CORE)) * GLINT;
        lit += glint * water * mix(u.ink.rgb, float3(1.0), 0.7);
        // Fresnel: at a grazing angle water stops being blue and starts being a
        // mirror, so it takes the sky. This is the cue that separates the two
        // materials at the limb, where the land stays matte.
        lit = mix(lit, sky, pow(1.0 - N.z, 5.0) * SEA_FRESNEL * water);

        // The deck, lit by the same sun as the ground under it.
        lit = mix(lit, mix(u.ink.rgb, float3(1.0), 0.82) * (NIGHT + (1.0 - NIGHT) * day),
                  cloud);

        // City lights: warm clumps on the unlit land, dimmed under cloud. The one
        // element that only exists on the night side, and what makes the terminator
        // read as a coastline of light rather than as an edge.
        // The clumps themselves are fine and dense, but people are not spread evenly
        // over the land -- so the same climate field that chose green against desert
        // serves a third time as the population, leaving whole coastlines dark
        // between the lit regions.
        float city = smoothstep(CITY_LEVEL, CITY_LEVEL + CITY_SOFT, vnoise(P * CITY_FREQ))
                   * smoothstep(POP_LO, POP_HI, w)
                   * land * (1.0 - day) * (1.0 - ice) * (1.0 - cloud * 0.8);
        lit += city * CITY_BRIGHT * mix(warm, float3(1.0), 0.25);

        // The atmosphere seen through its own limb, coloured the same way as the
        // shell outside it: blue where the sun is high over that point, gold where it
        // is setting on it.
        float3 tint = mix(dusk, sky, smoothstep(DUSK_LO, DUSK_HI, lam));
        float rim = pow(1.0 - N.z, RIM_POW) * RIM * smoothstep(-ATM_WRAP, ATM_WRAP * 0.35, lam);
        lit = mix(lit, tint, clamp(rim, 0.0, 1.0));

        rgb = mix(rgb, lit, disc);
    }

    return float4(mix(u.backdrop.rgb, rgb, u.opacity), 1.0);
}
"""

#: The HLSL translation of :data:`EARTH_MSL`. Line-for-line; only the dialect
#: differs. Keep the two in sync when tuning the scene.
EARTH_HLSL = """
// --- tunables (see EARTH_MSL for the rationale of each) ----------------------
static const float RADIUS      = 0.30;
static const float CENTRE_X    = 0.68;
static const float CENTRE_Y    = 0.40;
static const float SPIN        = 0.015;
static const float TILT        = 0.41;
static const float TAU         = 6.28318530718;

static const int   LAND_OCT    = 5;
static const int   WARP_OCT    = 2;
static const int   CLOUD_OCT   = 4;
static const int   DETAIL_OCT  = 2;
static const float LAND_FREQ   = 2.2;
static const float WARP        = 0.75;
static const float SEA         = 0.55;
static const float COAST       = 0.035;
static const float SHELF       = 0.13;
static const float ICE_LAT     = 0.80;

static const float DETAIL_FREQ = 9.0;
static const float DETAIL_AMT  = 0.45;
static const float BUMP        = 3.0;
static const float BUMP_STEP   = 0.014;

static const float DEEP_R      = 0.05;
static const float DEEP_G      = 0.14;
static const float DEEP_B      = 0.34;
static const float SHAL_R      = 0.12;
static const float SHAL_G      = 0.33;
static const float SHAL_B      = 0.64;
static const float GLINT_TIGHT = 220.0;
static const float GLINT_BROAD = 14.0;
static const float GLINT_CORE  = 0.65;
static const float GLINT       = 0.7;
static const float SEA_FRESNEL = 0.35;

static const float CLOUD_ALT   = 0.028;
static const float CLOUD_FREQ  = 3.1;
static const float CLOUD_LEVEL = 0.52;
static const float CLOUD_SOFT  = 0.20;
static const float CLOUD_MAX   = 0.80;
static const float CLOUD_DRIFT = 0.004;
static const float SHADOW_MAX  = 0.55;
static const float SHADOW_LEN  = 1.6;
static const float SHADOW_MIN  = 0.35;

static const float LIGHT_X     = -0.72;
static const float LIGHT_Y     = 0.28;
static const float LIGHT_Z     = 0.42;
static const float TERM_SOFT   = 0.18;
static const float NIGHT       = 0.06;

static const float ATM_ALT     = 0.055;
static const float ATM_OUT     = 0.9;
static const float ATM_POW     = 1.5;
static const float SKY_R       = 0.45;
static const float SKY_G       = 0.72;
static const float SKY_B       = 1.00;
static const float SKY_MIX     = 0.12;
static const float DUSK_G      = 0.66;
static const float DUSK_B      = 0.30;
static const float DUSK_LO     = 0.02;
static const float DUSK_HI     = 0.42;
static const float ATM_WRAP    = 0.30;
static const float SUNRISE     = 0.5;
static const float SUNRISE_W   = 0.16;
static const float SUNRISE_SPD = 2.5;
static const float RIM         = 1.0;
static const float RIM_POW     = 2.4;

static const float CITY_FREQ   = 45.0;
static const float CITY_LEVEL  = 0.74;
static const float CITY_SOFT   = 0.06;
static const float POP_LO      = 0.44;
static const float POP_HI      = 0.60;
static const float CITY_BRIGHT = 0.55;
static const float STAR_CELLS  = 30.0;
static const float STAR_RARE   = 0.86;
static const float STAR_PX     = 1.1;
static const float TWINKLE     = 1.7;

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
float hash13(float3 p) {
    p = frac(p * 0.1031);
    p += dot(p, p.zyx + 31.32);
    return frac((p.x + p.y) * p.z);
}

float vnoise(float3 x) {
    float3 i = floor(x);
    float3 f = x - i;
    f = f * f * (3.0 - 2.0 * f);
    float n000 = hash13(i);
    float n100 = hash13(i + float3(1.0, 0.0, 0.0));
    float n010 = hash13(i + float3(0.0, 1.0, 0.0));
    float n110 = hash13(i + float3(1.0, 1.0, 0.0));
    float n001 = hash13(i + float3(0.0, 0.0, 1.0));
    float n101 = hash13(i + float3(1.0, 0.0, 1.0));
    float n011 = hash13(i + float3(0.0, 1.0, 1.0));
    float n111 = hash13(i + float3(1.0, 1.0, 1.0));
    return lerp(lerp(lerp(n000, n100, f.x), lerp(n010, n110, f.x), f.y),
                lerp(lerp(n001, n101, f.x), lerp(n011, n111, f.x), f.y), f.z);
}

float fbm(float3 p, int octaves) {
    float sum = 0.0;
    float amp = 0.5;
    float norm = 0.0;
    for (int i = 0; i < octaves; ++i) {
        sum += amp * vnoise(p);
        norm += amp;
        p = p * 2.03 + 19.7;
        amp *= 0.5;
    }
    return sum / norm;
}

float3 spin_y(float3 p, float a) {
    float s = sin(a), c = cos(a);
    return float3(c * p.x + s * p.z, p.y, c * p.z - s * p.x);
}
float3 tilt_x(float3 p, float a) {
    float s = sin(a), c = cos(a);
    return float3(p.x, c * p.y - s * p.z, s * p.y + c * p.z);
}

float4 puikit_bg_fragment(float4 pos : SV_Position) : SV_Target {
    float S = min(resolution.x, resolution.y);
    float2 centre = resolution * float2(CENTRE_X, CENTRE_Y);
    float2 q = (pos.xy - centre) / (S * RADIUS);
    q.y = -q.y;
    float r = length(q);

    float3 L = normalize(float3(LIGHT_X, LIGHT_Y, LIGHT_Z));
    float3 warm = ink.zyx;
    float3 sky = lerp(ink.rgb * float3(SKY_R, SKY_G, SKY_B), float3(1.0, 1.0, 1.0), SKY_MIX);
    float3 dusk = warm * float3(1.0, DUSK_G, DUSK_B);
    float3 rgb = backdrop.rgb;
    float spin = -time * SPIN * TAU;
    float atmR = 1.0 + ATM_ALT;

    if (r > 1.0) {
        float2 g = pos.xy / S * STAR_CELLS;
        float2 cell = floor(g);
        float pick = hash11(cell.x * 51.7 + cell.y * 97.3);
        if (pick > STAR_RARE) {
            float2 j = hash21(cell + 3.7);
            float d = length(g - cell - j) * S / STAR_CELLS;
            float core = max(0.0, 1.0 - d / STAR_PX);
            float mag = (pick - STAR_RARE) / (1.0 - STAR_RARE);
            float tw = 0.7 + 0.3 * sin(time * TWINKLE + pick * 40.0);
            rgb = lerp(rgb, lerp(ink.rgb, float3(1.0, 1.0, 1.0), 0.5),
                       core * core * mag * tw);
        }
    }

    float aa = 1.5 / (S * RADIUS);

    if (r > 1.0 - aa) {
        float2 dir = q / max(r, 1e-4);
        float elev = dot(float3(dir, 0.0), L);
        float3 tint = lerp(dusk, sky, smoothstep(DUSK_LO, DUSK_HI, elev));
        float lit_air = smoothstep(-ATM_WRAP, ATM_WRAP * 0.35, elev);
        float chord = min(1.0, sqrt(max(0.0, atmR * atmR - r * r))
                             / sqrt(max(1e-4, atmR * atmR - 1.0)));
        float band = pow(chord, ATM_POW) * ATM_OUT;
        float flare = exp(-(r - 1.0) / (ATM_ALT * SUNRISE_SPD)) * SUNRISE
                    * exp(-elev * elev / (2.0 * SUNRISE_W * SUNRISE_W));
        float cover = clamp((band + flare) * lit_air, 0.0, 1.0);
        rgb = lerp(rgb, lerp(tint, float3(1.0, 1.0, 1.0), clamp(flare, 0.0, 1.0) * 0.5),
                   cover);
    }

    float disc = 1.0 - smoothstep(1.0 - aa, 1.0, r);
    if (disc > 0.0) {
        float3 N = float3(q, sqrt(max(0.0, 1.0 - min(r * r, 1.0))));
        float3 P = spin_y(tilt_x(N, -TILT), spin);
        float3 Lp = spin_y(tilt_x(L, -TILT), spin);

        float w = fbm(P * (LAND_FREQ * 0.6) + 11.0, WARP_OCT);
        float h = fbm(P * LAND_FREQ + (w - 0.5) * WARP, LAND_OCT);
        float land = smoothstep(SEA, SEA + COAST, h);
        float lam = dot(N, L);
        float day = smoothstep(-TERM_SOFT, TERM_SOFT, lam);

        float cloudR = 1.0 + CLOUD_ALT;
        float3 Nc = float3(q, sqrt(max(0.0, cloudR * cloudR - r * r))) / cloudR;
        float drift = -time * CLOUD_DRIFT * TAU;
        float cf = fbm(spin_y(spin_y(tilt_x(Nc, -TILT), spin), drift) * CLOUD_FREQ + 43.0,
                       CLOUD_OCT);
        float cloud = smoothstep(CLOUD_LEVEL, CLOUD_LEVEL + CLOUD_SOFT, cf) * CLOUD_MAX;

        float3 Ps = normalize(P + Lp * (CLOUD_ALT * SHADOW_LEN
                                        / max(dot(P, Lp), SHADOW_MIN)));
        float sf = fbm(spin_y(Ps, drift) * CLOUD_FREQ + 43.0, CLOUD_OCT);
        float shadow = smoothstep(CLOUD_LEVEL, CLOUD_LEVEL + CLOUD_SOFT, sf) * SHADOW_MAX;

        float3 deep = ink.rgb * float3(DEEP_R, DEEP_G, DEEP_B);
        float3 shallow = ink.rgb * float3(SHAL_R, SHAL_G, SHAL_B);
        float3 sea = lerp(deep, shallow, smoothstep(SEA - SHELF, SEA, h));

        float d0 = fbm(P * DETAIL_FREQ, DETAIL_OCT);
        float d1 = fbm((P + Lp * BUMP_STEP) * DETAIL_FREQ, DETAIL_OCT);
        float3 ground = lerp(ink.yzx * 0.42, warm * 0.66, smoothstep(0.42, 0.66, w));
        ground *= 1.0 - DETAIL_AMT * 0.5 + DETAIL_AMT * d0;
        float relief = clamp(1.0 - (d1 - d0) * BUMP, 0.35, 1.7);

        float3 surf = lerp(sea, ground, land);
        float ice = smoothstep(ICE_LAT, ICE_LAT + 0.16, abs(P.y) + (h - 0.5) * 0.22);
        surf = lerp(surf, lerp(ink.rgb, float3(1.0, 1.0, 1.0), 0.55), ice);

        float shade = day * lerp(1.0, relief, land) * (1.0 - shadow);
        float3 lit = surf * (NIGHT + (1.0 - NIGHT) * shade);

        float3 H = normalize(L + float3(0.0, 0.0, 1.0));
        float ndh = max(dot(N, H), 0.0);
        float water = (1.0 - land) * (1.0 - cloud) * (1.0 - ice) * day;
        float glint = (pow(ndh, GLINT_TIGHT) * GLINT_CORE
                       + pow(ndh, GLINT_BROAD) * (1.0 - GLINT_CORE)) * GLINT;
        lit += glint * water * lerp(ink.rgb, float3(1.0, 1.0, 1.0), 0.7);
        lit = lerp(lit, sky, pow(1.0 - N.z, 5.0) * SEA_FRESNEL * water);

        lit = lerp(lit, lerp(ink.rgb, float3(1.0, 1.0, 1.0), 0.82)
                        * (NIGHT + (1.0 - NIGHT) * day), cloud);

        // The clumps themselves are fine and dense, but people are not spread evenly
        // over the land -- so the same climate field that chose green against desert
        // serves a third time as the population, leaving whole coastlines dark
        // between the lit regions.
        float city = smoothstep(CITY_LEVEL, CITY_LEVEL + CITY_SOFT, vnoise(P * CITY_FREQ))
                   * smoothstep(POP_LO, POP_HI, w)
                   * land * (1.0 - day) * (1.0 - ice) * (1.0 - cloud * 0.8);
        lit += city * CITY_BRIGHT * lerp(warm, float3(1.0, 1.0, 1.0), 0.25);

        float3 tint = lerp(dusk, sky, smoothstep(DUSK_LO, DUSK_HI, lam));
        float rim = pow(1.0 - N.z, RIM_POW) * RIM
                  * smoothstep(-ATM_WRAP, ATM_WRAP * 0.35, lam);
        lit = lerp(lit, tint, clamp(rim, 0.0, 1.0));

        rgb = lerp(rgb, lit, disc);
    }

    return float4(lerp(backdrop.rgb, rgb, opacity), 1.0);
}
"""

#: Every scene TFM offers, by the name a theme's ``animation`` key uses, paired with
#: the puikit ``Shader`` fields that belong to the scene rather than to the theme.
#: ``_resolve_background`` in ``tfm.py`` resolves a theme's ``animation`` name here
#: and nowhere else: a name absent from this dict yields no background at all, so a
#: typo in a theme costs the scene rather than startup.
#:
#: ``resolution_scale`` is per scene because only the scene knows how much sharpness
#: it can give up. The wave is diffuse grain, and at half resolution it is four times
#: cheaper — which is what keeps it affordable on a Retina display, and it needs to
#: be: the texture-mapped sheet samples three octaves across 24 depth slabs. The
#: upscale does soften its dots, and that is a deliberate trade rather than a free
#: one; 0.75 renders them visibly crisper for a little over twice the cost. Every
#: other scene here is thin bright lines, where halving the scale and upscaling would
#: trade away the crispness that is the point of drawing them.
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
    # Thin dashes with crisp leading edges, and the far layers' rows are only a few
    # pixels apart — halving the scale would merge them into a band.
    "datastream": {"source": DATASTREAM_MSL, "source_hlsl": DATASTREAM_HLSL},
    # Hairline rules, 1px panel outlines and blocks a couple of pixels tall, all of
    # which the upscale from a half-scale render would smear into mush. It is also
    # the scene that most wants the resolution: its far planes fade out exactly where
    # a pixel stops resolving a row, so rendering at half scale would throw away
    # depth, not just sharpness.
    "hologram": {"source": HOLOGRAM_MSL, "source_hlsl": HOLOGRAM_HLSL},
    # The globe is a smooth gradient, so it is the one scene besides the wave that
    # could give up sharpness cheaply — but it does not, because its two smallest
    # features are the ones that carry it: the city lights are single noise cells a
    # few pixels across, and the atmosphere at the limb is a rim a few pixels wide.
    # Both are exactly what a half-scale render would blur away.
    "earth": {"source": EARTH_MSL, "source_hlsl": EARTH_HLSL},
}
