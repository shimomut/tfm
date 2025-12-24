#!/usr/bin/env python3
"""
Checkpoint 6: Verify core functionality works.

This test verifies:
1. getLogger() returns configured loggers
2. Logger messages are formatted correctly
3. Stdout/stderr is displayed as-is
"""

import sys
import logging
from collections import deque
from io import StringIO

# Save original streams before any imports that might redirect them
_original_stdout = sys.__stdout__
_original_stderr = sys.__stderr__

# Add src to path
sys.path.insert(0, 'src')

from tfm_log_manager import LogManager, LogPaneHandler, StreamOutputHandler, LoggingConfig


def print_output(msg):
    """Print to original stdout to bypass any redirection."""
    _original_stdout.write(msg + "\n")
    _original_stdout.flush()


def test_getlogger_returns_configured_logger():
    """Verify getLogger() returns a properly configured logger."""
    print_output("\n=== Test 1: getLogger() returns configured logger ===")
    
    # Create a minimal config object
    class MinimalConfig:
        MAX_LOG_MESSAGES = 1000
    
    config = MinimalConfig()
    
    # Create LogManager without remote monitoring or debug mode
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    # Configure handlers explicitly
    log_manager.configure_handlers(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_enabled=False
    )
    
    # Get a logger
    logger = log_manager.getLogger("TestLogger")
    
    # Verify it's a Logger instance
    assert isinstance(logger, logging.Logger), f"Expected logging.Logger, got {type(logger)}"
    print_output(f"✓ getLogger() returned a logging.Logger instance")
    
    # Verify it has handlers
    assert len(logger.handlers) > 0, "Logger should have handlers attached"
    print_output(f"✓ Logger has {len(logger.handlers)} handler(s) attached")
    
    # Verify it has a LogPaneHandler
    has_log_pane_handler = any(isinstance(h, LogPaneHandler) for h in logger.handlers)
    assert has_log_pane_handler, "Logger should have LogPaneHandler"
    print_output(f"✓ Logger has LogPaneHandler attached")
    
    # Verify logger name
    assert logger.name == "TestLogger", f"Expected name 'TestLogger', got '{logger.name}'"
    print_output(f"✓ Logger has correct name: {logger.name}")
    
    print_output("✓ Test 1 PASSED\n")
    
    # Clean up
    log_manager.restore_stdio()


def test_logger_messages_formatted_correctly():
    """Verify logger messages are formatted with timestamp, name, level, and message."""
    print_output("=== Test 2: Logger messages formatted correctly ===")
    
    # Create a minimal config object
    class MinimalConfig:
        MAX_LOG_MESSAGES = 1000
    
    config = MinimalConfig()
    
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    # Configure handlers explicitly
    log_manager.configure_handlers(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_enabled=False
    )
    
    logger = log_manager.getLogger("FileOp")
    
    # Emit a test message
    logger.info("Test message for formatting")
    
    # Get the LogPaneHandler
    log_pane_handler = None
    for handler in logger.handlers:
        if isinstance(handler, LogPaneHandler):
            log_pane_handler = handler
            break
    
    assert log_pane_handler is not None, "Should have LogPaneHandler"
    
    # Get messages from handler
    messages = list(log_pane_handler.messages)
    assert len(messages) > 0, "Should have at least one message"
    
    # Check the last message
    last_message = messages[-1]
    print_output(f"Formatted message: {last_message}")
    
    # Verify format: "HH:MM:SS [LoggerName] LEVEL: message"
    assert "[FileOp]" in last_message, f"Message should contain logger name [FileOp]: {last_message}"
    assert "INFO:" in last_message, f"Message should contain level INFO: {last_message}"
    assert "Test message for formatting" in last_message, f"Message should contain text: {last_message}"
    
    # Verify timestamp format (HH:MM:SS)
    import re
    timestamp_pattern = r'\d{2}:\d{2}:\d{2}'
    assert re.match(timestamp_pattern, last_message[:8]), f"Message should start with timestamp: {last_message}"
    
    print_output(f"✓ Message has correct format")
    print_output(f"✓ Contains timestamp: {last_message[:8]}")
    print_output(f"✓ Contains logger name: [FileOp]")
    print_output(f"✓ Contains level: INFO:")
    print_output(f"✓ Contains message text")
    print_output("✓ Test 2 PASSED\n")
    
    # Clean up
    log_manager.restore_stdio()


