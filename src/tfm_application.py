"""
TFM Application Controller

This module contains the main application controller that is UI-agnostic.
It accepts a UI backend (IUIBackend) and coordinates all business logic
without directly calling curses or Qt APIs.
"""

import os
import sys
import time
import subprocess
import importlib
import traceback
from pathlib import Path as StdPath
from typing import Optional

from tfm_path import Path
from tfm_ui_backend import IUIBackend, InputEvent, LayoutInfo
from tfm_config import get_config
from tfm_log_manager import LogManager
from tfm_pane_manager import PaneManager
from tfm_file_operations import FileOperations, FileOperationsUI
from tfm_list_dialog import ListDialog
from tfm_info_dialog import InfoDialog
from tfm_search_dialog import SearchDialog
from tfm_jump_dialog import JumpDialog
from tfm_drives_dialog import DrivesDialog
from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_quick_choice_bar import QuickChoiceBar
from tfm_general_purpose_dialog import GeneralPurposeDialog
from tfm_external_programs import ExternalProgramManager
from tfm_progress_manager import ProgressManager
from tfm_state_manager import get_state_manager, cleanup_state_manager
from tfm_archive import ArchiveOperations, ArchiveUI
from tfm_cache_manager import CacheManager
from tfm_const import VERSION, GITHUB_URL, APP_NAME


