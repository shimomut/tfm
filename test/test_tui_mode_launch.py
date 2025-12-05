#!/usr/bin/env python3
"""
Integration test for TUI mode launch

This test verifies that tfm.py launches correctly in TUI mode with:
- Curses initialization
- CursesBackend creation
- TFMApplication initialization
- Dual-pane layout setup
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import curses

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_curses_backend import CursesBackend
from tfm_application import TFMApplication
from tfm_ui_backend import IUIBackend


class TestTUIModelaunch(unittest.TestCase):
    """Test TUI mode launch integration"""
    
    def test_curses_backend_implements_interface(self):
        """Verify CursesBackend implements IUIBackend interface"""
        # Check that CursesBackend is a subclass of IUIBackend
        self.assertTrue(issubclass(CursesBackend, IUIBackend))
        print("✓ CursesBackend implements IUIBackend interface")
    
    def test_curses_backend_initialization(self):
        """Verify CursesBackend can be initialized with stdscr"""
        # Create mock stdscr
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        
        # Create backend
        backend = CursesBackend(mock_stdscr)
        
        # Verify backend was created
        self.assertIsNotNone(backend)
        self.assertEqual(backend.stdscr, mock_stdscr)
        print("✓ CursesBackend can be initialized with stdscr")
    
    @patch('tfm_curses_backend.init_colors')
    @patch('tfm_curses_backend.curses.curs_set')
    def test_curses_backend_initialize_method(self, mock_curs_set, mock_init_colors):
        """Verify CursesBackend.initialize() sets up curses environment"""
        # Create mock stdscr
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        
        # Create backend
        backend = CursesBackend(mock_stdscr)
        
        # Initialize backend
        backend.initialize()
        
        # Verify curses setup was called
        mock_stdscr.keypad.assert_called_once_with(True)
        mock_curs_set.assert_called_once_with(0)
        mock_init_colors.assert_called_once()
        print("✓ CursesBackend.initialize() sets up curses environment")
    
    @patch('tfm_application.LogManager')
    @patch('tfm_application.get_state_manager')
    @patch('tfm_application.get_config')
    def test_application_accepts_curses_backend(self, mock_config, mock_state_mgr, mock_log_mgr):
        """Verify TFMApplication accepts CursesBackend"""
        # Setup mocks
        mock_config.return_value = Mock()
        mock_state_mgr.return_value = Mock()
        mock_log_mgr.return_value = Mock()
        
        # Create mock backend
        mock_backend = Mock(spec=IUIBackend)
        mock_backend.get_screen_size.return_value = (24, 80)
        
        # Create application with backend
        app = TFMApplication(
            ui_backend=mock_backend,
            remote_log_port=None,
            left_dir=None,
            right_dir=None
        )
        
        # Verify application was created with backend
        self.assertIsNotNone(app)
        self.assertEqual(app.ui, mock_backend)
        print("✓ TFMApplication accepts CursesBackend")
    
    @patch('tfm_application.LogManager')
    @patch('tfm_application.get_state_manager')
    @patch('tfm_application.get_config')
    def test_application_has_run_method(self, mock_config, mock_state_mgr, mock_log_mgr):
        """Verify TFMApplication has run() method"""
        # Setup mocks
        mock_config.return_value = Mock()
        mock_state_mgr.return_value = Mock()
        mock_log_mgr.return_value = Mock()
        
        # Create mock backend
        mock_backend = Mock(spec=IUIBackend)
        mock_backend.get_screen_size.return_value = (24, 80)
        
        # Create application
        app = TFMApplication(
            ui_backend=mock_backend,
            remote_log_port=None,
            left_dir=None,
            right_dir=None
        )
        
        # Verify run method exists
        self.assertTrue(hasattr(app, 'run'))
        self.assertTrue(callable(app.run))
        print("✓ TFMApplication has run() method")
    
    @patch('tfm_application.LogManager')
    @patch('tfm_application.get_state_manager')
    @patch('tfm_application.get_config')
    @patch('tfm_application.PaneManager')
    def test_dual_pane_layout_initialized(self, mock_pane_mgr, mock_config, mock_state_mgr, mock_log_mgr):
        """Verify dual-pane layout is initialized"""
        # Setup mocks
        mock_config.return_value = Mock()
        mock_state_mgr.return_value = Mock()
        mock_log_mgr.return_value = Mock()
        
        # Create mock pane manager
        mock_pane_instance = Mock()
        mock_pane_instance.left_pane = {'path': Path('/tmp'), 'files': []}
        mock_pane_instance.right_pane = {'path': Path('/home'), 'files': []}
        mock_pane_mgr.return_value = mock_pane_instance
        
        # Create mock backend
        mock_backend = Mock(spec=IUIBackend)
        mock_backend.get_screen_size.return_value = (24, 80)
        
        # Create application
        app = TFMApplication(
            ui_backend=mock_backend,
            remote_log_port=None,
            left_dir=None,
            right_dir=None
        )
        
        # Verify pane manager was created
        self.assertIsNotNone(app.pane_manager)
        print("✓ Dual-pane layout is initialized")
    
    def test_entry_point_structure(self):
        """Verify tfm.py has correct structure for curses backend"""
        # Read tfm.py
        tfm_path = Path(__file__).parent.parent / 'tfm.py'
        with open(tfm_path, 'r') as f:
            content = f.read()
        
        # Verify imports
        self.assertIn('from tfm_curses_backend import CursesBackend', content)
        self.assertIn('from tfm_application import TFMApplication', content)
        
        # Verify backend creation
        self.assertIn('backend = CursesBackend(stdscr)', content)
        self.assertIn('backend.initialize()', content)
        
        # Verify application creation
        self.assertIn('app = TFMApplication', content)
        self.assertIn('ui_backend=backend', content)
        
        # Verify run call
        self.assertIn('app.run()', content)
        
        print("✓ tfm.py has correct structure for curses backend")


def run_tests():
    """Run all tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTUIModelaunch)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
