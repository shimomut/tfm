#!/usr/bin/env python3
"""
Test suite for FileOperations and FileOperationsUI TTK integration.

This test verifies that file operations work correctly with the TTK-migrated system.
Note: FileOperations and FileOperationsUI contain no rendering code - they are pure
business logic classes. All rendering is handled by tfm_main.py.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path as StdPath
import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_file_operations import FileOperations, FileOperationsUI
from tfm_path import Path as TFMPath


class MockConfig:
    """Mock configuration for testing"""
    SHOW_HIDDEN_FILES = False
    MAX_EXTENSION_LENGTH = 5
    SEPARATE_EXTENSIONS = True
    CONFIRM_COPY = False
    CONFIRM_MOVE = False
    CONFIRM_DELETE = False


class MockLogManager:
    """Mock log manager for testing"""
    def __init__(self):
        self.messages = []
    
    def add_message(self, level, message):
        self.messages.append((level, message))


class MockProgressManager:
    """Mock progress manager for testing"""
    def __init__(self):
        self.operations = []
        self.updates = []
    
    def start_operation(self, op_type, total, description, callback):
        self.operations.append(('start', op_type, total, description))
    
    def update_progress(self, item_name, count):
        self.updates.append(('update', item_name, count))
    
    def update_operation_total(self, total, description):
        self.operations.append(('update_total', total, description))
    
    def increment_errors(self):
        self.operations.append(('error',))
    
    def finish_operation(self):
        self.operations.append(('finish',))
    
    def refresh_animation(self):
        pass


class MockCacheManager:
    """Mock cache manager for testing"""
    def __init__(self):
        self.invalidations = []
    
    def invalidate_cache_for_copy_operation(self, sources, dest):
        self.invalidations.append(('copy', sources, dest))
    
    def invalidate_cache_for_move_operation(self, sources, dest):
        self.invalidations.append(('move', sources, dest))
    
    def invalidate_cache_for_delete_operation(self, sources):
        self.invalidations.append(('delete', sources))


class MockFileManager:
    """Mock file manager for testing"""
    def __init__(self):
        self.config = MockConfig()
        self.log_manager = MockLogManager()
        self.progress_manager = MockProgressManager()
        self.cache_manager = MockCacheManager()
        self.needs_full_redraw = False
        self.operation_in_progress = False
        self.operation_cancelled = False
        self.active_pane = 'left'
        self.panes = {
            'left': {
                'path': TFMPath('/tmp/left'),
                'files': [],
                'selected_files': set(),
                'selected_index': 0,
                'scroll_offset': 0,
                'filter_pattern': '',
                'sort_mode': 'name',
                'sort_reverse': False
            },
            'right': {
                'path': TFMPath('/tmp/right'),
                'files': [],
                'selected_files': set(),
                'selected_index': 0,
                'scroll_offset': 0,
                'filter_pattern': '',
                'sort_mode': 'name',
                'sort_reverse': False
            }
        }
        self.dialog_callback = None
        self.confirmation_callback = None
    
    def get_current_pane(self):
        return self.panes[self.active_pane]
    
    def get_inactive_pane(self):
        return self.panes['right' if self.active_pane == 'left' else 'left']
    
    def refresh_files(self, pane_data=None):
        pass
    
    def show_confirmation(self, message, callback):
        self.confirmation_callback = callback
    
    def show_dialog(self, message, choices, callback):
        self.dialog_callback = callback


class TestFileOperations:
    """Test FileOperations class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = MockConfig()
        self.file_ops = FileOperations(self.config)
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_operations_initialization(self):
        """Test that FileOperations initializes correctly"""
        assert self.file_ops.config == self.config
        assert self.file_ops.show_hidden == False
        assert self.file_ops.log_manager is None
    
    def test_get_file_info(self):
        """Test getting file information"""
        # Create a test file
        test_file = StdPath(self.temp_dir) / "test.txt"
        test_file.write_text("Test content")
        
        # Get file info
        size_str, date_str = self.file_ops.get_file_info(TFMPath(test_file))
        
        assert size_str is not None
        assert date_str is not None
        assert 'B' in size_str or 'K' in size_str or 'M' in size_str
    
    def test_get_file_info_directory(self):
        """Test getting directory information"""
        # Create a test directory
        test_dir = StdPath(self.temp_dir) / "testdir"
        test_dir.mkdir()
        
        # Get directory info
        size_str, date_str = self.file_ops.get_file_info(TFMPath(test_dir))
        
        assert size_str == "<DIR>"
        assert date_str is not None
    
    def test_sort_entries_by_name(self):
        """Test sorting entries by name"""
        # Create test files
        file1 = StdPath(self.temp_dir) / "zebra.txt"
        file2 = StdPath(self.temp_dir) / "alpha.txt"
        dir1 = StdPath(self.temp_dir) / "beta_dir"
        
        file1.write_text("test")
        file2.write_text("test")
        dir1.mkdir()
        
        entries = [TFMPath(file1), TFMPath(file2), TFMPath(dir1)]
        
        # Sort by name
        sorted_entries = self.file_ops.sort_entries(entries, 'name', False)
        
        # Directories should come first, then files alphabetically
        assert sorted_entries[0].name == "beta_dir"
        assert sorted_entries[1].name == "alpha.txt"
        assert sorted_entries[2].name == "zebra.txt"
    
    def test_sort_entries_by_size(self):
        """Test sorting entries by size"""
        # Create test files with different sizes
        file1 = StdPath(self.temp_dir) / "small.txt"
        file2 = StdPath(self.temp_dir) / "large.txt"
        
        file1.write_text("x")
        file2.write_text("x" * 1000)
        
        entries = [TFMPath(file1), TFMPath(file2)]
        
        # Sort by size
        sorted_entries = self.file_ops.sort_entries(entries, 'size', False)
        
        # Smaller file should come first
        assert sorted_entries[0].name == "small.txt"
        assert sorted_entries[1].name == "large.txt"
    
    def test_get_sort_description(self):
        """Test getting sort description"""
        pane_data = {'sort_mode': 'name', 'sort_reverse': False}
        desc = self.file_ops.get_sort_description(pane_data)
        assert 'Name' in desc
        assert '↑' in desc
        
        pane_data = {'sort_mode': 'size', 'sort_reverse': True}
        desc = self.file_ops.get_sort_description(pane_data)
        assert 'Size' in desc
        assert '↓' in desc
    
    def test_toggle_selection(self):
        """Test toggling file selection"""
        # Create test files
        file1 = StdPath(self.temp_dir) / "test1.txt"
        file1.write_text("test")
        
        pane_data = {
            'files': [TFMPath(file1)],
            'selected_index': 0,
            'selected_files': set()
        }
        
        # Toggle selection on
        success, message = self.file_ops.toggle_selection(pane_data, move_cursor=False)
        assert success
        assert str(file1) in pane_data['selected_files']
        
        # Toggle selection off
        success, message = self.file_ops.toggle_selection(pane_data, move_cursor=False)
        assert success
        assert str(file1) not in pane_data['selected_files']
    
    def test_toggle_hidden_files(self):
        """Test toggling hidden files visibility"""
        assert self.file_ops.show_hidden == False
        
        result = self.file_ops.toggle_hidden_files()
        assert result == True
        assert self.file_ops.show_hidden == True
        
        result = self.file_ops.toggle_hidden_files()
        assert result == False
        assert self.file_ops.show_hidden == False
    
    def test_find_matches(self):
        """Test finding files matching pattern"""
        # Create test files
        file1 = StdPath(self.temp_dir) / "test.txt"
        file2 = StdPath(self.temp_dir) / "example.txt"
        file3 = StdPath(self.temp_dir) / "test_example.txt"
        
        file1.write_text("test")
        file2.write_text("test")
        file3.write_text("test")
        
        pane_data = {
            'files': [TFMPath(file1), TFMPath(file2), TFMPath(file3)]
        }
        
        # Find files matching "test"
        matches = self.file_ops.find_matches(pane_data, "test")
        assert len(matches) == 2  # test.txt and test_example.txt
        
        # Find files matching "example"
        matches = self.file_ops.find_matches(pane_data, "example")
        assert len(matches) == 2  # example.txt and test_example.txt


