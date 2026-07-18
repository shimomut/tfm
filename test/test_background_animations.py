"""TFM's background animation generators — registration, the frame contract, and
each scene's defining behavior.

These run headless: a generator is a pure function of (width, height, t, speed)
returning line segments, so every property below is checked without a window, a
backend, or any native framework.

Run with: PYTHONPATH=.:src pytest test/test_background_animations.py -v
"""

import math
import unittest

from puikit.background import ANIMATIONS, group_by_alpha

import tfm_background_animations as anim
from tfm_background_animations import (
    ANIMATION_KINDS, constellation_segments, grid_tunnel_segments,
    rain_segments, starfield_segments, _camera, _rand, _tunnel_depth_alpha,
)

#: Every generator TFM registers, exercised by the shared contract tests below.
_ALL = list(ANIMATION_KINDS.items())

#: A few view sizes covering square, tall and very wide windows.
_SIZES = ((1200, 800), (600, 900), (1920, 400))


class Registration(unittest.TestCase):
    """The scenes are published into puikit's registry, which is the whole of the
    wiring — a theme naming one of these types resolves to the generator here."""

    def test_all_kinds_are_registered(self):
        for kind, generator in ANIMATION_KINDS.items():
            self.assertIs(ANIMATIONS[kind], generator, kind)

    def test_expected_kinds_are_offered(self):
        self.assertEqual(set(ANIMATION_KINDS),
                         {"starfield", "rain", "constellation", "grid"})

    def test_register_is_idempotent(self):
        anim.register()
        anim.register()
        self.assertIs(ANIMATIONS["starfield"], starfield_segments)

    def test_puikits_own_cube_still_resolves(self):
        # Registering TFM's scenes must not displace the toolkit's reference one.
        self.assertIn("cube", ANIMATIONS)


