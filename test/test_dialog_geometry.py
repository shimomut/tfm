"""Tests for pane-anchored dialog geometry (tfm_dialog_geometry.pane_anchored_box).

Run with: PYTHONPATH=.:src pytest test/test_dialog_geometry.py -v
"""

from tfm_dialog_geometry import pane_anchored_box


SCREEN = 100.0
LEFT = (0.0, 50.0)    # left pane: x=0, width=50
RIGHT = (50.0, 50.0)  # right pane: x=50, width=50


def _center(w, x):
    return x + w / 2.0


def test_grows_past_the_pane():
    # A 60-wide dialog over a 50-wide pane: the old code clamped to 50; now it
    # grows toward its desired width (capped at 1.4*pane = 70), so it lands at 60
    # — wider than the pane. Over the left-edge pane the on-screen clamp keeps it
    # from overhanging the screen, but it still leans left (center in the left
    # half) and covers the pane.
    w, x = pane_anchored_box(60.0, SCREEN, LEFT)
    assert w == 60.0
    assert x >= 2.0 and x + w <= SCREEN - 2.0 + 1e-9  # on-screen with margin
    assert _center(w, x) < SCREEN / 2.0               # leans over the left pane


def test_interior_pane_stays_centered_on_it():
    # A pane not against a screen edge: the wider box overhangs it symmetrically,
    # so its center is exactly the pane's center.
    w, x = pane_anchored_box(60.0, SCREEN, (25.0, 50.0))  # pane centered at 50
    assert w == 60.0
    assert _center(w, x) == 50.0


def test_capped_at_factor_times_pane():
    # A very wide desired width is capped at factor*pane_w (1.4*50 = 70).
    w, x = pane_anchored_box(200.0, SCREEN, LEFT, factor=1.4)
    assert w == 70.0


def test_never_narrower_than_pane_fit():
    # A dialog whose desired width already fits inside the pane is unchanged.
    w, x = pane_anchored_box(40.0, SCREEN, LEFT)
    assert w == 40.0
    assert _center(w, x) == 25.0


def test_right_pane_leans_right_and_stays_on_screen():
    # Over the right pane the box leans right (center on 75) but never runs off
    # the screen edge — a margin is kept.
    w, x = pane_anchored_box(60.0, SCREEN, RIGHT, margin=2.0)
    assert x + w <= SCREEN - 2.0 + 1e-9
    assert x >= 2.0 - 1e-9
    # Clamped on-screen, so the center may pull slightly left of the pane center,
    # but it still clearly leans toward the right pane.
    assert _center(w, x) > 50.0


def test_keeps_a_screen_margin_when_pane_is_huge():
    # A near-full-width pane: the box can't keep both margins at 1.4x, so it is
    # capped to the screen-minus-margins width and centered in the window.
    w, x = pane_anchored_box(200.0, SCREEN, (0.0, 98.0), margin=2.0)
    assert w == SCREEN - 4.0  # 96
    assert x == 2.0


def test_narrow_pane_near_edge_never_off_screen():
    w, x = pane_anchored_box(60.0, SCREEN, (90.0, 10.0), margin=2.0)
    assert 0.0 <= x
    assert x + w <= SCREEN - 2.0 + 1e-9
