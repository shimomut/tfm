# Debug Mode Implementation

## Overview

TFM's debug mode (`--debug` flag) enables dual output for stdout/stderr: messages are captured in the log pane (normal behavior) AND printed to the actual terminal (debug behavior). This is useful for debugging issues where you need to see output in real-time without switching to the log pane.

## Implementation Details

### Architecture

The debug mode is implemented through three main components:

1. **Command-line flag parsing** (`src/tfm_main.py`)
   - `--debug` flag sets `TFM_DEBUG=1` environment variable
   - Environment variable is checked when initializing LogManager

2. **LogCapture class** (`src/tfm_log_manager.py`)
   - Modified to accept `debug_mode` and `original_stream` parameters
   - In debug mode, writes to both log pane and original stream
   - Preserves all output including newlines for proper formatting

3. **LogManager class** (`src/tfm_log_manager.py`)
   - Accepts `debug_mode` parameter in constructor
   - Passes debug mode flag to LogCapture instances
   - Stores original stdout/stderr for debug output

### Code Flow

```
User runs: tfm.py --debug
    ↓
cli_main() sets TFM_DEBUG=1 environment variable
    ↓
FileManager.__init__() checks TFM_DEBUG
    ↓
LogManager(debug_mode=True) creates LogCapture with debug mode
    ↓
LogCapture.write() writes to BOTH:
    - log_messages (for log pane display)
    - original_stream (for terminal output)
```

### Key Implementation Details

#### LogCapture.write() Method

```python
def write(self, text):
    # In debug mode, always write to original stream first
    # This preserves all output including newlines
    if self.debug_mode and self.original_stream:
        try:
            self.original_stream.write(text)
            self.original_stream.flush()
        except (OSError, IOError):
            pass  # Ignore errors writing to original stream
    
    # Only log non-empty messages to the log pane
    if text.strip():
        timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
        log_entry = (timestamp, self.source, text.strip())
        self.log_messages.append(log_entry)
        # ... (update callbacks, remote clients)
```

**Important design decisions:**

1. **Write to original stream FIRST**: Ensures debug output appears immediately, even if log capture fails
2. **Always write in debug mode**: Preserves formatting (newlines, spaces) in terminal output
3. **Only log non-empty**: Prevents log pane from filling with blank entries
4. **Flush immediately**: Ensures output appears in real-time

#### Error Handling

All writes to the original stream are wrapped in try-except blocks to handle:
- `OSError`: Terminal closed or unavailable
- `IOError`: I/O errors during write

Errors are silently ignored to prevent debug mode from breaking normal operation.

## Usage

### Running TFM with Debug Mode

```bash
# Enable debug mode
python3 tfm.py --debug

# Debug mode with other options
python3 tfm.py --debug --left /path/to/dir --right /path/to/other
```

### What Debug Mode Does

**Normal mode (without --debug):**
- stdout/stderr captured in log pane only
- Terminal shows no output (clean UI)
- Stack traces only shown for uncaught exceptions

**Debug mode (with --debug):**
- stdout/stderr captured in log pane AND printed to terminal
- Terminal shows all output in real-time
- Full stack traces for uncaught exceptions
- Useful for debugging issues

### Example Output

```bash
$ python3 tfm.py --debug
Loaded configuration from: /Users/user/.tfm/config.py
TFM 1.0.0
GitHub: https://github.com/user/tfm
TFM started successfully
Configuration loaded
# ... (TFM UI appears, but debug output continues in terminal)
```

## Testing

### Unit Test

Run the debug mode unit test:

```bash
python3 temp/test_debug_mode.py
```

This test verifies:
1. Normal mode captures output in log only
2. Debug mode captures output in log AND prints to terminal
3. Both stdout and stderr are handled correctly

### Manual Testing

1. Run TFM with `--debug` flag
2. Trigger some stdout/stderr output (e.g., file operations, errors)
3. Verify output appears in both:
   - Terminal (where you ran TFM)
   - Log pane (F12 to view)

## Benefits

1. **Real-time debugging**: See output immediately without switching to log pane
2. **Stack traces**: Full exception details in terminal for easier debugging
3. **Development workflow**: Easier to debug issues during development
4. **No UI interference**: Debug output doesn't affect TFM's UI rendering

## Limitations

1. **Terminal clutter**: Debug output can clutter the terminal
2. **Not for production**: Debug mode is intended for development/debugging only
3. **Performance**: Slight overhead from dual output (negligible in practice)

## Related Files

- `src/tfm_main.py`: Command-line argument parsing, debug flag handling
- `src/tfm_log_manager.py`: LogManager and LogCapture implementation
- `temp/test_debug_mode.py`: Unit test for debug mode functionality
- `doc/dev/DEBUG_MODE_IMPLEMENTATION.md`: This documentation file

## Future Enhancements

Potential improvements for debug mode:

1. **Selective debug output**: Filter by source (STDOUT, STDERR, SYSTEM, etc.)
2. **Debug levels**: Different verbosity levels (INFO, DEBUG, TRACE)
3. **Log file output**: Write debug output to file instead of terminal
4. **Timestamp control**: Option to include/exclude timestamps in terminal output
