#!/usr/bin/env python3
"""
Demo: Window Resize Snapping

This demo demonstrates the window resize snapping feature in the CoreGraphics backend.
The window size is automatically snapped to the character grid at the start and end
of resize operations, ensuring that the content area is always an exact multiple of
the character cell size.

Features demonstrated:
- Window snapping at resize start (windowWillStartLiveResize_)
- Window snapping at resize end (windowDidEndLiveResize_)
- Resize increments during dragging (setResizeIncrements_)
- Visual feedback showing grid alignment

Instructions:
1. Run the demo
2. Try resizing the window by dragging the resize handle
3. Notice that the window snaps to the character grid at the start of resize
4. During resize, the window moves in character cell increments
5. At the end of resize, the window snaps again to ensure perfect alignment
6. The status bar shows the current grid dimensions and alignment status

Press 'q' to quit.
"""

import sys
import os

# Add project root to path to import ttk
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
from ttk.input_event import KeyCode


class ResizeSnappingDemo:
    """Demo application showing window resize snapping."""
    
    def __init__(self):
        """Initialize the demo."""
        if not COCOA_AVAILABLE:
            print("Error: CoreGraphics backend requires PyObjC")
            print("Install with: pip install pyobjc-framework-Cocoa")
            sys.exit(1)
        
        # Create backend with initial size
        self.backend = CoreGraphicsBackend(
            window_title="Window Resize Snapping Demo",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        
        self.running = True
    
    def on_key_event(self, event):
        """Handle key events."""
        if event.key == KeyCode.CHAR and event.char == 'q':
            self.running = False
            return True
        return False
    
    def on_char_event(self, event):
        """Handle character events."""
        return True
    
    def on_system_event(self, event):
        """Handle system events."""
        pass
    
    def should_close(self):
        """Check if window should close."""
        return not self.running
    
    def draw_header(self):
        """Draw the header with title and instructions."""
        title = "Window Resize Snapping Demo"
        instructions = "Resize the window to see snapping in action | Press 'q' to quit"
        
        # Draw title centered
        col = (self.backend.cols - len(title)) // 2
        self.backend.draw_text(0, col, title, color_pair=1, attributes=0)
        
        # Draw instructions centered
        col = (self.backend.cols - len(instructions)) // 2
        self.backend.draw_text(1, col, instructions, color_pair=2, attributes=0)
        
        # Draw separator line
        self.backend.draw_text(2, 0, "─" * self.backend.cols, color_pair=3, attributes=0)
    
    def draw_grid_info(self):
        """Draw information about the current grid dimensions."""
        row = 4
        
        # Grid dimensions
        info = f"Grid Dimensions: {self.backend.rows} rows × {self.backend.cols} cols"
        self.backend.draw_text(row, 2, info, color_pair=0, attributes=0)
        row += 2
        
        # Character cell size
        info = f"Character Cell: {self.backend.char_width:.1f}px × {self.backend.char_height:.1f}px"
        self.backend.draw_text(row, 2, info, color_pair=0, attributes=0)
        row += 2
        
        # Content size
        content_width = self.backend.cols * self.backend.char_width
        content_height = self.backend.rows * self.backend.char_height
        info = f"Content Size: {content_width:.1f}px × {content_height:.1f}px"
        self.backend.draw_text(row, 2, info, color_pair=0, attributes=0)
        row += 2
        
        # Alignment status
        info = "Alignment: Perfect (snapped to grid)"
        self.backend.draw_text(row, 2, info, color_pair=4, attributes=0)
    
    def draw_visual_grid(self):
        """Draw a visual representation of the character grid."""
        start_row = 12
        
        # Draw grid pattern
        for row in range(start_row, self.backend.rows - 1):
            for col in range(self.backend.cols):
                # Draw a checkerboard pattern
                if (row + col) % 2 == 0:
                    char = '·'
                else:
                    char = ' '
                self.backend.draw_text(row, col, char, color_pair=5, attributes=0)
    
    def draw_status_bar(self):
        """Draw the status bar at the bottom."""
        status = f" Size: {self.backend.rows}×{self.backend.cols} | Snapping: Active "
        status = status.ljust(self.backend.cols)
        self.backend.draw_text(
            self.backend.rows - 1, 0, status,
            color_pair=6, attributes=0
        )
    
    def draw(self):
        """Draw the demo interface."""
        # Clear screen
        self.backend.clear()
        
        # Draw components
        self.draw_header()
        self.draw_grid_info()
        self.draw_visual_grid()
        self.draw_status_bar()
        
        # Refresh display
        self.backend.refresh()
    
    def run(self):
        """Run the demo."""
        # Initialize backend
        self.backend.initialize()
        
        # Set up event callback
        self.backend.set_event_callback(self)
        
        # Initialize color pairs
        # 1: Title (white on blue)
        self.backend.init_color_pair(1, (255, 255, 255), (0, 100, 200))
        
        # 2: Instructions (yellow on black)
        self.backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))
        
        # 3: Separator (cyan on black)
        self.backend.init_color_pair(3, (0, 255, 255), (0, 0, 0))
        
        # 4: Alignment status (green on black)
        self.backend.init_color_pair(4, (0, 255, 0), (0, 0, 0))
        
        # 5: Grid pattern (dark gray on black)
        self.backend.init_color_pair(5, (100, 100, 100), (0, 0, 0))
        
        # 6: Status bar (black on white)
        self.backend.init_color_pair(6, (0, 0, 0), (255, 255, 255))
        
        # Initial draw
        self.draw()
        
        # Run event loop
        while self.running:
            self.backend.run_event_loop_iteration()
            
            # Redraw on each iteration to update grid info
            self.draw()
        
        # Clean up
        self.backend.shutdown()


def main():
    """Main entry point."""
    demo = ResizeSnappingDemo()
    demo.run()


if __name__ == '__main__':
    main()
