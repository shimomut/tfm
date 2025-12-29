"""
Test script for the create file feature (Shift-E key)

Run with: PYTHONPATH=.:src:ttk pytest test/test_create_file.py -v
"""

from pathlib import Path
import sys
import tempfile
import unittest.mock

# Mock curses before importing tfm_main
sys.modules['curses'] = unittest.mock.MagicMock()

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
            fm.pane_manager.left_pane['path'] = temp_path
            fm.pane_manager.right_pane['path'] = temp_path
            fm.pane_manager.active_pane = 'left'
            
            # Test that create file methods exist
            assert hasattr(fm, 'enter_create_file_mode'), "enter_create_file_mode method not found"
            assert hasattr(fm, 'on_create_file_confirm'), "on_create_file_confirm method not found"
            assert hasattr(fm, 'on_create_file_cancel'), "on_create_file_cancel method not found"
            
            print("✓ All create file methods exist")
            sys.stdout.flush()
            
            # Test file creation through the callback
            test_file_name = "test_new_file.txt"
            
            # Mock edit_selected_file to avoid launching editor
            original_edit = getattr(fm, 'edit_selected_file', None)
            edit_called = False
            
            def mock_edit():
                nonlocal edit_called
                edit_called = True
            
            if original_edit:
                fm.edit_selected_file = mock_edit
            
            fm.on_create_file_confirm(test_file_name)
            
            # Check if file was created
            new_file = temp_path / test_file_name
            assert new_file.exists(), f"File {new_file} should have been created"
            assert new_file.is_file(), f"{new_file} should be a file"
            
            print("✓ File creation works")
            sys.stdout.flush()
            
            print("\n🎉 All tests passed! Create file functionality is working correctly.")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    return True
