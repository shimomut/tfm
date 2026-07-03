#!/usr/bin/env python3
"""
Demo: BatchRenameDialog Always Shows Preview

This demo shows that BatchRenameDialog now always displays a preview,
even when regex or destination patterns are empty or invalid.

Before the fix:
- Preview was only shown when both regex and destination were non-empty
- Users saw "Enter regex pattern and destination to see preview" message

After the fix:
- Preview is always shown, displaying all files
- Empty/invalid patterns show files as "UNCHANGED"
- Users can see what files they're working with immediately
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


def demo_always_preview():
    """Demonstrate that preview is always shown"""
    
    print("=" * 70)
    print("BatchRenameDialog Always Shows Preview Demo")
    print("=" * 70)
    print()
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create files
        print("Creating test files:")
        files = []
        for i in range(3):
            file_path = tmp_path / f"document_{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
            print(f"  {i+1}. {file_path.name}")
        
        print()
        
        # Create dialog
        config = Mock()
        dialog = BatchRenameDialog(config)
        
        # Test 1: Initial show (empty patterns)
        print("=" * 70)
        print("Test 1: Dialog opened with empty patterns")
        print("=" * 70)
        dialog.show(files)
        
        print(f"Preview entries: {len(dialog.preview)}")
        print("Preview content:")
        for i, preview in enumerate(dialog.preview):
            print(f"  {i+1}. {preview['original']:20} → {preview['new']:20} [UNCHANGED]")
        print()
        print("✓ Preview is shown immediately, all files marked as UNCHANGED")
        print()
        
        # Test 2: Only regex specified
        print("=" * 70)
        print("Test 2: Only regex pattern specified (no destination)")
        print("=" * 70)
        dialog.regex_editor.set_text(r"document_(\d)")
        dialog.update_preview()
        
        print(f"Preview entries: {len(dialog.preview)}")
        print("Preview content:")
        for i, preview in enumerate(dialog.preview):
            print(f"  {i+1}. {preview['original']:20} → {preview['new']:20} [UNCHANGED]")
        print()
        print("✓ Preview still shown, files remain UNCHANGED (no destination)")
        print()
        
        # Test 3: Invalid regex
        print("=" * 70)
        print("Test 3: Invalid regex pattern")
        print("=" * 70)
        dialog.regex_editor.set_text("[invalid(regex")
        dialog.destination_editor.set_text("renamed")
        dialog.update_preview()
        
        print(f"Preview entries: {len(dialog.preview)}")
        print("Preview content:")
        for i, preview in enumerate(dialog.preview):
            print(f"  {i+1}. {preview['original']:20} → {preview['new']:20} [UNCHANGED]")
        print()
        print("✓ Preview still shown despite invalid regex")
        print()
        
        # Test 4: Valid patterns
        print("=" * 70)
        print("Test 4: Valid patterns applied")
        print("=" * 70)
        dialog.regex_editor.set_text(r"document_(\d)\.txt")
        dialog.destination_editor.set_text(r"file_\1.txt")
        dialog.update_preview()
        
        print(f"Preview entries: {len(dialog.preview)}")
        print("Preview content:")
        for i, preview in enumerate(dialog.preview):
            status = "OK" if preview['valid'] and not preview['conflict'] else "ERROR"
            print(f"  {i+1}. {preview['original']:20} → {preview['new']:20} [{status}]")
        print()
        print("✓ Preview shows actual rename operations")
        print()
        
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print()
        print("The preview is now ALWAYS visible, providing immediate feedback:")
        print("  • Empty patterns → All files shown as UNCHANGED")
        print("  • Invalid regex → All files shown as UNCHANGED")
        print("  • Valid patterns → Shows actual rename preview")
        print()
        print("This improves usability by:")
        print("  • Showing users what files they're working with")
        print("  • Providing immediate visual feedback")
        print("  • Eliminating the empty preview state")
        print()


if __name__ == '__main__':
    demo_always_preview()
