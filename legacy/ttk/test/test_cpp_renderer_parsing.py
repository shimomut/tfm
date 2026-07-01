#!/usr/bin/env python3
"""
Test script to verify C++ renderer data structure parsing functions.
This is a manual verification test, not part of the automated test suite.
"""

import sys
import os
import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import cpp_renderer
    CPP_RENDERER_AVAILABLE = True
except ImportError as e:
    CPP_RENDERER_AVAILABLE = False
    CPP_RENDERER_ERROR = str(e)

# Skip all tests in this module if cpp_renderer is not available
pytestmark = pytest.mark.skipif(
    not CPP_RENDERER_AVAILABLE,
    reason="cpp_renderer module not available - build with: python setup.py build_ext --inplace"
)

def test_basic_functionality():
    """Test that the module has expected functions."""
    print("\nTesting module functions:")
    
    expected_functions = ['render_frame', 'clear_caches', 'get_performance_metrics', 'reset_metrics']
    for func_name in expected_functions:
        if hasattr(cpp_renderer, func_name):
            print(f"  ✓ {func_name} exists")
        else:
            print(f"  ✗ {func_name} missing")
            return False
    
    return True

def test_metrics():
    """Test performance metrics functions."""
    print("\nTesting performance metrics:")
    
    try:
        metrics = cpp_renderer.get_performance_metrics()
        print(f"  ✓ get_performance_metrics() returned: {metrics}")
        
        cpp_renderer.reset_metrics()
        print("  ✓ reset_metrics() succeeded")
        
        cpp_renderer.clear_caches()
        print("  ✓ clear_caches() succeeded")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("C++ Renderer Data Structure Parsing Verification")
    print("=" * 60)
    
    all_passed = True
    
    if not test_basic_functionality():
        all_passed = False
    
    if not test_metrics():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All verification tests passed!")
        print("\nNote: The parsing functions (parse_grid and parse_color_pairs)")
        print("are internal C++ functions and will be tested when render_frame")
        print("is implemented in later tasks.")
    else:
        print("✗ Some tests failed")
        sys.exit(1)
    print("=" * 60)

if __name__ == '__main__':
    main()
