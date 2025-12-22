#!/usr/bin/env python3
"""
Benchmark script for comparing C++ and PyObjC rendering performance.

This script measures rendering time for various grid sizes and compares
the performance of C++ vs PyObjC implementations.

Requirements: 10.1
"""

import sys
import os
import time
import statistics
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import Cocoa
    import Quartz
except ImportError:
    print("Error: PyObjC not available. This benchmark requires macOS with PyObjC.")
    sys.exit(1)

# Try to import C++ renderer directly
try:
    import cpp_renderer
    CPP_AVAILABLE = True
except ImportError:
    print("Warning: C++ renderer not available")
    CPP_AVAILABLE = False


class BenchmarkResults:
    """Container for benchmark results."""
    
    def __init__(self, name: str):
        self.name = name
        self.times: List[float] = []
        self.grid_size: Tuple[int, int] = (0, 0)
        
    def add_time(self, elapsed: float):
        """Add a timing measurement."""
        self.times.append(elapsed)
        
    def get_stats(self) -> Dict[str, float]:
        """Calculate statistics from timing data."""
        if not self.times:
            return {}
            
        return {
            'min': min(self.times) * 1000,  # Convert to ms
            'max': max(self.times) * 1000,
            'mean': statistics.mean(self.times) * 1000,
            'median': statistics.median(self.times) * 1000,
            'stdev': statistics.stdev(self.times) * 1000 if len(self.times) > 1 else 0.0,
        }


