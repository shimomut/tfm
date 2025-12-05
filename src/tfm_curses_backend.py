"""
Curses Backend Implementation for TFM

This module implements the IUIBackend interface using the curses library,
wrapping the existing TUI functionality.
"""

import curses
from typing import Tuple, Dict, List, Any, Optional

from tfm_ui_backend import IUIBackend, InputEvent, LayoutInfo, DialogConfig
from tfm_colors import init_colors, get_background_color_pair, apply_background_to_window


class CursesBackend(IUIBackend):
    """
    Curses-based TUI backend implementation.
    
    This class wraps existing curses code and implements the IUIBackend
    interface, allowing the application controller to work with curses
    without direct dependencies.
    """
    
    def __init__(self, stdscr):
        """
        Initialize the curses backend.
        
        Args:
            stdscr: The curses standard screen object
        """
        self.stdscr = stdscr
        self.color_scheme = 'dark'  # Default color scheme
    
    def initialize(self) -> bool:
        """
        Initialize the curses UI backend.
        
        Sets up curses environment including:
        - Hiding cursor
        - Enabling keypad mode
        - Initializing colors
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Hide cursor
            curses.curs_set(0)
            
            # Enable keypad mode for special keys
            self.stdscr.keypad(True)
            
            # Initialize colors with default scheme
            init_colors(self.color_scheme)
            
            return True
            
        except curses.error as e:
            print(f"Error initializing curses backend: {e}")
            return False
    
    def cleanup(self):
        """
        Clean up curses resources.
        
        Restores the terminal to its original state.
        
        Note: When using curses.wrapper(), endwin() is automatically called.
        We only need to restore cursor visibility here.
        """
        try:
            # Restore cursor visibility
            curses.curs_set(1)
            
        except curses.error:
            # Ignore errors during cleanup - terminal may already be cleaned up
            pass
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get current terminal dimensions.
        
        Returns:
            Tuple of (height, width) in characters
        """
        try:
            height, width = self.stdscr.getmaxyx()
            return (height, width)
        except curses.error:
            # Return default size if error
            return (24, 80)
    
    def render_panes(self, left_pane: Dict, right_pane: Dict, 
                    active_pane: str, layout: LayoutInfo):
        """
        Render the dual-pane file browser.
        
        This method wraps the existing draw_pane logic from FileManager.
        
        Args:
            left_pane: Left pane data (path, files, selection, etc.)
            right_pane: Right pane data (path, files, selection, etc.)
            active_pane: Which pane is active ('left' or 'right')
            layout: Layout information for positioning
        """
        from tfm_colors import get_boundary_color
        
        # Draw vertical separator between panes
        for y in range(layout.panes_y, layout.footer_y):
            try:
                self.stdscr.addstr(y, layout.left_pane_width, "│", get_boundary_color())
            except curses.error:
                pass
        
        # Draw left pane
        self._draw_pane(left_pane, 0, layout.left_pane_width, 
                       active_pane == 'left', layout)
        
        # Draw right pane
        self._draw_pane(right_pane, layout.left_pane_width, layout.right_pane_width,
                       active_pane == 'right', layout)
    
    def render_header(self, left_path: str, right_path: str, active_pane: str):
        """
        Render the header with directory paths.
        
        This method wraps the existing draw_header logic from FileManager.
        
        Args:
            left_path: Path displayed in left pane header
            right_path: Path displayed in right pane header
            active_pane: Which pane is active ('left' or 'right')
        """
        from tfm_colors import get_header_color, get_boundary_color
        from tfm_wide_char_utils import safe_get_display_width, truncate_to_width
        
        height, width = self.get_screen_size()
        left_pane_width = width // 2
        right_pane_width = width - left_pane_width
        
        # Clear header area
        try:
            self.stdscr.addstr(0, 0, " " * (width - 1), get_header_color())
        except curses.error:
            pass
        
        # Left pane path
        if left_pane_width > 6:
            max_left_path_width = max(1, left_pane_width - 4)
            if safe_get_display_width(left_path) > max_left_path_width:
                left_path = truncate_to_width(left_path, max_left_path_width, "...")
            
            left_color = get_header_color(active_pane == 'left')
            try:
                self.stdscr.addstr(0, 2, left_path, left_color)
            except curses.error:
                pass
        
        # Separator
        if 0 <= left_pane_width < width:
            try:
                self.stdscr.addstr(0, left_pane_width, "│", get_boundary_color())
            except curses.error:
                pass
        
        # Right pane path
        if right_pane_width > 6:
            max_right_path_width = max(1, right_pane_width - 4)
            if safe_get_display_width(right_path) > max_right_path_width:
                right_path = truncate_to_width(right_path, max_right_path_width, "...")
            
            right_color = get_header_color(active_pane == 'right')
            try:
                right_start_x = left_pane_width + 2
                if right_start_x < width:
                    self.stdscr.addstr(0, right_start_x, right_path, right_color)
            except curses.error:
                pass
    
    def render_footer(self, left_info: str, right_info: str, active_pane: str):
        """
        Render the footer with file counts and sort info.
        
        This method wraps the existing draw_file_footers logic from FileManager.
        
        Args:
            left_info: Information text for left pane footer
            right_info: Information text for right pane footer
            active_pane: Which pane is active ('left' or 'right')
        """
        from tfm_colors import get_footer_color
        
        height, width = self.get_screen_size()
        left_pane_width = width // 2
        
        # Calculate footer Y position (depends on log height)
        # This will be passed in via layout in the future, but for now calculate it
        footer_y = height - 2  # Above status line
        
        # Left pane footer
        try:
            left_color = get_footer_color(active_pane == 'left')
            self.stdscr.addstr(footer_y, 2, left_info, left_color)
        except curses.error:
            pass
        
        # Right pane footer
        try:
            right_color = get_footer_color(active_pane == 'right')
            self.stdscr.addstr(footer_y, left_pane_width + 2, right_info, right_color)
        except curses.error:
            pass
    
    def render_status_bar(self, message: str, controls: List[Dict]):
        """
        Render the status bar with message and controls.
        
        This method wraps the existing draw_status logic from FileManager.
        
        Args:
            message: Status message to display
            controls: List of control hints (e.g., [{'key': 'F1', 'label': 'Help'}])
        """
        from tfm_colors import get_status_color
        
        height, width = self.get_screen_size()
        status_y = height - 1
        
        # Fill entire status line with background color
        status_line = " " * (width - 1)
        try:
            self.stdscr.addstr(status_y, 0, status_line, get_status_color())
        except curses.error:
            pass
        
        # Format controls string
        controls_str = "  •  ".join([f"{c['key']}:{c['label']}" for c in controls])
        
        # Draw status message and controls
        if message:
            try:
                self.stdscr.addstr(status_y, 2, message, get_status_color())
            except curses.error:
                pass
            
            # Right-align controls if there's space
            if len(message) + len(controls_str) + 8 < width:
                controls_x = width - len(controls_str) - 3
                try:
                    self.stdscr.addstr(status_y, controls_x, controls_str, get_status_color())
                except curses.error:
                    pass
        else:
            # Center controls when no message
            controls_x = max(2, (width - len(controls_str)) // 2)
            try:
                self.stdscr.addstr(status_y, controls_x, controls_str, get_status_color())
            except curses.error:
                pass
    
    def render_log_pane(self, messages: List[str], scroll_offset: int, 
                       height_ratio: float):
        """
        Render the log message pane.
        
        This method wraps the existing draw_log_pane logic from FileManager.
        
        Args:
            messages: List of log messages to display
            scroll_offset: Scroll position in the message list
            height_ratio: Ratio of screen height to use for log pane
        """
        from tfm_colors import get_boundary_color
        
        height, width = self.get_screen_size()
        calculated_height = int(height * height_ratio)
        log_height = calculated_height if height_ratio > 0 else 0
        
        # If log pane is hidden, don't draw anything
        if log_height == 0:
            return
        
        # Calculate positions
        footer_y = height - log_height - 2
        log_start_y = footer_y + 1
        
        # Draw horizontal separator
        try:
            separator_line = "─" * width
            self.stdscr.addstr(footer_y, 0, separator_line, get_boundary_color())
        except curses.error:
            pass
        
        # Delegate to LogManager for actual log rendering
        # Note: This requires the LogManager instance, which we don't have here
        # For now, we'll implement a simple version
        from tfm_colors import get_log_color
        
        if not messages or log_height <= 0:
            return
        
        display_height = log_height
        total_messages = len(messages)
        
        # Cap scroll offset
        max_scroll = max(0, total_messages - display_height)
        scroll_offset = min(scroll_offset, max_scroll)
        
        start_idx = max(0, total_messages - display_height - scroll_offset)
        end_idx = min(total_messages, start_idx + display_height)
        
        # Convert deque to list for slicing support
        messages_list = list(messages)
        messages_to_show = messages_list[start_idx:end_idx]
        
        for i, log_entry in enumerate(messages_to_show):
            if i >= display_height:
                break
            
            y = log_start_y + i
            if y >= log_start_y + log_height:
                break
            
            # Unpack log entry tuple (timestamp, source, message)
            timestamp, source, message = log_entry
            
            # Format log line
            log_line = f"{timestamp} [{source:>6}] {message}"
            
            # Truncate if too long
            if len(log_line) > width - 1:
                log_line = log_line[:width - 4] + "..."
            
            try:
                # Get color based on source
                color = get_log_color(source)
                self.stdscr.addstr(y, 0, log_line.ljust(width - 1)[:width - 1], color)
            except curses.error:
                pass
    
    def show_dialog(self, dialog_config: DialogConfig) -> Any:
        """
        Show a dialog and return user response.
        
        This method delegates to existing dialog classes.
        
        Args:
            dialog_config: Dialog configuration
        
        Returns:
            User response (type depends on dialog type):
            - confirmation: bool (True/False)
            - input: str or None
            - list: selected item(s) or None
            - info: None
            - progress: None (non-blocking)
        """
        # Import dialog classes
        from tfm_general_purpose_dialog import GeneralPurposeDialog, DialogHelpers
        from tfm_list_dialog import ListDialog
        from tfm_info_dialog import InfoDialog
        from tfm_config import get_config
        
        config = get_config()
        
        if dialog_config.type == 'confirmation':
            # Use GeneralPurposeDialog for confirmation
            dialog = GeneralPurposeDialog(config)
            DialogHelpers.create_confirmation_dialog(
                dialog,
                dialog_config.title,
                dialog_config.message
            )
            
            # Show dialog and get result
            result = None
            
            def on_confirm():
                nonlocal result
                result = True
            
            def on_cancel():
                nonlocal result
                result = False
            
            dialog.callback = on_confirm
            dialog.cancel_callback = on_cancel
            
            # Run dialog event loop
            while dialog.is_visible:
                dialog.draw(self.stdscr, lambda y, x, text, attr=0: self._safe_addstr(y, x, text, attr))
                self.stdscr.refresh()
                
                key = self.stdscr.getch()
                dialog.handle_key(key)
            
            return result
        
        elif dialog_config.type == 'input':
            # Use GeneralPurposeDialog for input
            dialog = GeneralPurposeDialog(config)
            DialogHelpers.create_input_dialog(
                dialog,
                dialog_config.title,
                dialog_config.message,
                dialog_config.default_value or ""
            )
            
            # Show dialog and get result
            result = None
            
            def on_confirm(text):
                nonlocal result
                result = text
            
            def on_cancel():
                nonlocal result
                result = None
            
            dialog.callback = on_confirm
            dialog.cancel_callback = on_cancel
            
            # Run dialog event loop
            while dialog.is_visible:
                dialog.draw(self.stdscr, lambda y, x, text, attr=0: self._safe_addstr(y, x, text, attr))
                self.stdscr.refresh()
                
                key = self.stdscr.getch()
                dialog.handle_key(key)
            
            return result
        
        elif dialog_config.type == 'list':
            # Use ListDialog for list selection
            dialog = ListDialog(config)
            
            # Convert choices to format expected by ListDialog
            items = [choice.get('label', str(choice)) for choice in dialog_config.choices] if dialog_config.choices else []
            
            selected_index = dialog.show(
                self.stdscr,
                items,
                dialog_config.title
            )
            
            if selected_index is not None and dialog_config.choices:
                return dialog_config.choices[selected_index]
            return None
        
        elif dialog_config.type == 'info':
            # Use InfoDialog for information display
            dialog = InfoDialog(config)
            dialog.show(
                self.stdscr,
                dialog_config.title,
                dialog_config.message
            )
            return None
        
        elif dialog_config.type == 'progress':
            # Progress dialogs are non-blocking and handled separately
            # via show_progress() method
            return None
        
        else:
            raise ValueError(f"Unknown dialog type: {dialog_config.type}")
    
    def _safe_addstr(self, y, x, text, attr=0):
        """Safely add string to screen, handling boundary conditions"""
        try:
            height, width = self.stdscr.getmaxyx()
            
            if y < 0 or y >= height or x < 0 or x >= width:
                return
            
            max_len = width - x - 1
            if max_len <= 0:
                return
            
            truncated_text = text[:max_len] if len(text) > max_len else text
            self.stdscr.addstr(y, x, truncated_text, attr)
        except curses.error:
            pass
    
    def show_progress(self, operation: str, current: int, total: int, 
                     message: str):
        """
        Show or update progress indicator for long operations.
        
        Args:
            operation: Name of the operation (e.g., 'Copying files')
            current: Current progress value
            total: Total progress value
            message: Current status message (e.g., current file name)
        """
        # Progress is typically shown in the status bar in TUI mode
        # The ProgressManager handles formatting, and we just display it
        # via render_status_bar()
        
        # For now, this is a no-op since progress is handled through
        # the status bar rendering in TUI mode
        pass
    
    def get_input_event(self, timeout: int = -1) -> Optional[InputEvent]:
        """
        Get next input event (key press, mouse click, etc.).
        
        Converts curses key codes to InputEvent objects.
        
        Args:
            timeout: Timeout in milliseconds (-1 for blocking, 0 for non-blocking)
        
        Returns:
            InputEvent if available, None if timeout or no event
        """
        try:
            # Set timeout
            if timeout >= 0:
                self.stdscr.timeout(timeout)
            else:
                self.stdscr.timeout(-1)  # Blocking
            
            # Get key
            key = self.stdscr.getch()
            
            # Check for no input (timeout)
            if key == -1:
                return None
            
            # Check for resize event
            if key == curses.KEY_RESIZE:
                return InputEvent(type='resize')
            
            # Convert to InputEvent
            return self._convert_curses_key(key)
            
        except curses.error:
            return None
    
    def _convert_curses_key(self, key: int) -> InputEvent:
        """
        Convert curses key code to InputEvent.
        
        Args:
            key: Curses key code
        
        Returns:
            InputEvent object
        """
        # Check for special keys
        key_name = None
        modifiers = set()
        
        # Map common special keys
        special_keys = {
            curses.KEY_UP: 'Up',
            curses.KEY_DOWN: 'Down',
            curses.KEY_LEFT: 'Left',
            curses.KEY_RIGHT: 'Right',
            curses.KEY_HOME: 'Home',
            curses.KEY_END: 'End',
            curses.KEY_PPAGE: 'PageUp',
            curses.KEY_NPAGE: 'PageDown',
            curses.KEY_DC: 'Delete',
            curses.KEY_BACKSPACE: 'Backspace',
            127: 'Backspace',  # Alternative backspace
            curses.KEY_ENTER: 'Enter',
            10: 'Enter',  # Line feed
            13: 'Enter',  # Carriage return
            9: 'Tab',
            27: 'Escape',
        }
        
        # Map function keys
        for i in range(1, 13):
            fkey = getattr(curses, f'KEY_F{i}', None)
            if fkey is not None:
                special_keys[fkey] = f'F{i}'
        
        if key in special_keys:
            key_name = special_keys[key]
        elif 32 <= key <= 126:
            # Printable ASCII
            key_name = chr(key)
        elif key < 32:
            # Control characters
            if key == 0:
                key_name = 'Ctrl+Space'
            else:
                # Ctrl+letter
                key_name = f'Ctrl+{chr(key + 64)}'
                modifiers.add('ctrl')
        
        return InputEvent(
            type='key',
            key=key,
            key_name=key_name,
            modifiers=modifiers
        )
    
    def refresh(self):
        """
        Refresh the display.
        
        Updates the screen to show all pending changes.
        """
        try:
            self.stdscr.refresh()
        except curses.error:
            pass  # Ignore refresh errors
    
    def set_color_scheme(self, scheme: str):
        """
        Set the color scheme.
        
        Args:
            scheme: Color scheme name (e.g., 'dark', 'light', 'custom')
        """
        from tfm_colors import init_colors
        
        # Store the scheme
        self.color_scheme = scheme
        
        # Reinitialize colors with the new scheme
        try:
            init_colors(scheme)
        except curses.error as e:
            print(f"Warning: Could not set color scheme '{scheme}': {e}")

    def _draw_pane(self, pane_data: Dict, start_x: int, pane_width: int, 
                   is_active: bool, layout: LayoutInfo):
        """
        Draw a single file pane.
        
        This is a helper method that wraps the existing draw_pane logic.
        
        Args:
            pane_data: Pane data dictionary
            start_x: Starting X position for the pane
            pane_width: Width of the pane
            is_active: Whether this pane is active
            layout: Layout information
        """
        import os
        from tfm_colors import get_file_color, get_error_color
        from tfm_wide_char_utils import safe_get_display_width, truncate_to_width, pad_to_width
        
        # Safety checks
        if pane_width < 10:
            return
        if start_x < 0 or start_x >= layout.screen_width:
            return
        
        # Check if there are no files to display
        if not pane_data['files']:
            message = "No items to show"
            message_y = layout.panes_y + layout.pane_height // 2
            message_display_width = safe_get_display_width(message)
            message_x = start_x + (pane_width - message_display_width) // 2
            
            try:
                self.stdscr.addstr(message_y, message_x, message, get_error_color())
            except curses.error:
                pass
            return
        
        # Calculate scroll offset
        if pane_data['selected_index'] < pane_data['scroll_offset']:
            pane_data['scroll_offset'] = pane_data['selected_index']
        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + layout.pane_height:
            pane_data['scroll_offset'] = pane_data['selected_index'] - layout.pane_height + 1
        
        # Draw files
        for i in range(layout.pane_height):
            file_index = i + pane_data['scroll_offset']
            y = layout.panes_y + i
            
            if file_index >= len(pane_data['files']):
                break
            
            file_path = pane_data['files'][file_index]
            display_name = file_path.name
            is_dir = file_path.is_dir()
            
            # Get file info
            from tfm_file_operations import FileOperations
            size_str, mtime_str = FileOperations.get_file_info(file_path)
            
            # Check selection states
            is_multi_selected = str(file_path) in pane_data['selected_files']
            is_selected = file_index == pane_data['selected_index']
            is_executable = file_path.is_file() and os.access(file_path, os.X_OK)
            
            # Get color
            color = get_file_color(is_dir, is_executable, is_selected, is_active)
            
            # Add standout for multi-selected files
            if is_multi_selected and not is_selected:
                base_color = get_file_color(is_dir, is_executable, False, False)
                color = base_color | curses.A_STANDOUT
            
            # Selection marker
            selection_marker = "●" if is_multi_selected else " "
            
            # Format line
            datetime_width = 16
            size_width = 8
            usable_width = pane_width - 2
            
            if pane_width < 20:
                # Too narrow - just show name
                max_name_width = max(1, pane_width - 5)
                truncated_name = truncate_to_width(display_name, max_name_width, "...")
                line = f"{selection_marker} {truncated_name}"
            elif pane_width < 60:
                # Narrow - show name and size
                name_width = usable_width - 11
                if safe_get_display_width(display_name) > name_width:
                    display_name = truncate_to_width(display_name, name_width, "...")
                padded_name = pad_to_width(display_name, name_width, align='left')
                line = f"{selection_marker} {padded_name}{size_str:>8}"
            else:
                # Wide - show name, size, and date
                name_width = usable_width - (12 + datetime_width)
                if safe_get_display_width(display_name) > name_width:
                    display_name = truncate_to_width(display_name, name_width, "...")
                padded_name = pad_to_width(display_name, name_width, align='left')
                line = f"{selection_marker} {padded_name} {size_str:>8} {mtime_str}"
            
            try:
                max_line_width = pane_width - 2
                if safe_get_display_width(line) > max_line_width:
                    line = truncate_to_width(line, max_line_width, "")
                self.stdscr.addstr(y, start_x + 1, line, color)
            except curses.error:
                pass
