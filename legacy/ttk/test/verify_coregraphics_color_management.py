#!/usr/bin/env python3
"""
Verification script for CoreGraphics backend color pair management.

This script demonstrates and verifies the color pair management functionality
of the CoreGraphics backend, including:
- Storing RGB color pairs
- Validating color pair IDs (1-255)
- Validating RGB components (0-255)
- Retrieving stored color pairs

Run this script to verify that color pair management works correctly.
"""

import sys

# Check if PyObjC is available
try:
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
    print("PyObjC not available - skipping CoreGraphics backend verification")
    print("Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(0)

from ttk.backends.coregraphics_backend import CoreGraphicsBackend


def verify_color_pair_storage():
    """Verify that color pairs are stored correctly."""
    print("Testing color pair storage...")
    
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    # Test storing a single color pair
    backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
    fg, bg = backend.color_pairs[1]
    assert fg == (255, 0, 0), f"Expected (255, 0, 0), got {fg}"
    assert bg == (0, 0, 0), f"Expected (0, 0, 0), got {bg}"
    print("✓ Single color pair stored correctly")
    
    # Test storing multiple color pairs
    test_pairs = {
        2: ((0, 255, 0), (0, 0, 0)),
        3: ((0, 0, 255), (255, 255, 255)),
        100: ((128, 128, 128), (64, 64, 64)),
        255: ((255, 255, 0), (128, 0, 128))
    }
    
    for pair_id, (fg_color, bg_color) in test_pairs.items():
        backend.init_color_pair(pair_id, fg_color, bg_color)
    
    for pair_id, (expected_fg, expected_bg) in test_pairs.items():
        fg, bg = backend.color_pairs[pair_id]
        assert fg == expected_fg, f"Pair {pair_id}: Expected fg {expected_fg}, got {fg}"
        assert bg == expected_bg, f"Pair {pair_id}: Expected bg {expected_bg}, got {bg}"
    
    print("✓ Multiple color pairs stored correctly")
    
    backend.shutdown()


def verify_default_color_pair():
    """Verify that default color pair (0) exists."""
    print("\nTesting default color pair...")
    
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    # Check that color pair 0 exists
    assert 0 in backend.color_pairs, "Default color pair 0 not found"
    
    # Check that it's white on black
    fg, bg = backend.color_pairs[0]
    assert fg == (255, 255, 255), f"Expected white foreground, got {fg}"
    assert bg == (0, 0, 0), f"Expected black background, got {bg}"
    
    print("✓ Default color pair (0) is white on black")
    
    backend.shutdown()


def verify_color_pair_id_validation():
    """Verify that color pair ID validation works."""
    print("\nTesting color pair ID validation...")
    
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    # Test ID too low (0)
    try:
        backend.init_color_pair(0, (255, 255, 255), (0, 0, 0))
        assert False, "Should have raised ValueError for ID 0"
    except ValueError as e:
        assert "Color pair ID must be 1-255" in str(e)
        print("✓ Correctly rejects color pair ID 0")
    
    # Test negative ID
    try:
        backend.init_color_pair(-1, (255, 255, 255), (0, 0, 0))
        assert False, "Should have raised ValueError for negative ID"
    except ValueError as e:
        assert "Color pair ID must be 1-255" in str(e)
        print("✓ Correctly rejects negative color pair ID")
    
    # Test ID too high (256)
    try:
        backend.init_color_pair(256, (255, 255, 255), (0, 0, 0))
        assert False, "Should have raised ValueError for ID 256"
    except ValueError as e:
        assert "Color pair ID must be 1-255" in str(e)
        print("✓ Correctly rejects color pair ID 256")
    
    # Test valid boundary IDs (1 and 255)
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    backend.init_color_pair(255, (0, 0, 0), (255, 255, 255))
    print("✓ Accepts valid boundary IDs (1 and 255)")
    
    backend.shutdown()


def verify_rgb_validation():
    """Verify that RGB component validation works."""
    print("\nTesting RGB component validation...")
    
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    # Test negative RGB in foreground
    try:
        backend.init_color_pair(1, (-1, 255, 255), (0, 0, 0))
        assert False, "Should have raised ValueError for negative RGB"
    except ValueError as e:
        assert "RGB components must be 0-255" in str(e)
        assert "foreground color" in str(e)
        print("✓ Correctly rejects negative RGB in foreground")
    
    # Test RGB > 255 in foreground
    try:
        backend.init_color_pair(1, (256, 255, 255), (0, 0, 0))
        assert False, "Should have raised ValueError for RGB > 255"
    except ValueError as e:
        assert "RGB components must be 0-255" in str(e)
        assert "foreground color" in str(e)
        print("✓ Correctly rejects RGB > 255 in foreground")
    
    # Test negative RGB in background
    try:
        backend.init_color_pair(1, (255, 255, 255), (-1, 0, 0))
        assert False, "Should have raised ValueError for negative RGB"
    except ValueError as e:
        assert "RGB components must be 0-255" in str(e)
        assert "background color" in str(e)
        print("✓ Correctly rejects negative RGB in background")
    
    # Test RGB > 255 in background
    try:
        backend.init_color_pair(1, (255, 255, 255), (256, 0, 0))
        assert False, "Should have raised ValueError for RGB > 255"
    except ValueError as e:
        assert "RGB components must be 0-255" in str(e)
        assert "background color" in str(e)
        print("✓ Correctly rejects RGB > 255 in background")
    
    # Test valid boundary RGB values (0 and 255)
    backend.init_color_pair(1, (0, 0, 0), (0, 0, 0))
    backend.init_color_pair(2, (255, 255, 255), (255, 255, 255))
    print("✓ Accepts valid boundary RGB values (0 and 255)")
    
    backend.shutdown()


def verify_color_pair_overwrite():
    """Verify that color pairs can be overwritten."""
    print("\nTesting color pair overwrite...")
    
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    # Initialize a color pair
    backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
    fg, bg = backend.color_pairs[1]
    assert fg == (255, 0, 0)
    assert bg == (0, 0, 0)
    
    # Overwrite with different colors
    backend.init_color_pair(1, (0, 255, 0), (255, 255, 255))
    fg, bg = backend.color_pairs[1]
    assert fg == (0, 255, 0), f"Expected (0, 255, 0), got {fg}"
    assert bg == (255, 255, 255), f"Expected (255, 255, 255), got {bg}"
    
    print("✓ Color pairs can be overwritten")
    
    backend.shutdown()


def verify_all_valid_ids():
    """Verify that all valid color pair IDs (1-255) can be initialized."""
    print("\nTesting all valid color pair IDs...")
    
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    # Initialize all valid IDs
    for pair_id in range(1, 256):
        r = pair_id % 256
        g = (pair_id * 2) % 256
        b = (pair_id * 3) % 256
        backend.init_color_pair(pair_id, (r, g, b), (255 - r, 255 - g, 255 - b))
    
    # Verify all were stored
    for pair_id in range(1, 256):
        assert pair_id in backend.color_pairs, f"Color pair {pair_id} not found"
    
    # Verify total count (0-255 = 256 pairs)
    assert len(backend.color_pairs) == 256, f"Expected 256 pairs, got {len(backend.color_pairs)}"
    
    print("✓ All 255 valid color pair IDs can be initialized")
    print(f"✓ Total color pairs stored: {len(backend.color_pairs)} (including default)")
    
    backend.shutdown()


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("CoreGraphics Backend Color Pair Management Verification")
    print("=" * 70)
    
    try:
        verify_color_pair_storage()
        verify_default_color_pair()
        verify_color_pair_id_validation()
        verify_rgb_validation()
        verify_color_pair_overwrite()
        verify_all_valid_ids()
        
        print("\n" + "=" * 70)
        print("✓ All color pair management verifications passed!")
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
