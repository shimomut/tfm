"""DirectoryDiffView — recursive side-by-side directory diff for the PuiKit port.

Compares two directories recursively and shows the union of their trees side by
side, each
node classified (only-left, only-right, content-different, contains-difference,
identical) with a centre separator glyph carrying the verdict. Directories
expand/collapse; ``n``/``N`` jump between differences; Enter on a differing file
opens the per-file diff (reusing :func:`tfm_diff_viewer.show_diff_viewer`).

Scanning is **progressive** and breadth-first: on open the viewer scans only the
top level of both roots (so items appear at once), then a background *scanner*
worker pulls directories off a queue level-by-level, inserting nodes into the
shared tree as they're discovered — the tree grows live, top-down. A decoupled
*comparator* worker resolves each two-sided file's content verdict off its own
queue. Both queues are priority queues so **visible / expanded** directories are
scanned first (re-prioritised on scroll / expand / collapse). Tree mutation
happens under a lock and raises a dirty flag; a per-frame tick registered via
``panel.request_animation_ticks`` runs on the main thread and re-renders when the
flag is set, so nothing blocks the UI. Pass ``background=False`` (tests) to scan
synchronously (full walk + one-shot classification).

This module keeps the backend-agnostic scanning/classification logic and renders
via a :class:`~puikit.widgets.base.Widget`, following the
:mod:`tfm_diff_viewer` pattern. Push it with :func:`show_directory_diff_viewer`.
"""

from __future__ import annotations

import itertools
import queue
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
    #: Progressive-scan bookkeeping (background mode). ``children_scanned`` guards
    #: against a directory being scanned twice; ``_hi_pri`` against re-enqueuing
    #: an already-prioritised directory on every scroll.
    children_scanned: bool = False
    content_compared: bool = False
    _hi_pri: bool = False


#: Scan-task priorities (higher = pulled off the queue first).
_PRIO_IMMEDIATE = 1000  # user just expanded this directory
_PRIO_VISIBLE = 100     # currently in the viewport
_PRIO_NORMAL = 10       # discovered but off-screen


# --- scanning / classification (backend-agnostic) ---------------------------


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

    def scan_level(self, directory: Path) -> dict[str, FileInfo]:
        """List only the *immediate* children of ``directory`` (non-recursive),
        keyed by bare filename. Powers the progressive breadth-first scan: each
        level is scanned on demand so the tree can grow top-down without a full
        upfront walk. Inaccessible entries are recorded, not raised."""
        files: dict[str, FileInfo] = {}
        try:
            children = list(directory.iterdir())
        except (OSError, PermissionError):
            return files
        for child in children:
            name = child.name
            if not self.show_hidden and name.startswith("."):
                continue
            try:
                st = child.stat()
                is_dir = child.is_dir()
                files[name] = FileInfo(child, name, is_dir,
                                       0 if is_dir else st.st_size, st.st_mtime, True)
            except (OSError, PermissionError) as exc:
                files[name] = FileInfo(child, name, False, 0, 0.0, False, str(exc))
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
#: Horizontal base units reserved per tree depth level (the connector column).
_INDENT = 2
#: Minimum width (base units) either pane may be shrunk to by the split drag.
_MIN_PANE = 8
#: Width (base units) of the centre gutter / splitter band holding the verdict
#: glyphs. Wide enough to read as a bar, not a hairline.
_GUTTER_W = 3
#: Max seconds between two clicks on the same row to count as a double-click.
_DOUBLE_CLICK_S = 0.4


