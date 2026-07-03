#!/usr/bin/env python3
"""
Demo: System Event Broadcasting to All Layers

This demo verifies that system events (resize, close) are broadcast to ALL
layers in the UI stack, not just the top layer. This is important because
all layers need to know about window resize events to update their layout.

Test procedure:
1. Create a layer stack with multiple layers
2. Send a resize event
3. Verify all layers receive the event
4. Verify all layers mark themselves as needing redraw
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import SystemEvent, SystemEventType
from src.tfm_ui_layer import UILayer, UILayerStack


class TestLayer(UILayer):
    """Test layer that tracks system events"""
    
    def __init__(self, name):
        self.name = name
        self.resize_count = 0
        self.close_count = 0
        self._dirty = False
        self._should_close = False
    
    def handle_key_event(self, event) -> bool:
        return False
    
    def handle_char_event(self, event) -> bool:
        return False
    
    def handle_system_event(self, event) -> bool:
        if event.is_resize():
            self.resize_count += 1
            self._dirty = True
            print(f"  {self.name}: Received resize event (count: {self.resize_count})")
            return True
        elif event.is_close():
            self.close_count += 1
            print(f"  {self.name}: Received close event (count: {self.close_count})")
            return True
        return False
    
    def render(self, renderer) -> None:
        pass
    
    def is_full_screen(self) -> bool:
        return self.name == "Bottom"  # Only bottom layer is full-screen
    
    def needs_redraw(self) -> bool:
        return self._dirty
    
    def mark_dirty(self) -> None:
        self._dirty = True
    
    def clear_dirty(self) -> None:
        self._dirty = False
    
    def should_close(self) -> bool:
        return self._should_close
    
    def on_activate(self) -> None:
        print(f"  {self.name}: Activated")
    
    def on_deactivate(self) -> None:
        print(f"  {self.name}: Deactivated")


def test_system_event_broadcast():
    """Test that system events are broadcast to all layers"""
    
    print("Testing system event broadcasting to all layers...")
    print()
    
    # Test 1: Create a layer stack with multiple layers
    print("Test 1: Creating layer stack with 3 layers")
    bottom_layer = TestLayer("Bottom")
    middle_layer = TestLayer("Middle")
    top_layer = TestLayer("Top")
    
    stack = UILayerStack(bottom_layer)
    stack.push(middle_layer)
    stack.push(top_layer)
    
    assert stack.get_layer_count() == 3, "Should have 3 layers"
    print("✓ Created stack with 3 layers")
    print()
    
    # Test 2: Send a resize event
    print("Test 2: Broadcasting resize event to all layers")
    resize_event = SystemEvent(event_type=SystemEventType.RESIZE)
    result = stack.handle_system_event(resize_event)
    
    assert result == True, "At least one layer should handle the event"
    assert bottom_layer.resize_count == 1, "Bottom layer should receive resize"
    assert middle_layer.resize_count == 1, "Middle layer should receive resize"
    assert top_layer.resize_count == 1, "Top layer should receive resize"
    print("✓ All layers received resize event")
    print()
    
    # Test 3: Verify all layers are marked dirty
    print("Test 3: Verifying all layers marked dirty after resize")
    assert bottom_layer.needs_redraw() == True, "Bottom layer should be dirty"
    assert middle_layer.needs_redraw() == True, "Middle layer should be dirty"
    assert top_layer.needs_redraw() == True, "Top layer should be dirty"
    print("✓ All layers marked dirty")
    print()
    
    # Test 4: Send multiple resize events
    print("Test 4: Broadcasting multiple resize events")
    for i in range(3):
        resize_event = SystemEvent(event_type=SystemEventType.RESIZE)
        stack.handle_system_event(resize_event)
    
    assert bottom_layer.resize_count == 4, f"Bottom layer should have 4 resizes, got {bottom_layer.resize_count}"
    assert middle_layer.resize_count == 4, f"Middle layer should have 4 resizes, got {middle_layer.resize_count}"
    assert top_layer.resize_count == 4, f"Top layer should have 4 resizes, got {top_layer.resize_count}"
    print("✓ All layers received all resize events")
    print()
    
    # Test 5: Send a close event
    print("Test 5: Broadcasting close event to all layers")
    close_event = SystemEvent(event_type=SystemEventType.CLOSE)
    result = stack.handle_system_event(close_event)
    
    assert result == True, "At least one layer should handle the event"
    assert bottom_layer.close_count == 1, "Bottom layer should receive close"
    assert middle_layer.close_count == 1, "Middle layer should receive close"
    assert top_layer.close_count == 1, "Top layer should receive close"
    print("✓ All layers received close event")
    print()
    
    # Test 6: Pop a layer and verify remaining layers still get events
    print("Test 6: Popping top layer and broadcasting resize")
    stack.pop()
    assert stack.get_layer_count() == 2, "Should have 2 layers after pop"
    
    resize_event = SystemEvent(event_type=SystemEventType.RESIZE)
    stack.handle_system_event(resize_event)
    
    assert bottom_layer.resize_count == 5, "Bottom layer should have 5 resizes"
    assert middle_layer.resize_count == 5, "Middle layer should have 5 resizes"
    assert top_layer.resize_count == 4, "Top layer should still have 4 resizes (not in stack)"
    print("✓ Only layers in stack received event after pop")
    print()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print()
    print("The fix ensures that:")
    print("1. System events are broadcast to ALL layers in the stack")
    print("2. All layers can respond to resize events")
    print("3. All layers can respond to close events")
    print("4. Broadcasting continues even if a layer is removed")
    print()
    print("Event counts:")
    print(f"  Bottom layer: {bottom_layer.resize_count} resizes, {bottom_layer.close_count} closes")
    print(f"  Middle layer: {middle_layer.resize_count} resizes, {middle_layer.close_count} closes")
    print(f"  Top layer: {top_layer.resize_count} resizes, {top_layer.close_count} closes")


if __name__ == "__main__":
    test_system_event_broadcast()
