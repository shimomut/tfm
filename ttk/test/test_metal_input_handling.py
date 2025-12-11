"""
Tests for Metal backend input handling.

This module tests the Metal backend's input handling functionality,
including keyboard events, mouse events, and modifier key detection.
"""

import unittest
import sys
from unittest.mock import Mock, MagicMock, patch, create_autospec
from ttk.backends.metal_backend import MetalBackend
from ttk.input_event import KeyCode, ModifierKey, InputEvent


# Create mock modules for Cocoa and Foundation
class MockCocoa:
    NSApplication = Mock()
    NSEventTypeKeyDown = 10
    NSEventTypeLeftMouseDown = 1
    NSEventTypeLeftMouseUp = 2
    NSEventTypeRightMouseDown = 3
    NSEventTypeRightMouseUp = 4
    NSEventTypeOtherMouseDown = 5
    NSEventTypeOtherMouseUp = 6
    NSEventTypeMouseMoved = 7
    NSEventTypeLeftMouseDragged = 8
    NSEventTypeRightMouseDragged = 9
    NSEventTypeOtherMouseDragged = 10
    NSEventModifierFlagShift = 1 << 17
    NSEventModifierFlagControl = 1 << 18
    NSEventModifierFlagOption = 1 << 19
    NSEventModifierFlagCommand = 1 << 20
    NSEventMaskKeyDown = 1 << 10
    NSEventMaskKeyUp = 1 << 11
    NSEventMaskFlagsChanged = 1 << 12
    NSEventMaskLeftMouseDown = 1 << 1
    NSEventMaskLeftMouseUp = 1 << 2
    NSEventMaskRightMouseDown = 1 << 3
    NSEventMaskRightMouseUp = 1 << 4
    NSEventMaskOtherMouseDown = 1 << 25
    NSEventMaskOtherMouseUp = 1 << 26
    NSEventMaskMouseMoved = 1 << 5
    NSEventMaskLeftMouseDragged = 1 << 6
    NSEventMaskRightMouseDragged = 1 << 7
    NSEventMaskOtherMouseDragged = 1 << 27
    NSEventMaskScrollWheel = 1 << 22
    NSDefaultRunLoopMode = "kCFRunLoopDefaultMode"


class MockFoundation:
    NSDate = Mock()


# Install mock modules
sys.modules['Cocoa'] = MockCocoa()
sys.modules['Foundation'] = MockFoundation()


