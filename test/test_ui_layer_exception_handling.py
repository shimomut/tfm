"""
Tests for exception handling in UILayerStack.

These tests verify that the layer stack handles exceptions gracefully
during event processing and rendering, continuing operation despite errors.
"""

import pytest
from src.tfm_ui_layer import UILayer, UILayerStack


class ExceptionThrowingLayer(UILayer):
    """Layer that throws exceptions for testing."""
    
    def __init__(self, name, throw_on_key=False, throw_on_char=False, throw_on_render=False):
        self.name = name
        self.throw_on_key = throw_on_key
        self.throw_on_char = throw_on_char
        self.throw_on_render = throw_on_render
        self.dirty = True
    
    def handle_key_event(self, event) -> bool:
        if self.throw_on_key:
            raise RuntimeError(f"Key event error in {self.name}")
        return False
    
    def handle_char_event(self, event) -> bool:
        if self.throw_on_char:
            raise RuntimeError(f"Char event error in {self.name}")
        return False
    
    def render(self, renderer) -> None:
        if self.throw_on_render:
            raise RuntimeError(f"Render error in {self.name}")
    
    def is_full_screen(self) -> bool:
        return False
    
    def needs_redraw(self) -> bool:
        return self.dirty
    
    def mark_dirty(self) -> None:
        self.dirty = True
    
    def clear_dirty(self) -> None:
        self.dirty = False
    
    def should_close(self) -> bool:
        return False
    
    def on_activate(self) -> None:
        pass
    
    def on_deactivate(self) -> None:
        pass


class MockLogManager:
    """Mock log manager for testing."""
    
    def __init__(self):
        self.messages = []
    
    def add_message(self, level, message):
        self.messages.append((level, message))


class MockRenderer:
    """Mock renderer for testing."""
    
    def refresh(self):
        pass


def test_exception_during_key_event_handling():
    """Test that exceptions during key event handling are caught and logged."""
    log_manager = MockLogManager()
    bottom = ExceptionThrowingLayer("bottom", throw_on_key=True)
    stack = UILayerStack(bottom, log_manager)
    
    # Should not raise exception
    result = stack.handle_key_event({'type': 'key'})
    
    # Event was not consumed (exception was caught)
    assert result is False
    
    # Error was logged
    assert len(log_manager.messages) == 1
    assert log_manager.messages[0][0] == "ERROR"
    assert "ExceptionThrowingLayer" in log_manager.messages[0][1]
    assert "key event" in log_manager.messages[0][1]


def test_exception_during_char_event_handling():
    """Test that exceptions during char event handling are caught and logged."""
    log_manager = MockLogManager()
    bottom = ExceptionThrowingLayer("bottom", throw_on_char=True)
    stack = UILayerStack(bottom, log_manager)
    
    # Should not raise exception
    result = stack.handle_char_event({'type': 'char'})
    
    # Event was not consumed (exception was caught)
    assert result is False
    
    # Error was logged
    assert len(log_manager.messages) == 1
    assert log_manager.messages[0][0] == "ERROR"
    assert "ExceptionThrowingLayer" in log_manager.messages[0][1]
    assert "char event" in log_manager.messages[0][1]


def test_exception_during_rendering():
    """Test that exceptions during rendering are caught and logged."""
    log_manager = MockLogManager()
    bottom = ExceptionThrowingLayer("bottom", throw_on_render=True)
    stack = UILayerStack(bottom, log_manager)
    
    renderer = MockRenderer()
    
    # Should not raise exception
    stack.render(renderer)
    
    # Error was logged
    assert len(log_manager.messages) == 1
    assert log_manager.messages[0][0] == "ERROR"
    assert "ExceptionThrowingLayer" in log_manager.messages[0][1]
    assert "rendering" in log_manager.messages[0][1]


def test_event_propagation_continues_after_exception():
    """Test that exception in top layer is caught and logged (no propagation)."""
    log_manager = MockLogManager()
    
    # Bottom layer that doesn't throw
    class GoodLayer(ExceptionThrowingLayer):
        def __init__(self):
            super().__init__("good", throw_on_key=False)
            self.key_received = False
        
        def handle_key_event(self, event) -> bool:
            self.key_received = True
            return True
    
    bottom = GoodLayer()
    stack = UILayerStack(bottom, log_manager)
    
    # Top layer that throws
    top = ExceptionThrowingLayer("top", throw_on_key=True)
    stack.push(top)
    
    # Only top layer receives event (no propagation even on exception)
    result = stack.handle_key_event({'type': 'key'})
    
    assert result is False  # Event not consumed (exception caught)
    assert bottom.key_received is False  # Bottom layer never received event
    assert len(log_manager.messages) == 1  # Exception was logged


def test_rendering_continues_after_exception():
    """Test that rendering continues with other layers after exception."""
    log_manager = MockLogManager()
    
    # Bottom layer that doesn't throw
    class GoodLayer(ExceptionThrowingLayer):
        def __init__(self):
            super().__init__("good", throw_on_render=False)
            self.render_called = False
        
        def render(self, renderer) -> None:
            self.render_called = True
    
    bottom = GoodLayer()
    stack = UILayerStack(bottom, log_manager)
    
    # Top layer that throws
    top = ExceptionThrowingLayer("top", throw_on_render=True)
    stack.push(top)
    
    renderer = MockRenderer()
    stack.render(renderer)
    
    # Both layers should have been attempted
    assert bottom.render_called is True
    assert len(log_manager.messages) == 1  # Exception was logged


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
