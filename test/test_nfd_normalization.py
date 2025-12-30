#!/usr/bin/env python3
"""
Test NFD normalization handling for macOS filenames.

This test verifies that TFM correctly handles NFD (Normalization Form D)
filenames from macOS filesystems, where characters like "が" are decomposed
into base character + combining mark.
"""

import sys
import os
import unicodedata

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_wide_char_utils import get_display_width, _is_wide_character


def test_nfd_vs_nfc_width_calculation():
    """Test that NFD and NFC forms have the same display width."""
    
    # Test cases with Japanese characters that are commonly decomposed on macOS
    test_cases = [
        ("が", "hiragana GA with dakuten"),
        ("ぎ", "hiragana GI with dakuten"),
        ("ぐ", "hiragana GU with dakuten"),
        ("げ", "hiragana GE with dakuten"),
        ("ご", "hiragana GO with dakuten"),
        ("ざ", "hiragana ZA with dakuten"),
        ("パ", "katakana PA with handakuten"),
        ("ピ", "katakana PI with handakuten"),
    ]
    
    print("Testing NFD vs NFC width calculation:")
    print("=" * 60)
    
    all_passed = True
    
    for char_nfc, description in test_cases:
        # Create NFD version (decomposed)
        char_nfd = unicodedata.normalize('NFD', char_nfc)
        
        # Get display widths
        width_nfc = get_display_width(char_nfc)
        width_nfd = get_display_width(char_nfd)
        
        # Both should be 2 (wide character)
        passed = (width_nfc == 2 and width_nfd == 2)
        status = "✓ PASS" if passed else "✗ FAIL"
        
        print(f"{status} {description}:")
        print(f"  NFC: '{char_nfc}' (len={len(char_nfc)}) -> width={width_nfc}")
        print(f"  NFD: '{char_nfd}' (len={len(char_nfd)}) -> width={width_nfd}")
        
        if not passed:
            all_passed = False
            print(f"  ERROR: Expected width=2 for both forms")
        print()
    
    return all_passed


def test_nfd_is_wide_character():
    """Test that _is_wide_character works correctly with NFD forms."""
    
    print("Testing _is_wide_character with NFD:")
    print("=" * 60)
    
    # Test character
    char_nfc = "が"
    char_nfd = unicodedata.normalize('NFD', char_nfc)
    
    # Check if recognized as wide
    is_wide_nfc = _is_wide_character(char_nfc)
    is_wide_nfd = _is_wide_character(char_nfd)
    
    print(f"NFC '{char_nfc}' (len={len(char_nfc)}): is_wide={is_wide_nfc}")
    print(f"NFD '{char_nfd}' (len={len(char_nfd)}): is_wide={is_wide_nfd}")
    
    # Note: NFD form has length > 1, so _is_wide_character returns False
    # This is expected - the normalization happens in get_display_width
    passed = is_wide_nfc == True
    
    if passed:
        print("✓ PASS: NFC form correctly identified as wide")
    else:
        print("✗ FAIL: NFC form not identified as wide")
    
    print()
    return passed


def test_mixed_nfd_nfc_string():
    """Test strings with mixed NFD and NFC characters."""
    
    print("Testing mixed NFD/NFC strings:")
    print("=" * 60)
    
    # Create a string with both NFC and NFD characters
    nfc_part = "こんにちは"  # NFC
    nfd_part = unicodedata.normalize('NFD', "がぎぐげご")  # NFD
    mixed_string = nfc_part + nfd_part
    
    # Calculate width
    width = get_display_width(mixed_string)
    expected_width = 20  # 10 wide characters = 20 columns
    
    passed = (width == expected_width)
    status = "✓ PASS" if passed else "✗ FAIL"
    
    print(f"{status} Mixed string:")
    print(f"  String: '{mixed_string}'")
    print(f"  Length: {len(mixed_string)} characters")
    print(f"  Display width: {width} columns")
    print(f"  Expected: {expected_width} columns")
    
    if not passed:
        print(f"  ERROR: Width mismatch")
    
    print()
    return passed


def test_filename_with_nfd():
    """Test realistic filename scenario with NFD characters."""
    
    print("Testing realistic filename with NFD:")
    print("=" * 60)
    
    # Simulate macOS filename (NFD)
    filename_nfc = "テストファイル_が.txt"
    filename_nfd = unicodedata.normalize('NFD', filename_nfc)
    
    width_nfc = get_display_width(filename_nfc)
    width_nfd = get_display_width(filename_nfd)
    
    # Both should have the same width
    passed = (width_nfc == width_nfd)
    status = "✓ PASS" if passed else "✗ FAIL"
    
    print(f"{status} Filename:")
    print(f"  NFC: '{filename_nfc}' -> width={width_nfc}")
    print(f"  NFD: '{filename_nfd}' -> width={width_nfd}")
    
    if not passed:
        print(f"  ERROR: Width mismatch between NFC and NFD forms")
    
    print()
    return passed


def main():
    """Run all NFD normalization tests."""
    
    print("\n" + "=" * 60)
    print("NFD Normalization Test Suite")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("NFD vs NFC width", test_nfd_vs_nfc_width_calculation()))
    results.append(("_is_wide_character", test_nfd_is_wide_character()))
    results.append(("Mixed NFD/NFC", test_mixed_nfd_nfc_string()))
    results.append(("Filename with NFD", test_filename_with_nfd()))
    
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
