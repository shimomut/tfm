#!/usr/bin/env python3
"""
Simple test to verify horizontal and vertical lines are visible.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from ttk.backends.curses_backend import CursesBackend
from ttk.test.test_utils import EventCapture


def test_lines():
    """Test that lines are visible."""
    print("Testing horizontal and vertical lines...")
    
    backend = CursesBackend()
    
    try:
        backend.initialize()
        
        # Set up event capture
        capture = EventCapture()
        backend.set_event_callback(capture)
        
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))  # Yellow
        backend.init_color_pair(3, (0, 255, 255), (0, 0, 0))  # Cyan
        
        # Clear screen
        backend.clear()
        
        # Get dimensions
        rows, cols = backend.get_dimensions()
        
        # Draw title
        backend.draw_text(1, 2, f"Terminal size: {rows}x{cols}", 1)
        backend.draw_text(2, 2, "Testing lines with box-drawing characters", 1)
        
        # Draw horizontal line
        backend.draw_text(4, 2, "Horizontal line (─):", 1)
        backend.draw_hline(5, 2, '─', min(30, cols - 4), 2)
        
        # Draw vertical line
        backend.draw_text(7, 2, "Vertical line (│):", 1)
        backend.draw_vline(8, 2, '│', min(5, rows - 10), 3)
        
        # Draw ASCII alternatives for comparison
        if rows > 16:
            backend.draw_text(14, 2, "ASCII horizontal (-):", 1)
            backend.draw_hline(15, 2, '-', min(30, cols - 4), 2)
        
        if rows > 20:
            backend.draw_text(17, 2, "ASCII vertical (|):", 1)
            backend.draw_vline(18, 2, '|', min(5, rows - 20), 3)
        
        # Instructions
        backend.draw_text(rows - 2, 2, "Press 'q' to quit", 1)
        
        # Refresh
        backend.refresh()
        
        # Wait for input using callback mode
        while True:
            event = capture.get_next_event(backend, timeout_ms=100)
            if event and event[0] == 'char' and event[1].char and event[1].char.lower() == 'q':
                break
        
        print("\n✓ Test completed")
        
    finally:
        backend.shutdown()


if __name__ == '__main__':
    test_lines()
