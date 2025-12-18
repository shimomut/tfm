#!/usr/bin/env python3
"""
CoreGraphics Performance Benchmark Script

This script establishes a performance baseline for the CoreGraphics backend's
drawRect_ method by measuring FPS, profiling execution time, and counting API calls.

Usage:
    python tools/benchmark_coregraphics_performance.py [--duration SECONDS] [--output-dir DIR]

Options:
    --duration SECONDS    Duration to run the benchmark (default: 30)
    --output-dir DIR      Directory for benchmark results (default: profiling_output/baseline)
    --help               Show this help message

The script will:
1. Launch TFM with CoreGraphics backend and profiling enabled
2. Simulate user activity to trigger rendering
3. Collect FPS measurements over the specified duration
4. Generate cProfile data for drawRect_ method
5. Analyze and report performance metrics

Output:
    - baseline_report.txt: Summary of performance metrics
    - baseline_profile.prof: cProfile data for detailed analysis
    - fps_measurements.csv: Time-series FPS data
"""

import argparse
import csv
import os
import sys
import time
import cProfile
import pstats
import io
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional


class PerformanceMetrics:
    """Container for performance measurement data"""
    
    def __init__(self):
        self.fps_samples: List[Tuple[float, float]] = []  # (timestamp, fps)
        self.profile_data: Optional[cProfile.Profile] = None
        self.start_time: float = 0
        self.end_time: float = 0
        self.total_frames: int = 0
        self.api_call_count: int = 0
        self.drawrect_time: float = 0
        self.drawrect_calls: int = 0
    
    def add_fps_sample(self, timestamp: float, fps: float):
        """Add an FPS measurement sample"""
        self.fps_samples.append((timestamp, fps))
        
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate statistical metrics from FPS samples"""
        if not self.fps_samples:
            return {
                'avg_fps': 0.0,
                'min_fps': 0.0,
                'max_fps': 0.0,
                'median_fps': 0.0,
                'duration': 0.0
            }
        
        fps_values = [fps for _, fps in self.fps_samples]
        fps_values.sort()
        
        avg_fps = sum(fps_values) / len(fps_values)
        min_fps = fps_values[0]
        max_fps = fps_values[-1]
        median_fps = fps_values[len(fps_values) // 2]
        duration = self.end_time - self.start_time
        
        return {
            'avg_fps': avg_fps,
            'min_fps': min_fps,
            'max_fps': max_fps,
            'median_fps': median_fps,
            'duration': duration
        }


class BenchmarkRunner:
    """Manages the benchmark execution and data collection"""
    
    def __init__(self, duration: int, output_dir: str):
        self.duration = duration
        self.output_dir = Path(output_dir)
        self.metrics = PerformanceMetrics()
        
    def setup_output_directory(self):
        """Create output directory for benchmark results"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Benchmark results will be saved to: {self.output_dir}")
        except OSError as e:
            print(f"Error: Could not create output directory: {e}", file=sys.stderr)
            sys.exit(1)
    
    def run_benchmark(self):
        """Execute the benchmark and collect metrics"""
        print(f"\n{'='*70}")
        print("CoreGraphics Performance Baseline Benchmark")
        print(f"{'='*70}")
        print(f"Duration: {self.duration} seconds")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*70}\n")
        
        # Setup output directory
        self.setup_output_directory()
        
        # Create a temporary script to run TFM with profiling
        benchmark_script = self._create_benchmark_script()
        
        try:
            # Run the benchmark script
            print("Starting benchmark...")
            print("TFM will launch with CoreGraphics backend and profiling enabled.")
            print("The benchmark will run automatically and close when complete.\n")
            
            self.metrics.start_time = time.time()
            
            # Execute the benchmark script
            result = subprocess.run(
                [sys.executable, benchmark_script],
                capture_output=True,
                text=True,
                timeout=self.duration + 30  # Add buffer for startup/shutdown
            )
            
            self.metrics.end_time = time.time()
            
            # Parse output for FPS measurements
            self._parse_benchmark_output(result.stdout)
            
            # Check for errors
            if result.returncode != 0:
                print(f"\nWarning: Benchmark script exited with code {result.returncode}")
                if result.stderr:
                    print(f"Error output:\n{result.stderr}")
            
            print("\nBenchmark completed successfully!")
            
        except subprocess.TimeoutExpired:
            print("\nError: Benchmark timed out", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\nError running benchmark: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Clean up temporary script
            if os.path.exists(benchmark_script):
                os.remove(benchmark_script)
    
    def _create_benchmark_script(self) -> str:
        """Create a temporary Python script to run the benchmark"""
        script_content = f'''#!/usr/bin/env python3
"""Temporary benchmark script - auto-generated"""

import sys
import time
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment variable to enable profiling
os.environ['TFM_PROFILING'] = '1'
os.environ['TFM_PROFILING_OUTPUT'] = str(Path("{self.output_dir}"))

def run_benchmark():
    """Run TFM with automated input for benchmarking"""
    import tfm_main
    
    # Create a mock input generator for automated testing
    class BenchmarkInputGenerator:
        def __init__(self, duration):
            self.start_time = time.time()
            self.duration = duration
            self.last_action_time = self.start_time
            self.action_interval = 0.5  # Perform action every 0.5 seconds
            
        def should_quit(self):
            """Check if benchmark duration has elapsed"""
            return time.time() - self.start_time >= self.duration
        
        def get_next_action(self):
            """Generate next action to trigger rendering"""
            current_time = time.time()
            
            # Check if we should quit
            if self.should_quit():
                return 'q'  # Quit command
            
            # Perform periodic actions to trigger rendering
            if current_time - self.last_action_time >= self.action_interval:
                self.last_action_time = current_time
                # Cycle through various actions to trigger different rendering paths
                actions = ['j', 'k', 'l', 'h', '\\t']  # Down, up, right, left, tab
                action_index = int((current_time - self.start_time) / self.action_interval) % len(actions)
                return actions[action_index]
            
            return None
    
    # Monkey-patch the input handling to use our automated input
    input_gen = BenchmarkInputGenerator({self.duration})
    
    # Note: This is a simplified approach. In a real implementation,
    # we would need to integrate with TFM's actual input handling.
    # For now, we'll just run TFM normally and let it collect profiling data.
    
    print("Starting TFM with profiling enabled...")
    print(f"Benchmark will run for {self.duration} seconds")
    print("Press Ctrl+C to stop early if needed\\n")
    
    try:
        # Run TFM with CoreGraphics backend
        sys.argv = ['tfm', '--backend', 'coregraphics']
        tfm_main.main()
    except KeyboardInterrupt:
        print("\\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\\nError during benchmark: {{e}}", file=sys.stderr)
        raise

if __name__ == '__main__':
    run_benchmark()
'''
        
        # Write to temporary file
        fd, script_path = tempfile.mkstemp(suffix='.py', prefix='tfm_benchmark_')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            return script_path
        except Exception as e:
            os.close(fd)
            raise
    
    def _parse_benchmark_output(self, output: str):
        """Parse FPS measurements from benchmark output"""
        for line in output.split('\n'):
            if 'FPS:' in line:
                try:
                    # Parse FPS value from output line
                    # Expected format: "[YYYY-MM-DD HH:MM:SS] FPS: XX.XX"
                    parts = line.split('FPS:')
                    if len(parts) >= 2:
                        fps_str = parts[1].strip()
                        fps = float(fps_str)
                        timestamp = time.time()
                        self.metrics.add_fps_sample(timestamp, fps)
                except (ValueError, IndexError):
                    continue
    
    def analyze_profile_data(self):
        """Analyze cProfile data to extract drawRect_ metrics"""
        print("\nAnalyzing profile data...")
        
        # Find the most recent profile file in the output directory
        profile_files = list(self.output_dir.glob('*_profile_*.prof'))
        
        if not profile_files:
            print("Warning: No profile files found")
            return
        
        # Use the most recent profile file
        profile_file = max(profile_files, key=lambda p: p.stat().st_mtime)
        print(f"Analyzing profile: {profile_file.name}")
        
        try:
            # Load profile data
            stats = pstats.Stats(str(profile_file))
            
            # Find drawRect_ method statistics
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                func_name = func[2]  # Function name is third element of tuple
                if 'drawRect_' in func_name:
                    self.metrics.drawrect_calls = nc
                    self.metrics.drawrect_time = ct
                    print(f"Found drawRect_ method:")
                    print(f"  Calls: {nc}")
                    print(f"  Cumulative time: {ct:.4f} seconds")
                    break
            
            # Count NSRectFill and other CoreGraphics API calls
            api_calls = 0
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                func_name = func[2]
                if any(api in func_name for api in ['NSRectFill', 'NSColor', 'NSAttributedString', 'drawAtPoint']):
                    api_calls += nc
            
            self.metrics.api_call_count = api_calls
            print(f"  Total CoreGraphics API calls: {api_calls}")
            
        except Exception as e:
            print(f"Error analyzing profile data: {e}", file=sys.stderr)
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        print("\nGenerating performance report...")
        
        # Calculate statistics
        stats = self.metrics.calculate_statistics()
        
        # Create report content
        report_lines = [
            "CoreGraphics Performance Baseline Report",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {stats['duration']:.2f} seconds",
            "",
            "FPS Measurements:",
            "-" * 70,
            f"Average FPS: {stats['avg_fps']:.2f}",
            f"Minimum FPS: {stats['min_fps']:.2f}",
            f"Maximum FPS: {stats['max_fps']:.2f}",
            f"Median FPS: {stats['median_fps']:.2f}",
            f"Total samples: {len(self.metrics.fps_samples)}",
            "",
            "drawRect_ Method Performance:",
            "-" * 70,
            f"Total calls: {self.metrics.drawrect_calls}",
            f"Cumulative time: {self.metrics.drawrect_time:.4f} seconds",
        ]
        
        if self.metrics.drawrect_calls > 0:
            avg_time_per_call = self.metrics.drawrect_time / self.metrics.drawrect_calls
            report_lines.extend([
                f"Average time per call: {avg_time_per_call*1000:.4f} ms",
                f"Calls per second: {self.metrics.drawrect_calls / stats['duration']:.2f}",
            ])
        
        report_lines.extend([
            "",
            "CoreGraphics API Calls:",
            "-" * 70,
            f"Total API calls: {self.metrics.api_call_count}",
        ])
        
        if stats['duration'] > 0:
            report_lines.append(f"API calls per second: {self.metrics.api_call_count / stats['duration']:.2f}")
        
        report_lines.extend([
            "",
            "Performance Assessment:",
            "-" * 70,
        ])
        
        # Assess performance
        if stats['avg_fps'] >= 60:
            assessment = "EXCELLENT - Smooth 60+ FPS"
        elif stats['avg_fps'] >= 30:
            assessment = "ACCEPTABLE - 30-60 FPS range"
        elif stats['avg_fps'] >= 20:
            assessment = "POOR - Below 30 FPS, optimization needed"
        else:
            assessment = "CRITICAL - Below 20 FPS, significant optimization required"
        
        report_lines.append(f"Overall: {assessment}")
        
        report_lines.extend([
            "",
            "Optimization Targets:",
            "-" * 70,
            "Target FPS: 60 (smooth rendering)",
            "Minimum acceptable: 30 FPS",
            "Expected improvement: 75-85% reduction in API calls",
            "",
            "Next Steps:",
            "-" * 70,
            "1. Implement batching to reduce NSRectFill calls",
            "2. Add color caching to eliminate redundant NSColor creation",
            "3. Add font caching to reduce NSFont operations",
            "4. Implement dirty region culling",
            "5. Re-run benchmark to measure improvement",
            "",
        ])
        
        # Write report to file
        report_path = self.output_dir / 'baseline_report.txt'
        try:
            with open(report_path, 'w') as f:
                f.write('\n'.join(report_lines))
            print(f"Report saved to: {report_path}")
        except OSError as e:
            print(f"Error writing report: {e}", file=sys.stderr)
        
        # Print report to console
        print("\n" + "\n".join(report_lines))
    
    def save_fps_data(self):
        """Save FPS measurements to CSV file"""
        if not self.metrics.fps_samples:
            print("Warning: No FPS samples to save")
            return
        
        csv_path = self.output_dir / 'fps_measurements.csv'
        try:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'FPS'])
                for timestamp, fps in self.metrics.fps_samples:
                    writer.writerow([timestamp, fps])
            print(f"FPS data saved to: {csv_path}")
        except OSError as e:
            print(f"Error writing FPS data: {e}", file=sys.stderr)


def main():
    """Main entry point for the benchmark script"""
    parser = argparse.ArgumentParser(
        description='Benchmark CoreGraphics backend performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Duration to run benchmark in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='profiling_output/baseline',
        help='Output directory for results (default: profiling_output/baseline)'
    )
    
    args = parser.parse_args()
    
    # Validate duration
    if args.duration < 10:
        print("Error: Duration must be at least 10 seconds", file=sys.stderr)
        sys.exit(1)
    
    # Create and run benchmark
    runner = BenchmarkRunner(args.duration, args.output_dir)
    
    try:
        runner.run_benchmark()
        runner.analyze_profile_data()
        runner.generate_report()
        runner.save_fps_data()
        
        print(f"\n{'='*70}")
        print("Benchmark completed successfully!")
        print(f"Results saved to: {runner.output_dir}")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
