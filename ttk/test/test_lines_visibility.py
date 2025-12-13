#!/usr/bin/env python3
"""
Minimal test to verify horizontal and vertical lines are visible with Unicode characters.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from ttk.backends.curses_backend import CursesBackend


def main():
    """Test line visibility with minimal setup."""
    backend = CursesBackend()
    
    try:
        backend.initialize()
        
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))  # White on black
        backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))    # Yellow on black
        backend.init_color_pair(3, (0, 255, 255), (0, 0, 0))    # Cyan on black
        
        # Clear screen
        backend.clear()
        
        # Get dimensions
        rows, cols = backend.get_dimensions()
        
        # Draw title
        backend.draw_text(1, 2, "Line Visibility Test", 1)
        backend.draw_text(2, 2, f"Terminal: {rows}x{cols}", 1)
        backend.draw_text(3, 2, "Press 'q' to quit", 1)
        
        # Draw horizontal line with Unicode box-drawing character
        backend.draw_text(5, 2, "Horizontal line (─):", 1)
        backend.draw_hline(6, 2, '─', 30, 2)
        
        # Draw vertical line with Unicode box-drawing character
        backend.draw_text(8, 2, "Vertical line (│):", 1)
        backend.draw_vline(9, 2, '│', 5, 3)
        
        # Draw a rectangle for comparison
        backend.draw_text(15, 2, "Rectangle:", 1)
        backend.draw_rect(16, 2, 5, 20, 2, filled=False)
        
        # Refresh
        backend.refresh()
        
        # Wait for input
        while True:
            event = backend.get_input(timeout_ms=-1)
            if event and event.char and event.char.lower() == 'q':
                break
        
    finally:
        backend.shutdown()


if __name__ == '__main__':
    main()
