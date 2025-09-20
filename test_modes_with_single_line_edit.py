#!/usr/bin/env python3
"""
Test script to verify that all modes are using SingleLineTextEdit correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
        fm = FileManager(MockStdscr())
        
        # Test that all modes have SingleLineTextEdit editors
        print("Testing mode editor types...")
        
        # Test filter mode
        assert hasattr(fm, 'filter_editor'), "filter_editor attribute missing"
        assert isinstance(fm.filter_editor, SingleLineTextEdit), "filter_editor is not SingleLineTextEdit"
        print("✓ Filter mode uses SingleLineTextEdit")
        
        # Test rename mode
        assert hasattr(fm, 'rename_editor'), "rename_editor attribute missing"
        assert isinstance(fm.rename_editor, SingleLineTextEdit), "rename_editor is not SingleLineTextEdit"
        print("✓ Rename mode uses SingleLineTextEdit")
        
        # Test create directory mode
        assert hasattr(fm, 'create_dir_editor'), "create_dir_editor attribute missing"
        assert isinstance(fm.create_dir_editor, SingleLineTextEdit), "create_dir_editor is not SingleLineTextEdit"
        print("✓ Create directory mode uses SingleLineTextEdit")
        
        # Test create file mode
        assert hasattr(fm, 'create_file_editor'), "create_file_editor attribute missing"
        assert isinstance(fm.create_file_editor, SingleLineTextEdit), "create_file_editor is not SingleLineTextEdit"
        print("✓ Create file mode uses SingleLineTextEdit")
        
        # Test create archive mode
        assert hasattr(fm, 'create_archive_editor'), "create_archive_editor attribute missing"
        assert isinstance(fm.create_archive_editor, SingleLineTextEdit), "create_archive_editor is not SingleLineTextEdit"
        print("✓ Create archive mode uses SingleLineTextEdit")
        
        # Test batch rename mode (already had SingleLineTextEdit)
        assert hasattr(fm, 'batch_rename_regex_editor'), "batch_rename_regex_editor attribute missing"
        assert isinstance(fm.batch_rename_regex_editor, SingleLineTextEdit), "batch_rename_regex_editor is not SingleLineTextEdit"
        assert hasattr(fm, 'batch_rename_destination_editor'), "batch_rename_destination_editor attribute missing"
        assert isinstance(fm.batch_rename_destination_editor, SingleLineTextEdit), "batch_rename_destination_editor is not SingleLineTextEdit"
        print("✓ Batch rename mode uses SingleLineTextEdit")
        
        print("\n✅ All modes successfully updated to use SingleLineTextEdit!")
        print("\nBenefits:")
        print("• Consistent text editing experience across all modes")
        print("• Better cursor movement and text selection")
        print("• Proper handling of special keys and edge cases")
        print("• Reduced code duplication in input handling")
        
        # Test that old pattern variables are gone
        print("\nVerifying old pattern variables are removed...")
        assert not hasattr(fm, 'filter_pattern'), "filter_pattern should be removed"
        assert not hasattr(fm, 'rename_pattern'), "rename_pattern should be removed"
        assert not hasattr(fm, 'create_dir_pattern'), "create_dir_pattern should be removed"
        assert not hasattr(fm, 'create_archive_pattern'), "create_archive_pattern should be removed"
        print("✓ Old pattern variables successfully removed")
        
        return True

if __name__ == "__main__":
    try:
        test_modes_use_single_line_edit()
        print("\n🎉 All tests passed! TFM modes successfully updated.")
    except Exception as e:
        import traceback
        print(f"\n❌ Test failed: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)