"""
Test for background color fix - verifying bkgd() replacement with addstr() approach

Run with: PYTHONPATH=.:src:ttk pytest test/test_background_color.py -v
"""

import curses
from ttk import KeyEvent, KeyCode, ModifierKey
import time

def test_background_color_fix(stdscr):
    """Test the new background color approach without using bkgd()"""
    
    # Initialize colors
    from tfm_colors import init_colors, apply_background_to_window, get_background_color_pair, COLOR_BACKGROUND
    
    # Test both color schemes
    schemes = ['dark', 'light']
    
    for scheme in schemes:
        stdscr.clear()
        
        # Initialize colors for this scheme
        init_colors(scheme)
        
        # Display scheme info
        stdscr.addstr(0, 0, f"Testing {scheme} scheme background color fix", curses.A_BOLD)
        stdscr.addstr(1, 0, "Press any key to continue to next scheme...")
        
        # Apply background using new method
        success = apply_background_to_window(stdscr)
        
        # Show status
        if success:
            stdscr.addstr(3, 0, f"✓ Background applied successfully using addstr() method", curses.A_BOLD)
        else:
            stdscr.addstr(3, 0, f"✗ Background application failed", curses.A_BOLD)
        
        # Show color pair info
        bg_pair = get_background_color_pair()
        stdscr.addstr(4, 0, f"Background color pair: {bg_pair}")
        stdscr.addstr(5, 0, f"COLOR_BACKGROUND constant: {COLOR_BACKGROUND}")
        
        # Test manual background filling
        stdscr.addstr(7, 0, "Manual background test area:")
        try:
            # Fill a small area manually
            for y in range(9, 15):
                stdscr.addstr(y, 2, ' ' * 40, bg_pair)
            
            # Add some text over the background
            stdscr.addstr(11, 4, "Text over background", curses.A_BOLD)
            stdscr.addstr(12, 4, "Should have proper colors", curses.A_NORMAL)
            
        except curses.error:
            stdscr.addstr(9, 0, "Error filling background area")
        
        stdscr.refresh()
        stdscr.getch()  # Wait for key press

def main():
    """Main test function"""
    try:
        curses.wrapper(test_background_color_fix)
        print("Background color fix test completed successfully!")
        print("The new approach uses addstr() with spaces instead of bkgd()")
        print("This should be more consistent across different terminal environments.")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return 1
    
    return 0
