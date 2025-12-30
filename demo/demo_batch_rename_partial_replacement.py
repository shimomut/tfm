#!/usr/bin/env python3
"""
Demo: BatchRenameDialog Partial Replacement Behavior

This demo shows that BatchRenameDialog now replaces only the matched portion
of filenames, keeping the rest intact. This is more intuitive and consistent
with how regex search/replace typically works.

Before the fix:
- Regex matched a portion of the filename
- Destination replaced the ENTIRE filename
- Users had to manually reconstruct the full filename in the destination

After the fix:
- Regex matches a portion of the filename
- Destination replaces ONLY the matched portion
- Unmatched parts of the filename are preserved automatically
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


def demo_partial_replacement():
    """Demonstrate partial filename replacement"""
    
    print("=" * 70)
    print("BatchRenameDialog Partial Replacement Demo")
    print("=" * 70)
    print()
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Example 1: Replace middle portion
        print("=" * 70)
        print("Example 1: Replace middle portion of filename")
        print("=" * 70)
        print()
        
        file1 = tmp_path / "photo_draft_2024.jpg"
        file1.write_text("content")
        files = [TFMPath(str(file1))]
        
        config = Mock()
        dialog = BatchRenameDialog(config)
        dialog.show(files)
        
        print(f"Original: {file1.name}")
        print(f"Regex:    draft")
        print(f"Replace:  final")
        print()
        
        dialog.regex_editor.set_text("draft")
        dialog.destination_editor.set_text("final")
        dialog.update_preview()
        
        print(f"Result:   {dialog.preview[0]['new']}")
        print()
        print("✓ Only 'draft' was replaced, 'photo_' and '_2024.jpg' preserved")
        print()
        
        # Example 2: Reformat date
        print("=" * 70)
        print("Example 2: Reformat date in filename")
        print("=" * 70)
        print()
        
        file2 = tmp_path / "report_2024_01_15.pdf"
        file2.write_text("content")
        files = [TFMPath(str(file2))]
        
        dialog.show(files)
        
        print(f"Original: {file2.name}")
        print(r"Regex:    (\d{4})_(\d{2})_(\d{2})")
        print(r"Replace:  \1-\2-\3")
        print()
        
        dialog.regex_editor.set_text(r"(\d{4})_(\d{2})_(\d{2})")
        dialog.destination_editor.set_text(r"\1-\2-\3")
        dialog.update_preview()
        
        print(f"Result:   {dialog.preview[0]['new']}")
        print()
        print("✓ Date format changed, 'report_' and '.pdf' preserved")
        print()
        
        # Example 3: Change extension
        print("=" * 70)
        print("Example 3: Change file extension")
        print("=" * 70)
        print()
        
        file3 = tmp_path / "document.txt"
        file3.write_text("content")
        files = [TFMPath(str(file3))]
        
        dialog.show(files)
        
        print(f"Original: {file3.name}")
        print(r"Regex:    \.txt$")
        print(r"Replace:  .md")
        print()
        
        dialog.regex_editor.set_text(r"\.txt$")
        dialog.destination_editor.set_text(".md")
        dialog.update_preview()
        
        print(f"Result:   {dialog.preview[0]['new']}")
        print()
        print("✓ Extension changed, filename preserved")
        print()
        
        # Example 4: Add prefix
        print("=" * 70)
        print("Example 4: Add prefix to filename")
        print("=" * 70)
        print()
        
        file4 = tmp_path / "image.jpg"
        file4.write_text("content")
        files = [TFMPath(str(file4))]
        
        dialog.show(files)
        
        print(f"Original: {file4.name}")
        print(r"Regex:    ^")
        print(r"Replace:  backup_")
        print()
        
        dialog.regex_editor.set_text("^")
        dialog.destination_editor.set_text("backup_")
        dialog.update_preview()
        
        print(f"Result:   {dialog.preview[0]['new']}")
        print()
        print("✓ Prefix added, rest of filename preserved")
        print()
        
        # Example 5: Replace entire filename (when needed)
        print("=" * 70)
        print("Example 5: Replace entire filename (using .*)")
        print("=" * 70)
        print()
        
        file5 = tmp_path / "old_name.txt"
        file5.write_text("content")
        files = [TFMPath(str(file5))]
        
        dialog.show(files)
        
        print(f"Original: {file5.name}")
        print(r"Regex:    .*")
        print(r"Replace:  new_name.txt")
        print()
        
        dialog.regex_editor.set_text(".*")
        dialog.destination_editor.set_text("new_name.txt")
        dialog.update_preview()
        
        print(f"Result:   {dialog.preview[0]['new']}")
        print()
        print("✓ Entire filename replaced (when .* is used)")
        print()
        
        # Summary
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print()
        print("The new behavior is more intuitive and powerful:")
        print()
        print("Benefits:")
        print("  • Consistent with standard regex search/replace")
        print("  • Automatically preserves unmatched portions")
        print("  • Easier to use - no need to reconstruct full filename")
        print("  • More flexible - can target specific parts")
        print()
        print("Common patterns:")
        print("  • Match specific text → Replace that text only")
        print("  • Match with groups → Rearrange/reformat matched parts")
        print(r"  • Match extension (\.ext$) → Change extension")
        print(r"  • Match start (^) → Add prefix")
        print(r"  • Match entire (.*) → Replace whole filename")
        print()


if __name__ == '__main__':
    demo_partial_replacement()
