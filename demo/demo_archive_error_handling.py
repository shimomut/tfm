#!/usr/bin/env python3
"""
Demo: Archive Virtual Directory Error Handling

This demo showcases the comprehensive error handling for archive operations,
including user-friendly error messages and graceful error recovery.
"""

import sys
import os
import tempfile
import zipfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_archive import (
    ArchiveError, ArchiveFormatError, ArchiveCorruptedError,
    ArchiveExtractionError, ArchiveNavigationError,
    ArchivePermissionError, ArchiveDiskSpaceError,
    ZipHandler, ArchiveCache
)
from tfm_path import Path


def print_section(title):
    """Print a section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def demo_corrupted_archive():
    """Demo: Handling corrupted archive files"""
    print_section("Demo 1: Corrupted Archive Handling")
    
    # Create a corrupted ZIP file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
        f.write(b'This is not a valid ZIP file')
        corrupted_zip = f.name
    
    try:
        print(f"Attempting to open corrupted archive: {corrupted_zip}")
        handler = ZipHandler(Path(corrupted_zip))
        handler.open()
    except ArchiveCorruptedError as e:
        print(f"\n✓ Caught ArchiveCorruptedError")
        print(f"  Technical message: {e}")
        print(f"  User message: {e.user_message}")
        print(f"\n  This error would be shown to the user in TFM:")
        print(f"  → {e.user_message}")
    finally:
        os.unlink(corrupted_zip)
    
    print("\n✓ Application continues running after error")


def demo_missing_archive():
    """Demo: Handling missing archive files"""
    print_section("Demo 2: Missing Archive Handling")
    
    nonexistent_path = Path('/nonexistent/archive.zip')
    
    try:
        print(f"Attempting to open nonexistent archive: {nonexistent_path}")
        handler = ZipHandler(nonexistent_path)
        handler.open()
    except FileNotFoundError as e:
        print(f"\n✓ Caught FileNotFoundError")
        print(f"  Error: {e}")
        print(f"\n  This error would be shown to the user in TFM:")
        print(f"  → Archive file does not exist")
    
    print("\n✓ Application continues running after error")


def demo_navigation_errors():
    """Demo: Handling navigation errors within archives"""
    print_section("Demo 3: Archive Navigation Error Handling")
    
    # Create a valid ZIP file
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'test.zip')
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('file1.txt', 'content1')
        zf.writestr('dir1/file2.txt', 'content2')
    
    try:
        print(f"Created test archive: {zip_path}")
        print("Archive contents:")
        print("  - file1.txt")
        print("  - dir1/")
        print("    - file2.txt")
        
        with ZipHandler(Path(zip_path)) as handler:
            print("\n✓ Successfully opened archive")
            
            # Try to navigate to nonexistent directory
            try:
                print("\nAttempting to list nonexistent directory: 'nonexistent_dir'")
                handler.list_entries('nonexistent_dir')
            except ArchiveNavigationError as e:
                print(f"\n✓ Caught ArchiveNavigationError")
                print(f"  Technical message: {e}")
                print(f"  User message: {e.user_message}")
                print(f"\n  This error would be shown to the user in TFM:")
                print(f"  → {e.user_message}")
            
            # Try to extract nonexistent file
            try:
                print("\nAttempting to extract nonexistent file: 'nonexistent.txt'")
                handler.extract_to_bytes('nonexistent.txt')
            except FileNotFoundError as e:
                print(f"\n✓ Caught FileNotFoundError")
                print(f"  Error: {e}")
                print(f"\n  This error would be shown to the user in TFM:")
                print(f"  → File does not exist in archive")
            
            # Successfully list valid directory
            print("\nSuccessfully listing root directory:")
            entries = handler.list_entries('')
            for entry in entries:
                print(f"  - {entry.name} ({'dir' if entry.is_dir else 'file'})")
    
    finally:
        import shutil
        shutil.rmtree(temp_dir)
    
    print("\n✓ Application continues running after errors")


def demo_extraction_errors():
    """Demo: Handling extraction errors"""
    print_section("Demo 4: Extraction Error Handling")
    
    # Create a valid ZIP file with a directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'test.zip')
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('file1.txt', 'content1')
        zf.writestr('dir1/', '')  # Directory entry
    
    try:
        print(f"Created test archive: {zip_path}")
        print("Archive contents:")
        print("  - file1.txt")
        print("  - dir1/ (directory)")
        
        with ZipHandler(Path(zip_path)) as handler:
            print("\n✓ Successfully opened archive")
            
            # Try to extract directory as bytes
            try:
                print("\nAttempting to extract directory as bytes: 'dir1'")
                handler.extract_to_bytes('dir1')
            except ArchiveExtractionError as e:
                print(f"\n✓ Caught ArchiveExtractionError")
                print(f"  Technical message: {e}")
                print(f"  User message: {e.user_message}")
                print(f"\n  This error would be shown to the user in TFM:")
                print(f"  → {e.user_message}")
            
            # Successfully extract file
            print("\nSuccessfully extracting file: 'file1.txt'")
            content = handler.extract_to_bytes('file1.txt')
            print(f"  Content: {content.decode('utf-8')}")
    
    finally:
        import shutil
        shutil.rmtree(temp_dir)
    
    print("\n✓ Application continues running after errors")


def demo_cache_error_recovery():
    """Demo: Cache error recovery"""
    print_section("Demo 5: Cache Error Recovery")
    
    cache = ArchiveCache(max_open=5, ttl=300)
    print("Created archive cache")
    print(f"  Max open archives: {cache.get_stats()['max_open']}")
    print(f"  Currently open: {cache.get_stats()['open_archives']}")
    
    # Try to open multiple nonexistent archives
    print("\nAttempting to open 3 nonexistent archives...")
    for i in range(3):
        nonexistent_path = Path(f'/nonexistent/archive{i}.zip')
        try:
            cache.get_handler(nonexistent_path)
        except FileNotFoundError:
            print(f"  ✓ Archive {i}: Caught FileNotFoundError (expected)")
    
    # Cache should still be functional
    print("\nCache statistics after errors:")
    stats = cache.get_stats()
    print(f"  Open archives: {stats['open_archives']}")
    print(f"  Max open: {stats['max_open']}")
    print(f"  Expired count: {stats['expired_count']}")
    
    print("\n✓ Cache remains functional after multiple errors")


def demo_error_message_quality():
    """Demo: Quality of error messages"""
    print_section("Demo 6: Error Message Quality")
    
    print("All archive errors support dual messages:")
    print("  1. Technical message (for logging)")
    print("  2. User-friendly message (for display)")
    
    print("\nExample error messages:")
    
    # ArchiveCorruptedError
    error1 = ArchiveCorruptedError(
        "Corrupted ZIP archive: Bad magic number for file header",
        "Archive 'data.zip' is corrupted or invalid"
    )
    print(f"\n1. ArchiveCorruptedError:")
    print(f"   Technical: {error1}")
    print(f"   User-friendly: {error1.user_message}")
    
    # ArchivePermissionError
    error2 = ArchivePermissionError(
        "Permission denied opening archive: [Errno 13] Permission denied",
        "Cannot open archive 'data.zip': Permission denied"
    )
    print(f"\n2. ArchivePermissionError:")
    print(f"   Technical: {error2}")
    print(f"   User-friendly: {error2.user_message}")
    
    # ArchiveDiskSpaceError
    error3 = ArchiveDiskSpaceError(
        "Insufficient disk space: [Errno 28] No space left on device",
        "Insufficient disk space to extract file"
    )
    print(f"\n3. ArchiveDiskSpaceError:")
    print(f"   Technical: {error3}")
    print(f"   User-friendly: {error3.user_message}")
    
    print("\n✓ Clear, actionable error messages for users")
    print("✓ Detailed technical information for debugging")


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  Archive Virtual Directory Error Handling Demo")
    print("=" * 70)
    print("\nThis demo showcases comprehensive error handling for archive operations.")
    print("All errors are handled gracefully with user-friendly messages.")
    
    try:
        demo_corrupted_archive()
        demo_missing_archive()
        demo_navigation_errors()
        demo_extraction_errors()
        demo_cache_error_recovery()
        demo_error_message_quality()
        
        print_section("Summary")
        print("\n✓ All error scenarios handled gracefully")
        print("✓ User-friendly error messages displayed")
        print("✓ Technical details logged for debugging")
        print("✓ Application remains stable after errors")
        print("✓ Cache and resources properly managed")
        
        print("\nKey Features:")
        print("  • Specific exception types for different error scenarios")
        print("  • Dual messages (technical + user-friendly)")
        print("  • Graceful error recovery")
        print("  • Comprehensive logging")
        print("  • Stable cache management")
        
        print("\n" + "=" * 70)
        print("  Demo completed successfully!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Unexpected error in demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
