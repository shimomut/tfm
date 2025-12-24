#!/usr/bin/env python3
"""
Tests for TFM logging handlers
"""

import sys
import os
import logging
import time
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_logging_handlers import LogPaneHandler, StreamOutputHandler, RemoteMonitoringHandler


def test_log_pane_handler_basic():
    """Test basic LogPaneHandler functionality"""
    handler = LogPaneHandler(max_messages=10)
    
    # Create a logger message (not stream capture)
    record = logging.LogRecord(
        name="TestLogger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = False
    
    handler.emit(record)
    messages = handler.get_messages()
    
    assert len(messages) == 1
    timestamp, source, message = messages[0]
    assert source == "TestLogger"
    assert "INFO: Test message" in message
    print("✓ LogPaneHandler basic test passed")


def test_log_pane_handler_stream_capture():
    """Test LogPaneHandler with stream capture (stdout/stderr)"""
    handler = LogPaneHandler(max_messages=10)
    
    # Create a stream capture message
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Raw stdout output",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = True
    
    handler.emit(record)
    messages = handler.get_messages()
    
    assert len(messages) == 1
    timestamp, source, message = messages[0]
    assert source == "STDOUT"
    assert message == "Raw stdout output"
    print("✓ LogPaneHandler stream capture test passed")


def test_log_pane_handler_multiline():
    """Test LogPaneHandler with multi-line stream capture"""
    handler = LogPaneHandler(max_messages=10)
    
    # Create a multi-line stream capture message
    record = logging.LogRecord(
        name="STDERR",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="Line 1\nLine 2\nLine 3",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = True
    
    handler.emit(record)
    messages = handler.get_messages()
    
    # Should have 3 separate messages (one per line)
    assert len(messages) == 3
    assert messages[0][2] == "Line 1"
    assert messages[1][2] == "Line 2"
    assert messages[2][2] == "Line 3"
    print("✓ LogPaneHandler multi-line test passed")


def test_log_pane_handler_max_messages():
    """Test LogPaneHandler message retention limit"""
    handler = LogPaneHandler(max_messages=3)
    
    # Add 5 messages
    for i in range(5):
        record = logging.LogRecord(
            name="TestLogger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Message {i}",
            args=(),
            exc_info=None
        )
        record.is_stream_capture = False
        handler.emit(record)
    
    messages = handler.get_messages()
    
    # Should only have 3 messages (oldest discarded)
    assert len(messages) == 3
    # Should have messages 2, 3, 4 (0 and 1 were discarded)
    assert "Message 2" in messages[0][2]
    assert "Message 3" in messages[1][2]
    assert "Message 4" in messages[2][2]
    print("✓ LogPaneHandler max messages test passed")


def test_stream_output_handler_logger_message():
    """Test StreamOutputHandler with logger message"""
    import io
    stream = io.StringIO()
    handler = StreamOutputHandler(stream)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # Create a logger message
    record = logging.LogRecord(
        name="TestLogger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = False
    
    handler.emit(record)
    output = stream.getvalue()
    
    assert "INFO: Test message" in output
    print("✓ StreamOutputHandler logger message test passed")


def test_stream_output_handler_stream_capture():
    """Test StreamOutputHandler with stream capture"""
    import io
    stream = io.StringIO()
    handler = StreamOutputHandler(stream)
    
    # Create a stream capture message
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Raw output",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = True
    
    handler.emit(record)
    output = stream.getvalue()
    
    # Should be raw output without formatting
    assert output.strip() == "Raw output"
    print("✓ StreamOutputHandler stream capture test passed")


def test_remote_monitoring_handler_basic():
    """Test RemoteMonitoringHandler basic functionality"""
    handler = RemoteMonitoringHandler(port=0)  # Port 0 = let OS choose
    
    # Don't start server for this basic test, just test emit doesn't crash
    record = logging.LogRecord(
        name="TestLogger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = False
    
    # Should not crash even without server running
    handler.emit(record)
    print("✓ RemoteMonitoringHandler basic test passed")


def test_is_stream_capture_flag():
    """Test that is_stream_capture flag is properly handled"""
    handler = LogPaneHandler(max_messages=10)
    
    # Test with flag set to True
    record1 = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Stream output",
        args=(),
        exc_info=None
    )
    record1.is_stream_capture = True
    handler.emit(record1)
    
    # Test with flag set to False
    record2 = logging.LogRecord(
        name="Logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Logger output",
        args=(),
        exc_info=None
    )
    record2.is_stream_capture = False
    handler.emit(record2)
    
    # Test with flag missing (should default to False)
    record3 = logging.LogRecord(
        name="Logger2",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Default output",
        args=(),
        exc_info=None
    )
    # Don't set is_stream_capture
    handler.emit(record3)
    
    messages = handler.get_messages()
    assert len(messages) == 3
    
    # First should be raw stream output
    assert messages[0][1] == "STDOUT"
    assert messages[0][2] == "Stream output"
    
    # Second should be formatted logger output
    assert messages[1][1] == "Logger"
    assert "INFO: Logger output" in messages[1][2]
    
    # Third should be formatted logger output (default)
    assert messages[2][1] == "Logger2"
    assert "INFO: Default output" in messages[2][2]
    
    print("✓ is_stream_capture flag test passed")


if __name__ == '__main__':
    print("Running logging handlers tests...\n")
    
    test_log_pane_handler_basic()
    test_log_pane_handler_stream_capture()
    test_log_pane_handler_multiline()
    test_log_pane_handler_max_messages()
    test_stream_output_handler_logger_message()
    test_stream_output_handler_stream_capture()
    test_remote_monitoring_handler_basic()
    test_is_stream_capture_flag()
    
    print("\n✅ All tests passed!")
