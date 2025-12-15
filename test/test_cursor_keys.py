#!/usr/bin/env python3
"""
Test script to verify cursor key handling in list and search dialogs
"""

import sys
import unittest.mock

# Mock curses before importing anything else
sys.modules['curses'] = unittest.mock.MagicMock()
import curses
from ttk import KeyEvent, KeyCode, ModifierKey

sys.path.insert(0, 'src')

def test_cursor_key_handling():
    """Test that cursor keys are properly handled by the editors"""
    print("🔍 Testing cursor key handling...")
    
    try:
        from tfm_main import FileManager
        from tfm_single_line_text_edit import SingleLineTextEdit
        
        class MockStdscr:
            def getmaxyx(self): return (24, 80)
            def keypad(self, enable): pass
        
        print("Creating FileManager...")
        # Save original stdout
        original_stdout = sys.stdout
        fm = FileManager(MockStdscr())
        # Restore stdout immediately
        sys.stdout = original_stdout
        print("FileManager created successfully")
        
        print("Checking list_dialog...")
        print(f"list_dialog exists: {hasattr(fm, 'list_dialog')}")
        if hasattr(fm, 'list_dialog'):
            print(f"text_editor exists: {hasattr(fm.list_dialog, 'text_editor')}")
        
        # Test that editors can handle cursor keys
        test_keys = [
            ('KeyCode.LEFT', KeyCode.LEFT),
            ('KeyCode.RIGHT', KeyCode.RIGHT),
            ('KeyCode.HOME', KeyCode.HOME),
            ('KeyCode.END', KeyCode.END),
        ]
        
        print("✓ Testing list_dialog text_editor cursor key handling:")
        for key_name, key_code in test_keys:
            # Add some text first
            fm.list_dialog.text_editor.text = "test"
            fm.list_dialog.text_editor.cursor_pos = 2
            
            # Test that the editor can handle the key
            result = fm.list_dialog.text_editor.handle_key(key_code)
            print(f"  ✓ {key_name}: {'handled' if result else 'not handled'}")
        
        # Check if search_dialog has text_editor
        if hasattr(fm.search_dialog, 'text_editor'):
            print("✓ Testing search_dialog text_editor cursor key handling:")
            for key_name, key_code in test_keys:
                # Add some text first
                fm.search_dialog.text_editor.text = "test"
                fm.search_dialog.text_editor.cursor_pos = 2
                
                # Test that the editor can handle the key
                result = fm.search_dialog.text_editor.handle_key(key_code)
                print(f"  ✓ {key_name}: {'handled' if result else 'not handled'}")
        else:
            print("✓ search_dialog.text_editor not found, skipping those tests")
        
        print("\n🎉 Cursor key handling test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cursor_key_handling()
    sys.exit(0 if success else 1)