def _mix(a: tuple, b: tuple, t: float) -> tuple:
    """Linear blend of two RGB colors, ``t`` in [0, 1] toward ``b``."""
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


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
        # Movable centre split: fraction of the content width given to the left
        # pane. Draggable by the gutter; nudged by ``[`` / ``]``.
        self._split_ratio = 0.5
        self._resizable = False       # set each draw once geometry is known
        self._dragging_split = False
        self._drag_offset = 0.0       # pointer offset within the grabbed band
        self._avail = 2               # content width (excludes gutter/scrollbar)
        # Double-click bookkeeping (no backend click-count; detect by time+row).
        self._last_click_row = -1
        self._last_click_t = 0.0
        # Nested modals (confirm boxes, the per-file diff) must sit *above* this
        # full-window layer; show_directory_diff_viewer raises it to (push z + 10).
        self._child_z = 90
        # Progressive-scan state shared with the worker threads. ``_lock`` guards
        # all tree mutation + reflow; ``visible`` is swapped atomically so draw
        # reads it lock-free. ``_dirty`` requests a main-thread re-render.
        self._lock = threading.RLock()
        self._dirty = True
        self._scanning = True
        self._cancel = False
        self._scanners: list[DirectoryScanner] = []
        self._phase = "scan"
        # Breadth-first directory-scan queue and decoupled file-comparison queue.
        # Both are priority queues holding ``(-priority, seq, node)`` — the seq
        # keeps items unique so ``TreeNode``s are never compared, and negating the
        # priority turns the min-heap into "highest priority first".
        self._scan_q: queue.PriorityQueue = queue.PriorityQueue()
        self._cmp_q: queue.PriorityQueue = queue.PriorityQueue()
        self._seq = itertools.count()
        # Progress counters surfaced in the footer / status screen.
        self._scanned = 0        # files + dirs discovered
        self._dirs_scanned = 0   # directories whose level has been listed
        self._dirs_total = 0     # directories queued for scanning
        self._compared = 0
        self._compare_total = 0
        self._thread: Optional[threading.Thread] = None  # the coordinator
        self._workers: list[threading.Thread] = []       # scanner + comparator
        # A rescan (after copy/delete) restores the prior expansion + cursor
        # across the freshly built tree so the user keeps their place.
        self._restore_expanded: Optional[set[str]] = None
        self._restore_cursor_path: Optional[str] = None
        if background:
            self._thread = threading.Thread(target=self._scan_coordinator, daemon=True)
            self._thread.start()
        else:
            self._scan_sync()

    # --- synchronous scan (tests) --------------------------------------------

    def _scan_sync(self) -> None:
        """Full recursive walk + one-shot classification, for ``background=False``
        (deterministic tests). Converges to the same finished tree the background
        workers produce, then finalises (restore on rescan; else collapsed)."""
        left_scanner = DirectoryScanner(self.show_hidden)
        right_scanner = DirectoryScanner(self.show_hidden)
        self._scanners = [left_scanner, right_scanner]
        left_files = left_scanner.scan(self.left_path)
        right_files = right_scanner.scan(self.right_path)
        with self._lock:
            self.root = DiffEngine(left_files, right_files, compare_content=True).build_tree()
            # The tree is fully built, so no branch needs an on-expand lazy scan.
            self.root.children_scanned = True
            for node in self._iter_nodes(self.root):
                if node.is_directory:
                    node.children_scanned = True
            self._scanned = len(left_files) + len(right_files)
            self._compared = self._compare_total = sum(
                1 for n in self._iter_nodes(self.root)
                if not n.is_directory and n.left_path is not None and n.right_path is not None)
            self._finalize_locked()
            self._dirty = True
            self._scanning = False

    # --- progressive background scanning -------------------------------------

    def _enqueue_scan(self, node: TreeNode, priority: int) -> None:
        self._scan_q.put((-priority, next(self._seq), node))

    def _enqueue_cmp(self, node: TreeNode, priority: int) -> None:
        self._cmp_q.put((-priority, next(self._seq), node))

    def _scan_coordinator(self) -> None:
        """Background driver (the joinable thread). Scans the roots' top level so
        items appear immediately, starts the scanner + comparator workers, waits
        for both queues to drain (breadth-first, visible-first), then finalises."""
        try:
            self._seed_root()
            if self._cancel:
                return
            scanner = threading.Thread(target=self._scanner_worker, daemon=True)
            comparator = threading.Thread(target=self._comparator_worker, daemon=True)
            self._workers = [scanner, comparator]
            scanner.start()
            comparator.start()
            self._scan_q.join()          # every directory level listed
            if self._cancel:
                return
            self._phase = "compare"
            self._cmp_q.join()           # every two-sided file compared
        finally:
            # Dirty *before* clearing scanning so the tick paints the final state
            # before it unregisters (see _tick).
            with self._lock:
                if not self._cancel:
                    self._finalize_locked()
                self._dirty = True
                self._scanning = False

    def _seed_root(self) -> None:
        """Build the top level of the unified tree (both roots' immediate
        children) and queue every two-sided subdirectory for background scanning."""
        left = DirectoryScanner(self.show_hidden).scan_level(self.left_path)
        right = DirectoryScanner(self.show_hidden).scan_level(self.right_path)
        with self._lock:
            self.root = TreeNode("", self.left_path, self.right_path, True,
                                 DifferenceType.PENDING, 0, True)
            self.root.children_scanned = True
            self._insert_children_locked(self.root, left, right)
            self._reflow_locked()
            self._dirty = True

    def _scanner_worker(self) -> None:
        """Pull directories off ``_scan_q`` and list one level each, enqueuing
        child directories (breadth-first) and file comparisons as it goes."""
        while self._scanning:
            try:
                _, _, node = self._scan_q.get(timeout=0.1)
            except queue.Empty:
                if self._cancel:
                    return
                continue
            try:
                if not self._cancel:
                    self._scan_node(node)
            finally:
                self._scan_q.task_done()

    def _scan_node(self, node: TreeNode) -> None:
        with self._lock:
            if node.children_scanned or self._cancel:
                return
            node.children_scanned = True      # claim it so duplicates skip
            left_root, right_root = node.left_path, node.right_path
        left = DirectoryScanner(self.show_hidden).scan_level(left_root) if left_root else {}
        right = DirectoryScanner(self.show_hidden).scan_level(right_root) if right_root else {}
        with self._lock:
            if self._cancel:
                return
            self._insert_children_locked(node, left, right)
            self._dirs_scanned += 1
            # Reflow only if this directory's new children are actually on screen.
            if node.is_expanded and self._rendered_locked(node):
                self._reflow_locked()
            self._dirty = True

    def _comparator_worker(self) -> None:
        """Resolve two-sided files' content verdicts off ``_cmp_q``, decoupled
        from directory scanning so neither blocks the other."""
        while self._scanning:
            try:
                _, _, node = self._cmp_q.get(timeout=0.1)
            except queue.Empty:
                if self._cancel:
                    return
                continue
            try:
                if not self._cancel:
                    self._compare_node(node)
            finally:
                self._cmp_q.task_done()

    def _compare_node(self, node: TreeNode) -> None:
        if node.left_path is None or node.right_path is None:
            return
        identical = DiffEngine.compare_file_content(node.left_path, node.right_path)
        with self._lock:
            if self._cancel:
                return
            node.difference_type = (DifferenceType.IDENTICAL if identical
                                    else DifferenceType.CONTENT_DIFFERENT)
            node.content_compared = True
            self._compared += 1
            self._reclassify_ancestors_locked(node)
            self._dirty = True

    # --- incremental tree mutation (call under _lock) ------------------------

    def _insert_children_locked(self, parent: TreeNode,
                                left: dict[str, FileInfo],
                                right: dict[str, FileInfo]) -> None:
        """Merge a freshly scanned level into ``parent``: create/attach new child
        nodes, classify them (queuing follow-up scans/comparisons), re-sort, and
        re-summarise the ancestor chain."""
        existing = {c.name: c for c in parent.children}
        for name in set(left) | set(right):
            li, ri = left.get(name), right.get(name)
            child = existing.get(name)
            if child is not None:
                if li is not None:
                    child.left_path = li.path
                if ri is not None:
                    child.right_path = ri.path
                continue
            is_dir = bool((li and li.is_directory) or (ri and ri.is_directory))
            child = TreeNode(name, li.path if li else None, ri.path if ri else None,
                             is_dir, DifferenceType.PENDING, parent.depth + 1, False,
                             parent=parent)
            parent.children.append(child)
            self._classify_new_locked(child)
        parent.children.sort(key=lambda c: (not c.is_directory, c.name.lower()))
        self._scanned += len(left) + len(right)
        # Re-summarise the scanned directory itself (an empty two-sided directory
        # has no children to trigger a later reclassify, so resolve it now) and
        # its ancestors.
        self._reclassify_self_and_ancestors_locked(parent)

    def _classify_new_locked(self, node: TreeNode) -> None:
        """Assign a newly created node's initial verdict and queue any follow-up
        work: two-sided directories go on the scan queue, two-sided files on the
        comparison queue; one-sided nodes are already fully classified."""
        left = node.left_path is not None
        right = node.right_path is not None
        if left and not right:
            node.difference_type = DifferenceType.ONLY_LEFT
        elif right and not left:
            node.difference_type = DifferenceType.ONLY_RIGHT
        elif node.is_directory:
            node.difference_type = DifferenceType.PENDING
            self._dirs_total += 1
            self._enqueue_scan(node, _PRIO_NORMAL)
        else:
            node.difference_type = DifferenceType.PENDING
            self._compare_total += 1
            self._enqueue_cmp(node, _PRIO_NORMAL)

    def _reclassify_ancestors_locked(self, node: TreeNode) -> None:
        """Re-summarise every two-sided directory (and the root) strictly *above*
        ``node``, so PENDING ancestors flip to identical / contains-difference as
        leaves resolve."""
        self._resummarize_chain_locked(node.parent)

    def _reclassify_self_and_ancestors_locked(self, node: TreeNode) -> None:
        """Like :meth:`_reclassify_ancestors_locked` but starting at ``node``
        itself (used after scanning a directory's level)."""
        self._resummarize_chain_locked(node)

    @staticmethod
    def _resummarize_chain_locked(node: Optional[TreeNode]) -> None:
        while node is not None:
            two_sided = node.left_path is not None and node.right_path is not None
            if node.depth == 0 or two_sided:
                node.difference_type = summarize_directory(node)
            node = node.parent

    def _rendered_locked(self, node: TreeNode) -> bool:
        """True if every ancestor of ``node`` is expanded (so ``node`` and its
        children currently contribute to the flattened ``visible`` list)."""
        cur = node.parent
        while cur is not None and cur.depth > 0:
            if not cur.is_expanded:
                return False
            cur = cur.parent
        return True

    def _finalize_locked(self) -> None:
        """One-shot tree finish (both scan paths). Directories stay collapsed —
        only the root is open (ttk parity: the user drills down themselves). A
        rescan restores the pre-rescan expansion + cursor so the user keeps their
        place across a copy/delete."""
        if self._restore_expanded is not None:
            self._restore_expansion(self._restore_expanded)
            self._restore_expanded = None
        self._reflow_locked()
        if self._restore_cursor_path is not None:
            self._restore_cursor(self._restore_cursor_path)
            self._restore_cursor_path = None

    def _lazy_scan(self, node: TreeNode) -> None:
        """Scan a directory's single level on the main thread (used when the
        background pass has already finished — one-sided branches are scanned
        on demand as the user drills into them)."""
        left = (DirectoryScanner(self.show_hidden).scan_level(node.left_path)
                if node.left_path else {})
        right = (DirectoryScanner(self.show_hidden).scan_level(node.right_path)
                 if node.right_path else {})
        with self._lock:
            node.children_scanned = True
            self._insert_children_locked(node, left, right)

    def _update_priorities(self) -> None:
        """Re-enqueue viewport directories at higher priority so what the user is
        looking at fills in first (called on scroll / expand / collapse). The
        scanner dedups via ``children_scanned``; ``_hi_pri`` bounds re-enqueues to
        one per node."""
        if not self._scanning:
            return
        first = int(self.top)
        for node in self.visible[first:first + self._view_h]:
            # Two-sided directories only — they're already queued (at NORMAL), so
            # this just bumps the on-screen ones ahead. One-sided branches stay
            # lazy (scanned on expand), so touching them here would skew progress.
            if (node.is_directory and not node.children_scanned and not node._hi_pri
                    and node.left_path is not None and node.right_path is not None):
                node._hi_pri = True
                self._enqueue_scan(node, _PRIO_VISIBLE)

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
        # Tear the old coordinator + workers down before swapping in fresh queues
        # (the workers read ``self._scan_q`` each loop, so they must be stopped).
        self.cancel()
        if self._thread is not None:
            self._thread.join(1.0)
        for worker in self._workers:
            worker.join(1.0)
        self._cancel = False
        self._scanning = True
        self._dirty = True
        self._phase = "scan"
        self._scan_q = queue.PriorityQueue()
        self._cmp_q = queue.PriorityQueue()
        self._scanned = self._dirs_scanned = self._dirs_total = 0
        self._compared = self._compare_total = 0
        self._scanners = []
        self._workers = []
        self._thread = threading.Thread(target=self._scan_coordinator, daemon=True)
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
        if node is None or not node.is_directory:
            return
        node.is_expanded = (not node.is_expanded) if expand is None else expand
        # Expanding a not-yet-scanned directory (a one-sided branch, or one still
        # queued): pull it in now. During the background pass a scanner worker
        # handles it at top priority; once idle, scan the single level inline.
        if node.is_expanded and not node.children_scanned:
            if self._scanning:
                self._dirs_total += 1
                self._enqueue_scan(node, _PRIO_IMMEDIATE)
            else:
                self._lazy_scan(node)
        self._reflow()
        if node in self.visible:
            self.cursor = self.visible.index(node)
        self._ensure_cursor_visible()
        self._update_priorities()

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
            "[ / ]                        move centre split (drag gutter too)\n"
            "Click / double-click         focus side · open dir/diff\n"
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
        wu, hu = ctx.size_units  # exact (sub-cell) extent — anchor chrome to it
        # Number of whole rows (row count / scroll math), but the *bottom* chrome
        # is anchored to ``hu`` so the footer sits flush with the pixel edge
        # instead of floating a fractional row above it (grid-snap gap).
        foot_y = hu - 1          # footer line, flush to the bottom
        det_y = hu - 2           # details line, just above it
        body_h = hu - 3          # header (1) + body + details + footer (2)
        accent = theme.accent if theme is not None else (0, 122, 204)
        muted = theme.muted_text if theme is not None else (150, 150, 150)
        # Surfaces: chrome (header/footer) sits on the lighter popup surface; the
        # content body sits on the app's darker editor surface (so the viewer
        # reads as part of TFM, not a floating menu). The gutter spine is a small
        # lift off the content so the centre split is visible on its own.
        text_fg = theme.text if theme is not None else (212, 212, 212)
        chrome_bg = getattr(theme, "popup_bg", None) if theme is not None else (37, 37, 38)
        content_bg = (30, 30, 38)
        if theme is not None and getattr(theme, "surfaces", None):
            content_bg = theme.surfaces.get("content", content_bg)
        self._chrome_bg = chrome_bg
        self._bg = content_bg
        self._gutter_bg = _mix(content_bg, text_fg, 0.14)
        self._empty_bg = _mix(content_bg, (0, 0, 0), 0.4)
        self._divider = getattr(theme, "divider_color", muted) if theme else muted
        bg = content_bg
        self._text_fg = text_fg
        self._muted = muted
        self._accent = accent
        self._sel_active = getattr(theme, "selection_active_bg", accent) if theme else accent
        self._sel_inactive = getattr(theme, "selection_inactive_bg", muted) if theme else muted
        # Content fills the whole widget; the chrome bars are painted over it.
        ctx.fill_rect(0, 0, wu, hu, Style(bg=content_bg))
        ctx.fill_rect(0, 0, wu, 1.0, Style(bg=chrome_bg))            # header bar
        ctx.fill_rect(0, det_y, wu, hu - det_y, Style(bg=chrome_bg))  # footer bars

        # Column geometry: [left tree] [ gutter ] [right tree] [scrollbar]. The
        # split is user-movable and *pixel-smooth* — the split position is a
        # fractional base-unit x (not a whole cell), so a GUI drag glides rather
        # than snapping column-by-column. Clamped so neither pane collapses;
        # too-narrow windows fall back to an even split.
        reserve = 1 if self.visible else 0
        # Width is measured in the exact sub-cell extent (``wu``), so the split,
        # the right pane, and the scrollbar reach the pixel edge instead of
        # snapping to whole columns.
        avail = max(2.0, wu - _GUTTER_W - reserve)
        self._avail = avail
        if avail >= 2 * _MIN_PANE:
            split_x = avail * self._split_ratio
            split_x = max(float(_MIN_PANE), min(avail - _MIN_PANE, split_x))
            self._resizable = True
        else:
            split_x = avail / 2
            self._resizable = False
        self._left_x = 0.0
        self._sep_x = split_x
        self._right_x = split_x + _GUTTER_W
        self._left_w = split_x
        self._right_w = avail - split_x

        # Rows sit between the header (row 0) and a details row + footer at the
        # bottom two lines.
        self._view_h = max(1, h - 3)

        # The splitter: a full-height band (header top → footer top, so it never
        # leaves a gap below the last row) in its own tone. This *is* the divider
        # — no separate hairline — and it's several pixels wide, not a stroke.
        ctx.fill_rect(self._sep_x, 0, float(_GUTTER_W), det_y, Style(bg=self._gutter_bg))

        # Header: the two directory paths, active side in accent, on the chrome bar.
        left_head = Style(fg=accent if self.active == "left" else self._text_fg, bg=chrome_bg,
                          attr=TextAttribute.BOLD)
        right_head = Style(fg=accent if self.active == "right" else self._text_fg, bg=chrome_bg,
                           attr=TextAttribute.BOLD)
        ctx.draw_text(0, 0, truncate_to_width(str(self.left_path), int(self._left_w)), left_head)
        ctx.draw_text(self._right_x, 0,
                      truncate_to_width(str(self.right_path), int(self._right_w)), right_head)

        self._clamp_scroll()

        if not self.visible:
            self._draw_status_screen(ctx, w, h, muted, bg)
        else:
            # The body clips to the exact fractional height, so the last row is a
            # partial sliver that reaches the footer — no whole-cell gap above it.
            ctx.draw_child(self._body, 0, 1, wu, body_h)
            if len(self.visible) > self._view_h:
                denom = len(self.visible) - self._view_h
                # Thumb size from the *fractional* visible height, so it reflects
                # the real viewport, not a whole-row-snapped count.
                ratio = min(1.0, body_h / len(self.visible))
                ctx.draw_scrollbar(wu - 1, 1, body_h,
                                   max(0.0, min(1.0, self.top / denom if denom else 0.0)), ratio)

        ctx.draw_text(0, det_y, self._details_line()[:w],
                      Style(fg=self._text_fg, bg=chrome_bg))
        ctx.draw_text(0, foot_y, self._footer()[:w],
                      Style(fg=muted, bg=chrome_bg, attr=TextAttribute.DIM))
        self._update_cursor(ctx, hu)

    def _update_cursor(self, ctx, h: int) -> None:
        """Claim the pointer shape every frame. This is a full-window modal, so
        without an explicit request the resize cursor of a widget *underneath*
        (the app's pane Splitter) leaks through at its fixed centre. We show
        ``col-resize`` only over our own gutter (or mid-drag) and reset to the
        default everywhere else — always overriding whatever drew below."""
        over = self._dragging_split
        if not over and self._resizable:
            panel = getattr(ctx, "panel", None)
            p = panel.pointer if panel is not None else None
            if p is not None:
                sx, sy, _sw, _sh = ctx.screen_rect
                lx, ly = p[0] - sx, p[1] - sy
                over = self._sep_x <= lx < self._right_x and 0 <= ly < h - 2
        ctx.set_cursor("col-resize" if over else None)

    def _draw_status_screen(self, ctx, w: int, h: int, muted, bg) -> None:
        if self._scanning:
            msg = f"Scanning… ({self._scanned} items)"
        else:
            msg = "Directories are identical — no differences found"
        ctx.draw_text(max(0, (w - len(msg)) // 2), h // 2, msg[:w], Style(fg=muted, bg=bg))

    @staticmethod
    def _pct(done: int, total: int) -> int:
        return int(100 * done / total) if total else 100

    def _footer(self) -> str:
        if self._scanning:
            if self._phase == "compare" and self._compare_total:
                queued = self._cmp_q.qsize()
                return (f" Comparing {self._compared}/{self._compare_total} "
                        f"({self._pct(self._compared, self._compare_total)}%) · "
                        f"{queued} queued · esc cancel ")
            queued = self._scan_q.qsize()
            return (f" Scanning… {self._scanned} items · dirs "
                    f"{self._dirs_scanned}/{self._dirs_total} "
                    f"({self._pct(self._dirs_scanned, self._dirs_total)}%) · "
                    f"{queued} queued · esc cancel ")
        diffs = sum(1 for n in self.visible if n.difference_type in _IS_DIFF)
        return (f" {len(self.visible)} nodes · {diffs} differences · "
                "n/N jump · ←/→ expand · [ ] resize · tab side · enter diff · q close ")

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
                ctx.fill_rect(x, y, col_w, 1.0, Style(bg=self._empty_bg))
            if vector:
                self._draw_side_vector(ctx, x, col_w, node, flags, path, y,
                                       fg, row_bg, suffix)
            else:
                self._draw_side_grid(ctx, x, col_w, node, path, y, fg, row_bg, suffix)

        side(self._left_x, self._left_w, node.left_path, self.active == "left")
        # The verdict glyph rides on the full-height splitter band (painted once
        # in draw()); its bg matches so the band stays continuous behind it.
        sep = _SEPARATOR.get(verdict, " ! ")
        sep_fg = _DIFF_FG if is_diff else self._muted
        ctx.draw_text(self._sep_x, y, sep,
                      Style(fg=sep_fg, bg=self._gutter_bg, attr=TextAttribute.BOLD, font=MONO))
        side(self._right_x, self._right_w, node.right_path, self.active == "right")

    def _draw_side_grid(self, ctx, x, col_w, node, path, y, fg, row_bg, suffix) -> None:
        """Terminal / character-grid tree column: box-drawing connectors in the
        cell grid (monospace, so ├ └ │ align and column-count truncation is
        exact)."""
        col_w = int(col_w)  # a fractional split width still slices whole cells
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

    # --- mouse ---------------------------------------------------------------

    def _row_at(self, y: float) -> Optional[int]:
        """Visible-list index under widget-local ``y`` (header is row 0, body
        starts at row 1), or None if the click is outside the row area."""
        if y < 1 or y >= 1 + self._view_h:
            return None
        ri = int(self.top + (y - 1.0))
        return ri if 0 <= ri < len(self.visible) else None

    def _side_at(self, x: float) -> Optional[str]:
        """Which pane column ``x`` falls in ('left'/'right'), or None for the
        gutter / scrollbar."""
        if self._left_x <= x < self._left_x + self._left_w:
            return "left"
        if self._right_x <= x < self._right_x + self._right_w:
            return "right"
        return None

    def _set_split_from_x(self, x: float) -> None:
        # Keep the fractional pointer position (no cell rounding) so the split
        # tracks the cursor pixel-for-pixel on a GUI backend.
        split_x = max(float(_MIN_PANE), min(self._avail - _MIN_PANE, x))
        self._split_ratio = split_x / self._avail
        self._render()

    def _nudge_split(self, delta: float) -> None:
        if not self._resizable:
            return
        lo, hi = _MIN_PANE / self._avail, 1.0 - _MIN_PANE / self._avail
        self._split_ratio = max(lo, min(hi, self._split_ratio + delta))
        self._render()

    def _handle_mouse(self, event: Event) -> bool:
        x = event.x if event.x is not None else 0.0
        y = event.y if event.y is not None else 0.0
        in_gutter = self._sep_x <= x < self._right_x
        if event.type is EventType.MOUSE_DOWN:
            if in_gutter and self._resizable:
                self._dragging_split = True
                self._drag_offset = x - self._sep_x  # grab point within the band
                return True
            # Click-to-select: move the cursor to the row and focus its side.
            ri = self._row_at(y)
            if ri is not None:
                self.cursor = ri
                side = self._side_at(x)
                if side is not None:
                    self.active = side
                self._ensure_cursor_visible()
                self._update_priorities()
                self._render()
            return True
        if event.type is EventType.MOUSE_DRAG:
            if self._dragging_split:
                self._set_split_from_x(x - self._drag_offset)
            return True
        if event.type is EventType.MOUSE_UP:
            self._dragging_split = False
            return True
        if event.type is EventType.MOUSE_CLICK:
            # A release over the same widget the press began on. Double-click
            # (two on the same row within the window) activates like Enter:
            # expand/collapse a directory, or open a file's diff.
            ri = self._row_at(y)
            now = time.monotonic()
            if (ri is not None and ri == self._last_click_row
                    and now - self._last_click_t <= _DOUBLE_CLICK_S):
                self.cursor = ri
                node = self._current()
                if node is not None and node.is_directory:
                    self._toggle()
                elif node is not None:
                    self._open_file_diff()
                self._last_click_row = -1
                self._render()
            else:
                self._last_click_row = ri if ri is not None else -1
                self._last_click_t = now
            return True
        return True

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
            self._update_priorities()  # scan what scrolled into view first
            return True
        if event.type in self._MOUSE:
            return self._handle_mouse(event)
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
        elif char == "[":
            self._nudge_split(-0.05)
        elif char == "]":
            self._nudge_split(0.05)
        elif char == "?":
            self._show_help()
        self._update_priorities()  # bias scanning toward the new viewport
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
