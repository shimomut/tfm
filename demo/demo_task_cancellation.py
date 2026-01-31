#!/usr/bin/env python3
"""
Demo: Task Cancellation with ESC Key

This demo shows how TFM blocks actions during task execution and allows
cancellation with the ESC key.

Features demonstrated:
1. Actions are blocked while a task is active
2. ESC key cancels the active task
3. Warning messages inform the user about blocked actions
4. Actions work normally after task completion or cancellation
"""

import sys
import time
from pathlib import Path

# Add src and ttk to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'ttk'))

from tfm_base_task import BaseTask
from tfm_log_manager import getLogger


class DemoTask(BaseTask):
    """Demo task that simulates a long-running operation."""
    
    def __init__(self, file_manager):
        super().__init__(file_manager, "DemoTask")
        self.state = "idle"
        self.progress = 0
    
    def start(self):
        """Start the demo task."""
        self.state = "running"
        self.progress = 0
        self.logger.info("Demo task started - simulating long operation...")
        self.logger.info("Try pressing keys (they will be blocked)")
        self.logger.info("Press ESC to cancel the task")
        
        # Simulate work in background
        # In a real task, this would be done in a thread
        self._simulate_work()
    
    def _simulate_work(self):
        """Simulate work being done."""
        # This is just for demo - real tasks would use threads
        for i in range(10):
            if self.is_cancelled():
                self.logger.info("Task cancelled by user")
                self.state = "cancelled"
                self.file_manager._clear_task()
                return
            
            self.progress = (i + 1) * 10
            self.logger.info(f"Progress: {self.progress}%")
            time.sleep(0.5)
        
        self.logger.info("Task completed successfully")
        self.state = "completed"
        self.file_manager._clear_task()
    
    def cancel(self):
        """Cancel the task."""
        self.logger.info("Cancellation requested...")
        self.request_cancellation()
    
    def is_active(self):
        """Check if task is active."""
        return self.state == "running"
    
    def get_state(self):
        """Get current state."""
        return self.state


def main():
    """Run the demo."""
    print("=" * 70)
    print("Task Cancellation Demo")
    print("=" * 70)
    print()
    print("This demo shows:")
    print("1. Starting a long-running task")
    print("2. Blocking actions while task is active")
    print("3. Cancelling task with ESC key")
    print()
    print("Key behaviors:")
    print("- While task is running: All actions are blocked")
    print("- Press ESC: Cancels the active task")
    print("- After cancellation: Actions work normally again")
    print()
    print("=" * 70)
    print()
    
    # Create a mock file manager for demo
    class MockFileManager:
        def __init__(self):
            self.logger = getLogger("Demo")
            self.current_task = None
            self._dirty = False
        
        def start_task(self, task):
            """Start a task."""
            if self.current_task and self.current_task.is_active():
                raise RuntimeError("Cannot start task: another task is already active")
            self.current_task = task
            task.start()
        
        def cancel_current_task(self):
            """Cancel the current task."""
            if self.current_task and self.current_task.is_active():
                self.current_task.cancel()
        
        def _clear_task(self):
            """Clear the current task."""
            self.current_task = None
        
        def mark_dirty(self):
            """Mark for redraw."""
            self._dirty = True
    
    fm = MockFileManager()
    
    # Demo 1: Start a task
    print("Demo 1: Starting a task")
    print("-" * 70)
    task = DemoTask(fm)
    fm.start_task(task)
    print(f"Task state: {task.get_state()}")
    print(f"Task active: {task.is_active()}")
    print()
    
    # Demo 2: Try to perform actions (blocked)
    print("Demo 2: Actions are blocked during task execution")
    print("-" * 70)
    if fm.current_task and fm.current_task.is_active():
        print("✓ Task is active - actions would be blocked")
        print("  User would see: 'Action blocked: task in progress (press ESC to cancel)'")
    print()
    
    # Demo 3: Cancel the task
    print("Demo 3: Cancelling task with ESC key")
    print("-" * 70)
    print("Simulating ESC key press...")
    fm.cancel_current_task()
    time.sleep(0.1)  # Give task time to process cancellation
    print(f"Task state: {task.get_state()}")
    print(f"Task active: {task.is_active()}")
    print()
    
    # Demo 4: Actions work after cancellation
    print("Demo 4: Actions work normally after cancellation")
    print("-" * 70)
    if not (fm.current_task and fm.current_task.is_active()):
        print("✓ No active task - actions would work normally")
    print()
    
    print("=" * 70)
    print("Demo completed!")
    print()
    print("In TFM:")
    print("- File operations (copy, move, delete) are tasks")
    print("- Archive operations (create, extract) are tasks")
    print("- Press ESC during any operation to cancel it")
    print("- All keyboard input is blocked during operations")
    print("=" * 70)


if __name__ == '__main__':
    main()
