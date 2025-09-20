# External Programs Feature

## Overview

The External Programs feature allows you to execute custom external programs directly from TFM with access to the current file manager state through environment variables. This extends TFM's functionality by integrating with external tools and scripts.

## Key Bindings

- **x / X**: Open the external programs dialog

Note: The sub-shell feature has been moved to **z / Z** keys to make room for the programs feature.

## Configuration

External programs are configured in the `PROGRAMS` list in your `config.py` file. Each program entry must have:

- `name`: Display name for the program
- `command`: List of command arguments (for safe subprocess execution)

### Example Configuration

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
]
```

## Environment Variables

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

## Usage

1. Press **x** or **X** to open the programs dialog
2. Use the searchable list to find and select a program
3. Press Enter to execute the selected program
4. The program runs in the current pane's directory with TFM environment variables set
5. Press Enter after the program completes to return to TFM

## Example Use Cases

### Git Operations
```python
{'name': 'Git Status', 'command': ['git', 'status']},
{'name': 'Git Add Selected', 'command': ['git', 'add'] + ['$TFM_THIS_SELECTED']},
{'name': 'Git Commit', 'command': ['git', 'commit', '-m']},
```

### File Operations
```python
{'name': 'File Permissions', 'command': ['ls', '-la']},
{'name': 'Disk Usage', 'command': ['du', '-sh', '*']},
{'name': 'Find Large Files', 'command': ['find', '.', '-size', '+100M']},
```

### Development Tools
```python
{'name': 'Python REPL', 'command': ['python3']},
{'name': 'Node.js REPL', 'command': ['node']},
{'name': 'Run Tests', 'command': ['pytest']},
```

### System Information
```python
{'name': 'System Info', 'command': ['uname', '-a']},
{'name': 'Memory Usage', 'command': ['free', '-h']},
{'name': 'Process List', 'command': ['ps', 'aux']},
```

## Security Notes

- Commands are executed using `subprocess.run()` with the command as a list, preventing shell injection
- Programs run with the same permissions as TFM
- Be careful with programs that modify files or system state
- Always use absolute paths for custom scripts to avoid PATH issues

## Integration with Scripts

Your custom scripts can access TFM state through environment variables:

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

## Troubleshooting

### Program Not Found
- Ensure the command exists in your PATH or use absolute paths
- Check that the command list is properly formatted

### Permission Denied
- Verify the program has execute permissions
- Check file/directory permissions for the operation

### Environment Variables Not Set
- Ensure you're running the program through TFM's external programs feature
- Check that `TFM_ACTIVE` environment variable is set to '1'

## Comparison with Sub-shell Mode

| Feature | External Programs (x) | Sub-shell Mode (z) |
|---------|----------------------|-------------------|
| Purpose | Execute specific programs | Interactive shell session |
| Configuration | Pre-configured program list | Uses default shell |
| Environment | TFM variables set | TFM variables + shell prompt |
| Interaction | Program runs and exits | Full shell session |
| Use Case | Quick operations, scripts | Extended command-line work |

Both features complement each other - use external programs for quick, specific tasks and sub-shell mode for interactive command-line work.