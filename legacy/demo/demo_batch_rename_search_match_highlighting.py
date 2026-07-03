#!/usr/bin/env python3
"""
Demo: BatchRenameDialog Search Match Highlighting

This demo shows that BatchRenameDialog now visually highlights which parts
of filenames are being changed using COLOR_SEARCH_MATCH:
- In the original filename: the matched portion is highlighted
- In the new filename: the replacement portion is highlighted

This makes it immediately clear what's changing in each filename.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


def demo_search_match_highlighting():
    """Demonstrate search match highlighting in preview"""
    
    print("=" * 70)
    print("BatchRenameDialog Search Match Highlighting Demo")
    print("=" * 70)
    print()
    print("NOTE: This demo shows the data structure. In the actual TUI,")
    print("      the matched and replaced portions use COLOR_SEARCH_MATCH.")
    print()
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Example: Replace middle portion
        print("Example: Replace 'draft' with 'final' in filename")
        print("-" * 70)
        
        file1 = tmp_path / "photo_draft_2024.jpg"
        file1.write_text("content")
        files = [TFMPath(str(file1))]
        
        config = Mock()
        dialog = BatchRenameDialog(config)
        dialog.show(files)
        
        dialog.regex_editor.set_text("draft")
        dialog.destination_editor.set_text("final")
        dialog.update_preview()
        
        preview = dialog.preview[0]
        original = preview['original']
        new = preview['new']
        match_start = preview['match_start']
        match_end = preview['match_end']
        replace_start = preview['replace_start']
        replace_end = preview['replace_end']
        
        print(f"Original filename: {original}")
        print(f"  Matched portion: '{original[match_start:match_end]}' at position {match_start}-{match_end}")
        print(f"  Visual: {original[:match_start]}[UNDERLINED:{original[match_start:match_end]}]{original[match_end:]}")
        print()
        print(f"New filename: {new}")
        print(f"  Replaced portion: '{new[replace_start:replace_end]}' at position {replace_start}-{replace_end}")
        print(f"  Visual: {new[:replace_start]}[UNDERLINED:{new[replace_start:replace_end]}]{new[replace_end:]}")
        print()
        print("In the TUI:")
        print(f"  Original: photo_[draft]_2024.jpg  (draft is underlined)")
        print(f"  New:      photo_[final]_2024.jpg  (final is underlined)")
        print()
        
        # Example 2: Change extension
        print("Example: Change extension from .txt to .md")
        print("-" * 70)
        
        file2 = tmp_path / "document.txt"
        file2.write_text("content")
        files = [TFMPath(str(file2))]
        
        dialog.show(files)
        dialog.regex_editor.set_text(r"\.txt$")
        dialog.destination_editor.set_text(".md")
        dialog.update_preview()
        
        preview = dialog.preview[0]
        original = preview['original']
        new = preview['new']
        match_start = preview['match_start']
        match_end = preview['match_end']
        replace_start = preview['replace_start']
        replace_end = preview['replace_end']
        
        print(f"Original filename: {original}")
        print(f"  Matched portion: '{original[match_start:match_end]}' at position {match_start}-{match_end}")
        print()
        print(f"New filename: {new}")
        print(f"  Replaced portion: '{new[replace_start:replace_end]}' at position {replace_start}-{replace_end}")
        print()
        print("In the TUI:")
        print(f"  Original: document[.txt]  (.txt is underlined)")
        print(f"  New:      document[.md]   (.md is underlined)")
        print()
        
        print("=" * 70)
        print("Benefits of Underline Highlighting")
        print("=" * 70)
        print()
        print("• Instantly see what's being changed")
        print("• Verify the regex is matching the right part")
        print("• Confirm the replacement is in the correct position")
        print("• Easier to spot mistakes before executing the rename")
        print()


if __name__ == '__main__':
    demo_search_match_highlighting()
