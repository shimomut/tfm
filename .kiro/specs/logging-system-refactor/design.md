# Design Document

## Overview

This design refactors TFM's logging system to use Python's standard `logging` module while preserving all existing functionality. The architecture introduces custom log handlers that route messages to multiple destinations: the TFM log pane, original stdout/stderr streams, and remote monitoring clients. The design maintains backward compatibility with existing code while providing a migration path to standard logging practices.

The key innovation is a set of custom handlers that integrate Python's logging framework with TFM's unique requirements: visual log display with color coding, configurable output routing based on execution mode (desktop vs terminal), and TCP-based remote monitoring.

## Architecture

### Component Overview

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

### Handler Architecture

The system uses three custom handlers:

1. **LogPaneHandler**: Routes messages to TFM's visual log display
   - Stores messages in a deque with configurable max size
   - Applies color coding based on log level and source
   - Triggers UI redraws when new messages arrive
   - Can be disabled for debugging

2. **StreamHandler**: Routes messages to original stdout/stderr
   - Writes to sys.__stdout__ or sys.__stderr__
   - Configurable per execution mode (desktop/terminal)
   - Handles write failures gracefully
   - Respects log level filtering

3. **RemoteHandler**: Broadcasts messages to TCP clients
   - Maintains list of connected clients
   - Formats messages as JSON
   - Handles client disconnections
   - Only active when remote monitoring is enabled

### LogCapture Integration

The existing `LogCapture` class is enhanced to convert stdout/stderr writes into `LogRecord` objects while preserving the raw, unformatted nature of the output:

```python
class LogCapture:
    def write(self, text):
        if text.strip():
            # For stdout/stderr, preserve the raw text without additional formatting
            # Multi-line output is preserved as-is
            record = logging.LogRecord(
                name=self.source,  # "STDOUT" or "STDERR"
                level=logging.INFO if self.source == "STDOUT" else logging.WARNING,
                pathname="",
                lineno=0,
                msg=text,  # Raw text, not stripped or modified
                args=(),
                exc_info=None
            )
            # CRITICAL: Mark this as a stream capture (not a formatted logger message)
            # Handlers will check this flag to determine formatting behavior
            record.is_stream_capture = True
            # Route through the logger
            self.logger.handle(record)
```

**Key Design Decision**: We use `logging.Logger` as the unified routing mechanism for both logger messages and stdout/stderr, but we distinguish them using the `is_stream_capture` attribute on the `LogRecord`. This allows:

1. **Unified routing**: All messages flow through the same handler pipeline
2. **Differential formatting**: Handlers check `is_stream_capture` to decide formatting:
   - If `True`: Display as-is (stdout/stderr)
   - If `False`: Apply full formatting (logger messages)
3. **Preserved semantics**: Stdout/stderr maintains its raw, unformatted nature

This approach ensures:
- Stdout/stderr output flows through the same handler pipeline as logger messages
- Stream output is displayed as-is without additional formatting
- Multi-line output (e.g., from print statements with newlines) is preserved
- Logger messages get full formatting (timestamp, name, level, message)

## Components and Interfaces

### LogManager Class

The refactored `LogManager` serves as the central configuration and coordination point:

```python
class LogManager:
    def __init__(self, config, remote_port=None, debug_mode=False):
        """
        Initialize logging system with configuration.
        
        Args:
            config: Configuration object with logging settings
            remote_port: TCP port for remote monitoring (None to disable)
            debug_mode: If True, enables original stream output in terminal mode
        """
        self._loggers = {}  # Cache of created loggers by name
        
    def getLogger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with TFM handlers configured.
        Returns existing logger if name was already used.
        
        TFM creates multiple loggers for different purposes:
        - "Main": Main application logging
        - "FileOp": File operation logging
        - "DirDiff": Directory diff viewer logging
        - "Archive": Archive operations logging
        - etc.
        
        Args:
            name: Logger name (e.g., "Main", "FileOp", "DirDiff")
            
        Returns:
            Configured logging.Logger instance (existing or newly created)
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        # Configure handlers...
        self._loggers[name] = logger
        return logger
        
    def add_message(self, source: str, message: str):
        """
        Legacy method for backward compatibility.
        Converts to logger call internally.
        
        Args:
            source: Message source identifier
            message: Message text
        """
        
    def configure_handlers(self, 
                          log_pane_enabled: bool = True,
                          stream_output_enabled: bool = None,
                          remote_enabled: bool = False):
        """
        Configure which handlers are active.
        
        Args:
            log_pane_enabled: Enable log pane display
            stream_output_enabled: Enable original stream output (None = auto-detect)
            remote_enabled: Enable remote monitoring
        """
```

