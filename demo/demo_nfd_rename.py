#!/usr/bin/env python3
"""
Demo: NFD/NFC normalization in SingleLineTextEdit for rename operations

This demo shows how SingleLineTextEdit correctly handles NFD (decomposed)
strings from macOS filenames, normalizing them to NFC internally for editing,
and converting back to NFD when retrieving the text.

This ensures that when renaming files with Japanese or other Unicode characters
on macOS (which uses NFD), the renamed file maintains the correct normalization.
"""

import unicodedata
from src.tfm_single_line_text_edit import SingleLineTextEdit


def print_unicode_info(text, label):
    """Print detailed Unicode information about a string"""
    print(f"\n{label}:")
    print(f"  Text: '{text}'")
    print(f"  Length: {len(text)} characters")
    print(f"  Bytes: {text.encode('utf-8')}")
    
    # Check normalization form
    is_nfc = text == unicodedata.normalize('NFC', text)
    is_nfd = text == unicodedata.normalize('NFD', text)
    
    if is_nfc and not is_nfd:
        print(f"  Form: NFC (composed)")
    elif is_nfd and not is_nfc:
        print(f"  Form: NFD (decomposed)")
    elif is_nfc and is_nfd:
        print(f"  Form: Both NFC and NFD (ASCII or no combining characters)")
    else:
        print(f"  Form: Mixed or invalid")
    
    # Show character breakdown
    if len(text) <= 20:
        print(f"  Characters: {[c for c in text]}")


def demo_basic_nfd_handling():
    """Demo 1: Basic NFD handling"""
    print("=" * 70)
    print("DEMO 1: Basic NFD Handling")
    print("=" * 70)
    
    # Simulate macOS filename (NFD)
    original_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
    print_unicode_info(original_filename, "Original filename (NFD from macOS)")
    
    # Create editor with NFD text
    editor = SingleLineTextEdit(initial_text=original_filename)
    print_unicode_info(editor.text, "Internal text (automatically converted to NFC)")
    
    # Get text back
    retrieved_text = editor.get_text()
    print_unicode_info(retrieved_text, "Retrieved text (converted back to NFD)")
    
    # Verify they match
    print(f"\n✓ Original and retrieved match: {original_filename == retrieved_text}")


def demo_editing_nfd_text():
    """Demo 2: Editing NFD text"""
    print("\n" + "=" * 70)
    print("DEMO 2: Editing NFD Text")
    print("=" * 70)
    
    # Start with NFD filename
    original = unicodedata.normalize('NFD', "が.txt")
    print_unicode_info(original, "Original filename")
    
    # Create editor
    editor = SingleLineTextEdit(initial_text=original)
    
    # Edit: remove extension and add "_backup"
    editor.set_cursor_pos(len(editor.text) - 4)  # Before ".txt"
    for char in "_backup":
        editor.insert_char(char)
    
    # Get result
    result = editor.get_text()
    print_unicode_info(result, "After editing (added '_backup')")
    
    # Verify NFD is preserved
    print(f"\n✓ Result is NFD: {result == unicodedata.normalize('NFD', result)}")
    print(f"✓ Expected result: '{unicodedata.normalize('NFD', 'が_backup.txt')}'")
    print(f"✓ Actual result:   '{result}'")
    print(f"✓ Match: {result == unicodedata.normalize('NFD', 'が_backup.txt')}")


def demo_set_text_nfd():
    """Demo 3: Setting NFD text after initialization"""
    print("\n" + "=" * 70)
    print("DEMO 3: Setting NFD Text After Initialization")
    print("=" * 70)
    
    # Start with NFC text
    editor = SingleLineTextEdit(initial_text="test.txt")
    print_unicode_info(editor.get_text(), "Initial text (NFC)")
    
    # Set to NFD text
    nfd_text = unicodedata.normalize('NFD', "がぎぐげご.txt")
    editor.set_text(nfd_text)
    print_unicode_info(editor.text, "Internal text after set_text (NFC)")
    print_unicode_info(editor.get_text(), "Retrieved text (NFD)")
    
    # Verify
    print(f"\n✓ Retrieved text matches input: {editor.get_text() == nfd_text}")


def demo_rename_scenario():
    """Demo 4: Complete rename scenario"""
    print("\n" + "=" * 70)
    print("DEMO 4: Complete Rename Scenario")
    print("=" * 70)
    
    # Simulate the actual rename workflow
    print("\nScenario: User wants to rename 'テストファイル_が.txt' to 'テストファイル_が_v2.txt'")
    
    # Step 1: Get filename from macOS (NFD)
    macos_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
    print_unicode_info(macos_filename, "Step 1: Filename from macOS")
    
    # Step 2: Create rename dialog with NFD filename
    editor = SingleLineTextEdit(initial_text=macos_filename)
    print_unicode_info(editor.text, "Step 2: Editor internal text (NFC)")
    
    # Step 3: User edits (adds "_v2" before extension)
    editor.set_cursor_pos(len(editor.text) - 4)  # Before ".txt"
    for char in "_v2":
        editor.insert_char(char)
    print_unicode_info(editor.text, "Step 3: After editing (internal NFC)")
    
    # Step 4: Get new filename for rename operation
    new_filename = editor.get_text()
    print_unicode_info(new_filename, "Step 4: New filename for rename (NFD)")
    
    # Step 5: Verify it matches expected NFD form
    expected = unicodedata.normalize('NFD', "テストファイル_が_v2.txt")
    print_unicode_info(expected, "Expected result (NFD)")
    
    print(f"\n✓ New filename matches expected: {new_filename == expected}")
    print(f"✓ New filename is NFD: {new_filename == unicodedata.normalize('NFD', new_filename)}")
    print("\n✓ Rename operation will work correctly on macOS!")


def demo_comparison():
    """Demo 5: Before and after comparison"""
    print("\n" + "=" * 70)
    print("DEMO 5: Before and After Comparison")
    print("=" * 70)
    
    test_string = "が"
    nfd_form = unicodedata.normalize('NFD', test_string)
    nfc_form = unicodedata.normalize('NFC', test_string)
    
    print("\nCharacter: が (Japanese hiragana 'ga')")
    print(f"\nNFD form (decomposed):")
    print(f"  Length: {len(nfd_form)} characters")
    print(f"  Characters: {[c for c in nfd_form]}")
    print(f"  Unicode: {[f'U+{ord(c):04X}' for c in nfd_form]}")
    
    print(f"\nNFC form (composed):")
    print(f"  Length: {len(nfc_form)} characters")
    print(f"  Characters: {[c for c in nfc_form]}")
    print(f"  Unicode: {[f'U+{ord(c):04X}' for c in nfc_form]}")
    
    print("\nWhy this matters:")
    print("  - macOS stores filenames in NFD (decomposed) form")
    print("  - NFD 'が' = 'か' (U+304B) + combining mark (U+3099)")
    print("  - NFC 'が' = single character (U+304C)")
    print("  - SingleLineTextEdit normalizes to NFC for consistent editing")
    print("  - Then converts back to NFD to match original form")


if __name__ == '__main__':
    demo_basic_nfd_handling()
    demo_editing_nfd_text()
    demo_set_text_nfd()
    demo_rename_scenario()
    demo_comparison()
    
    print("\n" + "=" * 70)
    print("All demos completed successfully!")
    print("=" * 70)
