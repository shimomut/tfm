#!/usr/bin/env python3
"""
Integration test for help dialog functionality
"""

import curses
import time
from tfm_main import FileManager

def test_help_integration(stdscr):
    """Test help dialog integration"""
    # Initialize file manager
    fm = FileManager(stdscr)
    
    # Set up initial display
    fm.needs_full_redraw = True
    
    # Test loop - simulate pressing '?' key
    test_steps = [
        ("Initial display", None),
        ("Press '?' to show help", ord('?')),
        ("Help dialog should be visible", None),
        ("Press 'q' to close help", ord('q')),
        ("Back to main interface", None),
        ("Press 'h' to show help again", ord('h')),
        ("Help dialog visible again", None),
        ("Press ESC to close", 27),
        ("Press 'q' to quit", ord('q'))
    ]
    
    step_index = 0
    
    while step_index < len(test_steps):
        step_name, key_to_press = test_steps[step_index]
        
        # Draw interface
        if fm.needs_full_redraw:
            fm.refresh_files()
            stdscr.clear()
            fm.draw_header()
            fm.draw_files()
            fm.draw_log_pane()
            fm.draw_status()
            stdscr.refresh()
            fm.needs_full_redraw = False
        
        # Show step info in log
        print(f"Test Step {step_index + 1}: {step_name}")
        
        # If we have a key to press, simulate it
        if key_to_press is not None:
            # Handle the key press
            if fm.search_mode:
                if fm.handle_search_input(key_to_press):
                    step_index += 1
                    continue
            
            if fm.dialog_mode:
                if fm.handle_dialog_input(key_to_press):
                    step_index += 1
                    continue
            
            if fm.info_dialog_mode:
                if fm.handle_info_dialog_input(key_to_press):
                    step_index += 1
                    continue
            
            # Handle main keys
            if fm.is_key_for_action(key_to_press, 'quit'):
                print("Quit requested - test complete!")
                break
            elif fm.is_key_for_action(key_to_press, 'help'):
                fm.show_help_dialog()
                print("Help dialog opened!")
            
            fm.needs_full_redraw = True
        
        step_index += 1
        
        # Small delay for visibility
        time.sleep(0.5)
    
    print("Help dialog integration test completed!")

if __name__ == "__main__":
    try:
        curses.wrapper(test_help_integration)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()