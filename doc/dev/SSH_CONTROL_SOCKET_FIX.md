# SSH Control Socket Path Fix for DMG-Packaged Apps

## Problem

When TFM is packaged as a DMG installer and run, SSH connections fail with the error:

```
Failed to establish control master: Connection closed by UNKNOWN port 65535
```

This error occurs specifically with the DMG-packaged version but not with the regular app bundle built via `make macos-app`.

## Root Cause

The SSH connection code was using `tempfile.gettempdir()` (which returns `/tmp` on macOS) to store SSH control master socket files. When running from a DMG-packaged app, the application may run in a restricted environment where:

1. `/tmp` access is limited or sandboxed
2. The temporary directory path may be different
3. Socket creation in `/tmp` may fail silently

The error "port 65535" is SSH's way of indicating it couldn't create the control socket at the specified path.

## Solution

Changed the SSH control socket path from `/tmp` to `~/.tfm/ssh_sockets/`:

**Before:**
```python
import tempfile
self._control_path = os.path.join(tempfile.gettempdir(), f'tfm-ssh-{hostname_hash}')
```

**After:**
```python
from pathlib import Path
ssh_socket_dir = Path.home() / '.tfm' / 'ssh_sockets'
ssh_socket_dir.mkdir(parents=True, exist_ok=True)
pid = os.getpid()
self._control_path = str(ssh_socket_dir / f'tfm-ssh-{hostname_hash}-{pid}')
```

## Why This Works

1. **User home directory is always accessible**: Even in sandboxed environments, apps can access the user's home directory
2. **Persistent location**: Using `~/.tfm/` keeps all TFM-related files in one place
3. **Explicit directory creation**: Ensures the directory exists before attempting to create sockets
4. **No sandboxing conflicts**: Home directory access doesn't conflict with macOS app sandboxing
5. **Process isolation**: Including PID ensures each TFM process has its own control socket, preventing race conditions when multiple instances connect to the same host

## Benefits

1. **DMG compatibility**: Fixes SSH connections when running from DMG-packaged apps
2. **Better organization**: All TFM files are now under `~/.tfm/`
3. **Debugging**: Easier to find and inspect control sockets
4. **Cleanup**: Users can easily clean up old sockets by removing `~/.tfm/ssh_sockets/`
5. **Process isolation**: Each TFM instance has its own control socket, preventing race conditions when:
   - Process A creates a socket and connects
   - Process B tries to use the same socket
   - Process A exits and deletes the socket
   - Process B gets connection errors

## File Locations

- **Control sockets**: `~/.tfm/ssh_sockets/tfm-ssh-{hash}-{pid}`
  - `{hash}`: 8-character MD5 hash of hostname
  - `{pid}`: Process ID to ensure uniqueness per TFM instance
- **Config file**: `~/.tfm/config.py`
- **SSH cache**: `~/.tfm/ssh_cache.json`

## Testing

To verify the fix:

1. Build DMG: `make macos-dmg`
2. Mount the DMG and run TFM.app from it
3. Connect to an SFTP server
4. Verify connection succeeds without "port 65535" errors
5. Check that socket files are created in `~/.tfm/ssh_sockets/`

## Related Code

- `src/tfm_ssh_connection.py` - SSH connection implementation
- `macos_app/build.sh` - App bundle build script
- `macos_app/create_dmg.sh` - DMG creation script

## Technical Details

### SSH Control Master

SSH control master is a feature that allows multiple SSH connections to share a single network connection. The control socket is a Unix domain socket file that coordinates these connections.

### Socket Path Requirements

- Must be writable by the application
- Must be accessible in the app's security context
- Path length should be reasonable (< 104 characters on most systems)
- Should persist across app restarts for connection reuse

### macOS App Sandboxing

While TFM doesn't explicitly enable sandboxing, DMG-mounted apps may run with restricted permissions:
- Limited `/tmp` access
- Full home directory access
- Network access allowed (for SSH)

## Future Considerations

If TFM ever enables full macOS sandboxing, additional entitlements may be needed:
- `com.apple.security.network.client` - For SSH connections
- `com.apple.security.files.user-selected.read-write` - For file operations
- `com.apple.security.temporary-exception.files.absolute-path.read-write` - For SSH socket directory
