"""
Test TFM main rendering migration to TTK API.
Verifies that tfm_main.py uses TTK renderer API correctly.

Run with: PYTHONPATH=.:src:ttk pytest test/test_tfm_main_ttk_rendering.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call

from tfm_main import FileManager
from tfm_path import Path


class TestTFMMainTTKRendering(unittest.TestCase):
    """Test that tfm_main.py uses TTK rendering API correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions = Mock(return_value=(24, 80))
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.clear = Mock()
        self.mock_renderer.refresh = Mock()
        self.mock_renderer.draw_hline = Mock()
        self.mock_renderer.draw_vline = Mock()
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.get_input = Mock(return_value=None)
        
    @patch('tfm_main.get_state_manager')
    @patch('tfm_main.LogManager')
    @patch('tfm_main.init_colors')
    @patch('tfm_main.get_config')
    def test_file_manager_uses_renderer_get_dimensions(self, mock_config, mock_init_colors, 
                                                       mock_log_manager, mock_state_manager):
        """Test that FileManager uses renderer.get_dimensions() instead of stdscr.getmaxyx()"""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.COLOR_SCHEME = 'dark'
        mock_config_instance.DEFAULT_LOG_HEIGHT_RATIO = 0.25
        mock_config_instance.SHOW_HIDDEN_FILES = False
        mock_config.return_value = mock_config_instance
        
        mock_log_instance = Mock()
        mock_log_manager.return_value = mock_log_instance
        
        mock_state_instance = Mock()
        mock_state_instance.load_window_layout = Mock(return_value=None)
        mock_state_instance.load_pane_state = Mock(return_value=None)
        mock_state_instance.update_session_heartbeat = Mock()
        mock_state_instance.cleanup_non_existing_directories = Mock()
        mock_state_manager.return_value = mock_state_instance
        
        # Create FileManager with mock renderer
        fm = FileManager(self.mock_renderer)
        
        # Verify renderer.get_dimensions was called (not stdscr.getmaxyx)
        self.mock_renderer.get_dimensions.assert_called()
        
    @patch('tfm_main.get_state_manager')
    @patch('tfm_main.LogManager')
    @patch('tfm_main.init_colors')
    @patch('tfm_main.get_config')
    def test_file_manager_uses_renderer_clear(self, mock_config, mock_init_colors,
                                              mock_log_manager, mock_state_manager):
        """Test that FileManager uses renderer.clear() instead of stdscr.clear()"""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.COLOR_SCHEME = 'dark'
        mock_config_instance.DEFAULT_LOG_HEIGHT_RATIO = 0.25
        mock_config_instance.SHOW_HIDDEN_FILES = False
        mock_config.return_value = mock_config_instance
        
        mock_log_instance = Mock()
        mock_log_manager.return_value = mock_log_instance
        
        mock_state_instance = Mock()
        mock_state_instance.load_window_layout = Mock(return_value=None)
        mock_state_instance.load_pane_state = Mock(return_value=None)
        mock_state_instance.update_session_heartbeat = Mock()
        mock_state_instance.cleanup_non_existing_directories = Mock()
        mock_state_manager.return_value = mock_state_instance
        
        # Create FileManager with mock renderer
        fm = FileManager(self.mock_renderer)
        
        # Call clear_screen_with_background
        fm.clear_screen_with_background()
        
        # Verify renderer.clear was called (not stdscr.clear)
        self.mock_renderer.clear.assert_called()
        
    @patch('tfm_main.get_state_manager')
    @patch('tfm_main.LogManager')
    @patch('tfm_main.init_colors')
    @patch('tfm_main.get_config')
    def test_file_manager_uses_renderer_draw_text(self, mock_config, mock_init_colors,
                                                   mock_log_manager, mock_state_manager):
        """Test that FileManager uses renderer.draw_text() instead of stdscr.addstr()"""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.COLOR_SCHEME = 'dark'
        mock_config_instance.DEFAULT_LOG_HEIGHT_RATIO = 0.25
        mock_config_instance.SHOW_HIDDEN_FILES = False
        mock_config.return_value = mock_config_instance
        
        mock_log_instance = Mock()
        mock_log_manager.return_value = mock_log_instance
        
        mock_state_instance = Mock()
        mock_state_instance.load_window_layout = Mock(return_value=None)
        mock_state_instance.load_pane_state = Mock(return_value=None)
        mock_state_instance.update_session_heartbeat = Mock()
        mock_state_instance.cleanup_non_existing_directories = Mock()
        mock_state_manager.return_value = mock_state_instance
        
        # Create FileManager with mock renderer
        fm = FileManager(self.mock_renderer)
        
        # Call safe_addstr with a tuple (color_pair, attributes)
        from ttk import TextAttribute
        fm.safe_addstr(0, 0, "Test", (0, TextAttribute.NORMAL))
        
        # Verify renderer.draw_text was called (not stdscr.addstr)
        self.mock_renderer.draw_text.assert_called()
        
    @patch('tfm_main.get_state_manager')
    @patch('tfm_main.LogManager')
    @patch('tfm_main.init_colors')
    @patch('tfm_main.get_config')
    def test_file_manager_uses_renderer_refresh(self, mock_config, mock_init_colors,
                                                 mock_log_manager, mock_state_manager):
        """Test that FileManager uses renderer.refresh() instead of stdscr.refresh()"""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.COLOR_SCHEME = 'dark'
        mock_config_instance.DEFAULT_LOG_HEIGHT_RATIO = 0.25
        mock_config_instance.SHOW_HIDDEN_FILES = False
        mock_config.return_value = mock_config_instance
        
        mock_log_instance = Mock()
        mock_log_manager.return_value = mock_log_instance
        
        mock_state_instance = Mock()
        mock_state_instance.load_window_layout = Mock(return_value=None)
        mock_state_instance.load_pane_state = Mock(return_value=None)
        mock_state_instance.update_session_heartbeat = Mock()
        mock_state_instance.cleanup_non_existing_directories = Mock()
        mock_state_manager.return_value = mock_state_instance
        
        # Create FileManager with mock renderer
        fm = FileManager(self.mock_renderer)
        
        # Call show_error which should use renderer.refresh
        fm.show_error("Test error")
        
        # Verify renderer.refresh was called (not stdscr.refresh)
        self.mock_renderer.refresh.assert_called()
