# Remote Log Monitoring Feature

## Overview

The Remote Log Monitoring feature lets you watch TFM's log messages from other terminal windows or even other computers. This is helpful for monitoring what TFM is doing while you work in multiple terminals.

## Features

- **Real-time log viewing**: See log messages as they happen
- **Multiple viewers**: Several terminals can watch the same TFM instance
- **Color-coded messages**: Different types of messages show in different colors
- **Network support**: Works locally and across networks

## How to Use

### Step 1: Start TFM with Log Monitoring

Start TFM with the `--remote-log-port` option:

```bash
# Start TFM with log monitoring on port 8888
python tfm.py --remote-log-port 8888
```

You'll see a message confirming the log server started.

### Step 2: Connect from Another Terminal

In a different terminal window, connect to watch the logs:

```bash
# Connect to the TFM instance
python tools/tfm_log_client.py localhost 8888

# Or use the default (localhost:8888)
python tools/tfm_log_client.py
```

### Step 3: Watch the Logs

Now when you use TFM in the first terminal, you'll see all the log messages in the second terminal in real-time.

## Message Types

You'll see different types of messages in different colors:

- **Green**: System messages (startup, version info)
- **Blue**: Configuration messages
- **White**: Normal output
- **Red**: Error messages
- **Magenta**: Remote monitoring messages

## Security Notes

- By default, only connections from the same computer are allowed
- Anyone who can connect to the port can see the logs
- Log messages might contain file paths and system information

## Examples

### Basic Setup

**Terminal 1 (TFM):**
```bash
python tfm.py --remote-log-port 8888
```

**Terminal 2 (Log Viewer):**
```bash
python tools/tfm_log_client.py
```

### Multiple Viewers

You can have several terminals watching the same TFM instance:

**Terminal 1 (TFM):**
```bash
python tfm.py --remote-log-port 8888
```

**Terminal 2 & 3 (Log Viewers):**
```bash
python tools/tfm_log_client.py localhost 8888
```

### Remote Monitoring

If TFM is running on another computer:

**Server:**
```bash
python tfm.py --remote-log-port 8888
```

**Your Computer:**
```bash
python tools/tfm_log_client.py server-name 8888
```

## Troubleshooting

### "Connection refused" error

- Make sure TFM is running with `--remote-log-port 8888`
- Check that the port numbers match
- Try a different port number if 8888 is in use

### No log messages appear

- Make sure TFM is actually doing something (try copying a file)
- Check that both terminals are using the same port number
- Restart both TFM and the log client

### Client disconnects

- Check that TFM is still running
- Make sure your network connection is stable
- Try reconnecting the log client

## When to Use This Feature

Remote log monitoring is useful when you:

- Want to monitor TFM operations while working in other terminals
- Need to debug issues by watching detailed log output
- Are running TFM on a server and want to monitor it remotely
- Want to keep track of file operations without switching windows

## Tips

- Use different port numbers if you're running multiple TFM instances
- The log viewer shows timestamps so you can see when things happened
- Press Ctrl+C to exit the log viewer
- You can start and stop log viewers anytime without affecting TFM