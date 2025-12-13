"""
Test CoreGraphics backend keyboard input handling.

This test verifies that the CoreGraphics backend correctly implements
keyboard input handling with timeout support and event translation.
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
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'backend') and self.backend:
            self.backend.shutdown()
    
    def test_get_input_method_exists(self):
        """Test that get_input method exists and is callable."""
        self.assertTrue(hasattr(self.backend, 'get_input'))
        self.assertTrue(callable(self.backend.get_input))
    
    def test_get_input_non_blocking_returns_none(self):
        """Test that non-blocking get_input returns None when no input available."""
        # Non-blocking mode should return immediately with None if no input
        result = self.backend.get_input(timeout_ms=0)
        
        # Should return None (no input available)
        self.assertIsNone(result)
    
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
