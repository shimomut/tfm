"""TextDialog — a modal scrollable-text viewer for the PuiKit port.

The read-only counterpart to the input / filter dialogs: a centered modal that
shows a title and a scrollable block of lines. It is the PuiKit equivalent of
ttk TFM's ``InfoDialog`` (help, file details, …).

It reuses PuiKit's ``ListView`` for the body — virtualized draw, smooth scroll,
a scrollbar, and ↑/↓/PageUp/PageDown navigation for free — and simply does not
act on a row selection: Enter and Esc both close the dialog. Push it with
:func:`show_text`, which sizes and centers the layer with the shared shadow /
dim-below intent the other PuiKit modals use.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.focus import FocusContainer
from puikit.panel import Rect
from puikit.widgets.base import Widget
from puikit.widgets.list import ListView

#: Keys the body list consumes for scrolling while the dialog is open. (Backend
#: key names are unsuffixed: "pageup"/"pagedown", matching ListView.)
_SCROLL_KEYS = frozenset({"up", "down", "pageup", "pagedown", "home", "end"})


class TextDialog(FocusContainer, Widget):
    """Modal scrollable-text viewer. Construct via :func:`show_text`, which sizes
    and pushes the layer; this class owns layout, focus, and events."""

    focusable = True
    focus_stop_when_empty = True

    def __init__(
        self,
        lines: Sequence[str],
        *,
        title: str = "",
        on_close: Callable[[], None] | None = None,
    ):
        self.title = title
        self.on_close = on_close
        self._panel: Any = None
        self.list = ListView([str(line) for line in lines])
        self._list_rect = Rect(0.0, 0.0, 0.0, 0.0)
        self._size: tuple[float, float] = (0.0, 0.0)

    # --- focus ---------------------------------------------------------------

    def focus_children(self) -> list[Any]:
        return [self.list]

    # --- outcome -------------------------------------------------------------

    def _close(self) -> None:
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()
        if self.on_close is not None:
            self.on_close()

    # --- drawing -------------------------------------------------------------

    def draw(self, ctx) -> None:
        self._panel = ctx.panel
        self._size = ctx.size_units
        theme = ctx.theme
        wu, hu = ctx.size_units
        surface_bg = theme.popup_bg if theme is not None else None
        box_style = Style(bg=surface_bg, fg=theme.popup_border if theme else None)
        ctx.draw_box(0, 0, ctx.width, ctx.height, box_style, hints={"fill": True})

        pad = 1.0
        y = pad
        if self.title:
            ctx.draw_text(2, y, self.title, Style(bg=surface_bg, attr=TextAttribute.BOLD))
            y += 1
        # A hint at the bottom of the title area.
        ctx.draw_text(2, y, "↑/↓ scroll · Esc close",
                      Style(bg=surface_bg, fg=theme.muted_text if theme else None,
                            attr=TextAttribute.DIM))
        y += 2

        list_h = max(1.0, hu - y - pad)
        self._list_rect = Rect(2.0, y, max(1.0, wu - 4.0), list_h)
        ctx.draw_child(
            self.list, self._list_rect.x, self._list_rect.y,
            self._list_rect.w, self._list_rect.h, hints={"focused": False},
        )

    # --- events --------------------------------------------------------------

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.KEY:
            key = event.key
            if key in ("escape", "enter"):
                self._close()
            elif key in _SCROLL_KEYS:
                self.list.handle_event(event)
            return True

        if event.type in (
            EventType.MOUSE_DOWN, EventType.MOUSE_UP, EventType.MOUSE_CLICK,
            EventType.MOUSE_DRAG, EventType.MOUSE_SCROLL,
        ):
            if event.x is not None and self._list_rect.contains(event.x, event.y):
                local = event.translated(-self._list_rect.x, -self._list_rect.y)
                self.list.handle_event(local)
            elif event.type is EventType.MOUSE_CLICK and event.x is not None and not (
                0 <= event.x < self._size[0] and 0 <= event.y < self._size[1]
            ):
                self._close()  # click outside dismisses
            return True
        return True  # modal: swallow everything else


def show_text(
    panel: Any,
    lines: Sequence[str],
    *,
    title: str = "",
    on_close: Callable[[], None] | None = None,
    z: int = 70,
) -> TextDialog:
    """Push a modal :class:`TextDialog` over ``panel`` and return it.

    Sized to a comfortable fraction of the window and centered, with the shared
    shadow + dim-below modal intent. Closes on Enter / Esc / outside-click."""
    dialog = TextDialog(lines, title=title, on_close=on_close)
    sw, sh = panel.backend.size_units
    w = max(48.0, min(sw * 0.7, 96.0))
    h = max(10.0, min(sh * 0.8, float(len(lines) + 6)))
    dialog._panel = panel
    panel.push_layer(dialog, z=z, hints={"shadow": True, "dim_below": True, "w": w, "h": h})
    panel.animate(dialog, hints={"transition": "fade", "duration_ms": 150})
    return dialog
