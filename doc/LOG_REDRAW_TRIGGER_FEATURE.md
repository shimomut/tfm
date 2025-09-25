# Log Redraw Trigger Feature

## Overview

TFM now automatically detects when new log messages are added and triggers a redraw to immediately display the updated content. This provides real-time feedback for file operations, error messages, and system status updates without requiring manual refresh or user interaction.

## How It Works

### Update Detection Mechanism

The LogManager tracks log updates through several mechanisms:

1. **Message Count Tracking**: Monitors the total number of log messages
2. **Update Flag**: Sets a flag when new messages are added
3. **Callback System**: LogCapture notifies LogManager when messages are written

### Integration with Main Loop

The main application loop checks for log updates on every iteration:

```python
def run(self):
    """Main application loop"""
    while True:
        # Check for log updates and trigger redraw if needed
        if self.log_manager.has_log_updates():
            self.needs_full_redraw = True
        
        # Only do full redraw when needed
        if self.needs_full_redraw:
            # ... draw interface including updated log pane ...
            # Updates are automatically marked as processed in draw_log_pane()
```

## Implementation Details

### LogManager Enhancements

#### New Properties
- `has_new_messages`: Boolean flag indicating new messages since last check
- `last_message_count`: Tracks the number of messages at last redraw

#### New Methods
- `_on_message_added()`: Called when new messages are added
- `has_log_updates()`: Checks if redraw is needed due to log updates
- `mark_log_updates_processed()`: Marks updates as processed after redraw
- `add_message(source, message)`: Directly add messages to log with update notification

### LogCapture Enhancements

#### Update Callback
- Added `update_callback` parameter to constructor
- Calls callback when non-empty messages are written
- Integrates with stdout/stderr capture mechanism

```python
def write(self, text):
    if text.strip():  # Only log non-empty messages
        # ... add message to log ...
        
        # Notify about new message for redraw triggering
        if self.update_callback:
            self.update_callback()
```

### Main Loop Integration

#### Update Detection
```python
# Check for log updates and trigger redraw if needed
if self.log_manager.has_log_updates():
    self.needs_full_redraw = True
```

#### Automatic Update Processing
Updates are automatically marked as processed when `draw_log_pane()` is called:

```python
def draw_log_pane(self, stdscr, y_start, height, width):
    """Draw the log pane at the specified position"""
    try:
        # ... draw log content ...
    except Exception:
        pass  # Ignore drawing errors
    finally:
        # Always mark log updates as processed when draw_log_pane is called
        self.mark_log_updates_processed()
```

## Benefits

### Real-Time Feedback
- **File Operations**: Progress and completion messages appear immediately
- **Error Messages**: Errors are displayed as soon as they occur
- **System Status**: Configuration changes and system events are instantly visible
- **Remote Monitoring**: Remote log messages appear in real-time

### Improved User Experience
- **No Manual Refresh**: Users don't need to press keys to see log updates
- **Immediate Response**: Operations provide instant visual feedback
- **Live Status**: Current operation status is always visible
- **Responsive Interface**: Interface feels more responsive and interactive

### Efficient Performance
- **Selective Redraw**: Only redraws when log content actually changes
- **Minimal Overhead**: Update detection is lightweight and fast
- **No Polling**: Event-driven updates instead of continuous polling
- **Optimized Rendering**: Existing redraw mechanism is reused

## Use Cases

### File Operations
```python
# These operations now provide real-time feedback
print("Copying file: document.txt")
# User sees message immediately

print("Copy completed successfully")
# User sees completion status immediately
```

### Error Handling
```python
# Error messages appear instantly
print("Error: Permission denied", file=sys.stderr)
# User sees error immediately without waiting
```

### Progress Updates
```python
# Progress messages during long operations
for i, file in enumerate(files):
    print(f"Processing {i+1}/{len(files)}: {file}")
    # Each progress update triggers immediate redraw
```

