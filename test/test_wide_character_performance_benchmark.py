#!/usr/bin/env python3
"""
Performance benchmark for wide character utilities.

This script measures the performance improvements from caching and ASCII optimizations.
"""

import os
import sys
import time
import statistics

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tfm_wide_char_utils


def benchmark_display_width():
    """Benchmark display width calculation performance."""
    print("=== Display Width Calculation Benchmark ===")
    
    # Test data with different character types
    ascii_files = [f"file_{i:03d}.txt" for i in range(100)]
    japanese_files = [f"ファイル_{i:03d}.txt" for i in range(100)]
    mixed_files = [f"mixed_{i:03d}_英語.txt" for i in range(100)]
    emoji_files = [f"emoji_{i:03d}_📁.txt" for i in range(100)]
    
    all_files = ascii_files + japanese_files + mixed_files + emoji_files
    
    # Clear cache to start fresh
    tfm_wide_char_utils.clear_display_width_cache()
    
    # Benchmark cold cache (first run)
    print("Testing cold cache performance...")
    times = []
    for _ in range(5):
        tfm_wide_char_utils.clear_display_width_cache()
        start_time = time.time()
        for filename in all_files:
            tfm_wide_char_utils.get_display_width(filename)
        end_time = time.time()
        times.append(end_time - start_time)
    
    cold_cache_time = statistics.mean(times)
    print(f"Cold cache: {cold_cache_time:.4f}s avg ({len(all_files)/cold_cache_time:.0f} files/sec)")
    
    # Benchmark warm cache (repeated runs)
    print("Testing warm cache performance...")
    times = []
    for _ in range(5):
        start_time = time.time()
        for filename in all_files:
            tfm_wide_char_utils.get_display_width(filename)
        end_time = time.time()
        times.append(end_time - start_time)
    
    warm_cache_time = statistics.mean(times)
    print(f"Warm cache: {warm_cache_time:.4f}s avg ({len(all_files)/warm_cache_time:.0f} files/sec)")
    
    # Calculate speedup
    speedup = cold_cache_time / warm_cache_time if warm_cache_time > 0 else float('inf')
    print(f"Cache speedup: {speedup:.1f}x")
    
    # Show cache statistics
    cache_info = tfm_wide_char_utils.get_cache_info()
    print(f"Cache info: {cache_info}")
    
    return cold_cache_time, warm_cache_time


def benchmark_ascii_optimization():
    """Benchmark ASCII optimization performance."""
    print("\n=== ASCII Optimization Benchmark ===")
    
    # Pure ASCII filenames (should be fastest)
    ascii_files = [f"file_{i:03d}.txt" for i in range(1000)]
    
    # Mixed character filenames (should use full Unicode processing)
    unicode_files = [f"ファイル_{i:03d}.txt" for i in range(1000)]
    
    # Test ASCII files
    print("Testing ASCII-only files...")
    start_time = time.time()
    for filename in ascii_files:
        tfm_wide_char_utils.get_display_width(filename)
    ascii_time = time.time() - start_time
    print(f"ASCII files: {ascii_time:.4f}s ({len(ascii_files)/ascii_time:.0f} files/sec)")
    
    # Test Unicode files
    print("Testing Unicode files...")
    start_time = time.time()
    for filename in unicode_files:
        tfm_wide_char_utils.get_display_width(filename)
    unicode_time = time.time() - start_time
    print(f"Unicode files: {unicode_time:.4f}s ({len(unicode_files)/unicode_time:.0f} files/sec)")
    
    # Calculate performance difference
    if unicode_time > 0:
        ratio = ascii_time / unicode_time
        print(f"ASCII optimization: {ratio:.1f}x faster than Unicode processing")
    
    return ascii_time, unicode_time


def benchmark_truncation_performance():
    """Benchmark truncation performance with different optimizations."""
    print("\n=== Truncation Performance Benchmark ===")
    
    # Test data
    ascii_text = "very_long_ascii_filename_that_needs_truncation.txt"
    unicode_text = "非常に長い日本語のファイル名で切り詰めが必要なテスト.txt"
    
    iterations = 10000
    
    # Test ASCII truncation
    print("Testing ASCII truncation...")
    start_time = time.time()
    for _ in range(iterations):
        tfm_wide_char_utils.truncate_to_width(ascii_text, 20)
    ascii_time = time.time() - start_time
    print(f"ASCII truncation: {ascii_time:.4f}s ({iterations/ascii_time:.0f} ops/sec)")
    
    # Test Unicode truncation
    print("Testing Unicode truncation...")
    start_time = time.time()
    for _ in range(iterations):
        tfm_wide_char_utils.truncate_to_width(unicode_text, 20)
    unicode_time = time.time() - start_time
    print(f"Unicode truncation: {unicode_time:.4f}s ({iterations/unicode_time:.0f} ops/sec)")
    
    return ascii_time, unicode_time


def benchmark_padding_performance():
    """Benchmark padding performance with different optimizations."""
    print("\n=== Padding Performance Benchmark ===")
    
    # Test data
    ascii_text = "short.txt"
    unicode_text = "短い.txt"
    
    iterations = 10000
    
    # Test ASCII padding
    print("Testing ASCII padding...")
    start_time = time.time()
    for _ in range(iterations):
        tfm_wide_char_utils.pad_to_width(ascii_text, 30)
    ascii_time = time.time() - start_time
    print(f"ASCII padding: {ascii_time:.4f}s ({iterations/ascii_time:.0f} ops/sec)")
    
    # Test Unicode padding
    print("Testing Unicode padding...")
    start_time = time.time()
    for _ in range(iterations):
        tfm_wide_char_utils.pad_to_width(unicode_text, 30)
    unicode_time = time.time() - start_time
    print(f"Unicode padding: {unicode_time:.4f}s ({iterations/unicode_time:.0f} ops/sec)")
    
    return ascii_time, unicode_time


def main():
    """Run all performance benchmarks."""
    print("Wide Character Utilities Performance Benchmark")
    print("=" * 50)
    
    # Run benchmarks
    cold_time, warm_time = benchmark_display_width()
    ascii_time, unicode_time = benchmark_ascii_optimization()
    ascii_trunc_time, unicode_trunc_time = benchmark_truncation_performance()
    ascii_pad_time, unicode_pad_time = benchmark_padding_performance()
    
    # Summary
    print("\n=== Performance Summary ===")
    print(f"Cache effectiveness: {cold_time/warm_time:.1f}x speedup")
    print(f"ASCII optimization: {unicode_time/ascii_time:.1f}x faster for ASCII files")
    print(f"ASCII truncation: {unicode_trunc_time/ascii_trunc_time:.1f}x faster for ASCII text")
    print(f"ASCII padding: {unicode_pad_time/ascii_pad_time:.1f}x faster for ASCII text")
    
    # Performance targets
    print("\n=== Performance Targets ===")
    target_files_per_sec = 1000
    actual_files_per_sec = 400 / warm_time if warm_time > 0 else float('inf')
    
    if actual_files_per_sec >= target_files_per_sec:
        print(f"✓ Performance target met: {actual_files_per_sec:.0f} files/sec >= {target_files_per_sec} files/sec")
    else:
        print(f"✗ Performance target missed: {actual_files_per_sec:.0f} files/sec < {target_files_per_sec} files/sec")


if __name__ == '__main__':
    main()