def test_stdout_stderr_displayed_as_is():
    """Verify stdout/stderr is displayed as-is without additional formatting."""
    print_output("=== Test 3: Stdout/stderr displayed as-is ===")
    
    # Create a minimal config object
    class MinimalConfig:
        MAX_LOG_MESSAGES = 1000
    
    config = MinimalConfig()
    
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    # Configure handlers explicitly
    log_manager.configure_handlers(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_enabled=False
    )
    
    # Get the root logger (used by LogCapture)
    root_logger = logging.getLogger()
    
    # Find the LogPaneHandler
    log_pane_handler = None
    for handler in root_logger.handlers:
        if isinstance(handler, LogPaneHandler):
            log_pane_handler = handler
            break
    
    if log_pane_handler is None:
        # Add one if not present
        log_pane_handler = LogPaneHandler()
        root_logger.addHandler(log_pane_handler)
    
    # Clear existing messages
    log_pane_handler.messages.clear()
    
    # Create a LogRecord simulating stdout capture
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Raw stdout output without formatting",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = True
    
    # Emit the record
    log_pane_handler.emit(record)
    
    # Get the formatted message
    messages = list(log_pane_handler.messages)
    assert len(messages) > 0, "Should have at least one message"
    
    last_message = messages[-1]
    print_output(f"Stdout message: {last_message}")
    
    # Verify it contains the raw text
    assert "Raw stdout output without formatting" in last_message, \
        f"Message should contain raw text: {last_message}"
    
    # Verify it has timestamp and source prefix
    assert "[STDOUT]" in last_message, f"Message should have [STDOUT] prefix: {last_message}"
    
    # Verify it does NOT have "INFO:" (that's for logger messages only)
    assert "INFO:" not in last_message, \
        f"Stdout message should NOT have 'INFO:' level indicator: {last_message}"
    
    print_output(f"✓ Stdout message contains raw text")
    print_output(f"✓ Has [STDOUT] source prefix")
    print_output(f"✓ Does NOT have 'INFO:' level indicator")
    
    # Test stderr
    log_pane_handler.messages.clear()
    
    record = logging.LogRecord(
        name="STDERR",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="Raw stderr output",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = True
    
    log_pane_handler.emit(record)
    
    messages = list(log_pane_handler.messages)
    last_message = messages[-1]
    print_output(f"Stderr message: {last_message}")
    
    assert "Raw stderr output" in last_message, f"Message should contain raw text: {last_message}"
    assert "[STDERR]" in last_message, f"Message should have [STDERR] prefix: {last_message}"
    assert "WARNING:" not in last_message, \
        f"Stderr message should NOT have 'WARNING:' level indicator: {last_message}"
    
    print_output(f"✓ Stderr message contains raw text")
    print_output(f"✓ Has [STDERR] source prefix")
    print_output(f"✓ Does NOT have 'WARNING:' level indicator")
    print_output("✓ Test 3 PASSED\n")
    
    # Clean up
    log_manager.restore_stdio()


def test_multi_line_stdout_preservation():
    """Verify multi-line stdout/stderr is preserved correctly."""
    print_output("=== Test 4: Multi-line stdout preservation ===")
    
    # Create a minimal config object
    class MinimalConfig:
        MAX_LOG_MESSAGES = 1000
    
    config = MinimalConfig()
    
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    # Configure handlers explicitly
    log_manager.configure_handlers(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_enabled=False
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Find the LogPaneHandler
    log_pane_handler = None
    for handler in root_logger.handlers:
        if isinstance(handler, LogPaneHandler):
            log_pane_handler = handler
            break
    
    if log_pane_handler is None:
        log_pane_handler = LogPaneHandler()
        root_logger.addHandler(log_pane_handler)
    
    log_pane_handler.messages.clear()
    
    # Create a multi-line message
    multi_line_text = "Line 1\nLine 2\nLine 3"
    
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=multi_line_text,
        args=(),
        exc_info=None
    )
    record.is_stream_capture = True
    
    # Emit the record
    log_pane_handler.emit(record)
    
    # Get messages
    messages = list(log_pane_handler.messages)
    
    # Should have 3 separate lines
    assert len(messages) >= 3, f"Should have at least 3 lines, got {len(messages)}"
    
    # Check each line
    for i, expected_text in enumerate(["Line 1", "Line 2", "Line 3"]):
        # Find the message containing this line
        found = False
        for msg in messages:
            if expected_text in msg:
                print_output(f"✓ Found line {i+1}: {msg}")
                assert "[STDOUT]" in msg, f"Line should have [STDOUT] prefix: {msg}"
                found = True
                break
        assert found, f"Should find '{expected_text}' in messages"
    
    print_output("✓ Test 4 PASSED\n")
    
    # Clean up
    log_manager.restore_stdio()


def test_logger_caching():
    """Verify getLogger() returns the same instance for the same name."""
    print_output("=== Test 5: Logger instance caching ===")
    
    # Create a minimal config object
    class MinimalConfig:
        MAX_LOG_MESSAGES = 1000
    
    config = MinimalConfig()
    
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    # Configure handlers explicitly
    log_manager.configure_handlers(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_enabled=False
    )
    
    # Get logger twice with same name
    logger1 = log_manager.getLogger("TestLogger")
    logger2 = log_manager.getLogger("TestLogger")
    
    # Should be the same instance
    assert logger1 is logger2, "getLogger() should return the same instance for the same name"
    print_output(f"✓ getLogger('TestLogger') returns same instance")
    
    # Get logger with different name
    logger3 = log_manager.getLogger("DifferentLogger")
    
    # Should be different instance
    assert logger1 is not logger3, "getLogger() should return different instances for different names"
    print_output(f"✓ getLogger('DifferentLogger') returns different instance")
    
    print_output("✓ Test 5 PASSED\n")
    
    # Clean up
    log_manager.restore_stdio()


def main():
    """Run all checkpoint tests."""
    print_output("\n" + "="*60)
    print_output("CHECKPOINT 6: Core Functionality Verification")
    print_output("="*60)
    
    try:
        test_getlogger_returns_configured_logger()
        test_logger_messages_formatted_correctly()
        test_stdout_stderr_displayed_as_is()
        test_multi_line_stdout_preservation()
        test_logger_caching()
        
        print_output("="*60)
        print_output("✓ ALL CHECKPOINT 6 TESTS PASSED")
        print_output("="*60)
        print_output("\nCore functionality verified:")
        print_output("  ✓ getLogger() returns configured loggers")
        print_output("  ✓ Logger messages are formatted correctly")
        print_output("  ✓ Stdout/stderr is displayed as-is")
        print_output("  ✓ Multi-line output is preserved")
        print_output("  ✓ Logger instances are cached correctly")
        print_output("")
        
        return 0
        
    except AssertionError as e:
        print_output(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print_output(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
