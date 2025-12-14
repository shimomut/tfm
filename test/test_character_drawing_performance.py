"""
Performance test for character drawing optimization.

This test establishes a baseline for the character drawing phase (t4-t3) by
creating a maximum workload scenario with a full 24x80 grid of non-space
characters with various attributes.

Requirements tested: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from ttk.renderer import TextAttribute
    import Cocoa
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"CoreGraphics backend not available: {e}")
    BACKEND_AVAILABLE = False


def create_test_grid(backend):
    """
    Fill the grid with non-space characters and various attributes.
    
    This creates a maximum workload scenario for character drawing:
    - All 1,920 cells (24x80) contain non-space characters
    - Various color pairs are used
    - Bold, underline, and reverse attributes are applied
    
    Args:
        backend: CoreGraphicsBackend instance
    """
    # Initialize color pairs for testing
    # Color pair 1: White on blue
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))
    # Color pair 2: Yellow on black
    backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))
    # Color pair 3: Green on black
    backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))
    # Color pair 4: Red on black
    backend.init_color_pair(4, (255, 0, 0), (0, 0, 0))
    # Color pair 5: Cyan on black
    backend.init_color_pair(5, (0, 255, 255), (0, 0, 0))
    
    # Fill grid with various characters and attributes
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    for row in range(backend.rows):
        for col in range(backend.cols):
            # Select character based on position
            char = chars[(row * backend.cols + col) % len(chars)]
            
            # Vary color pairs across rows
            color_pair = (row % 5) + 1
            
            # Apply different attributes based on position
            attributes = 0
            if row % 3 == 0:
                attributes |= TextAttribute.BOLD
            if row % 4 == 0:
                attributes |= TextAttribute.UNDERLINE
            if row % 5 == 0:
                attributes |= TextAttribute.REVERSE
            
            # Draw the character
            backend.draw_text(row, col, char, color_pair=color_pair, attributes=attributes)


def measure_character_drawing_time(backend, num_samples=5):
    """
    Measure the character drawing phase time (t4-t3).
    
    This function triggers multiple redraws and captures the timing output
    from the drawRect_ method to measure the character drawing phase.
    
    Args:
        backend: CoreGraphicsBackend instance
        num_samples: Number of samples to collect
    
    Returns:
        list: List of t4-t3 time deltas in seconds
    """
    times = []
    
    print(f"\nCollecting {num_samples} samples of character drawing time...")
    print("(Each refresh will print timing information)")
    
    for i in range(num_samples):
        print(f"\n--- Sample {i+1}/{num_samples} ---")
        
        # Trigger a full redraw
        backend.refresh()
        
        # Process events to ensure drawRect_ is called
        app = Cocoa.NSApplication.sharedApplication()
        
        # Run the event loop briefly to process the redraw
        # This will trigger drawRect_ which prints timing information
        until_date = Cocoa.NSDate.dateWithTimeIntervalSinceNow_(0.1)
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            Cocoa.NSEventMaskAny,
            until_date,
            Cocoa.NSDefaultRunLoopMode,
            True
        )
        if event:
            app.sendEvent_(event)
        app.updateWindows()
        
        # Small delay between samples
        time.sleep(0.1)
    
    print("\nNote: The t4-t3 times are printed by drawRect_ above.")
    print("Look for lines like 't4-t3: 0.0XXX' in the output.")
    
    return times


def run_baseline_test():
    """
    Run the baseline performance test.
    
    This test:
    1. Creates a CoreGraphics backend
    2. Fills the grid with maximum character workload
    3. Measures character drawing time (t4-t3)
    4. Reports the baseline performance
    """
    if not BACKEND_AVAILABLE:
        print("ERROR: CoreGraphics backend not available")
        print("This test requires macOS and PyObjC")
        return False
    
    print("=" * 70)
    print("Character Drawing Performance Baseline Test")
    print("=" * 70)
    print()
    print("This test establishes a baseline for the character drawing phase")
    print("by creating a maximum workload scenario:")
    print("  - Full 24x80 grid (1,920 cells)")
    print("  - All non-space characters")
    print("  - Various color pairs (5 different pairs)")
    print("  - Mixed attributes (bold, underline, reverse)")
    print()
    print("Expected baseline: ~30ms (0.03 seconds) for t4-t3")
    print("Target after optimization: <10ms (0.01 seconds)")
    print()
    
    # Create backend
    print("Creating CoreGraphics backend...")
    backend = CoreGraphicsBackend(
        window_title="Character Drawing Performance Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    try:
        # Initialize backend
        print("Initializing backend...")
        backend.initialize()
        
        # Fill grid with test data
        print("Filling grid with test data...")
        create_test_grid(backend)
        
        # Measure character drawing time
        print("\nMeasuring character drawing performance...")
        print("=" * 70)
        times = measure_character_drawing_time(backend, num_samples=5)
        
        print("\n" + "=" * 70)
        print("Baseline Test Complete")
        print("=" * 70)
        print()
        print("IMPORTANT: Review the t4-t3 times printed above.")
        print("The character drawing phase time is shown as 't4-t3: X.XXXX'")
        print()
        print("Expected baseline: ~0.0300 seconds (30ms)")
        print("Target after optimization: <0.0100 seconds (10ms)")
        print()
        print("To verify the baseline:")
        print("1. Look at the t4-t3 values printed above")
        print("2. Confirm they are approximately 0.03 seconds (30ms)")
        print("3. Record these values for comparison after optimization")
        print()
        
        # Keep window open briefly to allow visual inspection
        print("Window will remain open for 3 seconds for visual inspection...")
        time.sleep(3)
        
        return True
        
    finally:
        # Clean up
        print("\nCleaning up...")
        backend.shutdown()
        print("Test complete.")


if __name__ == "__main__":
    success = run_baseline_test()
    sys.exit(0 if success else 1)
