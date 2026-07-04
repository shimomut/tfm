"""InputDialog — a modal single-line text prompt for the PuiKit port.

The text-entry counterpart to :class:`tfm_filter_list_dialog.FilterListDialog`: a
small centered modal with a title, a prompt label, and one ``TextEdit``. It is
the PuiKit equivalent of ttk TFM's ``QuickEditBar`` prompts — Create Directory,
Create File, Rename — collapsed into one reusable primitive.

Like the filter-list dialog it reuses PuiKit primitives rather than
re-implementing them:

- ``TextEdit`` for the field — real caret, selection, clipboard, and focus-gated
  IME. Because the dialog is a ``FocusContainer`` and the top layer is the focus
  root, the field's ``wants_text_input`` engages the backend's text-input system
  while the dialog is open and releases it when it closes.

Interaction: typing edits the field; Enter accepts (the text is handed to
``on_accept``); Esc or an outside click cancels. An optional ``validate(text)``
returning an error string keeps the dialog open and shows the message inline
(empty / duplicate names), so a bad value never silently closes the dialog.

Push it with :func:`show_input`, which sizes and centers the layer with the
shared drop-shadow intent the other PuiKit modals use, and can anchor it
over the active pane via ``region`` (the same contract as ``show_filter_list``).
"""

from __future__ import annotations

from typing import Any, Callable

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.focus import FocusContainer, focus_on_click
from puikit.panel import Rect
from puikit.widgets.base import Widget
from puikit.widgets.text_edit import TextEdit

from tfm_dialog_geometry import pane_anchored_box


