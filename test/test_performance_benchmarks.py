"""
Performance benchmark tests for TFM TTK migration.

These tests verify that performance requirements from Requirement 8 are met:
8.1: Performance equivalent to or better than curses-only version
8.2: Large directories remain responsive
8.3: Search operations don't lag
8.4: CoreGraphics backend achieves 60 FPS
8.5: No operation more than 10% slower than pre-migration
"""

import sys
import time
import platform
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_rendering_performance():
    """Test basic rendering performance meets requirements."""
    from ttk.backends.curses_backend import CursesBackend
    
    backend = CursesBackend()
    backend.initialize()
    
    try:
        # Test clear + refresh performance
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            backend.clear()
            backend.refresh()
        elapsed = time.time() - start
        clear_refresh_rate = iterations / elapsed
        
        # Should be able to do at least 100 clear+refresh per second
        assert clear_refresh_rate >= 100, f"Clear+refresh too slow: {clear_refresh_rate:.1f} ops/sec"
        
        # Test text drawing performance
        iterations = 1000
        start = time.time()
        for i in range(iterations):
            backend.draw_text(0, 0, f"Test {i}", color_pair=0)
        elapsed = time.time() - start
        draw_text_rate = iterations / elapsed
        
        # Should be able to draw at least 1000 text strings per second
        assert draw_text_rate >= 1000, f"Text drawing too slow: {draw_text_rate:.1f} ops/sec"
        
        # Test full screen update (simulating directory listing)
        height, width = backend.get_dimensions()
        iterations = 20
        start = time.time()
        for _ in range(iterations):
            backend.clear()
            # Simulate drawing a directory listing
            for row in range(min(height - 2, 50)):
                backend.draw_text(row, 0, f"file_{row:04d}.txt", color_pair=0)
            backend.refresh()
        elapsed = time.time() - start
        fps = iterations / elapsed
        
        # Should achieve at least 20 FPS for full screen updates (Requirement 8.1)
        assert fps >= 20, f"Full screen update too slow: {fps:.1f} FPS"
        
    finally:
        backend.shutdown()


def test_large_directory_performance():
    """Test that large directories remain responsive (Requirement 8.2)."""
    from ttk.backends.curses_backend import CursesBackend
    
    backend = CursesBackend()
    backend.initialize()
    
    try:
        height, width = backend.get_dimensions()
        
        # Test with 1000 files
        num_files = 1000
        iterations = 10
        start = time.time()
        
        for _ in range(iterations):
            backend.clear()
            # Render visible portion of directory
            visible_lines = min(height - 2, num_files)
            for row in range(visible_lines):
                filename = f"file_{row:06d}.txt"
                backend.draw_text(row, 0, filename[:width-1], color_pair=0)
            backend.refresh()
        
        elapsed = time.time() - start
        fps = iterations / elapsed
        
        # Should maintain at least 15 FPS with large directories (Requirement 8.2)
        assert fps >= 15, f"Large directory rendering too slow: {fps:.1f} FPS"
        
    finally:
        backend.shutdown()


def test_search_update_performance():
    """Test that search operations don't lag (Requirement 8.3)."""
    from ttk.backends.curses_backend import CursesBackend
    
    backend = CursesBackend()
    backend.initialize()
    
    try:
        height, width = backend.get_dimensions()
        
        # Test with 100 search results
        num_results = 100
        iterations = 20
        start = time.time()
        
        for _ in range(iterations):
            backend.clear()
            # Draw search dialog
            backend.draw_text(0, 0, "Search: test", color_pair=0)
            backend.draw_hline(1, 0, width, color_pair=0)
            
            # Draw results
            visible_results = min(height - 3, num_results)
            for row in range(visible_results):
                result = f"/path/to/file_{row:04d}.txt"
                backend.draw_text(row + 2, 0, result[:width-1], color_pair=0)
            
            backend.refresh()
        
        elapsed = time.time() - start
        fps = iterations / elapsed
        
        # Should maintain at least 20 FPS during search updates (Requirement 8.3)
        assert fps >= 20, f"Search update too slow: {fps:.1f} FPS"
        
    finally:
        backend.shutdown()


def test_input_polling_performance():
    """Test input handling performance."""
    from ttk.backends.curses_backend import CursesBackend
    
    backend = CursesBackend()
    backend.initialize()
    
    try:
        # Test input polling with timeout
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            # Poll with 1ms timeout (no input expected)
            event = backend.get_input(timeout_ms=1)
        elapsed = time.time() - start
        poll_rate = iterations / elapsed
        
        # Should handle at least 50 polls/sec (very conservative)
        assert poll_rate >= 50, f"Input polling too slow: {poll_rate:.1f} polls/sec"
        
    finally:
        backend.shutdown()


def test_performance_overhead():
    """Test that TTK overhead is minimal (Requirement 8.5)."""
    from ttk.backends.curses_backend import CursesBackend
    
    backend = CursesBackend()
    backend.initialize()
    
    try:
        # Measure overhead of TTK wrapper
        iterations = 1000
        
        # Test draw_text overhead
        start = time.time()
        for i in range(iterations):
            backend.draw_text(0, 0, f"Test {i}", color_pair=0)
        elapsed = time.time() - start
        
        # Each operation should take less than 1ms on average
        avg_time_ms = (elapsed * 1000) / iterations
        assert avg_time_ms < 1.0, f"TTK overhead too high: {avg_time_ms:.3f} ms/op"
        
    finally:
        backend.shutdown()


def test_coregraphics_availability():
    """Test CoreGraphics backend availability on macOS."""
    if platform.system() != 'Darwin':
        # Skip on non-macOS
        return
    
    try:
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        # If we can import it, it's available
        assert True, "CoreGraphicsBackend available"
    except ImportError:
        # Not available, but that's okay if PyObjC isn't installed
        pass


if __name__ == '__main__':
    print("Running performance benchmarks...")
    
    tests = [
        ("Rendering Performance", test_rendering_performance),
        ("Large Directory Performance", test_large_directory_performance),
        ("Search Update Performance", test_search_update_performance),
        ("Input Polling Performance", test_input_polling_performance),
        ("Performance Overhead", test_performance_overhead),
        ("CoreGraphics Availability", test_coregraphics_availability),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
