# Entry Point Consistency Fix

## Problem

The macOS app bundle was using a different entry point (`create_window()`) than the command-line version (`cli_main()`), causing inconsistent behavior between the two modes.

### Entry Point Comparison

**Command-line version (`tfm.py`):**
```python
def main():
    from tfm_main import cli_main
    cli_main()  # ← Uses cli_main()
```

**macOS app bundle (before fix):**
```objective-c
PyObject *createWindowFunc = PyObject_GetAttrString(tfmModule, "create_window");
PyObject *result = PyObject_CallObject(createWindowFunc, NULL);  // ← Used create_window()
```

### Behavioral Differences

**`cli_main()` (correct):**
1. Parses command-line arguments
2. Uses `select_backend()` to choose backend based on args
3. Handles backend options properly (font names, size, etc.)
4. Sets `ESCDELAY` environment variable
5. Handles profiling targets
6. Proper error handling with debug mode

**`create_window()` (incorrect):**
1. No argument parsing
2. Hardcodes CoreGraphics backend initialization
3. Hardcodes backend options (font, size, etc.)
4. Doesn't set `ESCDELAY`
5. No profiling support
6. Limited error handling

## Solution

Changed the Objective-C launcher to call `cli_main()` instead of `create_window()`, and simulate `--desktop` mode by setting `sys.argv`.

### Code Changes

**Before:**
```objective-c
// Get create_window function
PyObject *createWindowFunc = PyObject_GetAttrString(tfmModule, "create_window");

// Call create_window()
PyObject *result = PyObject_CallObject(createWindowFunc, NULL);
```

**After:**
```objective-c
// Get cli_main function
PyObject *cliMainFunc = PyObject_GetAttrString(tfmModule, "cli_main");

// Set up sys.argv to simulate --desktop mode
PyRun_SimpleString("import sys");
PyRun_SimpleString("sys.argv = ['TFM', '--desktop']");

// Call cli_main()
PyObject *result = PyObject_CallObject(cliMainFunc, NULL);
```

## Benefits

### 1. Consistent Behavior
- macOS app now behaves identically to `python3 tfm.py --desktop`
- Same backend initialization logic
- Same configuration handling
- Same error handling

### 2. Proper Backend Selection
- Uses `select_backend()` which checks configuration
- Respects user preferences from config file
- Handles backend options correctly

### 3. Complete Feature Support
- Profiling support (if needed in future)
- Debug mode support
- All command-line features available

### 4. Maintainability
- Single code path for both modes
- Changes to `cli_main()` automatically apply to app bundle
- No need to maintain separate `create_window()` function

## Implementation Details

### sys.argv Simulation

The Objective-C launcher sets `sys.argv` to simulate command-line arguments:

```objective-c
PyRun_SimpleString("sys.argv = ['TFM', '--desktop']");
```

This makes `cli_main()` think it was invoked with:
```bash
python3 tfm.py --desktop
```

### Backend Selection

With `--desktop` flag, `select_backend()` in `tfm_backend_selector.py`:
1. Checks if `--desktop` flag is present
2. Selects CoreGraphics backend
3. Returns appropriate backend options

### Argument Parsing

`cli_main()` uses `argparse` to parse `sys.argv`:
```python
parser = create_parser()
args = parser.parse_args()  # Parses sys.argv
```

With `sys.argv = ['TFM', '--desktop']`, this results in:
- `args.desktop = True`
- `args.left = None`
- `args.right = None`
- `args.profile = None`
- etc.

## Testing

### Verification Steps

1. **Build app:**
   ```bash
   cd macos_app && ./build.sh
   ```

2. **Launch app:**
   ```bash
   open build/TFM.app
   ```

3. **Verify process running:**
   ```bash
   ps aux | grep TFM.app
   ```

4. **Compare with command-line:**
   ```bash
   python3 tfm.py --desktop
   ```

Both should behave identically.

### Expected Behavior

- ✅ Window opens with CoreGraphics backend
- ✅ Same font and size as command-line `--desktop` mode
- ✅ Same keyboard shortcuts
- ✅ Same menu bar (in desktop mode)
- ✅ Same error handling
- ✅ Same logging behavior

## Future Considerations

### Additional Arguments

If you want to pass additional arguments to the app bundle, modify the `sys.argv` setup:

```objective-c
// Example: Add profiling
PyRun_SimpleString("sys.argv = ['TFM', '--desktop', '--profile', 'rendering']");

// Example: Set initial directories
PyRun_SimpleString("sys.argv = ['TFM', '--desktop', '--left', '/Users/username/Documents']");
```

### Configuration File

The app bundle now respects the TFM configuration file (`~/.tfm/config.py`), just like the command-line version. Users can customize:
- Backend preferences
- Font settings
- Color schemes
- Key bindings
- etc.

### Deprecating create_window()

The `create_window()` function in `tfm_main.py` is now unused and can be removed in a future cleanup:

```python
# This function is no longer needed
def create_window():
    # ... (can be removed)
```

## Related Files

- `macos_app/src/TFMAppDelegate.m` - Objective-C launcher (modified)
- `src/tfm_main.py` - Contains both `cli_main()` and `create_window()`
- `src/tfm_backend_selector.py` - Backend selection logic
- `tfm.py` - Command-line wrapper that calls `cli_main()`

## References

- Python/C API: https://docs.python.org/3/c-api/
- PyRun_SimpleString: https://docs.python.org/3/c-api/veryhigh.html#c.PyRun_SimpleString
- PyObject_GetAttrString: https://docs.python.org/3/c-api/object.html#c.PyObject_GetAttrString
- PyObject_CallObject: https://docs.python.org/3/c-api/call.html#c.PyObject_CallObject

---

**Fix implemented: December 27, 2024**
**Status: Verified working**
**Result: Consistent behavior between command-line and app bundle**
