# Logging System Refactor - Developer Guide

## Overview

TFM's logging system has been refactored to use Python's standard `logging` module while maintaining all existing functionality. This guide covers the new architecture, migration from the old system, and best practices for using the new logging API.

## Architecture

### Component Overview

The refactored system uses Python's standard logging framework with custom handlers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Code                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ logging.     │  │   print()    │  │ sys.stderr.  │      │
│  │ getLogger()  │  │              │  │   write()    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Logging Infrastructure                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Python logging.Logger                    │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │ LogPane    │  │ Stream     │  │ Remote     │     │   │
│  │  │ Handler    │  │ Handler    │  │ Handler    │     │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘     │   │
│  └────────┼────────────────┼────────────────┼────────────┘   │
│           │                │                │                │
│  ┌────────┼────────────────┼────────────────┼────────────┐   │
│  │        │     LogCapture (stdout/stderr)  │            │   │
│  │        │     ┌──────────┴──────────┐     │            │   │
│  │        │     │  Converts to        │     │            │   │
│  │        │     │  LogRecord          │     │            │   │
│  │        │     └──────────┬──────────┘     │            │   │
│  └────────┼────────────────┼────────────────┼────────────┘   │
└───────────┼────────────────┼────────────────┼────────────────┘
            │                │                │
            ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Destinations                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Log Pane    │  │  Original    │  │  Remote      │      │
│  │  (Visual)    │  │  Streams     │  │  Clients     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **LogManager**: Central configuration and coordination point
2. **LogPaneHandler**: Routes messages to TFM's visual log display
3. **StreamOutputHandler**: Routes messages to original stdout/stderr
4. **RemoteMonitoringHandler**: Broadcasts messages to TCP clients
5. **LogCapture**: Converts stdout/stderr writes to LogRecords

## Using the New Logging System

### Getting a Logger

Use `LogManager.getLogger()` to obtain a configured logger:

```python
# Get the log manager instance
log_manager = self.log_manager  # From FileManager or other component

# Get a logger for your component
logger = log_manager.getLogger("FileOp")

# Use standard logging methods
logger.info("File operation started")
logger.warning("Large file detected")
logger.error("Permission denied")
logger.debug("Debug information")
```

### Logger Names

TFM uses descriptive logger names for different components:

- **"Main"**: Main application logging
- **"FileOp"**: File operation logging
- **"DirDiff"**: Directory diff viewer logging
- **"Archive"**: Archive operations logging
- **"Search"**: Search operations logging
- **"Remote"**: Remote monitoring logging

### Log Levels

The system supports all standard Python log levels:

```python
logger.debug("Detailed debugging information")    # DEBUG (10)
logger.info("General informational messages")     # INFO (20)
logger.warning("Warning messages")                # WARNING (30)
logger.error("Error messages")                    # ERROR (40)
logger.critical("Critical error messages")        # CRITICAL (50)
```

### Message Formatting

Logger messages are automatically formatted with timestamp, logger name, and level:

```python
logger.info("File copied successfully")
# Output: "14:23:45 [FileOp] INFO: File copied successfully"

logger.error("Permission denied")
# Output: "14:23:45 [FileOp] ERROR: Permission denied"
```

Stdout/stderr output is displayed as-is:

```python
print("Processing file...")
# Output: "14:23:45 [STDOUT] Processing file..."

sys.stderr.write("Warning: disk space low\n")
# Output: "14:23:45 [STDERR] Warning: disk space low"
```

## Migration Guide

### From add_message() to Logger

**Old Code:**
```python
self.log_manager.add_message("File operation completed", "USER")
self.log_manager.add_message("Error occurred", "ERROR")
```

**New Code:**
```python
logger = self.log_manager.getLogger("FileOp")
logger.info("File operation completed")
logger.error("Error occurred")
```

### Migration Steps

1. **Get a logger** for your component:
   ```python
   logger = self.log_manager.getLogger("ComponentName")
   ```

