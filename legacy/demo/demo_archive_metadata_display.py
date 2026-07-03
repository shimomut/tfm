#!/usr/bin/env python3
"""
Demo: Archive Metadata Display Feature

This demo shows how TFM displays detailed metadata for files within archives,
including uncompressed size, compressed size, compression ratio, archive type,
and internal path.
"""

import os
import sys
import tempfile
import zipfile
import tarfile
from pathlib import Path as PathlibPath

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_info_dialog import InfoDialogHelpers


def demo_zip_file_metadata():
    """Demo: Display metadata for a file in a ZIP archive"""
    print("=" * 70)
    print("DEMO: ZIP Archive File Metadata Display")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test zip archive with various files
        archive_path = PathlibPath(tmpdir) / "documents.zip"
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add a text file with good compression
            text_content = "Lorem ipsum dolor sit amet. " * 100
            zf.writestr("readme.txt", text_content)
            
            # Add a small file
            zf.writestr("config.json", '{"setting": "value"}')
            
            # Add a file in a subdirectory
            zf.writestr("docs/manual.txt", "User manual content here.")
        
        print(f"Created test archive: {archive_path}")
        print()
        
        # Show metadata for the text file
        print("Viewing metadata for 'readme.txt' inside the archive:")
        print("-" * 70)
        
        archive_uri = f"archive://{archive_path}#readme.txt"
        file_path = Path(archive_uri)
        
        # Mock info dialog to capture output
        class MockInfoDialog:
            def show(self, title, lines):
                print(f"Title: {title}")
                print()
                for line in lines:
                    print(f"  {line}")
        
        mock_dialog = MockInfoDialog()
        InfoDialogHelpers.show_file_details(mock_dialog, [file_path], None)
        print()


def demo_tar_archive_metadata():
    """Demo: Display metadata for a file in a TAR.GZ archive"""
    print("=" * 70)
    print("DEMO: TAR.GZ Archive File Metadata Display")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test tar.gz archive
        archive_path = PathlibPath(tmpdir) / "backup.tar.gz"
        
        with tarfile.open(archive_path, 'w:gz') as tf:
            # Create files in memory
            import io
            
            # Add a log file
            log_content = b"[INFO] Application started\n" * 50
            log_data = io.BytesIO(log_content)
            log_info = tarfile.TarInfo(name="logs/app.log")
            log_info.size = len(log_content)
            tf.addfile(log_info, log_data)
            
            # Add a config file
            config_content = b"# Configuration file\nport=8080\n"
            config_data = io.BytesIO(config_content)
            config_info = tarfile.TarInfo(name="config.conf")
            config_info.size = len(config_content)
            tf.addfile(config_info, config_data)
        
        print(f"Created test archive: {archive_path}")
        print()
        
        # Show metadata for the log file
        print("Viewing metadata for 'logs/app.log' inside the archive:")
        print("-" * 70)
        
        archive_uri = f"archive://{archive_path}#logs/app.log"
        file_path = Path(archive_uri)
        
        # Mock info dialog
        class MockInfoDialog:
            def show(self, title, lines):
                print(f"Title: {title}")
                print()
                for line in lines:
                    print(f"  {line}")
        
        mock_dialog = MockInfoDialog()
        InfoDialogHelpers.show_file_details(mock_dialog, [file_path], None)
        print()


def demo_directory_metadata():
    """Demo: Display metadata for a directory within an archive"""
    print("=" * 70)
    print("DEMO: Archive Directory Metadata Display")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test archive with directories
        archive_path = PathlibPath(tmpdir) / "project.zip"
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            # Create directory structure
            zf.writestr("src/", "")
            zf.writestr("src/main.py", "print('Hello')")
            zf.writestr("tests/", "")
            zf.writestr("tests/test_main.py", "def test(): pass")
        
        print(f"Created test archive: {archive_path}")
        print()
        
        # Show metadata for a directory
        print("Viewing metadata for 'src/' directory inside the archive:")
        print("-" * 70)
        
        archive_uri = f"archive://{archive_path}#src/"
        dir_path = Path(archive_uri)
        
        # Mock info dialog
        class MockInfoDialog:
            def show(self, title, lines):
                print(f"Title: {title}")
                print()
                for line in lines:
                    print(f"  {line}")
        
        mock_dialog = MockInfoDialog()
        InfoDialogHelpers.show_file_details(mock_dialog, [dir_path], None)
        print()
        
        print("Note: Directories don't show size/compression information")
        print()


