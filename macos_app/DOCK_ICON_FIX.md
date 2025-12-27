# Dock Icon Fix for Multi-Process Architecture

## Problem

When using the multi-process architecture (one process per window), each subprocess was showing its own Dock icon. This resulted in multiple TFM icons in the Dock, which is confusing for users.

**Expected behavior**: Single Dock icon for the application
**Actual behavior**: Multiple Dock icons (one per process)

## Root Cause

By default, every macOS application process shows a Dock icon. In our multi-process architecture:
- Main process: Should show Dock icon (manages application)
- Subprocesses: Should NOT show Dock icons (just run windows)

## Solution

Use `NSApplicationActivationPolicy` to control Dock icon visibility:

### Main Process
Set activation policy to `NSApplicationActivationPolicyRegular`:
- Shows Dock icon
- Appears in Cmd+Tab switcher
- Can have menu bar
- Normal application behavior

### Subprocesses
Set activation policy to `NSApplicationActivationPolicyAccessory`:
- Hides Dock icon
- Does NOT appear in Cmd+Tab switcher
- Can still create windows
- Runs in background

## Implementation

### Code Changes

Modified `applicationDidFinishLaunching` in `TFMAppDelegate.m`:

```objective-c
- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    NSString *isSubprocess = [[[NSProcessInfo processInfo] environment] 
                               objectForKey:@"TFM_SUBPROCESS"];
    
    if (isSubprocess && [isSubprocess isEqualToString:@"1"]) {
        // Subprocess: Hide from Dock
        [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];
        
        // Launch window...
    } else {
        // Main process: Show in Dock
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
        
        // Spawn subprocess...
    }
}
```

### Activation Policy Options

macOS provides three activation policies:

1. **NSApplicationActivationPolicyRegular** (Main process)
   - Normal application
   - Shows Dock icon
   - Appears in Cmd+Tab
   - Can have menu bar
   - Can be activated

2. **NSApplicationActivationPolicyAccessory** (Subprocesses)
   - Background application
   - NO Dock icon
   - NO Cmd+Tab appearance
   - Can create windows
   - Windows appear but app is "invisible"

3. **NSApplicationActivationPolicyProhibited** (Not used)
   - Cannot be activated
   - Cannot create windows
   - Used for daemons/agents

## Benefits

### User Experience
- ✅ Single Dock icon (clean interface)
- ✅ Single entry in Cmd+Tab switcher
- ✅ All windows appear to belong to one app
- ✅ Consistent with user expectations

### Technical
- ✅ Main process manages application lifecycle
- ✅ Subprocesses remain invisible to user
- ✅ Windows still function normally
- ✅ No changes to window behavior

## Testing

### Verification Steps

1. **Launch app:**
   ```bash
   open macos_app/build/TFM.app
   ```

2. **Check Dock:**
   - Should see ONE TFM icon
   - Icon should be active (dot underneath)

3. **Check processes:**
   ```bash
   ps aux | grep TFM.app | grep -v grep
   ```
   - Should see 2 processes (1 main + 1 subprocess)

4. **Check Cmd+Tab:**
   - Press Cmd+Tab
   - Should see ONE TFM entry

5. **Open second window:**
   - Right-click Dock icon → "New Window"
   - Should still see ONE Dock icon
   - Should see 3 processes (1 main + 2 subprocesses)

### Expected Results

| Scenario | Dock Icons | Processes | Cmd+Tab Entries |
|----------|------------|-----------|-----------------|
| 1 window | 1 | 2 (main + 1 sub) | 1 |
| 2 windows | 1 | 3 (main + 2 sub) | 1 |
| 3 windows | 1 | 4 (main + 3 sub) | 1 |

## Window Management

### Window Ownership

All windows appear to belong to the main process from the user's perspective:
- Windows show "TFM" in title bar
- Windows appear under single Dock icon
- Clicking Dock icon shows all windows
- All windows minimize to same Dock icon

### Window Switching

Users can switch between windows using:
- Clicking windows directly
- Cmd+` (cycle through app windows)
- Mission Control
- Window menu (if implemented)

## Alternative Approaches Considered

### 1. LSUIElement in Info.plist
**Rejected**: Would hide main process too
- Setting `LSUIElement=true` in Info.plist affects ALL processes
- Would hide the main process's Dock icon
- No way to differentiate main vs subprocess

### 2. Single Process with Threading
**Rejected**: Requires TFM code changes
- Would need thread-safe state management
- Complex synchronization
- GIL contention
- Not compatible with TFM's design

### 3. Separate App Bundles
**Rejected**: Too complex
- Would need two separate .app bundles
- Complex build process
- Confusing for users
- Harder to maintain

## Implementation Notes

### Timing

The activation policy must be set **before** any windows are created:
```objective-c
// CORRECT: Set policy first
[NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];
[self launchTFMWindowInCurrentProcess];

// WRONG: Set policy after window creation
[self launchTFMWindowInCurrentProcess];
[NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory]; // Too late!
```

### Process Identification

Subprocesses are identified by the `TFM_SUBPROCESS=1` environment variable:
- Set by main process when spawning subprocess
- Read by subprocess in `applicationDidFinishLaunching`
- Used to determine activation policy

### Main Process Behavior

The main process:
- Shows Dock icon (NSApplicationActivationPolicyRegular)
- Manages Dock menu ("New Window")
- Spawns subprocesses
- Stays alive even when all windows close
- Quits when user selects Quit from Dock menu

### Subprocess Behavior

Each subprocess:
- Hides from Dock (NSApplicationActivationPolicyAccessory)
- Runs one TFM window
- Terminates when window closes
- Independent from other subprocesses

## Troubleshooting

### Multiple Dock Icons Still Appear

**Cause**: Activation policy not set correctly
**Solution**: 
1. Check that `setActivationPolicy` is called before window creation
2. Verify `TFM_SUBPROCESS` environment variable is set
3. Rebuild app: `cd macos_app && ./build.sh`

### Dock Icon Disappears Completely

**Cause**: Main process using wrong activation policy
**Solution**:
1. Verify main process uses `NSApplicationActivationPolicyRegular`
2. Check that main process is NOT setting `TFM_SUBPROCESS=1` for itself

### Windows Don't Appear in Cmd+Tab

**Expected behavior**: Only main process appears in Cmd+Tab
**Reason**: Subprocesses use `NSApplicationActivationPolicyAccessory`
**This is correct**: All windows appear to belong to main process

## Related Files

- `macos_app/src/TFMAppDelegate.m` - Activation policy implementation
- `macos_app/MULTIPROCESS_ARCHITECTURE.md` - Overall architecture
- `macos_app/ENTRY_POINT_FIX.md` - Entry point and process spawning

## References

- NSApplicationActivationPolicy: https://developer.apple.com/documentation/appkit/nsapplicationactivationpolicy
- NSApplication: https://developer.apple.com/documentation/appkit/nsapplication
- Dock Integration: https://developer.apple.com/design/human-interface-guidelines/the-dock

---

**Fix implemented: December 27, 2024**
**Status: Verified working**
**Result: Single Dock icon with multi-process architecture**
