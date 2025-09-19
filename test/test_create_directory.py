#!/usr/bin/env python3
"""
Test script for the create directory feature (M key without selection)
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock curses before importing tfm_main
import unittest.mock
sys.modules['curses'] = unittest.mock.MagicMock()

def test_create_directory_functionality():
    """Test the create directory functionality"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"Testing in temporary directory: {temp_path}")
        
        # Test 1: Check that move_selected_files calls enter_create_directory_mode when no files selected
        from tfm_main import FileManager
        import curses
        
        # Mock curses for testing
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
            
            # Clear any selected files
            fm.left_pane['selected_files'].clear()
            
            # Test that enter_create_directory_mode exists
            assert hasattr(fm, 'enter_create_directory_mode'), "enter_create_directory_mode method not found"
            assert hasattr(fm, 'exit_create_directory_mode'), "exit_create_directory_mode method not found"
            assert hasattr(fm, 'perform_create_directory'), "perform_create_directory method not found"
            assert hasattr(fm, 'handle_create_directory_input'), "handle_create_directory_input method not found"
            
            # Test that create_dir_mode variables exist
            assert hasattr(fm, 'create_dir_mode'), "create_dir_mode attribute not found"
            assert hasattr(fm, 'create_dir_pattern'), "create_dir_pattern attribute not found"
            
            print("✓ All create directory methods and attributes exist")
            sys.stdout.flush()
            
            # Test entering create directory mode
            fm.enter_create_directory_mode()
            assert fm.create_dir_mode == True, "create_dir_mode should be True after entering"
            assert fm.create_dir_pattern == "", "create_dir_pattern should be empty initially"
            
            print("✓ Enter create directory mode works")
            sys.stdout.flush()
            
            # Test exiting create directory mode
            fm.exit_create_directory_mode()
            assert fm.create_dir_mode == False, "create_dir_mode should be False after exiting"
            assert fm.create_dir_pattern == "", "create_dir_pattern should be empty after exiting"
            
            print("✓ Exit create directory mode works")
            sys.stdout.flush()
            
            # Test directory creation
            fm.enter_create_directory_mode()
            fm.create_dir_pattern = "test_new_directory"
            
            # Mock the stdscr.getmaxyx for perform_create_directory
            original_getmaxyx = fm.stdscr.getmaxyx
            fm.stdscr.getmaxyx = lambda: (24, 80)
            
            fm.perform_create_directory()
            
            # Check if directory was created
            new_dir = temp_path / "test_new_directory"
            assert new_dir.exists(), f"Directory {new_dir} should have been created"
            assert new_dir.is_dir(), f"{new_dir} should be a directory"
            
            print("✓ Directory creation works")
            sys.stdout.flush()
            
            # Test that move_selected_files calls create directory mode when no files selected
            fm.left_pane['selected_files'].clear()  # Ensure no files selected
            
            # Mock enter_create_directory_mode to track if it's called
            create_dir_called = False
            original_enter_create_dir = fm.enter_create_directory_mode
            
            def mock_enter_create_dir():
                nonlocal create_dir_called
                create_dir_called = True
                original_enter_create_dir()
            
            fm.enter_create_directory_mode = mock_enter_create_dir
            
            # Call move_selected_files with no files selected
            fm.move_selected_files()
            
            assert create_dir_called, "move_selected_files should call enter_create_directory_mode when no files selected"
            
            print("✓ move_selected_files correctly calls create directory mode when no files selected")
            sys.stdout.flush()
            
            print("\n🎉 All tests passed! Create directory functionality is working correctly.")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
            
    return True

if __name__ == "__main__":
    success = test_create_directory_functionality()
    sys.exit(0 if success else 1)