"""FilePane — a single directory pane for the PuiKit port of TFM.

A thin PuiKit view over a ``pane_data`` dict (the same model
``tfm_pane_manager.PaneManager`` builds and ``tfm_file_list_manager`` populates),
so the storage-agnostic business logic is reused unchanged. The controller owns
the keymap and mutates ``pane_data['focused_index']``; this widget owns the
*rendering and pointer interaction* — and deliberately matches ``ListView``'s
quality there:

- **Virtualized**: only the visible window of rows is drawn, however long the
  directory.
- **Smooth scroll**: ``offset`` is a float in base units; a trackpad/precise
  wheel carries a sub-unit ``scroll_units`` delta, so GUI scrolling is
  pixel-granular (the first row slides partly off the top, clipped). Whole-unit
  backends only deliver whole deltas, so the TUI stays grid-aligned.
- **Mouse**: click selects a row (and activates the pane); wheel/trackpad scroll
  moves the viewport without moving the cursor — the pane *under the pointer*
  scrolls.
- **Scrollbar**: shown when the list outgrows the pane, flush to the right edge
  at fractional width.
- **Measured fitting**: names are elided by ``ctx.measure_text`` so a
  proportional GUI font and the TUI grid both render correctly.
"""

from __future__ import annotations

from typing import Callable

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.text import elide
from puikit.widgets.base import Widget, draw_list_row

#: Base-unit width reserved at the right edge for the size column.
SIZE_COL = 9
#: Gap (base units) between adjacent columns (name|size, size|date).
COL_GAP = 1
#: Smallest name column we'll allow before dropping the date column on a narrow
#: pane — mirrors ttk TFM, which hides the datetime when the pane gets tight.
MIN_NAME_W = 12
#: Left gutter (base units) for the selection marker, reserved always so names
#: don't shift when you select.
MARK_W = 1
#: Selection marker glyph + color (a warm amber, distinct from the blue dir
#: color). TODO: promote to a theme token when TFM's color schemes are ported.
MARKER = "•"
MARKED_FG = (229, 192, 123)


