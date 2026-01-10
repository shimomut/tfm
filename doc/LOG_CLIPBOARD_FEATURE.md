# Log Clipboard Copy Feature

## Overview

TFM provides the ability to copy log pane contents to the system clipboard in desktop mode. This feature allows you to easily share log information with others or save it for later reference.

## Availability

This feature is only available when running TFM in **desktop mode**. It is not available in terminal mode.

## Usage

### Accessing the Feature

The log clipboard copy feature is accessed through the **Edit** menu:

1. Open TFM in desktop mode
2. Click on the **Edit** menu in the menu bar
3. Select one of the clipboard copy options:
   - **Copy Visible Logs to Clipboard** - Copies only the log lines currently visible in the log pane
   - **Copy All Logs to Clipboard** - Copies all log messages, including those scrolled out of view

### Copy Visible Logs

This option copies only the log lines that are currently visible in the log pane. The copied content reflects:
- Your current scroll position in the log pane
- The number of lines that fit in the visible area
- The exact formatting as displayed on screen

**Use this when:**
- You want to share a specific section of the logs
- You've scrolled to a particular area of interest
- You only need recent log messages

### Copy All Logs

This option copies all log messages from the current session, including:
- All messages from application startup
- Messages that have scrolled out of view
- The complete log history (up to the configured maximum)

**Use this when:**
- You need the complete log history
- You're troubleshooting an issue and need full context
- You want to save all logs for later analysis

## Log Format

Copied logs preserve the same format as displayed in the log pane:
- Timestamp (HH:MM:SS format)
- Logger name (component that generated the message)
- Log level (INFO, WARNING, ERROR)
- Message content

Example:
```
14:23:45 [Main  ] INFO: Application started
14:23:46 [FileOp] INFO: Loaded directory: /home/user/documents
14:23:47 [Main  ] WARNING: Configuration file not found, using defaults
```

## Tips

- **Scroll position matters**: When using "Copy Visible Logs", make sure you've scrolled to the section you want to copy
- **Log pane size**: The visible logs option copies based on the current log pane height. Adjust the log divider if needed
- **Maximum logs**: TFM stores a limited number of log messages (default: 1000). Very old messages may be discarded
- **Paste anywhere**: After copying, you can paste the logs into any text editor, email, or document

## Keyboard Shortcuts

Currently, there are no keyboard shortcuts assigned to these commands. They must be accessed through the Edit menu.

## Related Features

- **Log Pane**: View real-time log messages at the bottom of the TFM window
- **Log Scrolling**: Use mouse wheel or keyboard shortcuts to scroll through logs
- **Log Divider**: Adjust the log pane height by moving the divider
