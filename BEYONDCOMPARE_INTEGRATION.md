# BeyondCompare Integration

## Overview

BeyondCompare has been successfully integrated as external programs in TFM. This provides two comparison modes:

1. **Directory Comparison**: Compare the directories shown in the left and right panes
2. **File Comparison**: Compare selected files from the left and right panes

## Setup

The integration consists of:

1. **Directory Wrapper Script**: `bcompare_dirs_wrapper.sh` - Launches BeyondCompare with left and right pane directories
2. **File Wrapper Script**: `bcompare_files_wrapper.sh` - Launches BeyondCompare with selected files from both panes
3. **Configuration**: Two BeyondCompare entries added to the `PROGRAMS` list with `auto_return: True` option enabled

## Usage

### Directory Comparison

1. **Start TFM**: Run `python3 tfm.py` or `python3 src/tfm_main.py`
2. **Navigate**: Use TFM to navigate to the directories you want to compare
   - Left pane: Navigate to the first directory
   - Right pane: Navigate to the second directory
3. **Launch**: Press `x` to open the external programs dialog
4. **Select**: Choose "Compare Directories (BeyondCompare)" from the list
5. **Compare**: BeyondCompare will launch with the left and right pane directories loaded

### File Comparison

1. **Start TFM**: Run `python3 tfm.py` or `python3 src/tfm_main.py`
2. **Navigate**: Navigate to directories containing the files you want to compare
3. **Select Files**: 
   - In the left pane: Navigate to and select a file (using Space or cursor position)
   - In the right pane: Navigate to and select a file to compare against
4. **Launch**: Press `x` to open the external programs dialog
5. **Select**: Choose "Compare Files (BeyondCompare)" from the list
6. **Compare**: BeyondCompare will launch with the selected files loaded for comparison

**Note**: For file comparison, if no files are explicitly selected, the files under the cursor in each pane will be used.

**Auto Return**: Both BeyondCompare programs are configured with `auto_return: True`, which means they will automatically return to TFM after BeyondCompare is closed, without requiring you to press Enter.

## Environment Variables

When BeyondCompare is launched, the following TFM environment variables are available:

- `TFM_LEFT_DIR`: Path of the left pane directory
- `TFM_RIGHT_DIR`: Path of the right pane directory
- `TFM_THIS_DIR`: Path of the current (active) pane directory
- `TFM_OTHER_DIR`: Path of the inactive pane directory
- `TFM_LEFT_SELECTED`: Selected files in the left pane (space-separated, quoted)
- `TFM_RIGHT_SELECTED`: Selected files in the right pane (space-separated, quoted)
- `TFM_THIS_SELECTED`: Selected files in the current pane (space-separated, quoted)
- `TFM_OTHER_SELECTED`: Selected files in the other pane (space-separated, quoted)
- `TFM_ACTIVE`: Set to '1' to indicate TFM is active

**Directory Comparison**: Uses `TFM_LEFT_DIR` and `TFM_RIGHT_DIR`
**File Comparison**: Uses `TFM_LEFT_SELECTED`, `TFM_RIGHT_SELECTED`, `TFM_LEFT_DIR`, and `TFM_RIGHT_DIR`

## Files Created/Modified

### New Files
- `bcompare_dirs_wrapper.sh`: Wrapper script for directory comparison
- `bcompare_files_wrapper.sh`: Wrapper script for file comparison
- `test_bcompare.py`: Test script to verify the integration
- `BEYONDCOMPARE_INTEGRATION.md`: This documentation file

### Modified Files
- `src/_config.py`: Added both BeyondCompare programs to the default PROGRAMS list
- `~/.tfm/config.py`: Added both BeyondCompare programs to the user's PROGRAMS list

## Wrapper Script Details

### Directory Comparison (`bcompare_dirs_wrapper.sh`)

1. Checks if BeyondCompare (`bcompare`) is installed and available in PATH
2. Verifies that TFM directory environment variables are set
3. Launches BeyondCompare with the left and right directories: `bcompare "$TFM_LEFT_DIR" "$TFM_RIGHT_DIR"`

### File Comparison (`bcompare_files_wrapper.sh`)

1. Checks if BeyondCompare (`bcompare`) is installed and available in PATH
2. Verifies that TFM file selection and directory environment variables are set
3. Extracts the first selected file from each pane (removes quotes if present)
4. Builds full file paths using directory + filename
5. Verifies both files exist
6. Launches BeyondCompare with the selected files: `bcompare "$LEFT_PATH" "$RIGHT_PATH"`

## Prerequisites

- **BeyondCompare**: Must be installed and the `bcompare` command must be available in your PATH
- **TFM**: The external programs feature must be working (press `x` to test)

## Installation Notes

If BeyondCompare is not installed, you can:

1. **macOS**: Download from [Beyond Compare website](https://www.scootersoftware.com/) or install via Homebrew:
   ```bash
   brew install --cask beyond-compare
   ```

2. **Linux**: Install the appropriate package for your distribution or download from the website

3. **Windows**: Download and install from the Beyond Compare website

## Testing

Run the test script to verify the integration:

```bash
python3 test_bcompare.py
```

This will check:
- BeyondCompare is properly configured in the programs list
- The wrapper script exists and is executable
- Mock environment variables work correctly

## Troubleshooting

### "Command not found: bcompare"
- Ensure BeyondCompare is installed
- Verify `bcompare` is in your PATH: `which bcompare`
- On macOS, you may need to add BeyondCompare to your PATH or use the full path

### "TFM environment variables not set"
- This error occurs if you run the wrapper script directly outside of TFM
- Always launch BeyondCompare through TFM's external programs feature (press `x`)

### "Wrapper script not found"
- Ensure the wrapper script path in the config is correct
- The script should be executable: `chmod +x bcompare_dirs_wrapper.sh`

## Customization

You can customize the BeyondCompare integration by:

1. **Modifying the wrapper script**: Add additional BeyondCompare command-line options
2. **Updating the config**: Change the program name or command in `~/.tfm/config.py`
3. **Adding more comparison tools**: Create similar integrations for other diff/comparison tools

## Example Use Cases

### Directory Comparison
- **Project Comparison**: Compare different versions of a project directory
- **Backup Verification**: Compare original and backup directories
- **Deployment Checking**: Compare local and deployed versions
- **File Synchronization**: Identify differences before syncing directories

### File Comparison
- **Code Review**: Compare different versions of the same file
- **Configuration Comparison**: Compare config files between environments
- **Document Comparison**: Compare different versions of documents
- **Merge Conflict Resolution**: Compare conflicting file versions
- **Template Comparison**: Compare template files with customized versions