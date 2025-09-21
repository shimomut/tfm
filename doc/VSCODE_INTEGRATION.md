# VSCode Integration Feature

## Overview
The VSCode integration allows you to open the current directory and selected files in Visual Studio Code directly from TFM. The integration intelligently detects git repositories and opens the repository root instead of the current directory when appropriate.

## Features
- Opens VSCode with the current directory from TFM
- Automatically detects git repositories and opens the repo root
- Opens selected files in VSCode (directories are filtered out)
- Handles files with spaces and special characters properly
- Provides error checking for VSCode availability

## Usage
1. Navigate to the desired directory in TFM
2. Optionally select files you want to open
3. Press `x` to open the external programs menu
4. Select "Open in VSCode"

## How It Works
The VSCode wrapper script (`tools/vscode_wrapper.sh`) uses TFM's environment variables:
- `TFM_THIS_DIR`: Current pane directory
- `TFM_THIS_SELECTED`: Space-separated list of selected files (quoted for safety)

### Git Repository Detection
When you're in a directory that's part of a git repository, the script will:
1. Walk up the directory tree to find the `.git` folder
2. Open the repository root directory in VSCode instead of the current subdirectory
3. Still open any selected files from the current directory

### Example Scenarios
- **Regular directory**: Opens the current directory in VSCode
- **Git repository subdirectory**: Opens the git repository root in VSCode
- **With selected files**: Opens the directory/repo root and the selected files (only regular files, directories are skipped)
- **Files with spaces**: Properly handles filenames containing spaces and special characters

## Configuration
The VSCode integration is configured in `src/_config.py` under the `PROGRAMS` section:

```python
{'name': 'Open in VSCode', 'command': ['./tools/vscode_wrapper.sh'], 'options': {'auto_return': True}}
```

The `auto_return: True` option means TFM will automatically return to the interface after launching VSCode without waiting for user input.

## Requirements
- Visual Studio Code must be installed
- The `code` command must be available in PATH
- To install the `code` command:
  1. Open VSCode
  2. Press Cmd+Shift+P (macOS) or Ctrl+Shift+P (Linux/Windows)
  3. Type "Shell Command: Install 'code' command in PATH"
  4. Select and run the command

## Error Handling
The script includes comprehensive error checking:
- Verifies VSCode is installed and available
- Checks that directories exist before opening them
- Validates selected files exist before adding them to the command
- Provides helpful error messages and installation instructions

## Technical Details
- Script location: `tools/vscode_wrapper.sh`
- Uses bash for cross-platform compatibility
- Properly handles quoted filenames from TFM
- Follows the same patterns as other TFM external program wrappers