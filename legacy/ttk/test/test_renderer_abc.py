"""
Test the Renderer abstract base class.

This test verifies that the Renderer ABC is properly defined and enforces
implementation of all abstract methods.
"""

import sys
import os

# Add parent directory to path to allow importing ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ttk.renderer import Renderer, TextAttribute


def test_renderer_is_abstract():
    """Test that Renderer cannot be instantiated directly."""
    try:
        renderer = Renderer()
        assert False, "Should not be able to instantiate Renderer directly"
    except TypeError as e:
        # Expected - Renderer is abstract
        assert "abstract" in str(e).lower()
        print("✓ Renderer is properly abstract")


def test_incomplete_implementation_raises_error():
    """Test that incomplete implementations raise TypeError."""
    
    class IncompleteRenderer(Renderer):
        """Incomplete implementation missing some methods."""
        
        def initialize(self):
            pass
        
        def shutdown(self):
            pass
        
        # Missing all other abstract methods
    
    try:
        renderer = IncompleteRenderer()
        assert False, "Should not be able to instantiate incomplete implementation"
    except TypeError as e:
        # Expected - missing abstract methods
        assert "abstract" in str(e).lower()
        print("✓ Incomplete implementation properly rejected")


def test_text_attribute_enum():
    """Test that TextAttribute enum is properly defined."""
    assert TextAttribute.NORMAL == 0
    assert TextAttribute.BOLD == 1
    assert TextAttribute.UNDERLINE == 2
    assert TextAttribute.REVERSE == 4
    print("✓ TextAttribute enum values are correct")


def test_text_attribute_combination():
    """Test that TextAttribute values can be combined with bitwise OR."""
    combined = TextAttribute.BOLD | TextAttribute.UNDERLINE
    assert combined == 3  # 1 | 2 = 3
    
    combined = TextAttribute.BOLD | TextAttribute.REVERSE
    assert combined == 5  # 1 | 4 = 5
    
    combined = TextAttribute.BOLD | TextAttribute.UNDERLINE | TextAttribute.REVERSE
    assert combined == 7  # 1 | 2 | 4 = 7
    
    print("✓ TextAttribute values can be combined")


def test_complete_implementation_can_be_instantiated():
    """Test that a complete implementation can be instantiated."""
    
    class CompleteRenderer(Renderer):
        """Complete implementation with all abstract methods."""
        
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
        
        def get_event(self, timeout_ms=-1):
            return None
        
        def get_input(self, timeout_ms=-1):
            return None
        
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
        
        def supports_drag_and_drop(self):
            return False
        
        def start_drag_session(self, file_urls, drag_image_text):
            return False
        
        def set_drag_completion_callback(self, callback):
            pass
    
    # Should be able to instantiate
    renderer = CompleteRenderer()
    assert renderer is not None
    print("✓ Complete implementation can be instantiated")
    
    # Test that methods can be called
    renderer.initialize()
    rows, cols = renderer.get_dimensions()
    assert rows == 24 and cols == 80
    renderer.clear()
    renderer.draw_text(0, 0, "test")
    renderer.refresh()
    renderer.shutdown()
    print("✓ All methods can be called on complete implementation")


if __name__ == '__main__':
    print("Testing Renderer ABC...")
    print()
    
    test_renderer_is_abstract()
    test_incomplete_implementation_raises_error()
    test_text_attribute_enum()
    test_text_attribute_combination()
    test_complete_implementation_can_be_instantiated()
    
    print()
    print("All tests passed! ✓")
