#!/usr/bin/env python3
"""
Demo: Text Diff Viewer

This demo showcases the side-by-side text diff viewer feature.
It creates two sample files with differences and displays them.
"""

import sys
import os
from pathlib import Path as StdPath

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_diff_viewer import view_diff


def create_demo_files():
    """Create demo files with differences"""
    demo_dir = StdPath(__file__).parent / 'temp_diff_demo'
    demo_dir.mkdir(exist_ok=True)
    
    # Create first file
    file1 = demo_dir / 'original.py'
    file1_content = """#!/usr/bin/env python3
\"\"\"
Original Python Script
\"\"\"

def calculate_sum(a, b):
    \"\"\"Calculate sum of two numbers\"\"\"
    return a + b

def calculate_product(a, b):
    \"\"\"Calculate product of two numbers\"\"\"
    return a * b

def main():
    x = 10
    y = 20
    print(f"Sum: {calculate_sum(x, y)}")
    print(f"Product: {calculate_product(x, y)}")

if __name__ == '__main__':
    main()
"""
    file1.write_text(file1_content)
    
    # Create second file with modifications
    file2 = demo_dir / 'modified.py'
    file2_content = """#!/usr/bin/env python3
\"\"\"
Modified Python Script - Enhanced Version
\"\"\"

def calculate_sum(a, b):
    \"\"\"Calculate sum of two numbers\"\"\"
    result = a + b
    return result

def calculate_difference(a, b):
    \"\"\"Calculate difference of two numbers\"\"\"
    return a - b

def calculate_product(a, b):
    \"\"\"Calculate product of two numbers\"\"\"
    return a * b

def main():
    x = 10
    y = 20
    z = 5
    print(f"Sum: {calculate_sum(x, y)}")
    print(f"Difference: {calculate_difference(x, z)}")
    print(f"Product: {calculate_product(x, y)}")

if __name__ == '__main__':
    main()
"""
    file2.write_text(file2_content)
    
    return file1, file2


def main():
    """Run the diff viewer demo"""
    print("TFM Diff Viewer Demo")
    print("=" * 60)
    print()
    print("This demo will show a side-by-side comparison of two files:")
    print("  - original.py (left)")
    print("  - modified.py (right)")
    print()
    print("Changes include:")
    print("  - Modified docstring")
    print("  - Enhanced calculate_sum function")
    print("  - Replaced calculate_product with calculate_difference")
    print("  - Added new variable in main()")
    print()
    print("Controls:")
    print("  ↑/↓     - Scroll up/down")
    print("  ←/→     - Scroll left/right")
    print("  PgUp/Dn - Page up/down")
    print("  q/Enter - Quit")
    print()
    input("Press Enter to start the diff viewer...")
    
    # Create demo files
    file1, file2 = create_demo_files()
    
    try:
        # Import renderer
        from ttk.curses_renderer import CursesRenderer
        
        # Create renderer
        renderer = CursesRenderer()
        
        try:
            # View the diff
            view_diff(renderer, Path(file1), Path(file2))
        finally:
            renderer.cleanup()
        
        print("\nDemo completed!")
        print(f"Demo files created in: {file1.parent}")
        
    except ImportError as e:
        print(f"Error: Could not import required modules: {e}")
        print("Make sure TTK is properly installed")
    except Exception as e:
        print(f"Error running demo: {e}")
    finally:
        # Clean up demo files
        cleanup = input("\nDelete demo files? (y/n): ")
        if cleanup.lower() == 'y':
            try:
                file1.unlink()
                file2.unlink()
                file1.parent.rmdir()
                print("Demo files deleted")
            except Exception as e:
                print(f"Error cleaning up: {e}")


if __name__ == '__main__':
    main()
