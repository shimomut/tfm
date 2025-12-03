#!/usr/bin/env python3
"""
TUI File Manager - Base List Dialog Component
Provides common functionality for list-based dialogs
"""

import curses
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color
from tfm_wide_char_utils import get_display_width, get_safe_functions


class BaseListDialog:
    """Base class for list-based dialog components"""
    
    def __init__(self, config):
        self.config = config
        
        # Common dialog state
        self.is_active = False
        self.selected = 0  # Index of currently selected item
        self.scroll = 0  # Scroll offset for the list
        self.text_editor = SingleLineTextEdit()  # Text editor for input
        
    def exit(self):
        """Exit dialog mode - to be overridden by subclasses"""
        self.is_active = False
        self.selected = 0
        self.scroll = 0
        self.text_editor.clear()
        
    def handle_common_navigation(self, key, items_list):
        """Handle common navigation keys for list dialogs
        
        Args:
            key: The input key
            items_list: List of items to navigate through
            
        Returns:
            True if key was handled, False otherwise
        """
        if key == 27:  # ESC - cancel
            return 'cancel'
        elif key == curses.KEY_UP:
            # Move selection up
            if items_list and self.selected > 0:
                self.selected -= 1
                self._adjust_scroll(len(items_list))
            return True
        elif key == curses.KEY_DOWN:
            # Move selection down
            if items_list and self.selected < len(items_list) - 1:
                self.selected += 1
                self._adjust_scroll(len(items_list))
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            if items_list:
                self.selected = max(0, self.selected - 10)
                self._adjust_scroll(len(items_list))
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            if items_list:
                self.selected = min(len(items_list) - 1, self.selected + 10)
                self._adjust_scroll(len(items_list))
            return True
        elif key == curses.KEY_HOME:  # Home
            # If there's text in editor, let editor handle it for cursor movement
            if self.text_editor.text:
                if self.text_editor.handle_key(key):
                    return True
            else:
                # If no text, use for list navigation
                if items_list:
                    self.selected = 0
                    self.scroll = 0
            return True
        elif key == curses.KEY_END:  # End
            # If there's text in editor, let editor handle it for cursor movement
            if self.text_editor.text:
                if self.text_editor.handle_key(key):
                    return True
            else:
                # If no text, use for list navigation
                if items_list:
                    self.selected = len(items_list) - 1
                    self._adjust_scroll(len(items_list))
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            return 'select'
        elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
            # Let the editor handle cursor movement keys
            if self.text_editor.handle_key(key):
                return 'text_changed'
            return True
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Let the editor handle backspace
            if self.text_editor.handle_key(key):
                return 'text_changed'
            return True
        elif isinstance(key, int) and 32 <= key <= 126:  # Printable characters
            # Let the editor handle printable characters
            if self.text_editor.handle_key(key):
                return 'text_changed'
            return True
        return False
        
    def _adjust_scroll(self, total_items, content_height=None):
        """Adjust scroll offset to keep selected item visible
        
        Args:
            total_items: Total number of items in the list
            content_height: Height of the content area (calculated if None)
        """
        if content_height is None:
            # Use default dialog dimensions for scroll calculation
            height_ratio = getattr(self.config, 'LIST_DIALOG_HEIGHT_RATIO', 0.7)
            min_height = getattr(self.config, 'LIST_DIALOG_MIN_HEIGHT', 15)
            screen_height = 24  # Default terminal height
            
            # Handle case where config values might be Mock objects in tests
            try:
                dialog_height = max(min_height, int(screen_height * height_ratio))
            except (TypeError, ValueError):
                dialog_height = 15  # Fallback for tests
            content_height = dialog_height - 6  # Account for title, input, borders, help
        
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + content_height:
            self.scroll = self.selected - content_height + 1
            
    def draw_dialog_frame(self, stdscr, safe_addstr_func, title, width_ratio=0.6, height_ratio=0.7, min_width=40, min_height=15):
        """Draw the basic dialog frame and return dimensions
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Safe string drawing function
            title: Dialog title text
            width_ratio: Dialog width as ratio of screen width
            height_ratio: Dialog height as ratio of screen height
            min_width: Minimum dialog width
            min_height: Minimum dialog height
            
        Returns:
            Tuple of (start_y, start_x, dialog_width, dialog_height)
        """
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions safely for narrow terminals
        desired_width = int(width * width_ratio)
        desired_height = int(height * height_ratio)
        
        # Apply minimum constraints, but never exceed terminal size
        dialog_width = max(min_width, desired_width)
        dialog_width = min(dialog_width, width)  # Never exceed terminal width
        
        dialog_height = max(min_height, desired_height)
        dialog_height = min(dialog_height, height)  # Never exceed terminal height
        
        # Calculate safe centering
        start_y = max(0, (height - dialog_height) // 2)
        start_x = max(0, (width - dialog_width) // 2)
        
        # Draw dialog background
        # When there are wide characters in the underlying content, we need to
        # ensure the background properly clears them. Use hline() which is more
        # reliable for clearing areas than addstr() with spaces.
        for y in range(start_y, start_y + dialog_height):
            if y < height and y >= 0 and start_x >= 0 and start_x < width:
                # Calculate the number of columns to fill
                columns_to_fill = min(dialog_width, width - start_x)
                
                try:
                    # Use hline() to draw a horizontal line of spaces
                    # This is more reliable than addstr() for clearing wide characters
                    stdscr.hline(y, start_x, ' ', columns_to_fill, get_status_color())
                except curses.error:
                    # Fallback to addstr if hline fails
                    try:
                        bg_line = " " * columns_to_fill
                        safe_addstr_func(y, start_x, bg_line, get_status_color())
                    except curses.error:
                        pass
        
        # Draw border with safe drawing
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0 and start_y < height:
            top_line = "┌" + "─" * max(0, dialog_width - 2) + "┐"
            # Truncate if line would exceed terminal width
            if start_x + len(top_line) > width:
                top_line = top_line[:width - start_x]
            if top_line:
                safe_addstr_func(start_y, start_x, top_line, border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height and y >= 0:
                # Left border
                if start_x >= 0 and start_x < width:
                    safe_addstr_func(y, start_x, "│", border_color)
                # Right border
                right_x = start_x + dialog_width - 1
                if right_x >= 0 and right_x < width:
                    safe_addstr_func(y, right_x, "│", border_color)
        
        # Bottom border
        bottom_y = start_y + dialog_height - 1
        if bottom_y >= 0 and bottom_y < height:
            bottom_line = "└" + "─" * max(0, dialog_width - 2) + "┘"
            # Truncate if line would exceed terminal width
            if start_x + len(bottom_line) > width:
                bottom_line = bottom_line[:width - start_x]
            if bottom_line:
                safe_addstr_func(bottom_y, start_x, bottom_line, border_color)
        
        # Draw title using wide character utilities with safe positioning
        if title and start_y >= 0 and start_y < height:
            title_text = f" {title} "
            # Get safe wide character functions
            safe_funcs = get_safe_functions()
            get_width = safe_funcs['get_display_width']
            truncate_text = safe_funcs['truncate_to_width']
            
            title_width = get_width(title_text)
            
            # Truncate title if it's too wide for the dialog
            if title_width > dialog_width:
                title_text = truncate_text(title_text, dialog_width - 2, "...")
                title_width = get_width(title_text)
            
            title_x = start_x + (dialog_width - title_width) // 2
            # Ensure title fits within terminal bounds
            if title_x >= 0 and title_x < width and title_x + title_width <= width:
                safe_addstr_func(start_y, title_x, title_text, border_color)
        
        return start_y, start_x, dialog_width, dialog_height
        
    def draw_text_input(self, stdscr, safe_addstr_func, y, start_x, dialog_width, prompt, is_active=True):
        """Draw text input field using the text editor
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Safe string drawing function
            y: Y position to draw at
            start_x: X position of dialog start
            dialog_width: Width of the dialog
            prompt: Prompt text to display
            is_active: Whether the input is active
        """
        if y < stdscr.getmaxyx()[0]:
            max_input_width = dialog_width - 4  # Leave some margin
            self.text_editor.draw(
                stdscr, y, start_x + 2, max_input_width,
                prompt,
                is_active=is_active
            )
            
    def draw_separator(self, stdscr, safe_addstr_func, y, start_x, dialog_width):
        """Draw a horizontal separator line
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Safe string drawing function
            y: Y position to draw at
            start_x: X position of dialog start
            dialog_width: Width of the dialog
        """
        if y < stdscr.getmaxyx()[0]:
            border_color = get_status_color() | curses.A_BOLD
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            safe_addstr_func(y, start_x, sep_line[:dialog_width], border_color)
            
    def draw_list_items(self, stdscr, safe_addstr_func, items_list, start_y, end_y, start_x, content_width, format_item_func=None):
        """Draw list items with selection highlighting
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Safe string drawing function
            items_list: List of items to display
            start_y: Starting Y position for list
            end_y: Ending Y position for list
            start_x: X position for content
            content_width: Width available for content
            format_item_func: Optional function to format items (item) -> str
        """
        height = stdscr.getmaxyx()[0]
        content_height = end_y - start_y + 1
        
        # Update scroll with actual content height
        self._adjust_scroll(len(items_list), content_height)
        
        # Draw visible items
        visible_items = items_list[self.scroll:self.scroll + content_height]
        
        for i, item in enumerate(visible_items):
            y = start_y + i
            if y <= end_y and y < height:
                item_index = self.scroll + i
                is_selected = item_index == self.selected
                
                # Format item text
                if format_item_func:
                    item_text = format_item_func(item)
                else:
                    item_text = str(item)
                
                # Get safe wide character functions
                safe_funcs = get_safe_functions()
                get_width = safe_funcs['get_display_width']
                truncate_text = safe_funcs['truncate_to_width']
                
                # Truncate item text if too wide, accounting for selection indicator
                available_width = content_width - 2  # Account for selection indicator
                if get_width(item_text) > available_width:
                    item_text = truncate_text(item_text, available_width, "...")
                
                # Add selection indicator
                if is_selected:
                    display_text = f"► {item_text}"
                    item_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                else:
                    display_text = f"  {item_text}"
                    item_color = get_status_color()
                
                # Ensure text fits using display width
                if get_width(display_text) > content_width:
                    display_text = truncate_text(display_text, content_width, "")
                safe_addstr_func(y, start_x, display_text, item_color)
                
    def draw_scrollbar(self, stdscr, safe_addstr_func, items_list, start_y, content_height, scrollbar_x):
        """Draw scrollbar if needed
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Safe string drawing function
            items_list: List of items
            start_y: Starting Y position for scrollbar
            content_height: Height of content area
            scrollbar_x: X position for scrollbar
        """
        height = stdscr.getmaxyx()[0]
        
        if len(items_list) > content_height:
            # Calculate scroll thumb position
            total_items = len(items_list)
            if total_items > 0:
                thumb_pos = int((self.scroll / max(1, total_items - content_height)) * (content_height - 1))
                thumb_pos = max(0, min(content_height - 1, thumb_pos))
                
                border_color = get_status_color() | curses.A_BOLD
                for i in range(content_height):
                    y = start_y + i
                    if y < height:
                        if i == thumb_pos:
                            safe_addstr_func(y, scrollbar_x, "█", border_color)
                        else:
                            safe_addstr_func(y, scrollbar_x, "░", get_status_color() | curses.A_DIM)
                            
    def draw_help_text(self, stdscr, safe_addstr_func, help_text, y, start_x, dialog_width):
        """Draw help text at the bottom of the dialog
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Safe string drawing function
            help_text: Help text to display
            y: Y position to draw at
            start_x: X position of dialog start
            dialog_width: Width of the dialog
        """
        height = stdscr.getmaxyx()[0]
        
        if y < height:
            # Get safe wide character functions
            safe_funcs = get_safe_functions()
            get_width = safe_funcs['get_display_width']
            truncate_text = safe_funcs['truncate_to_width']
            
            content_width = dialog_width - 4
            help_width = get_width(help_text)
            
            if help_width <= content_width:
                help_x = start_x + (dialog_width - help_width) // 2
                if help_x >= start_x:
                    safe_addstr_func(y, help_x, help_text, get_status_color() | curses.A_DIM)
            else:
                # Truncate help text if too wide
                truncated_help = truncate_text(help_text, content_width, "...")
                help_width = get_width(truncated_help)
                help_x = start_x + (dialog_width - help_width) // 2
                if help_x >= start_x:
                    safe_addstr_func(y, help_x, truncated_help, get_status_color() | curses.A_DIM)