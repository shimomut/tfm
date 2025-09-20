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
        
        # Layout settings
        self.log_height_ratio = getattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO', DEFAULT_LOG_HEIGHT_RATIO)
        self.needs_full_redraw = True  # Flag to control when to redraw everything
        
        # Isearch mode state
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        
        # Filter mode state
        self.filter_mode = False
        self.filter_editor = SingleLineTextEdit()
        
        # Rename mode state
        self.rename_mode = False
        self.rename_editor = SingleLineTextEdit()
        self.rename_original_name = ""
        self.rename_file_path = None
        
        # Create directory mode state
        self.create_dir_mode = False
        self.create_dir_editor = SingleLineTextEdit()
        
        # Create file mode state
        self.create_file_mode = False
        self.create_file_editor = SingleLineTextEdit()
        
        # Create archive mode state
        self.create_archive_mode = False
        self.create_archive_editor = SingleLineTextEdit()
        
        # Quick choice dialog state
        self.quick_choice_mode = False
        self.quick_choice_message = ""
        self.quick_choice_choices = []  # List of choice dictionaries: [{"text": "Yes", "key": "y", "value": True}, ...]
        self.quick_choice_callback = None
        self.quick_choice_selected = 0  # Index of currently selected choice
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
            display_height = height - log_height - 4
            
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
            display_height = height - log_height - 4
            
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
            display_height = height - log_height - 4
            
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
            display_height = height - log_height - 4
            
            self.pane_manager.adjust_scroll_for_selection(other_pane, display_height)
            self.needs_full_redraw = True
        
    def restore_cursor_position(self, pane_data):
        """Restore cursor position from history - wrapper for pane_manager method"""
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 4
        return self.pane_manager.restore_cursor_position(pane_data, display_height)
    
    def save_cursor_position(self, pane_data):
        """Save cursor position to history - wrapper for pane_manager method"""
        return self.pane_manager.save_cursor_position(pane_data)
    
    def adjust_scroll_for_selection(self, pane_data):
        """Adjust scroll for selection - wrapper for pane_manager method"""
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 4
        return self.pane_manager.adjust_scroll_for_selection(pane_data, display_height)
    
    def find_matches(self, pattern):
        """Find matches - wrapper for file_operations method"""
        current_pane = self.get_current_pane()
        return self.file_operations.find_matches(current_pane, pattern)
    
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
        return self.log_manager.get_log_scroll_percentage()
    
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
        display_height = height - log_height - 4  # Reserve space for header, log pane, and status
        
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
                    # For narrow panes: "● filename size" (no datetime)
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
                    # For wider panes: "● filename size datetime"
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
        self.log_manager.draw_log_pane(self.stdscr, log_start_y, log_height - 1, width)
                
    def draw_status(self):
        """Draw status line with file info and controls"""
        height, width = self.stdscr.getmaxyx()
        status_y = height - 1
        
        current_pane = self.get_current_pane()
        
        # If in quick choice mode, show quick choice dialog
        if self.quick_choice_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Show dialog message
            message = f"{self.quick_choice_message} "
            self.safe_addstr(status_y, 2, message, get_status_color())
            
            # Show choice buttons
            button_start_x = len(message) + 4
            
            for i, choice in enumerate(self.quick_choice_choices):
                choice_text = choice["text"]
                if i == self.quick_choice_selected:
                    # Highlight selected option with bold and standout
                    button_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                    button_text = f"[{choice_text}]"
                else:
                    button_color = get_status_color()
                    button_text = f" {choice_text} "
                
                if button_start_x + len(button_text) < width - 2:
                    self.safe_addstr(status_y, button_start_x, button_text, button_color)
                    button_start_x += len(button_text) + 1
            
            # Generate help text based on available quick keys
            quick_keys = []
            for choice in self.quick_choice_choices:
                if "key" in choice and choice["key"]:
                    quick_keys.append(choice["key"].upper())
            
            help_parts = ["←→:select", "Enter:confirm"]
            if quick_keys:
                help_parts.append(f"{'/'.join(quick_keys)}:quick")
            help_parts.append("ESC:cancel")
            help_text = " ".join(help_parts)
            
            if button_start_x + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > button_start_x + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
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
        
        # If in filter mode, show filter interface
        if self.filter_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Draw filter input using SingleLineTextEdit
            max_input_width = width - 50  # Leave space for help text
            self.filter_editor.draw(
                self.stdscr, status_y, 2, max_input_width,
                "Filter: ",
                is_active=True
            )
            
            # Show help text on the right if there's space
            help_text = "ESC:cancel Enter:apply (files only: *.py, test_*, *.[ch])"
            # Calculate space needed for the input field
            input_field_width = len("Filter: ") + len(self.filter_editor.text) + 2
            if input_field_width + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > input_field_width + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
            else:
                # Shorter help text for narrow terminals
                short_help = "ESC:cancel Enter:apply"
                if input_field_width + len(short_help) + 6 < width:
                    help_x = width - len(short_help) - 3
                    if help_x > input_field_width + 4:
                        self.safe_addstr(status_y, help_x, short_help, get_status_color() | curses.A_DIM)
            return
        
        # If in rename mode, show rename interface
        if self.rename_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Draw rename input using SingleLineTextEdit
            prompt_text = f"Rename '{self.rename_original_name}' to: "
            max_input_width = width - len(prompt_text) - 25  # Leave space for help text
            self.rename_editor.draw(
                self.stdscr, status_y, 2, max_input_width,
                prompt_text,
                is_active=True
            )
            
            # Show help text on the right if there's space
            help_text = "ESC:cancel Enter:confirm"
            # Calculate space needed for the input field
            input_field_width = len(prompt_text) + len(self.rename_editor.text) + 2
            if input_field_width + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > input_field_width + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
            return
        
        # If in create directory mode, show create directory interface
        if self.create_dir_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Draw create directory input using SingleLineTextEdit
            max_input_width = width - 20  # Leave space for help text
            self.create_dir_editor.draw(
                self.stdscr, status_y, 2, max_input_width,
                "Create directory: ",
                is_active=True
            )
            
            # Show help text on the right if there's space
            help_text = "ESC:cancel Enter:create"
            # Calculate space needed for the input field
            input_field_width = len("Create directory: ") + len(self.create_dir_editor.text) + 2
            if input_field_width + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > input_field_width + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
            return
        
        # If in create file mode, show create file interface
        if self.create_file_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Draw create file input using SingleLineTextEdit
            max_input_width = width - 20  # Leave space for help text
            self.create_file_editor.draw(
                self.stdscr, status_y, 2, max_input_width,
                "Create file: ",
                is_active=True
            )
            
            # Show help text on the right if there's space
            help_text = "ESC:cancel Enter:create"
            # Calculate space needed for the input field
            input_field_width = len("Create file: ") + len(self.create_file_editor.text) + 2
            if input_field_width + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > input_field_width + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
            return
        
        # If in create archive mode, show create archive interface
        if self.create_archive_mode:
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line, get_status_color())
            
            # Draw create archive input using SingleLineTextEdit
            max_input_width = width - 35  # Leave space for help text
            self.create_archive_editor.draw(
                self.stdscr, status_y, 2, max_input_width,
                "Archive filename: ",
                is_active=True
            )
            
            # Show help text on the right if there's space
            help_text = "ESC:cancel Enter:create (.zip/.tar.gz/.tgz)"
            # Calculate space needed for the input field
            input_field_width = len("Archive filename: ") + len(self.create_archive_editor.text) + 2
            if input_field_width + len(help_text) + 6 < width:
                help_x = width - len(help_text) - 3
                if help_x > input_field_width + 4:  # Ensure no overlap
                    self.safe_addstr(status_y, help_x, help_text, get_status_color() | curses.A_DIM)
            return
        
        # Normal status display
        # Left side: status info
        status_parts = []
        if self.file_operations.show_hidden:
            status_parts.append("showing hidden")
        
        # Add log scroll percentage
        log_percentage = self.get_log_scroll_percentage()
        status_parts.append(f"log: {log_percentage}%")
        
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
        matches = []
        
        if not pattern or not current_pane['files']:
            return matches
            
        # Split pattern by spaces to get individual patterns
        patterns = pattern.strip().split()
        if not patterns:
            return matches
            
        # Convert all patterns to lowercase for case-insensitive matching
        # and wrap each pattern with wildcards to match "contains" behavior
        wrapped_patterns = []
        for p in patterns:
            p_lower = p.lower()
            # If pattern doesn't start with *, add it for "contains" matching
            if not p_lower.startswith('*'):
                p_lower = '*' + p_lower
            # If pattern doesn't end with *, add it for "contains" matching  
            if not p_lower.endswith('*'):
                p_lower = p_lower + '*'
            wrapped_patterns.append(p_lower)
        
        for i, file_path in enumerate(current_pane['files']):
            # Parent directory (..) is no longer shown
            filename = file_path.name.lower()
            
            # Check if filename matches ALL patterns
            all_match = True
            for wrapped_pattern in wrapped_patterns:
                if not fnmatch.fnmatch(filename, wrapped_pattern):
                    all_match = False
                    break
                    
            if all_match:
                matches.append(i)
                
        return matches
        
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
        display_height = height - log_height - 4  # Reserve space for header, log pane, and status
        
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
        self.filter_mode = True
        current_pane = self.get_current_pane()
        self.filter_editor.text = current_pane['filter_pattern']  # Start with current filter
        self.filter_editor.cursor_pos = len(self.filter_editor.text)  # Position cursor at end
        self.needs_full_redraw = True
        
    def exit_filter_mode(self):
        """Exit filter mode"""
        self.filter_mode = False
        self.filter_editor.clear()
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
        
        # Enter rename mode
        self.rename_mode = True
        self.rename_file_path = selected_file
        self.rename_original_name = selected_file.name
        self.rename_editor.text = selected_file.name  # Start with current name
        self.rename_editor.cursor_pos = len(self.rename_editor.text)  # Position cursor at end
        self.needs_full_redraw = True
        print(f"Renaming: {self.rename_original_name}")
    
    def exit_rename_mode(self):
        """Exit rename mode"""
        self.rename_mode = False
        self.rename_editor.clear()
        self.rename_original_name = ""
        self.rename_file_path = None
        self.needs_full_redraw = True
    
    def enter_create_directory_mode(self):
        """Enter create directory mode"""
        current_pane = self.get_current_pane()
        
        # Check if current directory is writable
        if not os.access(current_pane['path'], os.W_OK):
            print(f"Permission denied: Cannot create directory in {current_pane['path']}")
            return
        
        # Enter create directory mode
        self.create_dir_mode = True
        self.create_dir_editor.clear()
        self.needs_full_redraw = True
        print("Creating new directory...")
    
    def exit_create_directory_mode(self):
        """Exit create directory mode"""
        self.create_dir_mode = False
        self.create_dir_editor.clear()
        self.needs_full_redraw = True
    
    def perform_create_directory(self):
        """Perform the actual directory creation"""
        if not self.create_dir_editor.text.strip():
            print("Invalid directory name")
            self.exit_create_directory_mode()
            return
        
        current_pane = self.get_current_pane()
        new_dir_name = self.create_dir_editor.text.strip()
        new_dir_path = current_pane['path'] / new_dir_name
        
        # Check if directory already exists
        if new_dir_path.exists():
            print(f"Directory '{new_dir_name}' already exists")
            self.exit_create_directory_mode()
            return
        
        try:
            # Create the directory
            new_dir_path.mkdir(parents=True, exist_ok=False)
            print(f"Created directory: {new_dir_name}")
            
            # Refresh the current pane to show the new directory
            self.refresh_files(current_pane)
            
            # Move cursor to the newly created directory
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_dir_name:
                    current_pane['selected_index'] = i
                    # Adjust scroll if needed
                    height, width = self.stdscr.getmaxyx()
                    calculated_height = int(height * self.log_height_ratio)
                    log_height = calculated_height if self.log_height_ratio > 0 else 0
                    display_height = height - log_height - 4
                    
                    if current_pane['selected_index'] < current_pane['scroll_offset']:
                        current_pane['scroll_offset'] = current_pane['selected_index']
                    elif current_pane['selected_index'] >= current_pane['scroll_offset'] + display_height:
                        current_pane['scroll_offset'] = current_pane['selected_index'] - display_height + 1
                    break
            
            self.exit_create_directory_mode()
            
        except OSError as e:
            print(f"Failed to create directory '{new_dir_name}': {e}")
            self.exit_create_directory_mode()
    
    def enter_create_file_mode(self):
        """Enter create file mode"""
        current_pane = self.get_current_pane()
        
        # Check if current directory is writable
        if not os.access(current_pane['path'], os.W_OK):
            print(f"Permission denied: Cannot create file in {current_pane['path']}")
            return
        
        # Enter create file mode
        self.create_file_mode = True
        self.create_file_editor.clear()
        self.needs_full_redraw = True
        print("Creating new text file...")
    
    def exit_create_file_mode(self):
        """Exit create file mode"""
        self.create_file_mode = False
        self.create_file_editor.clear()
        self.needs_full_redraw = True
    
    def perform_create_file(self):
        """Perform the actual file creation"""
        file_name = self.create_file_editor.get_text().strip()
        if not file_name:
            print("Invalid file name")
            self.exit_create_file_mode()
            return
        
        current_pane = self.get_current_pane()
        new_file_name = file_name
        new_file_path = current_pane['path'] / new_file_name
        
        # Check if file already exists
        if new_file_path.exists():
            print(f"File '{new_file_name}' already exists")
            self.exit_create_file_mode()
            return
        
        try:
            # Create the empty file
            new_file_path.touch()
            print(f"Created file: {new_file_name}")
            
            # Refresh the current pane to show the new file
            self.refresh_files(current_pane)
            
            # Move cursor to the newly created file
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_file_name:
                    current_pane['selected_index'] = i
                    # Adjust scroll if needed
                    height, width = self.stdscr.getmaxyx()
                    calculated_height = int(height * self.log_height_ratio)
                    log_height = calculated_height if self.log_height_ratio > 0 else 0
                    display_height = height - log_height - 4
                    
                    if current_pane['selected_index'] < current_pane['scroll_offset']:
                        current_pane['scroll_offset'] = current_pane['selected_index']
                    elif current_pane['selected_index'] >= current_pane['scroll_offset'] + display_height:
                        current_pane['scroll_offset'] = current_pane['selected_index'] - display_height + 1
                    break
            
            # Automatically open the file in the text editor
            self.edit_selected_file()
            
            self.exit_create_file_mode()
            
        except OSError as e:
            print(f"Failed to create file '{new_file_name}': {e}")
            self.exit_create_file_mode()
    
    def perform_rename(self):
        """Perform the actual rename operation"""
        if not self.rename_file_path or not self.rename_editor.text.strip():
            print("Invalid rename operation")
            self.exit_rename_mode()
            return
        
        new_name = self.rename_editor.text.strip()
        
        # Check if name actually changed
        if new_name == self.rename_original_name:
            print("Name unchanged")
            self.exit_rename_mode()
            return
        
        # Check for invalid characters (basic validation)
        if '/' in new_name or '\0' in new_name:
            print("Invalid characters in filename")
            return
        
        # Check if new name is empty
        if not new_name:
            print("Filename cannot be empty")
            return
        
        # Create new path
        new_path = self.rename_file_path.parent / new_name
        
        # Check if target already exists
        if new_path.exists():
            print(f"File or directory '{new_name}' already exists")
            return
        
        try:
            # Perform the rename
            self.rename_file_path.rename(new_path)
            print(f"Renamed '{self.rename_original_name}' to '{new_name}'")
            
            # Refresh the current pane
            current_pane = self.get_current_pane()
            self.refresh_files(current_pane)
            
            # Try to select the renamed file
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_name:
                    current_pane['selected_index'] = i
                    break
            
            self.exit_rename_mode()
            
        except PermissionError:
            print(f"Permission denied renaming '{self.rename_original_name}'")
        except FileExistsError:
            print(f"File '{new_name}' already exists")
        except Exception as e:
            print(f"Error renaming file: {e}")
    
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
        """Show quick choice dialog
        
        Args:
            message: The message to display
            choices: List of choice dictionaries with format:
                     [{"text": "Yes", "key": "y", "value": True}, 
                      {"text": "No", "key": "n", "value": False},
                      {"text": "Cancel", "key": "c", "value": None}]
            callback: Function to call with the selected choice's value
        """
        self.quick_choice_mode = True
        self.quick_choice_message = message
        self.quick_choice_choices = choices
        self.quick_choice_callback = callback
        self.quick_choice_selected = 0  # Default to first choice
        self.needs_full_redraw = True
    
    def show_confirmation(self, message, callback):
        """Show confirmation dialog with Yes/No/Cancel options (backward compatibility)"""
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False},
            {"text": "Cancel", "key": "c", "value": None}
        ]
        self.show_dialog(message, choices, callback)
        
    def exit_quick_choice_mode(self):
        """Exit quick choice mode"""
        self.quick_choice_mode = False
        self.quick_choice_message = ""
        self.quick_choice_choices = []
        self.quick_choice_callback = None
        self.quick_choice_selected = 0
        self.needs_full_redraw = True
    
    def exit_confirmation_mode(self):
        """Exit confirmation mode (backward compatibility)"""
        self.exit_quick_choice_mode()
        
    def handle_quick_choice_input(self, key):
        """Handle input while in quick choice mode"""
        if key == 27:  # ESC - cancel
            self.exit_quick_choice_mode()
            return True
        elif key == curses.KEY_LEFT:
            # Move selection left
            if self.quick_choice_choices:
                self.quick_choice_selected = (self.quick_choice_selected - 1) % len(self.quick_choice_choices)
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_RIGHT:
            # Move selection right
            if self.quick_choice_choices:
                self.quick_choice_selected = (self.quick_choice_selected + 1) % len(self.quick_choice_choices)
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Execute selected action
            if self.quick_choice_choices and 0 <= self.quick_choice_selected < len(self.quick_choice_choices):
                selected_choice = self.quick_choice_choices[self.quick_choice_selected]
                if self.quick_choice_callback:
                    self.quick_choice_callback(selected_choice["value"])
            self.exit_quick_choice_mode()
            return True
        else:
            # Check for quick key matches
            key_char = chr(key).lower() if 32 <= key <= 126 else None
            if key_char:
                for choice in self.quick_choice_choices:
                    if "key" in choice and choice["key"] and choice["key"].lower() == key_char:
                        # Found matching quick key
                        if self.quick_choice_callback:
                            self.quick_choice_callback(choice["value"])
                        self.exit_quick_choice_mode()
                        return True
    
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
        ListDialogHelpers.show_programs_dialog(
            self.list_dialog, self.execute_external_program, print
        )
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def execute_external_program(self, program):
        """Execute an external program with environment variables set"""
        # Restore stdout/stderr temporarily
        self.restore_stdio()
        
        # Clear the screen and reset cursor
        self.stdscr.clear()
        self.stdscr.refresh()
        
        # Reset terminal to normal mode
        curses.endwin()
        
        try:
            # Get current pane information
            left_pane = self.left_pane
            right_pane = self.right_pane
            current_pane = self.get_current_pane()
            other_pane = self.get_inactive_pane()
            
            # Set environment variables with TFM_ prefix
            env = os.environ.copy()
            env['TFM_LEFT_DIR'] = str(left_pane['path'])
            env['TFM_RIGHT_DIR'] = str(right_pane['path'])
            env['TFM_THIS_DIR'] = str(current_pane['path'])
            env['TFM_OTHER_DIR'] = str(other_pane['path'])
            
            # Get selected files for each pane, or cursor position if no selection
            def get_selected_or_cursor(pane_data):
                """Get selected files, or current cursor position if no files selected"""
                selected = [Path(f).name for f in pane_data['selected_files']]
                if not selected and pane_data['files'] and pane_data['selected_index'] < len(pane_data['files']):
                    # No files selected, use cursor position
                    cursor_file = pane_data['files'][pane_data['selected_index']]
                    selected = [cursor_file.name]
                return selected
            
            def quote_filenames(filenames):
                """Quote filenames for safe shell usage"""
                return [shlex.quote(filename) for filename in filenames]
            
            left_selected = quote_filenames(get_selected_or_cursor(left_pane))
            right_selected = quote_filenames(get_selected_or_cursor(right_pane))
            current_selected = quote_filenames(get_selected_or_cursor(current_pane))
            other_selected = quote_filenames(get_selected_or_cursor(other_pane))
            
            # Set selected files environment variables (space-separated) with TFM_ prefix
            env['TFM_LEFT_SELECTED'] = ' '.join(left_selected)
            env['TFM_RIGHT_SELECTED'] = ' '.join(right_selected)
            env['TFM_THIS_SELECTED'] = ' '.join(current_selected)
            env['TFM_OTHER_SELECTED'] = ' '.join(other_selected)
            
            # Set TFM indicator environment variable
            env['TFM_ACTIVE'] = '1'
            
            # Print information about the program execution
            print(f"TFM External Program: {program['name']}")
            print("=" * 50)
            print(f"Command: {' '.join(program['command'])}")
            print(f"Working Directory: {current_pane['path']}")
            print(f"TFM_THIS_DIR: {env['TFM_THIS_DIR']}")
            print(f"TFM_THIS_SELECTED: {env['TFM_THIS_SELECTED']}")
            print("=" * 50)
            print()
            
            # Change to the current directory
            os.chdir(current_pane['path'])
            
            # Execute the program with the modified environment
            result = subprocess.run(program['command'], env=env)
            
            # Check if auto_return option is enabled
            auto_return = program.get('options', {}).get('auto_return', False)
            
            # Show exit status
            print()
            print("=" * 50)
            if result.returncode == 0:
                print(f"Program '{program['name']}' completed successfully")
            else:
                print(f"Program '{program['name']}' exited with code {result.returncode}")
            
            if auto_return:
                print("Auto-returning to TFM...")
                import time
                time.sleep(1)  # Brief pause to show the message
            else:
                print("Press Enter to return to TFM...")
                input()
            
        except FileNotFoundError:
            print(f"Error: Command not found: {program['command'][0]}")
            print("Press Enter to continue...")
            input()
        except Exception as e:
            print(f"Error executing program '{program['name']}': {e}")
            print("Press Enter to continue...")
            input()
        
        finally:
            # Reinitialize curses
            self.stdscr = curses.initscr()
            curses.curs_set(0)  # Hide cursor
            self.stdscr.keypad(True)
            
            # Reinitialize colors with configured scheme
            color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
            init_colors(color_scheme)
            
            # Restore stdout/stderr capture
            from tfm_log_manager import LogCapture
            sys.stdout = LogCapture(self.log_manager.log_messages, "STDOUT")
            sys.stderr = LogCapture(self.log_manager.log_messages, "STDERR")
            
            # Log return from program execution
            print(f"Returned from external program: {program['name']}")
            
            # Force full redraw
            self.needs_full_redraw = True
    
    def show_sort_menu(self):
        """Show sort options menu using the quick choice dialog"""
        current_pane = self.get_current_pane()
        
        # Get current sort mode for display
        current_mode = current_pane['sort_mode']
        current_reverse = current_pane['sort_reverse']
        
        # Define the sort choices with current mode indication
        choices = [
            {"text": f"Name {'★' if current_mode == 'name' else ''}", "key": "n", "value": "name"},
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
            elif sort_type in ["name", "size", "date"]:
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
        current_scheme = get_current_color_scheme()
        available_schemes = get_available_color_schemes()
        
        print(f"Color scheme: {current_scheme}")
        print(f"Available schemes: {', '.join(available_schemes)}")
        
        # Get current scheme colors for key elements
        rgb_colors = get_current_rgb_colors()
        key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'SELECTED_FG', 'REGULAR_FILE_FG']
        
        for color_name in key_colors:
            if color_name in rgb_colors:
                rgb = rgb_colors[color_name]['rgb']
                print(f"  {color_name}: RGB{rgb}")
    
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
    
    def suspend_curses(self):
        """Suspend the curses system to allow external programs to run"""
        curses.endwin()
        
    def resume_curses(self):
        """Resume the curses system after external program execution"""
        self.stdscr.refresh()
        curses.curs_set(0)  # Hide cursor
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
            self.suspend_curses()
            
            # Launch the text editor as a subprocess
            import subprocess
            result = subprocess.run([editor, str(selected_file)], 
                                  cwd=str(current_pane['path']))
            
            # Resume curses
            self.resume_curses()
            
            if result.returncode == 0:
                print(f"Edited file: {selected_file.name}")
            else:
                print(f"Editor exited with code {result.returncode}")
                
        except FileNotFoundError:
            # Resume curses even if editor not found
            self.resume_curses()
            print(f"Text editor '{editor}' not found. Please install it or configure a different editor.")
        except Exception as e:
            # Resume curses even if there's an error
            self.resume_curses()
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
        
        # Start copying files
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
        """Perform the actual copy operation"""
        copied_count = 0
        error_count = 0
        
        for source_file in files_to_copy:
            try:
                dest_path = destination_dir / source_file.name
                
                # Skip if file exists and we're not overwriting
                if dest_path.exists() and not overwrite:
                    continue
                
                if source_file.is_dir():
                    # Copy directory recursively
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_file, dest_path)
                    print(f"Copied directory: {source_file.name}")
                else:
                    # Copy file
                    shutil.copy2(source_file, dest_path)
                    print(f"Copied file: {source_file.name}")
                
                copied_count += 1
                
            except PermissionError as e:
                print(f"Permission denied copying {source_file.name}: {e}")
                error_count += 1
            except Exception as e:
                print(f"Error copying {source_file.name}: {e}")
                error_count += 1
        
        # Refresh both panes to show the copied files
        self.refresh_files()
        self.needs_full_redraw = True
        
        # Clear selections after successful copy
        if copied_count > 0:
            current_pane = self.get_current_pane()
            current_pane['selected_files'].clear()
        
        if error_count > 0:
            print(f"Copy completed with {error_count} errors")
    
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
        
        # Start moving files
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
        """Perform the actual move operation"""
        moved_count = 0
        error_count = 0
        
        for source_file in files_to_move:
            try:
                dest_path = destination_dir / source_file.name
                
                # Skip if file exists and we're not overwriting
                if dest_path.exists() and not overwrite:
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
                    link_target = os.readlink(str(source_file))
                    dest_path.symlink_to(link_target)
                    source_file.unlink()
                    print(f"Moved symbolic link: {source_file.name}")
                elif source_file.is_dir():
                    # Move directory recursively
                    shutil.move(str(source_file), str(dest_path))
                    print(f"Moved directory: {source_file.name}")
                else:
                    # Move file
                    shutil.move(str(source_file), str(dest_path))
                    print(f"Moved file: {source_file.name}")
                
                moved_count += 1
                
            except PermissionError as e:
                print(f"Permission denied moving {source_file.name}: {e}")
                error_count += 1
            except Exception as e:
                print(f"Error moving {source_file.name}: {e}")
                error_count += 1
        
        # Refresh both panes to show the moved files
        self.refresh_files()
        self.needs_full_redraw = True
        
        # Clear selections after successful move
        if moved_count > 0:
            current_pane = self.get_current_pane()
            current_pane['selected_files'].clear()
        
        if error_count > 0:
            print(f"Move completed with {error_count} errors")
    
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
        
        def handle_delete_confirmation(confirmed):
            if confirmed:
                self.perform_delete_operation(files_to_delete)
            else:
                print("Delete operation cancelled")
        
        self.show_dialog(message, choices, handle_delete_confirmation)
    
    def perform_delete_operation(self, files_to_delete):
        """Perform the actual delete operation"""
        deleted_count = 0
        error_count = 0
        
        for file_path in files_to_delete:
            try:
                if file_path.is_symlink():
                    # Delete symbolic link (not its target)
                    file_path.unlink()
                    print(f"Deleted symbolic link: {file_path.name}")
                elif file_path.is_dir():
                    # Delete directory recursively
                    shutil.rmtree(file_path)
                    print(f"Deleted directory: {file_path.name}")
                else:
                    # Delete file
                    file_path.unlink()
                    print(f"Deleted file: {file_path.name}")
                
                deleted_count += 1
                
            except PermissionError as e:
                print(f"Permission denied deleting {file_path.name}: {e}")
                error_count += 1
            except FileNotFoundError:
                print(f"File not found (already deleted?): {file_path.name}")
                error_count += 1
            except Exception as e:
                print(f"Error deleting {file_path.name}: {e}")
                error_count += 1
        
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
        
        # Enter archive creation mode
        self.create_archive_mode = True
        self.create_archive_editor.clear()
        self.needs_full_redraw = True
        
        # Log what we're about to archive
        if len(files_to_archive) == 1:
            print(f"Creating archive from: {files_to_archive[0].name}")
        else:
            print(f"Creating archive from {len(files_to_archive)} selected items")
        print("Enter archive filename (with .zip, .tar.gz, or .tgz extension):")
    
    def exit_create_archive_mode(self):
        """Exit archive creation mode"""
        self.create_archive_mode = False
        self.create_archive_editor.clear()
        self.needs_full_redraw = True
    
    def handle_create_archive_input(self, key):
        """Handle input while in create archive mode"""
        if key == 27:  # ESC - cancel archive creation
            print("Archive creation cancelled")
            self.exit_create_archive_mode()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - create archive
            self.perform_create_archive()
            return True
        else:
            # Let the editor handle other keys
            if self.create_archive_editor.handle_key(key):
                self.needs_full_redraw = True
                return True
        
        return False
    
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
        """Create a ZIP archive"""
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_archive:
                if file_path.is_file():
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
                            file_full_path = root_path / file
                            file_rel_path = file_full_path.relative_to(file_path.parent)
                            zipf.write(file_full_path, str(file_rel_path))
    
    def create_tar_archive(self, archive_path, files_to_archive):
        """Create a TAR.GZ archive"""
        with tarfile.open(archive_path, 'w:gz') as tarf:
            for file_path in files_to_archive:
                # Add file or directory to archive with its name as the archive name
                tarf.add(file_path, arcname=file_path.name)
    
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
        """Extract a ZIP archive"""
        with zipfile.ZipFile(archive_file, 'r') as zipf:
            # Extract all files to the target directory
            zipf.extractall(extract_dir)
    
    def extract_tar_archive(self, archive_file, extract_dir):
        """Extract a TAR.GZ archive"""
        with tarfile.open(archive_file, 'r:gz') as tarf:
            # Extract all files to the target directory
            tarf.extractall(extract_dir)
        
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
    
    def handle_filter_input(self, key):
        """Handle input while in filter mode"""
        if key == 27:  # ESC - exit filter mode without applying
            self.exit_filter_mode()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - apply filter and exit filter mode
            self.apply_filter()
            self.exit_filter_mode()
            return True
        else:
            # Let the editor handle other keys
            if self.filter_editor.handle_key(key):
                self.needs_full_redraw = True
                return True
        
        # In filter mode, capture most other keys to prevent unintended actions
        return True
    
    def handle_rename_input(self, key):
        """Handle input while in rename mode"""
        if key == 27:  # ESC - cancel rename
            print("Rename cancelled")
            self.exit_rename_mode()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - perform rename
            self.perform_rename()
            return True
        else:
            # Let the editor handle other keys
            if self.rename_editor.handle_key(key):
                self.needs_full_redraw = True
                return True
        
        # In rename mode, capture most other keys to prevent unintended actions
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
    
    def handle_create_directory_input(self, key):
        """Handle input while in create directory mode"""
        if key == 27:  # ESC - cancel directory creation
            print("Directory creation cancelled")
            self.exit_create_directory_mode()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - create directory
            self.perform_create_directory()
            return True
        else:
            # Let the editor handle other keys
            if self.create_dir_editor.handle_key(key):
                self.needs_full_redraw = True
                return True
        
        # In create directory mode, capture most other keys to prevent unintended actions
        return True
    
    def handle_create_file_input(self, key):
        """Handle input while in create file mode"""
        if key == 27:  # ESC - cancel file creation
            print("File creation cancelled")
            self.exit_create_file_mode()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - create file
            self.perform_create_file()
            return True
        else:
            # Let the editor handle other keys
            if self.create_file_editor.handle_key(key):
                self.needs_full_redraw = True
                return True
        
        # In create file mode, capture most other keys to prevent unintended actions
        return True
        
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
        display_height = height - log_height - 4
        
        SearchDialogHelpers.adjust_scroll_for_display_height(current_pane, display_height)
        self.needs_full_redraw = True

    def enter_subshell_mode(self):
        """Enter sub-shell mode with environment variables set"""
        # Restore stdout/stderr temporarily
        self.restore_stdio()
        
        # Clear the screen and reset cursor
        self.stdscr.clear()
        self.stdscr.refresh()
        
        # Reset terminal to normal mode
        curses.endwin()
        
        try:
            # Get current pane information
            left_pane = self.left_pane
            right_pane = self.right_pane
            current_pane = self.get_current_pane()
            other_pane = self.get_inactive_pane()
            
            # Set environment variables with TFM_ prefix
            env = os.environ.copy()
            env['TFM_LEFT_DIR'] = str(left_pane['path'])
            env['TFM_RIGHT_DIR'] = str(right_pane['path'])
            env['TFM_THIS_DIR'] = str(current_pane['path'])
            env['TFM_OTHER_DIR'] = str(other_pane['path'])
            
            # Get selected files for each pane, or cursor position if no selection
            def get_selected_or_cursor(pane_data):
                """Get selected files, or current cursor position if no files selected"""
                selected = [Path(f).name for f in pane_data['selected_files']]
                if not selected and pane_data['files'] and pane_data['selected_index'] < len(pane_data['files']):
                    # No files selected, use cursor position
                    cursor_file = pane_data['files'][pane_data['selected_index']]
                    selected = [cursor_file.name]
                return selected
            
            def quote_filenames(filenames):
                """Quote filenames for safe shell usage"""
                return [shlex.quote(filename) for filename in filenames]
            
            left_selected = quote_filenames(get_selected_or_cursor(left_pane))
            right_selected = quote_filenames(get_selected_or_cursor(right_pane))
            current_selected = quote_filenames(get_selected_or_cursor(current_pane))
            other_selected = quote_filenames(get_selected_or_cursor(other_pane))
            
            # Set selected files environment variables (space-separated) with TFM_ prefix
            # Filenames are properly quoted for shell safety
            env['TFM_LEFT_SELECTED'] = ' '.join(left_selected)
            env['TFM_RIGHT_SELECTED'] = ' '.join(right_selected)
            env['TFM_THIS_SELECTED'] = ' '.join(current_selected)
            env['TFM_OTHER_SELECTED'] = ' '.join(other_selected)
            
            # Set TFM indicator environment variable
            env['TFM_ACTIVE'] = '1'
            
            # Modify shell prompt to include [TFM] label
            # Handle both bash (PS1) and zsh (PROMPT) prompts
            current_ps1 = env.get('PS1', '')
            current_prompt = env.get('PROMPT', '')
            
            # Modify PS1 for bash and other shells
            if current_ps1:
                env['PS1'] = f'[TFM] {current_ps1}'
            else:
                env['PS1'] = '[TFM] \\u@\\h:\\w\\$ '
            
            # Modify PROMPT for zsh
            if current_prompt:
                env['PROMPT'] = f'[TFM] {current_prompt}'
            else:
                env['PROMPT'] = '[TFM] %n@%m:%~%# '
            
            # Print information about the sub-shell environment
            print("TFM Sub-shell Mode")
            print("=" * 50)
            print(f"TFM_LEFT_DIR:      {env['TFM_LEFT_DIR']}")
            print(f"TFM_RIGHT_DIR:     {env['TFM_RIGHT_DIR']}")
            print(f"TFM_THIS_DIR:      {env['TFM_THIS_DIR']}")
            print(f"TFM_OTHER_DIR:     {env['TFM_OTHER_DIR']}")
            print(f"TFM_LEFT_SELECTED: {env['TFM_LEFT_SELECTED']}")
            print(f"TFM_RIGHT_SELECTED: {env['TFM_RIGHT_SELECTED']}")
            print(f"TFM_THIS_SELECTED: {env['TFM_THIS_SELECTED']}")
            print(f"TFM_OTHER_SELECTED: {env['TFM_OTHER_SELECTED']}")
            print("=" * 50)
            print("TFM_ACTIVE environment variable is set for shell customization")
            print("To show [TFM] in your prompt, add this to your shell config:")
            print("  Zsh (~/.zshrc): if [[ -n \"$TFM_ACTIVE\" ]]; then PROMPT=\"[TFM] $PROMPT\"; fi")
            print("  Bash (~/.bashrc): if [[ -n \"$TFM_ACTIVE\" ]]; then PS1=\"[TFM] $PS1\"; fi")
            print("Type 'exit' to return to TFM")
            print()
            
            # Change to the current directory
            os.chdir(current_pane['path'])
            
            # Start the shell with the modified environment
            shell = env.get('SHELL', '/bin/bash')
            subprocess.run([shell], env=env)
            
        except Exception as e:
            print(f"Error starting sub-shell: {e}")
            input("Press Enter to continue...")
        
        finally:
            # Reinitialize curses
            self.stdscr = curses.initscr()
            curses.curs_set(0)  # Hide cursor
            self.stdscr.keypad(True)
            
            # Reinitialize colors with configured scheme
            color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
            init_colors(color_scheme)
            
            # Restore stdout/stderr capture  
            from tfm_log_manager import LogCapture
            sys.stdout = LogCapture(self.log_manager.log_messages, "STDOUT")
            sys.stderr = LogCapture(self.log_manager.log_messages, "STDERR")
            
            # Log return from sub-shell
            print("Returned from sub-shell mode")
            
            # Force full redraw
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
                
                # Draw dialog overlays on top of the interface
                if self.list_dialog.mode:
                    self.list_dialog.draw(self.stdscr, self.safe_addstr)
                elif self.info_dialog.mode:
                    self.info_dialog.draw(self.stdscr, self.safe_addstr)
                elif self.search_dialog.mode:
                    self.search_dialog.draw(self.stdscr, self.safe_addstr)
                elif self.batch_rename_dialog.mode:
                    self.batch_rename_dialog.draw(self.stdscr, self.safe_addstr)
                
                # Refresh screen
                self.stdscr.refresh()
                self.needs_full_redraw = False
            
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
            
            # Handle filter mode input
            if self.filter_mode:
                if self.handle_filter_input(key):
                    continue  # Filter mode handled the key
            
            # Handle rename mode input
            if self.rename_mode:
                if self.handle_rename_input(key):
                    continue  # Rename mode handled the key
            
            # Handle create directory mode input
            if self.create_dir_mode:
                if self.handle_create_directory_input(key):
                    continue  # Create directory mode handled the key
            
            # Handle create file mode input
            if self.create_file_mode:
                if self.handle_create_file_input(key):
                    continue  # Create file mode handled the key
            
            # Handle create archive mode input
            if self.create_archive_mode:
                if self.handle_create_archive_input(key):
                    continue  # Create archive mode handled the key
            
            # Handle quick choice mode input
            if self.quick_choice_mode:
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
            if self.quick_choice_mode or self.info_dialog.mode or self.list_dialog.mode or self.search_dialog.mode or self.batch_rename_dialog.mode or self.isearch_mode or self.filter_mode or self.rename_mode or self.create_dir_mode or self.create_file_mode or self.create_archive_mode:
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
            elif key == curses.KEY_LEFT and self.pane_manager.active_pane == 'right':  # Left arrow in right pane - switch to left pane
                self.pane_manager.active_pane = 'left'

            elif key == 337:  # Shift+Up in many terminals
                if self.log_manager.scroll_log_up(1):
                    self.needs_full_redraw = True
            elif key == 336:  # Shift+Down in many terminals  
                if self.log_manager.scroll_log_down(1):
                    self.needs_full_redraw = True
            elif key == 393:  # Alternative Shift+Up code
                if self.log_manager.scroll_log_up(1):
                    self.needs_full_redraw = True
            elif key == 402:  # Alternative Shift+Down code
                if self.log_manager.scroll_log_down(1):
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
                # Option+Left sends 27 followed by 'b' (98)
                # Option+Right sends 27 followed by 'f' (102)
                # Option+Space sends 194 followed by 160
                next_key = self.stdscr.getch()
                if next_key == 98:  # Option+Left (ESC + 'b')
                    self.adjust_pane_boundary('left')
                elif next_key == 102:  # Option+Right (ESC + 'f')
                    self.adjust_pane_boundary('right')

                else:
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
            elif key == ord('T'):  # 'T' key - show file type filter
                self.show_file_type_filter()
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
            elif self.is_key_for_action(key, 'help'):  # Show help dialog
                self.show_help_dialog()
            elif key == ord('-'):  # '-' key - reset pane ratio to 50/50
                self.pane_manager.left_pane_ratio = 0.5
                self.needs_full_redraw = True
                print("Pane split reset to 50% | 50%")
            elif self.is_key_for_action(key, 'subshell'):  # Sub-shell mode
                self.enter_subshell_mode()
        
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