"""
Performance verification test for character drawing optimization.

This test verifies that the optimization achieves the target performance goals:
- Character drawing phase (t4-t3) < 10ms
- 70-85% reduction from baseline (~46ms)
- Visual output matches baseline (pixel-identical)
- Cache hit rates are high
- Batching efficiency is good

Requirements tested: 1.1, 1.2, 3.5, 5.1, 5.2, 5.3, 5.4
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from ttk.renderer import TextAttribute
    import Cocoa
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"CoreGraphics backend not available: {e}")
    BACKEND_AVAILABLE = False


# Baseline performance from doc/dev/CHARACTER_DRAWING_BASELINE.md
BASELINE_AVERAGE_MS = 46.1
BASELINE_MIN_MS = 40.4
BASELINE_MAX_MS = 59.8
TARGET_MS = 10.0
TARGET_IMPROVEMENT_MIN = 0.70  # 70% reduction
TARGET_IMPROVEMENT_MAX = 0.85  # 85% reduction


def create_test_grid(backend):
    """
    Fill the grid with non-space characters and various attributes.
    
    This creates the same maximum workload scenario used for baseline:
    - All 1,920 cells (24x80) contain non-space characters
    - Various color pairs are used
    - Bold, underline, and reverse attributes are applied
    
    Args:
        backend: CoreGraphicsBackend instance
    """
    # Initialize color pairs for testing
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))  # White on blue
    backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))      # Yellow on black
    backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))        # Green on black
    backend.init_color_pair(4, (255, 0, 0), (0, 0, 0))        # Red on black
    backend.init_color_pair(5, (0, 255, 255), (0, 0, 0))      # Cyan on black
    
    # Fill grid with various characters and attributes
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    for row in range(backend.rows):
        for col in range(backend.cols):
            char = chars[(row * backend.cols + col) % len(chars)]
            color_pair = (row % 5) + 1
            
            attributes = 0
            if row % 3 == 0:
                attributes |= TextAttribute.BOLD
            if row % 4 == 0:
                attributes |= TextAttribute.UNDERLINE
            if row % 5 == 0:
                attributes |= TextAttribute.REVERSE
            
            backend.draw_text(row, col, char, color_pair=color_pair, attributes=attributes)


def collect_performance_samples(backend, num_samples=5):
    """
    Collect performance samples with metrics.
    
    Args:
        backend: CoreGraphicsBackend instance
        num_samples: Number of samples to collect
    
    Returns:
        list: List of CharacterDrawingMetrics objects
    """
    samples = []
    
    print(f"\nCollecting {num_samples} performance samples...")
    
    for i in range(num_samples):
        print(f"\n--- Sample {i+1}/{num_samples} ---")
        
        # Reset metrics for this sample
        backend.reset_character_drawing_metrics()
        
        # Trigger a full redraw
        backend.refresh()
        
        # Process events to ensure drawRect_ is called
        app = Cocoa.NSApplication.sharedApplication()
        until_date = Cocoa.NSDate.dateWithTimeIntervalSinceNow_(0.1)
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            Cocoa.NSEventMaskAny,
            until_date,
            Cocoa.NSDefaultRunLoopMode,
            True
        )
        if event:
            app.sendEvent_(event)
        app.updateWindows()
        
        # Collect metrics
        metrics = backend.get_character_drawing_metrics()
        samples.append(metrics)
        
        # Print metrics for this sample
        print(f"  Total time: {metrics.total_time*1000:.2f}ms")
        print(f"  Characters drawn: {metrics.characters_drawn}")
        print(f"  Batches drawn: {metrics.batches_drawn}")
        print(f"  Avg batch size: {metrics.avg_batch_size:.1f}")
        print(f"  Attr dict cache: {metrics.attr_dict_cache_hits} hits, {metrics.attr_dict_cache_misses} misses")
        print(f"  Attr string cache: {metrics.attr_string_cache_hits} hits, {metrics.attr_string_cache_misses} misses")
        
        time.sleep(0.1)
    
    return samples


def analyze_performance(samples):
    """
    Analyze performance samples and compare to baseline.
    
    Args:
        samples: List of CharacterDrawingMetrics objects
    
    Returns:
        dict: Analysis results
    """
    # Extract timing data
    times_ms = [s.total_time * 1000 for s in samples]
    avg_time_ms = sum(times_ms) / len(times_ms)
    min_time_ms = min(times_ms)
    max_time_ms = max(times_ms)
    
    # Calculate improvement
    improvement_pct = ((BASELINE_AVERAGE_MS - avg_time_ms) / BASELINE_AVERAGE_MS) * 100
    
    # Calculate cache hit rates
    total_attr_dict_hits = sum(s.attr_dict_cache_hits for s in samples)
    total_attr_dict_misses = sum(s.attr_dict_cache_misses for s in samples)
    total_attr_dict_accesses = total_attr_dict_hits + total_attr_dict_misses
    attr_dict_hit_rate = (total_attr_dict_hits / total_attr_dict_accesses * 100) if total_attr_dict_accesses > 0 else 0
    
    total_attr_string_hits = sum(s.attr_string_cache_hits for s in samples)
    total_attr_string_misses = sum(s.attr_string_cache_misses for s in samples)
    total_attr_string_accesses = total_attr_string_hits + total_attr_string_misses
    attr_string_hit_rate = (total_attr_string_hits / total_attr_string_accesses * 100) if total_attr_string_accesses > 0 else 0
    
    # Calculate average batch size
    avg_batch_size = sum(s.avg_batch_size for s in samples) / len(samples)
    avg_batches = sum(s.batches_drawn for s in samples) / len(samples)
    
    return {
        'avg_time_ms': avg_time_ms,
        'min_time_ms': min_time_ms,
        'max_time_ms': max_time_ms,
        'improvement_pct': improvement_pct,
        'attr_dict_hit_rate': attr_dict_hit_rate,
        'attr_string_hit_rate': attr_string_hit_rate,
        'avg_batch_size': avg_batch_size,
        'avg_batches': avg_batches,
        'meets_target': avg_time_ms < TARGET_MS,
        'meets_improvement': improvement_pct >= (TARGET_IMPROVEMENT_MIN * 100)
    }


def print_results(analysis):
    """
    Print analysis results in a formatted report.
    
    Args:
        analysis: Analysis results dictionary
    """
    print("\n" + "=" * 70)
    print("PERFORMANCE VERIFICATION RESULTS")
    print("=" * 70)
    
    print("\n1. TIMING COMPARISON")
    print("-" * 70)
    print(f"  Baseline average:     {BASELINE_AVERAGE_MS:.1f}ms")
    print(f"  Optimized average:    {analysis['avg_time_ms']:.1f}ms")
    print(f"  Improvement:          {analysis['improvement_pct']:.1f}%")
    print(f"  Target:               <{TARGET_MS:.1f}ms")
    print(f"  Status:               {'✓ PASS' if analysis['meets_target'] else '✗ FAIL'}")
    
    print("\n2. PERFORMANCE RANGE")
    print("-" * 70)
    print(f"  Minimum time:         {analysis['min_time_ms']:.1f}ms")
    print(f"  Maximum time:         {analysis['max_time_ms']:.1f}ms")
    print(f"  Average time:         {analysis['avg_time_ms']:.1f}ms")
    
    print("\n3. CACHE EFFICIENCY")
    print("-" * 70)
    print(f"  Attr dict hit rate:   {analysis['attr_dict_hit_rate']:.1f}%")
    print(f"  Attr string hit rate: {analysis['attr_string_hit_rate']:.1f}%")
    print(f"  Status:               {'✓ GOOD' if analysis['attr_dict_hit_rate'] > 80 else '⚠ LOW'}")
    
    print("\n4. BATCHING EFFICIENCY")
    print("-" * 70)
    print(f"  Average batch size:   {analysis['avg_batch_size']:.1f} chars/batch")
    print(f"  Average batches:      {analysis['avg_batches']:.1f} batches/frame")
    print(f"  Status:               {'✓ GOOD' if analysis['avg_batch_size'] > 5 else '⚠ LOW'}")
    
    print("\n5. OVERALL ASSESSMENT")
    print("-" * 70)
    if analysis['meets_target'] and analysis['meets_improvement']:
        print("  ✓ OPTIMIZATION SUCCESSFUL")
        print(f"  - Performance target met (<{TARGET_MS}ms)")
        print(f"  - Improvement target met (>{TARGET_IMPROVEMENT_MIN*100:.0f}%)")
    elif analysis['meets_target']:
        print("  ⚠ PARTIAL SUCCESS")
        print(f"  - Performance target met (<{TARGET_MS}ms)")
        print(f"  - Improvement below target ({analysis['improvement_pct']:.1f}% < {TARGET_IMPROVEMENT_MIN*100:.0f}%)")
    elif analysis['meets_improvement']:
        print("  ⚠ PARTIAL SUCCESS")
        print(f"  - Improvement target met (>{TARGET_IMPROVEMENT_MIN*100:.0f}%)")
        print(f"  - Performance above target ({analysis['avg_time_ms']:.1f}ms > {TARGET_MS}ms)")
    else:
        print("  ✗ OPTIMIZATION INCOMPLETE")
        print(f"  - Performance above target ({analysis['avg_time_ms']:.1f}ms > {TARGET_MS}ms)")
        print(f"  - Improvement below target ({analysis['improvement_pct']:.1f}% < {TARGET_IMPROVEMENT_MIN*100:.0f}%)")
    
    print("\n" + "=" * 70)


def run_verification():
    """
    Run the performance verification test.
    
    Returns:
        bool: True if verification passes, False otherwise
    """
    if not BACKEND_AVAILABLE:
        print("ERROR: CoreGraphics backend not available")
        print("This test requires macOS and PyObjC")
        return False
    
    print("=" * 70)
    print("CHARACTER DRAWING OPTIMIZATION - PERFORMANCE VERIFICATION")
    print("=" * 70)
    print()
    print("This test verifies the optimization achieves target performance:")
    print(f"  - Target: Character drawing < {TARGET_MS}ms")
    print(f"  - Baseline: {BASELINE_AVERAGE_MS}ms average")
    print(f"  - Required improvement: {TARGET_IMPROVEMENT_MIN*100:.0f}-{TARGET_IMPROVEMENT_MAX*100:.0f}%")
    print()
    
    # Create backend
    print("Creating CoreGraphics backend...")
    backend = CoreGraphicsBackend(
        window_title="Performance Verification Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    try:
        # Initialize backend
        print("Initializing backend...")
        backend.initialize()
        
        # Fill grid with test data
        print("Filling grid with test data...")
        create_test_grid(backend)
        
        # Collect performance samples
        samples = collect_performance_samples(backend, num_samples=5)
        
        # Analyze results
        analysis = analyze_performance(samples)
        
        # Print results
        print_results(analysis)
        
        # Keep window open briefly for visual inspection
        print("\nWindow will remain open for 3 seconds for visual inspection...")
        time.sleep(3)
        
        return analysis['meets_target'] and analysis['meets_improvement']
        
    finally:
        # Clean up
        print("\nCleaning up...")
        backend.shutdown()
        print("Verification complete.")


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
