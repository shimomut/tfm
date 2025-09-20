# BeyondCompare Integration

## Overview

BeyondCompare has been successfully integrated as an external program in TFM. This allows you to quickly launch BeyondCompare to compare the directories shown in the left and right panes of TFM.

## Setup

The integration consists of:

1. **Wrapper Script**: `bcompare_wrapper.sh` - A shell script that launches BeyondCompare with the appropriate directories
2. **Configuration**: BeyondCompare entry added to the `PROGRAMS` list in both the template config and user config

## Usage

1. **Start TFM**: Run `python3 tfm.py` or `python3 src/tfm_main.py`
2. **Navigate**: Use TFM to navigate to the directories you want to compare
   - Left pane: Navigate to the first directory
   - Right pane: Navigate to the second directory
3. **Launch BeyondCompare**: Press `x` to open the external programs dialog
4. **Select BeyondCompare**: Use the searchable list to find and select "BeyondCompare"
5. **Compare**: BeyondCompare will launch with the left and right pane directories loaded

## Environment Variables

When BeyondCompare is launched, the following TFM environment variables are available:

- `TFM_LEFT_DIR`: Path of the left pane directory
- `TFM_RIGHT_DIR`: Path of the right pane directory
- `TFM_THIS_DIR`: Path of the current (active) pane directory
- `TFM_OTHER_DIR`: Path of the inactive pane directory
- `TFM_ACTIVE`: Set to '1' to indicate TFM is active

The wrapper script uses `TFM_LEFT_DIR` and `TFM_RIGHT_DIR` to launch BeyondCompare with the correct directories.

## Files Created/Modified

### New Files
- `bcompare_wrapper.sh`: Wrapper script that launches BeyondCompare
- `test_bcompare.py`: Test script to verify the integration
- `BEYONDCOMPARE_INTEGRATION.md`: This documentation file

### Modified Files
- `src/_config.py`: Added BeyondCompare to the default PROGRAMS list
- `~/.tfm/config.py`: Added BeyondCompare to the user's PROGRAMS list

## Wrapper Script Details

The `bcompare_wrapper.sh` script:

1. Checks if BeyondCompare (`bcompare`) is installed and available in PATH
2. Verifies that TFM environment variables are set
3. Launches BeyondCompare with the left and right directories: `bcompare "$TFM_LEFT_DIR" "$TFM_RIGHT_DIR"`

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
- The script should be executable: `chmod +x bcompare_wrapper.sh`

## Customization

You can customize the BeyondCompare integration by:

1. **Modifying the wrapper script**: Add additional BeyondCompare command-line options
2. **Updating the config**: Change the program name or command in `~/.tfm/config.py`
3. **Adding more comparison tools**: Create similar integrations for other diff/comparison tools

## Example Use Cases

- **Project Comparison**: Compare different versions of a project directory
- **Backup Verification**: Compare original and backup directories
- **Deployment Checking**: Compare local and deployed versions
- **Code Review**: Compare different branches or versions of code
- **File Synchronization**: Identify differences before syncing directories