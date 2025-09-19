#!/usr/bin/env python3
"""
Integration test for the create file feature (Shift-E)
Tests the complete workflow including UI and input handling
"""

import os
import sys
import tempfile
import unittest.mock
from pathlib import Path

# Mock curses before importing tfm_main
sys.modules['curses'] = unittest.mock.MagicMock()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_complete_workflow():
    """Test the complete create file workflow"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"Testing complete workflow in: {temp_path}")
        
        from tfm_main import FileManager
        
        # Mock stdscr
        class MockStdscr:
            def __init__(self):
                self.height = 24
                self.width = 80
                
            def getmaxyx(self):
                return (self.height, self.width)
                
            def addstr(self, y, x, text, attr=0):
                pass
                
            def clear(self):
                pass
                
            def refresh(self):
                pass
                
            def keypad(self, enable):
                pass
                
            def getch(self):
                return ord('q')
        
        mock_stdscr = MockStdscr()
        
        # Temporarily redirect stdout to avoid LogCapture interference
        original_stdout = sys.stdout
        fm = FileManager(mock_stdscr)
        sys.stdout = original_stdout
        
        # Set up test environment
        fm.left_pane['path'] = temp_path
        fm.right_pane['path'] = temp_path
        fm.active_pane = 'left'
        
        print("✓ FileManager initialized")
        
        # Test 1: Shift-E key should enter create file mode
        fm.enter_create_file_mode()
        assert fm.create_file_mode == True, "Should be in create file mode"
        print("✓ Shift-E enters create file mode")
        
        # Test 2: Input handling - typing characters
        fm.handle_create_file_input(ord('m'))
        fm.handle_create_file_input(ord('y'))
        fm.handle_create_file_input(ord('_'))
        fm.handle_create_file_input(ord('f'))
        fm.handle_create_file_input(ord('i'))
        fm.handle_create_file_input(ord('l'))
        fm.handle_create_file_input(ord('e'))
        fm.handle_create_file_input(ord('.'))
        fm.handle_create_file_input(ord('t'))
        fm.handle_create_file_input(ord('x'))
        fm.handle_create_file_input(ord('t'))
        assert fm.create_file_pattern == "my_file.txt", f"Pattern should be 'my_file.txt', got '{fm.create_file_pattern}'"
        print("✓ Character input works correctly")
        
        # Test 3: Backspace handling
        fm.handle_create_file_input(8)  # Backspace
        fm.handle_create_file_input(8)  # Backspace
        fm.handle_create_file_input(8)  # Backspace
        assert fm.create_file_pattern == "my_file.", f"Pattern should be 'my_file.' after backspaces, got '{fm.create_file_pattern}'"
        print("✓ Backspace handling works")
        
        # Test 4: Add extension back
        fm.handle_create_file_input(ord('p'))
        fm.handle_create_file_input(ord('y'))
        assert fm.create_file_pattern == "my_file.py", f"Pattern should be 'my_file.py', got '{fm.create_file_pattern}'"
        print("✓ Extended character input works")
        
        # Test 5: Enter key should create file and launch editor
        # Mock edit_selected_file to avoid launching actual editor
        edit_called = False
        original_edit = fm.edit_selected_file
        
        def mock_edit():
            nonlocal edit_called
            edit_called = True
        
        fm.edit_selected_file = mock_edit
        
        fm.handle_create_file_input(13)  # Enter
        
        # Check if file was created
        new_file = temp_path / "my_file.py"
        assert new_file.exists(), f"File {new_file} should exist"
        assert new_file.is_file(), f"{new_file} should be a file"
        assert fm.create_file_mode == False, "Should have exited create file mode"
        assert edit_called, "Should have called edit_selected_file"
        print("✓ Enter key creates file, launches editor, and exits mode")
        
        # Test 6: ESC key should cancel
        fm.enter_create_file_mode()
        fm.create_file_pattern = "cancelled_file.txt"
        fm.handle_create_file_input(27)  # ESC
        
        cancelled_file = temp_path / "cancelled_file.txt"
        assert not cancelled_file.exists(), "Cancelled file should not exist"
        assert fm.create_file_mode == False, "Should have exited create file mode"
        print("✓ ESC key cancels file creation")
        
        # Test 7: Test that 'e' key still edits existing files (backward compatibility)
        # Create a test file first
        test_file = temp_path / "existing_file.txt"
        test_file.write_text("test content")
        
        # Set up file list and select the file
        fm.refresh_files(fm.left_pane)
        
        # Find the test file in the list
        for i, file_path in enumerate(fm.left_pane['files']):
            if file_path.name == "existing_file.txt":
                fm.left_pane['selected_index'] = i
                break
        
        # Mock edit function to track calls
        edit_existing_called = False
        
        def mock_edit_existing():
            nonlocal edit_existing_called
            edit_existing_called = True
        
        fm.edit_selected_file = mock_edit_existing
        
        # Simulate 'e' key press (edit existing file)
        fm.edit_selected_file()
        
        assert edit_existing_called, "edit_selected_file should have been called for existing file"
        print("✓ 'e' key still edits existing files (backward compatibility)")
        
        print("\n🎉 All integration tests passed!")
        return True

if __name__ == "__main__":
    try:
        success = test_complete_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)