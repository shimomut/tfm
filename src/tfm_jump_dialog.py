#!/usr/bin/env python3
"""
TUI File Manager - Jump Dialog Component
Provides directory jumping functionality with threading support
"""

import curses
import threading
import time
from pathlib import Path
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color
from tfm_progress_animator import ProgressAnimatorFactory


class JumpDialog:
    """Jump dialog component for directory navigation with threading support"""
    
    def __init__(self, config):
        self.config = config
        
        # Jump dialog state
        self.mode = False
        self.search_editor = SingleLineTextEdit()  # Search editor for filtering directories
        self.directories = []  # List of all directories found
        self.filtered_directories = []  # Filtered directories based on search
        self.selected = 0  # Index of currently selected directory in filtered list
        self.scroll = 0  # Scroll offset for results
        self.searching = False  # Whether directory scan is in progress
        
        # Threading support
        self.scan_thread = None
        self.scan_lock = threading.Lock()
        self.cancel_scan = threading.Event()
        
        # Animation support
        self.progress_animator = ProgressAnimatorFactory.create_search_animator(config)
        
        # Get configurable directory scan limit
        self.max_directories = getattr(config, 'MAX_JUMP_DIRECTORIES', 5000)
        
    def show(self, root_directory):
        """Show the jump dialog and start scanning directories
        
        Args:
            root_directory: Path object representing the root directory to scan from
        """
        # Cancel any existing scan first
        self._cancel_current_scan()
        
        self.mode = True
        self.search_editor.clear()
        self.directories = []
        self.filtered_directories = []
        self.selected = 0
        self.scroll = 0
        self.searching = False
        
        # Reset animation
        self.progress_animator.reset()
        
        # Start directory scanning
        self._start_directory_scan(root_directory)
        
    def exit(self):
        """Exit jump dialog mode"""
        # Cancel any running scan
        self._cancel_current_scan()
        
        self.mode = False
        self.search_editor.clear()
        self.directories = []
        self.filtered_directories = []
        self.selected = 0
        self.scroll = 0
        self.searching = False
        
        # Reset animation
        self.progress_animator.reset()
        
    def handle_input(self, key):
        """Handle input while in jump dialog mode"""
        if key == 27:  # ESC - cancel
            # Cancel scan before exiting
            self._cancel_current_scan()
            self.exit()
            return True
        elif key == curses.KEY_UP:
            # Move selection up (thread-safe)
            with self.scan_lock:
                if self.filtered_directories and self.selected > 0:
                    self.selected -= 1
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_DOWN:
            # Move selection down (thread-safe)
            with self.scan_lock:
                if self.filtered_directories and self.selected < len(self.filtered_directories) - 1:
                    self.selected += 1
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            with self.scan_lock:
                if self.filtered_directories:
                    self.selected = max(0, self.selected - 10)
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            with self.scan_lock:
                if self.filtered_directories:
                    self.selected = min(len(self.filtered_directories) - 1, self.selected + 10)
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_HOME:  # Home - text cursor or list navigation
            # If there's text in search, let editor handle it for cursor movement
            if self.search_editor.text:
                if self.search_editor.handle_key(key):
                    return True
            else:
                # If no search text, use for list navigation (thread-safe)
                with self.scan_lock:
                    if self.filtered_directories:
                        self.selected = 0
                        self.scroll = 0
            return True
        elif key == curses.KEY_END:  # End - text cursor or list navigation
            # If there's text in search, let editor handle it for cursor movement
            if self.search_editor.text:
                if self.search_editor.handle_key(key):
                    return True
            else:
                # If no search text, use for list navigation (thread-safe)
                with self.scan_lock:
                    if self.filtered_directories:
                        self.selected = len(self.filtered_directories) - 1
                        self._adjust_scroll()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Cancel scan before navigating
            self._cancel_current_scan()
            
            # Return the selected directory for navigation (thread-safe)
            with self.scan_lock:
                if self.filtered_directories and 0 <= self.selected < len(self.filtered_directories):
                    selected_directory = self.filtered_directories[self.selected]
                    return ('navigate', selected_directory)
            return ('navigate', None)
        elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
            # Let the editor handle cursor movement keys
            if self.search_editor.handle_key(key):
                self._filter_directories()
            return True
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Let the editor handle backspace
            if self.search_editor.handle_key(key):
                self._filter_directories()
            return True
        elif 32 <= key <= 126:  # Printable characters
            # Let the editor handle printable characters
            if self.search_editor.handle_key(key):
                self._filter_directories()
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
    
    def _scan_worker(self, root_directory):
        """Worker thread for performing the actual directory scan
        
        Args:
            root_directory: Path object representing the root directory to scan from
        """
        temp_directories = []
        
        try:
            # Add the root directory itself first
            temp_directories.append(root_directory)
            
            # Recursively scan for directories
            for dir_path in root_directory.rglob('*'):
                # Check for cancellation
                if self.cancel_scan.is_set():
                    return
                
                # Check directory limit
                if len(temp_directories) >= self.max_directories:
                    break
                
                if dir_path.is_dir():
                    temp_directories.append(dir_path)
                    
                    # Update results periodically for real-time display
                    if len(temp_directories) % 50 == 0:
                        with self.scan_lock:
                            self.directories = temp_directories.copy()
                            self._filter_directories_internal()
                            
        except Exception as e:
            # Handle scan errors gracefully
            pass
        
        # Final update of results if not cancelled
        if not self.cancel_scan.is_set():
            with self.scan_lock:
                self.directories = temp_directories
                self._filter_directories_internal()
                self.searching = False
        
    def _filter_directories(self):
        """Filter directories based on current search pattern (thread-safe)"""
        with self.scan_lock:
            self._filter_directories_internal()
    
    def _filter_directories_internal(self):
        """Internal method to filter directories (must be called with lock held)"""
        # Remember currently selected directory if any
        currently_selected_dir = None
        if self.filtered_directories and 0 <= self.selected < len(self.filtered_directories):
            currently_selected_dir = self.filtered_directories[self.selected]
        
        search_text = self.search_editor.text.strip()
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
        self._adjust_scroll()
        
    def _adjust_scroll(self):
        """Adjust scroll offset to keep selected item visible"""
        # Use default dialog dimensions for scroll calculation
        dialog_height = 20  # Default height
        content_height = dialog_height - 8  # Account for title, search box, borders, help
        
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + content_height:
            self.scroll = self.selected - content_height + 1
            
    def draw(self, stdscr, safe_addstr_func):
        """Draw the jump dialog overlay"""
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(60, int(width * 0.8))
        dialog_height = max(20, int(height * 0.8))
        
        # Update scroll calculation with actual dimensions
        content_height = dialog_height - 8
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + content_height:
            self.scroll = self.selected - content_height + 1
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                safe_addstr_func(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            safe_addstr_func(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                safe_addstr_func(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    safe_addstr_func(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            safe_addstr_func(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        title_text = " Jump to Directory "
        title_x = start_x + (dialog_width - len(title_text)) // 2
        if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
            safe_addstr_func(start_y, title_x, title_text, border_color)
        
        # Draw search box
        search_y = start_y + 2
        # Draw search input using SingleLineTextEdit
        if search_y < height:
            max_search_width = dialog_width - 4  # Leave some margin
            self.search_editor.draw(
                stdscr, search_y, start_x + 2, max_search_width,
                "Filter: ",
                is_active=True
            )
        
        # Draw separator line
        sep_y = start_y + 3
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            safe_addstr_func(sep_y, start_x, sep_line[:dialog_width], border_color)
        
        # Draw results count with animated progress indicator (thread-safe)
        count_y = start_y + 4
        if count_y < height:
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
                    if self.search_editor.text.strip():
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
        content_height = results_end_y - results_start_y + 1
        
        # Draw results (thread-safe)
        with self.scan_lock:
            visible_directories = self.filtered_directories[self.scroll:self.scroll + content_height]
            current_selected = self.selected
        
        for i, directory in enumerate(visible_directories):
            y = results_start_y + i
            if y <= results_end_y and y < height:
                result_index = self.scroll + i
                is_selected = result_index == current_selected
                
                # Format directory text
                directory_text = f"📁 {str(directory)}"
                
                if len(directory_text) > content_width - 2:
                    directory_text = directory_text[:content_width - 5] + "..."
                
                # Add selection indicator
                if is_selected:
                    display_text = f"► {directory_text}"
                    item_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                else:
                    display_text = f"  {directory_text}"
                    item_color = get_status_color()
                
                # Ensure text fits
                display_text = display_text[:content_width]
                safe_addstr_func(y, content_start_x, display_text, item_color)
        
        # Draw help text
        help_y = start_y + dialog_height - 2
        if help_y < height:
            help_text = "Enter: Jump | Type: Filter | ESC: Cancel"
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                safe_addstr_func(help_y, help_x, help_text, get_status_color() | curses.A_DIM)


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