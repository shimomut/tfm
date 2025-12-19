#!/usr/bin/env python3
"""
Test TFM main initialization with TTK renderer
"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_file_manager_accepts_renderer():
    """Test that FileManager.__init__ accepts a renderer parameter"""
    from tfm_main import FileManager
    
    # Create a mock renderer
    mock_renderer = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    mock_renderer.get_dimensions = Mock(return_value=(24, 80))
    
    # Mock the init_colors function to avoid actual color initialization
    with patch('tfm_main.init_colors') as mock_init_colors:
        # Mock get_config to return a simple config
        with patch('tfm_main.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.COLOR_SCHEME = 'dark'
            mock_config.DEFAULT_LOG_HEIGHT_RATIO = 0.3
            mock_config.SHOW_HIDDEN_FILES = False
            mock_config.SORT_MODE = 'name'
            mock_config.SORT_REVERSE = False
            mock_get_config.return_value = mock_config
            
            # Mock other dependencies
            with patch('tfm_main.LogManager'):
                with patch('tfm_main.get_state_manager'):
                    with patch('tfm_main.PaneManager'):
                        with patch('tfm_main.FileOperations'):
                            # Create FileManager with renderer
                            fm = FileManager(mock_renderer)
                            
                            # Verify renderer was stored
                            assert fm.renderer is mock_renderer
                            assert fm.stdscr is mock_renderer  # Compatibility alias
                            
                            # Verify init_colors was called with renderer
                            mock_init_colors.assert_called_once()
                            args = mock_init_colors.call_args[0]
                            assert args[0] is mock_renderer
                            assert args[1] == 'dark'
                            
                            # Verify focus was hidden
                            mock_renderer.set_cursor_visibility.assert_called_once_with(False)
    
    print("✓ FileManager accepts renderer parameter")
    print("✓ FileManager stores renderer correctly")
    print("✓ init_colors called with renderer")
    print("✓ Cursor visibility set correctly")

def test_main_function_accepts_renderer():
    """Test that main() function accepts a renderer parameter"""
    from tfm_main import main
    import inspect
    
    # Check function signature
    sig = inspect.signature(main)
    params = list(sig.parameters.keys())
    
    # First parameter should be 'renderer'
    assert params[0] == 'renderer', f"Expected first parameter to be 'renderer', got '{params[0]}'"
    
    print("✓ main() function accepts renderer as first parameter")

def test_main_function_passes_renderer_to_file_manager():
    """Test that main() passes renderer to FileManager"""
    from tfm_main import main
    
    # Create a mock renderer
    mock_renderer = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    mock_renderer.get_dimensions = Mock(return_value=(24, 80))
    
    # Mock FileManager to capture initialization
    with patch('tfm_main.FileManager') as MockFileManager:
        mock_fm_instance = Mock()
        mock_fm_instance.run = Mock()
        mock_fm_instance.restore_stdio = Mock()
        MockFileManager.return_value = mock_fm_instance
        
        # Mock cleanup_state_manager
        with patch('tfm_main.cleanup_state_manager'):
            # Call main with renderer
            main(mock_renderer)
            
            # Verify FileManager was created with renderer
            MockFileManager.assert_called_once()
            args = MockFileManager.call_args[0]
            assert args[0] is mock_renderer
            
            # Verify run was called
            mock_fm_instance.run.assert_called_once()
    
    print("✓ main() passes renderer to FileManager")
    print("✓ FileManager.run() is called")

if __name__ == '__main__':
    print("Testing TFM main initialization with TTK renderer...")
    print()
    
    test_file_manager_accepts_renderer()
    print()
    
    test_main_function_accepts_renderer()
    print()
    
    test_main_function_passes_renderer_to_file_manager()
    print()
    
    print("All tests passed! ✓")
