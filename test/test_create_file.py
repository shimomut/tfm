#!/usr/bin/env python3
"""
Test script for the create file feature (Shift-E key)
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

def test_create_file_functionality():
    """Test the create file functionality"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"Testing in temporary directory: {temp_path}")
        
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
                return ord('q')  # Quit immediately
        
        # Create mock file manager
        mock_stdscr = MockStdscr()
        
        # Test that the functionality exists
        try:
            # Temporarily redirect stdout to avoid LogCapture interference
            original_stdout = sys.stdout
            fm = FileManager(mock_stdscr)
            # Restore stdout immediately
            sys.stdout = original_stdout
            
            # Set up test directories
            fm.left_pane['path'] = temp_path
            fm.right_pane['path'] = temp_path
            fm.active_pane = 'left'
            
            # Test that create file methods exist
            assert hasattr(fm, 'enter_create_file_mode'), "enter_create_file_mode method not found"
            assert hasattr(fm, 'exit_create_file_mode'), "exit_create_file_mode method not found"
            assert hasattr(fm, 'perform_create_file'), "perform_create_file method not found"
            assert hasattr(fm, 'handle_create_file_input'), "handle_create_file_input method not found"
            
            # Test that create_file_mode variables exist
            assert hasattr(fm, 'create_file_mode'), "create_file_mode attribute not found"
            assert hasattr(fm, 'create_file_pattern'), "create_file_pattern attribute not found"
            
            print("✓ All create file methods and attributes exist")
            sys.stdout.flush()
            
            # Test entering create file mode
            fm.enter_create_file_mode()
            assert fm.create_file_mode == True, "create_file_mode should be True after entering"
            assert fm.create_file_pattern == "", "create_file_pattern should be empty initially"
            
            print("✓ Enter create file mode works")
            sys.stdout.flush()
            
            # Test exiting create file mode
            fm.exit_create_file_mode()
            assert fm.create_file_mode == False, "create_file_mode should be False after exiting"
            assert fm.create_file_pattern == "", "create_file_pattern should be empty after exiting"
            
            print("✓ Exit create file mode works")
            sys.stdout.flush()
            
            # Test file creation (without editor launch)
            fm.enter_create_file_mode()
            fm.create_file_pattern = "test_new_file.txt"
            
            # Mock the stdscr.getmaxyx for perform_create_file
            original_getmaxyx = fm.stdscr.getmaxyx
            fm.stdscr.getmaxyx = lambda: (24, 80)
            
            # Mock edit_selected_file to avoid launching editor
            original_edit = fm.edit_selected_file
            edit_called = False
            
            def mock_edit():
                nonlocal edit_called
                edit_called = True
            
            fm.edit_selected_file = mock_edit
            
            fm.perform_create_file()
            
            # Check if file was created
            new_file = temp_path / "test_new_file.txt"
            assert new_file.exists(), f"File {new_file} should have been created"
            assert new_file.is_file(), f"{new_file} should be a file"
            assert edit_called, "edit_selected_file should have been called"
            
            print("✓ File creation works")
            sys.stdout.flush()
            
            # Test input handling - typing characters
            fm.enter_create_file_mode()
            fm.handle_create_file_input(ord('t'))
            fm.handle_create_file_input(ord('e'))
            fm.handle_create_file_input(ord('s'))
            fm.handle_create_file_input(ord('t'))
            assert fm.create_file_pattern == "test", f"Pattern should be 'test', got '{fm.create_file_pattern}'"
            
            print("✓ Character input works correctly")
            sys.stdout.flush()
            
            # Test backspace handling
            fm.handle_create_file_input(8)  # Backspace
            assert fm.create_file_pattern == "tes", f"Pattern should be 'tes' after backspace, got '{fm.create_file_pattern}'"
            
            print("✓ Backspace handling works")
            sys.stdout.flush()
            
            # Test ESC key cancellation
            fm.handle_create_file_input(27)  # ESC
            assert fm.create_file_mode == False, "Should have exited create file mode"
            
            print("✓ ESC key cancels file creation")
            sys.stdout.flush()
            
            print("\n🎉 All tests passed! Create file functionality is working correctly.")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    return True

if __name__ == "__main__":
    success = test_create_file_functionality()
    sys.exit(0 if success else 1)