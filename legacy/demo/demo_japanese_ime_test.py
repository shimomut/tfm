#!/usr/bin/env python3
"""
Demo: Japanese IME Input Test

This demo creates a simple text input field to test Japanese IME functionality.
It demonstrates:
1. IME composition text display (hiragana)
2. Candidate window positioning
3. Kanji conversion
4. Text commitment

Instructions:
1. Run this demo
2. Switch to Japanese input method (Hiragana)
3. Type romaji (e.g., "nihongo")
4. Press Space to see kanji candidates
5. Select a candidate or press Enter to commit
6. Press Escape to cancel composition
7. Press 'q' to quit

The demo will display:
- Current input text
- Composition state (if IME is active)
- Instructions
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import KeyEvent, CharEvent

class SimpleTextInput:
    """Simple text input widget for testing IME."""
    
    def __init__(self, backend):
        self.backend = backend
        self.text = ""
        self.cursor_pos = 0
        self.running = True
        
    def draw(self):
        """Draw the text input interface."""
        self.backend.clear()
        
        # Title
        title = "Japanese IME Test - Press 'q' to quit"
        self.backend.draw_text(0, 0, title, color_pair=1)
        self.backend.draw_text(1, 0, "=" * len(title), color_pair=1)
        
        # Instructions
        instructions = [
            "",
            "Instructions:",
            "1. Switch to Japanese input (Hiragana)",
            "2. Type romaji (e.g., 'nihongo')",
            "3. Press Space to see kanji candidates",
            "4. Select candidate or press Enter to commit",
            "5. Press Escape to cancel composition",
            "",
            "Current text:",
        ]
        
        row = 3
        for line in instructions:
            self.backend.draw_text(row, 0, line, color_pair=0)
            row += 1
        
        # Display current text with cursor
        text_row = row
        display_text = self.text[:self.cursor_pos] + "|" + self.text[self.cursor_pos:]
        self.backend.draw_text(text_row, 2, display_text, color_pair=2)
        
        # Update cursor position for IME
        self.backend.set_cursor_position(text_row, 2 + self.cursor_pos)
        
        self.backend.refresh()
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        """Handle keyboard events."""
        if event.char == 'q':
            self.running = False
            return True
        elif event.key == 'KEY_BACKSPACE':
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
            return True
        elif event.key == 'KEY_LEFT':
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
            return True
        elif event.key == 'KEY_RIGHT':
            if self.cursor_pos < len(self.text):
                self.cursor_pos += 1
            return True
        elif event.key == 'KEY_HOME':
            self.cursor_pos = 0
            return True
        elif event.key == 'KEY_END':
            self.cursor_pos = len(self.text)
            return True
        
        return False
    
    def handle_char_event(self, event: CharEvent) -> bool:
        """Handle character input events (including IME)."""
        # Insert character at cursor position
        self.text = self.text[:self.cursor_pos] + event.char + self.text[self.cursor_pos:]
        self.cursor_pos += 1
        return True
    
    def run(self):
        """Main event loop."""
        # Set up event callback
        class EventCallback:
            def __init__(self, widget):
                self.widget = widget
            
            def on_key_event(self, event: KeyEvent) -> bool:
                consumed = self.widget.handle_key_event(event)
                if consumed:
                    self.widget.draw()
                return consumed
            
            def on_char_event(self, event: CharEvent) -> bool:
                consumed = self.widget.handle_char_event(event)
                if consumed:
                    self.widget.draw()
                return consumed
        
        self.backend.event_callback = EventCallback(self)
        
        # Initial draw
        self.draw()
        
        # Event loop
        while self.running:
            # In callback mode, just run the event loop
            # Events will be delivered via callbacks
            self.backend.run_event_loop(timeout_ms=100)

def main():
    """Run the Japanese IME test demo."""
    print("Starting Japanese IME Test Demo...")
    print("Switch to Japanese input method and try typing!")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Japanese IME Test",
        font_name="Menlo",
        font_size=14,
        rows=20,
        cols=80
    )
    
    try:
        backend.initialize()
        
        # Initialize color pairs
        backend.init_color_pair(0, (255, 255, 255), (0, 0, 0))      # White on black
        backend.init_color_pair(1, (100, 200, 255), (0, 0, 0))      # Light blue on black
        backend.init_color_pair(2, (255, 255, 100), (0, 0, 0))      # Yellow on black
        
        # Create and run text input widget
        widget = SimpleTextInput(backend)
        widget.run()
        
    finally:
        backend.shutdown()
        print("Demo finished.")

if __name__ == '__main__':
    main()
