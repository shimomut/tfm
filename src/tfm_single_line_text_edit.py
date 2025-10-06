#!/usr/bin/env python3
"""
Single line text editor component for TFM (Terminal File Manager)

This module provides a reusable SingleLineTextEdit class that handles:
- Text input and editing
- Cursor positioning and movement
- Text rendering with cursor highlighting
- Common editing operations (insert, delete, backspace)
- Navigation (home, end, left, right)
- Wide character support for proper display and editing
"""

import curses
from tfm_colors import get_status_color
from tfm_wide_char_utils import get_display_width, truncate_to_width, get_safe_functions


class SingleLineTextEdit:
    """A single-line text editor with cursor control and visual feedback"""
    
    def __init__(self, initial_text="", max_length=None):
        """
        Initialize the text editor
        
        Args:
            initial_text (str): Initial text content
            max_length (int, optional): Maximum allowed text length
        """
        self.text = initial_text
        self.cursor_pos = len(initial_text)
        self.max_length = max_length
        
    def get_text(self):
        """Get the current text content"""
        return self.text
        
    def set_text(self, text):
        """Set the text content and adjust cursor if needed"""
        self.text = text
        self.cursor_pos = min(self.cursor_pos, len(self.text))
        
    def get_cursor_pos(self):
        """Get the current cursor position"""
        return self.cursor_pos
        
    def set_cursor_pos(self, pos):
        """Set the cursor position, ensuring it's within bounds"""
        self.cursor_pos = max(0, min(pos, len(self.text)))
        
    def clear(self):
        """Clear all text and reset cursor"""
        self.text = ""
        self.cursor_pos = 0
        
    def move_cursor_left(self):
        """Move cursor one character position to the left (handles wide characters properly)"""
        if self.cursor_pos > 0:
            self.cursor_pos -= 1
            return True
        return False
        
    def move_cursor_right(self):
        """Move cursor one character position to the right (handles wide characters properly)"""
        if self.cursor_pos < len(self.text):
            self.cursor_pos += 1
            return True
        return False
        
    def move_cursor_home(self):
        """Move cursor to the beginning of the text"""
        if self.cursor_pos > 0:
            self.cursor_pos = 0
            return True
        return False
        
    def move_cursor_end(self):
        """Move cursor to the end of the text"""
        if self.cursor_pos < len(self.text):
            self.cursor_pos = len(self.text)
            return True
        return False
        
    def insert_char(self, char):
        """
        Insert a character at the cursor position, handling wide characters
        
        Args:
            char (str): Character to insert
            
        Returns:
            bool: True if character was inserted, False if max_length exceeded
        """
        # Check max_length constraint (by character count, not display width)
        if self.max_length and len(self.text) >= self.max_length:
            return False
            
        self.text = (self.text[:self.cursor_pos] + 
                    char + 
                    self.text[self.cursor_pos:])
        self.cursor_pos += 1
        return True
        
    def delete_char_at_cursor(self):
        """
        Delete the character at the cursor position
        
        Returns:
            bool: True if character was deleted, False if nothing to delete
        """
        if self.cursor_pos < len(self.text):
            self.text = (self.text[:self.cursor_pos] + 
                        self.text[self.cursor_pos + 1:])
            return True
        return False
        
    def backspace(self):
        """
        Delete the character before the cursor position
        
        Returns:
            bool: True if character was deleted, False if nothing to delete
        """
        if self.cursor_pos > 0:
            self.text = (self.text[:self.cursor_pos - 1] + 
                        self.text[self.cursor_pos:])
            self.cursor_pos -= 1
            return True
        return False
        
    def handle_key(self, key, handle_vertical_nav=False):
        """
        Handle a key press and update the text/cursor accordingly
        
        Args:
            key (int): The key code from curses
            handle_vertical_nav (bool): Whether to handle Up/Down keys for cursor movement
            
        Returns:
            bool: True if the key was handled, False otherwise
        """
        # Handle cursor movement keys (use both curses constants and common numeric values)
        if key == 260 or (hasattr(curses, 'KEY_LEFT') and key == curses.KEY_LEFT):
            return self.move_cursor_left()
        elif key == 261 or (hasattr(curses, 'KEY_RIGHT') and key == curses.KEY_RIGHT):
            return self.move_cursor_right()
        elif key == 262 or (hasattr(curses, 'KEY_HOME') and key == curses.KEY_HOME):
            return self.move_cursor_home()
        elif key == 269 or (hasattr(curses, 'KEY_END') and key == curses.KEY_END):
            return self.move_cursor_end()
        elif handle_vertical_nav and (key == 259 or (hasattr(curses, 'KEY_UP') and key == curses.KEY_UP)):
            # Up arrow - move to beginning of line when vertical nav is enabled
            return self.move_cursor_home()
        elif handle_vertical_nav and (key == 258 or (hasattr(curses, 'KEY_DOWN') and key == curses.KEY_DOWN)):
            # Down arrow - move to end of line when vertical nav is enabled
            return self.move_cursor_end()
        elif (key == 263 or key == 127 or key == 8 or 
              (hasattr(curses, 'KEY_BACKSPACE') and key == curses.KEY_BACKSPACE)):
            return self.backspace()
        elif key == 330 or (hasattr(curses, 'KEY_DC') and key == curses.KEY_DC):  # Delete key
            return self.delete_char_at_cursor()
        elif 32 <= key <= 126:  # ASCII printable characters
            return self.insert_char(chr(key))
        elif key > 126:  # Extended characters (including wide characters)
            try:
                # Handle Unicode characters beyond ASCII range
                char = chr(key)
                return self.insert_char(char)
            except (ValueError, OverflowError):
                # Invalid character code
                return False
        
        return False
        
    def draw(self, stdscr, y, x, max_width, label="", is_active=True):
        """
        Draw the text field with cursor highlighting, supporting wide characters
        
        Args:
            stdscr: The curses screen object
            y (int): Y coordinate to draw at
            x (int): X coordinate to draw at
            max_width (int): Maximum width for the entire field
            label (str): Optional label to display before the text
            is_active (bool): Whether to show the cursor
        """
        # Get safe wide character functions for current terminal
        safe_funcs = get_safe_functions()
        get_width = safe_funcs['get_display_width']
        truncate_text = safe_funcs['truncate_to_width']
        
        # Calculate available space for text after label using display width
        label_width = get_width(label)
        text_start_x = x + label_width
        text_max_width = max_width - label_width
        
        if text_max_width <= 0:
            return
        
        # Draw the label
        base_color = get_status_color() | (curses.A_BOLD if is_active else 0)
        self._safe_addstr(stdscr, y, x, label, base_color)
        
        # Handle empty text case
        if not self.text:
            if is_active:
                # Show cursor at beginning of empty field
                self._safe_addstr(stdscr, y, text_start_x, " ", base_color | curses.A_REVERSE)
            return
        
        # Ensure cursor is within bounds
        cursor_pos = max(0, min(self.cursor_pos, len(self.text)))
        
        # Calculate display width of entire text
        text_display_width = get_width(self.text)
        
        # Calculate visible text window if text is too wide
        visible_start = 0
        visible_end = len(self.text)
        
        if text_display_width > text_max_width:
            # Need to scroll text to keep cursor visible
            # Calculate display position of cursor
            cursor_display_pos = get_width(self.text[:cursor_pos])
            
            # Reserve space for cursor if it's at the end of text
            effective_max_width = text_max_width
            if cursor_pos == len(self.text) and text_max_width > 1:
                effective_max_width = text_max_width - 1  # Reserve space for end cursor
            
            if cursor_display_pos < effective_max_width // 2:
                # Cursor near start, show from beginning
                visible_text = truncate_text(self.text, effective_max_width, "")
                visible_end = len(visible_text)
            elif cursor_display_pos >= text_display_width - effective_max_width // 2:
                # Cursor near end, show end portion
                # Find starting position that gives us the right width
                target_width = effective_max_width
                temp_start = 0
                for i in range(len(self.text)):
                    remaining_text = self.text[i:]
                    if get_width(remaining_text) <= target_width:
                        temp_start = i
                        break
                visible_start = temp_start
            else:
                # Cursor in middle, center the view around cursor
                # Find a good starting position that centers the cursor
                half_width = effective_max_width // 2
                
                # Start from cursor and work backwards to find start position
                temp_start = cursor_pos
                accumulated_width = 0
                for i in range(cursor_pos - 1, -1, -1):
                    char_width = get_width(self.text[i])
                    if accumulated_width + char_width > half_width:
                        break
                    accumulated_width += char_width
                    temp_start = i
                
                visible_start = temp_start
                # Truncate from this position
                remaining_text = self.text[visible_start:]
                visible_text = truncate_text(remaining_text, effective_max_width, "")
                visible_end = visible_start + len(visible_text)
        
        visible_text = self.text[visible_start:visible_end]
        cursor_in_visible = cursor_pos - visible_start
        
        # Draw text with cursor highlighting, accounting for wide characters
        current_x = text_start_x
        
        for i, char in enumerate(visible_text):
            char_width = get_width(char)
            
            if i == cursor_in_visible and is_active:
                # Draw cursor character with reversed colors
                self._safe_addstr(stdscr, y, current_x, char, base_color | curses.A_REVERSE)
            else:
                # Draw normal character
                self._safe_addstr(stdscr, y, current_x, char, base_color)
            
            # Advance cursor position by character's display width
            current_x += char_width
        
        # If cursor is at the end of text and field is active, show cursor after last character
        if cursor_in_visible >= len(visible_text) and is_active:
            # Make sure we have space to draw the cursor
            if current_x < x + max_width:
                self._safe_addstr(stdscr, y, current_x, " ", base_color | curses.A_REVERSE)
            elif len(visible_text) > 0:
                # If we're at the edge, we need to be more careful with wide characters
                # Find the last character that we can highlight as cursor
                last_char_pos = len(visible_text) - 1
                if last_char_pos >= 0:
                    last_char = visible_text[last_char_pos]
                    last_char_width = get_width(last_char)
                    last_char_x = current_x - last_char_width
                    self._safe_addstr(stdscr, y, last_char_x, last_char, base_color | curses.A_REVERSE)
    
    def _safe_addstr(self, stdscr, y, x, text, attr=0):
        """Safely add string to screen, handling boundary conditions and wide characters"""
        try:
            height, width = stdscr.getmaxyx()
            if 0 <= y < height and 0 <= x < width:
                # Get safe wide character functions
                safe_funcs = get_safe_functions()
                get_width = safe_funcs['get_display_width']
                truncate_text = safe_funcs['truncate_to_width']
                
                # Calculate available display width
                max_display_width = width - x
                
                # Truncate text if it would go beyond screen width (by display width)
                if get_width(text) > max_display_width:
                    text = truncate_text(text, max_display_width, "")
                
                stdscr.addstr(y, x, text, attr)
        except curses.error:
            # Ignore curses errors (e.g., writing to bottom-right corner)
            pass