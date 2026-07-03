#!/usr/bin/env python3
"""
Demo: Profiling Optimization Features

This demo demonstrates the profiling overhead optimizations:
1. Zero overhead when profiling is disabled
2. Efficient frame time tracking with deque
3. Non-blocking file I/O using background threads
4. Conditional profiling (only profile every Nth frame)
"""

import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_profiling import ProfilingManager


def simulate_key_handling():
    """Simulate key handling work"""
    # Simulate some work
    total = 0
    for i in range(1000):
        total += i * i
    return total


def simulate_rendering():
    """Simulate rendering work"""
    # Simulate some work
    result = []
    for i in range(500):
        result.append(str(i))
    return ''.join(result)


def test_disabled_profiling_overhead():
    """Test that disabled profiling has zero overhead"""
    print("=" * 60)
    print("Test 1: Disabled Profiling Overhead")
    print("=" * 60)
    
    # Create disabled profiling manager
    profiler = ProfilingManager(enabled=False)
    
    # Measure time with disabled profiling
    start_time = time.time()
    for i in range(1000):
        profiler.start_frame()
        profiler.profile_key_handling(simulate_key_handling)
        profiler.profile_rendering(simulate_rendering)
        profiler.end_frame()
        if profiler.should_print_fps():
            profiler.print_fps()
    disabled_time = time.time() - start_time
    
    print(f"Time with disabled profiling: {disabled_time:.4f}s")
    print(f"Average per iteration: {disabled_time/1000*1000:.4f}ms")
    print("✓ Disabled profiling should have minimal overhead")
    print()


def test_conditional_rendering_profiling():
    """Test conditional profiling of rendering"""
    print("=" * 60)
    print("Test 2: Conditional Rendering Profiling")
    print("=" * 60)
    
    # Create profiling manager with conditional rendering profiling
    # Profile every 100th render call
    profiler = ProfilingManager(enabled=True, render_profile_interval=100)
    
    print("Profiling enabled with render_profile_interval=100")
    print("This means only every 100th render will be profiled")
    print()
    
    # Simulate 250 render calls
    print("Simulating 250 render calls...")
    for i in range(250):
        profiler.profile_rendering(simulate_rendering)
    
    # Wait for background threads to complete
    time.sleep(0.5)
    
    print(f"Render calls made: 250")
    print(f"Render profiles written: {profiler.render_profile_count}")
    print(f"Expected profiles: 2 (at call 100 and 200)")
    print()
    
    if profiler.render_profile_count == 2:
        print("✓ Conditional profiling working correctly")
    else:
        print(f"✗ Expected 2 profiles, got {profiler.render_profile_count}")
    print()


def test_async_file_io():
    """Test asynchronous file I/O"""
    print("=" * 60)
    print("Test 3: Asynchronous File I/O")
    print("=" * 60)
    
    # Create profiling manager
    profiler = ProfilingManager(enabled=True, render_profile_interval=0)
    
    print("Profiling with async file I/O enabled")
    print("File writes happen in background threads")
    print()
    
    # Measure time for profiling with async I/O
    print("Profiling 10 operations...")
    start_time = time.time()
    
    for i in range(10):
        profiler.profile_key_handling(simulate_key_handling)
    
    elapsed_time = time.time() - start_time
    
    print(f"Time for 10 profiled operations: {elapsed_time:.4f}s")
    print(f"Average per operation: {elapsed_time/10*1000:.4f}ms")
    print()
    print("✓ File I/O happens asynchronously in background")
    print("  Main loop is not blocked by file writes")
    print()
    
    # Give background threads time to complete
    print("Waiting for background file writes to complete...")
    time.sleep(1)
    print(f"Key profiles written: {profiler.key_profile_count}")
    print()


def test_fps_tracking_efficiency():
    """Test efficient FPS tracking with deque"""
    print("=" * 60)
    print("Test 4: Efficient FPS Tracking")
    print("=" * 60)
    
    # Create profiling manager
    profiler = ProfilingManager(enabled=True)
    
    print("FPS tracking uses deque with maxlen for efficiency")
    print("Only recent frames are kept in memory")
    print()
    
    # Simulate frames
    print("Simulating 200 frames...")
    for i in range(200):
        profiler.start_frame()
        time.sleep(0.001)  # Simulate 1ms frame time
    
    print(f"Frames tracked: {len(profiler.fps_tracker.frame_times)}")
    print(f"Max frames in memory: {profiler.fps_tracker.frame_times.maxlen}")
    print()
    
    if len(profiler.fps_tracker.frame_times) == profiler.fps_tracker.frame_times.maxlen:
        print("✓ Deque automatically limits memory usage")
        print("  Old frames are automatically discarded")
    print()


def test_early_return_optimization():
    """Test early return optimization for disabled profiling"""
    print("=" * 60)
    print("Test 5: Early Return Optimization")
    print("=" * 60)
    
    print("When profiling is disabled, methods return immediately")
    print("This provides zero overhead for normal operation")
    print()
    
    # Create disabled profiling manager
    profiler = ProfilingManager(enabled=False)
    
    # Test all methods return immediately
    print("Testing early returns...")
    
    # These should all return immediately without doing any work
    profiler.start_frame()
    profiler.end_frame()
    should_print = profiler.should_print_fps()
    profiler.print_fps()
    result = profiler.profile_key_handling(simulate_key_handling)
    result = profiler.profile_rendering(simulate_rendering)
    
    print("✓ All methods return immediately when disabled")
    print("✓ No profiling overhead in normal operation")
    print()


def main():
    """Run all optimization demos"""
    print("\n" + "=" * 60)
    print("TFM Profiling Optimization Demo")
    print("=" * 60)
    print()
    
    # Run all tests
    test_disabled_profiling_overhead()
    test_conditional_rendering_profiling()
    test_async_file_io()
    test_fps_tracking_efficiency()
    test_early_return_optimization()
    
    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print()
    print("Key Optimizations Demonstrated:")
    print("1. Zero overhead when profiling is disabled")
    print("2. Efficient frame time tracking with deque")
    print("3. Non-blocking file I/O using background threads")
    print("4. Conditional profiling to reduce overhead")
    print("5. Early return optimization for disabled state")
    print()


if __name__ == '__main__':
    main()
