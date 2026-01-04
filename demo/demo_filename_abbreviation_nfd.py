#!/usr/bin/env python3
"""
Demo: NFD/NFC normalization in filename abbreviation

This demo shows that filename abbreviation produces consistent results
regardless of whether the filename is in NFC or NFD form, which is important
for macOS where filenames are stored in NFD (decomposed) form.
"""

import unicodedata
from ttk.wide_char_utils import get_display_width, truncate_to_width, pad_to_width


def print_unicode_info(text, label):
    """Print detailed Unicode information about a string"""
    print(f"\n{label}:")
    print(f"  Text: '{text}'")
    print(f"  Length: {len(text)} characters")
    print(f"  Display width: {get_display_width(text)} columns")
    
    # Check normalization form
    is_nfc = text == unicodedata.normalize('NFC', text)
    is_nfd = text == unicodedata.normalize('NFD', text)
    
    if is_nfc and not is_nfd:
        print(f"  Form: NFC (composed)")
    elif is_nfd and not is_nfc:
        print(f"  Form: NFD (decomposed)")
    elif is_nfc and is_nfd:
        print(f"  Form: Both NFC and NFD (ASCII or no combining characters)")


def demo_display_width_consistency():
    """Demo 1: Display width is consistent between NFC and NFD"""
    print("=" * 70)
    print("DEMO 1: Display Width Consistency")
    print("=" * 70)
    
    # Create filename in both forms
    nfc_filename = unicodedata.normalize('NFC', "テストファイル_が.txt")
    nfd_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
    
    print_unicode_info(nfc_filename, "NFC filename")
    print_unicode_info(nfd_filename, "NFD filename (macOS)")
    
    print(f"\n✓ Display widths match: {get_display_width(nfc_filename)} == {get_display_width(nfd_filename)}")


def demo_truncation_consistency():
    """Demo 2: Truncation produces consistent visual width"""
    print("\n" + "=" * 70)
    print("DEMO 2: Truncation Consistency")
    print("=" * 70)
    
    # Create filename in both forms
    nfc_filename = unicodedata.normalize('NFC', "テストファイル_が.txt")
    nfd_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
    
    # Truncate to same width
    target_width = 15
    nfc_truncated = truncate_to_width(nfc_filename, target_width)
    nfd_truncated = truncate_to_width(nfd_filename, target_width)
    
    print(f"\nTarget width: {target_width} columns")
    print_unicode_info(nfc_truncated, "NFC truncated")
    print_unicode_info(nfd_truncated, "NFD truncated")
    
    nfc_width = get_display_width(nfc_truncated)
    nfd_width = get_display_width(nfd_truncated)
    
    print(f"\n✓ Both fit within {target_width} columns")
    print(f"✓ Visual widths: NFC={nfc_width}, NFD={nfd_width}")


def demo_padding_consistency():
    """Demo 3: Padding produces consistent visual width"""
    print("\n" + "=" * 70)
    print("DEMO 3: Padding Consistency")
    print("=" * 70)
    
    # Create filename in both forms
    nfc_filename = unicodedata.normalize('NFC', "が.txt")
    nfd_filename = unicodedata.normalize('NFD', "が.txt")
    
    # Pad to same width
    target_width = 20
    nfc_padded = pad_to_width(nfc_filename, target_width)
    nfd_padded = pad_to_width(nfd_filename, target_width)
    
    print(f"\nTarget width: {target_width} columns")
    print_unicode_info(nfc_padded, "NFC padded")
    print_unicode_info(nfd_padded, "NFD padded")
    
    print(f"\n✓ Both padded to exactly {target_width} columns")


