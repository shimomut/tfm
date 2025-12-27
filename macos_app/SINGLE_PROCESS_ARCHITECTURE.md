# Single-Process Architecture for TFM macOS App

## Overview

The TFM macOS application uses a **single-process, single-window architecture**. This is the simplest approach that ensures a clean user experience with a single Dock icon.

## Architecture

```
TFM.app Process
├── NSApplication (manages Dock icon, menu bar, window)
├── Python interpreter (embedded)
├── TFM code (tfm_main.cli_main())
└── Single window (CoreGraphics-based TUI)
```

## Key Concepts

### 1. Single Process
- **Role**: Runs the entire application
- **Behavior**: 
  - Launches on app startup
  - Initializes Python interpreter
  - Calls `cli_main()` to create TFM window
  - Terminates when window closes

### 2. Single Window
- **Role**: Displays the TFM terminal interface
- **Behavior**:
  - Created by TFM's CoreGraphics backend
  - Runs in the same process as NSApplication
  - Closes when user quits (Cmd+Q or closes window)

### 3. Single Dock Icon
- **Result**: Clean user experience
- **Behavior**:
  - One process = one Dock icon
  - No subprocess management needed
  - No activation policy configuration needed

## Implementation Details

### Application Launch Flow

```objective-c
- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    // Initialize Python interpreter
    [self initializePython];
    
    // Launch TFM window in current process
    [self launchTFMWindow];
}
```

### Window Launch

```objective-c
- (void)launchTFMWindow {
    // Import tfm_main and call cli_main()
    PyObject *tfmModule = PyImport_ImportModule("tfm_main");
    PyObject *cliMainFunc = PyObject_GetAttrString(tfmModule, "cli_main");
    
    // Set sys.argv for --desktop mode
    PyRun_SimpleString("sys.argv = ['TFM', '--desktop']");
    
    // Call cli_main() - blocks until window closes
    PyObject *result = PyObject_CallObject(cliMainFunc, NULL);
    
    // When cli_main() returns, terminate application
    [NSApp terminate:self];
}
```

### Application Termination

```objective-c
- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    // Single-window mode: terminate when window closes
    return YES;
}
```

## Benefits

### 1. Simplicity
- No subprocess management
- No inter-process communication
- No activation policy configuration
- Straightforward code flow

### 2. Clean User Experience
- Single Dock icon (as expected)
- Single entry in Cmd+Tab switcher
- Consistent with most terminal applications
- No confusion about multiple processes

### 3. Resource Efficiency
- Single Python interpreter (~100-150 MB)
- No overhead from multiple processes
- Faster startup (no subprocess spawning)

### 4. Reliability
- No subprocess coordination issues
- No risk of orphaned processes
- Simpler error handling

## Comparison with Multi-Process Approach

| Aspect | Single-Process | Multi-Process |
|--------|----------------|---------------|
| Dock Icons | 1 (clean) | Multiple (confusing) |
| Complexity | Simple | Complex |
| Memory | ~150 MB | ~150 MB per window |
| Windows | 1 | Multiple |
| Isolation | N/A | Complete |
| User Experience | Standard | Non-standard |

## Process Lifecycle

### Application Launch
1. User double-clicks TFM.app
2. Process starts
3. `applicationDidFinishLaunching` called
4. Python interpreter initialized
5. `cli_main()` called
6. Window appears

### Application Quit
1. User closes window (Cmd+W or red button) OR quits (Cmd+Q)
2. `cli_main()` event loop detects quit signal
3. `cli_main()` returns
4. Application calls `[NSApp terminate:self]`
5. Python interpreter finalized
6. Process exits

## Multi-Window Support

### Current Status
The macOS app supports **single-window only**.

### Why Not Multi-Window?

The multi-process approach (one process per window) was attempted but resulted in multiple Dock icons because:
1. Each process creates its own NSApplication instance
2. TFM's CoreGraphics backend also creates NSApplication
3. macOS shows a Dock icon for each process
4. No way to share NSApplication across processes

### Future Multi-Window Support

To add multi-window support in the future, TFM's Python code would need modifications:
1. Make state management thread-safe
2. Support multiple windows in single Python interpreter
3. Coordinate window lifecycle properly

This is a significant undertaking and not currently planned.

### Workaround for Multiple Windows

Users who need multiple TFM windows can:
1. Open multiple instances of TFM.app
2. Each instance runs independently
3. Each instance has its own Dock icon (expected behavior)

## Performance Considerations

### Memory Usage
- Single process: ~100-150 MB (Python interpreter + TFM code)
- Comparable to command-line TFM

### Startup Time
- ~0.5-1.0 seconds (Python initialization + window creation)
- Faster than multi-process approach (no subprocess spawning)

### CPU Usage
- Idle: Minimal (event-driven)
- Active: One CPU core (file operations, rendering)

## Debugging

### Viewing Process
```bash
# List TFM process
ps aux | grep TFM.app | grep -v grep

# Expected output:
# Single process: /path/to/TFM.app/Contents/MacOS/TFM
```

### Console Logs
Process logs to Console.app:
```
"Launching TFM in single-process mode"
"Python initialized successfully"
"Calling cli_main()"
"cli_main() returned, terminating application"
```

## Related Files

- `macos_app/src/TFMAppDelegate.m` - Main implementation
- `macos_app/src/TFMAppDelegate.h` - Interface definition
- `src/tfm_main.py` - Contains `cli_main()` entry point
- `macos_app/ENTRY_POINT_FIX.md` - Entry point consistency documentation

## References

- NSApplication: https://developer.apple.com/documentation/appkit/nsapplication
- Python/C API: https://docs.python.org/3/c-api/
- macOS App Bundle: https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/

---

**Architecture implemented: December 27, 2024**
**Status: Active**
**Result: Simple, clean, single Dock icon**

