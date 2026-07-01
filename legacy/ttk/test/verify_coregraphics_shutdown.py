#!/usr/bin/env python3
"""
Verification script for CoreGraphics backend shutdown functionality.

This script demonstrates that the shutdown() method properly cleans up
all resources and handles errors gracefully.
"""

import sys
from unittest.mock import Mock, MagicMock, patch

# Mock PyObjC modules
sys.modules['Cocoa'] = MagicMock()
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

from ttk.backends.coregraphics_backend import CoreGraphicsBackend


def verify_basic_shutdown():
    """Verify basic shutdown functionality."""
    print("Testing basic shutdown...")
    
    backend = CoreGraphicsBackend()
    # Don't call initialize() - just set up the resources directly
    # backend.initialize()
    
    # Set up some resources
    backend.window = Mock()
    backend.view = Mock()
    backend.font = Mock()
    backend.grid = [[('A', 1, 0), ('B', 1, 0)]]
    backend.color_pairs = {1: ((255, 0, 0), (0, 0, 255))}
    backend.rows = 24
    backend.cols = 80
    backend.char_width = 10
    backend.char_height = 20
    backend.cursor_visible = True
    backend.cursor_row = 5
    backend.cursor_col = 10
    
    # Call shutdown
    backend.shutdown()
    
    # Verify all resources are cleared
    assert backend.window is None, "Window should be None after shutdown"
    assert backend.view is None, "View should be None after shutdown"
    assert backend.font is None, "Font should be None after shutdown"
    assert backend.grid == [], "Grid should be empty after shutdown"
    assert backend.color_pairs == {}, "Color pairs should be empty after shutdown"
    assert backend.rows == 0, "Rows should be 0 after shutdown"
    assert backend.cols == 0, "Cols should be 0 after shutdown"
    assert backend.char_width == 0, "Char width should be 0 after shutdown"
    assert backend.char_height == 0, "Char height should be 0 after shutdown"
    assert backend.cursor_visible is False, "Cursor should be invisible after shutdown"
    assert backend.cursor_row == 0, "Cursor row should be 0 after shutdown"
    assert backend.cursor_col == 0, "Cursor col should be 0 after shutdown"
    
    print("✓ Basic shutdown works correctly")


def verify_error_handling():
    """Verify shutdown handles errors gracefully."""
    print("\nTesting error handling during shutdown...")
    
    backend = CoreGraphicsBackend()
    # Don't call initialize() - just set up the resources directly
    
    # Mock window that raises error on close
    mock_window = Mock()
    mock_window.close.side_effect = RuntimeError("Window already closed")
    backend.window = mock_window
    
    # Shutdown should not raise exception
    try:
        backend.shutdown()
        print("✓ Shutdown handles window close errors gracefully")
    except Exception as e:
        print(f"✗ Shutdown raised exception: {e}")
        return False
    
    # Verify window reference is still cleared despite error
    assert backend.window is None, "Window should be None even after error"
    print("✓ Window reference cleared despite error")
    
    return True


def verify_multiple_shutdowns():
    """Verify shutdown can be called multiple times safely."""
    print("\nTesting multiple shutdown calls...")
    
    backend = CoreGraphicsBackend()
    # Don't call initialize() - just set up the resources directly
    
    # Set up resources
    backend.window = Mock()
    backend.grid = [[('X', 0, 0)]]
    
    # Call shutdown multiple times
    backend.shutdown()
    backend.shutdown()
    backend.shutdown()
    
    # Verify resources remain cleared
    assert backend.window is None, "Window should remain None"
    assert backend.grid == [], "Grid should remain empty"
    
    print("✓ Multiple shutdown calls work safely")


def verify_shutdown_without_initialization():
    """Verify shutdown works even without initialization."""
    print("\nTesting shutdown without initialization...")
    
    backend = CoreGraphicsBackend()
    
    # Shutdown should not raise exception
    try:
        backend.shutdown()
        print("✓ Shutdown works without initialization")
    except Exception as e:
        print(f"✗ Shutdown raised exception: {e}")
        return False
    
    # Verify all resources are cleared
    assert backend.window is None
    assert backend.view is None
    assert backend.grid == []
    
    print("✓ All resources cleared correctly")
    
    return True


def verify_configuration_preservation():
    """Verify shutdown preserves configuration parameters."""
    print("\nTesting configuration preservation...")
    
    backend = CoreGraphicsBackend(
        window_title="Test Window",
        font_name="Monaco",
        font_size=16,
        rows=40,
        cols=120
    )
    # Don't call initialize() - just test configuration preservation
    
    # Call shutdown
    backend.shutdown()
    
    # Verify configuration parameters are preserved
    assert backend.window_title == "Test Window", "Window title should be preserved"
    assert backend.font_name == "Monaco", "Font name should be preserved"
    assert backend.font_size == 16, "Font size should be preserved"
    
    print("✓ Configuration parameters preserved after shutdown")


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("CoreGraphics Backend Shutdown Verification")
    print("=" * 70)
    
    try:
        verify_basic_shutdown()
        verify_error_handling()
        verify_multiple_shutdowns()
        verify_shutdown_without_initialization()
        verify_configuration_preservation()
        
        print("\n" + "=" * 70)
        print("All shutdown verification tests passed! ✓")
        print("=" * 70)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Verification failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
