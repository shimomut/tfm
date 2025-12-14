#!/usr/bin/env python3
"""
Demo: FPS Tracking in TFM

This demo shows how FPS tracking works in profiling mode.
It simulates the main loop behavior and demonstrates FPS calculation.

Usage:
    python3 demo/demo_fps_tracking.py
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_profiling import ProfilingManager, FPSTracker


def demo_fps_tracker_basic():
    """Demo basic FPS tracker functionality"""
    print("=" * 60)
    print("Demo 1: Basic FPS Tracker")
    print("=" * 60)
    print()
    
    tracker = FPSTracker(window_size=60, print_interval=2.0)
    
    print("Simulating 60 FPS for 5 seconds...")
    print("FPS will be printed every 2 seconds")
    print()
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 5.0:
        # Record frame
        tracker.record_frame()
        frame_count += 1
        
        # Check if we should print FPS
        if tracker.should_print():
            print(tracker.format_output())
        
        # Sleep to simulate 60 FPS (16.67ms per frame)
        time.sleep(1.0 / 60.0)
    
    print()
    print(f"Total frames rendered: {frame_count}")
    print(f"Final FPS: {tracker.calculate_fps():.2f}")
    print()


def demo_fps_tracker_variable_rate():
    """Demo FPS tracker with variable frame rates"""
    print("=" * 60)
    print("Demo 2: Variable Frame Rate")
    print("=" * 60)
    print()
    
    tracker = FPSTracker(window_size=60, print_interval=1.0)
    
    print("Simulating variable frame rates...")
    print("Starting at 60 FPS, then dropping to 30 FPS, then 15 FPS")
    print()
    
    # 60 FPS for 2 seconds
    print("Phase 1: 60 FPS")
    start_time = time.time()
    while time.time() - start_time < 2.0:
        tracker.record_frame()
        if tracker.should_print():
            print(tracker.format_output())
        time.sleep(1.0 / 60.0)
    
    # 30 FPS for 2 seconds
    print("\nPhase 2: 30 FPS")
    start_time = time.time()
    while time.time() - start_time < 2.0:
        tracker.record_frame()
        if tracker.should_print():
            print(tracker.format_output())
        time.sleep(1.0 / 30.0)
    
    # 15 FPS for 2 seconds
    print("\nPhase 3: 15 FPS")
    start_time = time.time()
    while time.time() - start_time < 2.0:
        tracker.record_frame()
        if tracker.should_print():
            print(tracker.format_output())
        time.sleep(1.0 / 15.0)
    
    print()


def demo_profiling_manager_integration():
    """Demo ProfilingManager with FPS tracking"""
    print("=" * 60)
    print("Demo 3: ProfilingManager Integration")
    print("=" * 60)
    print()
    
    # Create profiling manager with shorter print interval for demo
    manager = ProfilingManager(enabled=True)
    manager.fps_tracker.print_interval = 1.0  # Print every 1 second for demo
    
    print("ProfilingManager created with FPS tracking enabled")
    print("Simulating main loop with FPS tracking...")
    print()
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 2.5:
        # Start frame (records frame time)
        manager.start_frame()
        
        # Simulate some work
        time.sleep(1.0 / 60.0)
        
        # End frame
        manager.end_frame()
        
        # Print FPS if interval elapsed
        if manager.should_print_fps():
            manager.print_fps()
        
        frame_count += 1
    
    print()
    print(f"Total frames: {frame_count}")
    print()


def demo_disabled_profiling():
    """Demo that disabled profiling has no overhead"""
    print("=" * 60)
    print("Demo 4: Disabled Profiling (No Overhead)")
    print("=" * 60)
    print()
    
    # Create profiling manager (disabled)
    manager = ProfilingManager(enabled=False)
    
    print("ProfilingManager created with profiling DISABLED")
    print("All profiling calls should be no-ops...")
    print()
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 1.0:
        # These should all be no-ops
        manager.start_frame()
        manager.end_frame()
        manager.should_print_fps()
        
        time.sleep(1.0 / 60.0)
        frame_count += 1
    
    print(f"Completed {frame_count} frames with disabled profiling")
    print("No FPS output (as expected)")
    print()


def main():
    """Run all demos"""
    print()
    print("FPS Tracking Demo")
    print("=" * 60)
    print()
    print("This demo shows how FPS tracking works in TFM profiling mode.")
    print()
    
    try:
        demo_fps_tracker_basic()
        time.sleep(1)
        
        demo_fps_tracker_variable_rate()
        time.sleep(1)
        
        demo_profiling_manager_integration()
        time.sleep(1)
        
        demo_disabled_profiling()
        
        print("=" * 60)
        print("Demo Complete!")
        print("=" * 60)
        print()
        print("To use FPS tracking in TFM:")
        print("  ./tfm.py --profile")
        print()
        print("FPS will be printed to stdout every 5 seconds")
        print()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