class SegmentContract(unittest.TestCase):
    """Properties every generator must satisfy to be safe to hand a backend."""

    def test_segments_are_four_or_five_tuples(self):
        for kind, gen in _ALL:
            for seg in gen(1200, 800, 2.5):
                self.assertIn(len(seg), (4, 5), f"{kind}: {seg}")

    def test_all_coordinates_are_finite(self):
        # A perspective divide by a near-zero depth would produce inf/nan and
        # poison the path; every scene must keep its divisor bounded away from 0.
        for kind, gen in _ALL:
            for t in (0.0, 0.37, 4.2, 60.0, 3600.0):
                for seg in gen(1200, 800, t, speed=1.3):
                    for v in seg:
                        self.assertTrue(math.isfinite(v), f"{kind} t={t}: {seg}")

    def test_alphas_are_within_unit_range(self):
        for kind, gen in _ALL:
            for t in (0.0, 1.1, 9.7):
                for seg in gen(1200, 800, t):
                    if len(seg) > 4:
                        self.assertGreaterEqual(seg[4], 0.0, kind)
                        self.assertLessEqual(seg[4], 1.0, kind)

    def test_degenerate_views_yield_nothing(self):
        for kind, gen in _ALL:
            self.assertEqual(gen(0, 800, 1.0), [], kind)
            self.assertEqual(gen(1200, 0, 1.0), [], kind)
            self.assertEqual(gen(-10, -10, 1.0), [], kind)

    def test_every_size_produces_a_scene(self):
        for kind, gen in _ALL:
            for w, h in _SIZES:
                self.assertTrue(gen(w, h, 3.0), f"{kind} at {w}x{h} drew nothing")

    def test_generators_are_pure(self):
        # The frame is recomputed from scratch every tick, so the same inputs must
        # give the same scene. A generator that drew fresh randomness (rather than
        # hashing a particle index) would fail here — and would visibly jitter.
        for kind, gen in _ALL:
            self.assertEqual(gen(1200, 800, 2.5), gen(1200, 800, 2.5), kind)

    def test_scenes_animate(self):
        for kind, gen in _ALL:
            self.assertNotEqual(gen(1200, 800, 0.0), gen(1200, 800, 2.0), kind)

    def test_speed_zero_is_static(self):
        for kind, gen in _ALL:
            self.assertEqual(gen(1200, 800, 0.0, speed=0.0),
                             gen(1200, 800, 90.0, speed=0.0), kind)

    def test_visible_motion_is_continuous(self):
        # Nothing the eye can follow may jump between frames. A scene is allowed to
        # recycle a particle by wrapping or respawning it, but only where it is
        # already transparent — so the invariant is over *visible* segments, and a
        # scene that teleported something in plain sight would fail here. Compare
        # the mean visible midpoint frame to frame; an outlier would move it.
        for kind, gen in _ALL:
            prev = None
            for step in range(24):
                segs = [s for s in gen(1200, 800, step * (1.0 / 30.0))
                        if len(s) == 4 or s[4] >= 0.05]
                self.assertTrue(segs, kind)
                mid = (sum((s[0] + s[2]) * 0.5 for s in segs) / len(segs),
                       sum((s[1] + s[3]) * 0.5 for s in segs) / len(segs))
                if prev is not None:
                    self.assertLess(math.dist(prev, mid), 40.0,
                                    f"{kind} jumped between frames")
                prev = mid

    def test_stroke_cost_stays_bounded(self):
        # Per-segment alpha is quantized into buckets and the backend strokes one
        # path per bucket, so a smoothly-shaded scene must not cost a path per
        # segment. Guards the reason quantization exists.
        for kind, gen in _ALL:
            segs = gen(1920, 1080, 5.0)
            self.assertLessEqual(len(group_by_alpha(segs)), 64, kind)

    def test_scenes_use_per_segment_alpha(self):
        # The point of these over the reference cube: depth/fade rather than a
        # flat uniform stroke. Each must emit more than one distinct alpha.
        for kind, gen in _ALL:
            buckets = group_by_alpha(gen(1200, 800, 4.0))
            self.assertGreater(len(buckets), 1, f"{kind} is uniformly stroked")

    def test_segments_stay_near_the_view(self):
        # Off-view work is culled rather than handed to the backend; a stray
        # segment far outside the bounds means a cull was missed.
        for kind, gen in _ALL:
            for w, h in _SIZES:
                for seg in gen(w, h, 3.3):
                    self.assertGreater(max(seg[0], seg[2]), -w, kind)
                    self.assertLess(min(seg[0], seg[2]), w * 2, kind)
                    self.assertGreater(max(seg[1], seg[3]), -h, kind)
                    self.assertLess(min(seg[1], seg[3]), h * 2, kind)


class DeterministicRandom(unittest.TestCase):
    """The hash that stands in for per-particle randomness."""

    def test_is_a_unit_float(self):
        for i in range(500):
            self.assertGreaterEqual(_rand(i), 0.0)
            self.assertLess(_rand(i), 1.0)

    def test_is_stable(self):
        self.assertEqual(_rand(7, 3), _rand(7, 3))

    def test_salts_are_uncorrelated(self):
        # x and y draws for the same particle must not track each other, or every
        # particle would sit on the diagonal.
        xs = [_rand(i, 1) for i in range(400)]
        ys = [_rand(i, 2) for i in range(400)]
        self.assertNotEqual(xs, ys)
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
        self.assertLess(abs(cov), 0.02)

    def test_is_roughly_uniform(self):
        # Particles must spread over the view, not clump into a corner.
        buckets = [0] * 10
        for i in range(2000):
            buckets[min(9, int(_rand(i, 5) * 10))] += 1
        for count in buckets:
            self.assertGreater(count, 100)


