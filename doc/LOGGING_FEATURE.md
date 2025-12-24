# Logging Feature

## Overview

TFM provides comprehensive logging functionality that captures application output, error messages, and operational information in a dedicated log pane. The logging system helps you monitor TFM's operations, troubleshoot issues, and understand what the application is doing.

## Features

### Log Pane Display

The log pane appears at the bottom of the TFM interface and displays:

- **Application Messages**: Information about file operations, searches, and other activities
- **Program Output**: Output from external programs and scripts
- **Error Messages**: Warnings and errors that occur during operations
- **Debug Information**: Detailed diagnostic information (when enabled)

### Message Types

Messages are color-coded by type:

- **Information** (white/normal): General operational messages
- **Warnings** (yellow): Warnings about potential issues
- **Errors** (red): Error messages for failed operations
- **Debug** (dim): Detailed diagnostic information
- **Program Output** (cyan): Output from external programs
- **Error Output** (magenta): Error output from external programs

### Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              Main TFM Interface                             │
│              (File Browser)                                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Log Messages:                                               │
│ 14:23:45 [Main] INFO: TFM started                          │
│ 14:23:46 [FileOp] INFO: Copying file.txt to backup/        │
│ 14:23:47 [FileOp] INFO: Copy completed successfully        │
│ 14:23:48 [STDOUT] Processing complete                      │
└─────────────────────────────────────────────────────────────┘
```

## Navigation

### Scrolling Through Logs

Use keyboard shortcuts to navigate through log history:

- **Shift+↑**: Scroll up one line
- **Shift+↓**: Scroll down one line
- **Shift+Page Up**: Scroll up one page
- **Shift+Page Down**: Scroll down one page
- **Shift+Home**: Jump to top of log (oldest messages)
- **Shift+End**: Jump to bottom of log (newest messages)

### Auto-Scroll Behavior

- New messages automatically appear at the bottom
- Log automatically scrolls to show new messages
- Manual scrolling temporarily disables auto-scroll
- Pressing Shift+End re-enables auto-scroll

## Common Use Cases

### Monitoring File Operations

Watch file operations in real-time:

```
14:23:45 [FileOp] INFO: Copying file1.txt to backup/
14:23:46 [FileOp] INFO: Copy completed successfully
14:23:46 [FileOp] INFO: Copying file2.txt to backup/
14:23:47 [FileOp] INFO: Copy completed successfully
```

### Troubleshooting Errors

Identify and understand errors:

```
14:23:45 [FileOp] INFO: Copying protected.txt to backup/
14:23:46 [FileOp] ERROR: Permission denied
```

### Viewing Program Output

See output from external programs:

```
14:23:45 [Main] INFO: Running external script
14:23:46 [STDOUT] Processing file 1 of 10
14:23:47 [STDOUT] Processing file 2 of 10
14:23:48 [STDOUT] Processing complete
```

### Tracking Progress

Monitor long-running operations:

```
14:23:45 [Archive] INFO: Extracting archive.zip
14:23:46 [Archive] INFO: Extracted 100 of 500 files
14:23:47 [Archive] INFO: Extracted 200 of 500 files
14:23:48 [Archive] INFO: Extracted 300 of 500 files
14:23:49 [Archive] INFO: Extraction completed
```

## Configuration

### Log Pane Size

The log pane size is configurable:

- Default: 25% of screen height
- Adjustable in configuration file
- Minimum: 3 lines
- Maximum: 50% of screen height

### Message Retention

TFM retains a configurable number of log messages:

- Default: 1000 messages
- Older messages are automatically removed
- Configurable in settings
- Prevents memory issues with long-running sessions

### Log Levels

Control the verbosity of logging:

- **INFO** (default): General operational messages
- **WARNING**: Warnings and errors only
- **DEBUG**: Detailed diagnostic information
- **ERROR**: Errors only

Set log level in configuration:

```python
# In config file
LOG_LEVEL = "INFO"  # or "WARNING", "DEBUG", "ERROR"
```

## Remote Monitoring

### Overview

TFM supports remote log monitoring, allowing you to view logs from another terminal or machine.

### Enabling Remote Monitoring

Enable in configuration:

```python
# In config file
REMOTE_MONITORING_ENABLED = True
REMOTE_MONITORING_PORT = 9999
```

### Connecting to Remote Logs

From another terminal:

```bash
# Using telnet
telnet localhost 9999

