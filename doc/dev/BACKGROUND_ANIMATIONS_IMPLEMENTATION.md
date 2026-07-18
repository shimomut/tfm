# Background Animations Implementation

How TFM's animated backgrounds are defined, registered and drawn, and what to do
to add one. End-user documentation is in
[BACKGROUND_ANIMATIONS_FEATURE.md](../BACKGROUND_ANIMATIONS_FEATURE.md).

## Where the pieces live

| Concern | Location |
|---------|----------|
| The scenes themselves | `src/tfm_background_animations.py` (TFM) |
| Registry a scene is published into | `puikit.background.ANIMATIONS` (PuiKit) |
| Descriptor a theme resolves to | `puikit.background.Background3D` (PuiKit) |
| Theme → descriptor resolution | `_resolve_background` in `tfm.py` |
| Push to the backend on theme switch | `TfmApp._apply_background` in `tfm.py` |
| Stroking the segments | `MacOSBackend._render_animation` (PuiKit) |

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

## Tuning notes

These sit behind a working file manager, so every scene is tuned to stay a
backdrop: a star crosses in roughly eight seconds, a constellation node takes about
half a minute, and alphas top out well below full. `speed=1.0` is the tuned look;
themes typically ask for `0.6`.

Each scene's tunables are module-level constants with comments explaining what
breaks at the extremes — notably `_STAR_NEAR`, which must stay well above zero
because the perspective divide would otherwise fling a star to infinity.
