"""
Demo: Extended Edge Background

This demo demonstrates the extended edge background feature where the
background colors of edge cells (top, bottom, left, right) are extended
to fill the frame area when the window size doesn't perfectly match the
grid dimensions.

When you resize the window, you should see NO white background - the edge
cells' backgrounds extend to fill the entire window.

Features demonstrated:
- Edge cell backgrounds extend beyond grid boundaries
- No white background visible around edges
- Smooth appearance during window resize

Usage:
    python ttk/demo/demo_centered_text_grid.py

Controls:
    - Resize the window to see the effect
    - Press 'q' to quit
"""

import sys
import os

# Add parent directory to path to import ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import Event, KeyEvent


class ExtendedEdgeBackgroundDemo:
    """Demo application showing extended edge backgrounds."""
    
    def __init__(self):
        """Initialize the demo."""
        self.backend = CoreGraphicsBackend(
            window_title="Extended Edge Background Demo",
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
        # Initialize color pairs with distinct colors for edge visibility
        self.backend.init_color_pair(1, (255, 255, 255), (0, 100, 200))    # White on blue
        self.backend.init_color_pair(2, (255, 255, 0), (0, 100, 200))      # Yellow on blue
        self.backend.init_color_pair(3, (0, 255, 0), (50, 50, 50))         # Green on dark gray
        self.backend.init_color_pair(4, (255, 255, 255), (200, 0, 0))      # White on red (for edges)
        
        # Fill entire grid with blue background to show edge extension
        for row in range(20):
            for col in range(60):
                self.backend.draw_text(row, col, " ", color_pair=1)
        
        # Draw title
        title = "Extended Edge Background Demo"
        self.backend.draw_text(0, (60 - len(title)) // 2, title, color_pair=2)
        
        # Draw instructions
        self.backend.draw_text(2, 2, "Edge cells extend their background to fill frame.", color_pair=1)
        self.backend.draw_text(3, 2, "Resize the window - no white background visible!", color_pair=1)
        
        # Highlight the edge cells with red background
        # Top row
        for col in range(60):
            self.backend.draw_text(0, col, " ", color_pair=4)
        
        # Bottom row
        for col in range(60):
            self.backend.draw_text(19, col, " ", color_pair=4)
        
        # Left column
        for row in range(20):
            self.backend.draw_text(row, 0, " ", color_pair=4)
        
        # Right column
        for row in range(20):
            self.backend.draw_text(row, 59, " ", color_pair=4)
        
        # Redraw title and instructions on top of red edges
        self.backend.draw_text(0, (60 - len(title)) // 2, title, color_pair=2)
        
        # Draw centered message
        msg1 = "Red edges extend beyond grid"
        msg2 = "to fill the frame area"
        self.backend.draw_text(9, (60 - len(msg1)) // 2, msg1, color_pair=1)
        self.backend.draw_text(10, (60 - len(msg2)) // 2, msg2, color_pair=1)
        
        # Draw quit instruction
        self.backend.draw_text(19, (60 - 17) // 2, "Press 'q' to quit", color_pair=2)
        
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
    demo = ExtendedEdgeBackgroundDemo()
    demo.run()
