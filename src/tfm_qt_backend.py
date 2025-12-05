"""
Qt Backend Implementation for TFM

This module implements the IUIBackend interface using Qt for Python (PySide6),
providing a graphical user interface for TFM.
"""

import os
import queue
import subprocess
from typing import Tuple, Dict, List, Any, Optional, Callable

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QEvent, QProcess
from PySide6.QtGui import QKeyEvent, QMouseEvent, QResizeEvent

from tfm_ui_backend import IUIBackend, InputEvent, LayoutInfo, DialogConfig
from tfm_qt_main_window import TFMMainWindow
from tfm_qt_file_pane import FilePaneWidget
from tfm_qt_header import HeaderWidget
from tfm_qt_footer import FooterWidget
from tfm_qt_log_pane import LogPaneWidget
from tfm_qt_colors import apply_color_scheme, get_qt_colors
from tfm_external_programs import quote_filenames_with_double_quotes, get_selected_or_cursor_files


class QtBackend(IUIBackend):
    """
    Qt-based GUI backend implementation.
    
    This class implements the IUIBackend interface using Qt for Python,
    allowing the application controller to work with a graphical interface
    without direct Qt dependencies in business logic.
    """
    
    def __init__(self, app: QApplication):
        """
        Initialize the Qt backend.
        
        Args:
            app: The QApplication instance
        """
        self.app = app
        self.main_window = None
        self.event_queue = queue.Queue()
        self.color_scheme = 'dark'  # Default color scheme
        
        # Widget references (will be set during initialization)
        self.left_pane_widget = None
        self.right_pane_widget = None
        self.header_widget = None
        self.footer_widget = None
        self.log_pane_widget = None
    
    def initialize(self) -> bool:
        """
        Initialize the Qt UI backend.
        
        Creates the main window and sets up all widgets.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Create main window
            self.main_window = TFMMainWindow()
            
            # Create header widget
            self.header_widget = HeaderWidget()
            
            # Create file pane widgets
            self.left_pane_widget = FilePaneWidget()
            self.right_pane_widget = FilePaneWidget()
            
            # Create footer widget
            self.footer_widget = FooterWidget()
            
            # Create log pane widget
            self.log_pane_widget = LogPaneWidget()
            
            # Set up the main window layout
            # TODO: Integrate widgets into main window layout
            # For now, just set the pane widgets
            self.main_window.set_left_pane_widget(self.left_pane_widget)
            self.main_window.set_right_pane_widget(self.right_pane_widget)
            
            # Connect signals for input events
            self._connect_signals()
            
            # Apply initial color scheme
            apply_color_scheme(self.app, self.color_scheme)
            self.left_pane_widget.set_color_scheme(self.color_scheme)
            self.right_pane_widget.set_color_scheme(self.color_scheme)
            
            # Show the main window
            self.main_window.show()
            
            return True
            
        except Exception as e:
            print(f"Error initializing Qt backend: {e}")
            return False
    
    def cleanup(self):
        """
        Clean up Qt resources.
        
        Closes the main window and releases resources.
        """
        if self.main_window:
            self.main_window.close()
            self.main_window = None
    
    def _connect_signals(self):
        """Connect Qt signals to event queue."""
        # Install event filter on main window to capture all events
        if self.main_window:
            self.main_window.installEventFilter(self)
            
            # Connect keyboard shortcut action signals
            self.main_window.action_triggered.connect(self._on_action_triggered)
            
            # Connect Tab key pane switching signal
            self.main_window.switch_pane_requested.connect(self._on_switch_pane_requested)
        
        # Connect file pane signals
        if self.left_pane_widget:
            self.left_pane_widget.file_selected.connect(
                lambda idx: self._queue_event(InputEvent(type='key', key_name='file_selected_left'))
            )
            self.left_pane_widget.file_activated.connect(
                lambda idx: self._queue_event(InputEvent(type='key', key_name='Enter'))
            )
            self.left_pane_widget.files_dropped.connect(
                lambda files, target: self._on_files_dropped(files, target, 'left')
            )
            self.left_pane_widget.context_action_triggered.connect(
                lambda action: self._on_context_action(action, 'left')
            )
        
        if self.right_pane_widget:
            self.right_pane_widget.file_selected.connect(
                lambda idx: self._queue_event(InputEvent(type='key', key_name='file_selected_right'))
            )
            self.right_pane_widget.file_activated.connect(
                lambda idx: self._queue_event(InputEvent(type='key', key_name='Enter'))
            )
            self.right_pane_widget.files_dropped.connect(
                lambda files, target: self._on_files_dropped(files, target, 'right')
            )
            self.right_pane_widget.context_action_triggered.connect(
                lambda action: self._on_context_action(action, 'right')
            )
    
    def _on_action_triggered(self, action_name: str):
        """
        Handle action triggered by keyboard shortcut.
        
        Args:
            action_name: Name of the action that was triggered
        """
        # Queue an input event with the action name
        self._queue_event(InputEvent(
            type='action',
            key_name=action_name
        ))
    
    def _on_switch_pane_requested(self):
        """Handle Tab key press for pane switching."""
        # Queue a Tab key event with key code 9 (Tab)
        self._queue_event(InputEvent(
            type='key',
            key=9,  # Tab key code
            key_name='Tab'
        ))
    
    def _on_files_dropped(self, file_paths: List[str], target_dir: str, pane: str):
        """
        Handle files dropped onto a pane.
        
        Args:
            file_paths: List of file paths that were dropped
            target_dir: Target directory where files were dropped
            pane: Which pane received the drop ('left' or 'right')
        """
        # Queue a custom event with drop information
        # The application controller can handle this event to perform copy/move
        self._queue_event(InputEvent(
            type='drop',
            key_name=f'files_dropped_{pane}',
            modifiers={'files': file_paths, 'target': target_dir}
        ))
    
    def _on_context_action(self, action: str, pane: str):
        """
        Handle context menu action triggered.
        
        Args:
            action: Action name (e.g., 'copy', 'move', 'delete')
            pane: Which pane triggered the action ('left' or 'right')
        """
        # Queue an action event
        self._queue_event(InputEvent(
            type='action',
            key_name=action
        ))
    
    def eventFilter(self, obj, event):
        """
        Event filter to capture Qt events and convert to InputEvents.
        
        Args:
            obj: Object that received the event
            event: The Qt event
        
        Returns:
            False to allow event to propagate
        """
        # Capture key press events
        if event.type() == QEvent.KeyPress:
            input_event = self._convert_qt_key_event(event)
            if input_event:
                self._queue_event(input_event)
        
        # Capture mouse events
        elif event.type() == QEvent.MouseButtonPress:
            input_event = self._convert_qt_mouse_event(event)
            if input_event:
                self._queue_event(input_event)
        
        # Capture resize events
        elif event.type() == QEvent.Resize:
            self._queue_event(InputEvent(type='resize'))
        
        # Allow event to propagate
        return False
    
    def _queue_event(self, event: InputEvent):
        """
        Queue an input event.
        
        Args:
            event: InputEvent to queue
        """
        self.event_queue.put(event)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get current window dimensions.
        
        Returns:
            Tuple of (height, width) in pixels
        """
        if self.main_window:
            size = self.main_window.size()
            return (size.height(), size.width())
        return (800, 1200)  # Default size
    
    def refresh(self):
        """
        Refresh the display.
        
        Processes Qt events to update the window.
        """
        if self.app:
            self.app.processEvents()
    
    def set_color_scheme(self, scheme: str):
        """
        Set the color scheme.
        
        Args:
            scheme: Color scheme name (e.g., 'dark', 'light', 'custom')
        """
        self.color_scheme = scheme
        
        # Apply color scheme to the application
        try:
            apply_color_scheme(self.app, scheme)
            
            # Update file pane colors
            if self.left_pane_widget:
                self.left_pane_widget.set_color_scheme(scheme)
            if self.right_pane_widget:
                self.right_pane_widget.set_color_scheme(scheme)
                
        except Exception as e:
            print(f"Warning: Could not set color scheme '{scheme}': {e}")
    
    def render_panes(self, left_pane: Dict, right_pane: Dict, 
                    active_pane: str, layout: LayoutInfo):
        """
        Render the dual-pane file browser.
        
        Updates the FilePaneWidget contents for both panes.
        
        Args:
            left_pane: Left pane data (path, files, selection, etc.)
            right_pane: Right pane data (path, files, selection, etc.)
            active_pane: Which pane is active ('left' or 'right')
            layout: Layout information for positioning
        """
        # Update left pane
        if self.left_pane_widget:
            self.left_pane_widget.update_files(left_pane.get('files', []))
            self.left_pane_widget.current_index = left_pane.get('selected_index', 0)
            self.left_pane_widget.selected_files = left_pane.get('selected_files', set())
            self.left_pane_widget.set_active(active_pane == 'left')
        
        # Update right pane
        if self.right_pane_widget:
            self.right_pane_widget.update_files(right_pane.get('files', []))
            self.right_pane_widget.current_index = right_pane.get('selected_index', 0)
            self.right_pane_widget.selected_files = right_pane.get('selected_files', set())
            self.right_pane_widget.set_active(active_pane == 'right')
        
        # Update keyboard shortcuts based on selection status
        # Check if any files are selected in the active pane
        active_pane_data = left_pane if active_pane == 'left' else right_pane
        has_selection = len(active_pane_data.get('selected_files', set())) > 0
        
        if self.main_window:
            self.main_window.update_shortcuts_for_selection(has_selection)
    
    def render_header(self, left_path: str, right_path: str, active_pane: str):
        """
        Render the header with directory paths.
        
        Updates the HeaderWidget with current paths.
        
        Args:
            left_path: Path displayed in left pane header
            right_path: Path displayed in right pane header
            active_pane: Which pane is active ('left' or 'right')
        """
        if self.header_widget:
            self.header_widget.set_paths(left_path, right_path)
            self.header_widget.set_active_pane(active_pane)
    
    def render_footer(self, left_info: str, right_info: str, active_pane: str):
        """
        Render the footer with file counts and sort info.
        
        Updates the FooterWidget with information text.
        
        Args:
            left_info: Information text for left pane footer
            right_info: Information text for right pane footer
            active_pane: Which pane is active ('left' or 'right')
        """
        if self.footer_widget:
            self.footer_widget.set_info(left_info, right_info)
            self.footer_widget.set_active_pane(active_pane)
    
    def render_status_bar(self, message: str, controls: List[Dict]):
        """
        Render the status bar with message and controls.
        
        Updates the main window status bar.
        
        Args:
            message: Status message to display
            controls: List of control hints (e.g., [{'key': 'F1', 'label': 'Help'}])
        """
        if self.main_window and self.main_window.status_bar:
            # Format controls string
            controls_str = "  •  ".join([f"{c['key']}:{c['label']}" for c in controls])
            
            # Combine message and controls
            if message and controls_str:
                full_message = f"{message}    {controls_str}"
            elif message:
                full_message = message
            else:
                full_message = controls_str
            
            self.main_window.status_bar.showMessage(full_message)
    
    def render_log_pane(self, messages: List[str], scroll_offset: int, 
                       height_ratio: float):
        """
        Render the log message pane.
        
        Updates the LogPaneWidget with messages.
        
        Args:
            messages: List of log messages to display (tuples of timestamp, source, message)
            scroll_offset: Scroll position in the message list
            height_ratio: Ratio of screen height to use for log pane
        """
        if self.log_pane_widget:
            # Update all messages
            self.log_pane_widget.update_messages(messages)
            
            # TODO: Handle scroll_offset and height_ratio
            # For now, the log pane auto-scrolls to the bottom
    
    def get_input_event(self, timeout: int = -1) -> Optional[InputEvent]:
        """
        Get next input event (key press, mouse click, etc.).
        
        Reads from the event queue populated by Qt signals.
        
        Args:
            timeout: Timeout in milliseconds (-1 for blocking, 0 for non-blocking)
        
        Returns:
            InputEvent if available, None if timeout or no event
        """
        try:
            if timeout == 0:
                # Non-blocking
                return self.event_queue.get_nowait()
            elif timeout > 0:
                # Blocking with timeout
                return self.event_queue.get(timeout=timeout / 1000.0)
            else:
                # Blocking indefinitely
                return self.event_queue.get()
        except queue.Empty:
            return None
    
    def _convert_qt_key_event(self, event: QKeyEvent) -> Optional[InputEvent]:
        """
        Convert Qt key event to InputEvent.
        
        Args:
            event: Qt key event
        
        Returns:
            InputEvent object or None
        """
        key = event.key()
        modifiers = event.modifiers()
        
        # Build modifiers set
        mod_set = set()
        if modifiers & Qt.ControlModifier:
            mod_set.add('ctrl')
        if modifiers & Qt.ShiftModifier:
            mod_set.add('shift')
        if modifiers & Qt.AltModifier:
            mod_set.add('alt')
        if modifiers & Qt.MetaModifier:
            mod_set.add('meta')
        
        # Map Qt keys to key names
        key_name = None
        
        # Special keys
        special_keys = {
            Qt.Key_Up: 'Up',
            Qt.Key_Down: 'Down',
            Qt.Key_Left: 'Left',
            Qt.Key_Right: 'Right',
            Qt.Key_Home: 'Home',
            Qt.Key_End: 'End',
            Qt.Key_PageUp: 'PageUp',
            Qt.Key_PageDown: 'PageDown',
            Qt.Key_Delete: 'Delete',
            Qt.Key_Backspace: 'Backspace',
            Qt.Key_Return: 'Enter',
            Qt.Key_Enter: 'Enter',
            Qt.Key_Tab: 'Tab',
            Qt.Key_Escape: 'Escape',
            Qt.Key_Space: 'Space',
        }
        
        # Function keys
        for i in range(1, 13):
            special_keys[getattr(Qt, f'Key_F{i}')] = f'F{i}'
        
        if key in special_keys:
            key_name = special_keys[key]
        else:
            # Try to get text representation
            text = event.text()
            if text:
                key_name = text
        
        return InputEvent(
            type='key',
            key=key,
            key_name=key_name,
            modifiers=mod_set
        )
    
    def _convert_qt_mouse_event(self, event: QMouseEvent) -> Optional[InputEvent]:
        """
        Convert Qt mouse event to InputEvent.
        
        Args:
            event: Qt mouse event
        
        Returns:
            InputEvent object or None
        """
        pos = event.pos()
        button = event.button()
        
        # Map Qt mouse buttons to button numbers
        button_map = {
            Qt.LeftButton: 1,
            Qt.MiddleButton: 2,
            Qt.RightButton: 3,
        }
        
        button_num = button_map.get(button, 0)
        
        # Build modifiers set
        modifiers = event.modifiers()
        mod_set = set()
        if modifiers & Qt.ControlModifier:
            mod_set.add('ctrl')
        if modifiers & Qt.ShiftModifier:
            mod_set.add('shift')
        if modifiers & Qt.AltModifier:
            mod_set.add('alt')
        if modifiers & Qt.MetaModifier:
            mod_set.add('meta')
        
        return InputEvent(
            type='mouse',
            mouse_x=pos.x(),
            mouse_y=pos.y(),
            mouse_button=button_num,
            modifiers=mod_set
        )
    
    def show_dialog(self, dialog_config: DialogConfig) -> Any:
        """
        Show a dialog and return user response.
        
        Args:
            dialog_config: Dialog configuration
        
        Returns:
            User response (type depends on dialog type):
            - confirmation: bool or str ('yes', 'no', 'cancel')
            - input: str or None
            - list: selected item(s) or None
            - info: None
            - progress: None (non-blocking)
        """
        from PySide6.QtWidgets import QMessageBox, QInputDialog
        
        if dialog_config.type == 'confirmation':
            # Show confirmation dialog with Yes/No/Cancel options
            # Check if Cancel option is needed
            buttons = QMessageBox.Yes | QMessageBox.No
            if dialog_config.choices and any(c.get('value') == 'cancel' for c in dialog_config.choices):
                buttons |= QMessageBox.Cancel
            
            result = QMessageBox.question(
                self.main_window,
                dialog_config.title,
                dialog_config.message,
                buttons,
                QMessageBox.No
            )
            
            # Return appropriate value based on button clicked
            if result == QMessageBox.Yes:
                return True
            elif result == QMessageBox.No:
                return False
            else:  # Cancel
                return None
        
        elif dialog_config.type == 'input':
            # Show input dialog
            text, ok = QInputDialog.getText(
                self.main_window,
                dialog_config.title,
                dialog_config.message,
                text=dialog_config.default_value or ""
            )
            return text if ok else None
        
        elif dialog_config.type == 'list':
            # Show custom list selection dialog with search/filter
            from tfm_qt_list_dialog import ListSelectionDialog
            
            if not dialog_config.choices:
                return None
            
            # Determine if multi-select is needed
            multi_select = dialog_config.default_value == 'multi' if dialog_config.default_value else False
            
            selected = ListSelectionDialog.get_selection(
                parent=self.main_window,
                title=dialog_config.title,
                message=dialog_config.message,
                items=dialog_config.choices,
                multi_select=multi_select
            )
            
            if selected:
                # Return single item for single-select, list for multi-select
                return selected if multi_select else selected[0]
            
            return None
        
        elif dialog_config.type == 'info':
            # Show custom information dialog with scrolling support
            from tfm_qt_info_dialog import InfoDialog
            
            # Use default_value as content if provided, otherwise use message
            content = dialog_config.default_value if dialog_config.default_value else dialog_config.message
            
            InfoDialog.show_info(
                parent=self.main_window,
                title=dialog_config.title,
                message="",
                content=content
            )
            return None
        
        elif dialog_config.type == 'progress':
            # Progress dialogs are handled separately via show_progress()
            return None
        
        else:
            raise ValueError(f"Unknown dialog type: {dialog_config.type}")
    
    def show_progress(self, operation: str, current: int, total: int, 
                     message: str, cancel_callback: Optional[Callable] = None):
        """
        Show or update progress indicator for long operations.
        
        Args:
            operation: Name of the operation (e.g., 'Copying files')
            current: Current progress value
            total: Total progress value
            message: Current status message (e.g., current file name)
            cancel_callback: Optional callback to call when user cancels
        """
        from tfm_qt_progress_dialog import ProgressDialog
        
        # Create progress dialog if it doesn't exist
        if not hasattr(self, '_progress_dialog') or self._progress_dialog is None:
            self._progress_dialog = ProgressDialog.create_progress(
                parent=self.main_window,
                title="Progress",
                operation=operation,
                cancelable=True
            )
            
            # Connect cancel signal if callback provided
            if cancel_callback:
                self._progress_dialog.cancelled.connect(cancel_callback)
        
        # Update progress
        self._progress_dialog.update_progress(current, total, message)
        
        # Auto-close when complete
        if current >= total and total > 0:
            self._progress_dialog.auto_close()
            self._progress_dialog = None
    
    def get_selected_files(self, pane: str) -> list:
        """
        Get selected files from a pane.
        
        Args:
            pane: Which pane ('left' or 'right')
        
        Returns:
            List of selected file paths
        """
        if pane == 'left' and self.left_pane_widget:
            return self.left_pane_widget.get_selected_files()
        elif pane == 'right' and self.right_pane_widget:
            return self.right_pane_widget.get_selected_files()
        return []
    
    def get_current_file(self, pane: str):
        """
        Get the current file (at cursor position) from a pane.
        
        Args:
            pane: Which pane ('left' or 'right')
        
        Returns:
            Path object for current file, or None
        """
        if pane == 'left' and self.left_pane_widget:
            return self.left_pane_widget.get_current_file()
        elif pane == 'right' and self.right_pane_widget:
            return self.right_pane_widget.get_current_file()
        return None
    
    def clear_selection(self, pane: str):
        """
        Clear file selection in a pane.
        
        Args:
            pane: Which pane ('left' or 'right')
        """
        if pane == 'left' and self.left_pane_widget:
            self.left_pane_widget.clear_selection()
        elif pane == 'right' and self.right_pane_widget:
            self.right_pane_widget.clear_selection()


    def execute_external_program(self, program: Dict, pane_manager) -> bool:
        """
        Execute an external program with TFM environment variables.
        
        This method launches external programs in Qt mode using the same
        environment variable approach as TUI mode, ensuring consistent
        integration across both interfaces.
        
        Args:
            program: Program configuration dict with 'name', 'command', and optional 'options'
            pane_manager: PaneManager instance for accessing pane data
        
        Returns:
            True if program executed successfully, False otherwise
        """
        try:
            # Get current pane information
            left_pane = pane_manager.left_pane
            right_pane = pane_manager.right_pane
            current_pane = pane_manager.get_current_pane()
            other_pane = pane_manager.get_inactive_pane()
            
            # Set environment variables with TFM_ prefix (same as TUI mode)
            env = os.environ.copy()
            env['TFM_LEFT_DIR'] = str(left_pane['path'])
            env['TFM_RIGHT_DIR'] = str(right_pane['path'])
            env['TFM_THIS_DIR'] = str(current_pane['path'])
            env['TFM_OTHER_DIR'] = str(other_pane['path'])
            
            # Get selected files for each pane, or cursor position if no selection
            left_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(left_pane))
            right_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(right_pane))
            current_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(current_pane))
            other_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(other_pane))
            
            # Set selected files environment variables (space-separated) with TFM_ prefix
            env['TFM_LEFT_SELECTED'] = ' '.join(left_selected)
            env['TFM_RIGHT_SELECTED'] = ' '.join(right_selected)
            env['TFM_THIS_SELECTED'] = ' '.join(current_selected)
            env['TFM_OTHER_SELECTED'] = ' '.join(other_selected)
            
            # Set TFM indicator environment variable
            env['TFM_ACTIVE'] = '1'
            
            # Use the command as-is (users should use tfm_tool() for TFM tools)
            command = program['command']
            
            # Determine working directory for external program
            # If current pane is browsing a remote directory (like S3), 
            # fallback to TFM's working directory
            working_dir = None
            if current_pane['path'].is_remote():
                working_dir = os.getcwd()
            else:
                working_dir = str(current_pane['path'])
            
            # Check if auto_return option is enabled
            auto_return = program.get('options', {}).get('auto_return', False)
            
            # Execute the program with the modified environment
            # Use QProcess for better Qt integration
            process = QProcess()
            process.setWorkingDirectory(working_dir)
            
            # Set environment variables
            process_env = QProcess.systemEnvironment()
            for key, value in env.items():
                process_env.append(f"{key}={value}")
            process.setEnvironment(process_env)
            
            # Start the process
            program_name = command[0]
            program_args = command[1:] if len(command) > 1 else []
            
            # For GUI programs with auto_return, start detached
            if auto_return:
                success = process.startDetached(program_name, program_args, working_dir)
                if not success:
                    raise OSError(f"Failed to start program: {program_name}")
                return True
            else:
                # For CLI programs, start and wait
                process.start(program_name, program_args)
                
                if not process.waitForStarted(5000):  # 5 second timeout
                    raise OSError(f"Failed to start program: {program_name}")
                
                # Wait for process to finish
                if not process.waitForFinished(-1):  # Wait indefinitely
                    raise OSError(f"Program did not finish properly: {program_name}")
                
                # Check exit code
                exit_code = process.exitCode()
                if exit_code != 0:
                    error_output = process.readAllStandardError().data().decode('utf-8', errors='replace')
                    raise subprocess.CalledProcessError(exit_code, command, stderr=error_output)
                
                return True
        
        except FileNotFoundError as e:
            # Program not found
            QMessageBox.critical(
                self.main_window,
                "Program Not Found",
                f"Error: Command not found: {program['command'][0]}\n\n"
                f"Tip: Use tfm_tool() function for TFM tools in your configuration\n\n"
                f"Details: {e}"
            )
            return False
        
        except subprocess.CalledProcessError as e:
            # Program exited with error
            error_msg = f"Program '{program['name']}' exited with code {e.returncode}"
            if e.stderr:
                error_msg += f"\n\nError output:\n{e.stderr}"
            
            QMessageBox.warning(
                self.main_window,
                "Program Error",
                error_msg
            )
            return False
        
        except OSError as e:
            # System error (permissions, etc.)
            QMessageBox.critical(
                self.main_window,
                "System Error",
                f"Error executing program '{program['name']}':\n\n{e}"
            )
            return False
        
        except Exception as e:
            # Unexpected error
            QMessageBox.critical(
                self.main_window,
                "Unexpected Error",
                f"Unexpected error executing program '{program['name']}':\n\n{e}"
            )
            return False
