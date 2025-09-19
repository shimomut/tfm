#!/usr/bin/env python3
"""
Demo script for the archive extraction feature
Creates test archives and demonstrates the extraction functionality
"""

import os
import tempfile
import zipfile
import tarfile
from pathlib import Path

def create_demo_archives():
    """Create demo archives for testing extraction"""
    print("Creating demo archives for extraction testing...")
    
    # Create test_dir if it doesn't exist
    test_dir = Path("test_dir")
    test_dir.mkdir(exist_ok=True)
    
    # Create some test files
    demo_files_dir = test_dir / "demo_files"
    demo_files_dir.mkdir(exist_ok=True)
    
    # Create test files
    (demo_files_dir / "readme.txt").write_text("This is a readme file\nContains important information.")
    (demo_files_dir / "config.json").write_text('{\n  "name": "demo",\n  "version": "1.0"\n}')
    (demo_files_dir / "script.py").write_text('#!/usr/bin/env python3\nprint("Hello from demo script!")')
    
    # Create a subdirectory with files
    subdir = demo_files_dir / "docs"
    subdir.mkdir(exist_ok=True)
    (subdir / "manual.txt").write_text("User manual content")
    (subdir / "changelog.txt").write_text("Version 1.0: Initial release")
    
    # Create ZIP archive
    zip_path = test_dir / "demo_project.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in demo_files_dir.rglob('*'):
            if file_path.is_file():
                # Store with relative path from demo_files_dir
                arcname = file_path.relative_to(demo_files_dir)
                zipf.write(file_path, arcname)
    
    # Create TAR.GZ archive
    tar_path = test_dir / "demo_backup.tar.gz"
    with tarfile.open(tar_path, 'w:gz') as tarf:
        for file_path in demo_files_dir.rglob('*'):
            if file_path.is_file():
                # Store with relative path from demo_files_dir
                arcname = file_path.relative_to(demo_files_dir)
                tarf.add(file_path, arcname=arcname)
    
    # Create TGZ archive (alternative tar.gz extension)
    tgz_path = test_dir / "demo_source.tgz"
    with tarfile.open(tgz_path, 'w:gz') as tarf:
        for file_path in demo_files_dir.rglob('*'):
            if file_path.is_file():
                # Store with relative path from demo_files_dir
                arcname = file_path.relative_to(demo_files_dir)
                tarf.add(file_path, arcname=arcname)
    
    print(f"✓ Created demo archives:")
    print(f"  - {zip_path} (ZIP format)")
    print(f"  - {tar_path} (TAR.GZ format)")
    print(f"  - {tgz_path} (TGZ format)")
    
    # Clean up the temporary demo_files directory
    import shutil
    shutil.rmtree(demo_files_dir)
    
    return zip_path, tar_path, tgz_path

def show_usage_instructions():
    """Show instructions for using the extraction feature"""
    print("\n" + "=" * 60)
    print("ARCHIVE EXTRACTION FEATURE DEMO")
    print("=" * 60)
    print()
    print("The U key has been implemented to extract archive files!")
    print()
    print("HOW TO USE:")
    print("1. Start TFM: python3 tfm.py")
    print("2. Navigate to an archive file (.zip, .tar.gz, .tgz)")
    print("3. Press 'U' or 'u' to extract the archive")
    print("4. The archive will be extracted to the other pane")
    print("5. A directory with the archive's base name will be created")
    print()
    print("SUPPORTED FORMATS:")
    print("- ZIP files (.zip)")
    print("- TAR.GZ files (.tar.gz)")
    print("- TGZ files (.tgz)")
    print()
    print("BEHAVIOR:")
    print("- Creates a directory named after the archive (without extension)")
    print("- Extracts to the non-focused pane's directory")
    print("- Asks for confirmation if target directory already exists")
    print("- Automatically refreshes the target pane after extraction")
    print()
    print("EXAMPLE:")
    print("- Select 'demo_project.zip' in left pane")
    print("- Press 'U'")
    print("- Creates 'demo_project/' directory in right pane")
    print("- Extracts all files into that directory")
    print()

def main():
    """Main demo function"""
    try:
        # Create demo archives
        archives = create_demo_archives()
        
        # Show usage instructions
        show_usage_instructions()
        
        print("DEMO ARCHIVES CREATED:")
        for archive in archives:
            print(f"  - {archive}")
        print()
        print("You can now test the extraction feature in TFM!")
        print("Navigate to test_dir/ and try extracting these archives with the 'U' key.")
        
    except Exception as e:
        print(f"Error creating demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()