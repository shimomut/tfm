#!/usr/bin/env python3
"""
Measure Optimized CoreGraphics Performance

This script measures the performance of the optimized CoreGraphics backend
and compares it with the baseline measurements.

Usage:
    python tools/measure_optimized_performance.py [--duration SECONDS] [--output-dir DIR] [--baseline-dir DIR]

Options:
    --duration SECONDS       Duration to run the benchmark (default: 30)
    --output-dir DIR        Directory for optimized results (default: profiling_output/optimized)
    --baseline-dir DIR      Directory with baseline results (default: profiling_output/baseline)
    --help                  Show this help message

The script will:
1. Run TFM with CoreGraphics backend and profiling enabled
2. Collect FPS measurements and profile data
3. Analyze performance metrics
4. Compare with baseline if available
5. Calculate percentage improvement
6. Generate comprehensive comparison report
"""

import argparse
import csv
import os
import sys
import time
import subprocess
import tempfile
import pstats
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple


class PerformanceData:
    """Container for performance metrics"""
    
    def __init__(self):
        self.avg_fps: float = 0.0
        self.min_fps: float = 0.0
        self.max_fps: float = 0.0
        self.median_fps: float = 0.0
        self.fps_samples: int = 0
        self.duration: float = 0.0
        
        self.drawrect_calls: int = 0
        self.drawrect_time: float = 0.0
        self.drawrect_avg_time: float = 0.0
        self.drawrect_calls_per_sec: float = 0.0
        
        self.api_call_count: int = 0
        self.api_calls_per_sec: float = 0.0
        self.api_calls_per_frame: float = 0.0
        
    def calculate_derived_metrics(self):
        """Calculate derived metrics from raw data"""
        if self.drawrect_calls > 0:
            self.drawrect_avg_time = self.drawrect_time / self.drawrect_calls
        
        if self.duration > 0:
            self.drawrect_calls_per_sec = self.drawrect_calls / self.duration
            self.api_calls_per_sec = self.api_call_count / self.duration
        
        if self.drawrect_calls > 0:
            self.api_calls_per_frame = self.api_call_count / self.drawrect_calls
    
    @classmethod
    def from_baseline_report(cls, report_path: Path) -> Optional['PerformanceData']:
        """Load performance data from baseline report file"""
        if not report_path.exists():
            return None
        
        data = cls()
        
        try:
            with open(report_path, 'r') as f:
                content = f.read()
            
            # Parse FPS metrics
            for line in content.split('\n'):
                if 'Average FPS:' in line:
                    data.avg_fps = float(line.split(':')[1].strip())
                elif 'Minimum FPS:' in line:
                    data.min_fps = float(line.split(':')[1].strip())
                elif 'Maximum FPS:' in line:
                    data.max_fps = float(line.split(':')[1].strip())
                elif 'Median FPS:' in line:
                    data.median_fps = float(line.split(':')[1].strip())
                elif 'Total samples:' in line:
                    data.fps_samples = int(line.split(':')[1].strip())
                elif 'Duration:' in line and 'seconds' in line:
                    data.duration = float(line.split(':')[1].replace('seconds', '').strip())
                elif 'Total calls:' in line and 'drawRect_' in content[max(0, content.find(line)-200):content.find(line)]:
                    data.drawrect_calls = int(line.split(':')[1].strip())
                elif 'Cumulative time:' in line and 'seconds' in line:
                    data.drawrect_time = float(line.split(':')[1].replace('seconds', '').strip())
                elif 'Total API calls:' in line:
                    data.api_call_count = int(line.split(':')[1].strip())
            
            data.calculate_derived_metrics()
            return data
            
        except Exception as e:
            print(f"Warning: Could not parse baseline report: {e}", file=sys.stderr)
            return None


