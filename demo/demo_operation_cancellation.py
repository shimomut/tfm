#!/usr/bin/env python3
"""
Demo: Operation Cancellation with ESC Key

This demo demonstrates:
1. Input blocking during file operations
2. ESC key cancellation support
3. Clean operation cleanup after cancellation
"""

import os
import sys
import time
import tempfile
import threading

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path
from tfm_progress_manager import ProgressManager, OperationType


def simulate_cancellable_operation():
    """Simulate a long operation that can be cancelled"""
    print("="*60)
    print("Testing Operation Cancellation")
    print("="*60)
    print("\nThis demo simulates a long copy operation.")
    print("Press 'c' to simulate ESC key cancellation.\n")
    
    # Simulate operation state
    class MockFileManager:
        def __init__(self):
            self.operation_in_progress = False
            self.operation_cancelled = False
    
    file_manager = MockFileManager()
    progress_manager = ProgressManager()
    
    def progress_callback(progress_data):
        if progress_data:
            frame = progress_manager.animator.get_current_frame()
            processed = progress_data['processed_items']
            total = progress_data['total_items']
            current = progress_data['current_item']
            print(f"\r{frame} Copying... {processed}/{total} - {current}", end='', flush=True)
    
    # Simulate copy operation
    def copy_operation():
        file_manager.operation_in_progress = True
        
        progress_manager.start_operation(
            OperationType.COPY,
            100,
            "test",
            progress_callback
        )
        
        # Start animation refresh
        stop_event = threading.Event()
        
        def animation_loop():
            while not stop_event.is_set():
                progress_manager.refresh_animation()
                time.sleep(0.1)
        
        animation_thread = threading.Thread(target=animation_loop, daemon=True)
        animation_thread.start()
        
        try:
            for i in range(100):
                # Check for cancellation
                if file_manager.operation_cancelled:
                    print("\n\n✓ Operation cancelled by user!")
                    break
                
                progress_manager.update_progress(f"file_{i}.txt", i + 1)
                time.sleep(0.1)  # Simulate file copy time
            else:
                print("\n\n✓ Operation completed successfully!")
        finally:
            stop_event.set()
            progress_manager.finish_operation()
            file_manager.operation_in_progress = False
    
    # Start operation in background
    operation_thread = threading.Thread(target=copy_operation, daemon=True)
    operation_thread.start()
    
    # Simulate user input monitoring
    print("Operation started. Press 'c' to cancel (simulating ESC key)...\n")
    
    while operation_thread.is_alive():
        # In real TFM, this would be the main event loop checking for ESC
        # Here we simulate with 'c' key
        try:
            import select
            import sys
            
            # Check if input is available (non-blocking)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                if key.lower() == 'c':
                    print("\n\nCancellation requested...")
                    file_manager.operation_cancelled = True
        except Exception:
            # Fallback for systems without select
            time.sleep(0.1)
    
    operation_thread.join(timeout=2)
    
    print("\n" + "="*60)
    print("Cancellation Test Completed")
    print("="*60)


def test_input_blocking():
    """Test that input is blocked during operations"""
    print("\n" + "="*60)
    print("Testing Input Blocking")
    print("="*60)
    
    class MockFileManager:
        def __init__(self):
            self.operation_in_progress = False
            self.operation_cancelled = False
    
    file_manager = MockFileManager()
    
    print("\nSimulating input handling:")
    print("- Normal mode: All keys processed")
    print("- Operation mode: Only ESC (27) processed\n")
    
    # Test normal mode
    print("Normal mode (operation_in_progress=False):")
    file_manager.operation_in_progress = False
    test_keys = [ord('a'), ord('j'), ord('k'), 27]  # a, j, k, ESC
    
    for key in test_keys:
        if file_manager.operation_in_progress:
            if key == 27:
                print(f"  Key {key} (ESC): Cancelling operation")
                file_manager.operation_cancelled = True
            else:
                print(f"  Key {key}: BLOCKED (operation in progress)")
        else:
            print(f"  Key {key}: Processed normally")
    
    # Test operation mode
    print("\nOperation mode (operation_in_progress=True):")
    file_manager.operation_in_progress = True
    file_manager.operation_cancelled = False
    
    for key in test_keys:
        if file_manager.operation_in_progress:
            if key == 27:
                print(f"  Key {key} (ESC): Cancelling operation")
                file_manager.operation_cancelled = True
            else:
                print(f"  Key {key}: BLOCKED (operation in progress)")
        else:
            print(f"  Key {key}: Processed normally")
    
    print("\n✓ Input blocking test completed!")
    print("✓ Only ESC key is processed during operations")


def main():
    """Main demo function"""
    print("\n" + "="*60)
    print("Operation Cancellation Demo")
    print("="*60)
    print("\nThis demo shows:")
    print("1. Input is blocked during file operations")
    print("2. ESC key can cancel operations")
    print("3. Operations clean up properly after cancellation\n")
    
    # Test input blocking logic
    test_input_blocking()
    
    # Test cancellable operation
    print("\n" + "="*60)
    print("Starting Cancellable Operation Test")
    print("="*60)
    print("\nNote: In real TFM, press ESC to cancel.")
    print("In this demo, press 'c' to simulate ESC.\n")
    
    input("Press Enter to start the operation test...")
    
    simulate_cancellable_operation()
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)
    print("\nIn TFM:")
    print("- File operations block all input except ESC")
    print("- Press ESC during operation to cancel")
    print("- Partial files are cleaned up on cancellation")
    print("- UI remains responsive with progress updates")


if __name__ == "__main__":
    main()
