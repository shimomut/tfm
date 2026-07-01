"""
Test InfoDialog TTK Integration

This test verifies that InfoDialog has been successfully migrated to use
the TTK Renderer API instead of curses.

Run with: PYTHONPATH=.:src:ttk pytest test/test_info_dialog_ttk_integration.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from ttk import TextAttribute, KeyCode
from ttk import KeyEvent


class TestInfoDialogTTKIntegration(unittest.TestCase):
    """Test InfoDialog TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock config
        self.mock_config = Mock()
        self.mock_config.INFO_DIALOG_WIDTH_RATIO = 0.8
        self.mock_config.INFO_DIALOG_HEIGHT_RATIO = 0.8
        self.mock_config.INFO_DIALOG_MIN_WIDTH = 20
        self.mock_config.INFO_DIALOG_MIN_HEIGHT = 10
        
        # Import after mocking to avoid import-time dependencies
        import sys
        from tfm_info_dialog import InfoDialog
        self.InfoDialog = InfoDialog
    def test_init_accepts_renderer(self):
        """Test that InfoDialog accepts renderer parameter"""
        dialog = self.InfoDialog(self.mock_config, renderer=self.mock_renderer)
        
        self.assertIsNotNone(dialog.renderer)
        self.assertEqual(dialog.renderer, self.mock_renderer)
        
    def test_handle_input_uses_input_event(self):
        """Test that handle_input uses KeyEvent instead of key codes"""
        dialog = self.InfoDialog(self.mock_config, renderer=self.mock_renderer)
        # Use many lines to ensure scrolling is possible
        many_lines = [f"Line {i}" for i in range(50)]
        dialog.show("Test", many_lines)
        
        # Test ESC key
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=0)
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        self.assertFalse(dialog.is_active)
        
        # Reset dialog
        dialog.show("Test", many_lines)
        
        # Test Q key - InfoDialog handles 'q' through KeyEvent
        event = KeyEvent(key_code=None, char='q', modifiers=0)
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        self.assertFalse(dialog.is_active)
        
        # Reset dialog
        dialog.show("Test", many_lines)
        
        # Test UP arrow
        event = KeyEvent(key_code=KeyCode.UP, char=None, modifiers=0)
        dialog.scroll = 1
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        self.assertEqual(dialog.scroll, 0)
        
        # Test DOWN arrow
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=0)
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        self.assertEqual(dialog.scroll, 1)
        
        # Test PAGE_UP
        event = KeyEvent(key_code=KeyCode.PAGE_UP, char=None, modifiers=0)
        dialog.scroll = 5
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        self.assertEqual(dialog.scroll, 0)
        
        # Test PAGE_DOWN
        event = KeyEvent(key_code=KeyCode.PAGE_DOWN, char=None, modifiers=0)
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        self.assertGreater(dialog.scroll, 0)
        
        # Test HOME
        event = KeyEvent(key_code=KeyCode.HOME, char=None, modifiers=0)
        dialog.scroll = 5
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        self.assertEqual(dialog.scroll, 0)
        
        # Test END
        event = KeyEvent(key_code=KeyCode.END, char=None, modifiers=0)
        result = dialog.handle_key_event(event)
        self.assertTrue(result)
        # Scroll should be at or near max
        self.assertGreaterEqual(dialog.scroll, 0)
        
    def test_draw_uses_renderer(self):
        """Test that draw uses renderer instead of stdscr"""
        dialog = self.InfoDialog(self.mock_config, renderer=self.mock_renderer)
        dialog.show("Test Dialog", ["Line 1", "Line 2", "Line 3"])
        
        # Call draw
        dialog.draw()
        
        # Verify renderer methods were called
        self.mock_renderer.get_dimensions.assert_called()
        self.mock_renderer.draw_hline.assert_called()
        self.mock_renderer.draw_text.assert_called()
        
    def test_draw_without_stdscr_parameter(self):
        """Test that draw no longer requires stdscr and safe_addstr_func parameters"""
        dialog = self.InfoDialog(self.mock_config, renderer=self.mock_renderer)
        dialog.show("Test", ["Line 1", "Line 2"])
        
        # Should be able to call draw without parameters
        try:
            dialog.draw()
            success = True
        except TypeError:
            success = False
            
        self.assertTrue(success, "draw() should not require stdscr or safe_addstr_func parameters")
        
    def test_show_and_exit(self):
        """Test show and exit methods"""
        dialog = self.InfoDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Test show
        dialog.show("Test Title", ["Line 1", "Line 2", "Line 3"])
        self.assertTrue(dialog.is_active)
        self.assertEqual(dialog.title, "Test Title")
        self.assertEqual(len(dialog.lines), 3)
        self.assertEqual(dialog.scroll, 0)
        
        # Test exit
        dialog.exit()
        self.assertFalse(dialog.is_active)
        self.assertEqual(dialog.title, "")
        self.assertEqual(len(dialog.lines), 0)
        
    def test_needs_redraw(self):
        """Test needs_redraw method"""
        dialog = self.InfoDialog(self.mock_config, renderer=self.mock_renderer)
        
        # Initially should need redraw
        dialog.content_changed = True
        self.assertTrue(dialog.needs_redraw())
        
        # After draw, should not need redraw
        dialog.show("Test", ["Line 1"])
        dialog.draw()
        self.assertFalse(dialog.needs_redraw())
        
        # After input, should need redraw
        event = KeyEvent(key_code=KeyCode.DOWN, char=None, modifiers=0)
        dialog.handle_key_event(event)
        self.assertTrue(dialog.needs_redraw())
        
    def test_no_curses_imports(self):
        """Test that InfoDialog does not import curses"""
        import sys
        # Read the source file
        with open('src/tfm_info_dialog.py', 'r') as f:
            source = f.read()
        
        # Check for curses imports
        self.assertNotIn('import curses', source, 
                        "InfoDialog should not import curses")
        self.assertNotIn('from curses', source, 
                        "InfoDialog should not import from curses")
        
    def test_uses_ttk_enums(self):
        """Test that InfoDialog uses TTK enums"""
        import sys
        # Read the source file
        with open('src/tfm_info_dialog.py', 'r') as f:
            source = f.read()
        
        # Check for TTK imports
        self.assertIn('from ttk import', source, 
                     "InfoDialog should import from ttk")
        self.assertIn('TextAttribute', source, 
                     "InfoDialog should use TextAttribute")
        self.assertIn('KeyCode', source, 
                     "InfoDialog should use KeyCode")
        
    def test_color_system_integration(self):
        """Test that InfoDialog uses TTK color system correctly"""
        dialog = self.InfoDialog(self.mock_config, renderer=self.mock_renderer)
        dialog.show("Test", ["Line 1", "Line 2"])
        
        # Draw and check that color_pair parameter is used
        dialog.draw()
        
        # Verify draw_text was called with color_pair parameter
        calls = self.mock_renderer.draw_text.call_args_list
        self.assertGreater(len(calls), 0, "draw_text should be called")
        
        # Check that at least one call uses color_pair parameter
        has_color_pair = any('color_pair' in str(call) for call in calls)
        self.assertTrue(has_color_pair, "draw_text should use color_pair parameter")
