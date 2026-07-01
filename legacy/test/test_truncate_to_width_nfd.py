"""
Test truncate_to_width() NFD handling and length accuracy.

This test suite verifies that:
1. truncate_to_width() correctly handles NFD-normalized strings
2. The truncated result's display width matches the requested max_width
3. NFD and NFC inputs produce consistent results
"""

import unicodedata
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk.wide_char_utils import truncate_to_width, get_display_width


def test_truncate_nfd_basic():
    """Test basic NFD truncation."""
    # "が" in NFD form (か + combining mark)
    nfd_text = "が" * 10  # 10 characters in NFC, 20 in NFD
    nfd_text = unicodedata.normalize('NFD', nfd_text)
    
    # Truncate to width 5 (should fit 2.5 characters, so 2 characters + ellipsis)
    result = truncate_to_width(nfd_text, 5)
    result_width = get_display_width(result)
    
    print(f"NFD basic truncation:")
    print(f"  Input: {repr(nfd_text[:20])}... (NFD form)")
    print(f"  Target width: 5")
    print(f"  Result: {repr(result)}")
    print(f"  Result width: {result_width}")
    print(f"  Result display: {result}")
    
    # The result width should be <= 5
    assert result_width <= 5, f"Result width {result_width} exceeds target 5"


def test_truncate_nfd_vs_nfc_consistency():
    """Test that NFD and NFC inputs produce consistent display widths."""
    # Create test string with Japanese characters
    nfc_text = "がぎぐげご" * 3  # 15 characters
    nfd_text = unicodedata.normalize('NFD', nfc_text)
    
    target_width = 10
    
    # Truncate both forms
    nfc_result = truncate_to_width(nfc_text, target_width)
    nfd_result = truncate_to_width(nfd_text, target_width)
    
    # Get display widths
    nfc_width = get_display_width(nfc_result)
    nfd_width = get_display_width(nfd_result)
    
    print(f"\nNFD vs NFC consistency:")
    print(f"  NFC input: {repr(nfc_text)}")
    print(f"  NFD input: {repr(nfd_text[:30])}...")
    print(f"  Target width: {target_width}")
    print(f"  NFC result: {repr(nfc_result)} (width: {nfc_width})")
    print(f"  NFD result: {repr(nfd_result)} (width: {nfd_width})")
    print(f"  NFC display: {nfc_result}")
    print(f"  NFD display: {nfd_result}")
    
    # Both should have same display width
    assert nfc_width == nfd_width, f"Width mismatch: NFC={nfc_width}, NFD={nfd_width}"
    
    # Both should be <= target width
    assert nfc_width <= target_width, f"NFC width {nfc_width} exceeds target {target_width}"
    assert nfd_width <= target_width, f"NFD width {nfd_width} exceeds target {target_width}"


def test_truncate_exact_width_match():
    """Test that truncated results match the requested width exactly (or are less)."""
    test_cases = [
        ("がぎぐげご" * 5, 10),  # Japanese, target 10
        ("がぎぐげご" * 5, 15),  # Japanese, target 15
        ("がぎぐげご" * 5, 20),  # Japanese, target 20
        ("hello world test", 10),  # ASCII, target 10
        ("hello world test", 5),   # ASCII, target 5
        ("混合mixed文字列", 10),   # Mixed, target 10
    ]
    
    print(f"\nExact width match tests:")
    
    for text, target_width in test_cases:
        # Test both NFC and NFD forms
        nfc_text = unicodedata.normalize('NFC', text)
        nfd_text = unicodedata.normalize('NFD', text)
        
        nfc_result = truncate_to_width(nfc_text, target_width)
        nfd_result = truncate_to_width(nfd_text, target_width)
        
        nfc_width = get_display_width(nfc_result)
        nfd_width = get_display_width(nfd_result)
        
        print(f"  Text: {repr(text[:20])}... Target: {target_width}")
        print(f"    NFC result width: {nfc_width} (expected <= {target_width})")
        print(f"    NFD result width: {nfd_width} (expected <= {target_width})")
        
        # Verify widths are within target
        assert nfc_width <= target_width, \
            f"NFC result width {nfc_width} exceeds target {target_width} for text {repr(text[:20])}"
        assert nfd_width <= target_width, \
            f"NFD result width {nfd_width} exceeds target {target_width} for text {repr(text[:20])}"
        
        # Verify NFC and NFD produce same width
        assert nfc_width == nfd_width, \
            f"Width mismatch for {repr(text[:20])}: NFC={nfc_width}, NFD={nfd_width}"


def test_truncate_edge_cases():
    """Test edge cases with NFD strings."""
    print(f"\nEdge case tests:")
    
    # Single NFD character
    single_nfd = unicodedata.normalize('NFD', "が")
    result = truncate_to_width(single_nfd, 2)
    width = get_display_width(result)
    print(f"  Single NFD char (width 2), target 2: result width = {width}")
    assert width <= 2
    
    # Single NFD character, target 1 (should truncate to ellipsis)
    result = truncate_to_width(single_nfd, 1)
    width = get_display_width(result)
    print(f"  Single NFD char (width 2), target 1: result width = {width}")
    assert width <= 1
    
    # Empty string
    result = truncate_to_width("", 10)
    width = get_display_width(result)
    print(f"  Empty string, target 10: result width = {width}")
    assert width == 0
    
    # Target width 0
    nfd_text = unicodedata.normalize('NFD', "がぎぐ")
    result = truncate_to_width(nfd_text, 0)
    width = get_display_width(result)
    print(f"  NFD text, target 0: result width = {width}")
    assert width <= 0


def test_truncate_long_nfd_string():
    """Test truncation of a long NFD string to verify no width overflow."""
    # Create a long NFD string
    nfc_text = "がぎぐげご" * 20  # 100 characters
    nfd_text = unicodedata.normalize('NFD', nfc_text)
    
    print(f"\nLong NFD string test:")
    print(f"  Original NFC length: {len(nfc_text)} chars")
    print(f"  Original NFD length: {len(nfd_text)} chars")
    print(f"  Original display width: {get_display_width(nfd_text)}")
    
    # Test various target widths
    for target in [10, 20, 30, 50, 100]:
        result = truncate_to_width(nfd_text, target)
        width = get_display_width(result)
        print(f"  Target {target}: result width = {width} (expected <= {target})")
        assert width <= target, f"Width {width} exceeds target {target}"


if __name__ == "__main__":
    print("Testing truncate_to_width() NFD handling and length accuracy\n")
    print("=" * 70)
    
    test_truncate_nfd_basic()
    test_truncate_nfd_vs_nfc_consistency()
    test_truncate_exact_width_match()
    test_truncate_edge_cases()
    test_truncate_long_nfd_string()
    
    print("\n" + "=" * 70)
    print("All tests passed!")
