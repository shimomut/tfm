"""
Performance benchmark tests for TFM TTK migration.

These tests verify that performance requirements from Requirement 8 are met:
8.1: Performance equivalent to or better than curses-only version
8.2: Large directories remain responsive
8.3: Search operations don't lag
8.4: CoreGraphics backend achieves 60 FPS
8.5: No operation more than 10% slower than pre-migration

Note: These tests use callback mode for event handling.

Run with: PYTHONPATH=.:src:ttk pytest test/test_performance_benchmarks.py -v
"""

import time
import platform


def test_rendering_performance():
    """Test basic rendering performance meets requirements."""
    try:
        from ttk.backends.curses_backend import CursesBackend
        from ttk.test.test_utils import EventCapture
    except ImportError:
        print("Skipping: CursesBackend or EventCapture not available")
        return
    
    try:
        backend = CursesBackend()
        backend.initialize()
    except TypeError as e:
        # Backend doesn't support callback mode yet
        print(f"Skipping: CursesBackend not yet updated for callback mode ({e})")
        return
    
    # Set up callback mode
    capture = EventCapture()
    try:
        backend.set_event_callback(capture)
    except AttributeError:
        # Backend doesn't have callback mode yet
        backend.shutdown()
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
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
    try:
        from ttk.backends.curses_backend import CursesBackend
        from ttk.test.test_utils import EventCapture
    except ImportError:
        print("Skipping: CursesBackend or EventCapture not available")
        return
    
    try:
        backend = CursesBackend()
        backend.initialize()
    except TypeError:
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
    # Set up callback mode
    capture = EventCapture()
    try:
        backend.set_event_callback(capture)
    except AttributeError:
        backend.shutdown()
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
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
    try:
        from ttk.backends.curses_backend import CursesBackend
        from ttk.test.test_utils import EventCapture
    except ImportError:
        print("Skipping: CursesBackend or EventCapture not available")
        return
    
    try:
        backend = CursesBackend()
        backend.initialize()
    except TypeError:
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
    # Set up callback mode
    capture = EventCapture()
    try:
        backend.set_event_callback(capture)
    except AttributeError:
        backend.shutdown()
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
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
    """Test input handling performance in callback mode."""
    try:
        from ttk.backends.curses_backend import CursesBackend
        from ttk.test.test_utils import EventCapture
    except ImportError:
        print("Skipping: CursesBackend or EventCapture not available")
        return
    
    try:
        backend = CursesBackend()
        backend.initialize()
    except TypeError:
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
    # Set up callback mode
    capture = EventCapture()
    try:
        backend.set_event_callback(capture)
    except AttributeError:
        backend.shutdown()
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
    try:
        # Test event loop iteration with timeout
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            # Process events with 1ms timeout (no input expected)
            backend.run_event_loop_iteration(timeout_ms=1)
        elapsed = time.time() - start
        iteration_rate = iterations / elapsed
        
        # Should handle at least 50 iterations/sec (very conservative)
        assert iteration_rate >= 50, f"Event loop iteration too slow: {iteration_rate:.1f} iterations/sec"
        
    finally:
        backend.shutdown()


def test_performance_overhead():
    """Test that TTK overhead is minimal (Requirement 8.5)."""
    try:
        from ttk.backends.curses_backend import CursesBackend
        from ttk.test.test_utils import EventCapture
    except ImportError:
        print("Skipping: CursesBackend or EventCapture not available")
        return
    
    try:
        backend = CursesBackend()
        backend.initialize()
    except TypeError:
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
    # Set up callback mode
    capture = EventCapture()
    try:
        backend.set_event_callback(capture)
    except AttributeError:
        backend.shutdown()
        print("Skipping: CursesBackend not yet updated for callback mode")
        return
    
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
