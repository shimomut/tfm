#!/usr/bin/env python3
"""
Demo: TextViewer Background Color Fix

This demo shows the TextViewer with proper background color filling.
The fix ensures that empty areas in the text viewer are filled with the 
color scheme's background color instead of the default terminal background.
"""

import os
import sys
import curses
import tempfile
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def demo_text_viewer_background_fix(stdscr):
    """Demonstrate TextViewer with proper background color filling"""
    from tfm_text_viewer import TextViewer
    from tfm_colors import init_colors, get_background_color_pair
    from tfm_config import get_config
    
    # Initialize colors
    config = get_config()
    color_scheme = getattr(config, 'COLOR_SCHEME', 'dark')
    init_colors(color_scheme)
    
    # Create a sample text file with various content
    sample_content = """# TextViewer Background Fix Demo

This demo shows the TextViewer with proper background color filling.

## Before the Fix
- Empty areas were cleared with clrtoeol()
- This left default terminal background color
- Inconsistent appearance with color scheme

## After the Fix  
- Empty areas are filled with background color
- Consistent with the selected color scheme
- Better visual integration

## Test Cases
1. Short lines (like this one)
2. Very long lines that might extend beyond the visible area and require horizontal scrolling to see the full content
3. Empty lines

4. Lines with syntax highlighting
   def example_function():
       return "Hello, World!"

5. Mixed content types

The fix replaces clrtoeol() with explicit background color filling
using addstr() with the proper color scheme background.

Press 'q' to exit, arrow keys to scroll, 'f' for search.
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_content)
        temp_file_path = Path(f.name)
    
    try:
        # Show demo info
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        title = "TextViewer Background Color Fix Demo"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        info_lines = [
            "",
            "This demo shows the TextViewer with proper background color filling.",
            "",
            "Key improvements:",
            "• Empty areas now use color scheme background",
            "• No more default terminal background showing through",
            "• Consistent visual appearance",
            "",
            "The viewer will open with a sample markdown file.",
            "Use arrow keys to scroll, 'f' for search, 'q' to quit.",
            "",
            "Press any key to start the demo..."
        ]
        
        for i, line in enumerate(info_lines):
            if i + 2 < height:
                stdscr.addstr(i + 2, 2, line)
        
        stdscr.refresh()
        stdscr.getch()
        
        # Create and run TextViewer
        viewer = TextViewer(stdscr, temp_file_path)
        viewer.run()
        
        # Show completion message
        stdscr.clear()
        completion_msg = "✓ TextViewer background fix demo completed"
        stdscr.addstr(height // 2, (width - len(completion_msg)) // 2, completion_msg, curses.A_BOLD)
        
        details = [
            "",
            "The fix ensures that:",
            "• Empty areas are filled with proper background color",
            "• Visual consistency with the color scheme",
            "• No terminal background bleeding through",
            "",
            "Press any key to exit..."
        ]
        
        for i, line in enumerate(details):
            if height // 2 + i + 2 < height:
                stdscr.addstr(height // 2 + i + 2, (width - len(line)) // 2, line)
        
        stdscr.refresh()
        stdscr.getch()
        
    finally:
        # Clean up
        os.unlink(temp_file_path)

def main():
    """Run the demo"""
    try:
        curses.wrapper(demo_text_viewer_background_fix)
        print("✓ TextViewer background fix demo completed")
    except KeyboardInterrupt:
        print("\n✓ Demo interrupted by user")
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())