2. **Replace add_message() calls** with appropriate log level methods:
   - `add_message(msg, "USER")` → `logger.info(msg)`
   - `add_message(msg, "ERROR")` → `logger.error(msg)`
   - `add_message(msg, "WARNING")` → `logger.warning(msg)`
   - `add_message(msg, "DEBUG")` → `logger.debug(msg)`

3. **Use f-strings** for formatted messages:
   ```python
   # Old
   self.log_manager.add_message(f"Processing {filename}")
   
   # New
   logger.info(f"Processing {filename}")
   ```

4. **Keep print() statements** - they're automatically captured:
   ```python
   # These still work and appear in the log pane
   print("Processing file...")
   sys.stderr.write("Warning message\n")
   ```

### Backward Compatibility

The old `add_message()` method still works during migration:

```python
# Still supported for backward compatibility
self.log_manager.add_message("Legacy message", "USER")
```

However, new code should use `getLogger()` for consistency.

## Configuration

### LoggingConfig Options

Configure logging behavior using `LoggingConfig`:

```python
from tfm_logging_handlers import LoggingConfig

config = LoggingConfig(
    # Log pane settings
    log_pane_enabled=True,
    max_log_messages=1000,
    
    # Stream output settings
    stream_output_enabled=None,  # None = auto-detect based on mode
    stream_output_desktop_default=True,
    stream_output_terminal_default=False,
    
    # Remote monitoring settings
    remote_monitoring_enabled=False,
    remote_monitoring_port=9999,
    
    # Log level settings
    default_log_level=logging.INFO,
    logger_levels={
        "FileOp": logging.DEBUG,  # Per-logger override
        "Archive": logging.WARNING
    }
)
```

### Dynamic Reconfiguration

Change configuration at runtime without restart:

```python
# Enable remote monitoring
log_manager.configure_handlers(
    log_pane_enabled=True,
    stream_output_enabled=True,
    remote_enabled=True
)

# Disable log pane for debugging
log_manager.configure_handlers(
    log_pane_enabled=False,
    stream_output_enabled=True
)
```

### Log Level Configuration

Set log levels globally or per-logger:

```python
# Set global default level
log_manager.set_default_level(logging.DEBUG)

# Set per-logger level
log_manager.set_logger_level("FileOp", logging.DEBUG)
log_manager.set_logger_level("Archive", logging.WARNING)
```

## Advanced Features

### Color Coding

Messages are automatically color-coded in the log pane:

- **DEBUG**: Dim/gray color
- **INFO**: Normal color
- **WARNING**: Yellow color
- **ERROR**: Red color
- **CRITICAL**: Bright red color
- **STDOUT**: Cyan color
- **STDERR**: Magenta color

### Remote Monitoring

Enable TCP-based remote monitoring:

```python
# Enable remote monitoring on port 9999
log_manager.configure_handlers(
    remote_enabled=True
)

# Connect from external client
# telnet localhost 9999
```

Messages are broadcast as JSON:

```json
{
    "timestamp": "14:23:45",
    "source": "FileOp",
    "level": "INFO",
    "message": "File operation completed"
}
```

### Thread Safety

The logging system is thread-safe:

```python
import threading

def worker():
    logger = log_manager.getLogger("Worker")
    logger.info("Worker thread started")
    # ... do work ...
    logger.info("Worker thread completed")

# Safe to use from multiple threads
threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
```

### Performance Optimization

The system includes several performance optimizations:

1. **Level checking**: Messages below the configured level are not formatted
2. **Lazy rendering**: Log pane only renders when visible
3. **Message limits**: Automatic cleanup of old messages
4. **Efficient storage**: Uses deque with maxlen for O(1) operations

## Error Handling

### Handler Failure Isolation

If one handler fails, others continue:

```python
# If LogPaneHandler fails, StreamOutputHandler still works
logger.info("This message reaches all working handlers")
```

### Client Failure Recovery

Remote clients are automatically removed on failure:

```python
# Client disconnects are handled gracefully
# Other clients continue receiving messages
```

### Stream Write Failures

Stream write errors are suppressed:

```python
# If stdout/stderr write fails, logging continues
logger.info("This message still reaches other handlers")
```

## Best Practices

### Logger Naming

Use descriptive, hierarchical names:

```python
# Good
logger = log_manager.getLogger("FileOp")
logger = log_manager.getLogger("DirDiff")
logger = log_manager.getLogger("Archive")

# Avoid
logger = log_manager.getLogger("log")
logger = log_manager.getLogger("x")
```

### Log Level Selection

Choose appropriate log levels:

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"Variable value: {value}")

# INFO: General informational messages
logger.info("File operation completed")

# WARNING: Warning messages for unexpected situations
logger.warning("Large file detected, may take time")

# ERROR: Error messages for failures
logger.error("Permission denied")

# CRITICAL: Critical errors requiring immediate attention
logger.critical("Disk full, cannot continue")
```

### Message Content

Write clear, actionable messages:

```python
# Good
logger.info(f"Copied {source} to {destination}")
logger.error(f"Permission denied: {path}")
logger.warning(f"Large file ({size} MB) may take time")

# Avoid
logger.info("Done")
logger.error("Error")
logger.warning("Warning")
```

### Exception Logging

Use exception logging for errors:

```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    # Or with traceback
    logger.exception("Operation failed")
```

### Avoid Excessive Logging

Don't log in tight loops:

```python
# Bad - logs every iteration
for item in large_list:
    logger.debug(f"Processing {item}")

# Good - log summary
logger.info(f"Processing {len(large_list)} items")
# ... process items ...
logger.info("Processing completed")
```

## Testing

### Unit Testing with Logging

Test logging behavior:

```python
def test_file_operation_logging():
    log_manager = LogManager(config)
    logger = log_manager.getLogger("FileOp")
    
    # Perform operation
    logger.info("Test message")
    
    # Verify message was logged
    messages = log_manager.get_messages()
    assert any("Test message" in msg for msg in messages)
```

### Mocking Loggers

Mock loggers for testing:

```python
from unittest.mock import Mock

def test_component():
    mock_logger = Mock()
    component = MyComponent(mock_logger)
    
    component.do_something()
    
    # Verify logging calls
    mock_logger.info.assert_called_once()
```

## Troubleshooting

### Messages Not Appearing

Check configuration:

```python
# Verify log pane is enabled
log_manager.configure_handlers(log_pane_enabled=True)

# Check log level
log_manager.set_default_level(logging.DEBUG)
```

### Performance Issues

Reduce logging verbosity:

```python
# Set higher log level
log_manager.set_default_level(logging.WARNING)

# Reduce message limit
config.max_log_messages = 500
```

### Remote Monitoring Not Working

Check configuration:

```python
# Verify remote monitoring is enabled
log_manager.configure_handlers(remote_enabled=True)

# Check port is not in use
# netstat -an | grep 9999
```

## Implementation Details

### Handler Pipeline

Messages flow through the handler pipeline:

1. Logger receives message
2. Level check (skip if below threshold)
3. Create LogRecord
4. Route to all configured handlers
5. Each handler formats and outputs message

### LogRecord Extensions

Custom fields added to LogRecord:

- `is_stream_capture`: True for stdout/stderr, False for logger messages
- Used by handlers to determine formatting behavior

### Message Storage

Messages stored in deque with maxlen:

```python
from collections import deque

self.messages = deque(maxlen=config.max_log_messages)
```

Automatic cleanup when limit reached.

## Future Enhancements

Potential improvements:

- **Log file output**: Save logs to file
- **Log filtering**: Filter display by level or logger
- **Log search**: Search through log history
- **Structured logging**: JSON format support
- **Log rotation**: Automatic log file rotation

## Conclusion

The refactored logging system provides a standard, flexible, and powerful logging infrastructure for TFM. By using Python's standard logging module, developers can leverage familiar patterns while maintaining TFM's unique features like log pane display, remote monitoring, and configurable output routing.

For questions or issues, refer to the requirements and design documents in `.kiro/specs/logging-system-refactor/`.
