#!/usr/bin/env python3
"""TFM on PuiKit — dual-pane file manager.

TFM running on PuiKit instead of ttk. It reuses the storage-agnostic business
logic unchanged — ``tfm_path.Path`` for listing, ``PaneManager`` /
``FileListManager`` for pane state, and ``tfm_config``'s keymap (ported to the
PuiKit keyboard contract) — and renders through a custom ``FilePane`` widget
hosted in a PuiKit ``Panel`` layout, on curses + macOS.

Wired so far: browse / navigate (cursor, pane switch, arrow-key focus, descend /
go up), selection, sort, hidden-file toggle, filename filter and incremental
search, the built-in text and diff viewers, and the create / rename / batch-
rename / favorites / jump-to-path dialogs. File operations (copy / move / delete)
and archive / remote storage are later phases. The original ttk implementation is
kept for reference under ``legacy/``.

    python tfm.py                       # TUI (curses)
    python tfm.py --backend gui         # macOS GUI
    python tfm.py --left ./src --right ./test
"""

import argparse
import os
import platform
import queue
import subprocess
import sys
from pathlib import Path as _StdPath

sys.path.insert(0, str(_StdPath(__file__).parent / "src"))

import _config  # noqa: E402  (the canonical default Config template)
from puikit import EventType, Item, Panel, Style, TextAttribute, Theme, VSplit, derive_theme  # noqa: E402
from puikit.backends import create_backend  # noqa: E402
from puikit.menu import Menu, MenuItem, SEPARATOR  # noqa: E402
from puikit.text import elide  # noqa: E402
from puikit.widgets import LayoutView, LogView, MenuBar, Splitter, show_message_box  # noqa: E402
from puikit.widgets.base import Widget  # noqa: E402

#: Initial share of the content area given to the file panes (vs the log pane).
PANES_FRACTION = 0.74

from tfm_config import KeyBindings, get_favorite_directories  # noqa: E402
from tfm_file_list_manager import FileListManager  # noqa: E402
from tfm_file_monitor_manager import FileMonitorManager  # noqa: E402
from tfm_file_pane import FilePane  # noqa: E402
from tfm_filter_list_dialog import show_filter_list  # noqa: E402
from tfm_input_dialog import show_input  # noqa: E402
from tfm_pane_manager import PaneManager  # noqa: E402
from tfm_path import Path  # noqa: E402
from tfm_state_manager import get_state_manager  # noqa: E402
from tfm_batch_rename_dialog import show_batch_rename  # noqa: E402
from tfm_diff_viewer import show_diff_viewer  # noqa: E402
from tfm_directory_diff_viewer import show_directory_diff_viewer  # noqa: E402
from tfm_text_dialog import show_text  # noqa: E402
from tfm_text_viewer import show_text_viewer  # noqa: E402


# --- theme palettes ----------------------------------------------------------
#
# Theme switching is pure intent, exactly as in PuiKit's demo catalog: the shell
# tags its panes with semantic surface roles (header / content / status) instead
# of hardcoded colors, and every widget reads its accent / selection / text
# colors from ``panel.theme`` at draw time (see ``PaneHeader`` / ``PaneFooter`` /
# ``StatusBar`` below). So cycling the active ``Theme`` (the ``toggle_color_scheme``
# action, bound to ``T``) recolors the whole file manager — chrome and file lists
# alike — with one assignment and no per-widget repaint logic; the surface
# backgrounds re-resolve from the new theme on the next render.
#
# Each theme is the six base colors ``derive_theme`` needs; it computes the rest
# (hovers, borders, inactive selections, dividers) by lighten/darken/blend rules.
#   background — content surface (its luminance also picks the lift direction)
#   foreground — primary text          muted     — secondary text / dividers
#   accent     — focus / status bar    surface   — raised panels (header/popup)
#   selection  — active selection fill
THEMES: list[tuple[str, Theme]] = [
    ("Dark+", derive_theme(
        background=(30, 30, 30), foreground=(212, 212, 212), muted=(157, 157, 157),
        accent=(0, 122, 204), surface=(48, 48, 52), selection=(10, 105, 178))),
    ("Monokai", derive_theme(
        background=(39, 40, 34), foreground=(248, 248, 242), muted=(140, 140, 130),
        accent=(166, 226, 46), surface=(56, 57, 48), selection=(86, 122, 38))),
    ("Dracula", derive_theme(
        background=(40, 42, 54), foreground=(248, 248, 242), muted=(98, 114, 164),
        accent=(189, 147, 249), surface=(56, 59, 76), selection=(120, 86, 175))),
    ("Nord", derive_theme(
        background=(46, 52, 64), foreground=(216, 222, 233), muted=(76, 86, 106),
        accent=(136, 192, 208), surface=(62, 70, 88), selection=(76, 128, 158))),
    ("Solarized", derive_theme(
        background=(0, 43, 54), foreground=(147, 161, 161), muted=(88, 110, 117),
        accent=(38, 139, 210), surface=(10, 62, 78), selection=(26, 102, 150))),
    # --- light variants: same six bases, opposite polarity (panels sink, text
    # defaults dark), so a light background reads correctly on every backend.
    ("Light+", derive_theme(
        background=(255, 255, 255), foreground=(30, 30, 30), muted=(110, 110, 110),
        accent=(0, 122, 204), surface=(235, 235, 238), selection=(120, 180, 240))),
    ("Solarized Light", derive_theme(
        background=(253, 246, 227), foreground=(88, 110, 117), muted=(147, 161, 161),
        accent=(38, 139, 210), surface=(234, 228, 206), selection=(150, 195, 230))),
]

#: Which theme each ``Config.COLOR_SCHEME`` value starts on (ttk TFM's two
#: schemes map onto the matching PuiKit palette; anything else falls back to the
#: first, dark, theme).
_INITIAL_THEME = {"dark": "Dark+", "light": "Light+"}


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

    HINTS = ("q quit   tab switch   space select   a all-files   ↵ open   "
             "⌫ parent   f find   ; filter   . hidden")

    def __init__(self, app: "TfmApp"):
        self.app = app

    def draw(self, ctx) -> None:
        text = elide(" " + self.HINTS, ctx.width, where="end", measure=ctx.measure_text)
        ctx.draw_text(0, 0, text, Style(fg=ctx.theme.muted_text))


