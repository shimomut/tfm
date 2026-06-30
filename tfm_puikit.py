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
import os
import sys
from pathlib import Path as _StdPath

sys.path.insert(0, str(_StdPath(__file__).parent / "src"))

import _config  # noqa: E402  (the canonical default Config template)
from puikit import EventType, Item, Panel, Style, TextAttribute, VSplit  # noqa: E402
from puikit.backends import create_backend  # noqa: E402
from puikit.menu import Menu, MenuItem, SEPARATOR  # noqa: E402
from puikit.text import elide  # noqa: E402
from puikit.widgets import LayoutView, LogView, MenuBar, Splitter, show_message_box  # noqa: E402
from puikit.widgets.base import Widget  # noqa: E402

#: Initial share of the content area given to the file panes (vs the log pane).
PANES_FRACTION = 0.74

from tfm_config import KeyBindings, get_favorite_directories  # noqa: E402
from tfm_file_list_manager import FileListManager  # noqa: E402
from tfm_file_pane import FilePane  # noqa: E402
from tfm_filter_list_dialog import show_filter_list  # noqa: E402
from tfm_input_dialog import show_input  # noqa: E402
from tfm_pane_manager import PaneManager  # noqa: E402
from tfm_path import Path  # noqa: E402
from tfm_batch_rename_view import show_batch_rename  # noqa: E402
from tfm_text_dialog import show_text  # noqa: E402


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
            fraction=PANES_FRACTION,
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
        self.log_info(f"TFM on PuiKit — {self.pm.left_pane['path']}")

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
        elif action in ("open_item", "nav_right"):
            self._open(pane)
        elif action in ("go_parent", "nav_left"):
            self._go_parent(pane)
        elif action == "toggle_hidden":
            self.flm.show_hidden = not self.flm.show_hidden
            self.flm.refresh_files(pane)
            self.log_info(f"Hidden files: {'shown' if self.flm.show_hidden else 'hidden'}")
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
        elif action == "jump_to_path":
            self.jump_to_path()
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

        sort_modes = (("Name", "name"), ("Size", "size"), ("Date", "date"), ("Type", "type"))
        sort_menu = Menu(*[
            MenuItem(label, on_select=(lambda m=mode: self._set_sort(m)),
                     checked=(lambda m=mode: self.active_pane()["sort_mode"] == m))
            for label, mode in sort_modes
        ], title="Sort By")

        file_menu = Menu(
            MenuItem("Open", on_select=lambda: self._menu("open_item"),
                     enabled=has_files, shortcut="Enter"),
            MenuItem("Parent Directory", on_select=lambda: self._menu("go_parent"),
                     shortcut="Backspace"),
            MenuItem("Go to Favorite…", on_select=self.show_favorites, shortcut="J"),
            MenuItem("Jump to Path…", on_select=self.jump_to_path, shortcut="Shift-J"),
            SEPARATOR,
            MenuItem("New Folder…", on_select=self.create_directory, shortcut="M"),
            MenuItem("New File…", on_select=self.create_file, shortcut="Shift-E"),
            MenuItem("Rename…", on_select=self.rename, enabled=has_files, shortcut="R"),
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
            title="Select",
        )
        view_menu = Menu(
            MenuItem("Show Hidden Files", on_select=lambda: self._menu("toggle_hidden"),
                     checked=lambda: self.flm.show_hidden, shortcut="."),
            MenuItem("Reverse Sort", on_select=self._toggle_reverse,
                     checked=lambda: self.active_pane()["sort_reverse"]),
            MenuItem("Sort By", submenu=sort_menu),
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
            on_result=lambda label: self.backend.quit() if label == "Quit" else None,
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
            ("favorites", "Go to a favorite directory"),
            ("jump_to_path", "Jump to a typed path"),
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
        )),
        ("View", (
            ("toggle_hidden", "Toggle hidden files"),
            ("sort_menu", "Sort options (menu)"),
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
            MenuItem("Deselect" if selected else "Select",
                     on_select=lambda: self._menu("select_file")),
            SEPARATOR,
            MenuItem("Rename…", on_select=self.rename, enabled=entry is not None),
            SEPARATOR,
            MenuItem("Copy", enabled=False),   # file ops land in a later phase
            MenuItem("Move", enabled=False),
            MenuItem("Delete", enabled=False),
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
