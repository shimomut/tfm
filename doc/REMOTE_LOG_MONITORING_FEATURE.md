# Remote Log Monitoring Feature

## Overview

The Remote Log Monitoring feature allows you to monitor TFM log messages from other terminals or even remote machines. This is useful for debugging, monitoring system activity, or keeping track of TFM operations while working in multiple terminals.

## Features

- **Real-time log streaming**: Log messages are sent to connected clients immediately
- **Multiple client support**: Multiple terminals can monitor the same TFM instance
- **Network capable**: Works locally and across networks
- **JSON message format**: Structured data for easy parsing
- **Automatic client management**: Handles client connections and disconnections gracefully
- **Color-coded output**: Different log sources are displayed in different colors

## Usage

### Starting TFM with Remote Log Monitoring

To enable remote log monitoring, start TFM with the `--remote-log-port` option:

```bash
# Start TFM with remote log monitoring on port 8888
python tfm.py --remote-log-port 8888

# Or use a different port
python tfm.py --remote-log-port 9999
```

When remote monitoring is enabled, you'll see a message in the log pane:
```
12:34:56 [REMOTE] Log server started on port 8888
```

### Connecting a Log Client

Use the provided client script to connect and monitor logs:

```bash
# Connect to local TFM instance
python tfm_log_client.py localhost 8888

# Connect to remote TFM instance
python tfm_log_client.py 192.168.1.100 8888

# Use default values (localhost:8888)
python tfm_log_client.py
```

### Client Options

The log client supports several options:

```bash
# Disable colored output
python tfm_log_client.py --no-color localhost 8888

# Show help
python tfm_log_client.py --help
```

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

## Color Coding

The client displays different log sources in different colors:

- **SYSTEM**: Green - System messages
- **CONFIG**: Blue - Configuration messages
- **STDOUT**: White - Standard output
- **STDERR**: Red - Error output
- **ERROR**: Red - Error messages
- **REMOTE**: Magenta - Remote monitoring messages

## Security Considerations

- The log server binds to `localhost` by default for security
- No authentication is implemented - anyone who can connect to the port can view logs
- Consider firewall rules if running on a network-accessible machine
- Log messages may contain sensitive file paths or system information

## Implementation Details

### Server Side (LogManager)

The `LogManager` class has been extended with:

- **TCP Server**: Listens for client connections on specified port
- **Client Management**: Tracks connected clients and handles disconnections
- **Message Broadcasting**: Sends log messages to all connected clients
- **Thread Safety**: Uses threading for non-blocking client handling

### Client Side (tfm_log_client.py)

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

## Examples

### Basic Usage

Terminal 1 (TFM):
```bash
python tfm.py --remote-log-port 8888
```

Terminal 2 (Client):
```bash
python tfm_log_client.py
```

### Multiple Clients

You can connect multiple clients to the same TFM instance:

Terminal 1 (TFM):
```bash
python tfm.py --remote-log-port 8888
```

Terminal 2 (Client 1):
```bash
python tfm_log_client.py localhost 8888
```

Terminal 3 (Client 2):
```bash
python tfm_log_client.py localhost 8888
```

### Remote Monitoring

If TFM is running on a server:

Server:
```bash
python tfm.py --remote-log-port 8888
```

Client machine:
```bash
python tfm_log_client.py server.example.com 8888
```

## Demo

A demo script is provided to test the functionality:

```bash
# Terminal 1: Start demo server
python demo_remote_log.py

# Terminal 2: Connect client
python tfm_log_client.py localhost 8888
```

## Testing

Run the test suite to verify functionality:

```bash
python test/test_remote_log_monitoring.py
```

## Troubleshooting

### Connection Refused

If you get "Connection refused" errors:

1. Make sure TFM is running with `--remote-log-port` option
2. Check that the port number matches
3. Verify no firewall is blocking the connection
4. Ensure the port isn't already in use

### No Log Messages

If the client connects but shows no messages:

1. Verify TFM is generating log output
2. Check that stdout/stderr redirection is working
3. Try performing operations in TFM to generate logs

### Client Disconnects

If clients disconnect unexpectedly:

1. Check network connectivity
2. Verify TFM is still running
3. Look for error messages in TFM log pane

## Future Enhancements

Potential improvements for future versions:

- **Authentication**: Add password or key-based authentication
- **SSL/TLS**: Encrypt connections for secure remote monitoring
- **Filtering**: Allow clients to filter messages by source or pattern
- **Log History**: Send recent log history to new clients
- **Web Interface**: HTML/JavaScript client for browser-based monitoring
- **Log Persistence**: Save logs to file while streaming
- **Compression**: Compress messages for high-volume scenarios

## Configuration

The remote log monitoring feature uses these configuration options:

- **Port**: Specified via `--remote-log-port` command line option
- **Host**: Currently hardcoded to `localhost` for security
- **Buffer Size**: Uses system defaults for socket buffers
- **Client Timeout**: 30-second ping interval to detect disconnections

## Performance Impact

The remote log monitoring feature has minimal performance impact:

- **Memory**: Small overhead for client connection tracking
- **CPU**: Minimal threading overhead for client handling
- **Network**: Only active when clients are connected
- **Disk**: No additional disk I/O

## Compatibility

- **Python Version**: Requires Python 3.6+
- **Operating System**: Works on Linux, macOS, and Windows
- **Network**: Standard TCP sockets, no special requirements
- **Dependencies**: Uses only Python standard library

## Conclusion

The Remote Log Monitoring feature provides a powerful way to monitor TFM operations from multiple terminals or remote locations. It's designed to be lightweight, secure (when used properly), and easy to use while providing real-time visibility into TFM's operation.