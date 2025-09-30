# External Programs Implementation

## Overview

The External Programs feature allows execution of custom external programs directly from TFM with access to the current file manager state through environment variables. This document covers the implementation details for developers.

## Implementation Details

### Configuration System

External programs are configured in the `PROGRAMS` list in the configuration file. Each program entry must have:

- `name`: Display name for the program
- `command`: List of command arguments (for safe subprocess execution)
- `options` (optional): Dictionary of program-specific options

### Available Options

- `auto_return`: Boolean (default: False) - If True, automatically returns to TFM after program execution without waiting for user input

### Example Configuration Structure

```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
    {'name': 'Git Log', 'command': ['git', 'log', '--oneline', '-10']},
    {'name': 'Disk Usage', 'command': ['du', '-sh', '*']},
    {'name': 'List Processes', 'command': ['ps', 'aux']},
    {'name': 'System Info', 'command': ['uname', '-a']},
    {'name': 'Network Connections', 'command': ['netstat', '-tuln']},
    {'name': 'Python REPL', 'command': ['python3']},
    {'name': 'My Script', 'command': ['/path/to/script.sh']},
    # Examples with options:
    {'name': 'Quick Git Status', 'command': ['git', 'status', '--short'], 'options': {'auto_return': True}},
    {'name': 'Compare Directories', 'command': ['./compare_script.sh'], 'options': {'auto_return': True}},
]
```

## Environment Variables System

When executing external programs, TFM sets the following environment variables:

- `TFM_ACTIVE`: Set to '1' to indicate TFM is active
- `TFM_LEFT_DIR`: Path of the left pane directory
- `TFM_RIGHT_DIR`: Path of the right pane directory  
- `TFM_THIS_DIR`: Path of the current (active) pane directory
- `TFM_OTHER_DIR`: Path of the inactive pane directory
- `TFM_LEFT_SELECTED`: Space-separated list of selected files in left pane (quoted)
- `TFM_RIGHT_SELECTED`: Space-separated list of selected files in right pane (quoted)
- `TFM_THIS_SELECTED`: Space-separated list of selected files in current pane (quoted)
- `TFM_OTHER_SELECTED`: Space-separated list of selected files in other pane (quoted)

If no files are selected in a pane, the file under the cursor is used instead.

## Security Implementation

- Commands are executed using `subprocess.run()` with the command as a list, preventing shell injection
- Programs run with the same permissions as TFM
- Be careful with programs that modify files or system state
- Always use absolute paths for custom scripts to avoid PATH issues

## Integration with Scripts

### Bash Script Integration

```bash
#!/bin/bash
# Example script that uses TFM environment variables

echo "Current directory: $TFM_THIS_DIR"
echo "Selected files: $TFM_THIS_SELECTED"

# Process selected files
for file in $TFM_THIS_SELECTED; do
    echo "Processing: $file"
    # Your processing logic here
done
```

### Python Script Integration

```python
#!/usr/bin/env python3
# Example Python script

import os

current_dir = os.environ.get('TFM_THIS_DIR', '.')
selected_files = os.environ.get('TFM_THIS_SELECTED', '').split()

print(f"Working in: {current_dir}")
for file in selected_files:
    print(f"Selected: {file}")
```

## Architecture Comparison

| Feature | External Programs (x) | Sub-shell Mode (z) |
|---------|----------------------|-------------------|
| Purpose | Execute specific programs | Interactive shell session |
| Configuration | Pre-configured program list | Uses default shell |
| Environment | TFM variables set | TFM variables + shell prompt |
| Interaction | Program runs and exits | Full shell session |
| Use Case | Quick operations, scripts | Extended command-line work |

Both features complement each other - use external programs for quick, specific tasks and sub-shell mode for interactive command-line work.

## Error Handling

### Program Not Found
- Ensure the command exists in your PATH or use absolute paths
- Check that the command list is properly formatted

### Permission Denied
- Verify the program has execute permissions
- Check file/directory permissions for the operation

### Environment Variables Not Set
- Ensure you're running the program through TFM's external programs feature
- Check that `TFM_ACTIVE` environment variable is set to '1'