"""
Final integration tests for UI Layer Stack System.

This test suite verifies all functionality of the UI layer stack system
including dialog/viewer operations, event routing, rendering optimization,
and error handling.

Requirements tested: 6.6
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from src.tfm_ui_layer import UILayer, UILayerStack, FileManagerLayer
from src.tfm_list_dialog import ListDialog
from src.tfm_info_dialog import InfoDialog
from src.tfm_search_dialog import SearchDialog
from src.tfm_jump_dialog import JumpDialog
from src.tfm_drives_dialog import DrivesDialog
from src.tfm_batch_rename_dialog import BatchRenameDialog
from src.tfm_text_viewer import TextViewer
from src.tfm_diff_viewer import DiffViewer


class MockLayer(UILayer):
    """Mock layer for testing."""
    
    def __init__(self, name, full_screen=False, consume_events=True):
        self.name = name
        self._full_screen = full_screen
        self._consume_events = consume_events
        self._dirty = True
        self._should_close = False
        self._activated = False
        self._deactivated = False
        self.key_events_received = []
        self.char_events_received = []
        self.render_calls = []
    
    def handle_key_event(self, event):
        self.key_events_received.append(event)
        return self._consume_events
    
    def handle_char_event(self, event):
        self.char_events_received.append(event)
        return self._consume_events
    
    def render(self, renderer):
        self.render_calls.append(renderer)
    
    def is_full_screen(self):
        return self._full_screen
    
    def needs_redraw(self):
        return self._dirty
    
    def mark_dirty(self):
        self._dirty = True
    
    def clear_dirty(self):
        self._dirty = False
    
    def should_close(self):
        return self._should_close
    
    def on_activate(self):
        self._activated = True
    
    def on_deactivate(self):
        self._deactivated = True
    
    def request_close(self):
        self._should_close = True


class TestDialogOperations:
    """Test opening and closing dialogs."""
    
    def test_open_and_close_list_dialog(self):
        """Test opening and closing a ListDialog."""
        # Create stack with bottom layer
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        # Create and push dialog
        mock_renderer = Mock()
        dialog = ListDialog(
            config={
                'title': 'Test Dialog',
                'items': ['item1', 'item2'],
                'selected_index': 0
            },
            renderer=mock_renderer
        )
        
        stack.push(dialog)
        assert stack.get_layer_count() == 2
        assert stack.get_top_layer() == dialog
        
        # Close dialog
        dialog.is_active = False
        assert dialog.should_close()
        stack.check_and_close_top_layer()
        
        assert stack.get_layer_count() == 1
        assert stack.get_top_layer() == bottom
    
    def test_open_and_close_info_dialog(self):
        """Test opening and closing an InfoDialog."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        dialog = InfoDialog(
            config={
                'title': 'Info',
                'message': 'Test message'
            },
            renderer=mock_renderer
        )
        
        stack.push(dialog)
        assert stack.get_layer_count() == 2
        
        dialog.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_layer_count() == 1
    
    def test_open_and_close_search_dialog(self):
        """Test opening and closing a SearchDialog."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        mock_file_manager = Mock()
        dialog = SearchDialog(mock_renderer, mock_file_manager)
        
        stack.push(dialog)
        assert stack.get_layer_count() == 2
        
        dialog.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_layer_count() == 1
    
    def test_open_and_close_jump_dialog(self):
        """Test opening and closing a JumpDialog."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        mock_file_manager = Mock()
        dialog = JumpDialog(mock_renderer, mock_file_manager)
        
        stack.push(dialog)
        assert stack.get_layer_count() == 2
        
        dialog.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_layer_count() == 1


