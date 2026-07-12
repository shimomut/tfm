"""TextViewer — a modal syntax-highlighting text viewer for the PuiKit port.

The PuiKit counterpart to ttk TFM's ``TextViewer``: a full-window read-only
viewer with line numbers, vertical + horizontal scroll, line wrapping, and
optional pygments syntax highlighting (a soft dependency — without it the text
shows plain). Search (``/``) highlights matches and ``n`` / ``N`` step between
them.

Content is drawn in a fixed-advance face so the line-number gutter, horizontal
scroll, and search highlights line up by column on the GUI as well as the TUI.
File reading goes through ``tfm_path.Path`` so it works for every storage
backend. Push it with :func:`show_text_viewer`.

Keys: ↑/↓/PageUp/PageDown/Home/End scroll vertically; ←/→ scroll horizontally
(when not wrapping); ``w`` toggles wrap; ``/`` searches, ``n``/``N`` next/prev;
``q`` or Esc closes.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.font import Font
from puikit.panel import Rect
from puikit.text import elide
from puikit.widgets.base import Widget

from tfm_text_dialog import keys_markdown, show_markdown

try:
    from pygments.lexers import get_lexer_for_filename, get_lexer_by_name, TextLexer
    from pygments.util import ClassNotFound
    _PYGMENTS = True
except ImportError:
    _PYGMENTS = False

#: Content is fixed-advance so columns (gutter, h-scroll, highlights) align.
MONO = Font(monospace=True)
_TAB = 8


def _content_bg(theme) -> tuple[int, int, int] | None:
    """The file-pane content surface, so a full-window viewer sits on TFM's own
    background instead of the lighter ``popup_bg`` (which reads as a floating
    menu). Falls back to ``popup_bg`` for a theme without surface roles."""
    if theme is None:
        return None
    return theme.surface_bg("content") or getattr(theme, "popup_bg", None)


def _status_bg(theme) -> tuple[int, int, int] | None:
    """The themed status-bar surface — the same ``status`` role the main window's
    bottom bar uses (its theme recipe / headroom pass already guarantees legible
    chrome text) — so a full-window viewer ends in a bar consistent with TFM
    proper instead of a dim hint on the content background. Falls back to the
    content surface for a theme without the role."""
    if theme is None:
        return None
    return theme.surface_bg("status") or _content_bg(theme)


def _header_bg(theme) -> tuple[int, int, int] | None:
    """The themed header surface — the same ``header`` role the main window's pane
    header bars use — so a viewer's title reads as a distinct band above the
    content rather than text floating on the content background. Falls back to the
    content surface for a theme without the role."""
    if theme is None:
        return None
    return theme.surface_bg("header") or _content_bg(theme)


def draw_status_bar(ctx, y: float, text: str, *, font=None, pad_x: float = 0.0,
                    bottom_pad: float = 0.0) -> None:
    """Paint a viewer's bottom status bar, exactly like the main window's
    ``StatusBar``: the ``status`` surface fills the **full** window width (edge to
    edge) and reaches the bottom edge (``bottom_pad`` extra height below the row),
    while only the *text* is inset — ``pad_x`` from the left. The bar text is
    auto-inked so it reads on every theme's status recipe. ``font`` pins a fixed
    advance where the caller needs columns to line up (the search field)."""
    wu, _hu = ctx.size_units
    theme = ctx.theme
    bar_bg = _status_bg(theme)
    fg = theme.muted_text if theme is not None else (150, 150, 150)
    ctx.fill_rect(0, y, wu, 1.0 + bottom_pad, Style(bg=bar_bg))
    label = elide(text, max(0.0, wu - 2 * pad_x), where="end", measure=ctx.measure_text)
    ctx.draw_text(pad_x, y, label, Style(fg=fg, bg=bar_bg, font=font))


#: Content inset for the full-window modal viewers (text / diff / directory diff),
#: matching the main window's ``BAR_PAD_PX``. A viewer fills the window with its
#: own surface and draws its chrome (header, gutter, rows, scrollbars, footer)
#: inset by this much, so it breathes in from the frame the same amount TFM's bars
#: and log do. GUI only — a character grid has no sub-cell, so it collapses flush.
VIEWER_PAD_PX = 4.0


def viewer_pad(ctx) -> tuple[float, float]:
    """The (x, y) content inset for a modal viewer, in base units: ``VIEWER_PAD_PX``
    device pixels on a vector backend, zero on a character grid. The bars keep
    their full-width surfaces (see :func:`draw_status_bar`); only text and the
    scrolling body are inset by this, so a viewer breathes in like the main
    window's chrome rather than sitting in a bordered card."""
    if not ctx.vector_shapes:
        return (0.0, 0.0)
    bw, bh = ctx.base_size
    return (VIEWER_PAD_PX / bw if bw else 0.0, VIEWER_PAD_PX / bh if bh else 0.0)

