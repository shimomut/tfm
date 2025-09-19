#!/usr/bin/env python3
"""
Test script for the help dialog functionality
"""

import curses
import sys
from tfm_main import FileManager

def test_help_dialog(stdscr):
    """Test the help dialog"""
    try:
        # Initialize file manager
        fm = FileManager(stdscr)
        
        # Show help dialog immediately
        fm.show_help_dialog()
        
        # Simple event loop to test the dialog
        while True:
            # Clear and redraw
            stdscr.clear()
            
            # Draw interface
            fm.draw_header()
            fm.draw_files()
            fm.draw_log_pane()
            fm.draw_status()
            
            # Refresh screen
            stdscr.refresh()
            
            # Get input
            key = stdscr.getch()
            
            # Handle dialog input
            if fm.info_dialog_mode:
                if fm.handle_info_dialog_input(key):
                    continue
            
            # Exit on 'q' or if dialog is closed
            if key == ord('q') or not fm.info_dialog_mode:
                break
                
    except Exception as e:
        # Restore stdout/stderr before handling exception
        fm.restore_stdio()
        raise

if __name__ == "__main__":
    curses.wrapper(test_help_dialog)