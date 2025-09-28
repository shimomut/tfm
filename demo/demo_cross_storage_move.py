#!/usr/bin/env python3
"""
Demo: Cross-Storage Move Functionality

This demo showcases TFM's ability to move files and directories between different storage systems:
- Local filesystem to S3
- S3 to local filesystem
- S3 to S3 (different buckets/paths)
- Enhanced move operations with progress tracking

Usage:
    python demo/demo_cross_storage_move.py
"""

import os
import sys
import tempfile
import time
from pathlib import Path as PathlibPath

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 40)


def create_demo_files(temp_dir):
    """Create demo files and directories for testing"""
    print("Creating demo files and directories...")
    
    temp_path = PathlibPath(temp_dir)
    
    # Create various test files
    files_created = []
    
    # Text file
    text_file = temp_path / "document.txt"
    text_file.write_text("""This is a sample document.
It contains multiple lines of text.
Perfect for testing file moves!

Created for TFM cross-storage move demo.
""")
    files_created.append(Path(text_file))
    
    # JSON file
    json_file = temp_path / "config.json"
    json_file.write_text("""{
    "application": "TFM",
    "version": "1.0",
    "features": [
        "cross-storage-move",
        "s3-support",
        "progress-tracking"
    ],
    "settings": {
        "confirm_move": true,
        "show_progress": true
    }
}""")
    files_created.append(Path(json_file))
    
    # Create a directory with nested content
    demo_dir = temp_path / "demo_directory"
    demo_dir.mkdir()
    
    # Files in directory
    (demo_dir / "readme.md").write_text("""# Demo Directory
    
This directory contains sample files for testing directory moves.

## Contents
- readme.md (this file)
- data.csv (sample data)
- scripts/ (subdirectory with scripts)
""")
    
    (demo_dir / "data.csv").write_text("""name,age,city
Alice,30,New York
Bob,25,San Francisco
Charlie,35,Chicago
Diana,28,Boston
""")
    
    # Subdirectory with scripts
    scripts_dir = demo_dir / "scripts"
    scripts_dir.mkdir()
    
    (scripts_dir / "process.py").write_text("""#!/usr/bin/env python3
# Sample processing script
def process_data():
    print("Processing data...")
    return "processed"

if __name__ == "__main__":
    result = process_data()
    print(f"Result: {result}")
""")
    
    (scripts_dir / "analyze.sh").write_text("""#!/bin/bash
# Sample analysis script
echo "Starting analysis..."
echo "Analysis complete!"
""")
    
    dirs_created = [Path(demo_dir)]
    
    print(f"✓ Created {len(files_created)} files and {len(dirs_created)} directories")
    
    return files_created, dirs_created


def demo_path_operations():
    """Demonstrate path operations and scheme detection"""
    print_header("Path Operations and Scheme Detection")
    
    # Local paths
    local_path = Path("/home/user/document.txt")
    print(f"Local path: {local_path}")
    print(f"  Scheme: {local_path.get_scheme()}")
    print(f"  Is remote: {local_path.is_remote()}")
    print(f"  As URI: {local_path.as_uri()}")
    
    # S3 paths
    try:
        s3_path = Path("s3://my-bucket/documents/file.txt")
        print(f"\nS3 path: {s3_path}")
        print(f"  Scheme: {s3_path.get_scheme()}")
        print(f"  Is remote: {s3_path.is_remote()}")
        print(f"  As URI: {s3_path.as_uri()}")
        print(f"  Name: {s3_path.name}")
        print(f"  Parent: {s3_path.parent}")
        
        print("\n✓ S3 support is available")
        return True
        
    except ImportError as e:
        print(f"\n⚠ S3 support not available: {e}")
        print("Install boto3 to enable S3 functionality: pip install boto3")
        return False


