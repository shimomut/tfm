#!/usr/bin/env python3
"""
Demo script showing command line directory specification functionality

This demo shows how to use the --left and --right command line arguments
to specify initial directories for TFM panes.
"""

import os
import sys
import tempfile
from pathlib import Path

def create_demo_directories():
    """Create temporary demo directories with sample content"""
    # Create a temporary directory structure for demonstration
    temp_base = Path(tempfile.mkdtemp(prefix='tfm_demo_'))
    
    # Create left demo directory with some files
    left_dir = temp_base / 'left_pane_demo'
    left_dir.mkdir()
    
    # Create some sample files in left directory
    (left_dir / 'readme.txt').write_text('This is the left pane directory\nContains project files')
    (left_dir / 'config.json').write_text('{"setting": "value"}')
    (left_dir / 'script.py').write_text('print("Hello from left pane")')
    
    # Create a subdirectory
    subdir = left_dir / 'subdirectory'
    subdir.mkdir()
    (subdir / 'nested_file.txt').write_text('File in subdirectory')
    
    # Create right demo directory with different content
    right_dir = temp_base / 'right_pane_demo'
    right_dir.mkdir()
    
    # Create some sample files in right directory
    (right_dir / 'data.csv').write_text('name,value\ntest,123\nexample,456')
    (right_dir / 'notes.md').write_text('# Notes\n\nThis is the right pane directory')
    (right_dir / 'backup.tar.gz').write_text('fake archive content')
    
    # Create another subdirectory
    backup_dir = right_dir / 'backups'
    backup_dir.mkdir()
    (backup_dir / 'old_file.bak').write_text('Backup file content')
    
    return left_dir, right_dir, temp_base

def print_demo_info():
    """Print information about the demo"""
    print("TFM Command Line Directory Demo")
    print("=" * 40)
    print()
    print("This demo shows how to use --left and --right arguments to specify")
    print("initial directories for TFM panes.")
    print()
    print("Usage examples:")
    print("  python tfm.py --left /path/to/left --right /path/to/right")
    print("  python tfm.py --left .")
    print("  python tfm.py --right /home/user/documents")
    print("  python tfm.py --left ./src --right ./test")
    print()

def main():
    """Main demo function"""
    print_demo_info()
    
    # Create demo directories
    left_dir, right_dir, temp_base = create_demo_directories()
    
    print(f"Created demo directories:")
    print(f"  Left pane:  {left_dir}")
    print(f"  Right pane: {right_dir}")
    print()
    
    print("Demo directory contents:")
    print()
    print("Left pane directory:")
    for item in sorted(left_dir.rglob('*')):
        if item.is_file():
            rel_path = item.relative_to(left_dir)
            print(f"  📄 {rel_path}")
        elif item.is_dir() and item != left_dir:
            rel_path = item.relative_to(left_dir)
            print(f"  📁 {rel_path}/")
    
    print()
    print("Right pane directory:")
    for item in sorted(right_dir.rglob('*')):
        if item.is_file():
            rel_path = item.relative_to(right_dir)
            print(f"  📄 {rel_path}")
        elif item.is_dir() and item != right_dir:
            rel_path = item.relative_to(right_dir)
            print(f"  📁 {rel_path}/")
    
    print()
    print("To test with TFM, run:")
    print(f"  python tfm.py --left '{left_dir}' --right '{right_dir}'")
    print()
    print("Features:")
    print("  • If directories don't exist, TFM falls back to defaults")
    print("  • Relative paths are supported (e.g., --left . --right ..)")
    print("  • Can be combined with other options like --remote-log-port")
    print("  • Command line directories override saved history/state")
    print("  • Only the specified pane(s) ignore history - others restore normally")
    print()
    print("History Override Behavior:")
    print("  • --left specified: Left pane uses command line path, ignores history")
    print("  • --right specified: Right pane uses command line path, ignores history") 
    print("  • Both specified: Both panes use command line paths, ignore history")
    print("  • Neither specified: Both panes restore from saved history (normal behavior)")
    print()
    print(f"Demo files will remain in: {temp_base}")
    print("You can delete this directory when done testing.")

if __name__ == '__main__':
    main()