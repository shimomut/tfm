#!/usr/bin/env python3
"""
Demo: Archive Sorting Support

This demo shows how archive entries can be sorted using all available sort modes:
- Name (alphabetical)
- Size (file size)
- Date (modification time)
- Extension (file extension)
- Type (same as extension)

All sort modes respect the "directories first" rule.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tempfile
import zipfile
import tarfile
import time
from pathlib import Path as PathlibPath
from tfm_path import Path
from tfm_file_operations import FileListManager
from tfm_config import get_config
from datetime import datetime


def create_demo_archive(archive_path, archive_type='zip'):
    """Create a demo archive with various files for sorting demonstration"""
    if archive_type == 'zip':
        with zipfile.ZipFile(archive_path, 'w') as zf:
            # Add directories
            zf.writestr('documents/', '')
            zf.writestr('images/', '')
            zf.writestr('scripts/', '')
            
            # Add files with different characteristics
            # Small text file (oldest)
            info = zipfile.ZipInfo('readme.txt')
            info.date_time = (2023, 1, 15, 10, 0, 0)
            zf.writestr(info, 'This is a readme file.')
            
            # Medium Python script
            info = zipfile.ZipInfo('script.py')
            info.date_time = (2023, 6, 20, 14, 30, 0)
            zf.writestr(info, '#!/usr/bin/env python3\n' + 'print("Hello")' * 50)
            
            # Large log file (newest)
            info = zipfile.ZipInfo('application.log')
            info.date_time = (2024, 12, 1, 9, 15, 0)
            zf.writestr(info, 'LOG: ' * 2000)
            
            # Markdown document
            info = zipfile.ZipInfo('notes.md')
            info.date_time = (2023, 9, 10, 16, 45, 0)
            zf.writestr(info, '# Notes\n\n' + 'Some notes here. ' * 100)
            
            # Configuration file
            info = zipfile.ZipInfo('config.json')
            info.date_time = (2024, 3, 5, 11, 20, 0)
            zf.writestr(info, '{"setting": "value"}')
            
            # Shell script
            info = zipfile.ZipInfo('deploy.sh')
            info.date_time = (2024, 7, 18, 8, 0, 0)
            zf.writestr(info, '#!/bin/bash\necho "Deploying..."')


def format_size(size):
    """Format file size for display"""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.1f}MB"
    else:
        return f"{size/(1024*1024*1024):.1f}GB"


def format_date(timestamp):
    """Format timestamp for display"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


def display_entries(entries, title):
    """Display a list of entries with their details"""
    print(f"\n{title}")
    print("=" * 80)
    print(f"{'Type':<6} {'Name':<25} {'Size':<12} {'Date':<18} {'Ext':<6}")
    print("-" * 80)
    
    for entry in entries:
        entry_type = "DIR" if entry.is_dir() else "FILE"
        name = entry.name
        
        if entry.is_file():
            size = format_size(entry.stat().st_size)
            date = format_date(entry.stat().st_mtime)
            ext = entry.suffix
        else:
            size = "<DIR>"
            date = "---"
            ext = ""
        
        print(f"{entry_type:<6} {name:<25} {size:<12} {date:<18} {ext:<6}")


def demo_archive_sorting():
    """Demonstrate archive sorting with all sort modes"""
    print("=" * 80)
    print("Archive Sorting Demo")
    print("=" * 80)
    print("\nThis demo shows how archive entries can be sorted using different modes.")
    print("All sort modes maintain 'directories first' ordering.")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create demo archive
        archive_path = PathlibPath(tmpdir) / 'demo.zip'
        create_demo_archive(archive_path, 'zip')
        print(f"\nCreated demo archive: {archive_path.name}")
        
        # Create archive path
        archive_uri = f"archive://{archive_path}#"
        archive_root = Path(archive_uri)
        
        # Get entries
        entries = list(archive_root.iterdir())
        print(f"Archive contains {len(entries)} entries")
        
        # Initialize file operations
        config = get_config()
        file_ops = FileListManager(config)
        
        # Demonstrate each sort mode
        print("\n" + "=" * 80)
        print("1. SORT BY NAME (Alphabetical)")
        print("=" * 80)
        sorted_entries = file_ops.sort_entries(entries, 'name', reverse=False)
        display_entries(sorted_entries, "Sorted by Name (A-Z)")
        
        print("\n" + "=" * 80)
        print("2. SORT BY SIZE (Smallest to Largest)")
        print("=" * 80)
        sorted_entries = file_ops.sort_entries(entries, 'size', reverse=False)
        display_entries(sorted_entries, "Sorted by Size (Ascending)")
        
        print("\n" + "=" * 80)
        print("3. SORT BY SIZE (Largest to Smallest)")
        print("=" * 80)
        sorted_entries = file_ops.sort_entries(entries, 'size', reverse=True)
        display_entries(sorted_entries, "Sorted by Size (Descending)")
        
        print("\n" + "=" * 80)
        print("4. SORT BY DATE (Oldest to Newest)")
        print("=" * 80)
        sorted_entries = file_ops.sort_entries(entries, 'date', reverse=False)
        display_entries(sorted_entries, "Sorted by Date (Ascending)")
        
        print("\n" + "=" * 80)
        print("5. SORT BY DATE (Newest to Oldest)")
        print("=" * 80)
        sorted_entries = file_ops.sort_entries(entries, 'date', reverse=True)
        display_entries(sorted_entries, "Sorted by Date (Descending)")
        
        print("\n" + "=" * 80)
        print("6. SORT BY EXTENSION")
        print("=" * 80)
        sorted_entries = file_ops.sort_entries(entries, 'ext', reverse=False)
        display_entries(sorted_entries, "Sorted by Extension")
        
        print("\n" + "=" * 80)
        print("7. SORT BY TYPE (Same as Extension)")
        print("=" * 80)
        sorted_entries = file_ops.sort_entries(entries, 'type', reverse=False)
        display_entries(sorted_entries, "Sorted by Type")
        
        print("\n" + "=" * 80)
        print("Key Observations:")
        print("=" * 80)
        print("✓ Directories always appear first, regardless of sort mode")
        print("✓ Files are sorted according to the selected criterion")
        print("✓ All sort modes work correctly with archive entries")
        print("✓ Archive entries support the same sorting as regular files")
        print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_archive_sorting()
