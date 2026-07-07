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

from puikit.backend import Style, TextAttribute, TRANSPARENT
from puikit.color import LC_BODY, LC_LARGE, ensure_text_headroom
from puikit.event import Event, EventType
from puikit.font import Font
from puikit.text import elide
from puikit.widgets.base import Widget

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
#: Left/right gutter (base units) reserved on a **grid** (TUI) for the cursor
#: row's framing brackets — ``[`` on the left, ``]`` on the right. GUI reserves
#: neither (its cursor is a drawn outline rectangle — see ``_draw_cursor``), so
#: names sit flush against the pane edge there.
GUTTER_W = 1
BRACKET_W = 1
#: Incremental-search match highlight: a wash behind every row matching the live
#: isearch pattern. Its base hue is the theme's **secondary accent**
#: (``theme.accent2``, or a theme's ``extras['isearch_match']`` override) blended
#: into the pane background by ``MATCH_TINT`` — kept distinct from the selection
#: fill (which is the *primary* accent) and drawn *under* it / the cursor cue.
#: Derived from the pane background so it tracks the theme: a dark wash on a dark
#: theme, a pale one on a light one.
MATCH_TINT = 0.28
#: File-type name foregrounds when a theme names no ``file_types`` palette (its
#: ``extras['file_types']`` sub-dict of ``directory`` / ``file`` / ``link``, the
#: same shape as the ``syntax`` palette). ``directory`` defaults to a soft yellow
#: (the ttk build's hue); ``link`` to a cyan (the ls convention); ``file`` to the
#: theme's own ``theme.text``. A theme (or a user's ``config.py`` ``THEMES``)
#: overrides any of them per palette; the legacy flat ``extras['directory']`` is
#: still honored as a shorthand for ``file_types['directory']``.
DIRECTORY_FG_DEFAULT = (204, 204, 120)
LINK_FG_DEFAULT = (86, 194, 214)
#: Cursor-position cue color when a theme names no ``cursor`` palette (its
#: ``extras['cursor']`` sub-dict of ``active`` / ``inactive``, the same shape as
#: the ``file_types`` palette) — a distinct **red**, orthogonal to the selection
#: fill so the two never read as the same channel: vivid on the active pane, a
#: muted red on the inactive one (the louder cue marks the focused pane). A theme
#: (or a user's ``config.py`` ``THEMES``) overrides either per palette — e.g. a
#: monochrome theme recolors the cue into its own hue instead of an off-palette red.
CURSOR_ACTIVE = (231, 76, 76)
CURSOR_INACTIVE = (140, 92, 94)
#: Selection fill = the pane background blended toward the accent by this ratio
#: (a tint that reads as "selected" without being the loud accent itself): a
#: firmer blend on the active pane, subtler on the inactive one.
SELECT_MIX_ACTIVE = 0.42
SELECT_MIX_INACTIVE = 0.22
#: Fallback pane background when the context reports none (mix base for the
#: selection tint).
DEFAULT_BG = (30, 30, 38)
#: Cursor-outline corner radius (device pixels) on a GUI backend.
CURSOR_RADIUS = 3.0
#: Top/bottom inner margin (device pixels) between the pane edge and its file
#: list, so the content breathes rather than butting the surrounding frame. GUI
#: only — a character grid has no sub-cell pixels, so it collapses to zero and
#: rows stay flush to whole cells.
INNER_MARGIN = 2.0
#: Left/right content padding (base units = cells) on a GUI backend: the gap
#: between the pane edge and where a row's text/columns sit, so names don't butt
#: the frame. Zero on a grid (flush to whole cells).
CONTENT_PAD_CELLS = 0.5
#: Left/right padding (cells) of the GUI cursor outline. Smaller than
#: ``CONTENT_PAD_CELLS`` so the red rectangle reclaims part of the content margin
#: and frames the row a touch wider than the text — a little breathing room
#: between the glyphs and the stroke.
CURSOR_PAD_CELLS = 0.25
#: Device pixels the GUI cursor outline extends *beyond* the row band on each
#: side, so the red frame sits a little wider than the selection fill.
CURSOR_BLEED_PX = 1.0
#: Manhattan distance (base units) a left-press must travel before it becomes a
#: file *drag* rather than a click — enough that ordinary click jitter never
#: starts a drag session, small enough that an intentional drag begins promptly.
DRAG_THRESHOLD = 1.5


