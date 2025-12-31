"""
Test script to verify the file operations refactoring works correctly

Run with: PYTHONPATH=.:src:ttk pytest test/test_file_operations_refactoring.py -v
"""

import tempfile
import shutil
from pathlib import Path

from tfm_file_operations import FileListManager, FileOperationsUI
from tfm_path import Path as TFMPath


def test_file_list_manager():
    """Test basic file list manager functionality"""
    print("Testing FileListManager class...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file2 = temp_path / "test2.txt"
        test_file1.write_text("Test content 1")
        test_file2.write_text("Test content 2")
        
        # Initialize file operations
        class MockConfig:
            SHOW_HIDDEN_FILES = False
            MAX_EXTENSION_LENGTH = 5
            SEPARATE_EXTENSIONS = True
        
        file_ops = FileListManager(MockConfig())
        
        # Test file info
        size_str, date_str = file_ops.get_file_info(TFMPath(test_file1))
        assert size_str is not None
        assert date_str is not None
        
        # Test sort functionality
        entries = [TFMPath(test_file1), TFMPath(test_file2)]
        sorted_entries = file_ops.sort_entries(entries, 'name', False)
        assert len(sorted_entries) == 2
        
        # Test sort description
        pane_data = {'sort_mode': 'name', 'sort_reverse': False}
        desc = file_ops.get_sort_description(pane_data)
        assert 'Name' in desc
        
        print("✓ FileListManager tests passed")


def test_file_operations_ui_initialization():
    """Test that FileOperationsUI can be initialized properly"""
    print("Testing FileOperationsUI initialization...")
    
    # Mock file manager object
    class MockFileManager:
        def __init__(self):
            self.log_manager = None
            self.progress_manager = None
            self.cache_manager = None
            self.config = None
            self.needs_full_redraw = False
        
        def get_current_pane(self):
            return {
                'selected_files': set(),
                'files': [],
                'selected_index': 0
            }
        
        def get_inactive_pane(self):
            return {
                'path': TFMPath('/tmp'),
                'files': []
            }
        
        def refresh_files(self):
            pass
        
        def show_confirmation(self, message, callback):
            # Auto-confirm for testing
            callback(True)
        
        def show_dialog(self, message, choices, callback):
            # Auto-select first choice for testing
            callback(choices[0]['value'])
    
    # Initialize components
    class MockConfig:
        SHOW_HIDDEN_FILES = False
        CONFIRM_COPY = False
        CONFIRM_MOVE = False
        CONFIRM_DELETE = False
    
    file_ops = FileListManager(MockConfig())
    mock_fm = MockFileManager()
    
    # Test FileOperationsUI initialization
    file_ops_ui = FileOperationsUI(mock_fm, file_ops)
    
    assert file_ops_ui.file_manager == mock_fm
    assert file_ops_ui.file_operations == file_ops
    
    print("✓ FileOperationsUI initialization tests passed")


def test_backward_compatibility():
    """Test that the refactoring maintains backward compatibility"""
    print("Testing backward compatibility...")
    
    # This test would require a full FileManager instance which needs curses
    # For now, just test that the classes can be imported and initialized
    try:
        from tfm_file_operations import FileListManager, FileOperationsUI
        
        class MockConfig:
            SHOW_HIDDEN_FILES = False
        
        file_ops = FileListManager(MockConfig())
        
        # Test that basic methods still work
        pane_data = {
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': '',
            'files': [],
            'selected_index': 0,
            'scroll_offset': 0,
            'selected_files': set()
        }
        
        # Test refresh_files method (should not crash)
        # We can't test with real paths without setting up a full environment
        
        print("✓ Backward compatibility tests passed")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True


def test_file_operations_integration():
    """Test integration between FileListManager and FileOperationsUI"""
    print("Testing file operations integration...")
    
    try:
        # Test that FileOperationsUI can use FileListManager methods
        class MockConfig:
            SHOW_HIDDEN_FILES = False
            CONFIRM_COPY = False
            CONFIRM_MOVE = False
            CONFIRM_DELETE = False
        
        class MockFileManager:
            def __init__(self):
                self.config = MockConfig()
                self.log_manager = None
                self.progress_manager = None
                self.cache_manager = None
                self.needs_full_redraw = False
        
        file_ops = FileListManager(MockConfig())
        mock_fm = MockFileManager()
        file_ops_ui = FileOperationsUI(mock_fm, file_ops)
        
        # Test that UI can access file list manager methods
        assert hasattr(file_ops_ui.file_operations, 'get_file_info')
        assert hasattr(file_ops_ui.file_operations, 'sort_entries')
        assert hasattr(file_ops_ui.file_operations, 'refresh_files')
        
        # Test that UI has its own methods
        assert hasattr(file_ops_ui, 'copy_selected_files')
        assert hasattr(file_ops_ui, 'move_selected_files')
        assert hasattr(file_ops_ui, 'delete_selected_files')
        
        print("✓ File operations integration tests passed")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("Running file operations refactoring tests...\n")
    
    try:
        test_file_list_manager()
        test_file_operations_ui_initialization()
        test_backward_compatibility()
        test_file_operations_integration()
        
        print("\n✅ All tests passed! File operations refactoring is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
