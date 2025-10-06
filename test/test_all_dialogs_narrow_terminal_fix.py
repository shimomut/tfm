#!/usr/bin/env python3
"""
Test narrow terminal dialog rendering fixes

This test verifies that all dialogs handle narrow terminals correctly
after the width calculation fixes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from unittest.mock import Mock, patch
from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_drives_dialog import DrivesDialog
from tfm_list_dialog import ListDialog
from tfm_jump_dialog import JumpDialog
from tfm_search_dialog import SearchDialog
from tfm_path import Path as TfmPath


class TestAllDialogsNarrowTerminalFix(unittest.TestCase):
    """Test that all dialogs handle narrow terminals correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock config
        self.mock_config = Mock()
        self.mock_config.LIST_DIALOG_WIDTH_RATIO = 0.6
        self.mock_config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        self.mock_config.LIST_DIALOG_MIN_WIDTH = 40
        self.mock_config.LIST_DIALOG_MIN_HEIGHT = 15
        self.mock_config.MAX_JUMP_DIRECTORIES = 5000
        self.mock_config.MAX_SEARCH_RESULTS = 10000
        
    def _create_mock_drawing_environment(self, terminal_width, terminal_height):
        """Create mock drawing environment for testing"""
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (terminal_height, terminal_width)
        mock_safe_addstr = Mock()
        return mock_stdscr, mock_safe_addstr
        
    def _verify_drawing_bounds(self, mock_safe_addstr, terminal_width, terminal_height):
        """Verify that all drawing operations stay within terminal bounds"""
        for call in mock_safe_addstr.call_args_list:
            if len(call[0]) >= 3:  # (y, x, text, ...)
                y, x, text = call[0][:3]
                
                # Check Y bounds
                self.assertGreaterEqual(y, 0, f"Y position {y} is negative")
                self.assertLess(y, terminal_height, f"Y position {y} exceeds terminal height {terminal_height}")
                
                # Check X bounds
                self.assertGreaterEqual(x, 0, f"X position {x} is negative")
                self.assertLess(x, terminal_width, f"X position {x} exceeds terminal width {terminal_width}")
                
                # Check text doesn't exceed terminal width
                text_str = str(text)
                self.assertLessEqual(x + len(text_str), terminal_width, 
                                   f"Text at ({x}, {y}) extends beyond terminal width: '{text_str}'")
    
    @patch('tfm_batch_rename_dialog.get_status_color')
    @patch('tfm_batch_rename_dialog.get_safe_functions')
    def test_batch_rename_dialog_narrow_terminal(self, mock_get_safe_functions, mock_get_status_color):
        """Test BatchRenameDialog in narrow terminal"""
        mock_get_status_color.return_value = 0
        
        # Mock wide character functions
        mock_safe_funcs = {
            'get_display_width': lambda text: len(str(text)),
            'truncate_to_width': lambda text, width, suffix: str(text)[:width-len(suffix)] + suffix if len(str(text)) > width else str(text),
            'pad_to_width': lambda text, width, align: str(text).ljust(width)
        }
        mock_get_safe_functions.return_value = mock_safe_funcs
        
        dialog = BatchRenameDialog(self.mock_config)
        
        # Create mock files
        mock_files = [TfmPath("file1.txt"), TfmPath("file2.txt")]
        dialog.show(mock_files)
        
        # Test various narrow terminal widths
        narrow_widths = [25, 30, 35, 40, 50]
        
        for terminal_width in narrow_widths:
            with self.subTest(width=terminal_width):
                mock_stdscr, mock_safe_addstr = self._create_mock_drawing_environment(terminal_width, 24)
                
                # This should not crash
                try:
                    dialog.draw(mock_stdscr, mock_safe_addstr)
                    dialog_rendered = True
                except Exception as e:
                    dialog_rendered = False
                    print(f"BatchRenameDialog failed at width {terminal_width}: {e}")
                
                self.assertTrue(dialog_rendered, f"BatchRenameDialog should render at width {terminal_width}")
                
                # Verify all drawing operations stay within bounds
                self._verify_drawing_bounds(mock_safe_addstr, terminal_width, 24)
    
    @patch('tfm_drives_dialog.get_status_color')
    def test_drives_dialog_narrow_terminal(self, mock_get_status_color):
        """Test DrivesDialog in narrow terminal"""
        mock_get_status_color.return_value = 0
        
        dialog = DrivesDialog(self.mock_config)
        dialog.show()
        
        # Test various narrow terminal widths
        narrow_widths = [25, 30, 35, 40, 50]
        
        for terminal_width in narrow_widths:
            with self.subTest(width=terminal_width):
                mock_stdscr, mock_safe_addstr = self._create_mock_drawing_environment(terminal_width, 24)
                
                # This should not crash
                try:
                    dialog.draw(mock_stdscr, mock_safe_addstr)
                    dialog_rendered = True
                except Exception as e:
                    dialog_rendered = False
                    print(f"DrivesDialog failed at width {terminal_width}: {e}")
                
                self.assertTrue(dialog_rendered, f"DrivesDialog should render at width {terminal_width}")
                
                # Verify all drawing operations stay within bounds
                self._verify_drawing_bounds(mock_safe_addstr, terminal_width, 24)
    
    @patch('tfm_list_dialog.get_status_color')
    def test_list_dialog_narrow_terminal(self, mock_get_status_color):
        """Test ListDialog in narrow terminal"""
        mock_get_status_color.return_value = 0
        
        dialog = ListDialog(self.mock_config)
        
        items = ["Item 1", "Item 2", "Item 3"]
        callback = Mock()
        dialog.show("Test List", items, callback)
        
        # Test various narrow terminal widths
        narrow_widths = [25, 30, 35, 40, 50]
        
        for terminal_width in narrow_widths:
            with self.subTest(width=terminal_width):
                mock_stdscr, mock_safe_addstr = self._create_mock_drawing_environment(terminal_width, 24)
                
                # This should not crash
                try:
                    dialog.draw(mock_stdscr, mock_safe_addstr)
                    dialog_rendered = True
                except Exception as e:
                    dialog_rendered = False
                    print(f"ListDialog failed at width {terminal_width}: {e}")
                
                self.assertTrue(dialog_rendered, f"ListDialog should render at width {terminal_width}")
                
                # Verify all drawing operations stay within bounds
                self._verify_drawing_bounds(mock_safe_addstr, terminal_width, 24)
    
    @patch('tfm_jump_dialog.get_status_color')
    def test_jump_dialog_narrow_terminal(self, mock_get_status_color):
        """Test JumpDialog in narrow terminal"""
        mock_get_status_color.return_value = 0
        
        dialog = JumpDialog(self.mock_config)
        
        # Mock root directory
        mock_root = Mock()
        mock_root.__str__ = Mock(return_value="/test")
        dialog.show(mock_root)
        
        # Test various narrow terminal widths
        narrow_widths = [25, 30, 35, 40, 50]
        
        for terminal_width in narrow_widths:
            with self.subTest(width=terminal_width):
                mock_stdscr, mock_safe_addstr = self._create_mock_drawing_environment(terminal_width, 24)
                
                # This should not crash
                try:
                    dialog.draw(mock_stdscr, mock_safe_addstr)
                    dialog_rendered = True
                except Exception as e:
                    dialog_rendered = False
                    print(f"JumpDialog failed at width {terminal_width}: {e}")
                
                self.assertTrue(dialog_rendered, f"JumpDialog should render at width {terminal_width}")
                
                # Verify all drawing operations stay within bounds
                self._verify_drawing_bounds(mock_safe_addstr, terminal_width, 24)
    
    @patch('tfm_search_dialog.get_status_color')
    def test_search_dialog_narrow_terminal(self, mock_get_status_color):
        """Test SearchDialog in narrow terminal"""
        mock_get_status_color.return_value = 0
        
        dialog = SearchDialog(self.mock_config)
        dialog.show('filename')
        
        # Test various narrow terminal widths
        narrow_widths = [25, 30, 35, 40, 50]
        
        for terminal_width in narrow_widths:
            with self.subTest(width=terminal_width):
                mock_stdscr, mock_safe_addstr = self._create_mock_drawing_environment(terminal_width, 24)
                
                # This should not crash
                try:
                    dialog.draw(mock_stdscr, mock_safe_addstr)
                    dialog_rendered = True
                except Exception as e:
                    dialog_rendered = False
                    print(f"SearchDialog failed at width {terminal_width}: {e}")
                
                self.assertTrue(dialog_rendered, f"SearchDialog should render at width {terminal_width}")
                
                # Verify all drawing operations stay within bounds
                self._verify_drawing_bounds(mock_safe_addstr, terminal_width, 24)
    
    def test_dialog_width_never_exceeds_terminal(self):
        """Test that dialog width calculations never exceed terminal width"""
        # Test various terminal sizes
        test_cases = [
            (20, 10),   # Very narrow
            (25, 15),   # Narrow
            (30, 20),   # Small
            (40, 24),   # Medium
            (80, 24),   # Normal
            (120, 30),  # Wide
        ]
        
        for terminal_width, terminal_height in test_cases:
            with self.subTest(size=f"{terminal_width}x{terminal_height}"):
                # Test BaseListDialog width calculation through ListDialog
                dialog = ListDialog(self.mock_config)
                items = ["Test"]
                callback = Mock()
                dialog.show("Test", items, callback)
                
                mock_stdscr, mock_safe_addstr = self._create_mock_drawing_environment(terminal_width, terminal_height)
                
                # Get the dialog frame dimensions
                start_y, start_x, dialog_width, dialog_height = dialog.draw_dialog_frame(
                    mock_stdscr, mock_safe_addstr, "Test", 0.6, 0.7, 40, 15
                )
                
                # Dialog should never exceed terminal dimensions
                self.assertLessEqual(dialog_width, terminal_width, 
                                   f"Dialog width {dialog_width} exceeds terminal width {terminal_width}")
                self.assertLessEqual(dialog_height, terminal_height,
                                   f"Dialog height {dialog_height} exceeds terminal height {terminal_height}")
                
                # Dialog should be positioned within terminal bounds
                self.assertGreaterEqual(start_x, 0, "Dialog start_x should not be negative")
                self.assertGreaterEqual(start_y, 0, "Dialog start_y should not be negative")
                self.assertLessEqual(start_x + dialog_width, terminal_width,
                                   "Dialog should not extend beyond terminal width")
                self.assertLessEqual(start_y + dialog_height, terminal_height,
                                   "Dialog should not extend beyond terminal height")
    
    def test_extremely_narrow_terminals(self):
        """Test dialogs in extremely narrow terminals"""
        # Test with very small terminal sizes
        extreme_cases = [
            (10, 5),    # Extremely narrow
            (15, 8),    # Very narrow
            (20, 10),   # Narrow
        ]
        
        for terminal_width, terminal_height in extreme_cases:
            with self.subTest(size=f"{terminal_width}x{terminal_height}"):
                # Test that dialogs don't crash even in extreme cases
                dialog = ListDialog(self.mock_config)
                items = ["A", "B"]
                callback = Mock()
                dialog.show("T", items, callback)
                
                mock_stdscr, mock_safe_addstr = self._create_mock_drawing_environment(terminal_width, terminal_height)
                
                try:
                    dialog.draw(mock_stdscr, mock_safe_addstr)
                    dialog_rendered = True
                except Exception as e:
                    dialog_rendered = False
                    print(f"Dialog failed at extreme size {terminal_width}x{terminal_height}: {e}")
                
                self.assertTrue(dialog_rendered, 
                              f"Dialog should render even at extreme size {terminal_width}x{terminal_height}")
                
                # Verify bounds
                self._verify_drawing_bounds(mock_safe_addstr, terminal_width, terminal_height)


if __name__ == '__main__':
    unittest.main()