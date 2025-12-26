"""
Test the Renderer drag-and-drop interface.

This test verifies that the drag-and-drop methods are properly defined
in the Renderer abstract base class.
"""

import sys
import os

# Add parent directory to path to allow importing ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ttk.renderer import Renderer


class TestRendererDragAndDropInterface:
    """Test cases for Renderer drag-and-drop interface."""
    
    def test_renderer_has_supports_drag_and_drop(self):
        """Test that Renderer has supports_drag_and_drop abstract method."""
        assert hasattr(Renderer, 'supports_drag_and_drop')
        assert callable(getattr(Renderer, 'supports_drag_and_drop'))
    
    def test_renderer_has_start_drag_session(self):
        """Test that Renderer has start_drag_session abstract method."""
        assert hasattr(Renderer, 'start_drag_session')
        assert callable(getattr(Renderer, 'start_drag_session'))
    
    def test_renderer_has_set_drag_completion_callback(self):
        """Test that Renderer has set_drag_completion_callback abstract method."""
        assert hasattr(Renderer, 'set_drag_completion_callback')
        assert callable(getattr(Renderer, 'set_drag_completion_callback'))
    
    def test_drag_and_drop_methods_are_abstract(self):
        """Test that drag-and-drop methods are abstract and must be implemented."""
        
        class IncompleteRenderer(Renderer):
            """Implementation missing drag-and-drop methods."""
            
            def initialize(self):
                pass
            
            def shutdown(self):
                pass
            
            def get_dimensions(self):
                return (24, 80)
            
            def clear(self):
                pass
            
            def clear_region(self, row, col, height, width):
                pass
            
            def draw_text(self, row, col, text, color_pair=0, attributes=0):
                pass
            
            def draw_hline(self, row, col, char, length, color_pair=0):
                pass
            
            def draw_vline(self, row, col, char, length, color_pair=0):
                pass
            
            def draw_rect(self, row, col, height, width, color_pair=0, filled=False):
                pass
            
            def refresh(self):
                pass
            
            def refresh_region(self, row, col, height, width):
                pass
            
            def init_color_pair(self, pair_id, fg_color, bg_color):
                pass
            
            def set_cursor_visibility(self, visible):
                pass
            
            def move_cursor(self, row, col):
                pass
            
            def set_menu_bar(self, menu_structure):
                pass
            
            def update_menu_item_state(self, item_id, enabled):
                pass
            
            def set_event_callback(self, callback):
                pass
            
            def run_event_loop(self):
                pass
            
            def run_event_loop_iteration(self, timeout_ms=-1):
                pass
            
            def set_caret_position(self, x, y):
                pass
            
            def supports_mouse(self):
                return False
            
            def get_supported_mouse_events(self):
                return set()
            
            def enable_mouse_events(self):
                return False
            
            # Missing: supports_drag_and_drop, start_drag_session, set_drag_completion_callback
        
        # Should not be able to instantiate without drag-and-drop methods
        try:
            renderer = IncompleteRenderer()
            assert False, "Should not be able to instantiate without drag-and-drop methods"
        except TypeError as e:
            # Expected - missing abstract methods
            assert "abstract" in str(e).lower()
            # Verify the error mentions the missing drag-and-drop methods
            error_msg = str(e)
            assert "supports_drag_and_drop" in error_msg or "drag" in error_msg.lower()


class TestDragAndDropImplementation:
    """Test that a complete implementation with drag-and-drop can be instantiated."""
    
    def test_complete_implementation_with_drag_and_drop(self):
        """Test that implementation with all drag-and-drop methods works."""
        
        class CompleteRenderer(Renderer):
            """Complete implementation including drag-and-drop."""
            
            def initialize(self):
                pass
            
            def shutdown(self):
                pass
            
            def get_dimensions(self):
                return (24, 80)
            
            def clear(self):
                pass
            
            def clear_region(self, row, col, height, width):
                pass
            
            def draw_text(self, row, col, text, color_pair=0, attributes=0):
                pass
            
            def draw_hline(self, row, col, char, length, color_pair=0):
                pass
            
            def draw_vline(self, row, col, char, length, color_pair=0):
                pass
            
            def draw_rect(self, row, col, height, width, color_pair=0, filled=False):
                pass
            
            def refresh(self):
                pass
            
            def refresh_region(self, row, col, height, width):
                pass
            
            def init_color_pair(self, pair_id, fg_color, bg_color):
                pass
            
            def set_cursor_visibility(self, visible):
                pass
            
            def move_cursor(self, row, col):
                pass
            
            def set_menu_bar(self, menu_structure):
                pass
            
            def update_menu_item_state(self, item_id, enabled):
                pass
            
            def set_event_callback(self, callback):
                pass
            
            def run_event_loop(self):
                pass
            
            def run_event_loop_iteration(self, timeout_ms=-1):
                pass
            
            def set_caret_position(self, x, y):
                pass
            
            def supports_mouse(self):
                return False
            
            def get_supported_mouse_events(self):
                return set()
            
            def enable_mouse_events(self):
                return False
            
            # Drag-and-drop methods
            def supports_drag_and_drop(self):
                return False
            
            def start_drag_session(self, file_urls, drag_image_text):
                return False
            
            def set_drag_completion_callback(self, callback):
                pass
        
        # Should be able to instantiate
        renderer = CompleteRenderer()
        assert renderer is not None
        
        # Test drag-and-drop methods can be called
        assert renderer.supports_drag_and_drop() == False
        assert renderer.start_drag_session([], "test") == False
        renderer.set_drag_completion_callback(lambda completed: None)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
