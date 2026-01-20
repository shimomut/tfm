"""Test that go_parent action focuses on the previous child directory."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.tfm_main import FileManager


class TestParentDirectoryCursorPositioning(unittest.TestCase):
    """Test cursor positioning when navigating to parent directory."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        self.mock_config = Mock()
        self.mock_config.DUAL_PANE_MODE = True
        self.mock_config.MAX_HISTORY_ENTRIES = 100
        
        # Create FileManager with mocked dependencies
        with patch('src.tfm_main.StateManager'), \
             patch('src.tfm_main.PaneManager'), \
             patch('src.tfm_main.MenuManager'), \
             patch('src.tfm_main.LogManager'):
            self.fm = FileManager(self.mock_renderer, self.mock_config)
    
    def test_go_parent_focuses_on_child_directory(self):
        """Test that navigating to parent focuses on the child directory we came from."""
        # Set up current pane in a subdirectory
        current_pane = self.fm.get_current_pane()
        test_dir = Path('/home/user/documents')
        current_pane['path'] = test_dir
        
        # Mock parent directory files (including 'documents' directory)
        parent_files = [
            Path('/home/user/desktop'),
            Path('/home/user/documents'),  # This should be focused
            Path('/home/user/downloads'),
            Path('/home/user/pictures'),
        ]
        
        # Mock refresh_files to populate the files list
        def mock_refresh_files(pane):
            pane['files'] = parent_files
        
        with patch.object(self.fm, 'refresh_files', side_effect=mock_refresh_files), \
             patch.object(self.fm, 'save_cursor_position'), \
             patch.object(self.fm, 'mark_dirty'):
            
            # Execute go_parent action
            result = self.fm._action_go_parent()
            
            # Verify action succeeded
            self.assertTrue(result)
            
            # Verify we navigated to parent
            self.assertEqual(current_pane['path'], Path('/home/user'))
            
            # Verify cursor is focused on 'documents' directory (index 1)
            self.assertEqual(current_pane['focused_index'], 1)
    
    def test_go_parent_adjusts_scroll_offset_for_visibility(self):
        """Test that scroll offset is adjusted to keep focused item visible."""
        current_pane = self.fm.get_current_pane()
        test_dir = Path('/home/user/zzz_last_dir')
        current_pane['path'] = test_dir
        
        # Create many files in parent so 'zzz_last_dir' would be off-screen
        parent_files = [Path(f'/home/user/dir_{i:03d}') for i in range(50)]
        parent_files.append(Path('/home/user/zzz_last_dir'))  # Last item
        
        def mock_refresh_files(pane):
            pane['files'] = parent_files
        
        with patch.object(self.fm, 'refresh_files', side_effect=mock_refresh_files), \
             patch.object(self.fm, 'save_cursor_position'), \
             patch.object(self.fm, 'mark_dirty'):
            
            # Execute go_parent action
            self.fm._action_go_parent()
            
            # Verify cursor is on last item
            self.assertEqual(current_pane['focused_index'], 50)
            
            # Verify scroll offset was adjusted (should not be 0)
            # With display_height of 20 (24 - 4), scroll should be adjusted
            self.assertGreater(current_pane['scroll_offset'], 0)
    
    def test_go_parent_at_root_does_nothing(self):
        """Test that go_parent at root directory does nothing."""
        current_pane = self.fm.get_current_pane()
        root_path = Path('/')
        current_pane['path'] = root_path
        
        with patch.object(self.fm, 'refresh_files') as mock_refresh, \
             patch.object(self.fm, 'mark_dirty') as mock_dirty:
            
            # Execute go_parent action at root
            result = self.fm._action_go_parent()
            
            # Verify action returned True but did nothing
            self.assertTrue(result)
            self.assertEqual(current_pane['path'], root_path)
            mock_refresh.assert_not_called()
            mock_dirty.assert_not_called()
    
    def test_go_parent_child_not_found_keeps_default_position(self):
        """Test that if child directory is not found in parent, cursor stays at top."""
        current_pane = self.fm.get_current_pane()
        test_dir = Path('/home/user/deleted_dir')
        current_pane['path'] = test_dir
        
        # Parent files don't include 'deleted_dir'
        parent_files = [
            Path('/home/user/documents'),
            Path('/home/user/downloads'),
        ]
        
        def mock_refresh_files(pane):
            pane['files'] = parent_files
        
        with patch.object(self.fm, 'refresh_files', side_effect=mock_refresh_files), \
             patch.object(self.fm, 'save_cursor_position'), \
             patch.object(self.fm, 'mark_dirty'):
            
            # Execute go_parent action
            self.fm._action_go_parent()
            
            # Verify cursor stays at default position (0)
            self.assertEqual(current_pane['focused_index'], 0)
            self.assertEqual(current_pane['scroll_offset'], 0)


if __name__ == '__main__':
    unittest.main()
