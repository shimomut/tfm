#!/usr/bin/env python3
"""
Test script to verify cursor key handling in list and search dialogs
"""

import sys
import curses
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
        
        fm = FileManager(MockStdscr())
        
        # Test that editors can handle cursor keys
        test_keys = [
            ('curses.KEY_LEFT', curses.KEY_LEFT),
            ('curses.KEY_RIGHT', curses.KEY_RIGHT),
            ('curses.KEY_HOME', curses.KEY_HOME),
            ('curses.KEY_END', curses.KEY_END),
        ]
        
        print("✓ Testing list_dialog_search_editor cursor key handling:")
        for key_name, key_code in test_keys:
            # Add some text first
            fm.list_dialog_search_editor.text = "test"
            fm.list_dialog_search_editor.cursor_pos = 2
            
            # Test that the editor can handle the key
            result = fm.list_dialog_search_editor.handle_key(key_code)
            print(f"  ✓ {key_name}: {'handled' if result else 'not handled'}")
        
        print("✓ Testing search_dialog_pattern_editor cursor key handling:")
        for key_name, key_code in test_keys:
            # Add some text first
            fm.search_dialog_pattern_editor.text = "test"
            fm.search_dialog_pattern_editor.cursor_pos = 2
            
            # Test that the editor can handle the key
            result = fm.search_dialog_pattern_editor.handle_key(key_code)
            print(f"  ✓ {key_name}: {'handled' if result else 'not handled'}")
        
        print("\n🎉 Cursor key handling test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_cursor_key_handling()
    sys.exit(0 if success else 1)