### LogPaneHandler Class

Custom handler for TFM's visual log display:

```python
class LogPaneHandler(logging.Handler):
    def __init__(self, max_messages: int = 1000):
        """
        Initialize log pane handler.
        
        Args:
            max_messages: Maximum messages to retain
        """
        
    def emit(self, record: logging.LogRecord):
        """
        Process a log record and add to display queue.
        Checks record.is_stream_capture to determine formatting:
        - If True: Display as-is (stdout/stderr)
        - If False: Format with timestamp, name, level, message (logger)
        
        Args:
            record: Log record to process
        """
        if getattr(record, 'is_stream_capture', False):
            # Stdout/stderr: display as-is with minimal formatting
            formatted_lines = self.format_stream_message(record)
            for line in formatted_lines:
                self.messages.append(line)
        else:
            # Logger message: apply full formatting
            formatted = self.format_logger_message(record)
            self.messages.append(formatted)
        
    def format_logger_message(self, record: logging.LogRecord) -> str:
        """
        Format a logger message with full formatting.
        
        Args:
            record: Log record from a logger
            
        Returns:
            Formatted string: "HH:MM:SS [LoggerName] LEVEL: message"
        """
        timestamp = datetime.fromtimestamp(record.created).strftime(LOG_TIME_FORMAT)
        return f"{timestamp} [{record.name}] {record.levelname}: {record.getMessage()}"
        
    def format_stream_message(self, record: logging.LogRecord) -> List[str]:
        """
        Format a stdout/stderr message as-is, preserving multi-line output.
        Only adds timestamp and source prefix, no other formatting.
        
        Args:
            record: Log record from stdout/stderr capture
            
        Returns:
            List of formatted lines, each with timestamp and source prefix
        """
        timestamp = datetime.fromtimestamp(record.created).strftime(LOG_TIME_FORMAT)
        raw_message = record.getMessage()
        
        # Preserve multi-line output
        lines = raw_message.split('\n')
        return [f"{timestamp} [{record.name}] {line}" for line in lines if line]
        
    def get_messages(self) -> List[Tuple[str, str, str]]:
        """
        Get messages for display.
        
        Returns:
            List of (timestamp, source, message) tuples
        """
        
    def get_color_for_record(self, record: logging.LogRecord) -> Tuple[int, int]:
        """
        Determine color pair and attributes for a log record.
        Uses record.levelno for logger messages, record.name for stdout/stderr.
        
        Args:
            record: Log record
            
        Returns:
            (color_pair, attributes) tuple
        """
```

**Formatting Logic Summary**:
- **Logger messages** (`is_stream_capture=False`): `"14:23:45 [FileOp] INFO: File copied successfully"`
- **Stdout** (`is_stream_capture=True`, `name="STDOUT"`): `"14:23:45 [STDOUT] Processing file..."`
- **Stderr** (`is_stream_capture=True`, `name="STDERR"`): `"14:23:45 [STDERR] Warning: disk space low"`

### StreamOutputHandler Class

Custom handler for original stdout/stderr output:

```python
class StreamOutputHandler(logging.Handler):
    def __init__(self, stream):
        """
        Initialize stream output handler.
        
        Args:
            stream: Output stream (sys.__stdout__ or sys.__stderr__)
        """
        self.stream = stream
        
    def emit(self, record: logging.LogRecord):
        """
        Write log record to stream.
        Respects is_stream_capture flag for formatting.
        
        Args:
            record: Log record to write
        """
        try:
            if getattr(record, 'is_stream_capture', False):
                # Stdout/stderr: write raw message without additional formatting
                self.stream.write(record.getMessage())
                if not record.getMessage().endswith('\n'):
                    self.stream.write('\n')
            else:
                # Logger message: write with full formatting
                formatted = f"{self.format(record)}\n"
                self.stream.write(formatted)
            self.stream.flush()
        except (OSError, IOError):
            # Suppress stream write errors
            pass
```

**Key Behavior**:
- **Logger messages**: Written with full formatting to original streams
- **Stdout/stderr**: Written as-is (raw text) to preserve original output
- This ensures that `print("Hello")` appears as `Hello` in sys.__stdout__, not as a formatted log message

### RemoteMonitoringHandler Class

Custom handler for TCP-based remote monitoring:

