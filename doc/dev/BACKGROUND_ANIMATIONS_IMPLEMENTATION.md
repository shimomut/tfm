# Background Animations Implementation

How TFM's animated backgrounds are defined, registered and drawn, and what to do
to add one. End-user documentation is in
[BACKGROUND_ANIMATIONS_FEATURE.md](../BACKGROUND_ANIMATIONS_FEATURE.md).

## Two renderers, one namespace

A theme names a scene through a single `animation` key, but there are two ways a
scene can be painted, and the choice follows from what the scene needs:

| | **Segment scenes** | **Shader scenes** |
|---|---|---|
| Defined in | `src/tfm_background_animations.py` | `src/tfm_background_shaders.py` |
| Written as | Python returning line segments | Metal fragment shader source |
| Painted by | CoreGraphics, on the CPU | the GPU, per pixel |
| Descriptor | `puikit.background.Background3D` | `puikit.background.Shader` |
| Registry | `puikit.background.ANIMATIONS` | `SHADER_KINDS` (resolved in `tfm.py`) |
| Cost | ~1.4µs per segment | independent of what it draws |
| Repaints the UI to animate | yes, every frame | no |
| Colour | one per scene | full RGBA per pixel |
| Available | anywhere the GUI backend runs | macOS + Metal only |
| Scenes | starfield, rain, constellation, grid | wave |

`_resolve_background` in `tfm.py` checks `SHADER_KINDS` first and builds a
`Shader`, otherwise a `Background3D`. The two name-spaces must stay disjoint —
there is a test for it — since a name in both would resolve by accident of
ordering.

**Pick the CPU path** for scenes made of *structure*: a few hundred lines, dots or
streaks, where one colour is fine. **Pick the GPU path** for scenes made of
*density and colour*: thousands of particles, gradients, glow. The wave is the
worked example of why the split exists — as segments it measured 10ms/frame and
still looked sparse; as a shader it is denser than the reference and costs a
fraction of that.

## Where the pieces live

| Concern | Location |
|---------|----------|
| Segment scenes | `src/tfm_background_animations.py` (TFM) |
| Shader scenes | `src/tfm_background_shaders.py` (TFM) |
| Registry a segment scene is published into | `puikit.background.ANIMATIONS` (PuiKit) |
| Descriptors | `Background3D` / `Shader` in `puikit.background` (PuiKit) |
| Theme → descriptor resolution | `_resolve_background` in `tfm.py` |
| Push to the backend on theme switch | `TfmApp._apply_background` in `tfm.py` |
| Stroking the segments | `MacOSBackend._render_animation` (PuiKit) |
| Compiling and drawing a shader | `puikit/backends/_metal.py` (PuiKit) |
| Compositing the GPU layer | `MacOSBackend._sync_shader_layer` (PuiKit) |

The split is deliberate: **PuiKit owns how a scene is stroked, TFM owns what the
scenes are.** PuiKit ships only the wireframe cube — a reference scene that
exercises its projection path — and exposes `ANIMATIONS` as the extension point an
application fills in. Every production animation is TFM's, so adding one touches
`src/tfm_background_animations.py` and nothing else.

## The generator contract

A scene is a **pure function**:

```python
def my_scene(width: float, height: float, t: float, *, speed: float = 1.0) -> list[tuple]:
    ...
```

