"""TFM's background animations — the scenes drawn behind the file panes.

A theme may name an ``animation`` (see ``_resolve_background`` in ``tfm.py``); the
GUI backend draws it under the whole display list, and a terminal has no sub-cell
pixels so it silently ignores the whole thing. PuiKit owns *how* a scene is
stroked; TFM owns *what* the scenes are. PuiKit ships only a wireframe cube — a
reference scene that exercises its projection path — and exposes
``puikit.background.ANIMATIONS`` as the registry an application extends. Every
production animation TFM offers is defined here and registered into it at import
(see :func:`register`), so adding one is a change to this file alone: no backend
change, no PuiKit change.

**The generator contract.** A scene is a *pure function* of
``(width, height, t, *, speed)`` returning the 2D line segments to stroke, in
pixels with a top-left origin. It is called once per frame with wall-clock ``t``
in seconds, which means all motion must be derived from ``t`` — a generator that
kept frame-to-frame state, or drew fresh randomness per call, would make every
particle jump each frame instead of travelling. Where a scene wants per-particle
variety it gets it from :func:`_rand`, a deterministic hash of the particle's
index: the same star is in the same place every time that ``t`` comes round.

A segment is ``(x0, y0, x1, y1)`` to stroke at the theme's own opacity, or
``(x0, y0, x1, y1, alpha)`` to scale it by a per-segment ``alpha``. That fifth
element is what carries *depth*: a far star is dim and a near one bright, a trail
fades along its length, a constellation edge fades in as two nodes approach.
Without it every line in a scene would be equally bright and the result reads
flat, so all four scenes here lean on it heavily.

A scene that needs *density or colour* rather than structure does not belong here
at all — per-segment stroking caps out around a few thousand segments and the whole
scene is drawn in one colour. Those are fragment shaders instead; see
``tfm_background_shaders``.

Three of the scenes compute screen coordinates straight from ``t``. The fourth,
the grid tunnel, is genuinely 3D — world points on the walls of a corridor, put
through a moving camera and projected — which is what lets its vanishing point
wander and its near geometry parallax against the far.

**Tuning.** These sit *behind a working file manager*, so every scene is tuned to
stay a backdrop: slow rates (a star crosses in ~8 seconds, a constellation node
takes about half a minute, the tunnel camera's sway cycles run 27–53 seconds), and
alphas that top out well below full so nothing competes with a filename for
attention. ``speed=1.0`` is the tuned look; a theme usually asks for less (TFM's
default is 0.6). The theme's foreground color is used for every line, so a scene is
always on-palette whatever the user's colors are.
"""

from __future__ import annotations

import math

from puikit.background import ANIMATIONS

_TAU = math.tau

#: How far off-view a segment may stray before it is culled rather than handed to
#: the backend. A whole streak just off the edge costs nothing to drop here.
_CULL_MARGIN = 24.0


def _rand(index: int, salt: int = 0) -> float:
    """A deterministic pseudo-random float in ``[0, 1)`` from an integer index.

    Stands in for ``random.random()``, which a frame generator must never call:
    the scene is recomputed from scratch every frame, so fresh randomness would
    re-roll every particle's position 60 times a second. Hashing the *index*
    instead gives each particle a fixed, arbitrary-looking constant — star 7 gets
    the same spawn point on every frame, and its motion comes from ``t`` alone.

    An integer avalanche hash (xorshift-multiply, in the spirit of splitmix): the
    ``salt`` distinguishes independent draws for the same particle, so
    ``_rand(i, 1)`` and ``_rand(i, 2)`` are uncorrelated x and y.
    """
    x = (index * 0x9E3779B1 + salt * 0x85EBCA77) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x2C1B3C6D) & 0xFFFFFFFF
    x ^= x >> 12
    x = (x * 0x297A2D39) & 0xFFFFFFFF
    x ^= x >> 15
    return x / 4294967296.0


