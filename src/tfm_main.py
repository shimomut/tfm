#!/usr/bin/env python3
"""
TUI File Manager - A terminal-based file manager using curses
"""

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
import importlib
import traceback
from tfm_path import Path
from datetime import datetime
from collections import deque
from tfm_single_line_text_edit import SingleLineTextEdit

# Import TTK input event system
from ttk.input_event import InputEvent, KeyCode, ModifierKey
from ttk.renderer import TextAttribute

# Import constants and colors
from tfm_const import *
from tfm_colors import *
from tfm_config import get_config, is_key_bound_to, is_key_bound_to_with_selection, is_action_available, is_special_key_bound_to_with_selection, is_input_event_bound_to, is_input_event_bound_to_with_selection, get_favorite_directories, get_programs, get_program_for_file, has_action_for_file, has_explicit_association
from tfm_text_viewer import view_text_file, is_text_file

# Import new modular components
from tfm_log_manager import LogManager
from tfm_pane_manager import PaneManager
from tfm_file_operations import FileOperations, FileOperationsUI
from tfm_list_dialog import ListDialog, ListDialogHelpers
from tfm_info_dialog import InfoDialog, InfoDialogHelpers
from tfm_search_dialog import SearchDialog, SearchDialogHelpers
from tfm_jump_dialog import JumpDialog, JumpDialogHelpers
from tfm_drives_dialog import DrivesDialog, DrivesDialogHelpers
from tfm_wide_char_utils import get_display_width, truncate_to_width, pad_to_width, safe_get_display_width
from tfm_batch_rename_dialog import BatchRenameDialog, BatchRenameDialogHelpers
from tfm_quick_choice_bar import QuickChoiceBar, QuickChoiceBarHelpers
from tfm_general_purpose_dialog import GeneralPurposeDialog, DialogHelpers
from tfm_external_programs import ExternalProgramManager
from tfm_progress_manager import ProgressManager, OperationType
from tfm_state_manager import get_state_manager, cleanup_state_manager
from tfm_archive import ArchiveOperations, ArchiveUI
from tfm_cache_manager import CacheManager

