"""
Test color coding implementation for logging system.

Tests that:
1. LogPaneHandler.get_color_for_record() returns correct colors for different log levels
2. LogPaneHandler.get_color_for_record() returns correct colors for stdout/stderr
3. draw_log_pane() uses colors from records

Run with: PYTHONPATH=.:src:ttk pytest test/test_color_coding.py -v
"""

import unittest
import logging
from unittest.mock import Mock, MagicMock, patch
from collections import deque

from tfm_logging_handlers import LogPaneHandler
from tfm_log_manager import LogManager
from tfm_colors import COLOR_ERROR, COLOR_LOG_SYSTEM, COLOR_LOG_STDOUT
from ttk import TextAttribute


class TestColorCoding(unittest.TestCase):
    """Test color coding for log messages"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = LogPaneHandler(max_messages=100)
    
    def test_get_color_for_logger_debug(self):
        """Test color for DEBUG level logger messages"""
        record = logging.LogRecord(
            name="TestLogger",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="Debug message",
            args=(),
            exc_info=None
        )
        record.is_stream_capture = False
        
        color_pair, attributes = self.handler.get_color_for_record(record)
        
        # DEBUG should use STDOUT color (gray)
        self.assertEqual(color_pair, COLOR_LOG_STDOUT)
        self.assertEqual(attributes, TextAttribute.NORMAL)
    
    def test_get_color_for_logger_info(self):
        """Test color for INFO level logger messages"""
        record = logging.LogRecord(
            name="TestLogger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Info message",
            args=(),
            exc_info=None
        )
        record.is_stream_capture = False
        
        color_pair, attributes = self.handler.get_color_for_record(record)
        
        # INFO should use STDOUT color (gray)
        self.assertEqual(color_pair, COLOR_LOG_STDOUT)
        self.assertEqual(attributes, TextAttribute.NORMAL)
    
    def test_get_color_for_logger_warning(self):
        """Test color for WARNING level logger messages"""
        record = logging.LogRecord(
            name="TestLogger",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        record.levelno = logging.WARNING  # Ensure levelno is set
        record.is_stream_capture = False
        
        color_pair, attributes = self.handler.get_color_for_record(record)
        
        # WARNING should use SYSTEM color (light blue)
        self.assertEqual(color_pair, COLOR_LOG_SYSTEM)
        self.assertEqual(attributes, TextAttribute.NORMAL)
    
    def test_get_color_for_logger_error(self):
        """Test color for ERROR level logger messages"""
        record = logging.LogRecord(
            name="TestLogger",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None
        )
        record.levelno = logging.ERROR  # Ensure levelno is set
        record.is_stream_capture = False
        
        color_pair, attributes = self.handler.get_color_for_record(record)
        
        # ERROR should use ERROR color (red)
        self.assertEqual(color_pair, COLOR_ERROR)
        self.assertEqual(attributes, TextAttribute.NORMAL)
    
    def test_get_color_for_logger_critical(self):
        """Test color for CRITICAL level logger messages"""
        record = logging.LogRecord(
            name="TestLogger",
            level=logging.CRITICAL,
            pathname="",
            lineno=0,
            msg="Critical message",
            args=(),
            exc_info=None
        )
        record.levelno = logging.CRITICAL  # Ensure levelno is set
        record.is_stream_capture = False
        
        color_pair, attributes = self.handler.get_color_for_record(record)
        
        # CRITICAL should use ERROR color (red)
        self.assertEqual(color_pair, COLOR_ERROR)
        self.assertEqual(attributes, TextAttribute.NORMAL)
    
    def test_get_color_for_stdout(self):
        """Test color for stdout stream capture"""
        record = logging.LogRecord(
            name="STDOUT",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Stdout message",
            args=(),
            exc_info=None
        )
        record.is_stream_capture = True
        
        color_pair, attributes = self.handler.get_color_for_record(record)
        
        # STDOUT should use STDOUT color (gray)
        self.assertEqual(color_pair, COLOR_LOG_STDOUT)
        self.assertEqual(attributes, TextAttribute.NORMAL)
    
    def test_get_color_for_stderr(self):
        """Test color for stderr stream capture"""
        record = logging.LogRecord(
            name="STDERR",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Stderr message",
            args=(),
            exc_info=None
        )
        record.is_stream_capture = True
        
        color_pair, attributes = self.handler.get_color_for_record(record)
        
        # STDERR should use ERROR color (red)
        self.assertEqual(color_pair, COLOR_ERROR)
        self.assertEqual(attributes, TextAttribute.NORMAL)
    
    def test_messages_stored_with_records(self):
        """Test that messages are stored with their LogRecords"""
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
        
        self.handler.emit(record)
        
        messages = self.handler.get_messages()
        self.assertEqual(len(messages), 1)
        
        formatted_message, stored_record = messages[0]
        self.assertIsInstance(formatted_message, str)
        self.assertIs(stored_record, record)
        self.assertIn("Test message", formatted_message)
    
    def test_draw_log_pane_uses_handler_colors(self):
        """Test that draw_log_pane uses colors from LogPaneHandler"""
        # Create a mock config
        mock_config = Mock()
        mock_config.MAX_LOG_MESSAGES = 100
        
        # Create LogManager
        log_manager = LogManager(mock_config, remote_port=None)
        
        # Create a logger and emit a message
        logger = log_manager.getLogger("TestLogger")
        logger.error("Test error message")
        
        # Create a mock renderer
        mock_renderer = Mock()
        mock_renderer.draw_text = Mock()
        
        # Draw the log pane
        log_manager.draw_log_pane(mock_renderer, y_start=0, height=10, width=80)
        
        # Verify that draw_text was called
        self.assertTrue(mock_renderer.draw_text.called)
        
        # Get the color_pair argument from the draw_text call
        # The call should be: draw_text(y, x, text, color_pair=..., attributes=...)
        call_args = mock_renderer.draw_text.call_args
        if call_args:
            # Check if color_pair was passed as keyword argument
            if 'color_pair' in call_args.kwargs:
                color_pair = call_args.kwargs['color_pair']
                # ERROR level should use ERROR color (red)
                self.assertEqual(color_pair, COLOR_ERROR)
