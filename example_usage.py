#!/usr/bin/env python3
"""
Example usage of SingleLineTextEdit class

This demonstrates how the batch rename dialog can be refactored to use
the SingleLineTextEdit class instead of manual text editing logic.
"""

import curses
from src.tfm_single_line_text_edit import SingleLineTextEdit


class BatchRenameDialogExample:
    """Example showing how to use SingleLineTextEdit in batch rename dialog"""
    
    def __init__(self):
        # Replace individual text/cursor variables with SingleLineTextEdit instances
        self.regex_editor = SingleLineTextEdit()
        self.destination_editor = SingleLineTextEdit()
        self.active_field = 'regex'  # 'regex' or 'destination'
        
    def get_active_editor(self):
        """Get the currently active text editor"""
        return self.regex_editor if self.active_field == 'regex' else self.destination_editor
        
    def handle_batch_rename_input(self, key):
        """Handle input while in batch rename mode - refactored version"""
        if key == 27:  # ESC - cancel batch rename
            print("Batch rename cancelled")
            return True
            
        elif key == 9:  # Tab - switch between regex and destination input
            if self.active_field == 'regex':
                self.active_field = 'destination'
            else:
                self.active_field = 'regex'
            return True
            
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            # Enter - perform batch rename
            regex_text = self.regex_editor.get_text()
            dest_text = self.destination_editor.get_text()
            if regex_text and dest_text:
                print(f"Would perform batch rename: '{regex_text}' -> '{dest_text}'")
            else:
                print("Please enter both regex pattern and destination pattern")
            return True
            
        elif key == curses.KEY_UP or key == curses.KEY_DOWN:
            # Handle preview scrolling (not implemented in this example)
            return True
            
        else:
            # Let the active editor handle the key
            active_editor = self.get_active_editor()
            return active_editor.handle_key(key)
    
    def draw_batch_rename_dialog(self, stdscr):
        """Draw the batch rename dialog - refactored version"""
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(80, int(width * 0.9))
        start_y = 5
        start_x = (width - dialog_width) // 2
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Draw regex input field
        regex_y = start_y + 2
        self.regex_editor.draw(
            stdscr, regex_y, content_start_x, content_width,
            "Regex Pattern: ",
            is_active=(self.active_field == 'regex')
        )
        
        # Draw destination input field
        dest_y = start_y + 3
        self.destination_editor.draw(
            stdscr, dest_y, content_start_x, content_width,
            "Destination:   ",
            is_active=(self.active_field == 'destination')
        )


def main():
    """Demo the SingleLineTextEdit functionality"""
    
    # Create a simple text editor for testing
    editor = SingleLineTextEdit("Hello World")
    
    print("SingleLineTextEdit Demo")
    print("======================")
    print(f"Initial text: '{editor.get_text()}'")
    print(f"Cursor position: {editor.get_cursor_pos()}")
    
    # Test cursor movement
    print("\nTesting cursor movement:")
    editor.move_cursor_home()
    print(f"After home: cursor at {editor.get_cursor_pos()}")
    
    editor.move_cursor_right()
    editor.move_cursor_right()
    print(f"After 2 right moves: cursor at {editor.get_cursor_pos()}")
    
    # Test text editing
    print("\nTesting text editing:")
    editor.insert_char('X')
    print(f"After inserting 'X': '{editor.get_text()}', cursor at {editor.get_cursor_pos()}")
    
    editor.backspace()
    print(f"After backspace: '{editor.get_text()}', cursor at {editor.get_cursor_pos()}")
    
    editor.move_cursor_end()
    editor.insert_char('!')
    print(f"After moving to end and adding '!': '{editor.get_text()}'")
    
    # Test delete
    editor.move_cursor_home()
    editor.delete_char_at_cursor()
    print(f"After deleting first char: '{editor.get_text()}'")
    
    print("\nDemo complete!")


if __name__ == "__main__":
    main()