def _on_view(x0: float, y0: float, x1: float, y1: float,
             width: float, height: float) -> bool:
    """True when a segment's bounding box overlaps the (margin-expanded) view."""
    m = _CULL_MARGIN
    if max(x0, x1) < -m or min(x0, x1) > width + m:
        return False
    if max(y0, y1) < -m or min(y0, y1) > height + m:
        return False
    return True


# --- starfield -----------------------------------------------------------------

#: Stars in flight at once. They are cheap (one segment each, most culled while
#: off-view), so the count buys density rather than cost.
_STAR_COUNT = 220
#: Fraction of the depth range a star crosses per second at ``speed=1.0`` — 0.12
#: is a little over eight seconds from spawn to camera, a drift rather than a jump
#: to hyperspace.
_STAR_RATE = 0.12
#: The depth a star spawns at. Above 1 on purpose: the plane is scaled by the
#: view's half-size, so a star at depth 1 would project exactly to the view edge
#: and the field would spawn already covering the whole window — stars would drift
#: outward from everywhere instead of streaming out of a vanishing point. Spawning
#: at 2.6 confines the far plane to the middle ~38% of the view, which is what
#: makes the effect read as flying forward.
_STAR_FAR = 2.6
#: Nearest depth a star reaches before respawning. Must stay well above zero: the
#: projection divides by it, so a star at z→0 would fling off to infinity.
_STAR_NEAR = 0.16
#: Depth offset of a streak's tail behind its head. Constant in *depth*, which
#: makes the drawn streak lengthen as the star nears — the motion blur of
#: something passing faster.
_STAR_TAIL = 0.055
#: Depth fraction at which a star reaches full brightness (it fades in from the
#: far plane over the first stretch of its travel, so nothing pops into being).
_STAR_FADE_IN = 0.55


def starfield_segments(width: float, height: float, t: float, *,
                       speed: float = 1.0) -> list[tuple]:
    """Stars streaming toward the viewer, drawn as radial motion streaks.

    Each star holds a fixed position on a plane in front of the camera and travels
    only in depth; the perspective divide does the rest, sweeping it outward from
    the centre and accelerating it as it nears. Brightness tracks depth, so the
    field reads three-dimensional rather than as scattered dots — the point of the
    per-segment alpha.

    The plane is scaled by the view's own half-width and half-height rather than a
    single radius, so the field fills the viewport on both axes as it opens out —
    no empty vertical bands in a wide window.
    """
    if width <= 0 or height <= 0:
        return []
    cx, cy = width * 0.5, height * 0.5
    hw, hh = cx, cy
    depth_span = _STAR_FAR - _STAR_NEAR
    segments: list[tuple] = []
    for i in range(_STAR_COUNT):
        # Fixed spawn point on the plane; a star that would sit dead centre is
        # nudged out, since one exactly on the axis never appears to move.
        sx = _rand(i, 1) * 2.0 - 1.0
        sy = _rand(i, 2) * 2.0 - 1.0
        if -0.02 < sx < 0.02 and -0.02 < sy < 0.02:
            sx += 0.05
        # Depth cycles _STAR_FAR → _STAR_NEAR, each star offset by its own phase so
        # they do not arrive in lockstep. Wrapping the phase respawns it at the far
        # plane, where its alpha is 0 — so the reset is never visible.
        phase = (t * speed * _STAR_RATE + _rand(i, 3)) % 1.0
        z = _STAR_FAR - phase * depth_span
        z_tail = min(_STAR_FAR, z + _STAR_TAIL)
        x0, y0 = cx + sx * hw / z, cy + sy * hh / z
        x1, y1 = cx + sx * hw / z_tail, cy + sy * hh / z_tail
        if not _on_view(x0, y0, x1, y1, width, height):
            continue
        travelled = phase  # 0 at the far plane, 1 at closest approach
        alpha = min(1.0, travelled / _STAR_FADE_IN)
        segments.append((x0, y0, x1, y1, alpha))
    return segments


# --- rain / phosphor streaks ---------------------------------------------------

