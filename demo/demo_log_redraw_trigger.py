#!/usr/bin/env python3
"""
Demo script showing log redraw trigger functionality

This demo shows how TFM automatically redraws when new log messages are added.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def simulate_log_activity():
    """Simulate various types of log activity"""
    print("Demo: Log Redraw Trigger Functionality")
    print("=" * 50)
    print()
    
    print("This demo shows how TFM detects log updates and triggers redraws.")
    print("In a real TFM session, any output to stdout/stderr would trigger a redraw.")
    print()
    
    # Simulate different types of log messages
    log_sources = [
        ("SYSTEM", "System initialization complete"),
        ("CONFIG", "Loading configuration from ~/.tfm/config.py"),
        ("FILE", "Scanning directory: /home/user/projects"),
        ("OPERATION", "Copying file: document.txt"),
        ("ERROR", "Permission denied: /root/secret.txt"),
        ("NETWORK", "Remote log server started on port 8888"),
        ("SEARCH", "Found 15 matches for pattern '*.py'"),
        ("FILTER", "Applied filter: *.txt (showing 42 files)"),
    ]
    
    print("Simulating log messages that would trigger redraws:")
    print()
    
    for i, (source, message) in enumerate(log_sources, 1):
        print(f"[{i:2d}] {source:>8}: {message}")
        time.sleep(0.5)  # Simulate real-time activity
    
    print()
    print("In TFM, each of these messages would:")
    print("  1. Be captured by LogCapture.write()")
    print("  2. Trigger LogManager._on_message_added()")
    print("  3. Set has_new_messages = True")
    print("  4. Cause main loop to detect update via has_log_updates()")
    print("  5. Set needs_full_redraw = True")
    print("  6. Redraw the entire interface including updated log pane")
    print("  7. Automatically mark updates as processed in draw_log_pane()")

def demonstrate_update_detection():
    """Demonstrate the update detection mechanism"""
    from tfm_log_manager import LogManager
    from unittest.mock import Mock
    
    print("\nDemonstrating LogManager update detection:")
    print("-" * 45)
    
    # Create a mock config
    mock_config = Mock()
    mock_config.MAX_LOG_MESSAGES = 100
    
    # Create LogManager
    log_manager = LogManager(mock_config)
    
    print(f"Initial state - has_log_updates(): {log_manager.has_log_updates()}")
    
    # Add a message
    log_manager.add_message("DEMO", "This is a test message")
    print(f"After adding message - has_log_updates(): {log_manager.has_log_updates()}")
    
    # Mark as processed
    log_manager.mark_log_updates_processed()
    print(f"After marking processed - has_log_updates(): {log_manager.has_log_updates()}")
    
    # Simulate stdout output
    print("Simulating stdout output...")
    print(f"After stdout - has_log_updates(): {log_manager.has_log_updates()}")
    
    # Mark as processed again
    log_manager.mark_log_updates_processed()
    print(f"After marking processed again - has_log_updates(): {log_manager.has_log_updates()}")
    
    # Clean up
    log_manager.restore_stdio()

def show_integration_example():
    """Show how this integrates with the main loop"""
    print("\nMain Loop Integration Example:")
    print("-" * 30)
    print()
    
    example_code = '''
    def run(self):
        """Main application loop"""
        while True:
            # Check for log updates and trigger redraw if needed
            if self.log_manager.has_log_updates():
                self.needs_full_redraw = True
            
            # Only do full redraw when needed
            if self.needs_full_redraw:
                self.refresh_files()
                self.clear_screen_with_background()
                
                # Draw interface
                self.draw_header()
                self.draw_files()
                self.draw_log_pane()  # ← Updates marked as processed here
                self.draw_status()
                
                # Refresh screen
                self.stdscr.refresh()
                self.needs_full_redraw = False
            
            # ... rest of main loop ...
    
    # In LogManager.draw_log_pane():
    def draw_log_pane(self, stdscr, y_start, height, width):
        try:
            # ... draw log content ...
        finally:
            # Always mark updates as processed when drawing
            self.mark_log_updates_processed()
    '''
    
    print("Key changes to main loop:")
    print(example_code)

def main():
    """Main demo function"""
    print("TFM Log Redraw Trigger Demo")
    print("=" * 40)
    print()
    
    print("This demo shows the automatic log redraw functionality added to TFM.")
    print("When log messages are added (via stdout, stderr, or direct calls),")
    print("TFM automatically detects the updates and triggers a redraw.")
    print()
    
    # Run the demonstrations
    simulate_log_activity()
    demonstrate_update_detection()
    show_integration_example()
    
    print("\nBenefits of this feature:")
    print("  • Real-time log updates without manual refresh")
    print("  • Immediate feedback for file operations")
    print("  • Better user experience with live status updates")
    print("  • Automatic redraw only when needed (efficient)")
    print("  • Works with both captured output and direct log messages")
    print()
    
    print("Usage in TFM:")
    print("  • File operations show progress in real-time")
    print("  • Error messages appear immediately")
    print("  • Remote log monitoring updates live")
    print("  • System messages are instantly visible")
    print("  • Background operations provide live feedback")

if __name__ == '__main__':
    main()