#!/usr/bin/env python3
"""
Verification script for curses backend black background fix.

This script verifies that the curses backend properly displays a black
background instead of using the terminal's default background color.

The fix involved:
1. Removing curses.use_default_colors() which allowed terminal defaults
2. Explicitly initializing color pair 1 with white on black
3. Setting the window background using bkgd() with the black color pair

Run this script to verify the background is black throughout the terminal.
"""

import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from ttk.backends.curses_backend import CursesBackend


def main():
    """Run the background verification test."""
    backend = CursesBackend()
    
    try:
        print("Initializing curses backend...")
        backend.initialize()
        
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))  # White on black
        backend.init_color_pair(2, (255, 0, 0), (0, 0, 0))      # Red on black
        
        # Clear screen - should show black background everywhere
        backend.clear()
        
        # Draw test text
        rows, cols = backend.get_dimensions()
        
        backend.draw_text(2, 2, "=" * (cols - 4), 1)
        backend.draw_text(3, 2, "Curses Backend Black Background Verification", 1)
        backend.draw_text(4, 2, "=" * (cols - 4), 1)
        backend.draw_text(6, 2, "If you see BLACK background everywhere, the fix works!", 1)
        backend.draw_text(7, 2, "If you see WHITE or other color background, there's still an issue.", 2)
        backend.draw_text(9, 2, f"Terminal size: {rows} rows x {cols} columns", 1)
        backend.draw_text(11, 2, "Press 'q' to quit", 1)
        
        # Refresh display
        backend.refresh()
        
        # Wait for user to quit
        while True:
            event = backend.get_input(timeout_ms=100)
            if event and event.char and event.char.lower() == 'q':
                break
        
        print("\nVerification completed!")
        print("Background should have been black throughout the terminal.")
        
    except Exception as e:
        print(f"\nError during verification: {e}", file=sys.stderr)
        raise
    finally:
        backend.shutdown()


if __name__ == '__main__':
    main()