#: Nominal column width in pixels; the column count follows the window so the
#: fall stays the same density whether the window is narrow or full-screen.
_RAIN_COLUMN_PX = 26.0
#: Fraction of a full fall covered per second at ``speed=1.0``, before each
#: column's own multiplier.
_RAIN_RATE = 0.16
#: Sub-segments per streak. The tail's fade is what makes it read as a trail
#: rather than a stick, and each step is one alpha level.
_RAIN_TAIL_STEPS = 7
#: Streaks per column, evenly offset in phase, so a column is never empty for
#: long without needing twice the columns.
_RAIN_DROPS_PER_COLUMN = 2
#: Streak length as a fraction of view height: the shortest and the extra range.
_RAIN_LEN_MIN, _RAIN_LEN_RANGE = 0.10, 0.22


def rain_segments(width: float, height: float, t: float, *,
                  speed: float = 1.0) -> list[tuple]:
    """Falling streaks with fading tails — the phosphor-terminal rain.

    Each column gets its own fall speed, length and phase from its index, so the
    field never pulses in unison. A streak is emitted as a short stack of
    sub-segments whose alpha decays from the bright head to nothing at the tail;
    that per-segment falloff is the whole effect, since a uniformly-stroked streak
    would just be a line.
    """
    if width <= 0 or height <= 0:
        return []
    columns = max(6, int(width / _RAIN_COLUMN_PX))
    col_w = width / columns
    segments: list[tuple] = []
    for c in range(columns):
        # Jitter the x within the column so the fall is not a perfect comb.
        x = (c + 0.15 + _rand(c, 1) * 0.7) * col_w
        fall = 0.55 + _rand(c, 2) * 1.0           # per-column speed multiplier
        length = (_RAIN_LEN_MIN + _RAIN_LEN_RANGE * _rand(c, 3)) * height
        bright = 0.45 + _rand(c, 6) * 0.55        # some columns stay faint
        for d in range(_RAIN_DROPS_PER_COLUMN):
            phase = _rand(c, 4 + d)
            # Travel 0→1 walks the head from just above the view to the bottom
            # edge, so a streak enters already fully formed rather than growing
            # out of the top edge.
            travel = (t * speed * _RAIN_RATE * fall + phase) % 1.0
            head = travel * (height + length) - length
            for k in range(_RAIN_TAIL_STEPS):
                y0 = head - length * (k / _RAIN_TAIL_STEPS)
                y1 = head - length * ((k + 1) / _RAIN_TAIL_STEPS)
                if y0 < -_CULL_MARGIN or y1 > height + _CULL_MARGIN:
                    continue
                # Falls off toward the tail; the exponent keeps the head crisp and
                # the tail long and faint rather than a linear ramp.
                alpha = (1.0 - k / _RAIN_TAIL_STEPS) ** 1.7 * bright
                segments.append((x, y0, x, y1, alpha))
    return segments


# --- constellation network -----------------------------------------------------

#: Drifting nodes. Edge testing is O(n²), so this stays modest — 38 nodes is ~700
#: pair tests a frame, trivial next to the stroking.
_NODE_COUNT = 38
#: Link radius as a fraction of the view's shorter side. Measured in pixels (not
#: normalized units) so the neighbourhood stays circular in a non-square window.
_LINK_FRACTION = 0.24
#: Node drift in view-widths per second at ``speed=1.0`` — a node crosses in about
#: half a minute, slow enough to read as calm.
_DRIFT_RATE = 0.035
#: Fraction of the view over which a node fades out as it reaches the border. The
#: field wraps, and this is what hides the wrap: a node is fully transparent by the
#: time it crosses, so it dissolves at one edge and resolves at the other instead
#: of teleporting with its edges snapping.
_EDGE_FADE = 0.10
#: Half-length of a node's dot, in pixels (drawn as a minimal segment).
_NODE_DOT = 1.1
#: Ceiling on an edge's alpha, and a node's own. Edges stay clearly secondary to
#: the nodes they connect.
_EDGE_ALPHA, _NODE_ALPHA = 0.5, 0.85


def _border_fade(u: float) -> float:
    """Fade factor for a normalized coordinate — 0 at the border, ramping to 1
    once ``_EDGE_FADE`` into the view."""
    return min(1.0, min(u, 1.0 - u) / _EDGE_FADE)


