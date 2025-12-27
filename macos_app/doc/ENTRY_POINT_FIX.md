# Entry Point Consistency and Multi-Process Architecture

## Problem

The macOS app bundle was initially designed to use a different entry point (`create_window()`) than the command-line version (`cli_main()`). This was changed to use `cli_main()` for both to ensure consistent behavior.

Additionally, `cli_main()` is a blocking function that runs an event loop. Using threading within a single Python interpreter would cause issues with TFM's state management, which wasn't designed for multi-window scenarios.

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

### State Management Issue

TFM's Python code wasn't designed for multiple windows within a single process:
- Shared global state
- No thread synchronization
- Single FileManager instance assumptions
- Configuration loaded once at startup

**Problem with threading**: Multiple threads sharing one Python interpreter would require:
1. Thread-safe state management throughout TFM
2. Synchronization primitives (locks, conditions)
3. Careful handling of shared resources
4. Significant code refactoring

## Solution: Multi-Process Architecture

Changed the architecture to use **one process per window**:
1. Main process manages application lifecycle and Dock
2. Each window runs in its own subprocess
3. Each subprocess has its own Python interpreter (complete isolation)
4. Subprocesses are identified by `TFM_SUBPROCESS=1` environment variable

### Architecture Diagram

```
Main Process (TFM.app)
├── Manages Dock and menu bar
├── Spawns subprocess for each window
└── Stays alive to handle "New Window" requests

Subprocess 1 (Window 1)
├── Own Python interpreter
├── Calls cli_main() directly
└── Terminates when window closes

Subprocess 2 (Window 2)
├── Own Python interpreter
├── Calls cli_main() directly
└── Terminates when window closes
```

### Code Changes

**Main Process Detection:**
```objective-c
- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    NSString *isSubprocess = [[[NSProcessInfo processInfo] environment] 
                               objectForKey:@"TFM_SUBPROCESS"];
    
    if (isSubprocess && [isSubprocess isEqualToString:@"1"]) {
        // Subprocess: launch window directly
        [self launchTFMWindowInCurrentProcess];
    } else {
        // Main process: spawn subprocess for first window
        [self launchNewTFMWindow];
    }
}
```

**Subprocess Spawning:**
```objective-c
- (void)launchNewTFMWindow {
    NSBundle *mainBundle = [NSBundle mainBundle];
    NSString *executablePath = [mainBundle executablePath];
    
    // Create task to launch subprocess
    NSTask *task = [[NSTask alloc] init];
    [task setLaunchPath:executablePath];
    
    // Set environment variable to mark as subprocess
    NSMutableDictionary *environment = [[NSMutableDictionary alloc] 
        initWithDictionary:[[NSProcessInfo processInfo] environment]];
    [environment setObject:@"1" forKey:@"TFM_SUBPROCESS"];
    [task setEnvironment:environment];
    
    // Launch subprocess
    [task launch];
}
```

**Subprocess Window Launch:**
```objective-c
- (void)launchTFMWindowInCurrentProcess {
    // Initialize Python in this subprocess
    [self initializePython];
    
    // Import tfm_main and call cli_main()
    PyObject *tfmModule = PyImport_ImportModule("tfm_main");
    PyObject *cliMainFunc = PyObject_GetAttrString(tfmModule, "cli_main");
    
    // Set sys.argv for --desktop mode
    PyRun_SimpleString("sys.argv = ['TFM', '--desktop']");
    
    // Call cli_main() - blocks until window closes
    PyObject *result = PyObject_CallObject(cliMainFunc, NULL);
    
    // When cli_main() returns, terminate subprocess
    [NSApp terminate:self];
}
```

## Benefits

### 1. Complete Isolation
- Each window has its own Python interpreter
- No shared state between windows
- No threading complexity
- No GIL (Global Interpreter Lock) contention

### 2. Consistent Behavior
- macOS app now behaves identically to `python3 tfm.py --desktop`
- Same backend initialization logic
- Same configuration handling
- Same error handling

### 3. No Code Changes Required
- TFM's Python code works as-is
- No need for thread-safe state management
- No synchronization primitives needed
- Maintains single-window design assumptions

### 4. Crash Resilience
- If one window crashes, others continue running
- Main process stays alive to spawn new windows
- Better fault tolerance

### 5. Memory Management
- Each subprocess has its own memory space
- Memory is freed when subprocess terminates
- No memory leaks between windows

### 6. Maintainability
- Simple architecture (no threading)
- Easy to debug (separate processes)
- Clear separation of concerns
- Single code path for both modes

## Comparison: Multi-Process vs Threading

| Aspect | Multi-Process (Chosen) | Multi-Threading (Rejected) |
|--------|------------------------|----------------------------|
| Isolation | Complete | Partial |
| State Management | Independent | Shared (requires sync) |
| TFM Code Changes | None | Extensive |
| Crashes | Isolated | Can crash entire app |
| Memory | Separate spaces | Shared space |
| GIL | No contention | GIL contention |
| Complexity | Simple | Complex |
| Debugging | Easy (separate logs) | Hard (race conditions) |

## Process Lifecycle

### First Window
1. User launches TFM.app
2. Main process starts
3. Main process spawns subprocess with `TFM_SUBPROCESS=1`
4. Subprocess initializes Python and calls `cli_main()`
5. Window appears

### Additional Windows
1. User clicks "New Window" in Dock menu
2. Main process spawns another subprocess
3. New subprocess initializes Python and calls `cli_main()`
4. Second window appears

### Window Close
1. User closes window
2. `cli_main()` returns
3. Subprocess terminates
4. Main process continues (ready for new windows)

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

3. **Verify processes:**
   ```bash
   ps aux | grep TFM.app
   # Should show: 1 main process + 1 subprocess per window
   ```

4. **Test multi-window:**
   - Right-click Dock icon → "New Window"
   - Verify second window opens
   - Both windows should be independent
   - Close one window, other continues

5. **Compare with command-line:**
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
- ✅ Multi-window support works
- ✅ "New Window" menu item functional
- ✅ Windows are completely independent
- ✅ Closing one window doesn't affect others

## Future Considerations

### Inter-Process Communication (IPC)
If future features require communication between windows:
- NSDistributedNotificationCenter (simple notifications)
- XPC (structured communication)
- Shared files (persistent data)
- Unix domain sockets (real-time communication)

### Performance Optimization
- Process pool: Pre-spawn subprocesses for faster window creation
- Shared Python framework: Reduce memory usage

### Not Recommended
- Threading: Would require extensive TFM code changes
- Single process: Would limit multi-window independence

## Related Files

- `macos_app/src/TFMAppDelegate.m` - Multi-process implementation
- `macos_app/MULTIPROCESS_ARCHITECTURE.md` - Detailed architecture documentation
- `src/tfm_main.py` - Contains `cli_main()` entry point
- `src/tfm_backend_selector.py` - Backend selection logic
- `tfm.py` - Command-line wrapper that calls `cli_main()`

## References

- NSTask: https://developer.apple.com/documentation/foundation/nstask
- Process Management: https://developer.apple.com/documentation/foundation/nsprocessinfo
- Python/C API: https://docs.python.org/3/c-api/

---

**Fix implemented: December 27, 2024**
**Status: Verified working**
**Result: Consistent behavior + complete window isolation + no code changes**