### Remote Monitoring
```python
# Remote log messages appear in real-time
# when using --remote-log-port option
```

## Configuration

### No Configuration Required
- Feature is automatically enabled
- Works with existing log configuration
- No additional setup needed
- Compatible with all existing log sources

### Customization Options
- Uses existing `MAX_LOG_MESSAGES` configuration
- Works with existing color schemes
- Integrates with remote log monitoring
- Respects existing log formatting

## Testing

### Unit Tests
- `test/test_log_redraw_trigger.py` provides comprehensive test coverage
- Tests update detection, callback mechanisms, and state management
- Verifies integration with stdout/stderr capture
- Validates message counting and flag management

### Demo Script
- `demo/demo_log_redraw_trigger.py` demonstrates the feature in action
- Shows various types of log messages and their effects
- Explains the integration with the main loop
- Provides usage examples and benefits

## Backward Compatibility

### Fully Compatible
- No breaking changes to existing functionality
- Existing log behavior is preserved
- All existing log sources continue to work
- No changes required to existing code

### Enhanced Behavior
- Existing log messages now trigger automatic redraws
- stdout/stderr capture works as before but with immediate display
- Remote log monitoring benefits from real-time updates
- All log sources (direct, captured, remote) trigger updates

## Performance Considerations

### Minimal Impact
- Update detection is O(1) operation
- No additional memory overhead
- Reuses existing redraw mechanism
- No performance degradation observed

### Efficient Implementation
- Only redraws when content actually changes
- Lightweight flag-based detection
- No continuous polling or timers
- Event-driven architecture

## Future Enhancements

### Potential Improvements
- **Selective Redraw**: Only redraw log pane instead of full screen
- **Throttling**: Limit redraw frequency for high-volume logging
- **Filtering**: Option to disable redraw for certain log sources
- **Animation**: Smooth scrolling for new messages

### Integration Opportunities
- **Progress Bars**: Enhanced progress display with real-time updates
- **Status Indicators**: Live status updates in header/footer
- **Notification System**: Visual indicators for important messages
- **Log Levels**: Different redraw behavior based on message importance

## Troubleshooting

### Common Issues
- **High CPU Usage**: May occur with very frequent log messages
- **Screen Flicker**: Possible with rapid successive messages
- **Memory Usage**: Large log buffers may impact performance

### Solutions
- Monitor log message frequency
- Use appropriate `MAX_LOG_MESSAGES` setting
- Consider throttling for high-volume operations
- Test with realistic log loads

## Implementation Improvements

### Automatic Update Processing in draw_log_pane()

The implementation has been optimized to automatically mark log updates as processed when the log pane is drawn, rather than requiring manual calls in the main loop. This provides several benefits:

#### Benefits of draw_log_pane() Processing
- **Cleaner Code**: No need to remember to call `mark_log_updates_processed()` in main loop
- **Automatic Handling**: Updates are processed whenever the log pane is drawn
- **Exception Safety**: Uses `finally` block to ensure processing even if drawing fails
- **Consistency**: Updates are always processed when log content is rendered

#### Implementation Details
```python
def draw_log_pane(self, stdscr, y_start, height, width):
    """Draw the log pane at the specified position"""
    try:
        # ... draw log content ...
    except Exception:
        pass  # Ignore drawing errors
    finally:
        # Always mark log updates as processed when draw_log_pane is called
        # This ensures updates are marked as processed even if drawing fails
        self.mark_log_updates_processed()
```

This approach ensures that log updates are always properly processed whenever the log pane is rendered, making the system more robust and easier to maintain.

## Summary

The log redraw trigger feature significantly improves TFM's user experience by providing immediate visual feedback for all log activity. The implementation is efficient, backward-compatible, and integrates seamlessly with the existing architecture. The automatic update processing in `draw_log_pane()` makes the system robust and maintainable. Users now see real-time updates for file operations, error messages, and system status without any additional configuration or interaction required.