class FileManager:
    def __init__(self, renderer, remote_log_port=None, left_dir=None, right_dir=None):
        self.renderer = renderer
        self.stdscr = renderer  # Keep stdscr as alias for compatibility during migration
        
        # Load configuration
        self.config = get_config()
        
        # Initialize Unicode handling from configuration
        from tfm_wide_char_utils import initialize_from_config
        initialize_from_config()
        
        # Create TFM user directories if they don't exist
        self._create_user_directories()
        
        # Initialize colors BEFORE any stdout/stderr redirection
        # This prevents issues where LogManager's stdout redirection interferes with color detection
        color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
        init_colors(renderer, color_scheme)
        
        # Initialize modular components
        self.log_manager = LogManager(self.config, remote_port=remote_log_port)
        self.state_manager = get_state_manager()
        
        # Track whether command line directories were provided
        self.cmdline_left_dir_provided = left_dir is not None
        self.cmdline_right_dir_provided = right_dir is not None
        
        # Set up initial directories
        # Use command line arguments if provided, otherwise use defaults
        initial_left_dir = Path(left_dir) if left_dir else Path.cwd()
        initial_right_dir = Path(right_dir) if right_dir else Path.home()
        
        # Validate directories exist, fall back to defaults if not
        if not initial_left_dir.exists() or not initial_left_dir.is_dir():
            self.log_manager.add_message("WARNING", f"Left directory '{initial_left_dir}' does not exist, using current directory")
            initial_left_dir = Path.cwd()
            
        if not initial_right_dir.exists() or not initial_right_dir.is_dir():
            self.log_manager.add_message("WARNING", f"Right directory '{initial_right_dir}' does not exist, using home directory")
            initial_right_dir = Path.home()
        
        # Use simple defaults since TFM loads previous state anyway
        self.pane_manager = PaneManager(self.config, initial_left_dir, initial_right_dir, self.state_manager)
        self.file_operations = FileOperations(self.config)
        self.file_operations.log_manager = self.log_manager  # Set log_manager for error reporting
        self.list_dialog = ListDialog(self.config, renderer)
        self.info_dialog = InfoDialog(self.config, renderer)
        self.search_dialog = SearchDialog(self.config, renderer)
        self.jump_dialog = JumpDialog(self.config, renderer)
        self.drives_dialog = DrivesDialog(self.config, renderer)
        self.batch_rename_dialog = BatchRenameDialog(self.config, renderer)
        self.quick_choice_bar = QuickChoiceBar(self.config, renderer)
        self.general_dialog = GeneralPurposeDialog(self.config, renderer)
        self.external_program_manager = ExternalProgramManager(self.config, self.log_manager, renderer)
        self.progress_manager = ProgressManager()
        self.cache_manager = CacheManager(self.log_manager)
        self.archive_operations = ArchiveOperations(self.log_manager, self.cache_manager, self.progress_manager)
        self.archive_ui = ArchiveUI(self, self.archive_operations)
        self.file_operations_ui = FileOperationsUI(self, self.file_operations)
        
        # Layout settings
        self.log_height_ratio = getattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO', DEFAULT_LOG_HEIGHT_RATIO)
        self.needs_full_redraw = True  # Flag to control when to redraw everything
        self.needs_dialog_redraw = False  # Flag to control when to redraw dialogs
        
        # Isearch mode state
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        

        
        # Dialog state (now handled by general_dialog)
        self.rename_file_path = None  # Still needed for rename operations
        
        # Operation state flags
        self.operation_in_progress = False  # Flag to block input during operations
        self.operation_cancelled = False  # Flag to signal operation cancellation

        self.should_quit = False  # Flag to control main loop exit

        # Add startup messages to log
        self.log_manager.add_startup_messages(VERSION, GITHUB_URL, APP_NAME)
        
        # Colors already initialized before LogManager creation to prevent
        # stdout/stderr redirection from interfering with color detection
        
        # Configure renderer
        self.renderer.set_cursor_visibility(False)  # Hide cursor
        # Note: TTK handles special keys automatically through InputEvent, no keypad() needed
        
        # Track startup time for delayed redraw
        self.startup_time = time.time()
        
        # Load saved state
        self.load_application_state()
    
    def _create_user_directories(self):
        """Create TFM user directories if they don't exist."""
        try:
            # Create ~/.tfm directory
            tfm_dir = Path.home() / '.tfm'
            tfm_dir.mkdir(exist_ok=True)
            
            # Create ~/.tfm/tools directory
            tools_dir = tfm_dir / 'tools'
            tools_dir.mkdir(exist_ok=True)
            
            # Optionally create other user directories that might be useful in the future
            # state_dir = tfm_dir / 'state'  # For future state persistence
            # state_dir.mkdir(exist_ok=True)
            
        except OSError as e:
            # If we can't create the directories, log a warning but don't fail
            # TFM should still work without user directories
            print(f"Warning: Could not create TFM user directories: {e}", file=sys.stderr)
        
    def safe_addstr(self, y, x, text, attr=None):
        """Safely add string to screen, handling boundary conditions
        
        Args:
            y: Row position
            x: Column position
            text: Text to display
            attr: Either a tuple of (color_pair, attributes) or None for default
        """
        try:
            height, width = self.renderer.get_dimensions()
            
            # Check bounds
            if y < 0 or y >= height or x < 0 or x >= width:
                return
                
            # Truncate text if it would exceed screen width
            max_len = width - x - 1  # Leave space to avoid last column
            if max_len <= 0:
                return
                
            truncated_text = text[:max_len] if len(text) > max_len else text
            
            # Handle attr parameter - should be a tuple of (color_pair, attributes)
            if attr is None:
                color_pair = 0
                attributes = TextAttribute.NORMAL
            elif isinstance(attr, tuple) and len(attr) == 2:
                color_pair, attributes = attr
            else:
                # Legacy: single integer, treat as color_pair with no attributes
                color_pair = attr if isinstance(attr, int) else 0
                attributes = TextAttribute.NORMAL
            
            self.renderer.draw_text(y, x, truncated_text, color_pair=color_pair, attributes=attributes)
        except Exception:
            pass  # Ignore rendering errors
    
    def clear_screen_with_background(self):
        """Clear screen and apply proper background color for current scheme"""
        try:
            # Clear the screen using TTK renderer
            self.renderer.clear()
            
            # TTK renderer handles background color automatically
            # No need for manual background filling
            
        except Exception as e:
            # Any other error, use regular clear
            print(f"Warning: Screen clear with background failed: {e}")
            self.renderer.clear()

    def is_key_for_action(self, event, action):
        """Check if an input event matches a configured action and respects selection requirements"""
        current_pane = self.get_current_pane()
        has_selection = len(current_pane['selected_files']) > 0
        
        # Use the new InputEvent-aware function
        return is_input_event_bound_to_with_selection(event, action, has_selection)
        
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
            left_color_pair, left_attributes = get_footer_color(self.pane_manager.active_pane == 'left')
            self.renderer.draw_text(y, 2, left_footer, color_pair=left_color_pair, attributes=left_attributes)
        except Exception:
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
            right_color_pair, right_attributes = get_footer_color(self.pane_manager.active_pane == 'right')
            self.renderer.draw_text(y, left_pane_width + 2, right_footer, color_pair=right_color_pair, attributes=right_attributes)
        except Exception:
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
    
    def unselect_all(self):
        """Unselect all items in current pane"""
        current_pane = self.get_current_pane()
        if current_pane['selected_files']:
            current_pane['selected_files'].clear()
            print("Unselected all items")
            self.needs_full_redraw = True
    
    def select_all(self):
        """Select all items (files and directories) in current pane"""
        current_pane = self.get_current_pane()
        selected_count = 0
        for file_path in current_pane['files']:
            if file_path not in current_pane['selected_files']:
                current_pane['selected_files'].add(file_path)
                selected_count += 1
        
        if selected_count > 0:
            print(f"Selected all {len(current_pane['selected_files'])} items")
            self.needs_full_redraw = True
        elif current_pane['selected_files']:
            print(f"All {len(current_pane['selected_files'])} items already selected")
    
    def sync_current_to_other(self):
        """Change current pane's directory to match the other pane's directory, or sync cursor if already same directory"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Check if both panes are already showing the same directory
        if current_pane['path'] == other_pane['path']:
            # Both panes show same directory, just sync cursor position
            if self.pane_manager.sync_cursor_to_other_pane(print):
                # Adjust scroll offset if needed to keep selection visible
                height, width = self.renderer.get_dimensions()
                calculated_height = int(height * self.log_height_ratio)
                log_height = calculated_height if self.log_height_ratio > 0 else 0
                display_height = height - log_height - 3
                
                self.pane_manager.adjust_scroll_for_selection(current_pane, display_height)
                self.needs_full_redraw = True
        else:
            # Different directories, sync directory
            if self.pane_manager.sync_current_to_other(print):
                self.refresh_files(current_pane)
                
                # Try to restore cursor position for this directory
                height, width = self.renderer.get_dimensions()
                calculated_height = int(height * self.log_height_ratio)
                log_height = calculated_height if self.log_height_ratio > 0 else 0
                display_height = height - log_height - 3
                
                if not self.pane_manager.restore_cursor_position(current_pane, display_height):
                    # If no history found, default to first item
                    current_pane['selected_index'] = 0
                    current_pane['scroll_offset'] = 0
                
                self.needs_full_redraw = True
    
    def sync_other_to_current(self):
        """Change other pane's directory to match the current pane's directory, or sync cursor if already same directory"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Check if both panes are already showing the same directory
        if current_pane['path'] == other_pane['path']:
            # Both panes show same directory, just sync cursor position
            if self.pane_manager.sync_cursor_from_current_pane(print):
                # Adjust scroll offset if needed to keep selection visible
                height, width = self.renderer.get_dimensions()
                calculated_height = int(height * self.log_height_ratio)
                log_height = calculated_height if self.log_height_ratio > 0 else 0
                display_height = height - log_height - 3
                
                self.pane_manager.adjust_scroll_for_selection(other_pane, display_height)
                self.needs_full_redraw = True
        else:
            # Different directories, sync directory
            if self.pane_manager.sync_other_to_current(print):
                self.refresh_files(other_pane)
                
                # Try to restore cursor position for this directory
                height, width = self.renderer.get_dimensions()
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
            height, width = self.renderer.get_dimensions()
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
            height, width = self.renderer.get_dimensions()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            self.pane_manager.adjust_scroll_for_selection(other_pane, display_height)
            self.needs_full_redraw = True
        
    def restore_cursor_position(self, pane_data):
        """Restore cursor position from history - wrapper for pane_manager method"""
        height, width = self.renderer.get_dimensions()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        return self.pane_manager.restore_cursor_position(pane_data, display_height)
    
    def save_cursor_position(self, pane_data):
        """Save cursor position to history - wrapper for pane_manager method"""
        return self.pane_manager.save_cursor_position(pane_data)
    
    def adjust_scroll_for_selection(self, pane_data):
        """Adjust scroll for selection - wrapper for pane_manager method"""
        height, width = self.renderer.get_dimensions()
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
        Returns the display width needed for the extension column.
        """
        max_width = 0
        max_ext_length = getattr(self.config, 'MAX_EXTENSION_LENGTH', 5)
        
        for file_path in pane_data['files']:
            if file_path.is_file():
                _, extension = self.separate_filename_extension(file_path.name, file_path.is_dir())
                if extension and len(extension) <= max_ext_length:
                    # Use display width instead of character count
                    ext_display_width = safe_get_display_width(extension)
                    max_width = max(max_width, ext_display_width)
        
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
        height, width = self.renderer.get_dimensions()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        return self.log_manager.get_log_scroll_percentage(log_height)
    
    def _get_log_pane_height(self):
        """Calculate the current log pane height in lines"""
        height, width = self.renderer.get_dimensions()
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
            
    def format_path_display(self, path_obj):
        """
        Format a path for display, with special handling for archive paths.
        
        Args:
            path_obj: Path object to format
            
        Returns:
            Formatted string for display
        """
        path_str = str(path_obj)
        
        # Check if this is an archive path
        if path_str.startswith('archive://'):
            # Format: archive:///path/to/archive.zip#internal/path
            # Extract archive file path and internal path
            path_part = path_str[10:]  # Remove 'archive://'
            
            if '#' in path_part:
                archive_path, internal_path = path_part.split('#', 1)
                
                # Get just the archive filename
                archive_name = Path(archive_path).name
                
                if internal_path:
                    # Show: [archive.zip]/internal/path
                    return f"[{archive_name}]/{internal_path}"
                else:
                    # Show: [archive.zip]
                    return f"[{archive_name}]"
            else:
                # Shouldn't happen, but handle gracefully
                return path_str
        else:
            # Regular path
            return path_str
    
    def draw_header(self):
        """Draw the header with pane paths and controls"""
        height, width = self.renderer.get_dimensions()
        left_pane_width = int(width * self.pane_manager.left_pane_ratio)
        right_pane_width = width - left_pane_width
        
        # Clear header area (avoid last column)
        try:
            color_pair, attributes = get_header_color()
            self.renderer.draw_text(0, 0, " " * (width - 1), color_pair=color_pair, attributes=attributes)
        except Exception:
            pass
        
        # Left pane path with safety checks
        if left_pane_width > 6:  # Minimum space needed
            left_path = self.format_path_display(self.pane_manager.left_pane['path'])
            max_left_path_width = max(1, left_pane_width - 4)
            # Use wide character aware truncation for path display
            if safe_get_display_width(left_path) > max_left_path_width:
                left_path = truncate_to_width(left_path, max_left_path_width, "...")
            
            color_pair, attributes = get_header_color(self.pane_manager.active_pane == 'left')
            try:
                self.renderer.draw_text(0, 2, left_path, color_pair=color_pair, attributes=attributes)
            except Exception:
                pass  # Ignore drawing errors for narrow panes
        
        # Separator with bounds check
        if 0 <= left_pane_width < width:
            try:
                color_pair, attributes = get_boundary_color()
                self.renderer.draw_text(0, left_pane_width, "│", color_pair=color_pair, attributes=attributes)
            except Exception:
                pass
        
        # Right pane path with safety checks
        if right_pane_width > 6:  # Minimum space needed
            right_path = self.format_path_display(self.pane_manager.right_pane['path'])
            max_right_path_width = max(1, right_pane_width - 4)
            # Use wide character aware truncation for path display
            if safe_get_display_width(right_path) > max_right_path_width:
                right_path = truncate_to_width(right_path, max_right_path_width, "...")
                
            right_color_pair, right_attributes = get_header_color(self.pane_manager.active_pane == 'right')
            try:
                right_start_x = left_pane_width + 2
                if right_start_x < width:
                    self.renderer.draw_text(0, right_start_x, right_path, color_pair=right_color_pair, attributes=right_attributes)
            except Exception:
                pass  # Ignore drawing errors for narrow panes
        
        # No controls in header anymore - moved to status bar
        
    def draw_pane(self, pane_data, start_x, pane_width, is_active):
        """Draw a single pane"""
        # Safety checks to prevent crashes
        if pane_width < 10:  # Minimum viable pane width
            return
        if start_x < 0 or start_x >= self.renderer.get_dimensions()[1]:
            return
            
        height, width = self.renderer.get_dimensions()
        # Allow log pane to be completely hidden (0 height) when ratio is 0
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3  # Reserve space for header, footer, and status
        
        # Check if there are no files to display
        if not pane_data['files']:
            # Show "no items to show" message in the center of the pane
            message = "No items to show"
            message_y = 1 + display_height // 2  # Center vertically in the pane
            # Use display width for proper centering with wide characters
            message_display_width = safe_get_display_width(message)
            message_x = start_x + (pane_width - message_display_width) // 2  # Center horizontally
            
            try:
                from tfm_colors import get_error_color
                error_color_pair, error_attributes = get_error_color()
                self.renderer.draw_text(message_y, message_x, message, color_pair=error_color_pair, attributes=error_attributes)
            except (Exception, ImportError):
                # Fallback if color function not available or position invalid
                try:
                    self.renderer.draw_text(message_y, start_x + 2, message)
                except Exception:
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
                color_pair, _ = get_file_color(is_dir, is_executable, False, False)
                color = (color_pair, TextAttribute.UNDERLINE)
            # Handle multi-selection highlighting
            elif is_multi_selected and not is_selected:
                # Get base color and add reverse video for multi-selected files
                color_pair, _ = get_file_color(is_dir, is_executable, False, False)
                color = (color_pair, TextAttribute.REVERSE)
                
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
                # Use wide character aware truncation
                max_name_width = max(1, pane_width - 5)
                truncated_name = truncate_to_width(display_name, max_name_width, "...")
                line = f"{selection_marker} {truncated_name}"
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
                            ext_width = safe_get_display_width(extension)
                        
                        # Reserve space for: marker(2) + space(1) + ext_width + space(1) + size(8) = 12 + ext_width
                        name_width = usable_width - (12 + ext_width)
                        
                        # Truncate basename using wide character aware truncation
                        if safe_get_display_width(basename) > name_width:
                            basename = truncate_to_width(basename, name_width, "...")
                        
                        # Pad basename to maintain column alignment using display width
                        padded_basename = pad_to_width(basename, name_width, align='left')
                        padded_extension = pad_to_width(extension, ext_width, align='left')
                        line = f"{selection_marker} {padded_basename} {padded_extension}{size_str:>8}"
                    else:
                        # No extension separation - use full width for filename
                        # Reserve space for: marker(2) + space(1) + size(8) = 11
                        name_width = usable_width - 11
                        
                        # Truncate filename using wide character aware truncation
                        if safe_get_display_width(display_name) > name_width:
                            display_name = truncate_to_width(display_name, name_width, "...")
                        
                        # Pad filename to maintain column alignment using display width
                        padded_name = pad_to_width(display_name, name_width, align='left')
                        line = f"{selection_marker} {padded_name}{size_str:>8}"
                else:
                    # For wider panes: "● basename ext size datetime"
                    if extension:
                        # Calculate actual maximum extension width for this pane
                        ext_width = self.calculate_max_extension_width(pane_data)
                        if ext_width == 0:  # No extensions in this pane
                            ext_width = safe_get_display_width(extension)
                        
                        # Reserve space for: marker(2) + space(1) + ext_width + space(1) + size(8) + space(1) + datetime(len) = 13 + ext_width + datetime_width
                        name_width = usable_width - (13 + ext_width + datetime_width)
                        
                        # Truncate basename using wide character aware truncation
                        if safe_get_display_width(basename) > name_width:
                            basename = truncate_to_width(basename, name_width, "...")
                        
                        # Pad basename to maintain column alignment using display width
                        padded_basename = pad_to_width(basename, name_width, align='left')
                        padded_extension = pad_to_width(extension, ext_width, align='left')
                        line = f"{selection_marker} {padded_basename} {padded_extension} {size_str:>8} {mtime_str}"
                    else:
                        # No extension separation - use full width for filename
                        # Reserve space for: marker(2) + space(1) + size(8) + space(1) + datetime(len) = 12 + datetime_width
                        name_width = usable_width - (12 + datetime_width)
                        
                        # Truncate filename using wide character aware truncation
                        if safe_get_display_width(display_name) > name_width:
                            display_name = truncate_to_width(display_name, name_width, "...")
                        
                        # Pad filename to maintain column alignment using display width
                        padded_name = pad_to_width(display_name, name_width, align='left')
                        line = f"{selection_marker} {padded_name} {size_str:>8} {mtime_str}"
            
            try:
                # Use wide character aware truncation for final line display
                max_line_width = pane_width - 2
                if safe_get_display_width(line) > max_line_width:
                    line = truncate_to_width(line, max_line_width, "")
                
                # Color is already a tuple of (color_pair, attributes)
                color_pair, attributes = color
                self.renderer.draw_text(y, start_x + 1, line, color_pair=color_pair, attributes=attributes)
            except Exception:
                pass  # Ignore if we can't write to screen edge
                
    def draw_files(self):
        """Draw both file panes"""
        height, width = self.renderer.get_dimensions()
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
                boundary_color_pair, boundary_attributes = get_boundary_color()
                self.renderer.draw_text(y, left_pane_width, "│", color_pair=boundary_color_pair, attributes=boundary_attributes)
            except Exception:
                pass
        
        # Draw left pane
        self.draw_pane(self.pane_manager.left_pane, 0, left_pane_width, self.pane_manager.active_pane == 'left')
        
        # Draw right pane
        self.draw_pane(self.pane_manager.right_pane, left_pane_width, right_pane_width, self.pane_manager.active_pane == 'right')
        
    def draw_log_pane(self):
        """Draw the log pane at the bottom"""
        height, width = self.renderer.get_dimensions()
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
            boundary_color_pair, boundary_attributes = get_boundary_color()
            self.renderer.draw_text(footer_y, 0, separator_line, color_pair=boundary_color_pair, attributes=boundary_attributes)
            
            # Always draw file list footers
            self.draw_file_footers(footer_y, left_pane_width)
        except Exception:
            pass
            
        # If log pane is hidden (0 height), don't draw log content
        if log_height == 0:
            return
            
        # Log content starts right after the footer line
        log_start_y = footer_y + 1
        
        # Use log manager to draw the log content
        self.log_manager.draw_log_pane(self.renderer, log_start_y, log_height, width)
                
    def draw_status(self):
        """Draw status line with file info and controls"""
        height, width = self.renderer.get_dimensions()
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
        if self.quick_choice_bar.is_active:
            self.quick_choice_bar.draw(status_y, width)
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
                    # Get status color
                    status_color_pair, status_attributes = get_status_color()
                    self.renderer.draw_text(status_y, help_x, help_text, status_color_pair, status_attributes)
            else:
                # Shorter help text for narrow terminals
                short_help = "ESC:exit Enter:accept ↑↓:nav"
                if len(isearch_prompt) + len(short_help) + 6 < width:
                    help_x = width - len(short_help) - 3
                    if help_x > len(isearch_prompt) + 4:
                        # Get status color
                        status_color_pair, status_attributes = get_status_color()
                        self.renderer.draw_text(status_y, help_x, short_help, status_color_pair, status_attributes)
            return
        
        # Normal status display
        # Left side: status info
        status_parts = []
        
        # Check if browsing an archive
        current_path_str = str(current_pane['path'])
        if current_path_str.startswith('archive://'):
            status_parts.append("📦 archive")
        
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
        elif self.archive_operations.is_archive(selected_file):
            # Navigate into archive as virtual directory
            try:
                # Import archive exceptions for specific error handling
                from tfm_archive import (
                    ArchiveError, ArchiveFormatError, ArchiveCorruptedError,
                    ArchivePermissionError, ArchiveDiskSpaceError
                )
                
                # Save current cursor position before entering archive
                self.save_cursor_position(current_pane)
                
                # Create archive URI for the root of the archive
                archive_uri = f"archive://{selected_file.absolute()}#"
                archive_path = Path(archive_uri)
                
                # Navigate into the archive
                current_pane['path'] = archive_path
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
                current_pane['selected_files'].clear()  # Clear selections when entering archive
                self.refresh_files(current_pane)
                
                # Default to first item
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
                
                self.needs_full_redraw = True
                self.log_manager.add_message("INFO", f"Entered archive: {selected_file.name}")
            except FileNotFoundError as e:
                # Archive file doesn't exist
                user_msg = getattr(e, 'args', ['Archive file not found'])[1] if len(getattr(e, 'args', [])) > 1 else "Archive file not found"
                self.show_error(user_msg)
                self.log_manager.add_message("ERROR", f"Archive not found: {selected_file}: {e}")
            except ArchiveCorruptedError as e:
                # Archive is corrupted
                user_msg = getattr(e, 'user_message', str(e))
                self.show_error(user_msg)
                self.log_manager.add_message("ERROR", f"Corrupted archive: {selected_file}: {e}")
            except ArchiveFormatError as e:
                # Unsupported or invalid format
                user_msg = getattr(e, 'user_message', str(e))
                self.show_error(user_msg)
                self.log_manager.add_message("ERROR", f"Invalid archive format: {selected_file}: {e}")
            except ArchivePermissionError as e:
                # Permission denied
                user_msg = getattr(e, 'user_message', str(e))
                self.show_error(user_msg)
                self.log_manager.add_message("ERROR", f"Permission denied: {selected_file}: {e}")
            except ArchiveDiskSpaceError as e:
                # Insufficient disk space
                user_msg = getattr(e, 'user_message', str(e))
                self.show_error(user_msg)
                self.log_manager.add_message("ERROR", f"Insufficient disk space: {e}")
            except ArchiveError as e:
                # Generic archive error
                user_msg = getattr(e, 'user_message', str(e))
                self.show_error(user_msg)
                self.log_manager.add_message("ERROR", f"Archive error: {selected_file}: {e}")
            except Exception as e:
                # Unexpected error
                self.show_error(f"Cannot open archive: {e}")
                self.log_manager.add_message("ERROR", f"Unexpected error opening archive: {selected_file}: {e}")
        else:
            # For files, try to use file association for 'open' action
            filename = selected_file.name
            command = get_program_for_file(filename, 'open')
            
            if command:
                # Use configured program from file associations
                try:
                    # Suspend curses
                    self.external_program_manager.suspend_curses()
                    
                    # Launch the program
                    result = subprocess.run(command + [str(selected_file)], 
                                          cwd=str(current_pane['path']))
                    
                    # Resume curses
                    self.external_program_manager.resume_curses()
                    
                    if result.returncode == 0:
                        print(f"Opened file: {selected_file.name}")
                    else:
                        print(f"Program exited with code {result.returncode}")
                    
                    self.needs_full_redraw = True
                    
                except Exception as e:
                    # Resume curses even if there's an error
                    self.external_program_manager.resume_curses()
                    print(f"Error opening file: {e}")
                    self.needs_full_redraw = True
            elif is_text_file(selected_file):
                # Fallback to text viewer for text files without association
                self.renderer.set_cursor_visibility(False)
                
                if view_text_file(self.renderer, selected_file):
                    print(f"Viewed file: {selected_file.name}")
                else:
                    self.show_info(f"File: {selected_file.name}")
                
                self.needs_full_redraw = True
            else:
                # For files without association, show file info
                self.show_info(f"File: {selected_file.name}")
            
    def show_error(self, message):
        """Show error message"""
        height, width = self.renderer.get_dimensions()
        error_color_pair, error_attributes = get_error_color()
        self.renderer.draw_text(height - 1, 2, f"ERROR: {message}", color_pair=error_color_pair, attributes=error_attributes)
        self.renderer.refresh()
        import time
        time.sleep(2.0)  # Show for 2 seconds
        
    def show_info(self, message):
        """Show info message"""
        height, width = self.renderer.get_dimensions()
        self.renderer.draw_text(height - 1, 2, message)
        self.renderer.refresh()
        import time
        time.sleep(1.5)  # Show for 1.5 seconds
        
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
        height, width = self.renderer.get_dimensions()
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
        
        # Check if this storage implementation supports directory renaming
        try:
            if selected_file.is_dir() and not selected_file.supports_directory_rename():
                print("Directory renaming is not supported on this storage type due to performance and cost considerations")
                return
        except Exception as e:
            # Handle any errors gracefully and continue
            print(f"Warning: Could not check directory rename capability: {e}")
        
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
        
        # Check if current directory is writable (only for local paths)
        if current_pane['path'].get_scheme() == 'file' and not os.access(current_pane['path'], os.W_OK):
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
            
            # Invalidate cache for the new directory
            self.cache_manager.invalidate_cache_for_create_operation(new_dir_path)
            
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
        
        # Check if current directory is writable (only for local paths)
        if current_pane['path'].get_scheme() == 'file' and not os.access(current_pane['path'], os.W_OK):
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
            
            # Invalidate cache for the new file
            self.cache_manager.invalidate_cache_for_create_operation(new_file_path)
            
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
                # Store callback before exiting mode
                callback = self.quick_choice_bar.callback
                # Exit quick choice mode first to allow new dialogs to be shown
                self.exit_quick_choice_mode()
                # Then execute the callback
                if callback:
                    callback(data)
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
    
    def _check_dialog_content_changed(self):
        """Check if any active dialog content has changed and needs redraw"""
        if self.general_dialog.is_active:
            return self.general_dialog.needs_redraw()
        elif self.list_dialog.is_active:
            return self.list_dialog.needs_redraw()
        elif self.info_dialog.is_active:
            return self.info_dialog.needs_redraw()
        elif self.search_dialog.is_active:
            return self.search_dialog.needs_redraw()
        elif self.jump_dialog.is_active:
            return self.jump_dialog.needs_redraw()
        elif self.drives_dialog.is_active:
            return self.drives_dialog.needs_redraw()
        elif self.batch_rename_dialog.is_active:
            return self.batch_rename_dialog.needs_redraw()
        return False
    

    def _draw_dialogs_if_needed(self):
        """Draw dialog overlays if content has changed or full redraw is needed. Returns True if any dialog was drawn."""
        dialog_drawn = False
        dialog_content_changed = self._check_dialog_content_changed()
        
        if dialog_content_changed or self.needs_full_redraw:
            if self.general_dialog.is_active:
                self.general_dialog.draw()
                dialog_drawn = True
            elif self.list_dialog.is_active:
                self.list_dialog.draw()
                dialog_drawn = True
            elif self.info_dialog.is_active:
                self.info_dialog.draw()
                dialog_drawn = True
            elif self.search_dialog.is_active:
                self.search_dialog.draw()
                dialog_drawn = True
            elif self.jump_dialog.is_active:
                self.jump_dialog.draw()
                dialog_drawn = True
            elif self.drives_dialog.is_active:
                self.drives_dialog.draw()
                dialog_drawn = True
            elif self.batch_rename_dialog.is_active:
                self.batch_rename_dialog.draw()
                dialog_drawn = True
            
            
        # Refresh screen if dialog was drawn or full redraw occurred
        if dialog_drawn or self.needs_full_redraw:
            self.renderer.refresh()
            
        return dialog_drawn

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
        if self.list_dialog.is_active:
            self.list_dialog.draw()
        elif self.info_dialog.is_active:
            self.info_dialog.draw()
        elif self.search_dialog.is_active:
            self.search_dialog.draw()
        elif self.jump_dialog.is_active:
            self.jump_dialog.draw()
        elif self.drives_dialog.is_active:
            self.drives_dialog.draw()
        elif self.batch_rename_dialog.is_active:
            self.batch_rename_dialog.draw()
        
        # Refresh screen immediately
        self.renderer.refresh()
        self.needs_full_redraw = False
        self.needs_dialog_redraw = False

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
        was_active = self.info_dialog.is_active
        if self.info_dialog.handle_input(key):
            # If dialog was active but is no longer active, it exited - need full redraw
            if was_active and not self.info_dialog.is_active:
                self.needs_full_redraw = True
            return True
        return False
    
    def handle_list_dialog_input(self, key):
        """Handle input while in list dialog mode - wrapper for list dialog component"""
        was_active = self.list_dialog.is_active
        if self.list_dialog.handle_input(key):
            # If dialog was active but is no longer active, it exited - need full redraw
            if was_active and not self.list_dialog.is_active:
                self.needs_full_redraw = True
            return True
        return False

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
    
    def show_history(self):
        """Show history with TAB switching between left and right pane histories"""
        current_pane = self.get_current_pane()
        initial_pane_name = 'left' if current_pane is self.pane_manager.left_pane else 'right'
        
        # Start with the current pane's history
        self._show_history_for_pane(initial_pane_name)
    
    def _show_history_for_pane(self, pane_name):
        """Show history for a specific pane with TAB switching support"""
        # Get history for the specified pane
        history = self.state_manager.get_ordered_pane_history(pane_name)
        
        # Extract just the paths (no timestamps or filenames needed in dialog)
        history_paths = []
        seen_paths = set()
        
        if history:
            # Reverse to show most recent first, and deduplicate
            for entry in reversed(history):
                path = entry['path']
                if path not in seen_paths:
                    history_paths.append(path)
                    seen_paths.add(path)
        
        # If no history, show empty list with message
        if not history_paths:
            history_paths = [f"No history available for {pane_name} pane"]
        
        # Create callback function to handle selection
        def on_history_selected(selected_path):
            if selected_path and not selected_path.startswith("No history available"):
                self.navigate_to_history_path(selected_path)
        
        # Create custom key handler for TAB switching
        def handle_custom_keys(key):
            if key == 9:  # TAB key
                # Switch to the other pane's history
                other_pane = 'right' if pane_name == 'left' else 'left'
                # Exit current dialog and show the other pane's history
                self.list_dialog.exit()
                self._show_history_for_pane(other_pane)
                self.needs_full_redraw = True
                self._force_immediate_redraw()
                return True
            return False
        
        # Show the list dialog with TAB switching support
        title = f"History - {pane_name.title()}"
        other_pane_name = 'Right' if pane_name == 'left' else 'Left'
        help_text = f"↑↓:select  Enter:choose  TAB:switch to {other_pane_name}  Type:search  ESC:cancel"
        self.list_dialog.show(title, history_paths, on_history_selected, handle_custom_keys, help_text)
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def navigate_to_history_path(self, selected_path):
        """Navigate the current pane to the selected history path"""
        try:
            target_path = Path(selected_path)
            
            # Check if the path still exists
            if not target_path.exists():
                print(f"Directory no longer exists: {selected_path}")
                return
            
            if not target_path.is_dir():
                print(f"Path is not a directory: {selected_path}")
                return
            
            # Get current pane and save cursor position before navigating
            current_pane = self.get_current_pane()
            self.pane_manager.save_cursor_position(current_pane)
            
            # Navigate to the selected path
            old_path = current_pane['path']
            current_pane['path'] = target_path
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()  # Clear selections when changing directory
            
            # Refresh files and restore cursor position for the new directory
            self.refresh_files(current_pane)
            
            # Try to restore cursor position for this directory
            height, width = self.renderer.get_dimensions()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            restored = self.pane_manager.restore_cursor_position(current_pane, display_height)
            
            # Log the navigation
            pane_name = "left" if current_pane is self.pane_manager.left_pane else "right"
            if restored and current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']].name
                print(f"Navigated {pane_name} pane: {old_path} → {target_path} (cursor: {selected_file})")
            else:
                print(f"Navigated {pane_name} pane: {old_path} → {target_path}")
            
            self.needs_full_redraw = True
            
        except Exception as e:
            print(f"Error navigating to {selected_path}: {e}")
    
    def show_programs_dialog(self):
        """Show external programs using the searchable list dialog"""
        def execute_program_wrapper(program):
            self.external_program_manager.execute_external_program(
                self.pane_manager, program
            )
            self.needs_full_redraw = True
        
        ListDialogHelpers.show_programs_dialog(
            self.list_dialog, execute_program_wrapper, print
        )
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def show_compare_selection_dialog(self):
        """Show compare selection dialog to select files and directories based on comparison with other pane"""
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
                init_colors(self.renderer, new_scheme)
                print(f"Switched to {new_scheme} color scheme")
                self.print_color_scheme_info()
                # Clear screen to apply new background color immediately
                self.clear_screen_with_background()
                self.needs_full_redraw = True
                
            elif option == "Toggle fallback color scheme":
                from tfm_colors import toggle_fallback_mode, init_colors, is_fallback_mode, get_current_color_scheme
                new_state = toggle_fallback_mode()
                # Re-initialize colors with current scheme
                color_scheme = get_current_color_scheme()
                init_colors(self.renderer, color_scheme)
                status = "enabled" if new_state else "disabled"
                print(f"Fallback color mode: {status}")
                # Clear screen to apply new background color immediately
                self.clear_screen_with_background()
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
                    self.external_program_manager.suspend_curses()
                    
                    # Launch the text editor as a subprocess
                    result = subprocess.run([editor, config_path])
                    
                    # Resume curses
                    self.external_program_manager.resume_curses()
                    
                    if result.returncode == 0:
                        print(f"Edited config file: {config_path}")
                    else:
                        print(f"Editor exited with code {result.returncode}")
                    
                    self.needs_full_redraw = True
                    
                except FileNotFoundError:
                    # Resume curses even if editor not found
                    self.external_program_manager.resume_curses()
                    print(f"Text editor '{editor}' not found. Please install it or configure a different editor.")
                    print("You can manually edit the file at: " + config_path)
                except Exception as e:
                    # Resume curses even if there's an error
                    self.external_program_manager.resume_curses()
                    print(f"Error opening config file: {e}")
                    print("You can manually edit the file at: " + config_path)
                
            elif option == "Reload config.py":
                try:
                    # Reload the configuration
                    from tfm_config import get_config
                    # Force reload by clearing any cached config
                    import tfm_config
                    importlib.reload(tfm_config)
                    
                    # Get the new config
                    old_config = self.config
                    self.config = get_config()
                    
                    # Apply any config changes that need immediate effect
                    if hasattr(self.config, 'COLOR_SCHEME'):
                        from tfm_colors import init_colors
                        init_colors(self.renderer, self.config.COLOR_SCHEME)
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
                except (OSError, ValueError) as e:
                    print(f"Warning: Could not process selected file path '{file_path_str}': {e}")
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
        from tfm_colors import toggle_fallback_mode, init_colors, is_fallback_mode, get_current_color_scheme
        
        # Toggle the fallback mode
        fallback_enabled = toggle_fallback_mode()
        
        # Reinitialize colors with the new mode
        color_scheme = get_current_color_scheme()
        init_colors(self.renderer, color_scheme)
        
        # Log the change
        mode_text = "enabled" if fallback_enabled else "disabled"
        print(f"Fallback color mode {mode_text}")
        
        # Print detailed color scheme info to log
        self.print_color_scheme_info()
        # Clear screen to apply new background color immediately
        self.clear_screen_with_background()
        self.needs_full_redraw = True
    
    def show_help_dialog(self):
        """Show help dialog with key bindings and usage information"""
        InfoDialogHelpers.show_help_dialog(self.info_dialog)
        self.needs_full_redraw = True
        self._force_immediate_redraw()
    
    def view_selected_file(self):
        """View the selected file using configured viewer from file associations"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            print("No files to view")
            return
        
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        if selected_file.is_dir():
            print("Cannot view directory")
            return
        
        # Try to use file association for 'view' action
        filename = selected_file.name
        command = get_program_for_file(filename, 'view')
        
        if command:
            # Use configured program from file associations
            try:
                # Suspend curses
                self.external_program_manager.suspend_curses()
                
                # Launch the viewer
                result = subprocess.run(command + [str(selected_file)], 
                                      cwd=str(current_pane['path']))
                
                # Resume curses
                self.external_program_manager.resume_curses()
                
                if result.returncode == 0:
                    print(f"Viewed file: {selected_file.name}")
                else:
                    print(f"Viewer exited with code {result.returncode}")
                
                self.needs_full_redraw = True
                
            except Exception as e:
                # Resume curses even if there's an error
                self.external_program_manager.resume_curses()
                print(f"Error viewing file: {e}")
                self.needs_full_redraw = True
        else:
            # No file association found - check if it's a text file
            if is_text_file(selected_file):
                # Fallback to built-in text viewer for text files
                try:
                    self.renderer.set_cursor_visibility(False)
                    
                    if view_text_file(self.renderer, selected_file):
                        print(f"Viewed text file: {selected_file.name}")
                    else:
                        print(f"Failed to view file: {selected_file.name}")
                    
                    self.needs_full_redraw = True
                    
                except Exception as e:
                    print(f"Error viewing file: {str(e)}")
                    self.needs_full_redraw = True
            else:
                # Not a text file and no viewer configured
                print(f"No viewer configured for '{selected_file.name}' (not a text file)")
    
    def edit_selected_file(self):
        """Edit the selected file using configured editor from file associations"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            print("No files in current directory")
            return
            
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        # Check if file editing is supported for this storage type
        if not selected_file.supports_file_editing():
            print("Editing S3 files is not supported for now")
            return
        
        # Allow editing directories (some editors can handle them)
        if selected_file.is_dir():
            print(f"Warning: '{selected_file.name}' is a directory")
        
        # Try to use file association for 'edit' action
        filename = selected_file.name
        command = get_program_for_file(filename, 'edit')
        
        if command:
            # Use configured program from file associations
            try:
                # Suspend curses
                self.external_program_manager.suspend_curses()
                
                # Launch the editor
                result = subprocess.run(command + [str(selected_file)], 
                                      cwd=str(current_pane['path']))
                
                # Resume curses
                self.external_program_manager.resume_curses()
                
                if result.returncode == 0:
                    print(f"Edited file: {selected_file.name}")
                else:
                    print(f"Editor exited with code {result.returncode}")
                    
            except FileNotFoundError:
                # Resume curses even if editor not found
                self.external_program_manager.resume_curses()
                print(f"Editor not found. Please check your file associations configuration.")
            except Exception as e:
                # Resume curses even if there's an error
                self.external_program_manager.resume_curses()
                print(f"Error launching editor: {e}")
        else:
            # Fallback to TEXT_EDITOR config for files without association
            editor = getattr(self.config, 'TEXT_EDITOR', DEFAULT_TEXT_EDITOR)
            
            try:
                # Suspend curses
                self.external_program_manager.suspend_curses()
                
                # Launch the text editor
                result = subprocess.run([editor, str(selected_file)], 
                                      cwd=str(current_pane['path']))
                
                # Resume curses
                self.external_program_manager.resume_curses()
                
                if result.returncode == 0:
                    print(f"Edited file: {selected_file.name}")
                else:
                    print(f"Editor exited with code {result.returncode}")
                    
            except FileNotFoundError:
                # Resume curses even if editor not found
                self.external_program_manager.resume_curses()
                print(f"Text editor '{editor}' not found. Please install it or configure a different editor.")
            except Exception as e:
                # Resume curses even if there's an error
                self.external_program_manager.resume_curses()
                print(f"Error launching editor: {e}")
    
    def copy_selected_files(self):
        """Copy selected files to the opposite pane's directory - delegated to FileOperationsUI"""
        self.file_operations_ui.copy_selected_files()
    
    def copy_files_to_directory(self, files_to_copy, destination_dir):
        """Copy files to directory - delegated to FileOperationsUI"""
        self.file_operations_ui.copy_files_to_directory(files_to_copy, destination_dir)
    
    def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):
        """Perform copy operation - delegated to FileOperationsUI"""
        self.file_operations_ui.perform_copy_operation(files_to_copy, destination_dir, overwrite)
    
    # Legacy helper method - functionality moved to FileOperationsUI
    def _copy_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
        """Copy directory with progress - delegated to FileOperationsUI"""
        return self.file_operations_ui._copy_directory_with_progress(source_dir, dest_dir, processed_files, total_files)
    
    def move_selected_files(self):
        """Move selected files to the opposite pane's directory - delegated to FileOperationsUI"""
        self.file_operations_ui.move_selected_files()
    
    def move_files_to_directory(self, files_to_move, destination_dir):
        """Move files to directory - delegated to FileOperationsUI"""
        self.file_operations_ui.move_files_to_directory(files_to_move, destination_dir)
    
    def perform_move_operation(self, files_to_move, destination_dir, overwrite=False):
        """Perform move operation - delegated to FileOperationsUI"""
        self.file_operations_ui.perform_move_operation(files_to_move, destination_dir, overwrite)
    
    # Legacy move operation methods - functionality moved to FileOperationsUI
    
    def delete_selected_files(self):
        """Delete selected files or current file with confirmation - delegated to FileOperationsUI"""
        self.file_operations_ui.delete_selected_files()
    
    def perform_delete_operation(self, files_to_delete):
        """Perform delete operation - delegated to FileOperationsUI"""
        self.file_operations_ui.perform_delete_operation(files_to_delete)
    
    # Legacy file operation methods - functionality moved to FileOperationsUI
    
    def enter_create_archive_mode(self):
        """Enter archive creation mode - delegated to ArchiveUI"""
        self.archive_ui.enter_create_archive_mode()
    
    def on_create_archive_confirm(self, archive_name):
        """Handle create archive confirmation - delegated to ArchiveUI"""
        self.archive_ui.on_create_archive_confirm(archive_name)
    
    def on_create_archive_cancel(self):
        """Handle create archive cancellation - delegated to ArchiveUI"""
        self.archive_ui.on_create_archive_cancel()
    
    # Legacy method - no longer used with new UI approach
    def perform_create_archive(self):
        """Create the archive file - legacy method, functionality moved to ArchiveUI"""
        print("Legacy archive creation method called - this should not happen")
        pass
    
    def _progress_callback(self, progress_data):
        """Callback for progress manager updates"""
        # Force a screen refresh to show progress
        try:
            self.draw_status()
            self.renderer.refresh()
        except Exception as e:
            print(f"Warning: Progress callback display update failed: {e}")
    
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
    
    # Legacy methods - delegated to ArchiveUI for backward compatibility
    def detect_archive_format(self, filename):
        """Detect archive format from filename extension - delegated to ArchiveUI"""
        return self.archive_ui.detect_archive_format(filename)
    
    # Legacy methods - functionality moved to ArchiveOperations class
    def create_zip_archive(self, archive_path, files_to_archive):
        """Create a ZIP archive - legacy method, functionality moved to ArchiveOperations"""
        print("Legacy ZIP creation method called - this should not happen")
        pass
    
    def create_tar_archive(self, archive_path, files_to_archive):
        """Create a TAR.GZ archive - legacy method, functionality moved to ArchiveOperations"""
        print("Legacy TAR creation method called - this should not happen")
        pass
    
    def extract_selected_archive(self):
        """Extract the selected archive file to the other pane - delegated to ArchiveUI"""
        self.archive_ui.extract_selected_archive()
    
    # Legacy methods - delegated to ArchiveUI for backward compatibility
    def get_archive_basename(self, filename):
        """Get the base name of an archive file - delegated to ArchiveUI"""
        return self.archive_ui.get_archive_basename(filename)
    
    # Legacy extraction methods - functionality moved to ArchiveUI and ArchiveOperations
    def perform_extraction(self, archive_file, extract_dir, archive_format, other_pane):
        """Perform extraction - legacy method, functionality moved to ArchiveUI"""
        print("Legacy extraction method called - this should not happen")
        pass
    
    def extract_zip_archive(self, archive_file, extract_dir):
        """Extract ZIP archive - legacy method, functionality moved to ArchiveOperations"""
        print("Legacy ZIP extraction method called - this should not happen")
        pass
    
    def extract_tar_archive(self, archive_file, extract_dir):
        """Extract TAR archive - legacy method, functionality moved to ArchiveOperations"""
        print("Legacy TAR extraction method called - this should not happen")
        pass
        
    def handle_isearch_input(self, event):
        """Handle input while in isearch mode"""
        if event.key_code == KeyCode.ESCAPE:
            # ESC - exit isearch mode
            self.exit_isearch_mode()
            return True
        elif event.key_code == KeyCode.ENTER:
            # Enter - exit isearch mode and keep current position
            self.exit_isearch_mode()
            return True
        elif event.key_code == KeyCode.BACKSPACE:
            # Backspace - remove last character
            if self.isearch_pattern:
                self.isearch_pattern = self.isearch_pattern[:-1]
                self.update_isearch_matches()
                self.needs_full_redraw = True
            return True
        elif event.key_code == KeyCode.UP:
            # Up arrow - go to previous match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index - 1) % len(self.isearch_matches)
                current_pane = self.get_current_pane()
                current_pane['selected_index'] = self.isearch_matches[self.isearch_match_index]
                self.needs_full_redraw = True
            return True
        elif event.key_code == KeyCode.DOWN:
            # Down arrow - go to next match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index + 1) % len(self.isearch_matches)
                current_pane = self.get_current_pane()
                current_pane['selected_index'] = self.isearch_matches[self.isearch_match_index]
                self.needs_full_redraw = True
            return True
        elif event.is_printable():
            # Add character to isearch pattern
            self.isearch_pattern += event.char
            self.update_isearch_matches()
            self.needs_full_redraw = True
            return True
        
        # In isearch mode, capture most other keys to prevent unintended actions
        # Only allow specific keys that make sense during isearch
        return True

    def get_batch_rename_active_editor(self):
        """Get the currently active editor in batch rename mode"""
        return self.batch_rename_dialog.get_active_editor()
    
    def switch_batch_rename_field(self, field):
        """Switch the active field in batch rename mode"""
        self.batch_rename_dialog.switch_field(field)
        self.needs_full_redraw = True
    
    def handle_batch_rename_input(self, key):
        """Handle input while in batch rename mode - wrapper for batch rename dialog component"""
        was_active = self.batch_rename_dialog.is_active
        result = self.batch_rename_dialog.handle_input(key)
        
        if result == True:
            # If dialog was active but is no longer active, it exited - need full redraw
            if was_active and not self.batch_rename_dialog.is_active:
                self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'cancel':
                print("Batch rename cancelled")
                self.exit_batch_rename_mode()
                return True
            elif action == 'field_switch':
                return True
            elif action == 'scroll':
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
        was_active = self.search_dialog.is_active
        result = self.search_dialog.handle_input(key)
        
        if result == True:
            # If dialog was active but is no longer active, it exited - need full redraw
            if was_active and not self.search_dialog.is_active:
                self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'search':
                self.perform_search()
                return True
            elif action == 'navigate':
                if data:
                    self._navigate_to_search_result(data)
                    
                # Save search term to history if it's not empty
                search_term = self.search_dialog.text_editor.text.strip()
                if search_term:
                    self.add_search_to_history(search_term)
                    
                self.exit_search_dialog_mode()
                return True
        
        return False

    def _navigate_to_search_result(self, result):
        """Navigate to the selected search result - wrapper for search dialog helper"""
        SearchDialogHelpers.navigate_to_result(result, self.pane_manager, self.file_operations, print)
        
        # Adjust scroll with proper display height
        current_pane = self.get_current_pane()
        height, width = self.renderer.get_dimensions()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        
        SearchDialogHelpers.adjust_scroll_for_display_height(current_pane, display_height)
        # needs_full_redraw will be set when dialog exits

    def show_jump_dialog(self):
        """Show the jump dialog - wrapper for jump dialog component"""
        current_pane = self.get_current_pane()
        root_directory = current_pane['path']
        self.jump_dialog.show(root_directory, self.file_operations)
        
        # Force immediate redraw to show dialog
        self._force_immediate_redraw()
    
    def exit_jump_dialog_mode(self):
        """Exit jump dialog mode - wrapper for jump dialog component"""
        self.jump_dialog.exit()
        self.needs_full_redraw = True
    
    def show_drives_dialog(self):
        """Show the drives dialog - wrapper for drives dialog component"""
        self.drives_dialog.show()
        self._force_immediate_redraw()
    
    def exit_drives_dialog_mode(self):
        """Exit drives dialog mode - wrapper for drives dialog component"""
        self.drives_dialog.exit()
        self.needs_full_redraw = True
    
    def handle_jump_dialog_input(self, key):
        """Handle input while in jump dialog mode - wrapper for jump dialog component"""
        was_active = self.jump_dialog.is_active
        result = self.jump_dialog.handle_input(key)
        
        if result == True:
            # If dialog was active but is no longer active, it exited - need full redraw
            if was_active and not self.jump_dialog.is_active:
                self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'navigate':
                if data:
                    JumpDialogHelpers.navigate_to_directory(data, self.pane_manager, print)
                    
                self.exit_jump_dialog_mode()
                return True
        
        return False
    
    def handle_drives_dialog_input(self, key):
        """Handle input while in drives dialog mode - wrapper for drives dialog component"""
        was_active = self.drives_dialog.is_active
        result = self.drives_dialog.handle_input(key)
        
        if result == True:
            # If dialog was active but is no longer active, it exited - need full redraw
            if was_active and not self.drives_dialog.is_active:
                self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'navigate':
                if data:
                    DrivesDialogHelpers.navigate_to_drive(data, self.pane_manager, print)
                    
                self.exit_drives_dialog_mode()
                return True
        
        return False

    def handle_key_input(self, event):
        """Handle input event and return True if the event was processed"""
        current_pane = self.get_current_pane()
        
        # Handle isearch mode input first
        if self.isearch_mode:
            if self.handle_isearch_input(event):
                return True  # Isearch mode handled the event
        
        # Handle general dialog input
        if self.general_dialog.is_active:
            if self.general_dialog.handle_input(event):
                return True  # General dialog handled the event
        
        # Handle quick choice mode input
        if self.quick_choice_bar.is_active:
            if self.handle_quick_choice_input(event):
                return True  # Quick choice mode handled the event
        
        # Handle info dialog mode input
        if self.info_dialog.is_active:
            if self.handle_info_dialog_input(event):
                return True  # Info dialog mode handled the event
        
        # Handle list dialog mode input
        if self.list_dialog.is_active:
            if self.handle_list_dialog_input(event):
                return True  # List dialog mode handled the event
        
        # Handle search dialog mode input
        if self.search_dialog.is_active:
            if self.handle_search_dialog_input(event):
                return True  # Search dialog mode handled the event
        
        # Handle jump dialog mode input
        if self.jump_dialog.is_active:
            if self.handle_jump_dialog_input(event):
                return True  # Jump dialog mode handled the event
        
        # Handle drives dialog mode input
        if self.drives_dialog.is_active:
            if self.handle_drives_dialog_input(event):
                return True  # Drives dialog mode handled the event
        
        # Handle batch rename dialog mode input
        if self.batch_rename_dialog.is_active:
            if self.handle_batch_rename_input(event):
                return True  # Batch rename mode handled the event
        
        # Skip regular key processing if any dialog is open
        # This prevents conflicts like starting isearch mode while help dialog is open
        if (self.quick_choice_bar.is_active or self.info_dialog.is_active or self.list_dialog.is_active or 
            self.search_dialog.is_active or self.jump_dialog.is_active or self.drives_dialog.is_active or 
            self.batch_rename_dialog.is_active or self.isearch_mode or self.general_dialog.is_active):
            return True
        
        # Handle main application keys
        if self.is_key_for_action(event, 'quit'):
            def quit_callback(confirmed):
                if confirmed:
                    # Set a flag to exit the main loop
                    self.should_quit = True
            
            # Check if quit confirmation is enabled
            if getattr(self.config, 'CONFIRM_QUIT', True):
                self.show_confirmation("Are you sure you want to quit TFM?", quit_callback)
            else:
                quit_callback(True)


        elif event.key_code == KeyCode.TAB:  # Tab key - switch panes
            self.pane_manager.active_pane = 'right' if self.pane_manager.active_pane == 'left' else 'left'
            self.needs_full_redraw = True
        elif event.key_code == KeyCode.UP:
            if current_pane['selected_index'] > 0:
                current_pane['selected_index'] -= 1
                self.needs_full_redraw = True
        elif event.key_code == KeyCode.DOWN:
            if current_pane['selected_index'] < len(current_pane['files']) - 1:
                current_pane['selected_index'] += 1
                self.needs_full_redraw = True
        elif event.key_code == KeyCode.ENTER:
            self.handle_enter()
            self.needs_full_redraw = True
        elif self.is_key_for_action(event, 'toggle_hidden'):
            self.file_operations.toggle_hidden_files()
            # Reset both panes
            self.pane_manager.left_pane['selected_index'] = 0
            self.pane_manager.left_pane['scroll_offset'] = 0
            self.pane_manager.right_pane['selected_index'] = 0
            self.pane_manager.right_pane['scroll_offset'] = 0
            self.needs_full_redraw = True
        elif self.is_key_for_action(event, 'toggle_color_scheme'):
            # Toggle between dark and light color schemes
            new_scheme = toggle_color_scheme()
            # Reinitialize colors with the new scheme
            init_colors(self.renderer, new_scheme)
            print(f"Switched to {new_scheme} color scheme")
            # Print detailed color scheme info to log
            self.print_color_scheme_info()
            # Clear screen to apply new background color immediately
            self.clear_screen_with_background()
            self.needs_full_redraw = True
        elif self.is_key_for_action(event, 'select_all'):
            self.select_all()
        elif self.is_key_for_action(event, 'unselect_all'):
            self.unselect_all()
        elif event.key_code == KeyCode.PAGE_UP:  # Page Up - file navigation only
            current_pane['selected_index'] = max(0, current_pane['selected_index'] - 10)
            self.needs_full_redraw = True
        elif event.key_code == KeyCode.PAGE_DOWN:  # Page Down - file navigation only
            current_pane['selected_index'] = min(len(current_pane['files']) - 1, current_pane['selected_index'] + 10)
            self.needs_full_redraw = True
        elif event.key_code == KeyCode.BACKSPACE:  # Backspace - go to parent directory
            # Check if we're at the root of an archive
            current_path_str = str(current_pane['path'])
            if current_path_str.startswith('archive://') and current_path_str.endswith('#'):
                # We're at the root of an archive, exit to the filesystem directory containing the archive
                try:
                    # Save current cursor position before exiting archive
                    self.save_cursor_position(current_pane)
                    
                    # Extract the archive file path from the URI
                    # Format: archive:///path/to/archive.zip#
                    archive_path_part = current_path_str[10:-1]  # Remove 'archive://' and trailing '#'
                    archive_file_path = Path(archive_path_part)
                    
                    # Get the directory containing the archive
                    parent_dir = archive_file_path.parent
                    archive_filename = archive_file_path.name
                    
                    # Navigate to the parent directory
                    current_pane['path'] = parent_dir
                    current_pane['selected_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()
                    self.refresh_files(current_pane)
                    
                    # Try to set cursor to the archive file we just exited
                    cursor_set = False
                    for i, file_path in enumerate(current_pane['files']):
                        if file_path.name == archive_filename:
                            current_pane['selected_index'] = i
                            self.adjust_scroll_for_selection(current_pane)
                            cursor_set = True
                            break
                    
                    if not cursor_set:
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                    
                    self.needs_full_redraw = True
                    self.log_manager.add_message("INFO", f"Exited archive: {archive_filename}")
                except Exception as e:
                    self.show_error(f"Error exiting archive: {e}")
                    self.log_manager.add_message("ERROR", f"Error exiting archive: {e}")
                    self.needs_full_redraw = True
            elif current_pane['path'] != current_pane['path'].parent:
                try:
                    # Save current cursor position before changing directory
                    self.save_cursor_position(current_pane)
                    
                    # Remember the child directory name we're leaving
                    child_directory_name = current_pane['path'].name
                    
                    current_pane['path'] = current_pane['path'].parent
                    current_pane['selected_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()  # Clear selections when changing directory
                    self.refresh_files(current_pane)
                    
                    # Try to set cursor to the child directory we just came from
                    cursor_set = False
                    for i, file_path in enumerate(current_pane['files']):
                        if file_path.name == child_directory_name and file_path.is_dir():
                            current_pane['selected_index'] = i
                            # Adjust scroll offset to keep selection visible
                            self.adjust_scroll_for_selection(current_pane)
                            cursor_set = True
                            break
                    
                    # If we couldn't find the child directory, try to restore cursor position from history
                    if not cursor_set and not self.restore_cursor_position(current_pane):
                        # If no history found, default to first item
                        current_pane['selected_index'] = 0
                        current_pane['scroll_offset'] = 0
                    
                    self.needs_full_redraw = True
                except PermissionError:
                    self.show_error("Permission denied")
                    self.needs_full_redraw = True
        elif event.key_code == KeyCode.LEFT and self.pane_manager.active_pane == 'left':  # Left arrow in left pane - go to parent
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
        elif event.key_code == KeyCode.RIGHT and self.pane_manager.active_pane == 'right':  # Right arrow in right pane - go to parent
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
        elif event.key_code == KeyCode.RIGHT and self.pane_manager.active_pane == 'left':  # Right arrow in left pane - switch to right pane
            self.pane_manager.active_pane = 'right'
            self.needs_full_redraw = True
        elif event.key_code == KeyCode.LEFT and self.pane_manager.active_pane == 'right':  # Left arrow in right pane - switch to left pane
            self.pane_manager.active_pane = 'left'
            self.needs_full_redraw = True
        elif event.key_code in (KEY_SHIFT_UP_1, KEY_SHIFT_UP_2):  # Shift+Up
            if self.log_manager.scroll_log_up(1):
                self.needs_full_redraw = True
        elif event.key_code in (KEY_SHIFT_DOWN_1, KEY_SHIFT_DOWN_2):  # Shift+Down
            if self.log_manager.scroll_log_down(1):
                self.needs_full_redraw = True
        elif event.key_code in (KEY_SHIFT_LEFT_1, KEY_SHIFT_LEFT_2):  # Shift+Left - fast scroll to older messages
            log_height = self._get_log_pane_height()
            if self.log_manager.scroll_log_up(max(1, log_height)):
                self.needs_full_redraw = True
        elif event.key_code in (KEY_SHIFT_RIGHT_1, KEY_SHIFT_RIGHT_2):  # Shift+Right - fast scroll to newer messages
            log_height = self._get_log_pane_height()
            if self.log_manager.scroll_log_down(max(1, log_height)):
                self.needs_full_redraw = True
        elif self.is_key_for_action(event, 'select_file'):  # Toggle file selection
            self.toggle_selection()
            self.needs_full_redraw = True
        elif event.key_code == KeyCode.ESCAPE:  # ESC key - check for Option key sequences
            # Option+Space sends ESC followed by another key
            next_event = self.renderer.get_input(timeout_ms=100)
            if next_event:
                # Log unknown ESC sequence for debugging
                print(f"Unknown ESC sequence: ESC, {next_event.key_code}")
        elif self.is_key_for_action(event, 'select_all_files'):  # Toggle all files selection
            self.toggle_all_files_selection()
        elif self.is_key_for_action(event, 'select_all_items'):  # Toggle all items selection
            self.toggle_all_items_selection()
        elif self.is_key_for_action(event, 'sync_current_to_other'):  # Sync current pane to other
            self.sync_current_to_other()
        elif self.is_key_for_action(event, 'sync_other_to_current'):  # Sync other pane to current
            self.sync_other_to_current()
        elif self.is_key_for_action(event, 'search_dialog'):  # Show search dialog (filename)
            self.show_search_dialog('filename')
        elif self.is_key_for_action(event, 'jump_dialog'):  # Show jump dialog (Shift+J)
            self.show_jump_dialog()
        elif self.is_key_for_action(event, 'drives_dialog'):  # Show drives dialog
            self.show_drives_dialog()
        elif self.is_key_for_action(event, 'search_content'):  # Show search dialog (content)
            self.show_search_dialog('content')
        elif self.is_key_for_action(event, 'edit_file'):  # Edit existing file
            self.edit_selected_file()
        elif self.is_key_for_action(event, 'create_file'):  # Create new file
            self.enter_create_file_mode()
        elif self.is_key_for_action(event, 'create_directory'):  # Create new directory
            self.enter_create_directory_mode()
        elif self.is_key_for_action(event, 'toggle_fallback_colors'):  # Toggle fallback color mode
            self.toggle_fallback_color_mode()
        elif self.is_key_for_action(event, 'view_options'):  # Show view options
            self.show_view_options()
        elif self.is_key_for_action(event, 'settings_menu'):  # Show settings menu
            self.show_settings_menu()
        elif self.is_key_for_action(event, 'search'):  # Search key - enter isearch mode
            self.enter_isearch_mode()
        elif self.is_key_for_action(event, 'filter'):  # Filter key - enter filter mode
            self.enter_filter_mode()
        elif self.is_key_for_action(event, 'clear_filter'):  # Clear filter key
            self.clear_filter()
        elif self.is_key_for_action(event, 'sort_menu'):  # Sort menu
            self.show_sort_menu()
        elif self.is_key_for_action(event, 'quick_sort_name'):  # Quick sort by name
            self.quick_sort('name')
        elif self.is_key_for_action(event, 'quick_sort_size'):  # Quick sort by size
            self.quick_sort('size')
        elif self.is_key_for_action(event, 'quick_sort_date'):  # Quick sort by date
            self.quick_sort('date')
        elif self.is_key_for_action(event, 'quick_sort_ext'):  # Quick sort by extension
            self.quick_sort('ext')
        elif self.is_key_for_action(event, 'file_details'):  # Show file details
            self.show_file_details()
        elif self.is_key_for_action(event, 'view_file'):  # View file
            self.view_selected_file()
        elif self.is_key_for_action(event, 'copy_files'):  # Copy selected files
            self.copy_selected_files()
        elif self.is_key_for_action(event, 'move_files'):  # Move selected files
            self.move_selected_files()
        elif self.is_key_for_action(event, 'delete_files'):  # Delete selected files
            self.delete_selected_files()
        elif self.is_key_for_action(event, 'create_archive'):  # Create archive
            self.enter_create_archive_mode()
        elif self.is_key_for_action(event, 'extract_archive'):  # Extract archive
            self.extract_selected_archive()
        elif self.is_key_for_action(event, 'rename_file'):  # Rename file
            self.enter_rename_mode()
        elif self.is_key_for_action(event, 'favorites'):  # Show favorite directories
            self.show_favorite_directories()
        elif self.is_key_for_action(event, 'history'):  # Show history
            self.show_history()
        elif self.is_key_for_action(event, 'programs'):  # Show external programs
            self.show_programs_dialog()
        elif self.is_key_for_action(event, 'compare_selection'):  # Show compare selection menu
            self.show_compare_selection_dialog()
        elif self.is_key_for_action(event, 'help'):  # Show help dialog
            self.show_help_dialog()
        elif self.is_key_for_action(event, 'adjust_pane_left'):  # Adjust pane boundary left
            self.adjust_pane_boundary('left')
        elif self.is_key_for_action(event, 'adjust_pane_right'):  # Adjust pane boundary right
            self.adjust_pane_boundary('right')
        elif self.is_key_for_action(event, 'adjust_log_up'):  # Adjust log boundary up
            self.adjust_log_boundary('down')
        elif self.is_key_for_action(event, 'adjust_log_down'):  # Adjust log boundary down
            self.adjust_log_boundary('up')
        elif self.is_key_for_action(event, 'reset_log_height'):  # Reset log pane height
            self.log_height_ratio = getattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO', 0.25)
            self.needs_full_redraw = True
            print(f"Log pane height reset to {int(self.log_height_ratio * 100)}%")
        elif event.key_code == ord('-'):  # '-' key - reset pane ratio to 50/50
            self.pane_manager.left_pane_ratio = 0.5
            self.needs_full_redraw = True
            print("Pane split reset to 50% | 50%")
        elif self.is_key_for_action(event, 'subshell'):  # Sub-shell mode
            self.external_program_manager.enter_subshell_mode(
                self.pane_manager
            )
            self.needs_full_redraw = True
        else:
            return False  # Key was not handled
        
        return True  # Key was handled

    def draw_interface(self):
        """Draw the complete interface"""
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
            self.renderer.refresh()
        
        # Draw dialogs if needed
        self._draw_dialogs_if_needed()
        
        # Reset full redraw flag after both main screen and dialogs are rendered
        if self.needs_full_redraw:
            self.needs_full_redraw = False

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
            
            # Check for log updates and trigger redraw if needed
            if self.log_manager.has_log_updates():
                self.needs_full_redraw = True
            
            # Get user input with timeout to allow timer checks
            event = self.renderer.get_input(timeout_ms=16)  # 16ms timeout
            
            # If no event was received (timeout), continue to next iteration
            if event is None:
                pass  # Continue to drawing
            elif event.key_code == KeyCode.RESIZE:  # Terminal window resized - handle at top level
                # Clear screen and trigger full redraw to handle new dimensions
                self.clear_screen_with_background()
                self.needs_full_redraw = True
            else:
                # Check if operation is in progress
                if hasattr(self, 'operation_in_progress') and self.operation_in_progress:
                    # Only allow ESC key to cancel operation
                    if event.key_code == KeyCode.ESCAPE:
                        self.operation_cancelled = True
                        print("Cancelling operation...")
                    # Ignore all other keys during operation
                else:
                    # Handle normal key input
                    self.handle_key_input(event)
            
            # Draw interface after handling input
            self.draw_interface()
        
        # Restore stdout/stderr before exiting
        self.restore_stdio()
        
        # Save application state before exiting
        self.save_application_state()
    
    def load_application_state(self):
        """Load saved application state from persistent storage."""
        try:
            # Update session heartbeat
            self.state_manager.update_session_heartbeat()
            
            # Clean up non-existing directories from history before restoring state
            self.state_manager.cleanup_non_existing_directories()
            
            # Load window layout
            layout = self.state_manager.load_window_layout()
            if layout:
                self.pane_manager.left_pane_ratio = layout.get('left_pane_ratio', 0.5)
                self.log_height_ratio = layout.get('log_height_ratio', 0.25)
                print(f"Restored window layout: panes {int(self.pane_manager.left_pane_ratio*100)}%/{int((1-self.pane_manager.left_pane_ratio)*100)}%, log {int(self.log_height_ratio*100)}%")
            
            # Load pane states
            left_state = self.state_manager.load_pane_state('left')
            if left_state and Path(left_state['path']).exists() and not self.cmdline_left_dir_provided:
                # Only restore if the directory still exists and no command line argument was provided
                self.pane_manager.left_pane['path'] = Path(left_state['path'])
                self.pane_manager.left_pane['sort_mode'] = left_state.get('sort_mode', 'name')
                self.pane_manager.left_pane['sort_reverse'] = left_state.get('sort_reverse', False)
                self.pane_manager.left_pane['filter_pattern'] = left_state.get('filter_pattern', '')
                print(f"Restored left pane: {left_state['path']}")
            elif self.cmdline_left_dir_provided:
                # Load other settings but keep command line directory
                if left_state:
                    self.pane_manager.left_pane['sort_mode'] = left_state.get('sort_mode', 'name')
                    self.pane_manager.left_pane['sort_reverse'] = left_state.get('sort_reverse', False)
                    self.pane_manager.left_pane['filter_pattern'] = left_state.get('filter_pattern', '')
                print(f"Using command line left directory: {self.pane_manager.left_pane['path']}")
            
            right_state = self.state_manager.load_pane_state('right')
            if right_state and Path(right_state['path']).exists() and not self.cmdline_right_dir_provided:
                # Only restore if the directory still exists and no command line argument was provided
                self.pane_manager.right_pane['path'] = Path(right_state['path'])
                self.pane_manager.right_pane['sort_mode'] = right_state.get('sort_mode', 'name')
                self.pane_manager.right_pane['sort_reverse'] = right_state.get('sort_reverse', False)
                self.pane_manager.right_pane['filter_pattern'] = right_state.get('filter_pattern', '')
                print(f"Restored right pane: {right_state['path']}")
            elif self.cmdline_right_dir_provided:
                # Load other settings but keep command line directory
                if right_state:
                    self.pane_manager.right_pane['sort_mode'] = right_state.get('sort_mode', 'name')
                    self.pane_manager.right_pane['sort_reverse'] = right_state.get('sort_reverse', False)
                    self.pane_manager.right_pane['filter_pattern'] = right_state.get('filter_pattern', '')
                print(f"Using command line right directory: {self.pane_manager.right_pane['path']}")
            
            # Refresh file lists after loading state
            self.refresh_files()
            
            # Restore cursor positions after files are loaded
            self.restore_startup_cursor_positions()
            
        except Exception as e:
            print(f"Warning: Could not load application state: {e}")
    
    def restore_startup_cursor_positions(self):
        """Restore cursor positions for both panes during startup."""
        try:
            # Calculate display height for cursor restoration
            height, width = self.renderer.get_dimensions()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            # Restore left pane cursor position
            left_restored = self.pane_manager.restore_cursor_position(self.pane_manager.left_pane, display_height)
            if left_restored:
                left_path = self.pane_manager.left_pane['path']
                if self.pane_manager.left_pane['files']:
                    selected_file = self.pane_manager.left_pane['files'][self.pane_manager.left_pane['selected_index']].name
                    print(f"Restored left pane cursor: {left_path} -> {selected_file}")
            
            # Restore right pane cursor position
            right_restored = self.pane_manager.restore_cursor_position(self.pane_manager.right_pane, display_height)
            if right_restored:
                right_path = self.pane_manager.right_pane['path']
                if self.pane_manager.right_pane['files']:
                    selected_file = self.pane_manager.right_pane['files'][self.pane_manager.right_pane['selected_index']].name
                    print(f"Restored right pane cursor: {right_path} -> {selected_file}")
            
            # If either cursor was restored, trigger a redraw
            if left_restored or right_restored:
                self.needs_full_redraw = True
                
        except Exception as e:
            print(f"Warning: Could not restore startup cursor positions: {e}")
    
    def save_application_state(self):
        """Save current application state to persistent storage."""
        try:
            # Save window layout
            self.state_manager.save_window_layout(
                self.pane_manager.left_pane_ratio,
                self.log_height_ratio
            )
            
            # Save pane states
            self.state_manager.save_pane_state('left', self.pane_manager.left_pane)
            self.state_manager.save_pane_state('right', self.pane_manager.right_pane)
            
            # Save current cursor positions before quitting
            self.save_quit_cursor_positions()
            
            # Add current directories to recent directories
            left_path = str(self.pane_manager.left_pane['path'])
            right_path = str(self.pane_manager.right_pane['path'])
            
            self.state_manager.add_recent_directory(left_path)
            if left_path != right_path:  # Don't add duplicate
                self.state_manager.add_recent_directory(right_path)
            
            # Clean up session
            self.state_manager.cleanup_session()
            
            print("Application state saved")
            
        except Exception as e:
            print(f"Warning: Could not save application state: {e}")
    
    def save_quit_cursor_positions(self):
        """Save current cursor positions when quitting TFM."""
        try:
            # Save left pane cursor position
            if (self.pane_manager.left_pane['files'] and 
                self.pane_manager.left_pane['selected_index'] < len(self.pane_manager.left_pane['files'])):
                
                self.pane_manager.save_cursor_position(self.pane_manager.left_pane)
                
                left_path = self.pane_manager.left_pane['path']
                selected_file = self.pane_manager.left_pane['files'][self.pane_manager.left_pane['selected_index']].name
                print(f"Saved left pane cursor position: {left_path} -> {selected_file}")
            
            # Save right pane cursor position
            if (self.pane_manager.right_pane['files'] and 
                self.pane_manager.right_pane['selected_index'] < len(self.pane_manager.right_pane['files'])):
                
                self.pane_manager.save_cursor_position(self.pane_manager.right_pane)
                
                right_path = self.pane_manager.right_pane['path']
                selected_file = self.pane_manager.right_pane['files'][self.pane_manager.right_pane['selected_index']].name
                print(f"Saved right pane cursor position: {right_path} -> {selected_file}")
                
        except Exception as e:
            print(f"Warning: Could not save cursor positions on quit: {e}")
    
    def get_recent_directories(self):
        """Get list of recent directories for quick navigation."""
        try:
            return self.state_manager.load_recent_directories()
        except Exception as e:
            print(f"Warning: Could not load recent directories: {e}")
            return []
    
    def add_search_to_history(self, search_term):
        """Add a search term to the search history."""
        try:
            self.state_manager.add_search_term(search_term)
        except Exception as e:
            print(f"Warning: Could not save search term: {e}")
    
    def get_search_history(self):
        """Get search history for auto-completion."""
        try:
            return self.state_manager.load_search_history()
        except Exception as e:
            print(f"Warning: Could not load search history: {e}")
            return []

def main(renderer, remote_log_port=None, left_dir=None, right_dir=None):
    """Main function to run the file manager"""
    fm = None
    try:
        fm = FileManager(renderer, remote_log_port=remote_log_port, left_dir=left_dir, right_dir=right_dir)
        fm.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
    except Exception as e:
        # Restore stdout/stderr before handling exception
        if fm is not None:
            fm.restore_stdio()
        
        # Print error information to help with debugging
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
        
        # Clean up state manager
        cleanup_state_manager()

if __name__ == "__main__":
    # Note: tfm_main.py should not be run directly anymore.
    # Use tfm.py which creates the appropriate TTK renderer.
    print("Error: tfm_main.py should not be run directly.")
    print("Please use: python tfm.py")
    import sys
    sys.exit(1)