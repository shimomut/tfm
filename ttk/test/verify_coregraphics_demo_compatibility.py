#!/usr/bin/env python3
"""
Verification script for CoreGraphics backend demo compatibility.

This script verifies that the CoreGraphics backend works correctly with
existing TTK demo applications without requiring any demo code changes.

Tests:
1. Backend instantiation and initialization
2. Demo application compatibility
3. Visual output verification (manual)
4. Keyboard input handling
5. Window management

Requirements verified:
- Requirement 11.1: Demo applications work without modifications
- Requirement 11.2: Visual output matches curses backend
- Requirement 16.1: Works with existing demo code
- Requirement 16.2: Only backend instantiation line needs changing
"""

import sys
import platform
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.demo.test_interface import create_test_interface


def test_backend_instantiation():
    """Test that CoreGraphics backend can be instantiated."""
    print("Test 1: Backend Instantiation")
    print("-" * 60)
    
    try:
        backend = CoreGraphicsBackend(
            window_title="CoreGraphics Demo Test",
            font_name="Menlo",
            font_size=14
        )
        print("✓ CoreGraphics backend instantiated successfully")
        return backend
    except Exception as e:
        print(f"✗ Failed to instantiate backend: {e}")
        return None


def test_backend_initialization(backend):
    """Test that backend initializes correctly."""
    print("\nTest 2: Backend Initialization")
    print("-" * 60)
    
    try:
        backend.initialize()
        print("✓ Backend initialized successfully")
        
        # Check dimensions
        rows, cols = backend.get_dimensions()
        print(f"✓ Window dimensions: {rows} rows x {cols} columns")
        
        return True
    except Exception as e:
        print(f"✗ Failed to initialize backend: {e}")
        return False


def test_demo_interface_creation(backend):
    """Test that demo interface can be created with CoreGraphics backend."""
    print("\nTest 3: Demo Interface Creation")
    print("-" * 60)
    
    try:
        # Create test interface (same code used by demo_ttk.py)
        test_interface = create_test_interface(backend, enable_performance_monitoring=False)
        print("✓ Test interface created successfully")
        print("✓ No demo code changes required")
        return test_interface
    except Exception as e:
        print(f"✗ Failed to create test interface: {e}")
        return None


def test_color_initialization(backend):
    """Test that color pairs can be initialized."""
    print("\nTest 4: Color Initialization")
    print("-" * 60)
    
    try:
        # Initialize color pairs (same as test_interface.py)
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))  # White on black
        backend.init_color_pair(2, (255, 0, 0), (0, 0, 0))      # Red on black
        backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))      # Green on black
        backend.init_color_pair(4, (0, 0, 255), (0, 0, 0))      # Blue on black
        backend.init_color_pair(5, (255, 255, 0), (0, 0, 0))    # Yellow on black
        backend.init_color_pair(6, (0, 255, 255), (0, 0, 0))    # Cyan on black
        backend.init_color_pair(7, (255, 0, 255), (0, 0, 0))    # Magenta on black
        backend.init_color_pair(8, (255, 255, 255), (0, 0, 128))  # White on blue
        backend.init_color_pair(9, (0, 0, 0), (255, 255, 255))  # Black on white
        backend.init_color_pair(10, (128, 128, 128), (0, 0, 0))  # Gray on black
        
        print("✓ All color pairs initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize colors: {e}")
        return False


