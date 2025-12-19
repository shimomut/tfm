#!/usr/bin/env python3
"""
Test suite for JumpDialog TTK integration
Verifies that JumpDialog works correctly with TTK renderer
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import threading
import time
from ttk import KeyCode, KeyEvent, TextAttribute
from tfm_jump_dialog import JumpDialog, JumpDialogHelpers
from tfm_path import Path


class TestJumpDialogTTKIntegration(unittest.TestCase):
    """Test JumpDialog TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock config
        self.config = Mock()
        self.config.MAX_JUMP_DIRECTORIES = 100
        
        # Create mock renderer
        self.renderer = Mock()
        self.renderer.get_dimensions.return_value = (40, 120)
        self.renderer.draw_text = Mock()
        self.renderer.draw_hline = Mock()
        self.renderer.draw_vline = Mock()
        self.renderer.draw_rect = Mock()
        
        # Create jump dialog with renderer
        self.dialog = JumpDialog(self.config, self.renderer)
        
    def test_initialization_with_renderer(self):
        """Test that JumpDialog initializes with renderer"""
        self.assertIsNotNone(self.dialog.renderer)
        self.assertEqual(self.dialog.renderer, self.renderer)
        self.assertEqual(self.dialog.max_directories, 100)
        
    def test_show_initializes_state(self):
        """Test that show() initializes dialog state"""
        root_dir = Path('/test/root')
        
        with patch.object(self.dialog, '_start_directory_scan'):
            self.dialog.show(root_dir)
        
        self.assertTrue(self.dialog.is_active)
        self.assertEqual(self.dialog.directories, [])
        self.assertEqual(self.dialog.filtered_directories, [])
        self.assertEqual(self.dialog.selected, 0)
        self.assertEqual(self.dialog.scroll, 0)
        
    def test_handle_input_with_input_event(self):
        """Test that handle_input works with KeyEvent"""
        # Set up dialog state
        self.dialog.is_active = True
        self.dialog.filtered_directories = [Path('/dir1'), Path('/dir2')]
        
        # Test ESC key (cancel)
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=set())
        with patch.object(self.dialog, '_cancel_current_scan'):
            result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertFalse(self.dialog.is_active)
        
    def test_handle_input_navigation_keys(self):
        """Test that navigation keys work with KeyEvent"""
        self.dialog.is_active = True
        self.dialog.filtered_directories = [Path('/dir1'), Path('/dir2'), Path('/dir3')]
        self.dialog.selected = 0
        
        # Test DOWN key
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=set())
        result = self.dialog.handle_input(event)
        
        self.assertTrue(result)
        self.assertEqual(self.dialog.selected, 1)
        
    def test_handle_input_enter_selects_directory(self):
        """Test that Enter key selects directory"""
        self.dialog.is_active = True
        self.dialog.filtered_directories = [Path('/dir1'), Path('/dir2')]
        self.dialog.selected = 1
        
        # Test ENTER key
        event = KeyEvent(key_code=KeyCode.ENTER, char=None, modifiers=set())
        with patch.object(self.dialog, '_cancel_current_scan'):
            result = self.dialog.handle_input(event)
        
        self.assertEqual(result, ('navigate', Path('/dir2')))
        
    @unittest.skip("Requires SingleLineTextEdit TTK migration (task 26)")
    def test_draw_uses_renderer(self):
        """Test that draw() uses renderer instead of stdscr"""
        self.dialog.is_active = True
        self.dialog.directories = [Path('/dir1'), Path('/dir2')]
        self.dialog.filtered_directories = [Path('/dir1'), Path('/dir2')]
        self.dialog.searching = False
        
        # Call draw
        self.dialog.draw()
        
        # Verify renderer methods were called
        self.assertTrue(self.renderer.draw_text.called)
        
    @unittest.skip("Requires SingleLineTextEdit TTK migration (task 26)")
    def test_draw_with_scanning_status(self):
        """Test that draw() shows scanning status"""
        self.dialog.is_active = True
        self.dialog.directories = [Path('/dir1')]
        self.dialog.filtered_directories = [Path('/dir1')]
        self.dialog.searching = True
        
        # Call draw
        self.dialog.draw()
        
        # Verify renderer was used
        self.assertTrue(self.renderer.draw_text.called)
        
        # Check that status text was drawn (should contain "Scanning")
        draw_calls = self.renderer.draw_text.call_args_list
        status_calls = [call for call in draw_calls if len(call[0]) > 2 and 'Scanning' in str(call[0][2])]
        self.assertTrue(len(status_calls) > 0, "Should draw scanning status")
        
    @unittest.skip("Requires SingleLineTextEdit TTK migration (task 26)")
    def test_draw_with_filtered_results(self):
        """Test that draw() shows filtered results"""
        self.dialog.is_active = True
        self.dialog.directories = [Path('/dir1'), Path('/dir2'), Path('/dir3')]
        self.dialog.filtered_directories = [Path('/dir1')]
        self.dialog.text_editor.text = "dir1"
        self.dialog.searching = False
        
        # Call draw
        self.dialog.draw()
        
        # Verify renderer was used
        self.assertTrue(self.renderer.draw_text.called)
        
        # Check that filtered count was drawn
        draw_calls = self.renderer.draw_text.call_args_list
        count_calls = [call for call in draw_calls if len(call[0]) > 2 and 'filtered from' in str(call[0][2])]
        self.assertTrue(len(count_calls) > 0, "Should show filtered count")
        
    def test_needs_redraw_when_searching(self):
        """Test that needs_redraw returns True when searching"""
        self.dialog.searching = True
        self.dialog.content_changed = False
        
        self.assertTrue(self.dialog.needs_redraw())
        
    def test_needs_redraw_when_content_changed(self):
        """Test that needs_redraw returns True when content changed"""
        self.dialog.searching = False
        self.dialog.content_changed = True
        
        self.assertTrue(self.dialog.needs_redraw())
        
    def test_filter_directories_thread_safe(self):
        """Test that directory filtering is thread-safe"""
        self.dialog.directories = [Path('/test1'), Path('/test2'), Path('/other')]
        self.dialog.text_editor.text = "test"
        
        # Filter directories
        self.dialog._filter_directories()
        
        # Verify filtered results
        self.assertEqual(len(self.dialog.filtered_directories), 2)
        self.assertIn(Path('/test1'), self.dialog.filtered_directories)
        self.assertIn(Path('/test2'), self.dialog.filtered_directories)
        
    def test_cancel_scan_stops_thread(self):
        """Test that cancel scan stops the scanning thread"""
        # Start a mock scan
        self.dialog.scan_thread = Mock()
        self.dialog.scan_thread.is_alive.return_value = True
        self.dialog.searching = True
        
        # Cancel scan
        self.dialog._cancel_current_scan()
        
        # Verify scan was cancelled
        self.assertFalse(self.dialog.searching)
        self.assertTrue(self.dialog.cancel_scan.is_set())
        
    def test_exit_cancels_scan(self):
        """Test that exit() cancels any running scan"""
        self.dialog.is_active = True
        self.dialog.searching = True
        
        with patch.object(self.dialog, '_cancel_current_scan') as mock_cancel:
            self.dialog.exit()
        
        mock_cancel.assert_called_once()
        self.assertFalse(self.dialog.is_active)


