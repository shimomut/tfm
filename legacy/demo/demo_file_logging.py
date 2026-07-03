#!/usr/bin/env python3
"""
Demo: File Logging Feature

This demo shows how the file logging feature works by:
1. Creating a LogManager with file logging enabled
2. Writing various log messages
3. Displaying the log file content

Run with: PYTHONPATH=.:src:ttk python demo/demo_file_logging.py
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_log_manager import LogManager
from unittest.mock import Mock


def main():
    """Demonstrate file logging functionality"""
    
    # Create a temporary log file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
    log_file_path = temp_file.name
    temp_file.close()
    
    print("=" * 60)
    print("File Logging Demo")
    print("=" * 60)
    print(f"\nLog file: {log_file_path}\n")
    
    # Create mock config
    mock_config = Mock()
    mock_config.MAX_LOG_MESSAGES = 100
    
    # Create LogManager with file logging enabled
    print("Creating LogManager with file logging enabled...")
    log_manager = LogManager(
        mock_config,
        remote_port=None,
        is_desktop_mode=False,
        log_file=log_file_path
    )
    
    # Get loggers for different components
    main_logger = log_manager.getLogger("Main")
    fileop_logger = log_manager.getLogger("FileOp")
    archive_logger = log_manager.getLogger("Archive")
    
    # Write various log messages
    sys.__stdout__.write("\nWriting log messages...\n")
    sys.__stdout__.write("-" * 60 + "\n")
    sys.__stdout__.flush()
    
    main_logger.info("Application started")
    main_logger.info("Configuration loaded successfully")
    
    fileop_logger.info("Copying file: source.txt -> destination.txt")
    fileop_logger.info("Copy operation completed")
    
    archive_logger.warning("Archive file is large (500MB)")
    archive_logger.info("Extracting archive: data.zip")
    
    # Write to stdout and stderr (these should also be logged)
    print("This is stdout output")
    print("This is stderr output", file=sys.stderr)
    
    main_logger.error("Simulated error: Connection timeout")
    main_logger.info("Application shutting down")
    
    sys.__stdout__.write("-" * 60 + "\n")
    sys.__stdout__.flush()
    
    # Close the file handler to flush all messages
    log_manager._file_logging_handler.close()
    
    # Read and display the log file
    sys.__stdout__.write("\nLog file contents:\n")
    sys.__stdout__.write("=" * 60 + "\n")
    sys.__stdout__.flush()
    with open(log_file_path, 'r') as f:
        content = f.read()
        sys.__stdout__.write(content)
        sys.__stdout__.flush()
    sys.__stdout__.write("=" * 60 + "\n")
    sys.__stdout__.flush()
    
    # Show statistics
    lines = content.strip().split('\n')
    sys.__stdout__.write(f"\nTotal log entries: {len(lines)}\n")
    sys.__stdout__.write(f"Log file size: {os.path.getsize(log_file_path)} bytes\n")
    sys.__stdout__.flush()
    
    # Clean up
    log_manager.restore_stdio()
    os.unlink(log_file_path)
    
    sys.__stdout__.write(f"\nLog file removed: {log_file_path}\n")
    sys.__stdout__.write("\nDemo completed successfully!\n")
    sys.__stdout__.flush()


if __name__ == '__main__':
    main()
