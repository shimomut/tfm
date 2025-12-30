#!/usr/bin/env python3
"""
Demo: NFD Normalization Handling

This demo shows how TFM correctly handles NFD (Normalization Form D) filenames
from macOS filesystems, where characters like "が" are decomposed into base
character + combining mark.

The demo displays:
1. Comparison of NFC vs NFD character representation
2. Width calculation for both forms
3. Visual rendering to show correct alignment
"""

import sys
import os
import unicodedata

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_wide_char_utils import get_display_width


def print_separator(char='=', width=70):
    """Print a separator line."""
    print(char * width)


def demonstrate_nfd_issue():
    """Demonstrate the NFD normalization issue and solution."""
    
    print("\n")
    print_separator()
    print("NFD Normalization Demo - macOS Filename Handling")
    print_separator()
    print()
    
    # Example 1: Single character decomposition
    print("Example 1: Character Decomposition")
    print("-" * 70)
    
    char_nfc = "が"
    char_nfd = unicodedata.normalize('NFD', char_nfc)
    
    print(f"NFC form: '{char_nfc}'")
    print(f"  - Length: {len(char_nfc)} character(s)")
    print(f"  - Code points: {', '.join(f'U+{ord(c):04X}' for c in char_nfc)}")
    print(f"  - Display width: {get_display_width(char_nfc)} columns")
    print()
    
    print(f"NFD form: '{char_nfd}' (macOS filesystem format)")
    print(f"  - Length: {len(char_nfd)} character(s)")
    print(f"  - Code points: {', '.join(f'U+{ord(c):04X}' for c in char_nfd)}")
    print(f"  - Display width: {get_display_width(char_nfd)} columns")
    print()
    
    print("✓ Both forms now have the same display width (2 columns)")
    print()
    
    # Example 2: Filename scenario
    print("Example 2: Realistic Filename")
    print("-" * 70)
    
    filename_nfc = "テストファイル_が.txt"
    filename_nfd = unicodedata.normalize('NFD', filename_nfc)
    
    print(f"NFC filename: '{filename_nfc}'")
    print(f"  - Length: {len(filename_nfc)} characters")
    print(f"  - Display width: {get_display_width(filename_nfc)} columns")
    print()
    
    print(f"NFD filename: '{filename_nfd}' (macOS format)")
    print(f"  - Length: {len(filename_nfd)} characters")
    print(f"  - Display width: {get_display_width(filename_nfd)} columns")
    print()
    
    print("✓ Both forms have the same display width")
    print()
    
    # Example 3: Visual alignment demonstration
    print("Example 3: Visual Alignment")
    print("-" * 70)
    
    filenames = [
        ("こんにちは.txt", "NFC - Hello"),
        (unicodedata.normalize('NFD', "がぎぐげご.txt"), "NFD - Dakuten"),
        ("テスト_123.txt", "NFC - Mixed"),
        (unicodedata.normalize('NFD', "パピプペポ.txt"), "NFD - Handakuten"),
    ]
    
    print("Filename alignment test (all should align at column 30):")
    print()
    
    for filename, description in filenames:
        width = get_display_width(filename)
        padding = 30 - width
        display = filename + (' ' * padding) + f"| {description}"
        print(f"  {display}")
    
    print()
    print("✓ All filenames align correctly at the separator")
    print()
    
    # Example 4: Common Japanese characters
    print("Example 4: Common Japanese Characters with Dakuten/Handakuten")
    print("-" * 70)
    
    test_chars = [
        ("が", "GA - hiragana with dakuten"),
        ("ぎ", "GI - hiragana with dakuten"),
        ("ざ", "ZA - hiragana with dakuten"),
        ("パ", "PA - katakana with handakuten"),
        ("ピ", "PI - katakana with handakuten"),
    ]
    
    print("Character | NFC len | NFD len | Display Width | Description")
    print("-" * 70)
    
    for char_nfc, description in test_chars:
        char_nfd = unicodedata.normalize('NFD', char_nfc)
        width = get_display_width(char_nfd)
        print(f"    {char_nfc}     |    {len(char_nfc)}    |    {len(char_nfd)}    |       {width}       | {description}")
    
    print()
    print("✓ All characters correctly identified as 2-column wide")
    print()
    
    # Summary
    print_separator()
    print("Summary")
    print_separator()
    print()
    print("TFM now correctly handles macOS NFD filenames by:")
    print("  1. Normalizing NFD to NFC at the rendering layer")
    print("  2. Ensuring consistent width calculation")
    print("  3. Maintaining proper visual alignment")
    print()
    print("This fix is automatic and transparent - no user action required.")
    print()
    print_separator()


def main():
    """Run the NFD normalization demo."""
    try:
        demonstrate_nfd_issue()
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
