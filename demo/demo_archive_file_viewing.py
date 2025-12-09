#!/usr/bin/env python3
"""
Demo: Archive File Viewing

This demo shows how TFM's text viewer can display files from within
archive files without extracting them to disk.

Features demonstrated:
1. Viewing text files from ZIP archives
2. Viewing text files from TAR archives
3. Viewing files in nested directories within archives
4. Archive path display in viewer header
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


def create_demo_archives():
    """Create demo archive files with various content"""
    temp_dir = tempfile.mkdtemp(prefix='tfm_archive_demo_')
    temp_path = PathlibPath(temp_dir)
    
    print(f"Creating demo archives in: {temp_dir}\n")
    
    # Create a ZIP archive with various files
    zip_path = temp_path / 'demo.zip'
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Root level file
        zf.writestr('readme.txt', 
                   'Welcome to the Archive Viewer Demo!\n\n'
                   'This file is being viewed directly from inside a ZIP archive\n'
                   'without being extracted to disk.\n\n'
                   'TFM uses the archive:// URI scheme to access files within archives.')
        
        # Nested directory structure
        zf.writestr('docs/guide.txt',
                   'User Guide\n'
                   '==========\n\n'
                   'This file is in a nested directory: docs/guide.txt\n\n'
                   'You can navigate through archive contents just like\n'
                   'regular directories using ENTER and backspace keys.')
        
        # Python source file (for syntax highlighting demo)
        zf.writestr('src/example.py',
                   '#!/usr/bin/env python3\n'
                   '"""Example Python file in archive"""\n\n'
                   'def hello_from_archive():\n'
                   '    """Greet from inside an archive"""\n'
                   '    print("Hello from inside a ZIP file!")\n'
                   '    return True\n\n'
                   'if __name__ == "__main__":\n'
                   '    hello_from_archive()\n')
        
        # JSON file
        zf.writestr('config/settings.json',
                   '{\n'
                   '  "app_name": "TFM Archive Viewer",\n'
                   '  "version": "1.0",\n'
                   '  "features": [\n'
                   '    "View files in archives",\n'
                   '    "Syntax highlighting",\n'
                   '    "No extraction needed"\n'
                   '  ]\n'
                   '}\n')
    
    # Create a TAR archive
    tar_path = temp_path / 'demo.tar'
    with tarfile.open(tar_path, 'w') as tf:
        import io
        
        # Add a text file
        content = ('TAR Archive Demo\n'
                  '================\n\n'
                  'This file is inside a TAR archive.\n'
                  'TFM supports multiple archive formats:\n'
                  '- ZIP (.zip)\n'
                  '- TAR (.tar, .tar.gz, .tgz, .tar.bz2, .tar.xz)\n')
        data = content.encode('utf-8')
        tarinfo = tarfile.TarInfo(name='readme.txt')
        tarinfo.size = len(data)
        tf.addfile(tarinfo, io.BytesIO(data))
    
    return temp_dir, zip_path, tar_path


def demo_archive_paths(zip_path, tar_path):
    """Demonstrate archive path creation and usage"""
    print("=" * 70)
    print("Archive Path Format")
    print("=" * 70)
    print()
    print("Archive paths use the format: archive://path/to/archive.ext#internal/path")
    print()
    
    # ZIP archive paths
    print("ZIP Archive Paths:")
    print(f"  Root:           archive://{zip_path}#")
    print(f"  Root file:      archive://{zip_path}#readme.txt")
    print(f"  Nested file:    archive://{zip_path}#docs/guide.txt")
    print(f"  Python file:    archive://{zip_path}#src/example.py")
    print(f"  JSON file:      archive://{zip_path}#config/settings.json")
    print()
    
    # TAR archive paths
    print("TAR Archive Paths:")
    print(f"  Root:           archive://{tar_path}#")
    print(f"  Root file:      archive://{tar_path}#readme.txt")
    print()


def demo_read_from_archive(zip_path):
    """Demonstrate reading file content from archives"""
    print("=" * 70)
    print("Reading Files from Archives")
    print("=" * 70)
    print()
    
    # Create archive path
    archive_uri = f"archive://{zip_path}#readme.txt"
    archive_path = Path(archive_uri)
    
    print(f"Reading: {archive_uri}")
    print()
    
    # Read the content
    content = archive_path.read_text()
    
    print("Content:")
    print("-" * 70)
    print(content)
    print("-" * 70)
    print()


def demo_nested_files(zip_path):
    """Demonstrate accessing nested files in archives"""
    print("=" * 70)
    print("Accessing Nested Files")
    print("=" * 70)
    print()
    
    # Access a file in a nested directory
    archive_uri = f"archive://{zip_path}#docs/guide.txt"
    archive_path = Path(archive_uri)
    
    print(f"Reading nested file: {archive_uri}")
    print()
    
    # Read the content
    content = archive_path.read_text()
    
    print("Content:")
    print("-" * 70)
    print(content)
    print("-" * 70)
    print()


def demo_file_properties(zip_path):
    """Demonstrate file properties for archive paths"""
    print("=" * 70)
    print("Archive Path Properties")
    print("=" * 70)
    print()
    
    # Create archive path
    archive_uri = f"archive://{zip_path}#src/example.py"
    archive_path = Path(archive_uri)
    
    print(f"Path: {archive_uri}")
    print()
    print(f"  name:       {archive_path.name}")
    print(f"  stem:       {archive_path.stem}")
    print(f"  suffix:     {archive_path.suffix}")
    print(f"  scheme:     {archive_path.get_scheme()}")
    print(f"  exists:     {archive_path.exists()}")
    print(f"  is_file:    {archive_path.is_file()}")
    print(f"  is_dir:     {archive_path.is_dir()}")
    print()


def demo_viewer_integration():
    """Demonstrate text viewer integration"""
    print("=" * 70)
    print("Text Viewer Integration")
    print("=" * 70)
    print()
    print("In TFM, you can view files from archives by:")
    print()
    print("1. Navigate to an archive file (e.g., demo.zip)")
    print("2. Press ENTER to enter the archive as a virtual directory")
    print("3. Navigate to any text file within the archive")
    print("4. Press ENTER or 'v' to view the file")
    print()
    print("The text viewer will:")
    print("  - Display the file content with syntax highlighting")
    print("  - Show the full archive path in the header")
    print("  - Support all normal viewer features (search, scroll, etc.)")
    print("  - Read directly from the archive (no temporary files)")
    print()
    print("Header format: ARCHIVE: archive.zip#internal/path/file.txt")
    print()


def main():
    """Run the demo"""
    print()
    print("=" * 70)
    print("TFM Archive File Viewing Demo")
    print("=" * 70)
    print()
    
    # Create demo archives
    temp_dir, zip_path, tar_path = create_demo_archives()
    
    try:
        # Demonstrate archive paths
        demo_archive_paths(zip_path, tar_path)
        
        # Demonstrate reading from archives
        demo_read_from_archive(zip_path)
        
        # Demonstrate nested files
        demo_nested_files(zip_path)
        
        # Demonstrate file properties
        demo_file_properties(zip_path)
        
        # Demonstrate viewer integration
        demo_viewer_integration()
        
        print("=" * 70)
        print("Demo Complete")
        print("=" * 70)
        print()
        print(f"Demo archives created in: {temp_dir}")
        print()
        print("To try the viewer interactively:")
        print(f"  1. Run TFM: python3 tfm.py")
        print(f"  2. Navigate to: {temp_dir}")
        print(f"  3. Press ENTER on demo.zip to browse its contents")
        print(f"  4. Navigate to any text file and press ENTER to view it")
        print()
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    # Note: We don't clean up temp_dir so user can explore the archives


if __name__ == '__main__':
    main()
