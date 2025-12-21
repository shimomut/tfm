#!/usr/bin/env python3
"""
Demo to debug help key ('?') binding issue.
This will log all key events to help diagnose why '?' doesn't open help dialog.
"""

import sys
import os

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

def main():
    from tfm_main import FileManager
    from ttk.backends.curses_backend import CursesBackend
    
    # Create renderer (CursesBackend is a Renderer)
    renderer = CursesBackend()
    
    # Create FileManager
    fm = FileManager(renderer)
    
    # Wrap the handle_input method to log events
    original_handle_input = fm.handle_input
    
    def logged_handle_input(event):
        from tfm_input_utils import input_event_to_key_char
        from ttk import KeyEvent, CharEvent
        
        event_type = type(event).__name__
        key_char = input_event_to_key_char(event) if isinstance(event, KeyEvent) else None
        
        if isinstance(event, KeyEvent):
            fm.log_manager.add_message("DEBUG", 
                f"KeyEvent: char={repr(event.char)}, key_code={event.key_code}, "
                f"modifiers={event.modifiers}, key_char={repr(key_char)}")
        elif isinstance(event, CharEvent):
            fm.log_manager.add_message("DEBUG", 
                f"CharEvent: char={repr(event.char)}")
        
        # Check if it matches help action
        if isinstance(event, KeyEvent):
            is_help = fm.is_key_for_action(event, 'help')
            fm.log_manager.add_message("DEBUG", f"  is_key_for_action('help') = {is_help}")
        
        return original_handle_input(event)
    
    fm.handle_input = logged_handle_input
    
    # Run the file manager
    fm.log_manager.add_message("INFO", "Press '?' to test help dialog. Press 'q' to quit.")
    fm.log_manager.add_message("INFO", "All key events will be logged to help debug the issue.")
    fm.run()

if __name__ == '__main__':
    main()
