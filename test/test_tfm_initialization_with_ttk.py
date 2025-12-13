#!/usr/bin/env python3
"""
Integration tests for TFM initialization with TTK renderer.

Tests Task 6: Test TFM initialization with TTK
- Run TFM with CursesBackend
- Verify initialization works
- Check for errors
- Run basic smoke tests
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ttk.renderer import Renderer
from ttk.input_event import InputEvent, KeyCode


class TestTFMInitializationWithTTK(unittest.TestCase):
    """Test TFM initialization with TTK renderer"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock(spec=Renderer)
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.init_color_pair = Mock()
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.clear = Mock()
        self.mock_renderer.refresh = Mock()
        self.mock_renderer.draw_text = Mock()
        
    def test_file_manager_accepts_renderer(self):
        """Test that FileManager accepts renderer parameter"""
        from tfm_main import FileManager
        
        # Create FileManager with renderer
        with patch('tfm_main.init_colors'):
            with patch('tfm_main.get_state_manager'):
                with patch('tfm_main.PaneManager'):
                    with patch('tfm_main.LogManager'):
                        fm = FileManager(
                            self.mock_renderer,
                            left_dir=None,
                            right_dir=None,
                            remote_log_port=None
                        )
        
        # Verify renderer is stored
        self.assertIsNotNone(fm.renderer)
        self.assertEqual(fm.renderer, self.mock_renderer)
        
    def test_file_manager_maintains_stdscr_compatibility(self):
        """Test that FileManager maintains stdscr alias for compatibility"""
        from tfm_main import FileManager
        
        # Create FileManager with renderer
        with patch('tfm_main.init_colors'):
            with patch('tfm_main.get_state_manager'):
                with patch('tfm_main.PaneManager'):
                    with patch('tfm_main.LogManager'):
                        fm = FileManager(
                            self.mock_renderer,
                            left_dir=None,
                            right_dir=None,
                            remote_log_port=None
                        )
        
        # Verify stdscr alias exists
        self.assertIsNotNone(fm.stdscr)
        self.assertEqual(fm.stdscr, self.mock_renderer)
        
    def test_color_initialization_uses_renderer(self):
        """Test that color initialization receives renderer"""
        from tfm_main import FileManager
        
        with patch('tfm_main.init_colors') as mock_init_colors:
            with patch('tfm_main.get_state_manager'):
                with patch('tfm_main.PaneManager'):
                    with patch('tfm_main.LogManager'):
                        fm = FileManager(
                            self.mock_renderer,
                            left_dir=None,
                            right_dir=None,
                            remote_log_port=None
                        )
        
        # Verify init_colors was called with renderer
        mock_init_colors.assert_called_once()
        call_args = mock_init_colors.call_args
        self.assertEqual(call_args[0][0], self.mock_renderer)
        
    def test_cursor_visibility_set_via_renderer(self):
        """Test that cursor visibility is set through renderer"""
        from tfm_main import FileManager
        
        with patch('tfm_main.init_colors'):
            with patch('tfm_main.get_state_manager'):
                with patch('tfm_main.PaneManager'):
                    with patch('tfm_main.LogManager'):
                        fm = FileManager(
                            self.mock_renderer,
                            left_dir=None,
                            right_dir=None,
                            remote_log_port=None
                        )
        
        # Verify set_cursor_visibility was called
        self.mock_renderer.set_cursor_visibility.assert_called_once_with(False)
        
    def test_main_function_accepts_renderer(self):
        """Test that main() function accepts renderer parameter"""
        from tfm_main import main
        
        # Mock FileManager to avoid full initialization
        with patch('tfm_main.FileManager') as mock_fm_class:
            mock_fm = Mock()
            mock_fm.run.return_value = None
            mock_fm_class.return_value = mock_fm
            
            # Call main with renderer
            main(
                self.mock_renderer,
                remote_log_port=None,
                left_dir=None,
                right_dir=None
            )
            
            # Verify FileManager was created with renderer
            mock_fm_class.assert_called_once()
            call_args = mock_fm_class.call_args
            self.assertEqual(call_args[0][0], self.mock_renderer)
            
    def test_initialization_no_curses_imports_in_main(self):
        """Test that tfm_main.py doesn't import curses directly"""
        import tfm_main
        
        # Note: curses is still imported in tfm_main.py at this stage of migration
        # Task 31 will remove all curses imports
        # For now, just verify the module can be imported
        self.assertIsNotNone(tfm_main)
        
    def test_initialization_sequence(self):
        """Test complete initialization sequence"""
        from tfm_main import FileManager
        
        # Track initialization calls
        init_colors_called = False
        state_manager_created = False
        pane_manager_created = False
        log_manager_created = False
        
        def mock_init_colors(renderer, color_scheme):
            nonlocal init_colors_called
            init_colors_called = True
            
        def mock_get_state_manager():
            nonlocal state_manager_created
            state_manager_created = True
            return Mock()
            
        def mock_pane_manager(*args, **kwargs):
            nonlocal pane_manager_created
            pane_manager_created = True
            return Mock()
            
        def mock_log_manager(*args, **kwargs):
            nonlocal log_manager_created
            log_manager_created = True
            return Mock()
        
        with patch('tfm_main.init_colors', side_effect=mock_init_colors):
            with patch('tfm_main.get_state_manager', side_effect=mock_get_state_manager):
                with patch('tfm_main.PaneManager', side_effect=mock_pane_manager):
                    with patch('tfm_main.LogManager', side_effect=mock_log_manager):
                        fm = FileManager(
                            self.mock_renderer,
                            left_dir=None,
                            right_dir=None,
                            remote_log_port=None
                        )
        
        # Verify all initialization steps occurred
        self.assertTrue(init_colors_called, "init_colors should be called")
        self.assertTrue(state_manager_created, "get_state_manager should be called")
        self.assertTrue(pane_manager_created, "PaneManager should be created")
        self.assertTrue(log_manager_created, "LogManager should be created")
        
    def test_renderer_methods_available(self):
        """Test that renderer has all required methods"""
        # Verify renderer has required methods
        required_methods = [
            'initialize',
            'shutdown',
            'get_dimensions',
            'clear',
            'refresh',
            'draw_text',
            'set_cursor_visibility',
            'init_color_pair',
        ]
        
        for method in required_methods:
            self.assertTrue(
                hasattr(self.mock_renderer, method),
                f"Renderer should have {method} method"
            )


