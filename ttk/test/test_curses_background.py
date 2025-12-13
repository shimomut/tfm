#!/usr/bin/env python3
"""
Test script to verify curses backend has proper black background.

This script initializes the curses backend and draws some text to verify
that the background is black, not white or terminal default.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from ttk.backends.curses_backend import CursesBackend
import time


def test_background():
    """Test that curses backend has black background."""
    backend = CursesBackend()
    
    try:
        # Initialize backend
        backend.initialize()
        
        # Initialize a color pair
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Clear screen (should show black background)
        backend.clear()
        
        # Draw some text
        backend.draw_text(5, 5, "Testing black background - you should see black everywhere", 1)
        backend.draw_text(7, 5, "If you see white background, the fix didn't work", 1)
        backend.draw_text(9, 5, "Press 'q' to quit", 1)
        
        # Refresh to show changes
        backend.refresh()
        
        # Wait for user input
        while True:
            event = backend.get_input(timeout_ms=100)
            if event and event.char and event.char.lower() == 'q':
                break
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        raise
    finally:
        backend.shutdown()


if __name__ == '__main__':
    test_background()