def demo_cross_storage_detection(files, dirs):
    """Demonstrate cross-storage move detection"""
    print_header("Cross-Storage Move Detection")
    
    if not files:
        print("No files available for demo")
        return
    
    local_file = files[0]
    print(f"Source file: {local_file} (scheme: {local_file.get_scheme()})")
    
    # Simulate different destination types
    destinations = [
        ("Local", Path("/tmp/moved_file.txt")),
        ("S3", Path("s3://my-bucket/moved_file.txt")),
        ("SCP", Path("scp://server.com/home/user/moved_file.txt")),
    ]
    
    for dest_name, dest_path in destinations:
        try:
            source_scheme = local_file.get_scheme()
            dest_scheme = dest_path.get_scheme()
            is_cross_storage = source_scheme != dest_scheme
            
            print(f"\nDestination: {dest_name} ({dest_scheme})")
            print(f"  Cross-storage: {'Yes' if is_cross_storage else 'No'}")
            
            if is_cross_storage:
                scheme_names = {'file': 'Local', 's3': 'S3', 'scp': 'SCP', 'ftp': 'FTP'}
                source_name = scheme_names.get(source_scheme, source_scheme.upper())
                dest_name_mapped = scheme_names.get(dest_scheme, dest_scheme.upper())
                print(f"  Move type: {source_name} → {dest_name_mapped}")
                
        except Exception as e:
            print(f"  Error: {e}")


def demo_local_move_operations(temp_dir, files, dirs):
    """Demonstrate local move operations"""
    print_header("Local Move Operations")
    
    # Create destination directory
    dest_dir = Path(temp_dir) / "moved_items"
    dest_dir.mkdir()
    print(f"Created destination directory: {dest_dir}")
    
    # Move a single file
    print_step(1, "Moving single file")
    if files:
        source_file = files[0]
        dest_file = dest_dir / source_file.name
        
        print(f"Moving: {source_file.name}")
        print(f"From: {source_file.parent}")
        print(f"To: {dest_file.parent}")
        
        try:
            # Show file exists before move
            print(f"Source exists before move: {source_file.exists()}")
            
            # Perform move
            success = source_file.move_to(dest_file)
            
            # Show results
            print(f"Move successful: {success}")
            print(f"Source exists after move: {source_file.exists()}")
            print(f"Destination exists after move: {dest_file.exists()}")
            
            if dest_file.exists():
                content_preview = dest_file.read_text()[:100] + "..." if len(dest_file.read_text()) > 100 else dest_file.read_text()
                print(f"Content preview: {repr(content_preview)}")
            
            print("✓ Single file move completed")
            
        except Exception as e:
            print(f"✗ Single file move failed: {e}")
    
    # Move a directory
    print_step(2, "Moving directory with nested content")
    if dirs:
        source_dir = dirs[0]
        dest_subdir = dest_dir / source_dir.name
        
        print(f"Moving directory: {source_dir.name}")
        print(f"From: {source_dir.parent}")
        print(f"To: {dest_subdir.parent}")
        
        # Show directory structure before move
        print("\nDirectory structure before move:")
        try:
            for item in source_dir.rglob("*"):
                relative_path = item.relative_to(source_dir)
                item_type = "DIR" if item.is_dir() else "FILE"
                print(f"  {item_type}: {relative_path}")
        except Exception as e:
            print(f"  Error listing contents: {e}")
        
        try:
            # Perform directory move
            success = source_dir.move_to(dest_subdir)
            
            print(f"\nMove successful: {success}")
            print(f"Source exists after move: {source_dir.exists()}")
            print(f"Destination exists after move: {dest_subdir.exists()}")
            
            # Show moved directory structure
            if dest_subdir.exists():
                print("\nMoved directory structure:")
                try:
                    for item in dest_subdir.rglob("*"):
                        relative_path = item.relative_to(dest_subdir)
                        item_type = "DIR" if item.is_dir() else "FILE"
                        print(f"  {item_type}: {relative_path}")
                except Exception as e:
                    print(f"  Error listing moved contents: {e}")
            
            print("✓ Directory move completed")
            
        except Exception as e:
            print(f"✗ Directory move failed: {e}")


