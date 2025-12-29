"""
Test CoreGraphics backend window dimension queries.

This test verifies that the get_dimensions() method correctly returns
the window dimensions in character cells as (rows, cols).

Requirements tested:
- 7.3: Window dimensions are returned as (rows, cols)
- Dimensions are always positive integers
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False
    BACKEND_ERROR = str(e)

# Skip all tests in this module if backend is not available
pytestmark = pytest.mark.skipif(
    not BACKEND_AVAILABLE,
    reason="CoreGraphics backend not available"
)


def test_get_dimensions_default():
    """Test get_dimensions() with default grid size."""
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return
    
    print("Testing get_dimensions() with default grid size...")
    
    # Create backend with default dimensions (24x80)
    backend = CoreGraphicsBackend(window_title="Test Dimensions")
    
    try:
        # Initialize the backend
        backend.initialize()
        
        # Get dimensions
        rows, cols = backend.get_dimensions()
        
        # Verify dimensions match defaults
        assert rows == 24, f"Expected 24 rows, got {rows}"
        assert cols == 80, f"Expected 80 cols, got {cols}"
        
        # Verify dimensions are positive integers
        assert isinstance(rows, int), f"Rows should be int, got {type(rows)}"
        assert isinstance(cols, int), f"Cols should be int, got {type(cols)}"
        assert rows > 0, f"Rows should be positive, got {rows}"
        assert cols > 0, f"Cols should be positive, got {cols}"
        
        print(f"✓ Default dimensions: {rows}x{cols}")
        
    finally:
        # Clean up
        if backend.window:
            backend.window.close()


def test_get_dimensions_custom():
    """Test get_dimensions() with custom grid size."""
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return
    
    print("Testing get_dimensions() with custom grid size...")
    
    # Create backend with custom dimensions
    custom_rows = 30
    custom_cols = 100
    backend = CoreGraphicsBackend(
        window_title="Test Custom Dimensions",
        rows=custom_rows,
        cols=custom_cols
    )
    
    try:
        # Initialize the backend
        backend.initialize()
        
        # Get dimensions
        rows, cols = backend.get_dimensions()
        
        # Verify dimensions match custom values
        assert rows == custom_rows, f"Expected {custom_rows} rows, got {rows}"
        assert cols == custom_cols, f"Expected {custom_cols} cols, got {cols}"
        
        # Verify dimensions are positive integers
        assert isinstance(rows, int), f"Rows should be int, got {type(rows)}"
        assert isinstance(cols, int), f"Cols should be int, got {type(cols)}"
        assert rows > 0, f"Rows should be positive, got {rows}"
        assert cols > 0, f"Cols should be positive, got {cols}"
        
        print(f"✓ Custom dimensions: {rows}x{cols}")
        
    finally:
        # Clean up
        if backend.window:
            backend.window.close()


def test_get_dimensions_various_sizes():
    """Test get_dimensions() with various grid sizes."""
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return
    
    print("Testing get_dimensions() with various grid sizes...")
    
    # Test various sizes
    test_sizes = [
        (10, 20),
        (50, 120),
        (1, 1),
        (100, 200)
    ]
    
    for test_rows, test_cols in test_sizes:
        backend = CoreGraphicsBackend(
            window_title=f"Test {test_rows}x{test_cols}",
            rows=test_rows,
            cols=test_cols
        )
        
        try:
            # Initialize the backend
            backend.initialize()
            
            # Get dimensions
            rows, cols = backend.get_dimensions()
            
            # Verify dimensions match
            assert rows == test_rows, f"Expected {test_rows} rows, got {rows}"
            assert cols == test_cols, f"Expected {test_cols} cols, got {cols}"
            
            # Verify dimensions are positive integers
            assert isinstance(rows, int), f"Rows should be int, got {type(rows)}"
            assert isinstance(cols, int), f"Cols should be int, got {type(cols)}"
            assert rows > 0, f"Rows should be positive, got {rows}"
            assert cols > 0, f"Cols should be positive, got {cols}"
            
            print(f"✓ Dimensions {test_rows}x{test_cols}: verified")
            
        finally:
            # Clean up
            if backend.window:
                backend.window.close()


def test_get_dimensions_consistency():
    """Test that get_dimensions() returns consistent values."""
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return
    
    print("Testing get_dimensions() consistency...")
    
    backend = CoreGraphicsBackend(window_title="Test Consistency", rows=25, cols=90)
    
    try:
        # Initialize the backend
        backend.initialize()
        
        # Call get_dimensions() multiple times
        dims1 = backend.get_dimensions()
        dims2 = backend.get_dimensions()
        dims3 = backend.get_dimensions()
        
        # Verify all calls return the same values
        assert dims1 == dims2, f"Inconsistent dimensions: {dims1} != {dims2}"
        assert dims2 == dims3, f"Inconsistent dimensions: {dims2} != {dims3}"
        
        # Verify the values are correct
        rows, cols = dims1
        assert rows == 25, f"Expected 25 rows, got {rows}"
        assert cols == 90, f"Expected 90 cols, got {cols}"
        
        print(f"✓ Consistent dimensions across multiple calls: {rows}x{cols}")
        
    finally:
        # Clean up
        if backend.window:
            backend.window.close()


def main():
    """Run all dimension query tests."""
    print("=" * 60)
    print("CoreGraphics Backend - Window Dimension Query Tests")
    print("=" * 60)
    print()
    
    if not COCOA_AVAILABLE:
        print("ERROR: PyObjC is not available")
        print("Install with: pip install pyobjc-framework-Cocoa")
        return 1
    
    try:
        # Run tests
        test_get_dimensions_default()
        print()
        
        test_get_dimensions_custom()
        print()
        
        test_get_dimensions_various_sizes()
        print()
        
        test_get_dimensions_consistency()
        print()
        
        print("=" * 60)
        print("All dimension query tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
