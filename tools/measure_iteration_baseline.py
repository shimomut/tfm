#!/usr/bin/env python3
"""
Dirty Region Iteration Baseline Performance Measurement

This script measures the baseline performance of the dirty region iteration phase
in the CoreGraphics backend's drawRect_ method. It specifically measures the
t2-t1 time delta (iteration and batching phase) for various grid states.

Usage:
    python tools/measure_iteration_baseline.py [--iterations N] [--output-dir DIR]

Options:
    --iterations N       Number of test iterations (default: 100)
    --output-dir DIR     Directory for results (default: profiling_output/iteration_baseline)
    --help              Show this help message

The script will:
1. Generate representative grid states with various color pairs and attributes
2. Measure the iteration phase time (t2-t1) for full-screen dirty regions
3. Record baseline performance metrics
4. Generate a detailed performance report

Output:
    - iteration_baseline_report.txt: Summary of performance metrics
    - iteration_measurements.csv: Raw timing data for each iteration
"""

import argparse
import csv
import sys
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import random


# Add project root to path for imports (before src)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from ttk import TextAttribute
    from ttk.backends.coregraphics_backend import RectangleBatcher
except ImportError as e:
    print(f"Error: Could not import required modules: {e}", file=sys.stderr)
    print("Make sure you're running from the project root directory", file=sys.stderr)
    sys.exit(1)


