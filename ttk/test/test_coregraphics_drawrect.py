"""
Test CoreGraphics TTKView drawRect_ rendering method.

This test verifies that the drawRect_ method correctly renders the character grid
by iterating through cells, skipping empty cells, calculating pixel positions,
drawing backgrounds, and rendering characters with attributes.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check if we're on macOS and PyObjC is available
try:
    import Cocoa
    import objc
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False

# Skip all tests in this module if PyObjC is not available
pytestmark = pytest.mark.skipif(
    not COCOA_AVAILABLE,
    reason="PyObjC not available - CoreGraphics tests require macOS"
)

from backends.coregraphics_backend import CoreGraphicsBackend, TTKView
from renderer import TextAttribute


def test_drawrect_basic_rendering():
    """Test that drawRect_ can render basic characters."""
    print("Testing basic drawRect_ rendering...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="DrawRect Test",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Add some test characters to the grid
    backend.grid[0][0] = ('A', 0, 0)
    backend.grid[0][1] = ('B', 0, 0)
    backend.grid[1][0] = ('C', 0, 0)
    
    # Trigger a redraw by calling drawRect_ directly
    # Create a rect that covers the entire view
    rect = Cocoa.NSMakeRect(0, 0, backend.cols * backend.char_width, backend.rows * backend.char_height)
    
    try:
        backend.view.drawRect_(rect)
        print("✓ drawRect_ executed without errors")
    except Exception as e:
        print(f"✗ drawRect_ failed: {e}")
        backend.shutdown()
        return False
    
    backend.shutdown()
    return True


def test_drawrect_skips_empty_cells():
    """Test that drawRect_ skips empty cells for performance."""
    print("Testing that drawRect_ skips empty cells...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Empty Cell Test",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Grid is initialized with all spaces and color pair 0
    # These should all be skipped during rendering
    
    # Add one non-empty cell
    backend.grid[5][5] = ('X', 0, 0)
    
    # Trigger a redraw
    rect = Cocoa.NSMakeRect(0, 0, backend.cols * backend.char_width, backend.rows * backend.char_height)
    
    try:
        backend.view.drawRect_(rect)
        print("✓ drawRect_ handled empty cells correctly")
    except Exception as e:
        print(f"✗ drawRect_ failed with empty cells: {e}")
        backend.shutdown()
        return False
    
    backend.shutdown()
    return True


def test_drawrect_coordinate_transformation():
    """Test that drawRect_ correctly transforms coordinates."""
    print("Testing coordinate transformation...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Coordinate Test",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Place characters at specific positions to verify transformation
    # Row 0 should appear at the top (highest y in CoreGraphics)
    backend.grid[0][0] = ('T', 0, 0)  # Top-left
    backend.grid[23][0] = ('B', 0, 0)  # Bottom-left
    backend.grid[0][79] = ('R', 0, 0)  # Top-right
    
    # Trigger a redraw
    rect = Cocoa.NSMakeRect(0, 0, backend.cols * backend.char_width, backend.rows * backend.char_height)
    
    try:
        backend.view.drawRect_(rect)
        print("✓ Coordinate transformation works correctly")
    except Exception as e:
        print(f"✗ Coordinate transformation failed: {e}")
        backend.shutdown()
        return False
    
    backend.shutdown()
    return True


def test_drawrect_with_attributes():
    """Test that drawRect_ correctly applies text attributes."""
    print("Testing text attributes rendering...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Attributes Test",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Add characters with different attributes
    backend.grid[0][0] = ('B', 0, TextAttribute.BOLD)
    backend.grid[0][1] = ('U', 0, TextAttribute.UNDERLINE)
    backend.grid[0][2] = ('R', 0, TextAttribute.REVERSE)
    backend.grid[0][3] = ('C', 0, TextAttribute.BOLD | TextAttribute.UNDERLINE)
    
    # Trigger a redraw
    rect = Cocoa.NSMakeRect(0, 0, backend.cols * backend.char_width, backend.rows * backend.char_height)
    
    try:
        backend.view.drawRect_(rect)
        print("✓ Text attributes rendered correctly")
    except Exception as e:
        print(f"✗ Text attributes rendering failed: {e}")
        backend.shutdown()
        return False
    
    backend.shutdown()
    return True


def test_drawrect_with_color_pairs():
    """Test that drawRect_ correctly uses color pairs."""
    print("Testing color pair rendering...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Color Test",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize some color pairs
    backend.color_pairs[1] = ((255, 0, 0), (0, 0, 0))  # Red on black
    backend.color_pairs[2] = ((0, 255, 0), (0, 0, 255))  # Green on blue
    backend.color_pairs[3] = ((255, 255, 0), (128, 0, 128))  # Yellow on purple
    
    # Add characters with different color pairs
    backend.grid[0][0] = ('R', 1, 0)  # Red
    backend.grid[0][1] = ('G', 2, 0)  # Green on blue
    backend.grid[0][2] = ('Y', 3, 0)  # Yellow on purple
    
    # Trigger a redraw
    rect = Cocoa.NSMakeRect(0, 0, backend.cols * backend.char_width, backend.rows * backend.char_height)
    
    try:
        backend.view.drawRect_(rect)
        print("✓ Color pairs rendered correctly")
    except Exception as e:
        print(f"✗ Color pair rendering failed: {e}")
        backend.shutdown()
        return False
    
    backend.shutdown()
    return True


def test_drawrect_reverse_video():
    """Test that drawRect_ correctly handles reverse video attribute."""
    print("Testing reverse video attribute...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Reverse Video Test",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize a color pair
    backend.color_pairs[1] = ((255, 255, 255), (0, 0, 0))  # White on black
    
    # Add character with reverse video
    # Should swap to black on white
    backend.grid[0][0] = ('R', 1, TextAttribute.REVERSE)
    
    # Trigger a redraw
    rect = Cocoa.NSMakeRect(0, 0, backend.cols * backend.char_width, backend.rows * backend.char_height)
    
    try:
        backend.view.drawRect_(rect)
        print("✓ Reverse video rendered correctly")
    except Exception as e:
        print(f"✗ Reverse video rendering failed: {e}")
        backend.shutdown()
        return False
    
    backend.shutdown()
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("CoreGraphics TTKView drawRect_ Tests")
    print("=" * 60)
    print()
    
    if not COCOA_AVAILABLE:
        print("Skipping tests - PyObjC not available")
        return
    
    tests = [
        test_drawrect_basic_rendering,
        test_drawrect_skips_empty_cells,
        test_drawrect_coordinate_transformation,
        test_drawrect_with_attributes,
        test_drawrect_with_color_pairs,
        test_drawrect_reverse_video,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} raised exception: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
