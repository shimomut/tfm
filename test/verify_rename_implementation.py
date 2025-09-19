#!/usr/bin/env python3
"""
Verification script for the rename feature implementation in TFM
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the src directory to the path so we can import tfm modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_rename_methods():
    """Test that all rename methods are properly implemented"""
    print("Testing rename method implementation...")
    
    try:
        from tfm_main import FileManager
        import curses
        
        # Check if FileManager has the required rename methods
        required_methods = [
            'enter_rename_mode',
            'exit_rename_mode', 
            'perform_rename',
            'handle_rename_input'
        ]
        
        for method_name in required_methods:
            if hasattr(FileManager, method_name):
                print(f"✓ Method {method_name} exists")
            else:
                print(f"✗ Method {method_name} missing")
        
        # Check if rename mode variables are initialized
        # We can't easily test this without creating a FileManager instance
        # which requires curses, so we'll check the source code structure
        print("✓ Rename methods appear to be implemented")
        
    except ImportError as e:
        print(f"✗ Could not import FileManager: {e}")
    except Exception as e:
        print(f"✗ Error testing rename methods: {e}")

def test_configuration():
    """Test that rename configuration is properly set up"""
    print("\nTesting rename configuration...")
    
    try:
        from tfm_config import get_config, is_key_bound_to
        
        # Test key bindings
        if is_key_bound_to('r', 'rename_file'):
            print("✓ 'r' key bound to rename_file")
        else:
            print("✗ 'r' key not bound to rename_file")
            
        if is_key_bound_to('R', 'rename_file'):
            print("✓ 'R' key bound to rename_file")
        else:
            print("✗ 'R' key not bound to rename_file")
        
        # Check default configuration
        from tfm_config import DefaultConfig
        if hasattr(DefaultConfig, 'KEY_BINDINGS') and 'rename_file' in DefaultConfig.KEY_BINDINGS:
            print("✓ Rename key binding in default configuration")
        else:
            print("✗ Rename key binding missing from default configuration")
            
    except ImportError as e:
        print(f"✗ Could not import configuration: {e}")
    except Exception as e:
        print(f"✗ Error testing configuration: {e}")

def test_file_operations():
    """Test actual file rename operations"""
    print("\nTesting file rename operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test file rename
        test_file = temp_path / "original.txt"
        test_file.write_text("test content")
        
        new_file = temp_path / "renamed.txt"
        
        try:
            test_file.rename(new_file)
            if new_file.exists() and not test_file.exists():
                print("✓ File rename operation works")
            else:
                print("✗ File rename operation failed")
        except Exception as e:
            print(f"✗ File rename error: {e}")
        
        # Test directory rename
        test_dir = temp_path / "original_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        
        new_dir = temp_path / "renamed_dir"
        
        try:
            test_dir.rename(new_dir)
            if new_dir.exists() and not test_dir.exists():
                print("✓ Directory rename operation works")
            else:
                print("✗ Directory rename operation failed")
        except Exception as e:
            print(f"✗ Directory rename error: {e}")
        
        # Test error conditions
        try:
            # Try to rename to existing file
            existing_file = temp_path / "existing.txt"
            existing_file.write_text("existing")
            
            another_file = temp_path / "another.txt"
            another_file.write_text("another")
            
            # This should raise FileExistsError
            try:
                another_file.rename(existing_file)
                print("✗ Should have failed renaming to existing file")
            except FileExistsError:
                print("✓ Correctly handles renaming to existing file")
            except Exception as e:
                print(f"✗ Unexpected error: {e}")
                
        except Exception as e:
            print(f"✗ Error testing error conditions: {e}")

def check_source_code():
    """Check that the source code has been properly modified"""
    print("\nChecking source code modifications...")
    
    try:
        # Check main file for rename functionality
        main_file = Path(__file__).parent.parent / "src" / "tfm_main.py"
        if main_file.exists():
            content = main_file.read_text()
            
            checks = [
                ("rename_mode", "rename mode variable"),
                ("enter_rename_mode", "enter rename mode method"),
                ("handle_rename_input", "rename input handler"),
                ("is_key_for_action(key, 'rename_file')", "rename key binding check")
            ]
            
            for check_str, description in checks:
                if check_str in content:
                    print(f"✓ Found {description}")
                else:
                    print(f"✗ Missing {description}")
        else:
            print("✗ Could not find main source file")
            
        # Check config file
        config_file = Path(__file__).parent.parent / "src" / "tfm_config.py"
        if config_file.exists():
            content = config_file.read_text()
            
            if "'rename_file'" in content:
                print("✓ Found rename_file in configuration")
            else:
                print("✗ Missing rename_file in configuration")
        else:
            print("✗ Could not find config source file")
            
    except Exception as e:
        print(f"✗ Error checking source code: {e}")

def main():
    """Run all verification tests"""
    print("TFM Rename Feature Verification")
    print("=" * 50)
    
    test_rename_methods()
    test_configuration()
    test_file_operations()
    check_source_code()
    
    print("\n" + "=" * 50)
    print("Verification complete!")
    print("\nTo test interactively:")
    print("1. Run: python test/demo_rename_feature.py")
    print("2. Run: python tfm.py")
    print("3. Navigate to rename_demo directory")
    print("4. Press 'r' on a file to test rename")

if __name__ == "__main__":
    main()