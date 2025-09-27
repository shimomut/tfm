#!/usr/bin/env python3
"""
Demo: JumpDialog Hidden Files Behavior

This demo shows how JumpDialog respects the show_hidden setting
when listing directories for navigation.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_jump_dialog import JumpDialog
from tfm_file_operations import FileOperations


def create_test_directory_structure():
    """Create a test directory structure with hidden and visible directories"""
    temp_dir = Path(tempfile.mkdtemp(prefix="tfm_jump_demo_"))
    
    print(f"Creating test directory structure in: {temp_dir}")
    
    # Create regular directories
    (temp_dir / "documents").mkdir()
    (temp_dir / "projects").mkdir()
    (temp_dir / "downloads").mkdir()
    (temp_dir / "documents" / "work").mkdir()
    (temp_dir / "documents" / "personal").mkdir()
    (temp_dir / "projects" / "python").mkdir()
    (temp_dir / "projects" / "javascript").mkdir()
    
    # Create hidden directories (common ones)
    (temp_dir / ".git").mkdir()
    (temp_dir / ".vscode").mkdir()
    (temp_dir / ".config").mkdir()
    (temp_dir / ".cache").mkdir()
    (temp_dir / "projects" / ".git").mkdir()
    (temp_dir / "projects" / "python" / ".venv").mkdir()
    (temp_dir / ".config" / "user_settings").mkdir()
    
    print("\nDirectory structure created:")
    print("Visible directories:")
    print("  - documents/")
    print("    - work/")
    print("    - personal/")
    print("  - projects/")
    print("    - python/")
    print("    - javascript/")
    print("  - downloads/")
    
    print("\nHidden directories:")
    print("  - .git/")
    print("  - .vscode/")
    print("  - .config/")
    print("    - user_settings/")
    print("  - .cache/")
    print("  - projects/.git/")
    print("  - projects/python/.venv/")
    
    return temp_dir


def wait_for_scan_completion(jump_dialog, timeout=5.0):
    """Wait for directory scanning to complete"""
    start_time = time.time()
    while jump_dialog.searching and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    if jump_dialog.searching:
        print("Warning: Scan did not complete within timeout")
        return False
    return True


def demo_hidden_files_behavior():
    """Demonstrate JumpDialog behavior with hidden files setting"""
    print("=" * 60)
    print("TFM JumpDialog Hidden Files Behavior Demo")
    print("=" * 60)
    
    # Create test directory structure
    test_dir = create_test_directory_structure()
    
    try:
        # Create mock config
        config = Mock()
        config.MAX_JUMP_DIRECTORIES = 1000
        
        # Create JumpDialog instance
        jump_dialog = JumpDialog(config)
        
        print("\n" + "=" * 60)
        print("TEST 1: show_hidden = False from visible root")
        print("=" * 60)
        
        # Test with show_hidden = False
        file_ops = FileOperations(config)
        file_ops.show_hidden = False
        
        print(f"Setting show_hidden = {file_ops.show_hidden}")
        print(f"Scanning from visible root: {test_dir}")
        
        jump_dialog.show(test_dir, file_ops)
        
        if wait_for_scan_completion(jump_dialog):
            print(f"Scan completed. Found {len(jump_dialog.directories)} directories.")
            
            print("\nDirectories found:")
            for i, directory in enumerate(jump_dialog.directories, 1):
                rel_path = directory.relative_to(test_dir)
                print(f"  {i:2d}. {rel_path}")
            
            # Check for hidden directories
            found_dirs = [str(d) for d in jump_dialog.directories]
            hidden_found = any('.git' in d or '.vscode' in d or '.config' in d or '.cache' in d or '.venv' in d for d in found_dirs)
            
            if hidden_found:
                print("\n❌ ERROR: Hidden directories were found when they should be filtered!")
            else:
                print("\n✅ SUCCESS: Hidden directories were properly filtered out.")
        
        jump_dialog.exit()
        
        print("\n" + "=" * 60)
        print("TEST 2: show_hidden = False from hidden root")
        print("=" * 60)
        
        # Test scanning from within a hidden directory
        hidden_root = test_dir / ".config"
        print(f"Setting show_hidden = {file_ops.show_hidden}")
        print(f"Scanning from hidden root: {hidden_root}")
        
        jump_dialog.show(hidden_root, file_ops)
        
        if wait_for_scan_completion(jump_dialog):
            print(f"Scan completed. Found {len(jump_dialog.directories)} directories.")
            
            print("\nDirectories found:")
            for i, directory in enumerate(jump_dialog.directories, 1):
                try:
                    rel_path = directory.relative_to(hidden_root)
                    print(f"  {i:2d}. {rel_path}")
                except ValueError:
                    print(f"  {i:2d}. {directory}")
            
            # When scanning from hidden root, should find subdirectories
            if len(jump_dialog.directories) > 1:  # More than just the root
                print("\n✅ SUCCESS: Subdirectories within hidden context are accessible.")
            else:
                print("\n⚠️  INFO: No subdirectories found in hidden directory.")
        
        jump_dialog.exit()
        
        print("\n" + "=" * 60)
        print("TEST 3: show_hidden = True")
        print("=" * 60)
        
        # Test with show_hidden = True
        file_ops.show_hidden = True
        
        print(f"Setting show_hidden = {file_ops.show_hidden}")
        print("Starting directory scan...")
        
        jump_dialog.show(test_dir, file_ops)
        
        if wait_for_scan_completion(jump_dialog):
            print(f"Scan completed. Found {len(jump_dialog.directories)} directories.")
            
            print("\nDirectories found:")
            visible_dirs = []
            hidden_dirs = []
            
            for directory in jump_dialog.directories:
                rel_path = directory.relative_to(test_dir)
                path_str = str(rel_path)
                
                # Check if any part of the path is hidden
                is_hidden = any(part.startswith('.') and part not in ['.', '..'] for part in rel_path.parts)
                
                if is_hidden:
                    hidden_dirs.append(path_str)
                else:
                    visible_dirs.append(path_str)
            
            print(f"\nVisible directories ({len(visible_dirs)}):")
            for i, dir_path in enumerate(sorted(visible_dirs), 1):
                print(f"  {i:2d}. {dir_path}")
            
            print(f"\nHidden directories ({len(hidden_dirs)}):")
            for i, dir_path in enumerate(sorted(hidden_dirs), 1):
                print(f"  {i:2d}. {dir_path}")
            
            if hidden_dirs:
                print("\n✅ SUCCESS: Hidden directories were included as expected.")
            else:
                print("\n❌ ERROR: No hidden directories found when they should be included!")
        
        jump_dialog.exit()
        
        print("\n" + "=" * 60)
        print("TEST 4: Fallback behavior (no file_operations reference)")
        print("=" * 60)
        
        print("Testing fallback behavior without file_operations reference...")
        
        jump_dialog.show(test_dir)  # No file_operations parameter
        
        if wait_for_scan_completion(jump_dialog):
            print(f"Scan completed. Found {len(jump_dialog.directories)} directories.")
            
            found_dirs = [str(d) for d in jump_dialog.directories]
            hidden_found = any('.git' in d or '.vscode' in d or '.config' in d or '.cache' in d or '.venv' in d for d in found_dirs)
            
            if hidden_found:
                print("✅ SUCCESS: Fallback behavior includes all directories (including hidden).")
            else:
                print("⚠️  WARNING: Fallback behavior may not be working as expected.")
        
        jump_dialog.exit()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("The JumpDialog now respects the show_hidden setting with smart context awareness:")
        print("• When show_hidden = False from visible root: Hidden directories are filtered out")
        print("• When show_hidden = False from hidden root: Subdirectories are accessible")
        print("• When show_hidden = True: All directories are included")
        print("• Fallback behavior: Includes all directories when no file_operations reference")
        print("\nThis allows navigation within hidden directories while still filtering them")
        print("when starting from visible directories.")
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\nCleaned up test directory: {test_dir}")


if __name__ == '__main__':
    demo_hidden_files_behavior()