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
import argparse
from pathlib import Path as StdPath
from tfm_path import Path
from datetime import datetime
from collections import deque
from typing import Optional
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_base_task import BaseTask

# Import TTK input event system
from ttk import KeyEvent, KeyCode, ModifierKey, SystemEvent, SystemEventType, MenuEvent, CharEvent, EventCallback, TextAttribute

# Import constants and colors
from tfm_const import *
from tfm_colors import *
from tfm_config import get_config, get_favorite_directories, get_programs, get_program_for_file, has_action_for_file, has_explicit_association, find_action_for_event, get_keys_for_action, format_key_for_display
from tfm_text_viewer import create_text_viewer, is_text_file
from tfm_diff_viewer import create_diff_viewer
from tfm_directory_diff_viewer import DirectoryDiffViewer

# Import new modular components
from tfm_log_manager import LogManager
from tfm_pane_manager import PaneManager
from tfm_file_list_manager import FileListManager
from tfm_file_operation_ui import FileOperationUI
from tfm_file_operation_executor import FileOperationExecutor
from tfm_list_dialog import ListDialog, ListDialogHelpers
from ttk.wide_char_utils import get_display_width, truncate_to_width, pad_to_width, safe_get_display_width

from tfm_info_dialog import InfoDialog, InfoDialogHelpers
from tfm_search_dialog import SearchDialog, SearchDialogHelpers
from tfm_drives_dialog import DrivesDialog, DrivesDialogHelpers
from tfm_batch_rename_dialog import BatchRenameDialog, BatchRenameDialogHelpers
from tfm_quick_choice_bar import QuickChoiceBar, QuickChoiceBarHelpers
from tfm_quick_edit_bar import QuickEditBar, QuickEditBarHelpers
from tfm_external_programs import ExternalProgramManager
from tfm_progress_manager import ProgressManager, OperationType
from tfm_state_manager import get_state_manager, cleanup_state_manager
from tfm_archive import ArchiveOperations, ArchiveUI
from tfm_cache_manager import CacheManager
from tfm_menu_manager import MenuManager
from tfm_ui_layer import UILayerStack, UILayer
from tfm_adaptive_fps import AdaptiveFPSManager
from tfm_drag_gesture import DragGestureDetector
from tfm_drag_payload import DragPayloadBuilder
from tfm_drag_session import DragSessionManager


