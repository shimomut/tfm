"""DirectoryDiffView — recursive side-by-side directory diff for the PuiKit port.

The PuiKit counterpart to ttk TFM's ``DirectoryDiffViewer``: compares two
directories recursively and shows the union of their trees side by side, each
node classified (only-left, only-right, content-different, contains-difference,
identical) with a centre separator glyph carrying the verdict. Directories
expand/collapse; ``n``/``N`` jump between differences; Enter on a differing file
opens the per-file diff (reusing :func:`tfm_diff_viewer.show_diff_viewer`).

Scanning is **progressive**: on open the viewer starts a background worker that
first walks both directory trees (metadata) and then compares each candidate
file's content, mutating the shared tree under a lock and raising a dirty flag.
A per-frame tick registered via ``panel.request_animation_ticks`` runs on the
main thread and re-renders when the flag is set, so a large tree fills in live
without blocking the UI. Pass ``background=False`` (tests) to scan synchronously.

This module keeps the backend-agnostic scanning/classification logic (ported
from the ttk version with the ttk imports dropped) and rewrites the rendering
and event handling as a :class:`~puikit.widgets.base.Widget`, following the
:mod:`tfm_diff_viewer` pattern. Push it with :func:`show_directory_diff_viewer`.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from puikit.backend import Style, TextAttribute
from puikit.event import Event, EventType
from puikit.panel import Rect
from puikit.text import elide, truncate_to_width
from puikit.widgets import show_message_box
from puikit.widgets.base import Widget

from tfm_path import Path
from tfm_str_format import format_size
from tfm_text_viewer import MONO, _ScrollBody
from tfm_diff_viewer import show_diff_viewer


class DifferenceType(Enum):
    """Classification of a node's difference between the two directories."""
    IDENTICAL = "identical"
    ONLY_LEFT = "only_left"
    ONLY_RIGHT = "only_right"
    CONTENT_DIFFERENT = "content_different"
    CONTAINS_DIFFERENCE = "contains_difference"
    PENDING = "pending"  # not yet scanned / compared


#: Centre separator glyph per verdict.
_SEPARATOR = {
    DifferenceType.IDENTICAL: " = ",
    DifferenceType.ONLY_LEFT: " < ",
    DifferenceType.ONLY_RIGHT: " > ",
    DifferenceType.CONTENT_DIFFERENT: " ! ",
    DifferenceType.CONTAINS_DIFFERENCE: " ! ",
    DifferenceType.PENDING: " ? ",
}
#: Verdicts that read as a "difference" (drive next/prev-diff and red tinting).
_IS_DIFF = frozenset({
    DifferenceType.ONLY_LEFT, DifferenceType.ONLY_RIGHT,
    DifferenceType.CONTENT_DIFFERENT, DifferenceType.CONTAINS_DIFFERENCE,
})


@dataclass
class FileInfo:
    """Metadata for a single scanned file or directory."""
    path: Path
    relative_path: str
    is_directory: bool
    size: int
    mtime: float
    is_accessible: bool
    error_message: Optional[str] = None


@dataclass
class TreeNode:
    """A single node in the unified directory tree."""
    name: str
    left_path: Optional[Path]
    right_path: Optional[Path]
    is_directory: bool
    difference_type: DifferenceType
    depth: int
    is_expanded: bool
    children: list["TreeNode"] = field(default_factory=list)
    parent: Optional["TreeNode"] = None


# --- scanning / classification (backend-agnostic, ported from ttk) -----------


class DirectoryScanner:
    """Recursively lists a directory into ``{relative_path: FileInfo}``.

    Iterative (stack-based) to avoid deep recursion; records inaccessible entries
    rather than aborting. ``show_hidden`` skips dot-entries when false. Supports
    cancellation via :meth:`cancel` (the progressive worker cancels on close)."""

    def __init__(self, show_hidden: bool = True):
        self.show_hidden = show_hidden
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def scan(self, root_path: Path,
             on_progress: Optional[Callable[[int], None]] = None) -> dict[str, FileInfo]:
        files: dict[str, FileInfo] = {}
        stack = [root_path]
        count = 0
        while stack and not self._cancel:
            current = stack.pop()
            try:
                relative = "" if current == root_path else str(current.relative_to(root_path))
                try:
                    st = current.stat()
                    is_dir = current.is_dir()
                    info = FileInfo(current, relative, is_dir,
                                    0 if is_dir else st.st_size, st.st_mtime, True)
                except (OSError, PermissionError) as exc:
                    info = FileInfo(current, relative, False, 0, 0.0, False, str(exc))
                if relative:
                    files[relative] = info
                    count += 1
                    if on_progress is not None and count % 50 == 0:
                        on_progress(count)
                if info.is_directory and info.is_accessible:
                    try:
                        for child in current.iterdir():
                            if not self.show_hidden and child.name.startswith("."):
                                continue
                            stack.append(child)
                    except (OSError, PermissionError) as exc:
                        info.is_accessible = False
                        info.error_message = f"Cannot read directory: {exc}"
            except Exception:
                continue
        if on_progress is not None:
            on_progress(count)
        return files