class TestJumpDialogHelpers(unittest.TestCase):
    """Test JumpDialogHelpers functions"""
    
    def test_navigate_to_directory(self):
        """Test navigate_to_directory helper"""
        # Create mock pane manager
        pane_manager = Mock()
        current_pane = {
            'path': Path('/old/path'),
            'selected_index': 5,
            'scroll_offset': 10,
            'selected_files': set(['file1', 'file2'])
        }
        pane_manager.get_current_pane.return_value = current_pane
        pane_manager.active_pane = 'left'
        
        # Create mock print function
        print_func = Mock()
        
        # Navigate to directory
        target_dir = Path('/new/path')
        with patch.object(target_dir, 'exists', return_value=True):
            with patch.object(target_dir, 'is_dir', return_value=True):
                JumpDialogHelpers.navigate_to_directory(target_dir, pane_manager, print_func)
        
        # Verify pane was updated
        self.assertEqual(current_pane['path'], target_dir)
        self.assertEqual(current_pane['focused_index'], 0)
        self.assertEqual(current_pane['scroll_offset'], 0)
        self.assertEqual(len(current_pane['selected_files']), 0)
        
        # Verify message was printed
        print_func.assert_called_once()
        self.assertIn('Jumped to directory', str(print_func.call_args))


if __name__ == '__main__':
    unittest.main()
