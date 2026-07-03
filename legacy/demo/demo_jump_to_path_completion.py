#!/usr/bin/env python3
"""
Demo: Jump-to-Path with Filepath Completion

This demo shows the jump-to-path dialog with TAB completion enabled.

Usage:
    python demo/demo_jump_to_path_completion.py

Features demonstrated:
- Press Shift+J to open jump-to-path dialog
- Type partial path and press TAB to see completions
- Candidate list shows matching directories/files
- Press TAB again to complete to common prefix
- Type more characters to filter candidates
- Press ESC to dismiss candidate list
- Press Enter to navigate to path

Example workflow:
1. Press Shift+J
2. Type: /Users/your_name/Do
3. Press TAB - see "Documents/", "Downloads/"
4. Type: c
5. Press TAB - completes to "Documents/"
6. Press Enter - navigates to Documents folder
"""

import sys
import os

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_main import TFM
from tfm_config import Config


def main():
    """Run the demo"""
    print("=" * 70)
    print("Jump-to-Path Filepath Completion Demo")
    print("=" * 70)
    print()
    print("This demo shows the jump-to-path dialog with TAB completion.")
    print()
    print("Instructions:")
    print("  1. Press Shift+J to open the jump-to-path dialog")
    print("  2. Start typing a path (e.g., /Users/your_name/Do)")
    print("  3. Press TAB to see completion candidates")
    print("  4. Type more characters to filter the list")
    print("  5. Press TAB again to complete to common prefix")
    print("  6. Press ESC to dismiss the candidate list")
    print("  7. Press Enter to navigate to the completed path")
    print("  8. Press Q to quit the demo")
    print()
    print("Features:")
    print("  • TAB completion for file and directory paths")
    print("  • Visual candidate list showing all matches")
    print("  • Dynamic filtering as you type")
    print("  • Directories shown with trailing / separator")
    print("  • Works with absolute and relative paths")
    print()
    print("=" * 70)
    print()
    input("Press Enter to start the demo...")
    
    # Create config and start TFM
    config = Config()
    tfm = TFM(config)
    
    # Run the application
    tfm.run()


if __name__ == '__main__':
    main()
