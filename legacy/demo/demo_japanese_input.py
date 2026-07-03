#!/usr/bin/env python3
"""
Demo: Japanese Character Input

This demo shows that Japanese characters (and other multi-byte UTF-8 characters)
are properly handled in text input fields. When you type Japanese characters,
they should appear correctly without generating spurious KeyEvents.

Instructions:
1. Run this demo
2. Type some Japanese characters (e.g., あいうえお)
3. The characters should appear correctly in the input field
4. Press Escape to exit

Expected behavior:
- Japanese characters generate CharEvent (not KeyEvent)
- Each multi-byte character generates exactly one CharEvent
- No KeyEvents are generated for UTF-8 continuation bytes
"""

import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk.backends.curses_backend import CursesBackend
from ttk.input_event import KeyEvent, CharEvent, KeyCode, SystemEvent
from ttk.renderer import EventCallback
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_colors import COLOR_REGULAR_FILE, COLOR_SELECTED


class JapaneseInputDemo(EventCallback):
    """Demo application for Japanese character input."""
    
    def __init__(self, renderer):
        self.renderer = renderer
        self.text_edit = SingleLineTextEdit(max_length=100)
        self.text_edit.set_text("")
        self.running = True
        self.event_log = []
        self.max_log_entries = 10
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle KeyEvent."""
        # Log the event
        self.event_log.append(f"KeyEvent: key_code={event.key_code}, char={repr(event.char)}")
        if len(self.event_log) > self.max_log_entries:
            self.event_log.pop(0)
        
        # Handle Escape to quit
        if event.key_code == KeyCode.ESCAPE:
            self.running = False
            return True
        
        # Pass to text edit
        return self.text_edit.handle_key(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        """Handle CharEvent."""
        # Log the event
        self.event_log.append(f"CharEvent: char={repr(event.char)}")
        if len(self.event_log) > self.max_log_entries:
            self.event_log.pop(0)
        
        # Pass to text edit
        return self.text_edit.handle_key(event)
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """Handle SystemEvent."""
        return False
    
    def draw(self):
        """Draw the demo interface."""
        self.renderer.clear()
        height, width = self.renderer.get_dimensions()
        
        # Draw title
        title = "Japanese Character Input Demo"
        self.renderer.draw_text(0, (width - len(title)) // 2, title, 
                               COLOR_SELECTED, 0)
        
        # Draw instructions
        instructions = [
            "Type Japanese characters (e.g., あいうえお)",
            "Each multi-byte character should generate one CharEvent",
            "Press Escape to exit"
        ]
        for i, line in enumerate(instructions):
            self.renderer.draw_text(2 + i, 2, line, COLOR_REGULAR_FILE, 0)
        
        # Draw text input field
        input_y = 6
        label = "Input: "
        self.renderer.draw_text(input_y, 2, label, COLOR_REGULAR_FILE, 0)
        self.text_edit.draw(self.renderer, 2 + len(label), input_y, width - 4 - len(label))
        
        # Draw event log
        log_y = 8
        self.renderer.draw_text(log_y, 2, "Event Log (last 10 events):", 
                               COLOR_REGULAR_FILE, 0)
        for i, log_entry in enumerate(self.event_log[-10:]):
            self.renderer.draw_text(log_y + 1 + i, 4, log_entry, 
                                   COLOR_REGULAR_FILE, 0)
        
        # Draw current text value
        value_y = height - 3
        self.renderer.draw_text(value_y, 2, f"Current text: {repr(self.text_edit.get_text())}", 
                               COLOR_REGULAR_FILE, 0)
        
        self.renderer.refresh()
    
    def run(self):
        """Run the demo."""
        # Set up callback
        self.renderer.set_event_callback(self)
        
        # Initial draw
        self.draw()
        
        # Event loop
        while self.running:
            # Process events (this will call our callbacks)
            self.renderer.run_event_loop_iteration(timeout_ms=16)
            
            # Redraw
            self.draw()


def main():
    """Main entry point."""
    backend = CursesBackend()
    
    try:
        backend.initialize()
        
        demo = JapaneseInputDemo(backend)
        demo.run()
        
    finally:
        backend.shutdown()


if __name__ == '__main__':
    main()
