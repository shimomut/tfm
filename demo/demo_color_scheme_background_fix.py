#!/usr/bin/env python3
"""
Demo: Color Scheme Background Fix

This demo tests the fix for black background areas remaining visible when
switching from dark to light color scheme in desktop mode.

The issue occurred in:
- Left-most column in left pane
- Right-most column in left pane
- Right-most column in right pane
- Empty areas where no items are rendered

The fix adds an update_background() method to CoreGraphicsBackend that updates
the NSView's background color when the color scheme changes.

Usage:
    python demo/demo_color_scheme_background_fix.py

Test procedure:
1. Application starts with dark color scheme
2. Press 't' to toggle to light color scheme
3. Verify that ALL areas show the correct light background (no black areas)
4. Press 't' again to toggle back to dark
5. Verify that ALL areas show the correct dark background
6. Press 'q' to quit
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import KeyEvent, KeyCode
from tfm_colors import init_colors, toggle_color_scheme, get_current_color_scheme


class ColorSchemeTestApp:
    """Test application for color scheme background fix"""
    
    def __init__(self):
        """Initialize the test application"""
        # Create backend with desktop mode
        self.backend = CoreGraphicsBackend(
            window_title="Color Scheme Background Fix Test",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize with dark color scheme
        init_colors(self.backend, 'dark')
        
        # Set event callback
        self.backend.set_event_callback(self)
        
        self.running = True
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle key events"""
        if event.key == KeyCode.CHAR and event.char == 'q':
            self.running = False
            return True
        elif event.key == KeyCode.CHAR and event.char == 't':
            # Toggle color scheme
            new_scheme = toggle_color_scheme()
            init_colors(self.backend, new_scheme)
            print(f"Switched to {new_scheme} color scheme")
            
            # Clear and redraw
            self.backend.clear()
            self.draw()
            self.backend.refresh()
            return True
        
        return False
    
    def on_char_event(self, event) -> bool:
        """Handle character events"""
        return False
    
    def on_system_event(self, event) -> None:
        """Handle system events"""
        pass
    
    def should_close(self) -> bool:
        """Check if application should close"""
        return not self.running
    
    def draw(self):
        """Draw the test interface"""
        # Get current color scheme
        scheme = get_current_color_scheme()
        
        # Draw title
        title = f"Color Scheme Background Fix Test - Current: {scheme}"
        self.backend.draw_text(0, 2, title, color_pair=1, attributes=0)
        
        # Draw instructions
        self.backend.draw_text(2, 2, "Instructions:", color_pair=1, attributes=0)
        self.backend.draw_text(3, 4, "Press 't' to toggle color scheme", color_pair=0, attributes=0)
        self.backend.draw_text(4, 4, "Press 'q' to quit", color_pair=0, attributes=0)
        
        # Draw test areas
        self.backend.draw_text(6, 2, "Test Areas:", color_pair=1, attributes=0)
        self.backend.draw_text(7, 4, "1. Left edge (column 0)", color_pair=0, attributes=0)
        self.backend.draw_text(8, 4, "2. Right edge (last column)", color_pair=0, attributes=0)
        self.backend.draw_text(9, 4, "3. Empty areas below", color_pair=0, attributes=0)
        
        # Draw some content in left column (column 0)
        for row in range(11, 20):
            self.backend.draw_text(row, 0, "|", color_pair=0, attributes=0)
        
        # Draw some content in right column (last column)
        height, width = self.backend.get_dimensions()
        for row in range(11, 20):
            self.backend.draw_text(row, width - 1, "|", color_pair=0, attributes=0)
        
        # Draw verification message
        self.backend.draw_text(22, 2, "Verify: No black areas should be visible in light mode", 
                             color_pair=1, attributes=0)
    
    def run(self):
        """Run the test application"""
        # Initial draw
        self.draw()
        self.backend.refresh()
        
        # Run event loop
        self.backend.run_event_loop()
        
        # Cleanup
        self.backend.shutdown()


def main():
    """Main entry point"""
    print("Starting Color Scheme Background Fix Test...")
    print("This demo tests the fix for black background areas in desktop mode")
    print()
    
    app = ColorSchemeTestApp()
    app.run()
    
    print("Test completed")


if __name__ == '__main__':
    main()
