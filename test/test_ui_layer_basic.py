"""
Basic tests for UILayer and UILayerStack implementation.

These tests verify that the core functionality of the UI layer stack system
works correctly, including stack operations, event routing, and rendering.

Run with: PYTHONPATH=.:src:ttk pytest test/test_ui_layer_basic.py -v
"""

import pytest
from src.tfm_ui_layer import UILayer, UILayerStack


class MockLayer(UILayer):
    """Mock layer for testing purposes."""
    
    def __init__(self, name, full_screen=False):
        self.name = name
        self.full_screen = full_screen
        self.dirty = True
        self.close_requested = False
        self.activated = False
        self.deactivated = False
        self.key_events_received = []
        self.char_events_received = []
        self.mouse_events_received = []
        self.system_events_received = []
        self.render_calls = 0
    
    def handle_key_event(self, event) -> bool:
        self.key_events_received.append(event)
        return event.get('consume', False)
    
    def handle_char_event(self, event) -> bool:
        self.char_events_received.append(event)
        return event.get('consume', False)
    
    def handle_system_event(self, event) -> bool:
        self.system_events_received.append(event)
        return event.get('consume', False)
    
    def handle_mouse_event(self, event) -> bool:
        self.mouse_events_received.append(event)
        return event.get('consume', False)
    
    def render(self, renderer) -> None:
        self.render_calls += 1
    
    def is_full_screen(self) -> bool:
        return self.full_screen
    
    def needs_redraw(self) -> bool:
        return self.dirty
    
    def mark_dirty(self) -> None:
        self.dirty = True
    
    def clear_dirty(self) -> None:
        self.dirty = False
    
    def should_close(self) -> bool:
        return self.close_requested
    
    def on_activate(self) -> None:
        self.activated = True
    
    def on_deactivate(self) -> None:
        self.deactivated = True


class MockRenderer:
    """Mock renderer for testing purposes."""
    
    def __init__(self):
        self.refresh_calls = 0
    
    def refresh(self):
        self.refresh_calls += 1


def test_stack_initialization():
    """Test that stack initializes with bottom layer."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    assert stack.get_layer_count() == 1
    assert stack.get_top_layer() == bottom
    assert bottom.activated


def test_push_layer():
    """Test pushing a layer onto the stack."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    top = MockLayer("top")
    stack.push(top)
    
    assert stack.get_layer_count() == 2
    assert stack.get_top_layer() == top
    assert bottom.deactivated
    assert top.activated


def test_pop_layer():
    """Test popping a layer from the stack."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    top = MockLayer("top")
    stack.push(top)
    
    # Reset flags
    bottom.activated = False
    top.deactivated = False
    
    popped = stack.pop()
    
    assert popped == top
    assert stack.get_layer_count() == 1
    assert stack.get_top_layer() == bottom
    assert top.deactivated
    assert bottom.activated


def test_cannot_pop_bottom_layer():
    """Test that bottom layer cannot be removed."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    result = stack.pop()
    
    assert result is None
    assert stack.get_layer_count() == 1
    assert stack.get_top_layer() == bottom


def test_event_routing_to_top_layer():
    """Test that events are routed to top layer first."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    top = MockLayer("top")
    stack.push(top)
    
    event = {'type': 'key', 'consume': True}
    result = stack.handle_key_event(event)
    
    assert result is True
    assert len(top.key_events_received) == 1
    assert len(bottom.key_events_received) == 0


def test_event_propagation():
    """Test that events only go to top layer (no propagation)."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    top = MockLayer("top")
    stack.push(top)
    
    event = {'type': 'key', 'consume': False}
    result = stack.handle_key_event(event)
    
    # Only top layer receives events (no propagation)
    assert len(top.key_events_received) == 1
    assert len(bottom.key_events_received) == 0


def test_rendering_dirty_layers():
    """Test that only dirty layers are rendered."""
    bottom = MockLayer("bottom", full_screen=True)
    stack = UILayerStack(bottom)
    
    renderer = MockRenderer()
    stack.render(renderer)
    
    assert bottom.render_calls == 1
    assert bottom.dirty is False
    assert renderer.refresh_calls == 1


def test_full_screen_optimization():
    """Test that layers below full-screen layer are not rendered."""
    bottom = MockLayer("bottom", full_screen=True)
    bottom.dirty = False  # Bottom is clean
    stack = UILayerStack(bottom)
    
    top = MockLayer("top", full_screen=True)
    top.dirty = True  # Top is dirty
    stack.push(top)
    
    renderer = MockRenderer()
    stack.render(renderer)
    
    # Only top should be rendered (bottom is obscured)
    assert bottom.render_calls == 0
    assert top.render_calls == 1


def test_check_and_close_top_layer():
    """Test that layers can signal they want to close."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    top = MockLayer("top")
    stack.push(top)
    
    # Layer doesn't want to close yet
    result = stack.check_and_close_top_layer()
    assert result is False
    assert stack.get_layer_count() == 2
    
    # Layer wants to close
    top.close_requested = True
    result = stack.check_and_close_top_layer()
    assert result is True
    assert stack.get_layer_count() == 1


def test_mouse_event_routing_to_top_layer():
    """Test that mouse events are routed to top layer only."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    top = MockLayer("top")
    stack.push(top)
    
    event = {'type': 'mouse', 'consume': True}
    result = stack.handle_mouse_event(event)
    
    assert result is True
    assert len(top.mouse_events_received) == 1
    assert len(bottom.mouse_events_received) == 0


def test_mouse_event_no_propagation():
    """Test that mouse events only go to top layer (no propagation)."""
    bottom = MockLayer("bottom")
    stack = UILayerStack(bottom)
    
    top = MockLayer("top")
    stack.push(top)
    
    event = {'type': 'mouse', 'consume': False}
    result = stack.handle_mouse_event(event)
    
    # Only top layer receives events (no propagation)
    assert len(top.mouse_events_received) == 1
    assert len(bottom.mouse_events_received) == 0


def test_is_point_inside_default_implementation():
    """Test the default is_point_inside implementation."""
    layer = MockLayer("test")
    
    # Without bounds attributes, should return False
    assert layer.is_point_inside(5, 5) is False
    
    # Add bounds attributes
    layer.x = 10
    layer.y = 10
    layer.width = 20
    layer.height = 15
    
    # Test points inside bounds
    assert layer.is_point_inside(10, 10) is True  # Top-left corner
    assert layer.is_point_inside(15, 15) is True  # Inside
    assert layer.is_point_inside(29, 24) is True  # Bottom-right corner (exclusive)
    
    # Test points outside bounds
    assert layer.is_point_inside(9, 10) is False   # Left of bounds
    assert layer.is_point_inside(10, 9) is False   # Above bounds
    assert layer.is_point_inside(30, 15) is False  # Right of bounds
    assert layer.is_point_inside(15, 25) is False  # Below bounds
