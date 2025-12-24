# Log Manager System

## Overview

The Log Manager System provides comprehensive logging functionality for TFM, capturing application output, error messages, and user feedback in a dedicated log pane. It enables debugging, monitoring, and user communication through a centralized logging interface.

## Important Note

**This document describes the legacy logging system.** TFM has been refactored to use Python's standard `logging` module. For new code, please refer to:

- **Developer Guide**: `doc/dev/LOGGING_SYSTEM_REFACTOR.md`
- **Migration Guide**: `doc/dev/LOGGING_MIGRATION_GUIDE.md`
- **Quick Reference**: `doc/dev/LOGGING_QUICK_REFERENCE.md`
- **User Guide**: `doc/LOGGING_FEATURE.md`

The legacy `add_message()` method is still supported for backward compatibility, but new code should use `getLogger()` instead.

## Features

### Core Capabilities
- **Output Capture**: Captures stdout and stderr from the application
- **Log Display**: Dedicated pane for viewing log messages
- **Scroll Management**: Full scrolling support for log history
- **Message Filtering**: Different message types and sources
- **Automatic Cleanup**: Configurable message limits and cleanup

### Advanced Features
- **Real-time Updates**: Live display of new log messages
- **Source Tracking**: Identifies message sources (STDOUT, STDERR, etc.)
- **Scroll Controls**: Keyboard navigation through log history
- **Memory Management**: Automatic cleanup of old messages
- **Thread Safety**: Safe operation in multi-threaded environments

## Class Structure

### LogCapture Class
```python
class LogCapture:
    def __init__(self, log_messages, source)
    def write(self, message)
    def flush()
```

### LogManager Class
```python
class LogManager:
    def __init__(self, config)
    def add_message(self, message, source="USER")
    def get_messages()
    def clear_messages()
    def setup_capture()
    def restore_stdio()
    def handle_scroll_input(self, key)
    def draw_log_pane(self, stdscr, safe_addstr_func, log_start_y, log_height, width)
```

## Usage Examples

### Basic Logging
```python
log_manager = LogManager(config)

# Add user messages
log_manager.add_message("File operation completed successfully")
log_manager.add_message("Warning: Large file detected", "WARNING")

# Automatic capture of print statements
print("This will appear in the log pane")
```

### Error Logging
```python
try:
    risky_operation()
except Exception as e:
    log_manager.add_message(f"Error: {str(e)}", "ERROR")
```

### Progress Updates
```python
for i, file in enumerate(files):
    log_manager.add_message(f"Processing {file.name} ({i+1}/{len(files)})")
    process_file(file)
```

## Output Capture System

### Automatic Capture
The system automatically captures:
- **stdout**: Regular print statements and program output
- **stderr**: Error messages and warnings
- **User Messages**: Explicit log messages from TFM operations

### Capture Setup
```python
# Setup capture (done automatically by TFM)
log_manager.setup_capture()

# All print statements now go to log pane
print("This appears in the log")

# Restore normal output when needed
log_manager.restore_stdio()
```

## Log Display Features

### Visual Layout
```
┌─────────────────────────────────────┐
│ Main TFM Interface                  │
│                                     │
├─────────────────────────────────────┤
│ Log Messages:                       │
│ [USER] File copied successfully     │
│ [STDOUT] Processing file.txt        │
│ [STDERR] Warning: Permission issue  │
│ [USER] Operation completed          │
└─────────────────────────────────────┘
```

### Message Format
- **Source Prefix**: `[USER]`, `[STDOUT]`, `[STDERR]`
- **Timestamp**: Optional timestamp for messages
- **Message Content**: The actual log message
- **Color Coding**: Different colors for different message types

## Navigation Controls

### Keyboard Shortcuts
- **Shift+↑**: Scroll log up one line
- **Shift+↓**: Scroll log down one line
- **Shift+Page Up**: Scroll log up one page
- **Shift+Page Down**: Scroll log down one page
- **Shift+Home**: Jump to top of log
- **Shift+End**: Jump to bottom of log (most recent)

### Scroll Behavior
- **Auto-scroll**: Automatically scrolls to show new messages
- **Manual Control**: User can scroll to view history
- **Position Memory**: Remembers scroll position during navigation
- **Bounds Checking**: Prevents scrolling beyond available content

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.log_manager = LogManager(self.config)

# Setup output capture
self.log_manager.setup_capture()

# Add messages during operations
self.log_manager.add_message("Starting file operation")

# Handle log scrolling
if self.log_manager.handle_scroll_input(key):
    self.needs_full_redraw = True
```

### Drawing Integration
```python
# In main draw loop
log_start_y = height - log_height
self.log_manager.draw_log_pane(
    self.stdscr, self.safe_addstr, 
    log_start_y, log_height, width
)
```

## Configuration Options

### Configurable Settings
- **MAX_LOG_MESSAGES**: Maximum number of messages to keep in memory
- **LOG_HEIGHT_RATIO**: Default height ratio for log pane
- **AUTO_SCROLL**: Whether to auto-scroll to new messages
- **MESSAGE_TIMESTAMPS**: Whether to include timestamps

### Example Configuration
```python
class Config:
    MAX_LOG_MESSAGES = 1000
    DEFAULT_LOG_HEIGHT_RATIO = 0.25
    LOG_AUTO_SCROLL = True
    LOG_TIMESTAMPS = False
