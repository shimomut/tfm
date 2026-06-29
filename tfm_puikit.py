#!/usr/bin/env python3
"""TFM on PuiKit — dual-pane shell spike (Phase 0/2).

The first time TFM runs on PuiKit instead of ttk. It reuses the storage-agnostic
business logic unchanged — ``tfm_path.Path`` for listing, ``PaneManager`` /
``FileListManager`` for pane state, and ``tfm_config``'s keymap (already ported
to the PuiKit keyboard contract) — and renders through a custom ``FilePane``
widget hosted in a PuiKit ``Panel`` layout.

Scope of this slice: browse, move the cursor, switch panes, descend / go up,
toggle hidden files, on curses + macOS. No dialogs, viewers, or file operations
yet — those are later phases. The legacy ``tfm.py`` (ttk) stays runnable.

    python tfm_puikit.py                       # TUI (curses)
    python tfm_puikit.py --backend gui         # macOS GUI
    python tfm_puikit.py --left ./src --right ./test
"""

import argparse
import sys
from pathlib import Path as _StdPath

sys.path.insert(0, str(_StdPath(__file__).parent / "src"))

import _config  # noqa: E402  (the canonical default Config template)
from puikit import EventType, Item, Panel, Style, TextAttribute, VSplit  # noqa: E402
from puikit.backends import create_backend  # noqa: E402
from puikit.text import elide  # noqa: E402
from puikit.widgets import LayoutView, LogView, Splitter  # noqa: E402
from puikit.widgets.base import Widget  # noqa: E402

#: Initial share of the content area given to the file panes (vs the log pane).
PANES_FRACTION = 0.74

from tfm_config import KeyBindings  # noqa: E402
from tfm_file_list_manager import FileListManager  # noqa: E402
from tfm_file_pane import FilePane  # noqa: E402
from tfm_pane_manager import PaneManager  # noqa: E402
from tfm_path import Path  # noqa: E402


class PaneHeader(Widget):
    """The location bar above a pane: its current path, brighter when active."""

    def __init__(self, app: "TfmApp", pane_name: str):
        self.app = app
        self.pane_name = pane_name

    def draw(self, ctx) -> None:
        pane = self.app.pane(self.pane_name)
        active = self.app.pm.active_pane == self.pane_name
        text = elide(" " + str(pane["path"]), ctx.width, where="middle", measure=ctx.measure_text)
        fg = ctx.theme.accent if active else ctx.theme.text
        ctx.draw_text(0, 0, text, Style(fg=fg, attr=TextAttribute.BOLD))


class PaneFooter(Widget):
    """The info bar below a pane: dir/file counts, selection, sort, filter."""

    def __init__(self, app: "TfmApp", pane_name: str):
        self.app = app
        self.pane_name = pane_name

    def draw(self, ctx) -> None:
        pane = self.app.pane(self.pane_name)
        active = self.app.pm.active_pane == self.pane_name
        dirs, files = self.app.counts(pane)
        nsel = len(pane["selected_files"])
        sel = f" ({nsel} selected)" if nsel else ""
        filt = f"  |  Filter: {pane['filter_pattern']}" if pane["filter_pattern"] else ""
        sort = self.app.flm.get_sort_description(pane)
        text = f" {dirs} dirs, {files} files{sel}  |  {sort}{filt}"
        fg = ctx.theme.text if active else ctx.theme.muted_text
        attr = TextAttribute.BOLD if active else TextAttribute.NORMAL
        ctx.draw_text(0, 0, elide(text, ctx.width, measure=ctx.measure_text), Style(fg=fg, attr=attr))


class StatusBar(Widget):
    """The bottom bar: global key hints (TFM's dynamic status line, simplified)."""

    HINTS = ("q quit   tab switch    space select   a all-files   ↵ open   "
             "⌫ parent   . hidden")

    def __init__(self, app: "TfmApp"):
        self.app = app

    def draw(self, ctx) -> None:
        text = elide(" " + self.HINTS, ctx.width, where="end", measure=ctx.measure_text)
        ctx.draw_text(0, 0, text, Style(fg=ctx.theme.muted_text))