#: pygments token category → RGB — the default syntax palette (VS Code Dark+),
#: categorised by substring of the token name (mirroring ttk TFM's
#: ``get_syntax_color``). A theme overrides any subset of these via its
#: ``extras['syntax']`` (see :func:`_syntax_palette` and tfm.py's ``_theme``); the
#: viewer bakes the resolved palette at show time.
DEFAULT_SYNTAX = {
    "keyword": (86, 156, 214),
    "string": (206, 145, 120),
    "comment": (106, 153, 85),
    "number": (181, 206, 168),
    "operator": (212, 212, 212),
    "builtin": (78, 201, 176),
    "name": (156, 220, 254),
}
_ERROR_FG = (229, 110, 110)
#: Search-match highlight = the content background blended toward amber; the
#: current match is a firmer blend. Derived (not a fixed dark constant) so the
#: highlight tracks the theme — a dark wash on a dark theme, a pale one on light.
_MATCH_HUE = (200, 175, 55)
_MATCH_TINT = 0.24
_CURRENT_MATCH_TINT = 0.46


def _mix(a, b, t):
    """Linear RGB blend a→b by ``t`` (0..1)."""
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _is_light(bg) -> bool:
    """True when ``bg`` is a light surface (Rec.601 luma). Lets a caller flip a
    polarity-dependent choice — e.g. keep the dark-tuned syntax palette exact on
    a dark theme but let auto-ink re-tone it for a light one."""
    if bg is None:
        return False
    return (0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]) >= 140


def _match_bg(content, current: bool):
    """Search-highlight background for ``content``, firmer for the current match."""
    return _mix(content or (30, 30, 38), _MATCH_HUE,
                _CURRENT_MATCH_TINT if current else _MATCH_TINT)


def _syntax_palette(panel) -> dict:
    """The active theme's text-viewer syntax palette — its ``extras['syntax']``
    merged onto :data:`DEFAULT_SYNTAX` — resolved from ``panel.theme`` at show
    time. A theme names only the tokens it wants to recolor; the rest fall back to
    the VS Code default. Resolved once when the viewer opens (the modal viewer
    swallows the theme-toggle key, so the palette can't change while it is up)."""
    theme = getattr(panel, "theme", None)
    extra = theme.extras.get("syntax") if theme is not None else None
    return {**DEFAULT_SYNTAX, **extra} if extra else DEFAULT_SYNTAX

_EXT_LEXERS = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".json": "json",
    ".md": "markdown", ".yml": "yaml", ".yaml": "yaml", ".xml": "xml",
    ".html": "html", ".css": "css", ".sh": "bash", ".bash": "bash", ".c": "c",
    ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".java": "java", ".go": "go",
    ".rs": "rust", ".php": "php", ".rb": "ruby", ".sql": "sql", ".ini": "ini",
    ".cfg": "ini", ".conf": "ini", ".toml": "toml",
}


