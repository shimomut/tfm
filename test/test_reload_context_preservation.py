"""
Unit tests for user context preservation during automatic reloads.

Tests verify that _handle_reload_request preserves user context:
- Cursor position on same file if it still exists
- Cursor moves to nearest file alphabetically if selected file deleted
- Scroll position preserved when possible
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import queue
from pathlib import Path


class TestReloadContextPreservation(unittest.TestCase):
    """Test user context preservation during automatic reloads."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock all the dependencies
        self.mock_config = Mock()
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)  # height, width
        self.mock_logger = Mock()
        
        # Create test files
        self.test_files = [
            Path('/test/dir/aaa.txt'),
            Path('/test/dir/bbb.txt'),
            Path('/test/dir/ccc.txt'),
            Path('/test/dir/ddd.txt'),
            Path('/test/dir/eee.txt'),
        ]
    
    def _create_pane_data(self, files, focused_index=0, scroll_offset=0):
        """Helper to create pane data structure."""
        return {
            'path': Path('/test/dir'),
            'files': files.copy(),
            'focused_index': focused_index,
            'scroll_offset': scroll_offset,
            'selected_files': set(),
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': '',
        }
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_preserves_cursor_on_same_file(self, mock_init):
        """Test cursor stays on same file when it still exists after reload."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with left pane
        fm.pane_manager = Mock()
        left_pane = self._create_pane_data(self.test_files, focused_index=2)  # Focus on ccc.txt
        fm.pane_manager.left_pane = left_pane
        
        # Mock refresh_files to simulate file list staying the same
        def mock_refresh(pane_data):
            # Files stay the same after refresh
            pass
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request
        fm._handle_reload_request("left")
        
        # Verify cursor stayed on same file (index 2 = ccc.txt)
        self.assertEqual(left_pane['focused_index'], 2)
        self.assertEqual(left_pane['files'][left_pane['focused_index']].name, 'ccc.txt')
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_moves_cursor_to_nearest_when_file_deleted(self, mock_init):
        """Test cursor moves to nearest file alphabetically when selected file deleted."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with left pane
        fm.pane_manager = Mock()
        left_pane = self._create_pane_data(self.test_files, focused_index=2)  # Focus on ccc.txt
        fm.pane_manager.left_pane = left_pane
        
        # Mock refresh_files to simulate ccc.txt being deleted
        def mock_refresh(pane_data):
            # Remove ccc.txt from the list
            pane_data['files'] = [
                Path('/test/dir/aaa.txt'),
                Path('/test/dir/bbb.txt'),
                Path('/test/dir/ddd.txt'),
                Path('/test/dir/eee.txt'),
            ]
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request
        fm._handle_reload_request("left")
        
        # Verify cursor moved to nearest file (ddd.txt comes after ccc.txt alphabetically)
        self.assertEqual(left_pane['files'][left_pane['focused_index']].name, 'ddd.txt')
        
        # Verify info log was called about moving cursor
        info_calls = [call[0][0] for call in fm.logger.info.call_args_list]
        self.assertTrue(any('deleted' in call.lower() and 'moved cursor' in call.lower() for call in info_calls))
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_moves_cursor_to_last_file_when_deleted_was_last(self, mock_init):
        """Test cursor moves to last file when selected file was last and got deleted."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with left pane
        fm.pane_manager = Mock()
        left_pane = self._create_pane_data(self.test_files, focused_index=4)  # Focus on eee.txt (last)
        fm.pane_manager.left_pane = left_pane
        
        # Mock refresh_files to simulate eee.txt being deleted
        def mock_refresh(pane_data):
            # Remove eee.txt from the list
            pane_data['files'] = [
                Path('/test/dir/aaa.txt'),
                Path('/test/dir/bbb.txt'),
                Path('/test/dir/ccc.txt'),
                Path('/test/dir/ddd.txt'),
            ]
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request
        fm._handle_reload_request("left")
        
        # Verify cursor moved to last file (ddd.txt)
        self.assertEqual(left_pane['focused_index'], 3)
        self.assertEqual(left_pane['files'][left_pane['focused_index']].name, 'ddd.txt')
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_preserves_scroll_position(self, mock_init):
        """Test scroll position is preserved when possible."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with left pane
        fm.pane_manager = Mock()
        # Create many files to enable scrolling
        many_files = [Path(f'/test/dir/file{i:03d}.txt') for i in range(50)]
        left_pane = self._create_pane_data(many_files, focused_index=25, scroll_offset=10)
        fm.pane_manager.left_pane = left_pane
        
        # Mock refresh_files to keep files the same
        def mock_refresh(pane_data):
            pass
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request
        fm._handle_reload_request("left")
        
        # Verify scroll position was preserved
        self.assertEqual(left_pane['scroll_offset'], 10)
        self.assertEqual(left_pane['focused_index'], 25)
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_adjusts_scroll_when_focused_item_not_visible(self, mock_init):
        """Test scroll position adjusts to keep focused item visible."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with left pane
        fm.pane_manager = Mock()
        # Create many files
        many_files = [Path(f'/test/dir/file{i:03d}.txt') for i in range(50)]
        left_pane = self._create_pane_data(many_files, focused_index=5, scroll_offset=20)
        fm.pane_manager.left_pane = left_pane
        
        # Mock refresh_files to keep files the same
        def mock_refresh(pane_data):
            pass
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request
        fm._handle_reload_request("left")
        
        # Verify scroll position was adjusted to make focused item visible
        # Focused item at index 5 should be visible, so scroll_offset should be <= 5
        self.assertLessEqual(left_pane['scroll_offset'], 5)
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_handles_empty_file_list_after_reload(self, mock_init):
        """Test handles case where all files are deleted."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with left pane
        fm.pane_manager = Mock()
        left_pane = self._create_pane_data(self.test_files, focused_index=2)
        fm.pane_manager.left_pane = left_pane
        
        # Mock refresh_files to simulate all files being deleted
        def mock_refresh(pane_data):
            pane_data['files'] = []
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request
        fm._handle_reload_request("left")
        
        # Verify cursor and scroll reset to 0
        self.assertEqual(left_pane['focused_index'], 0)
        self.assertEqual(left_pane['scroll_offset'], 0)
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_handles_new_file_added(self, mock_init):
        """Test cursor stays on same file when new files are added."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with left pane
        fm.pane_manager = Mock()
        left_pane = self._create_pane_data(self.test_files, focused_index=2)  # Focus on ccc.txt
        fm.pane_manager.left_pane = left_pane
        
        # Mock refresh_files to simulate new file being added
        def mock_refresh(pane_data):
            # Add new file between bbb and ccc
            pane_data['files'] = [
                Path('/test/dir/aaa.txt'),
                Path('/test/dir/bbb.txt'),
                Path('/test/dir/bbb_new.txt'),  # New file
                Path('/test/dir/ccc.txt'),
                Path('/test/dir/ddd.txt'),
                Path('/test/dir/eee.txt'),
            ]
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request
        fm._handle_reload_request("left")
        
        # Verify cursor stayed on ccc.txt (now at index 3)
        self.assertEqual(left_pane['files'][left_pane['focused_index']].name, 'ccc.txt')
        self.assertEqual(left_pane['focused_index'], 3)
    
    @patch('src.tfm_main.FileManager.__init__', return_value=None)
    def test_right_pane_context_preservation(self, mock_init):
        """Test context preservation works for right pane too."""
        from src.tfm_main import FileManager
        
        # Create FileManager instance
        fm = FileManager()
        fm.logger = self.mock_logger
        fm.renderer = self.mock_renderer
        fm.log_height_ratio = 0.3
        
        # Set up pane manager with right pane
        fm.pane_manager = Mock()
        right_pane = self._create_pane_data(self.test_files, focused_index=2)  # Focus on ccc.txt
        fm.pane_manager.right_pane = right_pane
        
        # Mock refresh_files to keep files the same
        def mock_refresh(pane_data):
            pass
        fm.refresh_files = mock_refresh
        
        # Call _handle_reload_request for right pane
        fm._handle_reload_request("right")
        
        # Verify cursor stayed on same file
        self.assertEqual(right_pane['focused_index'], 2)
        self.assertEqual(right_pane['files'][right_pane['focused_index']].name, 'ccc.txt')


if __name__ == '__main__':
    unittest.main()
