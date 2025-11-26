#!/usr/bin/env python3
"""
Demo: Rename Conflict Resolution Feature

This demo showcases the new "Rename" option when file conflicts occur during
copy, move, and archive extraction operations.

The demo simulates the user workflow when encountering file conflicts and
choosing to rename files instead of overwriting or skipping them.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path as StdPath

# Add src directory to path
sys.path.insert(0, str(StdPath(__file__).parent.parent / "src"))

from tfm_path import Path


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step_num, description):
    """Print a step description"""
    print(f"\n[Step {step_num}] {description}")


def demo_copy_with_rename():
    """Demonstrate copy operation with rename conflict resolution"""
    print_section("Demo 1: Copy with Rename")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup
        source_dir = StdPath(temp_dir) / "source"
        dest_dir = StdPath(temp_dir) / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create source file
        source_file = source_dir / "report.pdf"
        source_file.write_text("This is the new report content")
        
        # Create conflicting file in destination
        dest_file = dest_dir / "report.pdf"
        dest_file.write_text("This is the old report content")
        
        print_step(1, "Initial State")
        print(f"   Source: {source_file.name} (new report)")
        print(f"   Destination: {dest_file.name} (old report)")
        print(f"   Conflict: YES")
        
        print_step(2, "User Action: Press F5 to copy")
        print("   Dialog appears: 'report.pdf' already exists in destination")
        print("   Options: [O]verwrite, [S]kip, [R]ename, [C]ancel")
        
        print_step(3, "User Action: Press 'r' for Rename")
        print("   Input dialog appears: 'Rename report.pdf to:'")
        print("   User edits to: 'report_2024.pdf'")
        
        # Simulate rename
        new_name = "report_2024.pdf"
        new_dest = dest_dir / new_name
        
        source_path = Path(str(source_file))
        dest_path = Path(str(new_dest))
        source_path.copy_to(dest_path)
        
        print_step(4, "Result")
        print(f"   ✓ File copied as: {new_name}")
        print(f"   ✓ Original destination preserved: {dest_file.name}")
        print(f"   ✓ Both files now exist in destination")
        
        # Verify
        print("\n   Files in destination:")
        for f in sorted(dest_dir.iterdir()):
            content = f.read_text()
            print(f"     - {f.name}: {content[:30]}...")


def demo_move_with_recursive_rename():
    """Demonstrate move operation with recursive rename conflict resolution"""
    print_section("Demo 2: Move with Recursive Rename")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup
        source_dir = StdPath(temp_dir) / "source"
        dest_dir = StdPath(temp_dir) / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create source file
        source_file = source_dir / "data.csv"
        source_file.write_text("id,name,value\n1,test,100")
        
        # Create multiple conflicting files in destination
        (dest_dir / "data.csv").write_text("old data 1")
        (dest_dir / "data_backup.csv").write_text("old data 2")
        
        print_step(1, "Initial State")
        print(f"   Source: {source_file.name}")
        print(f"   Destination conflicts:")
        print(f"     - data.csv (exists)")
        print(f"     - data_backup.csv (exists)")
        
        print_step(2, "User Action: Press F6 to move")
        print("   Dialog: 'data.csv' already exists")
        print("   User presses 'r' for Rename")
        
        print_step(3, "First Rename Attempt")
        print("   User enters: 'data_backup.csv'")
        print("   Conflict check: FAILED (name also exists)")
        print("   Dialog appears again: 'data_backup.csv' already exists")
        print("   Options: [O]verwrite, [R]ename, [C]ancel")
        
        print_step(4, "Second Rename Attempt")
        print("   User presses 'r' again")
        print("   User enters: 'data_final.csv'")
        print("   Conflict check: PASSED (name is unique)")
        
        # Simulate final rename
        final_name = "data_final.csv"
        final_dest = dest_dir / final_name
        
        source_path = Path(str(source_file))
        dest_path = Path(str(final_dest))
        source_path.copy_to(dest_path)
        source_path.unlink()
        
        print_step(5, "Result")
        print(f"   ✓ File moved as: {final_name}")
        print(f"   ✓ Source file removed")
        print(f"   ✓ Original conflicts preserved")
        
        # Verify
        print("\n   Files in destination:")
        for f in sorted(dest_dir.iterdir()):
            print(f"     - {f.name}")
        print(f"\n   Source directory empty: {len(list(source_dir.iterdir())) == 0}")


def demo_archive_extraction_with_rename():
    """Demonstrate archive extraction with rename conflict resolution"""
    print_section("Demo 3: Archive Extraction with Rename")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup
        dest_dir = StdPath(temp_dir) / "projects"
        dest_dir.mkdir()
        
        # Create existing project directory
        existing_project = dest_dir / "myproject"
        existing_project.mkdir()
        (existing_project / "old_file.txt").write_text("Old project file")
        
        print_step(1, "Initial State")
        print(f"   Archive: myproject.zip")
        print(f"   Extraction target: {dest_dir}/myproject/")
        print(f"   Conflict: Directory 'myproject' already exists")
        
        print_step(2, "User Action: Press 'u' to extract")
        print("   Dialog: 'Directory myproject already exists'")
        print("   Options: [O]verwrite, [R]ename, [C]ancel")
        
        print_step(3, "User Action: Press 'r' for Rename")
        print("   Input dialog: 'Rename extraction directory to:'")
        print("   User edits to: 'myproject_v2'")
        print("   Conflict check: PASSED (name is unique)")
        
        # Simulate extraction to new directory
        new_project = dest_dir / "myproject_v2"
        new_project.mkdir()
        (new_project / "new_file.txt").write_text("New project file")
        (new_project / "README.md").write_text("# My Project v2")
        
        print_step(4, "Result")
        print(f"   ✓ Archive extracted to: myproject_v2/")
        print(f"   ✓ Original directory preserved: myproject/")
        print(f"   ✓ Both versions now exist")
        
        # Verify
        print("\n   Directories in projects:")
        for d in sorted(dest_dir.iterdir()):
            if d.is_dir():
                files = list(d.iterdir())
                print(f"     - {d.name}/ ({len(files)} files)")
                for f in files:
                    print(f"         {f.name}")


def demo_directory_rename():
    """Demonstrate directory rename conflict resolution"""
    print_section("Demo 4: Directory Copy with Rename")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup
        source_dir = StdPath(temp_dir) / "source"
        dest_dir = StdPath(temp_dir) / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create source directory with files
        source_folder = source_dir / "documents"
        source_folder.mkdir()
        (source_folder / "file1.txt").write_text("Document 1")
        (source_folder / "file2.txt").write_text("Document 2")
        (source_folder / "file3.txt").write_text("Document 3")
        
        # Create conflicting directory in destination
        dest_folder = dest_dir / "documents"
        dest_folder.mkdir()
        (dest_folder / "old_doc.txt").write_text("Old document")
        
        print_step(1, "Initial State")
        print(f"   Source: documents/ (3 files)")
        print(f"   Destination: documents/ (1 file)")
        print(f"   Conflict: Directory name exists")
        
        print_step(2, "User Action: Copy directory")
        print("   Dialog: 'documents' already exists")
        print("   User presses 'r' for Rename")
        
        print_step(3, "Rename Action")
        print("   User enters: 'documents_backup'")
        print("   Conflict check: PASSED")
        
        # Simulate directory copy with new name
        new_folder = dest_dir / "documents_backup"
        shutil.copytree(source_folder, new_folder)
        
        print_step(4, "Result")
        print(f"   ✓ Directory copied as: documents_backup/")
        print(f"   ✓ Original directory preserved")
        
        # Verify
        print("\n   Directories in destination:")
        for d in sorted(dest_dir.iterdir()):
            if d.is_dir():
                files = list(d.iterdir())
                print(f"     - {d.name}/ ({len(files)} files)")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("  TFM Rename Conflict Resolution Feature Demo")
    print("=" * 60)
    print("\nThis demo showcases the new 'Rename' option for handling")
    print("file conflicts during copy, move, and extract operations.")
    
    try:
        demo_copy_with_rename()
        demo_move_with_recursive_rename()
        demo_archive_extraction_with_rename()
        demo_directory_rename()
        
        print("\n" + "=" * 60)
        print("  Demo Complete!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("  ✓ Rename option in conflict dialogs")
        print("  ✓ Recursive conflict resolution")
        print("  ✓ Works with files and directories")
        print("  ✓ Preserves original files")
        print("  ✓ Supports copy, move, and extract operations")
        
        print("\nFor more information, see:")
        print("  doc/RENAME_CONFLICT_RESOLUTION_FEATURE.md")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Demo error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
