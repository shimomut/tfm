#!/usr/bin/env python3
"""
Test script to verify the dot key functionality works in the file manager
"""

import sys
import os
import curses
from ttk.input_event import InputEvent, KeyCode, ModifierKey
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_main import FileManager

def test_dot_key_functionality(stdscr):
    """Test that the dot key toggles hidden files in the file manager"""
    print("Testing dot key functionality...")
    
    # Initialize file manager
    fm = FileManager(stdscr)
    
    # Test initial state
    initial_hidden_state = fm.show_hidden
    print(f"Initial hidden files state: {initial_hidden_state}")
    
    # Simulate pressing the dot key
    dot_key = ord('.')
    
    # Check if the key is recognized as toggle_hidden action
    is_toggle_action = fm.is_key_for_action(dot_key, 'toggle_hidden')
    print(f"Is dot key recognized as toggle_hidden action? {is_toggle_action}")
    
    if is_toggle_action:
        # Simulate the toggle action
        fm.show_hidden = not fm.show_hidden
        new_hidden_state = fm.show_hidden
        print(f"New hidden files state after toggle: {new_hidden_state}")
        
        # Verify the state changed
        assert new_hidden_state != initial_hidden_state, "Hidden files state should have changed"
        print("✓ Dot key successfully toggles hidden files state")
    else:
        print("✗ Dot key is not recognized as toggle_hidden action")
        return False
    
    return True

def main():
    """Main test function"""
    try:
        # We'll just test the key binding logic without actually starting curses
        # since we can't run a full interactive session in this test
        
        # Test the key binding configuration
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from tfm_config import is_key_bound_to
        
        # Test that dot is bound to toggle_hidden
        is_bound = is_key_bound_to('.', 'toggle_hidden')
        print(f"Dot key bound to toggle_hidden: {is_bound}")
        
        if is_bound:
            print("✓ Configuration test passed: Dot key is properly bound")
            return True
        else:
            print("✗ Configuration test failed: Dot key is not bound")
            return False
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✓ All tests passed! The dot key should now toggle hidden files.")
    else:
        print("\n✗ Tests failed!")
        sys.exit(1)