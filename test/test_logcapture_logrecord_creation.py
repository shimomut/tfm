#!/usr/bin/env python3
"""
Test LogCapture.write() creates LogRecords correctly
"""

import sys
import logging
from collections import deque
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from tfm_log_manager import LogCapture
from tfm_const import LOG_TIME_FORMAT


class MockLogger:
    """Mock logger to capture LogRecords"""
    def __init__(self):
        self.records = []
    
    def handle(self, record):
        """Capture the record"""
        self.records.append(record)


def test_stdout_creates_info_logrecord():
    """Test that stdout writes create INFO level LogRecords"""
    log_messages = deque(maxlen=100)
    mock_logger = MockLogger()
    
    capture = LogCapture(
        log_messages=log_messages,
        source="STDOUT",
        logger=mock_logger
    )
    
    # Write to stdout
    capture.write("Test message")
    
    # Verify LogRecord was created
    assert len(mock_logger.records) == 1
    record = mock_logger.records[0]
    
    # Verify record properties
    assert record.name == "STDOUT"
    assert record.levelno == logging.INFO
    assert record.msg == "Test message"
    assert hasattr(record, 'is_stream_capture')
    assert record.is_stream_capture is True
    
    print("✓ stdout creates INFO LogRecord")


def test_stderr_creates_warning_logrecord():
    """Test that stderr writes create WARNING level LogRecords"""
    log_messages = deque(maxlen=100)
    mock_logger = MockLogger()
    
    capture = LogCapture(
        log_messages=log_messages,
        source="STDERR",
        logger=mock_logger
    )
    
    # Write to stderr
    capture.write("Error message")
    
    # Verify LogRecord was created
    assert len(mock_logger.records) == 1
    record = mock_logger.records[0]
    
    # Verify record properties
    assert record.name == "STDERR"
    assert record.levelno == logging.WARNING
    assert record.msg == "Error message"
    assert hasattr(record, 'is_stream_capture')
    assert record.is_stream_capture is True
    
    print("✓ stderr creates WARNING LogRecord")


def test_raw_text_preserved():
    """Test that raw text is preserved without stripping"""
    log_messages = deque(maxlen=100)
    mock_logger = MockLogger()
    
    capture = LogCapture(
        log_messages=log_messages,
        source="STDOUT",
        logger=mock_logger
    )
    
    # Write text with leading/trailing spaces
    capture.write("  Text with spaces  ")
    
    # Verify raw text is preserved in msg field
    assert len(mock_logger.records) == 1
    record = mock_logger.records[0]
    assert record.msg == "  Text with spaces  "
    
    print("✓ Raw text preserved without stripping")


def test_multiline_text_preserved():
    """Test that multi-line text is preserved"""
    log_messages = deque(maxlen=100)
    mock_logger = MockLogger()
    
    capture = LogCapture(
        log_messages=log_messages,
        source="STDOUT",
        logger=mock_logger
    )
    
    # Write multi-line text
    multiline = "Line 1\nLine 2\nLine 3"
    capture.write(multiline)
    
    # Verify multi-line text is preserved
    assert len(mock_logger.records) == 1
    record = mock_logger.records[0]
    assert record.msg == multiline
    assert "\n" in record.msg
    
    print("✓ Multi-line text preserved")


def test_empty_text_not_logged():
    """Test that empty or whitespace-only text is not logged"""
    log_messages = deque(maxlen=100)
    mock_logger = MockLogger()
    
    capture = LogCapture(
        log_messages=log_messages,
        source="STDOUT",
        logger=mock_logger
    )
    
    # Write empty and whitespace-only text
    capture.write("")
    capture.write("   ")
    capture.write("\n")
    
    # Verify no records were created
    assert len(mock_logger.records) == 0
    
    print("✓ Empty text not logged")


def test_fallback_without_logger():
    """Test that LogCapture falls back to old behavior without logger"""
    log_messages = deque(maxlen=100)
    
    capture = LogCapture(
        log_messages=log_messages,
        source="STDOUT",
        logger=None  # No logger provided
    )
    
    # Write text
    capture.write("Test message")
    
    # Verify old behavior: message added directly to log_messages
    assert len(log_messages) == 1
    timestamp, source, message = log_messages[0]
    assert source == "STDOUT"
    assert message == "Test message"
    
    print("✓ Fallback without logger works")


def test_is_stream_capture_flag():
    """Test that is_stream_capture flag is set correctly"""
    log_messages = deque(maxlen=100)
    mock_logger = MockLogger()
    
    capture = LogCapture(
        log_messages=log_messages,
        source="STDOUT",
        logger=mock_logger
    )
    
    # Write text
    capture.write("Test")
    
    # Verify flag is set
    record = mock_logger.records[0]
    assert hasattr(record, 'is_stream_capture')
    assert record.is_stream_capture is True
    
    print("✓ is_stream_capture flag set correctly")


if __name__ == '__main__':
    print("Testing LogCapture LogRecord creation...")
    print()
    
    test_stdout_creates_info_logrecord()
    test_stderr_creates_warning_logrecord()
    test_raw_text_preserved()
    test_multiline_text_preserved()
    test_empty_text_not_logged()
    test_fallback_without_logger()
    test_is_stream_capture_flag()
    
    print()
    print("All tests passed! ✓")
