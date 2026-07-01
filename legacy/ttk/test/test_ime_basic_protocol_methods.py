"""
Test basic NSTextInputClient protocol methods implementation.

This test verifies that the hasMarkedText, markedRange, selectedRange, and
validAttributesForMarkedText methods correctly use the IME state tracking
variables that were initialized in task 1.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False

# Skip all tests in this module if PyObjC is not available
pytestmark = pytest.mark.skipif(
    not COCOA_AVAILABLE,
    reason="PyObjC not available - IME tests require macOS"
)

from ttk.backends.coregraphics_backend import TTKView, CoreGraphicsBackend


def test_hasMarkedText_returns_false_initially():
    """Test that hasMarkedText returns False when no composition is active."""
    # Create a minimal backend
    backend = CoreGraphicsBackend(
        window_title="Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    # Create a TTKView
    frame = Cocoa.NSMakeRect(0, 0, 800, 480)
    view = TTKView.alloc().initWithFrame_backend_(frame, backend)
    
    # Initially, there should be no marked text
    assert view.hasMarkedText() == False, "hasMarkedText should return False initially"
    print("✓ hasMarkedText returns False initially")


def test_hasMarkedText_returns_true_when_marked_range_set():
    """Test that hasMarkedText returns True when marked_range is set."""
    # Create a minimal backend
    backend = CoreGraphicsBackend(
        window_title="Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    # Create a TTKView
    frame = Cocoa.NSMakeRect(0, 0, 800, 480)
    view = TTKView.alloc().initWithFrame_backend_(frame, backend)
    
    # Set marked_range to indicate active composition
    view.marked_range = Cocoa.NSMakeRange(0, 5)
    
    # Now hasMarkedText should return True
    assert view.hasMarkedText() == True, "hasMarkedText should return True when marked_range is set"
    print("✓ hasMarkedText returns True when marked_range is set")


def test_markedRange_returns_current_range():
    """Test that markedRange returns the current marked_range."""
    # Create a minimal backend
    backend = CoreGraphicsBackend(
        window_title="Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    # Create a TTKView
    frame = Cocoa.NSMakeRect(0, 0, 800, 480)
    view = TTKView.alloc().initWithFrame_backend_(frame, backend)
    
    # Initially, marked_range should be NSNotFound
    initial_range = view.markedRange()
    assert initial_range.location == Cocoa.NSNotFound, "Initial marked_range location should be NSNotFound"
    assert initial_range.length == 0, "Initial marked_range length should be 0"
    print("✓ markedRange returns NSNotFound initially")
    
    # Set marked_range to a specific value
    view.marked_range = Cocoa.NSMakeRange(0, 5)
    
    # markedRange should return the updated value
    updated_range = view.markedRange()
    assert updated_range.location == 0, "Updated marked_range location should be 0"
    assert updated_range.length == 5, "Updated marked_range length should be 5"
    print("✓ markedRange returns updated range")


def test_selectedRange_returns_current_range():
    """Test that selectedRange returns the current selected_range."""
    # Create a minimal backend
    backend = CoreGraphicsBackend(
        window_title="Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    # Create a TTKView
    frame = Cocoa.NSMakeRect(0, 0, 800, 480)
    view = TTKView.alloc().initWithFrame_backend_(frame, backend)
    
    # Initially, selected_range should be zero-length at position 0
    initial_range = view.selectedRange()
    assert initial_range.location == 0, "Initial selected_range location should be 0"
    assert initial_range.length == 0, "Initial selected_range length should be 0"
    print("✓ selectedRange returns zero-length range initially")
    
    # Set selected_range to a specific value
    view.selected_range = Cocoa.NSMakeRange(2, 3)
    
    # selectedRange should return the updated value
    updated_range = view.selectedRange()
    assert updated_range.location == 2, "Updated selected_range location should be 2"
    assert updated_range.length == 3, "Updated selected_range length should be 3"
    print("✓ selectedRange returns updated range")


def test_validAttributesForMarkedText_returns_empty_array():
    """Test that validAttributesForMarkedText returns an empty array."""
    # Create a minimal backend
    backend = CoreGraphicsBackend(
        window_title="Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    # Create a TTKView
    frame = Cocoa.NSMakeRect(0, 0, 800, 480)
    view = TTKView.alloc().initWithFrame_backend_(frame, backend)
    
    # validAttributesForMarkedText should return an empty array
    attributes = view.validAttributesForMarkedText()
    assert isinstance(attributes, list), "validAttributesForMarkedText should return a list"
    assert len(attributes) == 0, "validAttributesForMarkedText should return an empty list"
    print("✓ validAttributesForMarkedText returns empty array")


if __name__ == "__main__":
    print("Testing basic NSTextInputClient protocol methods...")
    print()
    
    test_hasMarkedText_returns_false_initially()
    test_hasMarkedText_returns_true_when_marked_range_set()
    test_markedRange_returns_current_range()
    test_selectedRange_returns_current_range()
    test_validAttributesForMarkedText_returns_empty_array()
    
    print()
    print("All tests passed! ✓")
