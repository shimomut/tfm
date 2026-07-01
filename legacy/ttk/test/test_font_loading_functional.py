#!/usr/bin/env python3
"""
Functional test for CoreGraphics font loading.

This test actually initializes the backend and verifies that:
1. Font loads successfully
2. Character dimensions are calculated
3. Invalid fonts raise appropriate errors
"""

import sys

# Add current directory to path for imports
sys.path.insert(0, '.')

from backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE


def test_default_font():
    """Test that default Menlo font loads and dimensions are calculated."""
    print("Test 1: Default Font Loading")
    print("-" * 50)
    
    if not COCOA_AVAILABLE:
        print("SKIPPED: PyObjC not available")
        return True
    
    try:
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Check font loaded
        assert backend.font is not None, "Font should be loaded"
        print(f"✓ Font loaded: {backend.font_name}")
        
        # Check dimensions calculated
        assert backend.char_width > 0, "char_width should be positive"
        assert backend.char_height > 0, "char_height should be positive"
        print(f"✓ Character dimensions: {backend.char_width}x{backend.char_height}")
        
        # Check dimensions are integers
        assert isinstance(backend.char_width, int), "char_width should be int"
        assert isinstance(backend.char_height, int), "char_height should be int"
        print(f"✓ Dimensions are integers")
        
        print("PASSED\n")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}\n")
        return False


def test_custom_font():
    """Test that custom Monaco font loads."""
    print("Test 2: Custom Font Loading")
    print("-" * 50)
    
    if not COCOA_AVAILABLE:
        print("SKIPPED: PyObjC not available")
        return True
    
    try:
        backend = CoreGraphicsBackend(font_name="Monaco", font_size=12)
        backend.initialize()
        
        assert backend.font is not None, "Font should be loaded"
        print(f"✓ Custom font loaded: Monaco")
        
        assert backend.char_width > 0, "char_width should be positive"
        assert backend.char_height > 0, "char_height should be positive"
        print(f"✓ Character dimensions: {backend.char_width}x{backend.char_height}")
        
        print("PASSED\n")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}\n")
        return False


def test_invalid_font():
    """Test that invalid font raises ValueError."""
    print("Test 3: Invalid Font Error Handling")
    print("-" * 50)
    
    if not COCOA_AVAILABLE:
        print("SKIPPED: PyObjC not available")
        return True
    
    try:
        backend = CoreGraphicsBackend(font_name="NonExistentFont123")
        
        try:
            backend.initialize()
            print("FAILED: Should have raised ValueError")
            return False
        except ValueError as e:
            error_msg = str(e)
            
            # Check error message is informative
            assert "NonExistentFont123" in error_msg, "Error should mention font name"
            assert "not found" in error_msg.lower(), "Error should say 'not found'"
            assert "monospace" in error_msg.lower(), "Error should mention monospace"
            
            print(f"✓ ValueError raised with informative message:")
            print(f"  '{error_msg}'")
            print("PASSED\n")
            return True
            
    except Exception as e:
        print(f"FAILED: Unexpected error: {e}\n")
        return False


def test_font_size_affects_dimensions():
    """Test that different font sizes produce different dimensions."""
    print("Test 4: Font Size Affects Dimensions")
    print("-" * 50)
    
    if not COCOA_AVAILABLE:
        print("SKIPPED: PyObjC not available")
        return True
    
    try:
        backend_small = CoreGraphicsBackend(font_name="Menlo", font_size=10)
        backend_small.initialize()
        
        backend_large = CoreGraphicsBackend(font_name="Menlo", font_size=20)
        backend_large.initialize()
        
        # Larger font should have larger dimensions
        assert backend_large.char_width > backend_small.char_width, \
            "Larger font should have larger width"
        assert backend_large.char_height > backend_small.char_height, \
            "Larger font should have larger height"
        
        print(f"✓ Small font (10pt): {backend_small.char_width}x{backend_small.char_height}")
        print(f"✓ Large font (20pt): {backend_large.char_width}x{backend_large.char_height}")
        print("PASSED\n")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}\n")
        return False


def test_line_spacing():
    """Test that line spacing is applied (height > font size)."""
    print("Test 5: Line Spacing Applied")
    print("-" * 50)
    
    if not COCOA_AVAILABLE:
        print("SKIPPED: PyObjC not available")
        return True
    
    try:
        backend = CoreGraphicsBackend(font_name="Menlo", font_size=14)
        backend.initialize()
        
        # With 20% line spacing, height should be at least font_size
        # and at most font_size * 2 (reasonable upper bound)
        assert backend.char_height >= backend.font_size, \
            "Height should be at least font size"
        assert backend.char_height <= backend.font_size * 2, \
            "Height should not be more than 2x font size"
        
        print(f"✓ Font size: {backend.font_size}pt")
        print(f"✓ Character height: {backend.char_height}px")
        print(f"✓ Line spacing applied (height >= font size)")
        print("PASSED\n")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}\n")
        return False


def main():
    """Run all functional tests."""
    print("=" * 70)
    print("CoreGraphics Font Loading Functional Tests")
    print("=" * 70)
    print()
    
    if not COCOA_AVAILABLE:
        print("WARNING: PyObjC not available, tests will be skipped")
        print()
    
    tests = [
        test_default_font,
        test_custom_font,
        test_invalid_font,
        test_font_size_affects_dimensions,
        test_line_spacing
    ]
    
    results = [test() for test in tests]
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