```python
class RemoteMonitoringHandler(logging.Handler):
    def __init__(self, port: int):
        """
        Initialize remote monitoring handler.
        
        Args:
            port: TCP port to listen on
        """
        
    def emit(self, record: logging.LogRecord):
        """
        Broadcast log record to all connected clients.
        
        Args:
            record: Log record to broadcast
        """
        
    def start_server(self):
        """Start TCP server for accepting client connections."""
        
    def stop_server(self):
        """Stop TCP server and close all client connections."""
        
    def _accept_connections(self):
        """Background thread for accepting new clients."""
        
    def _broadcast_to_clients(self, message: dict):
        """
        Send message to all connected clients.
        
        Args:
            message: JSON-serializable message dict
        """
```

### Configuration Object

Configuration structure for logging behavior:

```python
@dataclass
class LoggingConfig:
    """Configuration for logging system."""
    
    # Log pane settings
    log_pane_enabled: bool = True
    max_log_messages: int = 1000
    
    # Stream output settings
    stream_output_enabled: Optional[bool] = None  # None = auto-detect
    stream_output_desktop_default: bool = True
    stream_output_terminal_default: bool = False
    
    # Remote monitoring settings
    remote_monitoring_enabled: bool = False
    remote_monitoring_port: Optional[int] = None
    
    # Log level settings
    default_log_level: int = logging.INFO
    logger_levels: Dict[str, int] = field(default_factory=dict)
    
    # Format settings
    timestamp_format: str = "%H:%M:%S"
    message_format: str = "%(asctime)s [%(name)s] %(message)s"
```

## Data Models

### Log Message Structure

Log messages are represented differently based on their source:

**Logger Messages** (formatted):
```python
LoggerMessage = Tuple[str, str, str, str]
# (timestamp, logger_name, level, message)
# Example: ("14:23:45", "FileOp", "INFO", "File operation completed")
# Display format: "14:23:45 [FileOp] INFO: File operation completed"
```

**Stdout/Stderr Messages** (unformatted):
```python
StdStreamMessage = Tuple[str, str, str]
# (timestamp, source, raw_message)
# Example: ("14:23:45", "STDOUT", "Processing file: example.txt\nSize: 1024 bytes")
# Display format: "14:23:45 [STDOUT] Processing file: example.txt\n14:23:45 [STDOUT] Size: 1024 bytes"
# Note: Multi-line messages are preserved as-is, each line gets its own timestamp
```

The key distinction:
- **Logger messages**: Formatted with timestamp, logger name, level, and message
- **Stdout/stderr**: Displayed as-is with only timestamp and source prefix, preserving all original formatting including newlines

### Log Record Extensions

Custom fields added to `logging.LogRecord`:

```python
# Standard fields used:
# - name: Logger name or "STDOUT"/"STDERR"
# - levelname: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
# - levelno: Numeric level (10, 20, 30, 40, 50)
# - msg: Message text
# - created: Timestamp (float)

# Custom fields:
# - source_type: "LOGGER" | "STDOUT" | "STDERR"
# - display_color: Color pair for log pane display
```

### Remote Message Format

Messages sent to remote clients:

```python
{
    "timestamp": "14:23:45",
    "source": "tfm_main",
    "level": "INFO",
    "message": "Application started"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I identified several areas of redundancy:

**Redundancies Eliminated:**
- 2.4 is redundant with 2.3 (if stdout and stderr have distinct colors, both statements are true)
- 7.2 is redundant with 7.1 (both test the same level filtering behavior)
- 9.2, 9.4, 9.5 are implementation details, not testable behaviors (9.1 and 9.3 cover observable thread safety)
- 10.4 and 12.4 are general statements covered by specific tests elsewhere

**Properties Combined:**
- 5.3 and 5.4 can be combined into one property about stdout/stderr routing
- 4.4 and 4.5 can be combined into one property about remote monitoring routing

This reflection ensures each property provides unique validation value without overlap.

### Correctness Properties

Property 1: Logger type contract
*For any* logger name, calling getLogger(name) should return an instance of logging.Logger
**Validates: Requirements 1.1**

Property 2: Logger instance caching
*For any* logger name, calling getLogger(name) multiple times should return the same Logger instance (object identity, not just equality)
**Validates: Requirements 1.3**

Property 3: Multiple logger support
*For any* set of distinct logger names (e.g., "Main", "FileOp", "DirDiff"), the system should create and maintain separate Logger instances for each name
**Validates: Requirements 1.4**

Property 4: Logger handler configuration
*For any* logger name, the logger returned by getLogger(name) should have the configured handlers (LogPaneHandler, StreamOutputHandler, RemoteMonitoringHandler) attached according to the current configuration
**Validates: Requirements 1.2**

Property 5: Message routing to configured destinations
*For any* log message and configuration, emitting the message should result in it appearing in exactly the destinations enabled in the configuration (log pane, original streams, remote clients)
**Validates: Requirements 1.6, 2.6, 5.3, 5.4**

Property 6: Log pane default display
*For any* log message emitted with default configuration, the message should appear in the log pane
**Validates: Requirements 2.1**

Property 7: Color coding by log level
*For any* log message at a specific level, the message displayed in the log pane should have a color that corresponds to that level, and different levels should have different colors
**Validates: Requirements 2.2**

Property 8: Original streams usage
*For any* log message routed to original streams, the message should be written to sys.__stdout__ for INFO/DEBUG levels and sys.__stderr__ for WARNING/ERROR/CRITICAL levels
**Validates: Requirements 3.5**

Property 9: Remote broadcast to all clients
*For any* log message and any number of connected remote clients (when remote monitoring is enabled), all clients should receive the message
**Validates: Requirements 4.2, 4.4, 4.5**

Property 10: Source distinction preservation
*For any* stdout write and any stderr write, the two messages should be labeled with different source identifiers ("STDOUT" vs "STDERR") in all output destinations
**Validates: Requirements 5.5**

Property 11: Dynamic configuration application
*For any* configuration change made while the system is running, subsequent log messages should be routed according to the new configuration without requiring a restart
**Validates: Requirements 6.5**

Property 12: Log level filtering
*For any* logger with a minimum level set, only messages at or above that level should be emitted, and messages below that level should be suppressed
**Validates: Requirements 7.1**

Property 13: Per-logger level override
*For any* logger with a per-logger level override, the logger should use its override level instead of the global level, even when the global level is different
**Validates: Requirements 7.4**

Property 14: Timestamp inclusion
*For any* log message displayed in any destination, the message should include a timestamp formatted according to LOG_TIME_FORMAT
**Validates: Requirements 8.1, 8.5**

Property 15: Logger message formatting
*For any* message emitted by a logger, the displayed message should be formatted as "timestamp [logger_name] LEVEL: message"
**Validates: Requirements 8.1**

Property 16: Stdout/stderr raw display
*For any* stdout or stderr output, the displayed message should preserve the original text without additional formatting beyond timestamp and source prefix
**Validates: Requirements 8.2, 8.3**

Property 17: Multi-line preservation
*For any* stdout or stderr output containing newlines, each line should be displayed separately with its own timestamp and source prefix
**Validates: Requirements 8.4**

Property 18: Message truncation
*For any* log message longer than the display width, the displayed message should be truncated to fit the width with an ellipsis indicator
**Validates: Requirements 8.6**

Property 19: Thread-safe concurrent logging
*For any* set of log messages emitted concurrently from multiple threads, all messages should appear in the output without corruption (no interleaved characters, no lost messages)
**Validates: Requirements 9.1**

Property 20: Thread-safe client management
*For any* sequence of client connections and disconnections happening concurrently with message emission, the system should handle all operations without crashes or data corruption
**Validates: Requirements 9.3**

Property 21: Backward compatibility routing
*For any* message added via the legacy add_message() method, the message should be routed through the same handler pipeline as logger messages
**Validates: Requirements 10.2**

Property 22: Disabled level formatting skip
*For any* logger with a level disabled, messages at that level should not have their formatting operations executed (verifiable by checking that expensive formatting functions are not called)
**Validates: Requirements 11.1**

Property 23: Hidden log pane rendering skip
*For any* log message emitted when the log pane is not visible, the rendering operations for the log pane should be skipped (verifiable by checking that rendering functions are not called)
**Validates: Requirements 11.3**

Property 24: Message retention limit
*For any* sequence of messages exceeding the maximum message limit, the oldest messages should be discarded to maintain the limit, and the newest messages should be retained
**Validates: Requirements 11.4**

Property 25: Handler failure isolation
*For any* handler that fails during message emission, the other handlers should continue processing the message successfully
**Validates: Requirements 12.1**

Property 26: Client failure recovery
*For any* remote client that fails or disconnects, the system should remove the client from the active list and continue broadcasting to remaining clients
**Validates: Requirements 12.2**

Property 27: Stream write failure suppression
*For any* write to original streams that fails, the system should suppress the exception and continue processing the message through other handlers
**Validates: Requirements 12.3**

Property 28: Error logging fallback
*For any* error that occurs in the logging system, the system should attempt to log the error using sys.__stderr__ as a fallback mechanism
**Validates: Requirements 12.5**

## Error Handling

### Handler Failure Isolation

Each handler operates independently. If one handler fails, others continue:

```python
class LogManager:
    def _emit_to_handlers(self, record):
        """Emit record to all handlers with error isolation."""
        for handler in self.handlers:
            try:
                handler.emit(record)
            except Exception as e:
                # Log to fallback (sys.__stderr__)
                try:
                    sys.__stderr__.write(f"Handler {handler.__class__.__name__} failed: {e}\n")
                    sys.__stderr__.flush()
                except:
                    pass  # Even fallback failed, but continue
