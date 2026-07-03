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
from puikit.font import Font
from puikit.text import elide
from puikit.widgets.base import Widget, draw_list_row

#: Size and date are numeric columns: pin them to a fixed-advance face so digits
#: line up in their right-aligned columns. (Names keep the Panel's default
#: proportional UI font on GUI; on TUI everything is the one grid font anyway.)
MONO = Font(monospace=True)

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
#: Incremental-search match highlight: a muted background behind every row that
#: matches the live isearch pattern (the cursor row keeps its own fill). Green,
#: distinct from the amber selection marker and the blue directory color.
MATCH_BG = (58, 84, 58)


class FilePane(Widget):
    def __init__(
        self,
        pane_data: dict,
        config=None,
        on_click: Callable[[int], None] | None = None,
        on_context: Callable[[int, float, float], None] | None = None,
    ):
        self.pane = pane_data
        #: TFM Config; read for SEPARATE_EXTENSIONS / MAX_EXTENSION_LENGTH so the
        #: extension column matches the ttk build. None disables the split.
        self.config = config
        #: Active pane (controller sets it on switch_pane / click); drives the
        #: louder cursor highlight.
        self.active = False
        #: Row indices matching the live incremental-search pattern (the
        #: controller sets this while isearch is open; empty otherwise). Matched
        #: rows get a subtle green background so every hit is visible at once.
        self.search_matches: set[int] = set()
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
        #: Cached extension-column width keyed on the ``files`` list identity
        #: (refreshed/sorted/filtered lists are fresh objects), so we measure the
        #: whole pane once per listing rather than every frame.
        self._ext_cache: tuple[int, float] = (0, 0.0)

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

    def _split_name(self, name: str, is_dir: bool) -> tuple[str, str]:
        """Split ``name`` into (basename, extension) for the separate-extension
        column, mirroring ttk TFM's ``separate_filename_extension``:
        directories, dotfiles (leading dot), no-dot names, and over-long
        extensions are not split (extension == "").
        """
        if is_dir or self.config is None or not getattr(self.config, "SEPARATE_EXTENSIONS", False):
            return name, ""
        dot = name.rfind(".")
        if dot <= 0:
            return name, ""
        ext = name[dot:]
        if len(ext) > getattr(self.config, "MAX_EXTENSION_LENGTH", 5):
            return name, ""
        return name[:dot], ext

    def _ext_width(self, measure: Callable[[str], float]) -> float:
        """Width of the extension column: the widest split-off extension in the
        pane (0 when none qualify, so the column is dropped). Cached per listing.
        """
        if self.config is None or not getattr(self.config, "SEPARATE_EXTENSIONS", False):
            return 0.0
        files = self.pane["files"]
        if self._ext_cache[0] == id(files):
            return self._ext_cache[1]
        info_cache = self.pane.get("file_info", {})
        width = 0.0
        for entry in files:
            info = info_cache.get(str(entry))
            is_dir = info["is_dir"] if info else False
            _, ext = self._split_name(entry.name, is_dir)
            if ext:
                width = max(width, measure(ext))
        self._ext_cache = (id(files), width)
        return width

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
            if self.pane.get("loading"):
                # Blank until the load is slow enough to have crossed the
                # deferred-indicator threshold (``_loading_shown``), so a fast
                # (local) listing swaps in without ever flashing "Loading…".
                msg = "Loading…" if self.pane.get("_loading_shown") else ""
            elif self.pane.get("error"):
                msg = str(self.pane["error"])
            else:
                msg = "(empty)"
            if msg:
                ctx.draw_text(1, 0, elide(msg, max(0, ctx.width - 2), measure=ctx.measure_text),
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

        def measure(s: str) -> float:
            return ctx.measure_text(s)

        def measure_mono(s: str) -> float:
            return ctx.measure_text(s, Style(font=MONO))

        # Columns, left to right: marker | basename | ext | size | date. The
        # extension column sits between the name and size (ttk TFM layout); it is
        # dropped when the pane has no splittable extensions.
        ext_w = self._ext_width(measure)
        ext_block = (COL_GAP + ext_w) if ext_w > 0 else 0.0

        # Date column (right of size), shown only while the name still has room to
        # breathe, matching ttk TFM's narrow-pane behaviour.
        date_w = self._date_width()
        name_if_dated = full_w - MARK_W - SIZE_COL - date_w - COL_GAP * 2 - ext_block
        show_date = date_w > 0 and name_if_dated >= MIN_NAME_W
        tail = SIZE_COL + COL_GAP + (date_w + COL_GAP if show_date else 0)

        # Fractional name width / ext origin so the extension column lands at the
        # exact pixel after the (proportional) name, not snapped to the char grid.
        # (Whole-unit backends still snap on draw, so the TUI stays grid-aligned.)
        name_w = max(1.0, full_w - MARK_W - ext_block - tail)
        ext_x = MARK_W + name_w + COL_GAP
        # Right edges of the size / date columns.
        date_right = full_w
        size_right = (full_w - date_w - COL_GAP) if show_date else full_w
        selected = self.pane["selected_files"]

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
                               i in self.search_matches,
                               name_w, ext_x, ext_w, size_right, show_date, date_right,
                               measure, measure_mono)
            row += 1

        if show_bar:
            content_h = float(count)
            ratio = view_h / content_h
            denom = content_h - view_h
            pos = self.offset / denom if denom > 0 else 0.0
            ctx.draw_scrollbar(ctx.size_units[0] - 1, 0, view_h, max(0.0, min(1.0, pos)), ratio)

    def _draw_row(self, ctx, y, entry, is_cursor, selected, is_match,
                  name_w, ext_x, ext_w, size_right, show_date, date_right,
                  measure, measure_mono) -> None:
        theme = ctx.theme
        info = self._info(entry)
        is_dir = info["is_dir"]
        basename, ext = self._split_name(entry.name, is_dir)
        name = basename + ("/" if is_dir else "")
        size = info["size_str"]
        date = info["date_str"] if show_date else ""
        name_text = elide(name, name_w, where="end", measure=measure)
        ext_text = elide(ext, ext_w, where="end", measure=measure) if ext_w > 0 else ""

        if is_cursor:
            # Cursor row: a full-width fill (louder on the active pane); the
            # marker still shows so a selected-and-focused row is unambiguous.
            bg = theme.selection_active_bg if self.active else theme.selection_inactive_bg
            fg = (255, 255, 255) if self.active else theme.text
            draw_list_row(ctx, y, name_text, name_w, Style(fg=fg, bg=bg), x=MARK_W, fill_w=date_right)
            if selected:
                ctx.draw_text(0, y, MARKER, Style(fg=MARKED_FG, bg=bg, attr=TextAttribute.BOLD))
            if ext_text:
                ctx.draw_text(ext_x, y, ext_text, Style(fg=fg, bg=bg))
            if size:
                ctx.draw_text(size_right - measure_mono(size), y, size, Style(fg=fg, bg=bg, font=MONO))
            if date:
                ctx.draw_text(date_right - measure_mono(date), y, date, Style(fg=fg, bg=bg, font=MONO))
        else:
            # A live isearch match paints a full-width background behind the row
            # (the cursor row keeps its own fill above); text is then drawn with
            # the same bg so a proportional GUI font's cells match the fill.
            row_bg = MATCH_BG if is_match else None
            if row_bg is not None:
                ctx.fill_rect(0, y, date_right, 1.0, Style(bg=row_bg))
            if selected:
                ctx.draw_text(0, y, MARKER, Style(fg=MARKED_FG, bg=row_bg, attr=TextAttribute.BOLD))
                fg = MARKED_FG
            else:
                fg = theme.accent if is_dir else theme.text
            ctx.draw_text(MARK_W, y, name_text, Style(fg=fg, bg=row_bg))
            if ext_text:
                ctx.draw_text(ext_x, y, ext_text, Style(fg=fg, bg=row_bg))
            if size:
                ctx.draw_text(size_right - measure_mono(size), y, size, Style(fg=theme.muted_text, bg=row_bg, font=MONO))
            if date:
                ctx.draw_text(date_right - measure_mono(date), y, date, Style(fg=theme.muted_text, bg=row_bg, font=MONO))

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
