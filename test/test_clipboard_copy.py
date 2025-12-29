"""
Tests for clipboard copy name/path functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_clipboard_copy.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from tfm_main import FileManager
from tfm_menu_manager import MenuManager


class TestClipboardCopy(unittest.TestCase):
    """Test clipboard copy name and path features"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer with clipboard support
        self.mock_renderer = Mock()
        self.mock_renderer.is_desktop_mode.return_value = True
        self.mock_renderer.supports_clipboard.return_value = True
        self.mock_renderer.set_clipboard_text.return_value = True
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock file manager
        self.mock_fm = Mock(spec=FileManager)
        self.mock_fm.renderer = self.mock_renderer
        self.mock_fm.logger = Mock()
        self.mock_fm.is_desktop_mode.return_value = True
        self.mock_fm.mark_dirty = Mock()
        
        # Create mock Path objects with exists() returning True
        self.test_files = []
        for path_str in ['/test/file1.txt', '/test/file2.txt', '/test/dir1']:
            mock_path = Mock(spec=Path)
            mock_path.__str__ = Mock(return_value=path_str)
            mock_path.name = path_str.split('/')[-1]
            mock_path.exists.return_value = True
            mock_path.resolve.return_value = mock_path
            self.test_files.append(mock_path)
        
        self.mock_pane = {
            'path': Path('/test'),
            'files': self.test_files,
            'focused_index': 0,
            'selected_files': set()
        }
        
        self.mock_fm.get_current_pane.return_value = self.mock_pane
        
        # Bind action methods to mock
        self.mock_fm._action_copy_names = lambda: FileManager._action_copy_names(self.mock_fm)
        self.mock_fm._action_copy_paths = lambda: FileManager._action_copy_paths(self.mock_fm)
    
    def test_copy_names_single_selected_file(self):
        """Test copying name of single selected file"""
        # Select one file
        self.mock_pane['selected_files'] = {str(self.test_files[0])}
        
        # Call action
        result = self.mock_fm._action_copy_names()
        
        # Verify clipboard was set with file name
        self.assertTrue(result)
        self.mock_renderer.set_clipboard_text.assert_called_once_with('file1.txt')
        self.mock_fm.logger.info.assert_called()
    
    def test_copy_names_multiple_selected_files(self):
        """Test copying names of multiple selected files"""
        # Select multiple files
        self.mock_pane['selected_files'] = {
            str(self.test_files[0]),
            str(self.test_files[1])
        }
        
        # Call action
        result = self.mock_fm._action_copy_names()
        
        # Verify clipboard was set with file names (one per line)
        self.assertTrue(result)
        call_args = self.mock_renderer.set_clipboard_text.call_args[0][0]
        self.assertIn('file1.txt', call_args)
        self.assertIn('file2.txt', call_args)
        self.assertIn('\n', call_args)
    
    def test_copy_names_focused_file_when_no_selection(self):
        """Test copying name of focused file when nothing selected"""
        # No selection, focused on first file
        self.mock_pane['selected_files'] = set()
        self.mock_pane['focused_index'] = 0
        
        # Call action
        result = self.mock_fm._action_copy_names()
        
        # Verify clipboard was set with focused file name
        self.assertTrue(result)
        self.mock_renderer.set_clipboard_text.assert_called_once_with('file1.txt')
    
    def test_copy_paths_single_selected_file(self):
        """Test copying full path of single selected file"""
        # Select one file
        self.mock_pane['selected_files'] = {str(self.test_files[0])}
        
        # Call action
        result = self.mock_fm._action_copy_paths()
        
        # Verify clipboard was set with full path
        self.assertTrue(result)
        call_args = self.mock_renderer.set_clipboard_text.call_args[0][0]
        self.assertIn('/test/file1.txt', call_args)
    
    def test_copy_paths_multiple_selected_files(self):
        """Test copying full paths of multiple selected files"""
        # Select multiple files
        self.mock_pane['selected_files'] = {
            str(self.test_files[0]),
            str(self.test_files[1])
        }
        
        # Call action
        result = self.mock_fm._action_copy_paths()
        
        # Verify clipboard was set with full paths (one per line)
        self.assertTrue(result)
        call_args = self.mock_renderer.set_clipboard_text.call_args[0][0]
        self.assertIn('/test/file1.txt', call_args)
        self.assertIn('/test/file2.txt', call_args)
        self.assertIn('\n', call_args)
    
    def test_copy_names_no_clipboard_support(self):
        """Test copy names fails gracefully when clipboard not supported"""
        # Disable clipboard support
        self.mock_renderer.supports_clipboard.return_value = False
        
        # Call action
        result = self.mock_fm._action_copy_names()
        
        # Verify it failed gracefully
        self.assertFalse(result)
        self.mock_fm.logger.error.assert_called()
        self.mock_renderer.set_clipboard_text.assert_not_called()
    
    def test_copy_paths_no_clipboard_support(self):
        """Test copy paths fails gracefully when clipboard not supported"""
        # Disable clipboard support
        self.mock_renderer.supports_clipboard.return_value = False
        
        # Call action
        result = self.mock_fm._action_copy_paths()
        
        # Verify it failed gracefully
        self.assertFalse(result)
        self.mock_fm.logger.error.assert_called()
        self.mock_renderer.set_clipboard_text.assert_not_called()
    
    def test_copy_names_terminal_mode(self):
        """Test copy names fails in terminal mode"""
        # Switch to terminal mode
        self.mock_fm.is_desktop_mode.return_value = False
        
        # Call action
        result = self.mock_fm._action_copy_names()
        
        # Verify it failed
        self.assertFalse(result)
        self.mock_fm.logger.error.assert_called()
    
    def test_copy_names_empty_directory(self):
        """Test copy names fails gracefully when directory is empty"""
        # Empty directory - no files
        self.mock_pane['files'] = []
        self.mock_pane['selected_files'] = set()
        
        # Call action
        result = self.mock_fm._action_copy_names()
        
        # Verify it failed gracefully
        self.assertFalse(result)
        self.mock_fm.logger.error.assert_called_with("No files to copy names from")
    
    def test_copy_paths_empty_directory(self):
        """Test copy paths fails gracefully when directory is empty"""
        # Empty directory - no files
        self.mock_pane['files'] = []
        self.mock_pane['selected_files'] = set()
        
        # Call action
        result = self.mock_fm._action_copy_paths()
        
        # Verify it failed gracefully
        self.assertFalse(result)
        self.mock_fm.logger.error.assert_called_with("No files to copy paths from")
    
    def test_menu_states_with_selection(self):
        """Test menu items enabled when files selected"""
        menu_manager = MenuManager(self.mock_fm)
        
        # Set up selection
        self.mock_pane['selected_files'] = {str(self.test_files[0])}
        
        # Get menu states
        states = menu_manager.update_menu_states()
        
        # Verify copy name/path items are enabled
        self.assertTrue(states[MenuManager.EDIT_COPY_NAMES])
        self.assertTrue(states[MenuManager.EDIT_COPY_PATHS])
    
    def test_menu_states_without_selection(self):
        """Test menu items enabled even when no files selected (uses focused item)"""
        menu_manager = MenuManager(self.mock_fm)
        
        # No selection
        self.mock_pane['selected_files'] = set()
        
        # Get menu states
        states = menu_manager.update_menu_states()
        
        # Verify copy name/path items are still enabled (will use focused item)
        self.assertTrue(states[MenuManager.EDIT_COPY_NAMES])
        self.assertTrue(states[MenuManager.EDIT_COPY_PATHS])
