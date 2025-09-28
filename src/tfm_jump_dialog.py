#!/usr/bin/env python3
"""
TUI File Manager - Jump Dialog Component
Provides directory jumping functionality with threading support
"""

import curses
import threading
import time
from tfm_path import Path
from tfm_base_list_dialog import BaseListDialog
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color
from tfm_progress_animator import ProgressAnimatorFactory


class JumpDialog(BaseListDialog):
    """Jump dialog component for directory navigation with threading support"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Jump dialog specific state
        self.directories = []  # List of all directories found
        self.filtered_directories = []  # Filtered directories based on search
        self.searching = False  # Whether directory scan is in progress
        self.content_changed = True  # Track if content needs redraw
        
        # Threading support
        self.scan_thread = None
        self.scan_lock = threading.Lock()
        self.cancel_scan = threading.Event()
        
        # Animation support
        self.progress_animator = ProgressAnimatorFactory.create_search_animator(config)
        
        # Get configurable directory scan limit
        self.max_directories = getattr(config, 'MAX_JUMP_DIRECTORIES', 5000)
        
        # Store reference to file_operations for show_hidden setting
        self.file_operations = None
        
    def show(self, root_directory, file_operations=None):
        """Show the jump dialog and start scanning directories
        
        Args:
            root_directory: Path object representing the root directory to scan from
            file_operations: FileOperations instance to get show_hidden setting from
        """
        # Cancel any existing scan first
        self._cancel_current_scan()
        
        self.mode = True
        self.text_editor.clear()
        self.directories = []
        self.content_changed = True  # Mark content as changed when showing
        self.filtered_directories = []
        self.selected = 0
        self.scroll = 0
        self.searching = False
        
        # Store file_operations reference for show_hidden setting
        self.file_operations = file_operations
        
        # Store root directory for context in filtering
        self.root_directory = root_directory
        
        # Reset animation
        self.progress_animator.reset()
        
        # Start directory scanning
        self._start_directory_scan(root_directory)
        
    def exit(self):
        """Exit jump dialog mode"""
        # Cancel any running scan
        self._cancel_current_scan()
        
        super().exit()
        self.directories = []
        self.filtered_directories = []
        self.searching = False
        self.content_changed = True  # Mark content as changed when exiting
        
        # Reset animation
        self.progress_animator.reset()
        
    def handle_input(self, key):
        """Handle input while in jump dialog mode"""
        # Use base class navigation handling with thread safety
        with self.scan_lock:
            current_filtered = self.filtered_directories.copy()
        
        result = self.handle_common_navigation(key, current_filtered)
        
        if result == 'cancel':
            # Cancel scan before exiting
            self._cancel_current_scan()
            self.exit()
            return True
        elif result == 'select':
            # Cancel scan before navigating
            self._cancel_current_scan()
            
            # Return the selected directory for navigation (thread-safe)
            with self.scan_lock:
                if self.filtered_directories and 0 <= self.selected < len(self.filtered_directories):
                    selected_directory = self.filtered_directories[self.selected]
                    return ('navigate', selected_directory)
            return ('navigate', None)
        elif result == 'text_changed':
            self._filter_directories()
            self.content_changed = True  # Mark content as changed when filtering
            return True
        elif result:
            # Update selection in thread-safe manner for navigation keys
            if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_PPAGE, curses.KEY_NPAGE, curses.KEY_HOME, curses.KEY_END]:
                with self.scan_lock:
                    # The base class already updated self.selected, just need to adjust scroll
                    self._adjust_scroll(len(self.filtered_directories))
            
            # Mark content as changed for ANY handled key to ensure continued rendering
            self.content_changed = True
            return True
            
        return False
        
    def _start_directory_scan(self, root_directory):
        """Start asynchronous directory scanning
        
        Args:
            root_directory: Path object representing the root directory to scan from
        """
        # Cancel any existing scan
        self._cancel_current_scan()
        
        # Clear previous results immediately when starting new scan
        with self.scan_lock:
            self.directories = []
            self.filtered_directories = []
            self.selected = 0
            self.scroll = 0
        
        # Start new scan thread
        self.cancel_scan.clear()
        self.searching = True
        
        # Reset animation for new scan
        self.progress_animator.reset()
        
        self.scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(root_directory,),
            daemon=True
        )
        self.scan_thread.start()
    
    def _cancel_current_scan(self):
        """Cancel the current directory scan operation"""
        if self.scan_thread and self.scan_thread.is_alive():
            self.cancel_scan.set()
            # Give the thread a moment to finish
            self.scan_thread.join(timeout=0.1)
        
        self.searching = False
        self.scan_thread = None
        self.content_changed = True  # Mark content as changed when scan is canceled
    
    def _scan_worker(self, root_directory):
        """Worker thread for performing the actual directory scan
        
        Args:
            root_directory: Path object representing the root directory to scan from
        """
        temp_directories = []
        
        try:
            # Add the root directory itself first
            temp_directories.append(root_directory)
            
            # Use iterative approach instead of rglob to have better control over traversal
            self._scan_directory_tree(root_directory, root_directory, temp_directories)
                            
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not scan directory tree from {root_directory}: {e}")
        except Exception as e:
            print(f"Warning: Unexpected error during directory scan: {e}")
        
        # Final update of results if not cancelled
        if not self.cancel_scan.is_set():
            with self.scan_lock:
                self.directories = temp_directories
                self._filter_directories_internal()
                self.searching = False
                self.content_changed = True  # Mark content as changed when scan completes
        
    def _filter_directories(self):
        """Filter directories based on current search pattern (thread-safe)"""
        with self.scan_lock:
            self._filter_directories_internal()
            self.content_changed = True  # Mark content as changed when filtering
    
    def _filter_directories_internal(self):
        """Internal method to filter directories (must be called with lock held)"""
        # Remember currently selected directory if any
        currently_selected_dir = None
        if self.filtered_directories and 0 <= self.selected < len(self.filtered_directories):
            currently_selected_dir = self.filtered_directories[self.selected]
        
        search_text = self.text_editor.text.strip()
        if not search_text:
            self.filtered_directories = self.directories.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_directories = [
                directory for directory in self.directories 
                if search_lower in str(directory).lower()
            ]
        
        # Try to preserve selection if the previously selected directory is still in filtered results
        new_selected = 0
        if currently_selected_dir and currently_selected_dir in self.filtered_directories:
            try:
                new_selected = self.filtered_directories.index(currently_selected_dir)
            except ValueError:
                new_selected = 0
        
        # Update selection and adjust scroll
        self.selected = new_selected
        self._adjust_scroll(len(self.filtered_directories))
    
    def _scan_directory_tree(self, current_dir, root_directory, temp_directories):
        """Recursively scan directory tree with proper hidden file handling
        
        Args:
            current_dir: Current directory being scanned
            root_directory: Root directory where scanning started
            temp_directories: List to accumulate found directories
        """
        try:
            # Get all entries in current directory
            entries = list(current_dir.iterdir())
            
            for entry in entries:
                # Check for cancellation
                if self.cancel_scan.is_set():
                    return
                
                # Check directory limit
                if len(temp_directories) >= self.max_directories:
                    return
                
                if entry.is_dir():
                    # Check if this directory should be included
                    if self._should_include_directory(entry, current_dir, root_directory):
                        temp_directories.append(entry)
                        
                        # Update results periodically for real-time display
                        if len(temp_directories) % 50 == 0:
                            with self.scan_lock:
                                self.directories = temp_directories.copy()
                                self._filter_directories_internal()
                                self.content_changed = True
                        
                        # Recursively scan this directory
                        self._scan_directory_tree(entry, root_directory, temp_directories)
                    # If directory is hidden and we're not showing hidden files,
                    # don't recurse into it at all (skip its subdirectories)
                        
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
    
    def _should_include_directory(self, dir_path, parent_dir, root_directory):
        """Check if a directory should be included based on show_hidden setting
        
        Args:
            dir_path: Path object of the directory to check
            parent_dir: Parent directory of dir_path
            root_directory: Root directory where scanning started
            
        Returns:
            bool: True if directory should be included, False otherwise
        """
        # If no file_operations reference, include all directories (fallback behavior)
        if not self.file_operations:
            return True
        
        # Check if we should show hidden files
        show_hidden = getattr(self.file_operations, 'show_hidden', False)
        
        # If showing hidden files, include everything
        if show_hidden:
            return True
        
        # If not showing hidden files, check if this directory is hidden
        dir_name = dir_path.name
        if dir_name.startswith('.') and dir_name not in ['.', '..']:
            # This is a hidden directory
            # Only exclude it if we're not already inside a hidden directory context
            
            # Check if the root directory itself is hidden or contains hidden components
            try:
                # If root directory is already hidden, we're in a hidden context
                root_relative_to_parent = root_directory
                for part in root_directory.parts:
                    if part.startswith('.') and part not in ['.', '..']:
                        # Root is in hidden context, so allow hidden subdirectories
                        return True
                
                # Check if parent directory is hidden relative to root
                if parent_dir != root_directory:
                    try:
                        parent_relative = parent_dir.relative_to(root_directory)
                        for part in parent_relative.parts:
                            if part.startswith('.') and part not in ['.', '..']:
                                # Parent is hidden, so allow hidden subdirectories
                                return True
                    except ValueError:
                        # parent_dir is not relative to root_directory, allow it
                        return True
                
                # We're not in a hidden context, so exclude this hidden directory
                return False
                
            except (ValueError, AttributeError):
                # If we can't determine the relationship, err on the side of inclusion
                return True
        
        # Non-hidden directory, always include
        return True
            
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        # Always redraw when scanning to animate progress indicator
        return self.content_changed or self.searching
    
    def draw(self, stdscr, safe_addstr_func):
        """Draw the jump dialog overlay"""
        # Draw dialog frame
        start_y, start_x, dialog_width, dialog_height = self.draw_dialog_frame(
            stdscr, safe_addstr_func, "Jump to Directory", 0.8, 0.8, 60, 20
        )
        
        # Draw filter input
        search_y = start_y + 2
        self.draw_text_input(stdscr, safe_addstr_func, search_y, start_x, dialog_width, "Filter: ")
        
        # Draw separator
        sep_y = start_y + 3
        self.draw_separator(stdscr, safe_addstr_func, sep_y, start_x, dialog_width)
        
        # Draw results count with animated progress indicator (thread-safe)
        count_y = start_y + 4
        if count_y < stdscr.getmaxyx()[0]:
            with self.scan_lock:
                directory_count = len(self.directories)
                filtered_count = len(self.filtered_directories)
                is_searching = self.searching
                
                if is_searching:
                    # Get animated status text
                    if directory_count >= self.max_directories:
                        context_info = f"limit reached: {directory_count}"
                    else:
                        context_info = f"{directory_count} found"
                    
                    count_text = self.progress_animator.get_status_text("Scanning", context_info, is_searching)
                    
                    # Use brighter color for active scan
                    count_color = get_status_color() | curses.A_BOLD
                else:
                    if self.text_editor.text.strip():
                        count_text = f"Directories: {filtered_count} (filtered from {directory_count})"
                    else:
                        count_text = f"Directories: {directory_count}"
                    
                    if directory_count >= self.max_directories:
                        count_text += " (limit reached)"
                    
                    count_color = get_status_color() | curses.A_DIM
            
            safe_addstr_func(count_y, start_x + 2, count_text[:dialog_width - 4], count_color)
        
        # Calculate results area
        results_start_y = start_y + 5
        results_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Format directories for display
        def format_directory(directory):
            return f"📁 {str(directory)}"
        
        # Draw results (thread-safe)
        with self.scan_lock:
            current_filtered = self.filtered_directories.copy()
        
        self.draw_list_items(stdscr, safe_addstr_func, current_filtered, 
                           results_start_y, results_end_y, content_start_x, content_width, format_directory)
        
        # Draw scrollbar
        scrollbar_x = start_x + dialog_width - 2
        content_height = results_end_y - results_start_y + 1
        self.draw_scrollbar(stdscr, safe_addstr_func, current_filtered, 
                          results_start_y, content_height, scrollbar_x)
        
        # Draw help text
        help_text = "Enter: Jump | Type: Filter | ESC: Cancel"
        help_y = start_y + dialog_height - 2
        self.draw_help_text(stdscr, safe_addstr_func, help_text, help_y, start_x, dialog_width)
        
        # Automatically mark as not needing redraw after drawing (unless still searching)
        if not self.searching:
            self.content_changed = False


class JumpDialogHelpers:
    """Helper functions for jump dialog navigation and integration"""
    
    @staticmethod
    def navigate_to_directory(directory, pane_manager, print_func):
        """Navigate to the selected directory
        
        Args:
            directory: Path object of the directory to navigate to
            pane_manager: PaneManager instance
            print_func: Function to print messages
        """
        current_pane = pane_manager.get_current_pane()
        
        if directory and directory.exists() and directory.is_dir():
            old_path = current_pane['path']
            current_pane['path'] = directory
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            
            pane_name = "left" if pane_manager.active_pane == 'left' else "right"
            print_func(f"Jumped to directory: {directory}")
        else:
            print_func(f"Error: Directory no longer exists or is not accessible: {directory}")