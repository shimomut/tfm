#!/usr/bin/env python3
"""
Integration test for the create directory feature
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
    """Test the complete create directory workflow"""
    
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
        fm.left_pane['selected_files'].clear()
        
        print("✓ FileManager initialized")
        
        # Test 1: M key with no selection should enter create directory mode
        fm.move_selected_files()
        assert fm.create_dir_mode == True, "Should be in create directory mode"
        print("✓ M key with no selection enters create directory mode")
        
        # Test 2: Input handling - typing characters
        fm.handle_create_directory_input(ord('t'))
        fm.handle_create_directory_input(ord('e'))
        fm.handle_create_directory_input(ord('s'))
        fm.handle_create_directory_input(ord('t'))
        assert fm.create_dir_pattern == "test", f"Pattern should be 'test', got '{fm.create_dir_pattern}'"
        print("✓ Character input works correctly")
        
        # Test 3: Backspace handling
        fm.handle_create_directory_input(8)  # Backspace
        assert fm.create_dir_pattern == "tes", f"Pattern should be 'tes' after backspace, got '{fm.create_dir_pattern}'"
        print("✓ Backspace handling works")
        
        # Test 4: Add more characters
        fm.handle_create_directory_input(ord('t'))
        fm.handle_create_directory_input(ord('_'))
        fm.handle_create_directory_input(ord('d'))
        fm.handle_create_directory_input(ord('i'))
        fm.handle_create_directory_input(ord('r'))
        assert fm.create_dir_pattern == "test_dir", f"Pattern should be 'test_dir', got '{fm.create_dir_pattern}'"
        print("✓ Extended character input works")
        
        # Test 5: Enter key should create directory
        fm.handle_create_directory_input(13)  # Enter
        
        # Check if directory was created
        new_dir = temp_path / "test_dir"
        assert new_dir.exists(), f"Directory {new_dir} should exist"
        assert new_dir.is_dir(), f"{new_dir} should be a directory"
        assert fm.create_dir_mode == False, "Should have exited create directory mode"
        print("✓ Enter key creates directory and exits mode")
        
        # Test 6: ESC key should cancel
        fm.enter_create_directory_mode()
        fm.create_dir_pattern = "cancelled_dir"
        fm.handle_create_directory_input(27)  # ESC
        
        cancelled_dir = temp_path / "cancelled_dir"
        assert not cancelled_dir.exists(), "Cancelled directory should not exist"
        assert fm.create_dir_mode == False, "Should have exited create directory mode"
        print("✓ ESC key cancels directory creation")
        
        # Test 7: M key with files selected should still move files (backward compatibility)
        # Create a test file
        test_file = temp_path / "test_file.txt"
        test_file.write_text("test content")
        
        # Create another directory for destination
        dest_dir = temp_path / "dest"
        dest_dir.mkdir()
        
        # Set up panes
        fm.left_pane['path'] = temp_path
        fm.right_pane['path'] = dest_dir
        fm.refresh_files(fm.left_pane)
        fm.refresh_files(fm.right_pane)
        
        # Select the test file
        fm.left_pane['selected_files'].add(str(test_file))
        
        # Mock the move operation to avoid complex file operations in test
        move_called = False
        original_move_files_to_directory = fm.move_files_to_directory
        
        def mock_move_files_to_directory(files_to_move, destination_dir):
            nonlocal move_called
            move_called = True
            # Don't actually move files in test
        
        fm.move_files_to_directory = mock_move_files_to_directory
        
        # Call move_selected_files with files selected
        fm.move_selected_files()
        
        assert move_called, "move_files_to_directory should have been called"
        assert fm.create_dir_mode == False, "Should not be in create directory mode when files are selected"
        print("✓ M key with files selected still moves files (backward compatibility)")
        
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