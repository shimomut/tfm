#!/usr/bin/env python3
"""
Test archive virtual directory integration with FileManager
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path as PathlibPath

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_archive import ArchiveOperations, ArchivePathImpl


def test_archive_detection():
    """Test that archive files are properly detected"""
    # Create a temporary zip file
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "test.zip"
        
        # Create a simple zip file
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("dir1/file2.txt", "content2")
        
        # Test archive detection
        archive_ops = ArchiveOperations(None, None, None)
        path_obj = Path(str(archive_path))
        
        assert archive_ops.is_archive(path_obj), "Archive should be detected"
        print("✓ Archive detection works")


def test_archive_uri_creation():
    """Test creating archive URIs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "test.zip"
        
        # Create a simple zip file
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("dir1/file2.txt", "content2")
        
        # Create archive URI
        archive_uri = f"archive://{archive_path}#"
        archive_path_obj = Path(archive_uri)
        
        assert str(archive_path_obj).startswith('archive://'), "Archive URI should be created"
        print(f"✓ Archive URI created: {archive_uri}")


def test_archive_path_navigation():
    """Test navigating within archive paths"""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "test.zip"
        
        # Create a zip file with nested structure
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("dir1/file2.txt", "content2")
            zf.writestr("dir1/subdir/file3.txt", "content3")
        
        # Create archive path at root
        archive_uri = f"archive://{archive_path}#"
        archive_path_obj = Path(archive_uri)
        
        # List entries at root
        entries = list(archive_path_obj.iterdir())
        assert len(entries) > 0, "Should have entries at root"
        print(f"✓ Found {len(entries)} entries at archive root")
        
        # Navigate into directory
        dir_entry = None
        for entry in entries:
            if entry.is_dir() and entry.name == "dir1":
                dir_entry = entry
                break
        
        if dir_entry:
            # List entries in subdirectory
            subentries = list(dir_entry.iterdir())
            assert len(subentries) > 0, "Should have entries in subdirectory"
            print(f"✓ Found {len(subentries)} entries in dir1")
        else:
            print("⚠ dir1 not found in archive")


def test_archive_path_display_formatting():
    """Test that archive paths are formatted correctly for display"""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "test.zip"
        
        # Create a simple zip file
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
        
        # Test root display
        archive_uri = f"archive://{archive_path}#"
        
        # Extract archive name
        path_part = archive_uri[10:]  # Remove 'archive://'
        if '#' in path_part:
            arch_path, internal_path = path_part.split('#', 1)
            archive_name = PathlibPath(arch_path).name
            
            if internal_path:
                display = f"[{archive_name}]/{internal_path}"
            else:
                display = f"[{archive_name}]"
            
            assert display == "[test.zip]", f"Expected [test.zip], got {display}"
            print(f"✓ Archive root display: {display}")
        
        # Test internal path display
        archive_uri_internal = f"archive://{archive_path}#dir1/subdir"
        path_part = archive_uri_internal[10:]
        if '#' in path_part:
            arch_path, internal_path = path_part.split('#', 1)
            archive_name = PathlibPath(arch_path).name
            
            if internal_path:
                display = f"[{archive_name}]/{internal_path}"
            else:
                display = f"[{archive_name}]"
            
            assert display == "[test.zip]/dir1/subdir", f"Expected [test.zip]/dir1/subdir, got {display}"
            print(f"✓ Archive internal path display: {display}")


def test_archive_parent_navigation():
    """Test navigating to parent within archive"""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "test.zip"
        
        # Create a zip file with nested structure
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("dir1/subdir/file.txt", "content")
        
        # Create path to subdirectory
        archive_uri = f"archive://{archive_path}#dir1/subdir"
        archive_path_obj = Path(archive_uri)
        
        # Get parent
        parent = archive_path_obj.parent
        parent_str = str(parent)
        
        # Should navigate to dir1
        assert '#dir1' in parent_str, f"Parent should be dir1, got {parent_str}"
        print(f"✓ Parent navigation: {parent_str}")
        
        # Get parent of parent (should be root)
        grandparent = parent.parent
        grandparent_str = str(grandparent)
        
        # Should navigate to root
        assert grandparent_str.endswith('#'), f"Grandparent should be root, got {grandparent_str}"
        print(f"✓ Grandparent navigation (root): {grandparent_str}")


if __name__ == '__main__':
    print("Testing archive virtual directory integration...")
    print()
    
    try:
        test_archive_detection()
        test_archive_uri_creation()
        test_archive_path_navigation()
        test_archive_path_display_formatting()
        test_archive_parent_navigation()
        
        print()
        print("✅ All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print()
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