class TFMEventCallback(EventCallback):
    """
    Event callback implementation for TFM application layer.
    
    This class implements the EventCallback interface to handle events
    delivered by the TTK backend. It routes all events directly to the
    UI layer stack, which distributes them to the appropriate layer.
    """
    
    def __init__(self, file_manager):
        """
        Initialize the TFMEventCallback.
        
        Args:
            file_manager: FileManager instance for accessing layer stack
        """
        self.file_manager = file_manager
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """
        Handle a key event by routing to the UI layer stack.
        
        This method intercepts global keyboard shortcuts before routing to layers.
        Exceptions are caught to prevent TFM shutdown.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        try:
            # Mark activity for adaptive FPS
            self.file_manager.adaptive_fps.mark_activity()
            
            # Handle global desktop mode shortcuts (work in all contexts)
            if self.file_manager.is_desktop_mode() and event.has_modifier(ModifierKey.COMMAND):
                # Cmd-Plus or Cmd-= (increase font size)
                if event.char == '+' or event.char == '=':
                    if hasattr(self.file_manager.renderer, 'change_font_size'):
                        if self.file_manager.renderer.change_font_size(1):
                            self.file_manager.logger.info(f"Font size increased to {self.file_manager.renderer.font_size}pt")
                            self.file_manager.mark_dirty()
                            return True
                # Cmd-Minus (decrease font size)
                elif event.char == '-':
                    if hasattr(self.file_manager.renderer, 'change_font_size'):
                        if self.file_manager.renderer.change_font_size(-1):
                            self.file_manager.logger.info(f"Font size decreased to {self.file_manager.renderer.font_size}pt")
                            self.file_manager.mark_dirty()
                            return True
                        else:
                            self.file_manager.logger.info("Font size at minimum (8pt)")
                            return True
            
            # Route to UI layer stack
            return self.file_manager.ui_layer_stack.handle_key_event(event)
        except Exception as e:
            # Log error message
            self.file_manager.logger.error(f"Error handling key event: {e}")
            # Print stack trace to stderr if debug mode is enabled
            if os.environ.get('TFM_DEBUG') == '1':
                traceback.print_exc(file=sys.stderr)
            return True  # Event consumed to prevent further issues
    
    def on_char_event(self, event: CharEvent) -> bool:
        """
        Handle a character event by routing to the UI layer stack.
        
        Exceptions are caught to prevent TFM shutdown.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        try:
            # Mark activity for adaptive FPS
            self.file_manager.adaptive_fps.mark_activity()
            
            # Route to UI layer stack
            return self.file_manager.ui_layer_stack.handle_char_event(event)
        except Exception as e:
            # Log error message
            self.file_manager.logger.error(f"Error handling char event: {e}")
            # Print stack trace to stderr if debug mode is enabled
            if os.environ.get('TFM_DEBUG') == '1':
                traceback.print_exc(file=sys.stderr)
            return True  # Event consumed to prevent further issues
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """
        Handle a system event by routing to the UI layer stack.
        
        System events are broadcast to all layers in the stack.
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        # Mark activity for adaptive FPS
        self.file_manager.adaptive_fps.mark_activity()
        
        # Route to UI layer stack
        return self.file_manager.ui_layer_stack.handle_system_event(event)
    
    def on_menu_event(self, event) -> bool:
        """
        Handle a menu event by routing to FileManager._handle_menu_event().
        
        Menu events are desktop-mode specific and handled directly by FileManager
        as they affect application-wide state and commands.
        Exceptions are caught to prevent TFM shutdown.
        
        Args:
            event: MenuEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        try:
            # Mark activity for adaptive FPS
            self.file_manager.adaptive_fps.mark_activity()
            
            return self.file_manager._handle_menu_event(event)
        except Exception as e:
            # Log error message
            self.file_manager.logger.error(f"Error handling menu event: {e}")
            # Print stack trace to stderr if debug mode is enabled
            if os.environ.get('TFM_DEBUG') == '1':
                traceback.print_exc(file=sys.stderr)
            return True  # Event consumed to prevent further issues
    
    def on_menu_will_open(self) -> None:
        """
        Called when a menu is about to open.
        
        This callback updates menu item states right before the menu is displayed,
        ensuring that enabled/disabled states reflect the current application state.
        
        This is more efficient than continuously updating menu states, as it only
        updates when the user is about to interact with the menu.
        """
        try:
            # Update menu states to reflect current application state
            self.file_manager._update_menu_states()
        except Exception as e:
            # Log error message
            self.file_manager.logger.error(f"Error updating menu states: {e}")
            # Print stack trace to stderr if debug mode is enabled
            if os.environ.get('TFM_DEBUG') == '1':
                traceback.print_exc(file=sys.stderr)
    
    def on_mouse_event(self, event: 'MouseEvent') -> bool:
        """
        Handle a mouse event by routing to the UI layer stack.
        
        Mouse events are delivered to the topmost UILayer only, consistent
        with keyboard event routing. Mouse events are filtered out during
        input modes (quick edit, quick choice, i-search) to prevent
        accidental disruption of keyboard-based workflows.
        
        Args:
            event: MouseEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        # Mark activity for adaptive FPS
        self.file_manager.adaptive_fps.mark_activity()
        
        # Filter out mouse events during input modes
        if self.file_manager.is_in_input_mode():
            self.file_manager.logger.debug(f"Ignoring mouse event during input mode: {event.event_type}")
            return True  # Event consumed (ignored)
        
        # Route to UI layer stack
        return self.file_manager.ui_layer_stack.handle_mouse_event(event)


class FileManager(UILayer):
    def __init__(self, renderer, remote_log_port=None, left_dir=None, right_dir=None, profiling_targets=None, log_file=None, debug=False):
        self.renderer = renderer
        self.stdscr = renderer  # Keep stdscr as alias for compatibility during migration
        
        # Store profiling targets
        self.profiling_targets = profiling_targets or set()
        
        # Load configuration early (needed for LogManager and colors)
        self.config = get_config()
        
        # Initialize LogManager as early as possible to start capturing logs
        # This must happen before any operations that might generate log messages
        # Enable stream output in desktop mode (CoreGraphics), disable in terminal mode (Curses)
        is_desktop = renderer.is_desktop_mode()
        self.log_manager = LogManager(self.config, remote_port=remote_log_port, 
                                     is_desktop_mode=is_desktop, log_file=log_file)
        
        # Set the global LogManager instance for module-level getLogger() calls
        from tfm_log_manager import set_log_manager
        set_log_manager(self.log_manager)
        
        # Set log level to DEBUG if debug mode is enabled
        if debug:
            import logging
            self.log_manager.set_default_log_level(logging.DEBUG)
        
        # Create logger for main application
        self.logger = self.log_manager.getLogger("Main")
        
        # Log debug mode status
        if debug:
            self.logger.debug("Debug logging enabled - showing detailed diagnostic information")
        
        # Initialize colors (can happen after LogManager since it doesn't use stdout/stderr)
        color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
        init_colors(renderer, color_scheme)
        
        # Create TFM user directories if they don't exist
        self._create_user_directories()
        
        # Initialize adaptive FPS manager for CPU optimization
        self.adaptive_fps = AdaptiveFPSManager()
        
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
            self.logger.warning(f"Left directory '{initial_left_dir}' does not exist, using current directory")
            initial_left_dir = Path.cwd()
            
        if not initial_right_dir.exists() or not initial_right_dir.is_dir():
            self.logger.warning(f"Right directory '{initial_right_dir}' does not exist, using home directory")
            initial_right_dir = Path.home()
        
        # Use simple defaults since TFM loads previous state anyway
        self.pane_manager = PaneManager(self.config, initial_left_dir, initial_right_dir, self.state_manager)
        self.file_list_manager = FileListManager(self.config)
        self.file_list_manager.log_manager = self.log_manager  # Set log_manager for error reporting
        self.file_list_manager.logger = self.log_manager.getLogger("FileOp")  # Set logger for file operations
        self.pane_manager.file_list_manager = self.file_list_manager  # Set file_list_manager for refresh_files
        self.list_dialog = ListDialog(self.config, renderer)
        self.info_dialog = InfoDialog(self.config, renderer)
        self.search_dialog = SearchDialog(self.config, renderer)
        self.drives_dialog = DrivesDialog(self.config, renderer)
        self.batch_rename_dialog = BatchRenameDialog(self.config, renderer)
        self.quick_choice_bar = QuickChoiceBar(self.config, renderer)
        self.quick_edit_bar = QuickEditBar(self.config, renderer)
        self.external_program_manager = ExternalProgramManager(self.config, self.log_manager, renderer)
        self.progress_manager = ProgressManager()
        self.cache_manager = CacheManager(self.log_manager)
        self.file_operations_executor = FileOperationExecutor(self)
        self.archive_operations = ArchiveOperations(self.log_manager, self.cache_manager, self.progress_manager)
        self.archive_ui = ArchiveUI(self, self.archive_operations)
        self.file_operations_ui = FileOperationUI(self, self.file_list_manager)
        
        # Initialize drag-and-drop components
        self.drag_gesture_detector = DragGestureDetector()
        self.drag_payload_builder = DragPayloadBuilder()
        self.drag_session_manager = DragSessionManager(renderer)
        
        # Initialize menu system for desktop mode
        self.menu_manager = None
        if self.is_desktop_mode():
            self.menu_manager = MenuManager(self)
            self._setup_menu_bar()
        
        # Layout settings
        self.log_height_ratio = getattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO', DEFAULT_LOG_HEIGHT_RATIO)
        
        # Isearch mode state
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        

        
        # Dialog state (now handled by quick_edit_bar)
        self.rename_file_path = None  # Still needed for rename operations
        
        # Operation state flags
        self.operation_in_progress = False  # Flag to block input during operations
        self.operation_cancelled = False  # Flag to signal operation cancellation
        
        # Task management
        self.current_task: Optional[BaseTask] = None

        self.should_quit = False  # Flag to control main loop exit
        
        # Set up event callback (callback mode is always enabled)
        self.event_callback = TFMEventCallback(self)
        self.renderer.set_event_callback(self.event_callback)
        
        # Query and enable mouse capabilities
        self._setup_mouse_support()
        
        # Initialize UI layer stack with FileManager as bottom layer
        self.ui_layer_stack = UILayerStack(self, self.log_manager, self.adaptive_fps)
        
        # UILayer interface attributes
        self._dirty = True  # Start dirty to ensure initial render

        # Add startup messages to log
        self.log_manager.add_startup_messages(VERSION, GITHUB_URL, APP_NAME)
        
        # Colors already initialized before LogManager creation to prevent
        # stdout/stderr redirection from interfering with color detection
        
        # Configure renderer
        self.renderer.set_cursor_visibility(False)  # Hide cursor
        # Note: TTK handles special keys automatically through KeyEvent, no keypad() needed
        
        # Track startup time for delayed redraw
        self.startup_time = time.time()
        
        # Load saved state
        self.load_application_state()
    
    # Task management methods
    
    def start_task(self, task: BaseTask):
        """Start a new task
        
        Args:
            task: The task to start
            
        Raises:
            RuntimeError: If a task is already active
        """
        if self.current_task and self.current_task.is_active():
            raise RuntimeError("Cannot start task: another task is already active")
        
        self.current_task = task
        task.start()
    
    def cancel_current_task(self):
        """Cancel the currently active task"""
        if self.current_task and self.current_task.is_active():
            self.current_task.cancel()
    
    def _clear_task(self):
        """Clear the current task reference (called by task when complete)"""
        self.current_task = None
    
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
            self.logger.warning(f"Warning: Could not create TFM user directories: {e}")
    
    def _setup_mouse_support(self):
        """Query and enable mouse support capabilities at startup."""
        # Query if mouse is supported by the backend
        if self.renderer.supports_mouse():
            # Get supported mouse event types
            supported_events = self.renderer.get_supported_mouse_events()
            
            # Enable mouse event capture
            if self.renderer.enable_mouse_events():
                # Log success with event count (handle both set and mock objects)
                try:
                    event_count = len(supported_events)
                    self.logger.info(f"Mouse support enabled: {event_count} event types supported")
                except TypeError:
                    # Handle mock objects in tests
                    self.logger.info("Mouse support enabled")
            else:
                self.logger.warning("Mouse support available but failed to enable")
        else:
            self.logger.info("Mouse support not available on this backend")
    
    # UILayer interface implementation
    
    def handle_key_event(self, event) -> bool:
        """
        Handle a key event for the main FileManager screen.
        
        This method delegates to FileManager.handle_input(), which handles both
        FileManager-specific input modes and main screen keyboard events.
        
        Note: Global shortcuts like font size adjustment are handled in
        TFMEventCallback.on_key_event() before reaching this method.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        return self.handle_input(event)
    
    def handle_char_event(self, event) -> bool:
        """
        Handle a character event.
        
        This method delegates to FileManager.handle_input(), which checks for
        FileManager-specific input modes that handle character input (isearch,
        quick_edit_bar). The main screen doesn't handle char events directly.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        return self.handle_input(event)
    
    def handle_system_event(self, event) -> bool:
        """
        Handle a system event (resize, close, etc.).
        
        This method handles window resize and close events for the main
        FileManager screen.
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        if event.is_resize():
            # Handle window resize
            self.clear_screen_with_background()
            self.mark_dirty()
            return True
        elif event.is_close():
            # Handle window close request
            if hasattr(self, 'operation_in_progress') and self.operation_in_progress:
                # Ignore close event during operations
                self.logger.error("Cannot close: file operation in progress")
                return True
            else:
                # No operations in progress, request close
                self.should_quit = True
                return True
        return False
    
    def handle_mouse_event(self, event) -> bool:
        """
        Handle a mouse event for pane focus switching, wheel scrolling, double-click, and drag-and-drop.
        
        This method handles:
        - Drag gesture detection for drag-and-drop operations
        - Mouse button down events to switch focus between left and right panes
        - Mouse wheel events to scroll the file list in the active pane
        - Double-click events to open files/directories (same as Enter key)
        - Double-click on header to go to parent directory (same as Backspace key)
        
        Args:
            event: MouseEvent to handle
        
        Returns:
            True if the event was handled, False otherwise
        """
        # Import MouseEventType for event type checking
        from ttk.ttk_mouse_event import MouseEventType, transform_grid_to_screen
        
        # Block all mouse events if drag is in progress
        if self.drag_session_manager.is_dragging():
            return True
        
        # Get current dimensions and layout
        height, width = self.renderer.get_dimensions()
        left_pane_width = int(width * self.pane_manager.left_pane_ratio)
        
        # Calculate pane bounds
        # Panes start at row 1 (after header) and end before footer/log area
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        file_pane_bottom = height - log_height - 2
        log_pane_top = height - log_height - 1
        
        # Get cell dimensions for pixel coordinate conversion
        # Assume standard cell size (this is approximate for drag detection)
        cell_width = 8.0  # Typical monospace character width
        cell_height = 16.0  # Typical line height
        
        # Convert grid coordinates to pixel coordinates for drag detection
        pixel_x, pixel_y = transform_grid_to_screen(
            event.column, event.row,
            event.sub_cell_x, event.sub_cell_y,
            cell_width, cell_height
        )
        
        # Handle drag gesture detection
        if event.event_type == MouseEventType.BUTTON_DOWN:
            # Check if event is within the file pane area (vertically)
            if event.row >= 1 and event.row < file_pane_bottom:
                # Start tracking potential drag gesture
                self.drag_gesture_detector.handle_button_down(int(pixel_x), int(pixel_y))
        
        elif event.event_type == MouseEventType.MOVE:
            # Check for drag gesture
            if self.drag_gesture_detector.handle_move(int(pixel_x), int(pixel_y)):
                # Drag gesture detected - initiate drag
                return self._initiate_drag()
        
        elif event.event_type == MouseEventType.BUTTON_UP:
            # Check if this was a drag gesture
            was_dragging = self.drag_gesture_detector.handle_button_up()
            if was_dragging:
                # Was a drag, not a click - don't process as click
                return True
        
        # Handle double-click events
        if event.event_type == MouseEventType.DOUBLE_CLICK:
            # Check if double-click is on header (row 0) - go to parent directory
            if event.row == 0:
                # Determine which pane header was clicked
                if event.column < left_pane_width:
                    target_pane = 'left'
                else:
                    target_pane = 'right'
                
                # Switch to the clicked pane if not already active
                if self.pane_manager.active_pane != target_pane:
                    self.pane_manager.active_pane = target_pane
                    self.logger.info(f"Switched focus to {target_pane} pane")
                
                # Navigate to parent directory (same as Backspace key)
                self._action_go_parent()
                self.logger.info(f"Double-clicked header in {target_pane} pane - navigating to parent")
                return True
            
            # Check if event is within the file pane area (vertically)
            if event.row < 1 or event.row >= file_pane_bottom:
                return False
            
            # Determine which pane was double-clicked
            if event.column < left_pane_width:
                pane_data = self.pane_manager.left_pane
                target_pane = 'left'
            else:
                pane_data = self.pane_manager.right_pane
                target_pane = 'right'
            
            # Calculate which file was double-clicked
            clicked_file_index = event.row - 1 + pane_data['scroll_offset']
            
            # Validate the clicked index
            if pane_data['files'] and 0 <= clicked_file_index < len(pane_data['files']):
                # Switch to the clicked pane if not already active
                if self.pane_manager.active_pane != target_pane:
                    self.pane_manager.active_pane = target_pane
                    self.logger.info(f"Switched focus to {target_pane} pane")
                
                # Move cursor to the double-clicked item
                pane_data['focused_index'] = clicked_file_index
                
                # Trigger the same action as Enter key
                self.handle_enter()
                self.mark_dirty()
                
                self.logger.info(f"Double-clicked item {clicked_file_index} in {target_pane} pane")
                return True
            
            return False
        
        # Handle wheel events for scrolling
        if event.event_type == MouseEventType.WHEEL:
            # Check if event is in the log pane area
            if log_height > 0 and event.row >= log_pane_top:
                # Scroll the log pane
                scroll_lines = int(event.scroll_delta_y * 1)
                
                if scroll_lines > 0:
                    # Scroll up (toward older messages)
                    if self.log_manager.scroll_log_up(scroll_lines):
                        self.mark_dirty()
                elif scroll_lines < 0:
                    # Scroll down (toward newer messages)
                    if self.log_manager.scroll_log_down(-scroll_lines):
                        self.mark_dirty()
                
                return True
            
            # Check if event is within the file pane area (vertically)
            if event.row < 1 or event.row >= file_pane_bottom:
                return False
            # Determine which pane to scroll based on mouse position
            target_pane = 'left' if event.column < left_pane_width else 'right'
            pane_data = self.pane_manager.left_pane if target_pane == 'left' else self.pane_manager.right_pane
            
            # Calculate scroll amount (positive delta = scroll up, negative = scroll down)
            # Use a multiplier to make scrolling feel responsive
            scroll_lines = int(event.scroll_delta_y * 1)
            
            if scroll_lines != 0 and len(pane_data['files']) > 0:
                # Adjust scroll_offset based on scroll direction
                old_offset = pane_data['scroll_offset']
                new_offset = old_offset - scroll_lines  # Negative delta scrolls down (increases offset)
                
                # Calculate display height for clamping
                # file_pane_bottom already accounts for header (1) and status bar (1)
                display_height = file_pane_bottom - 1
                max_offset = max(0, len(pane_data['files']) - display_height)
                
                # Clamp to valid range
                new_offset = max(0, min(new_offset, max_offset))
                
                if new_offset != old_offset:
                    pane_data['scroll_offset'] = new_offset
                    self.mark_dirty()
                
                return True
            
            return True  # Event handled even if no scroll occurred
        
        # Handle button down events for focus switching and item selection
        if event.event_type == MouseEventType.BUTTON_DOWN:
            # Check if event is within the file pane area (vertically)
            if event.row < 1 or event.row >= file_pane_bottom:
                return False
            
            # Determine which pane was clicked based on column
            if event.column < left_pane_width:
                # Click in left pane
                pane_data = self.pane_manager.left_pane
                pane_changed = self.pane_manager.active_pane != 'left'
                if pane_changed:
                    self.pane_manager.active_pane = 'left'
                    self.logger.info("Switched focus to left pane")
                
                # Calculate which file was clicked (row 1 is first file)
                clicked_file_index = event.row - 1 + pane_data['scroll_offset']
                
                # Move cursor to clicked item if valid
                if pane_data['files'] and 0 <= clicked_file_index < len(pane_data['files']):
                    pane_data['focused_index'] = clicked_file_index
                    self.logger.info(f"Moved cursor to item {clicked_file_index} in left pane")
                
                self.mark_dirty()
                return True
            else:
                # Click in right pane (including the separator column)
                pane_data = self.pane_manager.right_pane
                pane_changed = self.pane_manager.active_pane != 'right'
                if pane_changed:
                    self.pane_manager.active_pane = 'right'
                    self.logger.info("Switched focus to right pane")
                
                # Calculate which file was clicked (row 1 is first file)
                clicked_file_index = event.row - 1 + pane_data['scroll_offset']
                
                # Move cursor to clicked item if valid
                if pane_data['files'] and 0 <= clicked_file_index < len(pane_data['files']):
                    pane_data['focused_index'] = clicked_file_index
                    self.logger.info(f"Moved cursor to item {clicked_file_index} in right pane")
                
                self.mark_dirty()
                return True
        
        return False
    
    def _initiate_drag(self) -> bool:
        """
        Initiate a drag operation.
        
        This method is called when a drag gesture is detected. It builds the
        drag payload from selected files or the focused item, and starts a
        native drag session through the backend.
        
        Returns:
            True if drag started successfully, False otherwise
        """
        # Get current pane data
        current_pane = self.get_current_pane()
        
        # Get selected files (convert strings to Path objects)
        # Note: selected_files is a set of strings (see tfm_file_operations.py line 67)
        selected_files = [Path(f) for f in current_pane['selected_files']]
        
        # Get focused item
        focused_item = None
        if current_pane['files'] and 0 <= current_pane['focused_index'] < len(current_pane['files']):
            focused_item = current_pane['files'][current_pane['focused_index']]
        
        # Get current directory
        current_dir = current_pane['path']
        
        # Build drag payload
        urls = self.drag_payload_builder.build_payload(
            selected_files,
            focused_item,
            current_dir
        )
        
        if not urls:
            # Payload building failed - check for error message
            error_msg = self.drag_payload_builder.get_last_error()
            if error_msg:
                # Show error dialog to user
                from tfm_quick_choice_bar import QuickChoiceBarHelpers
                QuickChoiceBarHelpers.show_error_dialog(
                    self.quick_choice_bar,
                    error_msg,
                    callback=lambda _: self.mark_dirty()
                )
            
            # Reset gesture detector
            self.drag_gesture_detector.reset()
            return False
        
        # Create drag image text
        if len(urls) == 1:
            # Single file - show filename
            if focused_item:
                drag_text = focused_item.name
            else:
                drag_text = "1 file"
        else:
            # Multiple files - show count
            drag_text = f"{len(urls)} files"
        
        # Start drag session
        success = self.drag_session_manager.start_drag(
            urls,
            drag_text,
            completion_callback=self._on_drag_completed
        )
        
        if not success:
            # Drag session failed to start
            # Check if backend doesn't support drag-and-drop
            if not self.renderer.supports_drag_and_drop():
                # Terminal mode - no error message (expected limitation)
                self.logger.info("Drag-and-drop not available in terminal mode")
            else:
                # Desktop mode but drag failed - show error
                from tfm_quick_choice_bar import QuickChoiceBarHelpers
                QuickChoiceBarHelpers.show_error_dialog(
                    self.quick_choice_bar,
                    "Failed to start drag operation. The system may have rejected the drag.",
                    callback=lambda _: self.mark_dirty()
                )
            
            self.drag_gesture_detector.reset()
            return False
        
        self.logger.info(f"Drag initiated: {drag_text}")
        return True
    
    def _on_drag_completed(self, completed: bool) -> None:
        """
        Called when drag session completes or is cancelled.
        
        This callback is invoked by the drag session manager when the drag
        operation finishes, either successfully (dropped on valid target) or
        cancelled (dropped on invalid target or ESC pressed).
        
        Args:
            completed: True if drag completed successfully, False if cancelled
        """
        if completed:
            self.logger.info("Drag completed successfully")
        else:
            self.logger.info("Drag was cancelled")
        
        # Reset gesture detector
        self.drag_gesture_detector.reset()
        
        # Redraw UI to restore normal state
        self.mark_dirty()
    
    def render(self, renderer) -> None:
        """
        Render the FileManager main screen.
        
        This method renders the complete main screen including header, file panes,
        log pane, status bar, and any active dialogs (quick_edit_bar, quick_choice_bar).
        It only performs a full redraw when needed.
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        # Only do full redraw when needed
        if self.needs_redraw():
            # Clear screen with proper background
            self.clear_screen_with_background()
            
            # Draw interface components
            self.draw_header()
            self.draw_files()
            self.draw_log_pane()
            self.draw_status()
            
            # Get dimensions for drawing overlays
            height, width = self.renderer.get_dimensions()
            status_y = height - 1
            
            # Draw general dialog if active (for text input in status bar)
            if self.quick_edit_bar.is_active:
                self.quick_edit_bar.draw()
            
            # Draw quick choice bar if active
            if self.quick_choice_bar.is_active:
                self.quick_choice_bar.draw(status_y, width)
            
            # Note: Don't call renderer.refresh() here - UILayerStack will do it
    
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen.
        
        The FileManager main screen always occupies the full terminal screen.
        
        Returns:
            True (main screen is always full-screen)
        """
        return True
    
    def needs_redraw(self) -> bool:
        """
        Query if this layer needs redrawing.
        
        Returns:
            True if the layer needs redrawing, False otherwise
        """
        return self._dirty
    
    def mark_dirty(self) -> None:
        """
        Mark this layer as needing a redraw.
        
        This is called by the layer stack when a lower layer has been redrawn,
        or by the layer itself when its content changes.
        """
        self._dirty = True
    
    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after rendering.
        
        This is called by the layer stack after successfully rendering this layer.
        """
        self._dirty = False
    
    def should_close(self) -> bool:
        """
        Query if this layer wants to close.
        
        FileManager is the bottom layer and never closes itself.
        Application quit is handled through the should_quit flag
        which is checked in the main loop.
        
        Returns:
            False (bottom layer never closes)
        """
        return False
    
    def on_activate(self) -> None:
        """
        Called when this layer becomes the top layer.
        
        The FileManager main screen is typically always active as the bottom
        layer, so no special activation is needed. However, if it becomes
        the top layer again after a dialog/viewer is closed, we mark it
        dirty to ensure it's redrawn.
        """
        # Main screen is always active, but mark dirty to ensure redraw
        # when it becomes the top layer again
        self._dirty = True
    
    def on_deactivate(self) -> None:
        """
        Called when this layer is no longer the top layer.
        
        The FileManager main screen remains active even when covered by
        dialogs or viewers, so no special deactivation is needed.
        """
        # Main screen remains active even when covered by dialogs
        pass
    
    def is_desktop_mode(self):
        """Check if running in desktop mode.
        
        Returns:
            bool: True if renderer supports menu bar (desktop mode)
        """
        return hasattr(self.renderer, 'set_menu_bar')
    
    def is_in_input_mode(self) -> bool:
        """
        Check if TFM is currently in an input mode that should block mouse events.
        
        This method checks if any of the following input modes are active:
        - Quick Edit Bar (for editing filenames and paths)
        - Quick Choice Bar (for confirmation dialogs)
        - I-search mode in Text Viewer (for incremental search)
        
        Uses defensive hasattr() checks to handle cases where components
        may not be initialized or attributes may not exist.
        
        Returns:
            True if in an input mode (quick edit, quick choice, or i-search),
            False otherwise.
        """
        # Check quick edit bar
        if hasattr(self, 'quick_edit_bar') and hasattr(self.quick_edit_bar, 'is_active'):
            if self.quick_edit_bar.is_active:
                return True
        
        # Check quick choice bar
        if hasattr(self, 'quick_choice_bar') and hasattr(self.quick_choice_bar, 'is_active'):
            if self.quick_choice_bar.is_active:
                return True
        
        # Check text viewer i-search mode
        # Text viewer is dynamically created and pushed onto the UI layer stack
        # Check if the top layer is a text viewer in isearch mode
        if hasattr(self, 'ui_layer_stack'):
            top_layer = self.ui_layer_stack.get_top_layer()
            if hasattr(top_layer, 'isearch_mode') and top_layer.isearch_mode:
                return True
        
        return False
    
    def _setup_menu_bar(self):
        """Initialize menu bar for desktop mode."""
        if not self.menu_manager:
            return
        
        try:
            menu_structure = self.menu_manager.get_menu_structure()
            self.renderer.set_menu_bar(menu_structure)
            self.logger.info("Menu bar initialized for desktop mode")
            
            # Set initial menu states to reflect current application state
            self._update_menu_states()
        except Exception as e:
            self.logger.error(f"Failed to initialize menu bar: {e}")
    
    def _update_menu_states(self):
        """
        Update menu item states based on current application state.
        
        This is called when application state changes that affect menu items
        (e.g., file selection changes, clipboard changes).
        """
        if not self.is_desktop_mode() or not self.menu_manager:
            return
        
        try:
            states = self.menu_manager.update_menu_states()
            for item_id, enabled in states.items():
                self.renderer.update_menu_item_state(item_id, enabled)
        except Exception as e:
            self.logger.error(f"Failed to update menu states: {e}")
    
    def _handle_menu_event(self, event):
        """Handle menu selection events.
        
        Args:
            event: MenuEvent with item_id
        
        Returns:
            bool: True if event was handled
        """
        if not isinstance(event, MenuEvent):
            return False
        
        item_id = event.item_id
        
        # App menu
        if item_id == MenuManager.APP_ABOUT:
            return self._action_show_about()
        elif item_id == MenuManager.APP_QUIT:
            return self._action_quit()
        
        # File menu
        elif item_id == MenuManager.FILE_NEW_FILE:
            return self._action_create_file()
        elif item_id == MenuManager.FILE_NEW_FOLDER:
            return self._action_create_directory()
        elif item_id == MenuManager.FILE_OPEN:
            return self._action_open_file()
        elif item_id == MenuManager.FILE_VIEW:
            return self._action_view_file()
        elif item_id == MenuManager.FILE_EDIT:
            return self._action_edit_file()
        elif item_id == MenuManager.FILE_COPY_TO_OTHER_PANE:
            return self._action_copy_to_other_pane()
        elif item_id == MenuManager.FILE_MOVE_TO_OTHER_PANE:
            return self._action_move_to_other_pane()
        elif item_id == MenuManager.FILE_DELETE:
            return self._action_delete()
        elif item_id == MenuManager.FILE_RENAME:
            return self._action_rename()
        elif item_id == MenuManager.FILE_PROPERTIES:
            return self._action_show_properties()
        
        # Edit menu
        elif item_id == MenuManager.EDIT_SELECT_ALL:
            return self._action_select_all()
        elif item_id == MenuManager.EDIT_COPY_NAMES:
            return self._action_copy_names()
        elif item_id == MenuManager.EDIT_COPY_PATHS:
            return self._action_copy_paths()
        
        # View menu
        elif item_id == MenuManager.VIEW_SHOW_HIDDEN:
            return self._action_toggle_hidden()
        elif item_id == MenuManager.VIEW_SORT_BY_NAME:
            return self._action_sort_by('name')
        elif item_id == MenuManager.VIEW_SORT_BY_SIZE:
            return self._action_sort_by('size')
        elif item_id == MenuManager.VIEW_SORT_BY_DATE:
            return self._action_sort_by('date')
        elif item_id == MenuManager.VIEW_SORT_BY_EXTENSION:
            return self._action_sort_by('extension')
        elif item_id == MenuManager.VIEW_REFRESH:
            return self._action_refresh()
        elif item_id == MenuManager.VIEW_MOVE_PANE_DIVIDER_LEFT:
            return self._action_pane_left()
        elif item_id == MenuManager.VIEW_MOVE_PANE_DIVIDER_RIGHT:
            return self._action_pane_right()
        elif item_id == MenuManager.VIEW_MOVE_LOG_DIVIDER_UP:
            return self._action_log_up()
        elif item_id == MenuManager.VIEW_MOVE_LOG_DIVIDER_DOWN:
            return self._action_log_down()
        
        # Go menu
        elif item_id == MenuManager.GO_PARENT:
            return self._action_go_parent()
        elif item_id == MenuManager.GO_HOME:
            return self._action_go_home()
        elif item_id == MenuManager.GO_DRIVES:
            return self._action_show_drives()
        elif item_id == MenuManager.GO_FAVORITES:
            return self._action_show_favorites()
        elif item_id == MenuManager.GO_RECENT:
            return self._action_show_recent()
        
        # Tools menu
        elif item_id == MenuManager.TOOLS_SEARCH_FILES:
            return self._action_search_files()
        elif item_id == MenuManager.TOOLS_SEARCH_CONTENT:
            return self._action_search_content()
        elif item_id == MenuManager.TOOLS_COMPARE_FILES:
            return self._action_compare_files()
        elif item_id == MenuManager.TOOLS_COMPARE_DIRECTORIES:
            return self._action_compare_directories()
        elif item_id == MenuManager.TOOLS_COMPARE_SELECTION:
            return self._action_compare_selection()
        elif item_id == MenuManager.TOOLS_CREATE_ARCHIVE:
            return self._action_create_archive()
        elif item_id == MenuManager.TOOLS_EXTRACT_ARCHIVE:
            return self._action_extract_archive()
        elif item_id == MenuManager.TOOLS_EXTERNAL_PROGRAMS:
            return self._action_external_programs()
        
        # Help menu
        elif item_id == MenuManager.HELP_KEYBOARD_SHORTCUTS:
            return self._action_show_help()
        elif item_id == MenuManager.HELP_ABOUT:
            return self._action_show_about()
        elif item_id == MenuManager.HELP_REPORT_ISSUE:
            return self._action_report_issue()
        
        # View menu
        elif item_id == MenuManager.VIEW_SHOW_HIDDEN:
            return self._action_toggle_hidden()
        elif item_id == MenuManager.VIEW_SORT_BY_NAME:
            return self._action_sort_by('name')
        elif item_id == MenuManager.VIEW_SORT_BY_SIZE:
            return self._action_sort_by('size')
        elif item_id == MenuManager.VIEW_SORT_BY_DATE:
            return self._action_sort_by('date')
        elif item_id == MenuManager.VIEW_SORT_BY_EXTENSION:
            return self._action_sort_by('extension')
        elif item_id == MenuManager.VIEW_REFRESH:
            return self._action_refresh()
        elif item_id == MenuManager.VIEW_MOVE_PANE_DIVIDER_LEFT:
            return self._action_pane_left()
        elif item_id == MenuManager.VIEW_MOVE_PANE_DIVIDER_RIGHT:
            return self._action_pane_right()
        elif item_id == MenuManager.VIEW_MOVE_LOG_DIVIDER_UP:
            return self._action_log_up()
        elif item_id == MenuManager.VIEW_MOVE_LOG_DIVIDER_DOWN:
            return self._action_log_down()
        
        # Go menu
        elif item_id == MenuManager.GO_PARENT:
            return self._action_go_parent()
        elif item_id == MenuManager.GO_HOME:
            return self._action_go_home()
        elif item_id == MenuManager.GO_FAVORITES:
            return self._action_show_favorites()
        elif item_id == MenuManager.GO_RECENT:
            return self._action_show_recent()
        
        # Help menu
        elif item_id == MenuManager.HELP_ABOUT:
            return self._action_show_about()
        elif item_id == MenuManager.HELP_REPORT_ISSUE:
            return self._action_report_issue()
        
        return False
    
    # Menu action methods
    def _action_show_about(self):
        """Show About TFM information in the log pane."""
        from tfm_const import VERSION, GITHUB_URL
        
        # Add empty line and separator before
        print("─" * 80)
        
        # TFM ASCII art logo (filled block style) with version and GitHub on the right
        logo_lines = [
            "  ████████╗███████╗███╗   ███╗",
            "  ╚══██╔══╝██╔════╝████╗ ████║",
            "     ██║   █████╗  ██╔████╔██║",
            "     ██║   ██╔══╝  ██║╚██╔╝██║",
            "     ██║   ██║     ██║ ╚═╝ ██║",
            "     ╚═╝   ╚═╝     ╚═╝     ╚═╝"
        ]
        
        # Add version and GitHub info on the right side of the logo
        info_lines = [
            "",
            "",
            f"Version: {VERSION}",
            f"GitHub: {GITHUB_URL}",
            "",
            "",
        ]
        
        # Print logo with info on the right
        for logo_line, info_line in zip(logo_lines, info_lines):
            if info_line:
                print(f"{logo_line}  {info_line}")
            else:
                print(logo_line)
        
        # Add empty line and separator after
        print("─" * 80)
        
        # Trigger redraw to show the messages
        self.mark_dirty()
        return True
    
    def _action_create_file(self):
        """Create a new file."""
        self.enter_create_file_mode()
        return True
    
    def _action_create_directory(self):
        """Create a new directory."""
        self.enter_create_directory_mode()
        return True
    
    def _action_open_file(self):
        """Open the selected file or directory."""
        self.handle_enter()
        return True
    
    def _action_delete(self):
        """Delete selected files."""
        self.file_operations_ui.delete_selected_files()
        return True
    
    def _action_rename(self):
        """Rename selected file."""
        self.enter_rename_mode()
        return True
    
    def _action_quit(self):
        """Quit the application."""
        self.should_quit = True
        return True
    
    def _action_copy_to_other_pane(self):
        """Copy selected files to the opposite pane's directory."""
        self.file_operations_ui.copy_selected_files()
        return True
    
    def _action_move_to_other_pane(self):
        """Move selected files to the opposite pane's directory."""
        self.file_operations_ui.move_selected_files()
        return True
    
    def _action_view_file(self):
        """View the selected file."""
        self.view_file()
        return True
    
    def _action_edit_file(self):
        """Edit the selected file."""
        self.edit_file()
        return True
    
    def _action_show_properties(self):
        """Show file properties."""
        self.show_file_details()
        return True
    
    def _action_show_drives(self):
        """Show drives dialog."""
        self.show_drives_dialog()
        return True
    
    def _action_search_files(self):
        """Show search files dialog."""
        self.show_search_dialog('filename')
        return True
    
    def _action_search_content(self):
        """Show search content dialog."""
        self.show_search_dialog('content')
        return True
    
    def _action_compare_files(self):
        """Compare two selected files."""
        self.diff_selected_files()
        return True
    
    def _action_compare_directories(self):
        """Compare directories."""
        self.show_directory_diff()
        return True
    
    def _action_compare_selection(self):
        """Show compare selection dialog."""
        self.show_compare_selection_dialog()
        return True
    
    def _action_create_archive(self):
        """Create archive."""
        self.enter_create_archive_mode()
        return True
    
    def _action_extract_archive(self):
        """Extract archive."""
        self.extract_selected_archive()
        return True
    
    def _action_external_programs(self):
        """Show external programs dialog."""
        self.show_programs_dialog()
        return True
    
    def _action_show_help(self):
        """Show help dialog."""
        self.show_help_dialog()
        return True
    
    def _action_select_all(self):
        """Select all items."""
        self.select_all()
        return True
    
    def _action_copy_names(self):
        """Copy file name(s) of selected files to system clipboard."""
        if not self.is_desktop_mode():
            self.logger.error("Clipboard operations only available in desktop mode")
            return False
        
        if not self.renderer.supports_clipboard():
            self.logger.error("Clipboard not supported on this backend")
            return False
        
        current_pane = self.get_current_pane()
        
        # Get selected files or focused file
        files_to_copy = []
        if current_pane['selected_files']:
            # Use files from the pane's file list that match selected_files
            for file_obj in current_pane['files']:
                if str(file_obj) in current_pane['selected_files']:
                    if file_obj.name != '..':
                        files_to_copy.append(file_obj)
        elif current_pane['files'] and 0 <= current_pane['focused_index'] < len(current_pane['files']):
            focused_file = current_pane['files'][current_pane['focused_index']]
            if focused_file.name != '..':
                files_to_copy.append(focused_file)
        
        if not files_to_copy:
            self.logger.error("No files to copy names from")
            return False
        
        # Build text with file names (one per line)
        names = [f.name for f in files_to_copy]
        text = '\n'.join(names)
        
        # Copy to clipboard
        if self.renderer.set_clipboard_text(text):
            count = len(files_to_copy)
            self.logger.info(f"Copied {count} file name{'s' if count > 1 else ''} to clipboard")
            self.mark_dirty()
            return True
        else:
            self.logger.error("Failed to copy to clipboard")
            return False
    
    def _action_copy_paths(self):
        """Copy full path(s) of selected files to system clipboard."""
        if not self.is_desktop_mode():
            self.logger.error("Clipboard operations only available in desktop mode")
            return False
        
        if not self.renderer.supports_clipboard():
            self.logger.error("Clipboard not supported on this backend")
            return False
        
        current_pane = self.get_current_pane()
        
        # Get selected files or focused file
        files_to_copy = []
        if current_pane['selected_files']:
            # Use files from the pane's file list that match selected_files
            for file_obj in current_pane['files']:
                if str(file_obj) in current_pane['selected_files']:
                    if file_obj.name != '..':
                        files_to_copy.append(file_obj)
        elif current_pane['files'] and 0 <= current_pane['focused_index'] < len(current_pane['files']):
            focused_file = current_pane['files'][current_pane['focused_index']]
            if focused_file.name != '..':
                files_to_copy.append(focused_file)
        
        if not files_to_copy:
            self.logger.error("No files to copy paths from")
            return False
        
        # Build text with full paths (one per line)
        paths = [str(f.resolve()) for f in files_to_copy]
        text = '\n'.join(paths)
        
        # Copy to clipboard
        if self.renderer.set_clipboard_text(text):
            count = len(files_to_copy)
            self.logger.info(f"Copied {count} full path{'s' if count > 1 else ''} to clipboard")
            self.mark_dirty()
            return True
        else:
            self.logger.error("Failed to copy to clipboard")
            return False
    
    def _action_toggle_hidden(self):
        """Toggle showing hidden files."""
        self.file_list_manager.show_hidden = not self.file_list_manager.show_hidden
        self.refresh_files()
        self.mark_dirty()
        status = "showing" if self.file_list_manager.show_hidden else "hiding"
        self.logger.info(f"Now {status} hidden files")
        return True
    
    def _action_sort_by(self, sort_type):
        """Sort files by specified type.
        
        Args:
            sort_type: Sort type ('name', 'size', 'date', 'extension')
        """
        current_pane = self.get_current_pane()
        current_pane['sort_mode'] = sort_type
        self.refresh_files(current_pane)
        self.mark_dirty()
        self.logger.info(f"Sorted by {sort_type}")
        return True
    
    def _action_refresh(self):
        """Refresh file list."""
        self.refresh_files()
        self.mark_dirty()
        self.logger.info("Refreshed file list")
        return True
    
    def _action_pane_left(self):
        """Move pane divider left."""
        self.adjust_pane_boundary('left')
        return True
    
    def _action_pane_right(self):
        """Move pane divider right."""
        self.adjust_pane_boundary('right')
        return True
    
    def _action_log_up(self):
        """Move log divider up."""
        self.adjust_log_boundary('up')
        return True
    
    def _action_log_down(self):
        """Move log divider down."""
        self.adjust_log_boundary('down')
        return True
    
    def _action_go_parent(self):
        """Navigate to parent directory."""
        current_pane = self.get_current_pane()
        parent = current_pane['path'].parent
        if parent != current_pane['path']:  # Not at root
            self.save_cursor_position(current_pane)
            current_pane['path'] = parent
            current_pane['focused_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            self.refresh_files(current_pane)
            self.restore_cursor_position(current_pane)
            self.mark_dirty()
        return True
    
    def _action_go_home(self):
        """Navigate to home directory."""
        current_pane = self.get_current_pane()
        home_path = Path.home()
        if current_pane['path'] != home_path:
            self.save_cursor_position(current_pane)
            current_pane['path'] = home_path
            current_pane['focused_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            self.refresh_files(current_pane)
            self.restore_cursor_position(current_pane)
            self.mark_dirty()
        return True
    
    def _action_show_favorites(self):
        """Show favorites dialog."""
        self.show_favorite_directories()
        return True
    
    def _action_show_recent(self):
        """Show recent locations dialog."""
        self.show_history()
        return True
    
    def _action_report_issue(self):
        """Open GitHub issues page in browser."""
        from tfm_const import GITHUB_URL
        try:
            import webbrowser
            issues_url = f"{GITHUB_URL}/issues"
            webbrowser.open(issues_url)
            self.logger.info(f"Opened {issues_url} in browser")
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
            self.logger.info(f"Please visit: {GITHUB_URL}/issues")
        self.mark_dirty()
        return True
        
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
            max_len = width - x
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
            
            # Set default caret position to bottom-left corner
            # This keeps the caret out of the way when not editing text
            height, width = self.renderer.get_dimensions()
            self.renderer.set_caret_position(0, height - 1)
            
        except Exception as e:
            # Any other error, use regular clear
            self.logger.error(f"Warning: Screen clear with background failed: {e}")
            self.renderer.clear()

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
        success, message = self.file_list_manager.toggle_selection(current_pane, move_cursor=True, direction=1)
        if success:
            self.logger.info(message)
            self.adjust_scroll_for_focus(current_pane)
            
    def toggle_selection_up(self):
        """Toggle selection of current file/directory and move to previous item"""
        current_pane = self.get_current_pane()
        success, message = self.file_list_manager.toggle_selection(current_pane, move_cursor=True, direction=-1)
        if success:
            self.logger.info(message)
            self.adjust_scroll_for_focus(current_pane)
    
    def toggle_all_files_selection(self):
        """Toggle selection status of all files (not directories) in current pane"""
        current_pane = self.get_current_pane()
        success, message = self.file_list_manager.toggle_all_files_selection(current_pane)
        if success:
            self.logger.info(message)
            self.mark_dirty()
    
    def toggle_all_items_selection(self):
        """Toggle selection status of all items (files and directories) in current pane"""
        current_pane = self.get_current_pane()
        success, message = self.file_list_manager.toggle_all_items_selection(current_pane)
        if success:
            self.logger.info(message)
            self.mark_dirty()
    
    def unselect_all(self):
        """Unselect all items in current pane"""
        current_pane = self.get_current_pane()
        if current_pane['selected_files']:
            current_pane['selected_files'].clear()
            self.logger.info("Unselected all items")
            self.mark_dirty()
    
    def select_all(self):
        """Select all items (files and directories) in current pane"""
        current_pane = self.get_current_pane()
        selected_count = 0
        for file_path in current_pane['files']:
            if file_path not in current_pane['selected_files']:
                current_pane['selected_files'].add(file_path)
                selected_count += 1
        
        if selected_count > 0:
            self.logger.info(f"Selected all {len(current_pane['selected_files'])} items")
            self.mark_dirty()
        elif current_pane['selected_files']:
            self.logger.info(f"All {len(current_pane['selected_files'])} items already selected")
    
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
                
                self.pane_manager.adjust_scroll_for_focus(current_pane, display_height)
                self.mark_dirty()
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
                    current_pane['focused_index'] = 0
                    current_pane['scroll_offset'] = 0
                
                self.mark_dirty()
    
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
                
                self.pane_manager.adjust_scroll_for_focus(other_pane, display_height)
                self.mark_dirty()
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
                    other_pane['focused_index'] = 0
                    other_pane['scroll_offset'] = 0
                
                self.mark_dirty()
    
    def sync_cursor_to_other_pane(self):
        """Move cursor in current pane to the same filename as the other pane's cursor"""
        if self.pane_manager.sync_cursor_to_other_pane(print):
            # Adjust scroll offset if needed to keep selection visible
            current_pane = self.get_current_pane()
            height, width = self.renderer.get_dimensions()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            self.pane_manager.adjust_scroll_for_focus(current_pane, display_height)
            self.mark_dirty()
    
    def sync_cursor_from_current_pane(self):
        """Move cursor in other pane to the same filename as the current pane's cursor"""
        if self.pane_manager.sync_cursor_from_current_pane(print):
            # Adjust scroll offset if needed to keep selection visible
            other_pane = self.get_inactive_pane()
            height, width = self.renderer.get_dimensions()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            self.pane_manager.adjust_scroll_for_focus(other_pane, display_height)
            self.mark_dirty()
        
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
    
    def adjust_scroll_for_focus(self, pane_data):
        """Adjust scroll for selection - wrapper for pane_manager method"""
        height, width = self.renderer.get_dimensions()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        return self.pane_manager.adjust_scroll_for_focus(pane_data, display_height)
    
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
    
    def get_date_column_width(self):
        """
        Calculate the date column width based on current date format setting.
        
        Returns:
            int: Width in characters for the date column
        """
        from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT
        
        date_format = getattr(self.config, 'DATE_FORMAT', 'short')
        
        if date_format == DATE_FORMAT_FULL:
            # YYYY-MM-DD HH:mm:ss = 19 characters
            return 19
        else:  # DATE_FORMAT_SHORT (default)
            # YY-MM-DD HH:mm = 14 characters
            return 14

    def apply_filter(self):
        """Apply filter - wrapper for file_list_manager method"""
        current_pane = self.get_current_pane()
        filter_pattern = self.filter_editor.get_text()
        count = self.file_list_manager.apply_filter(current_pane, filter_pattern)
        
        # Log the filter action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        
        if filter_pattern:
            self.logger.info(f"Applied filter '{filter_pattern}' to {pane_name} pane")
            self.logger.info(f"Showing {count} items")
        
        self.mark_dirty()
    
    def clear_filter(self):
        """Clear filter - wrapper for file_list_manager method"""
        current_pane = self.get_current_pane()
        
        if self.file_list_manager.clear_filter(current_pane):
            # Log the clear action
            pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
            
            self.logger.info(f"Cleared filter from {pane_name} pane")
            
            self.mark_dirty()
    
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
    
    def run(self):
        """
        Run the main application loop using callback-based event handling.
        
        Events are delivered via the TFMEventCallback that was set up during
        initialization. The event loop processes events and redraws the interface.
        Uses adaptive FPS to reduce CPU usage during idle periods.
        """
        # Draw initial interface
        self.draw_interface()
        
        # Run event loop with drawing
        while True:
            # Check if we should quit
            if self.should_quit:
                break
            
            # Check for startup redraw trigger
            if hasattr(self, 'startup_time') and time.time() - self.startup_time >= 0.033:
                self.mark_dirty()
                delattr(self, 'startup_time')
            
            # Check for log updates
            if self.log_manager.has_log_updates():
                self.mark_dirty()
            
            # Get adaptive timeout based on activity level
            timeout_ms = self.adaptive_fps.get_timeout_ms()

            # Process one event with adaptive timeout (events delivered via callbacks)
            if 'event' in self.profiling_targets:
                import cProfile
                cProfile.runctx(
                    "self.renderer.run_event_loop_iteration(timeout_ms=timeout_ms)",
                    globals(),
                    locals()
                )
            else:
                self.renderer.run_event_loop_iteration(timeout_ms=timeout_ms)
            

            
            # Check if top layer wants to close and pop it if so
            # This must be done after event processing but before drawing
            # to handle layers that want to close due to system events
            if self.ui_layer_stack.check_and_close_top_layer():
                self.mark_dirty()
            
            # Draw interface after event processing
            self.draw_interface()
        
        # Restore stdout/stderr before exiting
        self.restore_stdio()
        
        # Save application state before exiting
        self.save_application_state()

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
            self.file_list_manager.refresh_files(pane_data)
    
    def sort_entries(self, entries, sort_mode, reverse=False):
        """Sort file entries based on the specified mode"""
        return self.file_list_manager.sort_entries(entries, sort_mode, reverse)
    
    def get_sort_description(self, pane_data):
        """Get a human-readable description of the current sort mode"""
        return self.file_list_manager.get_sort_description(pane_data)
            
    def get_file_info(self, path):
        """Get file information for display"""
        return self.file_list_manager.get_file_info(path)
            
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
        
        # Clear header area
        try:
            color_pair, attributes = get_header_color()
            self.renderer.draw_text(0, 0, " " * width, color_pair=color_pair, attributes=attributes)
        except Exception:
            pass
        
        # Left pane path with safety checks
        if left_pane_width > 6:  # Minimum space needed
            left_path = self.format_path_display(self.pane_manager.left_pane['path'])
            max_left_path_width = max(1, left_pane_width - 4)
            # Use wide character aware truncation for path display
            if safe_get_display_width(left_path) > max_left_path_width:
                left_path = truncate_to_width(left_path, max_left_path_width, "…")
            
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
                right_path = truncate_to_width(right_path, max_right_path_width, "…")
                
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
        
        # Pre-calculate layout constants (once per pane, not per file)
        datetime_width = self.get_date_column_width()
        size_width = 8
        marker_width = 2
        usable_width = pane_width - 2
        
        # Determine layout mode based on pane width
        min_width_for_datetime = 2 + 1 + 16 + 1 + 4 + 1 + 8 + 1 + datetime_width
        show_datetime = pane_width >= min_width_for_datetime
        
        # Pre-calculate extension width once for the entire pane
        ext_width = self.calculate_max_extension_width(pane_data) if pane_width >= 20 else 0
        
        # Pre-calculate name width based on layout mode
        if pane_width < 20:
            max_name_width = max(1, pane_width - 5)
            name_width = None  # Will use max_name_width for truncation
        elif show_datetime:
            # Wide layout: marker + name + ext + size + datetime
            if ext_width > 0:
                name_width = usable_width - (13 + ext_width + datetime_width)
            else:
                name_width = usable_width - (12 + datetime_width)
        else:
            # Narrow layout: marker + name + ext + size (no datetime)
            if ext_width > 0:
                name_width = usable_width - (12 + ext_width)
            else:
                name_width = usable_width - 11
        
        # Cache for isearch matches (convert to set for O(1) lookup)
        isearch_match_set = set(self.isearch_matches) if self.isearch_mode and is_active else set()
        
        # Cache selected files set for O(1) lookup
        selected_set = pane_data['selected_files']
            
        # Draw files
        for i in range(display_height):
            file_index = i + pane_data['scroll_offset']
            y = i + 1  # Start after header
            
            if file_index >= len(pane_data['files']):
                break
                
            file_path = pane_data['files'][file_index]
            
            # Get file info (this is still per-file, but unavoidable)
            display_name = file_path.name
            is_dir = file_path.is_dir()
            size_str, mtime_str = self.get_file_info(file_path)
            
            # Fast lookups using pre-computed sets
            is_selected = str(file_path) in selected_set
            is_search_match = file_index in isearch_match_set
            is_focused = file_index == pane_data['focused_index']
            
            # Choose color
            is_executable = file_path.is_file() and os.access(file_path, os.X_OK)
            color = get_file_color(is_dir, is_executable, is_focused, is_active)
            
            # Add underline for search matches
            if is_search_match:
                color_pair, base_attrs = color
                color = (color_pair, base_attrs | TextAttribute.UNDERLINE)
            
            # Selection marker
            selection_marker = "●" if is_selected else " "
            
            # Format line based on pre-calculated layout
            if pane_width < 20:
                # Very narrow: just truncate name
                truncated_name = truncate_to_width(display_name, max_name_width, "…")
                line = f"{selection_marker} {truncated_name}"
            else:
                # Separate filename into basename and extension
                basename, extension = self.separate_filename_extension(display_name, is_dir)
                
                if show_datetime:
                    # Wide layout with datetime
                    if extension and ext_width > 0:
                        # Truncate and pad basename
                        if safe_get_display_width(basename) > name_width:
                            basename = truncate_to_width(basename, name_width, "…")
                        padded_basename = pad_to_width(basename, name_width, align='left')
                        padded_extension = pad_to_width(extension, ext_width, align='left')
                        line = f"{selection_marker} {padded_basename} {padded_extension} {size_str:>8} {mtime_str}"
                    else:
                        # No extension - use full width (name_width + ext_width + 1 space)
                        full_name_width = name_width + ext_width + (1 if ext_width > 0 else 0)
                        if safe_get_display_width(display_name) > full_name_width:
                            display_name = truncate_to_width(display_name, full_name_width, "…")
                        padded_name = pad_to_width(display_name, full_name_width, align='left')
                        line = f"{selection_marker} {padded_name} {size_str:>8} {mtime_str}"
                else:
                    # Narrow layout without datetime
                    if extension and ext_width > 0:
                        if safe_get_display_width(basename) > name_width:
                            basename = truncate_to_width(basename, name_width, "…")
                        padded_basename = pad_to_width(basename, name_width, align='left')
                        padded_extension = pad_to_width(extension, ext_width, align='left')
                        line = f"{selection_marker} {padded_basename} {padded_extension} {size_str:>8}"
                    else:
                        # No extension - use full width (name_width + ext_width + 1 space)
                        full_name_width = name_width + ext_width + (1 if ext_width > 0 else 0)
                        if safe_get_display_width(display_name) > full_name_width:
                            display_name = truncate_to_width(display_name, full_name_width, "…")
                        padded_name = pad_to_width(display_name, full_name_width, align='left')
                        line = f"{selection_marker} {padded_name} {size_str:>8}"
            
            try:
                # Final truncation if needed
                max_line_width = pane_width - 2
                if safe_get_display_width(line) > max_line_width:
                    line = truncate_to_width(line, max_line_width, "")
                
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
            status_line = " " * width
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
            status_line = " " * width
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
        
        if self.file_list_manager.show_hidden:
            status_parts.append("showing hidden")

        left_status = f"({', '.join(status_parts)})" if status_parts else ""
        
        # Build help message dynamically from config - detailed controls available in help dialog
        help_keys, _ = get_keys_for_action('help')
        help_key = format_key_for_display(help_keys[0]) if help_keys else '?'
        
        switch_keys, _ = get_keys_for_action('switch_pane')
        switch_key = format_key_for_display(switch_keys[0]) if switch_keys else 'Tab'
        
        open_keys, _ = get_keys_for_action('open_item')
        open_key = format_key_for_display(open_keys[0]) if open_keys else 'Enter'
        
        quit_keys, _ = get_keys_for_action('quit')
        quit_key = format_key_for_display(quit_keys[0]) if quit_keys else 'q'
        
        controls = f"Press {help_key} for help  •  {switch_key}:switch panes  •  {open_key}:open  •  {quit_key}:quit"
        
        # Draw status line with background color
        # Fill entire status line with background color
        status_line = " " * width
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
            
        focused_file = current_pane['files'][current_pane['focused_index']]
        
        # Parent directory (..) is no longer shown
        if focused_file.is_dir():
            try:
                # Save current cursor position before changing directory
                self.save_cursor_position(current_pane)
                
                current_pane['path'] = focused_file
                current_pane['focused_index'] = 0
                current_pane['scroll_offset'] = 0
                current_pane['selected_files'].clear()  # Clear selections when changing directory
                self.refresh_files(current_pane)
                
                # Try to restore cursor position for this directory
                if not self.restore_cursor_position(current_pane):
                    # If no history found, default to first item
                    current_pane['focused_index'] = 0
                    current_pane['scroll_offset'] = 0
                
                self.mark_dirty()
            except PermissionError:
                self.logger.error("ERROR: Permission denied")
        elif self.archive_operations.is_archive(focused_file):
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
                archive_uri = f"archive://{focused_file.absolute()}#"
                archive_path = Path(archive_uri)
                
                # Navigate into the archive
                current_pane['path'] = archive_path
                current_pane['focused_index'] = 0
                current_pane['scroll_offset'] = 0
                current_pane['selected_files'].clear()  # Clear selections when entering archive
                self.refresh_files(current_pane)
                
                # Default to first item
                current_pane['focused_index'] = 0
                current_pane['scroll_offset'] = 0
                
                self.mark_dirty()
                self.logger.info(f"Entered archive: {focused_file.name}")
            except FileNotFoundError as e:
                # Archive file doesn't exist
                user_msg = getattr(e, 'args', ['Archive file not found'])[1] if len(getattr(e, 'args', [])) > 1 else "Archive file not found"
                self.logger.error(f"Archive not found: {focused_file}: {e}")
            except ArchiveCorruptedError as e:
                # Archive is corrupted
                self.logger.error(f"Corrupted archive: {focused_file}: {e}")
            except ArchiveFormatError as e:
                # Unsupported or invalid format
                self.logger.error(f"Invalid archive format: {focused_file}: {e}")
            except ArchivePermissionError as e:
                # Permission denied
                self.logger.error(f"Permission denied: {focused_file}: {e}")
            except ArchiveDiskSpaceError as e:
                # Insufficient disk space
                self.logger.error(f"Insufficient disk space: {e}")
            except ArchiveError as e:
                # Generic archive error
                self.logger.error(f"Archive error: {focused_file}: {e}")
            except Exception as e:
                # Unexpected error
                self.logger.error(f"Unexpected error opening archive: {focused_file}: {e}")
        else:
            # For files, try to use file association for 'open' action
            filename = focused_file.name
            command = get_program_for_file(filename, 'open')
            
            if command:
                # Use configured program from file associations
                try:
                    # Suspend curses
                    self.external_program_manager.suspend_curses()
                    
                    # Launch the program
                    result = subprocess.run(command + [str(focused_file)], 
                                          cwd=str(current_pane['path']))
                    
                    # Resume curses
                    self.external_program_manager.resume_curses()
                    
                    if result.returncode == 0:
                        self.logger.info(f"Opened file: {focused_file.name}")
                    else:
                        self.logger.info(f"Program exited with code {result.returncode}")
                    
                    self.mark_dirty()
                    
                except Exception as e:
                    # Resume curses even if there's an error
                    self.external_program_manager.resume_curses()
                    self.logger.error(f"Error opening file: {e}")
                    self.mark_dirty()
            elif is_text_file(focused_file):
                # Fallback to text viewer for text files without association
                viewer = create_text_viewer(self.renderer, focused_file, self.ui_layer_stack)
                if viewer:
                    # Push viewer onto layer stack
                    self.push_layer(viewer)
                    self.renderer.set_cursor_visibility(False)
                    self.mark_dirty()
                    self.logger.info(f"Viewing file: {focused_file.name}")
                else:
                    self.logger.info(f"File: {focused_file.name}")
            else:
                # For files without association, show file info
                self.logger.info(f"File: {focused_file.name}")
            
    def find_matches(self, pattern):
        """Find all files matching the fnmatch patterns in current pane
        
        Supports multiple space-delimited patterns where all patterns must match.
        For example: "ab*c 12?3" will match files that contain both "*ab*c*" and "*12?3*"
        """
        current_pane = self.get_current_pane()
        return self.file_list_manager.find_matches(current_pane, pattern, match_all=True, return_indices_only=True)
        
    def update_isearch_matches(self):
        """Update isearch matches and move cursor to nearest match"""
        self.isearch_matches = self.find_matches(self.isearch_pattern)
        
        if self.isearch_matches:
            current_pane = self.get_current_pane()
            current_index = current_pane['focused_index']
            
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
            current_pane['focused_index'] = next_match
            self.isearch_match_index = self.isearch_matches.index(next_match)
            
            # Ensure the selected item is visible (adjust scroll if needed)
            self.adjust_scroll_for_focus(current_pane)
        else:
            self.isearch_match_index = 0
            
    def enter_isearch_mode(self):
        """Enter isearch mode"""
        self.isearch_mode = True
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        self.mark_dirty()
        
    def exit_isearch_mode(self):
        """Exit isearch mode"""
        self.isearch_mode = False
        self.isearch_pattern = ""
        self.isearch_matches = []
        self.isearch_match_index = 0
        self.mark_dirty()
    
    def enter_filter_mode(self):
        """Enter filename filter mode"""
        current_pane = self.get_current_pane()
        QuickEditBarHelpers.create_filter_dialog(self.quick_edit_bar, current_pane['filter_pattern'])
        self.quick_edit_bar.callback = self.on_filter_confirm
        self.quick_edit_bar.cancel_callback = self.on_filter_cancel
        self.mark_dirty()
        
    def on_filter_confirm(self, filter_text):
        """Handle filter confirmation"""
        current_pane = self.get_current_pane()
        count = self.file_list_manager.apply_filter(current_pane, filter_text)
        
        # Log the filter action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        
        if filter_text:
            self.logger.info(f"Applied filter '{filter_text}' to {pane_name} pane")
            self.logger.info(f"Showing {count} items")
        
        self.quick_edit_bar.hide()
        self.mark_dirty()
    
    def on_filter_cancel(self):
        """Handle filter cancellation"""
        self.quick_edit_bar.hide()
        self.mark_dirty()
    
    def apply_filter(self):
        """Apply the current filter pattern to the active pane"""
        current_pane = self.get_current_pane()
        filter_pattern = self.filter_editor.text
        current_pane['filter_pattern'] = filter_pattern
        current_pane['focused_index'] = 0  # Reset selection to top
        current_pane['scroll_offset'] = 0
        self.refresh_files(current_pane)
        
        # Log the filter action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        if filter_pattern:
            self.logger.info(f"Applied filter '{filter_pattern}' to {pane_name} pane")
        else:
            self.logger.info(f"Cleared filter from {pane_name} pane")
        
        self.mark_dirty()
    
    def clear_filter(self):
        """Clear the filter from the active pane"""
        current_pane = self.get_current_pane()
        current_pane['filter_pattern'] = ""
        current_pane['focused_index'] = 0  # Reset selection to top
        current_pane['scroll_offset'] = 0
        self.refresh_files(current_pane)
        
        # Log the clear action
        pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
        self.logger.info(f"Cleared filter from {pane_name} pane")
        
        self.mark_dirty()
    
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
            self.logger.info("No files to rename")
            return
            
        focused_file = current_pane['files'][current_pane['focused_index']]
        
        # Parent directory (..) is no longer shown, so no need to check for it
        
        # Check if this storage implementation supports directory renaming
        try:
            if focused_file.is_dir() and not focused_file.supports_directory_rename():
                self.logger.info("Directory renaming is not supported on this storage type due to performance and cost considerations")
                return
        except Exception as e:
            # Handle any errors gracefully and continue
            self.logger.warning(f"Warning: Could not check directory rename capability: {e}")
        
        # Enter rename mode using general dialog
        self.rename_file_path = focused_file
        QuickEditBarHelpers.create_rename_dialog(self.quick_edit_bar, focused_file.name, focused_file.name)
        self.quick_edit_bar.callback = self.on_rename_confirm
        self.quick_edit_bar.cancel_callback = self.on_rename_cancel
        self.mark_dirty()
        self.logger.info(f"Renaming: {focused_file.name}")
    
    def on_rename_confirm(self, new_name):
        """Handle rename confirmation"""
        if not self.rename_file_path or not new_name.strip():
            self.logger.error("Invalid rename operation")
            self.quick_edit_bar.hide()
            self.rename_file_path = None
            self.mark_dirty()
            return
        
        original_name = self.rename_file_path.name
        
        if new_name == original_name:
            self.logger.info("Name unchanged")
            self.quick_edit_bar.hide()
            self.rename_file_path = None
            self.mark_dirty()
            return
        
        try:
            # Perform the rename
            new_path = self.rename_file_path.parent / new_name
            
            # Check if target already exists
            if new_path.exists():
                self.logger.info(f"File '{new_name}' already exists")
                self.quick_edit_bar.hide()
                self.rename_file_path = None
                self.mark_dirty()
                return
            
            # Perform the rename
            self.rename_file_path.rename(new_path)
            self.logger.info(f"Renamed '{original_name}' to '{new_name}'")
            
            # Refresh the current pane
            current_pane = self.get_current_pane()
            self.refresh_files(current_pane)
            
            # Try to select the renamed file
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_name:
                    current_pane['focused_index'] = i
                    self.adjust_scroll_for_focus(current_pane)
                    break
            
            self.quick_edit_bar.hide()
            self.rename_file_path = None
            self.mark_dirty()
            
        except PermissionError:
            self.logger.error(f"Permission denied: Cannot rename '{original_name}'")
            self.quick_edit_bar.hide()
            self.rename_file_path = None
            self.mark_dirty()
        except OSError as e:
            self.logger.error(f"Error renaming file: {e}")
            self.quick_edit_bar.hide()
            self.rename_file_path = None
            self.mark_dirty()
    
    def on_rename_cancel(self):
        """Handle rename cancellation"""
        self.logger.info("Rename cancelled")
        self.quick_edit_bar.hide()
        self.rename_file_path = None
        self.mark_dirty()
    
    def enter_create_directory_mode(self):
        """Enter create directory mode"""
        current_pane = self.get_current_pane()
        
        # Check if current directory is writable (only for local paths)
        if current_pane['path'].get_scheme() == 'file' and not os.access(current_pane['path'], os.W_OK):
            self.logger.error(f"Permission denied: Cannot create directory in {current_pane['path']}")
            return
        
        # Enter create directory mode using general dialog
        QuickEditBarHelpers.create_create_directory_dialog(self.quick_edit_bar)
        self.quick_edit_bar.callback = self.on_create_directory_confirm
        self.quick_edit_bar.cancel_callback = self.on_create_directory_cancel
        self.mark_dirty()
        self.logger.info("Creating new directory...")
    
    def on_create_directory_confirm(self, dir_name):
        """Handle create directory confirmation"""
        if not dir_name.strip():
            self.logger.error("Invalid directory name")
            self.quick_edit_bar.hide()
            self.mark_dirty()
            return
        
        current_pane = self.get_current_pane()
        new_dir_name = dir_name.strip()
        new_dir_path = current_pane['path'] / new_dir_name
        
        # Check if directory already exists
        if new_dir_path.exists():
            self.logger.info(f"Directory '{new_dir_name}' already exists")
            self.quick_edit_bar.hide()
            self.mark_dirty()
            return
        
        try:
            # Create the directory
            new_dir_path.mkdir(parents=True, exist_ok=False)
            self.logger.info(f"Created directory: {new_dir_name}")
            
            # Invalidate cache for the new directory
            self.cache_manager.invalidate_cache_for_create_operation(new_dir_path)
            
            # Refresh the current pane
            self.refresh_files(current_pane)
            
            # Try to select the new directory
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_dir_name:
                    current_pane['focused_index'] = i
                    self.adjust_scroll_for_focus(current_pane)
                    break
            
            self.quick_edit_bar.hide()
            self.mark_dirty()
            
        except OSError as e:
            self.logger.error(f"Failed to create directory '{new_dir_name}': {e}")
            self.quick_edit_bar.hide()
            self.mark_dirty()
    
    def on_create_directory_cancel(self):
        """Handle create directory cancellation"""
        self.logger.info("Directory creation cancelled")
        self.quick_edit_bar.hide()
        self.mark_dirty()
    
    def enter_create_file_mode(self):
        """Enter create file mode"""
        current_pane = self.get_current_pane()
        
        # Check if current directory is writable (only for local paths)
        if current_pane['path'].get_scheme() == 'file' and not os.access(current_pane['path'], os.W_OK):
            self.logger.error(f"Permission denied: Cannot create file in {current_pane['path']}")
            return
        
        # Enter create file mode using general dialog
        QuickEditBarHelpers.create_create_file_dialog(self.quick_edit_bar)
        self.quick_edit_bar.callback = self.on_create_file_confirm
        self.quick_edit_bar.cancel_callback = self.on_create_file_cancel
        self.mark_dirty()
        self.logger.info("Creating new text file...")
    
    def on_create_file_confirm(self, file_name):
        """Handle create file confirmation"""
        if not file_name.strip():
            self.logger.error("Invalid file name")
            self.quick_edit_bar.hide()
            self.mark_dirty()
            return
        
        current_pane = self.get_current_pane()
        new_file_name = file_name.strip()
        new_file_path = current_pane['path'] / new_file_name
        
        # Check if file already exists
        if new_file_path.exists():
            self.logger.info(f"File '{new_file_name}' already exists")
            self.quick_edit_bar.hide()
            self.mark_dirty()
            return
        
        try:
            # Create the file
            new_file_path.touch()
            self.logger.info(f"Created file: {new_file_name}")
            
            # Invalidate cache for the new file
            self.cache_manager.invalidate_cache_for_create_operation(new_file_path)
            
            # Refresh the current pane
            self.refresh_files(current_pane)
            
            # Try to select the new file
            for i, file_path in enumerate(current_pane['files']):
                if file_path.name == new_file_name:
                    current_pane['focused_index'] = i
                    self.adjust_scroll_for_focus(current_pane)
                    break
            
            # Open the file for editing if it's a text file
            if is_text_file(new_file_path):
                self.edit_selected_file()
            
            self.quick_edit_bar.hide()
            self.mark_dirty()
            
        except OSError as e:
            self.logger.error(f"Failed to create file '{new_file_name}': {e}")
            self.quick_edit_bar.hide()
            self.mark_dirty()
    
    def on_create_file_cancel(self):
        """Handle create file cancellation"""
        self.logger.info("File creation cancelled")
        self.quick_edit_bar.hide()
        self.mark_dirty()

    def enter_batch_rename_mode(self):
        """Enter batch rename mode for multiple selected files"""
        current_pane = self.get_current_pane()
        
        if len(current_pane['selected_files']) < 2:
            self.logger.info("Select multiple files for batch rename")
            return
        
        # Get selected files using helper (only files, not directories for safety)
        # Preserve order from the file list for consistent \d numbering
        selected_files = []
        selected_files_set = current_pane['selected_files']
        
        # Iterate through files in display order and collect selected ones
        for file_path in current_pane['files']:
            file_path_str = str(file_path)
            if file_path_str in selected_files_set and file_path.exists() and file_path.is_file():
                selected_files.append(file_path)
        
        if not selected_files:
            self.logger.info("No files selected for batch rename")
            return
        
        if self.batch_rename_dialog.show(selected_files, on_rename_callback=self.on_batch_rename_complete):
            # Push dialog onto layer stack
            self.push_layer(self.batch_rename_dialog)
            self._force_immediate_redraw()
            self.logger.info(f"Batch rename mode: {len(selected_files)} files selected")
    
    def on_batch_rename_complete(self, success_count, errors):
        """Handle post-rename actions after batch rename completes
        
        Args:
            success_count: Number of successfully renamed files
            errors: List of error messages
        """
        # Refresh the current pane to show new names if any files were renamed
        if success_count > 0:
            current_pane = self.get_current_pane()
            self.refresh_files(current_pane)
    
    def exit_batch_rename_mode(self):
        """Exit batch rename mode - wrapper for batch rename dialog component"""
        self.batch_rename_dialog.exit()
        self.mark_dirty()
    
    def show_dialog(self, message, choices, callback, enable_shift_modifier=False):
        """Show quick choice dialog - wrapper for quick choice bar component
        
        Args:
            message: The message to display
            choices: List of choice dictionaries with format:
                     [{"text": "Yes", "key": "y", "value": True}, 
                      {"text": "No", "key": "n", "value": False},
                      {"text": "Cancel", "key": "c", "value": None}]
            callback: Function to call with the selected choice's value
            enable_shift_modifier: If True, Shift key applies choice to all remaining items
        """
        self.quick_choice_bar.show(message, choices, callback, enable_shift_modifier)
        self.mark_dirty()
    
    def show_confirmation(self, message, callback):
        """Show confirmation dialog with Yes/No options (ESC to cancel)"""
        QuickChoiceBarHelpers.show_yes_no_confirmation(self.quick_choice_bar, message, callback)
        self.mark_dirty()
        
    def exit_quick_choice_mode(self):
        """Exit quick choice mode - wrapper for quick choice bar component"""
        self.quick_choice_bar.exit()
        self.mark_dirty()
    
    def exit_confirmation_mode(self):
        """Exit confirmation mode (backward compatibility)"""
        self.exit_quick_choice_mode()
        
    def handle_quick_choice_input(self, key):
        """Handle input while in quick choice mode - wrapper for quick choice bar component"""
        result = self.quick_choice_bar.handle_input(key)
        
        if result == True or (isinstance(result, tuple) and result[0] == True):
            self.mark_dirty()
            return True
        elif isinstance(result, tuple):
            # Handle both old 2-tuple and new 3-tuple formats
            if len(result) == 3:
                action, data, apply_to_all = result
            else:
                action, data = result
                apply_to_all = False
                
            if action == 'cancel':
                # Store callback before exiting mode
                callback = self.quick_choice_bar.callback
                # Exit quick choice mode first to allow new dialogs to be shown
                self.exit_quick_choice_mode()
                # Call callback with None to indicate cancellation
                if callback:
                    callback(None)
                return True
            elif action == 'selection_changed':
                self.mark_dirty()
                return True
            elif action == 'execute':
                # Store callback before exiting mode
                callback = self.quick_choice_bar.callback
                # Exit quick choice mode first to allow new dialogs to be shown
                self.exit_quick_choice_mode()
                # Then execute the callback
                if callback:
                    # Pass apply_to_all flag if callback accepts it
                    import inspect
                    sig = inspect.signature(callback)
                    if len(sig.parameters) >= 2:
                        callback(data, apply_to_all)
                    else:
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
        # Push dialog onto layer stack
        self.push_layer(self.info_dialog)
        
        # Force immediate display of the dialog
        self._force_immediate_redraw()
    
    def push_layer(self, layer):
        """
        Push a new UI layer onto the stack.
        
        This method adds a new layer (dialog or viewer) to the UI layer stack,
        making it the active layer that receives input events.
        
        Args:
            layer: UILayer instance to push onto the stack
        """
        self.ui_layer_stack.push(layer)
        self.mark_dirty()
    
    def pop_layer(self):
        """
        Pop the top UI layer from the stack.
        
        This method removes the current top layer (dialog or viewer) from the
        UI layer stack, returning control to the layer below.
        
        Returns:
            The popped layer, or None if the operation was rejected
        """
        layer = self.ui_layer_stack.pop()
        self.mark_dirty()
        return layer
    
    def check_and_close_top_layer(self):
        """
        Check if the top layer wants to close and pop it if so.
        
        This method should be called after event handling to automatically
        close layers that have signaled they want to close.
        
        Returns:
            True if a layer was closed, False otherwise
        """
        return self.ui_layer_stack.check_and_close_top_layer()
    
    def _force_immediate_redraw(self):
        """Force an immediate screen redraw using the UI layer stack"""
        # Delegate rendering to the UI layer stack
        self.ui_layer_stack.render(self.renderer)

    def show_list_dialog(self, title, items, callback):
        """Show a searchable list dialog - wrapper for list dialog component"""
        self.list_dialog.show(title, items, callback)
        # Push dialog onto layer stack
        self.push_layer(self.list_dialog)
        
        # Force immediate display of the dialog
        self._force_immediate_redraw()
    

    def show_favorite_directories(self):
        """Show favorite directories using the searchable list dialog"""
        # Create a wrapper print function that also triggers redraw
        def print_with_redraw(message):
            self.logger.info(message)
            self.mark_dirty()
            
        ListDialogHelpers.show_favorite_directories(
            self.list_dialog, self.pane_manager, print_with_redraw
        )
        # Push dialog onto layer stack
        self.push_layer(self.list_dialog)
        self.mark_dirty()
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
                self.mark_dirty()
                self._force_immediate_redraw()
                return True
            return False
        
        # Show the list dialog with TAB switching support
        title = f"History - {pane_name.title()}"
        other_pane_name = 'Right' if pane_name == 'left' else 'Left'
        help_text = f"↑↓:select  Enter:choose  TAB:switch to {other_pane_name}  Type:search  ESC:cancel"
        self.list_dialog.show(title, history_paths, on_history_selected, handle_custom_keys, help_text)
        # Push dialog onto layer stack
        self.push_layer(self.list_dialog)
        self.mark_dirty()
        self._force_immediate_redraw()
    
    def navigate_to_history_path(self, selected_path):
        """Navigate the current pane to the selected history path"""
        try:
            target_path = Path(selected_path)
            
            # Check if the path still exists
            if not target_path.exists():
                self.logger.info(f"Directory no longer exists: {selected_path}")
                return
            
            if not target_path.is_dir():
                self.logger.info(f"Path is not a directory: {selected_path}")
                return
            
            # Get current pane and save cursor position before navigating
            current_pane = self.get_current_pane()
            self.pane_manager.save_cursor_position(current_pane)
            
            # Navigate to the selected path
            old_path = current_pane['path']
            current_pane['path'] = target_path
            current_pane['focused_index'] = 0
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
                focused_file = current_pane['files'][current_pane['focused_index']].name
                self.logger.info(f"Navigated {pane_name} pane: {old_path} → {target_path} (cursor: {focused_file})")
            else:
                self.logger.info(f"Navigated {pane_name} pane: {old_path} → {target_path}")
            
            self.mark_dirty()
            
        except Exception as e:
            self.logger.error(f"Error navigating to {selected_path}: {e}")
    
    def show_programs_dialog(self):
        """Show external programs using the searchable list dialog"""
        def execute_program_wrapper(program):
            self.external_program_manager.execute_external_program(
                self.pane_manager, program
            )
            self.mark_dirty()
        
        ListDialogHelpers.show_programs_dialog(
            self.list_dialog, execute_program_wrapper, print
        )
        # Push dialog onto layer stack
        self.push_layer(self.list_dialog)
        self.mark_dirty()
        self._force_immediate_redraw()
    
    def show_compare_selection_dialog(self):
        """Show compare selection dialog to select files and directories based on comparison with other pane"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Create a wrapper print function that also triggers redraw
        def print_with_redraw(message):
            self.logger.info(message)
            self.mark_dirty()
        
        ListDialogHelpers.show_compare_selection(
            self.list_dialog, current_pane, other_pane, print_with_redraw
        )
        # Push dialog onto layer stack
        self.push_layer(self.list_dialog)
        self.mark_dirty()
        self._force_immediate_redraw()
    
    def show_view_options(self):
        """Show view options dialog with toggle options"""
        def handle_view_option(option):
            if option is None:
                return  # User cancelled
            
            if option == "Toggle hidden files":
                old_state = self.file_list_manager.show_hidden
                new_state = self.file_list_manager.toggle_hidden_files()
                # Refresh file lists for both panes
                self.refresh_files()
                # Reset both panes
                self.pane_manager.left_pane['focused_index'] = 0
                self.pane_manager.left_pane['scroll_offset'] = 0
                self.pane_manager.right_pane['focused_index'] = 0
                self.pane_manager.right_pane['scroll_offset'] = 0
                self.logger.info(f"Hidden files: {'shown' if new_state else 'hidden'}")
                self.mark_dirty()
                
            elif option == "Toggle color scheme (dark/light)":
                from tfm_colors import toggle_color_scheme, init_colors
                new_scheme = toggle_color_scheme()
                init_colors(self.renderer, new_scheme)
                self.logger.info(f"Switched to {new_scheme} color scheme")
                self.print_color_scheme_info()
                # Clear screen to apply new background color immediately
                self.clear_screen_with_background()
                self.mark_dirty()
                
            elif option == "Toggle fallback color scheme":
                from tfm_colors import toggle_fallback_mode, init_colors, is_fallback_mode, get_current_color_scheme
                new_state = toggle_fallback_mode()
                # Re-initialize colors with current scheme
                color_scheme = get_current_color_scheme()
                init_colors(self.renderer, color_scheme)
                status = "enabled" if new_state else "disabled"
                self.logger.info(f"Fallback color mode: {status}")
                # Clear screen to apply new background color immediately
                self.clear_screen_with_background()
                self.mark_dirty()
                
            elif option == "Cycle date format":
                from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT
                current_format = getattr(self.config, 'DATE_FORMAT', 'short')
                
                # Toggle between formats: short <-> full
                if current_format == DATE_FORMAT_FULL:
                    new_format = DATE_FORMAT_SHORT
                    format_name = "Short (YY-MM-DD HH:mm)"
                else:  # DATE_FORMAT_SHORT (default)
                    new_format = DATE_FORMAT_FULL
                    format_name = "Full (YYYY-MM-DD HH:mm:ss)"
                
                # Update config
                self.config.DATE_FORMAT = new_format
                self.logger.info(f"Date format: {format_name}")
                self.mark_dirty()
        
        # Define the view options
        options = [
            "Toggle hidden files",
            "Toggle color scheme (dark/light)", 
            "Toggle fallback color scheme",
            "Cycle date format"
        ]
        
        self.show_list_dialog("View Options", options, handle_view_option)
        self._force_immediate_redraw()

    def show_settings_menu(self):
        """Show settings menu with configuration options"""
        def handle_settings_option(option):
            if option is None:
                return  # User cancelled
            
            if option == "About TFM":
                # Show About TFM information
                self._action_show_about()
                
            elif option == "Edit config.py (~/.tfm/config.py)":
                config_path = os.path.expanduser("~/.tfm/config.py")
                
                # Check if config file exists
                if not os.path.exists(config_path):
                    self.logger.info(f"Config file not found: {config_path}")
                    self.logger.info("TFM should have created this file automatically on startup.")
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
                        self.logger.info(f"Edited config file: {config_path}")
                    else:
                        self.logger.info(f"Editor exited with code {result.returncode}")
                    
                    self.mark_dirty()
                    
                except FileNotFoundError:
                    # Resume curses even if editor not found
                    self.external_program_manager.resume_curses()
                    self.logger.error(f"Text editor '{editor}' not found. Please install it or configure a different editor.")
                    self.logger.info("You can manually edit the file at: " + config_path)
                except Exception as e:
                    # Resume curses even if there's an error
                    self.external_program_manager.resume_curses()
                    self.logger.error(f"Error opening config file: {e}")
                    self.logger.info("You can manually edit the file at: " + config_path)
                
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
                        self.logger.info(f"Applied color scheme: {self.config.COLOR_SCHEME}")
                    
                    if hasattr(self.config, 'SHOW_HIDDEN_FILES'):
                        self.file_list_manager.show_hidden = self.config.SHOW_HIDDEN_FILES
                        self.logger.info(f"Hidden files setting: {'shown' if self.config.SHOW_HIDDEN_FILES else 'hidden'}")
                    
                    if hasattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO'):
                        self.log_height_ratio = self.config.DEFAULT_LOG_HEIGHT_RATIO
                        self.logger.info(f"Log height ratio: {self.config.DEFAULT_LOG_HEIGHT_RATIO}")
                    
                    self.logger.info("Configuration reloaded successfully")
                    self.mark_dirty()
                    
                except Exception as e:
                    self.logger.error(f"Error reloading configuration: {e}")
                    self.logger.error("Please check your config file for syntax errors")
                
            elif option == "Report issues":
                try:
                    # Open the GitHub issues page
                    webbrowser.open("https://github.com/shimomut/tfm/issues")
                    self.logger.info("Opened GitHub issues page in your default browser")
                except Exception as e:
                    self.logger.error(f"Error opening browser: {e}")
                    self.logger.error("Please visit: https://github.com/shimomut/tfm/issues")
        
        # Define the settings options
        options = [
            "About TFM",
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
                self.logger.info("Sort cancelled")
                return
                
            if sort_type == "reverse":
                # Toggle reverse order
                current_pane['sort_reverse'] = not current_pane['sort_reverse']
                reverse_status = "enabled" if current_pane['sort_reverse'] else "disabled"
                self.logger.info(f"Reverse sorting {reverse_status}")
            elif sort_type in ["name", "ext", "size", "date"]:
                # Set new sort mode
                current_pane['sort_mode'] = sort_type
                self.logger.info(f"Sorting by {sort_type}")
            
            # Refresh the file list after sorting
            self.refresh_files(current_pane)
            self.mark_dirty()
        
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
            self.logger.info(f"Toggled {pane_name} pane to {sort_mode} sorting ({reverse_status})")
        else:
            # Change to new sort mode (keep current reverse setting)
            current_pane['sort_mode'] = sort_mode
            self.logger.info(f"Sorted {pane_name} pane by {sort_mode}")
        
        # Refresh the file list
        self.refresh_files(current_pane)
        self.mark_dirty()

    def show_file_details(self):
        """Show detailed information about selected files or current file"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            self.logger.info("No files to show details for")
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
                    self.logger.warning(f"Warning: Could not process selected file path '{file_path_str}': {e}")
                    continue
        else:
            # Show details for current cursor position
            current_file = current_pane['files'][current_pane['focused_index']]
            files_to_show.append(current_file)
        
        if not files_to_show:
            self.logger.info("No valid files to show details for")
            return
        
        # Use the helper method to show file details
        InfoDialogHelpers.show_file_details(self.info_dialog, files_to_show, current_pane)
        # Push dialog onto layer stack
        self.push_layer(self.info_dialog)
        self.mark_dirty()
        self._force_immediate_redraw()
    
    def print_color_scheme_info(self):
        """Print current color scheme information to the log"""
        from tfm_colors import is_fallback_mode
        
        current_scheme = get_current_color_scheme()
        available_schemes = get_available_color_schemes()
        fallback_mode = is_fallback_mode()
        
        self.logger.info(f"Color scheme: {current_scheme}")
        self.logger.info(f"Available schemes: {', '.join(available_schemes)}")
        self.logger.info(f"Fallback mode: {'enabled' if fallback_mode else 'disabled'}")
        
        # Get current scheme colors for key elements
        rgb_colors = get_current_rgb_colors()
        key_colors = ['DIRECTORY_FG', 'EXECUTABLE_FG', 'SELECTED_FG', 'REGULAR_FILE_FG']
        
        for color_name in key_colors:
            if color_name in rgb_colors:
                rgb = rgb_colors[color_name]['rgb']
                self.logger.info(f"  {color_name}: RGB{rgb}")
    
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
        self.logger.info(f"Fallback color mode {mode_text}")
        
        # Print detailed color scheme info to log
        self.print_color_scheme_info()
        # Clear screen to apply new background color immediately
        self.clear_screen_with_background()
        self.mark_dirty()
    
    def show_help_dialog(self):
        """Show help dialog with key bindings and usage information"""
        InfoDialogHelpers.show_help_dialog(self.info_dialog)
        # Push dialog onto layer stack
        self.push_layer(self.info_dialog)
        self.mark_dirty()
        self._force_immediate_redraw()
    
    def view_selected_file(self):
        """View the selected file using configured viewer from file associations"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            self.logger.info("No files to view")
            return
        
        focused_file = current_pane['files'][current_pane['focused_index']]
        
        if focused_file.is_dir():
            self.logger.error("Cannot view directory")
            return
        
        # Try to use file association for 'view' action
        filename = focused_file.name
        command = get_program_for_file(filename, 'view')
        
        if command:
            # Use configured program from file associations
            try:
                # Suspend curses
                self.external_program_manager.suspend_curses()
                
                # Launch the viewer
                result = subprocess.run(command + [str(focused_file)], 
                                      cwd=str(current_pane['path']))
                
                # Resume curses
                self.external_program_manager.resume_curses()
                
                if result.returncode == 0:
                    self.logger.info(f"Viewed file: {focused_file.name}")
                else:
                    self.logger.info(f"Viewer exited with code {result.returncode}")
                
                self.mark_dirty()
                
            except Exception as e:
                # Resume curses even if there's an error
                self.external_program_manager.resume_curses()
                self.logger.error(f"Error viewing file: {e}")
                self.mark_dirty()
        else:
            # No file association found - check if it's a text file
            if is_text_file(focused_file):
                # Fallback to built-in text viewer for text files
                try:
                    viewer = create_text_viewer(self.renderer, focused_file, self.ui_layer_stack)
                    if viewer:
                        # Push viewer onto layer stack
                        self.push_layer(viewer)
                        self.renderer.set_cursor_visibility(False)
                        self.mark_dirty()
                        self.logger.info(f"Viewing text file: {focused_file.name}")
                    else:
                        self.logger.error(f"Failed to view file: {focused_file.name}")
                    
                except Exception as e:
                    self.logger.error(f"Error viewing file: {str(e)}")
                    self.mark_dirty()
            else:
                # Not a text file and no viewer configured
                self.logger.info(f"No viewer configured for '{focused_file.name}' (not a text file)")
    
    def diff_selected_files(self):
        """View diff between two selected text files"""
        # Collect selected files from both panes
        left_selected = [Path(f) for f in self.pane_manager.left_pane['selected_files']]
        right_selected = [Path(f) for f in self.pane_manager.right_pane['selected_files']]
        
        # Combine all selected files
        all_selected = left_selected + right_selected
        
        # Filter to only files (not directories)
        selected_files = [f for f in all_selected if f.exists() and f.is_file()]
        
        # Check if exactly 2 files are selected
        if len(selected_files) != 2:
            if len(all_selected) == 0:
                self.logger.info("No files selected. Select exactly 2 text files to compare.")
            elif len(all_selected) == 1:
                self.logger.info("Only 1 file selected. Select exactly 2 text files to compare.")
            elif len(selected_files) < len(all_selected):
                self.logger.info(f"Selected items include directories. Select exactly 2 text files to compare.")
            else:
                self.logger.info(f"Selected {len(selected_files)} files. Select exactly 2 text files to compare.")
            return
        
        file1, file2 = selected_files[0], selected_files[1]
        
        # Check if both are text files
        if not is_text_file(file1):
            self.logger.info(f"'{file1.name}' is not a text file")
            return
        
        if not is_text_file(file2):
            self.logger.info(f"'{file2.name}' is not a text file")
            return
        
        # Launch diff viewer
        try:
            viewer = create_diff_viewer(self.renderer, file1, file2, self.ui_layer_stack)
            if viewer:
                # Push viewer onto layer stack
                self.push_layer(viewer)
                self.renderer.set_cursor_visibility(False)
                self.mark_dirty()
                self.logger.info(f"Comparing: {file1.name} <-> {file2.name}")
            else:
                self.logger.error(f"Failed to compare files")
        except Exception as e:
            self.logger.error(f"Error creating diff viewer: {e}")
            self.mark_dirty()
            
        except Exception as e:
            self.logger.error(f"Error viewing diff: {e}")
            self.mark_dirty()
    
    def show_directory_diff(self):
        """Show directory diff viewer comparing left and right pane directories"""
        # Get paths from both panes
        left_path = self.pane_manager.left_pane['path']
        right_path = self.pane_manager.right_pane['path']
        
        # Validate that both paths are directories
        if not left_path.exists():
            self.logger.info(f"Left pane path does not exist: {left_path}")
            return
        
        if not right_path.exists():
            self.logger.info(f"Right pane path does not exist: {right_path}")
            return
        
        if not left_path.is_dir():
            self.logger.info(f"Left pane path is not a directory: {left_path}")
            return
        
        if not right_path.is_dir():
            self.logger.info(f"Right pane path is not a directory: {right_path}")
            return
        
        # Create and launch directory diff viewer
        try:
            viewer = DirectoryDiffViewer(self.renderer, left_path, right_path, self.ui_layer_stack, self.file_list_manager)
            if viewer:
                # Push viewer onto layer stack
                self.push_layer(viewer)
                self.renderer.set_cursor_visibility(False)
                self.mark_dirty()
                self.logger.info(f"Comparing directories: {left_path} <-> {right_path}")
            else:
                self.logger.error(f"Failed to create directory diff viewer")
        except Exception as e:
            self.logger.error(f"Error creating directory diff viewer: {e}")
            self.mark_dirty()
    
    def edit_selected_file(self):
        """Edit the selected file using configured editor from file associations"""
        current_pane = self.get_current_pane()
        
        if not current_pane['files']:
            self.logger.info("No files in current directory")
            return
            
        focused_file = current_pane['files'][current_pane['focused_index']]
        
        # Check if file editing is supported for this storage type
        if not focused_file.supports_file_editing():
            self.logger.info("Editing S3 files is not supported for now")
            return
        
        # Allow editing directories (some editors can handle them)
        if focused_file.is_dir():
            self.logger.warning(f"Warning: '{focused_file.name}' is a directory")
        
        # Try to use file association for 'edit' action
        filename = focused_file.name
        command = get_program_for_file(filename, 'edit')
        
        if command:
            # Use configured program from file associations
            try:
                # Suspend curses
                self.external_program_manager.suspend_curses()
                
                # Launch the editor
                result = subprocess.run(command + [str(focused_file)], 
                                      cwd=str(current_pane['path']))
                
                # Resume curses
                self.external_program_manager.resume_curses()
                
                if result.returncode == 0:
                    self.logger.info(f"Edited file: {focused_file.name}")
                else:
                    self.logger.info(f"Editor exited with code {result.returncode}")
                    
            except FileNotFoundError:
                # Resume curses even if editor not found
                self.external_program_manager.resume_curses()
                self.logger.error(f"Editor not found. Please check your file associations configuration.")
            except Exception as e:
                # Resume curses even if there's an error
                self.external_program_manager.resume_curses()
                self.logger.error(f"Error launching editor: {e}")
        else:
            # Fallback to TEXT_EDITOR config for files without association
            editor = getattr(self.config, 'TEXT_EDITOR', DEFAULT_TEXT_EDITOR)
            
            try:
                # Suspend curses
                self.external_program_manager.suspend_curses()
                
                # Launch the text editor
                result = subprocess.run([editor, str(focused_file)], 
                                      cwd=str(current_pane['path']))
                
                # Resume curses
                self.external_program_manager.resume_curses()
                
                if result.returncode == 0:
                    self.logger.info(f"Edited file: {focused_file.name}")
                else:
                    self.logger.info(f"Editor exited with code {result.returncode}")
                    
            except FileNotFoundError:
                # Resume curses even if editor not found
                self.external_program_manager.resume_curses()
                self.logger.error(f"Text editor '{editor}' not found. Please install it or configure a different editor.")
            except Exception as e:
                # Resume curses even if there's an error
                self.external_program_manager.resume_curses()
                self.logger.error(f"Error launching editor: {e}")
    
    def copy_selected_files(self):
        """Copy selected files to the opposite pane's directory - delegated to FileOperationUI"""
        self.file_operations_ui.copy_selected_files()
    
    def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):
        """Perform copy operation - delegated to FileOperationUI"""
        self.file_operations_ui.perform_copy_operation(files_to_copy, destination_dir, overwrite)
    
    # Legacy helper method - functionality moved to FileOperationUI
    def _copy_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
        """Copy directory with progress - delegated to FileOperationUI"""
        return self.file_operations_ui._copy_directory_with_progress(source_dir, dest_dir, processed_files, total_files)
    
    def move_selected_files(self):
        """Move selected files to the opposite pane's directory - delegated to FileOperationUI"""
        self.file_operations_ui.move_selected_files()
    
    def move_files_to_directory(self, files_to_move, destination_dir):
        """Move files to directory - delegated to FileOperationUI"""
        self.file_operations_ui.move_files_to_directory(files_to_move, destination_dir)
    
    def perform_move_operation(self, files_to_move, destination_dir, overwrite=False):
        """Perform move operation - delegated to FileOperationUI"""
        self.file_operations_ui.perform_move_operation(files_to_move, destination_dir, overwrite)
    
    # Legacy move operation methods - functionality moved to FileOperationUI
    
    def delete_selected_files(self):
        """Delete selected files or current file with confirmation - delegated to FileOperationUI"""
        self.file_operations_ui.delete_selected_files()
    
    def perform_delete_operation(self, files_to_delete):
        """Perform delete operation - delegated to FileOperationUI"""
        self.file_operations_ui.perform_delete_operation(files_to_delete)
    
    # Legacy file operation methods - functionality moved to FileOperationUI
    
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
        self.logger.info("Legacy archive creation method called - this should not happen")
        pass
    
    def _progress_callback(self, progress_data):
        """Callback for progress manager updates"""
        # Mark as needing redraw to show progress
        # Note: Don't call renderer.refresh() here - UILayerStack will do it
        try:
            self.draw_status()
            self.mark_dirty()
        except Exception as e:
            self.logger.error(f"Warning: Progress callback display update failed: {e}")
    
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
        self.logger.info("Legacy ZIP creation method called - this should not happen")
        pass
    
    def create_tar_archive(self, archive_path, files_to_archive):
        """Create a TAR.GZ archive - legacy method, functionality moved to ArchiveOperations"""
        self.logger.info("Legacy TAR creation method called - this should not happen")
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
        self.logger.info("Legacy extraction method called - this should not happen")
        pass
    
    def extract_zip_archive(self, archive_file, extract_dir):
        """Extract ZIP archive - legacy method, functionality moved to ArchiveOperations"""
        self.logger.info("Legacy ZIP extraction method called - this should not happen")
        pass
    
    def extract_tar_archive(self, archive_file, extract_dir):
        """Extract TAR archive - legacy method, functionality moved to ArchiveOperations"""
        self.logger.info("Legacy TAR extraction method called - this should not happen")
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
                self.mark_dirty()
            return True
        elif event.key_code == KeyCode.UP and not (event.modifiers & ModifierKey.SHIFT):
            # Up arrow - go to previous match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index - 1) % len(self.isearch_matches)
                current_pane = self.get_current_pane()
                current_pane['focused_index'] = self.isearch_matches[self.isearch_match_index]
                self.adjust_scroll_for_focus(current_pane)
                self.mark_dirty()
            return True
        elif event.key_code == KeyCode.DOWN and not (event.modifiers & ModifierKey.SHIFT):
            # Down arrow - go to next match
            if self.isearch_matches:
                self.isearch_match_index = (self.isearch_match_index + 1) % len(self.isearch_matches)
                current_pane = self.get_current_pane()
                current_pane['focused_index'] = self.isearch_matches[self.isearch_match_index]
                self.adjust_scroll_for_focus(current_pane)
                self.mark_dirty()
            return True
        
        # Handle CharEvent - text input for search pattern
        if isinstance(event, CharEvent):
            self.isearch_pattern += event.char
            self.update_isearch_matches()
            self.mark_dirty()
            return True
        
        # Handle KeyEvent with printable character (for backward compatibility)
        if isinstance(event, KeyEvent) and event.is_printable():
            # Add character to isearch pattern
            self.isearch_pattern += event.char
            self.update_isearch_matches()
            self.mark_dirty()
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
        self.mark_dirty()

    def adjust_pane_boundary(self, direction):
        """Adjust the boundary between left and right panes"""
        if direction == 'left':
            # Make left pane smaller, right pane larger
            self.pane_manager.left_pane_ratio = max(MIN_PANE_RATIO, self.pane_manager.left_pane_ratio - PANE_ADJUST_STEP)
        elif direction == 'right':
            # Make left pane larger, right pane smaller  
            self.pane_manager.left_pane_ratio = min(MAX_PANE_RATIO, self.pane_manager.left_pane_ratio + PANE_ADJUST_STEP)
            
        # Trigger a full redraw for the new pane layout
        self.mark_dirty()
        
        # Show immediate feedback in log pane
        left_percent = int(self.pane_manager.left_pane_ratio * 100)
        right_percent = 100 - left_percent
        
    def adjust_log_boundary(self, direction):
        """Adjust the boundary between file panes and log pane"""
        if direction == 'up':
            # Make log pane larger (divider moves up), file panes smaller
            self.log_height_ratio = min(MAX_LOG_HEIGHT_RATIO, self.log_height_ratio + LOG_HEIGHT_ADJUST_STEP)
        elif direction == 'down':
            # Make log pane smaller (divider moves down), file panes larger
            self.log_height_ratio = max(MIN_LOG_HEIGHT_RATIO, self.log_height_ratio - LOG_HEIGHT_ADJUST_STEP)
            
        # Trigger a full redraw for the new layout
        self.mark_dirty()
        
        # Show immediate feedback in log pane
        log_percent = int(self.log_height_ratio * 100)
        file_percent = 100 - log_percent
    
    def show_search_dialog(self, search_type='filename'):
        """Show the search dialog for filename or content search - wrapper for search dialog component"""
        current_pane = self.get_current_pane()
        search_root = current_pane['path']
        
        # Define callback for when a result is selected
        def on_search_result_selected(result):
            if result:
                # Navigate to the selected result
                self._navigate_to_search_result(result)
                
                # Save search term to history if it's not empty
                search_term = self.search_dialog.text_editor.text.strip()
                if search_term:
                    self.add_search_to_history(search_term)
        
        self.search_dialog.show(search_type, search_root, callback=on_search_result_selected)
        # Push dialog onto layer stack
        self.push_layer(self.search_dialog)
        
        # Force immediate display of the dialog
        self._force_immediate_redraw()
    

    def _navigate_to_search_result(self, result):
        """Navigate to the selected search result - wrapper for search dialog helper"""
        SearchDialogHelpers.navigate_to_result(result, self.pane_manager, self.file_list_manager, print)
        
        # Adjust scroll with proper display height
        current_pane = self.get_current_pane()
        height, width = self.renderer.get_dimensions()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        
        SearchDialogHelpers.adjust_scroll_for_display_height(current_pane, display_height)
        # Dirty flag will be set when dialog exits

    def enter_jump_to_path_mode(self):
        """Enter jump to path mode using QuickEditBar"""
        current_pane = self.get_current_pane()
        current_path = str(current_pane['path'])
        
        def on_confirm(path_str):
            """Handle path confirmation"""
            if not path_str.strip():
                return
            
            try:
                from tfm_path import Path
                target_path = Path(path_str.strip())
                
                # Expand ~ to home directory
                if str(target_path).startswith('~'):
                    target_path = Path.home() / str(target_path)[2:].lstrip('/')
                
                # Check if path exists and is a directory
                if not target_path.exists():
                    self.logger.error(f"Path does not exist: {target_path}")
                    return
                
                if not target_path.is_dir():
                    self.logger.error(f"Not a directory: {target_path}")
                    return
                
                # Save current cursor position
                self.save_cursor_position(current_pane)
                
                # Navigate to the path
                current_pane['path'] = target_path
                current_pane['focused_index'] = 0
                current_pane['scroll_offset'] = 0
                current_pane['selected_files'].clear()
                self.refresh_files(current_pane)
                
                # Try to restore cursor position for this directory
                if not self.restore_cursor_position(current_pane):
                    current_pane['focused_index'] = 0
                    current_pane['scroll_offset'] = 0
                
                self.mark_dirty()
                self.logger.info(f"Jumped to: {target_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to jump to path: {e}")
        
        def on_cancel():
            """Handle cancellation"""
            pass
        
        # Show QuickEditBar for path input
        self.quick_edit_bar.show_status_line_input(
            prompt="Jump to path: ",
            help_text="ESC:cancel Enter:jump",
            initial_text=current_path,
            callback=on_confirm,
            cancel_callback=on_cancel
        )
        self.mark_dirty()
    

    def show_drives_dialog(self):
        """Show the drives dialog - wrapper for drives dialog component"""
        
        # Define callback for when a drive is selected
        def drive_callback(drive_entry):
            if drive_entry and drive_entry.path:
                # Navigate to the selected drive
                current_pane = self.get_current_pane()
                
                try:
                    # Create Path object for the drive
                    drive_path = Path(drive_entry.path)
                    
                    # Validate the path exists and is accessible (for local drives)
                    if drive_entry.drive_type == 'local':
                        if not drive_path.exists() or not drive_path.is_dir():
                            self.logger.error(f"Error: Drive path no longer exists or is not accessible: {drive_entry.path}")
                            self.mark_dirty()
                            return
                    
                    # Update the current pane
                    old_path = current_pane['path']
                    current_pane['path'] = drive_path
                    current_pane['focused_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()
                    
                    # Refresh the file list
                    self.pane_manager.refresh_files(current_pane)
                    
                    pane_name = "left" if self.pane_manager.active_pane == 'left' else "right"
                    self.logger.info(f"Switched to {drive_entry.name}: {drive_entry.path}")
                    self.mark_dirty()
                    
                except Exception as e:
                    self.logger.error(f"Error: Failed to navigate to drive: {e}")
                    self.mark_dirty()
            else:
                # Cancelled or no selection
                self.logger.info("Drive selection cancelled")
                self.mark_dirty()
        
        self.drives_dialog.show(drive_callback)
        # Push dialog onto layer stack
        self.push_layer(self.drives_dialog)
        self._force_immediate_redraw()
    

    def handle_main_screen_key_event(self, event):
        """
        Handle key events for the main FileManager screen.
        
        This method contains all the main screen keyboard event handling logic
        including navigation, selection, commands, and shortcuts. It's called
        by handle_input() after checking for special input modes.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        current_pane = self.get_current_pane()
        
        # Handle main application keys (KeyEvent only)
        # CharEvents are not processed here as they don't have key_code
        if not isinstance(event, KeyEvent):
            return False
        
        # Check if there are selected files for action matching
        has_selection = len(current_pane['selected_files']) > 0
        
        # Find action for this key event (optimized single lookup)
        action = find_action_for_event(event, has_selection)
        
        # If no action found, return immediately
        if action is None:
            return False
        
        # Handle log scrolling actions
        if action == 'scroll_log_up':
            if self.log_manager.scroll_log_up(1):
                self.mark_dirty()
            return True
        elif action == 'scroll_log_down':
            if self.log_manager.scroll_log_down(1):
                self.mark_dirty()
            return True
        elif action == 'scroll_log_page_up':
            log_height = self._get_log_pane_height()
            if self.log_manager.scroll_log_up(max(1, log_height)):
                self.mark_dirty()
            return True
        elif action == 'scroll_log_page_down':
            log_height = self._get_log_pane_height()
            if self.log_manager.scroll_log_down(max(1, log_height)):
                self.mark_dirty()
            return True
        
        if action == 'quit':
            def quit_callback(confirmed):
                if confirmed:
                    # Set the flag to exit the main loop
                    self.should_quit = True
            
            # Check if quit confirmation is enabled
            if getattr(self.config, 'CONFIRM_QUIT', True):
                self.show_confirmation("Are you sure you want to quit TFM?", quit_callback)
            else:
                quit_callback(True)
            return True

        elif action == 'switch_pane':
            self.pane_manager.active_pane = 'right' if self.pane_manager.active_pane == 'left' else 'left'
            self.mark_dirty()
            return True
        elif action == 'cursor_up':
            if current_pane['focused_index'] > 0:
                current_pane['focused_index'] -= 1
                self.adjust_scroll_for_focus(current_pane)
                self.mark_dirty()
            return True
        elif action == 'cursor_down':
            if current_pane['focused_index'] < len(current_pane['files']) - 1:
                current_pane['focused_index'] += 1
                self.adjust_scroll_for_focus(current_pane)
                self.mark_dirty()
            return True
        elif action == 'open_item':
            self.handle_enter()
            self.mark_dirty()
            return True
        elif action == 'nav_left':
            # Context-aware LEFT arrow: go to parent in left pane, switch pane in right pane
            if self.pane_manager.active_pane == 'left':
                # Left arrow in left pane - go to parent directory
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        self.save_cursor_position(current_pane)
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['focused_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()
                        self.refresh_files(current_pane)
                        if not self.restore_cursor_position(current_pane):
                            current_pane['focused_index'] = 0
                            current_pane['scroll_offset'] = 0
                        self.mark_dirty()
                    except PermissionError:
                        self.logger.error("Permission denied")
            else:
                # Left arrow in right pane - switch to left pane
                self.pane_manager.active_pane = 'left'
                self.mark_dirty()
            return True
        elif action == 'nav_right':
            # Context-aware RIGHT arrow: go to parent in right pane, switch pane in left pane
            if self.pane_manager.active_pane == 'right':
                # Right arrow in right pane - go to parent directory
                if current_pane['path'] != current_pane['path'].parent:
                    try:
                        self.save_cursor_position(current_pane)
                        current_pane['path'] = current_pane['path'].parent
                        current_pane['focused_index'] = 0
                        current_pane['scroll_offset'] = 0
                        current_pane['selected_files'].clear()
                        self.refresh_files(current_pane)
                        if not self.restore_cursor_position(current_pane):
                            current_pane['focused_index'] = 0
                            current_pane['scroll_offset'] = 0
                        self.mark_dirty()
                    except PermissionError:
                        self.logger.error("Permission denied")
            else:
                # Right arrow in left pane - switch to right pane
                self.pane_manager.active_pane = 'right'
                self.mark_dirty()
            return True
        elif action == 'toggle_hidden':
            self.file_list_manager.toggle_hidden_files()
            # Refresh file lists for both panes
            self.refresh_files()
            # Reset both panes
            self.pane_manager.left_pane['focused_index'] = 0
            self.pane_manager.left_pane['scroll_offset'] = 0
            self.pane_manager.right_pane['focused_index'] = 0
            self.pane_manager.right_pane['scroll_offset'] = 0
            self.mark_dirty()
            return True
        elif action == 'toggle_color_scheme':
            # Toggle between dark and light color schemes
            new_scheme = toggle_color_scheme()
            # Reinitialize colors with the new scheme
            init_colors(self.renderer, new_scheme)
            self.logger.info(f"Switched to {new_scheme} color scheme")
            # Print detailed color scheme info to log
            self.print_color_scheme_info()
            # Clear screen to apply new background color immediately
            self.clear_screen_with_background()
            self.mark_dirty()
            return True
        elif action == 'select_all':
            self.select_all()
            return True
        elif action == 'unselect_all':
            self.unselect_all()
            return True
        elif action == 'page_up':
            current_pane['focused_index'] = max(0, current_pane['focused_index'] - 10)
            self.adjust_scroll_for_focus(current_pane)
            self.mark_dirty()
            return True
        elif action == 'page_down':
            current_pane['focused_index'] = min(len(current_pane['files']) - 1, current_pane['focused_index'] + 10)
            self.adjust_scroll_for_focus(current_pane)
            self.mark_dirty()
            return True
        elif action == 'go_parent':
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
                    current_pane['focused_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()
                    self.refresh_files(current_pane)
                    
                    # Try to set cursor to the archive file we just exited
                    cursor_set = False
                    for i, file_path in enumerate(current_pane['files']):
                        if file_path.name == archive_filename:
                            current_pane['focused_index'] = i
                            self.adjust_scroll_for_focus(current_pane)
                            cursor_set = True
                            break
                    
                    if not cursor_set:
                        current_pane['focused_index'] = 0
                        current_pane['scroll_offset'] = 0
                    
                    self.mark_dirty()
                    self.logger.info(f"Exited archive: {archive_filename}")
                except Exception as e:
                    self.logger.error(f"Error exiting archive: {e}")
                    self.mark_dirty()
            elif current_pane['path'] != current_pane['path'].parent:
                try:
                    # Save current cursor position before changing directory
                    self.save_cursor_position(current_pane)
                    
                    # Remember the child directory name we're leaving
                    child_directory_name = current_pane['path'].name
                    
                    current_pane['path'] = current_pane['path'].parent
                    current_pane['focused_index'] = 0
                    current_pane['scroll_offset'] = 0
                    current_pane['selected_files'].clear()  # Clear selections when changing directory
                    self.refresh_files(current_pane)
                    
                    # Try to set cursor to the child directory we just came from
                    cursor_set = False
                    for i, file_path in enumerate(current_pane['files']):
                        if file_path.name == child_directory_name and file_path.is_dir():
                            current_pane['focused_index'] = i
                            # Adjust scroll offset to keep selection visible
                            self.adjust_scroll_for_focus(current_pane)
                            cursor_set = True
                            break
                    
                    # If we couldn't find the child directory, try to restore cursor position from history
                    if not cursor_set and not self.restore_cursor_position(current_pane):
                        # If no history found, default to first item
                        current_pane['focused_index'] = 0
                        current_pane['scroll_offset'] = 0
                    
                    self.mark_dirty()
                except Exception as e:
                    self.logger.error(f"Error navigating to parent directory: {e}")
                    self.mark_dirty()
            return True
        elif action == 'select_file_up':  # Shift+Space - toggle selection and move up
            self.toggle_selection_up()
            self.mark_dirty()
            return True
        elif action == 'select_file':  # Toggle file selection
            self.toggle_selection()
            self.mark_dirty()
            return True
        elif action == 'select_all_files':  # Toggle all files selection
            self.toggle_all_files_selection()
            return True
        elif action == 'select_all_items':  # Toggle all items selection
            self.toggle_all_items_selection()
            return True
        elif action == 'sync_current_to_other':  # Sync current pane to other
            self.sync_current_to_other()
            return True
        elif action == 'sync_other_to_current':  # Sync other pane to current
            self.sync_other_to_current()
            return True
        elif action == 'search_dialog':  # Show search dialog (filename)
            self.show_search_dialog('filename')
            return True
        elif action == 'jump_to_path':  # Jump to path (Shift+J)
            self.enter_jump_to_path_mode()
            return True
        elif action == 'drives_dialog':  # Show drives dialog
            self.show_drives_dialog()
            return True
        elif action == 'search_content':  # Show search dialog (content)
            self.show_search_dialog('content')
            return True
        elif action == 'edit_file':  # Edit existing file
            self.edit_selected_file()
            return True
        elif action == 'create_file':  # Create new file
            self.enter_create_file_mode()
            return True
        elif action == 'create_directory':  # Create new directory
            self.enter_create_directory_mode()
            return True
        elif action == 'toggle_fallback_colors':  # Toggle fallback color mode
            self.toggle_fallback_color_mode()
            return True
        elif action == 'view_options':  # Show view options
            self.show_view_options()
            return True
        elif action == 'settings_menu':  # Show settings menu
            self.show_settings_menu()
            return True
        elif action == 'search':  # Search key - enter isearch mode
            self.enter_isearch_mode()
            return True
        elif action == 'filter':  # Filter key - enter filter mode
            self.enter_filter_mode()
            return True
        elif action == 'clear_filter':  # Clear filter key
            self.clear_filter()
            return True
        elif action == 'sort_menu':  # Sort menu
            self.show_sort_menu()
            return True
        elif action == 'quick_sort_name':  # Quick sort by name
            self.quick_sort('name')
            return True
        elif action == 'quick_sort_size':  # Quick sort by size
            self.quick_sort('size')
            return True
        elif action == 'quick_sort_date':  # Quick sort by date
            self.quick_sort('date')
            return True
        elif action == 'quick_sort_ext':  # Quick sort by extension
            self.quick_sort('ext')
            return True
        elif action == 'file_details':  # Show file details
            self.show_file_details()
            return True
        elif action == 'view_file':  # View file
            self.view_selected_file()
            return True
        elif action == 'diff_files':  # Diff two selected files
            self.diff_selected_files()
            return True
        elif action == 'diff_directories':  # Compare directories recursively
            self.show_directory_diff()
            return True
        elif action == 'copy_files':  # Copy selected files
            self.copy_selected_files()
            return True
        elif action == 'move_files':  # Move selected files
            self.move_selected_files()
            return True
        elif action == 'delete_files':  # Delete selected files
            self.delete_selected_files()
            return True
        elif action == 'create_archive':  # Create archive
            self.enter_create_archive_mode()
            return True
        elif action == 'extract_archive':  # Extract archive
            self.extract_selected_archive()
            return True
        elif action == 'rename_file':  # Rename file
            self.enter_rename_mode()
            return True
        elif action == 'favorites':  # Show favorite directories
            self.show_favorite_directories()
            return True
        elif action == 'history':  # Show history
            self.show_history()
            return True
        elif action == 'programs':  # Show external programs
            self.show_programs_dialog()
            return True
        elif action == 'compare_selection':  # Show compare selection menu
            self.show_compare_selection_dialog()
            return True
        elif action == 'help':  # Show help dialog
            self.show_help_dialog()
            return True
        elif action == 'adjust_pane_left':  # Adjust pane boundary left
            self.adjust_pane_boundary('left')
            return True
        elif action == 'adjust_pane_right':  # Adjust pane boundary right
            self.adjust_pane_boundary('right')
            return True
        elif action == 'adjust_log_up':  # Adjust log boundary up
            self.adjust_log_boundary('up')
            return True
        elif action == 'adjust_log_down':  # Adjust log boundary down
            self.adjust_log_boundary('down')
            return True
        elif action == 'reset_log_height':  # Reset log pane height
            self.log_height_ratio = getattr(self.config, 'DEFAULT_LOG_HEIGHT_RATIO', 0.25)
            self.mark_dirty()
            self.logger.info(f"Log pane height reset to {int(self.log_height_ratio * 100)}%")
            return True
        elif action == 'reset_pane_boundary':  # Reset pane split to 50/50
            self.pane_manager.left_pane_ratio = 0.5
            self.mark_dirty()
            self.logger.info("Pane split reset to 50% | 50%")
            return True
        elif action == 'subshell':  # Sub-shell mode
            self.external_program_manager.enter_subshell_mode(
                self.pane_manager
            )
            self.mark_dirty()
            return True
        else:
            return False  # Key was not handled

    def handle_input(self, event):
        """
        Handle all FileManager input events.
        
        This method handles both FileManager-specific input modes (isearch,
        quick_edit_bar, quick_choice_bar) and main screen keyboard events
        (navigation, selection, commands, shortcuts).
        
        Args:
            event: KeyEvent or CharEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        # Type check: only handle KeyEvent and CharEvent
        if not isinstance(event, (KeyEvent, CharEvent)):
            return False
        
        # Handle isearch mode input (FileManager-specific, not part of layer stack)
        if self.isearch_mode:
            result = self.handle_isearch_input(event)
            if result:
                self.mark_dirty()
            return result
        
        # Handle quick_edit_bar input (FileManager-specific, not part of layer stack)
        if self.quick_edit_bar.is_active:
            result = self.quick_edit_bar.handle_input(event)
            if result:
                self.mark_dirty()
            return result
        
        # Handle quick_choice_bar input (FileManager-specific, not part of layer stack, KeyEvent only)
        if isinstance(event, KeyEvent) and self.quick_choice_bar.is_active:
            result = self.handle_quick_choice_input(event)
            if result:
                self.mark_dirty()
            return result
        
        # Handle main screen key events
        # CharEvents are not processed for main screen (no text input on main screen)
        if not isinstance(event, KeyEvent):
            return False
        
        # Delegate to main screen key handling
        return self.handle_main_screen_key_event(event)

    def draw_interface(self):
        """Draw the complete interface using the UI layer stack"""
        # Delegate rendering to the UI layer stack
        self.ui_layer_stack.render(self.renderer)


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
                self.logger.info(f"Restored window layout: panes {int(self.pane_manager.left_pane_ratio*100)}%/{int((1-self.pane_manager.left_pane_ratio)*100)}%, log {int(self.log_height_ratio*100)}%")
            
            # Load pane states
            left_state = self.state_manager.load_pane_state('left')
            if left_state and Path(left_state['path']).exists() and not self.cmdline_left_dir_provided:
                # Only restore if the directory still exists and no command line argument was provided
                self.pane_manager.left_pane['path'] = Path(left_state['path'])
                self.pane_manager.left_pane['sort_mode'] = left_state.get('sort_mode', 'name')
                self.pane_manager.left_pane['sort_reverse'] = left_state.get('sort_reverse', False)
                self.pane_manager.left_pane['filter_pattern'] = left_state.get('filter_pattern', '')
                self.logger.info(f"Restored left pane: {left_state['path']}")
            elif self.cmdline_left_dir_provided:
                # Load other settings but keep command line directory
                if left_state:
                    self.pane_manager.left_pane['sort_mode'] = left_state.get('sort_mode', 'name')
                    self.pane_manager.left_pane['sort_reverse'] = left_state.get('sort_reverse', False)
                    self.pane_manager.left_pane['filter_pattern'] = left_state.get('filter_pattern', '')
                self.logger.info(f"Using command line left directory: {self.pane_manager.left_pane['path']}")
            
            right_state = self.state_manager.load_pane_state('right')
            if right_state and Path(right_state['path']).exists() and not self.cmdline_right_dir_provided:
                # Only restore if the directory still exists and no command line argument was provided
                self.pane_manager.right_pane['path'] = Path(right_state['path'])
                self.pane_manager.right_pane['sort_mode'] = right_state.get('sort_mode', 'name')
                self.pane_manager.right_pane['sort_reverse'] = right_state.get('sort_reverse', False)
                self.pane_manager.right_pane['filter_pattern'] = right_state.get('filter_pattern', '')
                self.logger.info(f"Restored right pane: {right_state['path']}")
            elif self.cmdline_right_dir_provided:
                # Load other settings but keep command line directory
                if right_state:
                    self.pane_manager.right_pane['sort_mode'] = right_state.get('sort_mode', 'name')
                    self.pane_manager.right_pane['sort_reverse'] = right_state.get('sort_reverse', False)
                    self.pane_manager.right_pane['filter_pattern'] = right_state.get('filter_pattern', '')
                self.logger.info(f"Using command line right directory: {self.pane_manager.right_pane['path']}")
            
            # Refresh file lists after loading state
            self.refresh_files()
            
            # Restore cursor positions after files are loaded
            self.restore_startup_cursor_positions()
            
        except Exception as e:
            self.logger.warning(f"Warning: Could not load application state: {e}")
    
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
                    selected_file = self.pane_manager.left_pane['files'][self.pane_manager.left_pane['focused_index']].name
                    self.logger.info(f"Restored left pane cursor: {left_path} -> {selected_file}")
            
            # Restore right pane cursor position
            right_restored = self.pane_manager.restore_cursor_position(self.pane_manager.right_pane, display_height)
            if right_restored:
                right_path = self.pane_manager.right_pane['path']
                if self.pane_manager.right_pane['files']:
                    selected_file = self.pane_manager.right_pane['files'][self.pane_manager.right_pane['focused_index']].name
                    self.logger.info(f"Restored right pane cursor: {right_path} -> {selected_file}")
            
            # If either cursor was restored, trigger a redraw
            if left_restored or right_restored:
                self.mark_dirty()
                
        except Exception as e:
            self.logger.warning(f"Warning: Could not restore startup cursor positions: {e}")
    
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
            
            self.logger.info("Application state saved")
            
        except Exception as e:
            self.logger.warning(f"Warning: Could not save application state: {e}")
    
    def save_quit_cursor_positions(self):
        """Save current cursor positions when quitting TFM."""
        try:
            # Save left pane cursor position
            if (self.pane_manager.left_pane['files'] and 
                self.pane_manager.left_pane['focused_index'] < len(self.pane_manager.left_pane['files'])):
                
                self.pane_manager.save_cursor_position(self.pane_manager.left_pane)
                
                left_path = self.pane_manager.left_pane['path']
                selected_file = self.pane_manager.left_pane['files'][self.pane_manager.left_pane['focused_index']].name
                self.logger.info(f"Saved left pane cursor position: {left_path} -> {selected_file}")
            
            # Save right pane cursor position
            if (self.pane_manager.right_pane['files'] and 
                self.pane_manager.right_pane['focused_index'] < len(self.pane_manager.right_pane['files'])):
                
                self.pane_manager.save_cursor_position(self.pane_manager.right_pane)
                
                right_path = self.pane_manager.right_pane['path']
                selected_file = self.pane_manager.right_pane['files'][self.pane_manager.right_pane['focused_index']].name
                self.logger.info(f"Saved right pane cursor position: {right_path} -> {selected_file}")
                
        except Exception as e:
            self.logger.warning(f"Warning: Could not save cursor positions on quit: {e}")
    
    def get_recent_directories(self):
        """Get list of recent directories for quick navigation."""
        try:
            return self.state_manager.load_recent_directories()
        except Exception as e:
            self.logger.warning(f"Warning: Could not load recent directories: {e}")
            return []
    
    def add_search_to_history(self, search_term):
        """Add a search term to the search history."""
        try:
            self.state_manager.add_search_term(search_term)
        except Exception as e:
            self.logger.warning(f"Warning: Could not save search term: {e}")
    
    def get_search_history(self):
        """Get search history for auto-completion."""
        try:
            return self.state_manager.load_search_history()
        except Exception as e:
            self.logger.warning(f"Warning: Could not load search history: {e}")
            return []

def main(renderer, remote_log_port=None, left_dir=None, right_dir=None, profiling_targets=None, log_file=None, debug=False):
    """Main function to run the file manager"""
    fm = None
    try:
        fm = FileManager(renderer, remote_log_port=remote_log_port, left_dir=left_dir, right_dir=right_dir, 
                        profiling_targets=profiling_targets or set(), log_file=log_file, debug=debug)
        fm.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
    except Exception as e:
        # Restore stdout/stderr before handling exception
        if fm is not None:
            fm.restore_stdio()
        
        # Print error information to help with debugging
        # Use fm.logger if available, otherwise use print
        if fm is not None and hasattr(fm, 'logger'):
            fm.logger.error(f"\nTFM encountered an unexpected error:")
            fm.logger.error(f"Error: {type(e).__name__}: {e}")
            fm.logger.info("\nFull traceback:")
        else:
            print(f"\nTFM encountered an unexpected error:")
            print(f"Error: {type(e).__name__}: {e}")
            print("\nFull traceback:")
        traceback.print_exc()
        
        # Re-raise the exception so it can be seen after TFM exits
        raise
    finally:
        # Always restore stdout/stderr in case of any exit path
        if fm is not None:
            fm.restore_stdio()
        
        # Clean up state manager
        cleanup_state_manager()

def create_parser():
    """Create and configure the argument parser"""
    # Import version info
    try:
        from tfm_const import VERSION, APP_NAME, APP_DESCRIPTION, GITHUB_URL
    except ImportError:
        VERSION = "1.00"
        APP_NAME = "TUI File Manager"
        APP_DESCRIPTION = "A terminal-based file manager using curses"
        GITHUB_URL = "https://github.com/shimomut/tfm"
    
    parser = argparse.ArgumentParser(
        prog='tfm',
        description=APP_DESCRIPTION,
        epilog=f"For more information, visit: {GITHUB_URL}"
    )
    
    parser.add_argument(
        '-v', '--version', 
        action='version', 
        version=f'{APP_NAME} {VERSION}'
    )
    
    parser.add_argument(
        '--backend',
        type=str,
        choices=['curses', 'coregraphics'],
        help='Rendering backend to use (default: curses)'
    )
    
    parser.add_argument(
        '--desktop',
        action='store_true',
        help='Run as desktop application (shorthand for --backend coregraphics)'
    )
    
    parser.add_argument(
        '--remote-log-port',
        type=int,
        metavar='PORT',
        help='Enable remote log monitoring on specified port (e.g., --remote-log-port 8888)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        metavar='PATH',
        help='Write logs to specified file (e.g., --log-file /tmp/tfm.log)'
    )
    
    parser.add_argument(
        '--left',
        type=str,
        metavar='PATH',
        help='Specify directory path for left pane (default: current directory)'
    )
    
    parser.add_argument(
        '--right',
        type=str,
        metavar='PATH',
        help='Specify directory path for right pane (default: home directory)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (show DEBUG level logs and full stack traces for uncaught exceptions)'
    )
    
    parser.add_argument(
        '--profile',
        type=str,
        metavar='TARGETS',
        help='Enable performance profiling for specified targets (comma-separated). '
             'Available targets: '
             'rendering (C++ renderer metrics, CoreGraphics only), '
             'event (cProfile event loop iteration). '
             'Example: --profile=event or --profile=rendering,event'
    )
    
    return parser

def cli_main():
    """Command-line entry point with argument parsing"""
    
    parser = create_parser()
    
    try:
        # Parse arguments
        args = parser.parse_args()
        
        # Store debug mode in environment for access by other modules
        if args.debug:
            os.environ['TFM_DEBUG'] = '1'
            print("Debug mode enabled - full stack traces will be shown for uncaught exceptions", file=sys.stderr)
        
        # Parse profiling targets
        profile_targets = set()
        if args.profile:
            profile_targets = set(target.strip() for target in args.profile.split(','))
            valid_targets = {'rendering', 'event'}
            invalid_targets = profile_targets - valid_targets
            if invalid_targets:
                print(f"Warning: Invalid profiling targets: {', '.join(invalid_targets)}", file=sys.stderr)
                print(f"Valid targets: {', '.join(sorted(valid_targets))}")
                profile_targets = profile_targets & valid_targets
        
        # Set ESC delay to 100ms BEFORE any curses-related imports for responsive ESC key
        os.environ.setdefault('ESCDELAY', '100')
        
        # Select backend based on arguments and configuration
        from tfm_backend_selector import select_backend
        backend_name, backend_options = select_backend(args)
        
        # Set Unicode mode based on backend (desktop backends always use full Unicode)
        from ttk.wide_char_utils import initialize_wide_char_utils
        
        # Get configuration values
        config = get_config()
        show_warnings = getattr(config, 'UNICODE_WARNINGS', True)
        terminal_detection = getattr(config, 'UNICODE_TERMINAL_DETECTION', True)
        fallback_char = getattr(config, 'UNICODE_FALLBACK_CHAR', '?')
        
        # Determine Unicode mode based on backend
        if backend_name == 'coregraphics':
            # Desktop backends always use full Unicode
            unicode_mode = 'full'
        else:
            # Terminal backends use configured mode
            unicode_mode = getattr(config, 'UNICODE_MODE', 'full')
        
        # Initialize wide character utilities with all configuration
        initialize_wide_char_utils(
            unicode_mode=unicode_mode,
            show_warnings=show_warnings,
            terminal_detection=terminal_detection,
            fallback_char=fallback_char
        )
        
        # Create TTK renderer directly based on selected backend
        if backend_name == 'curses':
            from ttk.backends.curses_backend import CursesBackend
            renderer = CursesBackend()
        elif backend_name == 'coregraphics':
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
            renderer = CoreGraphicsBackend(**backend_options)
            
            # Enable C++ performance logging if 'rendering' profiling target is specified
            if 'rendering' in profile_targets:
                try:
                    import ttk_coregraphics_render
                    ttk_coregraphics_render.enable_perf_logging(1)
                    print("TFM: C++ renderer performance logging enabled")
                except Exception as e:
                    print(f"TFM: Failed to enable C++ renderer performance logging: {e}", file=sys.stderr)
        else:
            raise ValueError(f"Unknown backend: {backend_name}")
        
        try:
            # Initialize the renderer
            renderer.initialize()
            
            # Pass renderer to main function
            main(renderer,
                 remote_log_port=args.remote_log_port,
                 left_dir=args.left,
                 right_dir=args.right,
                 profiling_targets=profile_targets,
                 log_file=args.log_file,
                 debug=args.debug)
        finally:
            # Ensure renderer is properly shut down
            renderer.shutdown()
        
    except ImportError as e:
        print(f"Error importing TFM modules: {e}", file=sys.stderr)
        print("Make sure you're running from the TFM root directory", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTFM interrupted by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # In debug mode, print full stack trace
        if os.environ.get('TFM_DEBUG') == '1':
            print("\n" + "="*60, file=sys.stderr)
            print("UNCAUGHT EXCEPTION (Debug Mode)", file=sys.stderr)
            print("="*60, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            print("="*60, file=sys.stderr)
        else:
            print(f"Error running TFM: {e}", file=sys.stderr)
            print("Run with --debug flag for full stack trace")
        sys.exit(1)

if __name__ == "__main__":
    cli_main()