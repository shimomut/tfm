#!/usr/bin/env python3
"""
Test TextViewer TTK Integration

This test verifies that the TextViewer component has been successfully
migrated to use the TTK API instead of curses.
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ttk import KeyEvent, KeyCode, ModifierKey
from ttk.renderer import TextAttribute
from tfm_path import Path
from tfm_text_viewer import TextViewer, is_text_file, view_text_file
from tfm_colors import COLOR_REGULAR_FILE, COLOR_ERROR


class TestTextViewerTTKIntegration(unittest.TestCase):
    """Test TextViewer TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        self.mock_renderer.draw_text = Mock()
        self.mock_renderer.clear = Mock()
        self.mock_renderer.refresh = Mock()
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.get_input = Mock()
        
        # Create a temporary test file with enough lines to enable scrolling
        # Display height is 21 lines (24 - 2 header - 1 status), so we need more than 21 lines
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        for i in range(1, 51):  # Create 50 lines
            self.temp_file.write(f"Line {i}\n")
        self.temp_file.close()
        self.test_path = Path(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_file.name)
        except OSError:
            pass
    
    def test_text_viewer_uses_renderer(self):
        """Test that TextViewer accepts renderer instead of stdscr"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Verify viewer was initialized with renderer
        self.assertEqual(viewer.renderer, self.mock_renderer)
        self.assertIsNotNone(viewer.file_path)
    
    def test_text_viewer_loads_file(self):
        """Test that TextViewer loads file content correctly"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Verify file was loaded
        self.assertEqual(len(viewer.lines), 50)
        self.assertEqual(viewer.lines[0], "Line 1")
        self.assertEqual(viewer.lines[1], "Line 2")
        self.assertEqual(viewer.lines[49], "Line 50")
    
    def test_get_display_dimensions_uses_renderer(self):
        """Test that get_display_dimensions uses renderer.get_dimensions()"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        start_y, start_x, display_height, display_width = viewer.get_display_dimensions()
        
        # Verify renderer.get_dimensions was called
        self.mock_renderer.get_dimensions.assert_called()
        
        # Verify dimensions are calculated correctly
        self.assertEqual(start_y, 2)  # Header takes 2 lines
        self.assertEqual(start_x, 0)
        self.assertEqual(display_height, 21)  # 24 - 2 (header) - 1 (status)
        self.assertEqual(display_width, 80)
    
    def test_draw_header_uses_renderer(self):
        """Test that draw_header uses renderer.draw_text()"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        viewer.draw_header()
        
        # Verify renderer.draw_text was called
        self.assertTrue(self.mock_renderer.draw_text.called)
        
        # Verify get_dimensions was called
        self.mock_renderer.get_dimensions.assert_called()
    
    def test_draw_status_bar_uses_renderer(self):
        """Test that draw_status_bar uses renderer.draw_text()"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        viewer.draw_status_bar()
        
        # Verify renderer.draw_text was called
        self.assertTrue(self.mock_renderer.draw_text.called)
    
    def test_draw_content_uses_renderer(self):
        """Test that draw_content uses renderer.draw_text()"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        viewer.draw_content()
        
        # Verify renderer.draw_text was called multiple times
        self.assertTrue(self.mock_renderer.draw_text.called)
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)
    
    def test_handle_key_accepts_input_event(self):
        """Test that handle_key accepts KeyEvent instead of key code"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Test with UP arrow key
        event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
        result = viewer.handle_key(event)
        
        # Should return True (continue viewing)
        self.assertTrue(result)
    
    def test_handle_key_quit_with_q(self):
        """Test that 'q' key quits the viewer"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Test with 'q' character
        event = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='q')
        result = viewer.handle_key(event)
        
        # Should return False (exit viewer)
        self.assertFalse(result)
    
    def test_handle_key_quit_with_escape(self):
        """Test that ESC key quits the viewer"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Test with ESC key
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        result = viewer.handle_key(event)
        
        # Should return False (exit viewer)
        self.assertFalse(result)
    
    def test_handle_key_scroll_down(self):
        """Test that DOWN arrow scrolls down"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        initial_offset = viewer.scroll_offset
        
        # Test with DOWN arrow key
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE)
        viewer.handle_key(event)
        
        # Scroll offset should increase
        self.assertGreaterEqual(viewer.scroll_offset, initial_offset)
    
    def test_handle_key_scroll_up(self):
        """Test that UP arrow scrolls up"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.scroll_offset = 5  # Start with some offset
        
        # Test with UP arrow key
        event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
        viewer.handle_key(event)
        
        # Scroll offset should decrease
        self.assertEqual(viewer.scroll_offset, 4)
    
    def test_handle_key_page_down(self):
        """Test that PAGE_DOWN scrolls by page"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        initial_offset = viewer.scroll_offset
        
        # Test with PAGE_DOWN key
        event = KeyEvent(key_code=KeyCode.PAGE_DOWN, modifiers=ModifierKey.NONE)
        viewer.handle_key(event)
        
        # Scroll offset should increase by display height
        self.assertGreater(viewer.scroll_offset, initial_offset)
    
    def test_handle_key_page_up(self):
        """Test that PAGE_UP scrolls by page"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.scroll_offset = 10  # Start with some offset
        
        # Test with PAGE_UP key
        event = KeyEvent(key_code=KeyCode.PAGE_UP, modifiers=ModifierKey.NONE)
        viewer.handle_key(event)
        
        # Scroll offset should decrease
        self.assertLess(viewer.scroll_offset, 10)
    
    def test_handle_key_home(self):
        """Test that HOME key goes to beginning"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.scroll_offset = 10
        viewer.horizontal_offset = 5
        
        # Test with HOME key
        event = KeyEvent(key_code=KeyCode.HOME, modifiers=ModifierKey.NONE)
        viewer.handle_key(event)
        
        # Both offsets should be reset
        self.assertEqual(viewer.scroll_offset, 0)
        self.assertEqual(viewer.horizontal_offset, 0)
    
    def test_handle_key_end(self):
        """Test that END key goes to end"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Test with END key
        event = KeyEvent(key_code=KeyCode.END, modifiers=ModifierKey.NONE)
        viewer.handle_key(event)
        
        # Scroll offset should be at maximum
        self.assertGreater(viewer.scroll_offset, 0)
    
    def test_handle_key_toggle_line_numbers(self):
        """Test that 'n' key toggles line numbers"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        initial_state = viewer.show_line_numbers
        
        # Test with 'n' character
        event = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='n')
        viewer.handle_key(event)
        
        # Line numbers should be toggled
        self.assertEqual(viewer.show_line_numbers, not initial_state)
    
    def test_handle_key_toggle_wrap(self):
        """Test that 'w' key toggles line wrapping"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        initial_state = viewer.wrap_lines
        
        # Test with 'w' character
        event = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='w')
        viewer.handle_key(event)
        
        # Wrap mode should be toggled
        self.assertEqual(viewer.wrap_lines, not initial_state)
    
    def test_handle_key_enter_isearch(self):
        """Test that 'f' key enters isearch mode"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Test with 'f' character
        event = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='f')
        viewer.handle_key(event)
        
        # Should enter isearch mode
        self.assertTrue(viewer.isearch_mode)
    
    def test_handle_isearch_input_accepts_input_event(self):
        """Test that handle_isearch_input accepts KeyEvent"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.enter_isearch_mode()
        
        # Test with character input
        event = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='t')
        result = viewer.handle_isearch_input(event)
        
        # Should handle the input
        self.assertTrue(result)
        self.assertEqual(viewer.isearch_pattern, 't')
    
    def test_handle_isearch_backspace(self):
        """Test that BACKSPACE removes character in isearch"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.enter_isearch_mode()
        viewer.isearch_pattern = "test"
        
        # Test with BACKSPACE key
        event = KeyEvent(key_code=KeyCode.BACKSPACE, modifiers=ModifierKey.NONE)
        viewer.handle_isearch_input(event)
        
        # Last character should be removed
        self.assertEqual(viewer.isearch_pattern, "tes")
    
    def test_handle_isearch_escape(self):
        """Test that ESC exits isearch mode"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.enter_isearch_mode()
        
        # Test with ESC key
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        viewer.handle_isearch_input(event)
        
        # Should exit isearch mode
        self.assertFalse(viewer.isearch_mode)
    
    def test_handle_isearch_enter(self):
        """Test that ENTER exits isearch mode"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        viewer.enter_isearch_mode()
        
        # Test with ENTER key
        event = KeyEvent(key_code=KeyCode.ENTER, modifiers=ModifierKey.NONE)
        viewer.handle_isearch_input(event)
        
        # Should exit isearch mode
        self.assertFalse(viewer.isearch_mode)
    
    def test_run_uses_renderer_methods(self):
        """Test that run() uses renderer methods"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Mock get_input to return quit event
        self.mock_renderer.get_input.return_value = KeyEvent(key_code=0, modifiers=ModifierKey.NONE, char='q')
        
        viewer.run()
        
        # Verify renderer methods were called
        self.mock_renderer.set_cursor_visibility.assert_called_with(False)
        self.mock_renderer.clear.assert_called()
        self.mock_renderer.refresh.assert_called()
        self.mock_renderer.get_input.assert_called()
    
    def test_view_text_file_accepts_renderer(self):
        """Test that view_text_file accepts renderer instead of stdscr"""
        # Mock the run method to avoid blocking
        with patch.object(TextViewer, 'run'):
            result = view_text_file(self.mock_renderer, self.test_path)
            
            # Should return True for successful viewing
            self.assertTrue(result)
    
    def test_highlighted_lines_use_color_info(self):
        """Test that highlighted lines have color information"""
        viewer = TextViewer(self.mock_renderer, self.test_path)
        
        # Verify highlighted lines were created
        self.assertEqual(len(viewer.highlighted_lines), 50)
        
        # Each line should have color information
        for line in viewer.highlighted_lines:
            self.assertIsInstance(line, list)
            if line:  # Non-empty line
                text, color = line[0]
                self.assertIsInstance(text, str)
                # Color can be either an int (color pair constant) or tuple (color_pair, attributes)
                self.assertTrue(isinstance(color, int) or isinstance(color, tuple))


if __name__ == '__main__':
    unittest.main()
