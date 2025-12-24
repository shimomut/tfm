#!/usr/bin/env python3
"""
Demo: Performance Optimizations in Logging System

This demo showcases the performance optimizations implemented in the logging system:
1. Level checking before formatting (Requirement 11.1)
2. Visibility checking for log pane (Requirement 11.3)
3. Message retention limit (Requirement 11.4)
"""

import sys
import time
import logging

sys.path.insert(0, 'src')

from tfm_log_manager import LogManager


def demo_level_checking():
    """
    Demonstrate level checking before formatting.
    
    When a logger's level is set to WARNING, DEBUG and INFO messages are
    skipped entirely - no LogRecord creation, no formatting, no processing.
    This saves CPU cycles when verbose logging is disabled.
    """
    sys.__stdout__.write("\n" + "=" * 60 + "\n")
    sys.__stdout__.write("Demo 1: Level Checking Before Formatting\n")
    sys.__stdout__.write("=" * 60 + "\n\n")
    
    class SimpleConfig:
        MAX_LOG_MESSAGES = 100
    
    config = SimpleConfig()
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    # Get a logger and set its level to WARNING
    logger = log_manager.getLogger("PerformanceDemo")
    logger.setLevel(logging.WARNING)
    
    sys.__stdout__.write("Logger level set to WARNING\n")
    sys.__stdout__.write("Attempting to log DEBUG and INFO messages...\n\n")
    
    # These messages will be skipped (no processing at all)
    start_time = time.time()
    for i in range(1000):
        logger.debug(f"Debug message {i} - this is skipped")
        logger.info(f"Info message {i} - this is also skipped")
    skip_time = time.time() - start_time
    
    sys.__stdout__.write(f"✓ 2000 DEBUG/INFO messages skipped in {skip_time:.4f} seconds\n")
    sys.__stdout__.write(f"  (No LogRecord creation, no formatting, no processing)\n\n")
    
    # These messages will be processed
    sys.__stdout__.write("Now logging WARNING messages...\n\n")
    start_time = time.time()
    for i in range(100):
        logger.warning(f"Warning message {i} - this is processed")
    process_time = time.time() - start_time
    
    sys.__stdout__.write(f"✓ 100 WARNING messages processed in {process_time:.4f} seconds\n")
    sys.__stdout__.write(f"  (Full LogRecord creation, formatting, and storage)\n\n")
    
    # Show the messages
    messages = log_manager._log_pane_handler.get_messages()
    sys.__stdout__.write(f"Total messages in log pane: {len(messages)}\n")
    sys.__stdout__.write(f"First message: {messages[0][0]}\n")
    sys.__stdout__.write(f"Last message: {messages[-1][0]}\n")
    
    log_manager.restore_stdio()


def demo_visibility_checking():
    """
    Demonstrate visibility checking for log pane.
    
    When the log pane is not visible, formatting operations are skipped.
    Messages are still stored (for when the pane becomes visible), but
    expensive formatting is deferred until needed.
    """
    sys.__stdout__.write("\n" + "=" * 60 + "\n")
    sys.__stdout__.write("Demo 2: Visibility Checking for Log Pane\n")
    sys.__stdout__.write("=" * 60 + "\n\n")
    
    class SimpleConfig:
        MAX_LOG_MESSAGES = 100
    
    config = SimpleConfig()
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    logger = log_manager.getLogger("VisibilityDemo")
    
    # Set log pane as not visible
    log_manager.set_log_pane_visible(False)
    sys.__stdout__.write("Log pane set to NOT VISIBLE\n")
    sys.__stdout__.write("Logging messages while not visible...\n\n")
    
    # Log messages while not visible (formatting is skipped)
    start_time = time.time()
    for i in range(1000):
        logger.info(f"Message {i} while not visible")
    not_visible_time = time.time() - start_time
    
    sys.__stdout__.write(f"✓ 1000 messages logged in {not_visible_time:.4f} seconds\n")
    sys.__stdout__.write(f"  (Messages stored, formatting skipped)\n\n")
    
    # Check unformatted count
    messages = log_manager._log_pane_handler.messages
    unformatted_count = sum(1 for msg, _ in messages if msg is None)
    sys.__stdout__.write(f"Unformatted messages: {unformatted_count}\n\n")
    
    # Now set log pane as visible
    log_manager.set_log_pane_visible(True)
    sys.__stdout__.write("Log pane set to VISIBLE\n")
    sys.__stdout__.write("Logging messages while visible...\n\n")
    
    # Log messages while visible (formatting happens immediately)
    start_time = time.time()
    for i in range(1000):
        logger.info(f"Message {i} while visible")
    visible_time = time.time() - start_time
    
    sys.__stdout__.write(f"✓ 1000 messages logged in {visible_time:.4f} seconds\n")
    sys.__stdout__.write(f"  (Messages stored AND formatted immediately)\n\n")
    
    # Get formatted messages (this will format any unformatted messages)
    sys.__stdout__.write("Retrieving messages for display...\n")
    start_time = time.time()
    formatted_messages = log_manager._log_pane_handler.get_messages()
    format_time = time.time() - start_time
    
    sys.__stdout__.write(f"✓ {len(formatted_messages)} messages formatted in {format_time:.4f} seconds\n")
    sys.__stdout__.write(f"  (Deferred formatting of previously unformatted messages)\n\n")
    
    # Performance comparison
    sys.__stdout__.write("Performance comparison:\n")
    sys.__stdout__.write(f"  Not visible: {not_visible_time:.4f}s (formatting skipped)\n")
    sys.__stdout__.write(f"  Visible:     {visible_time:.4f}s (formatting immediate)\n")
    speedup = visible_time / not_visible_time if not_visible_time > 0 else 0
    sys.__stdout__.write(f"  Speedup:     {speedup:.2f}x faster when not visible\n")
    
    log_manager.restore_stdio()


