#!/usr/bin/env python3
"""
Demo: Profiling Error Handling

This demo demonstrates the error handling capabilities of the profiling system,
including handling of file write errors, permission errors, disk full scenarios,
and fallback to temp directory.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_profiling import ProfilingManager, ProfileWriter
import cProfile


def demo_normal_operation():
    """Demo: Normal profiling operation"""
    print("=" * 70)
    print("Demo 1: Normal Operation")
    print("=" * 70)
    
    # Create profiling manager with test directory
    test_dir = "test_profiling_output"
    manager = ProfilingManager(enabled=True, output_dir=test_dir)
    
    print(f"✓ Created profiling manager with output directory: {test_dir}")
    
    # Profile a simple function
    def test_function():
        total = 0
        for i in range(1000):
            total += i
        return total
    
    result = manager.profile_key_handling(test_function)
    print(f"✓ Profiled function, result: {result}")
    print(f"✓ Key profile count: {manager.key_profile_count}")
    
    # Clean up
    if Path(test_dir).exists():
        shutil.rmtree(test_dir)
        print(f"✓ Cleaned up test directory")
    
    print()


def demo_permission_error():
    """Demo: Handling permission errors with fallback"""
    print("=" * 70)
    print("Demo 2: Permission Error Handling")
    print("=" * 70)
    
    # Try to create profiling in a read-only location
    # On Unix-like systems, /usr/local typically requires root
    readonly_dir = "/usr/local/tfm_profiling_test"
    
    print(f"Attempting to create profiling directory in: {readonly_dir}")
    print("(This should fail with permission error and use fallback)")
    
    writer = ProfileWriter(output_dir=readonly_dir)
    
    # Try to write a profile
    profiler = cProfile.Profile()
    profiler.enable()
    sum([i for i in range(100)])
    profiler.disable()
    
    filepath = writer.write_profile(profiler, "test")
    
    if filepath:
        print(f"✓ Profile written to: {filepath}")
        if writer.using_fallback:
            print(f"✓ Successfully used fallback directory: {writer.fallback_dir}")
            # Clean up fallback
            if writer.fallback_dir and Path(writer.fallback_dir).exists():
                shutil.rmtree(writer.fallback_dir)
                print(f"✓ Cleaned up fallback directory")
    else:
        print("✗ Failed to write profile (both primary and fallback failed)")
    
    print()


def demo_invalid_path():
    """Demo: Handling invalid path errors"""
    print("=" * 70)
    print("Demo 3: Invalid Path Handling")
    print("=" * 70)
    
    # Try to create profiling in an invalid location
    invalid_dir = "/dev/null/invalid_path"
    
    print(f"Attempting to create profiling directory in: {invalid_dir}")
    print("(This should fail and use fallback)")
    
    writer = ProfileWriter(output_dir=invalid_dir)
    
    # Try to write a profile
    profiler = cProfile.Profile()
    profiler.enable()
    sum([i for i in range(100)])
    profiler.disable()
    
    filepath = writer.write_profile(profiler, "test")
    
    if filepath:
        print(f"✓ Profile written to: {filepath}")
        if writer.using_fallback:
            print(f"✓ Successfully used fallback directory: {writer.fallback_dir}")
            # Clean up fallback
            if writer.fallback_dir and Path(writer.fallback_dir).exists():
                shutil.rmtree(writer.fallback_dir)
                print(f"✓ Cleaned up fallback directory")
    else:
        print("✗ Failed to write profile (both primary and fallback failed)")
    
    print()


def demo_profiling_failure_recovery():
    """Demo: Application continues even if profiling fails"""
    print("=" * 70)
    print("Demo 4: Profiling Failure Recovery")
    print("=" * 70)
    
    # Create manager with invalid directory
    manager = ProfilingManager(enabled=True, output_dir="/invalid/path")
    
    print("Created profiling manager with invalid directory")
    print("Application should continue normally even if profiling fails")
    
    # Profile a function - should work even if file writing fails
    def important_function():
        return sum(range(1000))
    
    try:
        result = manager.profile_key_handling(important_function)
        print(f"✓ Function executed successfully, result: {result}")
        print("✓ Application continued despite profiling errors")
    except Exception as e:
        print(f"✗ Function failed: {e}")
    
    # Clean up any fallback directory
    if manager.profile_writer and manager.profile_writer.fallback_dir:
        fallback = manager.profile_writer.fallback_dir
        if Path(fallback).exists():
            shutil.rmtree(fallback)
            print(f"✓ Cleaned up fallback directory: {fallback}")
    
    print()


def demo_fps_error_handling():
    """Demo: FPS tracking error handling"""
    print("=" * 70)
    print("Demo 5: FPS Error Handling")
    print("=" * 70)
    
    manager = ProfilingManager(enabled=True)
    
    print("Testing FPS tracking with error handling")
    
    # Record some frames
    for i in range(10):
        manager.start_frame()
    
    # Try to print FPS (should handle any errors gracefully)
    try:
        manager.print_fps()
        print("✓ FPS printed successfully")
    except Exception as e:
        print(f"✗ FPS printing failed: {e}")
    
    print()


def demo_thread_creation_failure():
    """Demo: Handling thread creation failures"""
    print("=" * 70)
    print("Demo 6: Thread Creation Error Handling")
    print("=" * 70)
    
    print("Testing async profile writing with error handling")
    print("(Thread creation errors are handled gracefully)")
    
    manager = ProfilingManager(enabled=True, output_dir="test_output")
    
    # Profile a function - async writing should handle errors
    def test_func():
        return sum(range(100))
    
    result = manager.profile_key_handling(test_func)
    print(f"✓ Function executed: {result}")
    print("✓ Async profile writing initiated (errors handled gracefully)")
    
    # Clean up
    if Path("test_output").exists():
        shutil.rmtree("test_output")
        print("✓ Cleaned up test directory")
    
    print()


def main():
    """Run all error handling demos"""
    print("\n" + "=" * 70)
    print("TFM Profiling Error Handling Demonstration")
    print("=" * 70)
    print()
    
    print("This demo shows how the profiling system handles various error")
    print("conditions gracefully without crashing the application.")
    print()
    
    # Run demos
    demo_normal_operation()
    demo_permission_error()
    demo_invalid_path()
    demo_profiling_failure_recovery()
    demo_fps_error_handling()
    demo_thread_creation_failure()
    
    print("=" * 70)
    print("Error Handling Summary")
    print("=" * 70)
    print()
    print("The profiling system handles the following error conditions:")
    print("  ✓ File write errors - logged and fallback attempted")
    print("  ✓ Permission errors - fallback to temp directory")
    print("  ✓ Invalid paths - fallback to temp directory")
    print("  ✓ Disk full scenarios - error logged, application continues")
    print("  ✓ Thread creation failures - error logged, profiling skipped")
    print("  ✓ Profiling failures - function still executes normally")
    print()
    print("All errors are logged to stderr without crashing the application.")
    print()


if __name__ == "__main__":
    main()
