#!/usr/bin/env python3
"""
Demo: TFM Performance Profiling System

This comprehensive demo demonstrates all profiling features in TFM:
1. Command-line flag activation (--profile)
2. Real-time FPS measurements
3. Key event profiling
4. Rendering profiling
5. Profile file generation and organization
6. How to analyze profile files

Usage:
    python3 demo/demo_profiling.py

This demo will:
- Show how to enable profiling mode
- Demonstrate FPS tracking in action
- Generate sample profile files
- Show how to analyze the results
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_profiling import ProfilingManager, FPSTracker


def print_section(title):
    """Print a formatted section header"""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()


def print_subsection(title):
    """Print a formatted subsection header"""
    print()
    print("-" * 70)
    print(title)
    print("-" * 70)
    print()


def demo_command_line_activation():
    """Demo 1: Command-line flag activation"""
    print_section("Demo 1: Command-Line Flag Activation")
    
    print("TFM profiling is activated via the --profile command-line flag:")
    print()
    print("  ./tfm.py --profile")
    print()
    print("When profiling is enabled:")
    print("  ✓ A message is displayed: 'Profiling mode enabled'")
    print("  ✓ FPS measurements are collected and printed every 5 seconds")
    print("  ✓ Key event handling is profiled")
    print("  ✓ Rendering operations are profiled")
    print("  ✓ Profile files are written to profiling_output/ directory")
    print()
    print("When profiling is disabled (default):")
    print("  ✓ Zero overhead - no profiling code executes")
    print("  ✓ Normal TFM operation")
    print()
    
    input("Press Enter to continue...")


def demo_fps_tracking():
    """Demo 2: Real-time FPS measurements"""
    print_section("Demo 2: Real-Time FPS Measurements")
    
    print("FPS (Frames Per Second) tracking measures rendering performance.")
    print("FPS is calculated using a sliding window of recent frame times.")
    print()
    print("Creating FPS tracker and simulating 60 FPS...")
    print()
    
    tracker = FPSTracker(window_size=60, print_interval=2.0)
    
    start_time = time.time()
    frame_count = 0
    
    print("Simulating frames (FPS will be printed every 2 seconds):")
    print()
    
    while time.time() - start_time < 6.0:
        tracker.record_frame()
        frame_count += 1
        
        if tracker.should_print():
            print(tracker.format_output())
        
        # Simulate 60 FPS
        time.sleep(1.0 / 60.0)
    
    print()
    print(f"Total frames rendered: {frame_count}")
    print(f"Final FPS: {tracker.calculate_fps():.2f}")
    print()
    print("In TFM, FPS is printed to stdout every 5 seconds when profiling is enabled.")
    print()
    
    input("Press Enter to continue...")


def simulate_key_handler(event_type):
    """Simulate a key handler that does some work"""
    # Simulate file list processing
    files = []
    for i in range(100):
        files.append(f"file_{i:03d}.txt")
    
    # Simulate sorting
    files.sort()
    
    # Simulate filtering based on event type
    if event_type == 'search':
        filtered = [f for f in files if '5' in f]
    else:
        filtered = files
    
    # Simulate cursor movement
    cursor_pos = 0
    for _ in range(20):
        cursor_pos = (cursor_pos + 1) % len(filtered)
    
    return len(filtered)


def simulate_render_operation():
    """Simulate a rendering operation"""
    # Simulate drawing file list
    lines = []
    for i in range(50):
        lines.append(f"  {i:3d}  file_{i:03d}.txt  {i * 1024:,} bytes")
    
    # Simulate text formatting
    formatted = []
    for line in lines:
        formatted.append(line.ljust(60))
    
    # Simulate color calculations
    colors = []
    for i in range(len(formatted)):
        colors.append((i % 8, i % 2))
    
    return len(formatted)


def demo_key_event_profiling(temp_dir):
    """Demo 3: Key event profiling"""
    print_section("Demo 3: Key Event Profiling")
    
    print("Key event profiling captures detailed performance data for input handling.")
    print("Each key event is profiled using Python's cProfile module.")
    print()
    print(f"Profile files will be written to: {temp_dir}")
    print()
    
    # Create profiling manager
    profiling_manager = ProfilingManager(enabled=True, output_dir=temp_dir)
    
    print("Simulating key events:")
    print()
    
    key_events = [
        ('DOWN', 'Down arrow - move cursor down'),
        ('UP', 'Up arrow - move cursor up'),
        ('ENTER', 'Enter - open file/directory'),
        ('/', 'Search - start search mode'),
        ('TAB', 'Tab - switch panes'),
    ]
    
    for key_code, description in key_events:
        print(f"  Processing: {description}")
        result = profiling_manager.profile_key_handling(
            simulate_key_handler, 
            key_code.lower()
        )
        print(f"    → Handler processed {result} items")
        time.sleep(0.01)  # Ensure unique timestamps
    
    print()
    
    # Show generated files
    profile_files = sorted(Path(temp_dir).glob("key_profile_*.prof"))
    print(f"Generated {len(profile_files)} key event profile files:")
    for profile_file in profile_files:
        size = profile_file.stat().st_size
        print(f"  • {profile_file.name} ({size:,} bytes)")
    
    print()
    input("Press Enter to continue...")
    
    return profile_files


def demo_rendering_profiling(temp_dir):
    """Demo 4: Rendering profiling"""
    print_section("Demo 4: Rendering Profiling")
    
    print("Rendering profiling captures performance data for drawing operations.")
    print("Each frame render is profiled to identify bottlenecks.")
    print()
    
    # Create profiling manager with render_profile_interval=0 to profile every call
    profiling_manager = ProfilingManager(enabled=True, output_dir=temp_dir, 
                                        render_profile_interval=0)
    
    print("Simulating frame renders:")
    print()
    
    for i in range(5):
        print(f"  Rendering frame {i + 1}...")
        result = profiling_manager.profile_rendering(simulate_render_operation)
        print(f"    → Drew {result} lines")
        time.sleep(0.01)  # Ensure unique timestamps
    
    print()
    
    # Show generated files
    profile_files = sorted(Path(temp_dir).glob("render_profile_*.prof"))
    print(f"Generated {len(profile_files)} rendering profile files:")
    for profile_file in profile_files:
        size = profile_file.stat().st_size
        print(f"  • {profile_file.name} ({size:,} bytes)")
    
    print()
    input("Press Enter to continue...")
    
    return profile_files


def demo_profile_file_organization(temp_dir):
    """Demo 5: Profile file organization"""
    print_section("Demo 5: Profile File Organization")
    
    print("Profile files are organized in a dedicated output directory:")
    print()
    print(f"Directory: {temp_dir}")
    print()
    
    # List all files
    all_files = sorted(Path(temp_dir).iterdir())
    
    print("Directory contents:")
    print()
    
    key_profiles = []
    render_profiles = []
    other_files = []
    
    for file in all_files:
        if file.name.startswith('key_profile_'):
            key_profiles.append(file)
        elif file.name.startswith('render_profile_'):
            render_profiles.append(file)
        else:
            other_files.append(file)
    
    if key_profiles:
        print(f"Key Event Profiles ({len(key_profiles)} files):")
        for file in key_profiles[:3]:
            print(f"  • {file.name}")
        if len(key_profiles) > 3:
            print(f"  ... and {len(key_profiles) - 3} more")
        print()
    
    if render_profiles:
        print(f"Rendering Profiles ({len(render_profiles)} files):")
        for file in render_profiles[:3]:
            print(f"  • {file.name}")
        if len(render_profiles) > 3:
            print(f"  ... and {len(render_profiles) - 3} more")
        print()
    
    if other_files:
        print("Other Files:")
        for file in other_files:
            print(f"  • {file.name}")
        print()
    
    # Show README if it exists
    readme_path = Path(temp_dir) / "README.txt"
    if readme_path.exists():
        print("README.txt contents (first 15 lines):")
        print()
        lines = readme_path.read_text().split('\n')[:15]
        for line in lines:
            print(f"  {line}")
        print()
    
    print("File naming convention:")
    print("  • key_profile_YYYYMMDD_HHMMSS_microseconds.prof")
    print("  • render_profile_YYYYMMDD_HHMMSS_microseconds.prof")
    print()
    print("Timestamps ensure unique filenames for each profiling operation.")
    print()
    
    input("Press Enter to continue...")


def demo_analyzing_profiles(profile_files):
    """Demo 6: How to analyze profile files"""
    print_section("Demo 6: Analyzing Profile Files")
    
    if not profile_files:
        print("No profile files available for analysis demo.")
        return
    
    sample_profile = profile_files[0]
    
    print("Profile files can be analyzed using several tools:")
    print()
    
    print_subsection("Method 1: pstats (Built-in Python Tool)")
    
    print("The pstats module is included with Python and provides")
    print("command-line analysis of profile files.")
    print()
    print("To analyze a profile file:")
    print(f"  python3 -m pstats {sample_profile}")
    print()
    print("Common pstats commands:")
    print("  sort cumulative    # Sort by cumulative time")
    print("  stats 20           # Show top 20 functions")
    print("  sort time          # Sort by internal time")
    print("  stats 10           # Show top 10 functions")
    print("  callers func_name  # Show who calls a function")
    print("  callees func_name  # Show what a function calls")
    print()
    
    print_subsection("Method 2: snakeviz (Visual Analysis)")
    
    print("snakeviz provides an interactive web-based visualization")
    print("of profile data with sunburst and icicle diagrams.")
    print()
    print("Installation:")
    print("  pip install snakeviz")
    print()
    print("Usage:")
    print(f"  snakeviz {sample_profile}")
    print()
    print("This will open a web browser with an interactive visualization")
    print("showing function call hierarchies and time distribution.")
    print()
    
    print_subsection("Method 3: gprof2dot (Call Graph)")
    
    print("gprof2dot converts profile data to a call graph visualization.")
    print()
    print("Installation:")
    print("  pip install gprof2dot")
    print()
    print("Usage:")
    print(f"  gprof2dot -f pstats {sample_profile} | dot -Tpng -o profile.png")
    print()
    print("This creates a PNG image showing the call graph with timing info.")
    print()
    
    print_subsection("Interpreting Results")
    
    print("When analyzing profiles, look for:")
    print()
    print("1. Functions with high cumulative time")
    print("   → These functions and their callees consume the most time")
    print()
    print("2. Functions with high internal time")
    print("   → These functions themselves are slow (not their callees)")
    print()
    print("3. Functions called many times")
    print("   → Even fast functions can be bottlenecks if called frequently")
    print()
    print("4. Unexpected function calls")
    print("   → Functions that shouldn't be in the hot path")
    print()
    
    input("Press Enter to continue...")


def demo_profiling_overhead():
    """Demo 7: Profiling overhead"""
    print_section("Demo 7: Profiling Overhead")
    
    print("Profiling has minimal overhead when disabled and acceptable")
    print("overhead when enabled.")
    print()
    
    # Test disabled profiling
    print("Testing DISABLED profiling (should have zero overhead):")
    print()
    
    disabled_manager = ProfilingManager(enabled=False)
    
    start_time = time.time()
    iterations = 1000
    
    for _ in range(iterations):
        disabled_manager.start_frame()
        disabled_manager.end_frame()
        disabled_manager.should_print_fps()
    
    disabled_time = time.time() - start_time
    
    print(f"  Completed {iterations} iterations in {disabled_time:.4f} seconds")
    print(f"  Average per iteration: {disabled_time / iterations * 1000:.4f} ms")
    print()
    
    # Test enabled profiling (FPS tracking only, not full profiling)
    print("Testing ENABLED profiling (FPS tracking only):")
    print()
    
    enabled_manager = ProfilingManager(enabled=True)
    
    start_time = time.time()
    
    for _ in range(iterations):
        enabled_manager.start_frame()
        enabled_manager.end_frame()
        enabled_manager.should_print_fps()
    
    enabled_time = time.time() - start_time
    
    print(f"  Completed {iterations} iterations in {enabled_time:.4f} seconds")
    print(f"  Average per iteration: {enabled_time / iterations * 1000:.4f} ms")
    print()
    
    overhead = ((enabled_time - disabled_time) / disabled_time) * 100
    print(f"Overhead: {overhead:.2f}%")
    print()
    
    if overhead < 10:
        print("✓ Overhead is within acceptable limits (<10%)")
    else:
        print("⚠ Overhead is higher than expected")
    
    print()
    print("Note: Full profiling (with cProfile) has higher overhead but only")
    print("      runs when key events or rendering operations occur.")
    print()
    
    input("Press Enter to continue...")


def demo_complete_workflow():
    """Demo 8: Complete profiling workflow"""
    print_section("Demo 8: Complete Profiling Workflow")
    
    print("Here's the complete workflow for profiling TFM:")
    print()
    
    print("Step 1: Enable Profiling")
    print("  ./tfm.py --profile")
    print()
    
    print("Step 2: Use TFM Normally")
    print("  • Navigate directories")
    print("  • Select files")
    print("  • Perform operations")
    print("  • Observe FPS output every 5 seconds")
    print()
    
    print("Step 3: Exit TFM")
    print("  • Press 'q' to quit")
    print("  • Profile files are saved in profiling_output/")
    print()
    
    print("Step 4: Analyze Results")
    print("  • Use pstats for command-line analysis")
    print("  • Use snakeviz for visual analysis")
    print("  • Identify performance bottlenecks")
    print()
    
    print("Step 5: Optimize Code")
    print("  • Focus on functions with high cumulative time")
    print("  • Optimize frequently-called functions")
    print("  • Reduce unnecessary operations")
    print()
    
    print("Step 6: Verify Improvements")
    print("  • Run profiling again")
    print("  • Compare FPS measurements")
    print("  • Compare profile data")
    print("  • Confirm optimizations worked")
    print()
    
    input("Press Enter to finish demo...")


def main():
    """Run all profiling demos"""
    print()
    print("=" * 70)
    print("TFM Performance Profiling System - Comprehensive Demo")
    print("=" * 70)
    print()
    print("This demo will walk you through all profiling features in TFM.")
    print()
    print("Topics covered:")
    print("  1. Command-line flag activation")
    print("  2. Real-time FPS measurements")
    print("  3. Key event profiling")
    print("  4. Rendering profiling")
    print("  5. Profile file organization")
    print("  6. Analyzing profile files")
    print("  7. Profiling overhead")
    print("  8. Complete profiling workflow")
    print()
    
    input("Press Enter to start the demo...")
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp(prefix="tfm_profiling_demo_")
    
    try:
        # Run all demos
        demo_command_line_activation()
        demo_fps_tracking()
        
        key_profiles = demo_key_event_profiling(temp_dir)
        render_profiles = demo_rendering_profiling(temp_dir)
        
        demo_profile_file_organization(temp_dir)
        
        all_profiles = key_profiles + render_profiles
        demo_analyzing_profiles(all_profiles)
        
        demo_profiling_overhead()
        demo_complete_workflow()
        
        # Summary
        print_section("Demo Complete!")
        
        print("You've seen all the profiling features in TFM:")
        print()
        print("✓ Command-line activation with --profile flag")
        print("✓ Real-time FPS measurements (printed every 5 seconds)")
        print("✓ Key event profiling with cProfile")
        print("✓ Rendering profiling with cProfile")
        print("✓ Organized profile file output")
        print("✓ Multiple analysis methods (pstats, snakeviz, gprof2dot)")
        print("✓ Minimal overhead when disabled")
        print("✓ Complete profiling workflow")
        print()
        print("To use profiling in TFM:")
        print("  ./tfm.py --profile")
        print()
        print("Profile files will be in: profiling_output/")
        print()
        print("For more information, see:")
        print("  doc/PERFORMANCE_PROFILING_FEATURE.md")
        print()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
    
    finally:
        # Clean up temporary directory
        if Path(temp_dir).exists():
            print("Cleaning up temporary files...")
            shutil.rmtree(temp_dir)
            print("✓ Cleanup complete")
            print()


if __name__ == '__main__':
    main()
