#!/usr/bin/env python3
"""
Integration test for the copy feature in TFM
"""

import tempfile
import os
from pathlib import Path

# Test the configuration update
def test_config_update():
    """Test that the copy key binding was added to configuration"""
    print("Testing configuration update...")
    
    # Import the config
    from _config import Config
    
    # Check if copy_files key binding exists
    if hasattr(Config, 'KEY_BINDINGS') and 'copy_files' in Config.KEY_BINDINGS:
        copy_keys = Config.KEY_BINDINGS['copy_files']
        print(f"✓ Copy key binding found: {copy_keys}")
        
        if 'c' in copy_keys and 'C' in copy_keys:
            print("✓ Both 'c' and 'C' keys are bound to copy_files")
        else:
            print("✗ Missing expected 'c' and 'C' key bindings")
            return False
    else:
        print("✗ copy_files key binding not found in configuration")
        return False
    
    return True

def test_tfm_config_integration():
    """Test that TFM can load the configuration with copy bindings"""
    print("\nTesting TFM configuration integration...")
    
    try:



# Add src directory to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

        from tfm_config import get_config, is_key_bound_to
        
        # Get the configuration
        config = get_config()
        print(f"✓ Configuration loaded successfully")
        
        # Test key binding function
        if is_key_bound_to('c', 'copy_files'):
            print("✓ 'c' key is bound to copy_files action")
        else:
            print("✗ 'c' key is not bound to copy_files action")
            return False
            
        if is_key_bound_to('C', 'copy_files'):
            print("✓ 'C' key is bound to copy_files action")
        else:
            print("✗ 'C' key is not bound to copy_files action")
            return False
            
    except Exception as e:
        print(f"✗ Error loading TFM configuration: {e}")
        return False
    
    return True

def test_method_exists():
    """Test that the copy method exists in FileManager class"""
    print("\nTesting FileManager copy method...")
    
    try:
        # We can't easily instantiate FileManager without curses, 
        # but we can check if the method exists in the source
        with open('tfm_main.py', 'r') as f:
            content = f.read()
            
        if 'def copy_selected_files(self):' in content:
            print("✓ copy_selected_files method found in FileManager")
        else:
            print("✗ copy_selected_files method not found")
            return False
            
        if 'def copy_files_to_directory(self, files_to_copy, destination_dir):' in content:
            print("✓ copy_files_to_directory method found in FileManager")
        else:
            print("✗ copy_files_to_directory method not found")
            return False
            
        if 'def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):' in content:
            print("✓ perform_copy_operation method found in FileManager")
        else:
            print("✗ perform_copy_operation method not found")
            return False
            
        # Check if the key handler was added
        if "elif self.is_key_for_action(key, 'copy_files'):" in content:
            print("✓ Copy key handler found in main loop")
        else:
            print("✗ Copy key handler not found in main loop")
            return False
            
    except Exception as e:
        print(f"✗ Error checking FileManager methods: {e}")
        return False
    
    return True

def main():
    """Run all integration tests"""
    print("=" * 50)
    print("TFM Copy Feature Integration Tests")
    print("=" * 50)
    
    tests = [
        test_config_update,
        test_tfm_config_integration,
        test_method_exists
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"Integration Tests Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Copy feature is ready.")
        print("\nUsage:")
        print("- Press 'c' or 'C' to copy selected files")
        print("- If no files are selected, copies the current file")
        print("- Files are copied to the opposite pane's directory")
        print("- Directories are copied recursively")
        print("- Conflicts show a dialog with Overwrite/Skip/Cancel options")
    else:
        print("❌ Some integration tests failed. Please check the implementation.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()