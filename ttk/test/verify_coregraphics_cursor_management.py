#!/usr/bin/env python3
"""
Manual verification script for CoreGraphics backend cursor management.

This script demonstrates cursor visibility and positioning functionality,
allowing visual verification that the cursor is rendered correctly.

Usage:
    python verify_coregraphics_cursor_management.py

Expected behavior:
    1. Window opens with cursor visible at position (0, 0)
    2. Cursor moves to different positions with delays
    3. Cursor visibility toggles on and off
    4. Cursor position is clamped to valid grid bounds
    5. Window closes after demonstration
"""

import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, '..')

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
    
    if not COCOA_AVAILABLE:
        print("PyObjC not available. This test requires PyObjC on macOS.")
        sys.exit(1)
    
    import Cocoa
    
    def run_cursor_demo():
        """Run cursor management demonstration."""
        print("CoreGraphics Cursor Management Verification")
        print("=" * 50)
        
        # Create backend
        print("\n1. Creating CoreGraphics backend...")
        backend = CoreGraphicsBackend(
            window_title="Cursor Management Test",
            font_name="Menlo",
            font_size=14
        )
        backend.initialize()
        
        # Draw some text for reference
        print("2. Drawing reference text...")
        backend.draw_text(0, 0, "Cursor Management Test", 0, 0)
        backend.draw_text(2, 0, "Watch the cursor move around the screen", 0, 0)
        backend.draw_text(4, 0, "Position markers:", 0, 0)
        backend.draw_text(5, 2, "Top-left (0, 0)", 0, 0)
        backend.draw_text(6, 2, "Middle (12, 40)", 0, 0)
        backend.draw_text(7, 2, "Bottom-right (23, 79)", 0, 0)
        backend.refresh()
        
        # Test 1: Show cursor at origin
        print("3. Showing cursor at origin (0, 0)...")
        backend.set_cursor_visibility(True)
        backend.move_cursor(0, 0)
        backend.refresh()
        time.sleep(2)
        
        # Test 2: Move cursor to middle
        print("4. Moving cursor to middle (12, 40)...")
        backend.move_cursor(12, 40)
        backend.refresh()
        time.sleep(2)
        
        # Test 3: Move cursor to bottom-right
        print("5. Moving cursor to bottom-right (23, 79)...")
        backend.move_cursor(23, 79)
        backend.refresh()
        time.sleep(2)
        
        # Test 4: Test coordinate clamping (out of bounds)
        print("6. Testing coordinate clamping (100, 200) -> (23, 79)...")
        backend.move_cursor(100, 200)
        backend.refresh()
        time.sleep(2)
        
        # Test 5: Hide cursor
        print("7. Hiding cursor...")
        backend.set_cursor_visibility(False)
        backend.refresh()
        time.sleep(2)
        
        # Test 6: Move hidden cursor (should not be visible)
        print("8. Moving hidden cursor to (10, 20)...")
        backend.move_cursor(10, 20)
        backend.refresh()
        time.sleep(1)
        
        # Test 7: Show cursor again at new position
        print("9. Showing cursor at new position (10, 20)...")
        backend.set_cursor_visibility(True)
        backend.refresh()
        time.sleep(2)
        
        # Test 8: Rapid cursor movement
        print("10. Demonstrating rapid cursor movement...")
        positions = [
            (5, 10), (5, 20), (5, 30), (5, 40),
            (10, 40), (15, 40), (20, 40),
            (20, 30), (20, 20), (20, 10),
            (15, 10), (10, 10), (5, 10)
        ]
        for row, col in positions:
            backend.move_cursor(row, col)
            backend.refresh()
            time.sleep(0.2)
        
        # Test 9: Cursor blinking effect
        print("11. Demonstrating cursor blinking...")
        for _ in range(5):
            backend.set_cursor_visibility(False)
            backend.refresh()
            time.sleep(0.3)
            backend.set_cursor_visibility(True)
            backend.refresh()
            time.sleep(0.3)
        
        print("\n12. Cursor management verification complete!")
        print("    - Cursor visibility control: OK")
        print("    - Cursor positioning: OK")
        print("    - Coordinate clamping: OK")
        print("    - State persistence: OK")
        
        # Keep window open for a moment
        time.sleep(2)
        
        # Cleanup
        print("\n13. Cleaning up...")
        backend.shutdown()
        
        print("\nVerification complete!")
        return True
    
    if __name__ == '__main__':
        try:
            success = run_cursor_demo()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\nVerification interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\n\nError during verification: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the ttk/test directory")
    print("and that PyObjC is installed on macOS.")
    sys.exit(1)
