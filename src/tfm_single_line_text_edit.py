#!/usr/bin/env python3
"""
Single line text editor component for TFM (Terminal File Manager)

This module provides a reusable SingleLineTextEdit class that handles:
- Text input and editing
- Cursor positioning and movement
- Text rendering with cursor highlighting
- Common editing operations (insert, delete, backspace)
- Navigation (home, end, left, right)
"""

import curses
from tfm_colors import get_status_color


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
        """Move cursor one position to the left"""
        if self.cursor_pos > 0:
            self.cursor_pos -= 1
            return True
        return False
        
    def move_cursor_right(self):
        """Move cursor one position to the right"""
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
        Insert a character at the cursor position
        
        Args:
            char (str): Character to insert
            
        Returns:
            bool: True if character was inserted, False if max_length exceeded
        """
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
        elif 32 <= key <= 126:  # Printable characters
            return self.insert_char(chr(key))
        
        return False
        
    def draw(self, stdscr, y, x, max_width, label="", is_active=True):
        """
        Draw the text field with cursor highlighting
        
        Args:
            stdscr: The curses screen object
            y (int): Y coordinate to draw at
            x (int): X coordinate to draw at
            max_width (int): Maximum width for the entire field
            label (str): Optional label to display before the text
            is_active (bool): Whether to show the cursor
        """
        # Calculate available space for text after label
        text_start_x = x + len(label)
        text_max_width = max_width - len(label)
        
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
        
        # Calculate visible text window if text is too long
        visible_start = 0
        visible_end = len(self.text)
        
        if len(self.text) > text_max_width:
            # Adjust visible window to keep cursor in view
            # Reserve space for cursor if it's at the end of text
            effective_max_width = text_max_width
            if cursor_pos == len(self.text) and text_max_width > 1:
                effective_max_width = text_max_width - 1  # Reserve space for end cursor
            
            if cursor_pos < effective_max_width // 2:
                # Cursor near start, show from beginning
                visible_end = effective_max_width
            elif cursor_pos >= len(self.text) - effective_max_width // 2:
                # Cursor near end, show end portion
                visible_start = max(0, len(self.text) - effective_max_width)
            else:
                # Cursor in middle, center the view
                visible_start = cursor_pos - effective_max_width // 2
                visible_end = visible_start + effective_max_width
        
        visible_text = self.text[visible_start:visible_end]
        cursor_in_visible = cursor_pos - visible_start
        
        # Draw text with cursor highlighting
        current_x = text_start_x
        
        for i, char in enumerate(visible_text):
            if i == cursor_in_visible and is_active:
                # Draw cursor character with reversed colors
                self._safe_addstr(stdscr, y, current_x, char, base_color | curses.A_REVERSE)
            else:
                # Draw normal character
                self._safe_addstr(stdscr, y, current_x, char, base_color)
            current_x += 1
        
        # If cursor is at the end of text and field is active, show cursor after last character
        if cursor_in_visible >= len(visible_text) and is_active:
            # Make sure we have space to draw the cursor
            if current_x < x + max_width:
                self._safe_addstr(stdscr, y, current_x, " ", base_color | curses.A_REVERSE)
            elif len(visible_text) > 0 and current_x == x + max_width:
                # If we're at the edge, replace the last character with cursor
                last_char_x = current_x - 1
                last_char = visible_text[-1] if visible_text else " "
                self._safe_addstr(stdscr, y, last_char_x, last_char, base_color | curses.A_REVERSE)
    
    def _safe_addstr(self, stdscr, y, x, text, attr=0):
        """Safely add string to screen, handling boundary conditions"""
        try:
            height, width = stdscr.getmaxyx()
            if 0 <= y < height and 0 <= x < width:
                # Truncate text if it would go beyond screen width
                max_len = width - x
                if len(text) > max_len:
                    text = text[:max_len]
                stdscr.addstr(y, x, text, attr)
        except curses.error:
            # Ignore curses errors (e.g., writing to bottom-right corner)
            pass