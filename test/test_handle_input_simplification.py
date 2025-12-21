"""
Test that the simplified handle_input method correctly delegates to UILayerStack.

This test verifies that task 14 (Remove if-elif chains from handle_input) was
completed successfully by ensuring event routing goes through the layer stack.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import sys
import inspect

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ttk import KeyEvent, CharEvent, KeyCode
from tfm_main import FileManager


class TestHandleInputSimplification(unittest.TestCase):
    """Test the simplified handle_input method delegates to UILayerStack"""
    
    @patch('tfm_main.get_state_manager')
    @patch('tfm_main.LogManager')
    @patch('tfm_main.init_colors')
    @patch('tfm_main.get_config')
    def setUp(self, mock_config, mock_init_colors, mock_log_manager, mock_state_manager):
        """Set up test fixtures"""
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
        
        # Mock the ui_layer_stack for delegation tests
        self.mock_layer_stack = Mock()
        self.file_manager.ui_layer_stack = self.mock_layer_stack
    
    def test_key_event_delegates_to_layer_stack(self):
        """Test that KeyEvents are delegated to UILayerStack.handle_key_event()"""
        # Create a key event
        event = KeyEvent(key_code=KeyCode.UP, modifiers=0, char='')
        
        # Configure mock to consume the event
        self.mock_layer_stack.handle_key_event.return_value = True
        self.mock_layer_stack.check_and_close_top_layer.return_value = False
        
        # Handle the event
        result = self.file_manager.handle_input(event)
        
        # Verify delegation occurred
        self.mock_layer_stack.handle_key_event.assert_called_once_with(event)
        self.assertTrue(result)
    
    def test_char_event_delegates_to_layer_stack(self):
        """Test that CharEvents are delegated to UILayerStack.handle_char_event()"""
        # Create a char event
        event = CharEvent(char='a')
        
        # Configure mock to consume the event
        self.mock_layer_stack.handle_char_event.return_value = True
        self.mock_layer_stack.check_and_close_top_layer.return_value = False
        
        # Handle the event
        result = self.file_manager.handle_input(event)
        
        # Verify delegation occurred
        self.mock_layer_stack.handle_char_event.assert_called_once_with(event)
        self.assertTrue(result)
    
    def test_layer_close_triggers_redraw(self):
        """Test that closing a layer triggers a redraw"""
        # Create a key event
        event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0, char='')
        
        # Configure mock to close a layer
        self.mock_layer_stack.handle_key_event.return_value = True
        self.mock_layer_stack.check_and_close_top_layer.return_value = True
        
        # Reset redraw flag
        self.file_manager.needs_full_redraw = False
        
        # Handle the event
        self.file_manager.handle_input(event)
        
        # Verify redraw was triggered
        self.assertTrue(self.file_manager.needs_full_redraw)
    
    def test_consumed_event_triggers_redraw(self):
        """Test that consuming an event triggers a redraw"""
        # Create a key event
        event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0, char='')
        
        # Configure mock to consume the event
        self.mock_layer_stack.handle_key_event.return_value = True
        self.mock_layer_stack.check_and_close_top_layer.return_value = False
        
        # Reset redraw flag
        self.file_manager.needs_full_redraw = False
        
        # Handle the event
        self.file_manager.handle_input(event)
        
        # Verify redraw was triggered
        self.assertTrue(self.file_manager.needs_full_redraw)
    
    def test_unconsumed_event_no_redraw(self):
        """Test that unconsumed events don't trigger redraw"""
        # Create a key event
        event = KeyEvent(key_code=KeyCode.F1, modifiers=0, char='')
        
        # Configure mock to not consume the event
        self.mock_layer_stack.handle_key_event.return_value = False
        self.mock_layer_stack.check_and_close_top_layer.return_value = False
        
        # Reset redraw flag
        self.file_manager.needs_full_redraw = False
        
        # Handle the event
        result = self.file_manager.handle_input(event)
        
        # Verify no redraw was triggered
        self.assertFalse(self.file_manager.needs_full_redraw)
        self.assertFalse(result)
    
    def test_isearch_mode_bypasses_layer_stack(self):
        """Test that isearch mode events bypass the layer stack"""
        # Enable isearch mode
        self.file_manager.isearch_mode = True
        
        # Create a key event
        event = KeyEvent(key_code=KeyCode.UP, modifiers=0, char='')
        
        # Mock the isearch handler
        with patch.object(self.file_manager, 'handle_isearch_input', return_value=True):
            # Handle the event
            result = self.file_manager.handle_input(event)
            
            # Verify layer stack was NOT called
            self.mock_layer_stack.handle_key_event.assert_not_called()
            self.assertTrue(result)
    
    def test_quick_edit_bar_bypasses_layer_stack(self):
        """Test that general dialog events bypass the layer stack"""
        # Activate general dialog
        self.file_manager.quick_edit_bar.is_active = True
        self.file_manager.quick_edit_bar.handle_input = Mock(return_value=True)
        
        # Create a key event
        event = KeyEvent(key_code=KeyCode.ENTER, modifiers=0, char='')
        
        # Handle the event
        result = self.file_manager.handle_input(event)
        
        # Verify layer stack was NOT called
        self.mock_layer_stack.handle_key_event.assert_not_called()
        self.assertTrue(result)
    
    def test_quick_choice_bypasses_layer_stack(self):
        """Test that quick choice bar events bypass the layer stack"""
        # Activate quick choice bar
        self.file_manager.quick_choice_bar.is_active = True
        
        # Create a key event
        event = KeyEvent(key_code=KeyCode.UP, modifiers=0, char='')
        
        # Mock the quick choice handler
        with patch.object(self.file_manager, 'handle_quick_choice_input', return_value=True):
            # Handle the event
            result = self.file_manager.handle_input(event)
            
            # Verify layer stack was NOT called
            self.mock_layer_stack.handle_key_event.assert_not_called()
            self.assertTrue(result)
    
    def test_no_dialog_if_elif_chains(self):
        """Test that there are no if-elif chains checking dialog.is_active in handle_input"""
        # Read the handle_input method source
        source = inspect.getsource(self.file_manager.handle_input)
        
        # Verify no dialog-specific if-elif chains exist
        # These should have been removed in task 14
        self.assertNotIn('if self.info_dialog.is_active:', source)
        self.assertNotIn('if self.list_dialog.is_active:', source)
        self.assertNotIn('if self.search_dialog.is_active:', source)
        self.assertNotIn('if self.jump_dialog.is_active:', source)
        self.assertNotIn('if self.drives_dialog.is_active:', source)
        self.assertNotIn('if self.batch_rename_dialog.is_active:', source)
        self.assertNotIn('if self.active_viewer:', source)
    
    def test_get_active_text_widget_removed(self):
        """Test that get_active_text_widget method was removed"""
        # Verify the method no longer exists
        self.assertFalse(hasattr(self.file_manager, 'get_active_text_widget'))


if __name__ == '__main__':
    unittest.main()
