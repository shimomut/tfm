"""
Directory Diff Viewer - Recursive directory comparison with tree-structured display.

This module provides a UILayer component for comparing two directories recursively,
displaying differences in an expandable/collapsible tree structure with visual highlighting.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
import threading
from tfm_path import Path
from tfm_ui_layer import UILayer
from ttk import KeyEvent, KeyCode, ModifierKey, CharEvent, SystemEvent, TextAttribute
from tfm_colors import (
    get_color_with_attrs,
    get_status_color,
    COLOR_DIFF_ONLY_ONE_SIDE,
    COLOR_DIFF_CHANGE,
    COLOR_DIFF_BLANK,
    COLOR_DIFF_FOCUSED,
    COLOR_REGULAR_FILE,
    COLOR_DIRECTORIES,
    COLOR_DIFF_SEPARATOR_RED,
    COLOR_TREE_LINES
)
from tfm_wide_char_utils import get_display_width, truncate_to_width
from tfm_diff_viewer import DiffViewer
from tfm_scrollbar import draw_scrollbar, calculate_scrollbar_width


class DifferenceType(Enum):
    """Classification of detected differences between directories."""
    IDENTICAL = "identical"
    ONLY_LEFT = "only_left"
    ONLY_RIGHT = "only_right"
    CONTENT_DIFFERENT = "content_different"
    CONTAINS_DIFFERENCE = "contains_difference"


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
                    try:
                        from tfm_log_manager import LogManager
                        LogManager.log_warning(f"Error scanning {current_path}: {e}")
                    except Exception:
                        # LogManager not available or failed, print to stderr
                        print(f"Error scanning {current_path}: {e}", file=__import__('sys').stderr)
                    continue
        
        except Exception as e:
            # Fatal error scanning root directory
            try:
                from tfm_log_manager import LogManager
                LogManager.log_error(f"Fatal error scanning {root_path}: {e}")
            except Exception:
                # LogManager not available or failed, print to stderr
                print(f"Fatal error scanning {root_path}: {e}", file=__import__('sys').stderr)
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
            if any(child.difference_type != DifferenceType.IDENTICAL for child in node.children):
                return DifferenceType.CONTAINS_DIFFERENCE
            return DifferenceType.IDENTICAL
        
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
            if any(child.difference_type != DifferenceType.IDENTICAL for child in node.children):
                return DifferenceType.CONTAINS_DIFFERENCE
            return DifferenceType.IDENTICAL
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
            
            # Try to log the error if LogManager is available
            try:
                from tfm_log_manager import LogManager
                LogManager.log_warning(error_msg)
            except Exception:
                # LogManager not available or failed, print to stderr
                print(error_msg, file=__import__('sys').stderr)
            
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
    
    def __init__(self, renderer, left_path: Path, right_path: Path, layer_stack=None):
        """
        Initialize the directory diff viewer.
        
        Args:
            renderer: TTK renderer instance
            left_path: Path to left directory
            right_path: Path to right directory
            layer_stack: Optional UILayerStack for pushing new layers (e.g., DiffViewer)
        """
        self.renderer = renderer
        self.left_path = left_path
        self.right_path = right_path
        self.layer_stack = layer_stack
        
        # Tree structure
        self.root_node: Optional[TreeNode] = None
        self.visible_nodes: List[TreeNode] = []
        self.node_index_map: Dict[int, int] = {}  # Maps id(node) -> index
        
        # Navigation state
        self.scroll_offset = 0
        self.cursor_position = 0
        self.horizontal_offset = 0
        
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
        self.scan_thread: Optional[threading.Thread] = None
        self.scan_cancelled = False
        self.scanner: Optional[DirectoryScanner] = None
        
        # Scan results
        self.left_files: Dict[str, FileInfo] = {}
        self.right_files: Dict[str, FileInfo] = {}
        self.scan_error: Optional[str] = None
        self.comparison_errors: Dict[str, str] = {}  # File comparison errors
        
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
        
        # If scan is in progress, only allow cancellation
        if self.scan_in_progress:
            if event.key_code == KeyCode.ESCAPE:
                # Cancel scan
                if self.scanner and not self.scan_cancelled:
                    self.scanner.cancel()
                    self.scan_cancelled = True
                    self.scan_status = "Cancelling scan..."
                    self.mark_dirty()
                    # Close viewer after cancellation
                    self._should_close = True
                return True
            # Ignore other keys during scan
            return True
        
        # Get display dimensions for scrolling calculations
        height, width = self.renderer.get_dimensions()
        # Reserve space for header (2 lines) and status bar (1 line)
        display_height = height - 3
        
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
        
        # Handle special keys
        if event.key_code == KeyCode.ESCAPE:
            # Close viewer
            self._should_close = True
            self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.UP:
            # Move cursor up
            if self.cursor_position > 0:
                self.cursor_position -= 1
                # Adjust scroll if cursor moves above visible area
                if self.cursor_position < self.scroll_offset:
                    self.scroll_offset = self.cursor_position
                self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.DOWN:
            # Move cursor down
            if self.cursor_position < len(self.visible_nodes) - 1:
                self.cursor_position += 1
                # Adjust scroll if cursor moves below visible area
                if self.cursor_position >= self.scroll_offset + display_height:
                    self.scroll_offset = self.cursor_position - display_height + 1
                self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.PAGE_UP:
            # Scroll up one page
            if self.cursor_position > 0:
                self.cursor_position = max(0, self.cursor_position - display_height)
                self.scroll_offset = max(0, self.scroll_offset - display_height)
                self.mark_dirty()
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
            # Right arrow: Expand directory or move to first child if already expanded
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
                            # Adjust scroll if needed
                            if self.cursor_position >= self.scroll_offset + display_height:
                                self.scroll_offset = self.cursor_position - display_height + 1
                            self.mark_dirty()
            return True
        
        elif event.key_code == KeyCode.LEFT:
            # Left arrow: Collapse directory or move to parent
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
                            # Adjust scroll if needed
                            if self.cursor_position < self.scroll_offset:
                                self.scroll_offset = self.cursor_position
                            self.mark_dirty()
                            break
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
    
    def render(self, renderer) -> None:
        """
        Render the directory diff viewer.
        
        Args:
            renderer: TTK renderer instance
        """
        height, width = renderer.get_dimensions()
        
        # Clear screen
        renderer.clear()
        
        # If scan is in progress, show progress screen
        if self.scan_in_progress:
            # Check if cancelling
            if self.scan_cancelled:
                self._render_cancellation_screen(renderer, width, height)
            else:
                self._render_progress_screen(renderer, width, height)
            return
        
        # If scan error occurred, show error screen
        if self.scan_error:
            self._render_error_screen(renderer, width, height)
            return
        
        # If no tree yet, show loading message
        if not self.root_node or not self.visible_nodes:
            self._render_loading_screen(renderer, width, height)
            return
        
        # Render normal view
        self._render_header(renderer, width)
        self._render_content(renderer, width, height)
        self._render_help_bar(renderer, width, height)
        self._render_status_bar(renderer, width, height)
    
    def _render_header(self, renderer, width: int) -> None:
        """
        Render the header with directory paths.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
        """
        # Get status color for header
        status_color_pair, status_attrs = get_status_color()
        
        # Line 1: Directory paths
        left_label = " " + str(self.left_path)  # Add 1-char space prefix
        right_label = " " + str(self.right_path)  # Add 1-char space prefix
        
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
            left_label = truncate_to_width(left_label, left_width, ellipsis="...")
        
        right_display_width = get_display_width(right_label)
        if right_display_width > right_width:
            right_label = truncate_to_width(right_label, right_width, ellipsis="...")
        
        # Pad labels to exact widths using spaces
        left_actual_width = get_display_width(left_label)
        right_actual_width = get_display_width(right_label)
        left_padding = " " * (left_width - left_actual_width)
        right_padding = " " * (right_width - right_actual_width)
        
        # Build header line
        header_separator = "   "  # 3 spaces to match separator width, no pipe
        header_line = left_label + left_padding + header_separator + right_label + right_padding
        
        # Draw header with background color
        renderer.draw_text(0, 0, header_line.ljust(width), status_color_pair, status_attrs)
    
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
        # Calculate content area (header is 1 line, help bar is 1 line, status bar is 1 line)
        content_start_y = 1
        content_height = height - 3
        
        # Check if directories are empty or identical
        if not self.visible_nodes or len(self.visible_nodes) == 0:
            # No visible nodes - directories are empty or all identical (with filter on)
            self._render_empty_or_identical_message(renderer, width, height, content_start_y, content_height)
            return
        
        # Calculate scrollbar width
        scrollbar_width = calculate_scrollbar_width(len(self.visible_nodes), content_height)
        
        # Always reserve space for scrollbar to prevent separator from moving
        # when tree expands/collapses and scrollbar appears/disappears
        reserved_scrollbar_width = 1  # Always reserve at least 1 column for scrollbar
        
        # Calculate column widths for side-by-side layout
        # Format: [indent][expand][name] | [indent][expand][name] [scrollbar]
        # Use the same separator as the header for alignment
        available_width = width - self.separator_width - reserved_scrollbar_width
        # Split evenly, giving any extra character to the left side (same as header)
        right_column_width = available_width // 2
        left_column_width = available_width - right_column_width  # Left gets any extra character
        left_column_x = 0
        separator_x = left_column_width
        right_column_x = left_column_width + self.separator_width
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
                    # Empty left column
                    renderer.draw_text(empty_y_pos, left_column_x, " " * left_column_width, 0, 0)
                    # Separator bar
                    renderer.draw_text(empty_y_pos, separator_x, empty_separator, separator_color_pair, separator_attrs)
                    # Empty right column
                    renderer.draw_text(empty_y_pos, right_column_x, " " * right_column_width, 0, 0)
                break
            
            node = self.visible_nodes[node_index]
            is_focused = (node_index == self.cursor_position)
            
            # Get colors for this node based on difference type
            color_pair, attrs = self._get_node_colors(node, is_focused)
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
            node_content = icon + error_indicator + node.name
            
            # Choose separator based on difference type
            if node.difference_type == DifferenceType.IDENTICAL:
                separator = self.separator_identical
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
                renderer.draw_text(y_pos, left_column_x + tree_lines_len, content_text, color_pair, attrs)
            else:
                # Node doesn't exist on left side - show tree lines for missing item
                # Use continuation lines only (no branch connectors)
                missing_tree_lines = self._build_tree_lines_for_missing(node)
                if missing_tree_lines:
                    renderer.draw_text(y_pos, left_column_x, missing_tree_lines, COLOR_TREE_LINES, TextAttribute.NORMAL)
                
                # Fill rest with blank
                blank_len = left_column_width - len(missing_tree_lines)
                if blank_len > 0:
                    blank_text = " " * blank_len
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
                renderer.draw_text(y_pos, right_column_x + tree_lines_len, content_text, color_pair, attrs)
            else:
                # Node doesn't exist on right side - show tree lines for missing item
                # Use continuation lines only (no branch connectors)
                missing_tree_lines = self._build_tree_lines_for_missing(node)
                if missing_tree_lines:
                    renderer.draw_text(y_pos, right_column_x, missing_tree_lines, COLOR_TREE_LINES, TextAttribute.NORMAL)
                
                # Fill rest with blank
                blank_len = right_column_width - len(missing_tree_lines)
                if blank_len > 0:
                    blank_text = " " * blank_len
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
    
    def _get_node_colors(self, node: TreeNode, is_focused: bool) -> tuple:
        """
        Get color pair and attributes for a node based on its difference type.
        
        Args:
            node: TreeNode to get colors for
            is_focused: Whether this node is currently focused (cursor on it)
            
        Returns:
            Tuple of (color_pair, attributes)
        """
        if is_focused:
            # Focused nodes always use focused color
            return get_color_with_attrs(COLOR_DIFF_FOCUSED)
        
        # Color based on difference type
        if node.difference_type == DifferenceType.ONLY_LEFT or \
           node.difference_type == DifferenceType.ONLY_RIGHT:
            return get_color_with_attrs(COLOR_DIFF_ONLY_ONE_SIDE)
        elif node.difference_type == DifferenceType.CONTENT_DIFFERENT:
            return get_color_with_attrs(COLOR_DIFF_CHANGE)
        elif node.difference_type == DifferenceType.CONTAINS_DIFFERENCE:
            return get_color_with_attrs(COLOR_DIFF_FOCUSED)
        else:  # IDENTICAL
            # Use regular file/directory color
            if node.is_directory:
                return get_color_with_attrs(COLOR_DIRECTORIES)
            else:
                return get_color_with_attrs(COLOR_REGULAR_FILE)
    
    def _render_help_bar(self, renderer, width: int, height: int) -> None:
        """
        Render the help bar with navigation controls.
        
        Args:
            renderer: TTK renderer instance
            width: Terminal width
            height: Terminal height
        """
        help_y = height - 2
        status_color_pair, status_attrs = get_status_color()
        
        # Controls/help text
        controls = "↑↓:Navigate  ←→:Expand/Collapse  Enter:View Diff/Expand  i:Toggle Identical  q/ESC:Quit"
        controls = controls[:width]
        renderer.draw_text(help_y, 0, controls.ljust(width), status_color_pair, status_attrs)
    
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
        
        # Count from all nodes in tree (not just visible)
        if self.root_node:
            self._count_differences(
                self.root_node,
                only_left_count, only_right_count, different_count,
                identical_count, contains_diff_count, error_count
            )
        
        # Build status text
        # Left side: position and filter status
        left_status = f"Item {current_pos}/{total_nodes}"
        if not self.show_identical:
            left_status += " [Identical Hidden]"
        
        # Right side: statistics
        stats_parts = []
        if only_left_count > 0:
            stats_parts.append(f"Left:{only_left_count}")
        if only_right_count > 0:
            stats_parts.append(f"Right:{only_right_count}")
        if different_count > 0:
            stats_parts.append(f"Diff:{different_count}")
        if identical_count > 0:
            stats_parts.append(f"Same:{identical_count}")
        
        right_status = " ".join(stats_parts) if stats_parts else "No differences"
        
        # Add error count if any
        if error_count > 0:
            right_status += f" Errors:{error_count}"
        
        # Combine left and right status
        # Calculate spacing to right-align the right status
        spacing = width - len(left_status) - len(right_status) - 2
        if spacing < 1:
            # Not enough space, truncate right status
            available = width - len(left_status) - 2
            if available > 0:
                right_status = right_status[:available]
                spacing = 1
            else:
                right_status = ""
                spacing = 0
        
        status_line = left_status + " " * spacing + right_status
        status_line = status_line[:width].ljust(width)
        
        renderer.draw_text(status_y, 0, status_line, status_color_pair, status_attrs)
    
    def _count_differences(self, node: TreeNode, only_left: int, only_right: int,
                          different: int, identical: int, contains_diff: int,
                          errors: int) -> tuple:
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
            only_left, only_right, different, identical, contains_diff, errors = \
                self._count_differences(child, only_left, only_right, different,
                                      identical, contains_diff, errors)
        
        return only_left, only_right, different, identical, contains_diff, errors
    
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
        return self._dirty
    
    def mark_dirty(self) -> None:
        """Mark this layer as needing a redraw."""
        self._dirty = True
    
    def clear_dirty(self) -> None:
        """Clear the dirty flag after rendering."""
        self._dirty = False
    
    def should_close(self) -> bool:
        """
        Query if this layer wants to close.
        
        Returns:
            True if layer should be closed, False otherwise
        """
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
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=1.0)
    
    # ========================================================================
    # Scanning Implementation (Task 5.2)
    # ========================================================================
    
    def start_scan(self) -> None:
        """
        Start scanning both directories in a worker thread.
        
        This method launches DirectoryScanner in a background thread to avoid
        blocking the UI. Progress updates are received through a callback and
        trigger UI redraws.
        """
        self.scan_in_progress = True
        self.scan_progress = 0.0
        self.scan_current = 0
        self.scan_total = 0
        self.scan_status = "Starting scan..."
        self.scan_cancelled = False
        self.scan_error = None
        self.mark_dirty()
        
        # Create scanner with progress callback
        self.scanner = DirectoryScanner(
            self.left_path,
            self.right_path,
            self._on_scan_progress
        )
        
        # Launch scan in worker thread
        self.scan_thread = threading.Thread(
            target=self._scan_worker,
            daemon=True
        )
        self.scan_thread.start()
    
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
            # Handle scan errors
            self.scan_in_progress = False
            self.scan_error = str(e)
            self.scan_status = "Scan failed"
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
        
        # Mark dirty to trigger redraw
        self.mark_dirty()
    
    def _build_tree(self) -> None:
        """
        Build the tree structure from scan results.
        
        This method uses DiffEngine to construct the unified tree and
        initializes the visible nodes list for rendering.
        """
        # Create diff engine
        engine = DiffEngine(self.left_files, self.right_files)
        
        # Build tree
        self.root_node = engine.build_tree()
        
        # Store comparison errors for display
        self.comparison_errors = engine.comparison_errors
        
        # Initialize visible nodes (start with root expanded)
        self.root_node.is_expanded = True
        self._update_visible_nodes()
    
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
            if self.show_identical or node.difference_type != DifferenceType.IDENTICAL:
                index = len(self.visible_nodes)
                self.visible_nodes.append(node)
                self.node_index_map[id(node)] = index
        
        # Add children if node is expanded
        if node.is_expanded:
            for child in node.children:
                self._flatten_tree(child)
    
    # ========================================================================
    # Tree Structure Management (Task 6.1)
    # ========================================================================
    
    def expand_node(self, node_index: int) -> None:
        """
        Expand a directory node to show its children.
        
        This method updates the visible_nodes list to include the children
        of the specified node. The cursor position is adjusted to stay on
        the same node after expansion.
        
        Args:
            node_index: Index of the node to expand in visible_nodes list
        """
        if node_index < 0 or node_index >= len(self.visible_nodes):
            return
        
        node = self.visible_nodes[node_index]
        
        # Only expand directories that aren't already expanded
        if not node.is_directory or node.is_expanded:
            return
        
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
        display_height = height - 3
        
        # If cursor is below visible area, adjust scroll
        if self.cursor_position >= self.scroll_offset + display_height:
            self.scroll_offset = self.cursor_position - display_height + 1
        
        # Mark dirty to trigger redraw
        self.mark_dirty()
    
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
        display_height = height - 3
        
        # If cursor is above visible area, adjust scroll
        if self.cursor_position < self.scroll_offset:
            self.scroll_offset = self.cursor_position
        # If cursor is below visible area, adjust scroll
        elif self.cursor_position >= self.scroll_offset + display_height:
            self.scroll_offset = self.cursor_position - display_height + 1
        
        # Mark dirty to trigger redraw
        self.mark_dirty()
    
    def _collect_visible_children(self, node: TreeNode, result: List[TreeNode]) -> None:
        """
        Recursively collect all visible children of a node.
        
        This respects the expansion state of child directories - only children
        of expanded directories are included.
        
        Args:
            node: Parent node whose children to collect
            result: List to append visible children to
        """
        for child in node.children:
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
    
    # ========================================================================
    # File Diff Viewer Integration (Task 13.1)
    # ========================================================================
    
    def open_file_diff(self, node_index: int) -> None:
        """
        Open file diff viewer for a content-different file node.
        
        This method checks if the cursor is on a file node that is marked as
        content-different, and if so, creates a DiffViewer instance with both
        file paths and pushes it onto the UI layer stack.
        
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
        
        # Only open diff for content-different files
        if node.difference_type != DifferenceType.CONTENT_DIFFERENT:
            return
        
        # Both paths must exist for content-different files
        if not node.left_path or not node.right_path:
            return
        
        # Check if layer_stack is available
        if not self.layer_stack:
            # Log warning if LogManager is available
            try:
                from tfm_log_manager import LogManager
                LogManager.log_warning("Cannot open file diff: layer_stack not provided to DirectoryDiffViewer")
            except Exception:
                pass
            return
        
        # Create DiffViewer instance
        try:
            diff_viewer = DiffViewer(self.renderer, node.left_path, node.right_path)
            
            # Push onto UI layer stack
            self.layer_stack.push(diff_viewer)
            
            # Mark dirty to trigger redraw when we return
            self.mark_dirty()
            
        except Exception as e:
            # Log error if LogManager is available
            try:
                from tfm_log_manager import LogManager
                LogManager.log_error(f"Error opening file diff viewer: {e}")
            except Exception:
                # LogManager not available or failed, print to stderr
                print(f"Error opening file diff viewer: {e}", file=__import__('sys').stderr)
