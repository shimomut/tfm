"""
Directory Diff Viewer - Recursive directory comparison with tree-structured display.

This module provides a UILayer component for comparing two directories recursively,
displaying differences in an expandable/collapsible tree structure with visual highlighting.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Tuple
import threading
import queue
import time
from threading import Thread
from tfm_path import Path
from tfm_ui_layer import UILayer
from ttk import KeyEvent, KeyCode, ModifierKey, CharEvent, SystemEvent, TextAttribute
from ttk.wide_char_utils import get_display_width, truncate_to_width

from tfm_colors import (
    get_color_with_attrs,
    get_status_color,
    get_log_color,
    COLOR_DIFF_BLANK,
    COLOR_REGULAR_FILE,
    COLOR_REGULAR_FILE_FOCUSED,
    COLOR_REGULAR_FILE_FOCUSED_INACTIVE,
    COLOR_DIRECTORIES,
    COLOR_DIRECTORIES_FOCUSED,
    COLOR_DIRECTORIES_FOCUSED_INACTIVE,
    COLOR_DIFF_SEPARATOR_RED,
    COLOR_TREE_LINES,
    COLOR_ERROR
)
from tfm_diff_viewer import DiffViewer
from tfm_scrollbar import draw_scrollbar, calculate_scrollbar_width
from tfm_info_dialog import InfoDialog
from tfm_progress_animator import ProgressAnimatorFactory
from tfm_log_manager import getLogger


class DifferenceType(Enum):
    """Classification of detected differences between directories."""
    IDENTICAL = "identical"
    ONLY_LEFT = "only_left"
    ONLY_RIGHT = "only_right"
    CONTENT_DIFFERENT = "content_different"
    CONTAINS_DIFFERENCE = "contains_difference"
    PENDING = "pending"  # Not yet scanned or compared


class ScanPriority:
    """Priority levels for progressive scanning tasks."""
    IMMEDIATE = 1000  # User just expanded this node
    VISIBLE = 100     # Currently visible in viewport
    EXPANDED = 50     # Expanded but scrolled off screen
    NORMAL = 10       # Not visible, not expanded
    LOW = 1           # One-sided directories (only on left or right)


@dataclass
class FileInfo:
    """Metadata for a single file or directory."""
    path: Path
    relative_path: str
    is_directory: bool
    size: int
    mtime: float
    is_accessible: bool
    error_message: Optional[str] = None


@dataclass
class ScanTask:
    """Task for queuing directory scan operations."""
    left_path: Optional[Path]
    right_path: Optional[Path]
    relative_path: str
    priority: int
    is_visible: bool


@dataclass
class ComparisonTask:
    """Task for queuing file comparison operations."""
    left_path: Optional[Path]
    right_path: Optional[Path]
    relative_path: str
    priority: int
    is_visible: bool


@dataclass
class TreeNode:
    """Represents a single node in the directory tree."""
    name: str
    left_path: Optional[Path]
    right_path: Optional[Path]
    is_directory: bool
    difference_type: DifferenceType
    depth: int
    is_expanded: bool
    children: List['TreeNode']
    parent: Optional['TreeNode'] = None
    # Progressive scanning state fields
    children_scanned: bool = False  # True if directory contents have been listed
    content_compared: bool = False  # True if file content has been compared
    scan_in_progress: bool = False  # True if currently being scanned


class DirectoryScanner:
    """
    Handles recursive directory traversal in a worker thread.
    
    This class scans two directories recursively, collecting file metadata
    and reporting progress through a callback function. It supports cancellation
    to allow users to abort long-running scans.
    """
    
    def __init__(self, left_path: Path, right_path: Path, progress_callback):
        """
        Initialize the directory scanner.
        
        Args:
            left_path: Root path for left directory
            right_path: Root path for right directory
            progress_callback: Callback function for progress updates.
                             Called with (current_count, total_estimate, status_message)
        """
        self.left_path = left_path
        self.right_path = right_path
        self.progress_callback = progress_callback
        self._cancel_flag = False
    
    def scan(self) -> tuple[Dict[str, FileInfo], Dict[str, FileInfo]]:
        """
        Scan both directories recursively.
        
        Returns:
            Tuple of (left_files, right_files) dictionaries.
            Keys are relative paths, values are FileInfo objects.
            
        Raises:
            Exception: If scanning is cancelled or encounters fatal errors
        """
        left_files = {}
        right_files = {}
        
        # Scan left directory
        if self.progress_callback:
            self.progress_callback(0, 0, "Scanning left directory...")
        left_files = self._scan_directory(self.left_path, "left")
        
        if self._cancel_flag:
            return {}, {}
        
        # Scan right directory
        if self.progress_callback:
            self.progress_callback(0, 0, "Scanning right directory...")
        right_files = self._scan_directory(self.right_path, "right")
        
        if self._cancel_flag:
            return {}, {}
        
        # Final progress update
        if self.progress_callback:
            total_files = len(left_files) + len(right_files)
            self.progress_callback(total_files, total_files, "Scan complete")
        
        return left_files, right_files
    
    def _scan_directory(self, root_path: Path, side: str) -> Dict[str, FileInfo]:
        """
        Recursively scan a single directory.
        
        Args:
            root_path: Root directory to scan
            side: "left" or "right" for progress messages
            
        Returns:
            Dictionary mapping relative paths to FileInfo objects
        """
        files = {}
        items_processed = 0
        
        try:
            # Use a stack for iterative traversal to avoid deep recursion
            stack = [root_path]
            
            while stack and not self._cancel_flag:
                current_path = stack.pop()
                
                try:
                    # Get relative path from root
                    if current_path == root_path:
                        relative_path = ""
                    else:
                        relative_path = str(current_path.relative_to(root_path))
                    
                    # Get file stats
                    try:
                        stat_info = current_path.stat()
                        is_accessible = True
                        error_message = None
                    except (OSError, PermissionError) as e:
                        # Mark as inaccessible but continue
                        is_accessible = False
                        error_message = str(e)
                        stat_info = None
                    
                    # Create FileInfo
                    if stat_info:
                        file_info = FileInfo(
                            path=current_path,
                            relative_path=relative_path,
                            is_directory=current_path.is_dir(),
                            size=stat_info.st_size if not current_path.is_dir() else 0,
                            mtime=stat_info.st_mtime,
                            is_accessible=is_accessible,
                            error_message=error_message
                        )
                    else:
                        # Create FileInfo for inaccessible items
                        file_info = FileInfo(
                            path=current_path,
                            relative_path=relative_path,
                            is_directory=False,  # Unknown, assume file
                            size=0,
                            mtime=0.0,
                            is_accessible=is_accessible,
                            error_message=error_message
                        )
                    
                    # Store in dictionary
                    if relative_path:  # Don't store root itself
                        files[relative_path] = file_info
                    
                    # If directory and accessible, add children to stack
                    if file_info.is_directory and is_accessible:
                        try:
                            for child in current_path.iterdir():
                                stack.append(child)
                        except (OSError, PermissionError) as e:
                            # Can't read directory contents, mark error
                            file_info.is_accessible = False
                            file_info.error_message = f"Cannot read directory: {e}"
                    
                    # Update progress periodically
                    items_processed += 1
                    if items_processed % 50 == 0 and self.progress_callback:
                        self.progress_callback(
                            items_processed,
                            items_processed,  # We don't know total yet
                            f"Scanning {side} directory... ({items_processed} items)"
                        )
                
                except Exception as e:
                    # Log error but continue scanning
                    self.logger.error(f"Error scanning {current_path}: {e}")
                    continue
        
        except Exception as e:
            # Fatal error scanning root directory
            self.logger.error(f"Fatal error scanning {root_path}: {e}")
            raise
        
        return files
    
    def cancel(self) -> None:
        """Cancel the scanning operation."""
        self._cancel_flag = True


class DiffEngine:
    """
    Builds the tree structure and detects differences between directories.
    
    This class takes the file dictionaries from DirectoryScanner and constructs
    a unified tree structure, classifying each node according to the type of
    difference detected.
    """
    
    def __init__(self, left_files: Dict[str, FileInfo], right_files: Dict[str, FileInfo]):
        """
        Initialize the diff engine.
        
        Args:
            left_files: Dictionary of files from left directory (relative_path -> FileInfo)
            right_files: Dictionary of files from right directory (relative_path -> FileInfo)
        """
        self.left_files = left_files
        self.right_files = right_files
        self.comparison_errors: Dict[str, str] = {}  # Track file comparison errors
    
    def build_tree(self) -> TreeNode:
        """
        Build a unified tree structure from both file sets.
        
        This method creates a tree that contains all unique paths from both
        directories, organized hierarchically. Each node is classified according
        to its difference type.
        
        Returns:
            Root TreeNode containing the entire tree
        """
        # Create root node
        root = TreeNode(
            name="",
            left_path=None,
            right_path=None,
            is_directory=True,
            difference_type=DifferenceType.IDENTICAL,  # Will be updated
            depth=0,
            is_expanded=True,
            children=[],
            parent=None
        )
        
        # Get all unique paths from both sides
        all_paths = set(self.left_files.keys()) | set(self.right_files.keys())
        
        # Build tree structure by processing paths in sorted order
        # This ensures parent directories are created before children
        for relative_path in sorted(all_paths):
            self._add_path_to_tree(root, relative_path)
        
        # Sort children at each level: directories first, then files, alphabetically within each group
        self._sort_tree(root)
        
        # Classify all nodes (bottom-up to propagate directory differences)
        self._classify_tree(root)
        
        return root
    
    def _add_path_to_tree(self, root: TreeNode, relative_path: str) -> None:
        """
        Add a path to the tree, creating intermediate directories as needed.
        
        Args:
            root: Root node of the tree
            relative_path: Relative path to add
        """
        # Split path into components
        parts = relative_path.split('/')
        
        current_node = root
        current_path = ""
        
        # Traverse/create path components
        for i, part in enumerate(parts):
            # Build current path
            if current_path:
                current_path = f"{current_path}/{part}"
            else:
                current_path = part
            
            # Check if this child already exists
            existing_child = None
            for child in current_node.children:
                if child.name == part:
                    existing_child = child
                    break
            
            if existing_child:
                # Move to existing child
                current_node = existing_child
            else:
                # Create new node
                left_info = self.left_files.get(current_path)
                right_info = self.right_files.get(current_path)
                
                # Determine if this is a directory
                # It's a directory if:
                # 1. It's not the last component (intermediate path)
                # 2. Either side marks it as a directory
                is_last_component = (i == len(parts) - 1)
                is_directory = not is_last_component or \
                              (left_info and left_info.is_directory) or \
                              (right_info and right_info.is_directory)
                
                # Create new child node
                new_node = TreeNode(
                    name=part,
                    left_path=left_info.path if left_info else None,
                    right_path=right_info.path if right_info else None,
                    is_directory=is_directory,
                    difference_type=DifferenceType.IDENTICAL,  # Will be classified later
                    depth=current_node.depth + 1,
                    is_expanded=False,  # Start collapsed
                    children=[],
                    parent=current_node
                )
                
                current_node.children.append(new_node)
                current_node = new_node
    
    def _sort_tree(self, node: TreeNode) -> None:
        """
        Recursively sort children at each level of the tree.
        
        Sorting order:
        1. Directories before files
        2. Within directories: alphabetical order (case-insensitive)
        3. Within files: alphabetical order (case-insensitive)
        
        Args:
            node: Node whose children should be sorted (recursively)
        """
        if not node.children:
            return
        
        # Sort children: directories first, then files, alphabetically within each group
        node.children.sort(key=lambda child: (
            not child.is_directory,  # False (directories) sorts before True (files)
            child.name.lower()       # Case-insensitive alphabetical order
        ))
        
        # Recursively sort children of each child
        for child in node.children:
            self._sort_tree(child)
    
    def _classify_tree(self, node: TreeNode) -> None:
        """
        Recursively classify all nodes in the tree.
        
        This method performs a post-order traversal (children first) to ensure
        directory classifications reflect their contents.
        
        Args:
            node: Node to classify (along with its subtree)
        """
        # First, classify all children
        for child in node.children:
            self._classify_tree(child)
        
        # Then classify this node
        node.difference_type = self.classify_node(node)
    
    def classify_node(self, node: TreeNode) -> DifferenceType:
        """
        Classify a node's difference type.
        
        Args:
            node: TreeNode to classify
            
        Returns:
            DifferenceType classification
        """
        # Root node is special - classify based on children
        if node.depth == 0:
            # Apply same logic as regular directories
            has_difference = False
            has_pending = False
            
            for child in node.children:
                if child.difference_type == DifferenceType.PENDING:
                    has_pending = True
                elif child.difference_type != DifferenceType.IDENTICAL:
                    # Found a real difference
                    has_difference = True
                    break
            
            # If any real difference found, mark as CONTAINS_DIFFERENCE immediately
            if has_difference:
                return DifferenceType.CONTAINS_DIFFERENCE
            
            # If all children are identical, mark as IDENTICAL
            if not has_pending:
                return DifferenceType.IDENTICAL
            
            # Otherwise, still have pending children and no differences found yet
            return DifferenceType.PENDING
        
        # Check if node exists on both sides
        exists_left = node.left_path is not None
        exists_right = node.right_path is not None
        
        # Only on left side
        if exists_left and not exists_right:
            return DifferenceType.ONLY_LEFT
        
        # Only on right side
        if exists_right and not exists_left:
            return DifferenceType.ONLY_RIGHT
        
        # Exists on both sides
        if node.is_directory:
            # For directories, check if any children have differences
            # Check for actual differences (not just pending)
            has_difference = False
            has_pending = False
            
            for child in node.children:
                if child.difference_type == DifferenceType.PENDING:
                    has_pending = True
                elif child.difference_type != DifferenceType.IDENTICAL:
                    # Found a real difference
                    has_difference = True
                    break
            
            # If any real difference found, mark as CONTAINS_DIFFERENCE immediately
            if has_difference:
                return DifferenceType.CONTAINS_DIFFERENCE
            
            # If all children are identical, mark as IDENTICAL
            if not has_pending:
                return DifferenceType.IDENTICAL
            
            # Otherwise, still have pending children and no differences found yet
            return DifferenceType.PENDING
        else:
            # For files, compare content
            if self.compare_file_content(node.left_path, node.right_path):
                return DifferenceType.IDENTICAL
            else:
                return DifferenceType.CONTENT_DIFFERENT
    
    def compare_file_content(self, left_path: Path, right_path: Path) -> bool:
        """
        Compare file content for equality.
        
        This method performs a byte-by-byte comparison of two files.
        For efficiency, it compares file sizes first, then reads and compares
        content in chunks.
        
        Args:
            left_path: Path to left file
            right_path: Path to right file
            
        Returns:
            True if files are identical, False otherwise
        """
        try:
            # Quick check: compare file sizes first
            left_stat = left_path.stat()
            right_stat = right_path.stat()
            
            if left_stat.st_size != right_stat.st_size:
                return False
            
            # Compare content in chunks for memory efficiency
            chunk_size = 8192  # 8KB chunks
            
            with left_path.open('rb') as left_file, right_path.open('rb') as right_file:
                while True:
                    left_chunk = left_file.read(chunk_size)
                    right_chunk = right_file.read(chunk_size)
                    
                    if left_chunk != right_chunk:
                        return False
                    
                    # End of file reached
                    if not left_chunk:
                        break
            
            return True
            
        except (OSError, IOError, PermissionError) as e:
            # Store error for this file comparison
            error_key = f"{left_path}|{right_path}"
            error_msg = f"Error comparing files: {e}"
            self.comparison_errors[error_key] = error_msg
            
            # Log the error
            self.logger.error(error_msg)
            
            # If we can't read the files, consider them different
            return False



class DirectoryDiffViewer(UILayer):
    """
    Directory comparison viewer implementing UILayer interface.
    
    This class provides a full-screen UI for comparing two directories recursively,
    displaying differences in an expandable/collapsible tree structure with visual
    highlighting. It integrates with TFM's UILayer stack system for seamless
    navigation between different views.
    """
    
    def __init__(self, renderer, left_path: Path, right_path: Path, layer_stack=None, file_list_manager=None):
        """
        Initialize the directory diff viewer.
        
        Args:
            renderer: TTK renderer instance
            left_path: Path to left directory
            right_path: Path to right directory
            layer_stack: Optional UILayerStack for pushing new layers (e.g., DiffViewer)
            file_list_manager: Optional FileListManager instance for accessing show_hidden setting
        """
        self.logger = getLogger("DirDiff")
        self.renderer = renderer
        self.left_path = left_path
        self.right_path = right_path
        self.layer_stack = layer_stack
        self.file_list_manager = file_list_manager
        
        # Tree structure
        self.root_node: Optional[TreeNode] = None
        self.visible_nodes: List[TreeNode] = []
        self.node_index_map: Dict[int, int] = {}  # Maps id(node) -> index
        
        # Navigation state
        self.scroll_offset = 0
        self.cursor_position = 0
        self.horizontal_offset = 0
        
        # Pane focus state (for future copy operations)
        self.active_pane = 'left'  # 'left' or 'right'
        
        # Display options
        self.show_identical = True  # Whether to show identical files
        
        # Layout constants - use ASCII characters for consistent width
        self.separator_identical = " = "   # Items are identical
        self.separator_different = " ! "   # Items are different
        self.separator_only_left = " < "   # Only on left
        self.separator_only_right = " > "  # Only on right
        self.separator_contains_diff = " ! " # Directory contains differences
        # All separators are now 3 characters wide
        self.separator_width = 3
        
        # Scanning state
        self.scan_in_progress = False
        self.scan_progress = 0.0
        self.scan_current = 0
        self.scan_total = 0
        self.scan_status = ""
        self.scan_cancelled = False
        self.scanner: Optional[DirectoryScanner] = None
        
        # Scan results
        self.left_files: Dict[str, FileInfo] = {}
        self.right_files: Dict[str, FileInfo] = {}
        self.scan_error: Optional[str] = None
        self.comparison_errors: Dict[str, str] = {}  # File comparison errors
        
        # Progressive tree building
        self.tree_lock = threading.Lock()  # Protect tree during updates
        self.last_tree_update = 0.0  # Time of last tree rebuild
        self.tree_update_interval = 0.5  # Rebuild tree every 0.5 seconds during scan
        
        # Thread synchronization primitives
        self.data_lock = threading.RLock()  # Protect file dictionaries
        self.queue_lock = threading.Lock()  # Protect work queues
        
        # Work queues for progressive scanning
        self.scan_queue: queue.Queue = queue.Queue()  # Directory scanning tasks
        self.priority_queue: queue.PriorityQueue = queue.PriorityQueue()  # High-priority scans
        self.comparison_queue: queue.Queue = queue.Queue()  # File comparison tasks
        self.priority_counter = 0  # Counter to make priority queue items unique
        
        # Worker thread management
        self.scanner_thread: Optional[Thread] = None  # Directory scanner worker thread
        self.comparator_thread: Optional[Thread] = None  # File comparator worker thread
        self.cancelled: bool = False  # Shutdown flag for worker threads
        self.worker_error: Optional[str] = None  # Error flag to notify main thread of worker exceptions
        
        # Progress animator
        # Create minimal config for animator
        class MinimalConfig:
            PROGRESS_ANIMATION_PATTERN = 'spinner'
            PROGRESS_ANIMATION_SPEED = 0.08
        self.progress_animator = ProgressAnimatorFactory.create_loading_animator(MinimalConfig())
        
        # Status bar state (Task 12.2)
        self._scan_complete_shown = False  # Track if scan complete message has been shown
        
        # Help dialog
        self.info_dialog = InfoDialog(None, renderer)
        
        # UILayer interface state
        self._dirty = True
        self._should_close = False
        
        # Start scanning immediately
        self.start_scan()
    
    # ========================================================================
    # UILayer Interface Implementation
    # ========================================================================
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        """
        Handle keyboard events.
        
        Args:
            event: KeyEvent to handle
            
        Returns:
            True if event was consumed, False otherwise
        """
        # Only handle KeyEvents, not CharEvents
        if not isinstance(event, KeyEvent) or event is None:
            return False
        
        # Allow ESC to cancel scan or close viewer
        if event.key_code == KeyCode.ESCAPE:
            if self.scan_in_progress:
                # Cancel scan
                if self.scanner and not self.scan_cancelled:
                    self.scanner.cancel()
                    self.scan_cancelled = True
                    self.scan_status = "Cancelling scan..."
                    self.mark_dirty()
                return True
            else:
                # Close viewer
                self._should_close = True
                self.mark_dirty()
                return True
        
        # Allow 'q' to quit even during scan
        if event.char and event.char.lower() == 'q':
            if self.scan_in_progress:
                # Cancel scan first
                if self.scanner and not self.scan_cancelled:
                    self.scanner.cancel()
                    self.scan_cancelled = True
                    self.scan_status = "Cancelling scan..."
            # Close viewer
            self._should_close = True
            self.mark_dirty()
            return True
        
        # Allow help dialog even during scan
        if event.char and event.char == '?':
            self._show_help_dialog()
            return True
        
        # Allow navigation and other controls even during scan
        # (tree will show partial results)
        
        # Get display dimensions for scrolling calculations
        height, width = self.renderer.get_dimensions()
        # Reserve space for header (1 line), divider (1 line), details pane (4 lines), and status bar (1 line)
        display_height = height - 7
        
        # Handle Tab key to switch active pane
        if event.key_code == KeyCode.TAB:
            # Toggle active pane between left and right
            old_pane = self.active_pane
            self.active_pane = 'right' if self.active_pane == 'left' else 'left'
            self.logger.info(f"Switched focus from {old_pane} to {self.active_pane} pane")
            self.mark_dirty()
            return True
        
        # Handle character-based commands (only from KeyEvent)
        if event.char:
            char_lower = event.char.lower()
            if char_lower == 'q':
                # Quit viewer
                self._should_close = True
                self.mark_dirty()
                return True
            elif char_lower == 'i':
                # Toggle showing identical files
                self.show_identical = not self.show_identical
                self._update_visible_nodes()
                # Adjust cursor if needed
                if self.cursor_position >= len(self.visible_nodes):
                    self.cursor_position = max(0, len(self.visible_nodes) - 1)
                self.mark_dirty()
                return True
            elif event.char == '?':
                # Show help dialog
                self._show_help_dialog()
                return True
        
        # Handle special keys
        if event.key_code == KeyCode.ESCAPE:
            # Close viewer
            self._should_close = True
            self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.UP:
            # Check for Shift modifier to jump to previous difference
            if event.modifiers & ModifierKey.SHIFT:
                self._jump_to_previous_difference(display_height)
            else:
                # Move cursor up
                if self.cursor_position > 0:
                    self.cursor_position -= 1
                    # Ensure cursor is visible
                    self._ensure_cursor_visible(display_height)
                    self.mark_dirty()
                    # Update priorities when viewport changes
                    self._update_priorities()
            return True
        
        elif event.key_code == KeyCode.DOWN:
            # Check for Shift modifier to jump to next difference
            if event.modifiers & ModifierKey.SHIFT:
                self._jump_to_next_difference(display_height)
            else:
                # Move cursor down
                if self.cursor_position < len(self.visible_nodes) - 1:
                    self.cursor_position += 1
                    # Ensure cursor is visible
                    self._ensure_cursor_visible(display_height)
                    self.mark_dirty()
                    # Update priorities when viewport changes
                    self._update_priorities()
            return True
        
        elif event.key_code == KeyCode.PAGE_UP:
            # Scroll up one page
            if self.cursor_position > 0:
                self.cursor_position = max(0, self.cursor_position - display_height)
                self.scroll_offset = max(0, self.scroll_offset - display_height)
                self.mark_dirty()
                # Update priorities when viewport changes
                self._update_priorities()
            return True
        
        elif event.key_code == KeyCode.PAGE_DOWN:
            # Scroll down one page
            if self.cursor_position < len(self.visible_nodes) - 1:
                self.cursor_position = min(
                    len(self.visible_nodes) - 1,
                    self.cursor_position + display_height
                )
                max_scroll = max(0, len(self.visible_nodes) - display_height)
                self.scroll_offset = min(max_scroll, self.scroll_offset + display_height)
                self.mark_dirty()
                # Update priorities when viewport changes
                self._update_priorities()
            return True
        
        elif event.key_code == KeyCode.HOME:
            # Jump to first item
            if self.cursor_position > 0:
                self.cursor_position = 0
                self.scroll_offset = 0
                self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.END:
            # Jump to last item
            if self.cursor_position < len(self.visible_nodes) - 1:
                self.cursor_position = len(self.visible_nodes) - 1
                max_scroll = max(0, len(self.visible_nodes) - display_height)
                self.scroll_offset = max_scroll
                self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.ENTER:
            # Enter: Toggle expand/collapse for directories, open diff viewer for files
            if 0 <= self.cursor_position < len(self.visible_nodes):
                node = self.visible_nodes[self.cursor_position]
                if node.is_directory:
                    # Toggle expand/collapse for directories
                    if node.is_expanded:
                        self.collapse_node(self.cursor_position)
                    else:
                        self.expand_node(self.cursor_position)
                else:
                    # Open file diff viewer for files
                    self.open_file_diff(self.cursor_position)
            return True
        
        elif event.key_code == KeyCode.RIGHT:
            # Check for Shift modifier for tree navigation
            if event.modifiers & ModifierKey.SHIFT:
                # Shift+Right: Expand directory or move to first child if already expanded
                if 0 <= self.cursor_position < len(self.visible_nodes):
                    node = self.visible_nodes[self.cursor_position]
                    if node.is_directory:
                        if not node.is_expanded:
                            # Expand collapsed directory
                            self.expand_node(self.cursor_position)
                        else:
                            # Already expanded, move to first child if it exists
                            if node.children and self.cursor_position + 1 < len(self.visible_nodes):
                                self.cursor_position += 1
                                # Ensure cursor is visible
                                self._ensure_cursor_visible(display_height)
                                self.mark_dirty()
            else:
                # Right arrow without modifier: Switch to right pane
                if self.active_pane != 'right':
                    old_pane = self.active_pane
                    self.active_pane = 'right'
                    self.logger.info(f"Switched focus from {old_pane} to right pane")
                    self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.LEFT:
            # Check for Shift modifier for tree navigation
            if event.modifiers & ModifierKey.SHIFT:
                # Shift+Left: Collapse directory or move to parent
                if 0 <= self.cursor_position < len(self.visible_nodes):
                    node = self.visible_nodes[self.cursor_position]
                    if node.is_directory and node.is_expanded:
                        # Collapse expanded directory
                        self.collapse_node(self.cursor_position)
                    elif node.parent and node.parent.depth >= 0:
                        # Move to parent (for files or collapsed directories)
                        # Find parent in visible_nodes
                        parent_node = node.parent
                        for i, visible_node in enumerate(self.visible_nodes):
                            if visible_node is parent_node:
                                self.cursor_position = i
                                # Ensure cursor is visible
                                self._ensure_cursor_visible(display_height)
                                self.mark_dirty()
                                break
            else:
                # Left arrow without modifier: Switch to left pane
                if self.active_pane != 'left':
                    old_pane = self.active_pane
                    self.active_pane = 'left'
                    self.logger.info(f"Switched focus from {old_pane} to left pane")
                    self.mark_dirty()
            return True
        
        return False
    
    def handle_char_event(self, event: CharEvent) -> bool:
        """
        Handle character input events.
        
        Args:
            event: CharEvent to handle
            
        Returns:
            True if event was consumed, False otherwise
        """
        # TODO: Implement character-based commands in later tasks
        return False
    
    def handle_system_event(self, event: SystemEvent) -> bool:
        """
        Handle system events (resize, close, etc.).
        
        Args:
            event: SystemEvent to handle
            
        Returns:
            True if event was consumed, False otherwise
        """
        # Mark dirty on resize to trigger redraw
        if event.is_resize():
            self.mark_dirty()
            return True
        
        return False
    
    def handle_mouse_event(self, event) -> bool:
        """
        Handle a mouse event (UILayer interface method).
        
        Supports:
        - Mouse wheel scrolling for vertical navigation
        - Mouse button clicks to move cursor to clicked item
        - Double-click to toggle expand/collapse or open file diff
        
        Args:
            event: MouseEvent to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        from ttk.ttk_mouse_event import MouseEventType
        
        # Get display dimensions
        height, width = self.renderer.get_dimensions()
        display_height = height - 7  # Reserve space for header, divider, details, status
        
        # Handle double-click events to toggle expand/collapse or open file diff
        if event.event_type == MouseEventType.DOUBLE_CLICK:
            # Check if click is within the tree view area
            tree_view_start = 1
            tree_view_end = height - 5  # Reserve space for details pane (3 lines) and status (2 lines)
            
            if event.row < tree_view_start or event.row >= tree_view_end:
                return False
            
            # Calculate which item was double-clicked
            clicked_item_index = event.row - tree_view_start + self.scroll_offset
            
            # Validate the clicked index
            if self.visible_nodes and 0 <= clicked_item_index < len(self.visible_nodes):
                # Move cursor to the double-clicked item
                self.cursor_position = clicked_item_index
                
                # Trigger the same action as Enter key
                node = self.visible_nodes[self.cursor_position]
                if node.is_directory:
                    # Toggle expand/collapse for directories
                    if node.is_expanded:
                        self.collapse_node(self.cursor_position)
                    else:
                        self.expand_node(self.cursor_position)
                else:
                    # Open file diff viewer for files
                    self.open_file_diff(self.cursor_position)
                
                self.logger.info(f"Double-clicked item {clicked_item_index}")
                return True
            
            return False
        
        # Handle wheel events for scrolling
        if event.event_type == MouseEventType.WHEEL:
            max_scroll = max(0, len(self.visible_nodes) - display_height)
            
            # Calculate scroll amount (positive delta = scroll up, negative = scroll down)
            scroll_lines = int(event.scroll_delta_y * 1)
            
            if scroll_lines != 0:
                # Adjust scroll_offset based on scroll direction
                old_offset = self.scroll_offset
                new_offset = old_offset - scroll_lines  # Negative delta scrolls down (increases offset)
                
                # Clamp to valid range
                new_offset = max(0, min(new_offset, max_scroll))
                
                if new_offset != old_offset:
                    self.scroll_offset = new_offset
                    self._dirty = True
                    
                    # Update priorities when viewport changes (only if we have real TreeNode objects)
                    if self.visible_nodes and len(self.visible_nodes) > 0:
                        # Check if first item is a TreeNode (not a mock string)
                        first_node = self.visible_nodes[0]
                        if hasattr(first_node, 'is_directory'):
                            self._update_priorities()
                
                return True
        
        # Handle button down events for cursor movement
        if event.event_type == MouseEventType.BUTTON_DOWN:
            # Check if click is within the tree view area
            # Tree view starts at row 1 (after header) and ends before details pane
            tree_view_start = 1
            tree_view_end = height - 5  # Reserve space for details pane (3 lines) and status (2 lines)
            
            if event.row < tree_view_start or event.row >= tree_view_end:
                return False
            
            # Calculate which item was clicked (row 1 is first visible item)
            clicked_item_index = event.row - tree_view_start + self.scroll_offset
            
            # Move cursor to clicked item if valid
            if self.visible_nodes and 0 <= clicked_item_index < len(self.visible_nodes):
                self.cursor_position = clicked_item_index
                self.logger.info(f"Moved cursor to item {clicked_item_index}")
                self._dirty = True
                return True
        
        return False
    
    def render(self, renderer) -> None:
        """
        Render the directory diff viewer.
        
        Args:
            renderer: TTK renderer instance
        """
        height, width = renderer.get_dimensions()
        
        # Clear screen
        renderer.clear()
        
        # If scan error occurred, show error screen
        if self.scan_error:
            self._render_error_screen(renderer, width, height)
            return
        
        # Always render normal dual-pane view (even during scanning)
        self._render_header(renderer, width)
        
        # If scan is in progress or no tree yet, show what we have so far
        # Note: With progressive scanning, the tree is built incrementally by worker threads
        # We should NOT rebuild it here as that would lose expansion state and undo progressive updates
        if not self.root_node or not self.visible_nodes:
            # Only build initial tree if we don't have one yet
            with self.tree_lock:
                if (self.left_files or self.right_files) and not self.root_node:
                    # Build initial tree structure (this should only happen once)
                    self._build_tree_with_pending()
        
        # Render content (will show partial results during scan)
        self._render_content(renderer, width, height)
        
        # Render details pane for focused item
        self._render_details_pane(renderer, width, height)
        
        # Render status bar with progress indicator if scanning
        self._render_status_bar(renderer, width, height)
    
    def _render_header(self, renderer, width: int) -> None:
        """
        Render the header with directory paths and focus indicators.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
        """
        # Get status color for header
        status_color_pair, status_attrs = get_status_color()
        
        # Line 1: Directory paths with bold for focused pane
        left_label = " " + str(self.left_path)
        right_label = " " + str(self.right_path)
        
        # Reserve space for scrollbar to match content area
        reserved_scrollbar_width = 1
        
        # Calculate available space for each path
        # Format: "<path>  |  <path> [scrollbar]"
        available_width = width - self.separator_width - reserved_scrollbar_width
        # Split evenly, giving any extra character to the left side
        right_width = available_width // 2
        left_width = available_width - right_width
        
        # Truncate paths if needed using wide-char aware functions
        left_display_width = get_display_width(left_label)
        if left_display_width > left_width:
            left_label = truncate_to_width(left_label, left_width, ellipsis="…")
        
        right_display_width = get_display_width(right_label)
        if right_display_width > right_width:
            right_label = truncate_to_width(right_label, right_width, ellipsis="…")
        
        # Pad labels to exact widths using spaces
        left_actual_width = get_display_width(left_label)
        right_actual_width = get_display_width(right_label)
        left_padding = " " * (left_width - left_actual_width)
        right_padding = " " * (right_width - right_actual_width)
        
        # Apply bold attribute to active pane
        left_attrs = status_attrs | TextAttribute.BOLD if self.active_pane == 'left' else status_attrs
        right_attrs = status_attrs | TextAttribute.BOLD if self.active_pane == 'right' else status_attrs
        
        # Draw left pane header
        left_text = left_label + left_padding
        renderer.draw_text(0, 0, left_text, status_color_pair, left_attrs)
        
        # Draw separator
        header_separator = "   "  # 3 spaces to match separator width, no pipe
        renderer.draw_text(0, left_width, header_separator, status_color_pair, status_attrs)
        
        # Draw right pane header
        right_text = right_label + right_padding
        renderer.draw_text(0, left_width + self.separator_width, right_text, status_color_pair, right_attrs)
        
        # Fill remaining space with status color
        remaining_start = left_width + self.separator_width + len(right_text)
        if remaining_start < width:
            remaining_text = " " * (width - remaining_start)
            renderer.draw_text(0, remaining_start, remaining_text, status_color_pair, status_attrs)
    
    def _render_progress_screen(self, renderer, width: int, height: int) -> None:
        """
        Render progress screen during scanning.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        status_color_pair, status_attrs = get_status_color()
        
        # Header
        header = "Directory Diff - Scanning..."
        renderer.draw_text(0, 0, header[:width].ljust(width), status_color_pair, status_attrs)
        
        # Directory paths being compared
        left_label = f"Left:  {self.left_path}"
        right_label = f"Right: {self.right_path}"
        renderer.draw_text(2, 2, left_label[:width-4])
        renderer.draw_text(3, 2, right_label[:width-4])
        
        # Status message
        status_line = self.scan_status
        renderer.draw_text(5, 2, status_line[:width-4])
        
        # Progress information
        if self.scan_total > 0:
            # Show progress with counts
            progress_text = f"Progress: {self.scan_current} / {self.scan_total} items ({int(self.scan_progress * 100)}%)"
            renderer.draw_text(7, 2, progress_text[:width-4])
            
            # Draw progress bar
            bar_width = min(60, width - 6)
            filled = int(bar_width * self.scan_progress)
            bar = "[" + "=" * filled + ">" + " " * (bar_width - filled - 1) + "]"
            renderer.draw_text(8, 2, bar[:width-4])
        elif self.scan_current > 0:
            # Indeterminate progress - show count without percentage
            progress_text = f"Scanned: {self.scan_current} items..."
            renderer.draw_text(7, 2, progress_text[:width-4])
            
            # Draw animated progress indicator
            # Use a simple spinner animation based on current count
            spinner_chars = ["|", "/", "-", "\\"]
            spinner = spinner_chars[self.scan_current % len(spinner_chars)]
            spinner_text = f"[{spinner}] Scanning..."
            renderer.draw_text(8, 2, spinner_text[:width-4])
        
        # Help text
        help_text = "Press ESC to cancel"
        renderer.draw_text(height - 1, 0, help_text[:width].ljust(width), status_color_pair, status_attrs)
    
    def _render_cancellation_screen(self, renderer, width: int, height: int) -> None:
        """
        Render cancellation screen when scan is being cancelled.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        status_color_pair, status_attrs = get_status_color()
        
        # Header
        header = "Directory Diff - Cancelling..."
        renderer.draw_text(0, 0, header[:width].ljust(width), status_color_pair, status_attrs)
        
        # Cancellation message
        cancel_msg = "Cancelling scan operation..."
        renderer.draw_text(2, 2, cancel_msg[:width-4])
        
        # Show what was scanned before cancellation
        if self.scan_current > 0:
            scanned_msg = f"Scanned {self.scan_current} items before cancellation"
            renderer.draw_text(4, 2, scanned_msg[:width-4])
        
        # Status message
        status_line = self.scan_status
        renderer.draw_text(6, 2, status_line[:width-4])
        
        # Help text
        help_text = "Cleaning up... Viewer will close shortly"
        renderer.draw_text(height - 1, 0, help_text[:width].ljust(width), status_color_pair, status_attrs)
    
    def _render_error_screen(self, renderer, width: int, height: int) -> None:
        """
        Render error screen when scan fails.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        status_color_pair, status_attrs = get_status_color()
        
        # Header
        header = "Directory Diff - Error"
        renderer.draw_text(0, 0, header[:width].ljust(width), status_color_pair, status_attrs)
        
        # Error message
        error_line = f"Error: {self.scan_error}"
        renderer.draw_text(2, 2, error_line[:width-4])
        
        # Help text
        help_text = "Press ESC or Q to close"
        renderer.draw_text(height - 1, 0, help_text[:width].ljust(width), status_color_pair, status_attrs)
    
    def _render_loading_screen(self, renderer, width: int, height: int) -> None:
        """
        Render loading screen while building tree.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        status_color_pair, status_attrs = get_status_color()
        
        # Header
        header = "Directory Diff - Loading..."
        renderer.draw_text(0, 0, header[:width].ljust(width), status_color_pair, status_attrs)
        
        # Loading message
        renderer.draw_text(2, 2, "Building tree structure...")
        
        # Help text
        help_text = "Press ESC or Q to close"
        renderer.draw_text(height - 1, 0, help_text[:width].ljust(width), status_color_pair, status_attrs)
    
    def _render_content(self, renderer, width: int, height: int) -> None:
        """
        Render the tree content with side-by-side layout.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        # Calculate content area (header is 1 line, divider is 1 line, details pane is 4 lines, status bar is 1 line)
        content_start_y = 1
        content_height = height - 7  # Reserve space for header, divider, details pane (4 lines), and status bar
        
        # Check if directories are empty or identical (but not during scanning)
        if not self.scan_in_progress and (not self.visible_nodes or len(self.visible_nodes) == 0):
            # No visible nodes - directories are empty or all identical (with filter on)
            self._render_empty_or_identical_message(renderer, width, height, content_start_y, content_height)
            return
        
        # During scanning or when we have nodes, show the tree view
        # If no nodes yet during scan, just show empty tree (will fill in as scan progresses)
        if not self.visible_nodes:
            # Show empty tree area during scan
            return
        
        # Calculate scrollbar width
        scrollbar_width = calculate_scrollbar_width(len(self.visible_nodes), content_height)
        
        # Always reserve space for scrollbar to prevent separator from moving
        # when tree expands/collapses and scrollbar appears/disappears
        reserved_scrollbar_width = 1  # Always reserve at least 1 column for scrollbar
        
        # Add 1-character left padding for each pane
        left_padding = 1
        right_padding = 1
        
        # Calculate column widths for side-by-side layout
        # Format: [padding][indent][expand][name] | [padding][indent][expand][name] [scrollbar]
        # Use the same separator as the header for alignment
        available_width = width - left_padding - right_padding - self.separator_width - reserved_scrollbar_width
        # Split evenly, giving any extra character to the left side (same as header)
        right_column_width = available_width // 2
        left_column_width = available_width - right_column_width  # Left gets any extra character
        left_column_x = left_padding
        separator_x = left_padding + left_column_width
        right_column_x = left_padding + left_column_width + self.separator_width + right_padding
        scrollbar_x = width - scrollbar_width if scrollbar_width > 0 else width
        
        # Render visible nodes
        for i in range(content_height):
            y_pos = content_start_y + i
            node_index = self.scroll_offset + i
            
            if node_index >= len(self.visible_nodes):
                # No more nodes to display - render empty rows with separator bar
                separator_color_pair, separator_attrs = get_status_color()
                empty_separator = " " * self.separator_width
                
                # Render remaining empty rows
                for j in range(i, content_height):
                    empty_y_pos = content_start_y + j
                    # Left padding
                    renderer.draw_text(empty_y_pos, 0, " " * left_padding, 0, 0)
                    # Empty left column
                    renderer.draw_text(empty_y_pos, left_column_x, " " * left_column_width, 0, 0)
                    # Separator bar
                    renderer.draw_text(empty_y_pos, separator_x, empty_separator, separator_color_pair, separator_attrs)
                    # Empty right column
                    renderer.draw_text(empty_y_pos, right_column_x, " " * right_column_width, 0, 0)
                break
            
            node = self.visible_nodes[node_index]
            is_focused = (node_index == self.cursor_position)
            
            # Get colors for this node based on difference type and which pane it's in
            left_color_pair, left_attrs = self._get_node_colors(node, is_focused, 'left')
            right_color_pair, right_attrs = self._get_node_colors(node, is_focused, 'right')
            blank_color_pair, blank_attrs = get_color_with_attrs(COLOR_DIFF_BLANK)
            
            # Build tree lines to show parent-child relationships
            tree_lines = self._build_tree_lines(node)
            tree_lines_len = len(tree_lines)
            
            # Build icon based on node type
            if node.is_directory:
                if node.is_expanded:
                    icon = "📂 "  # Open folder emoji
                else:
                    icon = "📁 "  # Closed folder emoji
            else:
                icon = "📄 "  # File emoji
            
            # Check for errors on this node
            relative_path = self._get_relative_path(node)
            left_info = self.left_files.get(relative_path)
            right_info = self.right_files.get(relative_path)
            has_left_error = left_info and not left_info.is_accessible
            has_right_error = right_info and not right_info.is_accessible
            
            # Check for file comparison errors
            has_comparison_error = False
            if node.left_path and node.right_path:
                error_key = f"{node.left_path}|{node.right_path}"
                has_comparison_error = error_key in self.comparison_errors
            
            # Add error indicator if node has errors
            error_indicator = ""
            if has_left_error or has_right_error or has_comparison_error:
                error_indicator = "⚠ "
            
            # Build node text without tree lines (we'll render them separately in gray)
            # Add scanning indicator if scan is in progress (Task 9.2)
            if node.scan_in_progress:
                node_content = icon + error_indicator + node.name + " [scanning...]"
            elif not node.children_scanned and node.is_directory:
                # Directory not yet scanned - show ellipsis indicator (Task 12.1)
                # BUT: Don't show "..." for one-sided directories since their result is deterministic
                exists_left = node.left_path is not None
                exists_right = node.right_path is not None
                if exists_left and exists_right:
                    # Both-sided directory - show "..." since we need to scan to find differences
                    node_content = icon + error_indicator + node.name + " ..."
                else:
                    # One-sided directory - no "..." needed, result is deterministic
                    node_content = icon + error_indicator + node.name
            elif not node.content_compared and not node.is_directory:
                # File not yet compared - show pending indicator (Task 12.1)
                node_content = icon + error_indicator + node.name + " [pending]"
            else:
                node_content = icon + error_indicator + node.name
            
            # Choose separator based on difference type
            if node.difference_type == DifferenceType.IDENTICAL:
                separator = self.separator_identical
            elif node.difference_type == DifferenceType.PENDING:
                # Use neutral separator for pending items (Task 12.3)
                separator = " ? "  # Question mark to indicate unknown status
            elif node.difference_type == DifferenceType.ONLY_LEFT:
                separator = self.separator_only_left
            elif node.difference_type == DifferenceType.ONLY_RIGHT:
                separator = self.separator_only_right
            elif node.difference_type == DifferenceType.CONTENT_DIFFERENT:
                separator = self.separator_different
            elif node.difference_type == DifferenceType.CONTAINS_DIFFERENCE:
                separator = self.separator_contains_diff
            else:
                separator = self.separator_different
            
            # Render left padding
            renderer.draw_text(y_pos, 0, " " * left_padding, 0, 0)
            
            # Render left column
            if node.left_path:
                # Node exists on left side
                # First render tree lines in gray
                if tree_lines:
                    renderer.draw_text(y_pos, left_column_x, tree_lines, COLOR_TREE_LINES, TextAttribute.NORMAL)
                
                # Then render the rest of the content in normal color
                content_text = truncate_to_width(node_content, left_column_width - tree_lines_len)
                content_text_width = get_display_width(content_text)
                content_padding = " " * (left_column_width - tree_lines_len - content_text_width)
                content_text = content_text + content_padding
                renderer.draw_text(y_pos, left_column_x + tree_lines_len, content_text, left_color_pair, left_attrs)
            else:
                # Node doesn't exist on left side - show tree lines for missing item
                # Use continuation lines only (no branch connectors)
                missing_tree_lines = self._build_tree_lines_for_missing(node)
                if missing_tree_lines:
                    renderer.draw_text(y_pos, left_column_x, missing_tree_lines, COLOR_TREE_LINES, TextAttribute.NORMAL)
                
                # Fill rest with blank - use focused color if this item is focused
                blank_len = left_column_width - len(missing_tree_lines)
                if blank_len > 0:
                    blank_text = " " * blank_len
                    # Use focused color for blank area if item is focused
                    if is_focused:
                        renderer.draw_text(y_pos, left_column_x + len(missing_tree_lines), blank_text, left_color_pair, left_attrs)
                    else:
                        renderer.draw_text(y_pos, left_column_x + len(missing_tree_lines), blank_text, blank_color_pair, blank_attrs)
            
            # Render separator with appropriate color
            # Use red foreground (with status background) for difference separators
            if (separator == self.separator_different or 
                separator == self.separator_contains_diff or
                separator == self.separator_only_left or
                separator == self.separator_only_right):
                # Red foreground with status bar background for differences
                separator_color_pair = COLOR_DIFF_SEPARATOR_RED
                separator_attrs = TextAttribute.NORMAL
            elif separator == " ? ":
                # Neutral color for pending separator (Task 12.3)
                # Use status bar color with NORMAL attribute
                separator_color_pair, _ = get_status_color()
                separator_attrs = TextAttribute.NORMAL
            else:
                # Status bar color for identical separator
                separator_color_pair, separator_attrs = get_status_color()
            
            renderer.draw_text(y_pos, separator_x, separator, separator_color_pair, separator_attrs)
            
            # Render right column
            if node.right_path:
                # Node exists on right side
                # First render tree lines in gray
                if tree_lines:
                    renderer.draw_text(y_pos, right_column_x, tree_lines, COLOR_TREE_LINES, TextAttribute.NORMAL)
                
                # Then render the rest of the content in normal color
                content_text = truncate_to_width(node_content, right_column_width - tree_lines_len)
                content_text_width = get_display_width(content_text)
                content_padding = " " * (right_column_width - tree_lines_len - content_text_width)
                content_text = content_text + content_padding
                renderer.draw_text(y_pos, right_column_x + tree_lines_len, content_text, right_color_pair, right_attrs)
            else:
                # Node doesn't exist on right side - show tree lines for missing item
                # Use continuation lines only (no branch connectors)
                missing_tree_lines = self._build_tree_lines_for_missing(node)
                if missing_tree_lines:
                    renderer.draw_text(y_pos, right_column_x, missing_tree_lines, COLOR_TREE_LINES, TextAttribute.NORMAL)
                
                # Fill rest with blank - use focused color if this item is focused
                blank_len = right_column_width - len(missing_tree_lines)
                if blank_len > 0:
                    blank_text = " " * blank_len
                    # Use focused color for blank area if item is focused
                    if is_focused:
                        renderer.draw_text(y_pos, right_column_x + len(missing_tree_lines), blank_text, right_color_pair, right_attrs)
                    else:
                        renderer.draw_text(y_pos, right_column_x + len(missing_tree_lines), blank_text, blank_color_pair, blank_attrs)

        
        # Draw scrollbar if needed
        if scrollbar_width > 0:
            draw_scrollbar(
                renderer,
                start_y=content_start_y,
                x_pos=scrollbar_x,
                display_height=content_height,
                total_items=len(self.visible_nodes),
                scroll_offset=self.scroll_offset,
                inverted=False
            )
    
    def _render_empty_or_identical_message(self, renderer, width: int, height: int, 
                                          content_start_y: int, content_height: int) -> None:
        """
        Render a message when directories are empty or identical.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
            content_start_y: Y position where content starts
            content_height: Height of content area
        """
        # Determine the appropriate message
        if not self.root_node or not self.root_node.children:
            # Both directories are empty
            message = "Both directories are empty"
        elif not self.show_identical:
            # All differences are hidden by filter
            message = "All files are identical (press 'i' to show them)"
        else:
            # Directories are identical
            message = "Directories are identical - no differences found"
        
        # Center the message vertically and horizontally
        message_y = content_start_y + (content_height // 2)
        message_x = (width - len(message)) // 2
        
        if message_x < 0:
            message_x = 0
            message = message[:width]
        
        renderer.draw_text(message_y, message_x, message)
    
    def _get_node_colors(self, node: TreeNode, is_focused: bool, pane: str = 'left') -> tuple:
        """
        Get color pair and attributes for a node based on its difference type.
        
        Args:
            node: TreeNode to get colors for
            is_focused: Whether this node is currently focused (cursor on it)
            pane: Which pane this is being rendered in ('left' or 'right')
            
        Returns:
            Tuple of (color_pair, attributes)
        """
        if is_focused:
            # Focused nodes use focused/inactive color pairs based on which pane is active
            # Active pane uses focused colors (blue background)
            # Inactive pane uses focused_inactive colors (gray background)
            is_active_pane = (pane == self.active_pane)
            
            if node.is_directory:
                if is_active_pane:
                    return get_color_with_attrs(COLOR_DIRECTORIES_FOCUSED)
                else:
                    return get_color_with_attrs(COLOR_DIRECTORIES_FOCUSED_INACTIVE)
            else:
                if is_active_pane:
                    return get_color_with_attrs(COLOR_REGULAR_FILE_FOCUSED)
                else:
                    return get_color_with_attrs(COLOR_REGULAR_FILE_FOCUSED_INACTIVE)
        
        # Non-focused nodes: use regular colors without background
        # Differences are indicated by separator symbols and foreground colors
        if node.difference_type == DifferenceType.PENDING:
            # Use neutral color for pending items (Task 12.3)
            # Use regular file/directory color with DIM attribute to distinguish from IDENTICAL
            if node.is_directory:
                color_pair, _ = get_color_with_attrs(COLOR_DIRECTORIES)
                return (color_pair, TextAttribute.NORMAL)
            else:
                color_pair, _ = get_color_with_attrs(COLOR_REGULAR_FILE)
                return (color_pair, TextAttribute.NORMAL)
        elif node.difference_type == DifferenceType.ONLY_LEFT or \
           node.difference_type == DifferenceType.ONLY_RIGHT:
            # Use error color (red foreground) for items only on one side
            return (COLOR_ERROR, TextAttribute.NORMAL)
        elif node.difference_type == DifferenceType.CONTENT_DIFFERENT:
            # Use error color (red foreground) for different content
            return (COLOR_ERROR, TextAttribute.NORMAL)
        elif node.difference_type == DifferenceType.CONTAINS_DIFFERENCE:
            # Directories containing differences - use directory color
            return get_color_with_attrs(COLOR_DIRECTORIES)
        else:  # IDENTICAL
            # Use regular file/directory color
            if node.is_directory:
                return get_color_with_attrs(COLOR_DIRECTORIES)
            else:
                return get_color_with_attrs(COLOR_REGULAR_FILE)
    
    def _show_help_dialog(self) -> None:
        """Show help dialog with keyboard shortcuts."""
        title = "Directory Diff Viewer - Help"
        help_lines = [
            "NAVIGATION",
            "  ↑/↓           Move cursor up/down",
            "  Shift+↑/↓     Jump to previous/next difference",
            "  PgUp/PgDn     Scroll one page up/down",
            "  Home/End      Jump to first/last item",
            "",
            "PANE FOCUS",
            "  ←/→           Switch active pane (left/right)",
            "  Tab           Switch active pane (alternate)",
            "",
            "TREE OPERATIONS",
            "  Shift+←/→     Collapse/expand directory or move to parent/child",
            "  Enter         View file diff (files) or toggle expand (directories)",
            "",
            "DISPLAY OPTIONS",
            "  i             Toggle showing identical files",
            "",
            "GENERAL",
            "  ?             Show this help",
            "  q/ESC         Close viewer",
            "",
            "LEGEND",
            "  =             Items are identical",
            "  !             Items are different",
            "  <             Item only exists on left side",
            "  >             Item only exists on right side",
        ]
        
        self.info_dialog.show(title, help_lines)
        if self.layer_stack:
            self.layer_stack.push(self.info_dialog)
        self.mark_dirty()
    
    def _render_details_pane(self, renderer, width: int, height: int) -> None:
        """
        Render the details pane showing information about focused files.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        import stat
        import time
        
        # Details pane occupies 4 lines above the status bar, plus 1 line for divider
        divider_y = height - 6
        details_start_y = height - 5
        details_height = 4
        
        # Draw horizontal divider above the details pane
        # Use status bar color for the divider
        status_color_pair, status_attrs = get_status_color()
        divider_line = "─" * width
        renderer.draw_text(divider_y, 0, divider_line, status_color_pair, status_attrs)
        
        # Clear the details pane area with log color
        log_color_pair, log_attrs = get_log_color("STDOUT")
        for i in range(details_height):
            renderer.draw_text(details_start_y + i, 0, " " * width, log_color_pair, log_attrs)
        
        # If no nodes or no focused node, show empty pane
        if not self.visible_nodes or self.cursor_position >= len(self.visible_nodes):
            return
        
        # Get the focused node
        focused_node = self.visible_nodes[self.cursor_position]
        relative_path = self._get_relative_path(focused_node)
        
        # Get file info for both sides
        left_info = self.left_files.get(relative_path) if relative_path else None
        right_info = self.right_files.get(relative_path) if relative_path else None
        
        # Helper function to format individual fields
        def format_field_value(file_info: Optional[FileInfo], field: str) -> str:
            """Format a specific field value."""
            if not file_info:
                if field == "path":
                    return "(not present)"
                return "-"
            
            if field == "path":
                return str(file_info.path)
            elif field == "type":
                return "Directory" if file_info.is_directory else "File"
            elif field == "size":
                if not file_info.is_accessible:
                    return "-"
                if file_info.is_directory:
                    return "-"
                size = file_info.size
                if size < 1024:
                    return f"{size}B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f}KB"
                elif size < 1024 * 1024 * 1024:
                    return f"{size / (1024 * 1024):.1f}MB"
                else:
                    return f"{size / (1024 * 1024 * 1024):.1f}GB"
            elif field == "permission":
                if not file_info.is_accessible:
                    return "-"
                try:
                    st = file_info.path.stat()
                    mode = st.st_mode
                    return stat.filemode(mode)
                except (OSError, AttributeError):
                    return "?"
            elif field == "modified":
                if not file_info.is_accessible:
                    return "-"
                try:
                    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_info.mtime))
                except (OSError, ValueError):
                    return "?"
            return "-"
        
        # Add 1-character left padding for details pane
        details_padding = 1
        details_content_width = width - details_padding
        
        # Line 0: Left path
        left_path_str = f"L Path: {format_field_value(left_info, 'path')}"
        if len(left_path_str) > details_content_width:
            left_path_str = left_path_str[:details_content_width-1] + "…"
        renderer.draw_text(details_start_y, details_padding, left_path_str, log_color_pair, log_attrs)
        
        # Line 1: Left details - Type, Size, Permission, Modified (aligned columns)
        left_type = format_field_value(left_info, "type")
        left_size = format_field_value(left_info, "size")
        left_perm = format_field_value(left_info, "permission")
        left_modified = format_field_value(left_info, "modified")
        
        # Build left line with fixed column positions
        # Format: "L Type: File      Size: 1.2MB    Permission: -rw-r--r--  Modified: 2025-12-22 10:30:45"
        left_line = f"L Type: {left_type:<10} Size: {left_size:<10} Permission: {left_perm:<12} Modified: {left_modified}"
        if len(left_line) > details_content_width:
            left_line = left_line[:details_content_width-1] + "…"
        renderer.draw_text(details_start_y + 1, details_padding, left_line, log_color_pair, log_attrs)
        
        # Line 2: Right path
        right_path_str = f"R Path: {format_field_value(right_info, 'path')}"
        if len(right_path_str) > details_content_width:
            right_path_str = right_path_str[:details_content_width-1] + "…"
        renderer.draw_text(details_start_y + 2, details_padding, right_path_str, log_color_pair, log_attrs)
        
        # Line 3: Right details - Type, Size, Permission, Modified (aligned columns)
        right_type = format_field_value(right_info, "type")
        right_size = format_field_value(right_info, "size")
        right_perm = format_field_value(right_info, "permission")
        right_modified = format_field_value(right_info, "modified")
        
        # Build right line with same column positions as left for alignment
        right_line = f"R Type: {right_type:<10} Size: {right_size:<10} Permission: {right_perm:<12} Modified: {right_modified}"
        if len(right_line) > details_content_width:
            right_line = right_line[:details_content_width-1] + "…"
        renderer.draw_text(details_start_y + 3, details_padding, right_line, log_color_pair, log_attrs)
    
    def _render_status_bar(self, renderer, width: int, height: int) -> None:
        """
        Render the status bar with position and statistics.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        status_y = height - 1
        status_color_pair, status_attrs = get_status_color()
        
        # Clear status bar area with colored background - fill entire width
        renderer.draw_text(status_y, 0, " " * width, status_color_pair, status_attrs)
        
        # Calculate statistics
        total_nodes = len(self.visible_nodes)
        current_pos = self.cursor_position + 1 if total_nodes > 0 else 0
        
        # Count differences by type
        only_left_count = 0
        only_right_count = 0
        different_count = 0
        identical_count = 0
        contains_diff_count = 0
        error_count = 0
        pending_count = 0  # Task 15.2: Count PENDING items separately
        
        # Count from all nodes in tree (not just visible)
        if self.root_node:
            only_left_count, only_right_count, different_count, \
            identical_count, contains_diff_count, error_count, pending_count = \
                self._count_differences(
                    self.root_node,
                    only_left_count, only_right_count, different_count,
                    identical_count, contains_diff_count, error_count, pending_count
                )
        
        # Build status text
        # Left side: navigation hints (or progress during scan)
        # Check if any node is currently being scanned on-demand (Task 9.2)
        scanning_nodes = []
        if self.root_node:
            self._find_scanning_nodes(self.root_node, scanning_nodes)
        
        # Check queue sizes for background scanning (Task 12.2)
        scan_queue_size = self.scan_queue.qsize()
        comparison_queue_size = self.comparison_queue.qsize()
        
        # Task 16.2: Calculate total pending work for percentage
        total_pending = scan_queue_size + comparison_queue_size
        
        # Determine scan status and update scan_in_progress flag
        if scanning_nodes:
            # Show on-demand scanning status
            animator_frame = self.progress_animator.get_current_frame()
            left_status = f" {animator_frame} Scanning directory... "
        elif scan_queue_size > 0:
            # Show background scanning progress (Task 12.2)
            animator_frame = self.progress_animator.get_current_frame()
            # Task 16.2: Show percentage if we can estimate total work
            if hasattr(self, '_initial_scan_queue_size') and self._initial_scan_queue_size > 0:
                completed = self._initial_scan_queue_size - scan_queue_size
                percentage = int((completed / self._initial_scan_queue_size) * 100)
                left_status = f" {animator_frame} Scanning... ({scan_queue_size} pending - {percentage}%) "
            else:
                left_status = f" {animator_frame} Scanning... ({scan_queue_size} pending) "
        elif comparison_queue_size > 0:
            # Show file comparison progress (Task 12.2)
            animator_frame = self.progress_animator.get_current_frame()
            # Task 16.2: Show percentage if we can estimate total work
            if hasattr(self, '_initial_comparison_queue_size') and self._initial_comparison_queue_size > 0:
                completed = self._initial_comparison_queue_size - comparison_queue_size
                percentage = int((completed / self._initial_comparison_queue_size) * 100)
                left_status = f" {animator_frame} Comparing... ({comparison_queue_size} pending - {percentage}%) "
            else:
                left_status = f" {animator_frame} Comparing... ({comparison_queue_size} pending) "
        elif self.scan_in_progress:
            # Both queues empty and no scanning nodes - scanning is complete
            self.scan_in_progress = False
            self.scan_status = "Scan complete"
            if not hasattr(self, '_scan_complete_shown'):
                self._scan_complete_shown = False
            # Show scan complete message
            left_status = " ✓ Scan complete "
            self._scan_complete_shown = True
        elif hasattr(self, '_scan_complete_shown') and not self._scan_complete_shown:
            # Show scan complete message briefly (Task 12.2)
            left_status = " ✓ Scan complete "
            self._scan_complete_shown = True
        else:
            # Normal navigation hints
            left_status = " ?:help  q:quit  ←/→:switch-pane  i:toggle-identical "
        
        # Right side: filter status and statistics
        right_parts = []
        if not self.show_identical:
            right_parts.append("[Identical Hidden]")
        
        # Add statistics
        stats_parts = []
        if only_left_count > 0:
            stats_parts.append(f"Left:{only_left_count}")
        if only_right_count > 0:
            stats_parts.append(f"Right:{only_right_count}")
        if different_count > 0:
            stats_parts.append(f"Diff:{different_count}")
        if identical_count > 0:
            stats_parts.append(f"Same:{identical_count}")
        # Task 15.2: Show pending count in status bar
        if pending_count > 0:
            stats_parts.append(f"Pending:{pending_count}")
        
        if stats_parts:
            right_parts.append(" ".join(stats_parts))
        elif not self.scan_in_progress:
            right_parts.append("No differences")
        
        # Add error count if any
        if error_count > 0:
            right_parts.append(f"Errors:{error_count}")
        
        right_status = " " + "  ".join(right_parts) + " " if right_parts else " "
        
        # Draw left status
        renderer.draw_text(status_y, 0, left_status, status_color_pair, status_attrs)
        
        # Draw right status (right-aligned)
        right_x = width - len(right_status)
        if right_x > len(left_status):
            renderer.draw_text(status_y, right_x, right_status, status_color_pair, status_attrs)
    
    def _count_differences(self, node: TreeNode, only_left: int, only_right: int,
                          different: int, identical: int, contains_diff: int,
                          errors: int, pending: int) -> tuple:
        """
        Recursively count differences in the tree.
        
        This is a helper method that counts nodes by difference type.
        Note: Python doesn't have pass-by-reference for integers, so we need
        to return the counts and update them in the caller.
        
        Args:
            node: Node to count (along with its children)
            only_left: Current count of only-left nodes
            only_right: Current count of only-right nodes
            different: Current count of content-different nodes
            identical: Current count of identical nodes
            contains_diff: Current count of contains-difference nodes
            errors: Current count of error nodes
            pending: Current count of pending nodes (Task 15.2)
            
        Returns:
            Tuple of updated counts
        """
        # Count this node (skip root)
        if node.depth > 0:
            if node.difference_type == DifferenceType.ONLY_LEFT:
                only_left += 1
            elif node.difference_type == DifferenceType.ONLY_RIGHT:
                only_right += 1
            elif node.difference_type == DifferenceType.CONTENT_DIFFERENT:
                different += 1
            elif node.difference_type == DifferenceType.IDENTICAL:
                identical += 1
            elif node.difference_type == DifferenceType.CONTAINS_DIFFERENCE:
                contains_diff += 1
            elif node.difference_type == DifferenceType.PENDING:
                # Task 15.2: Count PENDING items separately
                pending += 1
            
            # Check for errors (permission errors or comparison errors)
            relative_path = self._get_relative_path(node)
            left_info = self.left_files.get(relative_path)
            right_info = self.right_files.get(relative_path)
            
            # Check for permission/access errors
            has_access_error = (left_info and not left_info.is_accessible) or \
                              (right_info and not right_info.is_accessible)
            
            # Check for file comparison errors
            has_comparison_error = False
            if node.left_path and node.right_path:
                error_key = f"{node.left_path}|{node.right_path}"
                has_comparison_error = error_key in self.comparison_errors
            
            if has_access_error or has_comparison_error:
                errors += 1
        
        # Count children recursively
        for child in node.children:
            only_left, only_right, different, identical, contains_diff, errors, pending = \
                self._count_differences(child, only_left, only_right, different,
                                      identical, contains_diff, errors, pending)
        
        return only_left, only_right, different, identical, contains_diff, errors, pending
    
    def _find_scanning_nodes(self, node: TreeNode, scanning_nodes: List[TreeNode]) -> None:
        """
        Recursively find nodes that are currently being scanned.
        
        This helper method traverses the tree and collects all nodes
        with scan_in_progress flag set to True.
        
        Args:
            node: Node to check (along with its children)
            scanning_nodes: List to append scanning nodes to
        """
        # Check if this node is being scanned
        if node.scan_in_progress:
            scanning_nodes.append(node)
        
        # Check children recursively
        for child in node.children:
            self._find_scanning_nodes(child, scanning_nodes)
    
    def _get_relative_path(self, node: TreeNode) -> str:
        """
        Get the relative path for a node by traversing up to root.
        
        Args:
            node: Node to get path for
            
        Returns:
            Relative path string
        """
        if node.depth == 0:
            return ""
        
        parts = []
        current = node
        while current and current.depth > 0:
            parts.insert(0, current.name)
            current = current.parent
        
        return "/".join(parts)
    
    def _propagate_difference_to_parents(self, node: TreeNode) -> None:
        """
        Propagate difference status to parent directories.
        
        When a file is found to be different, all parent directories should
        be marked as CONTAINS_DIFFERENCE.
        
        Task 15.3: Helper method for updating parent directories when a file
        comparison reveals a difference.
        
        Args:
            node: Node whose difference should be propagated to parents
        """
        current = node.parent
        while current and current.depth > 0:
            # Update parent to CONTAINS_DIFFERENCE if it's not already marked as such
            if current.difference_type != DifferenceType.CONTAINS_DIFFERENCE:
                current.difference_type = DifferenceType.CONTAINS_DIFFERENCE
            current = current.parent
    
    def _build_tree_lines(self, node: TreeNode) -> str:
        """
        Build tree lines to show parent-child relationships.
        
        Uses box-drawing characters to create visual tree structure:
        - ├── for nodes with siblings below
        - └── for last child
        - │   for continuation lines
        -     for spacing
        
        Args:
            node: Node to build tree lines for
            
        Returns:
            String with tree line characters
        """
        if node.depth == 0:
            return ""
        
        lines = []
        ancestors = []
        
        # Collect all ancestors from node to root (excluding root itself)
        current = node
        while current.parent and current.parent.depth >= 0:
            ancestors.insert(0, current)
            current = current.parent
            if current.depth == 0:  # Stop at root
                break
        
        # Build tree lines for each level
        for i, ancestor in enumerate(ancestors):
            parent = ancestor.parent
            if parent is None or parent.depth < 0:
                continue
            
            # Check if this ancestor is the last child of its parent
            is_last_child = (parent.children[-1] == ancestor)
            
            if i == len(ancestors) - 1:
                # This is the node we're rendering
                if is_last_child:
                    lines.append("└─")
                else:
                    lines.append("├─")
            else:
                # This is an ancestor - show continuation or spacing
                if is_last_child:
                    lines.append("  ")  # No line needed
                else:
                    lines.append("│ ")  # Continuation line
        
        return "".join(lines)
    
    def _build_tree_lines_for_missing(self, node: TreeNode) -> str:
        """
        Build tree lines for missing items (items that don't exist on this side).
        
        For missing items, we only show vertical continuation lines from parent
        directories, not the branch connectors (├─ or └─).
        
        Uses box-drawing characters:
        - │   for continuation lines (when parent has more siblings)
        -     for spacing (when parent is last child)
        
        Args:
            node: Node to build tree lines for
            
        Returns:
            String with tree line characters (only vertical lines, no branches)
        """
        if node.depth == 0:
            return ""
        
        lines = []
        ancestors = []
        
        # Collect all ancestors from node to root (excluding root itself)
        current = node
        while current.parent and current.parent.depth >= 0:
            ancestors.insert(0, current)
            current = current.parent
            if current.depth == 0:  # Stop at root
                break
        
        # Build tree lines for each level (only continuation lines, no branches)
        for i, ancestor in enumerate(ancestors):
            parent = ancestor.parent
            if parent is None or parent.depth < 0:
                continue
            
            # Check if this ancestor is the last child of its parent
            is_last_child = (parent.children[-1] == ancestor)
            
            if i == len(ancestors) - 1:
                # This is the node we're rendering (missing item)
                # Don't show branch connector, only continuation from parent
                if is_last_child:
                    lines.append("  ")  # No line needed (last child)
                else:
                    lines.append("│ ")  # Continuation line (has siblings below)
            else:
                # This is an ancestor - show continuation or spacing
                if is_last_child:
                    lines.append("  ")  # No line needed
                else:
                    lines.append("│ ")  # Continuation line
        
        return "".join(lines)
    
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen.
        
        Returns:
            True (directory diff viewer is always full-screen)
        """
        return True
    
    def needs_redraw(self) -> bool:
        """
        Query if this layer needs redrawing.
        
        Returns:
            True if layer needs redraw, False otherwise
        """
        # Check if scanning is complete (queues empty and no active scanning)
        # This prevents the circular dependency where scan_in_progress is cleared during render
        if self.scan_in_progress:
            # Check if all work is actually done
            scanning_nodes = []
            if self.root_node:
                self._find_scanning_nodes(self.root_node, scanning_nodes)
            
            scan_queue_empty = self.scan_queue.empty()
            comparison_queue_empty = self.comparison_queue.empty()
            
            # If no active work, clear the flag
            if not scanning_nodes and scan_queue_empty and comparison_queue_empty:
                self.scan_in_progress = False
                self.scan_status = "Scan complete"
                # Mark dirty one final time to show completion, but only if not already dirty
                if not self._dirty:
                    self._dirty = True
                    return True
        
        # Return True if scanning or if there's pending work
        if self.scan_in_progress:
            return True
        
        # Check if any queues have pending work
        if not self.scan_queue.empty() or not self.comparison_queue.empty():
            return True
        
        return self._dirty
    
    def mark_dirty(self) -> None:
        """Mark this layer as needing a redraw."""
        self._dirty = True
    
    def clear_dirty(self) -> None:
        """Clear the dirty flag after rendering."""
        self._dirty = False
    
    def _stop_worker_threads(self) -> None:
        """
        Stop all worker threads gracefully.
        
        This method sets the cancellation flag and waits for all worker threads
        to finish with a timeout. It ensures proper cleanup of resources before
        the viewer closes.
        
        Thread cleanup order:
        1. Set self.cancelled = True to signal threads to stop
        2. Join scanner_thread with timeout
        3. Join comparator_thread with timeout
        4. Clean up any remaining resources
        """
        # Set cancellation flag to signal all worker threads to stop
        self.cancelled = True
        
        # Wait for scanner thread to finish (with timeout)
        if self.scanner_thread and self.scanner_thread.is_alive():
            try:
                self.scanner_thread.join(timeout=2.0)
                if self.scanner_thread.is_alive():
                    # Thread didn't stop in time - log warning
                    self.logger.warning("Scanner thread did not stop within timeout")
            except Exception as e:
                # Handle any exceptions during thread join
                self.logger.error(f"Error stopping scanner thread: {e}")
        
        # Wait for comparator thread to finish (with timeout)
        if self.comparator_thread and self.comparator_thread.is_alive():
            try:
                self.comparator_thread.join(timeout=2.0)
                if self.comparator_thread.is_alive():
                    # Thread didn't stop in time - log warning
                    self.logger.warning("Comparator thread did not stop within timeout")
            except Exception as e:
                # Handle any exceptions during thread join
                self.logger.error(f"Error stopping comparator thread: {e}")
        
        # Clean up resources
        # Clear queues to release any blocked threads
        try:
            while not self.scan_queue.empty():
                try:
                    self.scan_queue.get_nowait()
                except queue.Empty:
                    break
        except Exception:
            pass
        
        try:
            while not self.priority_queue.empty():
                try:
                    self.priority_queue.get_nowait()
                except queue.Empty:
                    break
        except Exception:
            pass
        
        try:
            while not self.comparison_queue.empty():
                try:
                    self.comparison_queue.get_nowait()
                except queue.Empty:
                    break
        except Exception:
            pass
    
    def should_close(self) -> bool:
        """
        Query if this layer wants to close.
        
        Ensures threads are stopped before closing the viewer.
        Handles timeout gracefully by logging warnings if threads don't stop in time.
        
        Returns:
            True if layer should be closed, False otherwise
        """
        # If we're about to close, stop all worker threads first
        if self._should_close:
            self._stop_worker_threads()
        
        return self._should_close
    
    def on_activate(self) -> None:
        """Called when this layer becomes the top layer."""
        self.mark_dirty()
    
    def on_deactivate(self) -> None:
        """Called when this layer is no longer the top layer."""
        # Cancel any ongoing scan
        if self.scan_in_progress and self.scanner:
            self.scanner.cancel()
            self.scan_cancelled = True
        
        # Wait for scan thread to finish (with timeout)
        if self.scanner_thread and self.scanner_thread.is_alive():
            self.scanner_thread.join(timeout=1.0)
    
    # ========================================================================
    # Scanning Implementation (Task 5.2)
    # ========================================================================
    
    def _scan_single_level(self, directory_path: Path) -> Dict[str, FileInfo]:
        """
        Scan only the immediate children of a directory (non-recursive).
        
        This method scans a single directory level, returning metadata for all
        immediate children without recursing into subdirectories. This enables
        progressive scanning where we can display top-level items immediately
        and scan deeper levels on demand.
        
        Args:
            directory_path: Path to directory to scan
            
        Returns:
            Dictionary mapping relative paths to FileInfo objects for immediate children.
            Keys are simple filenames (not full paths) since this is single-level.
            
        Raises:
            OSError: If the directory cannot be accessed
        """
        files = {}
        
        try:
            # Iterate over immediate children only (no recursion)
            for child_path in directory_path.iterdir():
                try:
                    # Get file stats
                    stat_info = child_path.stat()
                    is_accessible = True
                    error_message = None
                except (OSError, PermissionError) as e:
                    # Mark as inaccessible but continue
                    is_accessible = False
                    error_message = str(e)
                    stat_info = None
                
                # Get just the filename (not full path) for relative_path
                # since this is single-level scanning
                filename = child_path.name
                
                # Filter hidden files if show_hidden is False
                if self.file_list_manager and not self.file_list_manager.show_hidden:
                    if filename.startswith('.'):
                        continue  # Skip hidden files
                
                # Create FileInfo
                if stat_info:
                    file_info = FileInfo(
                        path=child_path,
                        relative_path=filename,
                        is_directory=child_path.is_dir(),
                        size=stat_info.st_size if not child_path.is_dir() else 0,
                        mtime=stat_info.st_mtime,
                        is_accessible=is_accessible,
                        error_message=error_message
                    )
                else:
                    # Create FileInfo for inaccessible items
                    file_info = FileInfo(
                        path=child_path,
                        relative_path=filename,
                        is_directory=False,  # Unknown, assume file
                        size=0,
                        mtime=0.0,
                        is_accessible=is_accessible,
                        error_message=error_message
                    )
                
                # Store in dictionary using filename as key
                files[filename] = file_info
                
        except (OSError, PermissionError) as e:
            # Cannot read directory contents - this is a fatal error for this directory
            # Log the error but don't raise - caller will handle empty result
            self.logger.error(f"Error scanning directory {directory_path}: {e}")
        
        return files
    
    def start_scan(self) -> None:
        """
        Start scanning both directories with progressive, top-level-first approach.
        
        This method performs an initial single-level scan of both root directories
        to enable immediate display (< 100ms), then starts worker threads for
        deeper scanning in the background.
        
        Progressive scanning workflow:
        1. Scan only top-level items from both directories (synchronous, fast)
        2. Build initial tree with PENDING status for subdirectories
        3. Mark tree as dirty to trigger immediate display
        4. Start worker threads for background scanning of deeper levels
        """
        self.scan_in_progress = True
        self.scan_progress = 0.0
        self.scan_current = 0
        self.scan_total = 0
        self.scan_status = "Scanning top level..."
        self.scan_cancelled = False
        self.scan_error = None
        self.mark_dirty()
        
        try:
            # Step 1: Scan only top-level items from both directories (synchronous)
            # This should complete in < 100ms for typical directories
            left_top_level = self._scan_single_level(self.left_path)
            right_top_level = self._scan_single_level(self.right_path)
            
            # Store top-level results
            with self.data_lock:
                self.left_files = left_top_level
                self.right_files = right_top_level
            
            # Step 2: Build initial tree with PENDING status for subdirectories
            # This creates the tree structure but marks unscanned directories as PENDING
            self.scan_status = "Building initial tree..."
            self._build_tree_with_pending()
            
            # Step 3: Mark tree as dirty to trigger immediate display
            self.scan_current = len(left_top_level) + len(right_top_level)
            self.scan_status = f"Displaying {self.scan_current} top-level items..."
            self.mark_dirty()
            
            # Step 4: Start worker threads for background scanning
            # Start directory scanner worker for progressive scanning
            self._start_scanner_worker()
            
            # Start file comparator worker for background file comparison
            self._start_comparator_worker()
            
            # Queue initial scan tasks for subdirectories
            self._queue_initial_scan_tasks()
            
        except Exception as e:
            # Handle errors during initial scan
            self.scan_in_progress = False
            self.scan_error = str(e)
            self.scan_status = "Initial scan failed"
            self.mark_dirty()
    
    def _build_tree_with_pending(self) -> None:
        """
        Build initial tree structure with PENDING status for unscanned items.
        
        This method builds a tree from the currently scanned files (top-level only),
        marking subdirectories as PENDING since their contents haven't been scanned yet.
        This allows immediate display while deeper scanning continues in background.
        """
        # Skip if no data yet
        if not self.left_files and not self.right_files:
            return
        
        # Create root node
        new_root = TreeNode(
            name="",
            left_path=str(self.left_path),
            right_path=str(self.right_path),
            is_directory=True,
            difference_type=DifferenceType.PENDING,
            depth=0,
            is_expanded=True,
            children=[],
            parent=None,
            children_scanned=True,  # Root level is scanned
            content_compared=False,
            scan_in_progress=False
        )
        
        # Get all unique child names from both sides
        all_child_names = set(self.left_files.keys()) | set(self.right_files.keys())
        
        # Create TreeNode for each child
        for child_name in sorted(all_child_names):
            left_info = self.left_files.get(child_name)
            right_info = self.right_files.get(child_name)
            
            # Determine if this is a directory
            is_directory = (left_info and left_info.is_directory) or \
                          (right_info and right_info.is_directory)
            
            # Determine difference type
            if left_info and not right_info:
                diff_type = DifferenceType.ONLY_LEFT
                content_compared = True  # One-sided files don't need comparison
            elif right_info and not left_info:
                diff_type = DifferenceType.ONLY_RIGHT
                content_compared = True  # One-sided files don't need comparison
            elif is_directory:
                diff_type = DifferenceType.PENDING  # Directory not yet scanned
                content_compared = False
            else:
                diff_type = DifferenceType.PENDING  # File not yet compared
                content_compared = False
            
            # Create child node
            child_node = TreeNode(
                name=child_name,
                left_path=left_info.path if left_info else None,
                right_path=right_info.path if right_info else None,
                is_directory=is_directory,
                difference_type=diff_type,
                depth=1,
                is_expanded=False,
                children=[],
                parent=new_root,
                children_scanned=False,  # Subdirectories not yet scanned
                content_compared=content_compared,  # One-sided files already "compared"
                scan_in_progress=False
            )
            
            new_root.children.append(child_node)
        
        # Sort children: directories first, then files
        new_root.children.sort(key=lambda child: (
            not child.is_directory,
            child.name.lower()
        ))
        
        # Queue file comparisons for top-level files
        self._queue_file_comparisons_for_node(new_root)
        
        # Update root node (thread-safe)
        with self.tree_lock:
            self.root_node = new_root
            
            # Initialize visible nodes (start with root expanded)
            if self.root_node:
                self.root_node.is_expanded = True
                self._update_visible_nodes()
    
    def _queue_file_comparisons_for_node(self, node: TreeNode) -> None:
        """
        Queue file comparison tasks for all files in a node's children.
        
        This method examines a node's children and queues comparison tasks
        for any files that exist on both sides.
        
        Args:
            node: The node whose children should be queued for comparison
        """
        for child in node.children:
            # Only queue files (not directories) that exist on both sides
            if not child.is_directory and child.left_path and child.right_path:
                # Build relative path for this file
                if node.depth == 0:
                    # Direct child of root
                    file_relative_path = child.name
                else:
                    # Build full relative path by traversing up to root
                    path_parts = [child.name]
                    current = node
                    while current and current.depth > 0:
                        path_parts.insert(0, current.name)
                        current = current.parent
                    file_relative_path = "/".join(path_parts)
                
                # Create comparison task
                comparison_task = ComparisonTask(
                    left_path=child.left_path,
                    right_path=child.right_path,
                    relative_path=file_relative_path,
                    priority=10,  # Normal priority
                    is_visible=False  # Will be updated by priority system
                )
                
                # Add to comparison queue
                with self.queue_lock:
                    self.comparison_queue.put(comparison_task)
    
    # ========================================================================
    # Progressive Scanning Worker Threads (Task 5)
    # ========================================================================
    
    def _start_scanner_worker(self) -> None:
        """
        Create and start the directory scanner worker thread.
        
        This method initializes the scanner_thread and starts it running
        the _directory_scanner_worker method. The thread is marked as a
        daemon thread so it won't prevent the program from exiting.
        """
        # Only start if not already running
        if self.scanner_thread and self.scanner_thread.is_alive():
            return
        
        # Reset cancelled flag
        self.cancelled = False
        
        # Create and start scanner thread
        self.scanner_thread = threading.Thread(
            target=self._directory_scanner_worker,
            daemon=True,
            name="DirectoryScanner"
        )
        self.scanner_thread.start()
    
    def _start_comparator_worker(self) -> None:
        """
        Create and start the file comparator worker thread.
        
        This method initializes the comparator_thread and starts it running
        the _file_comparator_worker method. The thread is marked as a
        daemon thread so it won't prevent the program from exiting.
        """
        # Only start if not already running
        if self.comparator_thread and self.comparator_thread.is_alive():
            return
        
        # Reset cancelled flag (if not already reset by scanner worker)
        self.cancelled = False
        
        # Create and start comparator thread
        self.comparator_thread = threading.Thread(
            target=self._file_comparator_worker,
            daemon=True,
            name="FileComparator"
        )
        self.comparator_thread.start()
    
    def _queue_initial_scan_tasks(self) -> None:
        """
        Queue initial scan tasks for subdirectories in the root.
        
        This method examines the root node's children and queues directories
        that exist on BOTH sides for automatic background scanning. One-sided
        directories (only on left or right) are NOT queued - they will be
        scanned lazily when the user expands them (Task 10.1).
        
        This provides a balance between:
        - Automatic scanning of both-sided directories (to detect differences)
        - Lazy scanning of one-sided directories (to avoid unnecessary work)
        """
        if not self.root_node:
            return
        
        # Queue scan tasks for subdirectories that exist on both sides
        with self.tree_lock:
            for child in self.root_node.children:
                if child.is_directory and not child.children_scanned:
                    # Check if directory exists on both sides (Task 10.1)
                    exists_left = child.left_path is not None
                    exists_right = child.right_path is not None
                    
                    # Only queue if exists on BOTH sides
                    if not (exists_left and exists_right):
                        # One-sided directory - skip automatic scanning
                        # Will be scanned on-demand when user expands it
                        continue
                    
                    # Create scan task for this both-sided directory
                    scan_task = ScanTask(
                        left_path=child.left_path,
                        right_path=child.right_path,
                        relative_path=child.name,
                        priority=10,  # Normal priority
                        is_visible=False  # Will be updated by priority system
                    )
                    
                    # Add to scan queue
                    with self.queue_lock:
                        self.scan_queue.put(scan_task)
    
    def _directory_scanner_worker(self) -> None:
        """
        Worker thread that progressively scans directories breadth-first.
        
        This method runs in a background thread, continuously pulling scan tasks
        from the scan_queue and processing them. For each directory:
        1. Scans only immediate children (single level)
        2. Updates file dictionaries with thread-safe locking
        3. Updates tree structure to include new children
        4. Adds child directories to scan_queue for breadth-first traversal
        5. Marks tree as dirty to trigger UI update
        
        The worker checks the cancelled flag periodically to support graceful shutdown.
        """
        try:
            while not self.cancelled:
                try:
                    # Get next scan task from queue (with timeout to check cancelled flag)
                    task = self.scan_queue.get(timeout=0.1)
                except queue.Empty:
                    # No tasks available, check cancelled flag and continue
                    continue
                
                # Check if cancelled before processing
                if self.cancelled:
                    break
                
                # Scan both sides (if they exist)
                left_children = {}
                right_children = {}
                
                # Scan left side
                if task.left_path:
                    try:
                        left_children = self._scan_single_level(task.left_path)
                    except Exception as e:
                        # Log error but continue
                        self.logger.error(f"Error scanning left path {task.left_path}: {e}")
                
                # Scan right side
                if task.right_path:
                    try:
                        right_children = self._scan_single_level(task.right_path)
                    except Exception as e:
                        # Log error but continue
                        self.logger.error(f"Error scanning right path {task.right_path}: {e}")
                
                # Update file dictionaries with thread-safe locking
                with self.data_lock:
                    # Add children to file dictionaries with proper relative paths
                    for filename, file_info in left_children.items():
                        # Build full relative path
                        if task.relative_path:
                            full_relative_path = f"{task.relative_path}/{filename}"
                        else:
                            full_relative_path = filename
                        
                        # Update file_info with correct relative path
                        file_info.relative_path = full_relative_path
                        
                        # Add to dictionary
                        self.left_files[full_relative_path] = file_info
                    
                    for filename, file_info in right_children.items():
                        # Build full relative path
                        if task.relative_path:
                            full_relative_path = f"{task.relative_path}/{filename}"
                        else:
                            full_relative_path = filename
                        
                        # Update file_info with correct relative path
                        file_info.relative_path = full_relative_path
                        
                        # Add to dictionary
                        self.right_files[full_relative_path] = file_info
                
                # Update tree structure to include new children
                # Find the node corresponding to this task and update it
                self._update_tree_node(task.relative_path, left_children, right_children)
                
                # Queue child directories for background scanning (Task 10.1)
                # Only queue directories that exist on BOTH sides for automatic scanning.
                # One-sided directories are scanned lazily when user expands them.
                all_child_dirs = set()
                for filename, file_info in left_children.items():
                    if file_info.is_directory:
                        all_child_dirs.add(filename)
                for filename, file_info in right_children.items():
                    if file_info.is_directory:
                        all_child_dirs.add(filename)
                
                # Create scan tasks for child directories that exist on both sides
                for child_dir_name in all_child_dirs:
                    # Check if directory exists on both sides
                    exists_left = child_dir_name in left_children
                    exists_right = child_dir_name in right_children
                    
                    # Only queue if exists on BOTH sides (Task 10.1)
                    if not (exists_left and exists_right):
                        # One-sided directory - skip automatic scanning
                        # Will be scanned on-demand when user expands it
                        continue
                    
                    # Build paths for child directory
                    child_left_path = left_children[child_dir_name].path
                    child_right_path = right_children[child_dir_name].path
                    
                    # Build relative path for child
                    if task.relative_path:
                        child_relative_path = f"{task.relative_path}/{child_dir_name}"
                    else:
                        child_relative_path = child_dir_name
                    
                    # Create scan task for child directory
                    child_task = ScanTask(
                        left_path=child_left_path,
                        right_path=child_right_path,
                        relative_path=child_relative_path,
                        priority=task.priority,  # Inherit priority from parent
                        is_visible=False  # Will be updated by priority system
                    )
                    
                    # Add to scan queue
                    with self.queue_lock:
                        self.scan_queue.put(child_task)
                
                # Mark tree as dirty to trigger UI update
                self.mark_dirty()
                
                # Mark task as done
                self.scan_queue.task_done()
                
        except Exception as e:
            # Log unexpected errors and set error flag to notify main thread
            error_msg = f"Directory scanner worker error: {e}"
            self.logger.error(error_msg)
            import traceback
            traceback.print_exc()
            
            # Set error flag to notify main thread
            self.worker_error = error_msg
            self.mark_dirty()  # Trigger UI update to show error
    
    def _start_directory_scanner_worker(self) -> None:
        """
        Create and start the directory scanner worker thread.
        
        This method initializes the scanner thread that will process scan tasks
        from the scan_queue in the background. The thread is marked as a daemon
        so it won't prevent the application from exiting.
        """
        # Create scanner thread
        self.scanner_thread = threading.Thread(
            target=self._directory_scanner_worker,
            name="DirectoryScanner",
            daemon=True
        )
        
        # Start the thread
        self.scanner_thread.start()
    
    def _update_tree_node(self, relative_path: str, 
                         left_children: Dict[str, FileInfo],
                         right_children: Dict[str, FileInfo]) -> None:
        """
        Update a tree node with newly scanned children (thread-safe).
        
        This method finds the node corresponding to the given relative path,
        updates its children_scanned flag, and adds new child nodes to the tree.
        All tree modifications are protected by tree_lock for thread safety.
        
        Args:
            relative_path: Relative path of the node to update (empty string for root)
            left_children: Dictionary of children from left directory
            right_children: Dictionary of children from right directory
        """
        with self.tree_lock:
            # Find the node to update
            if not relative_path:
                # Updating root node
                target_node = self.root_node
            else:
                # Find node by traversing tree
                target_node = self._find_node_by_path(self.root_node, relative_path)
            
            if not target_node:
                # Node not found - this shouldn't happen but handle gracefully
                self.logger.warning(f"Could not find node for path '{relative_path}'")
                return
            
            # Mark node as scanned
            target_node.children_scanned = True
            target_node.scan_in_progress = False
            
            # Get all unique child names from both sides
            all_child_names = set(left_children.keys()) | set(right_children.keys())
            
            # Create a map of existing children by name
            existing_children_map = {child.name: child for child in target_node.children}
            
            # Update existing children and create new ones as needed
            for child_name in all_child_names:
                left_info = left_children.get(child_name)
                right_info = right_children.get(child_name)
                
                # Determine if this is a directory
                is_directory = (left_info and left_info.is_directory) or \
                              (right_info and right_info.is_directory)
                
                # Check if this child already exists
                existing_child = existing_children_map.get(child_name)
                
                if existing_child:
                    # Update existing child node (preserve its classification and state)
                    if left_info:
                        existing_child.left_path = left_info.path
                    if right_info:
                        existing_child.right_path = right_info.path
                    # Don't reset children_scanned, difference_type, or other state
                else:
                    # Create new child node only if it doesn't exist
                    child_node = TreeNode(
                        name=child_name,
                        left_path=left_info.path if left_info else None,
                        right_path=right_info.path if right_info else None,
                        is_directory=is_directory,
                        difference_type=DifferenceType.PENDING,  # Will be classified later
                        depth=target_node.depth + 1,
                        is_expanded=False,
                        children=[],
                        parent=target_node,
                        children_scanned=False,
                        content_compared=False,
                        scan_in_progress=False
                    )
                    # Add new child to the list
                    target_node.children.append(child_node)
            
            # Sort children: directories first, then files, alphabetically
            target_node.children.sort(key=lambda child: (
                not child.is_directory,  # False (directories) sorts before True (files)
                child.name.lower()       # Case-insensitive alphabetical order
            ))
            
            # Queue file comparison tasks for any new files
            self._queue_file_comparisons_for_node(target_node)
            
            # Classify the updated node and its children
            self._classify_node_and_children(target_node)
            
            # Update parent classifications to propagate changes upward
            self._update_parent_classifications(target_node)
            
            # Update visible nodes if this node is expanded
            if target_node.is_expanded:
                self._update_visible_nodes()
    
    def _find_node_by_path(self, root: TreeNode, relative_path: str) -> Optional[TreeNode]:
        """
        Find a node in the tree by its relative path.
        
        Args:
            root: Root node to start search from
            relative_path: Relative path to find (e.g., "dir1/dir2/file.txt")
            
        Returns:
            TreeNode if found, None otherwise
        """
        if not relative_path:
            return root
        
        # Split path into components
        parts = relative_path.split('/')
        
        # Traverse tree following path components
        current_node = root
        for part in parts:
            # Find child with matching name
            found = False
            for child in current_node.children:
                if child.name == part:
                    current_node = child
                    found = True
                    break
            
            if not found:
                # Path component not found
                return None
        
        return current_node
    
    def _classify_node_and_children(self, node: TreeNode) -> None:
        """
        Classify a node and its children based on their difference types.
        
        This is similar to DiffEngine.classify_node but works on a single node
        and its immediate children, used during progressive tree updates.
        
        Args:
            node: Node to classify (along with its children)
        """
        # First classify all children
        for child in node.children:
            child.difference_type = self._classify_single_node(child)
        
        # Then classify the parent node
        node.difference_type = self._classify_single_node(node)
    
    def _classify_single_node(self, node: TreeNode) -> DifferenceType:
        """
        Classify a single node's difference type.
        
        Args:
            node: Node to classify
            
        Returns:
            DifferenceType classification
        """
        # Root node is special - classify based on children
        if node.depth == 0:
            # Apply same logic as regular directories
            has_difference = False
            has_pending = False
            
            for child in node.children:
                if child.difference_type == DifferenceType.PENDING:
                    has_pending = True
                elif child.difference_type != DifferenceType.IDENTICAL:
                    # Found a real difference
                    has_difference = True
                    break
            
            # If any real difference found, mark as CONTAINS_DIFFERENCE immediately
            if has_difference:
                return DifferenceType.CONTAINS_DIFFERENCE
            
            # If all children are identical, mark as IDENTICAL
            if not has_pending:
                return DifferenceType.IDENTICAL
            
            # Otherwise, still have pending children and no differences found yet
            return DifferenceType.PENDING
        
        # Check if node exists on both sides
        exists_left = node.left_path is not None
        exists_right = node.right_path is not None
        
        # Only on left side
        if exists_left and not exists_right:
            return DifferenceType.ONLY_LEFT
        
        # Only on right side
        if exists_right and not exists_left:
            return DifferenceType.ONLY_RIGHT
        
        # Exists on both sides
        if node.is_directory:
            # For directories, check if any children have differences
            # If directory has no children yet (not scanned), mark as PENDING
            if not node.children_scanned and len(node.children) == 0:
                # Not yet scanned and no children
                return DifferenceType.PENDING
            
            # Check for actual differences (not just pending)
            has_difference = False
            has_pending = False
            
            for child in node.children:
                if child.difference_type == DifferenceType.PENDING:
                    has_pending = True
                elif child.difference_type != DifferenceType.IDENTICAL:
                    # Found a real difference (ONLY_LEFT, ONLY_RIGHT, CONTENT_DIFFERENT, CONTAINS_DIFFERENCE)
                    has_difference = True
                    break  # Can immediately mark as CONTAINS_DIFFERENCE
            
            # If any real difference found, mark as CONTAINS_DIFFERENCE immediately
            if has_difference:
                return DifferenceType.CONTAINS_DIFFERENCE
            
            # If all children are identical, mark as IDENTICAL
            if not has_pending:
                return DifferenceType.IDENTICAL
            
            # Otherwise, still have pending children and no differences found yet
            return DifferenceType.PENDING
        else:
            # For files, compare content
            if not node.content_compared:
                # Not yet compared
                return DifferenceType.PENDING
            
            # Use DiffEngine to compare file content
            engine = DiffEngine(self.left_files, self.right_files)
            if engine.compare_file_content(node.left_path, node.right_path):
                return DifferenceType.IDENTICAL
            else:
                return DifferenceType.CONTENT_DIFFERENT
    
    def _mark_directories_pending(self, node: TreeNode) -> None:
        """
        Recursively mark directory nodes as PENDING and set children_scanned = False.
        
        This indicates that the directory exists but its contents haven't been
        fully scanned yet. Files are left with their current classification.
        
        Args:
            node: Node to process (along with its children)
        """
        # Process children first (post-order traversal)
        for child in node.children:
            self._mark_directories_pending(child)
        
        # Mark directories as PENDING if they haven't been scanned
        if node.is_directory and node.depth > 0:  # Don't mark root as PENDING
            # Directory hasn't been scanned yet
            node.difference_type = DifferenceType.PENDING
            node.children_scanned = False
        
        # Files keep their current classification (IDENTICAL, CONTENT_DIFFERENT, etc.)
        # but mark as not yet compared
        if not node.is_directory:
            node.content_compared = False
    
    def _scan_worker(self) -> None:
        """
        Worker thread function that performs the directory scan.
        
        This runs in a background thread to avoid blocking the UI. Results
        are stored in instance variables and the UI is marked dirty to trigger
        a redraw.
        """
        try:
            # Perform the scan
            left_files, right_files = self.scanner.scan()
            
            # Check if cancelled
            if self.scan_cancelled:
                self.scan_in_progress = False
                self.scan_status = "Scan cancelled by user"
                self.scan_progress = 0.0
                self.mark_dirty()
                # Don't close viewer immediately - let user see cancellation message
                # The viewer will close when they press ESC again or after a brief delay
                return
            
            # Store results
            self.left_files = left_files
            self.right_files = right_files
            
            # Build tree structure
            self.scan_status = "Building tree structure..."
            self.mark_dirty()
            self._build_tree()
            
            # Update state
            self.scan_in_progress = False
            self.scan_progress = 1.0
            self.scan_status = "Scan complete"
            self.mark_dirty()
            
        except Exception as e:
            # Handle scan errors and set error flag to notify main thread
            self.scan_in_progress = False
            self.scan_error = str(e)
            self.scan_status = "Scan failed"
            self.worker_error = f"Scan worker error: {e}"
            self.mark_dirty()
    
    def _on_scan_progress(self, current: int, total: int, status: str) -> None:
        """
        Progress callback for directory scanning.
        
        This is called by DirectoryScanner to report progress. It updates
        the UI state and marks the layer dirty to trigger a redraw.
        
        Args:
            current: Current number of items processed
            total: Total number of items (estimate)
            status: Status message describing current operation
        """
        # Update progress
        if total > 0:
            self.scan_progress = min(1.0, current / total)
        else:
            # For indeterminate progress, show a small value to indicate activity
            self.scan_progress = 0.0
        
        # Store current and total for display
        self.scan_current = current
        self.scan_total = total
        self.scan_status = status
        
        # Mark dirty to trigger redraw (which will update tree if needed)
        self.mark_dirty()
    
    def _build_tree(self) -> None:
        """
        Build the tree structure from scan results.
        
        This method uses DiffEngine to construct the unified tree and
        initializes the visible nodes list for rendering.
        Thread-safe: Can be called during scanning to show progressive results.
        """
        # Skip if no data yet
        if not self.left_files and not self.right_files:
            return
        
        # Create diff engine
        engine = DiffEngine(self.left_files, self.right_files)
        
        # Build tree
        new_root = engine.build_tree()
        
        # Store comparison errors for display
        self.comparison_errors = engine.comparison_errors
        
        # Update root node (thread-safe)
        self.root_node = new_root
        
        # Initialize visible nodes (start with root expanded)
        if self.root_node:
            self.root_node.is_expanded = True
            self._update_visible_nodes()
        
        # Task 16.2: Track initial queue sizes for percentage calculation
        # Only set these once at the start of scanning
        if not hasattr(self, '_initial_scan_queue_size'):
            self._initial_scan_queue_size = self.scan_queue.qsize()
        if not hasattr(self, '_initial_comparison_queue_size'):
            self._initial_comparison_queue_size = self.comparison_queue.qsize()
    
    def _update_visible_nodes(self) -> None:
        """
        Update the visible_nodes list based on current expansion state.
        
        This method flattens the tree into a list of visible nodes for
        efficient rendering. Only expanded directories show their children.
        Respects the show_identical filter to optionally hide identical files.
        """
        self.visible_nodes = []
        self.node_index_map = {}
        
        if self.root_node:
            self._flatten_tree(self.root_node)
    
    def _flatten_tree(self, node: TreeNode) -> None:
        """
        Recursively flatten the tree into visible_nodes list.
        
        Args:
            node: Node to flatten (along with its visible children)
        """
        # Don't add root node itself to visible list
        if node.depth > 0:
            # Apply show_identical filter
            # Task 15.1: Don't hide PENDING files (they might become different)
            # When hiding identical files, also consider PENDING but don't hide them
            if self.show_identical or node.difference_type != DifferenceType.IDENTICAL:
                index = len(self.visible_nodes)
                self.visible_nodes.append(node)
                self.node_index_map[id(node)] = index
        
        # Add children if node is expanded
        if node.is_expanded:
            for child in node.children:
                self._flatten_tree(child)
    
    def _ensure_cursor_visible(self, display_height: int) -> None:
        """
        Adjust scroll_offset to ensure cursor_position is visible in the viewport.
        
        This method should be called after any operation that changes cursor_position
        to ensure the cursor remains visible on screen.
        
        Args:
            display_height: Height of the display area for scroll adjustment
        """
        # If cursor is above visible area, scroll up
        if self.cursor_position < self.scroll_offset:
            self.scroll_offset = self.cursor_position
        # If cursor is below visible area, scroll down
        elif self.cursor_position >= self.scroll_offset + display_height:
            self.scroll_offset = self.cursor_position - display_height + 1
    
    def _jump_to_previous_difference(self, display_height: int) -> None:
        """
        Jump cursor to the previous node with a difference.
        
        Searches backwards from current position for a node that is not identical.
        Adjusts scroll position to keep the cursor visible.
        
        Args:
            display_height: Height of the display area for scroll adjustment
        """
        if not self.visible_nodes:
            return
        
        # Search backwards from current position
        for i in range(self.cursor_position - 1, -1, -1):
            node = self.visible_nodes[i]
            if node.difference_type != DifferenceType.IDENTICAL:
                self.cursor_position = i
                # Ensure cursor is visible
                self._ensure_cursor_visible(display_height)
                self.mark_dirty()
                return
        
        # No previous difference found - stay at current position
    
    def _jump_to_next_difference(self, display_height: int) -> None:
        """
        Jump cursor to the next node with a difference.
        
        Searches forwards from current position for a node that is not identical.
        Adjusts scroll position to keep the cursor visible.
        
        Args:
            display_height: Height of the display area for scroll adjustment
        """
        if not self.visible_nodes:
            return
        
        # Search forwards from current position
        for i in range(self.cursor_position + 1, len(self.visible_nodes)):
            node = self.visible_nodes[i]
            if node.difference_type != DifferenceType.IDENTICAL:
                self.cursor_position = i
                # Ensure cursor is visible
                self._ensure_cursor_visible(display_height)
                self.mark_dirty()
                return
        
        # No next difference found - stay at current position
    
    # ========================================================================
    # Tree Structure Management (Task 6.1)
    # ========================================================================
    
    def expand_node(self, node_index: int) -> None:
        """
        Expand a directory node to show its children.
        
        This method updates the visible_nodes list to include the children
        of the specified node. If the node hasn't been scanned yet, it performs
        an immediate on-demand scan in the main thread to provide instant feedback.
        
        Args:
            node_index: Index of the node to expand in visible_nodes list
        """
        if node_index < 0 or node_index >= len(self.visible_nodes):
            return
        
        node = self.visible_nodes[node_index]
        
        # Only expand directories that aren't already expanded
        if not node.is_directory or node.is_expanded:
            return
        
        # Check if node hasn't been scanned yet (Task 9.1)
        if not node.children_scanned:
            # Set scan_in_progress flag to show loading indicator
            node.scan_in_progress = True
            self.mark_dirty()  # Trigger redraw to show "scanning..." indicator
            
            # Force immediate render to show the indicator
            if self.renderer:
                self.render(self.renderer)
            
            # Perform immediate single-level scan in main thread
            left_children = {}
            right_children = {}
            
            # Scan left directory if it exists
            if node.left_path and node.left_path.is_dir():
                try:
                    left_children = self._scan_single_level(node.left_path)
                except Exception as e:
                    self.logger.error(f"Error scanning left directory {node.left_path}: {e}")
            
            # Scan right directory if it exists
            if node.right_path and node.right_path.is_dir():
                try:
                    right_children = self._scan_single_level(node.right_path)
                except Exception as e:
                    self.logger.error(f"Error scanning right directory {node.right_path}: {e}")
            
            # Update tree with new children (thread-safe)
            with self.tree_lock:
                # Get all unique child names from both sides
                all_child_names = set(left_children.keys()) | set(right_children.keys())
                
                # Create child nodes for each unique name
                new_children = []
                for child_name in sorted(all_child_names):
                    left_info = left_children.get(child_name)
                    right_info = right_children.get(child_name)
                    
                    # Determine if this is a directory
                    is_directory = (left_info and left_info.is_directory) or \
                                  (right_info and right_info.is_directory)
                    
                    # Determine difference type and content_compared status
                    if left_info and not right_info:
                        diff_type = DifferenceType.ONLY_LEFT
                        content_compared = True  # One-sided files don't need comparison
                    elif right_info and not left_info:
                        diff_type = DifferenceType.ONLY_RIGHT
                        content_compared = True  # One-sided files don't need comparison
                    else:
                        diff_type = DifferenceType.PENDING  # Will be classified later
                        content_compared = False
                    
                    # Create child node
                    child_node = TreeNode(
                        name=child_name,
                        left_path=left_info.path if left_info else None,
                        right_path=right_info.path if right_info else None,
                        is_directory=is_directory,
                        difference_type=diff_type,
                        depth=node.depth + 1,
                        is_expanded=False,
                        children=[],
                        parent=node,
                        children_scanned=False,
                        content_compared=content_compared,
                        scan_in_progress=False
                    )
                    
                    new_children.append(child_node)
                
                # Replace node's children with new children
                node.children = new_children
                
                # Sort children: directories first, then files, alphabetically
                node.children.sort(key=lambda child: (
                    not child.is_directory,  # False (directories) sorts before True (files)
                    child.name.lower()       # Case-insensitive alphabetical order
                ))
                
                # Mark node as scanned and no longer in progress
                node.children_scanned = True
                node.scan_in_progress = False
                
                # Classify the updated node and its children
                self._classify_node_and_children(node)
        
        # Remember the node we're expanding (by identity, not index)
        expanding_node_id = id(node)
        
        # Mark node as expanded
        node.is_expanded = True
        
        # Collect all children recursively (respecting their expansion state)
        children_to_insert = []
        self._collect_visible_children(node, children_to_insert)
        
        # Insert children after the parent node
        insert_position = node_index + 1
        self.visible_nodes[insert_position:insert_position] = children_to_insert
        
        # Rebuild node_index_map for efficient lookups
        self._rebuild_node_index_map()
        
        # Update cursor position to stay on the same node
        # The node we expanded is still at the same position (node_index)
        # But if cursor was below it, we need to adjust for inserted children
        if self.cursor_position > node_index:
            # Cursor was below the expanded node, adjust for inserted children
            self.cursor_position += len(children_to_insert)
        
        # Ensure scroll position keeps the cursor visible
        height, width = self.renderer.get_dimensions()
        display_height = height - 7
        
        # If cursor is below visible area, adjust scroll
        if self.cursor_position >= self.scroll_offset + display_height:
            self.scroll_offset = self.cursor_position - display_height + 1
        
        # Mark dirty to trigger redraw
        self.mark_dirty()
        
        # Update priorities when viewport changes due to expansion
        self._update_priorities()
    
    def collapse_node(self, node_index: int) -> None:
        """
        Collapse a directory node to hide its children.
        
        This method updates the visible_nodes list to remove all descendants
        of the specified node. The cursor position is adjusted to stay on
        a logical node after collapse.
        
        Args:
            node_index: Index of the node to collapse in visible_nodes list
        """
        if node_index < 0 or node_index >= len(self.visible_nodes):
            return
        
        node = self.visible_nodes[node_index]
        
        # Only collapse directories that are expanded
        if not node.is_directory or not node.is_expanded:
            return
        
        # Remember which node the cursor is on (by identity)
        cursor_node_id = id(self.visible_nodes[self.cursor_position]) if self.cursor_position < len(self.visible_nodes) else None
        
        # Mark node as collapsed
        node.is_expanded = False
        
        # Find all descendants to remove
        descendants_to_remove = []
        self._collect_all_descendants(node, descendants_to_remove)
        descendant_ids = {id(d) for d in descendants_to_remove}
        
        # Count how many descendants are before the cursor
        descendants_before_cursor = 0
        for i in range(node_index + 1, self.cursor_position):
            if i < len(self.visible_nodes) and id(self.visible_nodes[i]) in descendant_ids:
                descendants_before_cursor += 1
        
        # Check if cursor is on a descendant that will be removed
        cursor_on_descendant = cursor_node_id in descendant_ids
        
        # Remove descendants from visible_nodes
        # Work backwards to avoid index shifting issues
        for descendant in reversed(descendants_to_remove):
            desc_id = id(descendant)
            if desc_id in self.node_index_map:
                desc_index = self.node_index_map[desc_id]
                if desc_index < len(self.visible_nodes):
                    self.visible_nodes.pop(desc_index)
        
        # Rebuild node_index_map for efficient lookups
        self._rebuild_node_index_map()
        
        # Adjust cursor position
        if cursor_on_descendant:
            # Cursor was on a removed descendant, move to the collapsed parent
            self.cursor_position = node_index
        elif self.cursor_position > node_index:
            # Cursor was below the collapsed node, adjust for removed descendants
            self.cursor_position -= descendants_before_cursor
        
        # Ensure cursor is within bounds
        if self.cursor_position >= len(self.visible_nodes):
            self.cursor_position = max(0, len(self.visible_nodes) - 1)
        
        # Ensure cursor is visible in scroll area
        height, width = self.renderer.get_dimensions()
        display_height = height - 7
        
        # If cursor is above visible area, adjust scroll
        if self.cursor_position < self.scroll_offset:
            self.scroll_offset = self.cursor_position
        # If cursor is below visible area, adjust scroll
        elif self.cursor_position >= self.scroll_offset + display_height:
            self.scroll_offset = self.cursor_position - display_height + 1
        
        # Mark dirty to trigger redraw
        self.mark_dirty()
        
        # Update priorities when viewport changes due to collapse
        self._update_priorities()
    
    def _collect_visible_children(self, node: TreeNode, result: List[TreeNode]) -> None:
        """
        Recursively collect all visible children of a node.
        
        This respects the expansion state of child directories - only children
        of expanded directories are included. Also respects the show_identical filter.
        
        Args:
            node: Parent node whose children to collect
            result: List to append visible children to
        """
        for child in node.children:
            # Apply show_identical filter (same logic as _flatten_tree)
            if self.show_identical or child.difference_type != DifferenceType.IDENTICAL:
                result.append(child)
            
            # If child is an expanded directory, recursively collect its children
            if child.is_directory and child.is_expanded:
                self._collect_visible_children(child, result)
    
    def _collect_all_descendants(self, node: TreeNode, result: List[TreeNode]) -> None:
        """
        Recursively collect all descendants of a node.
        
        This collects ALL descendants regardless of expansion state, used
        when collapsing a node to remove all its visible descendants.
        
        Args:
            node: Parent node whose descendants to collect
            result: List to append descendants to
        """
        for child in node.children:
            result.append(child)
            
            # Recursively collect all descendants
            if child.is_directory:
                self._collect_all_descendants(child, result)
    
    def _rebuild_node_index_map(self) -> None:
        """
        Rebuild the node_index_map after modifying visible_nodes.
        
        This ensures the map stays synchronized with the visible_nodes list
        for efficient lookups during navigation and rendering.
        """
        self.node_index_map.clear()
        for index, node in enumerate(self.visible_nodes):
            self.node_index_map[id(node)] = index
    
    def _classify_node_quick(self, node: TreeNode) -> DifferenceType:
        """
        Quickly classify a node's difference type without deep comparison.
        
        This is a lightweight version of classify_node that doesn't perform
        file content comparison. It's used during progressive scanning to
        provide quick visual feedback.
        
        Args:
            node: TreeNode to classify
            
        Returns:
            DifferenceType classification
        """
        # Root node is special - classify based on children
        if node.depth == 0:
            # Apply same logic as regular directories
            has_difference = False
            has_pending = False
            
            for child in node.children:
                if child.difference_type == DifferenceType.PENDING:
                    has_pending = True
                elif child.difference_type != DifferenceType.IDENTICAL:
                    # Found a real difference
                    has_difference = True
                    break
            
            # If any real difference found, mark as CONTAINS_DIFFERENCE immediately
            if has_difference:
                return DifferenceType.CONTAINS_DIFFERENCE
            
            # If all children are identical, mark as IDENTICAL
            if not has_pending:
                return DifferenceType.IDENTICAL
            
            # Otherwise, still have pending children and no differences found yet
            return DifferenceType.PENDING
        
        # Check if node exists on both sides
        exists_left = node.left_path is not None
        exists_right = node.right_path is not None
        
        # Only on left side
        if exists_left and not exists_right:
            return DifferenceType.ONLY_LEFT
        
        # Only on right side
        if exists_right and not exists_left:
            return DifferenceType.ONLY_RIGHT
        
        # Exists on both sides
        if node.is_directory:
            # For directories, check if any children have differences
            # If directory has no children yet (not scanned), mark as PENDING
            if not node.children_scanned and len(node.children) == 0:
                # Not yet scanned and no children
                return DifferenceType.PENDING
            
            # Check for actual differences (not just pending)
            has_difference = False
            has_pending = False
            
            for child in node.children:
                if child.difference_type == DifferenceType.PENDING:
                    has_pending = True
                elif child.difference_type != DifferenceType.IDENTICAL:
                    # Found a real difference (ONLY_LEFT, ONLY_RIGHT, CONTENT_DIFFERENT, CONTAINS_DIFFERENCE)
                    has_difference = True
                    break  # Can immediately mark as CONTAINS_DIFFERENCE
            
            # If any real difference found, mark as CONTAINS_DIFFERENCE immediately
            if has_difference:
                return DifferenceType.CONTAINS_DIFFERENCE
            
            # If all children are identical, mark as IDENTICAL
            if not has_pending:
                return DifferenceType.IDENTICAL
            
            # Otherwise, still have pending children and no differences found yet
            return DifferenceType.PENDING
        else:
            # For files, mark as PENDING (will be compared by file comparator worker)
            if not node.content_compared:
                return DifferenceType.PENDING
            
            # If already compared, return current classification
            return node.difference_type
    
    # ========================================================================
    # File Comparator Worker Thread (Task 6)
    # ========================================================================
    
    def _file_comparator_worker(self) -> None:
        """
        Worker thread that processes file comparison tasks from the comparison queue.
        
        This method runs in a background thread, continuously processing comparison tasks
        from the comparison_queue. For each task, it:
        1. Gets a comparison task from the queue
        2. Calls compare_file_content() for the task paths
        3. Updates the tree node's difference_type
        4. Updates the node's content_compared flag
        5. Marks tree as dirty to trigger UI update
        
        The worker checks the cancelled flag periodically to support graceful shutdown.
        """
        while not self.cancelled:
            try:
                # Get next comparison task from queue (with timeout to check cancelled flag)
                try:
                    task = self.comparison_queue.get(timeout=0.1)
                except queue.Empty:
                    # No tasks available, check cancelled flag and continue
                    continue
                
                # Process the comparison task
                try:
                    # Both paths must exist for comparison
                    if not task.left_path or not task.right_path:
                        # Mark task as done and skip
                        self.comparison_queue.task_done()
                        continue
                    
                    # Create a DiffEngine instance to use its compare_file_content method
                    engine = DiffEngine(self.left_files, self.right_files)
                    
                    # Compare file content
                    files_identical = engine.compare_file_content(task.left_path, task.right_path)
                    
                    # Update tree node with comparison result
                    with self.tree_lock:
                        if self.root_node:
                            # Find the node by relative path
                            target_node = self._find_node_by_path(self.root_node, task.relative_path)
                            if target_node:
                                # Update node's difference_type based on comparison result
                                if files_identical:
                                    target_node.difference_type = DifferenceType.IDENTICAL
                                else:
                                    target_node.difference_type = DifferenceType.CONTENT_DIFFERENT
                                
                                # Mark as compared
                                target_node.content_compared = True
                                
                                # Update parent directories to reflect changes
                                self._update_parent_classifications(target_node)
                    
                    # Store any comparison errors
                    if engine.comparison_errors:
                        self.comparison_errors.update(engine.comparison_errors)
                    
                    # Mark tree as dirty to trigger UI update
                    self.mark_dirty()
                    
                except Exception as e:
                    # Log error but continue processing other tasks
                    self.logger.error(f"Error processing comparison task for {task.relative_path}: {e}")
                
                finally:
                    # Mark task as done
                    self.comparison_queue.task_done()
                    
            except Exception as e:
                # Unexpected error in worker loop - log and set error flag
                error_msg = f"Unexpected error in file comparator worker: {e}"
                self.logger.error(error_msg)
                
                # Set error flag to notify main thread
                self.worker_error = error_msg
                self.mark_dirty()  # Trigger UI update to show error
                
                # Continue running unless cancelled
    
    def _update_parent_classifications(self, node: TreeNode) -> None:
        """
        Update parent directory classifications after a child node changes.
        
        When a file's comparison result changes, parent directories may need
        to be reclassified from IDENTICAL to CONTAINS_DIFFERENCE.
        
        Args:
            node: Child node whose classification changed
        """
        # Walk up the tree updating parent classifications
        current = node.parent
        while current and current.depth >= 0:
            # Reclassify parent based on its children
            old_type = current.difference_type
            current.difference_type = self._classify_node_quick(current)
            
            # Optimization: If classification didn't change AND it's already CONTAINS_DIFFERENCE,
            # we can stop (no need to propagate further)
            # However, if it changed from PENDING to CONTAINS_DIFFERENCE, we must continue
            # propagating up the tree
            if old_type == current.difference_type and old_type == DifferenceType.CONTAINS_DIFFERENCE:
                break
            
            # Move to next parent
            current = current.parent
    
    # ========================================================================
    # Priority System (Task 8)
    # ========================================================================
    
    def _get_visible_nodes_range(self) -> List[TreeNode]:
        """
        Calculate which nodes are currently visible in the viewport.
        
        This method determines which tree nodes are currently displayed on screen
        based on the scroll_offset and display height. These nodes should be
        prioritized for scanning and comparison.
        
        Returns:
            List of TreeNodes that are currently visible in the viewport
        """
        # Get display dimensions
        height, width = self.renderer.get_dimensions()
        # Reserve space for header (1 line), divider (1 line), details pane (4 lines), and status bar (1 line)
        display_height = height - 7
        
        # Calculate visible range
        start_index = self.scroll_offset
        end_index = min(self.scroll_offset + display_height, len(self.visible_nodes))
        
        # Return visible nodes
        return self.visible_nodes[start_index:end_index]
    
    def _update_priorities(self) -> None:
        """
        Update scan priorities based on current viewport and expansion state.
        
        This method is called when the viewport changes (scroll, expand, collapse)
        to ensure visible items are scanned first. It:
        1. Gets currently visible nodes
        2. For each unscanned visible directory, creates a high-priority scan task
        3. Adds these tasks to the priority_queue for immediate processing
        
        The priority_handler_worker will move these tasks to the front of the
        scan_queue to ensure visible items are scanned before hidden ones.
        """
        # Get visible nodes
        visible_nodes = self._get_visible_nodes_range()
        
        # Process each visible node
        for node in visible_nodes:
            # Only prioritize directories that haven't been scanned yet
            if node.is_directory and not node.children_scanned and not node.scan_in_progress:
                # Build relative path for this node
                relative_path = self._get_relative_path(node)
                
                # Create high-priority scan task
                priority_task = ScanTask(
                    left_path=node.left_path,
                    right_path=node.right_path,
                    relative_path=relative_path,
                    priority=ScanPriority.VISIBLE,  # High priority for visible items
                    is_visible=True
                )
                
                # Add to priority queue
                # Use negative priority so higher values come first (PriorityQueue uses min-heap)
                # Include counter to make items unique and avoid comparison of ScanTask objects
                with self.queue_lock:
                    self.priority_queue.put((-priority_task.priority, self.priority_counter, priority_task))
                    self.priority_counter += 1
    
    def _priority_handler_worker(self) -> None:
        """
        Worker thread that processes high-priority scan tasks.
        
        This method runs in a background thread, continuously pulling high-priority
        tasks from the priority_queue and moving them to the front of the scan_queue.
        This ensures that visible items are scanned before hidden ones.
        
        The worker checks the cancelled flag periodically to support graceful shutdown.
        """
        try:
            while not self.cancelled:
                try:
                    # Get next priority task from queue (with timeout to check cancelled flag)
                    # priority_queue returns (priority, counter, task) tuples
                    priority_item = self.priority_queue.get(timeout=0.1)
                except queue.Empty:
                    # No tasks available, check cancelled flag and continue
                    continue
                
                # Check if cancelled before processing
                if self.cancelled:
                    break
                
                # Extract task from priority tuple (priority was negated for min-heap)
                _, _, task = priority_item
                
                # Move task to front of scan_queue by putting it there immediately
                # The scan_queue is a regular Queue (FIFO), so we can't truly move
                # items to the front. Instead, we'll put the priority task directly
                # into the scan_queue, and it will be processed before older tasks
                # that are still waiting.
                with self.queue_lock:
                    # Put the high-priority task into the scan_queue
                    # Since we're processing priority tasks immediately, they'll
                    # be picked up by the scanner worker before older normal-priority tasks
                    self.scan_queue.put(task)
                
                # Mark priority task as done
                self.priority_queue.task_done()
                
        except Exception as e:
            # Log unexpected errors and set error flag to notify main thread
            error_msg = f"Priority handler worker error: {e}"
            self.logger.error(error_msg)
            import traceback
            traceback.print_exc()
            
            # Set error flag to notify main thread
            self.worker_error = error_msg
            self.mark_dirty()  # Trigger UI update to show error
    
    # ========================================================================
    # File Diff Viewer Integration (Task 13.1)
    # ========================================================================
    
    def open_file_diff(self, node_index: int) -> None:
        """
        Open file diff viewer for a file node.
        
        This method checks if the cursor is on a file node that exists on both sides,
        and if so, creates a DiffViewer instance with both file paths and pushes it
        onto the UI layer stack.
        
        Task 15.3: If file content has not been compared yet (PENDING), compare it
        immediately before opening the diff viewer.
        
        Args:
            node_index: Index of the node in visible_nodes list
        """
        # Validate node index
        if node_index < 0 or node_index >= len(self.visible_nodes):
            return
        
        node = self.visible_nodes[node_index]
        
        # Only open diff for files (not directories)
        if node.is_directory:
            return
        
        # Need both paths to open diff viewer
        if not node.left_path or not node.right_path:
            # File only exists on one side, cannot open diff viewer
            return
        
        # Task 15.3: If file content has not been compared yet, compare it now
        if not node.content_compared:
            # Create a DiffEngine instance to compare the file
            diff_engine = DiffEngine(self.left_files, self.right_files)
            
            # Compare file content
            files_identical = diff_engine.compare_file_content(node.left_path, node.right_path)
            
            # Update node's difference type based on comparison
            with self.tree_lock:
                if files_identical:
                    node.difference_type = DifferenceType.IDENTICAL
                else:
                    node.difference_type = DifferenceType.CONTENT_DIFFERENT
                
                # Mark as compared
                node.content_compared = True
                
                # Propagate difference to parent directories if needed
                if not files_identical:
                    self._propagate_difference_to_parents(node)
            
            # Mark tree as dirty to update display
            self.mark_dirty()
        
        # Check if layer_stack is available
        if not self.layer_stack:
            # Log warning
            self.logger.warning("Cannot open file diff: layer_stack not provided to DirectoryDiffViewer")
            return
        
        # Create DiffViewer instance
        try:
            diff_viewer = DiffViewer(self.renderer, node.left_path, node.right_path, self.layer_stack)
            
            # Push onto UI layer stack
            self.layer_stack.push(diff_viewer)
            
            # Mark dirty to trigger redraw when we return
            self.mark_dirty()
            
        except Exception as e:
            # Log error
            self.logger.error(f"Error opening file diff viewer: {e}")
