#!/usr/bin/env python3
"""
Test script to verify that all modes are using SingleLineTextEdit correctly
"""

import sys
import os
import unittest.mock

# Mock curses before importing anything else
sys.modules['curses'] = unittest.mock.MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_main import FileManager
from tfm_single_line_text_edit import SingleLineTextEdit
import tempfile
from pathlib import Path

def test_modes_use_single_line_edit():
    """Test that all modes are using SingleLineTextEdit instances"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a mock stdscr object (minimal implementation)
        class MockStdscr:
            def getmaxyx(self):
                return (24, 80)
            def keypad(self, enable):
                pass
        
        # Create FileManager instance
        print("Creating FileManager...")
        original_stdout = sys.stdout
        try:
            fm = FileManager(MockStdscr())
            sys.stdout = original_stdout
            print("FileManager created successfully")
        except Exception as e:
            sys.stdout = original_stdout
            print(f"Error creating FileManager: {e}")
            raise
        
        # Test that dialog components have SingleLineTextEdit editors
        print("Testing dialog editor types...")
        
        # Test list dialog search
        assert hasattr(fm.list_dialog, 'text_editor'), "list_dialog.text_editor attribute missing"
        assert isinstance(fm.list_dialog.text_editor, SingleLineTextEdit), "list_dialog.text_editor is not SingleLineTextEdit"
        print("✓ List dialog search uses SingleLineTextEdit")
        
        # Test search dialog pattern
        assert hasattr(fm.search_dialog, 'text_editor'), "search_dialog.text_editor attribute missing"
        assert isinstance(fm.search_dialog.text_editor, SingleLineTextEdit), "search_dialog.text_editor is not SingleLineTextEdit"
        print("✓ Search dialog pattern uses SingleLineTextEdit")
        
        # Test batch rename mode
        assert hasattr(fm.batch_rename_dialog, 'regex_editor'), "batch_rename_dialog.regex_editor attribute missing"
        assert isinstance(fm.batch_rename_dialog.regex_editor, SingleLineTextEdit), "batch_rename_dialog.regex_editor is not SingleLineTextEdit"
        assert hasattr(fm.batch_rename_dialog, 'destination_editor'), "batch_rename_dialog.destination_editor attribute missing"
        assert isinstance(fm.batch_rename_dialog.destination_editor, SingleLineTextEdit), "batch_rename_dialog.destination_editor is not SingleLineTextEdit"
        print("✓ Batch rename mode uses SingleLineTextEdit")
        
        # Test general dialog (used for create file/directory operations)
        assert hasattr(fm, 'general_dialog'), "general_dialog attribute missing"
        print("✓ General dialog exists for create operations")
        
        print("\n✅ All modes successfully updated to use SingleLineTextEdit!")
        print("\nBenefits:")
        print("• Consistent text editing experience across all modes")
        print("• Better cursor movement and text selection")
        print("• Proper handling of special keys and edge cases")
        print("• Reduced code duplication in input handling")
        
        # Test that dialog components are properly integrated
        print("\nVerifying dialog integration...")
        assert hasattr(fm, 'list_dialog'), "list_dialog should exist"
        assert hasattr(fm, 'search_dialog'), "search_dialog should exist"
        assert hasattr(fm, 'batch_rename_dialog'), "batch_rename_dialog should exist"
        assert hasattr(fm, 'general_dialog'), "general_dialog should exist"
        print("✓ All dialog components properly integrated")
        
        return True

if __name__ == "__main__":
    try:
        print("Starting test...")
        result = test_modes_use_single_line_edit()
        if result:
            print("\n🎉 All tests passed! TFM modes successfully updated.")
        else:
            print("\n❌ Test failed!")
            sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n❌ Test failed: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)