#!/usr/bin/env python3
"""
Test QuickEditBar TTK integration

This test verifies that QuickEditBar has been successfully migrated
to use TTK's Renderer API instead of direct curses calls.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

# Add ttk directory to path
ttk_path = Path(__file__).parent.parent / 'ttk'
sys.path.insert(0, str(ttk_path))

from ttk import KeyEvent, KeyCode, ModifierKey
from tfm_quick_edit_bar import QuickEditBar, DialogType, QuickEditBarHelpers


class TestQuickEditBarTTKIntegration(unittest.TestCase):
    """Test QuickEditBar TTK integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create mock config
        self.mock_config = Mock()
        
    def test_initialization(self):
        """Test that QuickEditBar can be initialized with renderer"""
        # Create dialog with renderer
        dialog = QuickEditBar(config=self.mock_config, renderer=self.mock_renderer)
        
        # Verify initialization
        self.assertIsNotNone(dialog.renderer)
        self.assertEqual(dialog.renderer, self.mock_renderer)
        self.assertEqual(dialog.config, self.mock_config)
        self.assertFalse(dialog.is_active)
        self.assertIsNone(dialog.dialog_type)
    
    def test_no_curses_imports(self):
        """Test that QuickEditBar doesn't import curses directly"""
        import tfm_quick_edit_bar
        import inspect
        
        source = inspect.getsource(tfm_quick_edit_bar)
        
        # Check for direct curses imports (excluding comments)
        lines = source.split('\n')
        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith('#'):
                continue
            # Check for curses imports
            if 'import curses' in stripped and not stripped.startswith('#'):
                self.fail(f"Found curses import: {line}")
    
    def test_uses_ttk_types(self):
        """Test that QuickEditBar uses TTK types"""
        import tfm_quick_edit_bar
        import inspect
        
        source = inspect.getsource(tfm_quick_edit_bar)
        
        # Check for TTK imports
        self.assertIn('KeyCode', source, "KeyCode should be imported from TTK")
        self.assertIn('TextAttribute', source, "TextAttribute should be imported from TTK")
    
    def test_handle_input_method(self):
        """Test that QuickEditBar has handle_input method"""
        dialog = QuickEditBar(config=self.mock_config, renderer=self.mock_renderer)
        
        # Check that handle_input method exists
        self.assertTrue(hasattr(dialog, 'handle_input'))
        
        # Test with None event
        result = dialog.handle_input(None)
        self.assertFalse(result)
        
        # Test with event when not active
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=ModifierKey.NONE)
        result = dialog.handle_input(event)
        self.assertFalse(result)
    
    def test_draw_method(self):
        """Test that QuickEditBar has draw method using renderer"""
        dialog = QuickEditBar(config=self.mock_config, renderer=self.mock_renderer)
        
        # Check that draw method exists
        self.assertTrue(hasattr(dialog, 'draw'))
        
        # Get draw method signature
        import inspect
        sig = inspect.signature(dialog.draw)
        
        # Should not require stdscr parameter
        params = list(sig.parameters.keys())
        self.assertNotIn('stdscr', params, "draw should not require stdscr parameter")
        
        # Test drawing when not active (should not crash)
        dialog.draw()
    
    def test_status_line_input_dialog(self):
        """Test status line input dialog functionality"""
        dialog = QuickEditBar(config=self.mock_config, renderer=self.mock_renderer)
        
        # Show status line input dialog
        callback_called = []
        def test_callback(text):
            callback_called.append(text)
        
        dialog.show_status_line_input(
            prompt="Test: ",
            help_text="ESC:cancel Enter:confirm",
            initial_text="initial",
            callback=test_callback
        )
        
        # Verify dialog is active
        self.assertTrue(dialog.is_active)
        self.assertEqual(dialog.dialog_type, DialogType.STATUS_LINE_INPUT)
        self.assertEqual(dialog.get_text(), "initial")
        
        # Test ESC key
        event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=ModifierKey.NONE)
        result = dialog.handle_input(event)
        self.assertTrue(result)
        self.assertFalse(dialog.is_active)
        
        # Show again and test Enter key
        dialog.show_status_line_input(
            prompt="Test: ",
            callback=test_callback
        )
        dialog.set_text("test text")
        
        event = KeyEvent(key_code=KeyCode.ENTER, char=None, modifiers=ModifierKey.NONE)
        result = dialog.handle_input(event)
        self.assertTrue(result)
        self.assertFalse(dialog.is_active)
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0], "test text")


if __name__ == '__main__':
    unittest.main()
