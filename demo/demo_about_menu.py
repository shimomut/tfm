#!/usr/bin/env python3
"""
Demo: About Dialog with Matrix-style Animation

This demo showcases the AboutDialog feature which displays:
- TFM ASCII art logo
- Version number
- GitHub URL
- Matrix-style falling green characters in the background

The Matrix effect creates an animated background with falling characters
similar to the iconic "Matrix" movie visual effect.

This demo verifies the fix for black spaces appearing after border characters
when the dialog is drawn over the Matrix animation.

Usage:
    PYTHONPATH=.:src:ttk python demo/demo_about_menu.py

Controls:
    - Press any key to close the About dialog and exit
"""

import sys
import os

# Add src and ttk directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from ttk.backends.curses_backend import CursesBackend
from tfm_about_dialog import AboutDialog
from tfm_config import get_config
from tfm_log_manager import getLogger


def main():
    """Run the demo"""
    logger = getLogger("AboutDemo")
    
    # Create backend
    backend = CursesBackend()
    
    try:
        # Initialize curses
        backend.initialize()
        logger.info("About Dialog Demo started")
        
        # Get config
        config = get_config()
        
        # Create and show the about dialog
        about_dialog = AboutDialog(config, backend)
        about_dialog.show()
        
        # Main loop - render continuously for animation
        while about_dialog.is_active:
            # Clear and render
            backend.clear()
            about_dialog.draw()
            backend.refresh()
            
            # Check for input (non-blocking)
            backend.stdscr.timeout(16)  # ~60 FPS
            try:
                key = backend.stdscr.getch()
                if key != -1:  # Key was pressed
                    # Any key closes the dialog
                    about_dialog.exit()
            except:
                pass
        
        logger.info("About Dialog Demo ended")
        
    finally:
        # Clean up curses
        backend.shutdown()


if __name__ == '__main__':
    main()
