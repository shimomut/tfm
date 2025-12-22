#!/usr/bin/env python3
"""
Test for render_frame() function implementation.
Tests parameter validation, basic rendering, and error handling.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_module_import():
    """Test that cpp_renderer module can be imported."""
    try:
        import cpp_renderer
        print("✓ Module import successful")
        print(f"  Version: {cpp_renderer.__version__}")
        return True
    except ImportError as e:
        print(f"✗ Module import failed: {e}")
        return False

def test_parameter_validation():
    """Test parameter validation in render_frame()."""
    import cpp_renderer
    
    print("\nTesting parameter validation:")
    
    # Test 1: Null context
    try:
        cpp_renderer.render_frame(
            context=0,  # Null context
            grid=[],
            color_pairs={},
            dirty_rect=(0, 0, 100, 100),
            char_width=10.0,
            char_height=20.0,
            rows=10,
            cols=10,
            offset_x=0.0,
            offset_y=0.0,
            cursor_visible=False,
            cursor_row=0,
            cursor_col=0
        )
        print("✗ Should have raised ValueError for null context")
        return False
    except ValueError as e:
        if "null" in str(e).lower():
            print(f"✓ Null context validation: {e}")
        else:
            print(f"✗ Wrong error for null context: {e}")
            return False
    
    # Test 2: Invalid grid dimensions
    try:
        cpp_renderer.render_frame(
            context=1,  # Dummy non-null value
            grid=[],
            color_pairs={},
            dirty_rect=(0, 0, 100, 100),
            char_width=10.0,
            char_height=20.0,
            rows=0,  # Invalid
            cols=10,
            offset_x=0.0,
            offset_y=0.0,
            cursor_visible=False,
            cursor_row=0,
            cursor_col=0
        )
        print("✗ Should have raised ValueError for invalid dimensions")
        return False
    except ValueError as e:
        if "positive" in str(e).lower():
            print(f"✓ Invalid dimensions validation: {e}")
        else:
            print(f"✗ Wrong error for invalid dimensions: {e}")
            return False
    
    # Test 3: Grid not a list
    try:
        cpp_renderer.render_frame(
            context=1,
            grid="not a list",  # Invalid type
            color_pairs={},
            dirty_rect=(0, 0, 100, 100),
            char_width=10.0,
            char_height=20.0,
            rows=10,
            cols=10,
            offset_x=0.0,
            offset_y=0.0,
            cursor_visible=False,
            cursor_row=0,
            cursor_col=0
        )
        print("✗ Should have raised TypeError for non-list grid")
        return False
    except TypeError as e:
        if "list" in str(e).lower():
            print(f"✓ Grid type validation: {e}")
        else:
            print(f"✗ Wrong error for grid type: {e}")
            return False
    
    # Test 4: Color pairs not a dict
    try:
        cpp_renderer.render_frame(
            context=1,
            grid=[],
            color_pairs="not a dict",  # Invalid type
            dirty_rect=(0, 0, 100, 100),
            char_width=10.0,
            char_height=20.0,
            rows=10,
            cols=10,
            offset_x=0.0,
            offset_y=0.0,
            cursor_visible=False,
            cursor_row=0,
            cursor_col=0
        )
        print("✗ Should have raised TypeError for non-dict color_pairs")
        return False
    except TypeError as e:
        if "dict" in str(e).lower():
            print(f"✓ Color pairs type validation: {e}")
        else:
            print(f"✗ Wrong error for color_pairs type: {e}")
            return False
    
    print("✓ All parameter validation tests passed")
    return True

def test_cache_functions():
    """Test cache management functions."""
    import cpp_renderer
    
    print("\nTesting cache functions:")
    
    # Test clear_caches
    try:
        cpp_renderer.clear_caches()
        print("✓ clear_caches() executed successfully")
    except Exception as e:
        print(f"✗ clear_caches() failed: {e}")
        return False
    
    # Test get_performance_metrics
    try:
        metrics = cpp_renderer.get_performance_metrics()
        print(f"✓ get_performance_metrics() returned: {metrics}")
        
        # Check expected keys
        expected_keys = [
            'frames_rendered',
            'total_render_time_ms',
            'avg_render_time_ms',
            'total_batches',
            'avg_batches_per_frame',
            'attr_dict_cache_hits',
            'attr_dict_cache_misses',
            'attr_dict_cache_hit_rate'
        ]
        
        for key in expected_keys:
            if key not in metrics:
                print(f"✗ Missing key in metrics: {key}")
                return False
        
        print("✓ All expected metrics keys present")
        
    except Exception as e:
        print(f"✗ get_performance_metrics() failed: {e}")
        return False
    
    # Test reset_metrics
    try:
        cpp_renderer.reset_metrics()
        print("✓ reset_metrics() executed successfully")
        
        # Verify metrics were reset
        metrics = cpp_renderer.get_performance_metrics()
        if metrics['frames_rendered'] == 0:
            print("✓ Metrics successfully reset")
        else:
            print(f"✗ Metrics not reset: frames_rendered = {metrics['frames_rendered']}")
            return False
            
    except Exception as e:
        print(f"✗ reset_metrics() failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing render_frame() implementation")
    print("=" * 60)
    
    # Test 1: Module import
    if not test_module_import():
        print("\n✗ Module import failed - cannot continue")
        return False
    
    # Test 2: Parameter validation
    if not test_parameter_validation():
        print("\n✗ Parameter validation tests failed")
        return False
    
    # Test 3: Cache functions
    if not test_cache_functions():
        print("\n✗ Cache function tests failed")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
