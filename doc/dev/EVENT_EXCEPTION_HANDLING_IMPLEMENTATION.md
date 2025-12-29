# Event Exception Handling Implementation

## Overview

TFM now catches exceptions in event handlers to prevent application shutdown when errors occur during event processing. This makes TFM more robust and user-friendly by logging errors instead of crashing.

## Implementation Details

### Exception Handling Locations

Exception handling is implemented in the `TFMEventCallback` class in `src/tfm_main.py`, which serves as the bridge between the TTK backend and TFM's event processing logic.

### Protected Event Types

The following event handlers now have exception protection:

1. **Key Events** (`on_key_event`)
   - Handles keyboard input including shortcuts and navigation
   - Catches exceptions from global shortcuts and UI layer stack processing

2. **Character Events** (`on_char_event`)
   - Handles text input for dialogs and input fields
   - Catches exceptions from character processing in UI layers

3. **Menu Events** (`on_menu_event`)
   - Handles menu selections in desktop mode
   - Catches exceptions from menu action handlers

### Debug Mode Support

When TFM is run with the `--debug` flag, exception handling provides detailed stack traces to stderr:

- **Without `--debug`**: Logs error message only to TFM log
  ```
  Error handling key event: ValueError: Test error
  ```

- **With `--debug`**: Logs error message to TFM log and prints full stack trace to stderr
  ```
  # In TFM log:
  Error handling key event: ValueError: Test error
  
  # On stderr:
  Traceback (most recent call last):
    File "src/tfm_main.py", line 120, in on_key_event
      return self.file_manager.ui_layer_stack.handle_key_event(event)
    ...
  ValueError: Test error
  ```

### Debug Flag Detection

The debug flag is stored in the environment variable `TFM_DEBUG`:
- Set to `'1'` when `--debug` flag is provided
- Checked using `os.environ.get('TFM_DEBUG') == '1'`
- Available to all modules without passing through constructors

## Code Structure

### Exception Handling Pattern

```python
def on_key_event(self, event: KeyEvent) -> bool:
    try:
        # Mark activity for adaptive FPS
        self.file_manager.adaptive_fps.mark_activity()
        
        # Handle global shortcuts...
        # Route to UI layer stack...
        return self.file_manager.ui_layer_stack.handle_key_event(event)
    except Exception as e:
        # Log error message
        self.file_manager.logger.error(f"Error handling key event: {e}")
        # Print stack trace to stderr if debug mode is enabled
        if os.environ.get('TFM_DEBUG') == '1':
            traceback.print_exc(file=sys.stderr)
        return True  # Event consumed to prevent further issues
```

### Key Design Decisions

1. **Return True on Exception**: When an exception is caught, the handler returns `True` to indicate the event was consumed. This prevents the event from propagating further and potentially causing additional issues.

2. **Log Level**: Exceptions are logged at ERROR level since they represent unexpected failures in event processing.

3. **Separate Error Message and Traceback**: Error messages are logged through TFM's logging system, while stack traces are printed to stderr in debug mode. This keeps the log clean while still providing detailed debugging information when needed.

4. **No Re-raise**: Exceptions are not re-raised after logging, ensuring TFM continues running even when event handlers fail.

5. **Preserve Activity Marking**: The `adaptive_fps.mark_activity()` call is inside the try block to ensure it's always attempted, but exceptions from it are also caught.

## Testing

### Test Coverage

The implementation includes comprehensive tests in `test/test_event_exception_handling.py`:

- Exception handling without debug mode (3 tests) - verifies error messages are logged
- Exception handling with debug mode (3 tests) - verifies stack traces are printed to stderr
- Normal operation without exceptions (3 tests) - verifies no errors are logged

All tests verify:
- Exceptions don't crash TFM
- Errors are logged appropriately
- Stack traces are printed to stderr only in debug mode
- Normal operations continue to work correctly

### Running Tests

```bash
PYTHONPATH=.:src:ttk python -m pytest test/test_event_exception_handling.py -v
```

## Benefits

1. **Improved Stability**: TFM no longer crashes when event handlers encounter unexpected errors
2. **Better Debugging**: Debug mode provides detailed stack traces for troubleshooting
3. **User Experience**: Users can continue working even if an event handler fails
4. **Error Visibility**: All errors are logged for later analysis

## Future Enhancements

Potential improvements for future consideration:

1. **Error Recovery**: Implement automatic recovery strategies for specific error types
2. **Error Reporting**: Add option to automatically report errors to developers
3. **Error Statistics**: Track error frequency to identify problematic areas
4. **User Notifications**: Show non-intrusive notifications for errors in desktop mode

## Related Files

- `src/tfm_main.py` - TFMEventCallback implementation
- `test/test_event_exception_handling.py` - Test suite
- `ttk/input_event.py` - Event type definitions
- `src/tfm_log_manager.py` - Logging system
