#!/usr/bin/env python3
"""
Integration test for GUI mode launch

This test verifies that tfm_qt.py launches correctly in GUI mode with:
- Qt initialization
- QtBackend creation
- TFMApplication initialization
- Dual-pane layout setup
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_qt_backend import QtBackend
from tfm_application import TFMApplication
from tfm_ui_backend import IUIBackend


class TestGUIModeLaunch(unittest.TestCase):
    """Test GUI mode launch integration"""
    
    def test_qt_backend_implements_interface(self):
        """Verify QtBackend implements IUIBackend interface"""
        # Check that QtBackend is a subclass of IUIBackend
        self.assertTrue(issubclass(QtBackend, IUIBackend))
        print("✓ QtBackend implements IUIBackend interface")
    
    @patch('tfm_qt_backend.TFMMainWindow')
    @patch('tfm_qt_backend.FilePaneWidget')
    @patch('tfm_qt_backend.HeaderWidget')
    @patch('tfm_qt_backend.FooterWidget')
    @patch('tfm_qt_backend.LogPaneWidget')
    def test_qt_backend_initialization(self, mock_log_pane, mock_footer, 
                                      mock_header, mock_file_pane, mock_main_window):
        """Verify QtBackend can be initialized with QApplication"""
        # Create mock QApplication
        mock_app = Mock()
        
        # Setup mock widgets
        mock_main_window_instance = Mock()
        mock_main_window.return_value = mock_main_window_instance
        
        mock_file_pane_instance = Mock()
        mock_file_pane.return_value = mock_file_pane_instance
        
        mock_header_instance = Mock()
        mock_header.return_value = mock_header_instance
        
        mock_footer_instance = Mock()
        mock_footer.return_value = mock_footer_instance
        
        mock_log_pane_instance = Mock()
        mock_log_pane.return_value = mock_log_pane_instance
        
        # Create backend
        backend = QtBackend(mock_app)
        
        # Verify backend was created
        self.assertIsNotNone(backend)
        self.assertEqual(backend.app, mock_app)
        print("✓ QtBackend can be initialized with QApplication")
    
    @patch('tfm_qt_backend.TFMMainWindow')
    @patch('tfm_qt_backend.FilePaneWidget')
    @patch('tfm_qt_backend.HeaderWidget')
    @patch('tfm_qt_backend.FooterWidget')
    @patch('tfm_qt_backend.LogPaneWidget')
    def test_qt_backend_initialize_method(self, mock_log_pane, mock_footer,
                                         mock_header, mock_file_pane, mock_main_window):
        """Verify QtBackend.initialize() sets up Qt environment"""
        # Create mock QApplication
        mock_app = Mock()
        
        # Setup mock widgets
        mock_main_window_instance = Mock()
        mock_main_window.return_value = mock_main_window_instance
        
        mock_file_pane_instance = Mock()
        mock_file_pane.return_value = mock_file_pane_instance
        
        mock_header_instance = Mock()
        mock_header.return_value = mock_header_instance
        
        mock_footer_instance = Mock()
        mock_footer.return_value = mock_footer_instance
        
        mock_log_pane_instance = Mock()
        mock_log_pane.return_value = mock_log_pane_instance
        
        # Create backend
        backend = QtBackend(mock_app)
        
        # Initialize backend
        result = backend.initialize()
        
        # Verify initialization was successful
        self.assertTrue(result)
        
        # Verify main window was created and shown
        mock_main_window.assert_called_once()
        mock_main_window_instance.show.assert_called_once()
        
        # Verify widgets were created
        self.assertEqual(mock_file_pane.call_count, 2)  # Left and right panes
        mock_header.assert_called_once()
        mock_footer.assert_called_once()
        mock_log_pane.assert_called_once()
        
        print("✓ QtBackend.initialize() sets up Qt environment")
    
    @patch('tfm_application.LogManager')
    @patch('tfm_application.get_state_manager')
    @patch('tfm_application.get_config')
    def test_application_accepts_qt_backend(self, mock_config, mock_state_mgr, mock_log_mgr):
        """Verify TFMApplication accepts QtBackend"""
        # Setup mocks
        mock_config.return_value = Mock()
        mock_state_mgr.return_value = Mock()
        mock_log_mgr.return_value = Mock()
        
        # Create mock backend
        mock_backend = Mock(spec=IUIBackend)
        mock_backend.get_screen_size.return_value = (800, 1200)
        
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
        print("✓ TFMApplication accepts QtBackend")
    
    @patch('tfm_application.LogManager')
    @patch('tfm_application.get_state_manager')
    @patch('tfm_application.get_config')
    @patch('tfm_application.PaneManager')
    def test_dual_pane_layout_initialized(self, mock_pane_mgr, mock_config, 
                                         mock_state_mgr, mock_log_mgr):
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
        mock_backend.get_screen_size.return_value = (800, 1200)
        
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
    
    @patch('tfm_qt_backend.TFMMainWindow')
    @patch('tfm_qt_backend.FilePaneWidget')
    @patch('tfm_qt_backend.HeaderWidget')
    @patch('tfm_qt_backend.FooterWidget')
    @patch('tfm_qt_backend.LogPaneWidget')
    def test_qt_window_displayed(self, mock_log_pane, mock_footer,
                                 mock_header, mock_file_pane, mock_main_window):
        """Verify Qt window is displayed when backend is initialized"""
        # Create mock QApplication
        mock_app = Mock()
        
        # Setup mock main window
        mock_main_window_instance = Mock()
        mock_main_window.return_value = mock_main_window_instance
        
        # Setup other mock widgets
        mock_file_pane.return_value = Mock()
        mock_header.return_value = Mock()
        mock_footer.return_value = Mock()
        mock_log_pane.return_value = Mock()
        
        # Create and initialize backend
        backend = QtBackend(mock_app)
        backend.initialize()
        
        # Verify window was shown
        mock_main_window_instance.show.assert_called_once()
        print("✓ Qt window is displayed")
    
    @patch('tfm_qt_backend.TFMMainWindow')
    @patch('tfm_qt_backend.FilePaneWidget')
    @patch('tfm_qt_backend.HeaderWidget')
    @patch('tfm_qt_backend.FooterWidget')
    @patch('tfm_qt_backend.LogPaneWidget')
    def test_dual_pane_widgets_created(self, mock_log_pane, mock_footer,
                                       mock_header, mock_file_pane, mock_main_window):
        """Verify dual-pane widgets are created"""
        # Create mock QApplication
        mock_app = Mock()
        
        # Setup mock widgets
        mock_main_window.return_value = Mock()
        mock_file_pane.return_value = Mock()
        mock_header.return_value = Mock()
        mock_footer.return_value = Mock()
        mock_log_pane.return_value = Mock()
        
        # Create and initialize backend
        backend = QtBackend(mock_app)
        backend.initialize()
        
        # Verify two file pane widgets were created (left and right)
        self.assertEqual(mock_file_pane.call_count, 2)
        self.assertIsNotNone(backend.left_pane_widget)
        self.assertIsNotNone(backend.right_pane_widget)
        print("✓ Dual-pane widgets are created")
    
    def test_entry_point_structure(self):
        """Verify tfm_qt.py has correct structure for Qt backend"""
        # Read tfm_qt.py
        tfm_qt_path = Path(__file__).parent.parent / 'tfm_qt.py'
        
        # Check if file exists
        if not tfm_qt_path.exists():
            self.skipTest("tfm_qt.py not found - may not be implemented yet")
        
        with open(tfm_qt_path, 'r') as f:
            content = f.read()
        
        # Verify imports
        self.assertIn('from PySide6.QtWidgets import QApplication', content)
        self.assertIn('from tfm_qt_backend import QtBackend', content)
        self.assertIn('from tfm_application import TFMApplication', content)
        
        # Verify QApplication creation
        self.assertIn('app = QApplication', content)
        
        # Verify backend creation
        self.assertIn('backend = QtBackend(app)', content)
        self.assertIn('backend.initialize()', content)
        
        # Verify application creation
        self.assertIn('tfm_app = TFMApplication', content)
        self.assertIn('ui_backend=backend', content)
        
        # Verify run call
        self.assertIn('tfm_app.run()', content)
        
        print("✓ tfm_qt.py has correct structure for Qt backend")


def run_tests():
    """Run all tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGUIModeLaunch)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
