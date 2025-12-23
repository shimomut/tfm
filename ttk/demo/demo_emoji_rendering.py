#!/usr/bin/env python3
"""
Demo: Emoji Rendering with Surrogate Pairs

This demo showcases the CoreGraphics backend's ability to correctly render
emoji characters that require UTF-16 surrogate pairs. The fix ensures that
the C++ renderer properly handles multi-byte UTF-16 sequences.

Technical Details:
- Emoji like 😀 (U+1F600) require surrogate pairs in UTF-16
- In UTF-16: 0xD83D (high surrogate) + 0xDE00 (low surrogate)
- The C++ renderer now passes the full character data to CoreText APIs
- Font cascade system automatically selects Apple Color Emoji font

Press 'q' to quit.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import KeyCode


class EmojiDemo:
    """Demo application showing emoji rendering."""
    
    def __init__(self):
        self.backend = CoreGraphicsBackend(
            window_title="TTK Emoji Rendering Demo",
            font_size=16,
            rows=25,
            cols=70
        )
        self.running = True
    
    def run(self):
        """Run the demo."""
        self.backend.initialize()
        
        # Initialize color pairs
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))      # White on black
        self.backend.init_color_pair(2, (255, 255, 0), (0, 0, 128))      # Yellow on blue
        self.backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))          # Green on black
        self.backend.init_color_pair(4, (255, 128, 0), (0, 0, 0))        # Orange on black
        
        # Set event callback
        self.backend.set_event_callback(self)
        
        # Draw initial content
        self.draw_content()
        
        # Run event loop
        self.backend.run_event_loop()
        
        # Cleanup
        self.backend.shutdown()
    
    def draw_content(self):
        """Draw the demo content."""
        # Title
        self.backend.draw_text(0, 0, "TTK Emoji Rendering Demo", color_pair=2)
        self.backend.draw_text(1, 0, "=" * 70, color_pair=1)
        
        # Explanation
        row = 3
        self.backend.draw_text(row, 0, "Emoji characters require UTF-16 surrogate pairs:", color_pair=3)
        row += 2
        
        # Emoji categories
        categories = [
            ("Faces & People", ["😀", "😎", "🤔", "😂", "🥳", "😍", "🤗", "😴"]),
            ("Activities", ["🎉", "🎨", "🎵", "🎮", "⚽", "🎯", "🎪", "🎭"]),
            ("Objects", ["💻", "📱", "⌚", "📷", "💡", "🔧", "✏️", "📚"]),
            ("Nature", ["🌟", "🌈", "🌸", "🌺", "🍀", "🌙", "⭐", "☀️"]),
            ("Symbols", ["❤️", "💚", "💙", "💜", "🔥", "✨", "💫", "⚡"]),
            ("Transport", ["🚀", "✈️", "🚗", "🚲", "🚂", "⛵", "🚁", "🛸"]),
        ]
        
        for category, emojis in categories:
            # Category name
            self.backend.draw_text(row, 2, f"{category}:", color_pair=4)
            row += 1
            
            # Emoji row
            emoji_text = "  " + " ".join(emojis)
            self.backend.draw_text(row, 2, emoji_text, color_pair=1)
            row += 2
        
        # Footer
        self.backend.draw_text(row, 0, "=" * 70, color_pair=1)
        row += 1
        self.backend.draw_text(row, 0, "Technical: Each emoji is a UTF-16 surrogate pair", color_pair=3)
        row += 1
        self.backend.draw_text(row, 0, "Example: 😀 = U+1F600 = 0xD83D + 0xDE00", color_pair=3)
        row += 1
        self.backend.draw_text(row, 0, "Press 'q' to quit", color_pair=2)
        
        # Refresh display
        self.backend.refresh()
    
    def on_key_event(self, event):
        """Handle key events."""
        if event.key == KeyCode.CHAR and event.char == 'q':
            self.running = False
            return True
        return False
    
    def on_char_event(self, event):
        """Handle character events."""
        return False
    
    def on_system_event(self, event):
        """Handle system events."""
        pass
    
    def should_close(self):
        """Check if the application should close."""
        return not self.running


def main():
    """Main entry point."""
    demo = EmojiDemo()
    demo.run()


if __name__ == '__main__':
    main()
