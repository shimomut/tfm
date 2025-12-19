#!/usr/bin/env python3
"""
Demo: Focus Brackets Visual Design

This demo showcases the new visual design for filelist panes:
- Red "[" and "]" brackets around the focused item
- No ● marker for multi-selected items
- TextAttribute.REVERSE for multi-selected items
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tfm_main import FileManager

def main():
    """Run the file manager to demonstrate focus brackets"""
    print("=" * 60)
    print("Focus Brackets Visual Design Demo")
    print("=" * 60)
    print()
    print("This demo shows the new visual design:")
    print("  - Focused item: [filename] in red brackets")
    print("  - Multi-selected items: reverse video (no ● marker)")
    print()
    print("Instructions:")
    print("  1. Use arrow keys to move the focus")
    print("  2. Press SPACE to multi-select items")
    print("  3. Notice the red brackets around the focused item")
    print("  4. Notice multi-selected items use reverse video")
    print("  5. Press 'q' to quit")
    print()
    input("Press Enter to start the demo...")
    
    # Create and run file manager
    fm = FileManager()
    fm.run()

if __name__ == "__main__":
    main()
