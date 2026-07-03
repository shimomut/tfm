#!/usr/bin/env python3
"""
Demo: Progress Message Text Layout Improvements

This demo shows how the text layout system provides intelligent truncation
for progress messages with long filenames.

The demo simulates file operations with various path lengths and terminal widths
to demonstrate how the system preserves essential information while gracefully
handling space constraints.
"""

import sys
import os
import time

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_progress_manager import ProgressManager, OperationType


def print_section(title):
    """Print a section header"""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_subsection(title):
    """Print a subsection header"""
    print()
    print(title)
    print("-" * 80)


def demo_copy_operation():
    """Demonstrate copy operation with long paths"""
    print_section("Copy Operation with Long Nested Paths")
    
    pm = ProgressManager()
    pm.start_operation(OperationType.COPY, 100, "backup_folder")
    pm.update_operation_total(100, "backup_folder")
    
    # Simulate copying files with progressively longer paths
    test_paths = [
        "file.txt",
        "documents/report.pdf",
        "projects/web/assets/image.jpg",
        "projects/web_development/client_sites/acme_corp/assets/images/logo.png",
        "projects/web_development/client_sites/acme_corp/assets/images/products/thumbnails/high_resolution/product_image_final_v3.jpg"
    ]
    
    for i, path in enumerate(test_paths, 1):
        pm.update_progress(path, i * 20)
        
        print_subsection(f"File {i}: {path}")
        
        # Show at different terminal widths
        for width in [120, 100, 80, 60]:
            text = pm.get_progress_text(max_width=width)
            print(f"Width {width:3d}: {text}")
        
        time.sleep(0.3)


def demo_move_operation():
    """Demonstrate move operation"""
    print_section("Move Operation with Long Filenames")
    
    pm = ProgressManager()
    pm.start_operation(OperationType.MOVE, 50, "archive_2024")
    pm.update_operation_total(50, "archive_2024")
    
    test_files = [
        "report.pdf",
        "financial_report_Q4_2024.pdf",
        "financial_analysis_report_december_2024_final_revised_v5.pdf"
    ]
    
    for i, filename in enumerate(test_files, 1):
        path = f"documents/reports/quarterly/2024/Q4/{filename}"
        pm.update_progress(path, i * 15)
        
        print_subsection(f"Moving: {filename}")
        
        for width in [100, 80, 60]:
            text = pm.get_progress_text(max_width=width)
            print(f"Width {width:3d}: {text}")
        
        time.sleep(0.3)


def demo_delete_operation():
    """Demonstrate delete operation"""
    print_section("Delete Operation")
    
    pm = ProgressManager()
    pm.start_operation(OperationType.DELETE, 30, "")
    pm.update_operation_total(30, "")
    
    test_paths = [
        "temp/cache/file.tmp",
        "temp/cache/browser_cache/chrome/profile_1/cache_data/f_000123"
    ]
    
    for i, path in enumerate(test_paths, 1):
        pm.update_progress(path, i * 10)
        
        print_subsection(f"Deleting: {path}")
        
        for width in [80, 60, 50]:
            text = pm.get_progress_text(max_width=width)
            print(f"Width {width:3d}: {text}")
        
        time.sleep(0.3)


def demo_byte_progress():
    """Demonstrate byte progress for large files"""
    print_section("Copy with Byte Progress (Large Files)")
    
    pm = ProgressManager()
    pm.start_operation(OperationType.COPY, 10, "external_drive")
    pm.update_operation_total(10, "external_drive")
    
    large_file = "videos/projects/2024/vacation_footage_4k_uncompressed.mov"
    
    print_subsection("Copying large video file")
    
    # Simulate progress through the file
    file_size = 5 * 1024 * 1024 * 1024  # 5GB
    
    for progress in [0.2, 0.5, 0.8, 1.0]:
        bytes_copied = int(file_size * progress)
        pm.update_progress(large_file, 5)
        pm.update_file_byte_progress(bytes_copied, file_size)
        
        print(f"\nProgress: {int(progress * 100)}%")
        for width in [100, 80, 60]:
            text = pm.get_progress_text(max_width=width)
            print(f"Width {width:3d}: {text}")
        
        time.sleep(0.3)


def demo_archive_operations():
    """Demonstrate archive operations"""
    print_section("Archive Operations")
    
    # Archive creation
    print_subsection("Creating Archive")
    pm = ProgressManager()
    pm.start_operation(OperationType.ARCHIVE_CREATE, 200, "backup_2024_12_31.tar.gz")
    pm.update_operation_total(200, "backup_2024_12_31.tar.gz")
    
    archive_path = "home/user/documents/work/projects/2024/client_projects/website_redesign/assets/images/hero_banner_desktop_2x.png"
    pm.update_progress(archive_path, 150)
    
    for width in [100, 80, 60]:
        text = pm.get_progress_text(max_width=width)
        print(f"Width {width:3d}: {text}")
    
    time.sleep(0.3)
    
    # Archive extraction
    print_subsection("Extracting Archive")
    pm2 = ProgressManager()
    pm2.start_operation(OperationType.ARCHIVE_EXTRACT, 100, "data_backup.zip")
    pm2.update_operation_total(100, "data_backup.zip")
    
    extract_path = "extracted/documents/reports/annual/2024/financial_summary_complete.pdf"
    pm2.update_progress(extract_path, 75)
    
    for width in [100, 80, 60]:
        text = pm2.get_progress_text(max_width=width)
        print(f"Width {width:3d}: {text}")


def demo_comparison():
    """Show before/after comparison"""
    print_section("Key Improvements Summary")
    
    print("""
The text layout system provides several improvements for progress messages:

1. Intelligent Path Abbreviation
   - FilepathSegment abbreviates paths from the middle
   - Preserves important parts (filename, parent directories)
   - Example: "projects/…/high_resolution/product_image_final_v3.jpg"

2. Priority-Based Shortening
   - Essential information (operation, count) is always preserved
   - Optional information (byte progress) removed when space is tight
   - Graceful degradation as terminal width decreases

3. Wide Character Support
   - Correctly handles emoji, CJK characters
   - Accounts for characters that take 2 terminal columns

4. Consistent Behavior
   - All file operations (copy, move, delete) use the same system
   - Archive operations also benefit from intelligent truncation

5. Better User Experience
   - Users can always see meaningful progress information
   - Long filenames don't obscure the operation status
   - Works well on narrow terminals (60 columns and up)
""")


def main():
    """Run all demos"""
    print("=" * 80)
    print("Progress Message Text Layout Improvements Demo")
    print("=" * 80)
    print()
    print("This demo shows how the text layout system intelligently handles")
    print("progress messages with long filenames at various terminal widths.")
    
    try:
        demo_copy_operation()
        demo_move_operation()
        demo_delete_operation()
        demo_byte_progress()
        demo_archive_operations()
        demo_comparison()
        
        print()
        print("=" * 80)
        print("Demo completed successfully!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
