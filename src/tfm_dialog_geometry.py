"""Geometry for pane-anchored dialogs.

A picker that acts on one pane (filter, favorites, drives, an input prompt) is
anchored over that pane so the user can see which side it targets. It reads as
belonging to the pane by being *centered over it*, but its width is independent
of the pane: a narrow pane (splitter dragged over) must not shrink the dialog.
The box keeps its own desired width and just leans over its target pane.
"""

from __future__ import annotations


def pane_anchored_box(
    desired_w: float,
    screen_w: float,
    region: tuple[float, float],
    *,
    margin: float = 2.0,
) -> tuple[float, float]:
    """Return ``(w, x)`` in base units for a dialog anchored over the pane whose
    column span is ``region`` (its ``(x, width)``).

    The width is ``desired_w`` regardless of the pane's width — the splitter
    position never changes the dialog's size — subject only to an on-screen cap
    that keeps a ``margin`` on each side. The box is centered on the pane's
    center so it leans over the pane it acts on (near a screen edge the on-screen
    clamp shifts it inward, but it stays over its target pane rather than the
    other)."""
    region_x, region_w = region
    w = min(desired_w, max(1.0, screen_w - 2.0 * margin))
    center = region_x + region_w / 2.0
    if w >= screen_w - 2.0 * margin:
        # Too wide to keep both margins: center it in the whole window.
        x = max(0.0, (screen_w - w) / 2.0)
    else:
        x = max(margin, min(center - w / 2.0, screen_w - w - margin))
    return w, x
