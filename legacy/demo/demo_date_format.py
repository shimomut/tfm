#!/usr/bin/env python3
"""
Demo: Flexible Date-Time Formatting in File List Panes

This demo showcases the two date format variations available in TFM:
1. Short format: YY-MM-DD HH:mm (default)
2. Full format: YYYY-MM-DD HH:mm:ss

Users can toggle between formats using the View Options menu (z key).
"""

import sys
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path as StdPath

# Add src to path
sys.path.insert(0, str(StdPath(__file__).parent.parent / 'src'))

from tfm_file_list_manager import FileListManager
from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT


class MockConfig:
    """Mock configuration for demo"""
    def __init__(self, date_format='short'):
        self.DATE_FORMAT = date_format
        self.SHOW_HIDDEN_FILES = False


def create_demo_files():
    """Create temporary files with different timestamps for demo"""
    temp_dir = tempfile.mkdtemp(prefix='tfm_date_demo_')
    print(f"Created demo directory: {temp_dir}\n")
    
    now = datetime.now()
    
    # Create files with different timestamps
    files = [
        ("today_morning.txt", now.replace(hour=9, minute=30)),
        ("today_afternoon.txt", now.replace(hour=14, minute=45)),
        ("yesterday.txt", now - timedelta(days=1)),
        ("last_week.txt", now - timedelta(days=7)),
        ("last_month.txt", now - timedelta(days=30)),
        ("last_year.txt", now - timedelta(days=365)),
    ]
    
    created_files = []
    for filename, timestamp in files:
        filepath = StdPath(temp_dir) / filename
        filepath.write_text(f"Demo file created at {timestamp}")
        
        # Set modification time
        os.utime(filepath, (timestamp.timestamp(), timestamp.timestamp()))
        created_files.append((filepath, timestamp))
    
    return temp_dir, created_files


def display_file_list(files, config, format_name):
    """Display file list with specified date format"""
    file_ops = FileListManager(config)
    
    print(f"\n{'='*70}")
    print(f"Format: {format_name}")
    print(f"{'='*70}")
    print(f"{'Filename':<30} {'Size':<10} {'Date/Time':<20}")
    print(f"{'-'*70}")
    
    for filepath, original_timestamp in files:
        from tfm_path import Path
        path = Path(str(filepath))
        size_str, date_str = file_ops.get_file_info(path)
        
        filename = filepath.name
        print(f"{filename:<30} {size_str:<10} {date_str:<20}")
    
    print(f"{'='*70}")


def demo_all_formats():
    """Demonstrate all three date format variations"""
    
    print("=" * 70)
    print("TFM Date Format Demo")
    print("=" * 70)
    print("\nThis demo shows how files are displayed with different date formats.")
    print("In TFM, press 'z' to open View Options and select 'Cycle date format'.")
    print()
    
    # Create demo files
    temp_dir, files = create_demo_files()
    
    try:
        # Show both formats
        formats = [
            (DATE_FORMAT_SHORT, "Short (YY-MM-DD HH:mm) - Default"),
            (DATE_FORMAT_FULL, "Full (YYYY-MM-DD HH:mm:ss)"),
        ]
        
        for format_type, format_name in formats:
            config = MockConfig(date_format=format_type)
            display_file_list(files, config, format_name)
        
        # Explain the formats
        print("\n" + "=" * 70)
        print("Format Explanations:")
        print("=" * 70)
        
        print("\n1. Short Format (Default):")
        print("   - Always shows: YY-MM-DD HH:mm")
        print("   - Balanced detail, no seconds")
        print("   - Good for general file browsing")
        print("   - Uses ISO 8601 date format with hyphens")
        
        print("\n2. Full Format:")
        print("   - Always shows: YYYY-MM-DD HH:mm:ss")
        print("   - Most detailed, includes seconds")
        print("   - Best for precise timestamp tracking")
        print("   - Uses ISO 8601 date format with hyphens")
        
        print("\n" + "=" * 70)
        print("Configuration:")
        print("=" * 70)
        print("\nTo set default format, add to ~/.tfm/config.py:")
        print("  DATE_FORMAT = 'short'   # or 'full'")
        print("\nTo change format while running TFM:")
        print("  1. Press 'z' to open View Options menu")
        print("  2. Select 'Cycle date format'")
        print("  3. Format toggles: Short <-> Full")
        print("=" * 70)
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up demo directory: {temp_dir}")


def demo_format_cycling():
    """Demonstrate format cycling behavior"""
    
    print("\n\n" + "=" * 70)
    print("Format Cycling Demo")
    print("=" * 70)
    print("\nWhen you press 'z' and select 'Cycle date format', the format toggles:")
    print()
    
    formats = [
        (DATE_FORMAT_SHORT, "Short (YY-MM-DD HH:mm)"),
        (DATE_FORMAT_FULL, "Full (YYYY-MM-DD HH:mm:ss)"),
    ]
    
    now = datetime.now()
    sample_file = now.replace(hour=14, minute=30, second=45)
    
    print(f"{'Cycle':<8} {'Format':<35} {'Example':<25}")
    print("-" * 70)
    
    for i in range(6):  # Show three full cycles
        format_idx = i % len(formats)
        format_type, format_name = formats[format_idx]
        
        config = MockConfig(date_format=format_type)
        file_ops = FileListManager(config)
        
        formatted = file_ops._format_date(sample_file.timestamp())
        
        cycle_num = f"#{i+1}"
        print(f"{cycle_num:<8} {format_name:<35} {formatted:<25}")
    
    print("=" * 70)


if __name__ == '__main__':
    try:
        demo_all_formats()
        demo_format_cycling()
        
        print("\n✓ Demo completed successfully!")
        print("\nTry it in TFM:")
        print("  1. Run: python tfm.py")
        print("  2. Press 'z' for View Options")
        print("  3. Select 'Cycle date format'")
        print("  4. Watch the date column change!")
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
