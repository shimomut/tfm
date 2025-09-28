#!/usr/bin/env python3
"""
Demo script for TFM Archive Operations with cross-storage support

This script demonstrates:
1. Creating archives from local files
2. Creating archives from S3 files (if S3 is available)
3. Extracting archives to local storage
4. Extracting archives to S3 storage (if S3 is available)
5. Cross-storage archive operations (Local ↔ S3)
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path as PathlibPath

# Add the src directory to the path so we can import TFM modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_archive import ArchiveOperations
from tfm_log_manager import LogManager


class ArchiveDemo:
    """Demo class for archive operations"""
    
    def __init__(self):
        """Initialize the demo"""
        # Create a log manager for testing
        self.log_manager = LogManager(None)
        self.archive_ops = ArchiveOperations(self.log_manager)
        
        # Create temporary directory for demo files
        self.temp_dir = PathlibPath(tempfile.mkdtemp(prefix='tfm_archive_demo_'))
        print(f"Demo working directory: {self.temp_dir}")
        
        # Create some test files
        self.create_test_files()
    
    def create_test_files(self):
        """Create test files and directories for the demo"""
        print("\n=== Creating Test Files ===")
        
        # Create test directory structure
        test_dir = self.temp_dir / "test_data"
        test_dir.mkdir()
        
        # Create some test files
        (test_dir / "file1.txt").write_text("This is test file 1\nWith multiple lines\n")
        (test_dir / "file2.txt").write_text("This is test file 2\nWith different content\n")
        
        # Create a subdirectory with files
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.txt").write_text("This is a nested file\n")
        (subdir / "data.json").write_text('{"key": "value", "number": 42}\n')
        
        # Create individual files for single-file compression
        (self.temp_dir / "single_file.txt").write_text("This is a single file for compression testing\n" * 100)
        
        print(f"Created test files in: {test_dir}")
        print(f"Created single file: {self.temp_dir / 'single_file.txt'}")
    
    def demo_local_archive_creation(self):
        """Demo creating archives from local files"""
        print("\n=== Demo: Local Archive Creation ===")
        
        test_dir = self.temp_dir / "test_data"
        archives_dir = self.temp_dir / "archives"
        archives_dir.mkdir(exist_ok=True)
        
        # Get list of files to archive
        files_to_archive = [
            Path(test_dir / "file1.txt"),
            Path(test_dir / "file2.txt"),
            Path(test_dir / "subdir")
        ]
        
        # Test different archive formats
        formats = [
            ('tar.gz', 'test_archive.tar.gz'),
            ('tar.bz2', 'test_archive.tar.bz2'),
            ('tar.xz', 'test_archive.tar.xz'),
            ('zip', 'test_archive.zip'),
            ('tar', 'test_archive.tar')
        ]
        
        for format_type, filename in formats:
            print(f"\nCreating {format_type} archive: {filename}")
            archive_path = Path(archives_dir / filename)
            
            success = self.archive_ops.create_archive(files_to_archive, archive_path, format_type)
            
            if success:
                print(f"✓ Successfully created: {archive_path}")
                if archive_path.exists():
                    size = archive_path.stat().st_size
                    print(f"  Archive size: {size:,} bytes")
            else:
                print(f"✗ Failed to create: {archive_path}")
    
    def demo_single_file_compression(self):
        """Demo compressing single files"""
        print("\n=== Demo: Single File Compression ===")
        
        single_file = Path(self.temp_dir / "single_file.txt")
        compressed_dir = self.temp_dir / "compressed"
        compressed_dir.mkdir(exist_ok=True)
        
        # Test single file compression formats
        formats = [
            ('gzip', 'single_file.txt.gz'),
            ('bzip2', 'single_file.txt.bz2'),
            ('xz', 'single_file.txt.xz')
        ]
        
        for format_type, filename in formats:
            print(f"\nCompressing with {format_type}: {filename}")
            compressed_path = Path(compressed_dir / filename)
            
            # For single file compression, we need to handle it differently
            # The archive operations expect a list of files
            success = self.archive_ops.create_archive([single_file], compressed_path, format_type)
            
            if success:
                print(f"✓ Successfully compressed: {compressed_path}")
                if compressed_path.exists():
                    original_size = single_file.stat().st_size
                    compressed_size = compressed_path.stat().st_size
                    ratio = (1 - compressed_size / original_size) * 100
                    print(f"  Original size: {original_size:,} bytes")
                    print(f"  Compressed size: {compressed_size:,} bytes")
                    print(f"  Compression ratio: {ratio:.1f}%")
            else:
                print(f"✗ Failed to compress: {compressed_path}")
    
    def demo_archive_extraction(self):
        """Demo extracting archives"""
        print("\n=== Demo: Archive Extraction ===")
        
        archives_dir = self.temp_dir / "archives"
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        # Find archives to extract
        if not archives_dir.exists():
            print("No archives directory found. Run archive creation demo first.")
            return
        
        archive_files = list(archives_dir.glob("*"))
        
        for archive_file in archive_files:
            if self.archive_ops.is_archive(Path(archive_file)):
                print(f"\nExtracting: {archive_file.name}")
                
                # Create extraction subdirectory
                extract_subdir = Path(extract_dir / f"from_{archive_file.stem}")
                
                success = self.archive_ops.extract_archive(
                    Path(archive_file), 
                    extract_subdir, 
                    overwrite=True
                )
                
                if success:
                    print(f"✓ Successfully extracted to: {extract_subdir}")
                    # List extracted contents
                    if extract_subdir.exists():
                        extracted_items = list(extract_subdir.rglob("*"))
                        print(f"  Extracted {len(extracted_items)} items:")
                        for item in extracted_items[:10]:  # Show first 10 items
                            rel_path = item.relative_to(extract_subdir)
                            item_type = "DIR" if item.is_dir() else "FILE"
                            print(f"    {item_type}: {rel_path}")
                        if len(extracted_items) > 10:
                            print(f"    ... and {len(extracted_items) - 10} more items")
                else:
                    print(f"✗ Failed to extract: {archive_file.name}")
    
    def demo_archive_listing(self):
        """Demo listing archive contents"""
        print("\n=== Demo: Archive Content Listing ===")
        
        archives_dir = self.temp_dir / "archives"
        
        if not archives_dir.exists():
            print("No archives directory found. Run archive creation demo first.")
            return
        
        archive_files = list(archives_dir.glob("*"))
        
        for archive_file in archive_files:
            if self.archive_ops.is_archive(Path(archive_file)):
                print(f"\nListing contents of: {archive_file.name}")
                
                contents = self.archive_ops.list_archive_contents(Path(archive_file))
                
                if contents:
                    print(f"  Archive contains {len(contents)} items:")
                    for name, size, item_type in contents[:15]:  # Show first 15 items
                        size_str = f"{size:,}" if size > 0 else "-"
                        print(f"    {item_type.upper():4} {size_str:>10} {name}")
                    if len(contents) > 15:
                        print(f"    ... and {len(contents) - 15} more items")
                else:
                    print("  Could not list archive contents")
    
    def demo_s3_operations(self):
        """Demo S3 archive operations (if S3 is available)"""
        print("\n=== Demo: S3 Archive Operations ===")
        
        try:
            # Try to create an S3 path to test if S3 support is available
            s3_path = Path("s3://test-bucket/test-file.txt")
            print(f"S3 support detected: {s3_path.get_scheme()}")
            
            print("Note: S3 operations require valid AWS credentials and bucket access.")
            print("This demo shows the interface but won't perform actual S3 operations.")
            print("To test S3 operations:")
            print("1. Configure AWS credentials")
            print("2. Create or use an existing S3 bucket")
            print("3. Update the S3 paths in this demo")
            
            # Example S3 operations (commented out to avoid errors)
            """
            # Create archive from local files and save to S3
            local_files = [Path(self.temp_dir / "test_data" / "file1.txt")]
            s3_archive = Path("s3://your-bucket/archives/test_from_local.tar.gz")
            success = self.archive_ops.create_archive(local_files, s3_archive, 'tar.gz')
            
            # Extract S3 archive to local directory
            local_extract_dir = Path(self.temp_dir / "from_s3")
            success = self.archive_ops.extract_archive(s3_archive, local_extract_dir)
            """
            
        except ImportError:
            print("S3 support not available. Install boto3 and configure AWS credentials to enable S3 operations.")
        except Exception as e:
            print(f"S3 support check failed: {e}")
    
    def run_all_demos(self):
        """Run all demo functions"""
        print("TFM Archive Operations Demo")
        print("=" * 50)
        
        try:
            self.demo_local_archive_creation()
            self.demo_single_file_compression()
            self.demo_archive_listing()
            self.demo_archive_extraction()
            self.demo_s3_operations()
            
            print("\n=== Demo Summary ===")
            print("✓ Local archive creation")
            print("✓ Single file compression")
            print("✓ Archive content listing")
            print("✓ Archive extraction")
            print("✓ S3 operations interface (requires AWS setup)")
            
        except Exception as e:
            print(f"\nDemo error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files"""
        print(f"\n=== Cleanup ===")
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory: {e}")


def main():
    """Main function"""
    demo = ArchiveDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()