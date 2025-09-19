#!/usr/bin/env python3
"""
Demo script showing how to use TFM sub-shell environment variables
"""

import os
import sys
from pathlib import Path

def demo_subshell_usage():
    """Demonstrate usage of TFM sub-shell environment variables"""
    
    # Check if we're in TFM sub-shell
    if 'THIS_DIR' not in os.environ:
        print("This demo should be run from within TFM sub-shell mode.")
        print("1. Start TFM: python3 tfm.py")
        print("2. Press 'x' or 'X' to enter sub-shell mode")
        print("3. Run this script: python3 demo_subshell.py")
        return
    
    print("TFM Sub-shell Demo")
    print("=" * 50)
    
    # Show current directories
    left_dir = Path(os.environ['LEFT_DIR'])
    right_dir = Path(os.environ['RIGHT_DIR'])
    this_dir = Path(os.environ['THIS_DIR'])
    other_dir = Path(os.environ['OTHER_DIR'])
    
    print(f"Left pane:    {left_dir}")
    print(f"Right pane:   {right_dir}")
    print(f"Active pane:  {this_dir}")
    print(f"Other pane:   {other_dir}")
    print()
    
    # Show selected files
    left_selected = os.environ['LEFT_SELECTED'].split() if os.environ['LEFT_SELECTED'] else []
    right_selected = os.environ['RIGHT_SELECTED'].split() if os.environ['RIGHT_SELECTED'] else []
    this_selected = os.environ['THIS_SELECTED'].split() if os.environ['THIS_SELECTED'] else []
    other_selected = os.environ['OTHER_SELECTED'].split() if os.environ['OTHER_SELECTED'] else []
    
    print("Selected files:")
    print(f"  Left pane:   {left_selected if left_selected else 'None'}")
    print(f"  Right pane:  {right_selected if right_selected else 'None'}")
    print(f"  Active pane: {this_selected if this_selected else 'None'}")
    print(f"  Other pane:  {other_selected if other_selected else 'None'}")
    print()
    
    # Example operations
    print("Example operations you can perform:")
    print("=" * 50)
    
    # List files in current directory
    print("1. List files in active directory:")
    print(f"   ls -la '{this_dir}'")
    
    # Copy selected files to other pane
    if this_selected:
        print("\n2. Copy selected files to other pane:")
        for file in this_selected:
            src = this_dir / file
            dst = other_dir / file
            print(f"   cp '{src}' '{dst}'")
    
    # Show disk usage of both directories
    print("\n3. Compare disk usage:")
    print(f"   du -sh '{left_dir}' '{right_dir}'")
    
    # Find files in both directories
    print("\n4. Find Python files in both panes:")
    print(f"   find '{left_dir}' '{right_dir}' -name '*.py'")
    
    print("\n" + "=" * 50)
    print("Type 'exit' to return to TFM")

if __name__ == "__main__":
    demo_subshell_usage()