#!/usr/bin/env python3
"""
Verification script for CoreGraphics backend window dimension queries.

This script verifies that the get_dimensions() implementation meets all
requirements specified in the design document.

Requirements verified:
- 7.3: Window dimensions are returned as (rows, cols)
- Dimensions are always positive integers
- Dimensions match the initialized grid size
- Dimensions remain consistent across multiple calls
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
except ImportError as e:
    print(f"Error importing CoreGraphics backend: {e}")
    sys.exit(1)


def verify_requirement_7_3():
    """
    Verify Requirement 7.3: Window dimensions are returned as (rows, cols).
    
    WHEN window dimensions are queried THEN the system SHALL return the
    current grid size in rows and columns.
    """
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return True
    
    print("Verifying Requirement 7.3: Window dimension queries...")
    
    # Test with default dimensions
    backend = CoreGraphicsBackend(window_title="Verify 7.3")
    
    try:
        backend.initialize()
        
        # Get dimensions
        result = backend.get_dimensions()
        
        # Verify return type is tuple
        assert isinstance(result, tuple), \
            f"get_dimensions() should return tuple, got {type(result)}"
        
        # Verify tuple has exactly 2 elements
        assert len(result) == 2, \
            f"get_dimensions() should return 2 elements, got {len(result)}"
        
        rows, cols = result
        
        # Verify both are integers
        assert isinstance(rows, int), \
            f"Rows should be int, got {type(rows)}"
        assert isinstance(cols, int), \
            f"Cols should be int, got {type(cols)}"
        
        # Verify both are positive
        assert rows > 0, f"Rows should be positive, got {rows}"
        assert cols > 0, f"Cols should be positive, got {cols}"
        
        # Verify dimensions match initialized values
        assert rows == backend.rows, \
            f"Returned rows ({rows}) should match backend.rows ({backend.rows})"
        assert cols == backend.cols, \
            f"Returned cols ({cols}) should match backend.cols ({backend.cols})"
        
        print(f"  ✓ Returns (rows, cols) tuple: ({rows}, {cols})")
        print(f"  ✓ Both values are positive integers")
        print(f"  ✓ Values match initialized grid size")
        
        return True
        
    finally:
        if backend.window:
            backend.window.close()


def verify_dimension_consistency():
    """
    Verify that get_dimensions() returns consistent values.
    
    The dimensions should remain constant throughout the backend's lifetime
    (until resize is implemented).
    """
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return True
    
    print("Verifying dimension consistency...")
    
    backend = CoreGraphicsBackend(window_title="Verify Consistency", rows=30, cols=100)
    
    try:
        backend.initialize()
        
        # Call get_dimensions() multiple times
        dims = [backend.get_dimensions() for _ in range(10)]
        
        # Verify all calls return the same value
        first_dims = dims[0]
        for i, current_dims in enumerate(dims[1:], 1):
            assert current_dims == first_dims, \
                f"Call {i+1} returned {current_dims}, expected {first_dims}"
        
        print(f"  ✓ Consistent across 10 calls: {first_dims}")
        
        return True
        
    finally:
        if backend.window:
            backend.window.close()


def verify_various_sizes():
    """
    Verify get_dimensions() works correctly with various grid sizes.
    
    Tests edge cases like very small (1x1) and large (200x200) grids.
    """
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return True
    
    print("Verifying various grid sizes...")
    
    test_cases = [
        (1, 1, "minimum size"),
        (10, 20, "small size"),
        (24, 80, "default size"),
        (50, 120, "medium size"),
        (100, 200, "large size")
    ]
    
    for rows, cols, description in test_cases:
        backend = CoreGraphicsBackend(
            window_title=f"Verify {rows}x{cols}",
            rows=rows,
            cols=cols
        )
        
        try:
            backend.initialize()
            
            # Get dimensions
            result_rows, result_cols = backend.get_dimensions()
            
            # Verify dimensions match
            assert result_rows == rows, \
                f"Expected {rows} rows, got {result_rows}"
            assert result_cols == cols, \
                f"Expected {cols} cols, got {result_cols}"
            
            # Verify positive integers
            assert result_rows > 0 and result_cols > 0, \
                f"Dimensions should be positive: ({result_rows}, {result_cols})"
            
            print(f"  ✓ {description}: {result_rows}x{result_cols}")
            
        finally:
            if backend.window:
                backend.window.close()
    
    return True


def verify_implementation_details():
    """
    Verify implementation details of get_dimensions().
    
    Checks that the method:
    - Returns the backend's rows and cols attributes
    - Does not modify any state
    - Works before and after drawing operations
    """
    if not COCOA_AVAILABLE:
        print("SKIP: PyObjC not available")
        return True
    
    print("Verifying implementation details...")
    
    backend = CoreGraphicsBackend(window_title="Verify Implementation", rows=25, cols=85)
    
    try:
        backend.initialize()
        
        # Get dimensions before any operations
        dims_before = backend.get_dimensions()
        
        # Perform some drawing operations
        backend.draw_text(0, 0, "Test", 0, 0)
        backend.draw_rect(5, 5, 10, 20, 0, False)
        backend.refresh()
        
        # Get dimensions after operations
        dims_after = backend.get_dimensions()
        
        # Verify dimensions haven't changed
        assert dims_before == dims_after, \
            f"Dimensions changed after operations: {dims_before} -> {dims_after}"
        
        # Verify dimensions match backend attributes
        rows, cols = dims_after
        assert rows == backend.rows, \
            f"Returned rows ({rows}) != backend.rows ({backend.rows})"
        assert cols == backend.cols, \
            f"Returned cols ({cols}) != backend.cols ({backend.cols})"
        
        print(f"  ✓ Returns backend.rows and backend.cols")
        print(f"  ✓ Does not modify state")
        print(f"  ✓ Consistent before and after operations")
        
        return True
        
    finally:
        if backend.window:
            backend.window.close()


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("CoreGraphics Backend - Window Dimension Query Verification")
    print("=" * 70)
    print()
    
    if not COCOA_AVAILABLE:
        print("ERROR: PyObjC is not available")
        print("Install with: pip install pyobjc-framework-Cocoa")
        return 1
    
    all_passed = True
    
    # Run verification checks
    checks = [
        ("Requirement 7.3", verify_requirement_7_3),
        ("Dimension Consistency", verify_dimension_consistency),
        ("Various Grid Sizes", verify_various_sizes),
        ("Implementation Details", verify_implementation_details)
    ]
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                print(f"✗ {check_name} verification failed")
                all_passed = False
        except AssertionError as e:
            print(f"✗ {check_name} verification failed: {e}")
            all_passed = False
        except Exception as e:
            print(f"✗ {check_name} verification error: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
        print()
    
    print("=" * 70)
    if all_passed:
        print("✓ All verifications passed!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - get_dimensions() returns (rows, cols) tuple")
        print("  - Both values are positive integers")
        print("  - Values match initialized grid size")
        print("  - Dimensions remain consistent across calls")
        print("  - Works correctly with various grid sizes")
        print("  - Implementation follows design specification")
        return 0
    else:
        print("✗ Some verifications failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
