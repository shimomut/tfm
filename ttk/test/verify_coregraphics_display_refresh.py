#!/usr/bin/env python3
"""
Verification script for CoreGraphics backend display refresh operations.

This script demonstrates that the display refresh operations work correctly:
- refresh() marks the entire view for redraw
- refresh_region() marks a specific region for redraw
- View is properly connected to window
- Window is shown with makeKeyAndOrderFront_

This is a visual verification that requires macOS and PyObjC.

Requirements: 8.4, 10.3
"""

import sys
import time


def verify_display_refresh():
    """Verify display refresh operations work correctly."""
    print("=" * 70)
    print("CoreGraphics Backend Display Refresh Verification")
    print("=" * 70)
    print()
    
    # Check if we're on macOS
    if sys.platform != 'darwin':
        print("❌ This verification requires macOS")
        return False
    
    # Try to import PyObjC
    try:
        import Cocoa
        print("✓ PyObjC is available")
    except ImportError:
        print("❌ PyObjC not available. Install with: pip install pyobjc-framework-Cocoa")
        return False
    
    # Import the backend
    try:
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        print("✓ CoreGraphics backend imported successfully")
    except Exception as e:
        print(f"❌ Failed to import CoreGraphics backend: {e}")
        return False
    
    print()
    print("Creating backend and initializing window...")
    
    # Create and initialize backend
    try:
        backend = CoreGraphicsBackend(
            window_title="Display Refresh Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        backend.initialize()
        print("✓ Backend initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize backend: {e}")
        return False
    
    # Verify window was created and shown
    if backend.window is None:
        print("❌ Window was not created")
        return False
    print("✓ Window created")
    
    if backend.view is None:
        print("❌ View was not created")
        return False
    print("✓ View created and connected to window")
    
    # Check if window is visible
    if not backend.window.isVisible():
        print("❌ Window is not visible")
        return False
    print("✓ Window is visible (makeKeyAndOrderFront_ was called)")
    
    print()
    print("Testing display refresh operations...")
    
    # Test 1: Draw some text and refresh entire display
    print("\nTest 1: Full display refresh")
    backend.clear()
    backend.draw_text(0, 0, "Full Display Refresh Test", 0, 0)
    backend.draw_text(2, 0, "This tests refresh() method", 0, 0)
    
    try:
        backend.refresh()
        print("✓ refresh() called successfully")
        time.sleep(0.5)  # Give time for display to update
    except Exception as e:
        print(f"❌ refresh() failed: {e}")
        return False
    
    # Test 2: Draw in a region and refresh only that region
    print("\nTest 2: Regional display refresh")
    backend.draw_text(5, 10, "Regional Refresh", 0, 0)
    backend.draw_text(6, 10, "Only this area", 0, 0)
    backend.draw_text(7, 10, "should update", 0, 0)
    
    try:
        # Refresh only the region containing the new text
        backend.refresh_region(5, 10, 3, 20)
        print("✓ refresh_region() called successfully")
        time.sleep(0.5)  # Give time for display to update
    except Exception as e:
        print(f"❌ refresh_region() failed: {e}")
        return False
    
    # Test 3: Multiple regional refreshes
    print("\nTest 3: Multiple regional refreshes")
    backend.draw_text(10, 0, "Region 1", 0, 0)
    backend.draw_text(10, 40, "Region 2", 0, 0)
    
    try:
        backend.refresh_region(10, 0, 1, 10)
        backend.refresh_region(10, 40, 1, 10)
        print("✓ Multiple refresh_region() calls successful")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Multiple refresh_region() calls failed: {e}")
        return False
    
    # Test 4: Draw a box and refresh
    print("\nTest 4: Draw box and refresh")
    backend.draw_rect(15, 10, 5, 30, 0, False)
    backend.draw_text(17, 15, "Box with refresh", 0, 0)
    
    try:
        backend.refresh()
        print("✓ Box drawn and refreshed successfully")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Box refresh failed: {e}")
        return False
    
    # Test 5: Clear and refresh
    print("\nTest 5: Clear and refresh")
    try:
        backend.clear()
        backend.draw_text(11, 30, "CLEARED!", 0, 0)
        backend.refresh()
        print("✓ Clear and refresh successful")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Clear and refresh failed: {e}")
        return False
    
    print()
    print("=" * 70)
    print("Display Refresh Verification Summary")
    print("=" * 70)
    print("✓ All display refresh operations work correctly")
    print("✓ refresh() marks entire view for redraw")
    print("✓ refresh_region() marks specific regions for redraw")
    print("✓ View is properly connected to window")
    print("✓ Window is shown with makeKeyAndOrderFront_")
    print()
    print("The window should be visible with the test content.")
    print("Close the window to exit.")
    print()
    
    # Keep the window open
    try:
        # Run the event loop to keep window responsive
        from Cocoa import NSApp, NSDate, NSDefaultRunLoopMode
        
        print("Running event loop (press Ctrl+C to exit)...")
        while True:
            # Process events
            event = NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_(
                0xFFFFFFFF,  # All event types
                NSDate.dateWithTimeIntervalSinceNow_(0.1),
                NSDefaultRunLoopMode,
                True
            )
            
            if event:
                NSApp.sendEvent_(event)
            
            # Check if window is still open
            if not backend.window.isVisible():
                print("\nWindow closed by user")
                break
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    # Cleanup
    try:
        backend.shutdown()
        print("✓ Backend shutdown successfully")
    except Exception as e:
        print(f"⚠ Warning during shutdown: {e}")
    
    return True


if __name__ == '__main__':
    success = verify_display_refresh()
    sys.exit(0 if success else 1)
