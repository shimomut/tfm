#!/usr/bin/env python3
"""
Integration test for TFM initialization with TTK renderer
"""
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_tfm_can_initialize_with_curses_backend():
    """Test that TFM can initialize with CursesBackend"""
    from tfm_main import FileManager
    
    # Create a mock CursesBackend
    mock_backend = Mock()
    mock_backend.set_cursor_visibility = Mock()
    mock_backend.get_dimensions = Mock(return_value=(24, 80))
    mock_backend.getmaxyx = Mock(return_value=(24, 80))  # For compatibility
    
    # Mock all the dependencies
    with patch('tfm_main.init_colors'):
        with patch('tfm_main.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.COLOR_SCHEME = 'dark'
            mock_config.DEFAULT_LOG_HEIGHT_RATIO = 0.3
            mock_config.SHOW_HIDDEN_FILES = False
            mock_config.SORT_MODE = 'name'
            mock_config.SORT_REVERSE = False
            mock_get_config.return_value = mock_config
            
            with patch('tfm_main.LogManager'):
                with patch('tfm_main.get_state_manager'):
                    with patch('tfm_main.PaneManager'):
                        with patch('tfm_main.FileOperations'):
                            # This should not raise an exception
                            fm = FileManager(mock_backend)
                            
                            # Verify the renderer was set up correctly
                            assert fm.renderer is mock_backend
                            assert fm.stdscr is mock_backend
                            
                            # Verify cursor was hidden
                            mock_backend.set_cursor_visibility.assert_called_once_with(False)
    
    print("✓ TFM can initialize with CursesBackend")

def test_renderer_and_stdscr_are_same_object():
    """Test that renderer and stdscr point to the same object for compatibility"""
    from tfm_main import FileManager
    
    mock_renderer = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    mock_renderer.get_dimensions = Mock(return_value=(24, 80))
    
    with patch('tfm_main.init_colors'):
        with patch('tfm_main.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.COLOR_SCHEME = 'dark'
            mock_config.DEFAULT_LOG_HEIGHT_RATIO = 0.3
            mock_get_config.return_value = mock_config
            
            with patch('tfm_main.LogManager'):
                with patch('tfm_main.get_state_manager'):
                    with patch('tfm_main.PaneManager'):
                        with patch('tfm_main.FileOperations'):
                            fm = FileManager(mock_renderer)
                            
                            # Both should point to the same object
                            assert fm.renderer is fm.stdscr
                            assert fm.renderer is mock_renderer
    
    print("✓ renderer and stdscr are the same object")

if __name__ == '__main__':
    print("Testing TFM initialization integration...")
    print()
    
    test_tfm_can_initialize_with_curses_backend()
    print()
    
    test_renderer_and_stdscr_are_same_object()
    print()
    
    print("All integration tests passed! ✓")
