"""
Test script for the help dialog functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_help_dialog.py -v
"""

import curses
from ttk import KeyEvent, KeyCode, ModifierKey



# Add src directory to Python path
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
            if fm.info_dialog.mode:
                if fm.handle_info_dialog_input(key):
                    continue
            
            # Exit on 'q' or if dialog is closed
            if key == ord('q') or not fm.info_dialog.mode:
                break
                
    except Exception as e:
        # Restore stdout/stderr before handling exception
        fm.restore_stdio()
        raise
