#!/usr/bin/env python3
"""
Demo: Enhanced Copy Progress with Threading

This demo demonstrates the improved copy operation progress tracking:
1. Operations run in a background thread
2. Shows current filename being copied
3. Shows byte-level progress for large files
4. Shows animated progress indicator
"""

import os
import sys
import time
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_progress_manager import ProgressManager, OperationType


def create_test_files(test_dir):
    """Create test files of various sizes"""
    print(f"Creating test files in {test_dir}...")
    
    # Create a directory structure with files
    source_dir = test_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    
    # Create small files
    for i in range(5):
        file_path = source_dir / f"small_file_{i}.txt"
        with open(str(file_path), 'w') as f:
            f.write(f"Small file {i}\n" * 100)
    
    # Create medium files (1MB each)
    for i in range(3):
        file_path = source_dir / f"medium_file_{i}.dat"
        with open(str(file_path), 'wb') as f:
            f.write(b'M' * (1024 * 1024))
    
    # Create a large file (20MB)
    large_file = source_dir / "large_file.dat"
    with open(str(large_file), 'wb') as f:
        f.write(b'L' * (20 * 1024 * 1024))
    
    # Create a subdirectory with files
    subdir = source_dir / "subdir"
    subdir.mkdir(exist_ok=True)
    for i in range(3):
        file_path = subdir / f"sub_file_{i}.txt"
        with open(str(file_path), 'w') as f:
            f.write(f"Subdirectory file {i}\n" * 50)
    
    print(f"Created test files in {source_dir}")
    return source_dir


def progress_callback(progress_data):
    """Callback to display progress updates"""
    if progress_data is None:
        print("\n✓ Operation completed!")
        return
    
    # Get progress text
    progress_text = f"Progress: {progress_data['processed_items']}/{progress_data['total_items']} "
    progress_text += f"({int((progress_data['processed_items'] / progress_data['total_items']) * 100)}%)"
    
    if progress_data['current_item']:
        progress_text += f" - {progress_data['current_item']}"
    
    if progress_data.get('file_byte_progress', 0) > 0:
        progress_text += f" [{progress_data['file_byte_progress']}%]"
    
    # Print with carriage return to overwrite previous line
    print(f"\r{progress_text}", end='', flush=True)


def count_files_recursively(paths):
    """Count total number of files in the given paths"""
    total_files = 0
    for path in paths:
        if path.is_file():
            total_files += 1
        elif path.is_dir():
            for root, dirs, files in os.walk(path):
                total_files += len(files)
    return total_files


def simulate_copy_with_progress(source_dir, dest_dir):
    """Simulate copy operation with progress tracking"""
    print(f"\nCopying from {source_dir} to {dest_dir}...")
    
    # Initialize progress manager
    progress_manager = ProgressManager()
    
    # Get list of files to copy
    files_to_copy = [source_dir]
    
    # Count total files
    total_files = count_files_recursively(files_to_copy)
    print(f"Total files to copy: {total_files}")
    
    # Start progress tracking
    progress_manager.start_operation(
        OperationType.COPY,
        total_files,
        f"to {dest_dir.name}",
        progress_callback
    )
    
    processed_files = 0
    
    # Walk through source directory
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        rel_path = root_path.relative_to(source_dir)
        dest_root = dest_dir / rel_path
        
        # Create destination directory
        dest_root.mkdir(parents=True, exist_ok=True)
        
        # Copy files
        for file_name in files:
            source_file = root_path / file_name
            dest_file = dest_root / file_name
            
            processed_files += 1
            display_name = str(rel_path / file_name) if rel_path != Path('.') else file_name
            progress_manager.update_progress(display_name, processed_files)
            
            # Simulate byte-level progress for large files
            file_size = source_file.stat().st_size
            if file_size > 10 * 1024 * 1024:  # Files larger than 10MB
                # Copy in chunks and update byte progress
                chunk_size = 1024 * 1024  # 1MB chunks
                bytes_copied = 0
                
                with open(str(source_file), 'rb') as src:
                    with open(str(dest_file), 'wb') as dst:
                        while True:
                            chunk = src.read(chunk_size)
                            if not chunk:
                                break
                            dst.write(chunk)
                            bytes_copied += len(chunk)
                            
                            # Update byte progress with actual bytes
                            progress_manager.update_file_byte_progress(bytes_copied, file_size)
                            
                            # Small delay to make progress visible
                            time.sleep(0.05)
            else:
                # Copy small files directly
                shutil.copy2(str(source_file), str(dest_file))
                time.sleep(0.02)  # Small delay to make progress visible
    
    # Finish progress tracking
    progress_manager.finish_operation()
    
    print(f"\nCopy completed: {processed_files} files copied")


def test_progress_animator():
    """Test the progress animator"""
    print("\n" + "="*60)
    print("Testing Progress Animator")
    print("="*60)
    
    from tfm_progress_animator import ProgressAnimator
    
    # Create minimal config for animator
    class MinimalConfig:
        PROGRESS_ANIMATION_PATTERN = 'spinner'
        PROGRESS_ANIMATION_SPEED = 0.08
    
    animator = ProgressAnimator(MinimalConfig())
    
    print("\nAnimator frames (watch for 3 seconds):")
    start_time = time.time()
    while time.time() - start_time < 3:
        frame = animator.get_current_frame()
        print(f"\r{frame} Processing...", end='', flush=True)
        time.sleep(0.1)
    
    print("\n✓ Animator test completed")


def main():
    """Main demo function"""
    print("="*60)
    print("Enhanced Copy Progress Demo")
    print("="*60)
    
    # Test animator first
    test_progress_animator()
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Create test files
        source_dir = create_test_files(test_dir)
        
        # Create destination directory
        dest_dir = test_dir / "destination"
        dest_dir.mkdir(exist_ok=True)
        
        # Simulate copy with progress
        simulate_copy_with_progress(source_dir, dest_dir)
        
        # Verify copy
        print("\nVerifying copy...")
        source_files = count_files_recursively([source_dir])
        dest_files = count_files_recursively([dest_dir])
        
        if source_files == dest_files:
            print(f"✓ Copy verified: {dest_files} files copied successfully")
        else:
            print(f"✗ Copy verification failed: {source_files} source files, {dest_files} destination files")
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
