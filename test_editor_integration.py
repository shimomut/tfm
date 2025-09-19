#!/usr/bin/env python3
"""
Test script to verify the text editor integration is working correctly
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path to import TFM modules
sys.path.insert(0, str(Path(__file__).parent))

def test_editor_integration():
    """Test that the editor integration components are properly set up"""
    print("Testing TFM Text Editor Integration...")
    print("=" * 50)
    
    # Test 1: Check constants are defined
    try:
        from tfm_const import DEFAULT_TEXT_EDITOR, EDITOR_KEY
        print("✓ Constants defined correctly")
        print(f"  - DEFAULT_TEXT_EDITOR: {DEFAULT_TEXT_EDITOR}")
        print(f"  - EDITOR_KEY: {EDITOR_KEY} ('{chr(EDITOR_KEY)}')")
    except ImportError as e:
        print(f"✗ Error importing constants: {e}")
        return False
    
    # Test 2: Check configuration includes editor settings
    try:
        from tfm_config import DefaultConfig
        if hasattr(DefaultConfig, 'TEXT_EDITOR'):
            print("✓ Configuration includes TEXT_EDITOR setting")
            print(f"  - Default editor: {DefaultConfig.TEXT_EDITOR}")
        else:
            print("✗ TEXT_EDITOR not found in DefaultConfig")
            return False
            
        if 'edit_file' in DefaultConfig.KEY_BINDINGS:
            print("✓ Key binding for edit_file configured")
            print(f"  - Keys: {DefaultConfig.KEY_BINDINGS['edit_file']}")
        else:
            print("✗ edit_file key binding not found")
            return False
    except ImportError as e:
        print(f"✗ Error importing config: {e}")
        return False
    
    # Test 3: Check FileManager class has editor methods
    try:
        from tfm_main import FileManager
        
        # Check if methods exist
        methods_to_check = ['suspend_curses', 'resume_curses', 'edit_selected_file']
        for method in methods_to_check:
            if hasattr(FileManager, method):
                print(f"✓ FileManager.{method} method exists")
            else:
                print(f"✗ FileManager.{method} method missing")
                return False
    except ImportError as e:
        print(f"✗ Error importing FileManager: {e}")
        return False
    
    # Test 4: Check subprocess import is available
    try:
        import subprocess
        print("✓ subprocess module available for editor execution")
    except ImportError:
        print("✗ subprocess module not available")
        return False
    
    # Test 5: Check if default editor is available
    try:
        import subprocess
        result = subprocess.run(['which', DEFAULT_TEXT_EDITOR], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Default editor '{DEFAULT_TEXT_EDITOR}' is available")
            print(f"  - Path: {result.stdout.strip()}")
        else:
            print(f"⚠ Default editor '{DEFAULT_TEXT_EDITOR}' not found")
            print("  - You may want to configure a different editor")
    except Exception as e:
        print(f"⚠ Could not check editor availability: {e}")
    
    print()
    print("Integration test completed successfully!")
    print()
    print("To use the text editor feature:")
    print("1. Run TFM: python3 tfm_main.py")
    print("2. Navigate to a file")
    print("3. Press 'e' or 'E' to edit")
    print()
    print("To configure a different editor:")
    print("1. Edit ~/.tfm/config.py")
    print("2. Set TEXT_EDITOR = 'your_editor'")
    print("   (e.g., 'nano', 'emacs', 'code')")
    
    return True

if __name__ == "__main__":
    success = test_editor_integration()
    sys.exit(0 if success else 1)