class PerformanceMeasurement:
    """Manages performance measurement and analysis"""
    
    def __init__(self, duration: int, output_dir: str, baseline_dir: Optional[str] = None):
        self.duration = duration
        self.output_dir = Path(output_dir)
        self.baseline_dir = Path(baseline_dir) if baseline_dir else None
        self.optimized_data = PerformanceData()
        self.baseline_data: Optional[PerformanceData] = None
        
    def setup_directories(self):
        """Create output directory"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Results will be saved to: {self.output_dir}")
        except OSError as e:
            print(f"Error: Could not create output directory: {e}", file=sys.stderr)
            sys.exit(1)
    
    def load_baseline_data(self):
        """Load baseline performance data if available"""
        if not self.baseline_dir:
            print("No baseline directory specified")
            return
        
        baseline_report = self.baseline_dir / 'baseline_report.txt'
        if not baseline_report.exists():
            print(f"Warning: Baseline report not found at {baseline_report}")
            print("Run baseline benchmark first to enable comparison")
            return
        
        print(f"Loading baseline data from: {baseline_report}")
        self.baseline_data = PerformanceData.from_baseline_report(baseline_report)
        
        if self.baseline_data:
            print("Baseline data loaded successfully")
        else:
            print("Warning: Could not load baseline data")
    
    def run_measurement(self):
        """Run TFM and collect performance measurements"""
        print(f"\n{'='*70}")
        print("Measuring Optimized CoreGraphics Performance")
        print(f"{'='*70}")
        print(f"Duration: {self.duration} seconds")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*70}\n")
        
        print("Starting measurement...")
        print("TFM will launch with CoreGraphics backend and profiling enabled.")
        print("Please interact with TFM normally (navigate, scroll, etc.)")
        print(f"After {self.duration} seconds, press 'q' to quit.\n")
        
        # Set environment variables for profiling
        env = os.environ.copy()
        env['TFM_PROFILING'] = '1'
        env['TFM_PROFILING_OUTPUT'] = str(self.output_dir)
        
        start_time = time.time()
        
        try:
            # Run TFM with CoreGraphics backend
            result = subprocess.run(
                [sys.executable, 'tfm.py', '--backend', 'coregraphics'],
                env=env,
                capture_output=True,
                text=True,
                timeout=self.duration + 60  # Add buffer
            )
            
            end_time = time.time()
            self.optimized_data.duration = end_time - start_time
            
            # Parse FPS measurements from output
            self._parse_fps_output(result.stdout)
            
            print("\nMeasurement completed!")
            
        except subprocess.TimeoutExpired:
            print("\nMeasurement timed out (this is normal)")
            end_time = time.time()
            self.optimized_data.duration = end_time - start_time
        except KeyboardInterrupt:
            print("\nMeasurement interrupted by user")
            end_time = time.time()
            self.optimized_data.duration = end_time - start_time
        except Exception as e:
            print(f"\nError during measurement: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _parse_fps_output(self, output: str):
        """Parse FPS measurements from TFM output"""
        fps_values = []
        
        for line in output.split('\n'):
            if 'FPS:' in line:
                try:
                    parts = line.split('FPS:')
                    if len(parts) >= 2:
                        fps_str = parts[1].strip()
                        fps = float(fps_str)
                        fps_values.append(fps)
                except (ValueError, IndexError):
                    continue
        
        if fps_values:
            fps_values.sort()
            self.optimized_data.avg_fps = sum(fps_values) / len(fps_values)
            self.optimized_data.min_fps = fps_values[0]
            self.optimized_data.max_fps = fps_values[-1]
            self.optimized_data.median_fps = fps_values[len(fps_values) // 2]
            self.optimized_data.fps_samples = len(fps_values)
    
    def analyze_profile_data(self):
        """Analyze cProfile data from the measurement"""
        print("\nAnalyzing profile data...")
        
        # Find the most recent profile file
        profile_files = list(self.output_dir.glob('*_profile_*.prof'))
        
        if not profile_files:
            print("Warning: No profile files found")
            return
        
        profile_file = max(profile_files, key=lambda p: p.stat().st_mtime)
        print(f"Analyzing: {profile_file.name}")
        
        try:
            stats = pstats.Stats(str(profile_file))
            
            # Find drawRect_ statistics
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                func_name = func[2]
                if 'drawRect_' in func_name:
                    self.optimized_data.drawrect_calls = nc
                    self.optimized_data.drawrect_time = ct
                    print(f"  drawRect_ calls: {nc}")
                    print(f"  drawRect_ cumulative time: {ct:.4f}s")
                    break
            
            # Count CoreGraphics API calls
            api_patterns = ['NSRectFill', 'NSColor', 'NSAttributedString', 'drawAtPoint', 'setFill']
            api_count = 0
            
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                func_name = func[2]
                if any(pattern in func_name for pattern in api_patterns):
                    api_count += nc
            
            self.optimized_data.api_call_count = api_count
            print(f"  Total API calls: {api_count}")
            
            # Calculate derived metrics
            self.optimized_data.calculate_derived_metrics()
            
        except Exception as e:
            print(f"Error analyzing profile: {e}", file=sys.stderr)
    
    def calculate_improvements(self) -> Dict[str, float]:
        """Calculate percentage improvements over baseline"""
        if not self.baseline_data:
            return {}
        
        improvements = {}
        
        # FPS improvement
        if self.baseline_data.avg_fps > 0:
            fps_improvement = ((self.optimized_data.avg_fps - self.baseline_data.avg_fps) 
                             / self.baseline_data.avg_fps * 100)
            improvements['fps'] = fps_improvement
        
        # drawRect_ time improvement (negative is better)
        if self.baseline_data.drawrect_avg_time > 0:
            time_improvement = ((self.baseline_data.drawrect_avg_time - self.optimized_data.drawrect_avg_time)
                              / self.baseline_data.drawrect_avg_time * 100)
            improvements['drawrect_time'] = time_improvement
        
        # API call reduction
        if self.baseline_data.api_call_count > 0:
            api_reduction = ((self.baseline_data.api_call_count - self.optimized_data.api_call_count)
                           / self.baseline_data.api_call_count * 100)
            improvements['api_calls'] = api_reduction
        
        # API calls per frame reduction
        if self.baseline_data.api_calls_per_frame > 0:
            api_per_frame_reduction = ((self.baseline_data.api_calls_per_frame - self.optimized_data.api_calls_per_frame)
                                      / self.baseline_data.api_calls_per_frame * 100)
            improvements['api_calls_per_frame'] = api_per_frame_reduction
        
        return improvements
    
    def generate_report(self):
        """Generate comprehensive performance report with comparison"""
        print("\nGenerating performance report...")
        
        report_lines = [
            "Optimized CoreGraphics Performance Report",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {self.optimized_data.duration:.2f} seconds",
            "",
            "OPTIMIZED PERFORMANCE METRICS",
            "=" * 70,
            "",
            "FPS Measurements:",
            "-" * 70,
            f"Average FPS: {self.optimized_data.avg_fps:.2f}",
            f"Minimum FPS: {self.optimized_data.min_fps:.2f}",
            f"Maximum FPS: {self.optimized_data.max_fps:.2f}",
            f"Median FPS: {self.optimized_data.median_fps:.2f}",
            f"Total samples: {self.optimized_data.fps_samples}",
            "",
            "drawRect_ Method Performance:",
            "-" * 70,
            f"Total calls: {self.optimized_data.drawrect_calls}",
            f"Cumulative time: {self.optimized_data.drawrect_time:.4f} seconds",
            f"Average time per call: {self.optimized_data.drawrect_avg_time*1000:.4f} ms",
            f"Calls per second: {self.optimized_data.drawrect_calls_per_sec:.2f}",
            "",
            "CoreGraphics API Calls:",
            "-" * 70,
            f"Total API calls: {self.optimized_data.api_call_count}",
            f"API calls per second: {self.optimized_data.api_calls_per_sec:.2f}",
            f"API calls per frame: {self.optimized_data.api_calls_per_frame:.2f}",
            "",
        ]
        
        # Add comparison if baseline data is available
        if self.baseline_data:
            improvements = self.calculate_improvements()
            
            report_lines.extend([
                "COMPARISON WITH BASELINE",
                "=" * 70,
                "",
                "Baseline Performance:",
                "-" * 70,
                f"Average FPS: {self.baseline_data.avg_fps:.2f}",
                f"drawRect_ avg time: {self.baseline_data.drawrect_avg_time*1000:.4f} ms",
                f"Total API calls: {self.baseline_data.api_call_count}",
                f"API calls per frame: {self.baseline_data.api_calls_per_frame:.2f}",
                "",
                "Improvements:",
                "-" * 70,
            ])
            
            if 'fps' in improvements:
                report_lines.append(f"FPS improvement: {improvements['fps']:+.2f}%")
            
            if 'drawrect_time' in improvements:
                report_lines.append(f"drawRect_ time reduction: {improvements['drawrect_time']:+.2f}%")
            
            if 'api_calls' in improvements:
                report_lines.append(f"API call reduction: {improvements['api_calls']:+.2f}%")
            
            if 'api_calls_per_frame' in improvements:
                report_lines.append(f"API calls per frame reduction: {improvements['api_calls_per_frame']:+.2f}%")
            
            report_lines.append("")
            
            # Assessment
            report_lines.extend([
                "Assessment:",
                "-" * 70,
            ])
            
            # Check if we met the 20% improvement target
            if 'fps' in improvements and improvements['fps'] >= 20:
                report_lines.append("✓ Target achieved: FPS improved by 20% or more")
            elif 'fps' in improvements:
                report_lines.append(f"✗ Target not met: FPS improved by only {improvements['fps']:.2f}%")
            
            # Check API call reduction target (75-85%)
            if 'api_calls' in improvements:
                if improvements['api_calls'] >= 75:
                    report_lines.append(f"✓ Excellent API call reduction: {improvements['api_calls']:.2f}%")
                elif improvements['api_calls'] >= 50:
                    report_lines.append(f"✓ Good API call reduction: {improvements['api_calls']:.2f}%")
                else:
                    report_lines.append(f"⚠ Moderate API call reduction: {improvements['api_calls']:.2f}%")
            
            report_lines.append("")
        
        # Performance assessment
        report_lines.extend([
            "Performance Assessment:",
            "-" * 70,
        ])
        
        if self.optimized_data.avg_fps >= 60:
            assessment = "EXCELLENT - Smooth 60+ FPS achieved"
        elif self.optimized_data.avg_fps >= 30:
            assessment = "ACCEPTABLE - 30-60 FPS range"
        elif self.optimized_data.avg_fps >= 20:
            assessment = "POOR - Below 30 FPS, further optimization needed"
        else:
            assessment = "CRITICAL - Below 20 FPS, significant issues remain"
        
        report_lines.append(f"Overall: {assessment}")
        report_lines.append("")
        
        # Write report to file
        report_path = self.output_dir / 'optimized_report.txt'
        try:
            with open(report_path, 'w') as f:
                f.write('\n'.join(report_lines))
            print(f"Report saved to: {report_path}")
        except OSError as e:
            print(f"Error writing report: {e}", file=sys.stderr)
        
        # Print report to console
        print("\n" + "\n".join(report_lines))
        
        return report_lines


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Measure optimized CoreGraphics performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Duration to run measurement in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='profiling_output/optimized',
        help='Output directory for results (default: profiling_output/optimized)'
    )
    
    parser.add_argument(
        '--baseline-dir',
        type=str,
        default='profiling_output/baseline',
        help='Baseline directory for comparison (default: profiling_output/baseline)'
    )
    
    args = parser.parse_args()
    
    # Validate duration
    if args.duration < 10:
        print("Error: Duration must be at least 10 seconds", file=sys.stderr)
        sys.exit(1)
    
    # Create measurement instance
    measurement = PerformanceMeasurement(args.duration, args.output_dir, args.baseline_dir)
    
    try:
        measurement.setup_directories()
        measurement.load_baseline_data()
        measurement.run_measurement()
        measurement.analyze_profile_data()
        measurement.generate_report()
        
        print(f"\n{'='*70}")
        print("Performance measurement completed!")
        print(f"Results saved to: {measurement.output_dir}")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\nMeasurement interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