class GridStateGenerator:
    """Generates representative grid states for testing"""
    
    def __init__(self, rows: int = 24, cols: int = 80):
        self.rows = rows
        self.cols = cols
        
    def generate_uniform_grid(self, char: str = 'A', color_pair: int = 1, 
                            attributes: int = 0) -> List[List[Tuple]]:
        """Generate a grid with uniform cells"""
        grid = []
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                row_data.append((char, color_pair, attributes))
            grid.append(row_data)
        return grid
    
    def generate_random_grid(self, num_color_pairs: int = 8) -> List[List[Tuple]]:
        """Generate a grid with random color pairs and attributes"""
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 '
        grid = []
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                char = random.choice(chars)
                color_pair = random.randint(0, num_color_pairs - 1)
                # Randomly apply REVERSE attribute (10% chance)
                attributes = TextAttribute.REVERSE if random.random() < 0.1 else 0
                row_data.append((char, color_pair, attributes))
            grid.append(row_data)
        return grid
    
    def generate_striped_grid(self, stripe_width: int = 10) -> List[List[Tuple]]:
        """Generate a grid with vertical color stripes"""
        grid = []
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                color_pair = (col // stripe_width) % 8
                char = chr(65 + color_pair)  # A-H
                attributes = 0
                row_data.append((char, color_pair, attributes))
            grid.append(row_data)
        return grid
    
    def generate_checkerboard_grid(self) -> List[List[Tuple]]:
        """Generate a checkerboard pattern"""
        grid = []
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                color_pair = (row + col) % 2
                char = '#' if color_pair == 0 else ' '
                attributes = 0
                row_data.append((char, color_pair, attributes))
            grid.append(row_data)
        return grid
    
    def generate_reverse_video_grid(self) -> List[List[Tuple]]:
        """Generate a grid with many reverse video cells"""
        grid = []
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                char = 'R' if (row + col) % 3 == 0 else 'N'
                color_pair = random.randint(0, 7)
                # 50% of cells have reverse video
                attributes = TextAttribute.REVERSE if (row + col) % 2 == 0 else 0
                row_data.append((char, color_pair, attributes))
            grid.append(row_data)
        return grid
    
    def generate_high_color_diversity_grid(self) -> List[List[Tuple]]:
        """Generate a grid with maximum color diversity (worst case for caching)"""
        grid = []
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                # Each cell gets a unique color pair (cycling through available pairs)
                color_pair = (row * self.cols + col) % 16
                char = chr(65 + (color_pair % 26))  # A-Z cycling
                attributes = TextAttribute.REVERSE if (row + col) % 5 == 0 else 0
                row_data.append((char, color_pair, attributes))
            grid.append(row_data)
        return grid
    
    def generate_complex_text_grid(self) -> List[List[Tuple]]:
        """Generate a grid simulating complex text with varied attributes"""
        grid = []
        # Simulate a text editor with syntax highlighting
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                # Simulate different syntax elements
                if col < 4:  # Line numbers
                    char = str(row % 10)
                    color_pair = 8  # Gray
                    attributes = 0
                elif col < 8:  # Indentation
                    char = ' '
                    color_pair = 0
                    attributes = 0
                elif (row + col) % 7 == 0:  # Keywords
                    char = 'K'
                    color_pair = 3  # Blue
                    attributes = 0
                elif (row + col) % 11 == 0:  # Strings
                    char = '"'
                    color_pair = 2  # Green
                    attributes = 0
                elif (row + col) % 13 == 0:  # Comments
                    char = '#'
                    color_pair = 7  # Gray
                    attributes = 0
                else:  # Regular text
                    char = chr(97 + ((row * col) % 26))  # a-z
                    color_pair = 1
                    attributes = 0
                row_data.append((char, color_pair, attributes))
            grid.append(row_data)
        return grid


class IterationBenchmark:
    """Measures the performance of the dirty region iteration phase"""
    
    def __init__(self, rows: int = 24, cols: int = 80, char_width: int = 10, 
                 char_height: int = 20):
        self.rows = rows
        self.cols = cols
        self.char_width = char_width
        self.char_height = char_height
        self.generator = GridStateGenerator(rows, cols)
        
        # Create color pairs dictionary (simulating backend.color_pairs)
        self.color_pairs = {}
        for i in range(16):
            # Generate some representative RGB colors
            fg_rgb = (i * 16, i * 16, i * 16)
            bg_rgb = (255 - i * 16, 255 - i * 16, 255 - i * 16)
            self.color_pairs[i] = (fg_rgb, bg_rgb)
    
    def measure_iteration_time(self, grid: List[List[Tuple]], 
                              start_row: int = 0, end_row: int = None,
                              start_col: int = 0, end_col: int = None) -> float:
        """
        Measure the time taken for the iteration phase (t2-t1).
        This replicates the exact code from drawRect_ lines 1910-1945.
        """
        if end_row is None:
            end_row = self.rows
        if end_col is None:
            end_col = self.cols
        
        # Create a batcher (same as in drawRect_)
        batcher = RectangleBatcher()
        
        # Start timing (t1)
        t1 = time.time()
        
        # Iterate through dirty region cells and accumulate into batches
        # This is the exact code we're optimizing
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                # Get cell data: (char, color_pair, attributes)
                char, color_pair, attributes = grid[row][col]
                
                # Calculate pixel position using coordinate transformation
                x = col * self.char_width
                y = (self.rows - row - 1) * self.char_height
                
                # Get foreground and background colors from color pair
                if color_pair in self.color_pairs:
                    fg_rgb, bg_rgb = self.color_pairs[color_pair]
                else:
                    # Use default colors if color pair not found
                    fg_rgb, bg_rgb = self.color_pairs[0]
                
                # Handle reverse video attribute by swapping colors
                if attributes & TextAttribute.REVERSE:
                    fg_rgb, bg_rgb = bg_rgb, fg_rgb
                
                # Add cell to batch
                batcher.add_cell(x, y, self.char_width, 
                               self.char_height, bg_rgb)
            
            # Finish row - ensures current batch is completed
            batcher.finish_row()
        
        # End timing (t2)
        t2 = time.time()
        
        # Return the time delta (t2 - t1)
        return t2 - t1
    
    def run_benchmark_suite(self, iterations_per_test: int = 100) -> Dict[str, List[float]]:
        """Run a comprehensive benchmark suite with various grid states"""
        results = {}
        
        print(f"\n{'='*70}")
        print("Dirty Region Iteration Baseline Benchmark")
        print(f"{'='*70}")
        print(f"Grid size: {self.rows}x{self.cols} ({self.rows * self.cols} cells)")
        print(f"Iterations per test: {iterations_per_test}")
        print(f"{'='*70}\n")
        
        # Test 1: Uniform grid (best case - all same color)
        print("Test 1: Uniform grid (all same color)...")
        uniform_grid = self.generator.generate_uniform_grid()
        uniform_times = []
        for i in range(iterations_per_test):
            elapsed = self.measure_iteration_time(uniform_grid)
            uniform_times.append(elapsed)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations_per_test}")
        results['uniform'] = uniform_times
        print(f"  Average: {statistics.mean(uniform_times)*1000:.4f} ms")
        
        # Test 2: Random grid (realistic case)
        print("\nTest 2: Random grid (realistic mixed content)...")
        random_grid = self.generator.generate_random_grid()
        random_times = []
        for i in range(iterations_per_test):
            elapsed = self.measure_iteration_time(random_grid)
            random_times.append(elapsed)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations_per_test}")
        results['random'] = random_times
        print(f"  Average: {statistics.mean(random_times)*1000:.4f} ms")
        
        # Test 3: Striped grid (moderate batching)
        print("\nTest 3: Striped grid (vertical color stripes)...")
        striped_grid = self.generator.generate_striped_grid()
        striped_times = []
        for i in range(iterations_per_test):
            elapsed = self.measure_iteration_time(striped_grid)
            striped_times.append(elapsed)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations_per_test}")
        results['striped'] = striped_times
        print(f"  Average: {statistics.mean(striped_times)*1000:.4f} ms")
        
        # Test 4: Checkerboard grid (worst case - minimal batching)
        print("\nTest 4: Checkerboard grid (worst case batching)...")
        checkerboard_grid = self.generator.generate_checkerboard_grid()
        checkerboard_times = []
        for i in range(iterations_per_test):
            elapsed = self.measure_iteration_time(checkerboard_grid)
            checkerboard_times.append(elapsed)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations_per_test}")
        results['checkerboard'] = checkerboard_times
        print(f"  Average: {statistics.mean(checkerboard_times)*1000:.4f} ms")
        
        # Test 5: Reverse video grid (attribute handling)
        print("\nTest 5: Reverse video grid (heavy attribute usage)...")
        reverse_grid = self.generator.generate_reverse_video_grid()
        reverse_times = []
        for i in range(iterations_per_test):
            elapsed = self.measure_iteration_time(reverse_grid)
            reverse_times.append(elapsed)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations_per_test}")
        results['reverse_video'] = reverse_times
        print(f"  Average: {statistics.mean(reverse_times)*1000:.4f} ms")
        
        # Test 6: High color diversity (worst case for color caching)
        print("\nTest 6: High color diversity grid (maximum color pairs)...")
        high_color_grid = self.generator.generate_high_color_diversity_grid()
        high_color_times = []
        for i in range(iterations_per_test):
            elapsed = self.measure_iteration_time(high_color_grid)
            high_color_times.append(elapsed)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations_per_test}")
        results['high_color_diversity'] = high_color_times
        print(f"  Average: {statistics.mean(high_color_times)*1000:.4f} ms")
        
        # Test 7: Complex text (realistic editor content)
        print("\nTest 7: Complex text grid (simulated syntax highlighting)...")
        complex_text_grid = self.generator.generate_complex_text_grid()
        complex_text_times = []
        for i in range(iterations_per_test):
            elapsed = self.measure_iteration_time(complex_text_grid)
            complex_text_times.append(elapsed)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations_per_test}")
        results['complex_text'] = complex_text_times
        print(f"  Average: {statistics.mean(complex_text_times)*1000:.4f} ms")
        
        return results


