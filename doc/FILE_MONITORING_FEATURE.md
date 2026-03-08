# Automatic File List Reloading

## Overview

TFM automatically detects and displays changes made to files by external applications. When another program creates, deletes, modifies, or renames files in the directory you're viewing, TFM updates the file list automatically—no manual refresh needed.

This feature keeps your view synchronized with the actual filesystem state, preventing confusion and potential errors from working with outdated information.

## How It Works

TFM monitors both the left and right pane directories simultaneously. When an external application makes changes:

- **New files appear automatically** when created by other programs
- **Deleted files disappear** from the list immediately
- **Modified files** show updated sizes and timestamps
- **Renamed files** reflect their new names

Your cursor position and selection are preserved during automatic updates, so your workflow isn't interrupted.

## Configuration

### Enabling or Disabling Monitoring

Automatic file monitoring is enabled by default. To change this setting, edit your TFM configuration file:

```json
{
  "file_monitoring": {
    "enabled": true
  }
}
```

Set `enabled` to `false` to disable automatic monitoring. When disabled, TFM only updates the file list after you perform actions like navigating directories or manually refreshing.

### Advanced Configuration Options

Most users won't need to adjust these settings, but they're available for fine-tuning:

```json
{
  "file_monitoring": {
    "enabled": true,
    "coalesce_delay_ms": 200,
    "max_reloads_per_second": 5,
    "suppress_after_action_ms": 1000,
    "fallback_poll_interval_s": 5
  }
}
```

**Configuration Options:**

- `enabled` (default: `true`) - Enable or disable automatic monitoring
- `coalesce_delay_ms` (default: `200`) - Time window in milliseconds to batch multiple changes into a single update
- `max_reloads_per_second` (default: `5`) - Maximum number of automatic updates per second to prevent UI thrashing
- `suppress_after_action_ms` (default: `1000`) - Time in milliseconds to suppress automatic updates after you perform an action (prevents redundant reloads)
- `fallback_poll_interval_s` (default: `5`) - Polling interval in seconds when native monitoring is unavailable

## Runtime Toggle

You can enable or disable monitoring while TFM is running without restarting the application. Use the monitoring toggle command (check your key bindings) to switch monitoring on or off instantly.

When you disable monitoring at runtime:
- Automatic updates stop immediately
- File lists only update after your actions
- Monitoring can be re-enabled at any time

## Monitoring Modes

TFM uses different monitoring strategies depending on your storage type:

### Native Mode (Preferred)

For local filesystems, TFM uses efficient operating system APIs:
- **Linux**: inotify
- **macOS**: FSEvents  
- **Windows**: ReadDirectoryChangesW

Native mode provides instant change detection with minimal resource usage (typically less than 5MB memory and 1% CPU per watched directory).

### Fallback Mode (Polling)

When native monitoring isn't available, TFM automatically switches to polling mode. This happens with:
- **S3 buckets** and cloud storage
- **Network mounts** without change notification support
- **Remote filesystems** over SSH or similar protocols
- **Unsupported storage backends**

In fallback mode, TFM checks for changes every 5 seconds (configurable). While less responsive than native mode, it ensures monitoring works everywhere.

### Fallback Mode Indicator

When TFM operates in fallback mode due to storage limitations or errors, a status indicator appears in the interface. This lets you know that:
- Monitoring is active but using polling instead of native APIs
- Updates may take a few seconds to appear
- The feature is working correctly for your storage type

## What Gets Monitored

TFM monitors **only the immediate files and directories** in the current view. Changes in subdirectories don't trigger updates to the parent directory list—you'll see those changes when you navigate into the subdirectory.

Both panes are monitored independently:
- Changes in the left pane only update the left pane
- Changes in the right pane only update the right pane
- Each pane maintains its own cursor position and selection

## Cursor and Selection Behavior

During automatic updates, TFM preserves your context:

**If the selected file still exists:**
- Your cursor stays on the same file
- Your scroll position is maintained
- Your workflow continues uninterrupted

**If the selected file was deleted:**
- The cursor moves to the nearest remaining file alphabetically
- If the deleted file was "document.txt", the cursor moves to the next file alphabetically (e.g., "image.png")
- The scroll position adjusts to keep the cursor visible

