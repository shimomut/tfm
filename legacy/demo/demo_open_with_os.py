#!/usr/bin/env python3
"""
Demo: Open with OS Default Application

This demo shows the "Open with OS" feature that opens files using the
operating system's default file association (Command+Enter).

Features demonstrated:
- Opening files with OS default application
- Works with selected files or focused file
- Cross-platform support (macOS, Linux, Windows)
- Menu item: File > Open with Default App
- Keyboard shortcut: Command+Enter (macOS) / Ctrl+Enter (Linux/Windows)

Usage:
    python3 demo/demo_open_with_os.py

Test scenarios:
1. Focus on a file and press Command+Enter to open with OS default app
2. Select multiple files and press Command+Enter to open all
3. Use File menu > Open with Default App
4. Compare with regular Open (Command+O) which uses TFM's file associations
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_main import main
from ttk.backends.curses_backend import CursesBackend

def create_test_files():
    """Create test files in a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix='tfm_demo_open_default_'))
    
    # Create various file types
    (temp_dir / 'document.txt').write_text('This is a text document.\n')
    (temp_dir / 'README.md').write_text('# README\n\nThis is a markdown file.\n')
    (temp_dir / 'script.py').write_text('#!/usr/bin/env python3\nprint("Hello, World!")\n')
    (temp_dir / 'data.json').write_text('{"name": "test", "value": 123}\n')
    
    # Create a subdirectory
    subdir = temp_dir / 'subdirectory'
    subdir.mkdir()
    (subdir / 'nested.txt').write_text('Nested file content.\n')
    
    return temp_dir

if __name__ == '__main__':
    print("=" * 70)
    print("TFM Demo: Open with OS Default Application")
    print("=" * 70)
    print()
    print("This demo shows the 'Open with OS' feature.")
    print()
    print("Key Features:")
    print("  • Command+Enter (macOS) / Ctrl+Enter (Linux/Windows)")
    print("  • Opens files with OS default application")
    print("  • Works with selected files or focused file")
    print("  • Menu: File > Open with Default App")
    print()
    print("Comparison:")
    print("  • Command+O: Uses TFM's file associations (configurable)")
    print("  • Command+Enter: Uses OS default associations (system-wide)")
    print()
    print("Test Instructions:")
    print("  1. Focus on a file and press Command+Enter")
    print("  2. Select multiple files (Space) and press Command+Enter")
    print("  3. Try File menu > Open with Default App")
    print("  4. Compare with regular Open (Command+O)")
    print()
    print("Creating test files...")
    
    # Create test directory
    test_dir = create_test_files()
    print(f"Test directory: {test_dir}")
    print()
    print("Starting TFM...")
    print("=" * 70)
    print()
    
    # Start TFM with test directory
    renderer = CursesBackend()
    try:
        main(renderer, left_dir=str(test_dir), right_dir=str(test_dir.parent))
    finally:
        # Cleanup
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"\nCleaned up test directory: {test_dir}")
        except Exception as e:
            print(f"\nWarning: Could not clean up test directory: {e}")