class TfmApp:
    """Controller: owns pane state and maps key actions onto it."""

    def __init__(self, backend, left_dir: str, right_dir: str, *,
                 left_provided: bool = True, right_provided: bool = True,
                 state_manager=None):
        self.backend = backend
        self.config = _config.Config()
        self.keys = KeyBindings(self.config.KEY_BINDINGS)
        # Persistent cross-session state (window layout, pane dirs, cursor
        # positions, recent dirs). Injectable so tests can supply a temp-db
        # manager instead of touching ~/.tfm/state.db.
        self.state_manager = state_manager if state_manager is not None else get_state_manager()
        self._left_provided = left_provided
        self._right_provided = right_provided
        self.flm = FileListManager(self.config)
        self.pm = PaneManager(self.config, self._resolve_dir(left_dir),
                              self._resolve_dir(right_dir),
                              state_manager=self.state_manager,
                              file_list_manager=self.flm)
        # Restore saved window layout and pane paths/sort/filter *before* the
        # splitters are built (they read ``pm.left_pane_ratio`` /
        # ``_panes_fraction``) and before the first refresh lists a directory.
        self._restore_layout_and_paths()
        self.flm.refresh_files(self.pm.left_pane)
        self.flm.refresh_files(self.pm.right_pane)
        #: Recent-directory history for the history picker — a bounded, in-order
        #: list of visited paths, recorded on every directory change (see
        #: ``_record_history``). Seeded with the two starting directories.
        self._history: list[str] = []
        for p in (self.pm.left_pane["path"], self.pm.right_pane["path"]):
            self._record_history_path(str(p))

        self.panel = Panel(backend)
        self.left_view = FilePane(
            self.pm.left_pane,
            config=self.config,
            on_click=lambda i: self._on_click("left", i),
            on_context=lambda i, x, y: self._show_context_menu("left", i, x, y),
        )
        self.right_view = FilePane(
            self.pm.right_pane,
            config=self.config,
            on_click=lambda i: self._on_click("right", i),
            on_context=lambda i, x, y: self._show_context_menu("right", i, x, y),
        )
        self.log = LogView(max_lines=2000, auto_scroll=True, wrap=True)
        self.status = StatusBar(self)
        # One Menu model drives the OS-native menu bar on macOS (an NSMenu) and an
        # in-window strip on curses — the Panel resolves which, so we never branch.
        self.menu_bar = MenuBar(self._build_menu())
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
            fraction=self._panes_fraction,
            min_first=5, min_second=2,
            # No handle row on the grid: the pane footer already sits directly
            # above the log and serves as the divider, so a separate handle cell
            # would waste a row. Still draggable via the grab margin; the vector
            # backend keeps its hairline.
            flat=True,
        )
        self.panel.set_layout(
            VSplit(
                # The MenuBar self-sizes via "content": a 1-row strip on curses,
                # zero height on macOS (it installs the native bar instead), so
                # no row branch. Without "content" the item would flex and eat
                # half the window. It carries no divider after it — when it
                # collapses to 0 height (macOS), a divider here would float at the
                # very top — so the subtle divider lives on the nested split below,
                # only between the content and the status bar.
                Item(self.menu_bar, size="content", hints={"surface": "header"}),
                Item(
                    VSplit(
                        Item(self.content_splitter, weight=1, hints={"surface": "content"}),
                        Item(self.status, size=1, hints={"surface": "status"}),
                        divider="subtle",
                    ),
                    weight=1,
                ),
            ),
            margin_px=4,
        )
        # Seed the active theme from the config's color scheme, then let the
        # ``toggle_color_scheme`` action (T) cycle through the palettes.
        start = _INITIAL_THEME.get(getattr(self.config, "COLOR_SCHEME", "dark"), "Dark+")
        self._theme_index = next(
            (i for i, (name, _t) in enumerate(THEMES) if name == start), 0)
        self.panel.theme = THEMES[self._theme_index][1]
        self.log_info(f"TFM on PuiKit — {self.pm.left_pane['path']}")
        # Files are listed now, so the saved cursor filenames can be matched.
        self._restore_cursor_positions()

        # Filesystem monitoring: observer threads post pane names to
        # ``reload_queue``; the main thread drains it via an animation tick (and
        # opportunistically on every event). ``_sync_monitored_dirs`` re-points
        # the watchers whenever a pane navigates, so navigation code stays
        # unaware of monitoring. Auto-disables cleanly if watchdog is missing.
        self.reload_queue: queue.Queue = queue.Queue()
        self.file_monitor = FileMonitorManager(self.config, self)
        self._monitored: dict[str, object] = {"left": None, "right": None}
        self._sync_monitored_dirs()
        self.panel.request_animation_ticks(self._reload_tick)

    def _pane_column(self, name: str, view: FilePane) -> LayoutView:
        # A LayoutView wraps the header/list/footer sub-layout as a single widget
        # so it can be a Splitter child (Splitter hosts widgets, not layouts).
        # A "subtle" divider draws a hairline between the path/info bars and the
        # file list on GUI (zero base-unit cost) — without it the footer's status
        # surface matches the content background and the boundary vanishes; on TUI
        # nothing is reserved and the surface-role contrast does the separating.
        return LayoutView(VSplit(
            Item(PaneHeader(self, name), size=1, hints={"surface": "header"}),
            Item(view, weight=1, hints={"surface": "content"}),
            Item(PaneFooter(self, name), size=1, hints={"surface": "status"}),
            divider="subtle",
        ))

    @staticmethod
    def _resolve_dir(path_str: str) -> Path:
        """Make a startup directory absolute (expanding ``~``) so the pane header
        and every path derived from it — parents on ``go_parent``, children from
        ``iterdir``, the ``selected_files`` keys, history entries, and file-op
        destinations — is a full path, not one relative to the launch directory.
        Falls back to ``absolute`` (a plain cwd join, no symlink resolution) if
        ``resolve`` fails for an odd input."""
        p = Path(path_str).expanduser()
        try:
            return p.resolve()
        except Exception:
            return p.absolute()

    # --- persistent state ----------------------------------------------------

    def _restore_layout_and_paths(self) -> None:
        """Restore window layout and each pane's directory / sort / filter from
        the saved session, *before* the splitters and file lists are built.

        A pane's saved directory is only re-applied when the user did not pass an
        explicit startup directory for it on the command line, and only if that
        directory still exists; sort mode and filter are always restored. Fully
        best-effort — the log view does not exist yet, so failures stay silent
        rather than blocking startup on a corrupt or absent state store."""
        self._panes_fraction = PANES_FRACTION
        try:
            self.state_manager.update_session_heartbeat()
            self.state_manager.cleanup_non_existing_directories()

            layout = self.state_manager.load_window_layout()
            if layout:
                ratio = layout.get('left_pane_ratio', self.pm.left_pane_ratio)
                self.pm.left_pane_ratio = max(0.1, min(0.9, ratio))
                log_h = layout.get('log_height_ratio', 1.0 - PANES_FRACTION)
                self._panes_fraction = max(0.1, min(0.95, 1.0 - log_h))

            self._restore_one_pane('left', self.pm.left_pane, self._left_provided)
            self._restore_one_pane('right', self.pm.right_pane, self._right_provided)
        except Exception:
            pass

    def _restore_one_pane(self, name: str, pane: dict, cmdline_provided: bool) -> None:
        state = self.state_manager.load_pane_state(name)
        if not state:
            return
        if not cmdline_provided:
            try:
                saved = Path(state['path'])
                if saved.exists():
                    pane['path'] = saved
            except Exception:
                pass
        pane['sort_mode'] = state.get('sort_mode', pane['sort_mode'])
        pane['sort_reverse'] = state.get('sort_reverse', pane['sort_reverse'])
        pane['filter_pattern'] = state.get('filter_pattern', pane['filter_pattern'])

    def _display_height(self) -> int:
        """Rows available for a file list, used to keep a restored cursor on
        screen. Best-effort: falls back to a sane default before first layout."""
        try:
            _w, h = self.backend.size
            return max(1, int(h) - 4)
        except Exception:
            return 20

    def _restore_cursor_positions(self) -> None:
        """Move each pane's cursor to the file remembered for its directory."""
        try:
            display_height = self._display_height()
            self.pm.restore_cursor_position(self.pm.left_pane, display_height)
            self.pm.restore_cursor_position(self.pm.right_pane, display_height)
        except Exception:
            pass

    def _save_application_state(self) -> None:
        """Persist window layout, pane state, cursor positions, and recent dirs.
        Called on quit; best-effort so a state-store failure never blocks exit."""
        try:
            self.state_manager.save_window_layout(
                self.pane_splitter.fraction,
                1.0 - self.content_splitter.fraction,
            )
            self.state_manager.save_pane_state('left', self.pm.left_pane)
            self.state_manager.save_pane_state('right', self.pm.right_pane)
            self.pm.save_cursor_position(self.pm.left_pane)
            self.pm.save_cursor_position(self.pm.right_pane)

            left_path = str(self.pm.left_pane['path'])
            right_path = str(self.pm.right_pane['path'])
            self.state_manager.add_recent_directory(left_path)
            if left_path != right_path:
                self.state_manager.add_recent_directory(right_path)

            self.state_manager.cleanup_session()
        except Exception as e:
            self.log_info(f"Could not save application state: {e}")

    def _quit(self) -> None:
        """Stop monitoring, save state, then end the event loop."""
        if getattr(self, "file_monitor", None) is not None:
            self.file_monitor.stop_monitoring()
        self._save_application_state()
        self.backend.quit()

    # --- filesystem monitoring -----------------------------------------------

    def _sync_monitored_dirs(self) -> None:
        """Point each pane's watcher at that pane's current directory, (re)starting
        monitoring on the ones that changed. Called on every tick, so navigating a
        pane transparently moves its watcher — no navigation site needs to know."""
        if not self.file_monitor.is_monitoring_enabled():
            return
        for name in ("left", "right"):
            path = self.pane(name)["path"]
            if path != self._monitored[name]:
                self._monitored[name] = path
                self.file_monitor.update_monitored_directory(name, path)

    def _pump_monitoring(self) -> bool:
        """Re-point watchers and apply any queued reloads. Returns True if a pane
        was reloaded (so the caller re-renders)."""
        self._sync_monitored_dirs()
        return self._process_reload_queue()

    def _reload_tick(self) -> bool:
        """Animation-tick pump: drains reload requests on idle. Stays registered
        for the app's lifetime (returns True)."""
        if self._pump_monitoring():
            self.panel.render()
        return True

    def _process_reload_queue(self) -> bool:
        reloaded = False
        while True:
            try:
                pane_name = self.reload_queue.get_nowait()
            except queue.Empty:
                break
            if self._handle_reload_request(pane_name):
                reloaded = True
        return reloaded

    def _handle_reload_request(self, pane_name: str) -> bool:
        """Reload one pane's file list while preserving user context: keep the
        cursor on the same filename if it survives, otherwise the nearest name
        alphabetically, and hold the scroll offset where it can still show it.

        Returns True if the pane was reloaded, False for an unknown pane name."""
        if pane_name == "left":
            pane = self.pm.left_pane
        elif pane_name == "right":
            pane = self.pm.right_pane
        else:
            return False

        old_focused = pane["focused_index"]
        old_scroll = pane["scroll_offset"]
        selected_filename = None
        if pane["files"] and 0 <= old_focused < len(pane["files"]):
            selected_filename = pane["files"][old_focused].name

        self.flm.refresh_files(pane)

        files = pane["files"]
        if selected_filename and files:
            idx = next((i for i, f in enumerate(files)
                        if f.name == selected_filename), None)
            if idx is None:
                # Selected file is gone: land on where it would have sorted, so
                # the cursor stays near its old neighbours (list is name-sorted).
                idx = 0
                for i, f in enumerate(files):
                    if f.name < selected_filename:
                        idx = i + 1
                    else:
                        break
                idx = min(idx, len(files) - 1)
            pane["focused_index"] = idx

            display_height = self._display_height()
            max_offset = max(0, len(files) - display_height)
            pane["scroll_offset"] = min(old_scroll, max_offset)
            if pane["focused_index"] < pane["scroll_offset"]:
                pane["scroll_offset"] = pane["focused_index"]
            elif pane["focused_index"] >= pane["scroll_offset"] + display_height:
                pane["scroll_offset"] = pane["focused_index"] - display_height + 1
        else:
            pane["focused_index"] = 0
            pane["scroll_offset"] = 0
        return True

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
        self._record_history_path(str(pane["path"]))

    def _record_history_path(self, path: str) -> None:
        """Append ``path`` to the recent-directory history, coalescing an
        immediate repeat (a same-directory refresh from create/rename doesn't add
        a duplicate) and capping the list length."""
        if not self._history or self._history[-1] != path:
            self._history.append(path)
            del self._history[:-100]

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
            self.confirm_quit()
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
        elif action == "open_item":
            self._open(pane)
        elif action == "go_parent":
            self._go_parent(pane)
        elif action == "nav_left":
            # Context-aware LEFT (ttk TFM): from the right pane, move focus to the
            # left pane; already in the left pane, go to its parent directory.
            if self.pm.active_pane == "right":
                self.pm.active_pane = "left"
                self._sync_active()
            else:
                self._go_parent(pane)
        elif action == "nav_right":
            # Context-aware RIGHT (ttk TFM): from the left pane, move focus to the
            # right pane; already in the right pane, go to its parent directory.
            if self.pm.active_pane == "left":
                self.pm.active_pane = "right"
                self._sync_active()
            else:
                self._go_parent(pane)
        elif action == "toggle_hidden":
            self.flm.show_hidden = not self.flm.show_hidden
            self.flm.refresh_files(pane)
            self.log_info(f"Hidden files: {'shown' if self.flm.show_hidden else 'hidden'}")
        elif action == "toggle_color_scheme":
            self._cycle_theme()  # falls through to a full re-render below
        elif action in ("quick_sort_name", "quick_sort_size",
                        "quick_sort_date", "quick_sort_ext"):
            self._quick_sort(action[len("quick_sort_"):])
        elif action == "sort_menu":
            self.show_sort_menu()
            return False  # the menu popup drives its own redraw
        elif action == "clear_filter":
            if pane["filter_pattern"]:
                self.flm.apply_filter(pane, "")
                self.log_info("Filter cleared")
            else:
                self.log_info("No filter to clear")
        elif action == "sync_current_to_other":
            if self.pm.sync_current_to_other(self.log_info):
                self.flm.refresh_files(self.active_pane())
        elif action == "sync_other_to_current":
            if self.pm.sync_other_to_current(self.log_info):
                self.flm.refresh_files(self.pm.get_inactive_pane())
        elif action == "redraw":
            pass  # falls through to a full re-render below
        elif action == "adjust_pane_left":     # make the left pane smaller
            self._nudge(self.pane_splitter, -self._PANE_STEP)
        elif action == "adjust_pane_right":    # make the left pane larger
            self._nudge(self.pane_splitter, +self._PANE_STEP)
        elif action == "reset_pane_boundary":  # even 50 | 50 split
            self.pane_splitter.fraction = 0.5
        elif action == "adjust_log_up":        # grow the log (panes shrink)
            self._nudge(self.content_splitter, -self._LOG_STEP)
        elif action == "adjust_log_down":      # shrink the log (panes grow)
            self._nudge(self.content_splitter, +self._LOG_STEP)
        elif action == "reset_log_height":     # back to the default share
            self.content_splitter.fraction = PANES_FRACTION
        elif action == "scroll_log_up":
            self.log.scroll_by(-1.0)
        elif action == "scroll_log_down":
            self.log.scroll_by(+1.0)
        elif action == "scroll_log_page_up":
            self.log.scroll_by(-self._LOG_PAGE)
        elif action == "scroll_log_page_down":
            self.log.scroll_by(+self._LOG_PAGE)
        elif action == "file_details":
            self.file_details()
            return False  # the dialog drives its own redraw
        elif action == "drives_dialog":
            self.show_drives()
            return False
        elif action == "search_dialog":
            self.show_search()
            return False
        elif action == "history":
            self.show_history()
            return False
        elif action == "programs":
            self.show_programs()
            return False
        elif action == "open_with_os":
            self.open_with_os()
            return False  # hands off to the OS; no in-app redraw
        elif action == "reveal_in_os":
            self.reveal_in_os()
            return False
        elif action in ("edit_file", "subshell"):
            # Both need the TUI to release the terminal to a full-screen program
            # and reclaim it after — a backend suspend/resume PuiKit doesn't expose
            # yet. Report it rather than launch a program under the live UI.
            self.log_info(f"'{action}' needs terminal suspend/resume (a later phase)")
            return False
        elif action == "filter":
            self.enter_filter()
            return False  # the dialog drives its own redraw
        elif action == "search":
            self.enter_isearch()
            return False  # the isearch overlay drives its own redraw
        elif action == "favorites":
            self.show_favorites()
            return False  # the dialog drives its own redraw
        elif action == "create_directory":
            self.create_directory()
            return False  # the dialog drives its own redraw
        elif action == "create_file":
            self.create_file()
            return False
        elif action == "rename_file":
            self.rename()
            return False
        elif action == "copy_files":
            self.copy_files()
            return False  # the confirm dialog drives its own redraw
        elif action == "move_files":
            self.move_files()
            return False
        elif action == "delete_files":
            self.delete_files()
            return False
        elif action == "create_archive":
            self.create_archive()
            return False  # the dialog drives its own redraw
        elif action == "extract_archive":
            self.extract_archive()
            return False
        elif action == "jump_to_path":
            self.jump_to_path()
            return False
        elif action == "view_file":
            self.view_file()
            return False
        elif action == "diff_files":
            self.diff_files()
            return False
        elif action == "diff_directories":
            self.diff_directories()
            return False
        elif action == "help":
            self.show_help()
            return False
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

    # --- menus & dialogs -----------------------------------------------------

    def _build_menu(self) -> Menu:
        """The app menu model — one tree, realized as the macOS menu bar or an
        in-window strip. Items reuse the same callbacks the keymap and context
        menu drive, and ``checked``/``enabled`` predicates re-evaluate on open so
        the menu always mirrors live pane state."""
        def has_files() -> bool:
            return bool(self.active_pane()["files"])

        sort_menu = self._sort_menu()

        file_menu = Menu(
            MenuItem("Open", on_select=lambda: self._menu("open_item"),
                     enabled=has_files, shortcut="Enter"),
            MenuItem("View File", on_select=self.view_file,
                     enabled=has_files, shortcut="V"),
            MenuItem("Details…", on_select=self.file_details, enabled=has_files),
            MenuItem("Open with Default App", on_select=self.open_with_os, enabled=has_files),
            MenuItem("Reveal in File Manager", on_select=self.reveal_in_os, enabled=has_files),
            MenuItem("External Programs…", on_select=self.show_programs, shortcut="X"),
            SEPARATOR,
            MenuItem("Parent Directory", on_select=lambda: self._menu("go_parent"),
                     shortcut="Backspace"),
            MenuItem("Go to Favorite…", on_select=self.show_favorites, shortcut="J"),
            MenuItem("Jump to Path…", on_select=self.jump_to_path, shortcut="Shift-J"),
            MenuItem("Drives…", on_select=self.show_drives),
            MenuItem("History…", on_select=self.show_history, shortcut="H"),
            SEPARATOR,
            MenuItem("New Folder…", on_select=self.create_directory, shortcut="M"),
            MenuItem("New File…", on_select=self.create_file, shortcut="Shift-E"),
            MenuItem("Rename…", on_select=self.rename, enabled=has_files, shortcut="R"),
            MenuItem("Copy to Other Pane", on_select=self.copy_files,
                     enabled=has_files, shortcut="C"),
            MenuItem("Move to Other Pane", on_select=self.move_files,
                     enabled=has_files, shortcut="M"),
            MenuItem("Delete…", on_select=self.delete_files,
                     enabled=has_files, shortcut="K"),
            SEPARATOR,
            MenuItem("Create Archive…", on_select=self.create_archive,
                     enabled=has_files, shortcut="P"),
            MenuItem("Extract Archive…", on_select=self.extract_archive,
                     enabled=has_files, shortcut="U"),
            SEPARATOR,
            MenuItem("Quit", on_select=self.confirm_quit, shortcut="q"),
            title="File",
        )
        select_menu = Menu(
            MenuItem("Toggle Selection", on_select=lambda: self._menu("select_file"),
                     enabled=has_files, shortcut="Space"),
            MenuItem("Select All Items", on_select=lambda: self._menu("select_all")),
            MenuItem("Clear Selection", on_select=lambda: self._menu("unselect_all"),
                     enabled=lambda: bool(self.active_pane()["selected_files"])),
            SEPARATOR,
            MenuItem("Compare Selected Files…", on_select=self.diff_files, shortcut="="),
            MenuItem("Compare Directories…", on_select=self.diff_directories,
                     shortcut="Shift-="),
            title="Select",
        )
        view_menu = Menu(
            MenuItem("Find…", on_select=self.enter_isearch, enabled=has_files, shortcut="F"),
            MenuItem("Filter…", on_select=self.enter_filter, shortcut=";"),
            MenuItem("Search Files…", on_select=self.show_search, shortcut="Shift-F"),
            SEPARATOR,
            MenuItem("Show Hidden Files", on_select=lambda: self._menu("toggle_hidden"),
                     checked=lambda: self.flm.show_hidden, shortcut="."),
            MenuItem("Reverse Sort", on_select=self._toggle_reverse,
                     checked=lambda: self.active_pane()["sort_reverse"]),
            MenuItem("Sort By", submenu=sort_menu),
            SEPARATOR,
            MenuItem("Theme", submenu=self._theme_menu()),
            MenuItem("Next Theme", on_select=lambda: self._menu("toggle_color_scheme"),
                     shortcut="T"),
            SEPARATOR,
            MenuItem("Switch Pane", on_select=lambda: self._menu("switch_pane"), shortcut="Tab"),
            title="View",
        )
        help_menu = Menu(
            MenuItem("Keyboard Shortcuts…", on_select=self.show_help, shortcut="?"),
            SEPARATOR,
            MenuItem("About TFM", on_select=self.show_about),
            title="Help",
        )
        return Menu(
            MenuItem("File", submenu=file_menu),
            MenuItem("Select", submenu=select_menu),
            MenuItem("View", submenu=view_menu),
            MenuItem("Help", submenu=help_menu),
        )

    def _menu(self, action: str) -> None:
        """Run a keymap action from a menu/context-menu selection and redraw."""
        if self.dispatch(action):
            self.panel.render()

    def _focused_entry(self):
        """The entry under the cursor in the active pane, or None if empty."""
        pane = self.active_pane()
        files = pane["files"]
        if not files:
            return None
        return files[pane["focused_index"]]

    def file_details(self) -> None:
        """Show stat details for the focused entry — or an aggregate summary plus
        per-item details for a multi-file selection — in a scrollable text dialog
        (mirrors ttk TFM's file-details, reusing the shared text-dialog)."""
        import datetime as _dt
        import stat as _stat
        pane = self.active_pane()
        files = pane["files"]
        if not files:
            self.log_info("No file to show details for")
            return
        selected = [f for f in files if str(f) in pane["selected_files"]]
        targets = selected if selected else [files[pane["focused_index"]]]

        def details(entry) -> list[str]:
            out = [entry.name, f"  Path: {entry}"]
            try:
                st = entry.stat()
            except Exception as exc:
                out.append(f"  (stat unavailable: {exc})")
                return out
            try:
                kind = "Directory" if entry.is_dir() else \
                       ("Symlink" if entry.is_symlink() else "File")
            except Exception:
                kind = "File"
            mtime = _dt.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            out += [
                f"  Type: {kind}",
                f"  Size: {st.st_size:,} bytes",
                f"  Modified: {mtime}",
                f"  Permissions: {_stat.filemode(st.st_mode)}",
            ]
            return out

        if len(targets) == 1:
            lines = details(targets[0])
        else:
            total = 0
            for t in targets:
                try:
                    total += t.stat().st_size
                except Exception:
                    pass
            lines = [f"{len(targets)} items selected", f"  Total size: {total:,} bytes", ""]
            for t in targets:
                lines += details(t) + [""]
        show_text(self.panel, lines, title="Details")
        self.panel.render()

    def open_with_os(self) -> None:
        """Open the focused entry with the OS default application (the desktop
        'open' / 'xdg-open' / 'start'). Errors are logged, not raised."""
        entry = self._focused_entry()
        if entry is None:
            return
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", str(entry)], check=True)
            elif system == "Windows":
                subprocess.run(["start", "", str(entry)], shell=True, check=True)
            else:
                subprocess.run(["xdg-open", str(entry)], check=True)
        except Exception as exc:
            self.log_info(f"Failed to open {entry.name}: {exc}")
        else:
            self.log_info(f"Opened {entry.name} with the default app")

    def reveal_in_os(self) -> None:
        """Reveal the focused entry in the OS file manager (Finder / Explorer),
        falling back to opening its parent directory elsewhere."""
        entry = self._focused_entry()
        if entry is None:
            return
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", "-R", str(entry)], check=True)
            elif system == "Windows":
                subprocess.run(["explorer", "/select,", str(entry)], check=True)
            else:
                subprocess.run(["xdg-open", str(entry.parent)], check=True)
        except Exception as exc:
            self.log_info(f"Failed to reveal {entry.name}: {exc}")
        else:
            self.log_info(f"Revealed {entry.name}")

    def _sort_menu(self) -> Menu:
        """The sort-mode menu, shared by the menu-bar's 'Sort By' submenu and the
        keyboard-triggered sort popup (``show_sort_menu``). A live ``checked``
        predicate marks the active pane's current mode."""
        sort_modes = (("Name", "name"), ("Size", "size"), ("Date", "date"), ("Type", "type"))
        return Menu(*[
            MenuItem(label, on_select=(lambda m=mode: self._set_sort(m)),
                     checked=(lambda m=mode: self.active_pane()["sort_mode"] == m))
            for label, mode in sort_modes
        ], title="Sort By")

    def show_sort_menu(self) -> None:
        """Pop the sort menu over the active pane (the 's' key)."""
        rx, rw = self._active_pane_region()
        self.panel.popup_menu(self._sort_menu(), rx + rw / 2.0, 2.0)
        self.panel.render()

    #: Keyboard nudge for the pane boundary / log height (fraction of the split),
    #: and the page size (lines) for keyboard log scrolling.
    _PANE_STEP = 0.05
    _LOG_STEP = 0.05
    _LOG_PAGE = 10.0

    @staticmethod
    def _nudge(splitter, delta: float) -> None:
        """Shift a Splitter's fraction by ``delta`` from the keyboard, clamped to
        a sane range so a pane can't be nudged to nothing (the mouse-drag path has
        its own base-unit min-size clamp; this keeps the keyboard path safe too)."""
        splitter.fraction = max(0.1, min(0.9, splitter.fraction + delta))

    def _theme_menu(self) -> Menu:
        """The theme picker, shared by the View menu's 'Theme' submenu. A live
        ``checked`` predicate marks the active palette (mirrors ``_sort_menu``)."""
        return Menu(*[
            MenuItem(name, on_select=(lambda i=i: self._select_theme(i)),
                     checked=(lambda i=i: self._theme_index == i))
            for i, (name, _theme) in enumerate(THEMES)
        ], title="Theme")

    def _apply_theme(self, index: int) -> None:
        """Switch the active palette. One assignment recolors every widget: the
        chrome and file lists read the theme at draw time, and the surface-role
        backgrounds re-resolve on the next render."""
        self._theme_index = index % len(THEMES)
        name, theme = THEMES[self._theme_index]
        self.panel.theme = theme
        self.log_info(f"Theme: {name}")

    def _cycle_theme(self) -> None:
        """Advance to the next palette (the ``toggle_color_scheme`` / T action)."""
        self._apply_theme(self._theme_index + 1)

    def _select_theme(self, index: int) -> None:
        """Pick a specific palette from the menu, then redraw."""
        self._apply_theme(index)
        self.panel.render()

    def _quick_sort(self, mode: str) -> None:
        """Set the active pane's sort mode from a quick-sort key; pressing the
        same mode again toggles the sort direction (mirrors ttk TFM's quick_sort).
        The current reverse setting is kept when switching to a new mode."""
        pane = self.active_pane()
        if pane["sort_mode"] == mode:
            pane["sort_reverse"] = not pane["sort_reverse"]
        else:
            pane["sort_mode"] = mode
        self.flm.refresh_files(pane)
        self.log_info(f"Sort: {self.flm.get_sort_description(pane)}")

    def _set_sort(self, mode: str) -> None:
        pane = self.active_pane()
        pane["sort_mode"] = mode
        self.flm.refresh_files(pane)
        self.log_info(f"Sort: {self.flm.get_sort_description(pane)}")
        self.panel.render()

    def _toggle_reverse(self) -> None:
        pane = self.active_pane()
        pane["sort_reverse"] = not pane["sort_reverse"]
        self.flm.refresh_files(pane)
        self.log_info(f"Sort: {self.flm.get_sort_description(pane)}")
        self.panel.render()

    def confirm_quit(self) -> None:
        """A modal confirm before quitting — the canonical message-box pattern."""
        show_message_box(
            self.panel, "Quit TFM?", title="Confirm", icon="warning",
            buttons=("Quit", "Cancel"), default=1, cancel=1,
            on_result=lambda label: self._quit() if label == "Quit" else None,
        )
        self.panel.render()

    def show_favorites(self) -> None:
        """The modal filter-list dialog: pick a favorite directory and jump the
        active pane there. The canonical searchable-list-picker pattern (TFM's
        ``BaseListDialog`` workhorse), built from PuiKit's TextEdit + ListView."""
        favorites = get_favorite_directories()
        if not favorites:
            show_message_box(self.panel, "No favorite directories configured.",
                             title="Favorites", icon="info")
            self.panel.render()
            return
        show_filter_list(
            self.panel, favorites, title="Go to Favorite",
            to_label=lambda fav: f"{fav['name']}  —  {fav['path']}",
            on_accept=self._jump_to_favorite,
            region=self._active_pane_region(),
        )
        self.panel.render()

    def _active_pane_region(self) -> tuple[float, float]:
        """The ``(x, width)`` column span of the active pane, in base units, for
        anchoring pane-targeting dialogs over the pane they act on. Mirrors the
        pane_splitter geometry: the left pane gets ``left_pane_ratio`` of the
        width, the right pane the remainder."""
        sw, _ = self.panel.backend.size_units
        left_w = sw * self.pm.left_pane_ratio
        if self.pm.active_pane == "left":
            return (0.0, left_w)
        return (left_w, sw - left_w)

    def _local_drives(self) -> list[dict]:
        """Home / root / common folders + mounted volumes, as ``{name, path}``
        rows for the drives picker. SSH hosts are added by ``_ssh_drives``; S3
        buckets (an async, credentialed scan) remain a later phase."""
        drives = [{"name": "Home", "path": str(Path.home())},
                  {"name": "Root", "path": "/"}]
        for name in ("Documents", "Downloads", "Desktop"):
            p = Path.home() / name
            try:
                if p.exists() and p.is_dir():
                    drives.append({"name": name, "path": str(p)})
            except Exception:
                pass
        if platform.system() == "Darwin":
            vol_roots = ["/Volumes"]
        else:
            vol_roots = [f"/media/{os.environ.get('USER', '')}", "/media", "/mnt"]
        for root in vol_roots:
            try:
                rp = Path(root)
                if rp.exists() and rp.is_dir():
                    for v in rp.iterdir():
                        if v.is_dir():
                            drives.append({"name": v.name, "path": str(v)})
            except Exception:
                pass
        seen, out = set(), []
        for d in drives:
            if d["path"] not in seen:
                seen.add(d["path"])
                out.append(d)
        return out

    def _ssh_drives(self) -> list[dict]:
        """SSH hosts from ``~/.ssh/config`` as ``ssh://host/`` rows for the drives
        picker. Reads only the local config file (no network); best-effort, so a
        missing or unreadable config — or an absent SSH layer — yields nothing.
        ``Host *`` wildcard blocks are dropped by the parser, not connectable."""
        try:
            from tfm_ssh_config import SSHConfigParser
            hosts = SSHConfigParser().parse()
        except Exception:
            return []
        out = []
        for hostname, cfg in hosts.items():
            user = cfg.get("User", "")
            actual = cfg.get("HostName", hostname)
            label = f"{user}@{actual}" if user else actual
            out.append({"name": label, "path": f"ssh://{hostname}/"})
        return out

    def show_drives(self) -> None:
        """The drives picker: choose a volume / common location / SSH host and
        jump the active pane there (reuses the searchable-list dialog, like
        favorites). Selecting an ``ssh://`` host connects on first listing."""
        show_filter_list(
            self.panel, self._local_drives() + self._ssh_drives(), title="Drives",
            to_label=lambda d: f"{d['name']}  —  {d['path']}",
            on_accept=self._go_to_drive,
            region=self._active_pane_region())
        self.panel.render()

    def _go_to_drive(self, drive: dict) -> None:
        pane = self.active_pane()
        pane["path"] = Path(drive["path"])
        self._refresh(pane)
        pane["selected_files"].clear()
        self.log_info(f"Drive: {drive['path']}")
        self.panel.render()

    def show_search(self) -> None:
        """Recursive filename search under the active pane (the Shift-F dialog):
        prompt for a substring, walk the tree (bounded, honouring the hidden-file
        setting), then present the hits in the searchable-list dialog; picking one
        navigates to its directory and lands the cursor on it."""
        pane = self.active_pane()
        root = pane["path"]

        def run(pattern: str) -> None:
            pattern = pattern.strip()
            if not pattern:
                self.panel.render()
                return
            results = self._walk_match(root, pattern)
            if not results:
                show_message_box(self.panel, f"No matches for '{pattern}'.",
                                 title="Search", icon="info")
                self.panel.render()
                return
            root_str = str(root)
            def label(entry) -> str:
                s = str(entry)
                return s[len(root_str):].lstrip("/") if s.startswith(root_str) else s
            show_filter_list(
                self.panel, results, title=f"Search: {pattern} ({len(results)})",
                to_label=label, on_accept=self._go_to_result,
                region=self._active_pane_region())
            self.panel.render()

        show_input(self.panel, title="Search Files", prompt="Filename:",
                   on_accept=run, region=self._active_pane_region())
        self.panel.render()

    def _walk_match(self, root, pattern: str, cap: int = 1000, node_cap: int = 50000):
        """Depth-first walk under ``root`` collecting entries whose name contains
        ``pattern`` (case-insensitive), bounded by ``cap`` results and ``node_cap``
        entries visited so a huge tree can't hang the UI. Hidden entries are
        skipped unless the pane is showing them."""
        import fnmatch
        pat = pattern.lower()
        if not pat.startswith("*"):
            pat = "*" + pat
        if not pat.endswith("*"):
            pat = pat + "*"
        results, stack, nodes = [], [root], 0
        while stack and len(results) < cap and nodes < node_cap:
            try:
                entries = list(stack.pop().iterdir())
            except Exception:
                continue
            for e in entries:
                nodes += 1
                if not self.flm.show_hidden and e.name.startswith("."):
                    continue
                try:
                    if fnmatch.fnmatch(e.name.lower(), pat):
                        results.append(e)
                    if e.is_dir():
                        stack.append(e)
                except Exception:
                    continue
        return results

    def _go_to_result(self, entry) -> None:
        pane = self.active_pane()
        pane["path"] = entry.parent
        self._refresh(pane)
        self._select_by_name(pane, entry.name)
        self.log_info(f"Found: {entry}")
        self.panel.render()

    def show_history(self) -> None:
        """The recent-directory picker: pick a previously visited directory and
        jump the active pane there. Shows most-recent-first, de-duplicated."""
        seen, items = set(), []
        for p in reversed(self._history):
            if p not in seen:
                seen.add(p)
                items.append(p)
        if not items:
            show_message_box(self.panel, "No directory history yet.",
                             title="History", icon="info")
            self.panel.render()
            return
        show_filter_list(
            self.panel, items, title="History", to_label=lambda p: p,
            on_accept=self._go_to_history, region=self._active_pane_region())
        self.panel.render()

    def _go_to_history(self, path: str) -> None:
        pane = self.active_pane()
        pane["path"] = Path(path)
        self._refresh(pane)
        pane["selected_files"].clear()
        self.log_info(f"History: {path}")
        self.panel.render()

    def show_programs(self) -> None:
        """The external-programs picker: choose a configured program and launch it
        on the selection (or the focused entry). Launched fire-and-forget with the
        active pane as the working directory — well suited to the GUI launchers in
        the default config (VS Code, BeyondCompare). Programs that need to take
        over the terminal await a backend suspend/resume (see ``edit_file``)."""
        programs = getattr(self.config, "PROGRAMS", None) or []
        if not programs:
            show_message_box(self.panel, "No external programs configured.",
                             title="Programs", icon="info")
            self.panel.render()
            return
        show_filter_list(
            self.panel, programs, title="External Programs",
            to_label=lambda p: p.get("name", "?"),
            on_accept=self._run_program, region=self._active_pane_region())
        self.panel.render()

    def _run_program(self, program: dict) -> None:
        from tfm_external_programs import (ensure_common_paths_in_env,
                                           get_selected_or_cursor_files)
        pane = self.active_pane()
        command = list(program.get("command", []))
        if not command:
            self.log_info(f"Program '{program.get('name')}' has no command")
            return
        args = get_selected_or_cursor_files(pane)  # bare names, resolved via cwd
        env = os.environ.copy()
        ensure_common_paths_in_env(env)
        try:
            subprocess.Popen(command + args, cwd=str(pane["path"]), env=env)
        except Exception as exc:
            self.log_info(f"Failed to launch {program.get('name')}: {exc}")
        else:
            self.log_info(f"Launched: {program.get('name')}")
        self.panel.render()

    def _jump_to_favorite(self, fav: dict) -> None:
        pane = self.active_pane()
        pane["path"] = Path(fav["path"])
        self._refresh(pane)
        self.log_info(f"Jumped to {fav['name']} ({fav['path']})")
        self.panel.render()

    def _select_by_name(self, pane: dict, name: str) -> None:
        """Land the cursor on the entry called ``name`` (after create/rename)."""
        for i, entry in enumerate(pane["files"]):
            if entry.name == name:
                pane["focused_index"] = i
                break

    def create_directory(self) -> None:
        """Prompt for a name and create a directory in the active pane — the
        canonical text-input dialog, mirroring ttk TFM's create-directory flow."""
        pane = self.active_pane()

        def validate(name: str) -> str | None:
            name = name.strip()
            if not name:
                return "Directory name cannot be empty"
            if (pane["path"] / name).exists():
                return f"'{name}' already exists"
            return None

        def accept(name: str) -> None:
            name = name.strip()
            try:
                (pane["path"] / name).mkdir(parents=True, exist_ok=False)
            except OSError as exc:
                self.log_info(f"Failed to create directory '{name}': {exc}")
            else:
                self.log_info(f"Created directory: {name}")
                self._refresh(pane)
                self._select_by_name(pane, name)
            self.panel.render()

        show_input(self.panel, title="New Directory", prompt="Name:",
                   on_accept=accept, validate=validate, region=self._active_pane_region())
        self.panel.render()

    def create_file(self) -> None:
        """Prompt for a name and create an empty file in the active pane."""
        pane = self.active_pane()

        def validate(name: str) -> str | None:
            name = name.strip()
            if not name:
                return "File name cannot be empty"
            if (pane["path"] / name).exists():
                return f"'{name}' already exists"
            return None

        def accept(name: str) -> None:
            name = name.strip()
            try:
                (pane["path"] / name).touch()
            except OSError as exc:
                self.log_info(f"Failed to create file '{name}': {exc}")
            else:
                self.log_info(f"Created file: {name}")
                self._refresh(pane)
                self._select_by_name(pane, name)
            self.panel.render()

        show_input(self.panel, title="New File", prompt="Name:",
                   on_accept=accept, validate=validate, region=self._active_pane_region())
        self.panel.render()

    def rename(self) -> None:
        """Rename in the active pane. With more than one file selected this opens
        the batch-rename dialog; otherwise it prompts for the focused entry."""
        pane = self.active_pane()
        files = pane["files"]
        if not files:
            self.log_info("No file to rename")
            return
        selected = [f for f in files if str(f) in pane["selected_files"]]
        if len(selected) > 1:
            self.batch_rename(selected)
            return
        entry = files[pane["focused_index"]]
        original = entry.name

        def validate(name: str) -> str | None:
            name = name.strip()
            if not name:
                return "Name cannot be empty"
            if name == original:
                return None  # unchanged is allowed (a no-op on accept)
            if (entry.parent / name).exists():
                return f"'{name}' already exists"
            return None

        def accept(name: str) -> None:
            name = name.strip()
            if name == original:
                self.panel.render()
                return
            try:
                entry.rename(entry.parent / name)
            except OSError as exc:
                self.log_info(f"Failed to rename '{original}': {exc}")
            else:
                self.log_info(f"Renamed '{original}' to '{name}'")
                self._refresh(pane)
                self._select_by_name(pane, name)
            self.panel.render()

        show_input(self.panel, title="Rename", prompt="Rename to:", text=original,
                   on_accept=accept, validate=validate, region=self._active_pane_region())
        self.panel.render()

    def batch_rename(self, files: list) -> None:
        """Open the regex batch-rename dialog over the given selected files."""
        pane = self.active_pane()

        def done(success: int, errors: list[str]) -> None:
            for err in errors:
                self.log_info(f"Rename failed: {err}")
            self.log_info(f"Batch rename: {success} file(s) renamed"
                          + (f", {len(errors)} failed" if errors else ""))
            pane["selected_files"].clear()
            self._refresh(pane)
            self.panel.render()

        show_batch_rename(self.panel, files, on_done=done)
        self.panel.render()

    def view_file(self) -> None:
        """Open the focused file in the built-in text viewer (directories are
        skipped). Binary files show a placeholder rather than garbage."""
        pane = self.active_pane()
        files = pane["files"]
        if not files:
            return
        entry = files[pane["focused_index"]]
        try:
            if entry.is_dir():
                self.log_info(f"{entry.name} is a directory")
                return
        except Exception:
            pass
        show_text_viewer(self.panel, entry)
        self.panel.render()

    def diff_files(self) -> None:
        """Compare exactly two selected files side by side. Files may be selected
        across both panes (mirrors ttk TFM)."""
        selected: list = []
        for name in ("left", "right"):
            pane = self.pane(name)
            for entry in pane["files"]:
                if str(entry) in pane["selected_files"]:
                    selected.append(entry)
        files = []
        for entry in selected:
            try:
                if not entry.is_dir():
                    files.append(entry)
            except Exception:
                pass
        if len(files) != 2:
            self.log_info(f"Select exactly 2 files to compare (selected {len(files)})")
            return
        show_diff_viewer(self.panel, files[0], files[1])
        self.panel.render()

    def diff_directories(self) -> None:
        """Recursively compare the two panes' current directories side by side
        (the Shift-EQUAL action). Mirrors ttk TFM's directory diff viewer."""
        left = self.pane("left")["path"]
        right = self.pane("right")["path"]
        show_directory_diff_viewer(self.panel, left, right,
                                   show_hidden=self.flm.show_hidden)
        self.panel.render()

    # --- file operations (copy / move / delete) ------------------------------

    def _selected_or_focused(self, pane: dict) -> list:
        """The operation targets: the explicitly selected entries, or — when the
        selection is empty — the single entry under the cursor. Returns Path
        objects (``selected_files`` stores string paths), preserving list order."""
        selected = [f for f in pane["files"] if str(f) in pane["selected_files"]]
        if selected:
            return selected
        entry = self._focused_entry()
        return [entry] if entry is not None else []

    @staticmethod
    def _delete_path(entry) -> None:
        """Delete a file or directory through the storage-agnostic Path API,
        recursing into directories (``copy_to`` / ``move_to`` handle their own
        recursion, but delete has no single primitive)."""
        if entry.is_dir() and not entry.is_symlink():
            for child in entry.iterdir():
                TfmApp._delete_path(child)
            entry.rmdir()
        else:
            entry.unlink()

    def copy_files(self) -> None:
        """Copy the active pane's selection (or cursor entry) into the other
        pane's directory (the 'C' key). Mirrors ttk TFM's copy-to-other-pane."""
        self._transfer("copy")

    def move_files(self) -> None:
        """Move the active pane's selection (or cursor entry) into the other
        pane's directory (the 'M' key, when a selection exists)."""
        self._transfer("move")

    def _transfer(self, kind: str) -> None:
        """Shared copy/move flow: resolve targets and destination, warn on
        conflicts, confirm (honouring ``CONFIRM_COPY`` / ``CONFIRM_MOVE``), then
        run the transfer through ``Path.copy_to`` / ``Path.move_to`` (which
        recurse into directories and handle cross-storage transfers)."""
        verb = "Copy" if kind == "copy" else "Move"
        src_pane = self.active_pane()
        dst_pane = self.pm.get_inactive_pane()
        dest_dir = dst_pane["path"]
        targets = self._selected_or_focused(src_pane)
        if not targets:
            self.log_info(f"No file to {kind}")
            return
        if str(dest_dir) == str(src_pane["path"]):
            self.log_info(f"Cannot {kind}: source and destination are the same directory")
            return

        conflicts = [t for t in targets if (dest_dir / t.name).exists()]
        message = f"{verb} {len(targets)} item(s) to {dest_dir}?"
        if conflicts:
            message += f"\n{len(conflicts)} already exist there."

        def run(overwrite: bool) -> None:
            done = skipped = failed = 0
            for t in targets:
                dest = dest_dir / t.name
                try:
                    if dest.exists() and not overwrite:
                        skipped += 1
                        continue
                    (t.copy_to if kind == "copy" else t.move_to)(dest, overwrite=overwrite)
                    done += 1
                except Exception as exc:
                    failed += 1
                    self.log_info(f"{verb} failed for {t.name}: {exc}")
            self.flm.refresh_files(dst_pane)
            if kind == "move":
                self.flm.refresh_files(src_pane)
            src_pane["selected_files"].clear()
            summary = f"{verb}: {done} done"
            if skipped:
                summary += f", {skipped} skipped (exists)"
            if failed:
                summary += f", {failed} failed"
            self.log_info(summary)
            self.panel.render()

        confirm = getattr(self.config, f"CONFIRM_{verb.upper()}", True)
        # A conflict always prompts (never silently overwrite), even if the plain
        # confirm is disabled; the buttons then choose the overwrite policy.
        if conflicts:
            def on_result(label: str) -> None:
                if label == "Cancel":
                    self.panel.render()
                else:
                    run(overwrite=(label == "Overwrite"))
            show_message_box(
                self.panel, message, title=verb, icon="warning",
                buttons=("Overwrite", "Skip existing", "Cancel"),
                default=2, cancel=2, on_result=on_result)
        elif confirm:
            def on_result(label: str) -> None:
                if label == verb:
                    run(overwrite=False)
                else:
                    self.panel.render()
            show_message_box(
                self.panel, message, title=verb, icon="info",
                buttons=(verb, "Cancel"), default=0, cancel=1, on_result=on_result)
        else:
            run(overwrite=False)
            return
        self.panel.render()

    def delete_files(self) -> None:
        """Delete the active pane's selection (or cursor entry) after a confirm
        (honouring ``CONFIRM_DELETE``). Directories are removed recursively."""
        pane = self.active_pane()
        targets = self._selected_or_focused(pane)
        if not targets:
            self.log_info("No file to delete")
            return

        def run() -> None:
            done = failed = 0
            for t in targets:
                try:
                    self._delete_path(t)
                    done += 1
                except Exception as exc:
                    failed += 1
                    self.log_info(f"Delete failed for {t.name}: {exc}")
            pane["selected_files"].clear()
            self._refresh(pane)
            summary = f"Delete: {done} removed"
            if failed:
                summary += f", {failed} failed"
            self.log_info(summary)
            self.panel.render()

        if getattr(self.config, "CONFIRM_DELETE", True):
            names = ", ".join(t.name for t in targets[:3])
            if len(targets) > 3:
                names += f", … ({len(targets)} total)"
            def on_result(label: str) -> None:
                if label == "Delete":
                    run()
                else:
                    self.panel.render()
            show_message_box(
                self.panel, f"Delete {len(targets)} item(s)?\n{names}\nThis cannot be undone.",
                title="Delete", icon="warning", buttons=("Delete", "Cancel"),
                default=1, cancel=1, on_result=on_result)
            self.panel.render()
        else:
            run()

    # --- archives (create / extract) -----------------------------------------

    #: Recognised archive extensions → format label, longest suffixes first so
    #: ``.tar.gz`` is matched before ``.tar`` when scanning a filename's end.
    _ARCHIVE_EXTS = (
        (".tar.gz", "tar.gz"), (".tgz", "tar.gz"),
        (".tar.bz2", "tar.bz2"), (".tbz2", "tar.bz2"),
        (".tar.xz", "tar.xz"), (".txz", "tar.xz"),
        (".zip", "zip"), (".tar", "tar"),
    )
    #: tarfile write modes per format label (zip is handled separately).
    _TAR_MODES = {"tar": "w", "tar.gz": "w:gz", "tar.bz2": "w:bz2", "tar.xz": "w:xz"}

    @classmethod
    def _archive_format(cls, name: str) -> str | None:
        """The format label for ``name`` by its extension, or None if it isn't a
        recognised archive."""
        low = name.lower()
        return next((fmt for ext, fmt in cls._ARCHIVE_EXTS if low.endswith(ext)), None)

    @classmethod
    def _archive_basename(cls, name: str) -> str:
        """``name`` with its recognised archive extension stripped (the default
        extraction subdirectory), or unchanged if none matches."""
        low = name.lower()
        for ext, _fmt in cls._ARCHIVE_EXTS:
            if low.endswith(ext):
                return name[: -len(ext)]
        return name

    @staticmethod
    def _add_to_zip(zf, path, arcname: str) -> int:
        """Add ``path`` to an open ZipFile under ``arcname``, recursing into
        directories (tarfile recurses on its own; zipfile does not). Returns the
        number of files written."""
        if path.is_dir() and not path.is_symlink():
            count = 0
            for child in path.iterdir():
                count += TfmApp._add_to_zip(zf, child, f"{arcname}/{child.name}")
            return count
        zf.write(str(path), arcname)
        return 1

    def _write_archive(self, sources: list, archive_path, fmt: str) -> int:
        """Write ``sources`` into a new archive at ``archive_path`` in ``fmt``.
        Local filesystem paths (this phase); returns the number of files added."""
        import tarfile
        import zipfile
        if fmt == "zip":
            with zipfile.ZipFile(str(archive_path), "w", zipfile.ZIP_DEFLATED) as zf:
                return sum(self._add_to_zip(zf, s, s.name) for s in sources)
        with tarfile.open(str(archive_path), self._TAR_MODES[fmt]) as tf:
            for s in sources:
                tf.add(str(s), arcname=s.name)  # tarfile recurses into directories
            return len(tf.getmembers())

    def _extract_archive(self, archive_path, dest_dir, fmt: str) -> int:
        """Extract ``archive_path`` into ``dest_dir`` (created if absent). Returns
        the number of entries. Tar extraction uses the ``data`` filter where
        available (Python 3.12+) to reject unsafe member paths."""
        import tarfile
        import zipfile
        dest_dir.mkdir(parents=True, exist_ok=True)
        if fmt == "zip":
            with zipfile.ZipFile(str(archive_path)) as zf:
                zf.extractall(str(dest_dir))
                return len(zf.namelist())
        with tarfile.open(str(archive_path)) as tf:
            members = tf.getmembers()
            try:
                tf.extractall(str(dest_dir), filter="data")
            except TypeError:  # older Python without the extraction filter
                tf.extractall(str(dest_dir))
            return len(members)

    def create_archive(self) -> None:
        """Create an archive from the active pane's selection (or cursor entry)
        in the other pane's directory (the 'P' key). Prompts for a filename whose
        extension picks the format; an unrecognised extension defaults to
        ``.tar.gz``. Mirrors ttk TFM's create-archive flow."""
        pane = self.active_pane()
        sources = self._selected_or_focused(pane)
        if not sources:
            self.log_info("No files to archive")
            return
        dest_dir = self.pm.get_inactive_pane()["path"]
        # Prefill a single item's name plus a dot, ready for the extension.
        initial = ""
        if len(sources) == 1:
            base = sources[0].stem if sources[0].is_file() else sources[0].name
            initial = f"{base}."

        def accept(name: str) -> None:
            name = name.strip()
            if not name:
                self.panel.render()
                return
            fmt = self._archive_format(name)
            if fmt is None:  # no recognised extension → default to .tar.gz
                name += ".tar.gz"
                fmt = "tar.gz"
            archive_path = dest_dir / name

            def go() -> None:
                try:
                    added = self._write_archive(sources, archive_path, fmt)
                except Exception as exc:
                    self.log_info(f"Archive creation failed: {exc}")
                else:
                    self.log_info(f"Created {name} ({added} file(s)) in {dest_dir}")
                self.flm.refresh_files(self.pm.get_inactive_pane())
                self.panel.render()

            if archive_path.exists():
                show_message_box(
                    self.panel, f"'{name}' already exists in the other pane. Overwrite?",
                    title="Create Archive", icon="warning", buttons=("Overwrite", "Cancel"),
                    default=1, cancel=1,
                    on_result=lambda l: go() if l == "Overwrite" else self.panel.render())
                self.panel.render()
            else:
                go()

        def validate(name: str) -> str | None:
            return None if name.strip() else "Archive name cannot be empty"

        show_input(self.panel, title="Create Archive", prompt="Archive filename:",
                   text=initial, on_accept=accept, validate=validate, select_all=False,
                   region=self._active_pane_region())
        self.panel.render()

    def extract_archive(self) -> None:
        """Extract the focused archive into a subdirectory (named after the
        archive) in the other pane's directory (the 'U' key). Confirms when
        ``CONFIRM_EXTRACT_ARCHIVE`` is set or the destination already exists."""
        entry = self._focused_entry()
        if entry is None:
            self.log_info("No file to extract")
            return
        try:
            if not entry.is_file():
                self.log_info(f"{entry.name} is not a file")
                return
        except Exception:
            pass
        fmt = self._archive_format(entry.name)
        if fmt is None:
            self.log_info(f"'{entry.name}' is not a supported archive")
            return
        dest_dir = self.pm.get_inactive_pane()["path"]
        target = dest_dir / self._archive_basename(entry.name)

        def go() -> None:
            try:
                count = self._extract_archive(entry, target, fmt)
            except Exception as exc:
                self.log_info(f"Extraction failed: {exc}")
            else:
                self.log_info(f"Extracted {entry.name} → {target.name}/ ({count} entries)")
            self.flm.refresh_files(self.pm.get_inactive_pane())
            self.panel.render()

        exists = target.exists()
        if exists or getattr(self.config, "CONFIRM_EXTRACT_ARCHIVE", True):
            message = f"Extract '{entry.name}' to {target}?"
            if exists:
                message += "\nThe destination exists; files may be overwritten."
            show_message_box(
                self.panel, message, title="Extract Archive", icon="info",
                buttons=("Extract", "Cancel"), default=0, cancel=1,
                on_result=lambda l: go() if l == "Extract" else self.panel.render())
            self.panel.render()
        else:
            go()

    def _active_view(self) -> FilePane:
        return self.left_view if self.pm.active_pane == "left" else self.right_view

    def enter_filter(self) -> None:
        """Prompt for a filename filter and apply it to the active pane (the ';'
        key). An ``fnmatch`` glob (e.g. ``*.py``); directories are always shown,
        an empty pattern clears the filter. Mirrors ttk TFM's filter mode — the
        pattern lives in ``pane['filter_pattern']`` and the footer already shows
        it. Prefilled with the current filter so it's easy to edit or clear."""
        pane = self.active_pane()

        def accept(pattern: str) -> None:
            pattern = pattern.strip()
            count = self.flm.apply_filter(pane, pattern)
            if pattern:
                self.log_info(f"Filter '{pattern}': {count} item(s)")
            else:
                self.log_info("Filter cleared")
            self.panel.render()

        show_input(self.panel, title="Filter", prompt="Pattern:",
                   text=pane["filter_pattern"], on_accept=accept,
                   region=self._active_pane_region())
        self.panel.render()

    def enter_isearch(self) -> None:
        """Incremental search over the active pane (the 'F' key): a compact prompt
        pinned above the pane; as you type a case-insensitive *contains* pattern
        (space-separated patterns all match), every hit is highlighted and the
        cursor jumps to the nearest match at or after its current position. Enter
        keeps the landing spot; Esc restores the pre-search position. Mirrors ttk
        TFM's isearch, reusing ``FileListManager.find_matches``."""
        pane = self.active_pane()
        view = self._active_view()
        origin = pane["focused_index"]

        def jump(pattern: str) -> None:
            matches = self.flm.find_matches(
                pane, pattern, match_all=True, return_indices_only=True)
            view.search_matches = set(matches)
            if matches:
                cur = pane["focused_index"]
                pane["focused_index"] = next((m for m in matches if m >= cur), matches[0])
            else:
                pane["focused_index"] = origin
            self.panel.render()

        def finish(_pattern: str) -> None:
            view.search_matches = set()
            self.panel.render()

        def cancel() -> None:
            view.search_matches = set()
            pane["focused_index"] = origin
            self.panel.render()

        show_input(self.panel, prompt="I-Search:", on_change=jump,
                   on_accept=finish, on_cancel=cancel, dim_below=False,
                   anchor="top", region=self._active_pane_region())
        self.panel.render()

    def jump_to_path(self) -> None:
        """Prompt for a directory path and navigate the active pane there.
        Accepts ``~``, relative (to the current path), and absolute paths;
        mirrors ttk TFM's jump-to-path. (TAB path completion is a later phase.)"""
        pane = self.active_pane()
        current = str(pane["path"])

        def resolve(text: str) -> Path:
            text = text.strip()
            if text.startswith("~"):
                target = Path.home() / text[1:].lstrip("/")
            elif not os.path.isabs(text):
                target = Path(current) / text
            else:
                target = Path(text)
            return Path(os.path.normpath(str(target)))

        def validate(text: str) -> str | None:
            if not text.strip():
                return "Path cannot be empty"
            target = resolve(text)
            if not target.exists():
                return f"Path does not exist: {target}"
            if not target.is_dir():
                return f"Not a directory: {target}"
            return None

        def accept(text: str) -> None:
            target = resolve(text)
            pane["path"] = target
            self._refresh(pane)
            pane["selected_files"].clear()
            self.log_info(f"Jumped to: {target}")
            self.panel.render()

        # Prefill with the current path plus a trailing separator, ready to type
        # a child directory name (the ttk behaviour).
        initial = current if current.endswith(os.sep) else current + os.sep
        show_input(self.panel, title="Jump to Path", prompt="Path:", text=initial,
                   on_accept=accept, validate=validate, select_all=False,
                   region=self._active_pane_region())
        self.panel.render()

    #: Help layout: (section title, [(action, description)]). Only actions the
    #: PuiKit port actually handles are listed, so the help never promises a
    #: feature that isn't wired yet.
    _HELP_SECTIONS = (
        ("Navigation", (
            ("cursor_up", "Move cursor up"),
            ("cursor_down", "Move cursor down"),
            ("page_up", "Scroll up by page"),
            ("page_down", "Scroll down by page"),
            ("open_item", "Enter directory"),
            ("go_parent", "Go to parent directory"),
            ("switch_pane", "Switch active pane"),
            ("nav_left", "Focus left pane / go to parent"),
            ("nav_right", "Focus right pane / go to parent"),
            ("favorites", "Go to a favorite directory"),
            ("jump_to_path", "Jump to a typed path"),
            ("drives_dialog", "Open the drives / locations picker"),
            ("history", "Go to a recently-visited directory"),
            ("sync_current_to_other", "Go to the other pane's directory"),
            ("sync_other_to_current", "Send this directory to the other pane"),
        )),
        ("Selection", (
            ("select_file", "Toggle selection, move down"),
            ("select_file_up", "Toggle selection, move up"),
            ("select_all_files", "Toggle all files"),
            ("select_all_items", "Toggle all items"),
            ("select_all", "Select every item"),
            ("unselect_all", "Clear selection"),
        )),
        ("File Operations", (
            ("create_directory", "Create new directory"),
            ("create_file", "Create new file"),
            ("rename_file", "Rename file/directory"),
            ("copy_files", "Copy selection to the other pane"),
            ("move_files", "Move selection to the other pane"),
            ("delete_files", "Delete selection"),
            ("create_archive", "Create archive from selection"),
            ("extract_archive", "Extract the focused archive"),
            ("file_details", "Show file details"),
            ("open_with_os", "Open with the default app"),
            ("reveal_in_os", "Reveal in the OS file manager"),
            ("programs", "Run an external program on the selection"),
        )),
        ("Search", (
            ("search", "Incremental search (jump to match)"),
            ("filter", "Filter list by filename pattern"),
            ("clear_filter", "Clear the filename filter"),
            ("search_dialog", "Recursive filename search"),
        )),
        ("View", (
            ("view_file", "View file (text viewer)"),
            ("diff_files", "Compare two selected files"),
            ("toggle_hidden", "Toggle hidden files"),
            ("toggle_color_scheme", "Cycle color theme"),
            ("sort_menu", "Sort options (menu)"),
            ("quick_sort_name", "Quick-sort by name (repeat: reverse)"),
            ("quick_sort_size", "Quick-sort by size (repeat: reverse)"),
            ("quick_sort_date", "Quick-sort by date (repeat: reverse)"),
            ("quick_sort_ext", "Quick-sort by extension (repeat: reverse)"),
        )),
        ("Other", (
            ("help", "Show this help"),
            ("quit", "Quit TFM"),
        )),
    )

    def _keys_label(self, action: str) -> str:
        """Comma-joined, display-formatted key(s) bound to ``action`` ("—" if
        unbound), for the help dialog."""
        keys, _ = self.keys.get_keys_for_action(action)
        if not keys:
            return "—"
        return ", ".join(self.keys.format_key_for_display(k) for k in keys)

    def show_help(self) -> None:
        """A scrollable key-binding reference, built live from the port's keymap."""
        from tfm_const import VERSION
        lines = [f"TFM on PuiKit — Version {VERSION}", ""]
        for title, entries in self._HELP_SECTIONS:
            lines.append(f"{title}:")
            for action, desc in entries:
                lines.append(f"  {self._keys_label(action)}  —  {desc}")
            lines.append("")
        show_text(self.panel, lines, title="Help")
        self.panel.render()

    def show_about(self) -> None:
        from tfm_const import VERSION
        show_message_box(
            self.panel,
            f"TFM on PuiKit\nVersion {VERSION}\n\nA dual-pane file manager.",
            title="About", icon="info", buttons=("OK",),
        )
        self.panel.render()

    def _show_context_menu(self, pane_name: str, index: int, x: float, y: float) -> None:
        """Right-click on a row: activate that row, then pop a context menu at the
        pointer (native on macOS, a widget popup on curses)."""
        self.pm.active_pane = pane_name
        self._sync_active()
        pane = self.active_pane()
        pane["focused_index"] = index
        entry = pane["files"][index] if 0 <= index < len(pane["files"]) else None
        selected = entry is not None and str(entry) in pane["selected_files"]
        menu = Menu(
            MenuItem("Open", on_select=lambda: self._menu("open_item")),
            MenuItem("View File", on_select=self.view_file, enabled=entry is not None),
            MenuItem("Deselect" if selected else "Select",
                     on_select=lambda: self._menu("select_file")),
            SEPARATOR,
            MenuItem("Rename…", on_select=self.rename, enabled=entry is not None),
            SEPARATOR,
            MenuItem("Copy to Other Pane", on_select=self.copy_files, enabled=entry is not None),
            MenuItem("Move to Other Pane", on_select=self.move_files, enabled=entry is not None),
            MenuItem("Delete", on_select=self.delete_files, enabled=entry is not None),
            SEPARATOR,
            MenuItem("Show Hidden Files", on_select=lambda: self._menu("toggle_hidden"),
                     checked=lambda: self.flm.show_hidden),
        )
        self.panel.popup_menu(menu, x, y)
        self.panel.render()

    # --- run -----------------------------------------------------------------

    #: Mouse events routed to the widget under the pointer (the FilePanes own
    #: click + wheel/trackpad scroll); keyboard uses TFM's global keymap.
    _MOUSE = frozenset({
        EventType.MOUSE_DOWN, EventType.MOUSE_UP, EventType.MOUSE_CLICK,
        EventType.MOUSE_DRAG, EventType.MOUSE_SCROLL,
    })

    def on_event(self, event) -> None:
        # Flush any filesystem reloads that landed since the last frame, so user
        # input and idle ticks both surface them; render if a pane changed.
        if self._pump_monitoring():
            self.panel.render()
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
        # A modal layer (message box, menu popup) owns events while open: route
        # everything to it and let TFM's global keymap stand down.
        if self.panel.has_layers:
            if self.panel.dispatch_event(event):
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

_VERSION = "0.99"


def create_parser() -> argparse.ArgumentParser:
    """Build the command-line parser. Factored out of ``main`` so the entry
    point's argument contract (``--version``, ``--help``, the pane flags) can be
    unit-tested without launching the app."""
    parser = argparse.ArgumentParser(
        prog="tfm",
        description=__doc__,
        epilog="Project home: https://github.com/shimomut/tfm",
    )
    parser.add_argument("-v", "--version", action="version",
                        version=f"TUI File Manager {_VERSION}")
    parser.add_argument("--backend", default="tui", help="tui (curses) | gui (macOS)")
    # ``default=None`` lets us tell an explicit ``--left .`` from no flag: an
    # explicitly given directory wins over the one saved from the last session.
    parser.add_argument("--left", default=None, help="left pane startup directory")
    parser.add_argument("--right", default=None, help="right pane startup directory")
    return parser


def main() -> None:
    args = create_parser().parse_args()

    backend = create_backend(_BACKENDS.get(args.backend, args.backend))
    with backend:
        TfmApp(
            backend,
            args.left if args.left is not None else ".",
            args.right if args.right is not None else ".",
            left_provided=args.left is not None,
            right_provided=args.right is not None,
        ).run()


if __name__ == "__main__":
    main()