```

### Remote Client Failure Handling

Client failures are detected during broadcast and handled gracefully:

```python
def _broadcast_to_clients(self, message):
    """Broadcast with automatic client cleanup on failure."""
    failed_clients = []
    for client in self.clients:
        try:
            client.send(message)
        except (ConnectionError, BrokenPipeError):
            failed_clients.append(client)
    
    # Remove failed clients
    for client in failed_clients:
        self.clients.remove(client)
        try:
            client.close()
        except:
            pass
```

### Stream Write Failure Handling

Stream writes are wrapped in try-except to prevent crashes:

```python
def emit(self, record):
    """Emit with stream write protection."""
    try:
        self.stream.write(self.format(record) + '\n')
        self.stream.flush()
    except (OSError, IOError):
        # Suppress stream write errors
        pass
```

### Fallback Error Logging

When logging itself fails, use sys.__stderr__ as last resort:

```python
def _log_error_fallback(self, error, context):
    """Log error using fallback mechanism."""
    try:
        timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
        message = f"{timestamp} [ERROR] Logging system error in {context}: {error}\n"
        sys.__stderr__.write(message)
        sys.__stderr__.flush()
    except:
        pass  # Nothing more we can do
```

## Testing Strategy

### Dual Testing Approach

The logging system requires both unit tests and property-based tests:

**Unit Tests** focus on:
- Specific configuration examples (desktop mode defaults, terminal mode defaults)
- Edge cases (empty messages, very long messages, special characters)
- Error conditions (handler failures, client disconnections, stream write failures)
- Integration points (LogCapture to LogRecord conversion, handler registration)

**Property-Based Tests** focus on:
- Universal routing behavior across all configurations
- Thread safety under concurrent access
- Message formatting consistency across all inputs
- Handler isolation under failure conditions
- Level filtering across all loggers and levels

### Property-Based Testing Configuration

**Framework**: Use Python's `hypothesis` library for property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: `# Feature: logging-system-refactor, Property N: <property text>`
- Use custom strategies for generating:
  - Log messages (various lengths, special characters, unicode)
  - Log levels (DEBUG through CRITICAL)
  - Configuration combinations (all permutations of enabled/disabled flags)
  - Thread counts (1-10 concurrent threads)
  - Client counts (0-5 connected clients)

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

@given(
    message=st.text(min_size=1, max_size=1000),
    level=st.sampled_from([logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]),
    log_pane_enabled=st.booleans(),
    stream_enabled=st.booleans(),
    remote_enabled=st.booleans()
)
def test_message_routing_property(message, level, log_pane_enabled, stream_enabled, remote_enabled):
    """
    Feature: logging-system-refactor, Property 3: Message routing to configured destinations
    
    For any log message and configuration, emitting the message should result in it 
    appearing in exactly the destinations enabled in the configuration.
    """
    # Test implementation
    pass
```

### Testing Priorities

1. **Critical Path**: Message routing, handler configuration, thread safety
2. **High Priority**: Error handling, backward compatibility, configuration management
3. **Medium Priority**: Performance optimizations, message formatting
4. **Low Priority**: Edge cases in display rendering

### Integration Testing

Integration tests verify end-to-end flows:
- Logger creation → message emission → display in log pane
- stdout write → LogCapture → handler pipeline → multiple destinations
- Configuration change → handler reconfiguration → behavior change
- Remote client connection → message broadcast → client reception

### Migration Testing

During migration, verify:
- Old code using `add_message()` continues working
- New code using `getLogger()` works correctly
- Both methods can coexist in the same application
- No performance regression compared to old system