def constellation_segments(width: float, height: float, t: float, *,
                           speed: float = 1.0) -> list[tuple]:
    """Drifting nodes linked to their near neighbours, edges fading with distance.

    Nodes travel in straight lines and wrap at the borders, which spreads them
    evenly over the view: a node's position is uniform in time, so at any moment
    the field covers the window. (Sinusoidal paths, the obvious way to confine a
    node without wrapping, do the opposite — a sine dwells near its turning points,
    so nodes pile up along the edges and leave the middle bare.)

    Wrapping alone would teleport a node across the view with every edge it holds
    snapping at once, so each node's alpha is faded out toward the border: it
    dissolves as it leaves and resolves as it re-enters, and the crossing is never
    visible. Each edge's alpha carries both endpoints' fades as well as a falloff
    with distance, so links dissolve as nodes part instead of blinking out at the
    radius.
    """
    if width <= 0 or height <= 0:
        return []
    link = _LINK_FRACTION * min(width, height)
    points: list[tuple[float, float, float]] = []  # (x, y, fade)
    for i in range(_NODE_COUNT):
        # A uniform heading, so the field drifts in every direction rather than
        # sharing one diagonal; the per-node multiplier keeps them out of step.
        angle = _rand(i, 3) * _TAU
        rate = _DRIFT_RATE * (0.6 + _rand(i, 6) * 0.8) * t * speed
        px = (_rand(i, 1) + math.cos(angle) * rate) % 1.0
        py = (_rand(i, 2) + math.sin(angle) * rate) % 1.0
        points.append((px * width, py * height,
                       _border_fade(px) * _border_fade(py)))

    segments: list[tuple] = []
    for i in range(_NODE_COUNT):
        x0, y0, f0 = points[i]
        if f0 <= 0.0:
            continue
        for j in range(i + 1, _NODE_COUNT):
            x1, y1, f1 = points[j]
            if f1 <= 0.0:
                continue
            d = math.hypot(x1 - x0, y1 - y0)
            if d >= link:
                continue
            alpha = (1.0 - d / link) ** 1.6 * _EDGE_ALPHA * f0 * f1
            segments.append((x0, y0, x1, y1, alpha))
    # Nodes last so a dot is never buried under the edges meeting at it.
    for x, y, fade in points:
        if fade > 0.0:
            segments.append((x - _NODE_DOT, y, x + _NODE_DOT, y, _NODE_ALPHA * fade))
    return segments


# --- grid tunnel ---------------------------------------------------------------

#: World-space distance between rings (the rectangular cross-sections that band
#: the corridor). Also the depth subdivision of the rails, so grid cells align.
_TUNNEL_RING_SPACING = 0.5
#: Depth window actually drawn. ``NEAR`` is deliberately close: a ring there
#: projects far outside the view (the corridor is around the camera at that point),
#: so a ring leaving the window is never seen to vanish. ``FAR`` is where the fade
#: has reached zero, so the tunnel ends in darkness rather than a cut-off.
_TUNNEL_NEAR, _TUNNEL_FAR = 0.28, 9.0
#: Depths below this are treated as behind the camera and dropped — guards the
#: perspective divide when a pitched/yawed camera swings a near corner backward.
_TUNNEL_MIN_DEPTH = 0.05
#: Rails (longitudinal lines) across the side walls; the floor/ceiling count is
#: derived from the corridor's aspect so the cells stay roughly square, capped so a
#: very wide window does not multiply the segment count without bound.
_TUNNEL_RAILS_V = 5
_TUNNEL_RAILS_H_MAX = 12
#: Corridor half-height in world units. The half-width is derived from the view
#: aspect, so at depth 1 the cross-section maps exactly onto the viewport.
_TUNNEL_HALF_H = 1.0
#: Forward travel in world units per second at ``speed=1.0`` — a ring passes about
#: every 1.4s, roughly every 2.4s at TFM's default 0.6.
_TUNNEL_FORWARD = 0.35
#: Depth-fade exponent. Above 1 holds the near/middle distance bright and pushes
#: the falloff toward the vanishing point, which is what gives the corridor its
#: sense of length.
_TUNNEL_FADE_GAMMA = 1.2

