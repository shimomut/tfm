# Logging Handlers System

## Overview

The Logging Handlers System provides custom logging handlers for TFM's unified logging infrastructure. It extends Python's standard logging module with specialized handlers for UI integration, stream redirection, and remote monitoring.

## Architecture

### Core Handler Classes

**LogPaneHandler**
- Displays log messages in TFM's UI log pane
- Integrates with the details pane system
- Provides real-time log viewing within the application
- Supports log level filtering and formatting

**StreamOutputHandler**
- Redirects stdout/stderr to logging system
- Captures print statements and errors
- Ensures all output goes through logging
- Maintains output ordering

**RemoteMonitoringHandler**
- Sends log messages to remote monitoring service
- Enables remote debugging and monitoring
- Supports network-based log aggregation
- Handles connection failures gracefully

## Implementation Details

### LogPaneHandler

The LogPaneHandler integrates logging with TFM's UI:

```python
class LogPaneHandler(logging.Handler):
    def __init__(self, log_pane):
        """Initialize with reference to log pane UI component."""
        super().__init__()
        self.log_pane = log_pane
        
    def emit(self, record):
        """Emit log record to UI log pane."""
        # Format message
        msg = self.format(record)
        
        # Add to log pane with appropriate color
        self.log_pane.add_message(msg, record.levelno)
```

**Key Features**:
- **Thread-Safe**: Uses locks for concurrent access
- **Level Colors**: Different colors for different log levels
- **Scrolling**: Auto-scrolls to show latest messages
- **Filtering**: Can filter by log level
- **Buffering**: Buffers messages for efficient display

### StreamOutputHandler

The StreamOutputHandler captures stream output:

```python
class StreamOutputHandler(logging.Handler):
    def __init__(self, stream_name):
        """Initialize for stdout or stderr."""
        super().__init__()
        self.stream_name = stream_name
        
    def emit(self, record):
        """Emit captured stream output as log message."""
        # Determine log level based on stream
        level = logging.ERROR if self.stream_name == 'stderr' else logging.INFO
        
        # Log the message
        logger = logging.getLogger(self.stream_name)
        logger.log(level, record.getMessage())
```

**Key Features**:
- **Stream Capture**: Captures stdout and stderr
- **Level Mapping**: Maps streams to log levels
- **Preservation**: Preserves original output format
- **Buffering**: Handles line buffering correctly

### RemoteMonitoringHandler

The RemoteMonitoringHandler enables remote logging:

```python
class RemoteMonitoringHandler(logging.Handler):
    def __init__(self, host, port):
        """Initialize with remote host and port."""
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        
    def emit(self, record):
        """Send log record to remote monitoring service."""
        try:
            # Serialize record
            data = self.format(record)
            
            # Send to remote service
            self.send_to_remote(data)
        except Exception as e:
            # Handle connection errors
            self.handleError(record)
```

**Key Features**:
- **Network Logging**: Sends logs over network
- **Reconnection**: Automatically reconnects on failure
- **Buffering**: Buffers messages during disconnection
- **Compression**: Optionally compresses log data
- **Security**: Supports encrypted connections

## Handler Configuration

### LogPaneHandler Configuration

```python
# Configure log pane handler
log_pane_handler = LogPaneHandler(log_pane)
log_pane_handler.setLevel(logging.INFO)
log_pane_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Add to root logger
logging.getLogger().addHandler(log_pane_handler)
```

### StreamOutputHandler Configuration

```python
# Redirect stdout
stdout_handler = StreamOutputHandler('stdout')
sys.stdout = StreamRedirector(stdout_handler)

# Redirect stderr
stderr_handler = StreamOutputHandler('stderr')
sys.stderr = StreamRedirector(stderr_handler)
```

### RemoteMonitoringHandler Configuration

```python
# Configure remote monitoring
remote_handler = RemoteMonitoringHandler('monitor.example.com', 9999)
remote_handler.setLevel(logging.WARNING)  # Only send warnings and errors

# Add to root logger
logging.getLogger().addHandler(remote_handler)
```

## Integration Points

### Log Manager Integration

The handlers integrate with TFM's log manager:

- **Handler Registration**: Registered with log manager
- **Configuration**: Configured through log manager
- **Lifecycle**: Managed by log manager
- **Cleanup**: Properly cleaned up on shutdown

### UI Integration

LogPaneHandler integrates with UI system:

- **Details Pane**: Displays in details pane
- **Color Coding**: Uses TFM color system
- **Scrolling**: Integrates with scrolling system
- **Filtering**: Uses UI filtering controls

### Configuration System

Handlers respect configuration options:

- `logging.log_pane_enabled`: Enable/disable log pane
- `logging.remote_monitoring_enabled`: Enable/disable remote monitoring
- `logging.remote_host`: Remote monitoring host
- `logging.remote_port`: Remote monitoring port

## Error Handling

The handlers handle various error conditions:

- **UI Errors**: Handle UI component failures
- **Network Errors**: Handle connection failures
- **Format Errors**: Handle formatting errors
- **Thread Errors**: Handle threading issues

### Error Recovery

On error, handlers:

1. **Log Error**: Log handler errors to fallback handler
2. **Continue**: Don't crash on handler errors
3. **Retry**: Retry failed operations when appropriate
4. **Fallback**: Fall back to console logging if needed

## Performance Considerations

### Buffering

Handlers use buffering for performance:

- **Message Buffering**: Buffer messages for batch processing
- **Flush Control**: Control when buffers are flushed
- **Memory Limits**: Limit buffer size to prevent memory issues

### Threading

Handlers are thread-safe:

- **Locks**: Use locks for concurrent access
- **Queue**: Use queue for cross-thread communication
- **Async**: Support asynchronous logging

## Testing Considerations

Key areas for testing:

- **Message Delivery**: Verify messages reach handlers
- **Thread Safety**: Test concurrent logging
- **Error Handling**: Test error conditions
- **Performance**: Test with high message volume
- **Memory**: Test for memory leaks
- **Network**: Test remote monitoring

## Related Documentation

- [Logging Feature](../LOGGING_FEATURE.md) - User documentation
- [Log Manager System](LOG_MANAGER_SYSTEM.md) - Log manager implementation
- [Logging Migration Guide](LOGGING_MIGRATION_GUIDE.md) - Migration guide
- [Remote Log Monitoring Feature](../REMOTE_LOG_MONITORING_FEATURE.md) - Remote monitoring

## Future Enhancements

Potential improvements:

- **Database Handler**: Log to database
- **File Rotation**: Automatic log file rotation
- **Compression**: Compress old log files
- **Filtering**: Advanced filtering capabilities
- **Aggregation**: Aggregate similar messages
- **Analytics**: Log analytics and reporting
