"""TFM's GPU background shaders — the scenes a fragment shader draws.

Companion to :mod:`tfm_background_animations`, which defines the CPU-drawn scenes.
Both are TFM's own content; the split is by *how* a scene is painted, and that
choice follows from what the scene needs:

* a **segment** scene (``tfm_background_animations``) is Python that returns line
  segments, which the backend strokes on the CPU. Every segment costs ~1.4µs to
  stroke and the whole scene is drawn in one color, so it suits scenes made of
  structure — a few hundred lines, dots or streaks.
* a **shader** scene (here) is Metal source evaluated per pixel on the GPU. Cost is
  independent of how much it draws and each pixel gets its own RGBA, so it suits
  scenes made of *density and color* — thousands of particles, gradients, glow.

The wave below is the reason this module exists: a dense particle field, measured
at ~10ms/frame as segments (and still too sparse), is effectively free per-pixel.

**Writing one.** A shader is a single Metal fragment function named
``puikit_bg_fragment``. PuiKit prepends ``SHADER_PRELUDE`` — the uniform struct and
a fullscreen vertex stage — so the source here is just that function::

    fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                       constant BackgroundUniforms &u [[buffer(0)]])

``u`` carries ``resolution`` (pixels), ``time`` (seconds, already scaled by the
theme's speed), ``opacity``, and the theme's ``ink``/``backdrop`` as RGBA — so a
shader stays on-palette without knowing anything about TFM's theme system. The
source is compiled when the theme is applied; one that fails to compile draws
nothing and logs the compiler error, so a typo costs a blank background.
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
WAVE = """
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

#: Shader scenes TFM offers, by the name a theme's ``animation`` key uses, each
#: with the puikit ``Shader`` fields that belong to the scene rather than to the
#: theme. Kept separate from ``tfm_background_animations.ANIMATION_KINDS`` because
#: the two resolve into different puikit descriptors — a ``Shader`` here, a
#: ``Background3D`` there — but they share one namespace, so a theme just names a
#: scene and never has to know which renderer draws it.
#:
#: ``resolution_scale`` is per scene because only the scene knows how much
#: sharpness it can give up: the wave is diffuse grain, indistinguishable at half
#: resolution and four times cheaper there, which is what keeps it affordable on a
#: Retina display.
SHADER_KINDS: dict[str, dict] = {
    "wave": {"source": WAVE, "resolution_scale": 0.5},
}
