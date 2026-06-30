"""FilterListDialog — a modal, filterable list picker for the PuiKit port.

This is the PuiKit equivalent of TFM/ttk's ``BaseListDialog`` workhorse: a modal
overlay with a **filter text field** on top of a **scrollable list**, used for
discrete selection (favorites, drives, programs, …). It reuses PuiKit primitives
rather than re-implementing them:

- ``TextEdit`` for the filter field — so it carries the real caret, selection,
  clipboard, and (crucially) focus-gated IME. Because the dialog is a
  ``FocusContainer`` and the *top layer is the focus root*, the field's
  ``wants_text_input`` engages the backend's text-input system while the dialog
  is open and releases it when the dialog closes — no app branching.
- ``ListView`` for the results — virtualized draw, smooth scroll, a scrollbar,
  and ``on_select`` activation, all for free.

Interaction matches the ttk dialog: typing filters the list (substring,
case-insensitive); ↑/↓/PageUp/PageDown move the selection; Enter accepts the
selected value; Esc cancels; a click selects/activates a row. The dialog is
modal — it owns events while open — and reports its outcome through
``on_accept(value)`` / ``on_cancel()``.

Push it with :func:`show_filter_list`, which sizes and centers the layer with the
shared shadow / dim-below intent the other PuiKit modals use.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.focus import FocusContainer, focus_on_click
from puikit.panel import Rect
from puikit.widgets.base import Widget
from puikit.widgets.list import ListView
from puikit.widgets.text_edit import TextEdit

#: Navigation keys the *list* owns even while the filter field holds focus —
#: typing filters, but the arrows still drive the selection (the ttk behavior).
#: Backend key names are unsuffixed ("pageup"/"pagedown"), matching ListView.
_LIST_KEYS = frozenset({"up", "down", "pageup", "pagedown"})


class FilterListDialog(FocusContainer, Widget):
    """Modal filter-list picker. Construct via :func:`show_filter_list`, which
    sizes and pushes the layer; this class owns layout, focus, and events."""

    focusable = True
    # Always handles keys itself (escape closes), so it is a focus stop even when
    # the filtered list is momentarily empty.
    focus_stop_when_empty = True

    def __init__(
        self,
        items: Sequence[Any],
        *,
        title: str = "",
        to_label: Callable[[Any], str] = str,
        on_accept: Callable[[Any], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ):
        self.all_items = list(items)
        self.to_label = to_label
        self.title = title
        self.on_accept = on_accept
        self.on_cancel = on_cancel
        self._panel: Any = None
        # Values currently passing the filter, parallel to ``self.list.items``.
        self.filtered: list[Any] = list(self.all_items)

        self.filter_edit = TextEdit(on_change=self._refilter)
        self.list = ListView(
            [self.to_label(v) for v in self.all_items],
            on_select=lambda i, _label: self._accept_index(i),
        )
        # The filter field holds focus so typing flows there and the IME engages;
        # the arrows are routed to the list explicitly (see handle_event).
        self._focused: Any = self.filter_edit
        self._filter_rect = Rect(0.0, 0.0, 0.0, 0.0)
        self._list_rect = Rect(0.0, 0.0, 0.0, 0.0)
        self._size: tuple[float, float] = (0.0, 0.0)

    # --- focus ---------------------------------------------------------------

    def focus_children(self) -> list[Any]:
        return [self.filter_edit]

    # --- filtering -----------------------------------------------------------

    def _refilter(self, text: str) -> None:
        q = text.lower()
        self.filtered = [v for v in self.all_items if q in self.to_label(v).lower()]
        self.list.set_items([self.to_label(v) for v in self.filtered])
        self.list.selected = 0

    # --- outcome -------------------------------------------------------------

    def _accept_index(self, index: int) -> None:
        if 0 <= index < len(self.filtered):
            value = self.filtered[index]
            self._close()
            if self.on_accept is not None:
                self.on_accept(value)

    def _cancel(self) -> None:
        self._close()
        if self.on_cancel is not None:
            self.on_cancel()

    def _close(self) -> None:
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()

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

        # Filter field — one row, focused so the caret blinks and the IME stays on.
        self._filter_rect = Rect(2.0, y, max(1.0, wu - 4.0), 1.0)
        ctx.draw_child(
            self.filter_edit, self._filter_rect.x, self._filter_rect.y,
            self._filter_rect.w, self._filter_rect.h, hints={"focused": True},
        )
        y += 2

        # Result list fills the rest, above the bottom padding.
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
            if key == "escape":
                self._cancel()
            elif key == "enter":
                self._accept_index(self.list.selected)
            elif key in _LIST_KEYS:
                self.list.handle_event(event)  # arrows drive the list selection
            else:
                self.filter_edit.handle_event(event)  # typing/editing filters
            return True

        if event.type in (
            EventType.MOUSE_DOWN, EventType.MOUSE_UP, EventType.MOUSE_CLICK,
            EventType.MOUSE_DRAG, EventType.MOUSE_SCROLL,
        ):
            if event.x is not None and self._list_rect.contains(event.x, event.y):
                local = event.translated(-self._list_rect.x, -self._list_rect.y)
                self.list.handle_event(local)
            elif event.x is not None and self._filter_rect.contains(event.x, event.y):
                if event.type is EventType.MOUSE_DOWN:
                    focus_on_click(self, self.filter_edit)
                local = event.translated(-self._filter_rect.x, -self._filter_rect.y)
                self.filter_edit.handle_event(local)
            elif event.type is EventType.MOUSE_CLICK and event.x is not None and not (
                0 <= event.x < self._size[0] and 0 <= event.y < self._size[1]
            ):
                self._cancel()  # click outside the dialog dismisses it
            return True
        return True  # modal: swallow everything else


def show_filter_list(
    panel: Any,
    items: Sequence[Any],
    *,
    title: str = "",
    to_label: Callable[[Any], str] = str,
    on_accept: Callable[[Any], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
    region: tuple[float, float] | None = None,
    z: int = 70,
) -> FilterListDialog:
    """Push a modal :class:`FilterListDialog` over ``panel`` and return it.

    Sized to a comfortable fraction of the window and centered, with the shared
    shadow + dim-below modal intent. The chosen value is reported through
    ``on_accept``; ``on_cancel`` fires on escape / outside-click.

    ``region`` is an optional ``(x, width)`` column span (in base units) to anchor
    the dialog within instead of the whole window — used to place a pane-targeting
    picker (favorites, drives, …) over the active pane, so the user can tell which
    pane it will act on. The dialog is centered within the region and never wider
    than it."""
    dialog = FilterListDialog(
        items, title=title, to_label=to_label, on_accept=on_accept, on_cancel=on_cancel,
    )
    sw, sh = panel.backend.size_units
    w = max(36.0, min(sw * 0.6, 72.0))
    h = max(8.0, min(sh * 0.6, float(len(items) + 5)))
    hints: dict[str, Any] = {"shadow": True, "dim_below": True, "w": w, "h": h}
    if region is not None:
        region_x, region_w = region
        # Constrain to the region and center within it; clamp on-screen so a
        # narrow pane near the window edge still shows the whole dialog.
        w = min(w, region_w)
        hints["w"] = w
        hints["x"] = max(0.0, min(region_x + (region_w - w) / 2.0, sw - w))
    dialog._panel = panel
    panel.push_layer(dialog, z=z, hints=hints)
    panel.animate(dialog, hints={"transition": "fade", "duration_ms": 150})
    return dialog
