# External Programs Feature

## Overview

The External Programs feature allows you to execute custom external programs directly from TFM with access to the current file manager state through environment variables. This extends TFM's functionality by integrating with external tools and scripts.

## Key Bindings

- **x / X**: Open the external programs dialog

Note: The sub-shell feature has been moved to **z / Z** keys to make room for the programs feature.

## Configuration

External programs are configured in the `PROGRAMS` list in your `config.py` file. Each program entry needs:

- `name`: Display name for the program
- `command`: List of command arguments
- `options` (optional): Program-specific options like `auto_return`

### Basic Configuration Example

```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
    {'name': 'Git Log', 'command': ['git', 'log', '--oneline', '-10']},
    {'name': 'Disk Usage', 'command': ['du', '-sh', '*']},
    {'name': 'Python REPL', 'command': ['python3']},
    {'name': 'Quick Git Status', 'command': ['git', 'status', '--short'], 'options': {'auto_return': True}},
]
```

## Environment Variables

When you run external programs, TFM provides information about your current state through environment variables:

- `TFM_THIS_DIR`: Current pane directory
- `TFM_OTHER_DIR`: Other pane directory
- `TFM_THIS_SELECTED`: Selected files in current pane
- `TFM_OTHER_SELECTED`: Selected files in other pane

Your scripts can use these variables to work with your current selection and location.

## Usage

1. Press **x** or **X** to open the programs dialog
2. Use the searchable list to find and select a program
3. Press Enter to execute the selected program
4. The program runs in the current pane's directory
5. Press Enter after the program completes to return to TFM

## Example Use Cases

### Git Operations
- Check repository status
- View recent commits
- Add files to staging

### File Operations
- View file permissions
- Check disk usage
- Find large files

### Development Tools
- Open Python or Node.js REPL
- Run test suites
- Execute build scripts

### System Information
- View system information
- Check memory usage
- List running processes

## Creating Custom Scripts

You can create custom scripts that work with TFM's environment variables. For example:

```bash
#!/bin/bash
# Simple script that processes selected files
echo "Working in: $TFM_THIS_DIR"
echo "Selected files: $TFM_THIS_SELECTED"
```

## Troubleshooting

### Program Not Found
- Make sure the command exists in your PATH
- Use absolute paths for custom scripts

### Permission Denied
- Check that scripts have execute permissions
- Verify file/directory access rights

### No Output
- Some programs may run silently
- Check that the program completed successfully

## Quick Reference

- **x/X**: Open external programs dialog
- **z/Z**: Open sub-shell mode (different feature)
- Use external programs for quick, specific tasks
- Use sub-shell mode for interactive command-line work