#: Camera sway: lateral/vertical drift in world units, and yaw/pitch in radians
#: (~6° and ~4°). The drift stays well inside the corridor so the camera never
#: clips a wall, and the angles stay small so the vanishing point wanders without
#: the walls ever swinging out of frame.
_CAM_DRIFT_X, _CAM_DRIFT_Y = 0.30, 0.18
_CAM_YAW, _CAM_PITCH = 0.10, 0.07
#: Sway rates in cycles per second (x, y, yaw, pitch). Deliberately mutually
#: incommensurate — periods of about 27s, 34s, 43s and 53s — so the four never
#: come back into phase and the motion does not read as a loop.
_CAM_RATES = (0.037, 0.029, 0.023, 0.019)


def _camera(t: float, speed: float) -> tuple[float, float, float, float, float]:
    """Camera state at time ``t`` — ``(x, y, yaw, pitch, z)``.

    Position and angle both sway on slow sines while the camera travels forward at
    a constant rate. Split out from the scene so the motion can be reasoned about
    (and tested) on its own: everything is a function of ``t * speed``, so
    ``speed=0`` freezes the camera along with the rest of the scene.
    """
    ct = t * speed
    rx, ry, ryaw, rpitch = _CAM_RATES
    return (
        _CAM_DRIFT_X * math.sin(ct * rx * _TAU),
        _CAM_DRIFT_Y * math.sin(ct * ry * _TAU + 1.7),
        _CAM_YAW * math.sin(ct * ryaw * _TAU + 0.6),
        _CAM_PITCH * math.sin(ct * rpitch * _TAU + 2.4),
        ct * _TUNNEL_FORWARD,
    )


def _tunnel_depth_alpha(depth: float) -> float:
    """Fade for geometry at ``depth`` — full near the camera, zero at the far
    plane, so the corridor recedes into darkness instead of ending abruptly."""
    u = (_TUNNEL_FAR - depth) / (_TUNNEL_FAR - _TUNNEL_NEAR)
    return max(0.0, min(1.0, u)) ** _TUNNEL_FADE_GAMMA


