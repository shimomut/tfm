#!/usr/bin/env python3
"""
Demo: Character Drawing Performance Metrics

This demo shows how to use the performance instrumentation to track cache
hit/miss rates, batch sizes, and timing metrics during character drawing.

The demo creates a backend, draws some text with various attributes, and
displays the collected metrics.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
    from ttk.renderer import TextAttribute
except ImportError as e:
    print(f"Import error: {e}")
    print("This demo requires PyObjC to be installed.")
    sys.exit(1)

if not COCOA_AVAILABLE:
    print("PyObjC is not available. This demo requires macOS with PyObjC installed.")
    sys.exit(1)


def main():
    """Run the character drawing metrics demo."""
    print("Character Drawing Performance Metrics Demo")
    print("=" * 60)
    print()
    
    # Create backend
    print("Creating CoreGraphics backend...")
    backend = CoreGraphicsBackend(
        window_title="Character Drawing Metrics Demo",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    try:
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))  # White on black
        backend.init_color_pair(2, (255, 0, 0), (0, 0, 0))      # Red on black
        backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))      # Green on black
        backend.init_color_pair(4, (0, 0, 255), (0, 0, 0))      # Blue on black
        
        print("Drawing text with various attributes...")
        print()
        
        # Frame 1: Initial draw with cache misses
        print("Frame 1: Initial draw (expect cache misses)")
        print("-" * 60)
        
        backend.reset_character_drawing_metrics()
        
        # Draw some text
        backend.draw_text(0, 0, "Hello, World!", color_pair=1, attributes=0)
        backend.draw_text(1, 0, "Bold Text", color_pair=2, attributes=TextAttribute.BOLD)
        backend.draw_text(2, 0, "Underline", color_pair=3, attributes=TextAttribute.UNDERLINE)
        backend.draw_text(3, 0, "Bold + Underline", color_pair=4, 
                         attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
        
        # Simulate metrics collection (in real usage, drawRect_ would be called)
        # For demo purposes, we'll just show the structure
        metrics = backend.get_character_drawing_metrics()
        
        print_metrics(metrics)
        print()
        
        # Frame 2: Redraw with cache hits
        print("Frame 2: Redraw same text (expect cache hits)")
        print("-" * 60)
        
        backend.reset_character_drawing_metrics()
        
        # Draw the same text again
        backend.draw_text(0, 0, "Hello, World!", color_pair=1, attributes=0)
        backend.draw_text(1, 0, "Bold Text", color_pair=2, attributes=TextAttribute.BOLD)
        backend.draw_text(2, 0, "Underline", color_pair=3, attributes=TextAttribute.UNDERLINE)
        backend.draw_text(3, 0, "Bold + Underline", color_pair=4, 
                         attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
        
        metrics = backend.get_character_drawing_metrics()
        
        print_metrics(metrics)
        print()
        
        # Frame 3: Large batch
        print("Frame 3: Large batch (same attributes)")
        print("-" * 60)
        
        backend.reset_character_drawing_metrics()
        
        # Draw a long string with same attributes (good batching)
        long_text = "A" * 80
        backend.draw_text(5, 0, long_text, color_pair=1, attributes=0)
        
        metrics = backend.get_character_drawing_metrics()
        
        print_metrics(metrics)
        print()
        
        # Frame 4: Poor batching
        print("Frame 4: Poor batching (alternating attributes)")
        print("-" * 60)
        
        backend.reset_character_drawing_metrics()
        
        # Draw text with alternating attributes (poor batching)
        for i in range(20):
            attr = TextAttribute.BOLD if i % 2 == 0 else 0
            backend.draw_text(7, i * 4, "AB", color_pair=1, attributes=attr)
        
        metrics = backend.get_character_drawing_metrics()
        
        print_metrics(metrics)
        print()
        
        print("Demo complete!")
        print()
        print("Key Observations:")
        print("- Frame 1: Initial cache misses as new entries are created")
        print("- Frame 2: Cache hits improve performance for repeated patterns")
        print("- Frame 3: Large batches (high avg batch size) are most efficient")
        print("- Frame 4: Poor batching (low avg batch size) reduces efficiency")
        
    finally:
        backend.shutdown()


def print_metrics(metrics):
    """Print metrics in a formatted way."""
    print(f"  Total time: {metrics.total_time * 1000:.3f}ms")
    print(f"  Characters drawn: {metrics.characters_drawn}")
    print(f"  Batches drawn: {metrics.batches_drawn}")
    print(f"  Avg batch size: {metrics.avg_batch_size:.1f} chars/batch")
    print()
    
    # Calculate cache hit rates
    attr_dict_total = metrics.attr_dict_cache_hits + metrics.attr_dict_cache_misses
    attr_string_total = metrics.attr_string_cache_hits + metrics.attr_string_cache_misses
    
    if attr_dict_total > 0:
        attr_dict_hit_rate = metrics.attr_dict_cache_hits / attr_dict_total * 100
        print(f"  Attr Dict Cache:")
        print(f"    Hits: {metrics.attr_dict_cache_hits}, Misses: {metrics.attr_dict_cache_misses}")
        print(f"    Hit rate: {attr_dict_hit_rate:.1f}%")
    else:
        print(f"  Attr Dict Cache: No accesses")
    
    if attr_string_total > 0:
        attr_string_hit_rate = metrics.attr_string_cache_hits / attr_string_total * 100
        print(f"  Attr String Cache:")
        print(f"    Hits: {metrics.attr_string_cache_hits}, Misses: {metrics.attr_string_cache_misses}")
        print(f"    Hit rate: {attr_string_hit_rate:.1f}%")
    else:
        print(f"  Attr String Cache: No accesses")
    
    print()
    print(f"  Avg time per char: {metrics.avg_time_per_char:.2f}μs")
    print(f"  Avg time per batch: {metrics.avg_time_per_batch:.2f}μs")


if __name__ == "__main__":
    main()