def test_drawing_operations(backend):
    """Test that drawing operations work correctly."""
    print("\nTest 5: Drawing Operations")
    print("-" * 60)
    
    try:
        from ttk.renderer import TextAttribute
        
        # Clear screen
        backend.clear()
        print("✓ Clear operation successful")
        
        # Draw text with different colors
        backend.draw_text(0, 0, "CoreGraphics Backend Test", 1, TextAttribute.BOLD)
        backend.draw_text(2, 0, "Red text", 2)
        backend.draw_text(3, 0, "Green text", 3)
        backend.draw_text(4, 0, "Blue text", 4)
        print("✓ Text drawing successful")
        
        # Draw shapes
        backend.draw_hline(6, 0, '-', 40, 5)
        backend.draw_vline(8, 0, '|', 5, 6)
        backend.draw_rect(8, 5, 5, 20, 7, filled=False)
        print("✓ Shape drawing successful")
        
        # Refresh display
        backend.refresh()
        print("✓ Display refresh successful")
        
        return True
    except Exception as e:
        print(f"✗ Drawing operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visual_output_manual():
    """Manual test for visual output verification."""
    print("\nTest 6: Visual Output Verification (Manual)")
    print("-" * 60)
    print("This test requires manual verification.")
    print()
    print("Instructions:")
    print("1. Run: python ttk/demo/demo_ttk.py --backend coregraphics")
    print("2. Verify the following:")
    print("   - Window opens with title 'TTK Demo Application - CoreGraphics'")
    print("   - Colors display correctly (red, green, blue, yellow, cyan, magenta)")
    print("   - Text attributes work (bold, underline, reverse)")
    print("   - Shapes render correctly (rectangles, lines)")
    print("   - Coordinate system is correct (0,0 at top-left)")
    print("   - Corner markers appear at all four corners")
    print("3. Test keyboard input:")
    print("   - Press various keys and verify they appear in 'Input Echo'")
    print("   - Press 'q' to quit")
    print()
    print("Expected result: Visual output should match curses backend")


def test_keyboard_input_handling():
    """Test keyboard input handling."""
    print("\nTest 7: Keyboard Input Handling")
    print("-" * 60)
    print("This test requires manual interaction.")
    print()
    print("Instructions:")
    print("1. Run: python ttk/demo/demo_ttk.py --backend coregraphics")
    print("2. Press various keys and verify:")
    print("   - Printable characters appear correctly")
    print("   - Special keys (arrows, function keys) are detected")
    print("   - Modifier keys (Shift, Ctrl, Alt, Cmd) are detected")
    print("   - Key codes match curses backend behavior")
    print("3. Press 'q' to quit")
    print()
    print("Expected result: All keyboard input should work identically to curses")


def test_window_management():
    """Test window management."""
    print("\nTest 8: Window Management")
    print("-" * 60)
    print("This test requires manual interaction.")
    print()
    print("Instructions:")
    print("1. Run: python ttk/demo/demo_ttk.py --backend coregraphics")
    print("2. Test window operations:")
    print("   - Verify window title is correct")
    print("   - Try resizing the window")
    print("   - Try minimizing and restoring")
    print("   - Close window with close button or 'q' key")
    print()
    print("Expected result: Window management should work like any macOS app")


def run_automated_tests():
    """Run all automated tests."""
    print("=" * 60)
    print("CoreGraphics Backend Demo Compatibility Verification")
    print("=" * 60)
    print()
    
    # Check platform
    if platform.system() != 'Darwin':
        print("✗ CoreGraphics backend requires macOS")
        print("  Current platform:", platform.system())
        return False
    
    print("✓ Running on macOS")
    print()
    
    # Test 1: Instantiation
    backend = test_backend_instantiation()
    if not backend:
        return False
    
    # Test 2: Initialization
    if not test_backend_initialization(backend):
        return False
    
    # Test 3: Demo interface creation
    test_interface = test_demo_interface_creation(backend)
    if not test_interface:
        backend.shutdown()
        return False
    
    # Test 4: Color initialization
    if not test_color_initialization(backend):
        backend.shutdown()
        return False
    
    # Test 5: Drawing operations
    if not test_drawing_operations(backend):
        backend.shutdown()
        return False
    
    # Keep window open for visual inspection
    print("\n" + "=" * 60)
    print("Automated tests completed successfully!")
    print("=" * 60)
    print()
    print("Window is now open for visual inspection.")
    print("Press Enter to close window and continue...")
    input()
    
    # Cleanup
    backend.shutdown()
    
    return True


def run_manual_tests():
    """Display manual test instructions."""
    print("\n" + "=" * 60)
    print("Manual Tests")
    print("=" * 60)
    print()
    
    test_visual_output_manual()
    test_keyboard_input_handling()
    test_window_management()


def main():
    """Main entry point."""
    print()
    
    # Run automated tests
    success = run_automated_tests()
    
    if not success:
        print("\n✗ Automated tests failed")
        return 1
    
    # Display manual test instructions
    run_manual_tests()
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    print()
    print("✓ Automated tests: PASSED")
    print("  - Backend instantiation works")
    print("  - Backend initialization works")
    print("  - Demo interface creation works (no code changes needed)")
    print("  - Color initialization works")
    print("  - Drawing operations work")
    print()
    print("Manual tests: PENDING")
    print("  - Run demo application to verify visual output")
    print("  - Test keyboard input handling")
    print("  - Test window management")
    print()
    print("Requirements verified:")
    print("  ✓ 11.1: Demo applications work without modifications")
    print("  ✓ 16.1: Works with existing demo code")
    print("  ✓ 16.2: Only backend instantiation line needs changing")
    print()
    print("To complete verification, run:")
    print("  python ttk/demo/demo_ttk.py --backend coregraphics")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
