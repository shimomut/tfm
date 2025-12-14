#!/usr/bin/env python3
"""
Demo: Text Viewer TAB Character Handling

This demo shows how the text viewer properly handles TAB characters
when using horizontal scrolling.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path


def create_demo_file():
    """Create a demo file with various TAB characters"""
    demo_file = Path("temp/demo_tabs.txt")
    demo_file.parent.mkdir(parents=True, exist_ok=True)
    
    content = """Text Viewer TAB Handling Demo
=============================

This file demonstrates how the text viewer handles TAB characters.

Basic TAB usage:
	- This line starts with a TAB
	- TABs are expanded to spaces (default: 4 spaces per TAB)
	- This allows proper horizontal scrolling

Column alignment with TABs:
Name	Age	City	Country
Alice	30	NYC	USA
Bob	25	London	UK
Charlie	35	Tokyo	Japan

Code with TABs (Python):
def example():
	if True:
		print("TABs are expanded")
		for i in range(10):
			print(i)

Mixed TABs and spaces:
	One TAB at start
		Two TABs at start
			Three TABs at start

TAB stops (with tab_width=4):
a	b	c	d	e
ab	cd	ef	gh	ij
abc	def	ghi	jkl	mno

Try horizontal scrolling with arrow keys (← →) to see how TABs
are properly handled as expanded spaces!

Press 'q' or Enter to exit the viewer.
"""
    
    demo_file.write_text(content)
    return demo_file


def main():
    """Run the demo"""
    print("=" * 70)
    print("Text Viewer TAB Handling Demo")
    print("=" * 70)
    print()
    print("Creating demo file with TAB characters...")
    
    demo_file = create_demo_file()
    print(f"Created: {demo_file}")
    print()
    print("Features demonstrated:")
    print("  • TAB characters are expanded to spaces (default: 4 spaces per TAB)")
    print("  • TABs align to proper column positions (0, 4, 8, 12, ...)")
    print("  • Horizontal scrolling works correctly with expanded TABs")
    print("  • No display issues when scrolling through TAB-indented content")
    print()
    print("Controls:")
    print("  ← → : Horizontal scroll")
    print("  ↑ ↓ : Vertical scroll")
    print("  q   : Quit viewer")
    print()
    print("Opening text viewer...")
    print("=" * 70)
    
    # Import and run the text viewer
    try:
        from ttk.coregraphics_backend import CoreGraphicsBackend
        from tfm_text_viewer import view_text_file
        
        # Create renderer
        renderer = CoreGraphicsBackend()
        renderer.initialize()
        
        try:
            # View the file
            view_text_file(renderer, demo_file)
        finally:
            renderer.cleanup()
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if demo_file.exists():
            demo_file.unlink()
            print(f"\nCleaned up demo file: {demo_file}")


if __name__ == '__main__':
    main()
