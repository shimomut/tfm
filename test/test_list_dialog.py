#!/usr/bin/env python3
"""
Test script for the new searchable list dialog feature
"""

import curses
from ttk import KeyEvent, KeyCode, ModifierKey
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_main import FileManager

def test_list_dialog(stdscr):
    """Test the searchable list dialog"""
    try:
        # Initialize file manager
        fm = FileManager(stdscr)
        
        # Create test data
        test_items = [
            "Apple", "Apricot", "Avocado", "Banana", "Blackberry", "Blueberry",
            "Cherry", "Coconut", "Date", "Elderberry", "Fig", "Grape", "Grapefruit",
            "Honeydew", "Kiwi", "Lemon", "Lime", "Mango", "Melon", "Nectarine",
            "Orange", "Papaya", "Peach", "Pear", "Pineapple", "Plum", "Pomegranate",
            "Quince", "Raspberry", "Strawberry", "Tangerine", "Watermelon"
        ]
        
        def selection_callback(selected_item):
            if selected_item:
                print(f"Selected: {selected_item}")
            else:
                print("No selection made")
            # Exit after selection
            fm.should_quit = True
        
        # Show the list dialog
        fm.show_list_dialog("Choose a Fruit", test_items, selection_callback)
        
        # Run the file manager (it will show the dialog)
        fm.run()
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("Testing searchable list dialog...")
    print("Instructions:")
    print("- Use ↑↓ arrow keys to navigate")
    print("- Type to search/filter items")
    print("- Press Enter to select")
    print("- Press ESC to cancel")
    print("- Press any key to start...")
    input()
    
    try:
        curses.wrapper(test_list_dialog)
        print("Test completed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()