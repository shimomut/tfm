"""DiffViewer — a modal side-by-side text diff for the PuiKit port.

The PuiKit counterpart to ttk TFM's ``DiffViewer``: compares two text files
side by side using ``difflib``, line-by-line with character-level highlighting
within changed lines. Deletions, insertions, and replacements are tinted; the
matched/changed spans inside a replaced line are highlighted more strongly.

It reuses the text viewer's file reading and syntax highlighting
(:mod:`tfm_text_view`), so each side keeps its syntax colors with the diff
tint laid over them. Push it with :func:`show_diff_viewer`.

Keys: ↑/↓/PageUp/PageDown/Home/End scroll; ←/→ scroll horizontally;
``n``/``N`` jump to the next/previous change; ``q`` or Esc closes.
"""

from __future__ import annotations

import difflib
from typing import Any

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.panel import Rect
from puikit.widgets import Splitter
from puikit.widgets.base import Widget

from tfm_text_view import MONO, _ScrollBody, _highlight, _read_lines

#: Whole-row tints by diff tag.
_DEL_BG = (60, 30, 30)
_INS_BG = (28, 50, 30)
_REPLACE_BG = (50, 46, 28)
#: Stronger tints for the changed character spans inside a replaced line.
_CHAR_DEL_BG = (104, 42, 42)
_CHAR_INS_BG = (40, 82, 44)
#: Faint fill for the empty side of an insert/delete row.
_EMPTY_BG = (32, 32, 34)


