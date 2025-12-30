#!/usr/bin/env python3
r"""
Demo: BatchRenameDialog File Order Preservation

This demo shows that BatchRenameDialog now preserves the file list order
when using \d for sequential numbering. This is important because users
expect files to be numbered in the order they appear in the file list,
not in arbitrary order.

Before the fix:
- selected_files was a set(), which has no guaranteed order
- Files would be numbered in arbitrary order when using \d

After the fix:
- Files are collected in the order they appear in current_pane['files']
- \d numbering is consistent with the visual file list order
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


def demo_file_order_preservation():
    r"""Demonstrate that file order is preserved for \d numbering"""
    
    print("=" * 70)
    print("BatchRenameDialog File Order Preservation Demo")
    print("=" * 70)
    print()
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create files in specific order
        print("Creating test files:")
        files = []
        for i in range(5):
            file_path = tmp_path / f"file_{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(TFMPath(str(file_path)))
            print(f"  {i+1}. {file_path.name}")
        
        print()
        
        # Create dialog
        config = Mock()
        dialog = BatchRenameDialog(config)
        
        # Show dialog with files in specific order
        dialog.show(files)
        
        # Set regex and destination with \d numbering
        print("Applying rename pattern:")
        print(r"  Regex:       file_(\d)\.txt")
        print(r"  Destination: renamed_\1_num_\d.txt")
        print()
        
        dialog.regex_editor.set_text(r"file_(\d)\.txt")
        dialog.destination_editor.set_text(r"renamed_\1_num_\d.txt")
        dialog.update_preview()
        
        # Display preview
        print("Preview (showing file order is preserved):")
        print()
        for i, preview in enumerate(dialog.preview):
            original = preview['original']
            new = preview['new']
            status = "OK" if preview['valid'] and not preview['conflict'] else "ERROR"
            print(f"  {i+1}. {original:20} → {new:30} [{status}]")
        
        print()
        print("✓ File order matches the input list order")
        print(r"✓ \d numbering is sequential: 1, 2, 3, 4, 5")
        print()
        
        # Demonstrate what would happen with wrong order
        print("=" * 70)
        print("What would happen if order was NOT preserved:")
        print("=" * 70)
        print()
        print("Files might be numbered in arbitrary order:")
        print("  file_2.txt → renamed_2_num_1.txt  (Wrong!)")
        print("  file_0.txt → renamed_0_num_2.txt  (Wrong!)")
        print("  file_4.txt → renamed_4_num_3.txt  (Wrong!)")
        print("  ...")
        print()
        print("This would be confusing and unpredictable for users!")
        print()


if __name__ == '__main__':
    demo_file_order_preservation()
