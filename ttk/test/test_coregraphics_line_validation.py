#!/usr/bin/env python3
"""
Test validation of single-character constraint in draw_hline and draw_vline.

This test verifies that draw_hline() and draw_vline() properly validate
that the char parameter is a single character, which allows us to avoid
NFD normalization in _is_wide_character().
"""

import sys
import os
import unicodedata

# Add ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backends.coregraphics_backend import CoreGraphicsBackend


def test_draw_hline_single_char_validation():
    """Test that draw_hline validates char is a single character."""
    print("Testing draw_hline single character validation...")
    backend = CoreGraphicsBackend(rows=24, cols=80)
    
    # Valid single character should work
    try:
        backend.draw_hline(0, 0, '-', 10)
        print("  ✓ Single character accepted")
    except ValueError as e:
        print(f"  ✗ FAIL: Single character rejected: {e}")
        return False
    
    # Multi-character string should raise ValueError
    try:
        backend.draw_hline(0, 0, '--', 10)
        print("  ✗ FAIL: Multi-character string accepted")
        return False
    except ValueError:
        print("  ✓ Multi-character string rejected")
    
    # Empty string should raise ValueError
    try:
        backend.draw_hline(0, 0, '', 10)
        print("  ✗ FAIL: Empty string accepted")
        return False
    except ValueError:
        print("  ✓ Empty string rejected")
    
    return True


def test_draw_vline_single_char_validation():
    """Test that draw_vline validates char is a single character."""
    print("Testing draw_vline single character validation...")
    backend = CoreGraphicsBackend(rows=24, cols=80)
    
    # Valid single character should work
    try:
        backend.draw_vline(0, 0, '|', 10)
        print("  ✓ Single character accepted")
    except ValueError as e:
        print(f"  ✗ FAIL: Single character rejected: {e}")
        return False
    
    # Multi-character string should raise ValueError
    try:
        backend.draw_vline(0, 0, '||', 10)
        print("  ✗ FAIL: Multi-character string accepted")
        return False
    except ValueError:
        print("  ✓ Multi-character string rejected")
    
    # Empty string should raise ValueError
    try:
        backend.draw_vline(0, 0, '', 10)
        print("  ✗ FAIL: Empty string accepted")
        return False
    except ValueError:
        print("  ✓ Empty string rejected")
    
    return True


def test_draw_hline_with_wide_char():
    """Test that draw_hline works with wide characters."""
    print("Testing draw_hline with wide characters...")
    backend = CoreGraphicsBackend(rows=24, cols=80)
    
    # Wide character should work (single character, even if wide)
    try:
        backend.draw_hline(0, 0, '─', 10)  # Box drawing character
        backend.draw_hline(1, 0, '━', 10)  # Heavy box drawing
        backend.draw_hline(2, 0, '═', 10)  # Double box drawing
        print("  ✓ Wide single characters accepted")
        return True
    except ValueError as e:
        print(f"  ✗ FAIL: Wide character rejected: {e}")
        return False


def test_draw_vline_with_wide_char():
    """Test that draw_vline works with wide characters."""
    print("Testing draw_vline with wide characters...")
    backend = CoreGraphicsBackend(rows=24, cols=80)
    
    # Wide character should work (single character, even if wide)
    try:
        backend.draw_vline(0, 0, '│', 10)  # Box drawing character
        backend.draw_vline(0, 1, '┃', 10)  # Heavy box drawing
        backend.draw_vline(0, 2, '║', 10)  # Double box drawing
        print("  ✓ Wide single characters accepted")
        return True
    except ValueError as e:
        print(f"  ✗ FAIL: Wide character rejected: {e}")
        return False


def test_nfd_char_rejected():
    """Test that NFD-decomposed characters are rejected (length > 1)."""
    print("Testing NFD character rejection...")
    backend = CoreGraphicsBackend(rows=24, cols=80)
    
    # Create NFD character (decomposed)
    char_nfd = unicodedata.normalize('NFD', 'が')  # Length will be 2
    
    # Should be rejected because length > 1
    try:
        backend.draw_hline(0, 0, char_nfd, 10)
        print("  ✗ FAIL: NFD character accepted in draw_hline")
        return False
    except ValueError:
        print("  ✓ NFD character rejected in draw_hline")
    
    try:
        backend.draw_vline(0, 0, char_nfd, 10)
        print("  ✗ FAIL: NFD character accepted in draw_vline")
        return False
    except ValueError:
        print("  ✓ NFD character rejected in draw_vline")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CoreGraphics Line Drawing Validation Tests")
    print("=" * 60 + "\n")
    
    tests = [
        ("draw_hline validation", test_draw_hline_single_char_validation),
        ("draw_vline validation", test_draw_vline_single_char_validation),
        ("draw_hline wide chars", test_draw_hline_with_wide_char),
        ("draw_vline wide chars", test_draw_vline_with_wide_char),
        ("NFD rejection", test_nfd_char_rejected),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
