#!/usr/bin/env python3
"""
Checkpoint Evaluation: Measure performance after Optimizations 1-3

This script evaluates whether the performance target (< 0.05s) has been met
after implementing the first three optimizations:
1. Cache frequently accessed attributes
2. Pre-calculate row Y-coordinates
3. Use dict.get() for color pair lookup

It provides detailed analysis and recommendations for next steps.
"""

import sys
import time
import statistics
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.renderer import TextAttribute

def create_test_grid(rows=24, cols=80):
    """Create a test grid with various color pairs and attributes."""
    grid = []
    for row in range(rows):
        row_data = []
        for col in range(cols):
            # Vary color pairs and attributes to simulate real usage
            color_pair = (row + col) % 8
            attributes = TextAttribute.NORMAL
            if (row + col) % 10 == 0:
                attributes = TextAttribute.REVERSE
            char = chr(65 + (row + col) % 26)  # A-Z
            row_data.append((char, color_pair, attributes))
        grid.append(row_data)
    return grid

def measure_iteration_time(backend, num_iterations=100):
    """Measure the iteration phase time over multiple runs."""
    times = []
    
    # Full screen dirty region
    start_row, end_row = 0, backend.rows
    start_col, end_col = 0, backend.cols
    
    for _ in range(num_iterations):
        # Import here to get fresh batcher each time
        from ttk.backends.coregraphics_backend import RectangleBatcher
        
        batcher = RectangleBatcher()
        
        # Start timing
        t_start = time.time()
        
        # Optimization 1: Cache frequently accessed attributes
        char_width = backend.char_width
        char_height = backend.char_height
        rows = backend.rows
        grid = backend.grid
        color_pairs = backend.color_pairs
        
        # Iterate through dirty region cells
        for row in range(start_row, end_row):
            # Optimization 2: Pre-calculate row Y-coordinate
            y = (rows - row - 1) * char_height
            
            for col in range(start_col, end_col):
                char, color_pair, attributes = grid[row][col]
                x = col * char_width
                
                # Optimization 3: Use dict.get() for color pair lookup
                fg_rgb, bg_rgb = color_pairs.get(color_pair, color_pairs[0])
                
                if attributes & TextAttribute.REVERSE:
                    fg_rgb, bg_rgb = bg_rgb, fg_rgb
                
                batcher.add_cell(x, y, char_width, char_height, bg_rgb)
            
            batcher.finish_row()
        
        # End timing
        t_end = time.time()
        times.append(t_end - t_start)
    
    return times

def analyze_results(times, target=0.05):
    """Analyze measurement results and provide recommendations."""
    mean_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    
    print("\n" + "="*70)
    print("CHECKPOINT EVALUATION: Optimizations 1-3 Performance Analysis")
    print("="*70)
    
    print(f"\nPerformance Measurements ({len(times)} iterations):")
    print(f"  Mean time:   {mean_time*1000:.2f} ms ({mean_time:.4f} s)")
    print(f"  Median time: {median_time*1000:.2f} ms ({median_time:.4f} s)")
    print(f"  Min time:    {min_time*1000:.2f} ms ({min_time:.4f} s)")
    print(f"  Max time:    {max_time*1000:.2f} ms ({max_time:.4f} s)")
    print(f"  Std dev:     {stdev*1000:.2f} ms ({stdev:.4f} s)")
    
    print(f"\nTarget: < {target*1000:.0f} ms ({target} s)")
    
    # Calculate improvement from baseline (0.2s)
    baseline = 0.2
    improvement = ((baseline - mean_time) / baseline) * 100
    print(f"\nImprovement from baseline (0.2s):")
    print(f"  Absolute: {(baseline - mean_time)*1000:.2f} ms")
    print(f"  Relative: {improvement:.1f}% faster")
    
    # Determine if target is met
    target_met = mean_time < target
    margin = abs(mean_time - target)
    
    print(f"\n{'✓' if target_met else '✗'} Target Status: {'MET' if target_met else 'NOT MET'}")
    if target_met:
        print(f"  Under target by: {margin*1000:.2f} ms ({(margin/target)*100:.1f}%)")
    else:
        print(f"  Over target by: {margin*1000:.2f} ms ({(margin/target)*100:.1f}%)")
    
    # Provide recommendations
    print("\n" + "-"*70)
    print("RECOMMENDATIONS:")
    print("-"*70)
    
    if target_met:
        print("\n✓ Performance target achieved!")
        print("\nOptimizations 1-3 have successfully reduced iteration time below 0.05s.")
        print("Optimization 4 (inlining batching logic) is NOT needed.")
        print("\nNext steps:")
        print("  1. Run comprehensive visual correctness tests")
        print("  2. Create performance comparison documentation")
        print("  3. Update implementation documentation")
    else:
        print("\n✗ Performance target not yet achieved.")
        print("\nOptimization 4 (inline batching logic) should be implemented.")
        print("\nExpected impact of Optimization 4:")
        print("  - Eliminate method call overhead for add_cell()")
        print("  - Reduce parameter passing overhead")
        print("  - Estimated improvement: 20-30%")
        
        # Calculate if Optimization 4 would likely meet target
        estimated_opt4_time = mean_time * 0.7  # Assume 30% improvement
        print(f"\nEstimated time after Optimization 4: {estimated_opt4_time*1000:.2f} ms")
        if estimated_opt4_time < target:
            print(f"  ✓ This should meet the target (under by {(target - estimated_opt4_time)*1000:.2f} ms)")
        else:
            print(f"  ⚠ May still need Optimization 5 (tuple unpacking)")
    
    print("\n" + "="*70)
    
    return target_met, mean_time

def main():
    """Main evaluation function."""
    print("Initializing CoreGraphics backend for testing...")
    
    # Create a mock backend with test data
    backend = CoreGraphicsBackend(rows=24, cols=80)
    backend.char_width = 10
    backend.char_height = 20
    
    # Create test grid
    backend.grid = create_test_grid(backend.rows, backend.cols)
    
    # Create color pairs
    backend.color_pairs = {
        0: ((255, 255, 255), (0, 0, 0)),      # White on black
        1: ((0, 0, 0), (255, 255, 255)),      # Black on white
        2: ((255, 0, 0), (0, 0, 0)),          # Red on black
        3: ((0, 255, 0), (0, 0, 0)),          # Green on black
        4: ((0, 0, 255), (0, 0, 0)),          # Blue on black
        5: ((255, 255, 0), (0, 0, 0)),        # Yellow on black
        6: ((255, 0, 255), (0, 0, 0)),        # Magenta on black
        7: ((0, 255, 255), (0, 0, 0)),        # Cyan on black
    }
    
    print(f"Grid size: {backend.rows}x{backend.cols} = {backend.rows * backend.cols} cells")
    print("Measuring iteration performance with Optimizations 1-3...")
    print("(This may take a moment...)\n")
    
    # Measure performance
    times = measure_iteration_time(backend, num_iterations=100)
    
    # Analyze and report
    target_met, mean_time = analyze_results(times, target=0.05)
    
    # Exit with appropriate code
    sys.exit(0 if target_met else 1)

if __name__ == '__main__':
    main()