class Starfield(unittest.TestCase):

    def test_streaks_point_away_from_the_centre(self):
        # Each star travels only in depth, so perspective sweeps it radially
        # outward: the tail (further away) must sit nearer the centre than the head.
        w, h = 1200, 800
        cx, cy = w / 2, h / 2
        for seg in starfield_segments(w, h, 3.0):
            head = math.dist((seg[0], seg[1]), (cx, cy))
            tail = math.dist((seg[2], seg[3]), (cx, cy))
            self.assertGreaterEqual(head, tail - 1e-9)

    def test_stars_brighten_as_they_approach(self):
        # Alpha must track depth, so the field reads as 3D rather than as scattered
        # dots at one brightness. Streak length is the honest proxy for depth here:
        # it grows as the perspective divide accelerates the star. (Distance from
        # the centre is not — it mixes depth with the star's own offset on the
        # plane, so an edge-of-plane star reads "near" while still far away.)
        segs = starfield_segments(1200, 800, 3.0)
        by_length = sorted(segs, key=lambda s: math.dist((s[0], s[1]), (s[2], s[3])))
        third = max(1, len(by_length) // 3)
        shortest = [s[4] for s in by_length[:third]]
        longest = [s[4] for s in by_length[-third:]]
        self.assertGreater(sum(longest) / len(longest),
                           sum(shortest) / len(shortest))

    def test_stars_stream_out_of_a_vanishing_point(self):
        # The far plane must project *inside* the view, not fill it: stars have to
        # emerge from a central point and open outward. If the spawn plane covered
        # the whole window they would simply drift apart from everywhere.
        w, h = 1200, 800
        cx, cy = w / 2, h / 2
        segs = starfield_segments(w, h, 3.0)
        nearest = min(math.dist((s[0], s[1]), (cx, cy)) for s in segs)
        self.assertLess(nearest, min(w, h) * 0.25)

    def test_stars_fade_in_rather_than_popping(self):
        # A star respawns at the far plane, where it must be invisible — otherwise
        # the reset flashes. Some segment should always be near-transparent.
        self.assertLess(min(s[4] for s in starfield_segments(1200, 800, 5.0)), 0.1)

    def test_field_spans_the_view_on_both_axes(self):
        # Scaling by half-width and half-height (not one radius) is what keeps a
        # wide window from showing a narrow central band of stars.
        segs = starfield_segments(1920, 500, 4.0)
        xs = [s[0] for s in segs]
        self.assertLess(min(xs), 1920 * 0.25)
        self.assertGreater(max(xs), 1920 * 0.75)


class Rain(unittest.TestCase):

    def test_streaks_are_vertical(self):
        for seg in rain_segments(1200, 800, 2.0):
            self.assertEqual(seg[0], seg[2])

    def test_tails_fade_from_the_head(self):
        # Within one streak (one x), alpha must fall off along its length — the
        # falloff is what makes it a trail rather than a stick.
        segs = rain_segments(1200, 800, 2.0)
        column = [s for s in segs if s[0] == segs[0][0]]
        by_depth = sorted(column, key=lambda s: -max(s[1], s[3]))  # head first
        alphas = [s[4] for s in by_depth]
        self.assertGreater(alphas[0], alphas[-1])

    def test_density_follows_the_window_width(self):
        narrow = {s[0] for s in rain_segments(400, 800, 1.0)}
        wide = {s[0] for s in rain_segments(1600, 800, 1.0)}
        self.assertGreater(len(wide), len(narrow))

    def test_columns_fall_out_of_step(self):
        # Per-column speed and phase; if they moved in unison the field would
        # pulse. Distinct heads across columns proves they do not.
        segs = rain_segments(1200, 800, 3.0)
        heads = {}
        for s in segs:
            heads[s[0]] = max(heads.get(s[0], -1e9), s[1], s[3])
        self.assertGreater(len(set(round(v, 3) for v in heads.values())), 4)


class Constellation(unittest.TestCase):

    @staticmethod
    def _split(segments):
        """Separate node dots from edges. A dot is the minimal horizontal segment
        the scene draws for a node; anything else joins two nodes. (Alpha can no
        longer tell them apart — a dot's alpha carries its border fade.)"""
        dots, edges = [], []
        for s in segments:
            is_dot = s[1] == s[3] and abs((s[2] - s[0]) - 2 * anim._NODE_DOT) < 1e-9
            (dots if is_dot else edges).append(s)
        return dots, edges

    def test_nodes_are_drawn_as_dots(self):
        dots, _ = self._split(constellation_segments(1200, 800, 2.0))
        self.assertTrue(dots)
        self.assertLessEqual(len(dots), anim._NODE_COUNT)

    def test_nodes_fade_out_toward_the_border(self):
        # The wrap is hidden by fading a node as it nears the edge; verify the fade
        # law directly, since it is what keeps a crossing invisible.
        w, h = 1200, 800
        dots, _ = self._split(constellation_segments(w, h, 2.0))
        for s in dots:
            u, v = ((s[0] + s[2]) * 0.5) / w, s[1] / h
            expected = anim._NODE_ALPHA * anim._border_fade(u) * anim._border_fade(v)
            self.assertAlmostEqual(s[4], expected, places=9)
        # And the fade is actually exercised: some node is mid-crossing.
        self.assertLess(min(s[4] for s in dots), anim._NODE_ALPHA)

    def test_nodes_cover_the_whole_view(self):
        # Linear drift keeps the field uniform. Sinusoidal paths (the tempting way
        # to avoid a wrap) dwell at their turning points and pile nodes up along
        # the edges, leaving the middle bare — this is the regression guard.
        w, h = 1200, 800
        seen = set()
        for t in (0.0, 7.0, 19.0, 33.0):
            dots, _ = self._split(constellation_segments(w, h, t))
            for s in dots:
                seen.add((min(2, int(((s[0] + s[2]) * 0.5) / w * 3)),
                          min(2, int(s[1] / h * 3))))
        self.assertEqual(len(seen), 9, "nodes never reach some thirds of the view")

    def test_edges_stay_within_their_alpha_ceiling(self):
        _, edges = self._split(constellation_segments(1200, 800, 2.0))
        self.assertTrue(edges)
        for seg in edges:
            self.assertLessEqual(seg[4], anim._EDGE_ALPHA + 1e-9)

    def test_edges_fade_with_distance(self):
        # Sampled across frames: a single frame's longest edge can outshine a short
        # one if the short one's nodes happen to be mid-fade at the border.
        edges = []
        for t in (0.0, 3.0, 11.0, 27.0):
            edges += self._split(constellation_segments(1200, 800, t))[1]
        by_length = sorted(edges, key=lambda s: math.dist((s[0], s[1]), (s[2], s[3])))
        quarter = max(1, len(by_length) // 4)
        short = [s[4] for s in by_length[:quarter]]
        long_ = [s[4] for s in by_length[-quarter:]]
        self.assertGreater(sum(short) / len(short), sum(long_) / len(long_))

    def test_edges_respect_the_link_radius(self):
        w, h = 1200, 800
        link = anim._LINK_FRACTION * min(w, h)
        _, edges = self._split(constellation_segments(w, h, 2.0))
        for seg in edges:
            self.assertLess(math.dist((seg[0], seg[1]), (seg[2], seg[3])), link)

    def test_nodes_stay_inside_the_view(self):
        # Wrapped coordinates, so a node is always on-view — nothing to cull.
        w, h = 1200, 800
        for t in (0.0, 5.0, 50.0, 500.0):
            for seg in constellation_segments(w, h, t):
                self.assertTrue(0 <= seg[1] <= h)
                self.assertTrue(0 <= seg[3] <= h)


class GridTunnel(unittest.TestCase):
    """The corridor scene and the camera flying through it."""

    W, H = 1200, 800

    def _segs(self, t=2.0, w=None, h=None):
        return grid_tunnel_segments(w or self.W, h or self.H, t)

    def _far_point(self, t):
        """Approximate the vanishing point as the centroid of the dimmest tenth of
        the scene — those are the farthest segments, which cluster around it."""
        segs = sorted(self._segs(t), key=lambda s: s[4])
        far = segs[:max(1, len(segs) // 10)]
        return (sum((s[0] + s[2]) * 0.5 for s in far) / len(far),
                sum((s[1] + s[3]) * 0.5 for s in far) / len(far))

    def test_corridor_surrounds_the_camera(self):
        # The camera is *inside* the tunnel, so near geometry must run off all four
        # edges. A scene only reaching, say, the bottom would be a ground plane.
        segs = self._segs()
        self.assertLess(min(min(s[0], s[2]) for s in segs), self.W * 0.1)
        self.assertGreater(max(max(s[0], s[2]) for s in segs), self.W * 0.9)
        self.assertLess(min(min(s[1], s[3]) for s in segs), self.H * 0.1)
        self.assertGreater(max(max(s[1], s[3]) for s in segs), self.H * 0.9)

    def test_walls_converge_toward_a_vanishing_point(self):
        # The far end must close to a small region rather than staying full width;
        # that convergence is the whole perspective.
        segs = self._segs()
        far = sorted(segs, key=lambda s: s[4])[:max(1, len(segs) // 10)]
        spread_x = max(max(s[0], s[2]) for s in far) - min(min(s[0], s[2]) for s in far)
        self.assertLess(spread_x, self.W * 0.5)

    def test_depth_fade_is_monotonic(self):
        alphas = [_tunnel_depth_alpha(d) for d in (0.3, 1.0, 3.0, 6.0, 9.0)]
        self.assertEqual(alphas, sorted(alphas, reverse=True))
        self.assertAlmostEqual(alphas[-1], 0.0)
        self.assertGreater(alphas[0], 0.9)

    def test_far_geometry_is_dimmer_than_near(self):
        # Within a frame: segments near the vanishing point must be faint.
        vx, vy = self._far_point(2.0)
        segs = self._segs()
        near = [s for s in segs
                if math.dist(((s[0] + s[2]) * 0.5, (s[1] + s[3]) * 0.5), (vx, vy))
                > min(self.W, self.H) * 0.4]
        far = [s for s in segs
               if math.dist(((s[0] + s[2]) * 0.5, (s[1] + s[3]) * 0.5), (vx, vy))
               < min(self.W, self.H) * 0.1]
        self.assertTrue(near and far)
        self.assertGreater(sum(s[4] for s in near) / len(near),
                           sum(s[4] for s in far) / len(far))

    def test_camera_stays_inside_the_corridor(self):
        # Drift must never reach a wall, or the view would clip through one. The
        # corridor half-height is the tight bound (the half-width follows the view
        # aspect and is always at least as large).
        for step in range(400):
            x, y, yaw, pitch, _z = _camera(step * 0.9, 1.0)
            self.assertLess(abs(x), anim._CAM_DRIFT_X + 1e-9)
            self.assertLess(abs(y), anim._TUNNEL_HALF_H * 0.5)
            self.assertLess(abs(yaw), anim._CAM_YAW + 1e-9)
            self.assertLess(abs(pitch), anim._CAM_PITCH + 1e-9)

    def test_camera_travels_forward(self):
        depths = [_camera(t, 1.0)[4] for t in (0.0, 1.0, 5.0, 20.0)]
        self.assertEqual(depths, sorted(depths))
        self.assertGreater(depths[-1], depths[0])

    def test_camera_sway_does_not_repeat_quickly(self):
        # The four sway rates are mutually incommensurate so the motion never
        # visibly loops; if they shared a period this would find it.
        first = _camera(0.0, 1.0)[:4]
        for t in range(1, 600):
            self.assertNotAlmostEqual(
                sum(abs(a - b) for a, b in zip(_camera(float(t), 1.0)[:4], first)),
                0.0, places=4, msg=f"camera sway repeats after {t}s")

    def test_vanishing_point_moves_with_the_camera(self):
        # The payoff of a real camera over a scrolling fan: yaw and pitch swing the
        # convergence point around the view instead of pinning it to the centre.
        points = [self._far_point(t) for t in (0.0, 20.0, 40.0, 60.0)]
        spread = max(math.dist(a, b) for a in points for b in points)
        self.assertGreater(spread, 20.0)

    def test_ring_recycling_keeps_the_scene_stable(self):
        # Rings are selected by depth window, so the count must not pulse as the
        # camera advances past one ring spacing.
        counts = [len(self._segs(t)) for t in [i * 0.05 for i in range(40)]]
        self.assertLess(max(counts) - min(counts), max(counts) * 0.25)

    def test_grid_density_follows_the_view_aspect(self):
        # Floor/ceiling rail count is derived from the corridor aspect so cells stay
        # roughly square rather than stretching in a wide window.
        wide = len(self._segs(2.0, w=1920, h=600))
        square = len(self._segs(2.0, w=800, h=800))
        self.assertGreater(wide, square)


if __name__ == "__main__":
    unittest.main()
