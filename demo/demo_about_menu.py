#!/usr/bin/env python3
"""
Demo: About TFM Menu

This demo tests the "About TFM" menu item functionality.
It verifies that:
1. The About menu item is enabled
2. Clicking it displays the TFM logo, version, and GitHub URL in the log pane
3. The menu event is properly handled

Usage:
    python demo/demo_about_menu.py

Expected behavior:
- In Desktop mode, the "About TFM" menu item should be enabled
- Clicking it should display ASCII art logo, version, and GitHub URL in the log pane
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    """Run the About TFM menu demo."""
    print("About TFM Menu Demo")
    print("=" * 50)
    print()
    print("This demo tests the About TFM menu functionality.")
    print()
    print("Instructions:")
    print("1. Launch TFM in Desktop mode")
    print("2. Click on 'TFM' menu in the menu bar")
    print("3. Select 'About TFM'")
    print("4. Check the log pane for:")
    print("   - TFM ASCII art logo")
    print("   - Version number")
    print("   - GitHub URL")
    print()
    print("Starting TFM in Desktop mode...")
    print()
    
    # Import and run TFM
    from tfm_main import main as tfm_main
    
    # Run TFM (will use Desktop mode if available)
    sys.exit(tfm_main())

if __name__ == '__main__':
    main()
