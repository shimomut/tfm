#!/usr/bin/env python3
"""
Demo: Log Line Wrapping

This demo shows how log lines automatically wrap when they don't fit
within the terminal width, making long messages readable without truncation.

Features demonstrated:
- Automatic line wrapping for long log messages
- Scrolling works correctly with wrapped lines
- Scrollbar reflects total wrapped lines, not just message count
- Color and formatting preserved across wrapped lines

Run with: PYTHONPATH=.:src:ttk python3 demo/demo_log_line_wrapping.py
"""

import sys
import os
import time

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from ttk import TtkApplication, TtkWindow
from tfm_log_manager import LogManager, getLogger
from tfm_config import get_config


class LogWrappingDemo(TtkWindow):
    """Demo window showing log line wrapping"""
    
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        
        # Create log manager
        config = get_config()
        self.log_manager = LogManager(config, is_desktop_mode=False)
        
        # Get logger
        self.logger = getLogger("Demo")
        
        # Add demo messages
        self.add_demo_messages()
        
        # Instructions
        self.instructions = [
            "Log Line Wrapping Demo",
            "",
            "Long log messages automatically wrap to fit the terminal width.",
            "Try resizing the terminal to see wrapping adjust dynamically.",
            "",
            "Controls:",
            "  ↑/↓  - Scroll log",
            "  q    - Quit",
            "",
            "Notice how:",
            "- Long messages wrap across multiple lines",
            "- Colors are preserved on wrapped lines",
            "- Scrollbar shows total wrapped lines",
            "- Scrolling works smoothly with wrapped content",
        ]
    
    def add_demo_messages(self):
        """Add various demo messages to show wrapping"""
        # Short message
        self.logger.info("Short message")
        
        # Medium message
        self.logger.info("This is a medium-length message that might wrap on narrow terminals")
        
        # Long message
        self.logger.info("This is a very long log message that will definitely wrap across multiple lines when displayed in a narrow terminal window, demonstrating the automatic line wrapping feature")
        
        # Another long message with different content
        self.logger.warning("Warning: This is a long warning message that contains important information about potential issues that users should be aware of when using the application")
        
        # Error message
        self.logger.error("Error: Failed to process file '/very/long/path/to/some/directory/structure/that/contains/many/nested/folders/and/a/very/long/filename.txt' due to permission denied")
        
        # Info with technical details
        self.logger.info("Processing completed successfully. Total files: 1234, Total size: 5.67 GB, Duration: 12.34 seconds, Average speed: 459 MB/s, Errors: 0, Warnings: 3, Skipped: 5")
        
        # Multiple short messages
        for i in range(3):
            self.logger.info(f"Message {i+1}")
        
        # Another long message
        self.logger.info("The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet and is often used for testing text rendering and wrapping behavior in various applications")
    
    def draw(self):
        """Draw the demo window"""
        height, width = self.renderer.get_dimensions()
        
        # Clear screen
        self.renderer.clear()
        
        # Draw instructions at top
        for i, line in enumerate(self.instructions):
            if i >= height - 5:
                break
            self.renderer.draw_text(i, 0, line[:width])
        
        # Draw separator
        separator_y = len(self.instructions)
        if separator_y < height - 4:
            self.renderer.draw_text(separator_y, 0, "─" * width)
        
        # Draw log pane in remaining space
        log_start_y = separator_y + 1
        log_height = height - log_start_y
        
        if log_height > 0:
            self.log_manager.draw_log_pane(self.renderer, log_start_y, log_height, width)
        
        self.renderer.refresh()
    
    def handle_key(self, key):
        """Handle keyboard input"""
        if key == ord('q') or key == ord('Q'):
            return False
        elif key == self.renderer.KEY_UP:
            self.log_manager.scroll_log_up(1)
            self.content_changed = True
        elif key == self.renderer.KEY_DOWN:
            self.log_manager.scroll_log_down(1)
            self.content_changed = True
        elif key == self.renderer.KEY_PPAGE:  # Page Up
            self.log_manager.scroll_log_up(10)
            self.content_changed = True
        elif key == self.renderer.KEY_NPAGE:  # Page Down
            self.log_manager.scroll_log_down(10)
            self.content_changed = True
        
        return True


def main():
    """Run the demo"""
    app = TtkApplication()
    demo = LogWrappingDemo(app)
    app.run(demo)


if __name__ == "__main__":
    main()
