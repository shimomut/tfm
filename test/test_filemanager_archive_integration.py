#!/usr/bin/env python3
"""
Test FileManager integration with archive virtual directories
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path as PathlibPath

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_archive import ArchiveOperations


def test_enter_archive_simulation():
    """Simulate entering an archive file with ENTER key"""
    print("Testing ENTER key on archive file...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test archive
        archive_path = PathlibPath(tmpdir) / "test.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("dir1/file2.txt", "content2")
            zf.writestr("dir1/subdir/file3.txt", "content3")
        
        # Simulate FileManager state
        selected_file = Path(str(archive_path))
        
        # Check if it's an archive
        archive_ops = ArchiveOperations(None, None, None)
        assert archive_ops.is_archive(selected_file), "Should detect archive"
        
        # Simulate entering the archive (what handle_enter does)
        archive_uri = f"archive://{selected_file.absolute()}#"
        archive_path_obj = Path(archive_uri)
        
        # Verify we can list contents
        entries = list(archive_path_obj.iterdir())
        assert len(entries) > 0, "Should have entries"
        
        print(f"  ✓ Entered archive, found {len(entries)} entries")
        
        # Verify path display formatting
        path_str = str(archive_path_obj)
        assert path_str.startswith('archive://'), "Should be archive URI"
        print(f"  ✓ Archive URI: {path_str}")


def test_backspace_exit_archive_simulation():
    """Simulate exiting an archive with BACKSPACE key"""
    print("Testing BACKSPACE key to exit archive...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test archive
        archive_path = PathlibPath(tmpdir) / "test.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
        
        # Simulate being at archive root
        archive_uri = f"archive://{archive_path}#"
        current_path_str = archive_uri
        
        # Check if we're at archive root
        assert current_path_str.startswith('archive://'), "Should be in archive"
        assert current_path_str.endswith('#'), "Should be at root"
        
        # Simulate backspace logic
        archive_path_part = current_path_str[10:-1]  # Remove 'archive://' and '#'
        archive_file_path = Path(archive_path_part)
        parent_dir = archive_file_path.parent
        archive_filename = archive_file_path.name
        
        # Verify we got the correct parent directory
        assert str(parent_dir) == tmpdir, f"Parent should be {tmpdir}"
        assert archive_filename == "test.zip", "Archive filename should be test.zip"
        
        print(f"  ✓ Exited to: {parent_dir}")
        print(f"  ✓ Archive file: {archive_filename}")


def test_backspace_within_archive_simulation():
    """Simulate navigating up within an archive"""
    print("Testing BACKSPACE key within archive...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test archive with nested structure
        archive_path = PathlibPath(tmpdir) / "test.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("dir1/subdir/file.txt", "content")
        
        # Simulate being in a subdirectory
        archive_uri = f"archive://{archive_path}#dir1/subdir"
        current_path = Path(archive_uri)
        
        # Navigate to parent (should go to dir1)
        parent_path = current_path.parent
        parent_str = str(parent_path)
        
        assert '#dir1' in parent_str, "Should navigate to dir1"
        assert not parent_str.endswith('#dir1/subdir'), "Should not be in subdir"
        
        print(f"  ✓ Navigated to parent: {parent_str}")
        
        # Navigate to parent again (should go to root)
        grandparent_path = parent_path.parent
        grandparent_str = str(grandparent_path)
        
        assert grandparent_str.endswith('#'), "Should be at root"
        
        print(f"  ✓ Navigated to root: {grandparent_str}")


def test_path_display_formatting():
    """Test path display formatting for archives"""
    print("Testing path display formatting...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "myarchive.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file.txt", "content")
        
        # Test root display
        archive_uri = f"archive://{archive_path}#"
        path_part = archive_uri[10:]
        
        if '#' in path_part:
            arch_path, internal_path = path_part.split('#', 1)
            archive_name = PathlibPath(arch_path).name
            
            if internal_path:
                display = f"[{archive_name}]/{internal_path}"
            else:
                display = f"[{archive_name}]"
            
            assert display == "[myarchive.zip]", f"Expected [myarchive.zip], got {display}"
            print(f"  ✓ Root display: {display}")
        
        # Test internal path display
        archive_uri_internal = f"archive://{archive_path}#folder/subfolder"
        path_part = archive_uri_internal[10:]
        
        if '#' in path_part:
            arch_path, internal_path = path_part.split('#', 1)
            archive_name = PathlibPath(arch_path).name
            
            if internal_path:
                display = f"[{archive_name}]/{internal_path}"
            else:
                display = f"[{archive_name}]"
            
            assert display == "[myarchive.zip]/folder/subfolder"
            print(f"  ✓ Internal path display: {display}")


def test_archive_indicator_detection():
    """Test detecting when browsing an archive for status bar"""
    print("Testing archive indicator detection...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = PathlibPath(tmpdir) / "test.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file.txt", "content")
        
        # Test archive path
        archive_uri = f"archive://{archive_path}#"
        current_path_str = archive_uri
        
        is_archive = current_path_str.startswith('archive://')
        assert is_archive, "Should detect archive path"
        print(f"  ✓ Archive detected in path: {current_path_str[:50]}...")
        
        # Test regular path
        regular_path = str(Path(tmpdir))
        is_archive = regular_path.startswith('archive://')
        assert not is_archive, "Should not detect archive in regular path"
        print(f"  ✓ Regular path not detected as archive")


if __name__ == '__main__':
    print("Testing FileManager archive integration...")
    print()
    
    try:
        test_enter_archive_simulation()
        print()
        test_backspace_exit_archive_simulation()
        print()
        test_backspace_within_archive_simulation()
        print()
        test_path_display_formatting()
        print()
        test_archive_indicator_detection()
        
        print()
        print("✅ All FileManager integration tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print()
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