def demo_message_retention_limit():
    """
    Demonstrate message retention limit.
    
    The log pane uses a deque with maxlen to automatically discard oldest
    messages when the limit is reached. This prevents unbounded memory growth
    during long-running sessions.
    """
    sys.__stdout__.write("\n" + "=" * 60 + "\n")
    sys.__stdout__.write("Demo 3: Message Retention Limit\n")
    sys.__stdout__.write("=" * 60 + "\n\n")
    
    class SimpleConfig:
        MAX_LOG_MESSAGES = 50  # Small limit for demo
    
    config = SimpleConfig()
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    
    logger = log_manager.getLogger("RetentionDemo")
    
    sys.__stdout__.write(f"Message retention limit: {config.MAX_LOG_MESSAGES}\n")
    sys.__stdout__.write("Logging 100 messages...\n\n")
    
    # Log more messages than the limit
    for i in range(100):
        logger.info(f"Message {i}")
    
    # Check message count
    messages = log_manager._log_pane_handler.get_messages()
    sys.__stdout__.write(f"✓ Total messages in log pane: {len(messages)}\n")
    sys.__stdout__.write(f"  (Capped at {config.MAX_LOG_MESSAGES}, oldest discarded)\n\n")
    
    # Show which messages are retained
    first_message = messages[0][0]
    last_message = messages[-1][0]
    
    sys.__stdout__.write("Messages retained:\n")
    sys.__stdout__.write(f"  First: {first_message}\n")
    sys.__stdout__.write(f"  Last:  {last_message}\n\n")
    
    # Log more messages and show automatic discarding
    sys.__stdout__.write("Logging 10 more messages...\n\n")
    for i in range(100, 110):
        logger.info(f"Message {i}")
    
    messages = log_manager._log_pane_handler.get_messages()
    first_message = messages[0][0]
    last_message = messages[-1][0]
    
    sys.__stdout__.write(f"✓ Total messages still: {len(messages)}\n")
    sys.__stdout__.write("Messages retained:\n")
    sys.__stdout__.write(f"  First: {first_message}\n")
    sys.__stdout__.write(f"  Last:  {last_message}\n")
    sys.__stdout__.write(f"  (Oldest 10 messages automatically discarded)\n")
    
    log_manager.restore_stdio()


if __name__ == "__main__":
    sys.__stdout__.write("\n")
    sys.__stdout__.write("=" * 60 + "\n")
    sys.__stdout__.write("Performance Optimizations Demo\n")
    sys.__stdout__.write("=" * 60 + "\n")
    
    demo_level_checking()
    demo_visibility_checking()
    demo_message_retention_limit()
    
    sys.__stdout__.write("\n" + "=" * 60 + "\n")
    sys.__stdout__.write("Demo completed!\n")
    sys.__stdout__.write("=" * 60 + "\n\n")
