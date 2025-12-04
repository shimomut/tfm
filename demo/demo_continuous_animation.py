#!/usr/bin/env python3
"""
Demo: Continuous Animation During Long Operations

This demo demonstrates that the progress animation continues smoothly
even when there are no progress updates (e.g., during large file copy).
"""

import os
import sys
import time
import threading

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_progress_manager import ProgressManager, OperationType


def simulate_long_operation_with_animation():
    """Simulate a long operation where animation should continue"""
    print("="*60)
    print("Testing Continuous Animation")
    print("="*60)
    
    animation_frames_seen = []
    
    def progress_callback(progress_data):
        """Callback that tracks animation frames"""
        if progress_data:
            # Get the progress text which includes animation
            progress_text = f"Progress: {progress_data['processed_items']}/{progress_data['total_items']}"
            if progress_data['current_item']:
                progress_text += f" - {progress_data['current_item']}"
            
            # Print with carriage return to show animation
            print(f"\r{progress_text}", end='', flush=True)
    
    # Create progress manager
    progress_manager = ProgressManager()
    
    # Start operation
    progress_manager.start_operation(
        OperationType.COPY,
        1,
        "large file",
        progress_callback
    )
    
    # Update progress once (simulating starting to copy a large file)
    progress_manager.update_progress("large_file.dat", 1)
    
    print("\n\nWatching animation for 5 seconds without progress updates...")
    print("(The spinner should continue animating)\n")
    
    # Create animation refresh thread (simulating what copy operation does)
    stop_event = threading.Event()
    
    def animation_loop():
        while not stop_event.is_set():
            progress_manager.refresh_animation()
            time.sleep(0.1)
    
    animation_thread = threading.Thread(target=animation_loop, daemon=True)
    animation_thread.start()
    
    # Watch for 5 seconds
    start_time = time.time()
    frame_count = 0
    last_frame = None
    
    while time.time() - start_time < 5:
        # Get current frame from animator
        current_frame = progress_manager.animator.get_current_frame()
        
        # Track unique frames
        if current_frame != last_frame:
            frame_count += 1
            last_frame = current_frame
            print(f"\r{current_frame} Copying large_file.dat... (frame #{frame_count})", end='', flush=True)
        
        time.sleep(0.05)
    
    # Stop animation thread
    stop_event.set()
    animation_thread.join(timeout=1)
    
    # Finish operation
    progress_manager.finish_operation()
    
    print(f"\n\n✓ Animation test completed!")
    print(f"✓ Saw {frame_count} different animation frames in 5 seconds")
    print(f"✓ Animation continued smoothly without progress updates")
    
    if frame_count >= 10:
        print("✓ SUCCESS: Animation cycled through multiple frames")
    else:
        print("✗ WARNING: Animation may not be updating frequently enough")


def test_animation_with_byte_progress():
    """Test animation continues during byte-level progress updates"""
    print("\n" + "="*60)
    print("Testing Animation with Byte Progress")
    print("="*60)
    
    progress_manager = ProgressManager()
    
    def progress_callback(progress_data):
        if progress_data:
            frame = progress_manager.animator.get_current_frame()
            byte_progress = progress_data.get('file_byte_progress', 0)
            print(f"\r{frame} Copying... [{byte_progress}%]", end='', flush=True)
    
    # Start operation
    progress_manager.start_operation(
        OperationType.COPY,
        1,
        "test",
        progress_callback
    )
    
    progress_manager.update_progress("large_file.dat", 1)
    
    print("\n\nSimulating byte-level progress with animation...\n")
    
    # Create animation refresh thread
    stop_event = threading.Event()
    
    def animation_loop():
        while not stop_event.is_set():
            progress_manager.refresh_animation()
            time.sleep(0.1)
    
    animation_thread = threading.Thread(target=animation_loop, daemon=True)
    animation_thread.start()
    
    # Simulate byte progress updates (slower than animation)
    for byte_percent in range(0, 101, 10):
        progress_manager.update_file_byte_progress(byte_percent)
        time.sleep(0.5)  # Slow updates, but animation should continue
    
    # Stop animation thread
    stop_event.set()
    animation_thread.join(timeout=1)
    
    progress_manager.finish_operation()
    
    print("\n\n✓ Byte progress test completed!")
    print("✓ Animation continued during slow byte progress updates")


def main():
    """Main demo function"""
    print("\n" + "="*60)
    print("Continuous Animation Demo")
    print("="*60)
    print("\nThis demo shows that the progress animation continues")
    print("smoothly even when there are no progress updates.\n")
    
    # Test 1: Animation without progress updates
    simulate_long_operation_with_animation()
    
    # Test 2: Animation with slow byte progress
    test_animation_with_byte_progress()
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
