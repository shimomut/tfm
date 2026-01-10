# SSH DMG Connection Diagnostics

## Overview

This document describes the comprehensive diagnostics added to the SSH connection code to troubleshoot the "Connection closed by UNKNOWN port 65535" error that occurs when TFM is packaged as a DMG.

## Diagnostic Information Logged

When establishing an SSH control master connection, the following information is now logged:

### 1. Control Socket Path Information
- **Control socket path**: Full path to the Unix domain socket
- **Socket directory**: Parent directory of the socket
- **Socket directory exists**: Whether the directory exists
- **Socket directory writable**: Whether the directory is writable
- **Socket directory permissions**: Octal permissions (e.g., 755)

### 2. Existing Socket Check
- **Control socket already exists**: Warning if socket file already exists
- **Socket file permissions**: Octal permissions of existing socket

### 3. SSH Configuration
- **SSH hostname**: The hostname/alias from SSH config
- **SSH actual host**: The resolved hostname
- **SSH port**: Port number (default 22)
- **SSH user**: Username for connection
- **SSH identity file**: Path to private key file

### 4. SSH Binary and Identity File
- **SSH binary path**: Full path to ssh executable
- **Identity file exists**: Whether the private key file exists
- **Identity file readable**: Whether the key file is readable
- **Identity file permissions**: Octal permissions of key file

### 5. SSH Command Execution
- **SSH command**: Full command with all arguments
- **SSH return code**: Exit code from ssh command
- **SSH stdout**: Standard output (first 500 chars)
- **SSH stderr**: Standard error (first 50 lines) with verbose SSH debug output
- **Control socket created**: Whether the socket file was created

### 6. Error Information
- **Traceback**: Full Python traceback on exceptions

## How to Use These Diagnostics

### Step 1: Build and Run DMG Version

```bash
# Build the DMG
make macos-dmg

# Mount and run from DMG
open macos_app/build/TFM-*.dmg
# Then launch TFM.app from the mounted DMG
```

### Step 2: Attempt SSH Connection

Try to connect to your SFTP server through the TFM interface.

### Step 3: Review Log Output

Check the log pane at the bottom of TFM for detailed diagnostic information. Look for:

#### Socket Directory Issues
```
Socket directory: /Users/username/.tfm/ssh_sockets
Socket directory exists: True
Socket directory is writable: False  ← PROBLEM!
```

#### Permission Issues
```
Socket directory permissions: 000  ← PROBLEM!
Identity file permissions: 000  ← PROBLEM!
```

#### SSH Binary Issues
```
SSH binary path: None  ← PROBLEM!
```

#### SSH Verbose Output
The stderr output will contain SSH's verbose debug information. Look for:
- `debug1: identity file` - Key file loading
- `debug1: Connecting to` - Connection attempt
- `debug1: Connection established` - Success
- `debug1: control_persist_detach` - Control master setup
- Any error messages about permissions, keys, or network

### Step 4: Compare with Working Version

Run the same test with the regular app bundle:

```bash
# Build regular app
make macos-app

# Run from build directory
open macos_app/build/TFM.app
```

Compare the log output between DMG and regular app versions to identify differences.

## Common Issues to Look For

### 1. Socket Directory Not Writable
**Symptom**: `Socket directory is writable: False`

**Cause**: App doesn't have permission to write to `~/.tfm/ssh_sockets/`

**Solution**: Check macOS sandboxing or security settings

### 2. Identity File Not Readable
**Symptom**: `Identity file readable: False`

**Cause**: App can't read SSH private key file

**Solution**: May need to grant file access permissions or use different key location

### 3. SSH Binary Not Found
**Symptom**: `SSH binary path: None`

**Cause**: `ssh` command not in PATH or not accessible

**Solution**: Check if SSH is available in the app's environment

### 4. Socket Creation Fails
**Symptom**: `Control socket created: False` but `SSH return code: 0`

**Cause**: SSH command succeeds but socket isn't created at expected location

**Solution**: Check if SSH is creating socket elsewhere or if there's a path issue

### 5. Port 65535 Error
**Symptom**: `Connection closed by UNKNOWN port 65535` in stderr

**Cause**: SSH can't create control socket at specified path

**Possible reasons**:
- Path doesn't exist
- Path not writable
- Path too long
- Socket already exists and is stale
- Sandboxing prevents socket creation

## Analyzing SSH Verbose Output

The `-vvv` flag provides three levels of verbosity. Key things to look for:

### Connection Phase
```
debug1: Connecting to hostname [IP] port 22.
debug1: Connection established.
```

### Authentication Phase
```
debug1: identity file /Users/username/.ssh/id_rsa type 0
debug1: Authentications that can continue: publickey
debug1: Next authentication method: publickey
debug1: Offering public key: /Users/username/.ssh/id_rsa
debug1: Server accepts key: pkalg ssh-rsa
debug1: Authentication succeeded (publickey).
```

### Control Master Phase
```
debug1: Setting up multiplex socket: /Users/username/.tfm/ssh_sockets/tfm-ssh-12345678
debug1: control_persist_detach: backgrounding master process
```

### Error Indicators
- `Permission denied` - Authentication or file permission issue
- `Connection refused` - Network or firewall issue
- `No such file or directory` - Path issue
- `Operation not permitted` - Sandboxing or security issue

## Next Steps Based on Findings

### If Socket Directory Issue
- Verify `~/.tfm/ssh_sockets/` exists and is writable
- Check if different path works (e.g., `/tmp`)
- Investigate macOS sandboxing restrictions

### If Identity File Issue
- Verify key file exists and has correct permissions (600)
- Try using different key location
- Check if app can access `~/.ssh/` directory

### If SSH Binary Issue
- Verify `/usr/bin/ssh` exists
- Check if app's PATH includes `/usr/bin`
- Investigate if app environment differs from terminal

### If Socket Creation Issue
- Try shorter socket path
- Check if socket limit reached
- Verify no stale sockets exist
- Test with different socket location

## Temporary Workarounds

While investigating, you can try:

1. **Use different socket location**: Modify `_control_path` to use `/tmp`
2. **Disable control master**: Comment out control master options (performance impact)
3. **Use different SSH options**: Try different ControlPath format
4. **Check system logs**: Review Console.app for security/sandbox messages

## Reporting Issues

When reporting the issue, include:
1. Full log output from SSH connection attempt
2. macOS version
3. TFM version (DMG vs regular app)
4. SSH config file contents (sanitized)
5. Output of `ls -la ~/.tfm/ssh_sockets/`
6. Output of `ls -la ~/.ssh/`
