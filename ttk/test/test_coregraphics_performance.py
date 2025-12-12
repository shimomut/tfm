#!/usr/bin/env python3
"""
Performance tests for CoreGraphics backend.

Tests rendering performance to ensure the CoreGraphics backend meets
performance requirements specified in Requirement 10.5.

Requirements tested:
- 10.5: Full 80x24 grid redraw completes in under 10 milliseconds
"""

import time
import unittest
import sys
import platform

# Skip all tests if not on macOS
if platform.system() != 'Darwin':
    raise unittest.SkipTest("CoreGraphics backend only available on macOS")

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    COREGRAPHICS_AVAILABLE = True
except ImportError:
    COREGRAPHICS_AVAILABLE = False


@unittest.skipUnless(COREGRAPHICS_AVAILABLE, "CoreGraphics backend not available")
class TestCoreGraphicsPerformance(unittest.TestCase):
    """Test cases for CoreGraphics backend performance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = None
    
    def tearDown(self):
        """Clean up after tests."""
        if self.backend:
            try:
                self.backend.shutdown()
            except Exception:
                pass
    
    def test_80x24_grid_render_time(self):
        """Test that 80x24 grid renders in under 10ms (Requirement 10.5)."""
        # Create backend with standard 80x24 grid
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize some color pairs
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        self.backend.init_color_pair(2, (255, 0, 0), (0, 0, 0))
        self.backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))
        
        # Fill the entire grid with text
        for row in range(24):
            for col in range(80):
                char = chr(65 + (col % 26))  # A-Z cycling
                color_pair = 1 + (row % 3)
                self.backend.draw_text(row, col, char, color_pair=color_pair)
        
        # Measure rendering time
        start_time = time.perf_counter()
        self.backend.refresh()
        end_time = time.perf_counter()
        
        render_time_ms = (end_time - start_time) * 1000
        
        # Verify rendering completes in under 10ms
        self.assertLess(
            render_time_ms,
            10.0,
            f"80x24 grid rendering took {render_time_ms:.2f}ms, "
            f"exceeds 10ms requirement"
        )
        
        print(f"\n80x24 grid render time: {render_time_ms:.2f}ms")
    
    def test_multiple_renders_consistency(self):
        """Test that multiple renders maintain consistent performance."""
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Fill grid
        for row in range(24):
            for col in range(80):
                self.backend.draw_text(row, col, "X", color_pair=1)
        
        # Measure multiple renders
        render_times = []
        for i in range(10):
            start_time = time.perf_counter()
            self.backend.refresh()
            end_time = time.perf_counter()
            render_times.append((end_time - start_time) * 1000)
        
        # All renders should be under 10ms
        for i, render_time in enumerate(render_times):
            self.assertLess(
                render_time,
                10.0,
                f"Render {i+1} took {render_time:.2f}ms, exceeds 10ms requirement"
            )
        
        avg_time = sum(render_times) / len(render_times)
        max_time = max(render_times)
        min_time = min(render_times)
        
        print(f"\nMultiple render statistics:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
    
    def test_200x60_grid_performance(self):
        """Test performance with larger 200x60 grid."""
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=60,
            cols=200
        )
        self.backend.initialize()
        
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Fill the entire grid
        for row in range(60):
            for col in range(200):
                self.backend.draw_text(row, col, "A", color_pair=1)
        
        # Measure rendering time
        start_time = time.perf_counter()
        self.backend.refresh()
        end_time = time.perf_counter()
        
        render_time_ms = (end_time - start_time) * 1000
        
        # For larger grids, we expect longer render times but should still be reasonable
        # Let's say under 50ms for a grid 15x larger than 80x24
        self.assertLess(
            render_time_ms,
            50.0,
            f"200x60 grid rendering took {render_time_ms:.2f}ms, "
            f"exceeds 50ms threshold"
        )
        
        print(f"\n200x60 grid render time: {render_time_ms:.2f}ms")
    
    def test_sparse_grid_performance(self):
        """Test performance with sparse grid (few characters)."""
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Only draw a few characters (sparse grid)
        self.backend.draw_text(0, 0, "Hello", color_pair=1)
        self.backend.draw_text(23, 75, "World", color_pair=1)
        
        # Measure rendering time
        start_time = time.perf_counter()
        self.backend.refresh()
        end_time = time.perf_counter()
        
        render_time_ms = (end_time - start_time) * 1000
        
        # Sparse grids should render very quickly
        self.assertLess(
            render_time_ms,
            5.0,
            f"Sparse grid rendering took {render_time_ms:.2f}ms, "
            f"exceeds 5ms threshold"
        )
        
        print(f"\nSparse grid render time: {render_time_ms:.2f}ms")
    
    def test_full_grid_with_attributes(self):
        """Test performance with text attributes (bold, underline)."""
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Fill grid with attributed text
        from ttk.renderer import TextAttribute
        for row in range(24):
            for col in range(80):
                attrs = 0
                if row % 3 == 0:
                    attrs |= TextAttribute.BOLD
                if row % 3 == 1:
                    attrs |= TextAttribute.UNDERLINE
                if row % 3 == 2:
                    attrs |= TextAttribute.REVERSE
                
                self.backend.draw_text(row, col, "X", color_pair=1, attributes=attrs)
        
        # Measure rendering time
        start_time = time.perf_counter()
        self.backend.refresh()
        end_time = time.perf_counter()
        
        render_time_ms = (end_time - start_time) * 1000
        
        # Attributes may add some overhead, but should still be under 15ms
        self.assertLess(
            render_time_ms,
            15.0,
            f"Attributed text rendering took {render_time_ms:.2f}ms, "
            f"exceeds 15ms threshold"
        )
        
        print(f"\nAttributed text render time: {render_time_ms:.2f}ms")
    
    def test_clear_performance(self):
        """Test performance of clear operation."""
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize color pair and fill grid
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        for row in range(24):
            for col in range(80):
                self.backend.draw_text(row, col, "X", color_pair=1)
        
        # Measure clear operation time
        start_time = time.perf_counter()
        self.backend.clear()
        end_time = time.perf_counter()
        
        clear_time_ms = (end_time - start_time) * 1000
        
        # Clear should be very fast (just resetting grid cells)
        self.assertLess(
            clear_time_ms,
            1.0,
            f"Clear operation took {clear_time_ms:.2f}ms, exceeds 1ms threshold"
        )
        
        print(f"\nClear operation time: {clear_time_ms:.2f}ms")
    
    def test_partial_update_performance(self):
        """Test performance of partial grid updates."""
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Fill grid initially
        for row in range(24):
            for col in range(80):
                self.backend.draw_text(row, col, ".", color_pair=1)
        self.backend.refresh()
        
        # Update only a small region (10x10)
        for row in range(10):
            for col in range(10):
                self.backend.draw_text(row, col, "X", color_pair=1)
        
        # Measure rendering time for partial update
        start_time = time.perf_counter()
        self.backend.refresh()
        end_time = time.perf_counter()
        
        render_time_ms = (end_time - start_time) * 1000
        
        # Partial updates still render full grid, but should be fast
        self.assertLess(
            render_time_ms,
            10.0,
            f"Partial update rendering took {render_time_ms:.2f}ms, "
            f"exceeds 10ms requirement"
        )
        
        print(f"\nPartial update render time: {render_time_ms:.2f}ms")


@unittest.skipUnless(COREGRAPHICS_AVAILABLE, "CoreGraphics backend not available")
class TestCoreGraphicsPerformanceProfile(unittest.TestCase):
    """Profiling tests for CoreGraphics backend performance analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = None
    
    def tearDown(self):
        """Clean up after tests."""
        if self.backend:
            try:
                self.backend.shutdown()
            except Exception:
                pass
    
    def test_render_time_breakdown(self):
        """Profile different aspects of rendering performance."""
        self.backend = CoreGraphicsBackend(
            window_title="Performance Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.backend.initialize()
        
        # Initialize color pairs
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Test 1: Empty grid
        start = time.perf_counter()
        self.backend.refresh()
        empty_time = (time.perf_counter() - start) * 1000
        
        # Test 2: Single character
        self.backend.draw_text(0, 0, "X", color_pair=1)
        start = time.perf_counter()
        self.backend.refresh()
        single_char_time = (time.perf_counter() - start) * 1000
        
        # Test 3: Full line
        for col in range(80):
            self.backend.draw_text(0, col, "X", color_pair=1)
        start = time.perf_counter()
        self.backend.refresh()
        full_line_time = (time.perf_counter() - start) * 1000
        
        # Test 4: Full grid
        for row in range(24):
            for col in range(80):
                self.backend.draw_text(row, col, "X", color_pair=1)
        start = time.perf_counter()
        self.backend.refresh()
        full_grid_time = (time.perf_counter() - start) * 1000
        
        print(f"\nRender time breakdown:")
        print(f"  Empty grid: {empty_time:.2f}ms")
        print(f"  Single character: {single_char_time:.2f}ms")
        print(f"  Full line (80 chars): {full_line_time:.2f}ms")
        print(f"  Full grid (1920 chars): {full_grid_time:.2f}ms")
        
        # Verify full grid meets requirement
        self.assertLess(full_grid_time, 10.0)


if __name__ == '__main__':
    unittest.main()
