#!/usr/bin/env python3
"""
Demo: Archive Virtual Directory Browsing

This demo shows how TFM integrates archive browsing into the file manager.
Users can press ENTER on archive files to browse their contents as virtual
directories, navigate within archives, and exit back to the filesystem.
"""

import os
import sys
import tempfile
import zipfile
import tarfile
from pathlib import Path as PathlibPath

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_archive import ArchiveOperations


def create_demo_archive(archive_path, archive_type='zip'):
    """Create a demo archive with sample content"""
    if archive_type == 'zip':
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("README.txt", "This is a demo archive\n")
            zf.writestr("docs/guide.txt", "User guide content\n")
            zf.writestr("docs/api.txt", "API documentation\n")
            zf.writestr("src/main.py", "print('Hello from archive!')\n")
            zf.writestr("src/utils.py", "def helper(): pass\n")
            zf.writestr("data/config.json", '{"setting": "value"}\n')
    elif archive_type == 'tar.gz':
        with tarfile.open(archive_path, 'w:gz') as tf:
            # Create temporary files to add to tar
            with tempfile.TemporaryDirectory() as tmpdir:
                files = {
                    "README.txt": "This is a demo archive\n",
                    "docs/guide.txt": "User guide content\n",
                    "docs/api.txt": "API documentation\n",
                    "src/main.py": "print('Hello from archive!')\n",
                    "src/utils.py": "def helper(): pass\n",
                    "data/config.json": '{"setting": "value"}\n'
                }
                
                for filename, content in files.items():
                    filepath = PathlibPath(tmpdir) / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    filepath.write_text(content)
                    tf.add(filepath, arcname=filename)


def demo_enter_archive():
    """Demo: Entering an archive file"""
    print("=" * 70)
    print("DEMO 1: Entering an Archive File")
    print("=" * 70)
    print()
    print("When you press ENTER on an archive file in TFM:")
    print("1. TFM detects it's an archive (.zip, .tar.gz, etc.)")
    print("2. Creates an archive:// URI")
    print("3. Navigates into the archive as a virtual directory")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "demo.zip"
        create_demo_archive(archive_path, 'zip')
        
        print(f"Archive file: {archive_path.name}")
        print()
        
        # Simulate ENTER key behavior
        selected_file = Path(str(archive_path))
        archive_ops = ArchiveOperations(None, None, None)
        
        if archive_ops.is_archive(selected_file):
            print("✓ Archive detected")
            
            # Create archive URI
            archive_uri = f"archive://{selected_file.absolute()}#"
            archive_path_obj = Path(archive_uri)
            
            print(f"✓ Created URI: {archive_uri}")
            print()
            
            # List contents
            print("Archive contents at root:")
            entries = list(archive_path_obj.iterdir())
            for entry in sorted(entries, key=lambda e: (not e.is_dir(), e.name)):
                marker = "📁" if entry.is_dir() else "📄"
                print(f"  {marker} {entry.name}")
            
            print()
            print("You can now navigate into directories within the archive!")


def demo_path_display():
    """Demo: Path display formatting"""
    print("=" * 70)
    print("DEMO 2: Path Display Formatting")
    print("=" * 70)
    print()
    print("TFM shows archive paths in a clear format:")
    print("  [archive.zip]           - at archive root")
    print("  [archive.zip]/docs      - inside docs folder")
    print("  [archive.zip]/src/utils - nested path")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "project.zip"
        create_demo_archive(archive_path, 'zip')
        
        # Show different path displays
        examples = [
            (f"archive://{archive_path}#", "[project.zip]"),
            (f"archive://{archive_path}#docs", "[project.zip]/docs"),
            (f"archive://{archive_path}#src/utils", "[project.zip]/src/utils"),
        ]
        
        print("Path display examples:")
        for uri, expected_display in examples:
            path_part = uri[10:]  # Remove 'archive://'
            if '#' in path_part:
                arch_path, internal_path = path_part.split('#', 1)
                archive_name = PathlibPath(arch_path).name
                
                if internal_path:
                    display = f"[{archive_name}]/{internal_path}"
                else:
                    display = f"[{archive_name}]"
                
                print(f"  {display}")
                assert display == expected_display, f"Expected {expected_display}"


