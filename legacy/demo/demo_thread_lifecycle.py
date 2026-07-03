#!/usr/bin/env python3
"""
Demo: Thread Lifecycle Management

This demo shows how the Directory Diff Viewer properly manages worker threads:
1. Threads start when viewer opens
2. Threads process work in background
3. Threads stop gracefully when viewer closes
4. No resource leaks or hanging threads
"""

import sys
import os
import time
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path


def create_test_directories():
    """Create test directories with some files."""
    temp_dir = tempfile.mkdtemp()
    
    left_dir = Path(os.path.join(temp_dir, "left"))
    right_dir = Path(os.path.join(temp_dir, "right"))
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create some files to scan
    for i in range(10):
        (left_dir / f"file{i}.txt").write_text(f"left content {i}")
        (right_dir / f"file{i}.txt").write_text(f"right content {i}")
    
    # Create some subdirectories
    (left_dir / "subdir1").mkdir()
    (right_dir / "subdir1").mkdir()
    
    for i in range(5):
        (left_dir / "subdir1" / f"nested{i}.txt").write_text(f"nested left {i}")
        (right_dir / "subdir1" / f"nested{i}.txt").write_text(f"nested right {i}")
    
    return temp_dir, left_dir, right_dir


def main():
    """Run the demo."""
    print("=" * 70)
    print("Thread Lifecycle Management Demo")
    print("=" * 70)
    
    # Create test directories
    print("\n1. Creating test directories...")
    temp_dir, left_dir, right_dir = create_test_directories()
    
    try:
        # Create a mock renderer
        class MockRenderer:
            def get_dimensions(self):
                return (24, 80)
            def clear(self):
                pass
            def draw_text(self, y, x, text, color_pair=0, attrs=0):
                pass
        
        renderer = MockRenderer()
        
        # Create viewer
        print("2. Creating Directory Diff Viewer...")
        viewer = DirectoryDiffViewer(renderer, left_dir, right_dir)
        
        # Wait for threads to start
        time.sleep(0.5)
        
        # Check thread status
        print("\n3. Checking worker thread status...")
        scanner_alive = viewer.scanner_thread and viewer.scanner_thread.is_alive()
        comparator_alive = viewer.comparator_thread and viewer.comparator_thread.is_alive()
        
        print(f"   Scanner thread alive: {scanner_alive}")
        print(f"   Comparator thread alive: {comparator_alive}")
        print(f"   Cancelled flag: {viewer.cancelled}")
        print(f"   Worker error: {viewer.worker_error}")
        
        # Let threads do some work
        print("\n4. Letting threads process work...")
        time.sleep(1.0)
        
        # Check scan progress
        print(f"   Scan in progress: {viewer.scan_in_progress}")
        print(f"   Scan status: {viewer.scan_status}")
        print(f"   Items scanned: {viewer.scan_current}")
        
        # Request close
        print("\n5. Requesting viewer close...")
        viewer._should_close = True
        
        # Call should_close() which triggers thread cleanup
        print("6. Calling should_close() to stop threads...")
        start_time = time.time()
        result = viewer.should_close()
        elapsed_time = time.time() - start_time
        
        print(f"   should_close() returned: {result}")
        print(f"   Thread cleanup took: {elapsed_time:.3f}s")
        
        # Check thread status after close
        print("\n7. Checking worker thread status after close...")
        scanner_alive = viewer.scanner_thread and viewer.scanner_thread.is_alive()
        comparator_alive = viewer.comparator_thread and viewer.comparator_thread.is_alive()
        
        print(f"   Scanner thread alive: {scanner_alive}")
        print(f"   Comparator thread alive: {comparator_alive}")
        print(f"   Cancelled flag: {viewer.cancelled}")
        print(f"   Worker error: {viewer.worker_error}")
        
        # Verify threads are stopped
        print("\n8. Verification:")
        if viewer.cancelled:
            print("   ✓ Cancelled flag is set")
        else:
            print("   ✗ Cancelled flag is NOT set")
        
        if not scanner_alive and not comparator_alive:
            print("   ✓ All worker threads stopped")
        else:
            print("   ✗ Some worker threads still running")
        
        if viewer.worker_error is None:
            print("   ✓ No worker errors")
        else:
            print(f"   ✗ Worker error: {viewer.worker_error}")
        
        print("\n" + "=" * 70)
        print("Demo complete!")
        print("=" * 70)
        print("\nKey observations:")
        print("1. Worker threads start automatically when viewer is created")
        print("2. Threads process work in background without blocking")
        print("3. should_close() stops all threads gracefully")
        print("4. Thread cleanup completes within timeout (2s per thread)")
        print("5. No resource leaks or hanging threads")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
