#!/usr/bin/env python3
"""
TUI File Manager - A terminal-based file manager using curses
"""

import curses
import os
import stat
import shutil
import subprocess
import sys
import io
import fnmatch
import shlex
import zipfile
import tarfile
import time
import webbrowser
from pathlib import Path
from datetime import datetime
from collections import deque
from tfm_single_line_text_edit import SingleLineTextEdit

# Import constants and colors
from tfm_const import *
from tfm_colors import *
from tfm_config import get_config, get_startup_paths, is_key_bound_to, get_favorite_directories, get_programs
from tfm_text_viewer import view_text_file, is_text_file

# Import new modular components
from tfm_log_manager import LogManager
from tfm_pane_manager import PaneManager
from tfm_file_operations import FileOperations
from tfm_list_dialog import ListDialog, ListDialogHelpers
from tfm_info_dialog import InfoDialog, InfoDialogHelpers
from tfm_search_dialog import SearchDialog, SearchDialogHelpers
from tfm_batch_rename_dialog import BatchRenameDialog, BatchRenameDialogHelpers
from tfm_quick_choice_bar import QuickChoiceBar, QuickChoiceBarHelpers
from tfm_general_purpose_dialog import GeneralPurposeDialog, DialogHelpers
from tfm_external_programs import ExternalProgramManager
from tfm_progress_manager import ProgressManager, OperationType

class FileManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        
        # Load configuration
        self.config = get_config()
        
        # Get startup paths from configuration
        left_startup_path, right_startup_path = get_startup_paths()
        
        # Initialize modular components
        self.log_manager = LogManager(self.config)
        self.pane_manager = PaneManager(self.config, left_startup_path, right_startup_path)
        self.file_operations = FileOperations(self.config)
        self.list_dialog = ListDialog(self.config)
        self.info_dialog = InfoDialog(self.config)
        self.search_dialog = SearchDialog(self.config)
        self.batch_rename_dialog = BatchRenameDialog(self.config)
        self.quick_choice_bar = QuickChoiceBar(self.config)
        self.general_dialog = GeneralPurposeDialog(self.config)
        self.external_program_manager = ExternalProgramManager(self.config, self.log_manager)
        self.progress_manager = ProgressManager()
        
        # Layout settings
        self.log_height_ratio = getattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO', DEFAULT_LOG_HEIGHT_RATIO)
        self.needs_full_redraw = True  # Flag to control when to redraw everything
        
        # Isearch mode state
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        

        
        # Dialog state (now handled by general_dialog)
        self.rename_file_path = None  # Still needed for rename operations
        

        self.should_quit = False  # Flag to control main loop exit

        # Add startup messages to log
        self.log_manager.add_startup_messages(VERSION, GITHUB_URL, APP_NAME)
        
        # Initialize colors with configured scheme
        color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
        init_colors(color_scheme)
        
        # Configure curses
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)
        
        # Track startup time for delayed redraw
        self.startup_time = time.time()
        
    def safe_addstr(self, y, x, text, attr=curses.A_NORMAL):
        """Safely add string to screen, handling boundary conditions"""
        try:
            height, width = self.stdscr.getmaxyx()
            
            # Check bounds
            if y < 0 or y >= height or x < 0 or x >= width:
                return
                
            # Truncate text if it would exceed screen width
            max_len = width - x - 1  # Leave space to avoid last column
            if max_len <= 0:
                return
                
            truncated_text = text[:max_len] if len(text) > max_len else text
            self.stdscr.addstr(y, x, truncated_text, attr)
        except curses.error:
            pass  # Ignore curses errors
    
    def clear_screen_with_background(self):
        """Clear screen and apply proper background color for current scheme"""
        try:
            # Try to apply background color to the window
            from tfm_colors import apply_background_to_window, get_background_color_pair
            
            # Clear the screen first
            self.stdscr.clear()
            
            # Try to apply the background color
            if apply_background_to_window(self.stdscr):
                # Background applied successfully
                pass
            else:
                # Fallback: manually fill screen with background color
                try:
                    height, width = self.stdscr.getmaxyx()
                    bg_color_pair = get_background_color_pair()
                    
                    # Fill the screen with spaces using the background color
                    for y in range(height):
                        try:
                            self.stdscr.addstr(y, 0, ' ' * (width - 1), bg_color_pair)
                        except curses.error:
                            pass  # Ignore errors at screen edges
                    
                    # Move cursor back to top
                    self.stdscr.move(0, 0)
                except:
                    pass  # If all else fails, just use regular clear
            
        except ImportError:
            # Fallback to regular clear if color functions not available
            self.stdscr.clear()
        except:
            # Any other error, use regular clear
            self.stdscr.clear()

    def is_key_for_action(self, key, action):
        """Check if a key matches a configured action"""
        if 32 <= key <= 126:  # Printable ASCII
            key_char = chr(key)
            return is_key_bound_to(key_char, action)
        return False
        
    def count_files_and_dirs(self, pane_data):
        """Count directories and files in a pane"""
        return self.pane_manager.count_files_and_dirs(pane_data)
        
    def draw_file_footers(self, y, left_pane_width):
        """Draw footer bars for left and right file panes"""
        # Left pane footer
        left_dirs, left_files = self.count_files_and_dirs(self.pane_manager.left_pane)
        left_selected = len(self.pane_manager.left_pane['selected_files'])
        left_sort = self.get_sort_description(self.pane_manager.left_pane)
        
        # Add filter info to footer if active
        left_filter_info = ""
        if self.pane_manager.left_pane['filter_pattern']:
            left_filter_info = f" | Filter: {self.pane_manager.left_pane['filter_pattern']}"
        
        if left_selected > 0:
            left_footer = f" {left_dirs} dirs, {left_files} files ({left_selected} selected) | Sort: {left_sort}{left_filter_info} "
        else:
            left_footer = f" {left_dirs} dirs, {left_files} files | Sort: {left_sort}{left_filter_info} "
        
        try:
            # Left pane footer with active indicator
            left_color = get_footer_color(self.pane_manager.active_pane == 'left')
            self.stdscr.addstr(y, 2, left_footer, left_color)
        except curses.error:
            pass
            
        # Right pane footer  
        right_dirs, right_files = self.count_files_and_dirs(self.pane_manager.right_pane)
        right_selected = len(self.pane_manager.right_pane['selected_files'])
        right_sort = self.get_sort_description(self.pane_manager.right_pane)
        
        # Add filter info to footer if active
        right_filter_info = ""
        if self.pane_manager.right_pane['filter_pattern']:
            right_filter_info = f" | Filter: {self.pane_manager.right_pane['filter_pattern']}"
        
        if right_selected > 0:
            right_footer = f" {right_dirs} dirs, {right_files} files ({right_selected} selected) | Sort: {right_sort}{right_filter_info} "
        else:
            right_footer = f" {right_dirs} dirs, {right_files} files | Sort: {right_sort}{right_filter_info} "
        
        try:
            # Right pane footer with active indicator
            right_color = get_footer_color(self.pane_manager.active_pane == 'right')
            self.stdscr.addstr(y, left_pane_width + 2, right_footer, right_color)
        except curses.error:
            pass
            
    def toggle_selection(self):
        """Toggle selection of current file/directory and move to next item"""
        current_pane = self.get_current_pane()
        success, message = self.file_operations.toggle_selection(current_pane, move_cursor=True, direction=1)
        if success:
            print(message)
            
    def toggle_selection_up(self):
        """Toggle selection of current file/directory and move to previous item"""
        current_pane = self.get_current_pane()
        success, message = self.file_operations.toggle_selection(current_pane, move_cursor=True, direction=-1)
        if success:
            print(message)
    
    def toggle_all_files_selection(self):
        """Toggle selection status of all files (not directories) in current pane"""
        current_pane = self.get_current_pane()
        success, message = self.file_operations.toggle_all_files_selection(current_pane)
        if success:
            print(message)
            self.needs_full_redraw = True
    
    def toggle_all_items_selection(self):
        """Toggle selection status of all items (files and directories) in current pane"""
        current_pane = self.get_current_pane()
        success, message = self.file_operations.toggle_all_items_selection(current_pane)
        if success:
            print(message)
            self.needs_full_redraw = True
    
    def sync_pane_directories(self):
        """Change current pane's directory to match the other pane's directory, or sync cursor if already same directory"""
        if self.pane_manager.sync_pane_directories(print):
            current_pane = self.get_current_pane()
            self.refresh_files(current_pane)
            
            # Try to restore cursor position for this directory
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            if not self.pane_manager.restore_cursor_position(current_pane, display_height):
                # If no history found, default to first item
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
            
            self.needs_full_redraw = True
    
    def sync_other_pane_directory(self):
        """Change other pane's directory to match the current pane's directory, or sync cursor if already same directory"""
        if self.pane_manager.sync_other_pane_directory(print):
            other_pane = self.get_inactive_pane()
            self.refresh_files(other_pane)
            
            # Try to restore cursor position for this directory
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            if not self.pane_manager.restore_cursor_position(other_pane, display_height):
                # If no history found, default to first item
                other_pane['selected_index'] = 0
                other_pane['scroll_offset'] = 0
            
            self.needs_full_redraw = True
    
    def sync_cursor_to_other_pane(self):
        """Move cursor in current pane to the same filename as the other pane's cursor"""
        if self.pane_manager.sync_cursor_to_other_pane(print):
            # Adjust scroll offset if needed to keep selection visible
            current_pane = self.get_current_pane()
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            self.pane_manager.adjust_scroll_for_selection(current_pane, display_height)
            self.needs_full_redraw = True
    
    def sync_cursor_from_current_pane(self):
        """Move cursor in other pane to the same filename as the current pane's cursor"""
        if self.pane_manager.sync_cursor_from_current_pane(print):
            # Adjust scroll offset if needed to keep selection visible
            other_pane = self.get_inactive_pane()
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            self.pane_manager.adjust_scroll_for_selection(other_pane, display_height)
            self.needs_full_redraw = True
        
    def restore_cursor_position(self, pane_data):
        """Restore cursor position from history - wrapper for pane_manager method"""
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        return self.pane_manager.restore_cursor_position(pane_data, display_height)
    
    def save_cursor_position(self, pane_data):
        """Save cursor position to history - wrapper for pane_manager method"""
        return self.pane_manager.save_cursor_position(pane_data)
    
    def adjust_scroll_for_selection(self, pane_data):
        """Adjust scroll for selection - wrapper for pane_manager method"""
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        return self.pane_manager.adjust_scroll_for_selection(pane_data, display_height)
    
    def separate_filename_extension(self, filename, is_dir=False):
        """
        Separate filename into basename and extension for display.
        Returns (basename, extension) tuple.
        
        Args:
            filename: The filename to separate
            is_dir: Whether this is a directory (directories don't get extension separation)
        
        Returns:
            tuple: (basename, extension) where extension includes the dot
        """
        # Don't separate extensions for directories
        if is_dir:
            return filename, ""
        
        # Check if extension separation is enabled
        if not getattr(self.config, 'SEPARATE_EXTENSIONS', True):
            return filename, ""
        
        # Find the last dot in the filename
        dot_index = filename.rfind('.')
        
        # If no dot found, or dot is at the beginning (hidden files), don't separate
        if dot_index <= 0:
            return filename, ""
        
        basename = filename[:dot_index]
        extension = filename[dot_index:]
        
        # Check extension length limit
        max_ext_length = getattr(self.config, 'MAX_EXTENSION_LENGTH', 5)
        if len(extension) > max_ext_length:
            return filename, ""
        
        return basename, extension
    
    def calculate_max_extension_width(self, pane_data):
        """
        Calculate the maximum extension width for files in the current pane.
        Returns the width needed for the extension column.
        """
        max_width = 0
        max_ext_length = getattr(self.config, 'MAX_EXTENSION_LENGTH', 5)
        
        for file_path in pane_data['files']:
            if file_path.is_file():
                _, extension = self.separate_filename_extension(file_path.name, file_path.is_dir())
                if extension and len(extension) <= max_ext_length:
                    max_width = max(max_width, len(extension))
        
        return max_width

    def apply_filter(self):
        """Apply filter - wrapper for file_operations method"""
        current_pane = self.get_current_pane()
        filter_pattern = self.filter_editor.get_text()
        count = self.file_operations.apply_filter(current_pane, filter_pattern)
        
        # Log the filter action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        
        if filter_pattern:
            print(f"Applied filter '{filter_pattern}' to {pane_name} pane")
            print(f"Showing {count} items")
        
        self.needs_full_redraw = True
    
    def clear_filter(self):
        """Clear filter - wrapper for file_operations method"""
        current_pane = self.get_current_pane()
        
        if self.file_operations.clear_filter(current_pane):
            # Log the clear action
            pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
            
            print(f"Cleared filter from {pane_name} pane")
            
            self.needs_full_redraw = True
    
    def restore_stdio(self):
        """Restore stdout/stderr to original state"""
        self.log_manager.restore_stdio()
            
    def __del__(self):
        """Restore stdout/stderr when object is destroyed"""
        self.restore_stdio()
        
    def get_current_pane(self):
        """Get the currently active pane"""
        return self.pane_manager.get_current_pane()
    
    def get_inactive_pane(self):
        """Get the inactive pane"""
        return self.pane_manager.get_inactive_pane()

    def get_log_scroll_percentage(self):
        """Calculate the current log scroll position as a percentage"""
        # Calculate display height for accurate scroll percentage
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        return self.log_manager.get_log_scroll_percentage(log_height)
    
    def _get_log_pane_height(self):
        """Calculate the current log pane height in lines"""
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        return log_height
    
    def refresh_files(self, pane=None):
        """Refresh the file list for specified pane or both panes"""
        panes_to_refresh = [pane] if pane else [self.pane_manager.left_pane, self.pane_manager.right_pane]
        
        for pane_data in panes_to_refresh:
            self.file_operations.refresh_files(pane_data)
    
    def sort_entries(self, entries, sort_mode, reverse=False):
        """Sort file entries based on the specified mode"""
        return self.file_operations.sort_entries(entries, sort_mode, reverse)
    
    def get_sort_description(self, pane_data):
        """Get a human-readable description of the current sort mode"""
        return self.file_operations.get_sort_description(pane_data)
            
    def get_file_info(self, path):
        """Get file information for display"""
        return self.file_operations.get_file_info(path)
            
    def draw_header(self):
        """Draw the header with pane paths and controls"""
        height, width = self.stdscr.getmaxyx()
        left_pane_width = int(width * self.pane_manager.left_pane_ratio)
        right_pane_width = width - left_pane_width
        
        # Clear header area (avoid last column)
        try:
            self.stdscr.addstr(0, 0, " " * (width - 1), get_header_color())
        except curses.error:
            pass
        
        # Left pane path with safety checks
        if left_pane_width > 6:  # Minimum space needed
            left_path = str(self.pane_manager.left_pane['path'])
            max_left_path_width = max(1, left_pane_width - 4)
            if len(left_path) > max_left_path_width:
                left_path = "..." + left_path[-(max(1, max_left_path_width-3)):]
            
            left_color = get_header_color(self.pane_manager.active_pane == 'left')
            try:
                self.stdscr.addstr(0, 2, left_path[:max_left_path_width], left_color)
            except curses.error:
                pass  # Ignore drawing errors for narrow panes
        
        # Separator with bounds check
        if 0 <= left_pane_width < width:
            try:
                self.stdscr.addstr(0, left_pane_width, "│", get_boundary_color())
            except curses.error:
                pass
        
        # Right pane path with safety checks
        if right_pane_width > 6:  # Minimum space needed
            right_path = str(self.pane_manager.right_pane['path'])
            max_right_path_width = max(1, right_pane_width - 4)
            if len(right_path) > max_right_path_width:
                right_path = "..." + right_path[-(max(1, max_right_path_width-3)):]
                
            right_color = get_header_color(self.pane_manager.active_pane == 'right')
            try:
                right_start_x = left_pane_width + 2
                if right_start_x < width:
                    self.stdscr.addstr(0, right_start_x, right_path[:max_right_path_width], right_color)
            except curses.error:
                pass  # Ignore drawing errors for narrow panes
        
        # No controls in header anymore - moved to status bar
        
    def draw_pane(self, pane_data, start_x, pane_width, is_active):
        """Draw a single pane"""
        # Safety checks to prevent crashes
        if pane_width < 10:  # Minimum viable pane width
            return
        if start_x < 0 or start_x >= self.stdscr.getmaxyx()[1]:
            return
            
        height, width = self.stdscr.getmaxyx()
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3  # Reserve space for header, footer, and status
        
        # Check if there are no files to display
        if not pane_data['files']:
            # Show "no items to show" message in the center of the pane
            message = "No items to show"
            message_y = 1 + display_height // 2  # Center vertically in the pane
            message_x = start_x + (pane_width - len(message)) // 2  # Center horizontally
            
            try:
                from tfm_colors import get_error_color
                self.stdscr.addstr(message_y, message_x, message, get_error_color())
            except (curses.error, ImportError):
                # Fallback if color function not available or position invalid
                try:
                    self.stdscr.addstr(message_y, start_x + 2, message)
                except curses.error:
                    pass
            return
        
        # Calculate scroll offset
        if pane_data['selected_index'] < pane_data['scroll_offset']:
            pane_data['scroll_offset'] = pane_data['selected_index']
        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
            pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
            
        # Draw files
        for i in range(display_height):
            file_index = i + pane_data['scroll_offset']
            y = i + 1  # Start after header (no controls line anymore)
            
            if file_index >= len(pane_data['files']):
                break
                
            file_path = pane_data['files'][file_index]
            
            # Determine display name and attributes
            # Parent directory (..) is no longer shown
            display_name = file_path.name
            is_dir = file_path.is_dir()
                
            # Get file info
            size_str, mtime_str = self.get_file_info(file_path)
            
            # Check if this file is multi-selected
            is_multi_selected = str(file_path) in pane_data['selected_files']
            
            # Check if this file is an isearch match
            is_search_match = (self.isearch_mode and is_active and 
                             file_index in self.isearch_matches)
            
            # Choose color based on file properties and selection
            is_executable = file_path.is_file() and os.access(file_path, os.X_OK)
            is_selected = file_index == pane_data['selected_index']
            
            color = get_file_color(is_dir, is_executable, is_selected, is_active)
            
            # Handle search match highlighting (takes precedence over multi-selection)
            if is_search_match and not is_selected:
                # Highlight search matches with underline
                base_color = get_file_color(is_dir, is_executable, False, False)
                color = base_color | curses.A_UNDERLINE
            # Handle multi-selection highlighting
            elif is_multi_selected and not is_selected:
                # Get base color and add standout for multi-selected files
                base_color = get_file_color(is_dir, is_executable, False, False)
                color = base_color | curses.A_STANDOUT
                
            # Add selection marker for multi-selected files
            selection_marker = "●" if is_multi_selected else " "
            
            # Separate filename into basename and extension
            basename, extension = self.separate_filename_extension(display_name, is_dir)
            
            # Format line to fit pane - with safety checks for narrow panes
            datetime_width = 16  # "YYYY-MM-DD HH:MM" = 16 characters
            size_width = 8
            marker_width = 2  # Space for selection marker
            
            # Safety check: ensure we have minimum space for formatting
            if pane_width < 20:  # Too narrow to display properly
                line = f"{selection_marker} {display_name[:pane_width-5]}..."
            else:
                # Calculate precise filename width for column alignment
                # Account for the fact that line will be truncated to pane_width-2
                usable_width = pane_width - 2
                
                if pane_width < 60:
                    # For narrow panes: "● basename ext size" (no datetime)
                    if extension:
                        # Calculate actual maximum extension width for this pane
                        ext_width = self.calculate_max_extension_width(pane_data)
                        if ext_width == 0:  # No extensions in this pane
                            ext_width = len(extension)
                        
                        # Reserve space for: marker(2) + space(1) + ext_width + space(1) + size(8) = 12 + ext_width
                        name_width = usable_width - (12 + ext_width)
                        
                        # Truncate basename only if necessary
                        if len(basename) > name_width:
                            truncate_at = max(1, name_width - 3)  # Reserve 3 for "..."
                            basename = basename[:truncate_at] + "..."
                        
                        # Pad basename to maintain column alignment
                        padded_basename = basename.ljust(name_width)
                        padded_extension = extension.ljust(ext_width)
                        line = f"{selection_marker} {padded_basename} {padded_extension}{size_str:>8}"
                    else:
                        # No extension separation - use full width for filename
                        # Reserve space for: marker(2) + space(1) + size(8) = 11
                        name_width = usable_width - 11
                        
                        # Truncate filename only if necessary
                        if len(display_name) > name_width:
                            truncate_at = max(1, name_width - 3)  # Reserve 3 for "..."
                            display_name = display_name[:truncate_at] + "..."
                        
                        # Pad filename to maintain column alignment
                        padded_name = display_name.ljust(name_width)
                        line = f"{selection_marker} {padded_name}{size_str:>8}"
                else:
                    # For wider panes: "● basename ext size datetime"
                    if extension:
                        # Calculate actual maximum extension width for this pane
                        ext_width = self.calculate_max_extension_width(pane_data)
                        if ext_width == 0:  # No extensions in this pane
                            ext_width = len(extension)
                        
                        # Reserve space for: marker(2) + space(1) + ext_width + space(1) + size(8) + space(1) + datetime(len) = 13 + ext_width + datetime_width
                        name_width = usable_width - (13 + ext_width + datetime_width)
                        
                        # Truncate basename only if necessary
                        if len(basename) > name_width:
                            truncate_at = max(1, name_width - 3)  # Reserve 3 for "..."
                            basename = basename[:truncate_at] + "..."
                        
                        # Pad basename to maintain column alignment
                        padded_basename = basename.ljust(name_width)
                        padded_extension = extension.ljust(ext_width)
                        line = f"{selection_marker} {padded_basename} {padded_extension} {size_str:>8} {mtime_str}"
                    else:
                        # No extension separation - use full width for filename
                        # Reserve space for: marker(2) + space(1) + size(8) + space(1) + datetime(len) = 12 + datetime_width
                        name_width = usable_width - (12 + datetime_width)
                        
                        # Truncate filename only if necessary
                        if len(display_name) > name_width:
                            truncate_at = max(1, name_width - 3)  # Reserve 3 for "..."
                            display_name = display_name[:truncate_at] + "..."
                        
                        # Pad filename to maintain column alignment
                        padded_name = display_name.ljust(name_width)
                        line = f"{selection_marker} {padded_name} {size_str:>8} {mtime_str}"
            
            try:
                self.stdscr.addstr(y, start_x + 1, line[:pane_width-2], color)
            except curses.error:
                pass  # Ignore if we can't write to screen edge
                
    def draw_files(self):
        """Draw both file panes"""
        height, width = self.stdscr.getmaxyx()
        left_pane_width = int(width * self.pane_manager.left_pane_ratio)
        right_pane_width = width - left_pane_width
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        # Always reserve space for footer line (1) and status line (1)
        # Plus log content if visible
        file_pane_bottom = height - log_height - 2
        
        # Draw vertical separator for file panes
        for y in range(1, file_pane_bottom):
            try:
                self.stdscr.addstr(y, left_pane_width, "│", get_boundary_color())
            except curses.error:
                pass
        
        # Draw left pane
        self.draw_pane(self.pane_manager.left_pane, 0, left_pane_width, self.pane_manager.active_pane == 'left')
        
        # Draw right pane
        self.draw_pane(self.pane_manager.right_pane, left_pane_width, right_pane_width, self.pane_manager.active_pane == 'right')
        
    def draw_log_pane(self):
        """Draw the log pane at the bottom"""
        height, width = self.stdscr.getmaxyx()
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        left_pane_width = int(width * self.pane_manager.left_pane_ratio)
        
        # Always draw the file list footers at the correct position
        if log_height == 0:
            # When log is hidden, footers go right above status line
            footer_y = height - 2
        else:
            # When log is visible, footers go above the log area
            footer_y = height - log_height - 2
            
        # Draw horizontal separator and file list footers
        try:
            separator_line = "─" * width
            self.stdscr.addstr(footer_y, 0, separator_line, get_boundary_color())
            
            # Always draw file list footers
            self.draw_file_footers(footer_y, left_pane_width)
        except curses.error:
            pass
            
        # If log pane is hidden (0 height), don't draw log content
        if log_height == 0:
            return
            
        # Log content starts right after the footer line
        log_start_y = footer_y + 1
        
        # Use log manager to draw the log content
        self.log_manager.draw_log_pane(self.stdscr, log_start_y, log_height, width)
                
    def draw_status(self):
        """Draw status line with file info and controls"""
        height, width = self.stdscr.getmaxyx()
        status_y = height - 1
        
        current_pane = self.get_current_pane()
        
        # Progress display takes precedence over everything else during operations
        if self.progress_manager.is_operation_active():
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Get formatted progress text from progress manager
            progress_text = self.progress_manager.get_progress_text(width - 4)
            
            # Draw progress text
            self.safe_addstr(status_y, 2, progress_text, get_status_color())
            return

        # If in quick choice mode, show quick choice bar
        if self.quick_choice_bar.mode:
            self.quick_choice_bar.draw(self.stdscr, self.safe_addstr, status_y, width)
            return
        
        # All dialogs are now handled as overlays in main drawing loop
        
        # If in isearch mode, show isearch interface
        if self.isearch_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Show isearch prompt and pattern
            isearch_prompt = f"Isearch: {self.isearch_pattern}"
            if self.isearch_matches:
                match_info = f" ({self.isearch_match_index + 1}/{len(self.isearch_matches)} matches)"
                isearch_prompt += match_info
            else:
                if self.isearch_pattern.strip():
                    isearch_prompt += " (no matches)"
                else:
                    isearch_prompt += " (enter patterns separated by spaces)"
                
            # Add cursor indicator
            isearch_prompt += "_"
            
            # Draw isearch prompt
            self.safe_addstr(status_y, 2, isearch_prompt, get_status_color())
            
            # Show help text on the right if there's space
            help_text = "ESC:exit Enter:accept ↑↓:navigate Space:multi-pattern"
            if len(isearch_prompt) + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > len(isearch_prompt) + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
            else:
                # Shorter help text for narrow terminals
                short_help = "ESC:exit Enter:accept ↑↓:nav"
                if len(isearch_prompt) + len(short_help) + 6 < width:
                    help_x = width - len(short_help) - 3
                    if help_x > len(isearch_prompt) + 4:
                        self.safe_addstr(status_y, help_x, short_help, get_status_color() | curses.A_DIM)
            return
        
        # Normal status display
        # Left side: status info
        status_parts = []
        if self.file_operations.show_hidden:
            status_parts.append("showing hidden")

        left_status = f"({', '.join(status_parts)})" if status_parts else ""
        
        # Simple help message - detailed controls available in help dialog
        controls = "Press ? for help  •  Tab:switch panes  •  Enter:open  •  q:quit"
        
        # Draw status line with background color
        # Fill entire status line with background color
        status_line = " " * (width - 1)
        self.safe_addstr(status_y, 0, status_line, get_status_color())
        
        # Draw status info and controls
        if left_status:
            # Draw left status
            self.safe_addstr(status_y, 2, left_status, get_status_color())
            
            # Right-align controls if there's space
            if len(left_status) + len(controls) + 8 < width:
                controls_x = width - len(controls) - 3
                self.safe_addstr(status_y, controls_x, controls, get_status_color())
            else:
                # Center controls if no room for both
                controls_x = max(2, (width - len(controls)) // 2)
                self.safe_addstr(status_y, controls_x, controls, get_status_color())
        else:
            # Center controls when no left status
            controls_x = max(2, (width - len(controls)) // 2)
            self.safe_addstr(status_y, controls_x, controls, get_status_color())
        
    def handle_enter(self):
        """Handle Enter key - navigate or open file"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Parent directory (..) is no longer shown
        if selected_file.is_dir():
            try:
                # Save current cursor position before changing directory
                self.save_cursor_position(current_pane)
                
                current_pane['path'] = selected_file
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
                current_pane['selected_files'].clear()  # Clear selections when changing directory
                self.refresh_files(current_pane)
                
                # Try to restore cursor position for this directory
                if not self.restore_cursor_position(current_pane):
                    # If no history found, default to first item
                    current_pane['selected_index'] = 0
                    current_pane['scroll_offset'] = 0
                
                self.needs_full_redraw = True
            except PermissionError:
                self.show_error("Permission denied")
        else:
            # For files, try to open in text viewer if it's a text file
            if is_text_file(selected_file):
                # Save current screen state
                curses.curs_set(0)
                
                # Open text viewer
                if view_text_file(self.stdscr, selected_file):
                    # Text viewer completed successfully
                    print(f"Viewed file: {selected_file.name}")
                else:
                    # Fallback to file info if viewer failed
                    self.show_info(f"File: {selected_file.name}")
                
                # Restore TFM display
                self.needs_full_redraw = True
            else:
                # For non-text files, show file info
                self.show_info(f"File: {selected_file.name}")
            
    def show_error(self, message):
        """Show error message"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height - 1, 2, f"ERROR: {message}", get_error_color())
        self.stdscr.refresh()
        curses.napms(2000)  # Show for 2 seconds
        
    def show_info(self, message):
        """Show info message"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height - 1, 2, message)
        self.stdscr.refresh()
        curses.napms(1500)  # Show for 1.5 seconds
        
    def find_matches(self, pattern):
        """Find all files matching the fnmatch patterns in current pane
        
        Supports multiple space-delimited patterns where all patterns must match.
        For example: "ab*c 12?3" will match files that contain both "*ab*c*" and "*12?3*"
        """
        current_pane = self.get_current_pane()
        return self.file_operations.find_matches(current_pane, pattern, match_all=True, return_indices_only=True)
        
    def update_isearch_matches(self):
        """Update isearch matches and move cursor to nearest match"""
        self.isearch_matches = self.find_matches(self.isearch_pattern)
        
        if self.isearch_matches:
            current_pane = self.get_current_pane()
            current_index = current_pane['selected_index']
            
            # Find the next match at or after current position
            next_match = None
            for match_idx in self.isearch_matches:
                if match_idx >= current_index:
                    next_match = match_idx
                    break
                    
            # If no match found after current position, wrap to first match
            if next_match is None:
                next_match = self.isearch_matches[0]
                
            # Update cursor position
            current_pane['selected_index'] = next_match
            self.isearch_match_index = self.isearch_matches.index(next_match)
            
            # Ensure the selected item is visible (adjust scroll if needed)
            self.adjust_scroll_for_selection(current_pane)
        else:
            self.isearch_match_index = 0
            
    def adjust_scroll_for_selection(self, pane_data):
        """Ensure the selected item is visible by adjusting scroll offset"""
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3  # Reserve space for header, footer, and status
        
        # Adjust scroll offset to keep selection visible
        if pane_data['selected_index'] < pane_data['scroll_offset']:
            pane_data['scroll_offset'] = pane_data['selected_index']
        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
            pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
            
    def enter_isearch_mode(self):
        """Enter isearch mode"""
        self.isearch_mode = True
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        self.needs_full_redraw = True
        
    def exit_isearch_mode(self):
        """Exit isearch mode"""
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        self.needs_full_redraw = True
    
    def enter_filter_mode(self):
        """Enter filename filter mode"""
        current_pane = self.get_current_pane()
        DialogHelpers.create_filter_dialog(self.general_dialog, current_pane['filter_pattern'])
        self.general_dialog.callback = self.on_filter_confirm
        self.general_dialog.cancel_callback = self.on_filter_cancel
        self.needs_full_redraw = True
        
    def on_filter_confirm(self, filter_text):
        """Handle filter confirmation"""
        current_pane = self.get_current_pane()
        count = self.file_operations.apply_filter(current_pane, filter_text)
        
        # Log the filter action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        
        if filter_text:
            print(f"Applied filter '{filter_text}' to {pane_name} pane")
            print(f"Showing {count} items")
        
        self.general_dialog.hide()
        self.needs_full_redraw = True
    
    def on_filter_cancel(self):
        """Handle filter cancellation"""
        self.general_dialog.hide()
        self.needs_full_redraw = True
    
    def apply_filter(self):
        """Apply the current filter pattern to the active pane"""
        current_pane = self.get_current_pane()
        filter_pattern = self.filter_editor.text
        current_pane['filter_pattern'] = filter_pattern
        current_pane['selected_index'] = 0  # Reset selection to top
        current_pane['scroll_offset'] = 0
        self.refresh_files(current_pane)
        
        # Log the filter action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        if filter_pattern:
            print(f"Applied filter '{filter_pattern}' to {pane_name} pane")
        else:
            print(f"Cleared filter from {pane_name} pane")
        
        self.needs_full_redraw = True
    
    def clear_filter(self):
        """Clear the filter from the active pane"""
        current_pane = self.get_current_pane()
        current_pane['filter_pattern'] = ""
        current_pane['selected_index'] = 0  # Reset selection to top
        current_pane['scroll_offset'] = 0
        self.refresh_files(current_pane)
        
        # Log the clear action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        print(f"Cleared filter from {pane_name} pane")
        
        self.needs_full_redraw = True
    
    def enter_rename_mode(self):
        """Enter rename mode for the current file or batch rename for multiple files"""
        current_pane = self.get_current_pane()
        
        # Check if multiple files are selected
        if len(current_pane['selected_files']) > 1:
            # Enter batch rename mode
            self.enter_batch_rename_mode()
            return
        
        # Get the current file
        if not current_pane['files']:
            print("No files to rename")
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Parent directory (..) is no longer shown, so no need to check for it
        
        # Enter rename mode using general dialog
        self.rename_file_path = selected_file
        DialogHelpers.create_rename_dialog(self.general_dialog, selected_file.name, selected_file.name)
        self.general_dialog.callback = self.on_rename_confirm
        self.general_dialog.cancel_callback = self.on_rename_cancel
        self.needs_full_redraw = True
        print(f"Renaming: {selected_file.name}")
    
    def on_rename_confirm(self, new_name):
        """Handle rename confirmation"""
        if not self.rename_file_path or not new_name.strip():
            print("Invalid rename operation")
            self.general_dialog.hide()
            self.rename_file_path = None
            self.needs_full_redraw = True
            return
        
        original_name = self.rename_file_path.name
        
        if new_name == original_name:
            print("Name unchanged")
            self.general_dialog.hide()
            self.rename_file_path = None
            self.needs_full_redraw = True
            return
        
        try:
            # Perform the rename
            new_path = self.rename_file_path.parent / new_name
            
            # Check if target already exists
            if new_path.exists():
                print(f"File '{new_name}' already exists")
                self.general_dialog.hide()
                self.rename_file_path = None
                self.needs_full_redraw = True
                return
            
            # Perform the rename
            self.rename_file_path.rename(new_path)
            print(f"Renamed '{original_name}' to '{new_name}'")
            
            # Refresh the current pane
            current_pane = self.get_current_pane()
            self.refresh_files(current_pane)
            
            # Try to select the renamed file
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_name:
                    current_pane['selected_index'] = i
                    self.adjust_scroll_for_selection(current_pane)
                    break
            
            self.general_dialog.hide()
            self.rename_file_path = None
            self.needs_full_redraw = True
            
        except PermissionError:
            print(f"Permission denied: Cannot rename '{original_name}'")
            self.general_dialog.hide()
            self.rename_file_path = None
            self.needs_full_redraw = True
        except OSError as e:
            print(f"Error renaming file: {e}")
            self.general_dialog.hide()
            self.rename_file_path = None
            self.needs_full_redraw = True
    
    def on_rename_cancel(self):
        """Handle rename cancellation"""
        print("Rename cancelled")
        self.general_dialog.hide()
        self.rename_file_path = None
        self.needs_full_redraw = True
    
    def enter_create_directory_mode(self):
        """Enter create directory mode"""
        current_pane = self.get_current_pane()
        
        # Check if current directory is writable
        if not os.access(current_pane['path'], os.W_OK):
            print(f"Permission denied: Cannot create directory in {current_pane['path']}")
            return
        
        # Enter create directory mode using general dialog
        DialogHelpers.create_create_directory_dialog(self.general_dialog)
        self.general_dialog.callback = self.on_create_directory_confirm
        self.general_dialog.cancel_callback = self.on_create_directory_cancel
        self.needs_full_redraw = True
        print("Creating new directory...")
    
    def on_create_directory_confirm(self, dir_name):
        """Handle create directory confirmation"""
        if not dir_name.strip():
            print("Invalid directory name")
            self.general_dialog.hide()
            self.needs_full_redraw = True
            return
        
        current_pane = self.get_current_pane()
        new_dir_name = dir_name.strip()
        new_dir_path = current_pane['path'] / new_dir_name
        
        # Check if directory already exists
        if new_dir_path.exists():
            print(f"Directory '{new_dir_name}' already exists")
            self.general_dialog.hide()
            self.needs_full_redraw = True
            return
        
        try:
            # Create the directory
            new_dir_path.mkdir(parents=True, exist_ok=False)
            print(f"Created directory: {new_dir_name}")
            
            # Refresh the current pane
            self.refresh_files(current_pane)
            
            # Try to select the new directory
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_dir_name:
                    current_pane['selected_index'] = i
                    self.adjust_scroll_for_selection(current_pane)
                    break
            
            self.general_dialog.hide()
            self.needs_full_redraw = True
            
        except OSError as e:
            print(f"Failed to create directory '{new_dir_name}': {e}")
            self.general_dialog.hide()
            self.needs_full_redraw = True
    
    def on_create_directory_cancel(self):
        """Handle create directory cancellation"""
        print("Directory creation cancelled")
        self.general_dialog.hide()
        self.needs_full_redraw = True
    
    def enter_create_file_mode(self):
        """Enter create file mode"""
        current_pane = self.get_current_pane()
        
        # Check if current directory is writable
        if not os.access(current_pane['path'], os.W_OK):
            print(f"Permission denied: Cannot create file in {current_pane['path']}")
            return
        
        # Enter create file mode using general dialog
        DialogHelpers.create_create_file_dialog(self.general_dialog)
        self.general_dialog.callback = self.on_create_file_confirm
        self.general_dialog.cancel_callback = self.on_create_file_cancel
        self.needs_full_redraw = True
        print("Creating new text file...")
    
    def on_create_file_confirm(self, file_name):
        """Handle create file confirmation"""
        if not file_name.strip():
            print("Invalid file name")
            self.general_dialog.hide()
            self.needs_full_redraw = True
            return
        
        current_pane = self.get_current_pane()
        new_file_name = file_name.strip()
        new_file_path = current_pane['path'] / new_file_name
        
        # Check if file already exists
        if new_file_path.exists():
            print(f"File '{new_file_name}' already exists")
            self.general_dialog.hide()
            self.needs_full_redraw = True
            return
        
        try:
            # Create the file
            new_file_path.touch()
            print(f"Created file: {new_file_name}")
            
            # Refresh the current pane
            self.refresh_files(current_pane)
            
            # Try to select the new file
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_file_name:
                    current_pane['selected_index'] = i
                    self.adjust_scroll_for_selection(current_pane)
                    break
            
            # Open the file for editing if it's a text file
            if is_text_file(new_file_path):
                self.edit_selected_file()
            
            self.general_dialog.hide()
            self.needs_full_redraw = True
            
        except OSError as e:
            print(f"Failed to create file '{new_file_name}': {e}")
            self.general_dialog.hide()
            self.needs_full_redraw = True
    
    def on_create_file_cancel(self):
        """Handle create file cancellation"""
        print("File creation cancelled")
        self.general_dialog.hide()
        self.needs_full_redraw = True

    def enter_batch_rename_mode(self):
        """Enter batch rename mode for multiple selected files"""
        current_pane = self.get_current_pane()
        
        if len(current_pane['selected_files']) < 2:
            print("Select multiple files for batch rename")
            return
        
        # Get selected files using helper (only files, not directories for safety)
        selected_files = []
        for file_path_str in current_pane['selected_files']:
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.is_file():
                selected_files.append(file_path)
        
        if not selected_files:
            print("No files selected for batch rename")
            return
        
        if self.batch_rename_dialog.show(selected_files):
            self.needs_full_redraw = True
            self._force_immediate_redraw()
            print(f"Batch rename mode: {len(selected_files)} files selected")
    
    def exit_batch_rename_mode(self):
        """Exit batch rename mode - wrapper for batch rename dialog component"""
        self.batch_rename_dialog.exit()
        self.needs_full_redraw = True
    
    def update_batch_rename_preview(self):
        """Update the preview list for batch rename - wrapper for batch rename dialog component"""
        self.batch_rename_dialog.update_preview()
    
    def perform_batch_rename(self):
        """Perform the batch rename operation - wrapper for batch rename dialog component"""
        success_count, errors = self.batch_rename_dialog.perform_rename()
        
        # Report results using helper
        result_message = BatchRenameDialogHelpers.format_rename_results(success_count, errors)
        print(result_message)
        
        # Clear selections and refresh
        current_pane = self.get_current_pane()
        current_pane['selected_files'].clear()
        self.refresh_files(current_pane)
        
        self.exit_batch_rename_mode()
        
    def show_dialog(self, message, choices, callback):
        """Show quick choice dialog - wrapper for quick choice bar component
        
        Args:
            message: The message to display
            choices: List of choice dictionaries with format:
                     [{"text": "Yes", "key": "y", "value": True}, 
                      {"text": "No", "key": "n", "value": False},
                      {"text": "Cancel", "key": "c", "value": None}]
            callback: Function to call with the selected choice's value
        """
        self.quick_choice_bar.show(message, choices, callback)
        self.needs_full_redraw = True
    
    def show_confirmation(self, message, callback):
        """Show confirmation dialog with Yes/No/Cancel options (backward compatibility)"""
        QuickChoiceBarHelpers.show_confirmation(self.quick_choice_bar, message, callback)
        self.needs_full_redraw = True
        
    def exit_quick_choice_mode(self):
        """Exit quick choice mode - wrapper for quick choice bar component"""
        self.quick_choice_bar.exit()
        self.needs_full_redraw = True
    
    def exit_confirmation_mode(self):
        """Exit confirmation mode (backward compatibility)"""
        self.exit_quick_choice_mode()
        
    def handle_quick_choice_input(self, key):
        """Handle input while in quick choice mode - wrapper for quick choice bar component"""
        result = self.quick_choice_bar.handle_input(key)
        
        if result == True:
            self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'cancel':
                self.exit_quick_choice_mode()
                return True
            elif action == 'selection_changed':
                self.needs_full_redraw = True
                return True
            elif action == 'execute':
                if self.quick_choice_bar.callback:
                    self.quick_choice_bar.callback(data)
                self.exit_quick_choice_mode()
                return True
        
        return False
    
    def handle_dialog_input(self, key):
        """Handle input while in dialog mode (backward compatibility)"""
        return self.handle_quick_choice_input(key)
    
    def handle_confirmation_input(self, key):
        """Handle input while in confirmation mode (backward compatibility)"""
        return self.handle_quick_choice_input(key)
    

    def show_info_dialog(self, title, info_lines):
        """Show an information dialog with scrollable content - wrapper for info dialog component"""
        self.info_dialog.show(title, info_lines)
        self.needs_full_redraw = True
        
        # Force immediate display of the dialog
        self._force_immediate_redraw()
    
    def _force_immediate_redraw(self):
        """Force an immediate screen redraw to show dialogs instantly"""
        # Perform the same drawing sequence as the main loop
        self.refresh_files()
        self.clear_screen_with_background()
        self.draw_header()
        self.draw_files()
        self.draw_log_pane()
        self.draw_status()
        
        # Draw dialog overlays
        if self.list_dialog.mode:
            self.list_dialog.draw(self.stdscr, self.safe_addstr)
        elif self.info_dialog.mode:
            self.info_dialog.draw(self.stdscr, self.safe_addstr)
        elif self.search_dialog.mode:
            self.search_dialog.draw(self.stdscr, self.safe_addstr)
        elif self.batch_rename_dialog.mode:
            self.batch_rename_dialog.draw(self.stdscr, self.safe_addstr)
        
        # Refresh screen immediately
        self.stdscr.refresh()
        self.needs_full_redraw = False

    def show_list_dialog(self, title, items, callback):
        """Show a searchable list dialog - wrapper for list dialog component"""
        self.list_dialog.show(title, items, callback)
        self.needs_full_redraw = True
        
        # Force immediate display of the dialog
        self._force_immediate_redraw()
    
    def exit_info_dialog_mode(self):
        """Exit info dialog mode - wrapper for info dialog component"""
        self.info_dialog.exit()
        self.needs_full_redraw = True
    
    def exit_list_dialog_mode(self):
        """Exit list dialog mode - wrapper for list dialog component"""
        self.list_dialog.exit()
        self.needs_full_redraw = True
    
    def handle_info_dialog_input(self, key):
        """Handle input while in info dialog mode - wrapper for info dialog component"""
        if self.info_dialog.handle_input(key):
            self.needs_full_redraw = True
            return True
        return False
    
    def handle_list_dialog_input(self, key):
        """Handle input while in list dialog mode - wrapper for list dialog component"""
        if self.list_dialog.handle_input(key):
            self.needs_full_redraw = True
            return True
        return False
    
    def show_list_dialog_demo(self):
        """Demo function to show the searchable list dialog"""
        ListDialogHelpers.show_demo(self.list_dialog)
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def show_file_type_filter(self):
        """Show file type filter using the searchable list dialog"""
        current_pane = self.get_current_pane()
        ListDialogHelpers.show_file_type_filter(self.list_dialog, current_pane)
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def show_favorite_directories(self):
        """Show favorite directories using the searchable list dialog"""
        # Create a wrapper print function that also triggers redraw
        def print_with_redraw(message):
            print(message)
            self.needs_full_redraw = True
            
        ListDialogHelpers.show_favorite_directories(
            self.list_dialog, self.pane_manager, print_with_redraw
        )
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def show_programs_dialog(self):
        """Show external programs using the searchable list dialog"""
        def execute_program_wrapper(program):
            self.stdscr = self.external_program_manager.execute_external_program(
                self.stdscr, self.pane_manager, program
            )
            self.needs_full_redraw = True
        
        ListDialogHelpers.show_programs_dialog(
            self.list_dialog, execute_program_wrapper, print
        )
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def show_compare_selection_dialog(self):
        """Show compare selection dialog to select files based on comparison with other pane"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Create a wrapper print function that also triggers redraw
        def print_with_redraw(message):
            print(message)
            self.needs_full_redraw = True
        
        ListDialogHelpers.show_compare_selection(
            self.list_dialog, current_pane, other_pane, print_with_redraw
        )
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def show_view_options(self):
        """Show view options dialog with toggle options"""
        def handle_view_option(option):
            if option is None:
                return  # User cancelled
            
            if option == "Toggle hidden files":
                old_state = self.file_operations.show_hidden
                new_state = self.file_operations.toggle_hidden_files()
                # Reset both panes
                self.pane_manager.left_pane['selected_index'] = 0
                self.pane_manager.left_pane['scroll_offset'] = 0
                self.pane_manager.right_pane['selected_index'] = 0
                self.pane_manager.right_pane['scroll_offset'] = 0
                print(f"Hidden files: {'shown' if new_state else 'hidden'}")
                self.needs_full_redraw = True
                
            elif option == "Toggle color scheme (dark/light)":
                from tfm_colors import toggle_color_scheme, init_colors
                new_scheme = toggle_color_scheme()
                init_colors(new_scheme)
                print(f"Switched to {new_scheme} color scheme")
                self.print_color_scheme_info()
                self.needs_full_redraw = True
                
            elif option == "Toggle fallback color scheme":
                from tfm_colors import toggle_fallback_mode, init_colors, is_fallback_mode
                new_state = toggle_fallback_mode()
                # Re-initialize colors with current scheme
                color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
                init_colors(color_scheme)
                status = "enabled" if new_state else "disabled"
                print(f"Fallback color mode: {status}")
                self.needs_full_redraw = True
        
        # Define the view options
        options = [
            "Toggle hidden files",
            "Toggle color scheme (dark/light)", 
            "Toggle fallback color scheme"
        ]
        
        self.show_list_dialog("View Options", options, handle_view_option)
        self._force_immediate_redraw()

    def show_settings_menu(self):
        """Show settings menu with configuration options"""
        def handle_settings_option(option):
            if option is None:
                return  # User cancelled
            
            if option == "Edit config.py (~/.tfm/config.py)":
                config_path = os.path.expanduser("~/.tfm/config.py")
                
                # Check if config file exists
                if not os.path.exists(config_path):
                    print(f"Config file not found: {config_path}")
                    print("TFM should have created this file automatically on startup.")
                    return
                
                # Try to open the config file with the configured text editor
                try:
                    # Get the configured text editor
                    from tfm_const import DEFAULT_TEXT_EDITOR
                    editor = getattr(self.config, 'TEXT_EDITOR', DEFAULT_TEXT_EDITOR)
                    
                    # Suspend curses
                    self.external_program_manager.suspend_curses(self.stdscr)
                    
                    # Launch the text editor as a subprocess
                    result = subprocess.run([editor, config_path])
                    
                    # Resume curses
                    self.external_program_manager.resume_curses(self.stdscr)
                    
                    if result.returncode == 0:
                        print(f"Edited config file: {config_path}")
                    else:
                        print(f"Editor exited with code {result.returncode}")
                    
                    self.needs_full_redraw = True
                    
                except FileNotFoundError:
                    # Resume curses even if editor not found
                    self.external_program_manager.resume_curses(self.stdscr)
                    print(f"Text editor '{editor}' not found. Please install it or configure a different editor.")
                    print("You can manually edit the file at: " + config_path)
                except Exception as e:
                    # Resume curses even if there's an error
                    self.external_program_manager.resume_curses(self.stdscr)
                    print(f"Error opening config file: {e}")
                    print("You can manually edit the file at: " + config_path)
                
            elif option == "Reload config.py":
                try:
                    # Reload the configuration
                    from tfm_config import get_config
                    # Force reload by clearing any cached config
                    import importlib
                    import tfm_config
                    importlib.reload(tfm_config)
                    
                    # Get the new config
                    old_config = self.config
                    self.config = get_config()
                    
                    # Apply any config changes that need immediate effect
                    if hasattr(self.config, 'COLOR_SCHEME'):
                        from tfm_colors import init_colors
                        init_colors(self.config.COLOR_SCHEME)
                        print(f"Applied color scheme: {self.config.COLOR_SCHEME}")
                    
                    if hasattr(self.config, 'SHOW_HIDDEN_FILES'):
                        self.file_operations.show_hidden = self.config.SHOW_HIDDEN_FILES
                        print(f"Hidden files setting: {'shown' if self.config.SHOW_HIDDEN_FILES else 'hidden'}")
                    
                    if hasattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO'):
                        self.log_height_ratio = self.config.DEFAULT_LOG_HEIGHT_RATIO
                        print(f"Log height ratio: {self.config.DEFAULT_LOG_HEIGHT_RATIO}")
                    
                    print("Configuration reloaded successfully")
                    self.needs_full_redraw = True
                    
                except Exception as e:
                    print(f"Error reloading configuration: {e}")
                    print("Please check your config file for syntax errors")
                
            elif option == "Report issues":
                try:
                    # Open the GitHub issues page
                    webbrowser.open("https://github.com/shimomut/tfm/issues")
                    print("Opened GitHub issues page in your default browser")
                except Exception as e:
                    print(f"Error opening browser: {e}")
                    print("Please visit: https://github.com/shimomut/tfm/issues")
        
        # Define the settings options
        options = [
            "Edit config.py (~/.tfm/config.py)",
            "Reload config.py",
            "Report issues"
        ]
        
        self.show_list_dialog("Settings", options, handle_settings_option)
        self._force_immediate_redraw()

    def show_sort_menu(self):
        """Show sort options menu using the quick choice dialog"""
        current_pane = self.get_current_pane()
        
        # Get current sort mode for display
        current_mode = current_pane['sort_mode']
        current_reverse = current_pane['sort_reverse']
        
        # Define the sort choices with current mode indication
        choices = [
            {"text": f"Name {'★' if current_mode == 'name' else ''}", "key": "n", "value": "name"},
            {"text": f"Ext {'★' if current_mode == 'ext' else ''}", "key": "e", "value": "ext"},
            {"text": f"Size {'★' if current_mode == 'size' else ''}", "key": "s", "value": "size"},
            {"text": f"Date {'★' if current_mode == 'date' else ''}", "key": "d", "value": "date"},
            {"text": f"Reverse {'★' if current_reverse else ''}", "key": "r", "value": "reverse"},
            {"text": "Cancel", "key": "c", "value": None}
        ]
        
        def handle_sort_choice(sort_type):
            if sort_type is None:
                print("Sort cancelled")
                return
                
            if sort_type == "reverse":
                # Toggle reverse order
                current_pane['sort_reverse'] = not current_pane['sort_reverse']
                reverse_status = "enabled" if current_pane['sort_reverse'] else "disabled"
                print(f"Reverse sorting {reverse_status}")
            elif sort_type in ["name", "ext", "size", "date"]:
                # Set new sort mode
                current_pane['sort_mode'] = sort_type
                print(f"Sorting by {sort_type}")
            
            # Refresh the file list after sorting
            self.refresh_files(current_pane)
            self.needs_full_redraw = True
        
        # Show the dialog
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        message = f"Sort {pane_name} pane by:"
        self.show_dialog(message, choices, handle_sort_choice)
    
    def quick_sort(self, sort_mode):
        """Quickly change sort mode without showing dialog, or toggle reverse if already sorted by this mode"""
        current_pane = self.get_current_pane()
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        
        # Check if we're already sorting by this mode
        if current_pane['sort_mode'] == sort_mode:
            # Toggle reverse mode
            current_pane['sort_reverse'] = not current_pane['sort_reverse']
            reverse_status = "reverse" if current_pane['sort_reverse'] else "normal"
            print(f"Toggled {pane_name} pane to {sort_mode} sorting ({reverse_status})")
        else:
            # Change to new sort mode (keep current reverse setting)
            current_pane['sort_mode'] = sort_mode
            print(f"Sorted {pane_name} pane by {sort_mode}")
        
        # Refresh the file list
        self.refresh_files(current_pane)
        self.needs_full_redraw = True

    def show_file_details(self):
        """Show detailed information about selected files or current file"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            print("No files to show details for")
            return
        
        # Determine which files to show details for
        files_to_show = []
        
        if current_pane['selected_files']:
            # Show details for all selected files
            for file_path_str in current_pane['selected_files']:
                try:
                    file_path = Path(file_path_str)
                    if file_path.exists():
                        files_to_show.append(file_path)
                except:
                    continue
        else:
            # Show details for current cursor position
            current_file = current_pane['files'][current_pane['selected_index']]
            files_to_show.append(current_file)
        
        if not files_to_show:
            print("No valid files to show details for")
            return
        
        # Use the helper method to show file details
        InfoDialogHelpers.show_file_details(self.info_dialog, files_to_show, current_pane)
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def print_color_scheme_info(self):
        """Print current color scheme information to the log"""
        from tfm_colors import is_fallback_mode
        
        current_scheme = get_current_color_scheme()
        available_schemes = get_available_color_schemes()
        fallback_mode = is_fallback_mode()
        
        print(f"Color scheme: {current_scheme}")
        print(f"Available schemes: {', '.join(available_schemes)}")
        print(f"Fallback mode: {'enabled' if fallback_mode else 'disabled'}")
        
        # Get current scheme colors for key elements
        rgb_colors = get_current_rgb_colors()
        key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'SELECTED_FG', 'REGULAR_FILE_FG']
        
        for color_name in key_colors:
            if color_name in rgb_colors:
                rgb = rgb_colors[color_name]['rgb']
                print(f"  {color_name}: RGB{rgb}")
    
    def toggle_fallback_color_mode(self):
        """Toggle fallback color mode on/off"""
        from tfm_colors import toggle_fallback_mode, init_colors, is_fallback_mode
        
        # Toggle the fallback mode
        fallback_enabled = toggle_fallback_mode()
        
        # Reinitialize colors with the new mode
        init_colors()
        
        # Log the change
        mode_text = "enabled" if fallback_enabled else "disabled"
        print(f"Fallback color mode {mode_text}")
        
        # Print detailed color scheme info to log
        self.print_color_scheme_info()
        self.needs_full_redraw = True
    
    def show_help_dialog(self):
        """Show help dialog with key bindings and usage information"""
        InfoDialogHelpers.show_help_dialog(self.info_dialog)
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def view_selected_text_file(self):
        """View the selected file in text viewer if it's a text file"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            print("No files to view")
            return
        
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Parent directory (..) is no longer shown
        if selected_file.is_dir():
            print("Cannot view directory as text file")
            return
        
        if not is_text_file(selected_file):
            print(f"File '{selected_file.name}' is not recognized as a text file")
            return
        
        try:
            # Save current screen state
            curses.curs_set(0)
            
            # Open text viewer
            if view_text_file(self.stdscr, selected_file):
                print(f"Viewed text file: {selected_file.name}")
            else:
                print(f"Failed to view file: {selected_file.name}")
            
            # Restore TFM display
            self.needs_full_redraw = True
            
        except Exception as e:
            print(f"Error viewing file: {str(e)}")
            self.needs_full_redraw = True
    

        self.needs_full_redraw = True
    
    def edit_selected_file(self):
        """Edit the selected file using the configured text editor"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            print("No files in current directory")
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Parent directory (..) is no longer shown
        
        # Allow editing directories (some editors can handle them)
        # but warn if it's a directory
        if selected_file.is_dir():
            print(f"Warning: '{selected_file.name}' is a directory")
        
        # Get the configured text editor
        editor = getattr(self.config, 'TEXT_EDITOR', DEFAULT_TEXT_EDITOR)
        
        try:
            # Suspend curses
            self.external_program_manager.suspend_curses(self.stdscr)
            
            # Launch the text editor as a subprocess
            import subprocess
            result = subprocess.run([editor, str(selected_file)], 
                                  cwd=str(current_pane['path']))
            
            # Resume curses
            self.external_program_manager.resume_curses(self.stdscr)
            
            if result.returncode == 0:
                print(f"Edited file: {selected_file.name}")
            else:
                print(f"Editor exited with code {result.returncode}")
                
        except FileNotFoundError:
            # Resume curses even if editor not found
            self.external_program_manager.resume_curses(self.stdscr)
            print(f"Text editor '{editor}' not found. Please install it or configure a different editor.")
        except Exception as e:
            # Resume curses even if there's an error
            self.external_program_manager.resume_curses(self.stdscr)
            print(f"Error launching editor: {e}")
    
    def copy_selected_files(self):
        """Copy selected files to the opposite pane's directory"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Get files to copy - either selected files or current file if none selected
        files_to_copy = []
        
        if current_pane['selected_files']:
            # Copy all selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_copy.append(file_path)
        else:
            # Copy current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                
                # Parent directory (..) is no longer shown
                files_to_copy.append(selected_file)
        
        if not files_to_copy:
            print("No files to copy")
            return
        
        destination_dir = other_pane['path']
        
        # Check if destination directory is writable
        if not os.access(destination_dir, os.W_OK):
            print(f"Permission denied: Cannot write to {destination_dir}")
            return
        
        # Check if copy confirmation is enabled
        if getattr(self.config, 'CONFIRM_COPY', True):
            # Show confirmation dialog
            if len(files_to_copy) == 1:
                message = f"Copy '{files_to_copy[0].name}' to {destination_dir}?"
            else:
                message = f"Copy {len(files_to_copy)} items to {destination_dir}?"
            
            def copy_callback(confirmed):
                if confirmed:
                    self.copy_files_to_directory(files_to_copy, destination_dir)
                else:
                    print("Copy operation cancelled")
            
            self.show_confirmation(message, copy_callback)
        else:
            # Start copying files without confirmation
            self.copy_files_to_directory(files_to_copy, destination_dir)
    
    def copy_files_to_directory(self, files_to_copy, destination_dir):
        """Copy a list of files to the destination directory with conflict resolution"""
        conflicts = []
        
        # Check for conflicts first
        for source_file in files_to_copy:
            dest_path = destination_dir / source_file.name
            if dest_path.exists():
                conflicts.append((source_file, dest_path))
        
        if conflicts:
            # Show conflict resolution dialog
            conflict_names = [f.name for f, _ in conflicts]
            if len(conflicts) == 1:
                message = f"'{conflict_names[0]}' already exists in destination."
            else:
                message = f"{len(conflicts)} files already exist in destination."
            
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Skip", "key": "s", "value": "skip"},
                {"text": "Cancel", "key": "c", "value": "cancel"}
            ]
            
            def handle_conflict_choice(choice):
                if choice == "cancel":
                    print("Copy operation cancelled")
                    return
                elif choice == "skip":
                    # Copy only non-conflicting files
                    non_conflicting = [f for f in files_to_copy 
                                     if not (destination_dir / f.name).exists()]
                    if non_conflicting:
                        self.perform_copy_operation(non_conflicting, destination_dir)
                        print(f"Copied {len(non_conflicting)} files, skipped {len(conflicts)} conflicts")
                    else:
                        print("No files copied (all had conflicts)")
                elif choice == "overwrite":
                    # Copy all files, overwriting conflicts
                    self.perform_copy_operation(files_to_copy, destination_dir, overwrite=True)
                    print(f"Copied {len(files_to_copy)} files (overwrote {len(conflicts)} existing)")
            
            self.show_dialog(message, choices, handle_conflict_choice)
        else:
            # No conflicts, copy directly
            self.perform_copy_operation(files_to_copy, destination_dir)
            print(f"Copied {len(files_to_copy)} files")
    
    def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):
        """Perform the actual copy operation with fine-grained progress tracking"""
        copied_count = 0
        error_count = 0
        
        # Count total individual files for fine-grained progress
        total_individual_files = self._count_files_recursively(files_to_copy)
        
        # Start progress tracking for copy operation
        if total_individual_files > 1:  # Only show progress for multiple files
            self.progress_manager.start_operation(
                OperationType.COPY, 
                total_individual_files, 
                f"to {destination_dir.name}",
                self._progress_callback
            )
        
        processed_files = 0
        
        try:
            for source_file in files_to_copy:
                try:
                    dest_path = destination_dir / source_file.name
                    
                    # Skip if file exists and we're not overwriting
                    if dest_path.exists() and not overwrite:
                        # Still need to count skipped files for progress
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        elif source_file.is_dir():
                            # Count files in skipped directory
                            skipped_count = self._count_files_recursively([source_file])
                            processed_files += skipped_count
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        continue
                    
                    if source_file.is_dir():
                        # Copy directory recursively with progress tracking
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        
                        processed_files = self._copy_directory_with_progress(
                            source_file, dest_path, processed_files, total_individual_files
                        )
                        print(f"Copied directory: {source_file.name}")
                    else:
                        # Copy single file
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(source_file.name, processed_files)
                        
                        shutil.copy2(source_file, dest_path)
                        print(f"Copied file: {source_file.name}")
                    
                    copied_count += 1
                    
                except PermissionError as e:
                    print(f"Permission denied copying {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
                except Exception as e:
                    print(f"Error copying {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
        
        finally:
            # Finish progress tracking
            if total_individual_files > 1:
                self.progress_manager.finish_operation()
        
        # Refresh both panes to show the copied files
        self.refresh_files()
        self.needs_full_redraw = True
        
        # Clear selections after successful copy
        if copied_count > 0:
            current_pane = self.get_current_pane()
            current_pane['selected_files'].clear()
        
        if error_count > 0:
            print(f"Copy completed with {error_count} errors")
    
    def _copy_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
        """Copy directory recursively with fine-grained progress updates"""
        try:
            # Create destination directory
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Walk through source directory and copy files one by one
            for root, dirs, files in os.walk(source_dir):
                root_path = Path(root)
                
                # Calculate relative path from source directory
                rel_path = root_path.relative_to(source_dir)
                dest_root = dest_dir / rel_path
                
                # Create subdirectories
                dest_root.mkdir(parents=True, exist_ok=True)
                
                # Copy files in current directory
                for file_name in files:
                    source_file = root_path / file_name
                    dest_file = dest_root / file_name
                    
                    processed_files += 1
                    if total_files > 1:
                        # Show relative path for files in subdirectories
                        display_name = str(rel_path / file_name) if rel_path != Path('.') else file_name
                        self.progress_manager.update_progress(display_name, processed_files)
                    
                    try:
                        if source_file.is_symlink():
                            # Copy symbolic link
                            link_target = os.readlink(str(source_file))
                            dest_file.symlink_to(link_target)
                        else:
                            # Copy regular file
                            shutil.copy2(source_file, dest_file)
                    except Exception as e:
                        print(f"Error copying {source_file}: {e}")
                        if total_files > 1:
                            self.progress_manager.increment_errors()
                
                # Handle symbolic links to directories
                for dir_name in dirs:
                    source_subdir = root_path / dir_name
                    if source_subdir.is_symlink():
                        processed_files += 1
                        if total_files > 1:
                            display_name = str(rel_path / dir_name) if rel_path != Path('.') else dir_name
                            self.progress_manager.update_progress(f"Link: {display_name}", processed_files)
                        
                        dest_subdir = dest_root / dir_name
                        try:
                            link_target = os.readlink(str(source_subdir))
                            dest_subdir.symlink_to(link_target)
                        except Exception as e:
                            print(f"Error copying symlink {source_subdir}: {e}")
                            if total_files > 1:
                                self.progress_manager.increment_errors()
            
            return processed_files
            
        except Exception as e:
            print(f"Error copying directory {source_dir}: {e}")
            if total_files > 1:
                self.progress_manager.increment_errors()
            return processed_files
    
    def move_selected_files(self):
        """Move selected files to the opposite pane's directory, or create new directory if no files selected"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Check if any files are selected
        if not current_pane['selected_files']:
            # No files selected - create new directory instead
            self.enter_create_directory_mode()
            return
        
        # Get files to move - selected files
        files_to_move = []
        for file_path_str in current_pane['selected_files']:
            file_path = Path(file_path_str)
            if file_path.exists():
                files_to_move.append(file_path)
        
        if not files_to_move:
            print("No files to move")
            return
        
        destination_dir = other_pane['path']
        
        # Check if destination directory is writable
        if not os.access(destination_dir, os.W_OK):
            print(f"Permission denied: Cannot write to {destination_dir}")
            return
        
        # Check if any files are being moved to the same directory
        same_dir_files = [f for f in files_to_move if f.parent == destination_dir]
        if same_dir_files:
            if len(same_dir_files) == len(files_to_move):
                print("Cannot move files to the same directory")
                return
            else:
                # Remove files that are already in the destination directory
                files_to_move = [f for f in files_to_move if f.parent != destination_dir]
                print(f"Skipping {len(same_dir_files)} files already in destination directory")
        
        # Check if move confirmation is enabled
        if getattr(self.config, 'CONFIRM_MOVE', True):
            # Show confirmation dialog
            if len(files_to_move) == 1:
                message = f"Move '{files_to_move[0].name}' to {destination_dir}?"
            else:
                message = f"Move {len(files_to_move)} items to {destination_dir}?"
            
            def move_callback(confirmed):
                if confirmed:
                    self.move_files_to_directory(files_to_move, destination_dir)
                else:
                    print("Move operation cancelled")
            
            self.show_confirmation(message, move_callback)
        else:
            # Start moving files without confirmation
            self.move_files_to_directory(files_to_move, destination_dir)
    
    def move_files_to_directory(self, files_to_move, destination_dir):
        """Move a list of files to the destination directory with conflict resolution"""
        conflicts = []
        
        # Check for conflicts first
        for source_file in files_to_move:
            dest_path = destination_dir / source_file.name
            if dest_path.exists():
                conflicts.append((source_file, dest_path))
        
        if conflicts:
            # Show conflict resolution dialog
            conflict_names = [f.name for f, _ in conflicts]
            if len(conflicts) == 1:
                message = f"'{conflict_names[0]}' already exists in destination."
            else:
                message = f"{len(conflicts)} files already exist in destination."
            
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Skip", "key": "s", "value": "skip"},
                {"text": "Cancel", "key": "c", "value": "cancel"}
            ]
            
            def handle_conflict_choice(choice):
                if choice == "cancel":
                    print("Move operation cancelled")
                    return
                elif choice == "skip":
                    # Move only non-conflicting files
                    non_conflicting = [f for f in files_to_move 
                                     if not (destination_dir / f.name).exists()]
                    if non_conflicting:
                        self.perform_move_operation(non_conflicting, destination_dir)
                        print(f"Moved {len(non_conflicting)} files, skipped {len(conflicts)} conflicts")
                    else:
                        print("No files moved (all had conflicts)")
                elif choice == "overwrite":
                    # Move all files, overwriting conflicts
                    self.perform_move_operation(files_to_move, destination_dir, overwrite=True)
                    print(f"Moved {len(files_to_move)} files (overwrote {len(conflicts)} existing)")
            
            self.show_dialog(message, choices, handle_conflict_choice)
        else:
            # No conflicts, move directly
            self.perform_move_operation(files_to_move, destination_dir)
            print(f"Moved {len(files_to_move)} files")
    
    def perform_move_operation(self, files_to_move, destination_dir, overwrite=False):
        """Perform the actual move operation with fine-grained progress tracking"""
        moved_count = 0
        error_count = 0
        
        # Count total individual files for fine-grained progress
        total_individual_files = self._count_files_recursively(files_to_move)
        
        # Start progress tracking for move operation
        if total_individual_files > 1:  # Only show progress for multiple files
            self.progress_manager.start_operation(
                OperationType.MOVE, 
                total_individual_files, 
                f"to {destination_dir.name}",
                self._progress_callback
            )
        
        processed_files = 0
        
        try:
            for source_file in files_to_move:
                try:
                    dest_path = destination_dir / source_file.name
                    
                    # Skip if file exists and we're not overwriting
                    if dest_path.exists() and not overwrite:
                        # Still need to count skipped files for progress
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        elif source_file.is_dir():
                            # Count files in skipped directory
                            skipped_count = self._count_files_recursively([source_file])
                            processed_files += skipped_count
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        continue
                    
                    # Remove destination if it exists and we're overwriting
                    if dest_path.exists() and overwrite:
                        if dest_path.is_dir():
                            shutil.rmtree(dest_path)
                        else:
                            dest_path.unlink()
                    
                    # Move the file/directory
                    if source_file.is_symlink():
                        # For symbolic links, copy the link itself (not the target)
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(f"Link: {source_file.name}", processed_files)
                        
                        link_target = os.readlink(str(source_file))
                        dest_path.symlink_to(link_target)
                        source_file.unlink()
                        print(f"Moved symbolic link: {source_file.name}")
                    elif source_file.is_dir():
                        # For directories, we need to track individual files being moved
                        processed_files = self._move_directory_with_progress(
                            source_file, dest_path, processed_files, total_individual_files
                        )
                        print(f"Moved directory: {source_file.name}")
                    else:
                        # Move single file
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(source_file.name, processed_files)
                        
                        shutil.move(str(source_file), str(dest_path))
                        print(f"Moved file: {source_file.name}")
                    
                    moved_count += 1
                    
                except PermissionError as e:
                    print(f"Permission denied moving {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
                except Exception as e:
                    print(f"Error moving {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
        
        finally:
            # Finish progress tracking
            if total_individual_files > 1:
                self.progress_manager.finish_operation()
        
        # Refresh both panes to show the moved files
        self.refresh_files()
        self.needs_full_redraw = True
        
        # Clear selections after successful move
        if moved_count > 0:
            current_pane = self.get_current_pane()
            current_pane['selected_files'].clear()
        
        if error_count > 0:
            print(f"Move completed with {error_count} errors")
    
    def _move_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
        """Move directory using copy + delete with fine-grained progress updates"""
        try:
            # First copy the directory with progress tracking
            processed_files = self._copy_directory_with_progress(
                source_dir, dest_dir, processed_files, total_files
            )
            
            # Then remove the source directory
            shutil.rmtree(source_dir)
            
            return processed_files
            
        except Exception as e:
            print(f"Error moving directory {source_dir}: {e}")
            if total_files > 1:
                self.progress_manager.increment_errors()
            return processed_files
    
    def delete_selected_files(self):
        """Delete selected files or current file with confirmation"""
        current_pane = self.get_current_pane()
        
        # Get files to delete - either selected files or current file if none selected
        files_to_delete = []
        
        if current_pane['selected_files']:
            # Delete all selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_delete.append(file_path)
        else:
            # Delete current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                
                # Parent directory (..) is no longer shown
                files_to_delete.append(selected_file)
        
        if not files_to_delete:
            print("No files to delete")
            return
        
        def handle_delete_confirmation(confirmed):
            if confirmed:
                self.perform_delete_operation(files_to_delete)
            else:
                print("Delete operation cancelled")
        
        # Check if delete confirmation is enabled
        if getattr(self.config, 'CONFIRM_DELETE', True):
            # Show confirmation dialog
            if len(files_to_delete) == 1:
                file_name = files_to_delete[0].name
                if files_to_delete[0].is_dir():
                    message = f"Delete directory '{file_name}' and all its contents?"
                elif files_to_delete[0].is_symlink():
                    message = f"Delete symbolic link '{file_name}'?"
                else:
                    message = f"Delete file '{file_name}'?"
            else:
                dir_count = sum(1 for f in files_to_delete if f.is_dir())
                file_count = len(files_to_delete) - dir_count
                if dir_count > 0 and file_count > 0:
                    message = f"Delete {len(files_to_delete)} items ({dir_count} directories, {file_count} files)?"
                elif dir_count > 0:
                    message = f"Delete {dir_count} directories and all their contents?"
                else:
                    message = f"Delete {file_count} files?"
            
            choices = [
                {"text": "Yes", "key": "y", "value": True},
                {"text": "No", "key": "n", "value": False}
            ]
            
            self.show_dialog(message, choices, handle_delete_confirmation)
        else:
            # Delete without confirmation
            handle_delete_confirmation(True)
    
    def perform_delete_operation(self, files_to_delete):
        """Perform the actual delete operation with fine-grained progress tracking"""
        deleted_count = 0
        error_count = 0
        
        # Count total individual files for fine-grained progress
        total_individual_files = self._count_files_recursively(files_to_delete)
        
        # Start progress tracking for delete operation
        if total_individual_files > 1:  # Only show progress for multiple files
            self.progress_manager.start_operation(
                OperationType.DELETE, 
                total_individual_files, 
                "",
                self._progress_callback
            )
        
        processed_files = 0
        
        try:
            for file_path in files_to_delete:
                try:
                    if file_path.is_symlink():
                        # Delete symbolic link (not its target)
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(f"Link: {file_path.name}", processed_files)
                        
                        file_path.unlink()
                        print(f"Deleted symbolic link: {file_path.name}")
                    elif file_path.is_dir():
                        # Delete directory recursively with progress tracking
                        processed_files = self._delete_directory_with_progress(
                            file_path, processed_files, total_individual_files
                        )
                        print(f"Deleted directory: {file_path.name}")
                    else:
                        # Delete single file
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(file_path.name, processed_files)
                        
                        file_path.unlink()
                        print(f"Deleted file: {file_path.name}")
                    
                    deleted_count += 1
                    
                except PermissionError as e:
                    print(f"Permission denied deleting {file_path.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
                except FileNotFoundError:
                    print(f"File not found (already deleted?): {file_path.name}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
                except Exception as e:
                    print(f"Error deleting {file_path.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
        
        finally:
            # Finish progress tracking
            if total_individual_files > 1:
                self.progress_manager.finish_operation()
        
        # Refresh current pane to show the changes
        self.refresh_files(self.get_current_pane())
        self.needs_full_redraw = True
        
        # Clear selections after delete operation
        current_pane = self.get_current_pane()
        current_pane['selected_files'].clear()
        
        # Adjust cursor position if it's now out of bounds
        if current_pane['selected_index'] >= len(current_pane['files']):
            current_pane['selected_index'] = max(0, len(current_pane['files']) - 1)
        
        # Report results
        if deleted_count > 0:
            print(f"Successfully deleted {deleted_count} items")
    
    def _delete_directory_with_progress(self, dir_path, processed_files, total_files):
        """Delete directory recursively with fine-grained progress updates"""
        try:
            # Walk through directory and delete files one by one (bottom-up for safety)
            for root, dirs, files in os.walk(dir_path, topdown=False):
                root_path = Path(root)
                
                # Delete files in current directory
                for file_name in files:
                    file_path = root_path / file_name
                    processed_files += 1
                    
                    if total_files > 1:
                        # Show relative path from the main directory being deleted
                        try:
                            rel_path = file_path.relative_to(dir_path)
                            display_name = str(rel_path)
                        except ValueError:
                            display_name = file_path.name
                        
                        self.progress_manager.update_progress(display_name, processed_files)
                    
                    try:
                        file_path.unlink()  # Remove file or symlink
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                        if total_files > 1:
                            self.progress_manager.increment_errors()
                
                # Delete empty subdirectories (they should be empty now since we're going bottom-up)
                for dir_name in dirs:
                    subdir_path = root_path / dir_name
                    try:
                        # Only try to remove if it's empty or a symlink
                        if subdir_path.is_symlink():
                            # Count symlinks to directories as files for progress
                            processed_files += 1
                            if total_files > 1:
                                try:
                                    rel_path = subdir_path.relative_to(dir_path)
                                    display_name = f"Link: {rel_path}"
                                except ValueError:
                                    display_name = f"Link: {subdir_path.name}"
                                self.progress_manager.update_progress(display_name, processed_files)
                            subdir_path.unlink()
                        else:
                            # Try to remove empty directory (no progress update for empty dirs)
                            subdir_path.rmdir()
                    except OSError:
                        # Directory not empty or permission error - skip it
                        # The directory will be handled by shutil.rmtree fallback if needed
                        pass
                    except Exception as e:
                        print(f"Error deleting directory {subdir_path}: {e}")
                        if total_files > 1:
                            self.progress_manager.increment_errors()
            
            # Finally remove the main directory
            try:
                dir_path.rmdir()
            except OSError:
                # If directory is not empty, use shutil.rmtree as fallback
                # This shouldn't happen if our bottom-up deletion worked correctly
                shutil.rmtree(dir_path)
            
            return processed_files
            
        except Exception as e:
            print(f"Error deleting directory {dir_path}: {e}")
            if total_files > 1:
                self.progress_manager.increment_errors()
            return processed_files
        if error_count > 0:
            print(f"Delete completed with {error_count} errors")
    
    def enter_create_archive_mode(self):
        """Enter archive creation mode"""
        current_pane = self.get_current_pane()
        
        # Check if there are files to archive
        files_to_archive = []
        
        if current_pane['selected_files']:
            # Archive selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_archive.append(file_path)
        else:
            # Archive current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_archive.append(selected_file)
        
        if not files_to_archive:
            print("No files to archive")
            return
        
        # Determine default filename for single file/directory
        default_filename = ""
        if len(files_to_archive) == 1:
            # Use basename of the single file/directory with a dot for extension
            basename = files_to_archive[0].stem if files_to_archive[0].is_file() else files_to_archive[0].name
            default_filename = f"{basename}."
        
        # Enter archive creation mode using general dialog with default filename
        self.general_dialog.show_status_line_input(
            prompt="Archive filename: ",
            help_text="ESC:cancel Enter:create (.zip/.tar.gz/.tgz)",
            initial_text=default_filename,
            callback=self.on_create_archive_confirm,
            cancel_callback=self.on_create_archive_cancel
        )
        self.needs_full_redraw = True
        
        # Log what we're about to archive
        if len(files_to_archive) == 1:
            print(f"Creating archive from: {files_to_archive[0].name}")
        else:
            print(f"Creating archive from {len(files_to_archive)} selected items")
        print("Enter archive filename (with .zip, .tar.gz, or .tgz extension):")
    
    def on_create_archive_confirm(self, archive_name):
        """Handle create archive confirmation"""
        if not archive_name.strip():
            print("Invalid archive name")
            self.general_dialog.hide()
            self.needs_full_redraw = True
            return
        
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Get files to archive
        files_to_archive = []
        
        if current_pane['selected_files']:
            # Archive selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_archive.append(file_path)
        else:
            # Archive current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_archive.append(selected_file)
        
        if not files_to_archive:
            print("No files to archive")
            self.general_dialog.hide()
            self.needs_full_redraw = True
            return
        
        archive_filename = archive_name.strip()
        archive_path = other_pane['path'] / archive_filename
        
        # Check if archive already exists
        if archive_path.exists():
            print(f"Archive '{archive_filename}' already exists")
            self.general_dialog.hide()
            self.needs_full_redraw = True
            return
        
        try:
            # Detect archive format and create archive
            archive_format = self.detect_archive_format(archive_filename)
            
            if archive_format == 'zip':
                self.create_zip_archive(archive_path, files_to_archive)
            elif archive_format in ['tar.gz', 'tgz']:
                self.create_tar_archive(archive_path, files_to_archive)
            else:
                print(f"Unsupported archive format. Use .zip, .tar.gz, or .tgz")
                self.general_dialog.hide()
                self.needs_full_redraw = True
                return
            
            print(f"Created archive: {archive_filename}")
            
            # Refresh the other pane to show the new archive
            self.refresh_files(other_pane)
            
            # Try to select the new archive in the other pane
            for i, file_path in enumerate(other_pane['files']):
                if file_path.name == archive_filename:
                    other_pane['selected_index'] = i
                    self.adjust_scroll_for_selection(other_pane)
                    break
            
            self.general_dialog.hide()
            self.needs_full_redraw = True
            
        except Exception as e:
            print(f"Error creating archive: {e}")
            self.general_dialog.hide()
            self.needs_full_redraw = True
    
    def on_create_archive_cancel(self):
        """Handle create archive cancellation"""
        print("Archive creation cancelled")
        self.general_dialog.hide()
        self.needs_full_redraw = True
    
    def perform_create_archive(self):
        """Create the archive file"""
        if not self.create_archive_editor.text.strip():
            print("Archive filename cannot be empty")
            return
        
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Get files to archive
        files_to_archive = []
        
        if current_pane['selected_files']:
            # Archive selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_archive.append(file_path)
        else:
            # Archive current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_archive.append(selected_file)
        
        if not files_to_archive:
            print("No files to archive")
            self.exit_create_archive_mode()
            return
        
        # Determine archive path (save to other pane's directory)
        archive_filename = self.create_archive_editor.text.strip()
        archive_path = other_pane['path'] / archive_filename
        
        # Detect archive format from extension
        archive_format = self.detect_archive_format(archive_filename)
        if not archive_format:
            print("Unsupported archive format. Use .zip, .tar.gz, or .tgz extension")
            return
        
        try:
            if archive_format == 'zip':
                self.create_zip_archive(archive_path, files_to_archive)
            elif archive_format in ['tar.gz', 'tgz']:
                self.create_tar_archive(archive_path, files_to_archive)
            
            print(f"Archive created successfully: {archive_path}")
            
            # Refresh the other pane to show the new archive
            self.refresh_files(other_pane)
            self.needs_full_redraw = True
            
        except Exception as e:
            print(f"Error creating archive: {e}")
        
        self.exit_create_archive_mode()
    
    def update_archive_progress(self, current_file, processed, total):
        """Update status bar with archive creation progress (legacy method - now uses ProgressManager)"""
        # Update the progress manager if an operation is active
        if self.progress_manager.is_operation_active():
            self.progress_manager.update_progress(current_file, processed)
        
        # Force a screen refresh to show progress
        try:
            self.draw_status()
            self.stdscr.refresh()
        except:
            pass  # Ignore drawing errors during progress updates
    
    def _progress_callback(self, progress_data):
        """Callback for progress manager updates"""
        # Force a screen refresh to show progress
        try:
            self.draw_status()
            self.stdscr.refresh()
        except:
            pass  # Ignore drawing errors during progress updates
    
    def _count_files_recursively(self, paths):
        """Count total number of individual files in the given paths (including files in directories)"""
        total_files = 0
        for path in paths:
            if path.is_file() or path.is_symlink():
                total_files += 1
            elif path.is_dir():
                try:
                    for root, dirs, files in os.walk(path):
                        total_files += len(files)
                        # Count symlinks to directories as files
                        for d in dirs:
                            dir_path = Path(root) / d
                            if dir_path.is_symlink():
                                total_files += 1
                except (PermissionError, OSError):
                    # If we can't walk the directory, count it as 1 item
                    total_files += 1
        return total_files
    
    def detect_archive_format(self, filename):
        """Detect archive format from filename extension"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.zip'):
            return 'zip'
        elif filename_lower.endswith('.tar.gz'):
            return 'tar.gz'
        elif filename_lower.endswith('.tgz'):
            return 'tgz'
        else:
            return None
    
    def create_zip_archive(self, archive_path, files_to_archive):
        """Create a ZIP archive with progress updates"""
        # Count total files for progress tracking
        total_files = 0
        for file_path in files_to_archive:
            if file_path.is_file():
                total_files += 1
            elif file_path.is_dir():
                for root, dirs, files in os.walk(file_path):
                    total_files += len(files)
        
        # Start progress tracking
        self.progress_manager.start_operation(
            OperationType.ARCHIVE_CREATE, 
            total_files, 
            f"ZIP: {archive_path.name}",
            self._progress_callback
        )
        
        processed_files = 0
        
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_archive:
                    if file_path.is_file():
                        # Update progress
                        processed_files += 1
                        self.progress_manager.update_progress(file_path.name, processed_files)
                        
                        # Add file to archive
                        zipf.write(file_path, file_path.name)
                    elif file_path.is_dir():
                        # Add directory recursively
                        for root, dirs, files in os.walk(file_path):
                            root_path = Path(root)
                            # Calculate relative path from the base directory
                            rel_path = root_path.relative_to(file_path.parent)
                            
                            # Add directory entry
                            if rel_path != Path('.'):
                                zipf.write(root_path, str(rel_path) + '/')
                            
                            # Add files in directory
                            for file in files:
                                processed_files += 1
                                self.progress_manager.update_progress(file, processed_files)
                                
                                file_full_path = root_path / file
                                file_rel_path = file_full_path.relative_to(file_path.parent)
                                zipf.write(file_full_path, str(file_rel_path))
        finally:
            # Finish progress tracking
            self.progress_manager.finish_operation()
    
    def create_tar_archive(self, archive_path, files_to_archive):
        """Create a TAR.GZ archive with progress updates"""
        # Count total files for progress tracking
        total_files = 0
        for file_path in files_to_archive:
            if file_path.is_file():
                total_files += 1
            elif file_path.is_dir():
                for root, dirs, files in os.walk(file_path):
                    total_files += len(files)
        
        # Start progress tracking
        self.progress_manager.start_operation(
            OperationType.ARCHIVE_CREATE, 
            total_files, 
            f"TAR.GZ: {archive_path.name}",
            self._progress_callback
        )
        
        processed_files = 0
        
        try:
            with tarfile.open(archive_path, 'w:gz') as tarf:
                for file_path in files_to_archive:
                    if file_path.is_file():
                        processed_files += 1
                        self.progress_manager.update_progress(file_path.name, processed_files)
                        tarf.add(file_path, arcname=file_path.name)
                    elif file_path.is_dir():
                        # For directories, we need to track individual files being added
                        def progress_filter(tarinfo):
                            nonlocal processed_files
                            if tarinfo.isfile():
                                processed_files += 1
                                self.progress_manager.update_progress(tarinfo.name, processed_files)
                            return tarinfo
                        
                        tarf.add(file_path, arcname=file_path.name, filter=progress_filter)
        finally:
            # Finish progress tracking
            self.progress_manager.finish_operation()
    
    def extract_selected_archive(self):
        """Extract the selected archive file to the other pane"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        if not current_pane['files']:
            print("No files in current directory")
            return
        
        # Get the selected file
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        if not selected_file.is_file():
            print("Selected item is not a file")
            return
        
        # Check if it's an archive file
        archive_format = self.detect_archive_format(selected_file.name)
        if not archive_format:
            print(f"'{selected_file.name}' is not a supported archive format")
            print("Supported formats: .zip, .tar.gz, .tgz")
            return
        
        # Create extraction directory in the other pane
        # Use the base name of the archive (without extension) as directory name
        archive_basename = self.get_archive_basename(selected_file.name)
        extract_dir = other_pane['path'] / archive_basename
        
        # Check if extract confirmation is enabled
        if getattr(self.config, 'CONFIRM_EXTRACT_ARCHIVE', True):
            # Show confirmation dialog
            message = f"Extract '{selected_file.name}' to {other_pane['path']}?"
            
            def extract_callback(confirmed):
                if confirmed:
                    self._proceed_with_extraction(selected_file, extract_dir, archive_format, other_pane, archive_basename)
                else:
                    print("Extraction cancelled")
            
            self.show_confirmation(message, extract_callback)
        else:
            # Proceed with extraction without confirmation
            self._proceed_with_extraction(selected_file, extract_dir, archive_format, other_pane, archive_basename)
    
    def _proceed_with_extraction(self, selected_file, extract_dir, archive_format, other_pane, archive_basename):
        """Proceed with extraction after confirmation (if enabled)"""
        # Check if extraction directory already exists
        if extract_dir.exists():
            def overwrite_callback(confirmed):
                if confirmed:
                    try:
                        # Remove existing directory
                        shutil.rmtree(extract_dir)
                        self.perform_extraction(selected_file, extract_dir, archive_format, other_pane)
                    except Exception as e:
                        print(f"Error removing existing directory: {e}")
                else:
                    print("Extraction cancelled")
            
            self.show_confirmation(f"Directory '{archive_basename}' already exists. Overwrite?", overwrite_callback)
        else:
            self.perform_extraction(selected_file, extract_dir, archive_format, other_pane)
    
    def get_archive_basename(self, filename):
        """Get the base name of an archive file (without extension)"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.tar.gz'):
            return filename[:-7]  # Remove .tar.gz
        elif filename_lower.endswith('.tgz'):
            return filename[:-4]  # Remove .tgz
        elif filename_lower.endswith('.zip'):
            return filename[:-4]  # Remove .zip
        else:
            # Fallback - remove last extension
            return Path(filename).stem
    
    def perform_extraction(self, archive_file, extract_dir, archive_format, other_pane):
        """Perform the actual extraction"""
        try:
            # Create extraction directory
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            if archive_format == 'zip':
                self.extract_zip_archive(archive_file, extract_dir)
            elif archive_format in ['tar.gz', 'tgz']:
                self.extract_tar_archive(archive_file, extract_dir)
            
            print(f"Archive extracted successfully to: {extract_dir}")
            
            # Refresh the other pane to show the extracted contents
            self.refresh_files(other_pane)
            self.needs_full_redraw = True
            
        except Exception as e:
            print(f"Error extracting archive: {e}")
            # Clean up partially created directory on error
            try:
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
            except:
                pass
    
    def extract_zip_archive(self, archive_file, extract_dir):
        """Extract a ZIP archive with progress tracking"""
        with zipfile.ZipFile(archive_file, 'r') as zipf:
            # Get list of files to extract
            file_list = zipf.namelist()
            total_files = len(file_list)
            
            # Start progress tracking if there are multiple files
            if total_files > 1:
                self.progress_manager.start_operation(
                    OperationType.ARCHIVE_EXTRACT,
                    total_files,
                    f"ZIP: {archive_file.name}",
                    self._progress_callback
                )
            
            try:
                # Extract files one by one to track progress
                for i, file_info in enumerate(file_list):
                    if total_files > 1:
                        # Update progress with current file
                        filename = Path(file_info).name if file_info else f"file_{i+1}"
                        self.progress_manager.update_progress(filename, i)
                    
                    try:
                        # Extract individual file
                        zipf.extract(file_info, extract_dir)
                    except Exception as e:
                        print(f"Error extracting {file_info}: {e}")
                        if total_files > 1:
                            self.progress_manager.increment_errors()
                    
            finally:
                # Finish progress tracking
                if total_files > 1:
                    self.progress_manager.finish_operation()
    
    def extract_tar_archive(self, archive_file, extract_dir):
        """Extract a TAR.GZ archive with progress tracking"""
        with tarfile.open(archive_file, 'r:gz') as tarf:
            # Get list of members to extract
            members = tarf.getmembers()
            # Count only files (not directories) for progress
            file_members = [m for m in members if m.isfile()]
            total_files = len(file_members)
            
            # Start progress tracking if there are multiple files
            if total_files > 1:
                self.progress_manager.start_operation(
                    OperationType.ARCHIVE_EXTRACT,
                    total_files,
                    f"TAR.GZ: {archive_file.name}",
                    self._progress_callback
                )
            
            try:
                # Extract members one by one to track progress
                processed_files = 0
                for member in members:
                    if member.isfile():
                        processed_files += 1
                        if total_files > 1:
                            # Update progress with current file
                            filename = Path(member.name).name if member.name else f"file_{processed_files}"
                            self.progress_manager.update_progress(filename, processed_files)
                    
                    try:
                        # Extract individual member
                        tarf.extract(member, extract_dir)
                    except Exception as e:
                        print(f"Error extracting {member.name}: {e}")
                        if total_files > 1 and member.isfile():
                            self.progress_manager.increment_errors()
                    
            finally:
                # Finish progress tracking
                if total_files > 1:
                    self.progress_manager.finish_operation()
        
    def handle_isearch_input(self, key):
        """Handle input while in isearch mode"""
        if key == 27:  # ESC - exit isearch mode
            self.exit_isearch_mode()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - exit isearch mode and keep current position
            self.exit_isearch_mode()
            return True
        elif key == curses.KEY_BACKSPACE or key == KEY_BACKSPACE_1 or key == KEY_BACKSPACE_2:
            # Backspace - remove last character
            if self.isearch_pattern:
                self.isearch_pattern = self.isearch_pattern[:-1]
                self.update_isearch_matches()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_UP:
            # Up arrow - go to previous match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index - 1) % len(self.isearch_matches)
                current_pane = self.get_current_pane()
                current_pane['selected_index'] = self.isearch_matches[self.isearch_match_index]
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_DOWN:
            # Down arrow - go to next match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index + 1) % len(self.isearch_matches)
                current_pane = self.get_current_pane()
                current_pane['selected_index'] = self.isearch_matches[self.isearch_match_index]
                self.needs_full_redraw = True
            return True
        elif 32 <= key <= 126:  # Printable characters
            # Add character to isearch pattern
            self.isearch_pattern += chr(key)
            self.update_isearch_matches()
            self.needs_full_redraw = True
            return True
        
        # In isearch mode, capture most other keys to prevent unintended actions
        # Only allow specific keys that make sense during isearch
        return True

    def handle_batch_rename_input(self, key):
        """Handle input while in batch rename mode - wrapper for batch rename dialog component"""
        result = self.batch_rename_dialog.handle_input(key)
        
        if result == True:
            self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'cancel':
                print("Batch rename cancelled")
                self.exit_batch_rename_mode()
                return True
            elif action == 'field_switch':
                self.needs_full_redraw = True
                return True
            elif action == 'scroll':
                self.needs_full_redraw = True
                return True
            elif action == 'execute':
                self.perform_batch_rename()
                return True
            elif action == 'error':
                print(data)
                return True
            elif action == 'text_changed':
                self.update_batch_rename_preview()
                self.needs_full_redraw = True
                return True
        
        return True  # Capture most keys in batch rename mode

    def adjust_pane_boundary(self, direction):
        """Adjust the boundary between left and right panes"""
        if direction == 'left':
            # Make left pane smaller, right pane larger
            self.pane_manager.left_pane_ratio = max(MIN_PANE_RATIO, self.pane_manager.left_pane_ratio - PANE_ADJUST_STEP)
        elif direction == 'right':
            # Make left pane larger, right pane smaller  
            self.pane_manager.left_pane_ratio = min(MAX_PANE_RATIO, self.pane_manager.left_pane_ratio + PANE_ADJUST_STEP)
            
        # Trigger a full redraw for the new pane layout
        self.needs_full_redraw = True
        
        # Show immediate feedback in log pane
        left_percent = int(self.pane_manager.left_pane_ratio * 100)
        right_percent = 100 - left_percent
        print(f"Pane split: {left_percent}% | {right_percent}%")
        
    def adjust_log_boundary(self, direction):
        """Adjust the boundary between file panes and log pane"""
        if direction == 'up':
            # Make log pane smaller, file panes larger
            self.log_height_ratio = max(MIN_LOG_HEIGHT_RATIO, self.log_height_ratio - LOG_HEIGHT_ADJUST_STEP)
        elif direction == 'down':
            # Make log pane larger, file panes smaller
            self.log_height_ratio = min(MAX_LOG_HEIGHT_RATIO, self.log_height_ratio + LOG_HEIGHT_ADJUST_STEP)
            
        # Trigger a full redraw for the new layout
        self.needs_full_redraw = True
        
        # Show immediate feedback in log pane
        log_percent = int(self.log_height_ratio * 100)
        file_percent = 100 - log_percent
        print(f"Layout: {file_percent}% files | {log_percent}% log")
    
    def show_search_dialog(self, search_type='filename'):
        """Show the search dialog for filename or content search - wrapper for search dialog component"""
        self.search_dialog.show(search_type)
        self.needs_full_redraw = True
        
        # Force immediate display of the dialog
        self._force_immediate_redraw()
    
    def exit_search_dialog_mode(self):
        """Exit search dialog mode - wrapper for search dialog component"""
        self.search_dialog.exit()
        self.needs_full_redraw = True
    
    def perform_search(self):
        """Perform the actual search based on current pattern and type - wrapper for search dialog component"""
        current_pane = self.get_current_pane()
        search_root = current_pane['path']
        self.search_dialog.perform_search(search_root)
    
    def handle_search_dialog_input(self, key):
        """Handle input while in search dialog mode - wrapper for search dialog component"""
        result = self.search_dialog.handle_input(key)
        
        if result == True:
            self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'search':
                self.perform_search()
                self.needs_full_redraw = True
                return True
            elif action == 'navigate':
                if data:
                    self._navigate_to_search_result(data)
                self.exit_search_dialog_mode()
                return True
        
        return False

    def _navigate_to_search_result(self, result):
        """Navigate to the selected search result - wrapper for search dialog helper"""
        SearchDialogHelpers.navigate_to_result(result, self.pane_manager, self.file_operations, print)
        
        # Adjust scroll with proper display height
        current_pane = self.get_current_pane()
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        
        SearchDialogHelpers.adjust_scroll_for_display_height(current_pane, display_height)
        self.needs_full_redraw = True

    def run(self):
        """Main application loop"""
        while True:
            # Check if we should quit
            if self.should_quit:
                break
            
            # Check for startup redraw trigger (0.1 seconds after startup)
            if hasattr(self, 'startup_time') and time.time() - self.startup_time >= 0.033:
                self.needs_full_redraw = True
                delattr(self, 'startup_time')  # Remove the attribute to avoid repeated triggers
                
            # Only do full redraw when needed
            if self.needs_full_redraw:
                self.refresh_files()
                
                # Clear screen with proper background
                self.clear_screen_with_background()
                
                # Draw interface
                self.draw_header()
                self.draw_files()
                self.draw_log_pane()
                self.draw_status()
                
                # Refresh screen
                self.stdscr.refresh()
                self.needs_full_redraw = False
            
            # Always draw dialog overlays on top (they need to update every frame for cursor/text changes)
            dialog_drawn = False
            if self.general_dialog.is_active:
                self.general_dialog.draw(self.stdscr, self.safe_addstr)
                dialog_drawn = True
            elif self.list_dialog.mode:
                self.list_dialog.draw(self.stdscr, self.safe_addstr)
                dialog_drawn = True
            elif self.info_dialog.mode:
                self.info_dialog.draw(self.stdscr, self.safe_addstr)
                dialog_drawn = True
            elif self.search_dialog.mode:
                self.search_dialog.draw(self.stdscr, self.safe_addstr)
                dialog_drawn = True
            elif self.batch_rename_dialog.mode:
                self.batch_rename_dialog.draw(self.stdscr, self.safe_addstr)
                dialog_drawn = True
            
            # Refresh screen if dialog was drawn
            if dialog_drawn:
                self.stdscr.refresh()
            
            # Get user input with timeout to allow timer checks
            self.stdscr.timeout(16)  # 16ms timeout
            key = self.stdscr.getch()
            current_pane = self.get_current_pane()
            
            # If no key was pressed (timeout), continue to next iteration
            if key == -1:
                continue
            
            # Handle isearch mode input first
            if self.isearch_mode:
                if self.handle_isearch_input(key):
                    continue  # Isearch mode handled the key
            
            # Handle general dialog input
            if self.general_dialog.is_active:
                if self.general_dialog.handle_key(key):
                    continue  # General dialog handled the key
            
            # Handle quick choice mode input
            if self.quick_choice_bar.mode:
                if self.handle_quick_choice_input(key):
                    continue  # Quick choice mode handled the key
            
            # Handle info dialog mode input
            if self.info_dialog.mode:
                if self.handle_info_dialog_input(key):
                    continue  # Info dialog mode handled the key
            
            # Handle list dialog mode input
            if self.list_dialog.mode:
                if self.handle_list_dialog_input(key):
                    continue  # List dialog mode handled the key
            
            # Handle search dialog mode input
            if self.search_dialog.mode:
                if self.handle_search_dialog_input(key):
                    continue  # Search dialog mode handled the key
            
            # Handle batch rename dialog mode input
            if self.batch_rename_dialog.mode:
                if self.handle_batch_rename_input(key):
                    continue  # Batch rename mode handled the key
            
            # Skip regular key processing if any dialog is open
            # This prevents conflicts like starting isearch mode while help dialog is open
            if self.quick_choice_bar.mode or self.info_dialog.mode or self.list_dialog.mode or self.search_dialog.mode or self.batch_rename_dialog.mode or self.isearch_mode or self.general_dialog.is_active:
                continue
            
            if self.is_key_for_action(key, 'quit'):
                def quit_callback(confirmed):
                    if confirmed:
                        # Set a flag to exit the main loop
                        self.should_quit = True
                
                # Check if quit confirmation is enabled
                if getattr(self.config, 'CONFIRM_QUIT', True):
                    self.show_confirmation("Are you sure you want to quit TFM?", quit_callback)
                else:
                    quit_callback(True)
            elif key == KEY_CTRL_U:  # Ctrl+U - make log pane smaller
                self.adjust_log_boundary('up')
            elif key == KEY_CTRL_D:  # Ctrl+D - make log pane larger
                self.adjust_log_boundary('down')
            elif key == 11:  # Ctrl+K - scroll log up
                if self.log_manager.scroll_log_up(1):
                    self.needs_full_redraw = True
            elif key == 12:  # Ctrl+L - scroll log down
                if self.log_manager.scroll_log_down(1):
                    self.needs_full_redraw = True
            elif key == curses.KEY_RESIZE:  # Terminal window resized
                # Clear screen and trigger full redraw to handle new dimensions
                self.clear_screen_with_background()
                self.needs_full_redraw = True
            elif key == KEY_TAB:  # Tab key - switch panes
                self.pane_manager.active_pane = 'right' if self.pane_manager.active_pane == 'left' else 'left'
                self.needs_full_redraw = True
            elif key == curses.KEY_UP:
                if current_pane['selected_index'] > 0:
                    current_pane['selected_index'] -= 1
                    self.needs_full_redraw = True
            elif key == curses.KEY_DOWN:
                if current_pane['selected_index'] < len(current_pane['files']) - 1:
                    current_pane['selected_index'] += 1
                    self.needs_full_redraw = True
            elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
                self.handle_enter()
                self.needs_full_redraw = True
            elif self.is_key_for_action(key, 'toggle_hidden'):
                self.file_operations.toggle_hidden_files()
                # Reset both panes
                self.pane_manager.left_pane['selected_index'] = 0
                self.pane_manager.left_pane['scroll_offset'] = 0
                self.pane_manager.right_pane['selected_index'] = 0
                self.pane_manager.right_pane['scroll_offset'] = 0
                self.needs_full_redraw = True
            elif self.is_key_for_action(key, 'toggle_color_scheme'):
                # Toggle between dark and light color schemes
                new_scheme = toggle_color_scheme()
                # Reinitialize colors with the new scheme
                init_colors(new_scheme)
                print(f"Switched to {new_scheme} color scheme")
                # Print detailed color scheme info to log
                self.print_color_scheme_info()
                self.needs_full_redraw = True
            elif key == curses.KEY_HOME:
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
                self.needs_full_redraw = True
            elif key == curses.KEY_END:
                current_pane['selected_index'] = max(0, len(current_pane['files']) - 1)
                self.needs_full_redraw = True
            elif key == curses.KEY_PPAGE:  # Page Up - scroll log up when Ctrl is held, otherwise file navigation
                # Check if this is Ctrl+Page Up for log scrolling
                if self.log_manager.scroll_log_up(5):
                    self.needs_full_redraw = True
                else:
                    # Regular file navigation
                    current_pane['selected_index'] = max(0, current_pane['selected_index'] - 10)
                    self.needs_full_redraw = True
            elif key == curses.KEY_NPAGE:  # Page Down - scroll log down when Ctrl is held, otherwise file navigation  
                # Check if this is Ctrl+Page Down for log scrolling
                if self.log_manager.scroll_log_down(5):
                    self.needs_full_redraw = True
                else:
                    # Regular file navigation
                    current_pane['selected_index'] = min(len(current_pane['files']) - 1, current_pane['selected_index'] + 10)
                    self.needs_full_redraw = True
            elif key == curses.KEY_BACKSPACE or key == KEY_BACKSPACE_2 or key == KEY_BACKSPACE_1:  # Backspace - go to parent directory
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        # Save current cursor position before changing directory
                        self.save_cursor_position(current_pane)
                        
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()  # Clear selections when changing directory
                        self.refresh_files(current_pane)
                        
                        # Try to restore cursor position for this directory
                        if not self.restore_cursor_position(current_pane):
                            # If no history found, default to first item
                            current_pane['selected_index'] = 0
                            current_pane['scroll_offset'] = 0
                        
                        self.needs_full_redraw = True
                    except PermissionError:
                        self.show_error("Permission denied")
                        self.needs_full_redraw = True
            elif key == curses.KEY_LEFT and self.pane_manager.active_pane == 'left':  # Left arrow in left pane - go to parent
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        # Save current cursor position before changing directory
                        self.save_cursor_position(current_pane)
                        
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()  # Clear selections when changing directory
                        self.refresh_files(current_pane)
                        
                        # Try to restore cursor position for this directory
                        if not self.restore_cursor_position(current_pane):
                            # If no history found, default to first item
                            current_pane['selected_index'] = 0
                            current_pane['scroll_offset'] = 0
                        
                        self.needs_full_redraw = True
                    except PermissionError:
                        self.show_error("Permission denied")
            elif key == curses.KEY_RIGHT and self.pane_manager.active_pane == 'right':  # Right arrow in right pane - go to parent
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        # Save current cursor position before changing directory
                        self.save_cursor_position(current_pane)
                        
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()  # Clear selections when changing directory
                        self.refresh_files(current_pane)
                        
                        # Try to restore cursor position for this directory
                        if not self.restore_cursor_position(current_pane):
                            # If no history found, default to first item
                            current_pane['selected_index'] = 0
                            current_pane['scroll_offset'] = 0
                        
                        self.needs_full_redraw = True
                    except PermissionError:
                        self.show_error("Permission denied")
            elif key == curses.KEY_RIGHT and self.pane_manager.active_pane == 'left':  # Right arrow in left pane - switch to right pane
                self.pane_manager.active_pane = 'right'
                self.needs_full_redraw = True
            elif key == curses.KEY_LEFT and self.pane_manager.active_pane == 'right':  # Left arrow in right pane - switch to left pane
                self.pane_manager.active_pane = 'left'
                self.needs_full_redraw = True
            elif key in (KEY_SHIFT_UP_1,KEY_SHIFT_UP_2):  # Shift+Up
                if self.log_manager.scroll_log_up(1):
                    self.needs_full_redraw = True
            elif key in (KEY_SHIFT_DOWN_1, KEY_SHIFT_DOWN_2):  # Shift+Down
                if self.log_manager.scroll_log_down(1):
                    self.needs_full_redraw = True
            elif key in (KEY_SHIFT_LEFT_1, KEY_SHIFT_LEFT_2):  # Shift+Left - fast scroll to older messages
                log_height = self._get_log_pane_height()
                if self.log_manager.scroll_log_up(max(1, log_height)):
                    self.needs_full_redraw = True
            elif key in (KEY_SHIFT_RIGHT_1, KEY_SHIFT_RIGHT_2):  # Shift+Right - fast scroll to newer messages
                log_height = self._get_log_pane_height()
                if self.log_manager.scroll_log_down(max(1, log_height)):
                    self.needs_full_redraw = True
            elif self.is_key_for_action(key, 'select_file'):  # Toggle file selection
                self.toggle_selection()
                self.needs_full_redraw = True

            elif key == 0:  # Ctrl+Space - toggle selection and move up
                self.toggle_selection_up()
                self.needs_full_redraw = True
            elif key == 19:  # Ctrl+S - toggle selection and move up  
                self.toggle_selection_up()
                self.needs_full_redraw = True
            elif key == 27:  # ESC key - check for Option key sequences
                # Option+Space sends 194 followed by 160
                next_key = self.stdscr.getch()
                # Log unknown ESC sequence for debugging
                print(f"Unknown ESC sequence: 27, {next_key}")
            elif key == 194:  # Option+Space sequence (first byte)
                # Option+Space sends 194 followed by 160 on macOS
                next_key = self.stdscr.getch()
                if next_key == 160:  # Option+Space
                    self.toggle_selection_up()
                    self.needs_full_redraw = True
                else:
                    # Log unknown Option key sequence for debugging
                    print(f"Unknown Option key sequence: 194, {next_key}")
            elif self.is_key_for_action(key, 'select_all_files'):  # Toggle all files selection
                self.toggle_all_files_selection()
            elif self.is_key_for_action(key, 'select_all_items'):  # Toggle all items selection
                self.toggle_all_items_selection()
            elif self.is_key_for_action(key, 'sync_panes'):  # Sync panes
                # Handle both 'o' and 'O' for sync operations
                if key == ord('O'):  # Shift+O - sync other pane to current
                    self.sync_other_pane_directory()
                else:  # 'o' - sync current pane to other
                    self.sync_pane_directories()
            elif key == ord('F'):  # 'F' key (Shift-F) - show search dialog (filename)
                self.show_search_dialog('filename')
            elif key == ord('G'):  # 'G' key (Shift-G) - show search dialog (content)
                self.show_search_dialog('content')
            elif key == ord('e'):  # 'e' key - edit existing file
                self.edit_selected_file()
            elif key == ord('E'):  # 'E' key (Shift-E) - create new file
                self.enter_create_file_mode()
            elif key == ord('L'):  # 'L' key - show list dialog demo
                self.show_list_dialog_demo()
            elif key == ord('t'):  # 't' key - show file type filter
                self.show_file_type_filter()
            elif key == ord('T'):  # 'T' key (Shift+T) - toggle fallback color mode
                self.toggle_fallback_color_mode()
            elif key == ord('z'):  # 'z' key - show view options
                self.show_view_options()
            elif key == ord('Z'):  # 'Z' key (Shift+Z) - show settings menu
                self.show_settings_menu()
            elif self.is_key_for_action(key, 'search'):  # Search key - enter isearch mode
                self.enter_isearch_mode()
            elif self.is_key_for_action(key, 'filter'):  # Filter key - enter filter mode
                self.enter_filter_mode()
            elif self.is_key_for_action(key, 'clear_filter'):  # Clear filter key
                self.clear_filter()
            elif self.is_key_for_action(key, 'sort_menu'):  # Sort menu
                self.show_sort_menu()
            elif self.is_key_for_action(key, 'quick_sort_name'):  # Quick sort by name
                self.quick_sort('name')
            elif self.is_key_for_action(key, 'quick_sort_size'):  # Quick sort by size
                self.quick_sort('size')
            elif self.is_key_for_action(key, 'quick_sort_date'):  # Quick sort by date
                self.quick_sort('date')
            elif self.is_key_for_action(key, 'quick_sort_ext'):  # Quick sort by extension
                self.quick_sort('ext')
            elif self.is_key_for_action(key, 'file_details'):  # Show file details
                self.show_file_details()
            elif self.is_key_for_action(key, 'view_text'):  # View text file
                self.view_selected_text_file()
            elif self.is_key_for_action(key, 'copy_files'):  # Copy selected files
                self.copy_selected_files()
            elif self.is_key_for_action(key, 'move_files'):  # Move selected files
                self.move_selected_files()
            elif self.is_key_for_action(key, 'delete_files'):  # Delete selected files
                self.delete_selected_files()
            elif self.is_key_for_action(key, 'create_archive'):  # Create archive
                self.enter_create_archive_mode()
            elif self.is_key_for_action(key, 'extract_archive'):  # Extract archive
                self.extract_selected_archive()
            elif self.is_key_for_action(key, 'rename_file'):  # Rename file
                self.enter_rename_mode()
            elif self.is_key_for_action(key, 'favorites'):  # Show favorite directories
                self.show_favorite_directories()
            elif self.is_key_for_action(key, 'programs'):  # Show external programs
                self.show_programs_dialog()
            elif self.is_key_for_action(key, 'compare_selection'):  # Show compare selection menu
                self.show_compare_selection_dialog()
            elif self.is_key_for_action(key, 'help'):  # Show help dialog
                self.show_help_dialog()
            elif self.is_key_for_action(key, 'adjust_pane_left'):  # Adjust pane boundary left
                self.adjust_pane_boundary('left')
            elif self.is_key_for_action(key, 'adjust_pane_right'):  # Adjust pane boundary right
                self.adjust_pane_boundary('right')
            elif self.is_key_for_action(key, 'adjust_log_up'):  # Adjust log boundary up
                self.adjust_log_boundary('down')
            elif self.is_key_for_action(key, 'adjust_log_down'):  # Adjust log boundary down
                self.adjust_log_boundary('up')
            elif key == ord('-'):  # '-' key - reset pane ratio to 50/50
                self.pane_manager.left_pane_ratio = 0.5
                self.needs_full_redraw = True
                print("Pane split reset to 50% | 50%")
            elif self.is_key_for_action(key, 'subshell'):  # Sub-shell mode
                self.stdscr = self.external_program_manager.enter_subshell_mode(
                    self.stdscr, self.pane_manager
                )
                self.needs_full_redraw = True
        
        # Restore stdout/stderr before exiting
        self.restore_stdio()

def main(stdscr):
    """Main function to run the file manager"""
    fm = None
    try:
        fm = FileManager(stdscr)
        fm.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
    except Exception as e:
        # Restore stdout/stderr before handling exception
        if fm is not None:
            fm.restore_stdio()
        
        # Print error information to help with debugging
        import traceback
        print(f"\nTFM encountered an unexpected error:", file=sys.stderr)
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
        print("\nFull traceback:", file=sys.stderr)
        traceback.print_exc()
        
        # Re-raise the exception so it can be seen after TFM exits
        raise
    finally:
        # Always restore stdout/stderr in case of any exit path
        if fm is not None:
            fm.restore_stdio()

if __name__ == "__main__":
    curses.wrapper(main)