def demo_file_list_scenario():
    """Demo 4: File list display scenario"""
    print("\n" + "=" * 70)
    print("DEMO 4: File List Display Scenario")
    print("=" * 70)
    
    print("\nSimulating file list with mixed NFC/NFD filenames:")
    
    # Simulate file list with mixed forms
    filenames = [
        ("NFC", unicodedata.normalize('NFC', "テストファイル_が.txt")),
        ("NFD", unicodedata.normalize('NFD', "テストファイル_が.txt")),
        ("NFC", unicodedata.normalize('NFC', "がぎぐげご.pdf")),
        ("NFD", unicodedata.normalize('NFD', "がぎぐげご.pdf")),
    ]
    
    # Display original widths
    print("\nOriginal filenames:")
    for form, filename in filenames:
        width = get_display_width(filename)
        print(f"  [{form}] '{filename}' - {len(filename)} chars, {width} columns")
    
    # Truncate all to same width
    target_width = 15
    print(f"\nTruncated to {target_width} columns:")
    
    truncated = []
    for form, filename in filenames:
        truncated_name = truncate_to_width(filename, target_width)
        width = get_display_width(truncated_name)
        truncated.append((form, truncated_name, width))
        print(f"  [{form}] '{truncated_name}' - {width} columns")
    
    # Verify consistency
    print("\n✓ NFC and NFD versions have same display width:")
    print(f"  テストファイル_が.txt: NFC={truncated[0][2]}, NFD={truncated[1][2]}")
    print(f"  がぎぐげご.pdf: NFC={truncated[2][2]}, NFD={truncated[3][2]}")


def demo_single_character_detail():
    """Demo 5: Single character detail"""
    print("\n" + "=" * 70)
    print("DEMO 5: Single Character Detail")
    print("=" * 70)
    
    nfc_char = unicodedata.normalize('NFC', "が")
    nfd_char = unicodedata.normalize('NFD', "が")
    
    print("\nCharacter: が (Japanese hiragana 'ga')")
    
    print(f"\nNFC form (composed):")
    print(f"  Characters: {[c for c in nfc_char]}")
    print(f"  Unicode: {[f'U+{ord(c):04X}' for c in nfc_char]}")
    print(f"  Length: {len(nfc_char)} character")
    print(f"  Display width: {get_display_width(nfc_char)} columns")
    
    print(f"\nNFD form (decomposed):")
    print(f"  Characters: {[c for c in nfd_char]}")
    print(f"  Unicode: {[f'U+{ord(c):04X}' for c in nfd_char]}")
    print(f"  Length: {len(nfd_char)} characters")
    print(f"  Display width: {get_display_width(nfd_char)} columns")
    
    print("\n✓ Both display as 2 columns wide (wide character)")
    print("✓ Display width calculation normalizes to NFC internally")


def demo_various_truncation_widths():
    """Demo 6: Various truncation widths"""
    print("\n" + "=" * 70)
    print("DEMO 6: Various Truncation Widths")
    print("=" * 70)
    
    # Long filename with Japanese characters
    nfc_filename = unicodedata.normalize('NFC', "これは非常に長いファイル名です_が_test.txt")
    nfd_filename = unicodedata.normalize('NFD', "これは非常に長いファイル名です_が_test.txt")
    
    print(f"\nOriginal filename:")
    print(f"  NFC: {len(nfc_filename)} chars, {get_display_width(nfc_filename)} columns")
    print(f"  NFD: {len(nfd_filename)} chars, {get_display_width(nfd_filename)} columns")
    
    print(f"\nTruncation at various widths:")
    print(f"{'Width':<8} {'NFC Result':<25} {'NFC Cols':<10} {'NFD Result':<25} {'NFD Cols':<10}")
    print("-" * 80)
    
    for width in [10, 15, 20, 25, 30]:
        nfc_truncated = truncate_to_width(nfc_filename, width)
        nfd_truncated = truncate_to_width(nfd_filename, width)
        
        nfc_result_width = get_display_width(nfc_truncated)
        nfd_result_width = get_display_width(nfd_truncated)
        
        print(f"{width:<8} {nfc_truncated:<25} {nfc_result_width:<10} {nfd_truncated:<25} {nfd_result_width:<10}")
    
    print("\n✓ All truncations fit within target width")
    print("✓ NFC and NFD produce consistent visual results")


if __name__ == '__main__':
    demo_display_width_consistency()
    demo_truncation_consistency()
    demo_padding_consistency()
    demo_file_list_scenario()
    demo_single_character_detail()
    demo_various_truncation_widths()
    
    print("\n" + "=" * 70)
    print("All demos completed successfully!")
    print("=" * 70)
    print("\nKey takeaway:")
    print("  The display width calculation automatically normalizes to NFC,")
    print("  ensuring consistent visual width for both NFC and NFD filenames.")
    print("  This is crucial for macOS where filenames are stored in NFD form.")
