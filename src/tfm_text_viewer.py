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
from puikit.widgets.base import Widget

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

#: pygments token category → RGB (a VS Code-dark-ish palette). Categorised by
#: substring of the token name, mirroring ttk TFM's ``get_syntax_color``.
_SYNTAX = {
    "keyword": (86, 156, 214),
    "string": (206, 145, 120),
    "comment": (106, 153, 85),
    "number": (181, 206, 168),
    "operator": (212, 212, 212),
    "builtin": (78, 201, 176),
    "name": (156, 220, 254),
}
_ERROR_FG = (229, 110, 110)
_MATCH_BG = (78, 78, 40)
_CURRENT_MATCH_BG = (122, 102, 40)

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


def _syntax_fg(token_type) -> tuple[int, int, int] | None:
    name = str(token_type)
    if "Keyword" in name:
        return _SYNTAX["keyword"]
    if "String" in name:
        return _SYNTAX["string"]
    if "Comment" in name:
        return _SYNTAX["comment"]
    if "Number" in name:
        return _SYNTAX["number"]
    if "Operator" in name or "Punctuation" in name:
        return _SYNTAX["operator"]
    if "Builtin" in name:
        return _SYNTAX["builtin"]
    if "Name" in name:
        return _SYNTAX["name"]
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


def _highlight(lines: list[str], path) -> list[list[tuple[str, Any]]]:
    """Map each line to a list of ``(text, fg)`` segments. With pygments off (or
    on failure) each line is a single default-colored segment."""
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
            fg = _syntax_fg(token_type)
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
        # pygments appends a trailing newline; keep the row count aligned.
        return result[:len(lines)] if result else plain
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

    def __init__(self, path):
        self.path = path
        self.lines, self.is_error = _read_lines(path)
        self.highlighted = _highlight(self.lines, path)
        self._panel: Any = None
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
        w, h = ctx.width, ctx.height
        wu, hu = ctx.size_units  # exact (sub-cell) extent — anchor chrome to it
        bg = _content_bg(theme)  # sit on TFM's own pane background, not popup_bg
        ctx.fill_rect(0, 0, wu, hu, Style(bg=bg))

        text_fg = theme.text if theme is not None else (212, 212, 212)
        muted = theme.muted_text if theme is not None else (150, 150, 150)
        accent = theme.accent if theme is not None else (0, 122, 204)

        # Header.
        total = len(self.lines)
        pos = int(self.top) + 1
        header = f" {self.path.name}  ({total} lines)"
        ctx.draw_text(0, 0, header[:w], Style(fg=accent, bg=bg, attr=TextAttribute.BOLD))
        info = f"{pos}/{total}  {'WRAP' if self.wrap else ''} "
        ctx.draw_text(max(0, wu - len(info)), 0, info, Style(fg=muted, bg=bg))

        gutter_w = self._gutter_w()
        self._gutter = gutter_w
        self._content_x = gutter_w
        self._content_w = max(1, w - gutter_w - 1)
        # Fractional visible width for the h-scrollbar thumb (columns can be
        # sub-cell); text still lays out on the whole-column ``_content_w``.
        content_wf = max(1.0, wu - gutter_w - 1)
        self._bg, self._text_fg, self._muted = bg, text_fg, muted
        # A horizontal scrollbar (no-wrap only) steals a row when a line overruns
        # the content width; the header and footer always take one each. The
        # footer (and h-bar) anchor to ``hu`` so they sit flush with the pixel
        # bottom, not a fractional row above it; the body fills the exact gap.
        show_hbar = not self.wrap and self._max_line > self._content_w
        fy = hu - 1                              # footer, flush to the bottom
        hbar_y = hu - 2                           # h-scrollbar, just above it
        body_h = (hbar_y if show_hbar else fy) - 1
        self._view_h = max(1, int(body_h))
        if self.wrap:
            self._rebuild_wrap(self._content_w)
        self._clamp()

        # Scrolling rows live in a clipped child so a fractional self.top renders
        # a partial top/bottom row (smooth GUI scroll) without touching the header.
        ctx.draw_child(self._body, 0, 1, wu, body_h)

        # Vertical scrollbar. Thumb from the fractional visible height.
        total_rows = self._total_rows()
        if total_rows > self._view_h:
            ratio = min(1.0, body_h / total_rows)
            denom = total_rows - self._view_h
            sbpos = self.top / denom if denom > 0 else 0.0
            ctx.draw_scrollbar(wu - 1, 1, body_h,
                               max(0.0, min(1.0, sbpos)), ratio)

        # Horizontal scrollbar, in the row between the content and the footer.
        if show_hbar:
            draw_hscrollbar(ctx, self._content_x, hbar_y, content_wf,
                            self.left, content_wf, self._max_line)

        # Footer: search bar or hint.
        if self.searching or self.pattern:
            n = len(self.matches)
            here = (self.match_pos + 1) if n else 0
            label = f"/{self.pattern}"
            if not self.searching:
                label += f"   [{here}/{n}]" if n else "   (no matches)"
            ctx.draw_text(0, fy, label[:w], Style(fg=text_fg, bg=bg, font=MONO))
        else:
            hint = " ↑↓ scroll · ←→ pan · w wrap · / search · n/N next · q close "
            ctx.draw_text(0, fy, hint[:w], Style(fg=muted, bg=bg, attr=TextAttribute.DIM))

    def _draw_rows(self, ctx) -> None:
        """Render the visible rows into the clipped body. ``self.top``'s fractional
        part shifts every row up by ``frac``, so the first/last rows are partial
        (smooth scroll); the body's clip trims them at the content edges."""
        first = int(self.top)
        frac = self.top - first
        # One extra row so the partial bottom row is present to be clipped.
        for vis in range(self._view_h + 1):
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
                ctx.draw_text(content_x + (vis_start - col0_int) - xfrac, y, sub,
                              Style(fg=style_fg, bg=bg, font=MONO))
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
            hl_bg = _CURRENT_MATCH_BG if is_current else _MATCH_BG
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
        self._clamp()
        return True

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
    viewer = TextViewer(path)
    sw, sh = panel.backend.size_units
    viewer._panel = panel
    panel.push_layer(viewer, z=z, hints={"x": 0, "y": 0, "w": sw, "h": sh},
                     reflow=lambda sw, sh: Rect(0, 0, sw, sh))
    panel.animate(viewer, hints={"transition": "fade", "duration_ms": 120})
    return viewer
