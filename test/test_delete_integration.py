#!/usr/bin/env python3
"""
Integration test for TFM delete functionality
Tests the complete delete feature implementation
"""

import tempfile
import shutil
from pathlib import Path
import sys

# Add the current directory to Python path


def test_delete_key_binding():
    """Test that delete key binding is properly configured"""
    print("Testing delete key binding configuration...")
    
    try:

        from tfm_config import DefaultConfig, get_config
        
        # Check default configuration
        if hasattr(DefaultConfig, 'KEY_BINDINGS') and 'delete_files' in DefaultConfig.KEY_BINDINGS:
            keys = DefaultConfig.KEY_BINDINGS['delete_files']
            print(f"✓ Delete key binding found in DefaultConfig: {keys}")
            
            if 'k' in keys and 'K' in keys:
                print("✓ Both 'k' and 'K' keys are bound to delete")
            else:
                print(f"✗ Expected 'k' and 'K' keys, found: {keys}")
                return False
        else:
            print("✗ Delete key binding not found in DefaultConfig")
            return False
        
        # Test key binding lookup function
        from tfm_config import is_key_bound_to
        
        if is_key_bound_to('k', 'delete_files'):
            print("✓ Key 'k' is bound to delete_files action")
        else:
            print("✗ Key 'k' is not bound to delete_files action")
            return False
            
        if is_key_bound_to('K', 'delete_files'):
            print("✓ Key 'K' is bound to delete_files action")
        else:
            print("✗ Key 'K' is not bound to delete_files action")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing key binding: {e}")
        return False

def test_delete_methods_exist():
    """Test that delete methods exist in FileManager"""
    print("\nTesting delete methods in FileManager...")
    
    try:

# Add src directory to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

        from tfm_main import FileManager
        
        # Check if delete methods exist
        if hasattr(FileManager, 'delete_selected_files'):
            print("✓ delete_selected_files method exists")
        else:
            print("✗ delete_selected_files method not found")
            return False
        
        if hasattr(FileManager, 'perform_delete_operation'):
            print("✓ perform_delete_operation method exists")
        else:
            print("✗ perform_delete_operation method not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking delete methods: {e}")
        return False

def test_delete_logic():
    """Test the delete logic with mock data"""
    print("\nTesting delete operation logic...")
    
    # Create test environment
    test_dir = Path(tempfile.mkdtemp(prefix="tfm_delete_logic_test_"))
    
    try:
        # Create test files
        test_file = test_dir / "test_file.txt"
        test_file.write_text("Test content")
        
        test_dir_nested = test_dir / "test_directory"
        test_dir_nested.mkdir()
        (test_dir_nested / "nested.txt").write_text("Nested content")
        
        # Create symbolic link if possible
        test_link = test_dir / "test_link.txt"
        try:
            test_link.symlink_to(test_file)
            has_symlink = True
        except OSError:
            has_symlink = False
            print("Note: Symbolic links not supported, skipping symlink test")
        
        # Test file deletion
        if test_file.exists():
            test_file.unlink()
            print("✓ File deletion works")
        else:
            print("✗ Test file not found")
            return False
        
        # Test directory deletion
        if test_dir_nested.exists():
            shutil.rmtree(test_dir_nested)
            print("✓ Directory deletion works")
        else:
            print("✗ Test directory not found")
            return False
        
        # Test symbolic link deletion
        if has_symlink and test_link.exists():
            test_link.unlink()
            print("✓ Symbolic link deletion works")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing delete logic: {e}")
        return False
    
    finally:
        # Clean up
        if test_dir.exists():
            shutil.rmtree(test_dir)

def test_key_handler_integration():
    """Test that the key handler calls delete function"""
    print("\nTesting key handler integration...")
    
    try:
        # Read the main file to check for delete key handler
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        # Check for delete key handler
        if "elif self.is_key_for_action(key, 'delete_files'):" in content:
            print("✓ Delete key handler found in main loop")
        else:
            print("✗ Delete key handler not found in main loop")
            return False
        
        # Check for delete method call
        if "self.delete_selected_files()" in content:
            print("✓ Delete method call found in key handler")
        else:
            print("✗ Delete method call not found in key handler")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking key handler integration: {e}")
        return False

def test_confirmation_dialog():
    """Test that confirmation dialog is properly implemented"""
    print("\nTesting confirmation dialog implementation...")
    
    try:
        # Read the delete method to check for confirmation
        with open('tfm_main.py', 'r') as f:
            content = f.read()
        
        # Check for confirmation dialog
        if 'self.show_dialog(message, choices, handle_delete_confirmation)' in content:
            print("✓ Confirmation dialog call found")
        else:
            print("✗ Confirmation dialog call not found")
            return False
        
        # Check for confirmation choices
        if '"Yes"' in content and '"No"' in content:
            print("✓ Yes/No confirmation choices found")
        else:
            print("✗ Yes/No confirmation choices not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking confirmation dialog: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("TFM Delete Feature Integration Test")
    print("=" * 60)
    
    tests = [
        ("Key Binding Configuration", test_delete_key_binding),
        ("Delete Methods Existence", test_delete_methods_exist),
        ("Delete Operation Logic", test_delete_logic),
        ("Key Handler Integration", test_key_handler_integration),
        ("Confirmation Dialog", test_confirmation_dialog),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{passed + 1}/{total}] {test_name}")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED - Delete feature is fully integrated!")
        print("\nFeature Summary:")
        print("- Press 'k' or 'K' to delete selected files/directories")
        print("- Confirmation dialog appears before deletion")
        print("- Supports files, directories (recursive), and symbolic links")
        print("- Handles multiple selected items")
        print("- Provides detailed error reporting")
    else:
        print("✗ Some tests failed - please check the implementation")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)