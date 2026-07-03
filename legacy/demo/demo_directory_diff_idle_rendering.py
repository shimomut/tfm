#!/usr/bin/env python3
"""
Demo: DirectoryDiffViewer Idle Rendering Fix

This demo verifies that DirectoryDiffViewer does not constantly render
when there are no updates. It creates a simple directory comparison and
monitors the needs_redraw() method to ensure it only returns True when
there's actual work to do.

Expected behavior:
- needs_redraw() returns True during initial scan
- needs_redraw() returns True when queues have work
- needs_redraw() returns False when idle (no work, no changes)
- needs_redraw() returns True only after mark_dirty() is called
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_path import Path as TFMPath


def create_test_directories():
    """Create two temporary directories with some test files."""
    temp_dir = tempfile.mkdtemp(prefix="diff_test_")
    
    left_dir = Path(temp_dir) / "left"
    right_dir = Path(temp_dir) / "right"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create identical files
    (left_dir / "identical.txt").write_text("same content")
    (right_dir / "identical.txt").write_text("same content")
    
    # Create different files
    (left_dir / "different.txt").write_text("left content")
    (right_dir / "different.txt").write_text("right content")
    
    # Create file only on left
    (left_dir / "only_left.txt").write_text("only on left")
    
    # Create file only on right
    (right_dir / "only_right.txt").write_text("only on right")
    
    return TFMPath(str(left_dir)), TFMPath(str(right_dir)), temp_dir


def test_idle_rendering():
    """Test that DirectoryDiffViewer doesn't render constantly when idle."""
    print("Creating test directories...")
    left_path, right_path, temp_dir = create_test_directories()
    
    print(f"Left:  {left_path}")
    print(f"Right: {right_path}")
    print()
    
    # Create a mock renderer
    class MockRenderer:
        def get_dimensions(self):
            return (24, 80)
        
        def clear(self):
            pass
        
        def draw_text(self, row, col, text, color_pair=0, attrs=0):
            pass
    
    renderer = MockRenderer()
    
    print("Creating DirectoryDiffViewer...")
    viewer = DirectoryDiffViewer(renderer, left_path, right_path)
    
    # Wait for initial scan to complete
    print("Waiting for initial scan to complete...")
    max_wait = 10.0
    start_time = time.time()
    while (time.time() - start_time) < max_wait:
        # Check needs_redraw to trigger scan completion detection
        viewer.needs_redraw()
        if not viewer.scan_in_progress and viewer.scan_queue.empty() and viewer.comparison_queue.empty():
            break
        time.sleep(0.1)
    
    if viewer.scan_in_progress or not viewer.scan_queue.empty() or not viewer.comparison_queue.empty():
        print(f"WARNING: Scan did not complete within timeout")
        print(f"  scan_in_progress: {viewer.scan_in_progress}")
        print(f"  scan_queue: {viewer.scan_queue.qsize()}")
        print(f"  comparison_queue: {viewer.comparison_queue.qsize()}")
    else:
        print("Initial scan completed")
    
    # Wait a bit more for queues to drain
    print("Waiting for queues to drain...")
    time.sleep(0.5)
    
    # Now test needs_redraw() behavior
    print("\nTesting needs_redraw() behavior:")
    print("-" * 50)
    
    # Test 1: Should be False when idle
    print("\nTest 1: needs_redraw() when idle")
    viewer._dirty = False  # Clear dirty flag
    needs_redraw_count = 0
    for i in range(10):
        if viewer.needs_redraw():
            needs_redraw_count += 1
        time.sleep(0.05)
    
    if needs_redraw_count == 0:
        print(f"✓ PASS: needs_redraw() returned False all 10 times (idle)")
    else:
        print(f"✗ FAIL: needs_redraw() returned True {needs_redraw_count}/10 times (should be 0)")
    
    # Test 2: Should be True after mark_dirty()
    print("\nTest 2: needs_redraw() after mark_dirty()")
    viewer.mark_dirty()
    if viewer.needs_redraw():
        print("✓ PASS: needs_redraw() returned True after mark_dirty()")
    else:
        print("✗ FAIL: needs_redraw() returned False after mark_dirty()")
    
    # Test 3: Should be False after clear_dirty()
    print("\nTest 3: needs_redraw() after clear_dirty()")
    viewer.clear_dirty()
    if not viewer.needs_redraw():
        print("✓ PASS: needs_redraw() returned False after clear_dirty()")
    else:
        print("✗ FAIL: needs_redraw() returned True after clear_dirty()")
    
    # Test 4: Monitor for constant rendering over time
    print("\nTest 4: Monitor for constant rendering (5 seconds)")
    viewer._dirty = False
    render_count = 0
    start_time = time.time()
    while (time.time() - start_time) < 5.0:
        if viewer.needs_redraw():
            render_count += 1
            viewer.clear_dirty()
        time.sleep(0.1)
    
    print(f"Render count over 5 seconds: {render_count}")
    if render_count == 0:
        print("✓ PASS: No unnecessary renders detected")
    elif render_count < 5:
        print(f"⚠ WARNING: {render_count} renders detected (acceptable if queues had work)")
    else:
        print(f"✗ FAIL: {render_count} renders detected (too many for idle state)")
    
    # Cleanup
    print("\nCleaning up...")
    viewer._stop_worker_threads()
    
    # Remove temp directory
    import shutil
    shutil.rmtree(temp_dir)
    
    print("\nDemo complete!")


if __name__ == "__main__":
    test_idle_rendering()