def _char_ranges(a: str, b: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Per-side character spans that differ between ``a`` and ``b``."""
    matcher = difflib.SequenceMatcher(None, a, b)
    ra: list[tuple[int, int]] = []
    rb: list[tuple[int, int]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if i2 > i1:
            ra.append((i1, i2))
        if j2 > j1:
            rb.append((j1, j2))
    return ra, rb


def compute_diff(lines1: list[str], lines2: list[str]) -> tuple[list[dict], list[int]]:
    """Side-by-side diff of two line lists. Returns ``(rows, block_starts)``:
    one row dict per display line (``tag``, ``l1``/``l2`` text, ``n1``/``n2``
    line numbers or None, and ``cr1``/``cr2`` changed-char ranges), and the row
    index where each change block begins (for next/prev-change navigation)."""
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    rows: list[dict] = []
    blocks: list[int] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                rows.append({"tag": "equal", "l1": lines1[i1 + k], "l2": lines2[j1 + k],
                             "n1": i1 + k + 1, "n2": j1 + k + 1, "cr1": None, "cr2": None})
            continue
        blocks.append(len(rows))
        if tag == "replace":
            for k in range(max(i2 - i1, j2 - j1)):
                has1, has2 = i1 + k < i2, j1 + k < j2
                l1 = lines1[i1 + k] if has1 else ""
                l2 = lines2[j1 + k] if has2 else ""
                cr1 = cr2 = None
                if has1 and has2 and l1 and l2:
                    cr1, cr2 = _char_ranges(l1, l2)
                rows.append({"tag": "replace", "l1": l1, "l2": l2,
                             "n1": (i1 + k + 1) if has1 else None,
                             "n2": (j1 + k + 1) if has2 else None, "cr1": cr1, "cr2": cr2})
        elif tag == "delete":
            for i in range(i1, i2):
                rows.append({"tag": "delete", "l1": lines1[i], "l2": "",
                             "n1": i + 1, "n2": None, "cr1": None, "cr2": None})
        elif tag == "insert":
            for j in range(j1, j2):
                rows.append({"tag": "insert", "l1": "", "l2": lines2[j],
                             "n1": None, "n2": j + 1, "cr1": None, "cr2": None})
    return rows, blocks


def _side_bg(row: dict, side: str) -> tuple[int, int, int] | None:
    """Whole-row tint for one side of a diff row (None for an unchanged line)."""
    tag = row["tag"]
    if tag == "equal":
        return None
    if tag == "replace":
        return _REPLACE_BG
    if tag == "delete":
        return _DEL_BG if side == "l" else _EMPTY_BG
    return _EMPTY_BG if side == "l" else _INS_BG  # insert


class _DiffPane(Widget):
    """One side of the diff — its filename header, gutter, and scrolling content.
    Reads shared scroll state (``top``/``left``/``_view_h``) from the parent
    :class:`DiffViewer`, so the two sides stay row-aligned and pan together; only
    the split *width* differs (the Splitter owns that). The scrolling rows live
    in a clipped child for smooth fractional scroll on both axes."""

    def __init__(self, viewer: "DiffViewer", side: str):
        self.v = viewer
        self.side = side                 # "l" (left/old) or "r" (right/new)
        self._body = _ScrollBody(self._draw_rows)
        self._w = 1
        self._gutter = 2
        self._content_x = 2
        self._content_w = 1
        self._bg = self._text_fg = self._muted = None

    def draw(self, ctx) -> None:
        v = self.v
        theme = ctx.theme
        w = ctx.width
        bg = getattr(theme, "popup_bg", None) if theme is not None else None
        accent = theme.accent if theme is not None else (0, 122, 204)
        self._bg = bg
        self._text_fg = theme.text if theme is not None else (212, 212, 212)
        self._muted = theme.muted_text if theme is not None else (150, 150, 150)
        self._gutter = v._gutter_w()
        self._content_x = self._gutter
        self._w = w
        # The right pane leaves a column for the shared scrollbar at the edge.
        reserve = 1 if self.side == "r" else 0
        self._content_w = max(1, w - self._gutter - reserve)

        name = v.path1.name if self.side == "l" else v.path2.name
        ctx.draw_text(0, 0, f" {name}"[:w], Style(fg=accent, bg=bg, attr=TextAttribute.BOLD))
        # Content below the filename header, clipped for smooth scroll.
        ctx.draw_child(self._body, 0, 1, w, float(v._view_h))

    def _draw_rows(self, ctx) -> None:
        v = self.v
        side = self.side
        bg, muted, text_fg = self._bg, self._muted, self._text_fg
        content_x, content_w = self._content_x, self._content_w
        highlighted = v.hl1 if side == "l" else v.hl2
        char_bg = _CHAR_DEL_BG if side == "l" else _CHAR_INS_BG
        first = int(v.top)
        vfrac = v.top - first
        col0_int = int(v.left)
        xfrac = v.left - col0_int
        window_end = col0_int + content_w + (1 if xfrac > 0 else 0)
        for vis in range(v._view_h + 1):
            ri = first + vis
            if ri >= len(v.rows):
                break
            y = vis - vfrac
            row = v.rows[ri]
            lineno = row["n1"] if side == "l" else row["n2"]
            plain = row["l1"] if side == "l" else row["l2"]
            cranges = row["cr1"] if side == "l" else row["cr2"]
            side_bg = _side_bg(row, side)
            row_bg = side_bg if side_bg is not None else bg
            if side_bg is not None:
                ctx.fill_rect(0, y, self._w, 1.0, Style(bg=side_bg))
            if lineno is not None:
                segs = highlighted[lineno - 1] if 0 <= lineno - 1 < len(highlighted) else [(plain, None)]
                col = 0
                for text, fg in segs:
                    seg_end = col + len(text)
                    vis_start = max(col, col0_int)
                    vis_end = min(seg_end, window_end)
                    if vis_end > vis_start:
                        sub = text[vis_start - col: vis_end - col]
                        ctx.draw_text(content_x + (vis_start - col0_int) - xfrac, y, sub,
                                      Style(fg=fg if fg is not None else text_fg, bg=row_bg, font=MONO))
                    col = seg_end
                    if col >= window_end:
                        break
                for s, e in (cranges or []):
                    vs, ve = max(s, col0_int), min(e, window_end)
                    if ve > vs:
                        ctx.draw_text(content_x + (vs - col0_int) - xfrac, y, plain[vs:ve],
                                      Style(fg=text_fg, bg=char_bg, font=MONO))
            # Gutter (after content) masks the left horizontal bleed, then numbers.
            ctx.fill_rect(0, y, content_x, 1.0, Style(bg=row_bg))
            if lineno is not None:
                ctx.draw_text(0, y, str(lineno).rjust(self._gutter - 1),
                              Style(fg=muted, bg=row_bg, font=MONO))


class DiffViewer(Widget):
    """Full-window modal side-by-side diff. Two :class:`_DiffPane` children sit in
    a draggable :class:`Splitter`; a shared scrollbar and footer are chrome.
    Construct via :func:`show_diff_viewer`."""

    focusable = True

    _MOUSE = frozenset({
        EventType.MOUSE_DOWN, EventType.MOUSE_UP,
        EventType.MOUSE_CLICK, EventType.MOUSE_DRAG,
    })

    def __init__(self, path1, path2):
        self.path1, self.path2 = path1, path2
        self.lines1, _ = _read_lines(path1)
        self.lines2, _ = _read_lines(path2)
        self.hl1 = _highlight(self.lines1, path1)
        self.hl2 = _highlight(self.lines2, path2)
        self.rows, self.blocks = compute_diff(self.lines1, self.lines2)
        self._panel: Any = None
        self.top = 0.0
        self.left = 0.0
        self._view_h = 1
        self._max_line = max((len(line) for line in self.lines1 + self.lines2), default=0)
        self.left_pane = _DiffPane(self, "l")
        self.right_pane = _DiffPane(self, "r")
        self.splitter = Splitter(self.left_pane, self.right_pane,
                                 orientation="horizontal", fraction=0.5,
                                 min_first=10, min_second=10)

    def _gutter_w(self) -> int:
        return len(str(max(1, len(self.lines1), len(self.lines2)))) + 1

    def _clamp(self) -> None:
        self.top = max(0.0, min(self.top, float(max(0, len(self.rows) - self._view_h))))
        self.left = max(0.0, min(self.left, float(max(0, self._max_line - 1))))

    def _step_block(self, delta: int) -> None:
        if not self.blocks:
            return
        cur = int(self.top)
        if delta > 0:
            nxt = next((b for b in self.blocks if b > cur), self.blocks[0])
        else:
            nxt = next((b for b in reversed(self.blocks) if b < cur), self.blocks[-1])
        self.top = float(nxt)
        self._clamp()

    # --- drawing -------------------------------------------------------------

    def draw(self, ctx) -> None:
        self._panel = ctx.panel
        theme = ctx.theme
        w, h = ctx.width, ctx.height
        wu = ctx.size_units[0]
        bg = getattr(theme, "popup_bg", None) if theme is not None else None
        muted = theme.muted_text if theme is not None else (150, 150, 150)
        ctx.fill_rect(0, 0, wu, ctx.size_units[1], Style(bg=bg))
        self._view_h = max(1, h - 2)  # minus a filename header row and a footer
        self._clamp()

        # Two panes + the draggable divider fill the area above the footer.
        ctx.draw_child(self.splitter, 0, 0, wu, float(max(1, h - 1)))

        # Shared vertical scrollbar over the right edge of the content.
        if len(self.rows) > self._view_h:
            denom = len(self.rows) - self._view_h
            ratio = self._view_h / len(self.rows)
            ctx.draw_scrollbar(wu - 1, 1, self._view_h,
                               max(0.0, min(1.0, self.top / denom if denom else 0.0)), ratio)

        hint = (f" {len(self.rows)} rows · {len(self.blocks)} changes · "
                "n/N jump · ←→ pan · drag divider · q close ")
        ctx.draw_text(0, h - 1, hint[:w], Style(fg=muted, bg=bg, attr=TextAttribute.DIM))

    # --- events --------------------------------------------------------------

    def _close(self) -> None:
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.MOUSE_SCROLL:
            uy = event.hints.get("scroll_units")
            self.top -= float(uy) if uy is not None else float(event.scroll)
            ux = event.hints.get("scroll_units_x")
            if ux is not None:
                self.left -= float(ux)
            self._clamp()
            return True
        if event.type in self._MOUSE:
            # Route to the splitter so the divider can be dragged (the panes
            # themselves are display-only).
            self.splitter.handle_event(event)
            return True
        if event.type is not EventType.KEY:
            return True
        key = event.key
        if key in ("escape", "q") or event.char == "q":
            self._close()
        elif key == "down":
            self.top += 1
        elif key == "up":
            self.top -= 1
        elif key == "pagedown":
            self.top += self._view_h
        elif key == "pageup":
            self.top -= self._view_h
        elif key == "home":
            self.top = 0.0
        elif key == "end":
            self.top = float(max(0, len(self.rows) - self._view_h))
        elif key == "right":
            self.left += 4
        elif key == "left":
            self.left = max(0.0, self.left - 4)
        elif event.char == "n":
            self._step_block(1)
        elif event.char == "N":
            self._step_block(-1)
        self._clamp()
        return True


def show_diff_viewer(panel: Any, path1, path2, z: int = 80) -> DiffViewer:
    """Push a full-window modal :class:`DiffViewer` comparing two files."""
    viewer = DiffViewer(path1, path2)
    sw, sh = panel.backend.size_units
    viewer._panel = panel
    panel.push_layer(viewer, z=z, hints={"x": 0, "y": 0, "w": sw, "h": sh},
                     reflow=lambda sw, sh: Rect(0, 0, sw, sh))
    panel.animate(viewer, hints={"transition": "fade", "duration_ms": 120})
    return viewer
