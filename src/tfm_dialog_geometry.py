"""Geometry for pane-anchored dialogs.

A picker that acts on one pane (filter, favorites, drives, an input prompt) is
anchored over that pane so the user can see which side it targets. It should read
as belonging to the pane, but it need not be *confined* to the pane's width: a
dialog a bit wider than the pane is more comfortable to read and still clearly
leans over its target as long as it stays centered on the pane's center.
"""

from __future__ import annotations


def pane_anchored_box(
    desired_w: float,
    screen_w: float,
    region: tuple[float, float],
    *,
    factor: float = 1.4,
    margin: float = 2.0,
) -> tuple[float, float]:
    """Return ``(w, x)`` in base units for a dialog anchored over the pane whose
    column span is ``region`` (its ``(x, width)``).

    The box may grow up to ``factor``× the pane width for breathing room, but
    never past its own ``desired_w`` and never narrower than a plain pane-confined
    box — subject to a final on-screen cap that keeps a ``margin`` on each side.
    It is centered on the pane's center so it still leans over the pane it acts on
    (near a screen edge the on-screen clamp shifts it inward, but it stays over
    its target pane rather than the other)."""
    region_x, region_w = region
    pane_fit = min(desired_w, region_w)              # the old, pane-confined width
    w = min(desired_w, region_w * factor)            # grow past the pane a bit
    w = max(w, pane_fit)                             # never narrower than pane-fit
    w = min(w, max(1.0, screen_w - 2.0 * margin))    # ...but keep a screen margin
    center = region_x + region_w / 2.0
    if w >= screen_w - 2.0 * margin:
        # Too wide to keep both margins: center it in the whole window.
        x = max(0.0, (screen_w - w) / 2.0)
    else:
        x = max(margin, min(center - w / 2.0, screen_w - w - margin))
    return w, x
