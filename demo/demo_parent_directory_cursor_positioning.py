"""
Demo: Parent Directory Cursor Positioning

This demo demonstrates the improved behavior when navigating to parent directories.
When you press Backspace (or use LEFT/RIGHT arrow in the appropriate pane), 
the cursor will automatically focus on the directory you just came from.

Instructions:
1. Navigate into a subdirectory (press Enter on a directory)
2. Press Backspace to go back to parent
3. Notice the cursor is now on the directory you just left
4. Try with LEFT arrow (in left pane) or RIGHT arrow (in right pane)

This makes navigation more intuitive and helps you keep track of where you were.
"""

import sys
from pathlib import Path

# Add src and ttk to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'ttk'))

from tfm_backend_selector import select_backend

def main():
    """Run the file manager demo."""
    print(__doc__)
    print("\nStarting TFM...")
    print("Navigate into directories and press Backspace to see the improved cursor positioning.")
    print()
    
    # Select and initialize backend
    backend = select_backend()
    
    try:
        # Import after backend is selected
        from tfm_main import FileManager
        
        # Create and run file manager
        fm = FileManager(backend)
        fm.run()
        
    finally:
        backend.cleanup()

if __name__ == '__main__':
    main()