def _expand_tabs(line: str) -> str:
    """Column-aware tab expansion to ``_TAB`` stops."""
    if "\t" not in line:
        return line
    out: list[str] = []
    col = 0
    for ch in line:
        if ch == "\t":
            n = _TAB - (col % _TAB)
            out.append(" " * n)
            col += n
        else:
            out.append(ch)
            col += 1
    return "".join(out)


def _syntax_fg(token_type, palette: dict) -> tuple[int, int, int] | None:
    name = str(token_type)
    if "Keyword" in name:
        return palette["keyword"]
    if "String" in name:
        return palette["string"]
    if "Comment" in name:
        return palette["comment"]
    if "Number" in name:
        return palette["number"]
    if "Operator" in name or "Punctuation" in name:
        return palette["operator"]
    if "Builtin" in name:
        return palette["builtin"]
    if "Name" in name:
        return palette["name"]
    return None  # default text color


def _read_lines(path) -> tuple[list[str], bool]:
    """Read ``path`` into display lines (tabs expanded). Returns ``(lines,
    is_error)``; a binary file yields a one-line placeholder with error=True."""
    content = None
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            content = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except (FileNotFoundError, OSError) as exc:
            return [f"Error reading file: {exc}"], True
    if content is None:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            return [f"Error reading file: {exc}"], True
        if b"\x00" in raw[:1024]:
            return ["[Binary file — cannot display as text]"], True
        content = raw.decode("latin-1", errors="replace")
    return [_expand_tabs(line) for line in content.splitlines()], False


def _highlight(lines: list[str], path, palette: dict | None = None) -> list[list[tuple[str, Any]]]:
    """Map each line to a list of ``(text, fg)`` segments, colored per ``palette``
    (a token-category → RGB map; the active theme's syntax palette, defaulting to
    :data:`DEFAULT_SYNTAX`). With pygments off (or on failure) each line is a
    single default-colored segment."""
    palette = {**DEFAULT_SYNTAX, **(palette or {})}
    plain = [[(line, None)] for line in lines]
    if not _PYGMENTS or not lines:
        return plain
    try:
        try:
            lexer = get_lexer_for_filename(path.name)
        except ClassNotFound:
            lexer = get_lexer_by_name(_EXT_LEXERS[path.suffix.lower()]) \
                if path.suffix.lower() in _EXT_LEXERS else TextLexer()
        text = "\n".join(lines)
        result: list[list[tuple[str, Any]]] = []
        current: list[tuple[str, Any]] = []
        for token_type, value in lexer.get_tokens(text):
            fg = _syntax_fg(token_type, palette)
            if "\n" in value:
                parts = value.split("\n")
                if parts[0]:
                    current.append((parts[0], fg))
                result.append(current)
                for part in parts[1:-1]:
                    result.append([(part, fg)] if part else [])
                current = [(parts[-1], fg)] if parts[-1] else []
            elif value:
                current.append((value, fg))
        if current:
            result.append(current)
        if not result:
            return plain
        # Keep exactly one row per source line: pygments' token stream ends at
        # the last real newline, so a file ending in blank line(s) yields fewer
        # rows than splitlines() — pad with empty rows (drawing bounds line_idx
        # by self.lines, then indexes self.highlighted, so a short list crashes).
        result = result[:len(lines)]
        result += [[] for _ in range(len(lines) - len(result))]
        return result
    except Exception:
        return plain


def draw_hscrollbar(ctx, x: float, y: float, w: float, left: float,
                    content_w: int, max_line: int) -> None:
    """Draw a horizontal scrollbar spanning ``w`` columns in the row at ``y``.
    ``left`` is the first visible column, ``content_w`` the visible width, and
    ``max_line`` the longest line. A thin convenience wrapper that computes the
    thumb position/ratio and defers to the ``draw_scrollbar`` primitive (which
    renders the bar at the vertical bar's thickness, centered in the row).

    The viewer's surface (``popup_bg``) is passed so the half-block bar's upper
    half blends with the client area on a character grid."""
    ratio = min(1.0, content_w / max_line) if max_line > 0 else 1.0
    denom = max_line - content_w
    pos = max(0.0, min(1.0, left / denom)) if denom > 0 else 0.0
    surface = _content_bg(ctx.theme)
    ctx.draw_scrollbar(x, y, w, pos, ratio, orientation="horizontal", surface=surface)