## Troubleshooting

### File List Not Updating Automatically

**Check if monitoring is enabled:**
1. Verify `file_monitoring.enabled` is `true` in your configuration
2. Try toggling monitoring off and on at runtime
3. Restart TFM to reload configuration

**Check for fallback mode indicator:**
- If you see the fallback mode indicator, monitoring is working but using polling
- Changes may take up to 5 seconds to appear (or your configured polling interval)
- This is normal for S3, network mounts, and remote filesystems

**Check the log file:**
- TFM logs monitoring activity with the "FileMonitor" component name
- Look for initialization messages indicating monitoring mode
- Check for error messages that might explain issues

### Monitoring Not Working on Network Drives

Network drives and remote filesystems often don't support native change notifications. TFM automatically detects this and switches to fallback polling mode. You should see the fallback mode indicator, and changes will appear within a few seconds.

If monitoring doesn't work at all on a network drive:
1. Check that you have read permissions for the directory
2. Verify the network connection is stable
3. Check TFM logs for error messages
4. Consider increasing `fallback_poll_interval_s` if the network is slow

### Too Many Updates / UI Feels Sluggish

If you're working in a directory with very frequent changes (e.g., a build output directory), you might experience:
- Rapid file list updates
- Cursor jumping
- Sluggish interface

**Solutions:**
1. Reduce `max_reloads_per_second` to limit update frequency
2. Increase `coalesce_delay_ms` to batch more changes together
3. Temporarily disable monitoring in high-activity directories
4. Navigate to a parent directory where changes are less frequent

### Monitoring Stops Working After Errors

TFM includes automatic error recovery:
- If monitoring fails, TFM attempts to reinitialize (up to 3 times)
- If reinitialization fails, TFM switches to fallback polling mode
- If polling also fails, monitoring is disabled for that directory

Check the log file for error messages. Common issues:
- **Permission denied**: You don't have read access to the directory
- **Too many open files**: System limit on file watches exceeded (Linux)
- **Network timeout**: Remote filesystem connection lost

To recover:
1. Navigate to a different directory and back
2. Toggle monitoring off and on
3. Restart TFM
4. Check system limits (Linux: `cat /proc/sys/fs/inotify/max_user_watches`)

### Increasing Watch Limits (Linux)

Linux systems limit the number of directories that can be monitored simultaneously. If you see "too many open files" errors:

```bash
# Check current limit
cat /proc/sys/fs/inotify/max_user_watches

# Temporarily increase limit (until reboot)
sudo sysctl fs.inotify.max_user_watches=524288

# Permanently increase limit
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Performance Considerations

Automatic file monitoring is designed to be lightweight:
- **Memory**: Less than 5MB per watched directory in native mode
- **CPU**: Less than 1% during idle periods
- **Network**: No network traffic for local filesystems

For remote filesystems in fallback mode:
- Polling generates periodic network requests
- Adjust `fallback_poll_interval_s` to balance responsiveness vs. network usage
- Consider disabling monitoring for very slow or metered connections

## When to Disable Monitoring

You might want to disable automatic monitoring if:
- You're working with very large directories (thousands of files)
- You're on a slow or metered network connection
- You're experiencing performance issues
- You prefer manual control over when the file list updates
- You're working in a directory with constant high-frequency changes

Disabling monitoring doesn't affect TFM's core functionality—file lists still update after your actions like navigating, copying, or deleting files.

## Related Features

- **Manual Refresh**: You can always manually refresh the file list regardless of monitoring settings
- **Directory Navigation**: Monitoring automatically follows you as you navigate directories
- **Dual-Pane Operation**: Both panes are monitored independently

## Technical Details

For developers and advanced users interested in implementation details, see:
- `doc/dev/FILE_MONITORING_IMPLEMENTATION.md` - Architecture and implementation
- `src/tfm_file_monitor_manager.py` - Main monitoring coordinator
- `src/tfm_file_monitor_observer.py` - Per-directory monitoring

## Feedback and Issues

If you encounter issues with automatic file monitoring:
1. Check the troubleshooting section above
2. Review TFM logs for error messages
3. Try disabling and re-enabling monitoring
4. Report persistent issues with log excerpts and reproduction steps
