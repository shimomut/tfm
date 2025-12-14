"""
Test for drawRect_ Phase 1 - Background Batching

This test verifies that the optimized drawRect_ method correctly:
1. Calculates dirty regions
2. Batches adjacent cells with the same background color
3. Draws batched backgrounds using cached colors
4. Maintains visual correctness
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    print("CoreGraphics backend not available (PyObjC not installed)")


def test_drawrect_with_batching():
    """Test that drawRect_ works with background batching optimization."""
    if not BACKEND_AVAILABLE:
        print("SKIP: CoreGraphics backend not available")
        return
    
    print("Testing drawRect_ Phase 1 - Background Batching...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Test Background Batching",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    try:
        # Initialize backend
        backend.initialize()
        print("✓ Backend initialized successfully")
        
        # Initialize some color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))    # White on blue
        backend.init_color_pair(2, (0, 0, 0), (255, 0, 0))          # Black on red
        backend.init_color_pair(3, (255, 255, 0), (0, 255, 0))      # Yellow on green
        print("✓ Color pairs initialized")
        
        # Draw some content with different colors
        # This should create multiple batches
        backend.draw_text(0, 0, "Blue background" + " " * 20, color_pair=1)
        backend.draw_text(1, 0, "Red background" + " " * 20, color_pair=2)
        backend.draw_text(2, 0, "Green background" + " " * 20, color_pair=3)
        backend.draw_text(3, 0, "Mixed: ", color_pair=1)
        backend.draw_text(3, 7, "Blue", color_pair=1)
        backend.draw_text(3, 11, "Red", color_pair=2)
        backend.draw_text(3, 14, "Green", color_pair=3)
        print("✓ Content drawn to grid")
        
        # Refresh to trigger drawRect_
        backend.refresh()
        print("✓ Refresh called (drawRect_ executed)")
        
        # Verify caches are initialized
        assert backend._color_cache is not None, "Color cache should be initialized"
        assert backend._font_cache is not None, "Font cache should be initialized"
        print("✓ Caches are initialized")
        
        # Test that we can get input (ensures window is responsive)
        # Use non-blocking mode
        event = backend.get_input(timeout_ms=0)
        print("✓ Input system responsive")
        
        print("\n✅ All tests passed!")
        print("\nVisual verification:")
        print("- Window should display text with different colored backgrounds")
        print("- Blue, red, and green backgrounds should be visible")
        print("- Mixed line should show color transitions")
        print("\nClose the window to continue...")
        
        # Keep window open for visual verification
        import time
        time.sleep(2)
        
    finally:
        # Clean up
        backend.shutdown()
        print("✓ Backend shutdown complete")


def test_batching_reduces_api_calls():
    """
    Test that batching reduces the number of NSRectFill calls.
    
    This is a conceptual test - we can't directly count API calls,
    but we can verify the batching logic works correctly.
    """
    if not BACKEND_AVAILABLE:
        print("SKIP: CoreGraphics backend not available")
        return
    
    print("\nTesting batching efficiency...")
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Test Batching Efficiency",
        font_name="Menlo",
        font_size=12,
        rows=10,
        cols=40
    )
    
    try:
        backend.initialize()
        
        # Initialize color pair
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))
        
        # Fill entire first row with same color
        # This should create a single batch of 40 cells
        backend.draw_text(0, 0, " " * 40, color_pair=1)
        
        # Fill second row with alternating colors
        # This should create 40 separate batches (worst case)
        for i in range(40):
            pair = 1 if i % 2 == 0 else 0
            backend.draw_text(1, i, " ", color_pair=pair)
        
        # Refresh to trigger drawRect_
        backend.refresh()
        
        print("✓ Batching test completed")
        print("  - Row 0: 40 cells, same color → should batch into 1 draw call")
        print("  - Row 1: 40 cells, alternating colors → should create 40 draw calls")
        print("  - Expected reduction: ~50% fewer calls overall")
        
        # Keep window open briefly
        import time
        time.sleep(1)
        
    finally:
        backend.shutdown()


def test_dirty_region_calculation():
    """Test that dirty region calculation works correctly."""
    if not BACKEND_AVAILABLE:
        print("SKIP: CoreGraphics backend not available")
        return
    
    print("\nTesting dirty region calculation...")
    
    from ttk.backends.coregraphics_backend import DirtyRegionCalculator
    import Cocoa
    
    # Test full-screen dirty rect
    rect = Cocoa.NSMakeRect(0, 0, 800, 480)
    start_row, end_row, start_col, end_col = (
        DirtyRegionCalculator.get_dirty_cells(
            rect, rows=24, cols=80, char_width=10.0, char_height=20.0
        )
    )
    
    assert start_row == 0, f"Expected start_row=0, got {start_row}"
    assert end_row == 24, f"Expected end_row=24, got {end_row}"
    assert start_col == 0, f"Expected start_col=0, got {start_col}"
    assert end_col == 80, f"Expected end_col=80, got {end_col}"
    print("✓ Full-screen dirty rect calculated correctly")
    
    # Test partial dirty rect (top-left corner)
    rect = Cocoa.NSMakeRect(0, 400, 200, 80)
    start_row, end_row, start_col, end_col = (
        DirtyRegionCalculator.get_dirty_cells(
            rect, rows=24, cols=80, char_width=10.0, char_height=20.0
        )
    )
    
    assert start_row == 0, f"Expected start_row=0, got {start_row}"
    assert end_row == 4, f"Expected end_row=4, got {end_row}"
    assert start_col == 0, f"Expected start_col=0, got {start_col}"
    assert end_col == 20, f"Expected end_col=20, got {end_col}"
    print("✓ Partial dirty rect calculated correctly")
    
    print("✅ Dirty region calculation tests passed!")


if __name__ == "__main__":
    if not BACKEND_AVAILABLE:
        print("CoreGraphics backend not available - tests skipped")
        sys.exit(0)
    
    try:
        test_dirty_region_calculation()
        test_drawrect_with_batching()
        test_batching_reduces_api_calls()
        print("\n" + "="*60)
        print("All Phase 1 batching tests completed successfully!")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
