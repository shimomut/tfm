"""
Demo: truncate_to_width() NFD Handling Fix

This demo demonstrates that truncate_to_width() now correctly handles
NFD-normalized strings and produces consistent results regardless of
whether the input is in NFC or NFD form.

The fix ensures that:
1. NFD strings are normalized to NFC before character-by-character processing
2. NFD and NFC inputs produce identical truncated results
3. The truncated result's display width matches the requested max_width
"""

import unicodedata
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk.wide_char_utils import truncate_to_width, get_display_width


def demo_nfd_vs_nfc_consistency():
    """Demonstrate that NFD and NFC inputs produce consistent results."""
    print("=" * 70)
    print("Demo 1: NFD vs NFC Consistency")
    print("=" * 70)
    
    # Create test string with Japanese characters
    nfc_text = "がぎぐげごかきくけこ"  # 10 characters, 20 columns
    nfd_text = unicodedata.normalize('NFD', nfc_text)
    
    print(f"\nOriginal text: {nfc_text}")
    print(f"NFC form: {len(nfc_text)} chars, {get_display_width(nfc_text)} columns")
    print(f"NFD form: {len(nfd_text)} chars, {get_display_width(nfd_text)} columns")
    
    # Test various target widths
    for target in [5, 10, 15]:
        print(f"\n--- Target width: {target} ---")
        
        nfc_result = truncate_to_width(nfc_text, target)
        nfd_result = truncate_to_width(nfd_text, target)
        
        nfc_width = get_display_width(nfc_result)
        nfd_width = get_display_width(nfd_result)
        
        print(f"NFC result: '{nfc_result}' (width: {nfc_width})")
        print(f"NFD result: '{nfd_result}' (width: {nfd_width})")
        print(f"Results match: {nfc_result == nfd_result}")
        print(f"Widths match: {nfc_width == nfd_width}")


def demo_width_accuracy():
    """Demonstrate that truncated results have accurate display widths."""
    print("\n" + "=" * 70)
    print("Demo 2: Width Accuracy")
    print("=" * 70)
    
    test_cases = [
        ("がぎぐげご" * 5, 10, "Japanese text"),
        ("hello world test", 8, "ASCII text"),
        ("混合mixed文字列", 12, "Mixed text"),
    ]
    
    for text, target, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"Original: '{text}' (width: {get_display_width(text)})")
        print(f"Target width: {target}")
        
        # Test both NFC and NFD
        nfc_text = unicodedata.normalize('NFC', text)
        nfd_text = unicodedata.normalize('NFD', text)
        
        nfc_result = truncate_to_width(nfc_text, target)
        nfd_result = truncate_to_width(nfd_text, target)
        
        nfc_width = get_display_width(nfc_result)
        nfd_width = get_display_width(nfd_result)
        
        print(f"NFC result: '{nfc_result}' (width: {nfc_width})")
        print(f"NFD result: '{nfd_result}' (width: {nfd_width})")
        print(f"Width within target: NFC={nfc_width <= target}, NFD={nfd_width <= target}")


def demo_edge_cases():
    """Demonstrate edge cases with NFD strings."""
    print("\n" + "=" * 70)
    print("Demo 3: Edge Cases")
    print("=" * 70)
    
    # Single NFD character
    print("\n--- Single NFD character ---")
    single_nfd = unicodedata.normalize('NFD', "が")
    print(f"Character: 'が' in NFD form ({len(single_nfd)} chars)")
    print(f"Display width: {get_display_width(single_nfd)}")
    
    for target in [2, 1]:
        result = truncate_to_width(single_nfd, target)
        width = get_display_width(result)
        print(f"Target {target}: '{result}' (width: {width})")
    
    # Empty string
    print("\n--- Empty string ---")
    result = truncate_to_width("", 10)
    print(f"Empty string, target 10: '{result}' (width: {get_display_width(result)})")
    
    # Target width 0
    print("\n--- Target width 0 ---")
    nfd_text = unicodedata.normalize('NFD', "がぎぐ")
    result = truncate_to_width(nfd_text, 0)
    print(f"NFD text, target 0: '{result}' (width: {get_display_width(result)})")


def demo_before_after_comparison():
    """Show the problem that existed before the fix."""
    print("\n" + "=" * 70)
    print("Demo 4: Before/After Comparison")
    print("=" * 70)
    
    nfc_text = "がぎぐげご"
    nfd_text = unicodedata.normalize('NFD', nfc_text)
    target = 6
    
    print(f"\nTest case: '{nfc_text}' truncated to width {target}")
    print(f"NFC form: {len(nfc_text)} chars")
    print(f"NFD form: {len(nfd_text)} chars")
    
    print("\nBEFORE the fix:")
    print("  - NFD input would iterate over decomposed characters")
    print("  - Combining marks would be processed separately from base chars")
    print("  - Result would have inconsistent width and display")
    print(f"  - NFD result might be: 'がぎ…' (width: 5)")
    print(f"  - NFC result would be: 'がぎぐ…' (width: 7)")
    
    print("\nAFTER the fix:")
    nfc_result = truncate_to_width(nfc_text, target)
    nfd_result = truncate_to_width(nfd_text, target)
    nfc_width = get_display_width(nfc_result)
    nfd_width = get_display_width(nfd_result)
    
    print(f"  - Both inputs are normalized to NFC before processing")
    print(f"  - NFD result: '{nfd_result}' (width: {nfd_width})")
    print(f"  - NFC result: '{nfc_result}' (width: {nfc_width})")
    print(f"  - Results match: {nfc_result == nfd_result}")
    print(f"  - Widths match: {nfc_width == nfd_width}")


def demo_filename_truncation():
    """Demonstrate practical use case: filename truncation."""
    print("\n" + "=" * 70)
    print("Demo 5: Practical Use Case - Filename Truncation")
    print("=" * 70)
    
    # Simulate macOS filenames (stored in NFD)
    filenames_nfc = [
        "がんばって.txt",
        "プロジェクト資料.pdf",
        "データ分析結果.xlsx",
    ]
    
    print("\nTruncating filenames to width 15:")
    print("-" * 40)
    
    for filename_nfc in filenames_nfc:
        # macOS stores filenames in NFD
        filename_nfd = unicodedata.normalize('NFD', filename_nfc)
        
        # Truncate both forms
        truncated_nfc = truncate_to_width(filename_nfc, 15)
        truncated_nfd = truncate_to_width(filename_nfd, 15)
        
        width_nfc = get_display_width(truncated_nfc)
        width_nfd = get_display_width(truncated_nfd)
        
        print(f"\nOriginal: {filename_nfc}")
        print(f"  NFC truncated: '{truncated_nfc}' (width: {width_nfc})")
        print(f"  NFD truncated: '{truncated_nfd}' (width: {width_nfd})")
        print(f"  Match: {truncated_nfc == truncated_nfd}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("truncate_to_width() NFD Handling Fix Demo")
    print("=" * 70)
    
    demo_nfd_vs_nfc_consistency()
    demo_width_accuracy()
    demo_edge_cases()
    demo_before_after_comparison()
    demo_filename_truncation()
    
    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)
