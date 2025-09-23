#!/usr/bin/env python3
"""
TUI File Manager - Base List Dialog Component
Provides common functionality for list-based dialogs
"""

import curses
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color


class BaseListDialog:
    """Base class for list-based dialog components"""
    
    def __init__(self, config):
        self.config = config
        
        # Common dialog state
        self.mode = False
        self.selected = 0  # Index of currently selected item
        self.scroll = 0  # Scroll offset for the list
        self.text_editor = SingleLineTextEdit()  # Text editor for input
        
    def exit(self):
        """Exit dialog mode - to be overridden by subclasses"""
        self.mode = False
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
        
        # Calculate dialog dimensions
        dialog_width = max(min_width, int(width * width_ratio))
        dialog_height = max(min_height, int(height * height_ratio))
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                safe_addstr_func(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            safe_addstr_func(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                safe_addstr_func(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    safe_addstr_func(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            safe_addstr_func(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        if title and start_y >= 0:
            title_text = f" {title} "
            title_x = start_x + (dialog_width - len(title_text)) // 2
            if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
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
            content_width = dialog_width - 4
            if len(help_text) <= content_width:
                help_x = start_x + (dialog_width - len(help_text)) // 2
                if help_x >= start_x:
                    safe_addstr_func(y, help_x, help_text, get_status_color() | curses.A_DIM)