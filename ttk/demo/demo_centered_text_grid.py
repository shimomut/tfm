"""
Demo: Centered Text Grid

This demo demonstrates the centered text grid rendering feature where the
text grid is centered within the window when the window size doesn't perfectly
match the grid dimensions.

When you resize the window, you should see equal white background (frame) on
all sides of the text grid, rather than having it bunched up on the top and left.

Features demonstrated:
- Text grid centered within window content area
- Equal frame width on top/bottom and left/right
- Proper centering maintained during window resize

Usage:
    python ttk/demo/demo_centered_text_grid.py

Controls:
    - Resize the window to see the centering effect
    - Press 'q' to quit
"""

import sys
import os

# Add parent directory to path to import ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import Event, KeyEvent


class CenteredGridDemo:
    """Demo application showing centered text grid."""
    
    def __init__(self):
        """Initialize the demo."""
        self.backend = CoreGraphicsBackend(
            window_title="Centered Text Grid Demo",
            font_name="Menlo",
            font_size=14,
            rows=20,
            cols=60
        )
        self.running = True
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle key events."""
        if event.char == 'q':
            self.running = False
            return True
        return False
    
    def on_char_event(self, event: Event) -> bool:
        """Handle character events."""
        return False
    
    def on_system_event(self, event: Event):
        """Handle system events."""
        pass
    
    def should_close(self) -> bool:
        """Check if window should close."""
        return not self.running
    
    def draw_content(self):
        """Draw demo content."""
        # Initialize color pairs
        self.backend.init_color_pair(1, (255, 255, 255), (0, 100, 200))    # White on blue
        self.backend.init_color_pair(2, (255, 255, 0), (0, 100, 200))      # Yellow on blue
        self.backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))            # Green on black
        
        # Draw title
        title = "Centered Text Grid Demo"
        self.backend.draw_text(0, (60 - len(title)) // 2, title, color_pair=2)
        
        # Draw instructions
        self.backend.draw_text(2, 2, "This demo shows the centered text grid feature.", color_pair=1)
        self.backend.draw_text(3, 2, "Resize the window to see the effect.", color_pair=1)
        self.backend.draw_text(5, 2, "Notice:", color_pair=2)
        self.backend.draw_text(6, 2, "- Equal white frame on all sides", color_pair=1)
        self.backend.draw_text(7, 2, "- Text grid stays centered", color_pair=1)
        self.backend.draw_text(8, 2, "- Frame width adjusts automatically", color_pair=1)
        
        # Draw a border to show the grid boundaries
        for col in range(60):
            self.backend.draw_text(10, col, "─", color_pair=3)
            self.backend.draw_text(18, col, "─", color_pair=3)
        
        for row in range(10, 19):
            self.backend.draw_text(row, 0, "│", color_pair=3)
            self.backend.draw_text(row, 59, "│", color_pair=3)
        
        # Draw corners
        self.backend.draw_text(10, 0, "┌", color_pair=3)
        self.backend.draw_text(10, 59, "┐", color_pair=3)
        self.backend.draw_text(18, 0, "└", color_pair=3)
        self.backend.draw_text(18, 59, "┘", color_pair=3)
        
        # Draw centered text
        msg = "Text Grid Area"
        self.backend.draw_text(14, (60 - len(msg)) // 2, msg, color_pair=1)
        
        # Draw quit instruction
        self.backend.draw_text(19, 2, "Press 'q' to quit", color_pair=2)
        
        self.backend.refresh()
    
    def run(self):
        """Run the demo."""
        self.backend.initialize()
        self.backend.set_event_callback(self)
        
        # Draw initial content
        self.draw_content()
        
        # Run event loop
        self.backend.run_event_loop()
        
        # Clean up
        self.backend.shutdown()


if __name__ == '__main__':
    demo = CenteredGridDemo()
    demo.run()
