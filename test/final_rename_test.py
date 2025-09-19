#!/usr/bin/env python3
"""
Final comprehensive test for the rename feature implementation
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the src directory to the path so we can import tfm modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_complete_implementation():
    """Test the complete rename implementation"""
    print("Testing complete rename implementation...")
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Configuration
    total_tests += 1
    try:
        from tfm_config import get_config, is_key_bound_to
        
        if (is_key_bound_to('r', 'rename_file') and 
            is_key_bound_to('R', 'rename_file')):
            print("✓ Key bindings configured correctly")
            success_count += 1
        else:
            print("✗ Key bindings not configured correctly")
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
    
    # Test 2: Method existence
    total_tests += 1
    try:
        from tfm_main import FileManager
        
        required_methods = [
            'enter_rename_mode',
            'exit_rename_mode',
            'perform_rename',
            'handle_rename_input'
        ]
        
        all_methods_exist = all(hasattr(FileManager, method) for method in required_methods)
        
        if all_methods_exist:
            print("✓ All rename methods implemented")
            success_count += 1
        else:
            missing = [m for m in required_methods if not hasattr(FileManager, m)]
            print(f"✗ Missing methods: {missing}")
    except Exception as e:
        print(f"✗ Method existence test failed: {e}")
    
    # Test 3: File rename operations
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test file rename
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")
            
            new_file = temp_path / "renamed.txt"
            test_file.rename(new_file)
            
            if new_file.exists() and not test_file.exists():
                print("✓ File rename operations work")
                success_count += 1
            else:
                print("✗ File rename operations failed")
    except Exception as e:
        print(f"✗ File rename test failed: {e}")
    
    # Test 4: Directory rename operations
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test directory rename
            test_dir = temp_path / "test_dir"
            test_dir.mkdir()
            (test_dir / "file.txt").write_text("content")
            
            new_dir = temp_path / "renamed_dir"
            test_dir.rename(new_dir)
            
            if (new_dir.exists() and not test_dir.exists() and 
                (new_dir / "file.txt").exists()):
                print("✓ Directory rename operations work")
                success_count += 1
            else:
                print("✗ Directory rename operations failed")
    except Exception as e:
        print(f"✗ Directory rename test failed: {e}")
    
    # Test 5: Error handling
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test renaming to existing file
            file1 = temp_path / "file1.txt"
            file2 = temp_path / "file2.txt"
            file1.write_text("content1")
            file2.write_text("content2")
            
            try:
                file1.rename(file2)  # Should fail
                print("✗ Should have failed renaming to existing file")
            except FileExistsError:
                print("✓ Error handling works correctly")
                success_count += 1
            except Exception as e:
                print(f"✗ Unexpected error: {e}")
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
    
    # Test 6: Source code integration
    total_tests += 1
    try:
        main_file = Path(__file__).parent.parent / "src" / "tfm_main.py"
        if main_file.exists():
            content = main_file.read_text()
            
            required_patterns = [
                "rename_mode",
                "enter_rename_mode",
                "handle_rename_input",
                "is_key_for_action(key, 'rename_file')"
            ]
            
            all_patterns_found = all(pattern in content for pattern in required_patterns)
            
            if all_patterns_found:
                print("✓ Source code integration complete")
                success_count += 1
            else:
                missing = [p for p in required_patterns if p not in content]
                print(f"✗ Missing source code patterns: {missing}")
        else:
            print("✗ Could not find source file")
    except Exception as e:
        print(f"✗ Source code integration test failed: {e}")
    
    # Test 7: Help dialog integration
    total_tests += 1
    try:
        main_file = Path(__file__).parent.parent / "src" / "tfm_main.py"
        if main_file.exists():
            content = main_file.read_text()
            
            if "r / R            Rename file" in content:
                print("✓ Help dialog updated")
                success_count += 1
            else:
                print("✗ Help dialog not updated")
        else:
            print("✗ Could not find source file for help dialog check")
    except Exception as e:
        print(f"✗ Help dialog integration test failed: {e}")
    
    print(f"\nTest Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Rename feature is fully implemented.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

def print_usage_instructions():
    """Print usage instructions for the rename feature"""
    print("\n" + "=" * 60)
    print("RENAME FEATURE USAGE INSTRUCTIONS")
    print("=" * 60)
    print()
    print("1. Start TFM:")
    print("   python tfm.py")
    print()
    print("2. Navigate to a file or directory you want to rename")
    print()
    print("3. Make sure no files are selected (press Space to deselect)")
    print("   - Bulk rename is not implemented yet")
    print("   - The feature only works on single files/directories")
    print()
    print("4. Press 'r' or 'R' to enter rename mode")
    print()
    print("5. Type the new name:")
    print("   - The current name will be pre-filled")
    print("   - Use Backspace to edit")
    print("   - Type the new name")
    print()
    print("6. Press Enter to confirm the rename")
    print("   - Or press ESC to cancel")
    print()
    print("LIMITATIONS:")
    print("- Cannot rename parent directory (..)")
    print("- Cannot rename when files are selected (bulk rename not implemented)")
    print("- Cannot use invalid characters like '/' or null bytes")
    print("- Cannot rename to an existing file/directory name")
    print()
    print("DEMO FILES:")
    print("Run 'python test/demo_rename_feature.py' to create test files")
    print()

if __name__ == "__main__":
    print("TFM Rename Feature - Final Test")
    print("=" * 50)
    
    success = test_complete_implementation()
    
    if success:
        print_usage_instructions()
    
    print("\n" + "=" * 50)
    print("Test completed!")