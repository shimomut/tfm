"""
Test CoreGraphics backend keyboard input handling.

This test verifies that the CoreGraphics backend correctly implements
keyboard input handling with callback mode and event translation.
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock, patch

# Check if we're on macOS
IS_MACOS = sys.platform == 'darwin'

if IS_MACOS:
    try:
        import Cocoa
        import objc
        COCOA_AVAILABLE = True
    except ImportError:
        COCOA_AVAILABLE = False
else:
    COCOA_AVAILABLE = False


@unittest.skipUnless(IS_MACOS and COCOA_AVAILABLE, "Requires macOS with PyObjC")
class TestCoreGraphicsKeyboardInput(unittest.TestCase):
    """Test keyboard input handling in CoreGraphics backend."""
    
    def setUp(self):
        """Set up test fixtures."""
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        from ttk.input_event import KeyCode, ModifierKey
        from ttk.test.test_utils import EventCapture
        
        self.KeyCode = KeyCode
        self.ModifierKey = ModifierKey
        
        # Create backend instance
        self.backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        
        # Initialize the backend
        self.backend.initialize()
        
        # Set up event capture
        self.capture = EventCapture()
        self.backend.set_event_callback(self.capture)
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'backend') and self.backend:
            self.backend.shutdown()
    
    def test_set_event_callback_method_exists(self):
        """Test that set_event_callback method exists and is callable."""
        self.assertTrue(hasattr(self.backend, 'set_event_callback'))
        self.assertTrue(callable(self.backend.set_event_callback))
    
    def test_run_event_loop_iteration_method_exists(self):
        """Test that run_event_loop_iteration method exists and is callable."""
        self.assertTrue(hasattr(self.backend, 'run_event_loop_iteration'))
        self.assertTrue(callable(self.backend.run_event_loop_iteration))
    
    def test_translate_event_method_exists(self):
        """Test that _translate_event helper method exists."""
        self.assertTrue(hasattr(self.backend, '_translate_event'))
        self.assertTrue(callable(self.backend._translate_event))
    
    def test_extract_modifiers_method_exists(self):
        """Test that _extract_modifiers helper method exists."""
        self.assertTrue(hasattr(self.backend, '_extract_modifiers'))
        self.assertTrue(callable(self.backend._extract_modifiers))
    
    def test_translate_event_returns_none_for_none_input(self):
        """Test that _translate_event returns None for None input."""
        result = self.backend._translate_event(None)
        self.assertIsNone(result)
    
    def test_extract_modifiers_with_no_modifiers(self):
        """Test that _extract_modifiers returns NONE for no modifiers."""
        import Cocoa
        
        # Create a mock event with no modifier flags
        mock_event = Mock()
        mock_event.modifierFlags.return_value = 0
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Should be NONE
        self.assertEqual(modifiers, self.ModifierKey.NONE)
    
    def test_extract_modifiers_with_shift(self):
        """Test that _extract_modifiers detects Shift key."""
        import Cocoa
        
        # Create a mock event with Shift modifier
        mock_event = Mock()
        mock_event.modifierFlags.return_value = Cocoa.NSEventModifierFlagShift
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Should have SHIFT flag
        self.assertTrue(modifiers & self.ModifierKey.SHIFT)
    
    def test_extract_modifiers_with_control(self):
        """Test that _extract_modifiers detects Control key."""
        import Cocoa
        
        # Create a mock event with Control modifier
        mock_event = Mock()
        mock_event.modifierFlags.return_value = Cocoa.NSEventModifierFlagControl
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Should have CONTROL flag
        self.assertTrue(modifiers & self.ModifierKey.CONTROL)
    
    def test_extract_modifiers_with_alt(self):
        """Test that _extract_modifiers detects Alt/Option key."""
        import Cocoa
        
        # Create a mock event with Option modifier
        mock_event = Mock()
        mock_event.modifierFlags.return_value = Cocoa.NSEventModifierFlagOption
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Should have ALT flag
        self.assertTrue(modifiers & self.ModifierKey.ALT)
    
    def test_extract_modifiers_with_command(self):
        """Test that _extract_modifiers detects Command key."""
        import Cocoa
        
        # Create a mock event with Command modifier
        mock_event = Mock()
        mock_event.modifierFlags.return_value = Cocoa.NSEventModifierFlagCommand
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Should have COMMAND flag
        self.assertTrue(modifiers & self.ModifierKey.COMMAND)
    
    def test_extract_modifiers_with_multiple_modifiers(self):
        """Test that _extract_modifiers detects multiple modifiers."""
        import Cocoa
        
        # Create a mock event with Shift + Control modifiers
        mock_event = Mock()
        mock_event.modifierFlags.return_value = (
            Cocoa.NSEventModifierFlagShift | Cocoa.NSEventModifierFlagControl
        )
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Should have both SHIFT and CONTROL flags
        self.assertTrue(modifiers & self.ModifierKey.SHIFT)
        self.assertTrue(modifiers & self.ModifierKey.CONTROL)


if __name__ == '__main__':
    unittest.main()
