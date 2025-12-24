#!/usr/bin/env python3
"""
Demo script to test color coding in the logging system.

This script demonstrates:
1. Different log levels have different colors
2. Stdout and stderr have distinct colors
3. Logger messages are formatted with level information
4. Stream messages are displayed as-is
"""

import sys
import logging

# Add src to path
sys.path.insert(0, 'src')

from tfm_logging_handlers import LogPaneHandler
from tfm_colors import COLOR_ERROR, COLOR_LOG_SYSTEM, COLOR_LOG_STDOUT
from ttk import TextAttribute


def main():
    """Run the color coding demo"""
    print("Color Coding Demo")
    print("=" * 50)
    print()
    
    # Create a LogPaneHandler
    handler = LogPaneHandler(max_messages=100)
    
    # Test different log levels
    print("Testing logger message colors:")
    print("-" * 50)
    
    # DEBUG level
    record = logging.LogRecord(
        name="Demo",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="This is a DEBUG message",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = False
    color_pair, attributes = handler.get_color_for_record(record)
    print(f"DEBUG:    color_pair={color_pair}, expected={COLOR_LOG_STDOUT} (gray) - {'✓' if color_pair == COLOR_LOG_STDOUT else '✗'}")
    
    # INFO level
    record.level = logging.INFO
    record.msg = "This is an INFO message"
    color_pair, attributes = handler.get_color_for_record(record)
    print(f"INFO:     color_pair={color_pair}, expected={COLOR_LOG_STDOUT} (gray) - {'✓' if color_pair == COLOR_LOG_STDOUT else '✗'}")
    
    # WARNING level
    record.level = logging.WARNING
    record.levelno = logging.WARNING  # Need to set levelno as well
    record.msg = "This is a WARNING message"
    color_pair, attributes = handler.get_color_for_record(record)
    print(f"WARNING:  color_pair={color_pair}, expected={COLOR_LOG_SYSTEM} (light blue) - {'✓' if color_pair == COLOR_LOG_SYSTEM else '✗'}")
    
    # ERROR level
    record.level = logging.ERROR
    record.levelno = logging.ERROR  # Need to set levelno as well
    record.msg = "This is an ERROR message"
    color_pair, attributes = handler.get_color_for_record(record)
    print(f"ERROR:    color_pair={color_pair}, expected={COLOR_ERROR} (red) - {'✓' if color_pair == COLOR_ERROR else '✗'}")
    
    # CRITICAL level
    record.level = logging.CRITICAL
    record.levelno = logging.CRITICAL  # Need to set levelno as well
    record.msg = "This is a CRITICAL message"
    color_pair, attributes = handler.get_color_for_record(record)
    print(f"CRITICAL: color_pair={color_pair}, expected={COLOR_ERROR} (red) - {'✓' if color_pair == COLOR_ERROR else '✗'}")
    
    print()
    print("Testing stream capture colors:")
    print("-" * 50)
    
    # STDOUT
    record = logging.LogRecord(
        name="STDOUT",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="This is stdout output",
        args=(),
        exc_info=None
    )
    record.is_stream_capture = True
    color_pair, attributes = handler.get_color_for_record(record)
    print(f"STDOUT:   color_pair={color_pair}, expected={COLOR_LOG_STDOUT} (gray) - {'✓' if color_pair == COLOR_LOG_STDOUT else '✗'}")
    
    # STDERR
    record.name = "STDERR"
    record.msg = "This is stderr output"
    color_pair, attributes = handler.get_color_for_record(record)
    print(f"STDERR:   color_pair={color_pair}, expected={COLOR_ERROR} (red) - {'✓' if color_pair == COLOR_ERROR else '✗'}")
    
    print()
    print("All color coding tests completed!")


if __name__ == '__main__':
    main()