def demo_comparison_with_regular_file():
    """Demo: Compare archive file metadata with regular file metadata"""
    print("=" * 70)
    print("DEMO: Comparison - Archive File vs Regular File")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a regular file
        regular_file = PathlibPath(tmpdir) / "document.txt"
        content = "This is a regular file on the filesystem."
        regular_file.write_text(content)
        
        # Create an archive with the same content
        archive_path = PathlibPath(tmpdir) / "archive.zip"
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("document.txt", content)
        
        print("1. Regular File Metadata:")
        print("-" * 70)
        
        regular_path = Path(str(regular_file))
        
        class MockInfoDialog:
            def show(self, title, lines):
                print(f"Title: {title}")
                print()
                for line in lines:
                    print(f"  {line}")
        
        mock_dialog = MockInfoDialog()
        InfoDialogHelpers.show_file_details(mock_dialog, [regular_path], None)
        print()
        
        print("2. Archive File Metadata:")
        print("-" * 70)
        
        archive_uri = f"archive://{archive_path}#document.txt"
        archive_file_path = Path(archive_uri)
        
        InfoDialogHelpers.show_file_details(mock_dialog, [archive_file_path], None)
        print()
        
        print("Key Differences:")
        print("  • Archive files show 'Archive:' and 'Internal Path:' fields")
        print("  • Archive files show 'Archive Type:' (zip, tar.gz, etc.)")
        print("  • Archive files show both 'Uncompressed Size:' and 'Compressed Size:'")
        print("  • Archive files show 'Compression Ratio:' percentage")
        print()


def demo_multiple_archive_types():
    """Demo: Show metadata for different archive types"""
    print("=" * 70)
    print("DEMO: Multiple Archive Types")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        content = b"Sample content for compression testing. " * 20
        
        # Create different archive types
        archives = []
        
        # ZIP
        zip_path = PathlibPath(tmpdir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.txt", content)
        archives.append(("ZIP", zip_path))
        
        # TAR.GZ
        targz_path = PathlibPath(tmpdir) / "test.tar.gz"
        with tarfile.open(targz_path, 'w:gz') as tf:
            import io
            data = io.BytesIO(content)
            info = tarfile.TarInfo(name="data.txt")
            info.size = len(content)
            tf.addfile(info, data)
        archives.append(("TAR.GZ", targz_path))
        
        # TAR.BZ2
        tarbz2_path = PathlibPath(tmpdir) / "test.tar.bz2"
        with tarfile.open(tarbz2_path, 'w:bz2') as tf:
            import io
            data = io.BytesIO(content)
            info = tarfile.TarInfo(name="data.txt")
            info.size = len(content)
            tf.addfile(info, data)
        archives.append(("TAR.BZ2", tarbz2_path))
        
        class MockInfoDialog:
            def show(self, title, lines):
                print(f"Title: {title}")
                print()
                for line in lines:
                    print(f"  {line}")
        
        mock_dialog = MockInfoDialog()
        
        for archive_type, archive_path in archives:
            print(f"{archive_type} Archive:")
            print("-" * 70)
            
            archive_uri = f"archive://{archive_path}#data.txt"
            file_path = Path(archive_uri)
            
            InfoDialogHelpers.show_file_details(mock_dialog, [file_path], None)
            print()


if __name__ == '__main__':
    print()
    print("TFM Archive Metadata Display Demo")
    print("=" * 70)
    print()
    print("This demo shows how TFM displays detailed metadata for files")
    print("within archives, including compression information.")
    print()
    
    demo_zip_file_metadata()
    demo_tar_archive_metadata()
    demo_directory_metadata()
    demo_comparison_with_regular_file()
    demo_multiple_archive_types()
    
    print("=" * 70)
    print("Demo Complete!")
    print()
    print("In TFM, you can view file details by:")
    print("  1. Navigate into an archive (press ENTER on a .zip, .tar.gz, etc.)")
    print("  2. Select a file within the archive")
    print("  3. Press the file details key (default: 'i')")
    print()
    print("The file details dialog will show:")
    print("  • Archive file path")
    print("  • Internal path within the archive")
    print("  • Archive type (zip, tar.gz, tar.bz2, etc.)")
    print("  • Uncompressed size")
    print("  • Compressed size")
    print("  • Compression ratio")
    print("  • File permissions")
    print("  • Modification time")
    print()
