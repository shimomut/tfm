"""
Tests for CoreGraphics backend menu support.

This test module verifies that the CoreGraphics backend correctly implements
menu bar functionality including menu creation, menu item callbacks, and
menu event delivery.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys

# Mock PyObjC modules before importing the backend
cocoa_mock = MagicMock()
# Set up NSEventModifierFlag constants as integers
cocoa_mock.NSEventModifierFlagCommand = 1 << 20
cocoa_mock.NSEventModifierFlagShift = 1 << 17
cocoa_mock.NSEventModifierFlagControl = 1 << 18
cocoa_mock.NSEventModifierFlagOption = 1 << 19

sys.modules['Cocoa'] = cocoa_mock
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import MenuEvent


class TestCoreGraphicsMenuSupport(unittest.TestCase):
    """Test CoreGraphics backend menu support."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock backend with minimal initialization
        self.backend = CoreGraphicsBackend()
        
        # Mock the necessary attributes
        self.backend.window = Mock()
        self.backend.view = Mock()
        self.backend.menu_event_queue = []
        self.backend.menu_items = {}
    
    def test_parse_shortcut_cmd_n(self):
        """Test parsing 'Cmd+N' shortcut."""
        key, mask = self.backend._parse_shortcut('Cmd+N')
        
        self.assertEqual(key, 'n')
        self.assertIsNotNone(mask)
        # Verify Command flag is set (we can't check exact value without real Cocoa)
    
    def test_parse_shortcut_cmd_shift_s(self):
        """Test parsing 'Cmd+Shift+S' shortcut."""
        key, mask = self.backend._parse_shortcut('Cmd+Shift+S')
        
        # With Shift modifier, key should remain uppercase
        self.assertEqual(key, 'S')
        self.assertIsNotNone(mask)
    
    def test_parse_shortcut_ctrl_c(self):
        """Test parsing 'Ctrl+C' shortcut."""
        key, mask = self.backend._parse_shortcut('Ctrl+C')
        
        self.assertEqual(key, 'c')
        self.assertIsNotNone(mask)
    
    def test_parse_shortcut_empty(self):
        """Test parsing empty shortcut."""
        key, mask = self.backend._parse_shortcut('')
        
        self.assertEqual(key, '')
        self.assertIsNone(mask)
    
    def test_parse_shortcut_alt_f(self):
        """Test parsing 'Alt+F' shortcut."""
        key, mask = self.backend._parse_shortcut('Alt+F')
        
        self.assertEqual(key, 'f')
        self.assertIsNotNone(mask)
    
    def test_menu_item_selected_creates_event(self):
        """Test that menu item selection creates a MenuEvent."""
        # Create a mock sender with item ID
        sender = Mock()
        sender.representedObject.return_value = 'file.new'
        
        # Call the callback
        self.backend._menu_item_selected_(sender)
        
        # Verify event was added to queue
        self.assertEqual(len(self.backend.menu_event_queue), 1)
        event = self.backend.menu_event_queue[0]
        self.assertIsInstance(event, MenuEvent)
        self.assertEqual(event.item_id, 'file.new')
    
    def test_menu_item_selected_ignores_none_id(self):
        """Test that menu item selection with None ID is ignored."""
        # Create a mock sender with None item ID
        sender = Mock()
        sender.representedObject.return_value = None
        
        # Call the callback
        self.backend._menu_item_selected_(sender)
        
        # Verify no event was added
        self.assertEqual(len(self.backend.menu_event_queue), 0)
    
    def test_callback_receives_menu_event(self):
        """Test that menu events are delivered via callback."""
        from ttk.test.test_utils import EventCapture
        
        # Set up event capture
        capture = EventCapture()
        self.backend.event_callback = capture
        
        # Add a menu event to the queue
        menu_event = MenuEvent(item_id='file.quit')
        self.backend.menu_event_queue.append(menu_event)
        
        # Process events via callback
        self.backend.run_event_loop_iteration(timeout_ms=0)
        
        # Verify event was delivered via callback
        self.assertTrue(capture.has_event_type('system'))
        events = capture.get_all_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 'system')
        self.assertIsInstance(events[0][1], MenuEvent)
        self.assertEqual(events[0][1].item_id, 'file.quit')
    
    def test_update_menu_item_state_enables_item(self):
        """Test updating menu item state to enabled."""
        # Create a mock menu item
        mock_item = Mock()
        self.backend.menu_items['file.delete'] = mock_item
        
        # Enable the item
        self.backend.update_menu_item_state('file.delete', True)
        
        # Verify setEnabled was called with True
        mock_item.setEnabled_.assert_called_once_with(True)
    
    def test_update_menu_item_state_disables_item(self):
        """Test updating menu item state to disabled."""
        # Create a mock menu item
        mock_item = Mock()
        self.backend.menu_items['edit.paste'] = mock_item
        
        # Disable the item
        self.backend.update_menu_item_state('edit.paste', False)
        
        # Verify setEnabled was called with False
        mock_item.setEnabled_.assert_called_once_with(False)
    
    def test_update_menu_item_state_unknown_item(self):
        """Test updating state of unknown menu item (should not crash)."""
        # This should not raise an exception
        self.backend.update_menu_item_state('unknown.item', True)
    
    def test_update_menu_item_state_no_menu_items(self):
        """Test updating state when menu_items doesn't exist (should not crash)."""
        # Remove menu_items attribute
        delattr(self.backend, 'menu_items')
        
        # This should not raise an exception
        self.backend.update_menu_item_state('file.new', True)
    
    def test_multiple_menu_events_in_queue(self):
        """Test that multiple menu events are returned in order."""
        # Add multiple menu events
        event1 = MenuEvent(item_id='file.new')
        event2 = MenuEvent(item_id='edit.copy')
        event3 = MenuEvent(item_id='view.refresh')
        
        self.backend.menu_event_queue.extend([event1, event2, event3])
        
        # Get events in order
        e1 = self.backend.get_event(timeout_ms=0)
        e2 = self.backend.get_event(timeout_ms=0)
        e3 = self.backend.get_event(timeout_ms=0)
        
        self.assertEqual(e1.item_id, 'file.new')
        self.assertEqual(e2.item_id, 'edit.copy')
        self.assertEqual(e3.item_id, 'view.refresh')
        
        # Queue should be empty
        self.assertEqual(len(self.backend.menu_event_queue), 0)


if __name__ == '__main__':
    unittest.main()
