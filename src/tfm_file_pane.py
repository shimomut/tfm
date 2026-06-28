"""FilePane — a single directory pane for the PuiKit port of TFM.

A thin PuiKit view over a ``pane_data`` dict (the same model
``tfm_pane_manager.PaneManager`` builds and ``tfm_file_list_manager`` populates),
so the storage-agnostic business logic is reused unchanged. The controller owns
navigation and mutates ``pane_data``; this widget only draws the current state:
a scrollable list of entries with a cursor row, name + size columns, and a
directory/file color distinction. Fitting is measured (``ctx.measure_text``), so
it renders correctly with a proportional font on GUI and on the TUI grid alike.
"""

from __future__ import annotations

from puikit.backend import Style, TextAttribute
from puikit.text import elide
from puikit.widgets.base import Widget, draw_list_row

#: Base-unit width reserved at the right edge for the size column.
SIZE_COL = 9


class FilePane(Widget):
    def __init__(self, pane_data: dict):
        self.pane = pane_data
        #: Whether this is the active pane (controller sets it on switch_pane);
        #: drives the louder cursor highlight.
        self.active = False

    # --- helpers -------------------------------------------------------------

    def _info(self, entry) -> dict:
        """Cached (size_str, date_str, is_dir) for an entry, or a stat fallback."""
        info = self.pane.get("file_info", {}).get(str(entry))
        if info is not None:
            return info
        try:
            is_dir = entry.is_dir()
        except Exception:
            is_dir = False
        return {"size_str": "<DIR>" if is_dir else "", "date_str": "", "is_dir": is_dir}

    def _scroll_to_cursor(self, height: int) -> int:
        """Keep the cursor row visible; returns (and stores) the scroll offset."""
        files = self.pane["files"]
        cursor = self.pane["focused_index"]
        offset = self.pane.get("scroll_offset", 0)
        if cursor < offset:
            offset = cursor
        elif cursor >= offset + height:
            offset = cursor - height + 1
        offset = max(0, min(offset, max(0, len(files) - height)))
        self.pane["scroll_offset"] = offset
        return offset

    # --- draw ----------------------------------------------------------------

    def draw(self, ctx) -> None:
        theme = ctx.theme
        text_fg = theme.text
        muted_fg = theme.muted_text
        accent = theme.accent
        files = self.pane["files"]
        width = ctx.width
        height = ctx.height

        if not files:
            msg = "(empty)" if not self.pane.get("error") else str(self.pane["error"])
            ctx.draw_text(1, 0, elide(msg, max(0, width - 2)), Style(fg=muted_fg, attr=TextAttribute.DIM))
            return

        def measure(s: str) -> float:
            return ctx.measure_text(s)

        cursor = self.pane["focused_index"]
        offset = self._scroll_to_cursor(height)
        name_w = max(1, width - SIZE_COL - 1)

        for row in range(height):
            i = offset + row
            if i >= len(files):
                break
            entry = files[i]
            info = self._info(entry)
            is_dir = info["is_dir"]
            name = entry.name + ("/" if is_dir else "")
            size = info["size_str"]
            is_cursor = i == cursor

            name_text = elide(name, name_w, where="end", measure=measure)

            if is_cursor:
                # Cursor row: a full-width fill, louder on the active pane.
                bg = theme.selection_active_bg if self.active else theme.selection_inactive_bg
                fg = (255, 255, 255) if self.active else text_fg
                draw_list_row(ctx, row, name_text, name_w, Style(fg=fg, bg=bg), fill_w=width)
                if size:
                    ctx.draw_text(width - measure(size), row, size, Style(fg=fg, bg=bg))
            else:
                fg = accent if is_dir else text_fg
                ctx.draw_text(0, row, name_text, Style(fg=fg))
                if size:
                    ctx.draw_text(width - measure(size), row, size, Style(fg=muted_fg))
