#!/usr/bin/env python3
"""
Demo: Text Viewer Tab Width Feature

This demo showcases the ability to change tab width dynamically
in the text viewer. Press 't' to cycle through tab widths: 2, 4, 8.

The current tab width is displayed in the status bar as "TAB:n".
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_text_viewer import view_text_file
from tfm_path import Path
from ttk.curses_renderer import CursesRenderer


def create_demo_file():
    """Create a demo file with various tab indentation levels"""
    demo_file = "temp/demo_tab_width.py"
    os.makedirs("temp", exist_ok=True)
    
    content = '''#!/usr/bin/env python3
"""
Demo file with tab characters at various indentation levels.

Press 't' to cycle through tab widths: 2 → 4 → 8 → 2
The current tab width is shown in the status bar as "TAB:n"
"""

def outer_function():
	"""Function with tab indentation"""
	print("Outer function")
	
	def inner_function():
		"""Nested function with double tab indentation"""
		print("Inner function")
		
		if True:
			print("Triple tab indentation")
			
			for i in range(3):
				print(f"Quadruple tab: {i}")

class MyClass:
	"""Class with tab indentation"""
	
	def __init__(self):
		self.value = 42
		self.data = {
			'key1': 'value1',
			'key2': 'value2',
			'nested': {
				'deep': 'value'
			}
		}
	
	def method(self):
		"""Method with tab indentation"""
		if self.value > 0:
			return self.value * 2
		else:
			return 0

# Mixed indentation example
def mixed_example():
	x = 1	# Tab before comment
	y = 2	# Another tab
	z = x + y	# Yet another tab
	return z

# Try different tab widths to see how the alignment changes!
# Press 't' to cycle: 2 spaces → 4 spaces → 8 spaces → 2 spaces
'''
    
    with open(demo_file, 'w') as f:
        f.write(content)
    
    return demo_file


def main():
    """Run the tab width demo"""
    print("=" * 60)
    print("Text Viewer Tab Width Demo")
    print("=" * 60)
    print()
    print("This demo shows how to change tab width in the text viewer.")
    print()
    print("Key bindings:")
    print("  t - Cycle through tab widths (2 → 4 → 8 → 2)")
    print("  q - Quit viewer")
    print()
    print("The current tab width is displayed in the status bar.")
    print("Watch how the indentation changes as you press 't'!")
    print()
    print("Creating demo file with tab characters...")
    
    demo_file = create_demo_file()
    
    print(f"Demo file created: {demo_file}")
    print()
    print("Press Enter to open the text viewer...")
    input()
    
    try:
        # Open the demo file in the text viewer
        renderer = CursesRenderer()
        renderer.initialize()
        
        try:
            view_text_file(renderer, Path(demo_file))
        finally:
            renderer.cleanup()
        
        print("\nDemo completed!")
        print()
        print("What you should have seen:")
        print("- Initial tab width: 4 spaces")
        print("- Press 't' to change to 8 spaces (wider indentation)")
        print("- Press 't' again to change to 2 spaces (narrower indentation)")
        print("- Press 't' once more to cycle back to 4 spaces")
        print("- Status bar shows current tab width (e.g., 'TAB:4')")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up demo file
        if os.path.exists(demo_file):
            os.remove(demo_file)
            print(f"\nCleaned up demo file: {demo_file}")


if __name__ == "__main__":
    main()
