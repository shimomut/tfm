#!/usr/bin/env python3
"""
Demo: TextViewer Window Resize Handling

This demo verifies that TextViewer properly handles window resize events.
The fix ensures that:

1. TextViewer implements handle_system_event() method
2. Resize events mark the viewer as dirty for redraw
3. Close events properly close the viewer

Test procedure:
1. Run the demo
2. Simulate resize events
3. Verify the viewer marks itself dirty
4. Verify close events work
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import SystemEvent, SystemEventType
from src.tfm_text_viewer import TextViewer
from src.tfm_path import Path


class MockRenderer:
    """Mock renderer for testing"""
    def get_dimensions(self):
        return (24, 80)
    
    def set_cursor_visibility(self, visible):
        pass


def test_text_viewer_resize():
    """Test that TextViewer handles resize events"""
    
    # Create a test file
    test_file = Path("temp/test_resize.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Line 1: Test content\nLine 2: More content\nLine 3: Even more\n")
    
    # Create mock renderer and viewer
    renderer = MockRenderer()
    viewer = TextViewer(renderer, test_file)
    
    print("Testing TextViewer window resize handling...")
    print()
    
    # Test 1: Initial state
    print("Test 1: Initial state")
    assert viewer._dirty == True, "Viewer should start dirty"
    print("✓ Viewer starts in dirty state")
    print()
    
    # Clear dirty flag to test resize
    viewer.clear_dirty()
    assert viewer._dirty == False, "Dirty flag should be cleared"
    print("Test 2: Cleared dirty flag")
    print("✓ Dirty flag cleared")
    print()
    
    # Test 3: Handle resize event
    print("Test 3: Handling resize event")
    resize_event = SystemEvent(event_type=SystemEventType.RESIZE)
    result = viewer.handle_system_event(resize_event)
    print(f"  handle_system_event returned: {result}")
    assert result == True, "Should handle resize event"
    assert viewer._dirty == True, "Viewer should be marked dirty after resize"
    print("✓ Resize event handled and viewer marked dirty")
    print()
    
    # Test 4: Verify viewer is not closed after resize
    print("Test 4: Viewer should not close after resize")
    assert viewer._should_close == False, "Viewer should not close after resize"
    print("✓ Viewer remains open after resize")
    print()
    
    # Test 5: Handle close event
    print("Test 5: Handling close event")
    close_event = SystemEvent(event_type=SystemEventType.CLOSE)
    result = viewer.handle_system_event(close_event)
    print(f"  handle_system_event returned: {result}")
    assert result == True, "Should handle close event"
    assert viewer._should_close == True, "Viewer should be marked for closing"
    assert viewer._dirty == True, "Viewer should be marked dirty"
    print("✓ Close event handled and viewer marked for closing")
    print()
    
    # Test 6: Verify should_close() returns True
    print("Test 6: Checking should_close()")
    assert viewer.should_close() == True, "should_close() should return True"
    print("✓ should_close() returns True")
    print()
    
    # Test 7: Test with a fresh viewer - multiple resizes
    print("Test 7: Multiple resize events")
    viewer2 = TextViewer(renderer, test_file)
    viewer2.clear_dirty()
    
    for i in range(3):
        resize_event = SystemEvent(event_type=SystemEventType.RESIZE)
        result = viewer2.handle_system_event(resize_event)
        assert result == True, f"Should handle resize event {i+1}"
        assert viewer2._dirty == True, f"Should be dirty after resize {i+1}"
        print(f"  Resize {i+1}: ✓")
    
    print("✓ Multiple resize events handled correctly")
    print()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print()
    print("The fix ensures that:")
    print("1. TextViewer implements handle_system_event() method")
    print("2. Resize events mark the viewer as dirty for redraw")
    print("3. Close events properly close the viewer")
    print("4. Multiple resize events are handled correctly")
    
    # Cleanup
    test_file.unlink()


if __name__ == "__main__":
    test_text_viewer_resize()
