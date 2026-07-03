#!/usr/bin/env python3
"""
Demo: BatchRenameDialog Empty Destination Pattern

This demo shows that BatchRenameDialog can use an empty destination pattern
to delete the matched portion of filenames.

Use cases:
- Remove prefixes: regex="^old_", destination="" → "old_file.txt" becomes "file.txt"
- Remove suffixes: regex="_backup$", destination="" → "file_backup.txt" becomes "file.txt"
- Remove extensions: regex=r"\.txt$", destination="" → "document.txt" becomes "document"
- Remove middle portions: regex="_temp", destination="" → "file_temp_data.txt" becomes "file_data.txt"
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_path import Path as TFMPath


def demo_empty_destination():
    """Demonstrate empty destination pattern for deletion"""
    
    print("=" * 70)
    print("BatchRenameDialog Empty Destination Demo")
    print("=" * 70)
    print()
    print("Empty destination pattern deletes the matched portion of filenames.")
    print()
    
    # Create temporary directory and files
    temp_dir = tempfile.mkdtemp()
    
    test_cases = [
        {
            'files': ['old_file1.txt', 'old_file2.txt', 'old_file3.txt'],
            'regex': '^old_',
            'description': 'Remove prefix "old_"'
        },
        {
            'files': ['backup_file.txt', 'backup_data.txt'],
            'regex': '^backup_',
            'description': 'Remove prefix "backup_"'
        },
        {
            'files': ['document.txt', 'report.txt', 'notes.txt'],
            'regex': r'\.txt$',
            'description': 'Remove ".txt" extension'
        },
        {
            'files': ['file_temp_data.txt', 'test_temp_results.txt'],
            'regex': '_temp',
            'description': 'Remove "_temp" from middle'
        },
        {
            'files': ['test123.txt', 'file456.txt', 'doc789.txt'],
            'regex': r'\d+',
            'description': 'Remove all digits'
        }
    ]
    
    dialog = BatchRenameDialog(config={})
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['description']}")
        print(f"Regex: {test_case['regex']}")
        print(f"Destination: (empty)")
        print()
        
        # Create test files
        files = []
        for filename in test_case['files']:
            file_path = Path(temp_dir) / filename
            file_path.touch()
            files.append(TFMPath(str(file_path)))
        
        # Show dialog and set patterns
        dialog.show(files)
        dialog.regex_editor.set_text(test_case['regex'])
        dialog.destination_editor.set_text('')  # Empty destination
        dialog.update_preview()
        
        # Display results
        print("Results:")
        for preview in dialog.preview:
            original = preview['original']
            new = preview['new']
            if original != new:
                print(f"  {original:30} → {new}")
            else:
                print(f"  {original:30} (unchanged)")
        
        print()
        
        # Clean up files
        for file_path in files:
            try:
                Path(str(file_path)).unlink()
            except Exception:
                pass
    
    # Clean up temp directory
    try:
        Path(temp_dir).rmdir()
    except Exception:
        pass
    
    print("=" * 70)
    print("Key Points:")
    print("- Empty destination deletes the matched portion")
    print("- Useful for removing prefixes, suffixes, or middle portions")
    print("- Can be combined with regex groups for complex patterns")
    print("- Preview shows exactly what will be deleted")
    print("=" * 70)


if __name__ == '__main__':
    demo_empty_destination()
