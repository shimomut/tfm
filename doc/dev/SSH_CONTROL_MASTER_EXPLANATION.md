# SSH Control Master Explanation

## What is SSH Control Master?

SSH Control Master is an SSH multiplexing feature that allows multiple SSH sessions to share a single network connection. Instead of establishing a new TCP connection for each SFTP operation, all operations reuse the same persistent connection.

## Why TFM Uses Control Master

### Without Control Master (Traditional Approach)
```
Operation 1: Establish TCP connection → Authenticate → Transfer → Close
Operation 2: Establish TCP connection → Authenticate → Transfer → Close
Operation 3: Establish TCP connection → Authenticate → Transfer → Close
...
```

Each operation requires:
- TCP handshake (3-way handshake)
- SSH key exchange
- Authentication
- Connection teardown

**Cost per operation:** 100-500ms depending on network latency

### With Control Master (TFM's Approach)
```
Initial: Establish TCP connection → Authenticate → Keep alive
Operation 1: Use existing connection → Transfer
Operation 2: Use existing connection → Transfer
Operation 3: Use existing connection → Transfer
...
```

Only the first operation pays the connection cost. Subsequent operations are nearly instant.

**Cost per operation:** 1-10ms (99% faster!)

## How Control Master Works in TFM

### 1. Establishing the Control Master

When `SSHConnection.connect()` is called:

```python
# Create a background SSH process that stays alive
ssh -N -f \
    -o ControlMaster=yes \
    -o ControlPath=/tmp/tfm-ssh-abc123 \
    -o ControlPersist=10m \
    hostname
```

This creates a **master process** that:
- Establishes the TCP connection
- Performs authentication
- Stays running in the background
- Listens on a Unix socket at `/tmp/tfm-ssh-abc123`
- Automatically exits after 10 minutes of inactivity

### 2. Using the Control Master

When performing SFTP operations:

```python
# All SFTP commands automatically use the control master
sftp -o ControlPath=/tmp/tfm-ssh-abc123 hostname <<EOF
ls /path
EOF
```

The `sftp` command:
- Connects to the Unix socket (not the remote host)
- Sends commands through the existing SSH connection
- Returns results immediately (no connection overhead)

### 3. Checking the Control Master

This is where `_check_control_master()` comes in:

```python
def _check_control_master(self) -> bool:
    """Check if control master is still active"""
    result = subprocess.run(
        ['ssh', '-O', 'check', '-o', f'ControlPath={self._control_path}', hostname],
        capture_output=True,
        timeout=5
    )
    return result.returncode == 0
```

This command asks SSH: "Is the master process still running?"

## Why _check_control_master() is Needed

### Problem 1: Connection Can Die Silently

The control master process can terminate for several reasons:
- Network interruption
- Remote host reboot
- SSH daemon restart
- Idle timeout (after ControlPersist expires)
- Manual termination

If the master dies, subsequent SFTP operations will **hang or fail** with cryptic errors.

### Problem 2: No Automatic Notification

Unlike a direct connection, there's no automatic notification when the control master dies. The application must actively check.

### Problem 3: User Experience

Without checking:
```
User: Browse directory
TFM: (tries to use dead control master)
SFTP: Connection refused / Timeout
User: Sees error, confused why it suddenly stopped working
```

With checking:
```
User: Browse directory
TFM: (checks control master, finds it dead)
TFM: (automatically reconnects)
TFM: (operation succeeds)
User: Everything works smoothly
```

## The Performance Dilemma

### The Trade-off

**Checking too often:**
- ✅ Detects disconnections quickly
- ✅ Better error messages
- ❌ Subprocess overhead on every operation
- ❌ Negates the performance benefit of control master

**Checking too rarely:**
- ✅ Minimal overhead
- ✅ Maximum performance
- ❌ Delayed disconnection detection
- ❌ Operations fail before detection

### Current Implementation

TFM currently checks on **every operation**:
```python
def get_connection():
    if conn.is_connected():  # Calls _check_control_master()
        return conn
```

This is **safe but slow** - it defeats much of the control master benefit.

## The Optimization Opportunity

### Key Insight

The control master is **very stable** once established:
- It doesn't randomly die
- Network interruptions are rare
- When it does die, operations will fail anyway

Therefore, we can **cache the status** for a short period (5 seconds):

```python
def is_connected(self):
    # Only check every 5 seconds
    if time.time() - self._last_check < 5.0:
        return self._cached_status  # No subprocess!
    
    # Perform actual check
    status = self._check_control_master()
    self._cached_status = status
    self._last_check = time.time()
    return status
```

### Benefits of Caching

**For 100 operations in 5 seconds:**
- Before: 100 subprocess calls (1000-5000ms overhead)
- After: 1 subprocess call (10-50ms overhead)
- **Savings: 99% reduction in overhead**

**Disconnection detection:**
- Before: Immediate (0ms delay)
- After: Up to 5 seconds delay
- **Trade-off: Acceptable for most use cases**

### Why 5 Seconds is Safe

1. **Operations fail anyway:** If the connection is dead, the SFTP operation will fail within 1-2 seconds
2. **Automatic recovery:** Failed operations trigger immediate reconnection
3. **User perception:** 5 seconds is imperceptible for most workflows
4. **Network stability:** Connections rarely die during active use

## Real-World Scenarios

### Scenario 1: Browsing Directories

```
User scrolls through file list (100 files)
- Without caching: 100 checks × 20ms = 2000ms lag
- With caching: 1 check × 20ms = 20ms lag
Result: Smooth scrolling vs. stuttering
```

### Scenario 2: Sorting Files

```
User sorts by date (triggers stat on 100 files)
- Without caching: 100 checks × 20ms = 2000ms delay
- With caching: 1 check × 20ms = 20ms delay
Result: Instant sort vs. 2-second freeze
```

### Scenario 3: Connection Dies

```
Network interruption occurs
- Without caching: Next operation detects immediately
- With caching: Detection delayed up to 5 seconds
- Both cases: Operation fails, reconnection triggered
Result: Minimal difference in user experience
```

## Conclusion

`_check_control_master()` is **essential** for:
1. Detecting when the background SSH process dies
2. Enabling automatic reconnection
3. Providing clear error messages

But it's **too expensive** to call on every operation.

The solution is **caching**: Check once every 5 seconds instead of on every operation. This provides:
- 99% reduction in subprocess overhead
- Smooth, responsive UI
- Acceptable disconnection detection delay
- Automatic recovery on failures

This is the optimization proposed in the spec!