class TestFileOperationsUI:
    """Test FileOperationsUI class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_fm = MockFileManager()
        self.file_ops = FileOperations(MockConfig())
        self.file_ops_ui = FileOperationsUI(self.mock_fm, self.file_ops)
    
    def test_file_operations_ui_initialization(self):
        """Test that FileOperationsUI initializes correctly"""
        assert self.file_ops_ui.file_manager == self.mock_fm
        assert self.file_ops_ui.file_operations == self.file_ops
        assert self.file_ops_ui.log_manager == self.mock_fm.log_manager
        assert self.file_ops_ui.progress_manager == self.mock_fm.progress_manager
        assert self.file_ops_ui.cache_manager == self.mock_fm.cache_manager
        assert self.file_ops_ui.config == self.mock_fm.config
    
    def test_count_files_recursively_empty(self):
        """Test counting files in empty list"""
        count = self.file_ops_ui._count_files_recursively([])
        assert count == 0
    
    def test_validate_operation_capabilities_delete(self):
        """Test validating delete operation capabilities"""
        # Create a mock path that supports write operations
        class MockPath:
            def supports_write_operations(self):
                return True
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'delete', [MockPath()]
        )
        assert is_valid
        assert error_msg is None
    
    def test_validate_operation_capabilities_delete_readonly(self):
        """Test validating delete operation on read-only storage"""
        # Create a mock path that doesn't support write operations
        class MockPath:
            def supports_write_operations(self):
                return False
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'delete', [MockPath()]
        )
        assert not is_valid
        assert "read-only" in error_msg.lower()
    
    def test_validate_operation_capabilities_copy(self):
        """Test validating copy operation capabilities"""
        # Create mock paths
        class MockSourcePath:
            def supports_write_operations(self):
                return False  # Can copy FROM read-only
        
        class MockDestPath:
            def supports_write_operations(self):
                return True  # Must copy TO writable
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'copy', [MockSourcePath()], MockDestPath()
        )
        assert is_valid
        assert error_msg is None
    
    def test_validate_operation_capabilities_copy_readonly_dest(self):
        """Test validating copy operation to read-only destination"""
        # Create mock paths
        class MockSourcePath:
            def supports_write_operations(self):
                return True
        
        class MockDestPath:
            def supports_write_operations(self):
                return False  # Cannot copy TO read-only
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'copy', [MockSourcePath()], MockDestPath()
        )
        assert not is_valid
        assert "read-only" in error_msg.lower()
    
    def test_validate_operation_capabilities_move(self):
        """Test validating move operation capabilities"""
        # Create mock paths
        class MockPath:
            def supports_write_operations(self):
                return True
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'move', [MockPath()], MockPath()
        )
        assert is_valid
        assert error_msg is None
    
    def test_validate_operation_capabilities_move_readonly_source(self):
        """Test validating move operation from read-only storage"""
        # Create mock paths
        class MockSourcePath:
            def supports_write_operations(self):
                return False  # Cannot move FROM read-only
        
        class MockDestPath:
            def supports_write_operations(self):
                return True
        
        is_valid, error_msg = self.file_ops_ui._validate_operation_capabilities(
            'move', [MockSourcePath()], MockDestPath()
        )
        assert not is_valid
        assert "read-only" in error_msg.lower()


class TestFileOperationsIntegration:
    """Test integration between FileOperations and FileOperationsUI"""
    
    def test_file_operations_ui_uses_file_operations(self):
        """Test that FileOperationsUI can use FileOperations methods"""
        mock_fm = MockFileManager()
        file_ops = FileOperations(MockConfig())
        file_ops_ui = FileOperationsUI(mock_fm, file_ops)
        
        # Verify UI can access file operations methods
        assert hasattr(file_ops_ui.file_operations, 'get_file_info')
        assert hasattr(file_ops_ui.file_operations, 'sort_entries')
        assert hasattr(file_ops_ui.file_operations, 'refresh_files')
        assert hasattr(file_ops_ui.file_operations, 'toggle_selection')
        assert hasattr(file_ops_ui.file_operations, 'find_matches')
    
    def test_file_operations_ui_has_operation_methods(self):
        """Test that FileOperationsUI has operation methods"""
        mock_fm = MockFileManager()
        file_ops = FileOperations(MockConfig())
        file_ops_ui = FileOperationsUI(mock_fm, file_ops)
        
        # Verify UI has its own operation methods
        assert hasattr(file_ops_ui, 'copy_selected_files')
        assert hasattr(file_ops_ui, 'move_selected_files')
        assert hasattr(file_ops_ui, 'delete_selected_files')
        assert hasattr(file_ops_ui, 'perform_copy_operation')
        assert hasattr(file_ops_ui, 'perform_move_operation')
        assert hasattr(file_ops_ui, 'perform_delete_operation')
    
    def test_no_rendering_code_in_file_operations(self):
        """Verify that FileOperations contains no rendering code"""
        import inspect
        
        # Get all methods of FileOperations
        methods = inspect.getmembers(FileOperations, predicate=inspect.isfunction)
        
        # Check that no method contains rendering-related code
        rendering_keywords = ['stdscr', 'addstr', 'hline', 'vline', 'curses', 'draw_text', 'renderer']
        
        for method_name, method in methods:
            if method_name.startswith('_'):
                continue  # Skip private methods
            
            source = inspect.getsource(method)
            for keyword in rendering_keywords:
                assert keyword not in source, f"Found rendering keyword '{keyword}' in FileOperations.{method_name}"
    
    def test_no_rendering_code_in_file_operations_ui(self):
        """Verify that FileOperationsUI contains no rendering code"""
        import inspect
        
        # Get all methods of FileOperationsUI
        methods = inspect.getmembers(FileOperationsUI, predicate=inspect.isfunction)
        
        # Check that no method contains direct rendering calls
        # Note: FileOperationsUI can set needs_full_redraw flag and call show_dialog
        direct_rendering_keywords = ['stdscr', 'addstr', 'hline', 'vline', 'curses.']
        
        for method_name, method in methods:
            if method_name.startswith('_'):
                continue  # Skip private methods
            
            source = inspect.getsource(method)
            for keyword in direct_rendering_keywords:
                assert keyword not in source, f"Found direct rendering keyword '{keyword}' in FileOperationsUI.{method_name}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v'])
