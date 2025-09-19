#!/usr/bin/env python3
"""
Demo script for the favorite directories feature
"""

import curses
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from tfm_main import FileManager

def demo_favorites(stdscr):
    """Demo the favorite directories feature"""
    try:
        # Initialize file manager
        fm = FileManager(stdscr)
        
        # Show initial message
        print("Favorite Directories Demo")
        print("Current directory:", fm.get_current_pane()['path'])
        print("Press 'J' to open favorites, or any other key to continue...")
        
        # Run the file manager
        fm.run()
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("Favorite Directories Demo")
    print("=" * 30)
    print()
    print("This demo shows the favorite directories feature:")
    print("1. Press 'J' key to open the favorites dialog")
    print("2. Navigate with ↑↓ arrow keys")
    print("3. Type to search directories")
    print("4. Press Enter to go to selected directory")
    print("5. Press ESC to cancel")
    print()
    print("The current pane will change to your selected favorite directory.")
    print()
    print("Default favorites include:")
    print("- Home directory")
    print("- Documents, Downloads, Desktop")
    print("- Projects folder")
    print("- System directories (/tmp, /, ~/.config)")
    print()
    print("You can customize favorites in ~/.tfm/config.py")
    print()
    print("Press any key to start the demo...")
    input()
    
    try:
        curses.wrapper(demo_favorites)
        print("\nDemo completed!")
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()