class TestMetalInputHandling(unittest.TestCase):
    """Test Metal backend input handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = MetalBackend()
        # Initialize basic properties without full initialization
        self.backend.rows = 40
        self.backend.cols = 80
        self.backend.char_width = 10
        self.backend.char_height = 20
    
    def test_poll_macos_event_blocking(self):
        """Test polling macOS event queue in blocking mode."""
        import Cocoa
        import Foundation
        
        # Create mock application and event
        mock_app = Mock()
        mock_event = Mock()
        mock_app.nextEventMatchingMask_untilDate_inMode_dequeue_.return_value = mock_event
        Cocoa.NSApplication.sharedApplication = Mock(return_value=mock_app)
        Foundation.NSDate.distantFuture = Mock(return_value=Mock())
        
        # Poll with blocking timeout
        result = self.backend._poll_macos_event(-1)
        
        # Verify event was returned
        self.assertEqual(result, mock_event)
        
        # Verify distant future was used for blocking
        Foundation.NSDate.distantFuture.assert_called_once()
    
    @patch('ttk.backends.metal_backend.Cocoa')
    @patch('ttk.backends.metal_backend.Foundation')
    def test_poll_macos_event_nonblocking(self, mock_foundation, mock_cocoa):
        """Test polling macOS event queue in non-blocking mode."""
        # Create mock application with no event
        mock_app = Mock()
        mock_app.nextEventMatchingMask_untilDate_inMode_dequeue_.return_value = None
        mock_cocoa.NSApplication.sharedApplication.return_value = mock_app
        mock_foundation.NSDate.distantPast.return_value = Mock()
        
        # Poll with non-blocking timeout
        result = self.backend._poll_macos_event(0)
        
        # Verify None was returned (no event)
        self.assertIsNone(result)
        
        # Verify distant past was used for non-blocking
        mock_foundation.NSDate.distantPast.assert_called_once()
    
    @patch('ttk.backends.metal_backend.Cocoa')
    @patch('ttk.backends.metal_backend.Foundation')
    def test_poll_macos_event_timed(self, mock_foundation, mock_cocoa):
        """Test polling macOS event queue with timeout."""
        # Create mock application and event
        mock_app = Mock()
        mock_event = Mock()
        mock_app.nextEventMatchingMask_untilDate_inMode_dequeue_.return_value = mock_event
        mock_cocoa.NSApplication.sharedApplication.return_value = mock_app
        mock_date = Mock()
        mock_foundation.NSDate.dateWithTimeIntervalSinceNow_.return_value = mock_date
        
        # Poll with 100ms timeout
        result = self.backend._poll_macos_event(100)
        
        # Verify event was returned
        self.assertEqual(result, mock_event)
        
        # Verify timeout was calculated correctly (100ms = 0.1 seconds)
        mock_foundation.NSDate.dateWithTimeIntervalSinceNow_.assert_called_once_with(0.1)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_extract_modifiers_none(self, mock_cocoa):
        """Test extracting modifiers when no modifiers are pressed."""
        # Create mock event with no modifiers
        mock_event = Mock()
        mock_event.modifierFlags.return_value = 0
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Verify no modifiers
        self.assertEqual(modifiers, ModifierKey.NONE)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_extract_modifiers_shift(self, mock_cocoa):
        """Test extracting Shift modifier."""
        # Create mock event with Shift
        mock_event = Mock()
        mock_cocoa.NSEventModifierFlagShift = 1 << 17
        mock_event.modifierFlags.return_value = mock_cocoa.NSEventModifierFlagShift
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Verify Shift is set
        self.assertTrue(modifiers & ModifierKey.SHIFT)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_extract_modifiers_control(self, mock_cocoa):
        """Test extracting Control modifier."""
        # Create mock event with Control
        mock_event = Mock()
        mock_cocoa.NSEventModifierFlagControl = 1 << 18
        mock_event.modifierFlags.return_value = mock_cocoa.NSEventModifierFlagControl
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Verify Control is set
        self.assertTrue(modifiers & ModifierKey.CONTROL)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_extract_modifiers_alt(self, mock_cocoa):
        """Test extracting Alt/Option modifier."""
        # Create mock event with Alt
        mock_event = Mock()
        mock_cocoa.NSEventModifierFlagOption = 1 << 19
        mock_event.modifierFlags.return_value = mock_cocoa.NSEventModifierFlagOption
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Verify Alt is set
        self.assertTrue(modifiers & ModifierKey.ALT)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_extract_modifiers_command(self, mock_cocoa):
        """Test extracting Command modifier."""
        # Create mock event with Command
        mock_event = Mock()
        mock_cocoa.NSEventModifierFlagCommand = 1 << 20
        mock_event.modifierFlags.return_value = mock_cocoa.NSEventModifierFlagCommand
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Verify Command is set
        self.assertTrue(modifiers & ModifierKey.COMMAND)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_extract_modifiers_multiple(self, mock_cocoa):
        """Test extracting multiple modifiers."""
        # Create mock event with Shift + Command
        mock_event = Mock()
        mock_cocoa.NSEventModifierFlagShift = 1 << 17
        mock_cocoa.NSEventModifierFlagCommand = 1 << 20
        mock_event.modifierFlags.return_value = (
            mock_cocoa.NSEventModifierFlagShift | mock_cocoa.NSEventModifierFlagCommand
        )
        
        # Extract modifiers
        modifiers = self.backend._extract_modifiers(mock_event)
        
        # Verify both modifiers are set
        self.assertTrue(modifiers & ModifierKey.SHIFT)
        self.assertTrue(modifiers & ModifierKey.COMMAND)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_printable(self, mock_cocoa):
        """Test translating printable character keyboard event."""
        # Create mock keyboard event for 'a'
        mock_event = Mock()
        mock_event.keyCode.return_value = 0  # 'a' key
        mock_event.characters.return_value = 'a'
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, ord('a'))
        self.assertEqual(input_event.char, 'a')
        self.assertEqual(input_event.modifiers, ModifierKey.NONE)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_arrow_up(self, mock_cocoa):
        """Test translating arrow up key."""
        # Create mock keyboard event for up arrow
        mock_event = Mock()
        mock_event.keyCode.return_value = 126  # Up arrow
        mock_event.characters.return_value = ''
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.UP)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_arrow_down(self, mock_cocoa):
        """Test translating arrow down key."""
        # Create mock keyboard event for down arrow
        mock_event = Mock()
        mock_event.keyCode.return_value = 125  # Down arrow
        mock_event.characters.return_value = ''
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.DOWN)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_arrow_left(self, mock_cocoa):
        """Test translating arrow left key."""
        # Create mock keyboard event for left arrow
        mock_event = Mock()
        mock_event.keyCode.return_value = 123  # Left arrow
        mock_event.characters.return_value = ''
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.LEFT)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_arrow_right(self, mock_cocoa):
        """Test translating arrow right key."""
        # Create mock keyboard event for right arrow
        mock_event = Mock()
        mock_event.keyCode.return_value = 124  # Right arrow
        mock_event.characters.return_value = ''
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.RIGHT)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_function_keys(self, mock_cocoa):
        """Test translating function keys."""
        # Test F1
        mock_event = Mock()
        mock_event.keyCode.return_value = 122  # F1
        mock_event.characters.return_value = ''
        mock_event.modifierFlags.return_value = 0
        
        input_event = self.backend._translate_keyboard_event(mock_event)
        self.assertEqual(input_event.key_code, KeyCode.F1)
        
        # Test F12
        mock_event.keyCode.return_value = 111  # F12
        input_event = self.backend._translate_keyboard_event(mock_event)
        self.assertEqual(input_event.key_code, KeyCode.F12)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_enter(self, mock_cocoa):
        """Test translating Enter key."""
        # Create mock keyboard event for Enter
        mock_event = Mock()
        mock_event.keyCode.return_value = 36  # Return key
        mock_event.characters.return_value = '\r'
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.ENTER)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_escape(self, mock_cocoa):
        """Test translating Escape key."""
        # Create mock keyboard event for Escape
        mock_event = Mock()
        mock_event.keyCode.return_value = 53  # Escape
        mock_event.characters.return_value = '\x1b'
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.ESCAPE)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_backspace(self, mock_cocoa):
        """Test translating Backspace key."""
        # Create mock keyboard event for Backspace
        mock_event = Mock()
        mock_event.keyCode.return_value = 51  # Delete/Backspace
        mock_event.characters.return_value = '\x7f'
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.BACKSPACE)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_delete(self, mock_cocoa):
        """Test translating Delete key."""
        # Create mock keyboard event for Delete
        mock_event = Mock()
        mock_event.keyCode.return_value = 117  # Forward delete
        mock_event.characters.return_value = ''
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.DELETE)
        self.assertIsNone(input_event.char)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_keyboard_event_with_modifiers(self, mock_cocoa):
        """Test translating keyboard event with modifiers."""
        # Create mock keyboard event for 'a' with Shift
        mock_event = Mock()
        mock_event.keyCode.return_value = 0  # 'a' key
        mock_event.characters.return_value = 'A'
        mock_cocoa.NSEventModifierFlagShift = 1 << 17
        mock_event.modifierFlags.return_value = mock_cocoa.NSEventModifierFlagShift
        
        # Translate event
        input_event = self.backend._translate_keyboard_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, ord('A'))
        self.assertEqual(input_event.char, 'A')
        self.assertTrue(input_event.modifiers & ModifierKey.SHIFT)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_mouse_event_left_button(self, mock_cocoa):
        """Test translating left mouse button event."""
        # Set up backend with window
        self.backend.window = Mock()
        self.backend.metal_view = Mock()
        content_view = Mock()
        content_rect = Mock()
        content_rect.size.height = 800
        content_view.frame.return_value = content_rect
        self.backend.window.contentView.return_value = content_view
        
        # Create mock mouse event
        mock_event = Mock()
        mock_cocoa.NSEventTypeLeftMouseDown = 1
        mock_event.type.return_value = mock_cocoa.NSEventTypeLeftMouseDown
        location = Mock()
        location.x = 100
        location.y = 600  # Bottom-left origin
        mock_event.locationInWindow.return_value = location
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_mouse_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.MOUSE)
        self.assertEqual(input_event.mouse_button, 1)  # Left button
        self.assertIsNotNone(input_event.mouse_row)
        self.assertIsNotNone(input_event.mouse_col)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_mouse_event_right_button(self, mock_cocoa):
        """Test translating right mouse button event."""
        # Set up backend with window
        self.backend.window = Mock()
        self.backend.metal_view = Mock()
        content_view = Mock()
        content_rect = Mock()
        content_rect.size.height = 800
        content_view.frame.return_value = content_rect
        self.backend.window.contentView.return_value = content_view
        
        # Create mock mouse event
        mock_event = Mock()
        mock_cocoa.NSEventTypeRightMouseDown = 3
        mock_event.type.return_value = mock_cocoa.NSEventTypeRightMouseDown
        location = Mock()
        location.x = 100
        location.y = 600
        mock_event.locationInWindow.return_value = location
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_mouse_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.MOUSE)
        self.assertEqual(input_event.mouse_button, 3)  # Right button
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_macos_event_keyboard(self, mock_cocoa):
        """Test translating macOS keyboard event."""
        # Create mock keyboard event
        mock_event = Mock()
        mock_cocoa.NSEventTypeKeyDown = 10
        mock_event.type.return_value = mock_cocoa.NSEventTypeKeyDown
        mock_event.keyCode.return_value = 0
        mock_event.characters.return_value = 'a'
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_macos_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.char, 'a')
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_macos_event_mouse(self, mock_cocoa):
        """Test translating macOS mouse event."""
        # Set up backend with window
        self.backend.window = Mock()
        self.backend.metal_view = Mock()
        content_view = Mock()
        content_rect = Mock()
        content_rect.size.height = 800
        content_view.frame.return_value = content_rect
        self.backend.window.contentView.return_value = content_view
        
        # Create mock mouse event
        mock_event = Mock()
        mock_cocoa.NSEventTypeLeftMouseDown = 1
        mock_event.type.return_value = mock_cocoa.NSEventTypeLeftMouseDown
        location = Mock()
        location.x = 100
        location.y = 600
        mock_event.locationInWindow.return_value = location
        mock_event.modifierFlags.return_value = 0
        
        # Translate event
        input_event = self.backend._translate_macos_event(mock_event)
        
        # Verify translation
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.key_code, KeyCode.MOUSE)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    def test_translate_macos_event_unsupported(self, mock_cocoa):
        """Test translating unsupported macOS event."""
        # Create mock unsupported event
        mock_event = Mock()
        mock_event.type.return_value = 9999  # Unknown event type
        
        # Translate event
        input_event = self.backend._translate_macos_event(mock_event)
        
        # Verify None is returned for unsupported events
        self.assertIsNone(input_event)
    
    @patch('ttk.backends.metal_backend.Cocoa')
    @patch('ttk.backends.metal_backend.Foundation')
    def test_get_input_returns_event(self, mock_foundation, mock_cocoa):
        """Test get_input returns translated event."""
        # Create mock application and event
        mock_app = Mock()
        mock_event = Mock()
        mock_cocoa.NSEventTypeKeyDown = 10
        mock_event.type.return_value = mock_cocoa.NSEventTypeKeyDown
        mock_event.keyCode.return_value = 0
        mock_event.characters.return_value = 'a'
        mock_event.modifierFlags.return_value = 0
        mock_app.nextEventMatchingMask_untilDate_inMode_dequeue_.return_value = mock_event
        mock_cocoa.NSApplication.sharedApplication.return_value = mock_app
        mock_foundation.NSDate.distantPast.return_value = Mock()
        
        # Get input
        input_event = self.backend.get_input(timeout_ms=0)
        
        # Verify event was returned
        self.assertIsNotNone(input_event)
        self.assertEqual(input_event.char, 'a')
    
    @patch('ttk.backends.metal_backend.Cocoa')
    @patch('ttk.backends.metal_backend.Foundation')
    def test_get_input_returns_none_on_timeout(self, mock_foundation, mock_cocoa):
        """Test get_input returns None when no event is available."""
        # Create mock application with no event
        mock_app = Mock()
        mock_app.nextEventMatchingMask_untilDate_inMode_dequeue_.return_value = None
        mock_cocoa.NSApplication.sharedApplication.return_value = mock_app
        mock_foundation.NSDate.distantPast.return_value = Mock()
        
        # Get input
        input_event = self.backend.get_input(timeout_ms=0)
        
        # Verify None was returned
        self.assertIsNone(input_event)


if __name__ == '__main__':
    unittest.main()