It returns the 2D line segments to stroke, in pixels with a **top-left origin**
(matching the backend's flipped view). It is called once per frame with wall-clock
`t` in seconds.

Three rules follow from being called this way:

1. **All motion must derive from `t`.** The frame is recomputed from scratch every
   tick. A generator holding frame-to-frame state, or calling `random.random()`,
   would re-roll every particle 60 times a second — particles would jitter in
   place instead of travelling.
2. **Per-particle variety comes from `_rand(index, salt)`**, an integer avalanche
   hash. It gives each particle a fixed arbitrary-looking constant, so star 7 has
   the same spawn point on every frame and only its depth advances.
3. **`speed=0` must be static**, which falls out of rule 1 automatically when
   every time term is written `t * speed * rate`.

### Segments and per-segment alpha

A segment is either:

- `(x0, y0, x1, y1)` — stroked at the scene's own opacity, or
- `(x0, y0, x1, y1, alpha)` — that opacity scaled by `alpha` (0–1).

The optional fifth element is what carries **depth**, and it is the difference
between a flat line drawing and something that reads as three-dimensional: a far
star is dim, a trail fades along its length, a constellation edge fades in as two
nodes approach. All four scenes lean on it heavily.

`puikit.background.group_by_alpha` buckets segments by alpha so the backend strokes
one path per distinct level rather than one per segment. Alphas are quantized to
`ALPHA_LEVELS` (64) so a continuously-shaded scene stays bounded — a 400-star field
costs at most 64 strokes, not 400. Fully transparent segments are dropped, and
buckets are returned dim-to-bright so brighter strokes win where they overlap.

## Registration and resolution

`src/tfm_background_animations.py` publishes its scenes at import:

```python
ANIMATION_KINDS = {"starfield": starfield_segments, ...}

def register() -> None:
    ANIMATIONS.update(ANIMATION_KINDS)

register()
```

`tfm.py` imports the module purely for that side effect (the import carries a
`noqa: F401`). From there:

1. A theme names `animation='starfield'` (or a params dict).
2. `_resolve_background` builds a `Background3D(kind='starfield', ...)`, filling in
   `color` from the theme foreground and `backdrop` from the theme background so
   the scene stays on-palette. `_ANIM_DEFAULTS` supplies TFM's tuning
   (`speed=0.6, opacity=0.6`); `_ANIM_DEFAULT_KIND` is used when a theme says
   `animation=True` without naming a type.
3. The descriptor rides in `theme.extras['background']`.
4. `TfmApp._apply_background` pushes it on every theme switch, so switching away
   clears it.
5. Per frame, the backend looks `kind` up in `ANIMATIONS` and strokes the result.

An **unknown kind is not an error** anywhere in this chain — the backend's registry
lookup misses and the frame simply draws nothing. A config typo degrades to a plain
background rather than blocking startup.

A backend without the `background_3d` capability (curses) inherits a no-op
`set_background`, so none of this branches on the backend.

## Adding an animation

1. Write the generator in `src/tfm_background_animations.py`, following the
   contract above.
2. Add it to `ANIMATION_KINDS`.
3. Add a row to the table in `doc/BACKGROUND_ANIMATIONS_FEATURE.md` and to the
   theme comment block in `src/_config.py`.
4. Cover it in `test/test_background_animations.py` — the shared `SegmentContract`
   suite picks it up from `ANIMATION_KINDS` automatically, so you get purity,
   finiteness, alpha-range, culling, continuity and stroke-cost checks for free;
   add a class for whatever is specific to your scene.

### Verifying the look

The tests check invariants, not aesthetics, and TFM's TUI cannot be launched
non-interactively. To actually see a frame, rasterize it headlessly:

```bash
PYTHONPATH=.:src python tools/render_background_animations.py
PYTHONPATH=.:src python tools/render_background_animations.py --kind starfield --time 12 --size 1600x1000
```

It writes a PNG per scene (into `temp/` by default) and mirrors the backend's draw
— backdrop clear, alpha buckets, line width 1.5, flipped y — so what it produces is
what the app shows. Each scene is rendered against the theme it ships with.

This is worth doing: two defects in the original implementations were invisible to
the test suite and obvious in a render.

- The **starfield** spawned its stars at depth 1, where the plane projects to
  exactly the view bounds — so the field began already covering the window and
  stars drifted apart from everywhere instead of streaming out of a vanishing
  point. Fixed by spawning at `_STAR_FAR = 2.6`, which confines the far plane to
  the middle ~38% of the view.
- The **constellation** moved its nodes along sinusoidal paths, chosen to avoid a
  wrap discontinuity. But a sine dwells near its turning points, so nodes piled up
  along the edges and left the middle bare. Fixed by going back to linear drift
  with wrapping — uniform in time, hence uniform over the view — and hiding the
  wrap by fading each node out toward the border (`_border_fade`), so it dissolves
  as it leaves and resolves as it re-enters.

Both are now covered by regression tests
(`test_stars_stream_out_of_a_vanishing_point`, `test_nodes_cover_the_whole_view`).

## The grid tunnel is the one real 3D scene

`starfield`, `rain` and `constellation` compute screen coordinates directly.
`grid` does not: it places world points on the four walls of a corridor running
down +z, transforms them by a moving camera, and projects. That is what buys the
effect — the walls converge on a vanishing point that *moves* as the camera yaws
and pitches, and near geometry parallaxes against far geometry as it drifts.
Neither can be faked by scrolling a fixed fan of lines, which is what the scene
did originally.

- `_camera(t, speed)` returns `(x, y, yaw, pitch, z)`. Position and angle sway on
  four slow sines whose rates are mutually incommensurate (periods ~27s, ~34s,
  ~43s, ~53s), so the motion never comes back into phase and never reads as a
  loop. Drift amplitudes stay well inside the corridor so the camera cannot clip
  a wall.
- The corridor's half-width is derived from the view aspect so that **at depth 1
  its cross-section maps exactly onto the viewport**. Nearer than that the camera
  is inside it and the walls run off every edge; further away they close toward
  the centre.
- Geometry is **rings** (rectangular cross-sections at a fixed world spacing) and
  **rails** (longitudinal lines along the walls). Rails are subdivided at exactly
  the ring depths, so the two families meet and the cells line up.
- Rings live at fixed world positions and are selected by a depth window rather
  than scrolled, which makes recycling seamless by construction: a ring leaves
  the near end only once it is far outside the view, and enters at the far end
  where the fade has it at zero. `_TUNNEL_NEAR` is chosen small enough to
  guarantee the former.
- `_TUNNEL_MIN_DEPTH` guards the perspective divide when a pitched or yawed
  camera swings a near corner behind the eye; such a point projects to `None` and
  its segment is dropped.

## Idle parking (applies to both kinds)

An animated background is the only thing in TFM that keeps an idle app redrawing
indefinitely, so PuiKit stops it when nobody is watching. Lives in
`MacOSBackend`, so neither TFM nor any scene has to opt in.

- `_bg_target` asks for full rate while the window holds focus **and** input was
  recent (`_BG_IDLE_TIMEOUT`, 15s); otherwise zero. Same shape as
  `_roll_user_active` for the CRT roll.
- `_background_tick` eases `_bg_rate` toward that target — `_BG_RAMP_DOWN` (40s)
  falling, `_BG_RAMP_UP` (15s) rising — and runs it through `_smoothstep`, so the
  *change in speed* is gradual at both ends. Measured: at most **0.17%** change in
  speed per frame, which is below the threshold at which the eye reads the ramp
  itself as motion. Stopping dead would be as noticeable as the animation.
- Those spans are long deliberately, and they trade against the battery goal: the
  background keeps running for the ramp's length after you stop, so it is ~55s
  from last input to parked. Parking is deferred, not skipped — the steady-state
  saving is unchanged, only how quickly it is reached.
- At zero the tick returns `False`, unregistering itself. That lets
  `_ensure_animation_timer` drop the frame timer back to the 10Hz idle rate,
  which is where the actual power saving comes from. The last frame stays on
  screen (a shader's layer keeps its drawable; a segment scene its last paint).
- `_dispatch` calls `_ensure_background_ticker` on every input, alongside the
  roll ticker's re-arm.

**The clock is the subtle part.** `_bg_clock` counts *animated* time — it advances
by `dt × eased_rate`, never wall clock. So a background parked for ten minutes
resumes exactly where it stopped rather than teleporting ten minutes into the
scene. Both renderers read `_bg_clock`; neither uses wall clock. `dt` is also
clamped to 0.25s so a stalled main thread resumes by continuing rather than
lurching.

`_smoothstep` and `_approach` are module-level pure functions specifically so the
ramp is exactly testable, and `tests/test_background_idle.py` drives the whole
park/resume lifecycle against a fake clock — no window, no waiting.

## The shader path

### Writing one

A shader scene is a single Metal fragment function named `puikit_bg_fragment`.
PuiKit prepends `SHADER_PRELUDE` — the uniform struct and a fullscreen-triangle
vertex stage — so app source is only that function and cannot break the pipeline:

```metal
fragment float4 puikit_bg_fragment(float4 pos [[position]],
                                   constant BackgroundUniforms &u [[buffer(0)]])
```

`u` carries `resolution` (pixels), `time` (seconds, already scaled by the theme's
speed), `opacity`, and the theme's `ink`/`backdrop` as RGBA. Honour `speed` via
`time` (so `speed=0` freezes, as the segment scenes do) and derive colour from
`ink` so the scene stays in the palette's family.

Add the scene to `SHADER_KINDS` with any scene-owned `Shader` fields. The dict is
splatted into `Shader(...)`, so a stray key is a `TypeError` at theme-apply time —
there is a test that constructs every entry.

### Compositing

A `CALayer` draws its sublayers *above* its own contents, so the GPU layer cannot
live inside the UI view — it has to be a sibling behind it. `open()` therefore puts
the UI view inside a container, and `_sync_shader_layer` inserts a `CAMetalLayer`
at index 0 of the container's layer. Everything reads `_view.bounds()` rather than
the content view, so no other call site is affected.

When a shader is active the render pass clears the UI view to **transparent**
(with `NSCompositingOperationCopy` — source-over would leave the previous frame),
so the layer behind shows through. Otherwise the clear is the opaque backdrop
exactly as before.

The layer is created lazily on first use, so an app that never sets a shader
creates no Metal objects, and a machine without Metal reports
`background_shader: False` and never gets there.

### It does not repaint the UI

The biggest cost of an animated background is not the scene — it is that a segment
scene lives inside the UI's render pass, so advancing it repaints the whole file
manager 60 times a second. Measured: the wave's own cost was 0.5ms/frame while the
repaint it triggered was 8.1ms.

A shader has its own layer behind the UI, so `_background_tick` draws straight into
that layer and never marks the view dirty. The UI then repaints only on real
change. Idle, that took the wave from ~52% of a core to ~4% — and left it roughly
7× cheaper than the CPU scenes despite being far denser.

This is why `_render_into_view` deliberately does *not* dispatch on `Shader`: the
only thing the UI pass owes a shader is the transparent clear.

### Cost

Per-pixel, so the tunables that matter are the per-pixel loop and the resolution:

- `LAYERS × 3 cells` is the wave's inner loop. Measured roughly linear in
  `LAYERS`; 12 is the current setting.
- Everything inside that loop is deliberately transcendental-free. The usual
  `fract(sin(n) * 43758.0)` hash and a gaussian `exp()` splat together cost more
  than the surface itself; they are an arithmetic hash and a squared clamped
  polynomial instead.
- `Shader.resolution_scale` renders below native and lets the compositor scale up.
  The wave uses `0.5` — a quarter of the pixels, invisible on diffuse grain, and
  the difference between affordable and not on a Retina display.

Measure with `tools/render_background_animations.py` plus a timing loop over
`MetalBackground.render_to_texture`, or in the real app with `PUIKIT_BG_PROFILE=1`.

### Verifying a shader

`MetalBackground` renders to an offscreen texture as readily as to a layer, so a
shader can be compiled, drawn and inspected with no window — which is what both
the tests and the render tool use:

```bash
PYTHONPATH=.:src python tools/render_background_animations.py --kind wave
```

## Tuning notes

These sit behind a working file manager, so every scene is tuned to stay a
backdrop: a star crosses in roughly eight seconds, a constellation node takes about
half a minute, and alphas top out well below full. `speed=1.0` is the tuned look;
themes typically ask for `0.6`.

Each scene's tunables are module-level constants with comments explaining what
breaks at the extremes — notably `_STAR_NEAR`, which must stay well above zero
because the perspective divide would otherwise fling a star to infinity.