def grid_tunnel_segments(width: float, height: float, t: float, *,
                         speed: float = 1.0) -> list[tuple]:
    """A rectangular grid corridor with the camera flying through it.

    Unlike the other three scenes, this one is genuinely 3D: world points are
    placed on the four walls of a corridor running down +z, then transformed by a
    moving camera and projected. That is what buys the effect — the walls converge
    on a vanishing point that *moves* as the camera yaws and pitches, and the
    near geometry parallaxes against the far as it drifts, neither of which can be
    faked by scrolling a fixed fan of lines.

    The corridor's half-width is derived from the view aspect so that at depth 1
    its cross-section maps exactly onto the viewport: nearer than that the camera
    is inside it and the walls run off every edge, further away they close toward
    the centre.

    Two families of lines: **rings**, the rectangular cross-sections banding the
    corridor at a fixed world spacing, and **rails**, the longitudinal lines
    running along the walls. Rails are subdivided at exactly the ring depths, so
    the two families meet and the cells line up. Both fade with depth.

    Rings live at fixed world positions and are selected by depth window rather
    than scrolled, so the recycling is seamless by construction: as the camera
    advances, a ring leaves the near end of the window only once it is far outside
    the view, and a new one enters at the far end where the fade has it at zero.
    """
    if width <= 0 or height <= 0:
        return []
    cx, cy = width * 0.5, height * 0.5
    focal = height * 0.5
    half_h = _TUNNEL_HALF_H
    half_w = half_h * (width / height)

    cam_x, cam_y, yaw, pitch, cam_z = _camera(t, speed)
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    cos_p, sin_p = math.cos(pitch), math.sin(pitch)

    def project(wx: float, wy: float, depth: float):
        """World point on a wall → screen point, or ``None`` if behind the camera."""
        dx, dy = wx - cam_x, wy - cam_y
        # Yaw about the vertical axis, then pitch about the horizontal one.
        x1 = dx * cos_y - depth * sin_y
        z1 = dx * sin_y + depth * cos_y
        y2 = dy * cos_p - z1 * sin_p
        z2 = dy * sin_p + z1 * cos_p
        if z2 < _TUNNEL_MIN_DEPTH:
            return None
        return cx + focal * x1 / z2, cy + focal * y2 / z2

    # Rings sit at world z = k * spacing. Expressed relative to the moving camera
    # that is spacing * (k - frac), and taking every k whose depth falls in the
    # window gives a set that slides forward continuously and recycles at the ends.
    frac = (cam_z / _TUNNEL_RING_SPACING) % 1.0
    k0 = math.ceil(_TUNNEL_NEAR / _TUNNEL_RING_SPACING + frac)
    k1 = math.floor(_TUNNEL_FAR / _TUNNEL_RING_SPACING + frac)
    depths = [_TUNNEL_RING_SPACING * (k - frac) for k in range(k0, k1 + 1)]
    if not depths:
        return []

    rails_v = _TUNNEL_RAILS_V
    rails_h = max(2, min(_TUNNEL_RAILS_H_MAX,
                         round(rails_v * half_w / half_h)))
    step_h = 2.0 * half_w / rails_h
    step_v = 2.0 * half_h / rails_v

    segments: list[tuple] = []

    # Rings: the four corners projected once each, joined into a rectangle. A ring
    # is at constant depth, so its alpha is constant and it needs no subdivision.
    for depth in depths:
        alpha = _tunnel_depth_alpha(depth)
        if alpha <= 0.0:
            continue
        corners = [project(sx * half_w, sy * half_h, depth)
                   for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for a in range(4):
            p0, p1 = corners[a], corners[(a + 1) % 4]
            if p0 is None or p1 is None:
                continue
            if not _on_view(p0[0], p0[1], p1[0], p1[1], width, height):
                continue
            segments.append((p0[0], p0[1], p1[0], p1[1], alpha))

    # Rails: one lane per grid line on each wall. Floor and ceiling carry the
    # lanes across the width; the side walls carry those up the height, skipping
    # the ones at the corners since the floor/ceiling lanes already drew them.
    lanes: list[tuple[float, float]] = []
    for i in range(rails_h + 1):
        wx = -half_w + i * step_h
        lanes.append((wx, -half_h))   # ceiling
        lanes.append((wx, half_h))    # floor
    for j in range(1, rails_v):
        wy = -half_h + j * step_v
        lanes.append((-half_w, wy))   # left wall
        lanes.append((half_w, wy))    # right wall

    for wx, wy in lanes:
        prev = project(wx, wy, depths[0])
        for depth in depths[1:]:
            point = project(wx, wy, depth)
            if prev is not None and point is not None:
                alpha = _tunnel_depth_alpha(depth)
                if alpha > 0.0 and _on_view(prev[0], prev[1], point[0], point[1],
                                            width, height):
                    segments.append((prev[0], prev[1], point[0], point[1], alpha))
            prev = point
    return segments


#: The animation type names TFM offers, mapped to their generators. A theme's
#: ``animation`` key names one of these (``'starfield'``, ``'rain'``, ...); PuiKit's
#: own ``'cube'`` / ``'wireframe'`` stay registered on its side and remain valid.
ANIMATION_KINDS: dict[str, object] = {
    "starfield": starfield_segments,
    "rain": rain_segments,
    "constellation": constellation_segments,
    "grid": grid_tunnel_segments,
}


def register() -> None:
    """Publish TFM's animations into PuiKit's registry so themes can name them.

    Called at import (below), which is all the wiring there is: ``tfm.py`` imports
    this module, ``Background3D(kind=...)`` then resolves any of these names, and
    the GUI backend looks the generator up per frame. Idempotent — re-importing or
    calling again just rebinds the same functions.
    """
    ANIMATIONS.update(ANIMATION_KINDS)


register()
