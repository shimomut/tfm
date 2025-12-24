#!/usr/bin/env python3
"""
Integration test demonstrating log level filtering in action.
Shows how different loggers can have different levels and how messages are filtered.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Save original stdout before importing LogManager
original_stdout = sys.stdout

from tfm_log_manager import LogManager


class MockConfig:
    """Mock configuration object for testing"""
    MAX_LOG_MESSAGES = 100


def main():
    """Demonstrate log level filtering"""
    original_stdout.write("=" * 60 + "\n")
    original_stdout.write("Log Level Filtering Integration Test\n")
    original_stdout.write("=" * 60 + "\n\n")
    
    # Create LogManager with handlers configured
    config = MockConfig()
    log_manager = LogManager(config, debug_mode=True)  # debug_mode to see output
    log_manager.configure_handlers(log_pane_enabled=True, stream_output_enabled=True, remote_enabled=False)
    
    original_stdout.write("Scenario 1: Default level (INFO)\n")
    original_stdout.write("-" * 60 + "\n")
    
    # Create logger with default level (INFO)
    logger1 = log_manager.getLogger("MainApp")
    original_stdout.write(f"MainApp logger level: {logging.getLevelName(logger1.level)}\n")
    
    # These messages should appear
    logger1.info("This INFO message should appear")
    logger1.warning("This WARNING message should appear")
    logger1.error("This ERROR message should appear")
    
    # This message should be filtered
    logger1.debug("This DEBUG message should be filtered (not visible)")
    
    original_stdout.write("\n")
    
    original_stdout.write("Scenario 2: Per-logger override (DEBUG)\n")
    original_stdout.write("-" * 60 + "\n")
    
    # Set a specific logger to DEBUG level
    log_manager.set_logger_level("DebugLogger", logging.DEBUG)
    logger2 = log_manager.getLogger("DebugLogger")
    original_stdout.write(f"DebugLogger level: {logging.getLevelName(logger2.level)}\n")
    
    # All messages should appear
    logger2.debug("This DEBUG message should appear (logger has DEBUG level)")
    logger2.info("This INFO message should appear")
    logger2.warning("This WARNING message should appear")
    
    original_stdout.write("\n")
    
    original_stdout.write("Scenario 3: Change default level (WARNING)\n")
    original_stdout.write("-" * 60 + "\n")
    
    # Change default level to WARNING
    log_manager.set_default_log_level(logging.WARNING)
    logger3 = log_manager.getLogger("NewLogger")
    original_stdout.write(f"NewLogger level: {logging.getLevelName(logger3.level)}\n")
    original_stdout.write(f"MainApp logger updated to: {logging.getLevelName(logger1.level)}\n")
    original_stdout.write(f"DebugLogger kept override: {logging.getLevelName(logger2.level)}\n")
    
    # Only WARNING and above should appear for logger3
    logger3.debug("This DEBUG message should be filtered")
    logger3.info("This INFO message should be filtered")
    logger3.warning("This WARNING message should appear")
    logger3.error("This ERROR message should appear")
    
    # DebugLogger should still show DEBUG messages (has override)
    logger2.debug("DebugLogger still shows DEBUG (has override)")
    
    original_stdout.write("\n")
    
    original_stdout.write("Scenario 4: Clear override\n")
    original_stdout.write("-" * 60 + "\n")
    
    # Clear the DEBUG override
    log_manager.clear_logger_level("DebugLogger")
    original_stdout.write(f"DebugLogger after clearing override: {logging.getLevelName(logger2.level)}\n")
    
    # Now DEBUG should be filtered for logger2
    logger2.debug("This DEBUG message should now be filtered (override cleared)")
    logger2.warning("This WARNING message should appear")
    
    original_stdout.write("\n")
    
    original_stdout.write("=" * 60 + "\n")
    original_stdout.write("✓ Integration test complete\n")
    original_stdout.write("=" * 60 + "\n")
    
    # Clean up
    log_manager.restore_stdio()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        original_stdout.write(f"✗ ERROR: {e}\n")
        original_stdout.flush()
        import traceback
        traceback.print_exc(file=original_stdout)
        sys.exit(1)
