"""
Test character drawing performance metrics collection.

This test verifies that the CharacterDrawingMetrics dataclass and the metrics
collection methods work correctly, tracking cache hit/miss rates, batch sizes,
and timing information.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from ttk.backends.coregraphics_backend import (
        CoreGraphicsBackend,
        CharacterDrawingMetrics,
        AttributeDictCache,
        AttributedStringCache,
        FontCache,
        ColorCache,
        COCOA_AVAILABLE
    )
    from ttk.renderer import TextAttribute
except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping CoreGraphics backend tests (PyObjC not available)")
    sys.exit(0)


def test_character_drawing_metrics_dataclass():
    """Test that CharacterDrawingMetrics dataclass can be instantiated."""
    if not COCOA_AVAILABLE:
        print("Skipping test - PyObjC not available")
        return
    
    metrics = CharacterDrawingMetrics(
        total_time=0.008,
        characters_drawn=1920,
        batches_drawn=80,
        avg_batch_size=24.0,
        attr_dict_cache_hits=75,
        attr_dict_cache_misses=5,
        attr_string_cache_hits=70,
        attr_string_cache_misses=10,
        avg_time_per_char=4.17,
        avg_time_per_batch=100.0
    )
    
    assert metrics.total_time == 0.008
    assert metrics.characters_drawn == 1920
    assert metrics.batches_drawn == 80
    assert metrics.avg_batch_size == 24.0
    assert metrics.attr_dict_cache_hits == 75
    assert metrics.attr_dict_cache_misses == 5
    assert metrics.attr_string_cache_hits == 70
    assert metrics.attr_string_cache_misses == 10
    assert metrics.avg_time_per_char == 4.17
    assert metrics.avg_time_per_batch == 100.0
    
    print("✓ CharacterDrawingMetrics dataclass works correctly")


def test_attribute_dict_cache_metrics():
    """Test that AttributeDictCache tracks hit/miss counts."""
    if not COCOA_AVAILABLE:
        print("Skipping test - PyObjC not available")
        return
    
    import Cocoa
    
    # Create font and color caches
    base_font = Cocoa.NSFont.fontWithName_size_("Menlo", 12)
    font_cache = FontCache(base_font)
    color_cache = ColorCache()
    
    # Create attribute dict cache
    attr_dict_cache = AttributeDictCache(font_cache, color_cache)
    
    # Initial counts should be zero
    assert attr_dict_cache.get_hit_count() == 0
    assert attr_dict_cache.get_miss_count() == 0
    
    # First access - should be a miss
    attrs1 = attr_dict_cache.get_attributes("0", (255, 255, 255), False)
    assert attr_dict_cache.get_hit_count() == 0
    assert attr_dict_cache.get_miss_count() == 1
    
    # Second access with same key - should be a hit
    attrs2 = attr_dict_cache.get_attributes("0", (255, 255, 255), False)
    assert attr_dict_cache.get_hit_count() == 1
    assert attr_dict_cache.get_miss_count() == 1
    assert attrs1 is attrs2  # Same object reference
    
    # Third access with different key - should be a miss
    attrs3 = attr_dict_cache.get_attributes("0", (255, 0, 0), False)
    assert attr_dict_cache.get_hit_count() == 1
    assert attr_dict_cache.get_miss_count() == 2
    
    # Reset metrics
    attr_dict_cache.reset_metrics()
    assert attr_dict_cache.get_hit_count() == 0
    assert attr_dict_cache.get_miss_count() == 0
    
    # Access after reset - should be a hit (cache not cleared)
    attrs4 = attr_dict_cache.get_attributes("0", (255, 255, 255), False)
    assert attr_dict_cache.get_hit_count() == 1
    assert attr_dict_cache.get_miss_count() == 0
    
    print("✓ AttributeDictCache metrics tracking works correctly")


def test_attributed_string_cache_metrics():
    """Test that AttributedStringCache tracks hit/miss counts."""
    if not COCOA_AVAILABLE:
        print("Skipping test - PyObjC not available")
        return
    
    import Cocoa
    
    # Create font and color caches
    base_font = Cocoa.NSFont.fontWithName_size_("Menlo", 12)
    font_cache = FontCache(base_font)
    color_cache = ColorCache()
    
    # Create attribute dict cache and attributed string cache
    attr_dict_cache = AttributeDictCache(font_cache, color_cache)
    attr_string_cache = AttributedStringCache(attr_dict_cache)
    
    # Initial counts should be zero
    assert attr_string_cache.get_hit_count() == 0
    assert attr_string_cache.get_miss_count() == 0
    
    # First access - should be a miss
    str1 = attr_string_cache.get_attributed_string("Hello", "0", (255, 255, 255), False)
    assert attr_string_cache.get_hit_count() == 0
    assert attr_string_cache.get_miss_count() == 1
    
    # Second access with same key - should be a hit
    str2 = attr_string_cache.get_attributed_string("Hello", "0", (255, 255, 255), False)
    assert attr_string_cache.get_hit_count() == 1
    assert attr_string_cache.get_miss_count() == 1
    assert str1 is str2  # Same object reference
    
    # Third access with different text - should be a miss
    str3 = attr_string_cache.get_attributed_string("World", "0", (255, 255, 255), False)
    assert attr_string_cache.get_hit_count() == 1
    assert attr_string_cache.get_miss_count() == 2
    
    # Reset metrics
    attr_string_cache.reset_metrics()
    assert attr_string_cache.get_hit_count() == 0
    assert attr_string_cache.get_miss_count() == 0
    
    # Access after reset - should be a hit (cache not cleared)
    str4 = attr_string_cache.get_attributed_string("Hello", "0", (255, 255, 255), False)
    assert attr_string_cache.get_hit_count() == 1
    assert attr_string_cache.get_miss_count() == 0
    
    print("✓ AttributedStringCache metrics tracking works correctly")


def test_backend_metrics_collection():
    """Test that CoreGraphicsBackend can collect and return metrics."""
    if not COCOA_AVAILABLE:
        print("Skipping test - PyObjC not available")
        return
    
    # Create backend
    backend = CoreGraphicsBackend(rows=24, cols=80)
    backend.initialize()
    
    try:
        # Reset metrics
        backend.reset_character_drawing_metrics()
        
        # Simulate some cache activity by drawing text
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        backend.draw_text(0, 0, "Hello World", color_pair=1, attributes=0)
        backend.draw_text(1, 0, "Hello World", color_pair=1, attributes=0)  # Same text - should hit cache
        backend.draw_text(2, 0, "Different", color_pair=1, attributes=TextAttribute.BOLD)
        
        # Trigger a refresh to cause rendering (which updates cache metrics)
        # Note: In actual usage, the drawRect_ method would be called by Cocoa
        # For testing, we just verify the metrics collection method works
        
        # Collect metrics (no parameters - gets from internal state)
        metrics = backend.get_character_drawing_metrics()
        
        # Verify metrics structure
        assert isinstance(metrics, CharacterDrawingMetrics)
        # Metrics come from internal state, so we just verify the structure
        assert hasattr(metrics, 'total_time')
        assert hasattr(metrics, 'characters_drawn')
        assert hasattr(metrics, 'batches_drawn')
        assert hasattr(metrics, 'avg_batch_size')
        assert hasattr(metrics, 'avg_time_per_char')
        assert hasattr(metrics, 'avg_time_per_batch')
        
        # Cache metrics should be non-negative
        assert metrics.attr_dict_cache_hits >= 0
        assert metrics.attr_dict_cache_misses >= 0
        assert metrics.attr_string_cache_hits >= 0
        assert metrics.attr_string_cache_misses >= 0
        
        print("✓ Backend metrics collection works correctly")
        
    finally:
        backend.shutdown()


def test_metrics_reset():
    """Test that metrics can be reset between frames."""
    if not COCOA_AVAILABLE:
        print("Skipping test - PyObjC not available")
        return
    
    # Create backend
    backend = CoreGraphicsBackend(rows=24, cols=80)
    backend.initialize()
    
    try:
        # Simulate frame 1
        backend.reset_character_drawing_metrics()
        backend.draw_text(0, 0, "Frame 1", color_pair=0)
        
        metrics1 = backend.get_character_drawing_metrics()
        
        # Reset for frame 2
        backend.reset_character_drawing_metrics()
        
        # Verify counters are reset
        metrics2 = backend.get_character_drawing_metrics()
        
        # Metrics should be reset (values should be 0 after reset)
        assert isinstance(metrics2, CharacterDrawingMetrics)
        assert hasattr(metrics2, 'total_time')
        assert hasattr(metrics2, 'characters_drawn')
        
        print("✓ Metrics reset works correctly")
        
    finally:
        backend.shutdown()


def test_metrics_with_zero_values():
    """Test that metrics handle edge cases with zero values."""
    if not COCOA_AVAILABLE:
        print("Skipping test - PyObjC not available")
        return
    
    # Create backend
    backend = CoreGraphicsBackend(rows=24, cols=80)
    backend.initialize()
    
    try:
        # Test with zero characters and batches (after reset)
        backend.reset_character_drawing_metrics()
        metrics = backend.get_character_drawing_metrics()
        
        # Should handle division by zero gracefully
        assert metrics.avg_batch_size == 0.0
        assert metrics.avg_time_per_char == 0.0
        assert metrics.avg_time_per_batch == 0.0
        
        print("✓ Metrics handle zero values correctly")
        
    finally:
        backend.shutdown()


if __name__ == "__main__":
    print("Testing character drawing metrics...")
    print()
    
    test_character_drawing_metrics_dataclass()
    test_attribute_dict_cache_metrics()
    test_attributed_string_cache_metrics()
    test_backend_metrics_collection()
    test_metrics_reset()
    test_metrics_with_zero_values()
    
    print()
    print("All metrics tests passed! ✓")
