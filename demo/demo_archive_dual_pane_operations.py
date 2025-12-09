#!/usr/bin/env python3
"""
Demo: Dual-pane archive operations
Demonstrates browsing archives in both panes and copy operations
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
from tfm_pane_manager import PaneManager
from tfm_file_operations import FileOperations


class MockConfig:
    """Mock configuration"""
    DEFAULT_SORT_MODE = 'name'
    DEFAULT_SORT_REVERSE = False
    DEFAULT_LEFT_PANE_RATIO = 0.5
    MAX_HISTORY_ENTRIES = 100


class MockLogManager:
    """Mock log manager"""
    def __init__(self):
        self.messages = []
    
    def add_message(self, message, level="INFO"):
        self.messages.append((message, level))
        print(f"  [{level}] {message}")


def demo_dual_pane_archive_browsing():
    """Demo browsing archives in both panes"""
    print("=" * 70)
    print("DEMO: Browsing Archives in Both Panes")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two different archives
        print("Creating test archives...")
        
        left_archive = PathlibPath(tmpdir) / "documents.zip"
        with zipfile.ZipFile(left_archive, 'w') as zf:
            zf.writestr("readme.txt", "Documentation files")
            zf.writestr("docs/manual.txt", "User manual")
            zf.writestr("docs/guide.txt", "Quick start guide")
            zf.writestr("docs/api/reference.txt", "API reference")
        print(f"  Created: {left_archive.name}")
        
        right_archive = PathlibPath(tmpdir) / "backup.tar.gz"
        with tarfile.open(right_archive, 'w:gz') as tf:
            temp_file = PathlibPath(tmpdir) / "temp_data.txt"
            temp_file.write_text("Important data")
            tf.add(temp_file, arcname="data.txt")
            
            temp_dir = PathlibPath(tmpdir) / "temp_logs"
            temp_dir.mkdir(exist_ok=True)
            log_file = temp_dir / "app.log"
            log_file.write_text("Application logs")
            tf.add(log_file, arcname="logs/app.log")
        print(f"  Created: {right_archive.name}")
        print()
        
        # Setup dual-pane manager
        config = MockConfig()
        pane_manager = PaneManager(config, Path(tmpdir), Path(tmpdir))
        
        print("Setting up dual-pane view...")
        print(f"  Left pane:  {tmpdir}")
        print(f"  Right pane: {tmpdir}")
        print()
        
        # Navigate left pane into documents.zip
        print("Navigating left pane into documents.zip...")
        left_archive_uri = f"archive://{left_archive}#"
        pane_manager.left_pane['path'] = Path(left_archive_uri)
        
        left_entries = list(pane_manager.left_pane['path'].iterdir())
        print(f"  Left pane contents ({len(left_entries)} entries):")
        for entry in sorted(left_entries, key=lambda x: x.name):
            entry_type = "DIR " if entry.is_dir() else "FILE"
            print(f"    [{entry_type}] {entry.name}")
        print()
        
        # Navigate right pane into backup.tar.gz
        print("Navigating right pane into backup.tar.gz...")
        right_archive_uri = f"archive://{right_archive}#"
        pane_manager.right_pane['path'] = Path(right_archive_uri)
        
        right_entries = list(pane_manager.right_pane['path'].iterdir())
        print(f"  Right pane contents ({len(right_entries)} entries):")
        for entry in sorted(right_entries, key=lambda x: x.name):
            entry_type = "DIR " if entry.is_dir() else "FILE"
            print(f"    [{entry_type}] {entry.name}")
        print()
        
        # Demonstrate pane switching
        print("Demonstrating pane switching...")
        print(f"  Active pane: {pane_manager.active_pane}")
        pane_manager.switch_pane()
        print(f"  After switch: {pane_manager.active_pane}")
        pane_manager.switch_pane()
        print(f"  After switch: {pane_manager.active_pane}")
        print()
        
        # Navigate into subdirectory in left pane
        print("Navigating into docs/ subdirectory in left pane...")
        docs_uri = f"archive://{left_archive}#docs"
        pane_manager.left_pane['path'] = Path(docs_uri)
        
        docs_entries = list(pane_manager.left_pane['path'].iterdir())
        print(f"  docs/ contents ({len(docs_entries)} entries):")
        for entry in sorted(docs_entries, key=lambda x: x.name):
            entry_type = "DIR " if entry.is_dir() else "FILE"
            print(f"    [{entry_type}] {entry.name}")
        print()
        
        print("✓ Both panes can browse different archives independently")
        print()


def demo_copy_from_archive_to_filesystem():
    """Demo copying files from archive to filesystem"""
    print("=" * 70)
    print("DEMO: Copy from Archive to Filesystem")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source archive
        print("Creating source archive...")
        source_archive = PathlibPath(tmpdir) / "source.zip"
        with zipfile.ZipFile(source_archive, 'w') as zf:
            zf.writestr("document.txt", "Important document content")
            zf.writestr("data/report.txt", "Monthly report data")
            zf.writestr("data/stats.txt", "Statistics summary")
        print(f"  Created: {source_archive.name}")
        print()
        
        # Create destination directory
        dest_dir = PathlibPath(tmpdir) / "extracted"
        dest_dir.mkdir()
        print(f"Created destination directory: {dest_dir.name}/")
        print()
        
        # Setup panes
        config = MockConfig()
        log_manager = MockLogManager()
        pane_manager = PaneManager(config, Path(tmpdir), Path(tmpdir))
        
        # Left pane: archive, Right pane: filesystem
        archive_uri = f"archive://{source_archive}#"
        pane_manager.left_pane['path'] = Path(archive_uri)
        pane_manager.right_pane['path'] = Path(str(dest_dir))
        pane_manager.active_pane = 'left'
        
        print("Dual-pane setup:")
        print(f"  Left pane:  [source.zip] (archive)")
        print(f"  Right pane: extracted/ (filesystem)")
        print()
        
        # List files in archive
        archive_files = list(pane_manager.left_pane['path'].iterdir())
        print(f"Files in archive ({len(archive_files)} entries):")
        for f in sorted(archive_files, key=lambda x: x.name):
            file_type = "DIR " if f.is_dir() else "FILE"
            print(f"  [{file_type}] {f.name}")
        print()
        
        # Copy a file
        print("Copying document.txt from archive to filesystem...")
        source_file = None
        for f in archive_files:
            if f.name == "document.txt":
                source_file = f
                break
        
        if source_file:
            file_ops = FileOperations(log_manager, None, None)
            dest_path = Path(str(dest_dir)) / "document.txt"
            
            success = file_ops.copy_file(source_file, dest_path)
            
            if success:
                print("  ✓ Copy successful!")
                print(f"  Source: archive://.../source.zip#document.txt")
                print(f"  Dest:   {dest_dir.name}/document.txt")
                print()
                
                # Verify content
                content = dest_path.read_text()
                print(f"  Extracted content: '{content}'")
                print()
        
        # Copy a directory
        print("Copying data/ directory from archive...")
        data_dir = None
        for f in archive_files:
            if f.name == "data" and f.is_dir():
                data_dir = f
                break
        
        if data_dir:
            print("  Note: Directory extraction requires recursive copy")
            print("  Each file in the directory would be extracted individually")
            print()
        
        print("✓ Files can be extracted from archives to filesystem")
        print()


def demo_archive_to_archive_operations():
    """Demo operations between two archive panes"""
    print("=" * 70)
    print("DEMO: Operations Between Two Archives")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two archives
        print("Creating two archives...")
        
        archive1 = PathlibPath(tmpdir) / "archive1.zip"
        with zipfile.ZipFile(archive1, 'w') as zf:
            zf.writestr("file1.txt", "Content from archive 1")
            zf.writestr("shared.txt", "Shared file in archive 1")
        print(f"  Created: {archive1.name}")
        
        archive2 = PathlibPath(tmpdir) / "archive2.tar.gz"
        with tarfile.open(archive2, 'w:gz') as tf:
            temp_file = PathlibPath(tmpdir) / "temp.txt"
            temp_file.write_text("Content from archive 2")
            tf.add(temp_file, arcname="file2.txt")
            
            temp_shared = PathlibPath(tmpdir) / "temp_shared.txt"
            temp_shared.write_text("Shared file in archive 2")
            tf.add(temp_shared, arcname="shared.txt")
        print(f"  Created: {archive2.name}")
        print()
        
        # Setup panes
        config = MockConfig()
        pane_manager = PaneManager(config, Path(tmpdir), Path(tmpdir))
        
        # Both panes in archives
        uri1 = f"archive://{archive1}#"
        uri2 = f"archive://{archive2}#"
        pane_manager.left_pane['path'] = Path(uri1)
        pane_manager.right_pane['path'] = Path(uri2)
        
        print("Dual-pane setup:")
        print(f"  Left pane:  [archive1.zip]")
        print(f"  Right pane: [archive2.tar.gz]")
        print()
        
        # List contents
        left_files = list(pane_manager.left_pane['path'].iterdir())
        right_files = list(pane_manager.right_pane['path'].iterdir())
        
        print(f"Left pane contents ({len(left_files)} files):")
        for f in sorted(left_files, key=lambda x: x.name):
            print(f"  - {f.name}")
        print()
        
        print(f"Right pane contents ({len(right_files)} files):")
        for f in sorted(right_files, key=lambda x: x.name):
            print(f"  - {f.name}")
        print()
        
        print("Note: Archives are read-only virtual directories")
        print("  - You can extract files FROM archives")
        print("  - You cannot write directly TO archives")
        print("  - To copy between archives, extract to temp location first")
        print()
        
        # Demonstrate extraction
        print("Extracting file1.txt from archive1.zip...")
        temp_extract = PathlibPath(tmpdir) / "temp_extract"
        temp_extract.mkdir()
        
        source_file = None
        for f in left_files:
            if f.name == "file1.txt":
                source_file = f
                break
        
        if source_file:
            log_manager = MockLogManager()
            file_ops = FileOperations(log_manager, None, None)
            dest_path = Path(str(temp_extract)) / "file1.txt"
            
            success = file_ops.copy_file(source_file, dest_path)
            if success:
                print("  ✓ Extracted to temporary location")
                print(f"  Content: '{dest_path.read_text()}'")
                print()
        
        print("✓ Both panes can browse different archives")
        print("✓ Files can be extracted from either archive")
        print()


def demo_pane_synchronization():
    """Demo pane synchronization with archives"""
    print("=" * 70)
    print("DEMO: Pane Synchronization with Archives")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create archive and subdirectory
        archive_path = PathlibPath(tmpdir) / "data.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("readme.txt", "Archive contents")
            zf.writestr("data/file.txt", "Data file")
        
        subdir = PathlibPath(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "local.txt").write_text("Local file")
        
        print("Setup:")
        print(f"  Archive: {archive_path.name}")
        print(f"  Subdirectory: {subdir.name}/")
        print()
        
        # Setup panes
        config = MockConfig()
        log_manager = MockLogManager()
        pane_manager = PaneManager(config, Path(tmpdir), Path(str(subdir)))
        
        print("Initial pane state:")
        print(f"  Left pane:  {tmpdir}")
        print(f"  Right pane: {subdir.name}/")
        print()
        
        # Navigate left pane into archive
        archive_uri = f"archive://{archive_path}#"
        pane_manager.left_pane['path'] = Path(archive_uri)
        
        print("After navigating left pane into archive:")
        print(f"  Left pane:  [data.zip]")
        print(f"  Right pane: {subdir.name}/")
        print()
        
        # Try to sync right pane to left pane
        print("Attempting to sync right pane to left pane (archive)...")
        pane_manager.active_pane = 'right'
        result = pane_manager.sync_current_to_other(log_callback=log_manager.add_message)
        
        if result:
            print("  ✓ Sync successful!")
            right_path = str(pane_manager.right_pane['path'])
            if right_path.startswith('archive://'):
                print(f"  Right pane now shows: [data.zip]")
        else:
            print("  Sync handled appropriately")
        print()
        
        # Test syncing when both in same location
        print("Testing sync when both panes show same location...")
        pane_manager.left_pane['path'] = Path(archive_uri)
        pane_manager.right_pane['path'] = Path(archive_uri)
        
        result = pane_manager.sync_current_to_other(log_callback=log_manager.add_message)
        if not result:
            print("  ✓ Correctly detected both panes showing same location")
            print("  No sync needed")
        print()
        
        print("✓ Pane synchronization works with archives")
        print()


if __name__ == '__main__':
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "DUAL-PANE ARCHIVE OPERATIONS DEMO" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        demo_dual_pane_archive_browsing()
        input("Press ENTER to continue...")
        print()
        
        demo_copy_from_archive_to_filesystem()
        input("Press ENTER to continue...")
        print()
        
        demo_archive_to_archive_operations()
        input("Press ENTER to continue...")
        print()
        
        demo_pane_synchronization()
        
        print("=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print()
        print("Key Takeaways:")
        print("  • Both panes can browse archives independently")
        print("  • Files can be copied from archives to filesystem")
        print("  • Archives are read-only virtual directories")
        print("  • Pane synchronization works with archives")
        print("  • Navigation within archives doesn't affect other pane")
        print()
        
    except Exception as e:
        print()
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