class _ScrollBody(Widget):
    """A clip region whose draw delegates to a callback. Lets a viewer render its
    scrolling rows at a *fractional* vertical offset (smooth GUI scroll): the
    partial top/bottom rows are trimmed by this child's clip instead of bleeding
    into the header/footer the parent drew."""

    def __init__(self, render):
        self._render = render

    def draw(self, ctx) -> None:
        self._render(ctx)


class TextViewer(Widget):
    """Full-window modal text viewer. Construct via :func:`show_text_viewer`."""

    focusable = True

    def __init__(self, path, *, syntax: dict | None = None):
        self.path = path
        self.lines, self.is_error = _read_lines(path)
        self.highlighted = _highlight(self.lines, path, syntax)
        self._panel: Any = None
        self._child_z = 90  # z for the help overlay; raised above this viewer in show_
        self.top = 0.0       # first visible display row (vertical scroll)
        self.left = 0.0      # horizontal scroll, columns — float for smooth pan
        self.wrap = False
        self._view_h = 1
        self._content_w = 1
        self._max_line = max((len(line) for line in self.lines), default=0)
        # Wrap layout cache: keyed on content width, maps display row -> (line,
        # chunk) so wrapped rows virtualize without re-splitting every frame.
        self._wrap_w = -1
        self._row_map: list[tuple[int, int]] = []
        # Search state.
        self.searching = False       # the search bar is open / being typed
        self.pattern = ""
        self.matches: list[int] = []  # source line indices containing pattern
        self.match_pos = -1
        # Layout captured each draw, read by the clipped scroll body.
        self._body = _ScrollBody(self._draw_rows)
        self._gutter = 2
        self._content_x = 2
        self._bg = self._text_fg = self._muted = None

    # --- layout helpers ------------------------------------------------------

    def _gutter_w(self) -> int:
        return len(str(max(1, len(self.lines)))) + 1

    def _rebuild_wrap(self, content_w: int) -> None:
        if self.wrap and self._wrap_w == content_w:
            return
        self._wrap_w = content_w
        row_map: list[tuple[int, int]] = []
        for i, line in enumerate(self.lines):
            chunks = max(1, math.ceil(len(line) / content_w)) if content_w > 0 else 1
            for c in range(chunks):
                row_map.append((i, c))
        self._row_map = row_map

    def _total_rows(self) -> int:
        return len(self._row_map) if self.wrap else len(self.lines)

    def _clamp(self) -> None:
        max_top = max(0, self._total_rows() - self._view_h)
        self.top = max(0.0, min(self.top, float(max_top)))
        # No horizontal scroll while wrapping; otherwise clamp to the content.
        self.left = 0.0 if self.wrap else max(0.0, min(self.left, float(max(0, self._max_line - 1))))

    # --- search --------------------------------------------------------------

    def _recompute_matches(self) -> None:
        pat = self.pattern.lower()
        self.matches = [i for i, line in enumerate(self.lines) if pat in line.lower()] \
            if pat else []
        self.match_pos = 0 if self.matches else -1
        if self.matches:
            self._scroll_to_line(self.matches[0])

    def _step_match(self, delta: int) -> None:
        if not self.matches:
            return
        self.match_pos = (self.match_pos + delta) % len(self.matches)
        self._scroll_to_line(self.matches[self.match_pos])

    def _scroll_to_line(self, line: int) -> None:
        if self.wrap:
            for row, (src, chunk) in enumerate(self._row_map):
                if src == line and chunk == 0:
                    self.top = float(row)
                    break
        else:
            self.top = float(line)
        self._clamp()

    # --- drawing -------------------------------------------------------------

    def draw(self, ctx) -> None:
        self._panel = ctx.panel
        theme = ctx.theme
        wu, hu = ctx.size_units  # exact (sub-cell) extent — anchor chrome to it
        # Like the main window: the chrome surfaces fill the whole window, only
        # text and the scrolling body are inset (pad_x left/right, pad_y for the
        # header's top and the footer's bottom). Scroll is the only pointer event
        # and carries no position, so the geometry needs no un-insetting.
        pad_x, pad_y = viewer_pad(ctx)
        bg = _content_bg(theme)  # sit on TFM's own pane background, not popup_bg
        ctx.fill_rect(0, 0, wu, hu, Style(bg=bg))

        text_fg = theme.text if theme is not None else (212, 212, 212)
        muted = theme.muted_text if theme is not None else (150, 150, 150)
        accent = theme.accent if theme is not None else (0, 122, 204)

        # Header — a distinct 'header' surface band across the top (reaching the
        # top edge, like the main window's pane headers), with the text inset from
        # the top/left/right.
        head_h = 1.0 + pad_y
        header_bg = _header_bg(theme)
        ctx.fill_rect(0, 0, wu, head_h, Style(bg=header_bg))
        total = len(self.lines)
        pos = int(self.top) + 1
        iw = max(1.0, wu - 2 * pad_x)            # content width inside the l/r pad
        header = f" {self.path.name}  ({total} lines)"
        ctx.draw_text(pad_x, pad_y, elide(header, iw, where="end", measure=ctx.measure_text),
                      Style(fg=accent, bg=header_bg, attr=TextAttribute.BOLD))
        info = f"{pos}/{total}  {'WRAP' if self.wrap else ''} "
        ctx.draw_text(max(pad_x, wu - pad_x - len(info)), pad_y, info, Style(fg=muted, bg=header_bg))

        gutter_w = self._gutter_w()
        self._gutter = gutter_w
        self._content_x = gutter_w
        self._content_w = max(1, int(iw) - gutter_w - 1)
        # Fractional visible width for the h-scrollbar thumb (columns can be
        # sub-cell); text still lays out on the whole-column ``_content_w``.
        content_wf = max(1.0, iw - gutter_w - 1)
        self._bg, self._text_fg, self._muted = bg, text_fg, muted
        # The footer takes one row plus its bottom pad (its status surface reaches
        # the bottom edge). A horizontal scrollbar (no-wrap only) steals a row when
        # a line overruns the width. (``head_h`` was set with the header above.)
        fy = hu - 1.0 - pad_y                     # footer text row (surface below)
        show_hbar = not self.wrap and self._max_line > self._content_w
        hbar_y = fy - 1.0                          # h-scrollbar, just above footer
        body_h = (hbar_y if show_hbar else fy) - head_h
        self._view_h = max(1, int(body_h))
        if self.wrap:
            self._rebuild_wrap(self._content_w)
        self._clamp()

        # Scrolling rows live in a clipped child, inset by the l/r pad and sitting
        # below the header; a fractional self.top renders partial top/bottom rows.
        ctx.draw_child(self._body, pad_x, head_h, iw, body_h)

        # Vertical scrollbar, at the content's right edge (inset by the l/r pad).
        total_rows = self._total_rows()
        if total_rows > self._view_h:
            ratio = min(1.0, body_h / total_rows)
            denom = total_rows - self._view_h
            sbpos = self.top / denom if denom > 0 else 0.0
            ctx.draw_scrollbar(wu - pad_x - 1, head_h, body_h,
                               max(0.0, min(1.0, sbpos)), ratio)

        # Horizontal scrollbar, in the row between the content and the footer.
        if show_hbar:
            draw_hscrollbar(ctx, pad_x + self._content_x, hbar_y, content_wf,
                            self.left, content_wf, self._max_line)

        # Footer status bar — full-width 'status' surface reaching the bottom edge,
        # its text inset by the l/r pad, matching the main window's StatusBar.
        if self.searching or self.pattern:
            n = len(self.matches)
            here = (self.match_pos + 1) if n else 0
            label = f" /{self.pattern}"
            if not self.searching:
                label += f"   [{here}/{n}]" if n else "   (no matches)"
            draw_status_bar(ctx, fy, label, font=MONO, pad_x=pad_x, bottom_pad=pad_y)
        else:
            hint = " ↑↓ scroll · ←→ pan · w wrap · / search · n/N next · q close "
            draw_status_bar(ctx, fy, hint, pad_x=pad_x, bottom_pad=pad_y)

    def _draw_rows(self, ctx) -> None:
        """Render the visible rows into the clipped body. ``self.top``'s fractional
        part shifts every row up by ``frac``, so the first/last rows are partial
        (smooth scroll); the body's clip trims them at the content edges."""
        first = int(self.top)
        frac = self.top - first
        # Two extra rows, not one: a fractional body height (the l/r-padded viewer
        # rarely lands on a whole cell) plus the fractional scroll offset can push
        # the visible span up to two rows past the whole count, so the partial
        # bottom row is always drawn to be clipped rather than vanishing early.
        for vis in range(self._view_h + 2):
            row = first + vis
            if row >= self._total_rows():
                break
            y = vis - frac
            if self.wrap:
                line_idx, chunk = self._row_map[row]
                col0 = float(chunk * self._content_w)
                show_no = chunk == 0
            else:
                line_idx, col0, show_no = row, self.left, True
            # Content first, then the gutter — the gutter fill masks the partial
            # left column that a fractional horizontal offset bleeds leftward.
            self._draw_line(ctx, y, line_idx, col0)
            ctx.fill_rect(0, y, self._content_x, 1.0, Style(bg=self._bg))
            if show_no:
                num = str(line_idx + 1).rjust(self._gutter - 1)
                ctx.draw_text(0, y, num, Style(fg=self._muted, bg=self._bg, font=MONO))

    def _draw_line(self, ctx, y, line_idx, col0) -> None:
        """Draw source line ``line_idx`` showing columns [col0, col0+content_w).
        ``col0`` may be fractional: the view shifts left by its fractional part
        (``xfrac``) for smooth horizontal scroll, with one extra column drawn so
        the right edge fills; the gutter (drawn after) masks the left bleed."""
        content_x, text_fg, bg = self._content_x, self._text_fg, self._bg
        col0_int = int(col0)
        xfrac = col0 - col0_int
        window_end = col0_int + self._content_w + (1 if xfrac > 0 else 0)
        col = 0
        for text, fg in self.highlighted[line_idx]:
            seg_end = col + len(text)
            vis_start = max(col, col0_int)
            vis_end = min(seg_end, window_end)
            if vis_end > vis_start:
                sub = text[vis_start - col: vis_end - col]
                style_fg = _ERROR_FG if self.is_error else (fg if fg is not None else text_fg)
                # The syntax palette is tuned for a dark background, so on a dark
                # theme a real syntax color is kept exact (ink=False) and reads as
                # designed — recessive comments and all. On a light theme that same
                # palette would be unreadable, so auto-ink re-tones each token
                # (hue preserved, darkened to the light surface). The error color
                # and the uncolored fallback are always auto-inked.
                ctx.draw_text(content_x + (vis_start - col0_int) - xfrac, y, sub,
                              Style(fg=style_fg, bg=bg, font=MONO),
                              ink=self.is_error or fg is None or _is_light(bg))
            col = seg_end
            if col >= window_end:
                break
        # Overlay search highlights for this column window.
        if self.pattern:
            self._draw_matches(ctx, y, line_idx, col0_int, xfrac, window_end, content_x, text_fg)

    def _draw_matches(self, ctx, y, line_idx, col0_int, xfrac, window_end, content_x, text_fg) -> None:
        plain = self.lines[line_idx].lower()
        pat = self.pattern.lower()
        if not pat:
            return
        is_current = self.match_pos >= 0 and self.matches[self.match_pos] == line_idx
        start = 0
        while True:
            hit = plain.find(pat, start)
            if hit < 0:
                break
            s, e = hit, hit + len(pat)
            start = e
            vis_start = max(s, col0_int)
            vis_end = min(e, window_end)
            if vis_end <= vis_start:
                continue
            sub = self.lines[line_idx][vis_start:vis_end]
            hl_bg = _match_bg(self._bg, is_current)
            ctx.draw_text(content_x + (vis_start - col0_int) - xfrac, y, sub,
                          Style(fg=text_fg, bg=hl_bg, font=MONO))

    # --- events --------------------------------------------------------------

    def _close(self) -> None:
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.MOUSE_SCROLL:
            uy = event.hints.get("scroll_units")
            self.top -= float(uy) if uy is not None else float(event.scroll)
            ux = event.hints.get("scroll_units_x")  # precise horizontal swipe
            if ux is not None and not self.wrap:
                self.left -= float(ux)
            self._clamp()
            return True
        if event.type is not EventType.KEY:
            return True  # modal: swallow non-key events
        key = event.key
        if self.searching:
            self._handle_search_key(event)
            return True
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
            self.top = float(max(0, self._total_rows() - self._view_h))
        elif key == "right" and not self.wrap:
            self.left += 4
        elif key == "left" and not self.wrap:
            self.left = max(0.0, self.left - 4)
        elif event.char == "w":
            self.wrap = not self.wrap
            self.left = 0.0
            self._wrap_w = -1
        elif event.char == "/":
            self.searching = True
            self.pattern = ""
            self.matches = []
            self.match_pos = -1
        elif event.char == "n":
            self._step_match(1)
        elif event.char == "N":
            self._step_match(-1)
        elif event.char == "?":
            self._show_help()
        self._clamp()
        return True

    def _show_help(self) -> None:
        if self._panel is None:
            return
        rows = [
            ("↑ / ↓", "scroll line"),
            ("PgUp / PgDn", "scroll page"),
            ("Home / End", "top / bottom"),
            ("← / →", "scroll horizontally (no-wrap)"),
            ("w", "toggle line wrap"),
            ("/", "search"),
            ("n / N", "next / prev match"),
            ("?", "this help"),
            ("q / Esc", "close"),
        ]
        show_markdown(self._panel, keys_markdown(rows),
                      title="Text Viewer — Keys", z=self._child_z)

    def _handle_search_key(self, event: Event) -> None:
        key = event.key
        if key == "escape":
            self.searching = False
            self.pattern = ""
            self.matches = []
            self.match_pos = -1
        elif key == "enter":
            self.searching = False  # keep pattern + matches for n/N
        elif key == "backspace":
            self.pattern = self.pattern[:-1]
            self._recompute_matches()
        elif event.char and event.char.isprintable():
            self.pattern += event.char
            self._recompute_matches()


def show_text_viewer(panel: Any, path, z: int = 80) -> TextViewer:
    """Push a full-window modal :class:`TextViewer` over ``panel``. The ``reflow``
    callback re-derives the layer rect from the live window size each render, so
    the viewer follows terminal / window resizes."""
    viewer = TextViewer(path, syntax=_syntax_palette(panel))
    sw, sh = panel.backend.size_units
    viewer._panel = panel
    viewer._child_z = z + 10  # help overlay stacks above the viewer's own layer
    panel.push_layer(viewer, z=z, hints={"x": 0, "y": 0, "w": sw, "h": sh},
                     reflow=lambda sw, sh: Rect(0, 0, sw, sh))
    panel.animate(viewer, hints={"transition": "fade", "duration_ms": 120})
    return viewer
