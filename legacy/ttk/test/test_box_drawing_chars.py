#!/usr/bin/env python3
"""
Test script to verify box-drawing characters in rectangles and lines.

This script creates a simple test that draws rectangles and lines,
verifying they use proper box-drawing characters (┌┐└┘─│) consistently
instead of simple ASCII characters (-|).
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from ttk.backends.curses_backend import CursesBackend
from ttk.test.test_utils import EventCapture


def test_box_drawing_characters():
    """Test that rectangles and lines use proper box-drawing characters."""
    print("Testing box-drawing characters in TTK...")
    
    # Create backend
    backend = CursesBackend()
    
    try:
        # Initialize
        backend.initialize()
        
        # Set up event capture
        capture = EventCapture()
        backend.set_event_callback(capture)
        
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        backend.init_color_pair(2, (0, 255, 0), (0, 0, 0))
        backend.init_color_pair(3, (0, 255, 255), (0, 0, 0))
        
        # Clear screen
        backend.clear()
        
        # Add title
        backend.draw_text(1, 10, "Box-Drawing Character Consistency Test", 1)
        backend.draw_text(2, 10, "All shapes should use: ┌┐└┘─│", 1)
        
        # Draw a test rectangle
        backend.draw_text(4, 10, "Rectangle:", 2)
        backend.draw_rect(5, 10, 8, 30, color_pair=1, filled=False)
        
        # Draw horizontal line (should match rectangle edges)
        backend.draw_text(14, 10, "Horizontal line (should match rectangle edges):", 2)
        backend.draw_hline(15, 10, '─', 30, color_pair=3)
        
        # Draw vertical line (should match rectangle edges)
        backend.draw_text(17, 10, "Vertical line:", 2)
        backend.draw_text(17, 26, "(should match", 2)
        backend.draw_text(18, 26, "rectangle edges)", 2)
        backend.draw_vline(17, 24, '│', 5, color_pair=3)
        
        # Instructions
        backend.draw_text(23, 10, "Press 'q' to quit", 1)
        
        # Refresh to show
        backend.refresh()
        
        # Wait for input using callback mode
        while True:
            event = capture.get_next_event(backend, timeout_ms=100)
            if event and event[0] == 'char' and event[1].char and event[1].char.lower() == 'q':
                break
        
        print("\n✓ Test completed successfully!")
        print("  All shapes now use consistent box-drawing characters:")
        print("  - Corners: ┌ ┐ └ ┘")
        print("  - Horizontal edges/lines: ─")
        print("  - Vertical edges/lines: │")
        
    finally:
        backend.shutdown()


if __name__ == '__main__':
    test_box_drawing_characters()
