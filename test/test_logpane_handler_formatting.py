#!/usr/bin/env python3
"""
Test LogPaneHandler message formatting functionality.

This test verifies that:
1. Logger messages are formatted with timestamp, logger name, level, and message
2. Stdout/stderr messages are displayed as-is with minimal formatting
3. Multi-line output is preserved correctly
4. The emit() method dispatches to the correct formatter based on is_stream_capture flag
"""

import logging
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_logging_handlers import LogPaneHandler
from tfm_const import LOG_TIME_FORMAT


def test_format_logger_message():
    """Test that logger messages are formatted correctly."""
    handler = LogPaneHandler()
    
    # Create a logger message record
    record = logging.LogRecord(
        name="TestLogger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.created = datetime(2024, 1, 15, 14, 23, 45).timestamp()
    
    # Format the message
    timestamp, source, message = handler.format_logger_message(record)
    
    # Verify format
    assert timestamp == "14:23:45", f"Expected timestamp '14:23:45', got '{timestamp}'"
    assert source == "TestLogger", f"Expected source 'TestLogger', got '{source}'"
    assert message == "INFO: Test message", f"Expected message 'INFO: Test message', got '{message}'"
    
    print("✓ Logger message formatting works correctly")


def test_format_stream_message_single_line():
    """Test that single-line stdout/stderr messages are formatted correctly."""
    handler = LogPaneHandler()
    
    # Create a stdout record
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Single line output",
        args=(),
        exc_info=None
    )
    record.created = datetime(2024, 1, 15, 14, 23, 45).timestamp()
    
    # Format the message
    formatted_lines = handler.format_stream_message(record)
    
    # Verify format
    assert len(formatted_lines) == 1, f"Expected 1 line, got {len(formatted_lines)}"
    timestamp, source, message = formatted_lines[0]
    assert timestamp == "14:23:45", f"Expected timestamp '14:23:45', got '{timestamp}'"
    assert source == "STDOUT", f"Expected source 'STDOUT', got '{source}'"
    assert message == "Single line output", f"Expected message 'Single line output', got '{message}'"
    
    print("✓ Single-line stream message formatting works correctly")


def test_format_stream_message_multi_line():
    """Test that multi-line stdout/stderr messages preserve all lines."""
    handler = LogPaneHandler()
    
    # Create a multi-line stdout record
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Line 1\nLine 2\nLine 3",
        args=(),
        exc_info=None
    )
    record.created = datetime(2024, 1, 15, 14, 23, 45).timestamp()
    
    # Format the message
    formatted_lines = handler.format_stream_message(record)
    
    # Verify format
    assert len(formatted_lines) == 3, f"Expected 3 lines, got {len(formatted_lines)}"
    
    for i, (timestamp, source, message) in enumerate(formatted_lines):
        assert timestamp == "14:23:45", f"Line {i}: Expected timestamp '14:23:45', got '{timestamp}'"
        assert source == "STDOUT", f"Line {i}: Expected source 'STDOUT', got '{source}'"
        assert message == f"Line {i+1}", f"Line {i}: Expected message 'Line {i+1}', got '{message}'"
    
    print("✓ Multi-line stream message formatting works correctly")


def test_emit_logger_message():
    """Test that emit() correctly dispatches logger messages."""
    handler = LogPaneHandler()
    
    # Create a logger message record (no is_stream_capture flag)
    record = logging.LogRecord(
        name="TestLogger",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="Warning message",
        args=(),
        exc_info=None
    )
    record.created = datetime(2024, 1, 15, 14, 23, 45).timestamp()
    
    # Emit the record
    handler.emit(record)
    
    # Verify message was added
    messages = handler.get_messages()
    assert len(messages) == 1, f"Expected 1 message, got {len(messages)}"
    
    timestamp, source, message = messages[0]
    assert timestamp == "14:23:45", f"Expected timestamp '14:23:45', got '{timestamp}'"
    assert source == "TestLogger", f"Expected source 'TestLogger', got '{source}'"
    assert message == "WARNING: Warning message", f"Expected message 'WARNING: Warning message', got '{message}'"
    
    print("✓ emit() correctly handles logger messages")