class InputDialog(FocusContainer, Widget):
    """Modal single-line text prompt. Construct via :func:`show_input`, which
    sizes and pushes the layer; this class owns layout, focus, and events."""

    focusable = True
    # Always handles keys itself (escape closes), so it stays a focus stop.
    focus_stop_when_empty = True

    def __init__(
        self,
        *,
        title: str = "",
        prompt: str = "",
        text: str = "",
        on_accept: Callable[[str], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        on_change: Callable[[str], None] | None = None,
        validate: Callable[[str], str | None] | None = None,
        select_all: bool = True,
    ):
        self.title = title
        self.prompt = prompt
        self.on_accept = on_accept
        self.on_cancel = on_cancel
        #: Fires with the field's current text after every edit keystroke, for
        #: live-updating prompts (incremental search). Never fires on Enter/Esc.
        self.on_change = on_change
        self.validate = validate
        self._panel: Any = None
        self._error = ""

        self.edit = TextEdit(text=text)
        # Caret at the end. With ``select_all`` the whole value is also selected,
        # so the first keystroke replaces it (rename); without it the caret just
        # sits at the end, ready to append (jump-to-path's trailing separator).
        self.edit.cursor = len(text)
        self.edit._anchor = 0 if select_all else len(text)
        self._field_rect = Rect(0.0, 0.0, 0.0, 0.0)
        self._size: tuple[float, float] = (0.0, 0.0)

    # --- focus ---------------------------------------------------------------

    def focus_children(self) -> list[Any]:
        return [self.edit]

    # --- outcome -------------------------------------------------------------

    def _accept(self) -> None:
        text = self.edit.text
        if self.validate is not None:
            error = self.validate(text)
            if error:
                self._error = error
                if self._panel is not None:
                    self._panel.render()
                return
        self._close()
        if self.on_accept is not None:
            self.on_accept(text)

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
        wu, _ = ctx.size_units
        surface_bg = theme.popup_bg if theme is not None else None
        box_style = Style(bg=surface_bg, fg=theme.popup_border if theme else None)
        ctx.draw_box(0, 0, ctx.width, ctx.height, box_style, hints={"fill": True})

        pad = 1.0
        y = pad
        if self.title:
            ctx.draw_text(2, y, self.title, Style(bg=surface_bg, attr=TextAttribute.BOLD))
            y += 2

        # Prompt label + field on one row; the field fills the rest of the width.
        field_x = 2.0
        if self.prompt:
            ctx.draw_text(2, y, self.prompt, Style(bg=surface_bg))
            field_x = 2.0 + ctx.measure_text(self.prompt + " ")
        field_w = max(1.0, wu - field_x - 2.0)
        # The field's own ``width`` caps how wide its box draws, so stretch it to
        # the slot we hand it — otherwise it keeps its default 24u and leaves a gap
        # to the dialog's right edge.
        self.edit.width = field_w
        self._field_rect = Rect(field_x, y, field_w, 1.0)
        ctx.draw_child(
            self.edit, field_x, y, field_w, 1.0, hints={"focused": True},
        )
        y += 1

        if self._error:
            ctx.draw_text(2, y, self._error,
                          Style(bg=surface_bg, fg=(229, 110, 110), attr=TextAttribute.DIM))

    # --- events --------------------------------------------------------------

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.KEY:
            key = event.key
            if key == "escape":
                self._cancel()
            elif key == "enter":
                self._accept()
            else:
                # Editing clears a stale validation message as the user retypes.
                self._error = ""
                before = self.edit.text
                self.edit.handle_event(event)
                if self.on_change is not None and self.edit.text != before:
                    self.on_change(self.edit.text)
            return True

        if event.type in (
            EventType.MOUSE_DOWN, EventType.MOUSE_UP, EventType.MOUSE_CLICK,
            EventType.MOUSE_DRAG, EventType.MOUSE_SCROLL,
        ):
            if event.x is not None and self._field_rect.contains(event.x, event.y):
                if event.type is EventType.MOUSE_DOWN:
                    focus_on_click(self, self.edit)
                local = event.translated(-self._field_rect.x, -self._field_rect.y)
                self.edit.handle_event(local)
            elif event.type is EventType.MOUSE_CLICK and event.x is not None and not (
                0 <= event.x < self._size[0] and 0 <= event.y < self._size[1]
            ):
                self._cancel()  # click outside the dialog dismisses it
            return True
        return True  # modal: swallow everything else


def show_input(
    panel: Any,
    *,
    title: str = "",
    prompt: str = "",
    text: str = "",
    on_accept: Callable[[str], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
    on_change: Callable[[str], None] | None = None,
    validate: Callable[[str], str | None] | None = None,
    select_all: bool = True,
    region: tuple[float, float] | None = None,
    anchor: str = "center",
    z: int = 70,
) -> InputDialog:
    """Push a modal :class:`InputDialog` over ``panel`` and return it.

    Sized to a comfortable fraction of the window and centered, with the shared
    drop-shadow modal intent. The entered text is reported through
    ``on_accept``; ``on_cancel`` fires on escape / outside-click; ``on_change``
    fires live on every keystroke (incremental search). ``region`` is an optional
    ``(x, width)`` column span to anchor the dialog over the pane it acts on (see
    :func:`tfm_filter_list_dialog.show_filter_list`). ``anchor="top"`` pins the box
    near the top of the window instead of centering it, keeping the list below
    visible."""
    dialog = InputDialog(
        title=title, prompt=prompt, text=text,
        on_accept=on_accept, on_cancel=on_cancel, on_change=on_change,
        validate=validate, select_all=select_all,
    )
    sw, sh = panel.backend.size_units
    w = max(36.0, min(sw * 0.6, 64.0))
    # pad + [title + gap] + field + error row + pad. Error shares the row directly
    # below the field, so no blank line is reserved for it.
    h = 6.0 if title else 4.0
    hints: dict[str, Any] = {"shadow": True, "w": w, "h": h}
    if anchor == "top":
        hints["y"] = 2.0
    if region is not None:
        w, x = pane_anchored_box(w, sw, region)
        hints["w"] = w
        hints["x"] = x
    dialog._panel = panel
    panel.push_layer(dialog, z=z, hints=hints)
    panel.animate(dialog, hints={"transition": "fade", "duration_ms": 150})
    return dialog
