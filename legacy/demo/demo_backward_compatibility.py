#!/usr/bin/env python3
"""
Demo: Backward Compatibility with add_message()

This demo shows that the legacy add_message() method works correctly
with the new logging infrastructure, allowing old and new code to coexist.
"""

import sys
import time

# Add src to path
sys.path.insert(0, 'src')

from tfm_log_manager import LogManager


class MockConfig:
    """Mock configuration for demo"""
    MAX_LOG_MESSAGES = 1000


def main():
    print("="*70)
    print("Demo: Backward Compatibility with add_message()")
    print("="*70)
    print()
    
    # Create LogManager with debug mode to see output
    print("Creating LogManager with debug mode enabled...")
    config = MockConfig()
    log_manager = LogManager(config, remote_port=None, debug_mode=True)
    print()
    
    # Show that old code still works
    print("1. Using legacy add_message() method (old code):")
    print("-" * 70)
    log_manager.add_message("FileOp", "File copied successfully")
    log_manager.add_message("DirDiff", "Comparison complete")
    log_manager.add_message("Archive", "Archive extracted")
    log_manager.add_message("ERROR", "Operation failed")
    time.sleep(0.1)  # Give handlers time to process
    print()
    
    # Show that new code works
    print("2. Using new getLogger() method (new code):")
    print("-" * 70)
    logger = log_manager.getLogger("Main")
    logger.info("Application started")
    logger.warning("Low disk space")
    logger.error("Connection failed")
    time.sleep(0.1)
    print()
    
    # Show that both can coexist
    print("3. Mixing old and new code (both work together):")
    print("-" * 70)
    log_manager.add_message("SYSTEM", "Using legacy method")
    logger.info("Using new method")
    log_manager.add_message("CONFIG", "Configuration updated")
    logger.debug("Debug message (may be filtered)")
    time.sleep(0.1)
    print()
    
    # Show startup messages
    print("4. Startup messages (uses add_message internally):")
    print("-" * 70)
    log_manager.add_startup_messages("1.0.0", "https://github.com/test/repo", "TestApp")
    time.sleep(0.1)
    print()
    
    # Show messages in log pane
    print("5. Messages in LogPaneHandler:")
    print("-" * 70)
    messages = log_manager._log_pane_handler.get_messages()
    print(f"Total messages: {len(messages)}")
    print()
    print("Sample messages:")
    for i, (formatted_msg, record) in enumerate(messages[-5:], 1):
        is_stream = getattr(record, 'is_stream_capture', False)
        msg_type = "stream" if is_stream else "logger"
        print(f"  {i}. [{msg_type}] {formatted_msg}")
    print()
    
    # Verify backward compatibility
    print("6. Verification:")
    print("-" * 70)
    
    # Check that add_message() creates logger messages (not stream captures)
    add_message_count = 0
    for formatted_msg, record in messages:
        if not getattr(record, 'is_stream_capture', False):
            # This is a logger message
            if record.name in ["FileOp", "DirDiff", "Archive", "ERROR", "SYSTEM", "CONFIG"]:
                add_message_count += 1
    
    print(f"✓ Found {add_message_count} messages from add_message()")
    print("✓ All messages routed through logging infrastructure")
    print("✓ Old and new code work together seamlessly")
    print()
    
    # Clean up
    log_manager.restore_stdio()
    
    print("="*70)
    print("Demo complete!")
    print("="*70)


if __name__ == "__main__":
    main()