def create_test_grid(rows: int, cols: int) -> List[List[Tuple]]:
    """Create a test grid with varied content."""
    grid = []
    
    for row in range(rows):
        row_data = []
        for col in range(cols):
            # Create varied content
            if col % 10 == 0:
                # Some colored text
                char = chr(65 + (col // 10) % 26)  # A-Z
                color_pair = (row % 8) + 1
                attrs = 0
            elif col % 5 == 0:
                # Bold text
                char = '*'
                color_pair = 2
                attrs = 1  # BOLD
            else:
                # Regular text
                char = chr(97 + (col % 26))  # a-z
                color_pair = 0
                attrs = 0
                
            row_data.append((char, color_pair, attrs))
        grid.append(row_data)
        
    return grid


def create_color_pairs() -> Dict[int, Tuple[Tuple[int, int, int], Tuple[int, int, int]]]:
    """Create color pairs for testing."""
    return {
        0: ((255, 255, 255), (0, 0, 0)),      # White on black
        1: ((0, 255, 0), (0, 0, 0)),          # Green on black
        2: ((255, 0, 0), (0, 0, 0)),          # Red on black
        3: ((0, 0, 255), (0, 0, 0)),          # Blue on black
        4: ((255, 255, 0), (0, 0, 0)),        # Yellow on black
        5: ((255, 0, 255), (0, 0, 0)),        # Magenta on black
        6: ((0, 255, 255), (0, 0, 0)),        # Cyan on black
        7: ((128, 128, 128), (0, 0, 0)),      # Gray on black
        8: ((255, 255, 255), (64, 64, 64)),   # White on dark gray
    }


def benchmark_cpp_renderer(grid: List[List[Tuple]], iterations: int = 100) -> BenchmarkResults:
    """Benchmark C++ renderer with the given grid."""
    if not CPP_AVAILABLE:
        raise RuntimeError("C++ renderer not available")
        
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    
    results = BenchmarkResults("C++")
    results.grid_size = (rows, cols)
    
    color_pairs = create_color_pairs()
    cursor_visible = True
    cursor_row = rows // 2
    cursor_col = cols // 2
    
    # Create offscreen context for rendering
    char_width = 10.0
    char_height = 20.0
    width = int(cols * char_width)
    height = int(rows * char_height)
    
    # Import objc to get pointer value
    import objc
    
    # Warm up (first few renders are slower)
    print(f"  Warming up...", end='', flush=True)
    for _ in range(5):
        colorspace = Quartz.CGColorSpaceCreateDeviceRGB()
        context = Quartz.CGBitmapContextCreate(
            None, width, height, 8, width * 4,
            colorspace, Quartz.kCGImageAlphaPremultipliedLast
        )
        
        if context:
            # Dirty rect as tuple (x, y, width, height)
            dirty_rect = (0.0, 0.0, float(width), float(height))
            # Get pointer value from CGContext
            context_ptr = objc.pyobjc_id(context)
            cpp_renderer.render_frame(
                context_ptr, grid, color_pairs,
                dirty_rect, char_width, char_height,
                rows, cols, 0.0, 0.0,
                cursor_visible, cursor_row, cursor_col,
                None
            )
    print(' Done!')
    
    # Actual benchmark
    print(f"  Running {iterations} iterations...", end='', flush=True)
    
    for i in range(iterations):
        colorspace = Quartz.CGColorSpaceCreateDeviceRGB()
        context = Quartz.CGBitmapContextCreate(
            None, width, height, 8, width * 4,
            colorspace, Quartz.kCGImageAlphaPremultipliedLast
        )
        
        if context:
            dirty_rect = (0.0, 0.0, float(width), float(height))
            context_ptr = objc.pyobjc_id(context)
            
            start = time.perf_counter()
            cpp_renderer.render_frame(
                context_ptr, grid, color_pairs,
                dirty_rect, char_width, char_height,
                rows, cols, 0.0, 0.0,
                cursor_visible, cursor_row, cursor_col,
                None
            )
            elapsed = time.perf_counter() - start
            results.add_time(elapsed)
            
        if (i + 1) % 20 == 0:
            print('.', end='', flush=True)
    
    print(' Done!')
    return results


def print_results(results: BenchmarkResults):
    """Print benchmark results."""
    stats = results.get_stats()
    rows, cols = results.grid_size
    
    print(f"\n{results.name} Backend - Grid size: {rows}x{cols} ({rows * cols} cells)")
    print(f"  Min:    {stats['min']:7.3f} ms")
    print(f"  Max:    {stats['max']:7.3f} ms")
    print(f"  Mean:   {stats['mean']:7.3f} ms")
    print(f"  Median: {stats['median']:7.3f} ms")
    print(f"  StdDev: {stats['stdev']:7.3f} ms")


def compare_results(cpp_results: BenchmarkResults, pyobjc_results: BenchmarkResults = None):
    """Compare C++ and PyObjC results."""
    cpp_stats = cpp_results.get_stats()
    
    if not cpp_stats:
        print("\nCannot compare: insufficient data")
        return
    
    if pyobjc_results:
        pyobjc_stats = pyobjc_results.get_stats()
        speedup = pyobjc_stats['mean'] / cpp_stats['mean']
        improvement = ((pyobjc_stats['mean'] - cpp_stats['mean']) / pyobjc_stats['mean']) * 100
        
        print(f"\n{'='*60}")
        print(f"Performance Comparison")
        print(f"{'='*60}")
        print(f"C++ Mean:    {cpp_stats['mean']:7.3f} ms")
        print(f"PyObjC Mean: {pyobjc_stats['mean']:7.3f} ms")
        print(f"Speedup:     {speedup:.2f}x")
        print(f"Improvement: {improvement:.1f}%")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"C++ Performance Summary")
        print(f"{'='*60}")
        print(f"Mean:   {cpp_stats['mean']:7.3f} ms")
        print(f"Median: {cpp_stats['median']:7.3f} ms")
        print(f"{'='*60}")


def main():
    """Run benchmarks."""
    print("="*60)
    print("C++ Rendering Performance Benchmark")
    print("="*60)
    
    if not CPP_AVAILABLE:
        print("\nERROR: C++ renderer not available!")
        print("Please build the C++ extension first:")
        print("  python setup.py build_ext --inplace")
        sys.exit(1)
    
    # Test grid sizes
    grid_sizes = [
        (25, 80),    # Small terminal
        (40, 120),   # Medium terminal
        (50, 200),   # Large terminal
    ]
    
    iterations = 100
    all_results = []
    
    for rows, cols in grid_sizes:
        print(f"\n{'='*60}")
        print(f"Testing grid size: {rows}x{cols} ({rows * cols} cells)")
        print(f"{'='*60}")
        
        # Create test grid
        grid = create_test_grid(rows, cols)
        
        # Test C++ backend
        print("\nBenchmarking C++ renderer...")
        cpp_results = benchmark_cpp_renderer(grid, iterations)
        print_results(cpp_results)
        all_results.append(cpp_results)
        
        # Get C++ metrics
        try:
            metrics = cpp_renderer.get_performance_metrics()
            print(f"\n  Cache Statistics:")
            print(f"    Hit Rate:    {metrics.get('attr_dict_cache_hit_rate', 0):.1f}%")
            print(f"    Hits:        {metrics.get('attr_dict_cache_hits', 0)}")
            print(f"    Misses:      {metrics.get('attr_dict_cache_misses', 0)}")
            print(f"    Avg Batches: {metrics.get('avg_batches_per_frame', 0):.1f}")
            
            # Reset metrics for next test
            cpp_renderer.reset_metrics()
        except Exception as e:
            print(f"  Could not retrieve metrics: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Benchmark Summary")
    print(f"{'='*60}")
    for result in all_results:
        stats = result.get_stats()
        rows, cols = result.grid_size
        cells = rows * cols
        print(f"\nGrid {rows}x{cols} ({cells} cells):")
        print(f"  Mean:   {stats['mean']:7.3f} ms")
        print(f"  Median: {stats['median']:7.3f} ms")
        print(f"  FPS:    {1000.0 / stats['mean']:7.1f}")
    
    print(f"\n{'='*60}")
    print("Benchmark Complete")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
