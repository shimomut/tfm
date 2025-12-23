# Implementation Plan: Logging System Refactor

## Overview

This implementation plan refactors TFM's logging system to use Python's standard `logging` module while maintaining all existing functionality. The approach is incremental: we'll create new components alongside the existing system, migrate functionality piece by piece, and maintain backward compatibility throughout. The implementation focuses on creating custom handlers that route messages to TFM's log pane, original streams, and remote monitoring clients.

## Tasks

- [ ] 1. Create custom logging handlers
  - Create `LogPaneHandler` class that stores messages in a deque
  - Create `StreamOutputHandler` class that writes to original streams
  - Create `RemoteMonitoringHandler` class that broadcasts to TCP clients
  - Implement `is_stream_capture` flag handling in all handlers
  - _Requirements: 1.1, 1.2, 2.1, 3.5, 4.1_

- [ ]* 1.1 Write property test for handler configuration
  - **Property 4: Logger handler configuration**
  - **Validates: Requirements 1.2**

- [ ] 2. Implement LogManager.getLogger() method
  - [ ] 2.1 Add logger caching dictionary to LogManager.__init__
    - Store created loggers by name in self._loggers
    - _Requirements: 1.3_

  - [ ] 2.2 Implement getLogger(name) method
    - Return cached logger if exists
    - Create new logger with Python's logging.getLogger()
    - Attach configured handlers to new logger
    - Cache and return logger
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 2.3 Write property test for logger instance caching
    - **Property 2: Logger instance caching**
    - **Validates: Requirements 1.3**

  - [ ]* 2.4 Write property test for multiple logger support
    - **Property 3: Multiple logger support**
    - **Validates: Requirements 1.4**