class DiffEngine:
    """Builds the unified tree from two scan dictionaries and classifies it.

    With ``compare_content=False`` two-sided files are left ``PENDING`` (their
    content comparison is deferred to the progressive comparison phase) and
    directories summarise their children — so the tree structure appears before
    any file is read."""

    def __init__(self, left_files: dict[str, FileInfo], right_files: dict[str, FileInfo],
                 compare_content: bool = True):
        self.left_files = left_files
        self.right_files = right_files
        self.compare_content = compare_content

    def build_tree(self) -> TreeNode:
        root = TreeNode("", None, None, True, DifferenceType.IDENTICAL, 0, True)
        for relative in sorted(set(self.left_files) | set(self.right_files)):
            self._add_path(root, relative)
        self._sort(root)
        self._classify(root)
        return root

    def _add_path(self, root: TreeNode, relative_path: str) -> None:
        node = root
        current_path = ""
        parts = relative_path.split("/")
        for i, part in enumerate(parts):
            current_path = f"{current_path}/{part}" if current_path else part
            existing = next((c for c in node.children if c.name == part), None)
            if existing is not None:
                node = existing
                continue
            left = self.left_files.get(current_path)
            right = self.right_files.get(current_path)
            is_last = i == len(parts) - 1
            is_dir = (not is_last
                      or bool(left and left.is_directory)
                      or bool(right and right.is_directory))
            child = TreeNode(part, left.path if left else None, right.path if right else None,
                             is_dir, DifferenceType.IDENTICAL, node.depth + 1, False,
                             parent=node)
            node.children.append(child)
            node = child

    def _sort(self, node: TreeNode) -> None:
        node.children.sort(key=lambda c: (not c.is_directory, c.name.lower()))
        for child in node.children:
            self._sort(child)

    def _classify(self, node: TreeNode) -> None:
        for child in node.children:
            self._classify(child)
        node.difference_type = self.classify_node(node)

    def classify_node(self, node: TreeNode) -> DifferenceType:
        if node.depth > 0:
            exists_left = node.left_path is not None
            exists_right = node.right_path is not None
            if exists_left and not exists_right:
                return DifferenceType.ONLY_LEFT
            if exists_right and not exists_left:
                return DifferenceType.ONLY_RIGHT
            if not node.is_directory:
                if not self.compare_content:
                    return DifferenceType.PENDING
                return (DifferenceType.IDENTICAL
                        if self.compare_file_content(node.left_path, node.right_path)
                        else DifferenceType.CONTENT_DIFFERENT)
        return summarize_directory(node)

    @staticmethod
    def compare_file_content(left_path: Path, right_path: Path) -> bool:
        """Byte-equality of two files (size check first, then 8 KB chunks)."""
        try:
            if left_path.stat().st_size != right_path.stat().st_size:
                return False
            with left_path.open("rb") as lf, right_path.open("rb") as rf:
                while True:
                    lc, rc = lf.read(8192), rf.read(8192)
                    if lc != rc:
                        return False
                    if not lc:
                        return True
        except (OSError, IOError, PermissionError):
            return False


def summarize_directory(node: TreeNode) -> DifferenceType:
    """A directory's (or the root's) verdict from its children: any real
    difference → contains-difference; else any pending child → pending; else
    identical."""
    has_difference = has_pending = False
    for child in node.children:
        if child.difference_type == DifferenceType.PENDING:
            has_pending = True
        elif child.difference_type != DifferenceType.IDENTICAL:
            has_difference = True
            break
    if has_difference:
        return DifferenceType.CONTAINS_DIFFERENCE
    if not has_pending:
        return DifferenceType.IDENTICAL
    return DifferenceType.PENDING


def reclassify_directories(node: TreeNode) -> None:
    """Post-order re-summarise every two-sided directory (and the root) from its
    children's current verdicts, leaving file and one-sided nodes untouched.
    Used after the comparison phase resolves file verdicts, so ancestor
    directories flip PENDING → identical / contains-difference."""
    for child in node.children:
        reclassify_directories(child)
    if node.is_directory:
        two_sided = node.left_path is not None and node.right_path is not None
        if node.depth == 0 or two_sided:
            node.difference_type = summarize_directory(node)


