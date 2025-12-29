#!/usr/bin/env python3
"""
Demo: Clipboard Copy Name/Path Feature

This demo demonstrates the new clipboard copy features that allow users to:
1. Copy file name(s) of selected files to the system clipboard
2. Copy full path(s) of selected files to the system clipboard

These features are accessible from the Edit menu in desktop mode:
- Edit > Copy Name(s) (Cmd+Shift+C)
- Edit > Copy Full Path(s) (Cmd+Shift+P)

The features work with:
- Single selected file
- Multiple selected files
- Focused file when nothing is selected

Usage:
    python demo/demo_clipboard_copy.py

Note: This demo only works in desktop mode (CoreGraphics backend) as clipboard
operations are not available in terminal mode.
"""

import sys
import os

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_main import FileManager
from tfm_backend_selector import select_backend


def main():
    """Run the clipboard copy demo"""
    
    print("=" * 80)
    print("TFM Clipboard Copy Feature Demo")
    print("=" * 80)
    print()
    print("This demo shows the new clipboard copy features:")
    print()
    print("1. Copy Name(s) - Copies file names to clipboard")
    print("   - Menu: Edit > Copy Name(s)")
    print("   - Shortcut: Cmd+Shift+C (macOS) / Ctrl+Shift+C (other)")
    print()
    print("2. Copy Full Path(s) - Copies full paths to clipboard")
    print("   - Menu: Edit > Copy Full Path(s)")
    print("   - Shortcut: Cmd+Shift+P (macOS) / Ctrl+Shift+P (other)")
    print()
    print("How to use:")
    print("  1. Select one or more files using Space or Shift+Space")
    print("     OR just navigate to a file without selecting")
    print("  2. Use the menu or keyboard shortcut to copy")
    print("  3. Paste the result in any text editor to see the copied content")
    print()
    print("Features:")
    print("  - Works with single or multiple selected files")
    print("  - Uses focused file if nothing is selected")
    print("  - Menu items are always enabled (no need to select first)")
    print("  - Only available in desktop mode (not terminal mode)")
    print()
    print("=" * 80)
    print()
    print("Starting TFM in desktop mode...")
    print()
    
    # Force desktop mode for this demo
    backend = select_backend(force_desktop=True)
    
    if not backend:
        print("Error: Could not initialize desktop backend")
        print("This demo requires desktop mode (CoreGraphics backend)")
        return 1
    
    # Check clipboard support
    if not backend.supports_clipboard():
        print("Error: Clipboard not supported on this backend")
        return 1
    
    print("Desktop mode initialized with clipboard support")
    print()
    print("Try the following:")
    print("  1. Navigate to a directory with files")
    print("  2. Select some files with Space")
    print("  3. Press Cmd+Shift+C to copy file names")
    print("  4. Open a text editor and paste to see the result")
    print("  5. Press Cmd+Shift+P to copy full paths")
    print("  6. Paste again to see the full paths")
    print()
    
    # Create and run file manager
    try:
        fm = FileManager(backend)
        fm.run()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
