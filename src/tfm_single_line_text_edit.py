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

from ttk import TextAttribute, KeyCode, ModifierKey
from ttk.input_event import CharEvent, KeyEvent
from tfm_colors import get_status_color
from tfm_wide_char_utils import get_display_width, truncate_to_width, get_safe_functions


class SingleLineTextEdit:
    """A single-line text editor with cursor control and visual feedback"""
    
    def __init__(self, initial_text="", max_length=None, renderer=None):
        """
        Initialize the text editor
        
        Args:
            initial_text (str): Initial text content
            max_length (int, optional): Maximum allowed text length
            renderer: TTK Renderer instance for clipboard access (optional)
        """
        self.text = initial_text
        self.cursor_pos = len(initial_text)
        self.max_length = max_length
        self.renderer = renderer
        
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
    
    def paste_from_clipboard(self):
        """
        Paste text from system clipboard at cursor position.
        
        Only works if renderer was provided during initialization and
        clipboard is supported by the backend.
        
        Returns:
            bool: True if text was pasted, False otherwise
        """
        if not self.renderer:
            return False
        
        if not hasattr(self.renderer, 'supports_clipboard') or not self.renderer.supports_clipboard():
            return False
        
        if not hasattr(self.renderer, 'get_clipboard_text'):
            return False
        
        # Get text from clipboard
        clipboard_text = self.renderer.get_clipboard_text()
        if not clipboard_text:
            return False
        
        # Only paste the first line (single-line editor)
        # Replace newlines with spaces
        paste_text = clipboard_text.replace('\n', ' ').replace('\r', ' ')
        
        # Check max_length constraint
        if self.max_length:
            available_space = self.max_length - len(self.text)
            if available_space <= 0:
                return False
            # Truncate paste text if needed
            paste_text = paste_text[:available_space]
        
        # Insert text at cursor position
        self.text = (self.text[:self.cursor_pos] + 
                    paste_text + 
                    self.text[self.cursor_pos:])
        self.cursor_pos += len(paste_text)
        return True
        
    def handle_key(self, event, handle_vertical_nav=False):
        """
        Handle a key press and update the text/cursor accordingly
        
        Args:
            event: KeyEvent or CharEvent from TTK
            handle_vertical_nav (bool): Whether to handle Up/Down keys for cursor movement
            
        Returns:
            bool: True if the key was handled, False otherwise
        """
        if not event:
            return False
        
        # Handle CharEvent - text input
        if isinstance(event, CharEvent):
            return self.insert_char(event.char)
        
        # Handle KeyEvent - navigation and editing commands
        if isinstance(event, KeyEvent):
            # Check for Cmd+V / Ctrl+V paste (exact modifier match)
            if event.char == 'v' and event.modifiers == ModifierKey.COMMAND:
                return self.paste_from_clipboard()
            
            if event.key_code == KeyCode.LEFT:
                return self.move_cursor_left()
            elif event.key_code == KeyCode.RIGHT:
                return self.move_cursor_right()
            elif event.key_code == KeyCode.HOME:
                return self.move_cursor_home()
            elif event.key_code == KeyCode.END:
                return self.move_cursor_end()
            elif handle_vertical_nav and event.key_code == KeyCode.UP:
                # Up arrow - move to beginning of line when vertical nav is enabled
                return self.move_cursor_home()
            elif handle_vertical_nav and event.key_code == KeyCode.DOWN:
                # Down arrow - move to end of line when vertical nav is enabled
                return self.move_cursor_end()
            elif event.key_code == KeyCode.BACKSPACE:
                return self.backspace()
            elif event.key_code == KeyCode.DELETE:
                return self.delete_char_at_cursor()
        
        return False
        
    def draw(self, renderer, y, x, max_width, label="", is_active=True):
        """
        Draw the text field with cursor highlighting, supporting wide characters
        
        Args:
            renderer: TTK Renderer instance
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
            # Not enough space - return early
            return
        
        # Get color and attributes
        base_color, default_attributes = get_status_color()
        base_attributes = TextAttribute.BOLD if is_active else default_attributes
        
        # Draw the label
        self._safe_draw_text(renderer, y, x, label, base_color, base_attributes)
        
        # Handle empty text case
        if not self.text:
            if is_active:
                # Show cursor at beginning of empty field
                self._safe_draw_text(renderer, y, text_start_x, " ", base_color, 
                                   base_attributes | TextAttribute.REVERSE)
                # Set caret position at the beginning of the text field
                renderer.set_caret_position(text_start_x, y)
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
        caret_x = text_start_x  # Track caret position
        
        for i, char in enumerate(visible_text):
            char_width = get_width(char)
            
            if i == cursor_in_visible and is_active:
                # Draw cursor character with reversed colors
                self._safe_draw_text(renderer, y, current_x, char, base_color, 
                                   base_attributes | TextAttribute.REVERSE)
                # Store caret position at cursor
                caret_x = current_x
            else:
                # Draw normal character
                self._safe_draw_text(renderer, y, current_x, char, base_color, base_attributes)
            
            # Advance cursor position by character's display width
            current_x += char_width
        
        # If cursor is at the end of text and field is active, show cursor after last character
        if cursor_in_visible >= len(visible_text) and is_active:
            # Make sure we have space to draw the cursor
            if current_x < x + max_width:
                self._safe_draw_text(renderer, y, current_x, " ", base_color, 
                                   base_attributes | TextAttribute.REVERSE)
                # Store caret position at end
                caret_x = current_x
            elif len(visible_text) > 0:
                # If we're at the edge, we need to be more careful with wide characters
                # Find the last character that we can highlight as cursor
                last_char_pos = len(visible_text) - 1
                if last_char_pos >= 0:
                    last_char = visible_text[last_char_pos]
                    last_char_width = get_width(last_char)
                    last_char_x = current_x - last_char_width
                    self._safe_draw_text(renderer, y, last_char_x, last_char, base_color, 
                                       base_attributes | TextAttribute.REVERSE)
                    # Store caret position at last character
                    caret_x = last_char_x
        
        # Set caret position for IME composition text positioning
        # TTK refresh() will automatically restore this position
        if is_active:
            renderer.set_caret_position(caret_x, y)
    
    def _safe_draw_text(self, renderer, y, x, text, color_pair, attributes):
        """Safely draw text to screen, handling boundary conditions and wide characters"""
        try:
            height, width = renderer.get_dimensions()
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
                
                renderer.draw_text(y, x, text, color_pair=color_pair, attributes=attributes)
        except Exception:
            # Ignore rendering errors (e.g., writing to bottom-right corner)
            pass