class TfmApp:
    """Controller: owns pane state and maps key actions onto it."""

    def __init__(self, backend, left_dir: str, right_dir: str):
        self.backend = backend
        self.config = _config.Config()
        self.keys = KeyBindings(self.config.KEY_BINDINGS)
        self.flm = FileListManager(self.config)
        self.pm = PaneManager(self.config, Path(left_dir), Path(right_dir))
        self.flm.refresh_files(self.pm.left_pane)
        self.flm.refresh_files(self.pm.right_pane)

        self.panel = Panel(backend)
        self.left_view = FilePane(self.pm.left_pane, on_click=lambda i: self._on_click("left", i))
        self.right_view = FilePane(self.pm.right_pane, on_click=lambda i: self._on_click("right", i))
        self.log = LogView(max_lines=2000, auto_scroll=True, wrap=True)
        self.status = StatusBar(self)
        self._sync_active()

        # Two draggable splitters: the file panes side-by-side (vertical handle),
        # and the panes-over-log split (horizontal handle). The status bar stays
        # a fixed bottom row outside the splitters.
        self.pane_splitter = Splitter(
            self._pane_column("left", self.left_view),
            self._pane_column("right", self.right_view),
            orientation="horizontal",
            fraction=self.pm.left_pane_ratio,
            min_first=10, min_second=10,
        )
        self.content_splitter = Splitter(
            self.pane_splitter, self.log,
            orientation="vertical",
            fraction=PANES_FRACTION,
            min_first=5, min_second=2,
        )
        self.panel.set_layout(
            VSplit(
                Item(self.content_splitter, weight=1, hints={"surface": "content"}),
                Item(self.status, size=1, hints={"surface": "status"}),
                divider="subtle",
            ),
            margin_px=4,
        )
        self.log_info(f"TFM on PuiKit — {self.pm.left_pane['path']}")

    def _pane_column(self, name: str, view: FilePane) -> LayoutView:
        # A LayoutView wraps the header/list/footer sub-layout as a single widget
        # so it can be a Splitter child (Splitter hosts widgets, not layouts).
        return LayoutView(VSplit(
            Item(PaneHeader(self, name), size=1, hints={"surface": "header"}),
            Item(view, weight=1, hints={"surface": "content"}),
            Item(PaneFooter(self, name), size=1, hints={"surface": "status"}),
        ))

    # --- state ---------------------------------------------------------------

    def active_pane(self) -> dict:
        return self.pm.get_current_pane()

    def pane(self, name: str) -> dict:
        return self.pm.left_pane if name == "left" else self.pm.right_pane

    def counts(self, pane: dict) -> tuple[int, int]:
        """(dirs, files) in a pane, read from the file-info cache."""
        info = pane.get("file_info", {})
        dirs = sum(1 for f in pane["files"] if info.get(str(f), {}).get("is_dir"))
        return dirs, len(pane["files"]) - dirs

    def log_info(self, message: str) -> None:
        """Append a line to the log pane."""
        self.log.append(message, Style(fg=(180, 200, 230)))

    def _log_result(self, result) -> None:
        """Log the (success, message) a FileListManager action returns."""
        if isinstance(result, tuple) and len(result) == 2 and result[1]:
            self.log_info(result[1])

    def _sync_active(self) -> None:
        self.left_view.active = self.pm.active_pane == "left"
        self.right_view.active = self.pm.active_pane == "right"

    def _on_click(self, pane_name: str, index: int) -> None:
        """A FilePane was left-clicked: make it active and move the cursor."""
        self.pm.active_pane = pane_name
        self._sync_active()
        self.active_pane()["focused_index"] = index

    def _refresh(self, pane: dict) -> None:
        pane["focused_index"] = 0
        pane["scroll_offset"] = 0
        self.flm.refresh_files(pane)

    # --- actions -------------------------------------------------------------

    def dispatch(self, action: str | None) -> bool:
        """Apply an action to the active pane. Returns True if a redraw is needed."""
        if action is None:
            return False
        pane = self.active_pane()
        files = pane["files"]
        last = max(0, len(files) - 1)
        idx = pane["focused_index"]

        if action == "quit":
            self.backend.quit()
            return False
        if action == "cursor_up":
            pane["focused_index"] = max(0, idx - 1)
        elif action == "cursor_down":
            pane["focused_index"] = min(last, idx + 1)
        elif action == "page_up":
            pane["focused_index"] = max(0, idx - 10)
        elif action == "page_down":
            pane["focused_index"] = min(last, idx + 10)
        # --- selection (reuses FileListManager) ---
        elif action == "select_file":  # SPACE: toggle current, move down
            self._log_result(self.flm.toggle_selection(pane, move_cursor=True, direction=1))
        elif action == "select_file_up":  # Shift-SPACE: toggle, move up
            self._log_result(self.flm.toggle_selection(pane, move_cursor=True, direction=-1))
        elif action == "select_all_files":  # A: toggle all files
            self._log_result(self.flm.toggle_all_files_selection(pane))
        elif action == "select_all_items":  # Shift-A: toggle all items
            self._log_result(self.flm.toggle_all_items_selection(pane))
        elif action == "select_all":  # HOME: select every item
            pane["selected_files"] = {str(f) for f in files}
        elif action == "unselect_all":  # END: clear selection
            pane["selected_files"].clear()
        elif action == "switch_pane":
            self.pm.active_pane = "right" if self.pm.active_pane == "left" else "left"
            self._sync_active()
        elif action in ("open_item", "nav_right"):
            self._open(pane)
        elif action in ("go_parent", "nav_left"):
            self._go_parent(pane)
        elif action == "toggle_hidden":
            self.flm.show_hidden = not self.flm.show_hidden
            self.flm.refresh_files(pane)
            self.log_info(f"Hidden files: {'shown' if self.flm.show_hidden else 'hidden'}")
        else:
            return False
        return True

    def _open(self, pane: dict) -> None:
        files = pane["files"]
        if not files:
            return
        entry = files[pane["focused_index"]]
        try:
            if entry.is_dir():
                pane["path"] = entry
                self._refresh(pane)
                self.log_info(f"Entered {entry.name}/")
        except Exception as exc:
            self.log_info(f"Cannot open {entry.name}: {exc}")

    def _go_parent(self, pane: dict) -> None:
        parent = pane["path"].parent
        if str(parent) != str(pane["path"]):
            child_name = pane["path"].name
            pane["path"] = parent
            self._refresh(pane)
            self.log_info(f"Up to {parent}")
            # Land the cursor on the directory we came from.
            for i, f in enumerate(pane["files"]):
                if f.name == child_name:
                    pane["focused_index"] = i
                    break

    # --- run -----------------------------------------------------------------

    #: Mouse events routed to the widget under the pointer (the FilePanes own
    #: click + wheel/trackpad scroll); keyboard uses TFM's global keymap.
    _MOUSE = frozenset({
        EventType.MOUSE_DOWN, EventType.MOUSE_UP, EventType.MOUSE_CLICK,
        EventType.MOUSE_DRAG, EventType.MOUSE_SCROLL,
    })

    def on_event(self, event) -> None:
        if event.type is EventType.RESIZE:
            self.panel.render()
            return
        if event.type is EventType.MOUSE_MOVE:
            # Pointer movement only updates hover state — let the Splitters under
            # the cursor swap in their resize cursor (and drop it again on the way
            # out). GUI emits these; the TUI does not, so it's a GUI-only affordance.
            self.panel.dispatch_event(event)
            self.panel.render()
            return
        if event.type is EventType.KEY:
            has_sel = bool(self.active_pane()["selected_files"])
            action = self.keys.find_action_for_event(event, has_sel)
            if self.dispatch(action):
                self.panel.render()
            return
        if event.type in self._MOUSE:
            if self.panel.dispatch_event(event):
                self.panel.render()

    def run(self) -> None:
        self.panel.render()
        self.backend.run_event_loop(self.on_event)


_BACKENDS = {"tui": "tui", "curses": "tui", "gui": "gui", "macos": "gui"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default="tui", help="tui (curses) | gui (macOS)")
    parser.add_argument("--left", default=".", help="left pane startup directory")
    parser.add_argument("--right", default=".", help="right pane startup directory")
    args = parser.parse_args()

    backend = create_backend(_BACKENDS.get(args.backend, args.backend))
    with backend:
        TfmApp(backend, args.left, args.right).run()


if __name__ == "__main__":
    main()