- [ ] 3. Enhance LogCapture for logging integration
  - [ ] 3.1 Modify LogCapture.write() to create LogRecords
    - Create LogRecord with appropriate level (INFO for stdout, WARNING for stderr)
    - Set `is_stream_capture=True` flag on record
    - Preserve raw text in msg field (don't strip or modify)
    - Route through logger.handle() instead of direct append
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 3.2 Write property test for stdout/stderr routing
    - **Property 5: Message routing to configured destinations**
    - **Validates: Requirements 1.6, 2.6, 5.3, 5.4**

  - [ ]* 3.3 Write property test for source distinction
    - **Property 10: Source distinction preservation**
    - **Validates: Requirements 5.5**

- [ ] 4. Implement message formatting logic
  - [ ] 4.1 Implement LogPaneHandler.format_logger_message()
    - Format as "timestamp [logger_name] LEVEL: message"
    - Use LOG_TIME_FORMAT for timestamp
    - _Requirements: 8.1_

  - [ ] 4.2 Implement LogPaneHandler.format_stream_message()
    - Format as "timestamp [source] raw_message"
    - Preserve multi-line output (split on newlines)
    - Each line gets its own timestamp and source prefix
    - _Requirements: 8.2, 8.3, 8.4_

  - [ ] 4.3 Implement LogPaneHandler.emit() with format dispatch
    - Check `is_stream_capture` flag
    - Call format_logger_message() for logger messages
    - Call format_stream_message() for stdout/stderr
    - Add formatted messages to deque
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 4.4 Write property test for logger message formatting
    - **Property 15: Logger message formatting**
    - **Validates: Requirements 8.1**

  - [ ]* 4.5 Write property test for stdout/stderr raw display
    - **Property 16: Stdout/stderr raw display**
    - **Validates: Requirements 8.2, 8.3**

  - [ ]* 4.6 Write property test for multi-line preservation
    - **Property 17: Multi-line preservation**
    - **Validates: Requirements 8.4**

- [ ] 5. Implement configuration management
  - [ ] 5.1 Create LoggingConfig dataclass
    - Define all configuration fields with defaults
    - Include log_pane_enabled, stream_output_enabled, remote_monitoring_enabled
    - Include max_log_messages, default_log_level, logger_levels
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 5.2 Implement LogManager.configure_handlers()
    - Add/remove handlers based on configuration
    - Support dynamic reconfiguration without restart
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [ ]* 5.3 Write property test for dynamic configuration
    - **Property 11: Dynamic configuration application**
    - **Validates: Requirements 6.5**

- [ ] 6. Checkpoint - Ensure core functionality works
  - Verify getLogger() returns configured loggers
  - Verify logger messages are formatted correctly
  - Verify stdout/stderr is displayed as-is
  - Ask the user if questions arise

- [ ] 7. Implement log level filtering
  - [ ] 7.1 Add level configuration to LogManager
    - Store global default level
    - Store per-logger level overrides
    - _Requirements: 7.1, 7.3, 7.4, 7.5_

  - [ ] 7.2 Apply levels when creating loggers
    - Set logger.setLevel() based on configuration
    - Apply per-logger overrides if specified
    - _Requirements: 7.1, 7.4_

  - [ ]* 7.3 Write property test for log level filtering
    - **Property 12: Log level filtering**
    - **Validates: Requirements 7.1**

  - [ ]* 7.4 Write property test for per-logger level override
    - **Property 13: Per-logger level override**
    - **Validates: Requirements 7.4**

- [ ] 8. Implement color coding
  - [ ] 8.1 Implement LogPaneHandler.get_color_for_record()
    - Check `is_stream_capture` flag
    - For logger messages: use record.levelno to determine color
    - For stdout/stderr: use record.name ("STDOUT"/"STDERR") to determine color
    - Return (color_pair, attributes) tuple
    - _Requirements: 2.2, 2.3_

  - [ ] 8.2 Update draw_log_pane() to use colors from records
    - Get color for each message based on its record
    - Apply color when drawing text
    - _Requirements: 2.2_

  - [ ]* 8.3 Write property test for color coding by level
    - **Property 7: Color coding by log level**
    - **Validates: Requirements 2.2**

- [ ] 9. Implement remote monitoring handler
  - [ ] 9.1 Implement RemoteMonitoringHandler.emit()
    - Convert LogRecord to JSON message
    - Broadcast to all connected clients
    - Handle client failures gracefully
    - _Requirements: 4.2, 4.4, 4.5_

  - [ ] 9.2 Implement RemoteMonitoringHandler server lifecycle
    - Implement start_server() to begin accepting connections
    - Implement stop_server() to close all connections
    - Implement _accept_connections() background thread
    - _Requirements: 4.1_

  - [ ]* 9.3 Write property test for remote broadcast
    - **Property 9: Remote broadcast to all clients**
    - **Validates: Requirements 4.2, 4.4, 4.5**

- [ ] 10. Implement backward compatibility
  - [ ] 10.1 Update LogManager.add_message() to use logging
    - Create a LogRecord for the message
    - Set appropriate source and level
    - Route through handler pipeline
    - _Requirements: 10.1, 10.2_

  - [ ]* 10.2 Write property test for backward compatibility routing
    - **Property 21: Backward compatibility routing**
    - **Validates: Requirements 10.2**

- [ ] 11. Checkpoint - Ensure all routing works
  - Verify messages reach all configured destinations
  - Verify remote monitoring works
  - Verify backward compatibility with add_message()
  - Ask the user if questions arise

- [ ] 12. Implement error handling
  - [ ] 12.1 Add error isolation to handler emission
    - Wrap each handler.emit() in try-except
    - Continue with remaining handlers on failure
    - Log errors to fallback (sys.__stderr__)
    - _Requirements: 12.1, 12.5_

  - [ ] 12.2 Add error handling to remote client operations
    - Detect client failures during broadcast
    - Remove failed clients from active list
    - Close failed client sockets
    - _Requirements: 12.2_

  - [ ] 12.3 Add error handling to stream writes
    - Wrap stream writes in try-except
    - Suppress OSError and IOError
    - Continue processing with other handlers
    - _Requirements: 12.3_

  - [ ]* 12.4 Write property test for handler failure isolation
    - **Property 25: Handler failure isolation**
    - **Validates: Requirements 12.1**

  - [ ]* 12.5 Write property test for client failure recovery
    - **Property 26: Client failure recovery**
    - **Validates: Requirements 12.2**

  - [ ]* 12.6 Write property test for stream write failure suppression
    - **Property 27: Stream write failure suppression**
    - **Validates: Requirements 12.3**

- [ ] 13. Implement thread safety
  - [ ] 13.1 Add locking to LogPaneHandler
    - Use threading.Lock for message deque access
    - Protect emit() and get_messages() operations
    - _Requirements: 9.1_

  - [ ] 13.2 Add locking to RemoteMonitoringHandler
    - Use threading.Lock for client list access
    - Protect client addition/removal operations
    - _Requirements: 9.3_

  - [ ]* 13.3 Write property test for thread-safe concurrent logging
    - **Property 19: Thread-safe concurrent logging**
    - **Validates: Requirements 9.1**

  - [ ]* 13.4 Write property test for thread-safe client management
    - **Property 20: Thread-safe client management**
    - **Validates: Requirements 9.3**

- [ ] 14. Implement performance optimizations
  - [ ] 14.1 Add level checking before formatting
    - Check logger.isEnabledFor(level) before creating LogRecord
    - Skip expensive formatting for disabled levels
    - _Requirements: 11.1_

  - [ ] 14.2 Add visibility checking for log pane
    - Track whether log pane is visible
    - Skip rendering operations when not visible
    - _Requirements: 11.3_

  - [ ] 14.3 Implement message retention limit
    - Use deque with maxlen for automatic old message removal
    - Verify oldest messages are discarded when limit reached
    - _Requirements: 11.4_

  - [ ]* 14.4 Write property test for message retention limit
    - **Property 24: Message retention limit**
    - **Validates: Requirements 11.4**

- [ ] 15. Update existing code to use new logging
  - [ ] 15.1 Update tfm_main.py to use getLogger()
    - Replace add_message() calls with logger.info(), logger.error(), etc.
    - Create "Main" logger
    - _Requirements: 1.1, 1.4_

  - [ ] 15.2 Update tfm_file_operations.py to use getLogger()
    - Create "FileOp" logger
    - Replace add_message() calls with logger methods
    - _Requirements: 1.4_

  - [ ] 15.3 Update tfm_directory_diff_viewer.py to use getLogger()
    - Create "DirDiff" logger
    - Replace add_message() calls with logger methods
    - _Requirements: 1.4_

  - [ ] 15.4 Update tfm_archive.py to use getLogger()
    - Create "Archive" logger
    - Replace add_message() calls with logger methods
    - _Requirements: 1.4_

- [ ] 16. Final checkpoint - Integration testing
  - Run TFM and verify all logging works correctly
  - Test logger messages appear with correct formatting
  - Test stdout/stderr appears as-is
  - Test remote monitoring works
  - Test configuration changes work dynamically
  - Test thread safety under concurrent load
  - Ask the user if questions arise

- [ ] 17. Update documentation
  - Document getLogger() usage in developer docs
  - Document logging configuration options
  - Document migration guide from add_message() to logger
  - Add examples of using different log levels
  - _Requirements: All_

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using hypothesis library
- Unit tests validate specific examples and edge cases
- The implementation maintains backward compatibility throughout the migration
