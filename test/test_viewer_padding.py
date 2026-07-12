"""Full-window modal viewers pad like the main window's chrome: each bar's
surface fills the window edge to edge, and only the *text* (and the scrolling
body) is inset by VIEWER_PAD_PX — not a bordered card around the whole viewer.

The MemoryBackend renders as a grid (no sub-cell), where the inset collapses to
flush; the GUI inset path is driven here with a minimal vector-reporting draw
context that records where things land.
"""

import os
import sys
import tempfile
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, os.path.join(_HERE, ".."))

from tfm_text_viewer import (  # noqa: E402
    TextViewer, viewer_pad, draw_status_bar, VIEWER_PAD_PX,
)
from tfm_diff_viewer import DiffViewer  # noqa: E402
from tfm_directory_diff_viewer import DirectoryDiffView, _GUTTER_W  # noqa: E402

PX, PY = VIEWER_PAD_PX / 8, VIEWER_PAD_PX / 16  # inset for an 8x16px base cell


class _GuiCtx:
    """A vector (GUI) draw context stand-in: 8px-wide, 16px-tall base cells. It
    records fills / texts / children / scrollbars where they land."""

    vector_shapes = True
    base_size = (8, 16)

    def __init__(self, w, h):
        self.size_units = (w, h)
        self.width = int(w)
        self.height = int(h)
        self.panel = None
        self.theme = None
        self.fills = []
        self.texts = []
        self.kids = []
        self.bars = []

    def measure_text(self, t, style=None):
        return float(len(t))

    def fill_rect(self, x, y, w, h, style=None):
        self.fills.append((round(x, 3), round(y, 3), round(w, 3), round(h, 3)))

    def draw_text(self, x, y, t, style=None, **kw):
        self.texts.append((round(x, 3), round(y, 3), t))

    def draw_child(self, widget, x, y, w, h, **kw):
        self.kids.append((round(x, 3), round(y, 3), round(w, 3), round(h, 3)))

    def draw_scrollbar(self, x, y, h, pos, ratio, style=None):
        self.bars.append((round(x, 3), round(y, 3)))

    def set_cursor(self, *a, **kw):
        pass

    def screen_rect(self):
        return (0, 0, 0, 0)


class _GridCtx(_GuiCtx):
    vector_shapes = False


def test_viewer_pad_gui_and_grid():
    assert viewer_pad(_GuiCtx(200, 100)) == (PX, PY)
    assert viewer_pad(_GridCtx(200, 100)) == (0.0, 0.0)


def test_draw_status_bar_fills_full_width_insets_text():
    # The status surface spans the full window and reaches the bottom edge
    # (bottom_pad extra height); only the text is inset.
    ctx = _GuiCtx(200.0, 100.0)
    draw_status_bar(ctx, 98.75, "hello", pad_x=PX, bottom_pad=PY)
    assert (0.0, 98.75, 200.0, 1.0 + PY) in ctx.fills   # edge to edge, reaches hu
    assert any(t[0] == PX and t[1] == 98.75 for t in ctx.texts)  # text inset


def test_text_viewer_header_and_footer_are_full_width_with_inset_text():
    d = tempfile.mkdtemp()
    p = Path(d) / "f.txt"
    p.write_text("\n".join(f"line{i}" for i in range(200)))
    ctx = _GuiCtx(200.0, 100.0)
    TextViewer(p).draw(ctx)
    fy = 100.0 - 1.0 - PY
    # Header text inset from the top-left; body child inset below the header.
    assert (PX, PY) == ctx.texts[0][:2]
    assert ctx.kids[0][:2] == (PX, 1.0 + PY)
    # Footer surface full width to the bottom, text inset.
    assert (0.0, fy, 200.0, 1.0 + PY) in ctx.fills
    assert any(t[0] == PX and t[1] == fy for t in ctx.texts)


def test_diff_viewer_footer_full_width_panes_inset():
    d = tempfile.mkdtemp()
    a = Path(d) / "a.txt"; a.write_text("\n".join(f"a{i}" for i in range(300)))
    b = Path(d) / "b.txt"; b.write_text("\n".join(f"b{i}" for i in range(300)))
    ctx = _GuiCtx(200.0, 100.0)
    DiffViewer(a, b).draw(ctx)
    fy = 100.0 - 1.0 - PY
    # The two-pane splitter is inset from top/left; footer surface fills full width.
    assert ctx.kids[0][:2] == (PX, PY)
    assert (0.0, fy, 200.0, 1.0 + PY) in ctx.fills
    assert any(t[0] == PX and t[1] == fy for t in ctx.texts)


def test_dir_diff_viewer_bars_full_width_text_inset_and_hit_testing():
    d = tempfile.mkdtemp()
    ld = Path(d) / "L"; ld.mkdir()
    rd = Path(d) / "R"; rd.mkdir()
    v = DirectoryDiffView(ld, rd, background=False)
    ctx = _GuiCtx(200.0, 100.0)
    v.draw(ctx)
    head_h = 1.0 + PY
    fy = 100.0 - 1.0 - PY
    # Header bar surface reaches the top edge and is full width; text inset.
    assert (0.0, 0.0, 200.0, head_h) in ctx.fills
    assert any(t[0] == PX and t[1] == PY for t in ctx.texts)
    # Footer surface full width to the bottom; text inset.
    assert (0.0, fy, 200.0, 1.0 + PY) in ctx.fills
    assert any(t[0] == PX and t[1] == fy for t in ctx.texts)
    # The l/r pad is baked into the column geometry (events stay window-space).
    assert v._left_x == PX
    assert v._avail == 200.0 - _GUTTER_W - 2 * PX
    # A click above the header row (in the top pad) is not a row hit.
    assert v._row_at(PY) is None
    # The left header column starts at the inset, not the window edge.
    assert v._side_at(PX + 1) == "left"
    assert v._side_at(0.0) is None
