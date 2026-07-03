#!/usr/bin/env python3
"""
Demo: Diff Viewer Whitespace Ignore Mode

This demo showcases the whitespace ignore feature in the diff viewer.
It creates two files with identical content but different whitespace,
then demonstrates how the 'w' key toggles whitespace ignore mode.

Usage:
    python3 demo/demo_diff_viewer_whitespace.py
    
    Press 'w' to toggle whitespace ignore mode
    Press 'q' or Enter to quit
"""

import sys
import os
from pathlib import Path as StdPath

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_diff_viewer import view_diff
from ttk import get_default_renderer


def create_demo_files():
    """Create demo files with whitespace differences"""
    demo_dir = StdPath(__file__).parent / 'temp_diff_demo'
    demo_dir.mkdir(exist_ok=True)
    
    file1 = demo_dir / 'whitespace_original.py'
    file2 = demo_dir / 'whitespace_modified.py'
    
    # File 1: Normal formatting
    content1 = """def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def calculate_average(numbers):
    if not numbers:
        return 0
    return calculate_sum(numbers) / len(numbers)

def main():
    data = [1, 2, 3, 4, 5]
    print(f"Sum: {calculate_sum(data)}")
    print(f"Average: {calculate_average(data)}")
"""
    
    # File 2: Same content but with different whitespace
    # - Extra spaces around operators
    # - Tabs instead of spaces in some places
    # - Extra spaces at end of lines
    content2 = """def calculate_sum(numbers):
    total  =  0  
    for num in numbers:
\t\ttotal  +=  num
    return total

def calculate_average(numbers):
    if not numbers:  
        return 0
    return calculate_sum(numbers)  /  len(numbers)

def main():
    data  =  [1, 2, 3, 4, 5]
    print(f"Sum: {calculate_sum(data)}")  
    print(f"Average: {calculate_average(data)}")
"""
    
    file1.write_text(content1)
    file2.write_text(content2)
    
    return Path(file1), Path(file2)


def cleanup_demo_files():
    """Clean up demo files"""
    demo_dir = StdPath(__file__).parent / 'temp_diff_demo'
    if demo_dir.exists():
        for file in demo_dir.iterdir():
            try:
                file.unlink()
            except OSError as e:
                print(f"Warning: Could not delete {file}: {e}")
        try:
            demo_dir.rmdir()
        except OSError as e:
            print(f"Warning: Could not remove directory {demo_dir}: {e}")


def main():
    """Run the demo"""
    print("=" * 70)
    print("Diff Viewer - Whitespace Ignore Mode Demo")
    print("=" * 70)
    print()
    print("This demo shows two Python files with identical logic but different")
    print("whitespace formatting:")
    print()
    print("  - Extra spaces around operators")
    print("  - Tabs vs spaces")
    print("  - Trailing whitespace")
    print()
    print("Controls:")
    print("  w - Toggle whitespace ignore mode (watch the status bar!)")
    print("  q or Enter - Quit")
    print()
    print("Notice how pressing 'w' changes which lines are highlighted as different.")
    print("With whitespace ignore ON, only real content differences are shown.")
    print()
    input("Press Enter to start the demo...")
    
    try:
        # Create demo files
        file1, file2 = create_demo_files()
        
        # Get renderer and run diff viewer
        renderer = get_default_renderer()
        view_diff(renderer, file1, file2)
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error running demo: {e}")
    finally:
        # Clean up
        cleanup_demo_files()
        print("\nDemo complete!")


if __name__ == '__main__':
    main()
