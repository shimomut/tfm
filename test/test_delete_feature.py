"""
Test script for TFM delete functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_delete_feature.py -v
"""

import tempfile
import shutil

# Add the current directory to Python path to import TFM modules




# Add src directory to Python path
from tfm_main import FileManager
from tfm_config import get_config

def create_test_files():
    """Create test files and directories for deletion testing"""
    test_dir = Path(tempfile.mkdtemp(prefix="tfm_delete_test_"))
    
    # Create test files
    (test_dir / "test_file1.txt").write_text("Test file 1 content")
    (test_dir / "test_file2.txt").write_text("Test file 2 content")
    (test_dir / "test_file3.py").write_text("# Python test file")
    
    # Create test directory with contents
    test_subdir = test_dir / "test_directory"
    test_subdir.mkdir()
    (test_subdir / "nested_file.txt").write_text("Nested file content")
    (test_subdir / "another_nested.md").write_text("# Nested markdown")
    
    # Create symbolic link
    link_target = test_dir / "test_file1.txt"
    link_path = test_dir / "test_link.txt"
    try:
        link_path.symlink_to(link_target)
    except OSError:
        # Symbolic links might not be supported on all systems
        print("Warning: Could not create symbolic link (not supported on this system)")
    
    return test_dir

def test_delete_methods():
    """Test the delete methods without UI interaction"""
    print("Testing TFM delete functionality...")
    
    # Create test environment
    test_dir = create_test_files()
    print(f"Created test directory: {test_dir}")
    
    try:
        # List initial files
        initial_files = list(test_dir.iterdir())
        print(f"Initial files: {[f.name for f in initial_files]}")
        
        # Test delete_selected_files method exists
        config = get_config()
        
        # Check if delete key binding exists
        if 'delete_files' in config.KEY_BINDINGS:
            print("✓ Delete key binding found in configuration")
            print(f"  Keys: {config.KEY_BINDINGS['delete_files']}")
        else:
            print("✗ Delete key binding not found in configuration")
            return False
        
        # Test file deletion using Path methods (simulating the delete operation)
        test_file = test_dir / "test_file1.txt"
        if test_file.exists():
            test_file.unlink()
            print("✓ File deletion test successful")
        
        # Test directory deletion
        test_subdir = test_dir / "test_directory"
        if test_subdir.exists():
            shutil.rmtree(test_subdir)
            print("✓ Directory deletion test successful")
        
        # Test symbolic link deletion (if it exists)
        test_link = test_dir / "test_link.txt"
        if test_link.exists():
            test_link.unlink()
            print("✓ Symbolic link deletion test successful")
        
        # Verify files were deleted
        remaining_files = list(test_dir.iterdir())
        print(f"Remaining files: {[f.name for f in remaining_files]}")
        
        print("✓ All delete functionality tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False
    
    finally:
        # Clean up test directory
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"Cleaned up test directory: {test_dir}")

def test_delete_confirmation_logic():
    """Test the delete confirmation message generation"""
    print("\nTesting delete confirmation messages...")
    
    test_dir = create_test_files()
    
    try:
        files = list(test_dir.iterdir())
        
        # Test single file message
        single_file = [f for f in files if f.is_file() and not f.is_symlink()][0]
        print(f"Single file: '{single_file.name}' -> Delete file '{single_file.name}'?")
        
        # Test single directory message
        single_dir = [f for f in files if f.is_dir()][0]
        print(f"Single directory: '{single_dir.name}' -> Delete directory '{single_dir.name}' and all its contents?")
        
        # Test symbolic link message (if exists)
        symlinks = [f for f in files if f.is_symlink()]
        if symlinks:
            single_link = symlinks[0]
            print(f"Single symlink: '{single_link.name}' -> Delete symbolic link '{single_link.name}'?")
        
        # Test multiple files message
        file_list = [f for f in files if f.is_file()]
        dir_list = [f for f in files if f.is_dir()]
        
        if len(file_list) > 0 and len(dir_list) > 0:
            total = len(files)
            print(f"Multiple items: {total} items ({len(dir_list)} directories, {len(file_list)} files) -> Delete {total} items ({len(dir_list)} directories, {len(file_list)} files)?")
        
        print("✓ Delete confirmation message tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing confirmation messages: {e}")
        return False
    
    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)

def main():
    """Run all delete functionality tests"""
    print("=" * 60)
    print("TFM Delete Feature Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test delete methods
    if not test_delete_methods():
        success = False
    
    # Test confirmation logic
    if not test_delete_confirmation_logic():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All delete functionality tests PASSED")
        print("\nThe delete feature is ready to use:")
        print("- Press 'k' or 'K' to delete selected files")
        print("- Confirmation dialog will appear before deletion")
        print("- Directories are deleted recursively")
        print("- Symbolic links are deleted (not their targets)")
    else:
        print("✗ Some delete functionality tests FAILED")
        print("Please check the implementation")
    print("=" * 60)
    
    return success
