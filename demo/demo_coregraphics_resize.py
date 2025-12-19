#!/usr/bin/env python3
"""
Demo: CoreGraphics Backend Window Resize Event Handling

This demo demonstrates that the CoreGraphics backend properly generates
KeyCode.RESIZE events when the window is resized, allowing applications
to respond to window size changes.

Features demonstrated:
- Window resize event detection
- Dynamic UI updates on resize
- Dimension display updates
- Resize event counter

Instructions:
1. Run the demo
2. Resize the window by dragging the edges or corners
3. Observe the resize event counter increment
4. Observe the dimensions update in real-time
5. Press 'q' to quit

Expected behavior:
- Each window resize should generate a KeyCode.RESIZE event
- The UI should update to show new dimensions
- The resize counter should increment with each resize
- The interface should adapt to the new window size
"""

import sys

# Check if PyObjC is available
try:
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
    print("Error: PyObjC is required for CoreGraphics backend")
    print("Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)

# Check platform
if sys.platform != 'darwin':
    print("Error: CoreGraphics backend is only available on macOS")
    sys.exit(1)

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import KeyCode, ModifierKey


class ResizeDemo:
    """Demo application for testing window resize events."""
    
    def __init__(self):
        """Initialize the demo."""
        self.backend = CoreGraphicsBackend(
            window_title="CoreGraphics Resize Demo",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.resize_count = 0
    
    def draw_interface(self):
        """Draw the demo interface."""
        rows, cols = self.backend.get_dimensions()
        
        # Clear screen
        for row in range(rows):
            for col in range(cols):
                self.backend.draw_text(row, col, ' ', color_pair=0)
        
        # Draw title
        title = "CoreGraphics Window Resize Demo"
        title_col = (cols - len(title)) // 2
        self.backend.draw_text(0, title_col, title, color_pair=1, attributes=0)
        
        # Draw instructions
        instructions = [
            "",
            "Instructions:",
            "  - Resize the window by dragging edges or corners",
            "  - Watch the dimensions and resize counter update",
            "  - Press 'q' to quit",
            "",
        ]
        
        for i, line in enumerate(instructions):
            if 2 + i < rows:
                self.backend.draw_text(2 + i, 2, line, color_pair=0)
        
        # Draw separator
        separator_row = 2 + len(instructions)
        if separator_row < rows:
            separator = "─" * (cols - 4)
            self.backend.draw_text(separator_row, 2, separator, color_pair=0)
        
        # Draw current dimensions
        info_row = separator_row + 2
        if info_row < rows:
            dim_text = f"Current dimensions: {rows} rows × {cols} columns"
            self.backend.draw_text(info_row, 2, dim_text, color_pair=2)
        
        # Draw resize counter
        if info_row + 1 < rows:
            counter_text = f"Resize events received: {self.resize_count}"
            self.backend.draw_text(info_row + 1, 2, counter_text, color_pair=2)
        
        # Draw status
        if info_row + 3 < rows:
            status_text = "Status: Ready - Try resizing the window!"
            self.backend.draw_text(info_row + 3, 2, status_text, color_pair=3)
        
        # Draw border
        self._draw_border(rows, cols)
        
        # Refresh display
        self.backend.refresh()
    
    def _draw_border(self, rows, cols):
        """Draw a border around the window."""
        # Top border
        self.backend.draw_text(0, 0, "┌", color_pair=0)
        for col in range(1, cols - 1):
            self.backend.draw_text(0, col, "─", color_pair=0)
        self.backend.draw_text(0, cols - 1, "┐", color_pair=0)
        
        # Bottom border
        if rows > 1:
            self.backend.draw_text(rows - 1, 0, "└", color_pair=0)
            for col in range(1, cols - 1):
                self.backend.draw_text(rows - 1, col, "─", color_pair=0)
            self.backend.draw_text(rows - 1, cols - 1, "┘", color_pair=0)
        
        # Side borders
        for row in range(1, rows - 1):
            self.backend.draw_text(row, 0, "│", color_pair=0)
            self.backend.draw_text(row, cols - 1, "│", color_pair=0)
    
    def run(self):
        """Run the demo."""
        # Initialize backend
        self.backend.initialize()
        
        # Initialize color pairs
        self.backend.init_color_pair(0, (200, 200, 200), (0, 0, 0))      # Normal text
        self.backend.init_color_pair(1, (100, 200, 255), (0, 0, 0))      # Title (blue)
        self.backend.init_color_pair(2, (100, 255, 100), (0, 0, 0))      # Info (green)
        self.backend.init_color_pair(3, (255, 200, 100), (0, 0, 0))      # Status (orange)
        
        # Draw initial interface
        self.draw_interface()
        
        # Main event loop
        print("Demo running. Resize the window to test resize events.")
        print("Press 'q' to quit.")
        
        while True:
            # Get input with short timeout for responsive UI
            event = self.backend.get_input(timeout_ms=100)
            
            if event is None:
                continue
            
            # Handle resize event
            if event.key_code == KeyCode.RESIZE:
                self.resize_count += 1
                print(f"Resize event #{self.resize_count} detected!")
                rows, cols = self.backend.get_dimensions()
                print(f"  New dimensions: {rows} rows × {cols} columns")
                self.draw_interface()
                continue
            
            # Handle quit
            if event.char and event.char.lower() == 'q':
                print(f"\nDemo completed. Total resize events: {self.resize_count}")
                break
        
        # Clean up
        self.backend.shutdown()


def main():
    """Main entry point."""
    print("=" * 60)
    print("CoreGraphics Backend Window Resize Demo")
    print("=" * 60)
    print()
    
    demo = ResizeDemo()
    demo.run()


if __name__ == '__main__':
    main()
