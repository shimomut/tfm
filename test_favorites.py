#!/usr/bin/env python3
"""
Test script for the favorite directories feature
"""

import curses
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from tfm_main import FileManager
from tfm_config import get_favorite_directories

def test_favorites_config():
    """Test the favorite directories configuration"""
    print("Testing favorite directories configuration...")
    
    favorites = get_favorite_directories()
    print(f"Found {len(favorites)} favorite directories:")
    
    for i, fav in enumerate(favorites, 1):
        print(f"  {i}. {fav['name']} -> {fav['path']}")
    
    return len(favorites) > 0

def test_favorites_dialog(stdscr):
    """Test the favorite directories dialog"""
    try:
        # Initialize file manager
        fm = FileManager(stdscr)
        
        # Show the favorites dialog
        fm.show_favorite_directories()
        
        # Run the file manager (it will show the dialog)
        fm.run()
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("Favorite Directories Feature Test")
    print("=" * 40)
    
    # Test configuration loading
    if not test_favorites_config():
        print("No favorite directories found in configuration!")
        return
    
    print("\nInstructions for interactive test:")
    print("- The favorites dialog will open automatically")
    print("- Use ↑↓ arrow keys to navigate")
    print("- Type to search/filter directories")
    print("- Press Enter to select a directory")
    print("- Press ESC to cancel")
    print("- After selection, the current pane will change to that directory")
    print("\nPress any key to start the test...")
    input()
    
    try:
        curses.wrapper(test_favorites_dialog)
        print("Test completed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()