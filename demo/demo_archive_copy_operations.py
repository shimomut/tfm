#!/usr/bin/env python3
"""
Demo: Archive Copy Operations

This demo shows how to copy files and directories from archive virtual directories
to local filesystem or other storage systems.
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path as PathlibPath

# Add src directory to path
sys.path.insert(0, str(PathlibPath(__file__).parent.parent / 'src'))

from tfm_path import Path


def create_demo_archive(archive_path):
    """Create a demo archive with sample files"""
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add some sample files
        zf.writestr('README.txt', 'This is a demo archive\n')
        zf.writestr('docs/guide.txt', 'User guide content\n')
        zf.writestr('docs/api.txt', 'API documentation\n')
        zf.writestr('src/main.py', 'print("Hello from archive")\n')
        zf.writestr('src/utils.py', 'def helper(): pass\n')
        zf.writestr('data/config.json', '{"setting": "value"}\n')


def demo_copy_single_file():
    """Demo: Copy a single file from an archive"""
    print("\n" + "=" * 60)
    print("Demo 1: Copy Single File from Archive")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create demo archive
        archive_path = PathlibPath(tmpdir) / 'demo.zip'
        create_demo_archive(archive_path)
        print(f"Created demo archive: {archive_path}")
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'extracted'
        dest_dir.mkdir()
        
        # Copy a single file from the archive
        archive_file = Path(f"archive://{archive_path}#README.txt")
        dest_file = Path(dest_dir / 'README.txt')
        
        print(f"\nCopying: {archive_file}")
        print(f"To: {dest_file}")
        
        success = archive_file.copy_to(dest_file)
        
        if success:
            print("✓ Copy successful!")
            content = dest_file.read_text()
            print(f"Content: {content.strip()}")
        else:
            print("✗ Copy failed")


def demo_copy_directory():
    """Demo: Copy an entire directory from an archive"""
    print("\n" + "=" * 60)
    print("Demo 2: Copy Directory from Archive")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create demo archive
        archive_path = PathlibPath(tmpdir) / 'demo.zip'
        create_demo_archive(archive_path)
        print(f"Created demo archive: {archive_path}")
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'extracted'
        dest_dir.mkdir()
        
        # Copy entire docs directory from the archive
        archive_dir = Path(f"archive://{archive_path}#docs")
        dest_path = Path(dest_dir / 'docs')
        
        print(f"\nCopying directory: {archive_dir}")
        print(f"To: {dest_path}")
        
        success = archive_dir.copy_to(dest_path)
        
        if success:
            print("✓ Copy successful!")
            print("\nExtracted files:")
            for file in dest_path.rglob('*'):
                if file.is_file():
                    rel_path = file.relative_to(dest_path)
                    print(f"  - {rel_path}")
        else:
            print("✗ Copy failed")


def demo_browse_and_copy():
    """Demo: Browse archive contents and copy selected files"""
    print("\n" + "=" * 60)
    print("Demo 3: Browse Archive and Copy Files")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create demo archive
        archive_path = PathlibPath(tmpdir) / 'demo.zip'
        create_demo_archive(archive_path)
        print(f"Created demo archive: {archive_path}")
        
        # Browse archive root
        archive_root = Path(f"archive://{archive_path}#")
        
        print("\nArchive contents:")
        for entry in archive_root.iterdir():
            if entry.is_dir():
                print(f"  [DIR]  {entry.name}/")
            else:
                size = entry.stat().st_size
                print(f"  [FILE] {entry.name} ({size} bytes)")
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'selected'
        dest_dir.mkdir()
        
        # Copy selected files
        print("\nCopying selected files:")
        files_to_copy = ['README.txt', 'src/main.py']
        
        for file_path in files_to_copy:
            archive_file = Path(f"archive://{archive_path}#{file_path}")
            dest_file = Path(dest_dir / PathlibPath(file_path).name)
            
            print(f"  Copying: {file_path}")
            success = archive_file.copy_to(dest_file)
            
            if success:
                print(f"    ✓ Copied to {dest_file.name}")
            else:
                print(f"    ✗ Failed")


def demo_nested_directory_copy():
    """Demo: Copy nested directory structure from archive"""
    print("\n" + "=" * 60)
    print("Demo 4: Copy Nested Directory Structure")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create demo archive
        archive_path = PathlibPath(tmpdir) / 'demo.zip'
        create_demo_archive(archive_path)
        print(f"Created demo archive: {archive_path}")
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / 'project'
        dest_dir.mkdir()
        
        # Copy src directory (which contains Python files)
        archive_dir = Path(f"archive://{archive_path}#src")
        dest_path = Path(dest_dir / 'src')
        
        print(f"\nCopying nested directory: {archive_dir}")
        print(f"To: {dest_path}")
        
        success = archive_dir.copy_to(dest_path)
        
        if success:
            print("✓ Copy successful!")
            print("\nDirectory structure:")
            for file in dest_path.rglob('*'):
                if file.is_file():
                    rel_path = file.relative_to(dest_dir)
                    content = file.read_text().strip()
                    print(f"  {rel_path}")
                    print(f"    Content: {content[:50]}...")
        else:
            print("✗ Copy failed")


def main():
    """Run all demos"""
    print("=" * 60)
    print("Archive Copy Operations Demo")
    print("=" * 60)
    print("\nThis demo shows how to copy files and directories from")
    print("archive virtual directories to the local filesystem.")
    
    try:
        demo_copy_single_file()
        demo_copy_directory()
        demo_browse_and_copy()
        demo_nested_directory_copy()
        
        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
