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


class DiffViewer(Widget):
    """Full-window modal side-by-side diff. Construct via :func:`show_diff_viewer`."""

    focusable = True

    def __init__(self, path1, path2):
        self.path1, self.path2 = path1, path2
        self.lines1, _ = _read_lines(path1)
        self.lines2, _ = _read_lines(path2)
        self.hl1 = _highlight(self.lines1, path1)
        self.hl2 = _highlight(self.lines2, path2)
        self.rows, self.blocks = compute_diff(self.lines1, self.lines2)
        self._panel: Any = None
        self.top = 0.0
        self.left = 0
        self._view_h = 1
        # Layout captured each draw, read by the clipped scroll body.
        self._body = _ScrollBody(self._draw_rows)
        self._cols: dict = {}
        self._bg = self._text_fg = self._muted = None

    def _gutter_w(self) -> int:
        return len(str(max(1, len(self.lines1), len(self.lines2)))) + 1

    def _clamp(self) -> None:
        self.top = max(0.0, min(self.top, float(max(0, len(self.rows) - self._view_h))))
        self.left = max(0, self.left)

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
        text_fg = theme.text if theme is not None else (212, 212, 212)
        muted = theme.muted_text if theme is not None else (150, 150, 150)
        accent = theme.accent if theme is not None else (0, 122, 204)
        ctx.fill_rect(0, 0, wu, ctx.size_units[1], Style(bg=bg))

        gutter = self._gutter_w()
        side_w = (w - 1) // 2            # one column reserved for the divider
        r_gutter_x = side_w + 1
        r_content_x = r_gutter_x + gutter
        self._cols = {
            "sep_x": side_w,
            "l_content_x": gutter, "l_content_w": max(1, side_w - gutter),
            "r_gutter_x": r_gutter_x, "r_content_x": r_content_x,
            "r_content_w": max(1, w - r_content_x - 1),
        }
        self._bg, self._text_fg, self._muted = bg, text_fg, muted
        self._view_h = max(1, h - 2)
        self._clamp()

        # Header.
        ctx.draw_text(0, 0, f" {self.path1.name}"[:side_w],
                      Style(fg=accent, bg=bg, attr=TextAttribute.BOLD))
        ctx.draw_text(r_gutter_x, 0, f" {self.path2.name}"[:self._cols['r_content_w'] + gutter],
                      Style(fg=accent, bg=bg, attr=TextAttribute.BOLD))

        # Scrolling rows in a clipped child for smooth fractional GUI scroll.
        ctx.draw_child(self._body, 0, 1, wu, float(self._view_h))

        if len(self.rows) > self._view_h:
            denom = len(self.rows) - self._view_h
            ratio = self._view_h / len(self.rows)
            ctx.draw_scrollbar(wu - 1, 1, self._view_h,
                               max(0.0, min(1.0, self.top / denom if denom else 0.0)), ratio)

        changes = len(self.blocks)
        hint = f" {len(self.rows)} rows · {changes} change blocks · n/N jump · ←→ pan · q close "
        ctx.draw_text(0, h - 1, hint[:w], Style(fg=muted, bg=bg, attr=TextAttribute.DIM))

    def _draw_rows(self, ctx) -> None:
        """Render the visible diff rows into the clipped body, shifted up by the
        fractional part of ``self.top`` for smooth GUI scroll."""
        c = self._cols
        text_fg, muted, bg = self._text_fg, self._muted, self._bg
        first = int(self.top)
        frac = self.top - first
        for vis in range(self._view_h + 1):
            ri = first + vis
            if ri >= len(self.rows):
                break
            y = vis - frac
            row = self.rows[ri]
            ctx.draw_text(c["sep_x"], y, "│", Style(fg=muted, bg=bg))
            self._draw_side(ctx, y, 0, c["l_content_x"], c["l_content_w"],
                            row["n1"], row["l1"], self.hl1, self._side_bg(row, "l"),
                            row["cr1"], _CHAR_DEL_BG, text_fg, muted, bg)
            self._draw_side(ctx, y, c["r_gutter_x"], c["r_content_x"], c["r_content_w"],
                            row["n2"], row["l2"], self.hl2, self._side_bg(row, "r"),
                            row["cr2"], _CHAR_INS_BG, text_fg, muted, bg)

    @staticmethod
    def _side_bg(row: dict, side: str) -> tuple[int, int, int] | None:
        tag = row["tag"]
        if tag == "equal":
            return None
        if tag == "replace":
            return _REPLACE_BG
        if tag == "delete":
            return _DEL_BG if side == "l" else _EMPTY_BG
        # insert
        return _EMPTY_BG if side == "l" else _INS_BG

    def _draw_side(self, ctx, y, gutter_x, content_x, content_w, lineno, plain,
                   highlighted, side_bg, char_ranges, char_bg, text_fg, muted, bg) -> None:
        # Row tint fills the gutter + content for this side.
        if side_bg is not None:
            ctx.fill_rect(gutter_x, y, (content_x - gutter_x) + content_w, 1.0, Style(bg=side_bg))
        row_bg = side_bg if side_bg is not None else bg
        if lineno is not None:
            ctx.draw_text(gutter_x, y, str(lineno).rjust(self._gutter_w() - 1),
                          Style(fg=muted, bg=row_bg, font=MONO))
        if lineno is None:
            return
        # Syntax segments for this line (clipped to the horizontal window).
        segs = highlighted[lineno - 1] if 0 <= lineno - 1 < len(highlighted) else [(plain, None)]
        col0, window_end = self.left, self.left + content_w
        col = 0
        for text, fg in segs:
            seg_end = col + len(text)
            vis_start = max(col, col0)
            vis_end = min(seg_end, window_end)
            if vis_end > vis_start:
                sub = text[vis_start - col: vis_end - col]
                ctx.draw_text(content_x + (vis_start - col0), y, sub,
                              Style(fg=fg if fg is not None else text_fg, bg=row_bg, font=MONO))
            col = seg_end
            if col >= window_end:
                break
        # Char-level diff overlay (stronger bg over the changed spans).
        if char_ranges:
            for s, e in char_ranges:
                vis_start = max(s, col0)
                vis_end = min(e, window_end)
                if vis_end <= vis_start:
                    continue
                ctx.draw_text(content_x + (vis_start - col0), y, plain[vis_start:vis_end],
                              Style(fg=text_fg, bg=char_bg, font=MONO))

    # --- events --------------------------------------------------------------

    def _close(self) -> None:
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.MOUSE_SCROLL:
            amount = event.hints.get("scroll_units")
            self.top -= float(amount) if amount is not None else float(event.scroll)
            self._clamp()
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
            self.left = max(0, self.left - 4)
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
