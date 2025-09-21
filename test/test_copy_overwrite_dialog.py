#!/usr/bin/env python3
"""
Test for copy operation overwrite dialog issue
"""

import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_copy_dialog_flow():
    """Test the copy operation dialog flow to identify the issue"""
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source and destination directories
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files
        test_file = source_dir / "test.txt"
        test_file.write_text("source content")
        
        # Create conflicting file in destination
        dest_file = dest_dir / "test.txt"
        dest_file.write_text("destination content")
        
        print("Testing copy operation dialog flow...")
        print(f"Source file: {test_file}")
        print(f"Destination: {dest_dir}")
        print(f"Conflict exists: {dest_file.exists()}")
        
        # Simulate the copy operation logic
        files_to_copy = [test_file]
        
        # Step 1: Check for conflicts (this is what copy_files_to_directory does)
        conflicts = []
        for source_file in files_to_copy:
            dest_path = dest_dir / source_file.name
            if dest_path.exists():
                conflicts.append((source_file, dest_path))
        
        print(f"Conflicts detected: {len(conflicts)}")
        
        if conflicts:
            print("This is where the overwrite dialog should appear")
            print("The issue might be that the previous CONFIRM_COPY dialog")
            print("doesn't properly reset the dialog state before showing the overwrite dialog")
            
        return True


if __name__ == "__main__":
    test_copy_dialog_flow()