class TestViewerOperations:
    """Test opening and closing viewers."""
    
    def test_open_and_close_text_viewer(self):
        """Test opening and closing a TextViewer."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        mock_renderer.get_size.return_value = (80, 24)
        
        with patch('src.tfm_text_viewer.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.is_file.return_value = True
            mock_path.return_value.read_text.return_value = "test content"
            
            viewer = TextViewer(mock_renderer, "/tmp/test.txt")
            
            stack.push(viewer)
            assert stack.get_layer_count() == 2
            assert viewer.is_full_screen()
            
            viewer._should_close = True
            stack.check_and_close_top_layer()
            assert stack.get_layer_count() == 1
    
    def test_open_and_close_diff_viewer(self):
        """Test opening and closing a DiffViewer."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        mock_renderer.get_size.return_value = (80, 24)
        
        with patch('src.tfm_diff_viewer.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.is_file.return_value = True
            mock_path.return_value.read_text.return_value = "test content"
            
            viewer = DiffViewer(mock_renderer, "/tmp/file1.txt", "/tmp/file2.txt")
            
            stack.push(viewer)
            assert stack.get_layer_count() == 2
            assert viewer.is_full_screen()
            
            viewer._should_close = True
            stack.check_and_close_top_layer()
            assert stack.get_layer_count() == 1


class TestStackingMultipleDialogs:
    """Test stacking multiple dialogs."""
    
    def test_stack_two_dialogs(self):
        """Test stacking two dialogs on top of each other."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        
        # Push first dialog
        dialog1 = ListDialog(
            config={'title': 'Dialog 1', 'items': ['a'], 'selected_index': 0},
            renderer=mock_renderer
        )
        stack.push(dialog1)
        assert stack.get_layer_count() == 2
        
        # Push second dialog
        dialog2 = ListDialog(
            config={'title': 'Dialog 2', 'items': ['b'], 'selected_index': 0},
            renderer=mock_renderer
        )
        stack.push(dialog2)
        assert stack.get_layer_count() == 3
        assert stack.get_top_layer() == dialog2
        
        # Close second dialog
        dialog2.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_layer_count() == 2
        assert stack.get_top_layer() == dialog1
        
        # Close first dialog
        dialog1.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_layer_count() == 1
        assert stack.get_top_layer() == bottom
    
    def test_stack_three_dialogs(self):
        """Test stacking three dialogs."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        
        dialogs = []
        for i in range(3):
            dialog = ListDialog(
                config={'title': f'Dialog {i}', 'items': [f'{i}'], 'selected_index': 0},
                renderer=mock_renderer
            )
            stack.push(dialog)
            dialogs.append(dialog)
        
        assert stack.get_layer_count() == 4
        
        # Close in reverse order
        for i in range(2, -1, -1):
            assert stack.get_top_layer() == dialogs[i]
            dialogs[i].is_active = False
            stack.check_and_close_top_layer()
        
        assert stack.get_layer_count() == 1
        assert stack.get_top_layer() == bottom


class TestFullScreenViewerWithDialog:
    """Test full-screen viewer with dialog on top."""
    
    def test_viewer_with_dialog_on_top(self):
        """Test opening a dialog on top of a full-screen viewer."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        mock_renderer.get_size.return_value = (80, 24)
        
        # Open viewer
        with patch('src.tfm_text_viewer.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.is_file.return_value = True
            mock_path.return_value.read_text.return_value = "test content"
            
            viewer = TextViewer(mock_renderer, "/tmp/test.txt")
            stack.push(viewer)
            assert stack.get_layer_count() == 2
        
        # Open dialog on top of viewer
        dialog = ListDialog(
            config={'title': 'Help', 'items': ['help1'], 'selected_index': 0},
            renderer=mock_renderer
        )
        stack.push(dialog)
        assert stack.get_layer_count() == 3
        assert stack.get_top_layer() == dialog
        
        # Verify viewer is still in stack
        assert stack._layers[1] == viewer
        
        # Close dialog
        dialog.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_layer_count() == 2
        assert stack.get_top_layer() == viewer
        
        # Close viewer
        viewer._should_close = True
        stack.check_and_close_top_layer()
        assert stack.get_layer_count() == 1
    
    def test_multiple_dialogs_on_viewer(self):
        """Test stacking multiple dialogs on top of a viewer."""
        bottom = MockLayer("bottom", full_screen=True)
        stack = UILayerStack(bottom)
        
        mock_renderer = Mock()
        mock_renderer.get_size.return_value = (80, 24)
        
        # Open viewer
        with patch('src.tfm_text_viewer.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.is_file.return_value = True
            mock_path.return_value.read_text.return_value = "test content"
            
            viewer = TextViewer(mock_renderer, "/tmp/test.txt")
            stack.push(viewer)
        
        # Open two dialogs
        dialog1 = ListDialog(
            config={'title': 'Dialog 1', 'items': ['a'], 'selected_index': 0},
            renderer=mock_renderer
        )
        stack.push(dialog1)
        
        dialog2 = ListDialog(
            config={'title': 'Dialog 2', 'items': ['b'], 'selected_index': 0},
            renderer=mock_renderer
        )
        stack.push(dialog2)
        
        assert stack.get_layer_count() == 4
        
        # Close dialogs
        dialog2.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_top_layer() == dialog1
        
        dialog1.is_active = False
        stack.check_and_close_top_layer()
        assert stack.get_top_layer() == viewer


class TestEventRoutingThroughLayers:
    """Test event routing through multiple layers."""
    
    def test_event_goes_to_top_layer_first(self):
        """Test that events are routed to the top layer first."""
        bottom = MockLayer("bottom", consume_events=False)
        middle = MockLayer("middle", consume_events=False)
        top = MockLayer("top", consume_events=True)
        
        stack = UILayerStack(bottom)
        stack.push(middle)
        stack.push(top)
        
        mock_event = Mock()
        result = stack.handle_key_event(mock_event)
        
        assert result is True
        assert len(top.key_events_received) == 1
        assert len(middle.key_events_received) == 0
        assert len(bottom.key_events_received) == 0
    
    def test_event_propagates_when_not_consumed(self):
        """Test that events only go to top layer (no propagation)."""
        bottom = MockLayer("bottom", consume_events=True)
        middle = MockLayer("middle", consume_events=False)
        top = MockLayer("top", consume_events=False)
        
        stack = UILayerStack(bottom)
        stack.push(middle)
        stack.push(top)
        
        mock_event = Mock()
        result = stack.handle_key_event(mock_event)
        
        # Only top layer receives events (no propagation)
        assert result is False  # Top doesn't consume
        assert len(top.key_events_received) == 1
        assert len(middle.key_events_received) == 0
        assert len(bottom.key_events_received) == 0
    
    def test_event_stops_at_consuming_layer(self):
        """Test that only top layer receives events."""
        bottom = MockLayer("bottom", consume_events=True)
        middle = MockLayer("middle", consume_events=True)
        top = MockLayer("top", consume_events=False)
        
        stack = UILayerStack(bottom)
        stack.push(middle)
        stack.push(top)
        
        mock_event = Mock()
        result = stack.handle_key_event(mock_event)
        
        # Only top layer receives events (no propagation)
        assert result is False  # Top doesn't consume
        assert len(top.key_events_received) == 1
        assert len(middle.key_events_received) == 0
        assert len(bottom.key_events_received) == 0
    
    def test_char_event_routing(self):
        """Test character event routing through layers."""
        bottom = MockLayer("bottom", consume_events=False)
        top = MockLayer("top", consume_events=True)
        
        stack = UILayerStack(bottom)
        stack.push(top)
        
        mock_event = Mock()
        result = stack.handle_char_event(mock_event)
        
        assert result is True
        assert len(top.char_events_received) == 1
        assert len(bottom.char_events_received) == 0


class TestRenderingOptimization:
    """Test rendering optimization with full-screen layers."""
    
    def test_fullscreen_layer_skips_lower_layers(self):
        """Test that full-screen layers skip rendering lower layers."""
        bottom = MockLayer("bottom", full_screen=True)
        middle = MockLayer("middle", full_screen=True)
        top = MockLayer("top", full_screen=False)
        
        stack = UILayerStack(bottom)
        stack.push(middle)
        stack.push(top)
        
        mock_renderer = Mock()
        stack.render(mock_renderer)
        
        # Bottom should not be rendered (obscured by middle)
        assert len(bottom.render_calls) == 0
        # Middle should be rendered (topmost full-screen)
        assert len(middle.render_calls) == 1
        # Top should be rendered (above middle)
        assert len(top.render_calls) == 1
    
    def test_dirty_tracking_optimization(self):
        """Test that only dirty layers are rendered."""
        bottom = MockLayer("bottom", full_screen=True)
        top = MockLayer("top", full_screen=False)
        
        stack = UILayerStack(bottom)
        stack.push(top)
        
        # First render - both dirty
        mock_renderer = Mock()
        stack.render(mock_renderer)
        
        assert len(bottom.render_calls) == 1
        assert len(top.render_calls) == 1
        
        # Second render - nothing dirty
        bottom._dirty = False
        top._dirty = False
        stack.render(mock_renderer)
        
        # No additional renders
        assert len(bottom.render_calls) == 1
        assert len(top.render_calls) == 1
    
    def test_lower_layer_redraw_marks_upper_dirty(self):
        """Test that redrawing a lower layer marks upper layers dirty."""
        bottom = MockLayer("bottom", full_screen=True)
        top = MockLayer("top", full_screen=False)
        
        stack = UILayerStack(bottom)
        stack.push(top)
        
        # First render
        mock_renderer = Mock()
        stack.render(mock_renderer)
        
        # Mark only bottom dirty
        bottom._dirty = True
        top._dirty = False
        
        # Render again
        stack.render(mock_renderer)
        
        # Both should have been rendered
        assert len(bottom.render_calls) == 2
        assert len(top.render_calls) == 2
    
    def test_fullscreen_removal_restores_rendering(self):
        """Test that removing a full-screen layer restores rendering of lower layers."""
        bottom = MockLayer("bottom", full_screen=True)
        middle = MockLayer("middle", full_screen=True)
        
        stack = UILayerStack(bottom)
        stack.push(middle)
        
        # Render with middle on top
        mock_renderer = Mock()
        stack.render(mock_renderer)
        
        # Bottom should not be rendered
        assert len(bottom.render_calls) == 0
        assert len(middle.render_calls) == 1
        
        # Remove middle
        middle._should_close = True
        stack.check_and_close_top_layer()
        
        # Mark bottom dirty and render
        bottom._dirty = True
        stack.render(mock_renderer)
        
        # Now bottom should be rendered
        assert len(bottom.render_calls) == 1


class TestErrorHandling:
    """Test error handling with exception-throwing layers."""
    
    def test_exception_during_key_event_handling(self):
        """Test that exceptions during key event handling are caught."""
        
        class ExceptionLayer(MockLayer):
            def handle_key_event(self, event):
                raise ValueError("Test exception")
        
        bottom = MockLayer("bottom", consume_events=True)
        exception_layer = ExceptionLayer("exception")
        
        stack = UILayerStack(bottom)
        stack.push(exception_layer)
        
        mock_event = Mock()
        # Should not raise exception
        result = stack.handle_key_event(mock_event)
        
        # Exception caught, event not consumed (no propagation)
        assert result is False
        assert len(bottom.key_events_received) == 0
    
    def test_exception_during_char_event_handling(self):
        """Test that exceptions during char event handling are caught."""
        
        class ExceptionLayer(MockLayer):
            def handle_char_event(self, event):
                raise ValueError("Test exception")
        
        bottom = MockLayer("bottom", consume_events=True)
        exception_layer = ExceptionLayer("exception")
        
        stack = UILayerStack(bottom)
        stack.push(exception_layer)
        
        mock_event = Mock()
        # Should not raise exception
        result = stack.handle_char_event(mock_event)
        
        # Exception caught, event not consumed (no propagation)
        assert result is False
        assert len(bottom.char_events_received) == 0
    
    def test_exception_during_rendering(self):
        """Test that exceptions during rendering are caught."""
        
        class ExceptionLayer(MockLayer):
            def render(self, renderer):
                raise ValueError("Test exception")
        
        bottom = MockLayer("bottom", full_screen=True)
        exception_layer = ExceptionLayer("exception", full_screen=False)
        
        stack = UILayerStack(bottom)
        stack.push(exception_layer)
        
        mock_renderer = Mock()
        # Should not raise exception
        stack.render(mock_renderer)
        
        # Bottom layer should still be rendered
        assert len(bottom.render_calls) == 1
    
    def test_multiple_exceptions_dont_stop_processing(self):
        """Test that exception in top layer is caught (no propagation)."""
        
        class ExceptionLayer(MockLayer):
            def handle_key_event(self, event):
                raise ValueError("Test exception")
        
        bottom = MockLayer("bottom", consume_events=True)
        exception1 = ExceptionLayer("exception1")
        exception2 = ExceptionLayer("exception2")
        
        stack = UILayerStack(bottom)
        stack.push(exception1)
        stack.push(exception2)
        
        mock_event = Mock()
        result = stack.handle_key_event(mock_event)
        
        # Only top layer (exception2) receives event, exception caught
        assert result is False
        assert len(bottom.key_events_received) == 0


class TestExistingFunctionality:
    """Verify all existing functionality still works."""
    
    def test_lifecycle_callbacks_called(self):
        """Test that lifecycle callbacks are called correctly."""
        bottom = MockLayer("bottom")
        layer1 = MockLayer("layer1")
        layer2 = MockLayer("layer2")
        
        stack = UILayerStack(bottom)
        
        # Push layer1
        stack.push(layer1)
        assert layer1._activated is True
        assert bottom._deactivated is True
        
        # Push layer2
        layer1._activated = False
        layer1._deactivated = False
        stack.push(layer2)
        assert layer2._activated is True
        assert layer1._deactivated is True
        
        # Pop layer2
        layer2._activated = False
        layer2._deactivated = False
        layer1._activated = False
        stack.pop()
        assert layer2._deactivated is True
        assert layer1._activated is True
    
    def test_bottom_layer_cannot_be_removed(self):
        """Test that the bottom layer cannot be removed."""
        bottom = MockLayer("bottom")
        stack = UILayerStack(bottom)
        
        result = stack.pop()
        assert result is None
        assert stack.get_layer_count() == 1
        assert stack.get_top_layer() == bottom
    
    def test_get_layer_count(self):
        """Test getting the layer count."""
        bottom = MockLayer("bottom")
        stack = UILayerStack(bottom)
        
        assert stack.get_layer_count() == 1
        
        stack.push(MockLayer("layer1"))
        assert stack.get_layer_count() == 2
        
        stack.push(MockLayer("layer2"))
        assert stack.get_layer_count() == 3
        
        stack.pop()
        assert stack.get_layer_count() == 2
    
    def test_check_and_close_top_layer(self):
        """Test the check_and_close_top_layer method."""
        bottom = MockLayer("bottom")
        top = MockLayer("top")
        
        stack = UILayerStack(bottom)
        stack.push(top)
        
        # Top layer doesn't want to close
        result = stack.check_and_close_top_layer()
        assert result is False
        assert stack.get_layer_count() == 2
        
        # Top layer wants to close
        top._should_close = True
        result = stack.check_and_close_top_layer()
        assert result is True
        assert stack.get_layer_count() == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