def _mix(a, b, t):
    """Linear RGB blend a→b by ``t`` (0..1)."""
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


class FilePane(Widget):
    def __init__(
        self,
        pane_data: dict,
        config=None,
        on_click: Callable[[int], None] | None = None,
        on_context: Callable[[int, float, float], None] | None = None,
        on_drag: Callable[[int, Event], None] | None = None,
        on_drop: Callable[[int, list], None] | None = None,
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
        #: Called with (row index, drag Event) when a left-press over a row is
        #: dragged past ``DRAG_THRESHOLD`` — the controller starts a native OS
        #: file drag (``panel.begin_file_drag``) so the row (or the whole
        #: selection) can be dropped onto another app / Finder.
        self.on_drag = on_drag
        #: Called with (row index under the drop, list of dropped paths) when files
        #: are dropped onto the pane from another app (drop-IN, a FILE_DROP event).
        #: ``index`` is ``-1`` when the drop lands below the last row (target the
        #: pane's own directory); a directory row lets the controller target it.
        self.on_drop = on_drop
        #: Left-drag gesture state: the row a press landed on (``-1`` = none / not
        #: a file row), the press position (base units), and whether a drag session
        #: has already been kicked off, so the drag fires exactly once per gesture.
        self._press_index = -1
        self._press_xy: tuple[float, float] = (0.0, 0.0)
        self._dragging = False
        #: This pane's absolute rect, captured each draw, to map a widget-local
        #: pointer back to screen coords for ``popup_menu``.
        self._abs: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
        #: First visible row in base units. Whole on whole-unit backends;
        #: fractional on backends whose scroll carries sub-unit deltas (smooth).
        self.offset: float = 0.0
        self._last_cursor = -1
        #: Top inner-margin (base units) captured each draw, so a pointer's
        #: widget-local ``y`` maps back to the right row despite the inset.
        self._margin_y = 0.0
        self._view_h = 1.0
        self._viewport_rows = 1
        #: Cached extension-column width keyed on the ``files`` list identity
        #: (refreshed/sorted/filtered lists are fresh objects), so we measure the
        #: whole pane once per listing rather than every frame.
        self._ext_cache: tuple[int, float] = (0, 0.0)

    # --- helpers -------------------------------------------------------------

    def _info(self, entry) -> dict:
        """Cached (size_str, date_str, is_dir, is_link) for an entry, or a stat
        fallback."""
        info = self.pane.get("file_info", {}).get(str(entry))
        if info is not None:
            return info
        try:
            is_dir = entry.is_dir()
        except Exception:
            is_dir = False
        try:
            is_link = entry.is_symlink()
        except Exception:
            is_link = False
        return {"size_str": "<DIR>" if is_dir else "", "date_str": "",
                "is_dir": is_dir, "is_link": is_link}

    @staticmethod
    def _type_fg(theme, is_dir: bool, is_link: bool):
        """The raw name foreground for a file type, from the theme's ``file_types``
        palette (``extras['file_types']``: directory / file / link). A symlink wins
        over a directory so a link to a folder still reads as a link. Falls back to
        the legacy flat ``extras['directory']`` and to the module defaults; the
        returned color is passed through ``ctx.ink`` by the caller for legibility."""
        ft = theme.extras.get("file_types") or {}
        if is_link:
            return ft.get("link") or LINK_FG_DEFAULT
        if is_dir:
            return (ft.get("directory")
                    or theme.extras.get("directory")  # legacy flat shorthand
                    or DIRECTORY_FG_DEFAULT)
        return ft.get("file") or theme.text

    def _cursor_fg(self, theme):
        """The cursor-cue color for this pane's focus state, from the theme's
        ``cursor`` sub-palette (``extras['cursor']``: active / inactive), falling
        back to the module reds. The active (focused-pane) cue is the louder cue."""
        cur = theme.extras.get("cursor") or {}
        key = "active" if self.active else "inactive"
        return cur.get(key) or (CURSOR_ACTIVE if self.active else CURSOR_INACTIVE)

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

    def _display_name(self, entry) -> str:
        """The text shown in the name column. Normally the entry's basename; on a
        **virtual (search-results) pane** the path relative to the search root, so
        a hit scattered deep in the tree shows *where* it lives (``sub/dir/a.txt``)
        rather than a bare, location-less ``a.txt``."""
        virtual = self.pane.get("virtual")
        if virtual:
            root = str(virtual["root"])
            s = str(entry)
            if s.startswith(root):
                rel = s[len(root):].lstrip("/\\")
                if rel:
                    return rel
        return entry.name

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
        # A virtual pane shows whole relative paths in the name column, not split
        # basename/ext — so there is no extension column to size.
        if self.pane.get("virtual"):
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
        # Inner margins, in base units, dropped to zero on a character grid (no
        # sub-cell pixels). Horizontal is a fixed fraction of a cell so the text
        # padding reads the same at any font size; vertical converts INNER_MARGIN
        # device pixels through the backend's pixel-per-unit.
        _, bh = ctx.base_size
        mx = CONTENT_PAD_CELLS if ctx.vector_shapes else 0.0
        cursor_pad = CURSOR_PAD_CELLS if ctx.vector_shapes else 0.0
        my = (INNER_MARGIN / bh) if (ctx.vector_shapes and bh) else 0.0
        self._margin_y = my
        # Exact (fractional) extent so the last partial row and the scroll bounds
        # line up with the pane edge at pixel granularity, not whole base units.
        # The margin eats into it on top and bottom.
        view_h = max(0.0, ctx.size_units[1] - 2 * my)
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
                ctx.draw_text(mx + 1, my, elide(msg, max(0, ctx.width - 2), measure=ctx.measure_text),
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
        right_edge = ctx.size_units[0] - (1.0 if show_bar else 0.0)
        grid = not ctx.vector_shapes

        # Content region [content_left, content_right): where a row's text/columns
        # and its selection/match fill sit — inset by the content margin, up to the
        # scrollbar's left edge, plus a bracket gutter on a grid (the TUI cursor's
        # channel).
        content_left = mx + (GUTTER_W if grid else 0.0)
        content_right = right_edge - mx - (BRACKET_W if grid else 0.0)

        # Cursor band [band_left, band_right): where the row's cursor cue is drawn.
        # A grid puts its framing brackets in the gutter cells, one cell outside the
        # content on each side; a GUI strokes its red outline at CURSOR_PAD_CELLS —
        # inside the content margin but wider than the text, so the rectangle frames
        # the row with a little breathing room around the glyphs.
        if grid:
            band_left = mx
            band_right = right_edge - mx
        else:
            band_left = cursor_pad
            band_right = right_edge - cursor_pad

        def measure(s: str) -> float:
            return ctx.measure_text(s)

        def measure_mono(s: str) -> float:
            return ctx.measure_text(s, Style(font=MONO))

        # Columns, left to right: gutter | basename | ext | size | date. The
        # extension column sits between the name and size (ttk TFM layout); it is
        # dropped when the pane has no splittable extensions.
        ext_w = self._ext_width(measure)
        ext_block = (COL_GAP + ext_w) if ext_w > 0 else 0.0

        # Date column (right of size), shown only while the name still has room to
        # breathe, matching ttk TFM's narrow-pane behaviour.
        date_w = self._date_width()
        name_if_dated = content_right - content_left - SIZE_COL - date_w - COL_GAP * 2 - ext_block
        show_date = date_w > 0 and name_if_dated >= MIN_NAME_W
        tail = SIZE_COL + COL_GAP + (date_w + COL_GAP if show_date else 0)

        # Fractional name width / ext origin so the extension column lands at the
        # exact pixel after the (proportional) name, not snapped to the char grid.
        # (Whole-unit backends still snap on draw, so the TUI stays grid-aligned.)
        name_w = max(1.0, content_right - content_left - ext_block - tail)
        ext_x = content_left + name_w + COL_GAP
        # Right edges of the size / date columns.
        date_right = content_right
        size_right = (content_right - date_w - COL_GAP) if show_date else content_right
        selected = self.pane["selected_files"]

        first = int(self.offset)
        frac = self.offset - first
        row = 0
        while True:
            i = first + row
            ry = row - frac
            if ry >= view_h or i >= count:
                break
            if i >= 0:
                entry = files[i]
                self._draw_row(ctx, my + ry, entry, i == cursor, str(entry) in selected,
                               i in self.search_matches, grid,
                               content_left, name_w, ext_x, ext_w, size_right, show_date,
                               date_right, content_right, band_left, band_right,
                               measure, measure_mono)
            row += 1

        if show_bar:
            content_h = float(count)
            ratio = view_h / content_h
            denom = content_h - view_h
            pos = self.offset / denom if denom > 0 else 0.0
            ctx.draw_scrollbar(ctx.size_units[0] - 1, my, view_h, max(0.0, min(1.0, pos)), ratio)

    def _draw_row(self, ctx, y, entry, is_cursor, selected, is_match, grid,
                  content_left, name_w, ext_x, ext_w, size_right, show_date,
                  date_right, content_right, band_left, band_right,
                  measure, measure_mono) -> None:
        theme = ctx.theme
        info = self._info(entry)
        is_dir = info["is_dir"]
        virtual = self.pane.get("virtual")
        if virtual:
            # Whole root-relative path in the name column, no extension split;
            # elide in the middle so both the leading dirs and the trailing
            # filename stay visible when the path is too long for the column.
            basename, ext = self._display_name(entry), ""
            name_elide = "middle"
        else:
            basename, ext = self._split_name(entry.name, is_dir)
            name_elide = "end"
        name = basename
        size = info["size_str"]
        date = info["date_str"] if show_date else ""
        name_text = elide(name, name_w, where=name_elide, measure=measure)
        ext_text = elide(ext, ext_w, where="end", measure=measure) if ext_w > 0 else ""

        # Row background carries "selected": the pane background tinted toward the
        # accent (never the accent itself), firmer on the active pane, painted
        # over any live isearch-match tint. It spans only the content region, so
        # the grid's cursor-bracket gutters stay clear (they are the cursor's
        # channel).
        gui_cursor = is_cursor and not grid
        base = ctx.background or DEFAULT_BG
        if selected:
            ratio = SELECT_MIX_ACTIVE if self.active else SELECT_MIX_INACTIVE
            # The accent tint reads as "selected"; on a light theme it lands
            # mid-luminance and can't bear the row's body text, so nudge it back
            # toward the pane background just enough to clear the body floor (a
            # no-op on dark themes, where the dark tint already has headroom).
            row_bg = ensure_text_headroom(_mix(base, theme.accent, ratio), base, LC_BODY)
        elif is_match:
            # Base hue = the theme's secondary accent (or an isearch_match
            # override), blended into the pane bg — distinct from the accent
            # selection fill.
            match_base = theme.extras.get("isearch_match") or theme.accent2
            row_bg = _mix(base, match_base, MATCH_TINT)
        else:
            row_bg = None

        # Paint the row background first, then (on a GUI cursor row) the red
        # outline, then the text — the three layers the cursor cue needs, in
        # order. The cursor row always gets a solid fill so the outline sits on an
        # opaque base: its own tint when selected/matched, else the pane bg.
        fill_bg = row_bg if row_bg is not None else (base if gui_cursor else None)
        if fill_bg is not None:
            ctx.fill_rect(content_left, y, max(0.0, content_right - content_left), 1.0,
                          Style(bg=fill_bg))
        if gui_cursor:
            self._draw_cursor(ctx, y, band_left, band_right, grid)

        # Foreground keeps the file-type color language on every row (link / dir /
        # file from the theme's file_types palette, a symlink winning over a dir),
        # but is passed through ctx.ink against the *actual* background behind the
        # glyphs — the pane base, or the selection/match tint where one is painted —
        # so the name stays legible even on a row tinted toward a nearby hue
        # (floor-only: unchanged wherever it already reads). The cursor row's glyphs
        # draw over a *transparent* background so they land directly on the fill +
        # outline below without a per-run fill repainting (and breaking) the stroke —
        # but they still contrast against that fill (eff_bg), not None.
        eff_bg = row_bg if row_bg is not None else base
        is_link = info.get("is_link", False)
        name_fg = ctx.ink(self._type_fg(theme, is_dir, is_link), on=eff_bg, target=LC_BODY)
        col_fg = ctx.ink(theme.muted_text, on=eff_bg, target=LC_LARGE)
        text_bg = TRANSPARENT if gui_cursor else row_bg

        ctx.draw_text(content_left, y, name_text, Style(fg=name_fg, bg=text_bg))
        if ext_text:
            ctx.draw_text(ext_x, y, ext_text, Style(fg=name_fg, bg=text_bg))
        if size:
            ctx.draw_text(size_right - measure_mono(size), y, size, Style(fg=col_fg, bg=text_bg, font=MONO))
        if date:
            ctx.draw_text(date_right - measure_mono(date), y, date, Style(fg=col_fg, bg=text_bg, font=MONO))

        # Grid cursor cue drawn last: bold ``[`` … ``]`` brackets in the gutter
        # (they sit in the reserved gutter columns, clear of the glyphs).
        if is_cursor and grid:
            self._draw_cursor(ctx, y, band_left, band_right, grid)

    def _draw_cursor(self, ctx, y, band_left, band_right, grid) -> None:
        """Draw the cursor-position cue for the current row — the theme's ``cursor``
        color (default a distinct **red**), orthogonal to the selection fill. Vivid
        on the active pane, muted on the inactive one so the focused pane's cursor
        reads louder. Framed within the margin-inset content band
        ``[band_left, band_right)``.

        - **GUI** (``vector_shapes``): an outline rectangle framing the row.
        - **TUI** (grid): a bold ``[`` … ``]`` bracket pair around the row.
        """
        color = self._cursor_fg(ctx.theme)
        if not grid:
            # Span the full row height so the outline matches the selection fill
            # exactly (top and bottom flush). Horizontally, bleed CURSOR_BLEED_PX
            # past the band on each side so the red frame sits a touch wider than
            # the fill (the band already clears the scrollbar, so there is room to
            # grow outward).
            bw, _ = ctx.base_size
            bleed = CURSOR_BLEED_PX / bw if bw else 0.0
            ctx.round_rect(band_left - bleed, y,
                           max(0.0, (band_right - band_left) + 2 * bleed), 1.0,
                           Style(fg=color), radius=CURSOR_RADIUS)
            return
        style = Style(fg=color, attr=TextAttribute.BOLD)
        ctx.draw_text(int(band_left), y, "[", style)
        ctx.draw_text(int(band_right) - BRACKET_W, y, "]", style)

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
        if event.type is EventType.MOUSE_DOWN and event.button == "left":
            # Arm a possible drag: remember the row and press point. The click is
            # still synthesized by the Panel on release (so plain clicks keep
            # selecting); a drag only starts if the pointer travels far enough.
            index = int(self.offset + max(0.0, (event.y or 0.0) - self._margin_y))
            self._press_index = index if 0 <= index < len(self.pane["files"]) else -1
            self._press_xy = (event.x or 0.0, event.y or 0.0)
            self._dragging = False
            return False  # don't consume: let the press→click gesture run
        if event.type is EventType.MOUSE_DRAG and event.button == "left":
            if (not self._dragging and self._press_index >= 0 and self.on_drag is not None):
                dx = abs((event.x or 0.0) - self._press_xy[0])
                dy = abs((event.y or 0.0) - self._press_xy[1])
                if dx + dy >= DRAG_THRESHOLD:
                    # Threshold crossed: hand off to a native OS file drag. Fire
                    # once; the native session then captures the mouse, so no
                    # further MOUSE_DRAGs arrive until the next press.
                    self._dragging = True
                    self.on_drag(self._press_index, event)
                    return True
            return False
        if event.type is EventType.MOUSE_UP and event.button == "left":
            self._press_index = -1
            self._dragging = False
            return False
        if event.type is EventType.MOUSE_CLICK and event.button == "left":
            index = int(self.offset + max(0.0, (event.y or 0.0) - self._margin_y))
            if 0 <= index < len(self.pane["files"]):
                if self.on_click is not None:
                    self.on_click(index)
                return True
        if event.type is EventType.MOUSE_CLICK and event.button == "right":
            index = int(self.offset + max(0.0, (event.y or 0.0) - self._margin_y))
            if 0 <= index < len(self.pane["files"]) and self.on_context is not None:
                rx, ry, *_ = self._abs
                self.on_context(index, rx + (event.x or 0.0), ry + (event.y or 0.0))
                return True
        if event.type is EventType.FILE_DROP and self.on_drop is not None:
            # Files dropped onto the pane from another app. Map the drop point to a
            # row so a drop *on a directory* can target it; a drop past the last
            # row (or on empty space) reports -1 → the pane's own directory.
            index = int(self.offset + max(0.0, (event.y or 0.0) - self._margin_y))
            if not (0 <= index < len(self.pane["files"])):
                index = -1
            paths = event.hints.get("paths") or []
            if paths:
                self.on_drop(index, list(paths))
                return True
        return False
