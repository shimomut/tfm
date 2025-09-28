# TFM External Programs Policy

## Overview

This document establishes the standards and guidelines for creating external programs that integrate with TFM (TUI File Manager). External programs are shell scripts or executables that can be launched from within TFM and have access to TFM's context through environment variables.

## Core Principles

### 1. Use TFM Environment Variables, Not Arguments
- **ALL external programs MUST use TFM environment variables** instead of command-line arguments
- This provides consistent integration with TFM's selection and navigation system
- Arguments make programs less flexible and harder to integrate

### 2. Environment Variable Usage
External programs should use these TFM-provided environment variables:

#### Directory Variables
- `TFM_THIS_DIR` - Current pane's directory path
- `TFM_OTHER_DIR` - Other pane's directory path  
- `TFM_LEFT_DIR` - Left pane's directory path
- `TFM_RIGHT_DIR` - Right pane's directory path

#### Selection Variables (space-separated, quoted filenames)
- `TFM_THIS_SELECTED` - Selected files in current pane
- `TFM_OTHER_SELECTED` - Selected files in other pane
- `TFM_LEFT_SELECTED` - Selected files in left pane
- `TFM_RIGHT_SELECTED` - Selected files in right pane

#### Status Variables
- `TFM_ACTIVE` - Set to "1" when running from TFM

### 3. File Placement
- **ALL external programs MUST be placed in the `/tools` directory**
- Follow the naming convention: `descriptive_name.sh` or `tool_name_wrapper.sh`
- Make scripts executable: `chmod +x tools/script_name.sh`

## Implementation Guidelines

### 1. Script Structure Template
```bash
#!/bin/bash

# script_name.sh - Brief description of what the script does
# This script uses TFM environment variables for integration

# Check if TFM environment variables are set
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Get current directory
CURRENT_DIR="$TFM_THIS_DIR"

# Handle selected files if needed
if [ -n "$TFM_THIS_SELECTED" ]; then
    # Parse selected files (properly handle quoted filenames)
    eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
    
    # Process selected files...
    for file in "${SELECTED_FILES[@]}"; do
        if [ -n "$file" ]; then
            TARGET_PATH="$CURRENT_DIR/$file"
            # Process file...
        fi
    done
else
    # No files selected, work with current directory
    echo "No files selected, working with directory: $CURRENT_DIR"
fi

# Unset TFM environment variables before launching GUI apps (optional)
# unset TFM_THIS_DIR TFM_THIS_SELECTED TFM_OTHER_DIR TFM_OTHER_SELECTED TFM_LEFT_DIR TFM_LEFT_SELECTED TFM_RIGHT_DIR TFM_RIGHT_SELECTED TFM_ACTIVE
```

### 2. Error Handling Requirements
- **ALWAYS validate TFM environment variables are set**
- Check file/directory existence before operations
- Provide clear, informative error messages
- Use appropriate exit codes (0 for success, non-zero for errors)

### 3. Platform-Specific Programs
- Use platform detection when creating platform-specific programs
- Add conditional inclusion in `src/_config.py`:

```python
import platform

# Add platform-specific programs
if platform.system() == 'Darwin':  # macOS
    PROGRAMS.append({'name': 'macOS Program', 'command': ['./tools/macos_program.sh'], 'options': {'auto_return': True}})
elif platform.system() == 'Linux':
    PROGRAMS.append({'name': 'Linux Program', 'command': ['./tools/linux_program.sh'], 'options': {'auto_return': True}})
```

### 4. Configuration Integration
Add programs to `PROGRAMS` list in `src/_config.py`:

```python
PROGRAMS = [
    # ... existing programs ...
    {'name': 'Program Name', 'command': ['./tools/program_script.sh'], 'options': {'auto_return': True}},
]
```

#### Options
- `auto_return: True` - Automatically return to TFM without user input (recommended for GUI apps)
- `auto_return: False` - Wait for user input before returning (default, good for CLI tools)

## Best Practices

### 1. Selection Handling
- **Support both selected files and no selection scenarios**
- When files are selected: operate on selected files
- When no files selected: operate on current directory or cursor position
- Always validate file existence before operations

### 2. Path Handling
- Use `eval` to properly parse quoted filenames from TFM selection variables
- Build absolute paths by combining `TFM_THIS_DIR` with relative filenames
- Handle spaces and special characters in filenames correctly

### 3. GUI Application Integration
- Unset TFM environment variables before launching GUI applications
- Use `auto_return: True` option for seamless user experience
- Provide informative output about what's being launched

### 4. Error Recovery
- Never fail silently - always provide error messages
- Use appropriate exit codes for different error conditions
- Validate all inputs and dependencies before execution

## Examples

### File Operation Script
```bash
# Process selected files or current directory
if [ -n "$TFM_THIS_SELECTED" ]; then
    eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
    for file in "${SELECTED_FILES[@]}"; do
        process_file "$TFM_THIS_DIR/$file"
    done
else
    process_directory "$TFM_THIS_DIR"
fi
```

### GUI Application Launcher
```bash
# Launch GUI app with selected files
eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
TARGET_FILE="$TFM_THIS_DIR/${SELECTED_FILES[0]}"

# Unset TFM variables before GUI launch
unset TFM_THIS_DIR TFM_THIS_SELECTED TFM_OTHER_DIR TFM_OTHER_SELECTED TFM_LEFT_DIR TFM_LEFT_SELECTED TFM_RIGHT_DIR TFM_RIGHT_SELECTED TFM_ACTIVE

exec gui_application "$TARGET_FILE"
```

## Migration Guidelines

When updating existing external programs:

1. **Remove command-line argument parsing**
2. **Add TFM environment variable validation**
3. **Update file/directory handling to use TFM variables**
4. **Test with both selected files and no selection scenarios**
5. **Update program configuration in `_config.py` if needed**

## Testing Requirements

Before adding an external program:

1. **Test with files selected** - Verify it works with single and multiple file selections
2. **Test with no selection** - Verify it handles the no-selection case gracefully
3. **Test with special filenames** - Files with spaces, quotes, and special characters
4. **Test error conditions** - Non-existent files, permission errors, etc.
5. **Test platform compatibility** - Ensure platform-specific programs are properly gated

## Benefits of This Policy

- **Consistent Integration**: All programs work the same way with TFM's selection system
- **Flexible Usage**: Programs adapt to user's current context automatically
- **Better UX**: No need to manually specify file paths or arguments
- **Maintainable**: Standard patterns make programs easier to understand and modify
- **Robust**: Proper error handling and validation prevent issues