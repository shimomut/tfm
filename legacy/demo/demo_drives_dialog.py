#!/usr/bin/env python3
"""
Demo script for DrivesDialog functionality
Shows the drives dialog with local filesystem and S3 buckets
"""

import sys
import os
import curses
import time
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_drives_dialog import DrivesDialog, DriveEntry
from tfm_colors import init_colors


def demo_drives_dialog(stdscr):
    """Demo the drives dialog functionality"""
    # Initialize colors
    init_colors('dark')
    
    # Create mock config
    config = Mock()
    config.PROGRESS_ANIMATION_PATTERN = 'spinner'
    config.PROGRESS_ANIMATION_SPEED = 0.2
    
    # Create drives dialog
    dialog = DrivesDialog(config)
    
    # Show instructions
    stdscr.clear()
    stdscr.addstr(0, 0, "DrivesDialog Demo")
    stdscr.addstr(1, 0, "================")
    stdscr.addstr(3, 0, "This demo shows the drives selection dialog.")
    stdscr.addstr(4, 0, "The dialog lists local filesystem locations and S3 buckets.")
    stdscr.addstr(6, 0, "Controls:")
    stdscr.addstr(7, 0, "  ↑/↓     - Navigate drives")
    stdscr.addstr(8, 0, "  Type    - Filter drives")
    stdscr.addstr(9, 0, "  Enter   - Select drive")
    stdscr.addstr(10, 0, "  ESC     - Cancel")
    stdscr.addstr(12, 0, "Press any key to start the demo...")
    stdscr.refresh()
    stdscr.getch()
    
    # Show the drives dialog
    dialog.show()
    
    # Safe string drawing function
    def safe_addstr(y, x, text, attr=0):
        try:
            height, width = stdscr.getmaxyx()
            if 0 <= y < height and 0 <= x < width:
                # Truncate text to fit within screen bounds
                max_len = width - x
                if len(text) > max_len:
                    text = text[:max_len]
                stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass  # Ignore drawing errors
    
    # Main demo loop
    while dialog.mode:
        stdscr.clear()
        
        # Draw the dialog
        dialog.draw(stdscr, safe_addstr)
        
        stdscr.refresh()
        
        # Handle input
        try:
            key = stdscr.getch()
            result = dialog.handle_input(key)
            
            if result == True:
                continue  # Dialog handled the key
            elif isinstance(result, tuple) and result[0] == 'navigate':
                # User selected a drive
                drive_entry = result[1]
                if drive_entry:
                    stdscr.clear()
                    stdscr.addstr(0, 0, f"Selected Drive: {drive_entry.name}")
                    stdscr.addstr(1, 0, f"Path: {drive_entry.path}")
                    stdscr.addstr(2, 0, f"Type: {drive_entry.drive_type}")
                    if drive_entry.description:
                        stdscr.addstr(3, 0, f"Description: {drive_entry.description}")
                    stdscr.addstr(5, 0, "Press any key to continue...")
                    stdscr.refresh()
                    stdscr.getch()
                break
            else:
                # Dialog didn't handle the key, might be exit
                break
                
        except KeyboardInterrupt:
            break
    
    # Clean up
    dialog.exit()
    
    # Show completion message
    stdscr.clear()
    stdscr.addstr(0, 0, "DrivesDialog Demo Complete")
    stdscr.addstr(1, 0, "=========================")
    stdscr.addstr(3, 0, "The drives dialog allows users to:")
    stdscr.addstr(4, 0, "• Browse local filesystem locations")
    stdscr.addstr(5, 0, "• Access S3 buckets (if AWS credentials are configured)")
    stdscr.addstr(6, 0, "• Filter drives by typing")
    stdscr.addstr(7, 0, "• Navigate to selected storage location")
    stdscr.addstr(9, 0, "Integration with TFM:")
    stdscr.addstr(10, 0, "• Bound to 'd' or 'D' key by default")
    stdscr.addstr(11, 0, "• Changes the path of the focused file pane")
    stdscr.addstr(12, 0, "• Supports both local and remote storage")
    stdscr.addstr(14, 0, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()


def main():
    """Main demo function"""
    try:
        curses.wrapper(demo_drives_dialog)
        return 0
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())