class FilePane(Widget):
    def __init__(
        self,
        pane_data: dict,
        on_click: Callable[[int], None] | None = None,
        on_context: Callable[[int, float, float], None] | None = None,
    ):
        self.pane = pane_data
        #: Active pane (controller sets it on switch_pane / click); drives the
        #: louder cursor highlight.
        self.active = False
        #: Called with the clicked row index — the controller makes this pane
        #: active and moves the cursor there.
        self.on_click = on_click
        #: Called with (row index, screen_x, screen_y) on right-click, so the
        #: controller can pop a context menu anchored at the pointer.
        self.on_context = on_context
        #: This pane's absolute rect, captured each draw, to map a widget-local
        #: pointer back to screen coords for ``popup_menu``.
        self._abs: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
        #: First visible row in base units. Whole on whole-unit backends;
        #: fractional on backends whose scroll carries sub-unit deltas (smooth).
        self.offset: float = 0.0
        self._last_cursor = -1
        self._view_h = 1.0
        self._viewport_rows = 1

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

    def _date_width(self) -> int:
        """Character width of the date column, from the first dated entry.

        ``tfm_file_list_manager`` formats every entry in a pane with the same
        ``config.DATE_FORMAT`` (short ``YY-MM-DD HH:MM`` = 14, full
        ``YYYY-MM-DD HH:MM:SS`` = 19), so one sample gives the column width.
        Returns 0 when nothing carries a date (so the column is dropped).
        """
        for info in self.pane.get("file_info", {}).values():
            date_str = info.get("date_str")
            if date_str:
                return len(date_str)
        return 0

    def _clamp(self, count: int, view_h: float) -> None:
        self.offset = max(0.0, min(self.offset, max(0.0, count - view_h)))

    def _ensure_cursor_visible(self, cursor: int, view_h: float) -> None:
        if cursor < self.offset:
            self.offset = float(cursor)
        elif cursor + 1 > self.offset + view_h:
            self.offset = cursor + 1 - view_h

    def scroll_by(self, amount: float) -> None:
        """Move the viewport (not the cursor) by ``amount`` base units; clamped
        on the next draw against the real viewport height."""
        self.offset += amount

    # --- draw ----------------------------------------------------------------

    def draw(self, ctx) -> None:
        theme = ctx.theme
        self._abs = ctx.screen_rect
        files = self.pane["files"]
        count = len(files)
        # Exact (fractional) extent so the last partial row and the scroll bounds
        # line up with the pane edge at pixel granularity, not whole base units.
        view_h = ctx.size_units[1]
        self._view_h = view_h
        self._viewport_rows = max(1, int(view_h))

        if count == 0:
            msg = "(empty)" if not self.pane.get("error") else str(self.pane["error"])
            ctx.draw_text(1, 0, elide(msg, max(0, ctx.width - 2)),
                          Style(fg=theme.muted_text, attr=TextAttribute.DIM))
            return

        cursor = self.pane["focused_index"]
        # Auto-scroll to the cursor only when it *moved* (keyboard nav). A wheel
        # scroll leaves the cursor put, so the viewport stays where the user put
        # it instead of snapping back.
        if cursor != self._last_cursor:
            self._ensure_cursor_visible(cursor, view_h)
            self._last_cursor = cursor
        self._clamp(count, view_h)

        show_bar = count > view_h
        # Fractional inner width (up to the scrollbar's left edge) so a row fill
        # and the right-aligned columns reach the true pane edge.
        full_w = ctx.size_units[0] - (1.0 if show_bar else 0.0)

        # Date column, shown to the right of size — but only while the name still
        # has room to breathe, matching ttk TFM's narrow-pane behaviour.
        date_w = self._date_width()
        name_if_dated = int(full_w) - MARK_W - SIZE_COL - date_w - COL_GAP * 2
        show_date = date_w > 0 and name_if_dated >= MIN_NAME_W
        tail = SIZE_COL + COL_GAP + (date_w + COL_GAP if show_date else 0)
        name_w = max(1, int(full_w) - MARK_W - tail)
        # Right edges of the size / date columns.
        date_right = full_w
        size_right = (full_w - date_w - COL_GAP) if show_date else full_w
        selected = self.pane["selected_files"]

        def measure(s: str) -> float:
            return ctx.measure_text(s)

        first = int(self.offset)
        frac = self.offset - first
        row = 0
        while True:
            i = first + row
            y = row - frac
            if y >= view_h or i >= count:
                break
            if i >= 0:
                entry = files[i]
                self._draw_row(ctx, y, entry, i == cursor, str(entry) in selected,
                               name_w, size_right, show_date, date_right, measure)
            row += 1

        if show_bar:
            content_h = float(count)
            ratio = view_h / content_h
            denom = content_h - view_h
            pos = self.offset / denom if denom > 0 else 0.0
            ctx.draw_scrollbar(ctx.size_units[0] - 1, 0, view_h, max(0.0, min(1.0, pos)), ratio)

    def _draw_row(self, ctx, y, entry, is_cursor, selected,
                  name_w, size_right, show_date, date_right, measure) -> None:
        theme = ctx.theme
        info = self._info(entry)
        is_dir = info["is_dir"]
        name = entry.name + ("/" if is_dir else "")
        size = info["size_str"]
        date = info["date_str"] if show_date else ""
        name_text = elide(name, name_w, where="end", measure=measure)

        if is_cursor:
            # Cursor row: a full-width fill (louder on the active pane); the
            # marker still shows so a selected-and-focused row is unambiguous.
            bg = theme.selection_active_bg if self.active else theme.selection_inactive_bg
            fg = (255, 255, 255) if self.active else theme.text
            draw_list_row(ctx, y, name_text, name_w, Style(fg=fg, bg=bg), x=MARK_W, fill_w=date_right)
            if selected:
                ctx.draw_text(0, y, MARKER, Style(fg=MARKED_FG, bg=bg, attr=TextAttribute.BOLD))
            if size:
                ctx.draw_text(size_right - measure(size), y, size, Style(fg=fg, bg=bg))
            if date:
                ctx.draw_text(date_right - measure(date), y, date, Style(fg=fg, bg=bg))
        else:
            if selected:
                ctx.draw_text(0, y, MARKER, Style(fg=MARKED_FG, attr=TextAttribute.BOLD))
                fg = MARKED_FG
            else:
                fg = theme.accent if is_dir else theme.text
            ctx.draw_text(MARK_W, y, name_text, Style(fg=fg))
            if size:
                ctx.draw_text(size_right - measure(size), y, size, Style(fg=theme.muted_text))
            if date:
                ctx.draw_text(date_right - measure(date), y, date, Style(fg=theme.muted_text))

    # --- events --------------------------------------------------------------

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.MOUSE_SCROLL:
            # A precise (trackpad) scroll carries a sub-unit delta; a plain wheel
            # moves one row per notch. The viewport moves; the cursor does not.
            amount = event.hints.get("scroll_units")
            if amount is None:
                amount = float(event.scroll)
            self.scroll_by(-amount)
            return True
        if event.type is EventType.MOUSE_CLICK and event.button == "left":
            index = int(self.offset + (event.y or 0.0))
            if 0 <= index < len(self.pane["files"]):
                if self.on_click is not None:
                    self.on_click(index)
                return True
        if event.type is EventType.MOUSE_CLICK and event.button == "right":
            index = int(self.offset + (event.y or 0.0))
            if 0 <= index < len(self.pane["files"]) and self.on_context is not None:
                rx, ry, *_ = self._abs
                self.on_context(index, rx + (event.x or 0.0), ry + (event.y or 0.0))
                return True
        return False
