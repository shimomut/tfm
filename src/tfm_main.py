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

class LogCapture:
    """Capture stdout/stderr and redirect to log pane"""
    def __init__(self, log_messages, source):
        self.log_messages = log_messages
        self.source = source
        
    def write(self, text):
        if text.strip():  # Only log non-empty messages
            timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
            self.log_messages.append((timestamp, self.source, text.strip()))
    
    def flush(self):
        pass  # Required for file-like object interface

class FileManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        
        # Load configuration
        self.config = get_config()
        
        # Get startup paths from configuration
        left_startup_path, right_startup_path = get_startup_paths()
        
        # Dual pane setup with configuration
        self.left_pane = {
            'path': left_startup_path,
            'selected_index': 0,
            'scroll_offset': 0,
            'files': [],
            'selected_files': set(),  # Track multi-selected files
            'sort_mode': getattr(self.config, 'DEFAULT_SORT_MODE', 'name'),
            'sort_reverse': getattr(self.config, 'DEFAULT_SORT_REVERSE', False),
            'filter_pattern': "",  # Filename filter pattern for this pane
            'cursor_history': deque(maxlen=100)  # Store cursor position history (filename, directory_path)
        }
        self.right_pane = {
            'path': right_startup_path,
            'selected_index': 0,
            'scroll_offset': 0,
            'files': [],
            'selected_files': set(),  # Track multi-selected files
            'sort_mode': getattr(self.config, 'DEFAULT_SORT_MODE', 'name'),
            'sort_reverse': getattr(self.config, 'DEFAULT_SORT_REVERSE', False),
            'filter_pattern': "",  # Filename filter pattern for this pane
            'cursor_history': deque(maxlen=100)  # Store cursor position history (filename, directory_path)
        }
        
        self.active_pane = 'left'  # 'left' or 'right'
        self.show_hidden = getattr(self.config, 'SHOW_HIDDEN_FILES', False)
        
        # Pane layout - track left pane width ratio (0.1 to 0.9)
        self.left_pane_ratio = getattr(self.config, 'DEFAULT_LEFT_PANE_RATIO', 0.5)
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
        
        # Info dialog state
        self.info_dialog_mode = False
        self.info_dialog_title = ""
        self.info_dialog_lines = []
        self.info_dialog_scroll = 0
        
        # List dialog state
        self.list_dialog_mode = False
        self.list_dialog_title = ""
        self.list_dialog_items = []  # List of items to choose from
        self.list_dialog_filtered_items = []  # Filtered items based on search
        self.list_dialog_selected = 0  # Index of currently selected item in filtered list
        self.list_dialog_scroll = 0  # Scroll offset for the list
        self.list_dialog_search_editor = SingleLineTextEdit()  # Search editor for list dialog
        self.list_dialog_callback = None  # Callback function when item is selected
        
        # Search dialog state
        self.search_dialog_mode = False
        self.search_dialog_type = 'filename'  # 'filename' or 'content'
        self.search_dialog_pattern_editor = SingleLineTextEdit()  # Pattern editor for search dialog
        self.search_dialog_results = []  # List of search results
        self.search_dialog_selected = 0  # Index of currently selected result
        self.search_dialog_scroll = 0  # Scroll offset for results
        self.search_dialog_searching = False  # Whether search is in progress
        
        # Batch rename dialog state
        self.batch_rename_mode = False
        # Text editors for batch rename dialog
        self.batch_rename_regex_editor = SingleLineTextEdit()
        self.batch_rename_destination_editor = SingleLineTextEdit()
        self.batch_rename_active_field = 'regex'  # 'regex' or 'destination'
        self.batch_rename_files = []  # List of selected files to rename
        self.batch_rename_preview = []  # List of preview results
        self.batch_rename_scroll = 0  # Scroll offset for preview list
        
        # Log pane setup
        max_log_messages = getattr(self.config, 'MAX_LOG_MESSAGES', MAX_LOG_MESSAGES)
        self.log_messages = deque(maxlen=max_log_messages)
        self.log_scroll_offset = 0
        
        # Redirect stdout and stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = LogCapture(self.log_messages, "STDOUT")
        sys.stderr = LogCapture(self.log_messages, "STDERR")
        
        # Add startup messages to log
        self.add_startup_messages()
        
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
        
    def add_startup_messages(self):
        """Add startup messages directly to log pane"""
        timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
        self.log_messages.append((timestamp, "SYSTEM", f"TFM {VERSION}"))
        self.log_messages.append((timestamp, "SYSTEM", f"GitHub: {GITHUB_URL}"))
        self.log_messages.append((timestamp, "SYSTEM", f"{APP_NAME} started successfully"))
        
        # Add configuration info
        config_file = getattr(self.config, '__module__', 'built-in defaults')
        if hasattr(self.config, '__file__'):
            config_file = self.config.__file__
        self.log_messages.append((timestamp, "CONFIG", f"Configuration loaded"))
    
    def is_key_for_action(self, key, action):
        """Check if a key matches a configured action"""
        if 32 <= key <= 126:  # Printable ASCII
            key_char = chr(key)
            return is_key_bound_to(key_char, action)
        return False
        
    def count_files_and_dirs(self, pane_data):
        """Count directories and files in a pane"""
        if not pane_data['files']:
            return 0, 0
            
        files = pane_data['files']
        # No need to skip parent directory since it's no longer added
        
        dir_count = 0
        file_count = 0
        
        for file_path in files:
            if file_path.is_dir():
                dir_count += 1
            else:
                file_count += 1
                
        return dir_count, file_count
        
    def draw_file_footers(self, y, left_pane_width):
        """Draw footer bars for left and right file panes"""
        # Left pane footer
        left_dirs, left_files = self.count_files_and_dirs(self.left_pane)
        left_selected = len(self.left_pane['selected_files'])
        left_sort = self.get_sort_description(self.left_pane)
        
        # Add filter info to footer if active
        left_filter_info = ""
        if self.left_pane['filter_pattern']:
            left_filter_info = f" | Filter: {self.left_pane['filter_pattern']}"
        
        if left_selected > 0:
            left_footer = f" {left_dirs} dirs, {left_files} files ({left_selected} selected) | Sort: {left_sort}{left_filter_info} "
        else:
            left_footer = f" {left_dirs} dirs, {left_files} files | Sort: {left_sort}{left_filter_info} "
        
        try:
            # Left pane footer with active indicator
            left_color = get_footer_color(self.active_pane == 'left')
            self.stdscr.addstr(y, 2, left_footer, left_color)
        except curses.error:
            pass
            
        # Right pane footer  
        right_dirs, right_files = self.count_files_and_dirs(self.right_pane)
        right_selected = len(self.right_pane['selected_files'])
        right_sort = self.get_sort_description(self.right_pane)
        
        # Add filter info to footer if active
        right_filter_info = ""
        if self.right_pane['filter_pattern']:
            right_filter_info = f" | Filter: {self.right_pane['filter_pattern']}"
        
        if right_selected > 0:
            right_footer = f" {right_dirs} dirs, {right_files} files ({right_selected} selected) | Sort: {right_sort}{right_filter_info} "
        else:
            right_footer = f" {right_dirs} dirs, {right_files} files | Sort: {right_sort}{right_filter_info} "
        
        try:
            # Right pane footer with active indicator
            right_color = get_footer_color(self.active_pane == 'right')
            self.stdscr.addstr(y, left_pane_width + 2, right_footer, right_color)
        except curses.error:
            pass
            
    def toggle_selection(self):
        """Toggle selection of current file/directory and move to next item"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Parent directory (..) is no longer shown, so no need to check for it
        file_path_str = str(selected_file)
        
        if file_path_str in current_pane['selected_files']:
            current_pane['selected_files'].remove(file_path_str)
            print(f"Deselected: {selected_file.name}")
        else:
            current_pane['selected_files'].add(file_path_str)
            print(f"Selected: {selected_file.name}")
        
        print(f"Total selected: {len(current_pane['selected_files'])}")
        
        # Move cursor to next item after selection
        if current_pane['selected_index'] < len(current_pane['files']) - 1:
            current_pane['selected_index'] += 1
            
    def toggle_selection_up(self):
        """Toggle selection of current file/directory and move to previous item"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Parent directory (..) is no longer shown, so no need to check for it
        file_path_str = str(selected_file)
        
        if file_path_str in current_pane['selected_files']:
            current_pane['selected_files'].remove(file_path_str)
            print(f"Deselected: {selected_file.name}")
        else:
            current_pane['selected_files'].add(file_path_str)
            print(f"Selected: {selected_file.name}")
        
        print(f"Total selected: {len(current_pane['selected_files'])}")
        
        # Move cursor to previous item after selection
        if current_pane['selected_index'] > 0:
            current_pane['selected_index'] -= 1
    
    def toggle_all_files_selection(self):
        """Toggle selection status of all files (not directories) in current pane"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
        
        # Get all files (not directories) in current pane
        files_only = []
        for file_path in current_pane['files']:
            # Skip directories (parent directory no longer shown)
            if file_path.is_dir():
                continue
            files_only.append(file_path)
        
        if not files_only:
            print("No files to select in current directory")
            return
        
        # Check if all files are currently selected
        files_only_str = {str(f) for f in files_only}
        currently_selected_files = current_pane['selected_files'] & files_only_str
        
        if len(currently_selected_files) == len(files_only):
            # All files are selected, deselect them all
            current_pane['selected_files'] -= files_only_str
            print(f"Deselected all {len(files_only)} files")
        else:
            # Not all files are selected, select them all
            current_pane['selected_files'].update(files_only_str)
            print(f"Selected all {len(files_only)} files")
        
        print(f"Total selected: {len(current_pane['selected_files'])}")
        self.needs_full_redraw = True
    
    def toggle_all_items_selection(self):
        """Toggle selection status of all items (files and directories) in current pane"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            return
        
        # Get all items (parent directory no longer shown)
        all_items = []
        for file_path in current_pane['files']:
            all_items.append(file_path)
        
        if not all_items:
            print("No items to select in current directory")
            return
        
        # Check if all items are currently selected
        all_items_str = {str(f) for f in all_items}
        currently_selected_items = current_pane['selected_files'] & all_items_str
        
        if len(currently_selected_items) == len(all_items):
            # All items are selected, deselect them all
            current_pane['selected_files'] -= all_items_str
            print(f"Deselected all {len(all_items)} items")
        else:
            # Not all items are selected, select them all
            current_pane['selected_files'].update(all_items_str)
            print(f"Selected all {len(all_items)} items")
        
        print(f"Total selected: {len(current_pane['selected_files'])}")
        self.needs_full_redraw = True
    
    def sync_pane_directories(self):
        """Change current pane's directory to match the other pane's directory, or sync cursor if already same directory"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Check if both panes are already showing the same directory
        if current_pane['path'] == other_pane['path']:
            # Both panes show same directory, sync cursor position instead
            # For 'o', move cursor in CURRENT pane to match other pane's cursor
            self.sync_cursor_to_other_pane()
            return
        
        # Get the other pane's directory
        target_directory = other_pane['path']
        
        # Check if target directory exists and is accessible
        if not target_directory.exists():
            print(f"Target directory does not exist: {target_directory}")
            return
            
        if not target_directory.is_dir():
            print(f"Target is not a directory: {target_directory}")
            return
            
        try:
            # Test if we can access the directory
            list(target_directory.iterdir())
        except PermissionError:
            print(f"Permission denied accessing: {target_directory}")
            return
        except Exception as e:
            print(f"Error accessing directory: {e}")
            return
        
        # Save current cursor position before changing directory
        self.save_cursor_position(current_pane)
        
        # Change current pane to the other pane's directory
        old_directory = current_pane['path']
        current_pane['path'] = target_directory
        current_pane['selected_index'] = 0
        current_pane['scroll_offset'] = 0
        current_pane['selected_files'].clear()  # Clear selections when changing directory
        self.refresh_files(current_pane)
        
        # Try to restore cursor position for this directory
        if not self.restore_cursor_position(current_pane):
            # If no history found, default to first item
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
        
        # Log the change
        pane_name = "left" if self.active_pane == 'left' else "right"
        print(f"Synchronized {pane_name} pane: {old_directory} → {target_directory}")
        
        self.needs_full_redraw = True
    
    def sync_other_pane_directory(self):
        """Change other pane's directory to match the current pane's directory, or sync cursor if already same directory"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Check if both panes are already showing the same directory
        if current_pane['path'] == other_pane['path']:
            # Both panes show same directory, sync cursor position instead
            # For Shift-O, move cursor in OTHER pane to match current pane's cursor
            self.sync_cursor_from_current_pane()
            return
        
        # Get the current pane's directory
        target_directory = current_pane['path']
        
        # Check if target directory exists and is accessible
        if not target_directory.exists():
            print(f"Current directory does not exist: {target_directory}")
            return
            
        if not target_directory.is_dir():
            print(f"Current path is not a directory: {target_directory}")
            return
            
        try:
            # Test if we can access the directory
            list(target_directory.iterdir())
        except PermissionError:
            print(f"Permission denied accessing: {target_directory}")
            return
        except Exception as e:
            print(f"Error accessing directory: {e}")
            return
        
        # Save current cursor position in other pane before changing directory
        self.save_cursor_position(other_pane)
        
        # Change other pane to the current pane's directory
        old_directory = other_pane['path']
        other_pane['path'] = target_directory
        other_pane['selected_index'] = 0
        other_pane['scroll_offset'] = 0
        other_pane['selected_files'].clear()  # Clear selections when changing directory
        self.refresh_files(other_pane)
        
        # Try to restore cursor position for this directory
        if not self.restore_cursor_position(other_pane):
            # If no history found, default to first item
            other_pane['selected_index'] = 0
            other_pane['scroll_offset'] = 0
        
        # Log the change
        other_pane_name = "right" if self.active_pane == 'left' else "left"
        current_pane_name = "left" if self.active_pane == 'left' else "right"
        print(f"Synchronized {other_pane_name} pane to {current_pane_name} pane: {old_directory} → {target_directory}")
        
        self.needs_full_redraw = True
    
    def sync_cursor_to_other_pane(self):
        """Move cursor in current pane to the same filename as the other pane's cursor"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Get the currently selected file in the other pane
        if not other_pane['files'] or other_pane['selected_index'] >= len(other_pane['files']):
            print("No file selected in other pane")
            return
            
        other_selected_file = other_pane['files'][other_pane['selected_index']]
        
        # Parent directory (..) is no longer shown
        target_filename = other_selected_file.name
        
        # Find the same filename in current pane
        target_index = None
        for i, file_path in enumerate(current_pane['files']):
            if file_path.name == target_filename:
                target_index = i
                break
        
        if target_index is not None:
            # Move cursor to the matching file
            current_pane['selected_index'] = target_index
            
            # Adjust scroll offset if needed to keep selection visible
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 4  # Reserve space for header, log pane, and status
            
            if current_pane['selected_index'] < current_pane['scroll_offset']:
                current_pane['scroll_offset'] = current_pane['selected_index']
            elif current_pane['selected_index'] >= current_pane['scroll_offset'] + display_height:
                current_pane['scroll_offset'] = current_pane['selected_index'] - display_height + 1
            
            pane_name = "left" if self.active_pane == 'left' else "right"
            print(f"Moved {pane_name} pane cursor to: {target_filename}")
            self.needs_full_redraw = True
        else:
            print(f"File '{target_filename}' not found in current pane")
    
    def sync_cursor_from_current_pane(self):
        """Move cursor in other pane to the same filename as the current pane's cursor"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Get the currently selected file in the current pane
        if not current_pane['files'] or current_pane['selected_index'] >= len(current_pane['files']):
            print("No file selected in current pane")
            return
            
        current_selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Parent directory (..) is no longer shown
        target_filename = current_selected_file.name
        
        # Find the same filename in other pane
        target_index = None
        for i, file_path in enumerate(other_pane['files']):
            if file_path.name == target_filename:
                target_index = i
                break
        
        if target_index is not None:
            # Move cursor to the matching file in other pane
            other_pane['selected_index'] = target_index
            
            # Adjust scroll offset if needed to keep selection visible
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 4  # Reserve space for header, log pane, and status
            
            if other_pane['selected_index'] < other_pane['scroll_offset']:
                other_pane['scroll_offset'] = other_pane['selected_index']
            elif other_pane['selected_index'] >= other_pane['scroll_offset'] + display_height:
                other_pane['scroll_offset'] = other_pane['selected_index'] - display_height + 1
            
            other_pane_name = "right" if self.active_pane == 'left' else "left"
            print(f"Moved {other_pane_name} pane cursor to: {target_filename}")
            self.needs_full_redraw = True
        else:
            other_pane_name = "right" if self.active_pane == 'left' else "left"
            print(f"File '{target_filename}' not found in {other_pane_name} pane")
        
    def restore_stdio(self):
        """Restore stdout/stderr to original state"""
        if hasattr(self, 'original_stdout') and sys.stdout != self.original_stdout:
            sys.stdout = self.original_stdout
        if hasattr(self, 'original_stderr') and sys.stderr != self.original_stderr:
            sys.stderr = self.original_stderr
            
    def __del__(self):
        """Restore stdout/stderr when object is destroyed"""
        self.restore_stdio()
        
    def get_current_pane(self):
        """Get the currently active pane"""
        return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    def get_inactive_pane(self):
        """Get the inactive pane"""
        return self.right_pane if self.active_pane == 'left' else self.left_pane
    
    def save_cursor_position(self, pane_data):
        """Save current cursor position to history"""
        if not pane_data['files'] or pane_data['selected_index'] >= len(pane_data['files']):
            return
            
        current_file = pane_data['files'][pane_data['selected_index']]
        current_dir = pane_data['path']
        
        # Save as (filename, directory_path) tuple
        cursor_entry = (current_file.name, str(current_dir))
        
        # Remove any existing entry for this directory to avoid duplicates
        pane_data['cursor_history'] = deque(
            [entry for entry in pane_data['cursor_history'] if entry[1] != str(current_dir)],
            maxlen=100
        )
        
        # Add the new entry
        pane_data['cursor_history'].append(cursor_entry)
    
    def restore_cursor_position(self, pane_data):
        """Restore cursor position from history when changing to a directory"""
        current_dir = str(pane_data['path'])
        
        # Look for a saved cursor position for this directory
        for filename, saved_dir in reversed(pane_data['cursor_history']):
            if saved_dir == current_dir:
                # Try to find this filename in current files
                for i, file_path in enumerate(pane_data['files']):
                    if file_path.name == filename:
                        pane_data['selected_index'] = i
                        
                        # Adjust scroll offset to keep selection visible
                        height, width = self.stdscr.getmaxyx()
                        calculated_height = int(height * self.log_height_ratio)
                        log_height = calculated_height if self.log_height_ratio > 0 else 0
                        display_height = height - log_height - 4
                        
                        if pane_data['selected_index'] < pane_data['scroll_offset']:
                            pane_data['scroll_offset'] = pane_data['selected_index']
                        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
                            pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
                        
                        return True
        
        return False
    
    def get_log_scroll_percentage(self):
        """Calculate the current log scroll position as a percentage"""
        if len(self.log_messages) <= 1:
            return 100  # If no messages or only one, we're at 100%
        
        # When scroll_offset is 0, we're at the bottom (newest messages) = 100%
        # When scroll_offset is max, we're at the top (oldest messages) = 0%
        max_scroll = len(self.log_messages) - 1
        if max_scroll == 0:
            return 100
        
        # Invert the percentage since offset 0 = bottom (100%) and max offset = top (0%)
        percentage = int(((max_scroll - self.log_scroll_offset) / max_scroll) * 100)
        return max(0, min(100, percentage))
    
    def refresh_files(self, pane=None):
        """Refresh the file list for specified pane or both panes"""
        panes_to_refresh = [pane] if pane else [self.left_pane, self.right_pane]
        
        for pane_data in panes_to_refresh:
            try:
                entries = list(pane_data['path'].iterdir())
                if not self.show_hidden:
                    entries = [e for e in entries if not e.name.startswith('.')]
                
                # Apply filename filter if set for this pane (only to files, not directories)
                if pane_data['filter_pattern']:
                    filtered_entries = []
                    for entry in entries:
                        # Always include directories, only filter files
                        if entry.is_dir() or fnmatch.fnmatch(entry.name, pane_data['filter_pattern']):
                            filtered_entries.append(entry)
                    entries = filtered_entries
                
                # Sort files using the pane's sort mode
                pane_data['files'] = self.sort_entries(entries, pane_data['sort_mode'], pane_data['sort_reverse'])
                
                # Parent directory (..) suppressed per user request
                # if pane_data['path'] != pane_data['path'].parent:
                #     pane_data['files'].insert(0, pane_data['path'].parent)
                    
            except PermissionError:
                pane_data['files'] = []
                
            # Reset selection if out of bounds
            if pane_data['selected_index'] >= len(pane_data['files']):
                pane_data['selected_index'] = max(0, len(pane_data['files']) - 1)
                
            # Don't clear selected files here - only clear when directory actually changes
    
    def sort_entries(self, entries, sort_mode, reverse=False):
        """Sort file entries based on the specified mode
        
        Args:
            entries: List of Path objects to sort
            sort_mode: 'name', 'size', or 'date'
            reverse: Whether to reverse the sort order
            
        Returns:
            Sorted list with directories always first
        """
        def get_sort_key(entry):
            """Generate sort key for an entry"""
            try:
                if sort_mode == 'name':
                    # Sort by name (case-insensitive)
                    return entry.name.lower()
                elif sort_mode == 'size':
                    # Sort by file size (directories get size 0)
                    if entry.is_dir():
                        return 0
                    else:
                        return entry.stat().st_size
                elif sort_mode == 'date':
                    # Sort by modification time
                    return entry.stat().st_mtime
                else:
                    # Default to name sorting
                    return entry.name.lower()
            except (OSError, PermissionError):
                # If we can't get file info, sort by name as fallback
                return entry.name.lower()
        
        # Separate directories and files
        directories = [e for e in entries if e.is_dir()]
        files = [e for e in entries if not e.is_dir()]
        
        # Sort directories and files separately
        sorted_dirs = sorted(directories, key=get_sort_key, reverse=reverse)
        sorted_files = sorted(files, key=get_sort_key, reverse=reverse)
        
        # Always put directories first, then files
        return sorted_dirs + sorted_files
    
    def get_sort_description(self, pane_data):
        """Get a human-readable description of the current sort mode"""
        mode = pane_data['sort_mode']
        reverse = pane_data['sort_reverse']
        
        mode_names = {
            'name': 'Name',
            'size': 'Size', 
            'date': 'Date'
        }
        
        description = mode_names.get(mode, 'Name')
        if reverse:
            description += ' ↓'
        else:
            description += ' ↑'
            
        return description
            
    def get_file_info(self, path):
        """Get file information for display"""
        try:
            stat_info = path.stat()
            size = stat_info.st_size
            mtime = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Format size using constants
            if size < SIZE_KB:
                size_str = f"{size}B"
            elif size < SIZE_MB:
                size_str = f"{size/SIZE_KB:.1f}K"
            elif size < SIZE_GB:
                size_str = f"{size/SIZE_MB:.1f}M"
            else:
                size_str = f"{size/SIZE_GB:.1f}G"
                
            return size_str, mtime.strftime(DATETIME_FORMAT)
        except (OSError, PermissionError):
            return "---", "---"
            
    def draw_header(self):
        """Draw the header with pane paths and controls"""
        height, width = self.stdscr.getmaxyx()
        left_pane_width = int(width * self.left_pane_ratio)
        right_pane_width = width - left_pane_width
        
        # Clear header area (avoid last column)
        try:
            self.stdscr.addstr(0, 0, " " * (width - 1), get_header_color())
        except curses.error:
            pass
        
        # Left pane path with safety checks
        if left_pane_width > 6:  # Minimum space needed
            left_path = str(self.left_pane['path'])
            max_left_path_width = max(1, left_pane_width - 4)
            if len(left_path) > max_left_path_width:
                left_path = "..." + left_path[-(max(1, max_left_path_width-3)):]
            
            left_color = get_header_color(self.active_pane == 'left')
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
            right_path = str(self.right_pane['path'])
            max_right_path_width = max(1, right_pane_width - 4)
            if len(right_path) > max_right_path_width:
                right_path = "..." + right_path[-(max(1, max_right_path_width-3)):]
                
            right_color = get_header_color(self.active_pane == 'right')
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
        left_pane_width = int(width * self.left_pane_ratio)
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
        self.draw_pane(self.left_pane, 0, left_pane_width, self.active_pane == 'left')
        
        # Draw right pane
        self.draw_pane(self.right_pane, left_pane_width, right_pane_width, self.active_pane == 'right')
        
    def draw_log_pane(self):
        """Draw the log pane at the bottom"""
        height, width = self.stdscr.getmaxyx()
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        left_pane_width = int(width * self.left_pane_ratio)
        
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
        
        # Calculate visible log messages (subtract 1 for the footer line)
        visible_lines = log_height - 1
        total_messages = len(self.log_messages)
        
        if total_messages == 0:
            try:
                self.stdscr.addstr(log_start_y, 2, "No log messages", curses.A_DIM)
            except curses.error:
                pass
            return
        
        # Auto-scroll to bottom if not manually scrolled
        if self.log_scroll_offset == 0:
            start_idx = max(0, total_messages - visible_lines)
        else:
            start_idx = max(0, total_messages - visible_lines - self.log_scroll_offset)
        
        # Draw log messages
        for i in range(visible_lines):
            msg_idx = start_idx + i
            y = log_start_y + i
            
            if msg_idx >= total_messages:
                break
                
            timestamp, source, message = self.log_messages[msg_idx]
            
            # Choose color based on source
            color = get_log_color(source)
            
            # Format log line
            log_line = f"{timestamp} [{source}] {message}"
            if len(log_line) > width - 2:
                log_line = log_line[:width-5] + "..."
                
            try:
                self.stdscr.addstr(y, 2, log_line, color)
            except curses.error:
                pass
                
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
        
        # If in info dialog mode, show info dialog
        if self.info_dialog_mode:
            self.draw_info_dialog()
            return
            
        # If in list dialog mode, show list dialog
        if self.list_dialog_mode:
            self.draw_list_dialog()
            return
            
        # If in search dialog mode, show search dialog
        if self.search_dialog_mode:
            self.draw_search_dialog()
            return
        
        # If in batch rename mode, show batch rename dialog
        if self.batch_rename_mode:
            self.draw_batch_rename_dialog()
            return
            
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
        if self.show_hidden:
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
        pane_name = "left" if self.active_pane == 'left' else "right"
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
        pane_name = "left" if self.active_pane == 'left' else "right"
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
        
        # Get list of selected files (only files, not directories for safety)
        selected_files = []
        for file_path_str in current_pane['selected_files']:
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.is_file():
                selected_files.append(file_path)
        
        if not selected_files:
            print("No files selected for batch rename")
            return
        
        self.batch_rename_mode = True
        self.batch_rename_files = selected_files
        self.batch_rename_regex_editor.clear()
        self.batch_rename_destination_editor.clear()
        self.batch_rename_active_field = 'regex'
        self.batch_rename_preview = []
        self.batch_rename_scroll = 0
        
        self.needs_full_redraw = True
        print(f"Batch rename mode: {len(selected_files)} files selected")
    
    def exit_batch_rename_mode(self):
        """Exit batch rename mode"""
        self.batch_rename_mode = False
        self.batch_rename_files = []
        self.batch_rename_regex_editor.clear()
        self.batch_rename_destination_editor.clear()
        self.batch_rename_active_field = 'regex'
        self.batch_rename_preview = []
        self.batch_rename_scroll = 0
        self.needs_full_redraw = True
    
    def update_batch_rename_preview(self):
        """Update the preview list for batch rename"""
        import re
        
        self.batch_rename_preview = []
        
        regex_pattern = self.batch_rename_regex_editor.get_text()
        destination_pattern = self.batch_rename_destination_editor.get_text()
        
        if not regex_pattern or not destination_pattern:
            return
        
        try:
            pattern = re.compile(regex_pattern)
        except re.error as e:
            # Invalid regex pattern
            return
        
        for i, file_path in enumerate(self.batch_rename_files):
            original_name = file_path.name
            match = pattern.search(original_name)
            
            if match:
                # Apply destination pattern with substitutions
                new_name = destination_pattern
                
                # Replace \0 with entire original filename
                new_name = new_name.replace('\\0', original_name)
                
                # Replace \1-\9 with regex groups
                for j in range(1, 10):
                    group_placeholder = f'\\{j}'
                    if group_placeholder in new_name:
                        try:
                            group_value = match.group(j) if j <= len(match.groups()) else ''
                            new_name = new_name.replace(group_placeholder, group_value)
                        except IndexError:
                            new_name = new_name.replace(group_placeholder, '')
                
                # Replace \d with index number
                new_name = new_name.replace('\\d', str(i + 1))
                
                # Check for conflicts
                new_path = file_path.parent / new_name
                conflict = new_path.exists() and new_path != file_path
                
                self.batch_rename_preview.append({
                    'original': original_name,
                    'new': new_name,
                    'conflict': conflict,
                    'valid': bool(new_name.strip() and '/' not in new_name and '\0' not in new_name)
                })
            else:
                # No match - keep original name
                self.batch_rename_preview.append({
                    'original': original_name,
                    'new': original_name,
                    'conflict': False,
                    'valid': True
                })
    
    def perform_batch_rename(self):
        """Perform the batch rename operation"""
        if not self.batch_rename_preview:
            print("No rename preview available")
            return
        
        # Check for conflicts and invalid names
        conflicts = [p for p in self.batch_rename_preview if p['conflict']]
        invalid = [p for p in self.batch_rename_preview if not p['valid']]
        
        if conflicts:
            conflict_names = [p['new'] for p in conflicts]
            print(f"Cannot rename: conflicts with existing files: {', '.join(conflict_names)}")
            return
        
        if invalid:
            invalid_names = [p['new'] for p in invalid]
            print(f"Cannot rename: invalid filenames: {', '.join(invalid_names)}")
            return
        
        # Perform renames
        renamed_count = 0
        errors = []
        
        for i, preview in enumerate(self.batch_rename_preview):
            if preview['original'] != preview['new']:
                try:
                    old_path = self.batch_rename_files[i]
                    new_path = old_path.parent / preview['new']
                    old_path.rename(new_path)
                    renamed_count += 1
                except Exception as e:
                    errors.append(f"{preview['original']}: {e}")
        
        # Report results
        if renamed_count > 0:
            print(f"Successfully renamed {renamed_count} files")
        
        if errors:
            print(f"Errors: {'; '.join(errors)}")
        
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
        """Show an information dialog with scrollable content"""
        self.info_dialog_mode = True
        self.info_dialog_title = title
        self.info_dialog_lines = info_lines
        self.info_dialog_scroll = 0
        self.needs_full_redraw = True
    
    def show_list_dialog(self, title, items, callback):
        """Show a searchable list dialog
        
        Args:
            title: The title to display at the top of the dialog
            items: List of items to choose from (strings or objects with __str__ method)
            callback: Function to call with the selected item (or None if cancelled)
        """
        self.list_dialog_mode = True
        self.list_dialog_title = title
        self.list_dialog_items = items
        self.list_dialog_filtered_items = items.copy()  # Initially show all items
        self.list_dialog_selected = 0
        self.list_dialog_scroll = 0
        self.list_dialog_search_editor.clear()
        self.list_dialog_callback = callback
        self.needs_full_redraw = True
    
    def exit_info_dialog_mode(self):
        """Exit info dialog mode"""
        self.info_dialog_mode = False
        self.info_dialog_title = ""
        self.info_dialog_lines = []
        self.info_dialog_scroll = 0
        self.needs_full_redraw = True
    
    def exit_list_dialog_mode(self):
        """Exit list dialog mode"""
        self.list_dialog_mode = False
        self.list_dialog_title = ""
        self.list_dialog_items = []
        self.list_dialog_filtered_items = []
        self.list_dialog_selected = 0
        self.list_dialog_scroll = 0
        self.list_dialog_search_editor.clear()
        self.list_dialog_callback = None
        self.needs_full_redraw = True
    
    def handle_info_dialog_input(self, key):
        """Handle input while in info dialog mode"""
        if key == 27 or key == ord('q') or key == ord('Q'):  # ESC or Q - close
            self.exit_info_dialog_mode()
            return True
        elif key == curses.KEY_UP:
            # Scroll up
            if self.info_dialog_scroll > 0:
                self.info_dialog_scroll -= 1
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_DOWN:
            # Scroll down
            max_scroll = max(0, len(self.info_dialog_lines) - 10)  # Assuming 10 visible lines
            if self.info_dialog_scroll < max_scroll:
                self.info_dialog_scroll += 1
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            self.info_dialog_scroll = max(0, self.info_dialog_scroll - 10)
            self.needs_full_redraw = True
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            max_scroll = max(0, len(self.info_dialog_lines) - 10)
            self.info_dialog_scroll = min(max_scroll, self.info_dialog_scroll + 10)
            self.needs_full_redraw = True
            return True
        elif key == curses.KEY_HOME:  # Home - go to top
            self.info_dialog_scroll = 0
            self.needs_full_redraw = True
            return True
        elif key == curses.KEY_END:  # End - go to bottom
            max_scroll = max(0, len(self.info_dialog_lines) - 10)
            self.info_dialog_scroll = max_scroll
            self.needs_full_redraw = True
            return True
        return False
    
    def handle_list_dialog_input(self, key):
        """Handle input while in list dialog mode"""
        if key == 27:  # ESC - cancel
            if self.list_dialog_callback:
                self.list_dialog_callback(None)
            self.exit_list_dialog_mode()
            return True
        elif key == curses.KEY_UP:
            # Move selection up
            if self.list_dialog_filtered_items and self.list_dialog_selected > 0:
                self.list_dialog_selected -= 1
                self._adjust_list_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_DOWN:
            # Move selection down
            if self.list_dialog_filtered_items and self.list_dialog_selected < len(self.list_dialog_filtered_items) - 1:
                self.list_dialog_selected += 1
                self._adjust_list_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            if self.list_dialog_filtered_items:
                self.list_dialog_selected = max(0, self.list_dialog_selected - 10)
                self._adjust_list_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            if self.list_dialog_filtered_items:
                self.list_dialog_selected = min(len(self.list_dialog_filtered_items) - 1, self.list_dialog_selected + 10)
                self._adjust_list_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_HOME:  # Home - text cursor or list navigation
            # If there's text in search, let editor handle it for cursor movement
            if self.list_dialog_search_editor.text:
                if self.list_dialog_search_editor.handle_key(key):
                    self.needs_full_redraw = True
            else:
                # If no search text, use for list navigation
                if self.list_dialog_filtered_items:
                    self.list_dialog_selected = 0
                    self.list_dialog_scroll = 0
                    self.needs_full_redraw = True
            return True
        elif key == curses.KEY_END:  # End - text cursor or list navigation
            # If there's text in search, let editor handle it for cursor movement
            if self.list_dialog_search_editor.text:
                if self.list_dialog_search_editor.handle_key(key):
                    self.needs_full_redraw = True
            else:
                # If no search text, use for list navigation
                if self.list_dialog_filtered_items:
                    self.list_dialog_selected = len(self.list_dialog_filtered_items) - 1
                    self._adjust_list_dialog_scroll()
                    self.needs_full_redraw = True
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Select current item
            if self.list_dialog_filtered_items and 0 <= self.list_dialog_selected < len(self.list_dialog_filtered_items):
                selected_item = self.list_dialog_filtered_items[self.list_dialog_selected]
                if self.list_dialog_callback:
                    self.list_dialog_callback(selected_item)
            else:
                if self.list_dialog_callback:
                    self.list_dialog_callback(None)
            self.exit_list_dialog_mode()
            return True
        elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
            # Let the editor handle cursor movement keys
            if self.list_dialog_search_editor.handle_key(key):
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Let the editor handle backspace
            if self.list_dialog_search_editor.handle_key(key):
                self._filter_list_dialog_items()
                self.needs_full_redraw = True
            return True
        elif 32 <= key <= 126:  # Printable characters
            # Let the editor handle printable characters
            if self.list_dialog_search_editor.handle_key(key):
                self._filter_list_dialog_items()
                self.needs_full_redraw = True
            return True
        return False
    
    def _filter_list_dialog_items(self):
        """Filter list dialog items based on current search pattern"""
        search_text = self.list_dialog_search_editor.text
        if not search_text:
            self.list_dialog_filtered_items = self.list_dialog_items.copy()
        else:
            search_lower = search_text.lower()
            self.list_dialog_filtered_items = [
                item for item in self.list_dialog_items 
                if search_lower in str(item).lower()
            ]
        
        # Reset selection to top of filtered list
        self.list_dialog_selected = 0
        self.list_dialog_scroll = 0
    
    def _adjust_list_dialog_scroll(self):
        """Adjust scroll offset to keep selected item visible"""
        height, width = self.stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        width_ratio = getattr(self.config, 'LIST_DIALOG_WIDTH_RATIO', 0.6)
        height_ratio = getattr(self.config, 'LIST_DIALOG_HEIGHT_RATIO', 0.7)
        min_height = getattr(self.config, 'LIST_DIALOG_MIN_HEIGHT', 15)
        
        dialog_height = max(min_height, int(height * height_ratio))
        content_height = dialog_height - 6  # Account for title, search, borders, help
        
        if self.list_dialog_selected < self.list_dialog_scroll:
            self.list_dialog_scroll = self.list_dialog_selected
        elif self.list_dialog_selected >= self.list_dialog_scroll + content_height:
            self.list_dialog_scroll = self.list_dialog_selected - content_height + 1
    
    def draw_info_dialog(self):
        """Draw the info dialog overlay"""
        height, width = self.stdscr.getmaxyx()
        
        # Calculate dialog dimensions using configuration
        width_ratio = getattr(self.config, 'INFO_DIALOG_WIDTH_RATIO', 0.8)
        height_ratio = getattr(self.config, 'INFO_DIALOG_HEIGHT_RATIO', 0.8)
        min_width = getattr(self.config, 'INFO_DIALOG_MIN_WIDTH', 20)
        min_height = getattr(self.config, 'INFO_DIALOG_MIN_HEIGHT', 10)
        
        dialog_width = max(min_width, int(width * width_ratio))
        dialog_height = max(min_height, int(height * height_ratio))
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                self.safe_addstr(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            self.safe_addstr(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                self.safe_addstr(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    self.safe_addstr(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            self.safe_addstr(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        if self.info_dialog_title and start_y >= 0:
            title_text = f" {self.info_dialog_title} "
            title_x = start_x + (dialog_width - len(title_text)) // 2
            if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
                self.safe_addstr(start_y, title_x, title_text, border_color)
        
        # Calculate content area
        content_start_y = start_y + 2
        content_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = content_end_y - content_start_y + 1
        
        # Draw content lines
        visible_lines = self.info_dialog_lines[self.info_dialog_scroll:self.info_dialog_scroll + content_height]
        
        for i, line in enumerate(visible_lines):
            y = content_start_y + i
            if y <= content_end_y and y < height:
                # Truncate line if too long
                display_line = line[:content_width] if len(line) > content_width else line
                self.safe_addstr(y, content_start_x, display_line, get_status_color())
        
        # Draw scroll indicators
        if len(self.info_dialog_lines) > content_height:
            # Show scroll position
            total_lines = len(self.info_dialog_lines)
            scroll_pos = self.info_dialog_scroll
            
            # Scroll bar on the right side
            scrollbar_x = start_x + dialog_width - 2
            scrollbar_start_y = content_start_y
            scrollbar_height = content_height
            
            # Calculate scroll thumb position
            if total_lines > 0:
                thumb_pos = int((scroll_pos / max(1, total_lines - content_height)) * (scrollbar_height - 1))
                thumb_pos = max(0, min(scrollbar_height - 1, thumb_pos))
                
                for i in range(scrollbar_height):
                    y = scrollbar_start_y + i
                    if y < height:
                        if i == thumb_pos:
                            self.safe_addstr(y, scrollbar_x, "█", border_color)
                        else:
                            self.safe_addstr(y, scrollbar_x, "░", get_status_color() | curses.A_DIM)
        
        # Draw help text at bottom
        help_text = "↑↓:scroll  PgUp/PgDn:page  Home/End:top/bottom  Q/ESC:close"
        help_y = start_y + dialog_height - 2
        if help_y < height and len(help_text) <= content_width:
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                self.safe_addstr(help_y, help_x, help_text, get_status_color() | curses.A_DIM)
    
    def draw_list_dialog(self):
        """Draw the searchable list dialog overlay"""
        height, width = self.stdscr.getmaxyx()
        
        # Calculate dialog dimensions using configuration
        width_ratio = getattr(self.config, 'LIST_DIALOG_WIDTH_RATIO', 0.6)
        height_ratio = getattr(self.config, 'LIST_DIALOG_HEIGHT_RATIO', 0.7)
        min_width = getattr(self.config, 'LIST_DIALOG_MIN_WIDTH', 40)
        min_height = getattr(self.config, 'LIST_DIALOG_MIN_HEIGHT', 15)
        
        dialog_width = max(min_width, int(width * width_ratio))
        dialog_height = max(min_height, int(height * height_ratio))
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                self.safe_addstr(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            self.safe_addstr(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                self.safe_addstr(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    self.safe_addstr(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            self.safe_addstr(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        if self.list_dialog_title and start_y >= 0:
            title_text = f" {self.list_dialog_title} "
            title_x = start_x + (dialog_width - len(title_text)) // 2
            if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
                self.safe_addstr(start_y, title_x, title_text, border_color)
        
        # Draw search box
        search_y = start_y + 2
        # Draw search input using SingleLineTextEdit
        if search_y < height:
            max_search_width = dialog_width - 4  # Leave some margin
            self.list_dialog_search_editor.draw(
                self.stdscr, search_y, start_x + 2, max_search_width,
                "Search: ",
                is_active=True
            )
        
        # Draw separator line
        sep_y = start_y + 3
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            self.safe_addstr(sep_y, start_x, sep_line[:dialog_width], border_color)
        
        # Calculate list area
        list_start_y = start_y + 4
        list_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = list_end_y - list_start_y + 1
        
        # Draw list items
        visible_items = self.list_dialog_filtered_items[self.list_dialog_scroll:self.list_dialog_scroll + content_height]
        
        for i, item in enumerate(visible_items):
            y = list_start_y + i
            if y <= list_end_y and y < height:
                item_index = self.list_dialog_scroll + i
                is_selected = item_index == self.list_dialog_selected
                
                # Format item text
                item_text = str(item)
                if len(item_text) > content_width - 2:
                    item_text = item_text[:content_width - 5] + "..."
                
                # Add selection indicator
                if is_selected:
                    display_text = f"► {item_text}"
                    item_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                else:
                    display_text = f"  {item_text}"
                    item_color = get_status_color()
                
                # Ensure text fits
                display_text = display_text[:content_width]
                self.safe_addstr(y, content_start_x, display_text, item_color)
        
        # Draw scroll indicators if needed
        if len(self.list_dialog_filtered_items) > content_height:
            scrollbar_x = start_x + dialog_width - 2
            scrollbar_start_y = list_start_y
            scrollbar_height = content_height
            
            # Calculate scroll thumb position
            total_items = len(self.list_dialog_filtered_items)
            if total_items > 0:
                thumb_pos = int((self.list_dialog_scroll / max(1, total_items - content_height)) * (scrollbar_height - 1))
                thumb_pos = max(0, min(scrollbar_height - 1, thumb_pos))
                
                for i in range(scrollbar_height):
                    y = scrollbar_start_y + i
                    if y < height:
                        if i == thumb_pos:
                            self.safe_addstr(y, scrollbar_x, "█", border_color)
                        else:
                            self.safe_addstr(y, scrollbar_x, "░", get_status_color() | curses.A_DIM)
        
        # Draw status info
        status_y = start_y + dialog_height - 2
        if status_y < height:
            if self.list_dialog_filtered_items:
                status_text = f"{self.list_dialog_selected + 1}/{len(self.list_dialog_filtered_items)} items"
                if len(self.list_dialog_filtered_items) != len(self.list_dialog_items):
                    status_text += f" (filtered from {len(self.list_dialog_items)})"
            else:
                status_text = "No items found"
            
            if self.list_dialog_search_editor.text:
                status_text += f" | Filter: '{self.list_dialog_search_editor.text}'"
            
            # Center the status text
            if len(status_text) <= content_width:
                status_x = start_x + (dialog_width - len(status_text)) // 2
                self.safe_addstr(status_y, status_x, status_text, get_status_color() | curses.A_DIM)
        
        # Draw help text at bottom
        help_text = "↑↓:select  Enter:choose  Type:search  Backspace:clear  ESC:cancel"
        help_y = start_y + dialog_height - 1
        if help_y < height and len(help_text) <= content_width:
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                self.safe_addstr(help_y, help_x, help_text, get_status_color() | curses.A_DIM)
    
    def show_list_dialog_demo(self):
        """Demo function to show the searchable list dialog"""
        # Create a sample list of items
        sample_items = [
            "Apple", "Banana", "Cherry", "Date", "Elderberry", "Fig", "Grape",
            "Honeydew", "Ice cream bean", "Jackfruit", "Kiwi", "Lemon", "Mango",
            "Nectarine", "Orange", "Papaya", "Quince", "Raspberry", "Strawberry",
            "Tangerine", "Ugli fruit", "Vanilla bean", "Watermelon", "Xigua",
            "Yellow passion fruit", "Zucchini"
        ]
        
        def callback(selected_item):
            if selected_item:
                print(f"You selected: {selected_item}")
            else:
                print("Selection cancelled")
        
        self.show_list_dialog("Choose a Fruit", sample_items, callback)
    
    def show_file_type_filter(self):
        """Show file type filter using the searchable list dialog"""
        current_pane = self.get_current_pane()
        
        # Get all unique file extensions in current directory
        extensions = set()
        for file_path in current_pane['files']:
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext:
                    extensions.add(ext)
                else:
                    extensions.add("(no extension)")
        
        if not extensions:
            print("No files with extensions found in current directory")
            return
        
        # Convert to sorted list
        extension_list = sorted(list(extensions))
        extension_list.insert(0, "(show all files)")  # Add option to show all
        
        def filter_callback(selected_ext):
            if selected_ext:
                if selected_ext == "(show all files)":
                    print("Showing all files")
                    # Reset any filtering (this would need additional implementation)
                else:
                    print(f"Filtering by extension: {selected_ext}")
                    # Filter files by extension (this would need additional implementation)
            else:
                print("File type filter cancelled")
        
        self.show_list_dialog("Filter by File Type", extension_list, filter_callback)
    
    def show_favorite_directories(self):
        """Show favorite directories using the searchable list dialog"""
        favorites = get_favorite_directories()
        
        if not favorites:
            print("No favorite directories configured")
            return
        
        # Create display items with name and path
        display_items = []
        for fav in favorites:
            display_items.append(f"{fav['name']} ({fav['path']})")
        
        def favorite_callback(selected_item):
            if selected_item:
                # Extract the path from the selected item
                # Format is "Name (path)"
                try:
                    # Find the path in parentheses
                    start_paren = selected_item.rfind('(')
                    end_paren = selected_item.rfind(')')
                    if start_paren != -1 and end_paren != -1 and end_paren > start_paren:
                        selected_path = selected_item[start_paren + 1:end_paren]
                        
                        # Change current pane to selected directory
                        current_pane = self.get_current_pane()
                        target_path = Path(selected_path)
                        
                        if target_path.exists() and target_path.is_dir():
                            old_path = current_pane['path']
                            current_pane['path'] = target_path
                            current_pane['selected_index'] = 0
                            current_pane['scroll_offset'] = 0
                            current_pane['selected_files'].clear()  # Clear selections
                            
                            pane_name = "left" if self.active_pane == 'left' else "right"
                            print(f"Changed {pane_name} pane to favorite: {old_path} → {target_path}")
                            self.needs_full_redraw = True
                        else:
                            print(f"Error: Directory no longer exists: {selected_path}")
                    else:
                        print("Error: Could not parse selected favorite directory")
                except Exception as e:
                    print(f"Error changing to favorite directory: {e}")
            else:
                print("Favorite directory selection cancelled")
        
        self.show_list_dialog("Go to Favorite Directory", display_items, favorite_callback)
    
    def show_programs_dialog(self):
        """Show external programs using the searchable list dialog"""
        programs = get_programs()
        
        if not programs:
            print("No external programs configured")
            return
        
        # Create display items with program names
        display_items = []
        for prog in programs:
            display_items.append(prog['name'])
        
        def program_callback(selected_item):
            if selected_item:
                # Find the selected program
                selected_program = None
                for prog in programs:
                    if prog['name'] == selected_item:
                        selected_program = prog
                        break
                
                if selected_program:
                    self.execute_external_program(selected_program)
                else:
                    print(f"Error: Program not found: {selected_item}")
            else:
                print("Program selection cancelled")
        
        self.show_list_dialog("Execute External Program", display_items, program_callback)
    
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
            sys.stdout = LogCapture(self.log_messages, "STDOUT")
            sys.stderr = LogCapture(self.log_messages, "STDERR")
            
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
        pane_name = "left" if self.active_pane == 'left' else "right"
        message = f"Sort {pane_name} pane by:"
        self.show_dialog(message, choices, handle_sort_choice)
    
    def quick_sort(self, sort_mode):
        """Quickly change sort mode without showing dialog, or toggle reverse if already sorted by this mode"""
        current_pane = self.get_current_pane()
        pane_name = "left" if self.active_pane == 'left' else "right"
        
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
        
        # Generate details for each file
        details_lines = []
        
        for file_path in files_to_show:
            try:
                # Get file stats
                stat_info = file_path.stat()
                
                # Basic info
                details_lines.append(f"File: {file_path.name}")
                details_lines.append(f"Path: {file_path}")
                
                # Type
                if file_path.is_dir():
                    details_lines.append("Type: Directory")
                elif file_path.is_file():
                    details_lines.append("Type: File")
                elif file_path.is_symlink():
                    details_lines.append("Type: Symbolic Link")
                    try:
                        target = file_path.readlink()
                        details_lines.append(f"Target: {target}")
                    except:
                        details_lines.append("Target: <unreadable>")
                else:
                    details_lines.append("Type: Special")
                
                # Size
                if file_path.is_file():
                    size = stat_info.st_size
                    if size < 1024:
                        size_str = f"{size} bytes"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
                    details_lines.append(f"Size: {size_str}")
                elif file_path.is_dir():
                    # Count directory contents
                    try:
                        contents = list(file_path.iterdir())
                        dir_count = sum(1 for item in contents if item.is_dir())
                        file_count = sum(1 for item in contents if item.is_file())
                        details_lines.append(f"Contents: {dir_count} directories, {file_count} files")
                    except PermissionError:
                        details_lines.append("Contents: <permission denied>")
                    except:
                        details_lines.append("Contents: <error reading>")
                
                # Timestamps
                import time
                mod_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime))
                details_lines.append(f"Modified: {mod_time}")
                
                access_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_atime))
                details_lines.append(f"Accessed: {access_time}")
                
                # Permissions
                import stat
                mode = stat_info.st_mode
                perms = stat.filemode(mode)
                details_lines.append(f"Permissions: {perms}")
                
                # Owner info (Unix-like systems)
                try:
                    import pwd
                    import grp
                    owner = pwd.getpwuid(stat_info.st_uid).pw_name
                    group = grp.getgrgid(stat_info.st_gid).gr_name
                    details_lines.append(f"Owner: {owner}:{group}")
                except:
                    details_lines.append(f"Owner: UID {stat_info.st_uid}, GID {stat_info.st_gid}")
                
                # Add separator if multiple files
                if len(files_to_show) > 1:
                    details_lines.append("-" * 50)
                
            except Exception as e:
                details_lines.append(f"Error reading {file_path.name}: {str(e)}")
                if len(files_to_show) > 1:
                    details_lines.append("-" * 50)
        
        # Show the details in a dialog
        if len(files_to_show) == 1:
            title = f"Details: {files_to_show[0].name}"
        else:
            title = f"Details: {len(files_to_show)} items"
        
        self.show_info_dialog(title, details_lines)
    
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
        help_lines = []
        
        # Title and version info
        help_lines.append(f"TFM {VERSION} - Terminal File Manager")
        help_lines.append(f"GitHub: {GITHUB_URL}")
        help_lines.append("")
        
        # Navigation section
        help_lines.append("=== NAVIGATION ===")
        help_lines.append("↑↓ / j k         Navigate files")
        help_lines.append("←→ / h l         Switch panes / Navigate directories")
        help_lines.append("Tab              Switch between panes")
        help_lines.append("Enter            Open directory / View file")
        help_lines.append("Backspace        Go to parent directory")
        help_lines.append("Home / End       Go to first / last file")
        help_lines.append("Page Up/Down     Navigate by page")
        help_lines.append("")
        
        # File operations section
        help_lines.append("=== FILE OPERATIONS ===")
        help_lines.append("Space            Select/deselect file")
        help_lines.append("Ctrl+Space       Select file and move up")
        help_lines.append("a                Select all files")
        help_lines.append("A                Select all items (files + directories)")
        help_lines.append("v / V            View text file")
        help_lines.append("e                Edit existing file with text editor")
        help_lines.append("E                Create new text file and edit")
        help_lines.append("i / I            Show file details")
        help_lines.append("c / C            Copy files to other pane")
        help_lines.append("m / M            Move files to other pane / Create directory (no selection)")
        help_lines.append("k / K            Delete files")
        help_lines.append("r / R            Rename file (single) / Batch rename (multiple selected)")
        help_lines.append("p / P            Create archive from selected files")
        help_lines.append("u / U            Extract archive to other pane")
        help_lines.append("")
        
        # Search and sorting section
        help_lines.append("=== SEARCH & SORTING ===")
        help_lines.append("f / F            Search files")
        help_lines.append(";                Filter files by filename pattern")
        help_lines.append("                 (files only, directories always shown)")
        help_lines.append("                 (fnmatch: *.py, test_*, *.[ch], etc.)")
        help_lines.append(": (Shift+;)      Clear filter from current pane")
        help_lines.append("s / S            Sort menu")
        help_lines.append("1                Quick sort by name (toggle reverse if already active)")
        help_lines.append("2                Quick sort by size (toggle reverse if already active)")
        help_lines.append("3                Quick sort by date (toggle reverse if already active)")
        help_lines.append("")
        
        # View options section
        help_lines.append("=== VIEW OPTIONS ===")
        help_lines.append(".                Toggle hidden files")
        help_lines.append("t                Toggle color scheme (Dark/Light)")
        help_lines.append("o                Sync current pane to other pane")
        help_lines.append("O                Sync other pane to current pane")
        help_lines.append("-                Reset pane split to 50/50")
        help_lines.append("Opt+← / Opt+→    Adjust pane boundary")
        help_lines.append("")
        
        # Log pane controls section
        help_lines.append("=== LOG PANE CONTROLS ===")
        help_lines.append("Ctrl+U           Make log pane smaller")
        help_lines.append("Ctrl+D           Make log pane larger")
        help_lines.append("Ctrl+K           Scroll log up")
        help_lines.append("Ctrl+L           Scroll log down")
        help_lines.append("l                Scroll log up (alternative)")
        help_lines.append("L                Scroll log down (alternative)")
        help_lines.append("")
        
        # General controls section
        help_lines.append("=== GENERAL ===")
        help_lines.append("? / h            Show this help")
        help_lines.append("q / Q            Quit TFM")
        help_lines.append("x / X            Execute external programs")
        help_lines.append("z / Z            Enter sub-shell mode")
        help_lines.append("ESC              Cancel current operation")
        help_lines.append("")
        
        # Configuration info
        help_lines.append("=== CONFIGURATION ===")
        help_lines.append("Configuration file: _config.py")
        help_lines.append("Customize key bindings, colors, and behavior")
        help_lines.append("See CONFIGURATION_SYSTEM.md for details")
        help_lines.append("")
        
        # Tips section
        help_lines.append("=== TIPS ===")
        help_lines.append("• Use multi-selection with Space to operate on multiple files")
        help_lines.append("• Batch rename (R with multiple files) supports regex and macros:")
        help_lines.append("  \\0=full name, \\1-\\9=regex groups, \\d=index number")
        help_lines.append("• Search supports multiple patterns separated by spaces")
        help_lines.append("• Log pane shows operation results and system messages")
        help_lines.append("• File details (i) shows comprehensive file information")
        help_lines.append("• Text viewer (v) supports syntax highlighting")
        help_lines.append("• External programs (x) execute with TFM environment variables")
        help_lines.append("• Sub-shell mode (z) provides environment variables:")
        help_lines.append("  TFM_LEFT_DIR, TFM_RIGHT_DIR, TFM_THIS_DIR, TFM_OTHER_DIR")
        help_lines.append("  TFM_LEFT_SELECTED, TFM_RIGHT_SELECTED, TFM_THIS_SELECTED, TFM_OTHER_SELECTED")
        help_lines.append("• Archive operations support ZIP, TAR.GZ, and TGZ formats")
        help_lines.append("• Archive extraction creates directory with archive base name")
        
        self.show_info_dialog("TFM Help", help_lines)
    
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
    
    def get_batch_rename_active_editor(self):
        """Get the currently active batch rename text editor"""
        return (self.batch_rename_regex_editor if self.batch_rename_active_field == 'regex' 
                else self.batch_rename_destination_editor)
    
    def switch_batch_rename_field(self, field):
        """Switch to the specified batch rename field"""
        if field in ['regex', 'destination'] and field != self.batch_rename_active_field:
            self.batch_rename_active_field = field
            return True
        return False
    
    def handle_batch_rename_input(self, key):
        """Handle input while in batch rename mode with Up/Down field navigation"""
        if key == 27:  # ESC - cancel batch rename
            print("Batch rename cancelled")
            self.exit_batch_rename_mode()
            return True
            
        elif key == KEY_TAB:  # Tab - switch between regex and destination input
            if self.batch_rename_active_field == 'regex':
                self.switch_batch_rename_field('destination')
            else:
                self.switch_batch_rename_field('regex')
            self.needs_full_redraw = True
            return True
            
        elif key == curses.KEY_UP:
            # Up arrow - move to regex field (previous field)
            if self.switch_batch_rename_field('regex'):
                self.needs_full_redraw = True
            return True
            
        elif key == curses.KEY_DOWN:
            # Down arrow - move to destination field (next field)
            if self.switch_batch_rename_field('destination'):
                self.needs_full_redraw = True
            return True
            
        elif key == curses.KEY_PPAGE:  # Page Up - scroll preview up
            if self.batch_rename_scroll > 0:
                self.batch_rename_scroll = max(0, self.batch_rename_scroll - 10)
                self.needs_full_redraw = True
            return True
            
        elif key == curses.KEY_NPAGE:  # Page Down - scroll preview down
            if self.batch_rename_preview:
                max_scroll = max(0, len(self.batch_rename_preview) - 10)
                self.batch_rename_scroll = min(max_scroll, self.batch_rename_scroll + 10)
                self.needs_full_redraw = True
            return True
            
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - perform batch rename
            regex_text = self.batch_rename_regex_editor.get_text()
            dest_text = self.batch_rename_destination_editor.get_text()
            if regex_text and dest_text:
                self.perform_batch_rename()
            else:
                print("Please enter both regex pattern and destination pattern")
            return True
            
        else:
            # Let the active editor handle other keys
            active_editor = self.get_batch_rename_active_editor()
            if active_editor.handle_key(key):
                # Text changed, update preview
                self.update_batch_rename_preview()
                self.needs_full_redraw = True
                return True
        
        # In batch rename mode, capture most other keys to prevent unintended actions
        return True
    
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
            self.left_pane_ratio = max(MIN_PANE_RATIO, self.left_pane_ratio - PANE_ADJUST_STEP)
        elif direction == 'right':
            # Make left pane larger, right pane smaller  
            self.left_pane_ratio = min(MAX_PANE_RATIO, self.left_pane_ratio + PANE_ADJUST_STEP)
            
        # Trigger a full redraw for the new pane layout
        self.needs_full_redraw = True
        
        # Show immediate feedback in log pane
        left_percent = int(self.left_pane_ratio * 100)
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
        """Show the search dialog for filename or content search"""
        self.search_dialog_mode = True
        self.search_dialog_type = search_type
        self.search_dialog_pattern_editor.clear()
        self.search_dialog_results = []
        self.search_dialog_selected = 0
        self.search_dialog_scroll = 0
        self.search_dialog_searching = False
        self.needs_full_redraw = True
    
    def exit_search_dialog_mode(self):
        """Exit search dialog mode"""
        self.search_dialog_mode = False
        self.search_dialog_type = 'filename'
        self.search_dialog_pattern_editor.clear()
        self.search_dialog_results = []
        self.search_dialog_selected = 0
        self.search_dialog_scroll = 0
        self.search_dialog_searching = False
        self.needs_full_redraw = True
    
    def perform_search(self):
        """Perform the actual search based on current pattern and type"""
        pattern_text = self.search_dialog_pattern_editor.text.strip()
        if not pattern_text:
            self.search_dialog_results = []
            return
        
        self.search_dialog_searching = True
        self.search_dialog_results = []
        
        current_pane = self.get_current_pane()
        search_root = current_pane['path']
        
        try:
            if self.search_dialog_type == 'filename':
                # Recursive filename search using fnmatch
                for file_path in search_root.rglob('*'):
                    if fnmatch.fnmatch(file_path.name.lower(), pattern_text.lower()):
                        relative_path = file_path.relative_to(search_root)
                        self.search_dialog_results.append({
                            'path': file_path,
                            'relative_path': str(relative_path),
                            'type': 'file' if file_path.is_file() else 'dir',
                            'match_info': file_path.name
                        })
            
            elif self.search_dialog_type == 'content':
                # Recursive grep-based content search
                import re
                pattern = re.compile(pattern_text, re.IGNORECASE)
                
                for file_path in search_root.rglob('*'):
                    if file_path.is_file():
                        try:
                            # Only search text files
                            if self._is_text_file(file_path):
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    for line_num, line in enumerate(f, 1):
                                        if pattern.search(line):
                                            relative_path = file_path.relative_to(search_root)
                                            self.search_dialog_results.append({
                                                'path': file_path,
                                                'relative_path': str(relative_path),
                                                'type': 'content',
                                                'line_num': line_num,
                                                'match_info': f"Line {line_num}: {line.strip()[:60]}..."
                                            })
                                            break  # Only show first match per file
                        except (PermissionError, UnicodeDecodeError, OSError):
                            continue
        
        except Exception as e:
            print(f"Search error: {e}")
        
        self.search_dialog_searching = False
        self.search_dialog_selected = 0
        self.search_dialog_scroll = 0
    
    def _is_text_file(self, file_path):
        """Check if a file is likely a text file"""
        try:
            # Check file extension
            text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.md', '.json', '.xml', '.yml', '.yaml', '.cfg', '.conf', '.ini', '.log'}
            if file_path.suffix.lower() in text_extensions:
                return True
            
            # Check if file has no extension (might be text)
            if not file_path.suffix:
                # Read first few bytes to check for binary content
                with open(file_path, 'rb') as f:
                    chunk = f.read(1024)
                    # If it contains null bytes, it's likely binary
                    return b'\x00' not in chunk
            
            return False
        except:
            return False
    
    def handle_search_dialog_input(self, key):
        """Handle input while in search dialog mode"""
        if key == 27:  # ESC - cancel
            self.exit_search_dialog_mode()
            return True
        elif key == curses.KEY_UP:
            # Move selection up
            if self.search_dialog_results and self.search_dialog_selected > 0:
                self.search_dialog_selected -= 1
                self._adjust_search_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_DOWN:
            # Move selection down
            if self.search_dialog_results and self.search_dialog_selected < len(self.search_dialog_results) - 1:
                self.search_dialog_selected += 1
                self._adjust_search_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            if self.search_dialog_results:
                self.search_dialog_selected = max(0, self.search_dialog_selected - 10)
                self._adjust_search_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            if self.search_dialog_results:
                self.search_dialog_selected = min(len(self.search_dialog_results) - 1, self.search_dialog_selected + 10)
                self._adjust_search_dialog_scroll()
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_HOME:  # Home - text cursor or list navigation
            # If there's text in pattern, let editor handle it for cursor movement
            if self.search_dialog_pattern_editor.text:
                if self.search_dialog_pattern_editor.handle_key(key):
                    self.needs_full_redraw = True
            else:
                # If no pattern text, use for list navigation
                if self.search_dialog_results:
                    self.search_dialog_selected = 0
                    self.search_dialog_scroll = 0
                    self.needs_full_redraw = True
            return True
        elif key == curses.KEY_END:  # End - text cursor or list navigation
            # If there's text in pattern, let editor handle it for cursor movement
            if self.search_dialog_pattern_editor.text:
                if self.search_dialog_pattern_editor.handle_key(key):
                    self.needs_full_redraw = True
            else:
                # If no pattern text, use for list navigation
                if self.search_dialog_results:
                    self.search_dialog_selected = len(self.search_dialog_results) - 1
                    self._adjust_search_dialog_scroll()
                    self.needs_full_redraw = True
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Select current result
            if self.search_dialog_results and 0 <= self.search_dialog_selected < len(self.search_dialog_results):
                selected_result = self.search_dialog_results[self.search_dialog_selected]
                self._navigate_to_search_result(selected_result)
            self.exit_search_dialog_mode()
            return True
        elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
            # Let the editor handle cursor movement keys
            if self.search_dialog_pattern_editor.handle_key(key):
                self.needs_full_redraw = True
            return True
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Let the editor handle backspace
            if self.search_dialog_pattern_editor.handle_key(key):
                self.perform_search()
                self.needs_full_redraw = True
            return True
        elif key == ord('\t'):  # Tab - switch between filename and content search
            self.search_dialog_type = 'content' if self.search_dialog_type == 'filename' else 'filename'
            self.perform_search()
            self.needs_full_redraw = True
            return True
        elif 32 <= key <= 126:  # Printable characters
            # Let the editor handle printable characters
            if self.search_dialog_pattern_editor.handle_key(key):
                self.perform_search()
                self.needs_full_redraw = True
            return True
        return False
    
    def _adjust_search_dialog_scroll(self):
        """Adjust scroll offset to keep selected item visible"""
        height, width = self.stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_height = max(20, int(height * 0.8))
        content_height = dialog_height - 8  # Account for title, search box, borders, help
        
        if self.search_dialog_selected < self.search_dialog_scroll:
            self.search_dialog_scroll = self.search_dialog_selected
        elif self.search_dialog_selected >= self.search_dialog_scroll + content_height:
            self.search_dialog_scroll = self.search_dialog_selected - content_height + 1
    
    def _navigate_to_search_result(self, result):
        """Navigate to the selected search result"""
        current_pane = self.get_current_pane()
        target_path = result['path']
        
        if result['type'] == 'dir':
            # Navigate to directory
            current_pane['path'] = target_path
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            print(f"Navigated to directory: {result['relative_path']}")
        else:
            # Navigate to file's directory and select the file
            parent_dir = target_path.parent
            current_pane['path'] = parent_dir
            current_pane['selected_files'].clear()
            
            # Refresh files and find the target file
            self.refresh_files(current_pane)
            
            # Find and select the target file
            for i, file_path in enumerate(current_pane['files']):
                if file_path == target_path:
                    current_pane['selected_index'] = i
                    # Adjust scroll to make selection visible
                    height, width = self.stdscr.getmaxyx()
                    calculated_height = int(height * self.log_height_ratio)
                    log_height = calculated_height if self.log_height_ratio > 0 else 0
                    display_height = height - log_height - 4
                    
                    if current_pane['selected_index'] < current_pane['scroll_offset']:
                        current_pane['scroll_offset'] = current_pane['selected_index']
                    elif current_pane['selected_index'] >= current_pane['scroll_offset'] + display_height:
                        current_pane['scroll_offset'] = current_pane['selected_index'] - display_height + 1
                    break
            
            if result['type'] == 'content':
                print(f"Found content match in: {result['relative_path']} at line {result['line_num']}")
            else:
                print(f"Navigated to file: {result['relative_path']}")
        
        self.needs_full_redraw = True
    
    def draw_search_dialog(self):
        """Draw the search dialog overlay"""
        height, width = self.stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(60, int(width * 0.8))
        dialog_height = max(20, int(height * 0.8))
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                self.safe_addstr(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            self.safe_addstr(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                self.safe_addstr(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    self.safe_addstr(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            self.safe_addstr(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        title_text = f" Search ({self.search_dialog_type.title()}) "
        title_x = start_x + (dialog_width - len(title_text)) // 2
        if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
            self.safe_addstr(start_y, title_x, title_text, border_color)
        
        # Draw search box
        search_y = start_y + 2
        # Draw pattern input using SingleLineTextEdit
        if search_y < height:
            max_pattern_width = dialog_width - 4  # Leave some margin
            self.search_dialog_pattern_editor.draw(
                self.stdscr, search_y, start_x + 2, max_pattern_width,
                "Pattern: ",
                is_active=True
            )
        
        # Draw search type indicator
        type_y = start_y + 3
        if type_y < height:
            type_text = f"Mode: {self.search_dialog_type.title()} (Tab to switch)"
            self.safe_addstr(type_y, start_x + 2, type_text[:dialog_width - 4], get_status_color() | curses.A_DIM)
        
        # Draw separator line
        sep_y = start_y + 4
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            self.safe_addstr(sep_y, start_x, sep_line[:dialog_width], border_color)
        
        # Draw results count
        count_y = start_y + 5
        if count_y < height:
            if self.search_dialog_searching:
                count_text = "Searching..."
            else:
                count_text = f"Results: {len(self.search_dialog_results)}"
            self.safe_addstr(count_y, start_x + 2, count_text, get_status_color() | curses.A_DIM)
        
        # Calculate results area
        results_start_y = start_y + 6
        results_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = results_end_y - results_start_y + 1
        
        # Draw results
        visible_results = self.search_dialog_results[self.search_dialog_scroll:self.search_dialog_scroll + content_height]
        
        for i, result in enumerate(visible_results):
            y = results_start_y + i
            if y <= results_end_y and y < height:
                result_index = self.search_dialog_scroll + i
                is_selected = result_index == self.search_dialog_selected
                
                # Format result text
                if result['type'] == 'dir':
                    result_text = f"📁 {result['relative_path']}"
                elif result['type'] == 'content':
                    result_text = f"📄 {result['relative_path']} - {result['match_info']}"
                else:
                    result_text = f"📄 {result['relative_path']}"
                
                if len(result_text) > content_width - 2:
                    result_text = result_text[:content_width - 5] + "..."
                
                # Add selection indicator
                if is_selected:
                    display_text = f"► {result_text}"
                    item_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                else:
                    display_text = f"  {result_text}"
                    item_color = get_status_color()
                
                # Ensure text fits
                display_text = display_text[:content_width]
                self.safe_addstr(y, content_start_x, display_text, item_color)
        
        # Draw help text
        help_y = start_y + dialog_height - 2
        if help_y < height:
            help_text = "Enter: Select | Tab: Switch mode | ESC: Cancel"
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                self.safe_addstr(help_y, help_x, help_text, get_status_color() | curses.A_DIM)
    

    def draw_batch_rename_dialog(self):
        """Draw the batch rename dialog overlay"""
        height, width = self.stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(80, int(width * 0.9))
        dialog_height = max(25, int(height * 0.9))
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                self.safe_addstr(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            self.safe_addstr(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                self.safe_addstr(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    self.safe_addstr(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            self.safe_addstr(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        title_text = f" Batch Rename ({len(self.batch_rename_files)} files) "
        title_x = start_x + (dialog_width - len(title_text)) // 2
        if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
            self.safe_addstr(start_y, title_x, title_text, border_color)
        
        # Draw regex input
        regex_y = start_y + 2
        regex_label = "Regex Pattern: "
        
        if regex_y < height:
            content_start_x = start_x + 2
            content_width = dialog_width - 4
            
            # Draw regex input field using SingleLineTextEdit
            self.batch_rename_regex_editor.draw(
                self.stdscr, regex_y, content_start_x, content_width,
                regex_label,
                is_active=(self.batch_rename_active_field == 'regex')
            )
        
        # Draw destination input
        dest_y = start_y + 3
        dest_label = "Destination:   "
        
        if dest_y < height:
            # Draw destination input field using SingleLineTextEdit
            self.batch_rename_destination_editor.draw(
                self.stdscr, dest_y, content_start_x, content_width,
                dest_label,
                is_active=(self.batch_rename_active_field == 'destination')
            )
        
        # Draw navigation help
        nav_help_y = start_y + 4
        if nav_help_y < height:
            nav_help_text = "Navigation: ↑/↓=Switch fields, Tab=Alt switch, PgUp/PgDn=Scroll preview"
            self.safe_addstr(nav_help_y, content_start_x, nav_help_text[:content_width], get_status_color() | curses.A_DIM)
        
        # Draw help for macros
        help_y = start_y + 5
        if help_y < height:
            help_text = "Macros: \\0=full name, \\1-\\9=regex groups, \\d=index"
            self.safe_addstr(help_y, content_start_x, help_text[:content_width], get_status_color() | curses.A_DIM)
        
        # Draw separator line
        sep_y = start_y + 6
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            self.safe_addstr(sep_y, start_x, sep_line[:dialog_width], border_color)
        
        # Draw preview header
        preview_header_y = start_y + 7
        if preview_header_y < height:
            header_text = "Preview:"
            self.safe_addstr(preview_header_y, content_start_x, header_text, get_status_color() | curses.A_BOLD)
        
        # Calculate preview area
        preview_start_y = start_y + 8
        preview_end_y = start_y + dialog_height - 3
        preview_height = preview_end_y - preview_start_y + 1
        
        # Draw preview list
        if self.batch_rename_preview:
            visible_preview = self.batch_rename_preview[self.batch_rename_scroll:self.batch_rename_scroll + preview_height]
            
            for i, preview in enumerate(visible_preview):
                y = preview_start_y + i
                if y <= preview_end_y and y < height:
                    original = preview['original']
                    new = preview['new']
                    conflict = preview['conflict']
                    valid = preview['valid']
                    
                    # Format preview line
                    if original == new:
                        status = "UNCHANGED"
                        status_color = get_status_color() | curses.A_DIM
                    elif conflict:
                        status = "CONFLICT!"
                        status_color = get_status_color() | curses.A_BOLD | curses.color_pair(1)  # Red
                    elif not valid:
                        status = "INVALID!"
                        status_color = get_status_color() | curses.A_BOLD | curses.color_pair(1)  # Red
                    else:
                        status = "OK"
                        status_color = get_status_color() | curses.color_pair(2)  # Green
                    
                    # Create preview line
                    max_name_width = (content_width - 20) // 2
                    original_display = original[:max_name_width] if len(original) > max_name_width else original
                    new_display = new[:max_name_width] if len(new) > max_name_width else new
                    
                    preview_line = f"{original_display:<{max_name_width}} → {new_display:<{max_name_width}} [{status}]"
                    preview_line = preview_line[:content_width]
                    
                    self.safe_addstr(y, content_start_x, preview_line, status_color)
        else:
            # No preview available
            no_preview_y = preview_start_y + 2
            if no_preview_y < height:
                no_preview_text = "Enter regex pattern and destination to see preview"
                self.safe_addstr(no_preview_y, content_start_x, no_preview_text, get_status_color() | curses.A_DIM)
        
        # Draw help text
        help_y = start_y + dialog_height - 2
        if help_y < height:
            help_text = "Tab: Switch input | ←→: Move cursor | Home/End: Start/End | Enter: Rename | ESC: Cancel | ↑↓: Scroll"
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                self.safe_addstr(help_y, help_x, help_text, get_status_color() | curses.A_DIM)
        
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
            sys.stdout = LogCapture(self.log_messages, "STDOUT")
            sys.stderr = LogCapture(self.log_messages, "STDERR")
            
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
            if self.info_dialog_mode:
                if self.handle_info_dialog_input(key):
                    continue  # Info dialog mode handled the key
            
            # Handle list dialog mode input
            if self.list_dialog_mode:
                if self.handle_list_dialog_input(key):
                    continue  # List dialog mode handled the key
            
            # Handle search dialog mode input
            if self.search_dialog_mode:
                if self.handle_search_dialog_input(key):
                    continue  # Search dialog mode handled the key
            
            # Handle batch rename dialog mode input
            if self.batch_rename_mode:
                if self.handle_batch_rename_input(key):
                    continue  # Batch rename mode handled the key
            
            # Skip regular key processing if any dialog is open
            # This prevents conflicts like starting isearch mode while help dialog is open
            if self.quick_choice_mode or self.info_dialog_mode or self.list_dialog_mode or self.search_dialog_mode or self.batch_rename_mode or self.isearch_mode or self.filter_mode or self.rename_mode or self.create_dir_mode or self.create_file_mode or self.create_archive_mode:
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
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
                    self.needs_full_redraw = True
            elif key == 12:  # Ctrl+L - scroll log down
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
                    self.needs_full_redraw = True
            elif key == curses.KEY_RESIZE:  # Terminal window resized
                # Clear screen and trigger full redraw to handle new dimensions
                self.clear_screen_with_background()
                self.needs_full_redraw = True
            elif key == KEY_TAB:  # Tab key - switch panes
                self.active_pane = 'right' if self.active_pane == 'left' else 'left'
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
                self.show_hidden = not self.show_hidden
                # Reset both panes
                self.left_pane['selected_index'] = 0
                self.left_pane['scroll_offset'] = 0
                self.right_pane['selected_index'] = 0
                self.right_pane['scroll_offset'] = 0
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
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    # Try log scrolling first, fall back to file navigation
                    self.log_scroll_offset += 5  # Scroll multiple lines
                    self.log_scroll_offset = min(self.log_scroll_offset, len(self.log_messages) - 1)
                    self.needs_full_redraw = True
                else:
                    # Regular file navigation
                    current_pane['selected_index'] = max(0, current_pane['selected_index'] - 10)
                    self.needs_full_redraw = True
            elif key == curses.KEY_NPAGE:  # Page Down - scroll log down when Ctrl is held, otherwise file navigation  
                # Check if this is Ctrl+Page Down for log scrolling
                if self.log_scroll_offset > 0:
                    # Try log scrolling first, fall back to file navigation
                    self.log_scroll_offset -= 5  # Scroll multiple lines
                    self.log_scroll_offset = max(0, self.log_scroll_offset)
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
            elif key == curses.KEY_LEFT and self.active_pane == 'left':  # Left arrow in left pane - go to parent
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
            elif key == curses.KEY_RIGHT and self.active_pane == 'right':  # Right arrow in right pane - go to parent
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
            elif key == curses.KEY_RIGHT and self.active_pane == 'left':  # Right arrow in left pane - switch to right pane
                self.active_pane = 'right'
            elif key == curses.KEY_LEFT and self.active_pane == 'right':  # Left arrow in right pane - switch to left pane
                self.active_pane = 'left'

            elif key == 337:  # Shift+Up in many terminals
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
                    self.needs_full_redraw = True
            elif key == 336:  # Shift+Down in many terminals  
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
                    self.needs_full_redraw = True
            elif key == 393:  # Alternative Shift+Up code
                if self.log_scroll_offset < len(self.log_messages) - 1:
                    self.log_scroll_offset += 1
                    self.needs_full_redraw = True
            elif key == 402:  # Alternative Shift+Down code
                if self.log_scroll_offset > 0:
                    self.log_scroll_offset -= 1
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
                self.left_pane_ratio = 0.5
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