def test_emit_stream_message():
    """Test that emit() correctly dispatches stdout/stderr messages."""
    handler = LogPaneHandler()
    
    # Create a stdout record with is_stream_capture flag
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Stream output",
        args=(),
        exc_info=None
    )
    record.created = datetime(2024, 1, 15, 14, 23, 45).timestamp()
    record.is_stream_capture = True  # Mark as stream capture
    
    # Emit the record
    handler.emit(record)
    
    # Verify message was added
    messages = handler.get_messages()
    assert len(messages) == 1, f"Expected 1 message, got {len(messages)}"
    
    timestamp, source, message = messages[0]
    assert timestamp == "14:23:45", f"Expected timestamp '14:23:45', got '{timestamp}'"
    assert source == "STDOUT", f"Expected source 'STDOUT', got '{source}'"
    assert message == "Stream output", f"Expected message 'Stream output', got '{message}'"
    
    print("✓ emit() correctly handles stream messages")


def test_emit_stream_message_multi_line():
    """Test that emit() correctly handles multi-line stream messages."""
    handler = LogPaneHandler()
    
    # Create a multi-line stdout record with is_stream_capture flag
    record = logging.LogRecord(
        name="STDERR",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="Error line 1\nError line 2",
        args=(),
        exc_info=None
    )
    record.created = datetime(2024, 1, 15, 14, 23, 45).timestamp()
    record.is_stream_capture = True  # Mark as stream capture
    
    # Emit the record
    handler.emit(record)
    
    # Verify messages were added (one per line)
    messages = handler.get_messages()
    assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
    
    # Check first line
    timestamp, source, message = messages[0]
    assert timestamp == "14:23:45", f"Line 1: Expected timestamp '14:23:45', got '{timestamp}'"
    assert source == "STDERR", f"Line 1: Expected source 'STDERR', got '{source}'"
    assert message == "Error line 1", f"Line 1: Expected message 'Error line 1', got '{message}'"
    
    # Check second line
    timestamp, source, message = messages[1]
    assert timestamp == "14:23:45", f"Line 2: Expected timestamp '14:23:45', got '{timestamp}'"
    assert source == "STDERR", f"Line 2: Expected source 'STDERR', got '{source}'"
    assert message == "Error line 2", f"Line 2: Expected message 'Error line 2', got '{message}'"
    
    print("✓ emit() correctly handles multi-line stream messages")


def test_mixed_messages():
    """Test that handler correctly handles a mix of logger and stream messages."""
    handler = LogPaneHandler()
    
    # Add a logger message
    logger_record = logging.LogRecord(
        name="FileOp",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="File copied",
        args=(),
        exc_info=None
    )
    logger_record.created = datetime(2024, 1, 15, 14, 23, 45).timestamp()
    handler.emit(logger_record)
    
    # Add a stdout message
    stdout_record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Processing...",
        args=(),
        exc_info=None
    )
    stdout_record.created = datetime(2024, 1, 15, 14, 23, 46).timestamp()
    stdout_record.is_stream_capture = True
    handler.emit(stdout_record)
    
    # Add another logger message
    logger_record2 = logging.LogRecord(
        name="FileOp",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="File not found",
        args=(),
        exc_info=None
    )
    logger_record2.created = datetime(2024, 1, 15, 14, 23, 47).timestamp()
    handler.emit(logger_record2)
    
    # Verify all messages were added correctly
    messages = handler.get_messages()
    assert len(messages) == 3, f"Expected 3 messages, got {len(messages)}"
    
    # Check logger message 1
    timestamp, source, message = messages[0]
    assert source == "FileOp", f"Message 1: Expected source 'FileOp', got '{source}'"
    assert "INFO: File copied" == message, f"Message 1: Expected 'INFO: File copied', got '{message}'"
    
    # Check stdout message
    timestamp, source, message = messages[1]
    assert source == "STDOUT", f"Message 2: Expected source 'STDOUT', got '{source}'"
    assert message == "Processing...", f"Message 2: Expected 'Processing...', got '{message}'"
    
    # Check logger message 2
    timestamp, source, message = messages[2]
    assert source == "FileOp", f"Message 3: Expected source 'FileOp', got '{source}'"
    assert "ERROR: File not found" == message, f"Message 3: Expected 'ERROR: File not found', got '{message}'"
    
    print("✓ Handler correctly handles mixed logger and stream messages")


if __name__ == '__main__':
    print("Testing LogPaneHandler message formatting...")
    print()
    
    test_format_logger_message()
    test_format_stream_message_single_line()
    test_format_stream_message_multi_line()
    test_emit_logger_message()
    test_emit_stream_message()
    test_emit_stream_message_multi_line()
    test_mixed_messages()
    
    print()
    print("All tests passed! ✓")