# Using netcat
nc localhost 9999
```

### Remote Log Format

Logs are sent as JSON:

```json
{
    "timestamp": "14:23:45",
    "source": "FileOp",
    "level": "INFO",
    "message": "File operation completed"
}
```

## Tips and Tricks

### Finding Recent Errors

1. Press **Shift+End** to jump to bottom
2. Press **Shift+↑** to scroll up
3. Look for red error messages

### Reviewing Operation History

1. Press **Shift+Home** to jump to top
2. Press **Shift+Page Down** to scroll through history
3. Review messages chronologically

### Monitoring Long Operations

1. Keep log pane visible during operations
2. Watch for progress messages
3. Check for errors or warnings
4. Verify completion messages

### Debugging Issues

1. Enable DEBUG log level for detailed information
2. Reproduce the issue
3. Review log messages for clues
4. Look for error messages and warnings

## Troubleshooting

### Log Pane Not Visible

**Problem:** Log pane doesn't appear.

**Solution:** Check configuration:
- Verify `LOG_PANE_ENABLED = True` in config
- Check screen height is sufficient
- Try resizing terminal window

### Messages Scrolling Too Fast

**Problem:** New messages scroll by too quickly.

**Solution:** 
- Use **Shift+↑** to scroll up and review
- Press **Shift+Home** to jump to top
- Consider reducing log level to WARNING

### Too Many Messages

**Problem:** Log pane fills with too many messages.

**Solution:**
- Increase `MAX_LOG_MESSAGES` in config (default: 1000)
- Set higher log level (WARNING or ERROR)
- Clear old messages by restarting TFM

### Remote Monitoring Not Working

**Problem:** Cannot connect to remote monitoring.

**Solution:**
- Verify `REMOTE_MONITORING_ENABLED = True`
- Check port is not in use: `netstat -an | grep 9999`
- Verify firewall allows connections
- Try different port number

## Benefits

### For Users

- **Immediate Feedback**: See what TFM is doing in real-time
- **Error Visibility**: Quickly identify and understand errors
- **Operation History**: Review recent actions and results
- **Progress Tracking**: Monitor long-running operations

### For Troubleshooting

- **Error Diagnosis**: Detailed error messages help identify issues
- **Operation Tracking**: See exactly what operations were performed
- **Debug Information**: Detailed diagnostic data when needed
- **Remote Monitoring**: View logs from another terminal

### For Developers

- **Easy Debugging**: Centralized location for debug output
- **Error Tracking**: Comprehensive error logging
- **Progress Feedback**: Easy to add progress messages
- **Flexible Output**: Support for different message types

## Advanced Features

### Message Timestamps

All messages include timestamps:

```
14:23:45 [FileOp] INFO: Operation started
14:23:46 [FileOp] INFO: Operation completed
```

Format: `HH:MM:SS` (24-hour format)

### Source Identification

Messages show their source:

- **[Main]**: Main application
- **[FileOp]**: File operations
- **[DirDiff]**: Directory diff viewer
- **[Archive]**: Archive operations
- **[STDOUT]**: Program output
- **[STDERR]**: Error output

### Multi-line Messages

Multi-line output is preserved:

```
14:23:45 [STDOUT] Processing file: example.txt
14:23:45 [STDOUT] Size: 1024 bytes
14:23:45 [STDOUT] Modified: 2024-01-15
```

### Color Coding

Messages are color-coded for easy identification:

- Normal messages: White/default color
- Warnings: Yellow
- Errors: Red
- Debug: Dim/gray
- Program output: Cyan
- Error output: Magenta

## Best Practices

### Regular Monitoring

- Keep log pane visible during operations
- Check for errors after operations
- Review warnings for potential issues

### Log Level Selection

- Use INFO for normal operations
- Use WARNING to reduce verbosity
- Use DEBUG for troubleshooting
- Use ERROR for critical issues only

### Remote Monitoring

- Enable for debugging complex issues
- Use for monitoring background operations
- Disable when not needed (security)

### Message Review

- Review logs after errors
- Check for warnings before operations
- Monitor progress during long operations

## Conclusion

TFM's logging feature provides comprehensive visibility into application operations, helping you monitor activity, troubleshoot issues, and understand what the application is doing. The color-coded, scrollable log pane makes it easy to track operations and identify problems quickly.

For developer documentation, see `doc/dev/LOGGING_SYSTEM_REFACTOR_GUIDE.md`.