class TFMApplication:
    """
    Main application controller - UI agnostic.
    
    This class contains all business logic and coordinates between
    the UI backend and various managers. It does not directly call
    curses or Qt APIs.
    """
    
    def __init__(self, ui_backend: IUIBackend, remote_log_port: Optional[int] = None,
                 left_dir: Optional[str] = None, right_dir: Optional[str] = None):
        """
        Initialize the TFM application.
        
        Args:
            ui_backend: UI backend implementation (curses or Qt)
            remote_log_port: Optional port for remote log monitoring
            left_dir: Optional initial directory for left pane
            right_dir: Optional initial directory for right pane
        """
        self.ui = ui_backend
        
        # Load configuration
        self.config = get_config()
        
        # Initialize Unicode handling from configuration
        from tfm_wide_char_utils import initialize_from_config
        initialize_from_config()
        
        # Create TFM user directories if they don't exist
        self._create_user_directories()
        
        # Initialize modular components
        self.log_manager = LogManager(self.config, remote_port=remote_log_port)
        self.state_manager = get_state_manager()
        
        # Track whether command line directories were provided
        self.cmdline_left_dir_provided = left_dir is not None
        self.cmdline_right_dir_provided = right_dir is not None
        
        # Set up initial directories
        initial_left_dir = Path(left_dir) if left_dir else Path.cwd()
        initial_right_dir = Path(right_dir) if right_dir else Path.home()
        
        # Validate directories exist, fall back to defaults if not
        if not initial_left_dir.exists() or not initial_left_dir.is_dir():
            self.log_manager.add_message(f"Warning: Left directory '{initial_left_dir}' does not exist, using current directory")
            initial_left_dir = Path.cwd()
            
        if not initial_right_dir.exists() or not initial_right_dir.is_dir():
            self.log_manager.add_message(f"Warning: Right directory '{initial_right_dir}' does not exist, using home directory")
            initial_right_dir = Path.home()
        
        # Initialize managers
        self.pane_manager = PaneManager(self.config, initial_left_dir, initial_right_dir, self.state_manager)
        self.file_operations = FileOperations(self.config)
        self.progress_manager = ProgressManager()
        self.cache_manager = CacheManager(self.log_manager)
        self.archive_operations = ArchiveOperations(self.log_manager, self.cache_manager, self.progress_manager)
        
        # Note: Dialog components and UI-specific managers will be initialized
        # by the UI backend as they may need UI-specific setup
        
        # Layout settings
        self.log_height_ratio = getattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO', 0.25)
        self.needs_full_redraw = True
        
        # Application state flags
        self.should_quit = False
        self.operation_in_progress = False
        self.operation_cancelled = False
        
        # Add startup messages to log
        self.log_manager.add_startup_messages(VERSION, GITHUB_URL, APP_NAME)
        
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
            
        except OSError as e:
            # If we can't create the directories, log a warning but don't fail
            print(f"Warning: Could not create TFM user directories: {e}", file=sys.stderr)
    
    def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        # Initialize UI backend
        if not self.ui.initialize():
            return False
        
        # Set color scheme
        color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
        self.ui.set_color_scheme(color_scheme)
        
        return True
    
    def cleanup(self):
        """Clean up application resources."""
        # Restore stdout/stderr
        self.log_manager.restore_stdio()
        
        # Save application state
        self.save_application_state()
        
        # Clean up UI backend
        self.ui.cleanup()
        
        # Clean up state manager
        cleanup_state_manager()
    
    def run(self):
        """
        Main application loop.
        
        This method implements the main event loop that:
        1. Checks for events (keyboard, mouse, resize)
        2. Handles input events
        3. Renders the UI
        """
        if not self.initialize():
            return False
        
        try:
            while not self.should_quit:
                # Check for startup redraw trigger
                if hasattr(self, 'startup_time') and time.time() - self.startup_time >= 0.033:
                    self.needs_full_redraw = True
                    delattr(self, 'startup_time')
                
                # Check for log updates
                if self.log_manager.has_log_updates():
                    self.needs_full_redraw = True
                
                # Get input event with timeout
                event = self.ui.get_input_event(timeout=16)  # 16ms timeout
                
                if event:
                    self.handle_input(event)
                
                # Render UI
                self.render()
        
        finally:
            self.cleanup()
        
        return True
    
    def handle_input(self, event: InputEvent):
        """
        Handle input events.
        
        Args:
            event: Input event to handle
        """
        if event.type == 'resize':
            self.needs_full_redraw = True
            return
        
        if event.type == 'key':
            self._handle_key_event(event)
        elif event.type == 'mouse':
            self._handle_mouse_event(event)
    
    def _handle_key_event(self, event: InputEvent):
        """Handle keyboard events."""
        # Check if operation is in progress
        if self.operation_in_progress:
            # Only allow ESC key to cancel operation
            if event.key == 27:  # ESC key
                self.operation_cancelled = True
                self.log_manager.add_message("Cancelling operation...")
            return
        
        # Get current pane
        current_pane = self.pane_manager.get_current_pane()
        
        # Handle basic navigation keys
        key = event.key
        
        # Tab key - switch panes
        if key == 9:  # Tab
            self.pane_manager.active_pane = 'right' if self.pane_manager.active_pane == 'left' else 'left'
            self.needs_full_redraw = True
        
        # Arrow keys - navigation
        elif event.key_name == 'KEY_UP':
            if current_pane['selected_index'] > 0:
                current_pane['selected_index'] -= 1
                self.needs_full_redraw = True
        
        elif event.key_name == 'KEY_DOWN':
            if current_pane['selected_index'] < len(current_pane['files']) - 1:
                current_pane['selected_index'] += 1
                self.needs_full_redraw = True
        
        # Enter key - open directory or file
        elif event.key_name in ('KEY_ENTER', '\n', '\r') or key in (10, 13):
            self._handle_enter()
            self.needs_full_redraw = True
        
        # Backspace - go to parent directory
        elif event.key_name in ('KEY_BACKSPACE', '\x7f') or key in (127, 263, 8):
            if current_pane['path'] != current_pane['path'].parent:
                try:
                    current_pane['path'] = current_pane['path'].parent
                    current_pane['selected_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()
                    self.file_operations.refresh_files(current_pane)
                    self.needs_full_redraw = True
                except PermissionError:
                    self.log_manager.add_message("Permission denied", "ERROR")
        
        # Page Up/Down
        elif event.key_name == 'KEY_PPAGE':
            current_pane['selected_index'] = max(0, current_pane['selected_index'] - 10)
            self.needs_full_redraw = True
        
        elif event.key_name == 'KEY_NPAGE':
            current_pane['selected_index'] = min(len(current_pane['files']) - 1, current_pane['selected_index'] + 10)
            self.needs_full_redraw = True
        
        # Left/Right arrows - pane switching or parent navigation
        elif event.key_name == 'KEY_LEFT':
            if self.pane_manager.active_pane == 'right':
                # Switch to left pane
                self.pane_manager.active_pane = 'left'
                self.needs_full_redraw = True
            elif current_pane['path'] != current_pane['path'].parent:
                # Go to parent directory
                try:
                    current_pane['path'] = current_pane['path'].parent
                    current_pane['selected_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()
                    self.file_operations.refresh_files(current_pane)
                    self.needs_full_redraw = True
                except PermissionError:
                    self.log_manager.add_message("Permission denied", "ERROR")
        
        elif event.key_name == 'KEY_RIGHT':
            if self.pane_manager.active_pane == 'left':
                # Switch to right pane
                self.pane_manager.active_pane = 'right'
                self.needs_full_redraw = True
            elif current_pane['path'] != current_pane['path'].parent:
                # Go to parent directory
                try:
                    current_pane['path'] = current_pane['path'].parent
                    current_pane['selected_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()
                    self.file_operations.refresh_files(current_pane)
                    self.needs_full_redraw = True
                except PermissionError:
                    self.log_manager.add_message("Permission denied", "ERROR")
        
        # 'q' key - quit
        elif key == ord('q') or key == ord('Q'):
            self.should_quit = True
        
        # '.' key - toggle hidden files
        elif key == ord('.'):
            self.file_operations.toggle_hidden_files()
            self.pane_manager.left_pane['selected_index'] = 0
            self.pane_manager.left_pane['scroll_offset'] = 0
            self.pane_manager.right_pane['selected_index'] = 0
            self.pane_manager.right_pane['scroll_offset'] = 0
            self.file_operations.refresh_files(self.pane_manager.left_pane)
            self.file_operations.refresh_files(self.pane_manager.right_pane)
            self.needs_full_redraw = True
    
    def _handle_enter(self):
        """Handle Enter key - open directory or file."""
        current_pane = self.pane_manager.get_current_pane()
        
        if not current_pane['files']:
            return
        
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        if selected_file.is_dir():
            # Navigate into directory
            try:
                current_pane['path'] = selected_file
                current_pane['selected_index'] = 0
                current_pane['scroll_offset'] = 0
                current_pane['selected_files'].clear()
                self.file_operations.refresh_files(current_pane)
            except PermissionError:
                self.log_manager.add_message(f"Permission denied: {selected_file}", "ERROR")
        else:
            # For files, just log for now (file viewing will be implemented later)
            self.log_manager.add_message(f"File: {selected_file.name}")
    
    def _handle_mouse_event(self, event: InputEvent):
        """Handle mouse events."""
        # TODO: Implement mouse handling logic
        pass
    
    def render(self):
        """
        Render all UI components.
        
        This method coordinates rendering of all UI elements through
        the UI backend.
        """
        if not self.needs_full_redraw:
            return
        
        # Get screen size
        height, width = self.ui.get_screen_size()
        
        # Calculate layout
        layout = LayoutInfo.calculate(height, width, self.log_height_ratio)
        
        # Render header
        self.ui.render_header(
            str(self.pane_manager.left_pane['path']),
            str(self.pane_manager.right_pane['path']),
            self.pane_manager.active_pane
        )
        
        # Render panes
        self.ui.render_panes(
            self.pane_manager.left_pane,
            self.pane_manager.right_pane,
            self.pane_manager.active_pane,
            layout
        )
        
        # Render footer
        left_info = self._get_pane_footer_info(self.pane_manager.left_pane)
        right_info = self._get_pane_footer_info(self.pane_manager.right_pane)
        self.ui.render_footer(left_info, right_info, self.pane_manager.active_pane)
        
        # Render status bar
        status_message = self._get_status_message()
        controls = self._get_status_controls()
        self.ui.render_status_bar(status_message, controls)
        
        # Render log pane
        messages = self.log_manager.log_messages
        scroll_offset = self.log_manager.log_scroll_offset
        self.ui.render_log_pane(messages, scroll_offset, self.log_height_ratio)
        
        # Refresh display
        self.ui.refresh()
        
        self.needs_full_redraw = False
    
    def _get_pane_footer_info(self, pane_data: dict) -> str:
        """Get footer information string for a pane."""
        dirs, files = self.pane_manager.count_files_and_dirs(pane_data)
        selected = len(pane_data['selected_files'])
        sort_desc = self.file_operations.get_sort_description(pane_data)
        
        filter_info = ""
        if pane_data['filter_pattern']:
            filter_info = f" | Filter: {pane_data['filter_pattern']}"
        
        if selected > 0:
            return f" {dirs} dirs, {files} files ({selected} selected) | Sort: {sort_desc}{filter_info} "
        else:
            return f" {dirs} dirs, {files} files | Sort: {sort_desc}{filter_info} "
    
    def _get_status_message(self) -> str:
        """Get status bar message."""
        # Progress display takes precedence
        if self.progress_manager.is_operation_active():
            return self.progress_manager.get_progress_text(80)  # TODO: Use actual width
        
        # Normal status display
        status_parts = []
        if self.file_operations.show_hidden:
            status_parts.append("showing hidden")
        
        return f"({', '.join(status_parts)})" if status_parts else ""
    
    def _get_status_controls(self) -> list:
        """Get status bar control hints."""
        return [
            {'key': '?', 'label': 'help'},
            {'key': 'Tab', 'label': 'switch panes'},
            {'key': 'Enter', 'label': 'open'},
            {'key': 'q', 'label': 'quit'}
        ]
    
    def load_application_state(self):
        """Load saved application state from persistent storage."""
        try:
            # Update session heartbeat
            self.state_manager.update_session_heartbeat()
            
            # Clean up non-existing directories from history
            self.state_manager.cleanup_non_existing_directories()
            
            # Load window layout
            layout = self.state_manager.load_window_layout()
            if layout:
                self.pane_manager.left_pane_ratio = layout.get('left_pane_ratio', 0.5)
                self.log_height_ratio = layout.get('log_height_ratio', 0.25)
                print(f"Restored window layout: panes {int(self.pane_manager.left_pane_ratio*100)}%/{int((1-self.pane_manager.left_pane_ratio)*100)}%, log {int(self.log_height_ratio*100)}%")
            
            # Load pane states
            self._load_pane_state('left', self.cmdline_left_dir_provided)
            self._load_pane_state('right', self.cmdline_right_dir_provided)
            
            # Refresh file lists after loading state
            self.file_operations.refresh_files(self.pane_manager.left_pane)
            self.file_operations.refresh_files(self.pane_manager.right_pane)
            
        except Exception as e:
            print(f"Warning: Could not load application state: {e}")
    
    def _load_pane_state(self, pane_name: str, cmdline_dir_provided: bool):
        """Load state for a specific pane."""
        pane = self.pane_manager.left_pane if pane_name == 'left' else self.pane_manager.right_pane
        state = self.state_manager.load_pane_state(pane_name)
        
        if state and Path(state['path']).exists() and not cmdline_dir_provided:
            # Only restore if the directory still exists and no command line argument was provided
            pane['path'] = Path(state['path'])
            pane['sort_mode'] = state.get('sort_mode', 'name')
            pane['sort_reverse'] = state.get('sort_reverse', False)
            pane['filter_pattern'] = state.get('filter_pattern', '')
            print(f"Restored {pane_name} pane: {state['path']}")
        elif cmdline_dir_provided:
            # Load other settings but keep command line directory
            if state:
                pane['sort_mode'] = state.get('sort_mode', 'name')
                pane['sort_reverse'] = state.get('sort_reverse', False)
                pane['filter_pattern'] = state.get('filter_pattern', '')
            print(f"Using command line {pane_name} directory: {pane['path']}")
    
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
            
            # Add current directories to recent directories
            left_path = str(self.pane_manager.left_pane['path'])
            right_path = str(self.pane_manager.right_pane['path'])
            
            self.state_manager.add_recent_directory(left_path)
            if left_path != right_path:
                self.state_manager.add_recent_directory(right_path)
            
            # Clean up session
            self.state_manager.cleanup_session()
            
            print("Application state saved")
            
        except Exception as e:
            print(f"Warning: Could not save application state: {e}")
