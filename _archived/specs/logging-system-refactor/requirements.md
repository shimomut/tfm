# Requirements Document

## Introduction

This specification defines the requirements for refactoring TFM's logging system to use Python's standard `logging` module while maintaining all existing functionality. The current system uses a custom `LogManager.add_message()` method alongside direct stdout/stderr output. The new system will standardize on Python's logging framework while preserving TFM's unique features: log pane display, remote monitoring, and configurable output routing.

## Glossary

- **Logger**: Python's standard `logging.Logger` instance obtained via `getLogger(name)`
- **LogCapture**: Custom stream wrapper that intercepts stdout/stderr writes
- **Log_Pane**: TFM's visual display area showing log messages with color coding
- **Remote_Monitoring**: TCP-based system for viewing logs from external clients
- **Desktop_Mode**: TFM running in a native window (not terminal-based)
- **Terminal_Mode**: TFM running in a terminal using curses
- **Log_Handler**: Python logging component that processes and routes log records
- **Log_Level**: Severity classification (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Original_Streams**: The system's default stdout/stderr (sys.__stdout__, sys.__stderr__)

## Requirements

### Requirement 1: Standard Logger Integration

**User Story:** As a TFM developer, I want to use Python's standard logging module, so that I can leverage familiar logging patterns and tools.

#### Acceptance Criteria

1. THE System SHALL provide a `getLogger(name)` function that returns a `logging.Logger` instance
2. WHEN a developer calls `getLogger(name)`, THE System SHALL configure the logger with appropriate handlers for TFM's routing requirements
3. WHEN a developer calls `getLogger(name)` with a name that already exists, THE System SHALL return the existing Logger instance
4. THE System SHALL support creating multiple Logger instances for different purposes (Main, FileOp, DirDiff, Archive, etc.)
5. THE System SHALL support all standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
6. WHEN a logger emits a message, THE System SHALL route it according to the configured output destinations
7. THE System SHALL maintain backward compatibility during migration by supporting both old and new logging methods

### Requirement 2: Log Pane Display

**User Story:** As a TFM user, I want all logs to appear in the log pane with appropriate color coding, so that I can monitor system activity and distinguish message severity.

#### Acceptance Criteria

1. WHEN a logger emits a message, THE System SHALL display it in the Log_Pane by default
2. WHEN displaying log messages, THE System SHALL apply color coding based on Log_Level
3. WHEN displaying stdout messages, THE System SHALL use a distinct color from stderr messages
4. WHEN displaying stderr messages, THE System SHALL use a distinct color from stdout messages
5. THE System SHALL support disabling Log_Pane output for debugging purposes
6. WHEN Log_Pane output is disabled, THE System SHALL continue routing logs to other configured destinations

### Requirement 3: Original Stream Output

**User Story:** As a TFM developer, I want logs to optionally write to the original stdout/stderr, so that I can debug issues without terminal rendering interference.

#### Acceptance Criteria

1. WHEN running in Desktop_Mode, THE System SHALL write logs to Original_Streams by default
2. WHEN running in Terminal_Mode, THE System SHALL NOT write logs to Original_Streams by default
3. THE System SHALL provide configuration to enable Original_Streams output in Terminal_Mode
4. THE System SHALL provide configuration to disable Original_Streams output in Desktop_Mode
5. WHEN writing to Original_Streams, THE System SHALL use sys.__stdout__ and sys.__stderr__

### Requirement 4: Remote Monitoring Support

**User Story:** As a TFM developer, I want to send logs to a remote monitoring system, so that I can observe application behavior from external tools.

#### Acceptance Criteria

1. THE System SHALL support remote log monitoring via TCP connections
2. WHEN remote monitoring is enabled, THE System SHALL broadcast log messages to all connected clients
3. THE System SHALL disable remote monitoring by default
4. WHEN a logger emits a message, THE System SHALL send it to remote clients if monitoring is enabled
5. WHEN stdout or stderr produces output, THE System SHALL send it to remote clients if monitoring is enabled

### Requirement 5: Stdout/Stderr Capture

**User Story:** As a TFM developer, I want stdout/stderr to be captured and routed through the logging system, so that all output appears in the log pane regardless of source.

#### Acceptance Criteria

1. THE System SHALL intercept stdout writes using LogCapture
2. THE System SHALL intercept stderr writes using LogCapture
3. WHEN stdout is written to, THE System SHALL route the output according to configured destinations
4. WHEN stderr is written to, THE System SHALL route the output according to configured destinations
5. THE System SHALL preserve the distinction between stdout and stderr sources

### Requirement 6: Configuration Management

**User Story:** As a TFM user, I want to configure logging behavior, so that I can control where logs are displayed and stored.

#### Acceptance Criteria

1. THE System SHALL provide configuration for enabling/disabling Log_Pane output
2. THE System SHALL provide configuration for enabling/disabling Original_Streams output
3. THE System SHALL provide configuration for enabling/disabling Remote_Monitoring
4. THE System SHALL provide configuration for setting the remote monitoring port
5. WHEN configuration changes, THE System SHALL apply the new settings without requiring restart

### Requirement 7: Log Level Filtering

**User Story:** As a TFM developer, I want to filter logs by severity level, so that I can control the verbosity of logging output.

#### Acceptance Criteria

1. THE System SHALL support setting a minimum Log_Level for each logger
2. WHEN a logger's level is set, THE System SHALL only emit messages at or above that level
3. THE System SHALL provide a global log level configuration
4. THE System SHALL allow per-logger level overrides
5. THE System SHALL default to INFO level for production use

### Requirement 8: Message Formatting

**User Story:** As a TFM user, I want log messages to include timestamps and source information, so that I can understand when and where events occurred.

#### Acceptance Criteria

1. WHEN displaying a logger message, THE System SHALL format it with timestamp, logger name, log level, and message text
2. WHEN displaying stdout output, THE System SHALL display it as-is without additional formatting
3. WHEN displaying stderr output, THE System SHALL display it as-is without additional formatting
4. WHEN stdout or stderr contains multiple lines, THE System SHALL preserve all lines without modification
5. THE System SHALL format logger timestamps consistently with the existing LOG_TIME_FORMAT
6. THE System SHALL truncate long messages to fit the display width

### Requirement 9: Thread Safety

**User Story:** As a TFM developer, I want the logging system to be thread-safe, so that concurrent operations don't corrupt log output.

#### Acceptance Criteria

1. WHEN multiple threads emit log messages simultaneously, THE System SHALL serialize the output correctly
2. THE System SHALL use appropriate locking mechanisms for shared data structures
3. WHEN remote clients connect or disconnect, THE System SHALL handle concurrent access safely
4. THE System SHALL prevent race conditions in the log message queue
5. THE System SHALL ensure atomic operations for critical sections

### Requirement 10: Backward Compatibility

**User Story:** As a TFM developer, I want existing code to continue working during migration, so that I can refactor incrementally.

#### Acceptance Criteria

1. THE System SHALL maintain the existing `LogManager.add_message()` method during migration
2. WHEN `add_message()` is called, THE System SHALL route the message through the new logging infrastructure
3. THE System SHALL maintain the existing LogCapture behavior for stdout/stderr
4. THE System SHALL preserve all existing log pane functionality
5. THE System SHALL maintain compatibility with remote monitoring clients

### Requirement 11: Performance

**User Story:** As a TFM user, I want logging to have minimal performance impact, so that the application remains responsive.

#### Acceptance Criteria

1. WHEN logging is disabled for a level, THE System SHALL skip message formatting
2. THE System SHALL use efficient data structures for log message storage
3. WHEN the log pane is not visible, THE System SHALL minimize rendering overhead
4. THE System SHALL limit the maximum number of stored log messages
5. WHEN remote monitoring is disabled, THE System SHALL not incur networking overhead

### Requirement 12: Error Handling

**User Story:** As a TFM developer, I want the logging system to handle errors gracefully, so that logging failures don't crash the application.

#### Acceptance Criteria

1. WHEN a log handler fails, THE System SHALL continue operating with remaining handlers
2. WHEN remote client connections fail, THE System SHALL remove the client and continue
3. WHEN writing to Original_Streams fails, THE System SHALL suppress the error and continue
4. THE System SHALL catch and handle all exceptions in logging code paths
5. WHEN an error occurs in logging, THE System SHALL attempt to log the error using a fallback mechanism
