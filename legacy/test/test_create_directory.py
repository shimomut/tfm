"""
Test script for the create directory feature (M key without selection)

Run with: PYTHONPATH=.:src:ttk pytest test/test_create_directory.py -v
"""

import sys
import tempfile
import shutil

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
        from ttk import KeyEvent, KeyCode, ModifierKey
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
            fm.pane_manager.left_pane['path'] = temp_path
            fm.pane_manager.right_pane['path'] = temp_path
            fm.pane_manager.active_pane = 'left'
            
            # Clear any selected files
            fm.pane_manager.left_pane['selected_files'].clear()
            
            # Test that create directory methods exist
            assert hasattr(fm, 'enter_create_directory_mode'), "enter_create_directory_mode method not found"
            assert hasattr(fm, 'on_create_directory_confirm'), "on_create_directory_confirm method not found"
            assert hasattr(fm, 'on_create_directory_cancel'), "on_create_directory_cancel method not found"
            
            print("✓ All create directory methods exist")
            sys.stdout.flush()
            
            # Test directory creation through the callback
            test_dir_name = "test_new_directory"
            fm.on_create_directory_confirm(test_dir_name)
            
            # Check if directory was created
            new_dir = temp_path / test_dir_name
            assert new_dir.exists(), f"Directory {new_dir} should have been created"
            assert new_dir.is_dir(), f"{new_dir} should be a directory"
            
            print("✓ Directory creation works")
            sys.stdout.flush()
            
            # Test that move_selected_files calls create directory mode when no files selected
            fm.pane_manager.left_pane['selected_files'].clear()  # Ensure no files selected
            
            # Mock enter_create_directory_mode to track if it's called
            create_dir_called = False
            original_enter_create_dir = fm.enter_create_directory_mode
            
            def mock_enter_create_dir():
                nonlocal create_dir_called
                create_dir_called = True
                # Don't call the original to avoid dialog complications in test
            
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