class ReportGenerator:
    """Generates performance reports from benchmark results"""
    
    def __init__(self, results: Dict[str, List[float]], output_dir: Path):
        self.results = results
        self.output_dir = output_dir
        
    def calculate_statistics(self, times: List[float]) -> Dict[str, float]:
        """Calculate statistical metrics from timing data"""
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times),
            'p95': sorted(times)[int(len(times) * 0.95)],
            'p99': sorted(times)[int(len(times) * 0.99)]
        }
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        print("\n\nGenerating performance report...")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate statistics for each test
        all_stats = {}
        for test_name, times in self.results.items():
            all_stats[test_name] = self.calculate_statistics(times)
        
        # Create report content
        report_lines = [
            "Dirty Region Iteration Baseline Performance Report",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total iterations: {len(next(iter(self.results.values())))} per test",
            "",
            "Performance Target:",
            "-" * 70,
            "Target: < 0.05 seconds (50 ms) for full-screen update",
            "Current requirement: Measure baseline to establish improvement goals",
            "",
            "Test Results:",
            "=" * 70,
        ]
        
        # Add results for each test
        test_descriptions = {
            'uniform': 'Uniform Grid (Best Case - All Same Color)',
            'random': 'Random Grid (Realistic Mixed Content)',
            'striped': 'Striped Grid (Moderate Batching)',
            'checkerboard': 'Checkerboard Grid (Worst Case Batching)',
            'reverse_video': 'Reverse Video Grid (Heavy Attribute Usage)',
            'high_color_diversity': 'High Color Diversity Grid (Maximum Color Pairs)',
            'complex_text': 'Complex Text Grid (Simulated Syntax Highlighting)'
        }
        
        for test_name, stats in all_stats.items():
            description = test_descriptions.get(test_name, test_name)
            report_lines.extend([
                "",
                f"{description}:",
                "-" * 70,
                f"Mean:     {stats['mean']*1000:8.4f} ms",
                f"Median:   {stats['median']*1000:8.4f} ms",
                f"Std Dev:  {stats['stdev']*1000:8.4f} ms",
                f"Min:      {stats['min']*1000:8.4f} ms",
                f"Max:      {stats['max']*1000:8.4f} ms",
                f"95th %:   {stats['p95']*1000:8.4f} ms",
                f"99th %:   {stats['p99']*1000:8.4f} ms",
            ])
            
            # Performance assessment
            if stats['mean'] < 0.05:
                assessment = "✓ MEETS TARGET"
            elif stats['mean'] < 0.10:
                assessment = "⚠ NEEDS OPTIMIZATION (within 2x of target)"
            elif stats['mean'] < 0.20:
                assessment = "✗ REQUIRES OPTIMIZATION (within 4x of target)"
            else:
                assessment = "✗ CRITICAL - SIGNIFICANT OPTIMIZATION REQUIRED"
            
            report_lines.append(f"Assessment: {assessment}")
        
        # Overall summary
        all_means = [stats['mean'] for stats in all_stats.values()]
        overall_mean = statistics.mean(all_means)
        overall_max = max(all_means)
        
        report_lines.extend([
            "",
            "Overall Summary:",
            "=" * 70,
            f"Average across all tests: {overall_mean*1000:.4f} ms",
            f"Worst case (slowest test): {overall_max*1000:.4f} ms",
            f"Target performance: 50.00 ms",
        ])
        
        if overall_mean < 0.05:
            report_lines.append("Status: ✓ BASELINE MEETS TARGET")
        else:
            speedup_needed = overall_mean / 0.05
            report_lines.extend([
                f"Status: ✗ OPTIMIZATION NEEDED",
                f"Required speedup: {speedup_needed:.2f}x faster",
            ])
        
        report_lines.extend([
            "",
            "Bottleneck Analysis:",
            "=" * 70,
            "Primary bottlenecks identified:",
            "1. Repeated attribute access (self.backend.char_width, etc.)",
            "2. Redundant y-coordinate calculations per row",
            "3. Dictionary lookups for color pairs (1920 per frame)",
            "4. Method call overhead (batcher.add_cell() 1920 times)",
            "",
            "Recommended Optimizations:",
            "-" * 70,
            "1. Cache frequently accessed attributes in local variables",
            "2. Pre-calculate y-coordinates once per row",
            "3. Use dict.get() to reduce lookup overhead",
            "4. Consider inlining add_cell() logic if needed",
            "",
            "Next Steps:",
            "-" * 70,
            "1. Implement Optimization 1: Cache attributes",
            "2. Implement Optimization 2: Pre-calculate y-coordinates",
            "3. Implement Optimization 3: Optimize color pair lookup",
            "4. Re-measure and compare with this baseline",
            "5. Implement additional optimizations if target not met",
            "",
        ])
        
        # Write report to file
        report_path = self.output_dir / 'iteration_baseline_report.txt'
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        print(f"Report saved to: {report_path}")
        
        # Print report to console
        print("\n" + "\n".join(report_lines))
    
    def save_raw_data(self):
        """Save raw timing data to CSV file"""
        csv_path = self.output_dir / 'iteration_measurements.csv'
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            header = ['iteration'] + list(self.results.keys())
            writer.writerow(header)
            
            # Write data rows
            num_iterations = len(next(iter(self.results.values())))
            for i in range(num_iterations):
                row = [i + 1]
                for test_name in self.results.keys():
                    row.append(f"{self.results[test_name][i]*1000:.6f}")
                writer.writerow(row)
        
        print(f"Raw data saved to: {csv_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Measure dirty region iteration baseline performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        default=100,
        help='Number of test iterations per grid type (default: 100)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='profiling_output/iteration_baseline',
        help='Output directory for results (default: profiling_output/iteration_baseline)'
    )
    
    args = parser.parse_args()
    
    # Validate iterations
    if args.iterations < 10:
        print("Error: Iterations must be at least 10", file=sys.stderr)
        sys.exit(1)
    
    output_dir = Path(args.output_dir)
    
    try:
        # Create benchmark instance
        benchmark = IterationBenchmark()
        
        # Run benchmark suite
        results = benchmark.run_benchmark_suite(args.iterations)
        
        # Generate report
        report_gen = ReportGenerator(results, output_dir)
        report_gen.generate_report()
        report_gen.save_raw_data()
        
        print(f"\n{'='*70}")
        print("Baseline measurement completed successfully!")
        print(f"Results saved to: {output_dir}")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