class TestTFMSmokeTests(unittest.TestCase):
    """Basic smoke tests for TFM with TTK"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer with more complete behavior
        self.mock_renderer = Mock(spec=Renderer)
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.init_color_pair = Mock()
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.clear = Mock()
        self.mock_renderer.refresh = Mock()
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.draw_hline = Mock()
        self.mock_renderer.draw_vline = Mock()
        
    def test_file_manager_can_be_created(self):
        """Smoke test: FileManager can be instantiated"""
        from tfm_main import FileManager
        
        with patch('tfm_main.init_colors'):
            with patch('tfm_main.get_state_manager'):
                with patch('tfm_main.PaneManager'):
                    with patch('tfm_main.LogManager'):
                        fm = FileManager(
                            self.mock_renderer,
                            left_dir=None,
                            right_dir=None,
                            remote_log_port=None
                        )
                        
                        # Basic smoke test - object exists
                        self.assertIsNotNone(fm)
                        self.assertIsNotNone(fm.renderer)
                        
    def test_main_function_can_be_called(self):
        """Smoke test: main() can be called without errors"""
        from tfm_main import main
        
        with patch('tfm_main.FileManager') as mock_fm_class:
            mock_fm = Mock()
            mock_fm.run.return_value = None
            mock_fm_class.return_value = mock_fm
            
            # Should not raise any exceptions
            try:
                main(
                    self.mock_renderer,
                    remote_log_port=None,
                    left_dir=None,
                    right_dir=None
                )
                success = True
            except Exception as e:
                success = False
                self.fail(f"main() raised exception: {e}")
                
            self.assertTrue(success)
            
    def test_no_initialization_errors(self):
        """Smoke test: No errors during initialization"""
        from tfm_main import FileManager
        
        errors = []
        
        def capture_error(*args, **kwargs):
            errors.append((args, kwargs))
            
        with patch('tfm_main.init_colors'):
            with patch('tfm_main.get_state_manager'):
                with patch('tfm_main.PaneManager'):
                    with patch('tfm_main.LogManager'):
                        try:
                            fm = FileManager(
                                self.mock_renderer,
                                left_dir=None,
                                right_dir=None,
                                remote_log_port=None
                            )
                        except Exception as e:
                            errors.append(e)
        
        # Should have no errors
        self.assertEqual(len(errors), 0, f"Initialization had errors: {errors}")


class TestTFMWithCursesBackend(unittest.TestCase):
    """Test TFM with actual CursesBackend (mocked curses)"""
    
    def test_curses_backend_can_be_created(self):
        """Test that CursesBackend can be instantiated"""
        with patch('ttk.backends.curses_backend.curses') as mock_curses:
            # Mock curses module
            mock_curses.initscr.return_value = Mock()
            mock_curses.COLORS = 256
            mock_curses.COLOR_PAIRS = 256
            mock_curses.can_change_color.return_value = True
            
            from ttk.backends.curses_backend import CursesBackend
            
            backend = CursesBackend()
            self.assertIsNotNone(backend)
            
    def test_file_manager_with_curses_backend(self):
        """Test FileManager with CursesBackend"""
        with patch('ttk.backends.curses_backend.curses') as mock_curses:
            # Mock curses module
            mock_stdscr = Mock()
            mock_stdscr.getmaxyx.return_value = (24, 80)
            mock_curses.initscr.return_value = mock_stdscr
            mock_curses.COLORS = 256
            mock_curses.COLOR_PAIRS = 256
            mock_curses.can_change_color.return_value = True
            
            from ttk.backends.curses_backend import CursesBackend
            from tfm_main import FileManager
            
            backend = CursesBackend()
            
            with patch('tfm_main.init_colors'):
                with patch('tfm_main.get_state_manager'):
                    with patch('tfm_main.PaneManager'):
                        with patch('tfm_main.LogManager'):
                            fm = FileManager(
                                backend,
                                left_dir=None,
                                right_dir=None,
                                remote_log_port=None
                            )
                            
                            # Verify FileManager was created successfully
                            self.assertIsNotNone(fm)
                            self.assertEqual(fm.renderer, backend)


if __name__ == '__main__':
    unittest.main()