```

## Message Management

### Message Storage
- **Circular Buffer**: Efficient storage with automatic cleanup
- **Memory Limits**: Configurable maximum message count
- **Source Tracking**: Maintains message source information
- **Thread Safety**: Safe concurrent access to message storage

### Cleanup Strategy
```python
# Automatic cleanup when limit exceeded
if len(self.log_messages) > self.config.MAX_LOG_MESSAGES:
    # Remove oldest messages
    self.log_messages = self.log_messages[-self.config.MAX_LOG_MESSAGES:]
```

## Advanced Features

### Message Filtering
```python
# Filter by source
stdout_messages = [msg for msg in messages if msg.source == "STDOUT"]
error_messages = [msg for msg in messages if msg.source == "STDERR"]
```

### Custom Message Types
```python
log_manager.add_message("Debug info", "DEBUG")
log_manager.add_message("Performance metric", "PERF")
log_manager.add_message("User action", "ACTION")
```

### Batch Operations
```python
# Log multiple related messages
messages = [
    "Starting batch operation",
    f"Processing {len(files)} files",
    "Batch operation completed"
]
for msg in messages:
    log_manager.add_message(msg)
```

## Error Handling

### Capture Errors
- **Setup Failures**: Graceful handling of capture setup failures
- **Write Errors**: Safe handling of write operation errors
- **Memory Issues**: Protection against memory exhaustion
- **Thread Safety**: Safe operation in concurrent environments

### Recovery Mechanisms
```python
try:
    log_manager.setup_capture()
except Exception as e:
    # Fallback to normal stdout/stderr
    print(f"Log capture setup failed: {e}")
```

## Performance Considerations

### Efficiency Features
- **Lazy Rendering**: Only renders visible log lines
- **Efficient Storage**: Optimized message storage and retrieval
- **Minimal Overhead**: Low impact on application performance
- **Smart Updates**: Only redraws when log content changes

### Memory Management
- **Automatic Cleanup**: Removes old messages automatically
- **Configurable Limits**: User-controllable memory usage
- **Efficient Data Structures**: Optimized for log operations
- **Garbage Collection**: Proper cleanup of message objects

## Common Use Cases

### File Operations
```python
log_manager.add_message(f"Copying {source} to {destination}")
# ... perform copy operation ...
log_manager.add_message("Copy completed successfully")
```

### Error Reporting
```python
try:
    dangerous_operation()
except PermissionError:
    log_manager.add_message("Permission denied - check file permissions", "ERROR")
except FileNotFoundError:
    log_manager.add_message("File not found - verify path", "ERROR")
```

### Progress Tracking
```python
total_files = len(file_list)
for i, file in enumerate(file_list):
    progress = f"({i+1}/{total_files})"
    log_manager.add_message(f"Processing {file.name} {progress}")
```

### Debug Information
```python
if debug_mode:
    log_manager.add_message(f"Debug: Variable value = {variable}", "DEBUG")
    log_manager.add_message(f"Debug: Function called with args: {args}", "DEBUG")
```

## Benefits

### User Experience
- **Immediate Feedback**: Real-time information about operations
- **Error Visibility**: Clear display of errors and warnings
- **Operation History**: Review of recent actions and results
- **Progress Tracking**: Visual progress for long operations

### Developer Experience
- **Easy Debugging**: Centralized location for debug output
- **Error Tracking**: Comprehensive error logging and display
- **Simple API**: Easy to add logging to any operation
- **Flexible Output**: Support for different message types and sources

### System Benefits
- **Centralized Logging**: All output in one managed location
- **Memory Efficient**: Automatic cleanup prevents memory leaks
- **Thread Safe**: Safe operation in multi-threaded environments
- **Configurable**: User-controllable logging behavior

## Future Enhancements

### Potential Improvements
- **Log Levels**: Support for different log levels (DEBUG, INFO, WARN, ERROR)
- **Log Filtering**: Filter display by message type or source
- **Log Export**: Save log messages to file
- **Search**: Search through log history
- **Timestamps**: Optional timestamp display for messages

### Advanced Features
- **Log Rotation**: Automatic log file rotation
- **Remote Logging**: Send logs to remote servers
- **Structured Logging**: JSON or structured log format support
- **Log Analysis**: Built-in log analysis tools
- **Custom Formatters**: User-configurable message formatting

## Testing

### Test Coverage
- **Message Storage**: Verify correct message storage and retrieval
- **Capture System**: Test stdout/stderr capture functionality
- **Scroll Operations**: Test all scroll navigation controls
- **Memory Management**: Verify automatic cleanup works correctly
- **Integration**: Test integration with main application

### Test Scenarios
- **Basic Logging**: Simple message addition and display
- **Capture Operations**: Verify output capture works correctly
- **Scroll Navigation**: Test all navigation controls
- **Memory Limits**: Test behavior at message limits
- **Error Conditions**: Test error handling and recovery

## Conclusion

The Log Manager System provides essential logging and output management functionality for TFM. It offers real-time feedback, comprehensive error tracking, and efficient memory management while maintaining excellent performance and user experience. The system's flexibility and ease of use make it an integral part of TFM's user interface and debugging capabilities.