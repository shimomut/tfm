# SSH DMG Connection Fix

## Problem

When TFM is packaged as a DMG, SSH connections fail with "Connection closed by UNKNOWN port 65535" error or hang indefinitely. This issue does not occur when running the regular app bundle built with `make macos-app`.

## Root Cause

The issue had two components:

1. **Missing PATH for ProxyCommand**: When TFM runs from a DMG-mounted app, the environment PATH doesn't include common binary locations like `/opt/homebrew/bin` or `/usr/local/bin`. SSH configurations that use ProxyCommand (e.g., AWS SSM with `exec aws ssm start-session`) fail because the `aws` command cannot be found.

2. **SSH `-f` flag causing hangs**: The SSH control master was using the `-f` (fork to background) flag, which caused the parent process to return immediately while the child process hung indefinitely when ProxyCommand failed. This prevented proper error detection and timeout handling.

## Solution

### 1. PATH Setup in TFMAppDelegate.m

Added `setupEnvironmentPath` method that configures PATH before launching TFM:

```objective-c
- (void)setupEnvironmentPath {
    // Get current PATH
    NSString *currentPath = [[[NSProcessInfo processInfo] environment] objectForKey:@"PATH"];
    
    // Common locations for CLI tools (aws, gcloud, etc.)
    NSArray *additionalPaths = @[
        @"/usr/local/bin",           // Homebrew (Intel Mac)
        @"/opt/homebrew/bin",        // Homebrew (Apple Silicon)
        @"/opt/local/bin",           // MacPorts
        @"/usr/bin",                 // System binaries
        @"/bin",                     // Core system binaries
        [@"~/bin" stringByExpandingTildeInPath],
        [@"~/.local/bin" stringByExpandingTildeInPath],
        [@"~/Library/Python/3.13/bin" stringByExpandingTildeInPath],
        [@"~/Library/Python/3.12/bin" stringByExpandingTildeInPath],
        [@"~/Library/Python/3.11/bin" stringByExpandingTildeInPath]
    ];
    
    // Build new PATH by prepending additional paths
    // (includes deduplication and joining logic)
    
    // Set environment variable for current process
    setenv("PATH", [newPath UTF8String], 1);
    
    // Also update Python's os.environ
    NSString *pythonCmd = [NSString stringWithFormat:@"import os; os.environ['PATH'] = '%@'", newPath];
    PyRun_SimpleString([pythonCmd UTF8String]);
}
```

This method is called in `launchTFMWindow` before importing the TFM module.

### 2. Removed `-f` Flag from SSH Command

Modified `_establish_control_master()` in `tfm_ssh_connection.py`:

**Before:**
```python
ssh_cmd = ['ssh', '-N', '-f']  # -f: fork to background
```

**After:**
```python
ssh_cmd = ['ssh', '-N']  # Removed -f flag
```

Without `-f`, the SSH process runs in foreground, allowing us to:
- Detect when the connection is established by checking for the control socket
- Properly timeout and capture errors if connection fails
- Terminate the master process after connection (ControlPersist keeps socket alive)

### 3. Improved Connection Detection

The connection establishment now:
1. Starts SSH process without `-f` flag
2. Waits up to 10 seconds for connection
3. Checks if control socket was created
4. If socket exists, terminates the master process (ControlPersist=10m keeps it alive)
5. If socket doesn't exist, captures stderr and reports error

## Files Modified

- `macos_app/src/TFMAppDelegate.m` - Added PATH setup
- `src/tfm_ssh_connection.py` - Removed `-f` flag, improved connection detection
- `test/test_ssh_socket_path.py` - Tests for socket path change (kept from earlier investigation)

## Testing

1. Build DMG: `make macos-dmg`
2. Mount DMG: `open macos_app/build/TFM-*.dmg`
3. Launch TFM.app from mounted DMG
4. Connect to SSH server that uses ProxyCommand
5. Verify connection succeeds

## Related Changes

During investigation, the control socket path was changed from `/tmp` to `~/.tfm/ssh_sockets/` for better organization and to avoid potential sandboxing issues. This change is independent of the DMG fix but improves overall reliability. See `SSH_CONTROL_SOCKET_FIX.md` for details.

## Why This Works

### PATH Setup
- DMG-mounted apps don't inherit the user's shell PATH
- ProxyCommand in SSH config needs to find external tools like `aws`, `gcloud`, etc.
- Setting PATH in Objective-C before Python starts ensures all subprocesses see it

### Removing `-f` Flag
- With `-f`, SSH forks to background and parent returns immediately
- If child process hangs (e.g., ProxyCommand fails), we can't detect it
- Without `-f`, we can monitor the process and check for socket creation
- ControlPersist keeps the socket alive even after we terminate the master

## Debugging

If SSH connections still fail, check the logs for:
- `Current PATH:` - Verify PATH includes necessary directories
- `SSH process exited unexpectedly` - Connection failed immediately
- `Control socket not created` - Connection timed out

The logs will show stderr output from SSH which can help diagnose ProxyCommand issues.
