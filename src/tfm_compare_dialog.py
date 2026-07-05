"""CompareSelectDialog — the modal that builds a :class:`~tfm_compare_selection.CompareCriteria`
for the ``compare_selection`` action (ttk TFM's ``W`` key, rebuilt for PuiKit).

Three side-by-side radio columns pick the relation the other pane's counterpart
must satisfy for each attribute — **Size** (any/equal/differs), **Modified**
(any/same/newer/older), **Content** (any/equal/differs) — plus a checkbox to also
take items with no counterpart, and a **Selection** mode (replace vs. add to the
current selection). It reports the assembled criteria through ``on_result`` (or
``None`` on cancel); the engine and the app do the actual comparing and selecting.

Layout is hand-placed in :meth:`draw` and focus is a flat Tab ring over the
columns / checkbox / mode / buttons, mirroring :class:`ConflictDialog` — no nested
layout view or popup layers, so it composes cleanly inside a pushed modal.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Optional

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.focus import FocusContainer, move_focus
from puikit.widgets import Button, Checkbox, RadioGroup
from puikit.widgets.base import Widget
from puikit.widgets.checkbox import is_activate

from tfm_compare_selection import CompareCriteria
from tfm_dialog_geometry import draw_title_bar, pane_anchored_box

# Each column: header + (label, value) options. Labels double as the radio rows;
# values feed CompareCriteria. Defaults are all "any" (= legacy "by filename").
_SIZE = ("Size", [("any", "any"), ("equal", "equal"), ("differs", "differs")])
_MTIME = ("Modified", [("any", "any"), ("same", "same"),
                       ("newer", "newer"), ("older", "older")])
_CONTENT = ("Content", [("any", "any"), ("equal", "equal"), ("differs", "differs")])
_MODE = ("Selection", [("Replace", "replace"), ("Add", "add")])


def _layout_context(backend):
    """Build a ``LayoutContext`` for ``backend`` off-draw, so :meth:`show` can
    measure child heights (and thus size the box) before there is a DrawContext.
    Mirrors ``DrawContext.layout_context`` — the same capability resolution."""
    from puikit.layout import LayoutContext
    cw, ch = backend.base_size
    caps = backend.capabilities
    return LayoutContext(
        cw, ch,
        snap=not caps.supports("pixel_layout"),
        hairline=caps.supports("hairline"),
        native_menus=caps.supports("native_menus"),
        measure=backend.measure_text,
        line_height=backend.measure_line_height,
        scrollbar_units=backend.scrollbar_units,
        image_size=backend.image_size,
    )


class CompareSelectDialog(FocusContainer, Widget):
    """Modal criteria picker. Construct via :func:`show_compare_select`, which sizes
    and pushes the layer; this class owns layout, focus, and events."""

    focusable = True
    focus_stop_when_empty = True

    def __init__(self, on_result: Callable[[Optional[CompareCriteria]], None]):
        self.title = "Compare & Select"
        self.on_result = on_result
        self._panel: Any = None

        self._values = {}  # widget -> option value list, for reading the choice back
        self._size = self._radio(_SIZE)
        self._mtime = self._radio(_MTIME)
        self._content = self._radio(_CONTENT)
        self._mode = self._radio(_MODE)
        self._missing = Checkbox("also select items missing in the other pane",
                                 checked=False)
        self._select_btn = Button("Select", variant="primary",
                                  on_click=self._accept)
        self._cancel_btn = Button("Cancel", variant="secondary",
                                  on_click=lambda: self._finish(None))

        self._columns = [self._size, self._mtime, self._content]
        self._focused: Any = self._size  # start on the first comparison column
        self._child_rects: list[tuple[Any, tuple[float, float, float, float]]] = []

    def _radio(self, spec) -> RadioGroup:
        _header, options = spec
        group = RadioGroup([label for label, _v in options])
        self._values[group] = [v for _label, v in options]
        return group

    # --- focus ---------------------------------------------------------------

    def focus_children(self) -> list[Any]:
        return [self._size, self._mtime, self._content, self._missing, self._mode,
                self._select_btn, self._cancel_btn]

    # --- layout --------------------------------------------------------------

    #: Rows reserved for the title bar when sizing the box. On a grid backend
    #: ``draw_title_bar`` returns exactly this; on vector it returns less (a thin
    #: measured bar), so this is a safe upper bound — any slack lands as bottom pad.
    _TITLE_ROWS = 3.0

    def _flow(self, y0: float, band_h: float, cb_h: float,
              mode_h: float, btn_h: float) -> dict:
        """Vertical positions for one top-down pass from the title bottom ``y0``,
        shared by :meth:`show` (to size the box) and :meth:`draw` (to place). Row
        origins snap to integers so a radio group's unit-pitch rows never round two
        options onto one grid cell; measured heights keep the taller vector pitch.
        The Selection group and the button row share the bottom band."""
        head_y = float(int(y0) + 2)              # blank row between intro and headers
        band_top = head_y + 1.0
        cb_y = float(int(band_top + band_h + 1.0))
        sel_head_y = float(int(cb_y + cb_h + 1.0))
        mode_y = sel_head_y + 1.0
        band2_h = max(mode_h, btn_h)
        btn_y = mode_y + max(0.0, band2_h - btn_h)  # bottom-align buttons with the mode group
        bottom = mode_y + band2_h
        return {"head_y": head_y, "band_top": band_top, "cb_y": cb_y,
                "sel_head_y": sel_head_y, "mode_y": mode_y, "btn_y": btn_y,
                "bottom": bottom}

    def _metrics(self, lc) -> tuple:
        """Measured child heights (band = tallest column). Backend-aware via ``lc``,
        so the vector pitch (mark box taller than a cell) is reflected."""
        band_h = max(g.measure(lc, "y", 0.0).preferred for g in self._columns)
        cb_h = self._missing.measure(lc, "y", 0.0).preferred
        mode_h = self._mode.measure(lc, "y", 0.0).preferred
        btn_h = self._select_btn.measure(lc, "y", 0.0).preferred
        return band_h, cb_h, mode_h, btn_h

    # --- lifecycle -----------------------------------------------------------

    def show(self, panel: Any, *, region=None, z: int = 70) -> None:
        self._panel = panel
        sw, sh = panel.backend.size_units
        w = float(max(58, min(76, int(sw) - 4)))
        # Height is measured, not guessed: the radio pitch is taller than a cell on
        # vector backends, so size the box from the actual child heights and the
        # shared top-down flow (+ a bottom pad), capped to the window.
        lc = _layout_context(panel.backend)
        flow = self._flow(self._TITLE_ROWS, *self._metrics(lc))
        h = float(min(sh - 2.0, flow["bottom"] + 1.0))
        hints: dict[str, Any] = {"shadow": True, "w": w, "h": h}
        if region is not None:
            w, x = pane_anchored_box(w, sw, region)
            hints["w"] = w
            hints["x"] = x
        panel.push_layer(self, z=z, hints=hints)
        panel.animate(self, hints={"transition": "fade", "duration_ms": 150})

    def _finish(self, criteria: Optional[CompareCriteria]) -> None:
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()
        if self.on_result is not None:
            self.on_result(criteria)

    def _accept(self) -> None:
        self._finish(self._criteria())

    def _criteria(self) -> CompareCriteria:
        return CompareCriteria(
            size=self._values[self._size][self._size.selected],
            mtime=self._values[self._mtime][self._mtime.selected],
            content=self._values[self._content][self._content.selected],
            include_missing=self._missing.checked,
            mode=self._values[self._mode][self._mode.selected],
        )

    # --- drawing -------------------------------------------------------------

    def draw(self, ctx) -> None:
        self._panel = ctx.panel
        theme = ctx.theme
        surface_bg = theme.popup_bg if theme is not None else None
        border = theme.popup_border if theme is not None else None
        text_fg = theme.text if theme is not None else None
        box_style = Style(bg=surface_bg, fg=border)
        box_w, box_h = ctx.size_units
        ctx.draw_box(0, 0, box_w, box_h, box_style, hints={"fill": True})
        y = draw_title_bar(ctx, self.title, surface_bg=surface_bg, border=border, y=1.0)
        self._child_rects = []

        head_style = Style(bg=surface_bg, fg=text_fg, attr=TextAttribute.BOLD)
        body_style = Style(bg=surface_bg, fg=text_fg)
        lc = ctx.layout_context()

        ctx.draw_text(2, y, "Select items here, compared with the same-named item "
                            "in the other pane:", body_style)

        # A single top-down flow from the title bottom, using measured child
        # heights (so the taller vector radio pitch is accounted for) — no
        # bottom-anchoring, so any box slack is harmless bottom pad rather than a
        # collision. Origins snap to integer rows so unit-pitch grid rows never
        # round two options onto one cell.
        band_h, cb_h, mode_h, btn_h = self._metrics(lc)
        f = self._flow(y, band_h, cb_h, mode_h, btn_h)

        # --- three comparison columns (header + radio group) ------------------
        gap = 1.0
        col_w = (box_w - 4.0 - 2.0 * gap) / 3.0
        col_x = [2.0 + i * (col_w + gap) for i in range(3)]
        specs = (_SIZE, _MTIME, _CONTENT)
        for (header, _opts), group, gx in zip(specs, self._columns, col_x):
            ctx.draw_text(gx, f["head_y"], header, head_style)
            gh = group.measure(lc, "y", 0.0).preferred
            ctx.draw_child(group, gx, f["band_top"], col_w, gh,
                           hints={"focused": self._focused is group})
            self._child_rects.append(
                (group, (gx, gx + col_w, f["band_top"], f["band_top"] + gh)))

        # --- "missing" checkbox ----------------------------------------------
        cb_y = f["cb_y"]
        ctx.draw_child(self._missing, 2, cb_y, box_w - 4, 1.0,
                       hints={"focused": self._focused is self._missing})
        self._child_rects.append((self._missing, (2.0, box_w - 2.0, cb_y, cb_y + 1.0)))

        # --- bottom band: Selection mode (left) + buttons (right) ------------
        mode_w = 18.0
        mode_top = f["mode_y"]
        ctx.draw_text(2, f["sel_head_y"], _MODE[0], head_style)
        ctx.draw_child(self._mode, 2, mode_top, mode_w, mode_h,
                       hints={"focused": self._focused is self._mode})
        self._child_rects.append((self._mode, (2.0, 2.0 + mode_w, mode_top, mode_top + mode_h)))

        by = f["btn_y"]
        buttons = [self._select_btn, self._cancel_btn]
        widths = [b.measure(lc, "x", btn_h).preferred for b in buttons]
        bh = btn_h
        bx = box_w - 2.0 - sum(widths) - gap  # right-align the button row
        for btn, bw in zip(buttons, widths):
            ctx.draw_child(btn, bx, by, bw, bh, hints={"focused": self._focused is btn})
            self._child_rects.append((btn, (bx, bx + bw, by, by + bh)))
            bx += bw + gap

    # --- events --------------------------------------------------------------

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.KEY:
            self._on_key(event)
            return True
        if event.type in (EventType.MOUSE_DOWN, EventType.MOUSE_UP,
                          EventType.MOUSE_CLICK):
            self._on_mouse(event)
            return True
        return True  # modal: swallow the rest

    def _on_key(self, event: Event) -> None:
        key = event.key
        if key == "escape":
            self._finish(None)
        elif key == "tab":
            move_focus(self, -1 if "shift" in event.modifiers else 1, wrap=True)
            self._render()
        elif key == "enter":
            if self._focused is self._cancel_btn:
                self._finish(None)
            else:
                self._accept()  # Enter accepts from anywhere except Cancel
        elif key in ("up", "down") and isinstance(self._focused, RadioGroup):
            self._focused.handle_event(event)
            self._render()
        elif is_activate(event) and self._focused is self._missing:
            self._missing.toggle()
            self._render()

    def _on_mouse(self, event: Event) -> None:
        if event.x is None or event.type is not EventType.MOUSE_CLICK:
            return
        for widget, (x0, x1, y0, y1) in self._child_rects:
            if x0 <= event.x < x1 and y0 <= event.y < y1:
                self._focused = widget
                if widget is self._missing:
                    self._missing.toggle()
                elif isinstance(widget, RadioGroup):
                    # RadioGroup hit-tests in its own local coords.
                    widget.handle_event(dataclasses.replace(
                        event, x=event.x - x0, y=event.y - y0))
                elif isinstance(widget, Button):
                    widget.on_click()
                self._render()
                return

    def _render(self) -> None:
        if self._panel is not None:
            self._panel.render()


def show_compare_select(panel: Any, *, region=None,
                        on_result: Callable[[Optional[CompareCriteria]], None],
                        z: int = 70) -> CompareSelectDialog:
    """Push a modal :class:`CompareSelectDialog` over ``panel`` and return it. The
    assembled :class:`CompareCriteria` is reported through ``on_result`` (``None``
    on cancel). ``region`` anchors it over a pane like the other pickers."""
    dialog = CompareSelectDialog(on_result=on_result)
    dialog.show(panel, region=region, z=z)
    return dialog
