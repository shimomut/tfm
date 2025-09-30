# Remote Log Monitoring Implementation

## Overview

The Remote Log Monitoring feature allows monitoring TFM log messages from other terminals or remote machines. This document covers the implementation details for developers.

## Architecture

### Server Side (LogManager)

The `LogManager` class has been extended with:

- **TCP Server**: Listens for client connections on specified port
- **Client Management**: Tracks connected clients and handles disconnections
- **Message Broadcasting**: Sends log messages to all connected clients
- **Thread Safety**: Uses threading for non-blocking client handling

### Client Side (tools/tfm_log_client.py)

The client application provides:

- **Connection Management**: Handles connection and reconnection
- **Message Parsing**: Parses JSON log messages
- **Color Output**: Displays messages with appropriate colors
- **Graceful Exit**: Handles Ctrl+C and connection errors

### Key Components

1. **LogCapture Enhancement**: Modified to support remote callback
2. **LogManager Extension**: Added TCP server and client management
3. **Command Line Integration**: Added `--remote-log-port` option
4. **Client Application**: Standalone script for monitoring

## Message Format

Log messages are sent as JSON objects with the following structure:

```json
{
    "timestamp": "12:34:56",
    "source": "STDOUT",
    "message": "File operation completed"
}
```

### Log Sources

Different types of log messages have different sources:

- **SYSTEM**: System messages (startup, version info)
- **CONFIG**: Configuration-related messages
- **STDOUT**: Standard output from operations
- **STDERR**: Error output from operations
- **ERROR**: Error messages
- **REMOTE**: Remote monitoring system messages

## Color Coding Implementation

The client displays different log sources in different colors:

- **SYSTEM**: Green - System messages
- **CONFIG**: Blue - Configuration messages
- **STDOUT**: White - Standard output
- **STDERR**: Red - Error output
- **ERROR**: Red - Error messages
- **REMOTE**: Magenta - Remote monitoring messages

## Security Implementation

- The log server binds to `localhost` by default for security
- No authentication is implemented - anyone who can connect to the port can view logs
- Consider firewall rules if running on a network-accessible machine
- Log messages may contain sensitive file paths or system information

## Implementation Details

### Server Implementation

```python
# TCP Server setup in LogManager
self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
self.server_socket.bind(('localhost', port))
self.server_socket.listen(5)
```

### Client Management

```python
# Client tracking
self.clients = []
self.client_lock = threading.Lock()

# Message broadcasting
def broadcast_message(self, message):
    with self.client_lock:
        for client in self.clients[:]:  # Copy list to avoid modification during iteration
            try:
                client.send(json.dumps(message).encode() + b'\n')
            except:
                self.clients.remove(client)
```

### Thread Safety

- Uses threading locks for client list management
- Non-blocking client handling to prevent TFM freezing
- Graceful client disconnection handling

## Testing

### Demo Script

A demo script is provided to test the functionality:

```bash
# Terminal 1: Start demo server
python demo/demo_remote_log.py

# Terminal 2: Connect client
python tools/tfm_log_client.py localhost 8888
```

### Test Suite

Run the test suite to verify functionality:

```bash
python test/test_remote_log_monitoring.py
```

## Performance Impact

The remote log monitoring feature has minimal performance impact:

- **Memory**: Small overhead for client connection tracking
- **CPU**: Minimal threading overhead for client handling
- **Network**: Only active when clients are connected
- **Disk**: No additional disk I/O

## Configuration Options

The remote log monitoring feature uses these configuration options:

- **Port**: Specified via `--remote-log-port` command line option
- **Host**: Currently hardcoded to `localhost` for security
- **Buffer Size**: Uses system defaults for socket buffers
- **Client Timeout**: 30-second ping interval to detect disconnections

## Future Enhancements

Potential improvements for future versions:

- **Authentication**: Add password or key-based authentication
- **SSL/TLS**: Encrypt connections for secure remote monitoring
- **Filtering**: Allow clients to filter messages by source or pattern
- **Log History**: Send recent log history to new clients
- **Web Interface**: HTML/JavaScript client for browser-based monitoring
- **Log Persistence**: Save logs to file while streaming
- **Compression**: Compress messages for high-volume scenarios

## Compatibility

- **Python Version**: Requires Python 3.9+
- **Operating System**: Works on Linux, macOS, and Windows
- **Network**: Standard TCP sockets, no special requirements
- **Dependencies**: Uses only Python standard library

## Error Handling

### Connection Issues

```python
try:
    client_socket.send(data)
except ConnectionError:
    print("Connection lost to remote client")
    self.remove_client(client_socket)
except OSError as e:
    print(f"Network error: {e}")
```

### Client Disconnection

- Automatic detection of disconnected clients
- Graceful removal from client list
- No impact on TFM operation when clients disconnect

## Integration Points

### LogManager Integration

```python
# Add remote callback to LogCapture
if self.remote_log_port:
    self.log_capture = LogCapture(
        callback=self.add_message,
        remote_callback=self.broadcast_to_clients
    )
```

### Command Line Integration

```python
# Add argument parser option
parser.add_argument(
    '--remote-log-port',
    type=int,
    help='Enable remote log monitoring on specified port'
)
```