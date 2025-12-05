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
from tfm_config import get_programs


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
        self.external_program_manager = ExternalProgramManager(self.config, self.log_manager)
        
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
        
        # 'x' key - show external programs menu
        elif key == ord('x'):
            self._handle_external_programs_menu()
        
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
        
        # 't' key - toggle color scheme
        elif key == ord('t') or key == ord('T'):
            self._handle_toggle_color_scheme()
        
        # F5 key - copy files
        elif event.key_name == 'F5':
            self._handle_copy_operation()
        
        # F6 key - move files
        elif event.key_name == 'F6':
            self._handle_move_operation()
        
        # F8 key - delete files
        elif event.key_name == 'F8':
            self._handle_delete_operation()
        
        # F2 key - rename file
        elif event.key_name == 'F2':
            self._handle_rename_operation()
        
        # Space key - toggle selection
        elif key == ord(' '):
            self._handle_toggle_selection()
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
    
    def _handle_copy_operation(self):
        """Handle copy operation (F5 key)."""
        current_pane = self.pane_manager.get_current_pane()
        other_pane = self.pane_manager.get_inactive_pane()
        
        # Get files to copy
        files_to_copy = self._get_files_for_operation()
        if not files_to_copy:
            self.log_manager.add_message("No files to copy")
            return
        
        destination_dir = other_pane['path']
        
        # Show confirmation dialog
        if len(files_to_copy) == 1:
            message = f"Copy '{files_to_copy[0].name}' to {destination_dir}?"
        else:
            message = f"Copy {len(files_to_copy)} items to {destination_dir}?"
        
        # Use DialogConfig for confirmation
        from tfm_ui_backend import DialogConfig
        dialog_config = DialogConfig(
            type='confirmation',
            title='Confirm Copy',
            message=message
        )
        
        result = self.ui.show_dialog(dialog_config)
        
        if result:
            # Perform copy operation
            self._perform_copy(files_to_copy, destination_dir)
        else:
            self.log_manager.add_message("Copy operation cancelled")
    
    def _handle_move_operation(self):
        """Handle move operation (F6 key)."""
        current_pane = self.pane_manager.get_current_pane()
        other_pane = self.pane_manager.get_inactive_pane()
        
        # Get files to move
        files_to_move = self._get_files_for_operation()
        if not files_to_move:
            self.log_manager.add_message("No files to move")
            return
        
        destination_dir = other_pane['path']
        
        # Check if moving to same directory
        same_dir_files = [f for f in files_to_move if f.parent == destination_dir]
        if same_dir_files:
            if len(same_dir_files) == len(files_to_move):
                self.log_manager.add_message("Cannot move files to the same directory")
                return
            else:
                files_to_move = [f for f in files_to_move if f.parent != destination_dir]
                self.log_manager.add_message(f"Skipping {len(same_dir_files)} files already in destination")
        
        # Show confirmation dialog
        if len(files_to_move) == 1:
            message = f"Move '{files_to_move[0].name}' to {destination_dir}?"
        else:
            message = f"Move {len(files_to_move)} items to {destination_dir}?"
        
        from tfm_ui_backend import DialogConfig
        dialog_config = DialogConfig(
            type='confirmation',
            title='Confirm Move',
            message=message
        )
        
        result = self.ui.show_dialog(dialog_config)
        
        if result:
            # Perform move operation
            self._perform_move(files_to_move, destination_dir)
        else:
            self.log_manager.add_message("Move operation cancelled")
    
    def _handle_delete_operation(self):
        """Handle delete operation (F8 key)."""
        # Get files to delete
        files_to_delete = self._get_files_for_operation()
        if not files_to_delete:
            self.log_manager.add_message("No files to delete")
            return
        
        # Show confirmation dialog
        if len(files_to_delete) == 1:
            file_name = files_to_delete[0].name
            if files_to_delete[0].is_dir():
                message = f"Delete directory '{file_name}' and all its contents?"
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
        
        from tfm_ui_backend import DialogConfig
        dialog_config = DialogConfig(
            type='confirmation',
            title='Confirm Delete',
            message=message
        )
        
        result = self.ui.show_dialog(dialog_config)
        
        if result:
            # Perform delete operation
            self._perform_delete(files_to_delete)
        else:
            self.log_manager.add_message("Delete operation cancelled")
    
    def _handle_rename_operation(self):
        """Handle rename operation (F2 key)."""
        current_pane = self.pane_manager.get_current_pane()
        
        # Get current file
        if not current_pane['files']:
            self.log_manager.add_message("No file to rename")
            return
        
        current_file = current_pane['files'][current_pane['selected_index']]
        
        # Show input dialog
        from tfm_ui_backend import DialogConfig
        dialog_config = DialogConfig(
            type='input',
            title='Rename File',
            message=f"Enter new name for '{current_file.name}':",
            default_value=current_file.name
        )
        
        new_name = self.ui.show_dialog(dialog_config)
        
        if new_name and new_name != current_file.name:
            # Perform rename
            self._perform_rename(current_file, new_name)
        else:
            self.log_manager.add_message("Rename operation cancelled")
    
    def _handle_toggle_selection(self):
        """Handle toggle selection (Space key)."""
        current_pane = self.pane_manager.get_current_pane()
        
        if not current_pane['files']:
            return
        
        # Toggle selection of current file
        success, message = self.file_operations.toggle_selection(current_pane, move_cursor=True, direction=1)
        if success:
            self.log_manager.add_message(message)
    
    def _handle_toggle_color_scheme(self):
        """Handle toggle color scheme (t key)."""
        from tfm_colors import toggle_color_scheme, get_current_color_scheme
        
        # Toggle the color scheme
        new_scheme = toggle_color_scheme()
        
        # Apply the new color scheme to the UI backend
        self.ui_backend.set_color_scheme(new_scheme)
        
        # Log the change
        self.log_manager.add_message(f"Switched to {new_scheme} color scheme")
        
        # Force full redraw
        self.needs_full_redraw = True
    
    def _get_files_for_operation(self) -> list:
        """
        Get files for an operation (either selected files or current file).
        
        Returns:
            List of Path objects
        """
        current_pane = self.pane_manager.get_current_pane()
        files = []
        
        if current_pane['selected_files']:
            # Use selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files.append(file_path)
        else:
            # Use current file
            if current_pane['files']:
                current_file = current_pane['files'][current_pane['selected_index']]
                files.append(current_file)
        
        return files
    
    def _perform_copy(self, files_to_copy: list, destination_dir: Path):
        """
        Perform copy operation in a background thread.
        
        Args:
            files_to_copy: List of files to copy
            destination_dir: Destination directory
        """
        import threading
        from tfm_progress_manager import OperationType
        
        # Set operation in progress
        self.operation_in_progress = True
        self.operation_cancelled = False
        
        # Start progress with cancel callback
        def on_cancel():
            self.operation_cancelled = True
        
        self.progress_manager.start_operation(
            OperationType.COPY,
            len(files_to_copy),
            f"to {destination_dir.name}",
            lambda data: setattr(self, 'needs_full_redraw', True)
        )
        
        # Show progress dialog with cancel support
        self.ui.show_progress("Copying files", 0, len(files_to_copy), "", on_cancel)
        
        def copy_thread():
            try:
                copied_count = 0
                error_count = 0
                
                for i, source_file in enumerate(files_to_copy):
                    if self.operation_cancelled:
                        break
                    
                    try:
                        dest_path = destination_dir / source_file.name
                        
                        # Update progress
                        self.progress_manager.update_progress(source_file.name, i + 1)
                        self.ui.show_progress("Copying files", i + 1, len(files_to_copy), source_file.name)
                        
                        # Copy file
                        source_file.copy_to(dest_path, overwrite=False)
                        copied_count += 1
                        
                    except Exception as e:
                        self.log_manager.add_message(f"Error copying {source_file.name}: {e}", "ERROR")
                        error_count += 1
                        self.progress_manager.increment_errors()
                
                # Finish progress
                self.progress_manager.finish_operation()
                
                # Refresh panes
                self.file_operations.refresh_files(self.pane_manager.left_pane)
                self.file_operations.refresh_files(self.pane_manager.right_pane)
                self.needs_full_redraw = True
                
                # Clear selection
                current_pane = self.pane_manager.get_current_pane()
                current_pane['selected_files'].clear()
                
                # Log result
                if self.operation_cancelled:
                    self.log_manager.add_message(f"Copy cancelled: {copied_count} files copied")
                elif error_count > 0:
                    self.log_manager.add_message(f"Copy completed: {copied_count} files copied, {error_count} errors")
                else:
                    self.log_manager.add_message(f"Successfully copied {copied_count} files")
                
            finally:
                self.operation_in_progress = False
        
        thread = threading.Thread(target=copy_thread, daemon=True)
        thread.start()
    
    def _perform_move(self, files_to_move: list, destination_dir: Path):
        """
        Perform move operation in a background thread.
        
        Args:
            files_to_move: List of files to move
            destination_dir: Destination directory
        """
        import threading
        from tfm_progress_manager import OperationType
        
        # Set operation in progress
        self.operation_in_progress = True
        self.operation_cancelled = False
        
        # Start progress with cancel callback
        def on_cancel():
            self.operation_cancelled = True
        
        self.progress_manager.start_operation(
            OperationType.MOVE,
            len(files_to_move),
            f"to {destination_dir.name}",
            lambda data: setattr(self, 'needs_full_redraw', True)
        )
        
        # Show progress dialog with cancel support
        self.ui.show_progress("Moving files", 0, len(files_to_move), "", on_cancel)
        
        def move_thread():
            try:
                moved_count = 0
                error_count = 0
                
                for i, source_file in enumerate(files_to_move):
                    if self.operation_cancelled:
                        break
                    
                    try:
                        dest_path = destination_dir / source_file.name
                        
                        # Update progress
                        self.progress_manager.update_progress(source_file.name, i + 1)
                        self.ui.show_progress("Moving files", i + 1, len(files_to_move), source_file.name)
                        
                        # Move file
                        source_file.rename(dest_path)
                        moved_count += 1
                        
                    except Exception as e:
                        self.log_manager.add_message(f"Error moving {source_file.name}: {e}", "ERROR")
                        error_count += 1
                        self.progress_manager.increment_errors()
                
                # Finish progress
                self.progress_manager.finish_operation()
                
                # Refresh panes
                self.file_operations.refresh_files(self.pane_manager.left_pane)
                self.file_operations.refresh_files(self.pane_manager.right_pane)
                self.needs_full_redraw = True
                
                # Clear selection
                current_pane = self.pane_manager.get_current_pane()
                current_pane['selected_files'].clear()
                
                # Log result
                if self.operation_cancelled:
                    self.log_manager.add_message(f"Move cancelled: {moved_count} files moved")
                elif error_count > 0:
                    self.log_manager.add_message(f"Move completed: {moved_count} files moved, {error_count} errors")
                else:
                    self.log_manager.add_message(f"Successfully moved {moved_count} files")
                
            finally:
                self.operation_in_progress = False
        
        thread = threading.Thread(target=move_thread, daemon=True)
        thread.start()
    
    def _perform_delete(self, files_to_delete: list):
        """
        Perform delete operation in a background thread.
        
        Args:
            files_to_delete: List of files to delete
        """
        import threading
        from tfm_progress_manager import OperationType
        
        # Set operation in progress
        self.operation_in_progress = True
        self.operation_cancelled = False
        
        # Start progress with cancel callback
        def on_cancel():
            self.operation_cancelled = True
        
        self.progress_manager.start_operation(
            OperationType.DELETE,
            len(files_to_delete),
            "",
            lambda data: setattr(self, 'needs_full_redraw', True)
        )
        
        # Show progress dialog with cancel support
        self.ui.show_progress("Deleting files", 0, len(files_to_delete), "", on_cancel)
        
        def delete_thread():
            try:
                deleted_count = 0
                error_count = 0
                
                for i, file_path in enumerate(files_to_delete):
                    if self.operation_cancelled:
                        break
                    
                    try:
                        # Update progress
                        self.progress_manager.update_progress(file_path.name, i + 1)
                        self.ui.show_progress("Deleting files", i + 1, len(files_to_delete), file_path.name)
                        
                        # Delete file or directory
                        if file_path.is_dir():
                            import shutil
                            shutil.rmtree(str(file_path))
                        else:
                            file_path.unlink()
                        
                        deleted_count += 1
                        
                    except Exception as e:
                        self.log_manager.add_message(f"Error deleting {file_path.name}: {e}", "ERROR")
                        error_count += 1
                        self.progress_manager.increment_errors()
                
                # Finish progress
                self.progress_manager.finish_operation()
                
                # Refresh current pane
                current_pane = self.pane_manager.get_current_pane()
                self.file_operations.refresh_files(current_pane)
                self.needs_full_redraw = True
                
                # Clear selection
                current_pane['selected_files'].clear()
                
                # Adjust cursor if needed
                if current_pane['selected_index'] >= len(current_pane['files']):
                    current_pane['selected_index'] = max(0, len(current_pane['files']) - 1)
                
                # Log result
                if self.operation_cancelled:
                    self.log_manager.add_message(f"Delete cancelled: {deleted_count} files deleted")
                elif error_count > 0:
                    self.log_manager.add_message(f"Delete completed: {deleted_count} files deleted, {error_count} errors")
                else:
                    self.log_manager.add_message(f"Successfully deleted {deleted_count} files")
                
            finally:
                self.operation_in_progress = False
        
        thread = threading.Thread(target=delete_thread, daemon=True)
        thread.start()
    
    def _perform_rename(self, file_path: Path, new_name: str):
        """
        Perform rename operation.
        
        Args:
            file_path: File to rename
            new_name: New name for the file
        """
        try:
            new_path = file_path.parent / new_name
            
            # Check if destination exists
            if new_path.exists():
                self.log_manager.add_message(f"File '{new_name}' already exists", "ERROR")
                return
            
            # Rename file
            file_path.rename(new_path)
            
            # Refresh current pane
            current_pane = self.pane_manager.get_current_pane()
            self.file_operations.refresh_files(current_pane)
            self.needs_full_redraw = True
            
            self.log_manager.add_message(f"Renamed '{file_path.name}' to '{new_name}'")
            
        except Exception as e:
            self.log_manager.add_message(f"Error renaming file: {e}", "ERROR")
    
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
            {'key': 'x', 'label': 'programs'},
            {'key': 'q', 'label': 'quit'}
        ]
    
    def _handle_external_programs_menu(self):
        """Handle external programs menu (x key)."""
        programs = get_programs()
        
        if not programs:
            self.log_manager.add_message("No external programs configured")
            return
        
        # Create list of program names for dialog
        program_names = [p['name'] for p in programs]
        
        # Show list selection dialog
        from tfm_ui_backend import DialogConfig
        dialog_config = DialogConfig(
            type='list',
            title='External Programs',
            message='Select a program to execute:',
            choices=program_names
        )
        
        selected = self.ui.show_dialog(dialog_config)
        
        if selected:
            # Find the selected program
            program = next((p for p in programs if p['name'] == selected), None)
            if program:
                self._execute_external_program(program)
        else:
            self.log_manager.add_message("Program selection cancelled")
    
    def _execute_external_program(self, program: dict):
        """
        Execute an external program and refresh file listings after completion.
        
        This method handles external program execution for both TUI and GUI modes
        by delegating to the appropriate backend implementation.
        
        Args:
            program: Program configuration dict with 'name', 'command', and optional 'options'
        """
        # Check if UI backend has execute_external_program method (Qt mode)
        if hasattr(self.ui, 'execute_external_program'):
            # Qt mode - use Qt backend's implementation
            success = self.ui.execute_external_program(program, self.pane_manager)
            
            # Refresh file listings after program completes
            if success:
                self._refresh_after_external_program()
        else:
            # TUI mode - would use curses-based implementation
            # This will be implemented when CursesBackend is updated
            self.log_manager.add_message("External programs not yet supported in TUI mode through abstraction layer")
    
    def _refresh_after_external_program(self):
        """
        Refresh file listings after external program execution.
        
        This ensures that any changes made by the external program
        (file creation, deletion, modification) are visible in TFM.
        """
        # Refresh both panes
        self.file_operations.refresh_files(self.pane_manager.left_pane)
        self.file_operations.refresh_files(self.pane_manager.right_pane)
        
        # Trigger full redraw
        self.needs_full_redraw = True
        
        # Log the refresh
        self.log_manager.add_message("File listings refreshed after external program execution")
    
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
