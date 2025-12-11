"""
Simple tests for Metal backend input handling implementation.

This module tests that the Metal backend input handling methods exist
and have the correct signatures.
"""

import unittest
from ttk.backends.metal_backend import MetalBackend
from ttk.input_event import InputEvent


class TestMetalInputHandlingSimple(unittest.TestCase):
    """Simple tests for Metal backend input handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = MetalBackend()
    
    def test_get_input_method_exists(self):
        """Test that get_input method exists."""
        self.assertTrue(hasattr(self.backend, 'get_input'))
        self.assertTrue(callable(self.backend.get_input))
    
    def test_poll_macos_event_method_exists(self):
        """Test that _poll_macos_event method exists."""
        self.assertTrue(hasattr(self.backend, '_poll_macos_event'))
        self.assertTrue(callable(self.backend._poll_macos_event))
    
    def test_translate_macos_event_method_exists(self):
        """Test that _translate_macos_event method exists."""
        self.assertTrue(hasattr(self.backend, '_translate_macos_event'))
        self.assertTrue(callable(self.backend._translate_macos_event))
    
    def test_translate_keyboard_event_method_exists(self):
        """Test that _translate_keyboard_event method exists."""
        self.assertTrue(hasattr(self.backend, '_translate_keyboard_event'))
        self.assertTrue(callable(self.backend._translate_keyboard_event))
    
    def test_translate_mouse_event_method_exists(self):
        """Test that _translate_mouse_event method exists."""
        self.assertTrue(hasattr(self.backend, '_translate_mouse_event'))
        self.assertTrue(callable(self.backend._translate_mouse_event))
    
    def test_extract_modifiers_method_exists(self):
        """Test that _extract_modifiers method exists."""
        self.assertTrue(hasattr(self.backend, '_extract_modifiers'))
        self.assertTrue(callable(self.backend._extract_modifiers))
    
    def test_get_input_signature(self):
        """Test that get_input has correct signature."""
        import inspect
        sig = inspect.signature(self.backend.get_input)
        params = list(sig.parameters.keys())
        self.assertIn('timeout_ms', params)
    
    def test_get_input_returns_none_without_pyobjc(self):
        """Test that get_input returns None when PyObjC is not available."""
        # Without PyObjC installed or without a real macOS event queue,
        # get_input should handle the ImportError gracefully
        result = self.backend.get_input(timeout_ms=0)
        # Should return None (no event available)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
