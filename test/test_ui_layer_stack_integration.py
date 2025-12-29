"""
Integration tests for UILayerStack with FileManager.

These tests verify that the UILayerStack is properly integrated into
the FileManager and that layers can be pushed and popped correctly.

Run with: PYTHONPATH=.:src:ttk pytest test/test_ui_layer_stack_integration.py -v
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from tfm_main import FileManager
from tfm_ui_layer import UILayer, UILayerStack


class MockLayer(UILayer):
    """Mock layer for testing."""
    
    def __init__(self, name="MockLayer"):
        self.name = name
        self._dirty = True
        self._should_close = False
        self.activated = False
        self.deactivated = False
        self.key_events_handled = []
        self.char_events_handled = []
        self.mouse_events_handled = []
        self.system_events_handled = []
        self.render_called = False
    
    def handle_key_event(self, event) -> bool:
        self.key_events_handled.append(event)
        return True
    
    def handle_char_event(self, event) -> bool:
        self.char_events_handled.append(event)
        return True
    
    def handle_system_event(self, event) -> bool:
        self.system_events_handled.append(event)
        return True
    
    def handle_mouse_event(self, event) -> bool:
        self.mouse_events_handled.append(event)
        return True
    
    def render(self, renderer) -> None:
        self.render_called = True
    
    def is_full_screen(self) -> bool:
        return False
    
    def needs_redraw(self) -> bool:
        return self._dirty
    
    def mark_dirty(self) -> None:
        self._dirty = True
    
    def clear_dirty(self) -> None:
        self._dirty = False
    
    def should_close(self) -> bool:
        return self._should_close
    
    def on_activate(self) -> None:
        self.activated = True
    
    def on_deactivate(self) -> None:
        self.deactivated = True


class TestUILayerStackIntegration(unittest.TestCase):
    """Test UILayerStack integration with FileManager."""
    
    @patch('tfm_main.get_state_manager')
    @patch('tfm_main.LogManager')
    @patch('tfm_main.init_colors')
    @patch('tfm_main.get_config')
    def setUp(self, mock_config, mock_init_colors, mock_log_manager, mock_state_manager):
        """Set up test fixtures."""
        # Mock configuration
        mock_config_instance = Mock()
        mock_config_instance.DEFAULT_LOG_HEIGHT_RATIO = 0.25
        mock_config_instance.CONFIRM_QUIT = False
        mock_config.return_value = mock_config_instance
        
        # Mock state manager
        mock_state_instance = Mock()
        mock_state_instance.load_window_layout = Mock(return_value=None)
        mock_state_instance.load_pane_state = Mock(return_value=None)
        mock_state_instance.update_session_heartbeat = Mock()
        mock_state_instance.cleanup_non_existing_directories = Mock()
        mock_state_manager.return_value = mock_state_instance
        
        # Mock log manager
        mock_log_instance = Mock()
        mock_log_instance.add_startup_messages = Mock()
        mock_log_instance.has_log_updates = Mock(return_value=False)
        mock_log_manager.return_value = mock_log_instance
        
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions = Mock(return_value=(24, 80))
        self.mock_renderer.set_event_callback = Mock()
        self.mock_renderer.set_cursor_visibility = Mock()
        self.mock_renderer.clear = Mock()
        self.mock_renderer.refresh = Mock()
        self.mock_renderer.draw_text = Mock()
        
        # Create FileManager instance
        self.file_manager = FileManager(self.mock_renderer)
    
    def test_file_manager_has_ui_layer_stack(self):
        """Test that FileManager has a UILayerStack instance."""
        self.assertIsInstance(self.file_manager.ui_layer_stack, UILayerStack)
    
    def test_ui_layer_stack_has_file_manager_layer_as_bottom(self):
        """Test that UILayerStack has FileManager as bottom layer."""
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 1)
        bottom_layer = self.file_manager.ui_layer_stack.get_top_layer()
        self.assertIsInstance(bottom_layer, FileManager)
    
    def test_push_layer_adds_to_stack(self):
        """Test that push_layer adds a layer to the stack."""
        mock_layer = MockLayer("TestLayer")
        
        # Push layer
        self.file_manager.push_layer(mock_layer)
        
        # Verify layer was added
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 2)
        self.assertEqual(self.file_manager.ui_layer_stack.get_top_layer(), mock_layer)
        self.assertTrue(mock_layer.activated)
    
    def test_pop_layer_removes_from_stack(self):
        """Test that pop_layer removes a layer from the stack."""
        mock_layer = MockLayer("TestLayer")
        
        # Push and pop layer
        self.file_manager.push_layer(mock_layer)
        popped_layer = self.file_manager.pop_layer()
        
        # Verify layer was removed
        self.assertEqual(popped_layer, mock_layer)
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 1)
        self.assertTrue(mock_layer.deactivated)
    
    def test_cannot_pop_bottom_layer(self):
        """Test that bottom layer cannot be popped."""
        # Try to pop bottom layer
        result = self.file_manager.pop_layer()
        
        # Verify operation was rejected
        self.assertIsNone(result)
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 1)
    
    def test_check_and_close_top_layer(self):
        """Test that check_and_close_top_layer closes layers that want to close."""
        mock_layer = MockLayer("TestLayer")
        mock_layer._should_close = True
        
        # Push layer
        self.file_manager.push_layer(mock_layer)
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 2)
        
        # Check and close
        closed = self.file_manager.check_and_close_top_layer()
        
        # Verify layer was closed
        self.assertTrue(closed)
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 1)
    
    def test_draw_interface_delegates_to_ui_layer_stack(self):
        """Test that draw_interface delegates to UILayerStack.render()."""
        # Mock the UILayerStack render method
        self.file_manager.ui_layer_stack.render = Mock()
        
        # Call draw_interface
        self.file_manager.draw_interface()
        
        # Verify delegation
        self.file_manager.ui_layer_stack.render.assert_called_once_with(self.mock_renderer)
    
    def test_multiple_layers_can_be_stacked(self):
        """Test that multiple layers can be stacked."""
        layer1 = MockLayer("Layer1")
        layer2 = MockLayer("Layer2")
        layer3 = MockLayer("Layer3")
        
        # Push multiple layers
        self.file_manager.push_layer(layer1)
        self.file_manager.push_layer(layer2)
        self.file_manager.push_layer(layer3)
        
        # Verify stack state
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 4)  # 3 + bottom layer
        self.assertEqual(self.file_manager.ui_layer_stack.get_top_layer(), layer3)
        
        # Pop layers and verify order
        self.assertEqual(self.file_manager.pop_layer(), layer3)
        self.assertEqual(self.file_manager.pop_layer(), layer2)
        self.assertEqual(self.file_manager.pop_layer(), layer1)
        self.assertEqual(self.file_manager.ui_layer_stack.get_layer_count(), 1)