def demo_backspace_navigation():
    """Demo: Backspace navigation"""
    print("=" * 70)
    print("DEMO 3: Backspace Navigation")
    print("=" * 70)
    print()
    print("Backspace key behavior in archives:")
    print("1. Within archive: navigates to parent directory")
    print("2. At archive root: exits to filesystem directory")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "demo.zip"
        create_demo_archive(archive_path, 'zip')
        
        # Simulate navigation within archive
        print("Starting at: [demo.zip]/src/utils")
        current_path = Path(f"archive://{archive_path}#src/utils")
        
        # Press backspace once
        parent = current_path.parent
        print(f"After backspace: {str(parent).split('#')[1] if '#' in str(parent) else 'root'}")
        print(f"  → [demo.zip]/src")
        
        # Press backspace again
        grandparent = parent.parent
        print(f"After backspace: {str(grandparent).split('#')[1] if '#' in str(grandparent) and not str(grandparent).endswith('#') else 'root'}")
        print(f"  → [demo.zip]")
        
        # Press backspace at root
        print("After backspace at root:")
        print(f"  → Exits to: {tmpdir}")
        print(f"  → Cursor on: demo.zip")


def demo_status_indicator():
    """Demo: Status bar indicator"""
    print("=" * 70)
    print("DEMO 4: Status Bar Indicator")
    print("=" * 70)
    print()
    print("When browsing an archive, the status bar shows:")
    print("  (📦 archive)")
    print()
    print("This helps you know you're in a virtual directory.")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "demo.zip"
        create_demo_archive(archive_path, 'zip')
        
        # Check status indicator logic
        archive_uri = f"archive://{archive_path}#"
        current_path_str = archive_uri
        
        if current_path_str.startswith('archive://'):
            print("✓ Archive indicator would be shown")
            print("  Status: (📦 archive)")
        
        # Regular path
        regular_path = str(Path(tmpdir))
        if not regular_path.startswith('archive://'):
            print("✓ Regular directory - no archive indicator")
            print("  Status: ()")


def demo_supported_formats():
    """Demo: Supported archive formats"""
    print("=" * 70)
    print("DEMO 5: Supported Archive Formats")
    print("=" * 70)
    print()
    print("TFM supports browsing these archive formats:")
    print("  • .zip")
    print("  • .tar")
    print("  • .tar.gz, .tgz")
    print("  • .tar.bz2, .tbz2")
    print("  • .tar.xz, .txz")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test zip
        zip_path = PathlibPath(tmpdir) / "test.zip"
        create_demo_archive(zip_path, 'zip')
        
        # Test tar.gz
        targz_path = PathlibPath(tmpdir) / "test.tar.gz"
        create_demo_archive(targz_path, 'tar.gz')
        
        archive_ops = ArchiveOperations(None, None, None)
        
        print("Testing format detection:")
        for path in [zip_path, targz_path]:
            path_obj = Path(str(path))
            if archive_ops.is_archive(path_obj):
                print(f"  ✓ {path.name} - detected and browsable")


if __name__ == '__main__':
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Archive Virtual Directory Browsing Demo" + " " * 14 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        demo_enter_archive()
        print()
        
        demo_path_display()
        print()
        
        demo_backspace_navigation()
        print()
        
        demo_status_indicator()
        print()
        
        demo_supported_formats()
        print()
        
        print("=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
        print()
        print("To try this in TFM:")
        print("1. Launch TFM")
        print("2. Navigate to a directory with archive files")
        print("3. Press ENTER on an archive file")
        print("4. Use arrow keys to navigate within the archive")
        print("5. Press BACKSPACE to go up or exit the archive")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
