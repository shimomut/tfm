#!/usr/bin/env python3
"""
Demo: Word-level navigation and deletion in SingleLineTextEdit

This demo showcases the new word-level editing features:
- Alt+Left: Move cursor to previous word
- Alt+Right: Move cursor to next word
- Alt+Backspace: Delete previous word

Instructions:
- Type some text with multiple words
- Use Alt+Left/Right to jump between words
- Use Alt+Backspace to delete words quickly
- Press Escape to exit
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import TtkApplication, TextAttribute, KeyCode, ModifierKey
from ttk.input_event import CharEvent, KeyEvent
from src.tfm_single_line_text_edit import SingleLineTextEdit


class WordNavigationDemo(TtkApplication):
    """Demo application for word-level navigation"""
    
    def __init__(self):
        super().__init__()
        self.editor = SingleLineTextEdit(
            "hello-world/path/to/file.txt key=value [test]",
            renderer=self.renderer
        )
        self.status_message = "Use Alt+Left/Right for word navigation, Alt+Backspace to delete words"
        
    def on_key(self, event):
        """Handle keyboard input"""
        if isinstance(event, KeyEvent):
            # Exit on Escape
            if event.key_code == KeyCode.ESCAPE:
                self.quit()
                return True
            
            # Handle editor keys
            if self.editor.handle_key(event):
                self.redraw()
                return True
        
        elif isinstance(event, CharEvent):
            # Handle character input
            if self.editor.handle_key(event):
                self.redraw()
                return True
        
        return False
    
    def draw(self):
        """Draw the demo interface"""
        height, width = self.renderer.get_dimensions()
        
        # Clear screen
        self.renderer.clear()
        
        # Draw title
        title = "Word-Level Navigation Demo"
        self.renderer.draw_text(0, (width - len(title)) // 2, title,
                              attributes=TextAttribute.BOLD)
        
        # Draw instructions
        instructions = [
            "",
            "Keyboard shortcuts:",
            "  Alt+Left       - Move to previous word",
            "  Alt+Right      - Move to next word", 
            "  Alt+Backspace  - Delete previous word",
            "  Left/Right     - Move by character",
            "  Backspace      - Delete character",
            "  Escape         - Exit",
            "",
            "Word boundaries:",
            "  - Alphanumeric characters and underscores are word characters",
            "  - Punctuation (- / = [ ] . etc.) separates words",
            "  - Try navigating through the example text below!",
            "",
            "Try it out:",
        ]
        
        y = 2
        for line in instructions:
            self.renderer.draw_text(y, 2, line)
            y += 1
        
        # Draw the text editor
        editor_y = y + 1
        self.editor.draw(self.renderer, editor_y, 2, width - 4, 
                        label="Text: ", is_active=True)
        
        # Draw cursor position info
        info_y = editor_y + 2
        cursor_info = f"Cursor position: {self.editor.get_cursor_pos()}"
        self.renderer.draw_text(info_y, 2, cursor_info)
        
        # Draw status message
        status_y = height - 2
        self.renderer.draw_text(status_y, 2, self.status_message,
                              attributes=TextAttribute.DIM)
        
        # Refresh the screen
        self.renderer.refresh()


def main():
    """Run the demo"""
    app = WordNavigationDemo()
    app.run()


if __name__ == "__main__":
    main()