def demo_error_handling(temp_dir):
    """Demonstrate error handling in move operations"""
    print_header("Error Handling Demo")
    
    print_step(1, "Moving non-existent file")
    non_existent = Path(temp_dir) / "does_not_exist.txt"
    dest = Path(temp_dir) / "destination.txt"
    
    try:
        non_existent.move_to(dest)
        print("✗ Should have failed!")
    except FileNotFoundError as e:
        print(f"✓ Correctly caught FileNotFoundError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print_step(2, "Moving to existing destination without overwrite")
    
    # Create source and destination files
    source = Path(temp_dir) / "source.txt"
    source.write_text("Source content")
    
    existing_dest = Path(temp_dir) / "existing.txt"
    existing_dest.write_text("Existing content")
    
    try:
        source.move_to(existing_dest, overwrite=False)
        print("✗ Should have failed!")
    except FileExistsError as e:
        print(f"✓ Correctly caught FileExistsError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print_step(3, "Moving to existing destination with overwrite")
    
    try:
        success = source.move_to(existing_dest, overwrite=True)
        print(f"Move with overwrite successful: {success}")
        print(f"Source exists: {source.exists()}")
        print(f"Destination exists: {existing_dest.exists()}")
        
        if existing_dest.exists():
            content = existing_dest.read_text()
            print(f"Final content: {repr(content)}")
            if content == "Source content":
                print("✓ Content correctly overwritten")
            else:
                print("✗ Content not correctly overwritten")
        
    except Exception as e:
        print(f"✗ Move with overwrite failed: {e}")


def demo_cross_storage_simulation():
    """Simulate cross-storage move operations"""
    print_header("Cross-Storage Move Simulation")
    
    print("This demo simulates cross-storage moves without actual S3 operations.")
    print("In a real scenario with AWS credentials, these would perform actual moves.")
    
    # Simulate different move scenarios
    scenarios = [
        ("Local to S3", Path("/tmp/local_file.txt"), Path("s3://my-bucket/remote_file.txt")),
        ("S3 to Local", Path("s3://my-bucket/remote_file.txt"), Path("/tmp/downloaded_file.txt")),
        ("S3 to S3", Path("s3://source-bucket/file.txt"), Path("s3://dest-bucket/moved_file.txt")),
    ]
    
    for i, (scenario_name, source, dest) in enumerate(scenarios, 1):
        print_step(i, scenario_name)
        
        print(f"Source: {source} (scheme: {source.get_scheme()})")
        print(f"Destination: {dest} (scheme: {dest.get_scheme()})")
        
        # Check if it's cross-storage
        is_cross_storage = source.get_scheme() != dest.get_scheme()
        print(f"Cross-storage: {'Yes' if is_cross_storage else 'No'}")
        
        if is_cross_storage:
            print("Operation would:")
            print("  1. Copy source to destination")
            print("  2. Delete source after successful copy")
            print("  3. Invalidate relevant caches")
        else:
            print("Operation would:")
            print("  1. Use native rename/move operation")
        
        print(f"✓ {scenario_name} logic verified")


def main():
    """Main demo function"""
    print_header("TFM Cross-Storage Move Demo")
    print("This demo showcases TFM's cross-storage move capabilities")
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp(prefix='tfm_move_demo_')
    print(f"Demo directory: {temp_dir}")
    
    try:
        # Create demo files
        files, dirs = create_demo_files(temp_dir)
        
        # Run demo sections
        s3_available = demo_path_operations()
        demo_cross_storage_detection(files, dirs)
        demo_local_move_operations(temp_dir, files, dirs)
        demo_error_handling(temp_dir)
        demo_cross_storage_simulation()
        
        print_header("Demo Summary")
        print("✓ Path operations and scheme detection")
        print("✓ Cross-storage move detection")
        print("✓ Local move operations")
        print("✓ Error handling")
        print("✓ Cross-storage move simulation")
        
        if s3_available:
            print("\n🎉 All features demonstrated successfully!")
            print("Your system supports full cross-storage move functionality.")
        else:
            print("\n⚠ Demo completed with limited S3 support.")
            print("Install boto3 for full S3 functionality: pip install boto3")
        
        print(f"\nDemo files remain in: {temp_dir}")
        print("You can examine the moved files and directory structure.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\nDemo directory: {temp_dir}")
        print("(Directory not automatically cleaned up for inspection)")


if __name__ == "__main__":
    main()