def _recursive_delete(entry: Path) -> None:
    """Delete a file or directory through the storage-agnostic Path API,
    recursing into directories (mirrors ``tfm.TfmApp._delete_path``)."""
    if entry.is_dir() and not entry.is_symlink():
        for child in entry.iterdir():
            _recursive_delete(child)
        entry.rmdir()
    else:
        entry.unlink()


# --- rendering / interaction (PuiKit widget) ---------------------------------

#: Foreground for a node that differs (only-one-side / content-different).
_DIFF_FG = (222, 120, 110)
#: Faint fill for the blank side of an only-left / only-right row.
_EMPTY_BG = (32, 32, 34)
#: Horizontal base units reserved per tree depth level (the connector column).
_INDENT = 2


class DirectoryDiffView(Widget):
    """Full-window modal recursive directory diff. Construct via
    :func:`show_directory_diff_viewer`."""

    focusable = True

    _MOUSE = frozenset({
        EventType.MOUSE_DOWN, EventType.MOUSE_UP,
        EventType.MOUSE_CLICK, EventType.MOUSE_DRAG,
    })

    def __init__(self, left_path: Path, right_path: Path, show_hidden: bool = True,
                 background: bool = True):
        self.left_path = left_path
        self.right_path = right_path
        self.show_hidden = show_hidden
        self._panel: Any = None
        # An empty tree until the worker's first build; navigation state.
        self.root = TreeNode("", None, None, True, DifferenceType.PENDING, 0, True)
        self.visible: list[TreeNode] = []
        self.cursor = 0
        self.top = 0.0
        self.active = "left"
        self._view_h = 1
        self._body_widget: Optional[_ScrollBody] = None
        # Nested modals (confirm boxes, the per-file diff) must sit *above* this
        # full-window layer; show_directory_diff_viewer raises it to (push z + 10).
        self._child_z = 90
        # Progressive-scan state shared with the worker thread. ``_lock`` guards
        # tree mutation + reflow; ``visible`` is swapped atomically so draw reads
        # it lock-free. ``_dirty`` requests a main-thread re-render.
        self._lock = threading.RLock()
        self._dirty = True
        self._scanning = True
        self._cancel = False
        self._scanners: list[DirectoryScanner] = []
        self._phase = "scan"
        self._scanned = 0
        self._compared = 0
        self._compare_total = 0
        self._thread: Optional[threading.Thread] = None
        # A rescan (after copy/delete) restores expansion + cursor across the
        # freshly built tree instead of auto-expanding from scratch.
        self._restore_expanded: Optional[set[str]] = None
        self._restore_cursor_path: Optional[str] = None
        if background:
            self._thread = threading.Thread(target=self._scan_worker, daemon=True)
            self._thread.start()
        else:
            self._scan_worker()

    # --- background scanning -------------------------------------------------

    def _scan_worker(self) -> None:
        """Walk both trees (metadata), build the deferred-comparison tree, then
        compare each candidate file's content, refreshing the view as it goes."""
        try:
            left_scanner = DirectoryScanner(self.show_hidden)
            right_scanner = DirectoryScanner(self.show_hidden)
            self._scanners = [left_scanner, right_scanner]

            def on_scan(count: int) -> None:
                self._scanned += 50
                self._dirty = True

            self._phase = "scan"
            left_files = left_scanner.scan(self.left_path, on_scan)
            if self._cancel:
                return
            right_files = right_scanner.scan(self.right_path, on_scan)
            if self._cancel:
                return

            root = DiffEngine(left_files, right_files, compare_content=False).build_tree()
            with self._lock:
                self.root = root
                if self._restore_expanded is not None:
                    self._restore_expansion(self._restore_expanded)
                    self._restore_expanded = None
                else:
                    self._auto_expand(self.root)
                self._reflow_locked()
                if self._restore_cursor_path is not None:
                    self._restore_cursor(self._restore_cursor_path)
                    self._restore_cursor_path = None
                self._dirty = True

            # Comparison phase: resolve every two-sided file's content verdict,
            # periodically re-summarising ancestors and refreshing the view.
            self._phase = "compare"
            pending = [n for n in self._iter_nodes(root)
                       if not n.is_directory and n.left_path is not None
                       and n.right_path is not None]
            self._compare_total = len(pending)
            last = time.monotonic()
            for i, node in enumerate(pending):
                if self._cancel:
                    return
                verdict = (DifferenceType.IDENTICAL
                           if DiffEngine.compare_file_content(node.left_path, node.right_path)
                           else DifferenceType.CONTENT_DIFFERENT)
                with self._lock:
                    node.difference_type = verdict
                    self._compared = i + 1
                    now = time.monotonic()
                    if now - last > 0.15:
                        reclassify_directories(self.root)
                        self._reflow_locked()
                        self._dirty = True
                        last = now
            with self._lock:
                reclassify_directories(self.root)
                self._reflow_locked()
        finally:
            # Set dirty *before* clearing scanning so the tick always paints the
            # final state before it unregisters (see _tick).
            with self._lock:
                self._dirty = True
                self._scanning = False

    def _tick(self) -> bool:
        """Animation-tick callback (main thread): re-render when the worker has
        flagged a change; keep ticking while the scan runs."""
        if self._cancel:
            return False
        if self._dirty:
            self._dirty = False
            if self._panel is not None:
                self._panel.render()
        return self._scanning or self._dirty

    def join(self, timeout: float = 5.0) -> None:
        """Block until the background scan finishes (tests / teardown)."""
        if self._thread is not None:
            self._thread.join(timeout)

    def cancel(self) -> None:
        self._cancel = True
        for scanner in self._scanners:
            scanner.cancel()

    def _restart_scan(self) -> None:
        """Re-run the scan after a copy/delete, preserving the expanded set and
        the focused node so the user keeps their place."""
        self._restore_expanded = self._save_expansion()
        node = self._current()
        self._restore_cursor_path = self._node_rel_path(node) if node is not None else None
        self.cancel()
        if self._thread is not None:
            self._thread.join(1.0)
        self._cancel = False
        self._scanning = True
        self._dirty = True
        self._phase = "scan"
        self._scanned = self._compared = self._compare_total = 0
        self._scanners = []
        self._thread = threading.Thread(target=self._scan_worker, daemon=True)
        self._thread.start()
        if self._panel is not None:
            self._panel.request_animation_ticks(self._tick)

    # --- tree state ----------------------------------------------------------

    def _iter_nodes(self, node: TreeNode) -> Iterator[TreeNode]:
        for child in node.children:
            yield child
            yield from self._iter_nodes(child)

    def _node_rel_path(self, node: TreeNode) -> str:
        """The node's path relative to the compared roots (``sub/a.txt``)."""
        parts: list[str] = []
        cur: Optional[TreeNode] = node
        while cur is not None and cur.depth > 0:
            parts.append(cur.name)
            cur = cur.parent
        return "/".join(reversed(parts))

    def _save_expansion(self) -> set[str]:
        expanded: set[str] = set()
        for node in self._iter_nodes(self.root):
            if node.is_directory and node.is_expanded:
                expanded.add(self._node_rel_path(node))
        return expanded

    def _restore_expansion(self, expanded: set[str]) -> None:
        for node in self._iter_nodes(self.root):
            if node.is_directory:
                node.is_expanded = self._node_rel_path(node) in expanded

    def _restore_cursor(self, rel_path: str) -> None:
        for i, node in enumerate(self.visible):
            if self._node_rel_path(node) == rel_path:
                self.cursor = i
                self._ensure_cursor_visible()
                return

    def _auto_expand(self, node: TreeNode) -> None:
        """Open directories that (may) contain a difference so diffs are visible
        as they resolve; identical/leaf branches stay collapsed."""
        for child in node.children:
            if child.is_directory and child.difference_type in (
                    _IS_DIFF | {DifferenceType.PENDING}):
                child.is_expanded = True
                self._auto_expand(child)

    def _reflow(self) -> None:
        with self._lock:
            self._reflow_locked()

    def _reflow_locked(self) -> None:
        """Rebuild the flattened visible list (call under ``_lock``); assigns
        ``visible`` atomically so a concurrent draw sees a consistent list."""
        flat: list[TreeNode] = []
        self._flatten(self.root, flat)
        self.visible = flat
        if self.cursor >= len(flat):
            self.cursor = max(0, len(flat) - 1)

    def _flatten(self, node: TreeNode, out: list[TreeNode]) -> None:
        if node.depth > 0:
            out.append(node)
        if node.is_expanded:
            for child in node.children:
                self._flatten(child, out)

    def _connector_chain(self, node: TreeNode) -> list[bool]:
        """One ``is_last_child`` flag per depth level from the top ancestor down
        to ``node`` (length == ``node.depth``). Drives both the box-drawing
        connectors (grid) and the drawn connector lines (vector)."""
        nodes: list[TreeNode] = []
        cur: Optional[TreeNode] = node
        while cur is not None and cur.depth > 0:
            nodes.insert(0, cur)
            cur = cur.parent
        return [n.parent.children[-1] is n for n in nodes if n.parent is not None]

    def _tree_lines(self, node: TreeNode, *, branch: bool) -> str:
        """Box-drawing prefix showing this node's place in the tree. With
        ``branch`` the node's own level gets a ├─/└─ connector; without (a node
        missing on this side) only ancestor continuation bars are drawn."""
        if node.depth == 0:
            return ""
        chain: list[TreeNode] = []
        cur: Optional[TreeNode] = node
        while cur is not None and cur.parent is not None and cur.parent.depth >= 0:
            chain.insert(0, cur)
            cur = cur.parent
            if cur.depth == 0:
                break
        out = []
        for i, anc in enumerate(chain):
            parent = anc.parent
            if parent is None:
                continue
            is_last = parent.children[-1] is anc
            if i == len(chain) - 1:
                out.append(("└─" if is_last else "├─") if branch else ("  " if is_last else "│ "))
            else:
                out.append("  " if is_last else "│ ")
        return "".join(out)

    # --- navigation ----------------------------------------------------------

    def _clamp_scroll(self) -> None:
        self.top = max(0.0, min(self.top, float(max(0, len(self.visible) - self._view_h))))

    def _ensure_cursor_visible(self) -> None:
        top = int(self.top)
        if self.cursor < top:
            self.top = float(self.cursor)
        elif self.cursor >= top + self._view_h:
            self.top = float(self.cursor - self._view_h + 1)
        self._clamp_scroll()

    def _move_cursor(self, delta: int) -> None:
        if not self.visible:
            return
        self.cursor = max(0, min(self.cursor + delta, len(self.visible) - 1))
        self._ensure_cursor_visible()

    def _current(self) -> Optional[TreeNode]:
        if 0 <= self.cursor < len(self.visible):
            return self.visible[self.cursor]
        return None

    def _toggle(self, expand: Optional[bool] = None) -> None:
        """Expand/collapse the focused directory. ``expand`` forces a direction;
        None toggles. Preserves the focused node across the reflow."""
        node = self._current()
        if node is None or not node.is_directory or not node.children:
            return
        node.is_expanded = (not node.is_expanded) if expand is None else expand
        self._reflow()
        if node in self.visible:
            self.cursor = self.visible.index(node)
        self._ensure_cursor_visible()

    def _step_diff(self, delta: int) -> None:
        """Move the cursor to the next/previous node that is a difference."""
        n = len(self.visible)
        if n == 0:
            return
        for step in range(1, n + 1):
            idx = (self.cursor + delta * step) % n
            if self.visible[idx].difference_type in _IS_DIFF:
                self.cursor = idx
                self._ensure_cursor_visible()
                return

    def _open_file_diff(self) -> None:
        """Enter/`d` on a two-sided differing file opens the per-file diff."""
        node = self._current()
        if (node is not None and not node.is_directory
                and node.left_path is not None and node.right_path is not None
                and self._panel is not None):
            show_diff_viewer(self._panel, node.left_path, node.right_path, z=self._child_z)

    # --- file operations across sides ----------------------------------------

    def _active_side_path(self, node: TreeNode) -> Optional[Path]:
        return node.left_path if self.active == "left" else node.right_path

    def _opposite_root(self) -> Path:
        return self.right_path if self.active == "left" else self.left_path

    def _render(self) -> None:
        if self._panel is not None:
            self._panel.render()

    def _notify(self, message: str, title: str = "Directory Diff") -> None:
        if self._panel is not None:
            show_message_box(self._panel, message, title=title, icon="info", z=self._child_z)

    def _copy_focused(self) -> None:
        """Copy the focused node from the active side to the mirrored location on
        the opposite side (creating parent directories), then rescan."""
        node = self._current()
        if node is None or self._panel is None:
            return
        src = self._active_side_path(node)
        if src is None:
            self._notify(f"'{node.name}' does not exist on the {self.active} side.")
            return
        rel = self._node_rel_path(node)
        dest_root = self._opposite_root()
        parent = node.parent
        parent_rel = self._node_rel_path(parent) if parent is not None and parent.depth > 0 else ""
        dest_dir = (dest_root / parent_rel) if parent_rel else dest_root
        dest = dest_dir / node.name

        def result(label: str) -> None:
            if label != "Copy":
                self._render()
                return
            try:
                if not dest_dir.exists():
                    dest_dir.mkdir(parents=True, exist_ok=True)
                src.copy_to(dest, overwrite=True)
            except Exception as exc:
                self._notify(f"Copy failed: {exc}")
                return
            self._restart_scan()
            self._render()

        show_message_box(
            self._panel, f"Copy '{rel}' to the {self._other_side()} side?",
            title="Copy", icon="info", buttons=("Copy", "Cancel"),
            default=0, cancel=1, on_result=result, z=self._child_z)

    def _delete_focused(self) -> None:
        """Delete the focused node from the active side (recursively), then
        rescan. Confirmation defaults to Cancel (destructive)."""
        node = self._current()
        if node is None or self._panel is None:
            return
        path = self._active_side_path(node)
        if path is None:
            self._notify(f"'{node.name}' does not exist on the {self.active} side.")
            return
        rel = self._node_rel_path(node)

        def result(label: str) -> None:
            if label != "Delete":
                self._render()
                return
            try:
                _recursive_delete(path)
            except Exception as exc:
                self._notify(f"Delete failed: {exc}")
                return
            self._restart_scan()
            self._render()

        show_message_box(
            self._panel, f"Delete '{rel}' from the {self.active} side?",
            title="Delete", icon="warning", buttons=("Delete", "Cancel"),
            default=1, cancel=1, on_result=result, z=self._child_z)

    def _other_side(self) -> str:
        return "right" if self.active == "left" else "left"

    def _show_help(self) -> None:
        if self._panel is None:
            return
        show_message_box(
            self._panel,
            "↑/↓ · PgUp/PgDn · Home/End   move\n"
            "→ / ←                        expand / collapse\n"
            "Enter                        open dir · diff file\n"
            "n / N                        next / prev difference\n"
            "Tab                          switch active side\n"
            "c                            copy focused → other side\n"
            "x / Del                      delete focused (active side)\n"
            "r                            rescan\n"
            "q / Esc                      close",
            title="Directory Diff — Keys", icon="info", z=self._child_z)

    # --- drawing -------------------------------------------------------------

    def draw(self, ctx) -> None:
        self._panel = ctx.panel
        theme = ctx.theme
        w, h = ctx.width, ctx.height
        wu = ctx.size_units[0]
        bg = getattr(theme, "popup_bg", None) if theme is not None else None
        accent = theme.accent if theme is not None else (0, 122, 204)
        muted = theme.muted_text if theme is not None else (150, 150, 150)
        self._bg = bg
        self._text_fg = theme.text if theme is not None else (212, 212, 212)
        self._muted = muted
        self._accent = accent
        self._sel_active = getattr(theme, "selection_active_bg", accent) if theme else accent
        self._sel_inactive = getattr(theme, "selection_inactive_bg", muted) if theme else muted
        ctx.fill_rect(0, 0, wu, ctx.size_units[1], Style(bg=bg))

        # Column geometry: [left tree] [ sep ] [right tree] [scrollbar].
        reserve = 1 if self.visible else 0
        avail = max(2, w - 3 - reserve)
        right_w = avail // 2
        left_w = avail - right_w
        self._left_x = 0
        self._sep_x = left_w
        self._right_x = left_w + 3
        self._left_w = left_w
        self._right_w = right_w

        # Header: the two directory paths, active side in accent.
        head = Style(bg=bg, attr=TextAttribute.BOLD)
        left_head = Style(fg=accent if self.active == "left" else self._text_fg, bg=bg,
                          attr=TextAttribute.BOLD)
        right_head = Style(fg=accent if self.active == "right" else self._text_fg, bg=bg,
                           attr=TextAttribute.BOLD)
        ctx.draw_text(0, 0, truncate_to_width(str(self.left_path), left_w), left_head)
        ctx.draw_text(self._sep_x, 0, " │ ", head)
        ctx.draw_text(self._right_x, 0, truncate_to_width(str(self.right_path), right_w),
                      right_head)

        # Rows sit between the header (row 0) and a details row + footer at the
        # bottom two lines.
        self._view_h = max(1, h - 3)
        self._clamp_scroll()

        if not self.visible:
            self._draw_status_screen(ctx, w, h, muted, bg)
        else:
            ctx.draw_child(self._body, 0, 1, w, float(self._view_h))
            if len(self.visible) > self._view_h:
                denom = len(self.visible) - self._view_h
                ratio = self._view_h / len(self.visible)
                ctx.draw_scrollbar(wu - 1, 1, self._view_h,
                                   max(0.0, min(1.0, self.top / denom if denom else 0.0)), ratio)

        ctx.draw_text(0, h - 2, self._details_line()[:w],
                      Style(fg=self._text_fg, bg=bg))
        ctx.draw_text(0, h - 1, self._footer()[:w],
                      Style(fg=muted, bg=bg, attr=TextAttribute.DIM))

    def _draw_status_screen(self, ctx, w: int, h: int, muted, bg) -> None:
        if self._scanning:
            msg = f"Scanning… ({self._scanned} items)"
        else:
            msg = "Directories are identical — no differences found"
        ctx.draw_text(max(0, (w - len(msg)) // 2), h // 2, msg[:w], Style(fg=muted, bg=bg))

    def _footer(self) -> str:
        if self._scanning:
            if self._phase == "compare" and self._compare_total:
                return (f" Comparing {self._compared}/{self._compare_total} files… "
                        "· esc cancel ")
            return f" Scanning… ({self._scanned} items) · esc cancel "
        diffs = sum(1 for n in self.visible if n.difference_type in _IS_DIFF)
        return (f" {len(self.visible)} nodes · {diffs} differences · "
                "n/N jump · ←/→ expand · tab side · enter diff · q close ")

    def _details_line(self) -> str:
        """The focused node's size on each side (the details pane, condensed to a
        single row)."""
        node = self._current()
        if node is None:
            return ""

        def side(path: Optional[Path]) -> str:
            if path is None:
                return "—"
            try:
                if path.is_dir():
                    return "dir"
                return format_size(path.stat().st_size)
            except Exception:
                return "?"

        return f" {node.name}    L: {side(node.left_path)}    R: {side(node.right_path)}"

    @property
    def _body(self) -> _ScrollBody:
        if self._body_widget is None:
            self._body_widget = _ScrollBody(self._draw_rows)
        return self._body_widget

    def _draw_rows(self, ctx) -> None:
        rows = self.visible  # atomic snapshot (worker swaps the list wholesale)
        first = int(self.top)
        vfrac = self.top - first
        for vis in range(self._view_h + 1):
            ri = first + vis
            if ri >= len(rows):
                break
            self._draw_row(ctx, rows[ri], vis - vfrac, ri == self.cursor)

    def _draw_row(self, ctx, node: TreeNode, y: float, focused: bool) -> None:
        bg = self._bg
        verdict = node.difference_type
        is_diff = verdict in _IS_DIFF
        base_fg = _DIFF_FG if is_diff else self._text_fg
        # A directory that contains a difference reads as accent, not red.
        if verdict == DifferenceType.CONTAINS_DIFFERENCE:
            base_fg = self._accent
        # A pending file/dir is dimmed until its verdict resolves.
        pending = verdict == DifferenceType.PENDING
        suffix = " …" if (pending and not node.is_directory) else ""
        vector = ctx.vector_shapes
        flags = self._connector_chain(node)

        def side(x: int, col_w: int, path, is_active: bool) -> None:
            row_bg = bg
            fg = self._muted if pending else base_fg
            if focused:
                row_bg = self._sel_active if is_active else self._sel_inactive
                fg = (255, 255, 255)
                ctx.fill_rect(x, y, col_w, 1.0, Style(bg=row_bg))
            elif path is None:
                ctx.fill_rect(x, y, col_w, 1.0, Style(bg=_EMPTY_BG))
            if vector:
                self._draw_side_vector(ctx, x, col_w, node, flags, path, y,
                                       fg, row_bg, suffix)
            else:
                self._draw_side_grid(ctx, x, col_w, node, path, y, fg, row_bg, suffix)

        side(self._left_x, self._left_w, node.left_path, self.active == "left")
        sep = _SEPARATOR.get(verdict, " ! ")
        sep_fg = _DIFF_FG if is_diff else self._muted
        ctx.draw_text(self._sep_x, y, sep,
                      Style(fg=sep_fg, bg=bg, attr=TextAttribute.BOLD, font=MONO))
        side(self._right_x, self._right_w, node.right_path, self.active == "right")

    def _draw_side_grid(self, ctx, x, col_w, node, path, y, fg, row_bg, suffix) -> None:
        """Terminal / character-grid tree column: box-drawing connectors in the
        cell grid (monospace, so ├ └ │ align and column-count truncation is
        exact)."""
        if path is None:
            lines = self._tree_lines(node, branch=False)
            if lines:
                ctx.draw_text(x, y, lines[:col_w], Style(fg=self._muted, bg=row_bg, font=MONO))
            return
        lines = self._tree_lines(node, branch=True)
        marker = ("▾ " if node.is_expanded else "▸ ") if node.is_directory else ""
        label = lines + marker + node.name + ("/" if node.is_directory else "") + suffix
        ctx.draw_text(x, y, truncate_to_width(label, col_w), Style(fg=fg, bg=row_bg, font=MONO))
        if lines:  # redraw the tree lines muted over the label's start
            ctx.draw_text(x, y, lines[:col_w], Style(fg=self._muted, bg=row_bg, font=MONO))

    def _draw_side_vector(self, ctx, x, col_w, node, flags, path, y,
                          fg, row_bg, suffix) -> None:
        """GUI / pixel tree column: connectors drawn as thin lines (aligned to a
        base-unit grid regardless of the proportional font) with the name in the
        proportional UI font, indented a fixed distance per depth and elided to
        the column by measured width."""
        depth = len(flags)
        line_style = Style(bg=self._muted)
        lw = 1.0 / max(1, ctx.base_size[0])   # ~1 device-pixel vertical stroke
        lh = 1.0 / max(1, ctx.base_size[1])   # ~1 device-pixel horizontal stroke
        mid = y + 0.5
        label_x = x + depth * _INDENT
        for i, is_last in enumerate(flags):
            cx = x + i * _INDENT + 0.5
            if i < depth - 1:
                if not is_last:  # ancestor with siblings below → continuation bar
                    ctx.fill_rect(cx, y, lw, 1.0, line_style)
            elif path is not None:
                # The node's own level: a stem from the top to the middle (full
                # height when it has siblings below), plus an elbow to the label.
                ctx.fill_rect(cx, y, lw, 1.0 if not is_last else 0.5, line_style)
                ctx.fill_rect(cx, mid, max(0.0, label_x - cx), lh, line_style)
            elif not is_last:
                # Missing on this side: only the continuation bar, no elbow.
                ctx.fill_rect(cx, y, lw, 1.0, line_style)
        if path is None:
            return
        marker = ("▾ " if node.is_expanded else "▸ ") if node.is_directory else ""
        label = marker + node.name + ("/" if node.is_directory else "") + suffix
        avail = col_w - depth * _INDENT
        if avail > 0:
            ctx.draw_text(label_x, y, elide(label, float(avail), measure=ctx.measure_text),
                          Style(fg=fg, bg=row_bg))

    # --- events --------------------------------------------------------------

    def _close(self) -> None:
        self.cancel()
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.MOUSE_SCROLL:
            uy = event.hints.get("scroll_units")
            self.top -= float(uy) if uy is not None else float(event.scroll)
            self._clamp_scroll()
            return True
        if event.type in self._MOUSE:
            return True  # slice 4: click-to-focus row; display-only for now
        if event.type is not EventType.KEY:
            return True
        key = event.key
        char = event.char
        if key in ("escape", "q") or char == "q":
            self._close()
        elif key == "down":
            self._move_cursor(1)
        elif key == "up":
            self._move_cursor(-1)
        elif key == "pagedown":
            self._move_cursor(self._view_h)
        elif key == "pageup":
            self._move_cursor(-self._view_h)
        elif key == "home":
            self.cursor = 0
            self._ensure_cursor_visible()
        elif key == "end":
            self.cursor = max(0, len(self.visible) - 1)
            self._ensure_cursor_visible()
        elif key == "right":
            self._toggle(expand=True)
        elif key == "left":
            node = self._current()
            if node is not None and node.is_directory and node.is_expanded:
                self._toggle(expand=False)
            elif node is not None and node.parent is not None and node.parent.depth > 0:
                if node.parent in self.visible:
                    self.cursor = self.visible.index(node.parent)
                    self._ensure_cursor_visible()
        elif key in ("enter", "return"):
            node = self._current()
            if node is not None and node.is_directory:
                self._toggle()
            else:
                self._open_file_diff()
        elif key == "tab":
            self.active = "right" if self.active == "left" else "left"
        elif char == "n":
            self._step_diff(1)
        elif char == "N":
            self._step_diff(-1)
        elif char == "d":
            self._open_file_diff()
        elif char == "c":
            self._copy_focused()
        elif char == "x" or key == "delete":
            self._delete_focused()
        elif char == "r":
            self._restart_scan()
        elif char == "?":
            self._show_help()
        return True


def show_directory_diff_viewer(panel: Any, left_path: Path, right_path: Path,
                               show_hidden: bool = True, background: bool = True,
                               z: int = 80) -> DirectoryDiffView:
    """Push a full-window modal :class:`DirectoryDiffView` for two directories.

    Scanning runs in the background and repaints live via an animation tick (see
    the module docstring). On a still backend without animation ticks the tick
    simply never fires; the tree still fills in and repaints on the next user
    event."""
    viewer = DirectoryDiffView(left_path, right_path, show_hidden=show_hidden,
                               background=background)
    viewer._child_z = z + 10
    sw, sh = panel.backend.size_units
    viewer._panel = panel
    panel.push_layer(viewer, z=z, hints={"x": 0, "y": 0, "w": sw, "h": sh},
                     reflow=lambda sw, sh: Rect(0, 0, sw, sh))
    panel.request_animation_ticks(viewer._tick)
    panel.animate(viewer, hints={"transition": "fade", "duration_ms": 120})
    return viewer
