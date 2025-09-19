# Archive Creation Feature Implementation

## Overview

This document describes the implementation of the archive creation feature in TFM (Terminal File Manager). The feature allows users to create archive files (ZIP, TAR.GZ, TGZ) from selected files and directories using the P key.

## Feature Description

### Functionality
- **Key Binding**: P key (configurable via `create_archive` action)
- **Supported Formats**: 
  - ZIP (.zip)
  - TAR.GZ (.tar.gz)
  - TGZ (.tgz)
- **Source**: Selected files/directories in the focused pane, or current file if none selected
- **Destination**: Archive is saved in the non-focused pane's directory
- **Format Detection**: Automatic based on filename extension

### User Workflow
1. Navigate to desired directory in one pane
2. Select files/directories to archive (using Space key) or position cursor on single item
3. Press P key to enter archive creation mode
4. Enter filename with appropriate extension (.zip, .tar.gz, or .tgz)
5. Press Enter to create archive or ESC to cancel
6. Archive appears in the opposite pane's directory

## Implementation Details

### Configuration Changes

#### Key Binding Addition
Added `create_archive` action to key bindings in both configuration files:

**src/tfm_config.py** (DefaultConfig class):
```python
KEY_BINDINGS = {
    # ... existing bindings ...
    'create_archive': ['p', 'P'],
}
```

**src/_config.py** (user template):
```python
KEY_BINDINGS = {
    # ... existing bindings ...
    'create_archive': ['p', 'P'],
}
```

### Core Implementation

#### New Imports
Added required modules to `src/tfm_main.py`:
```python
import zipfile
import tarfile
```

#### State Management
Added archive creation mode state variables to FileManager class:
```python
# Create archive mode state
self.create_archive_mode = False
self.create_archive_pattern = ""
```

#### Main Methods

##### `enter_create_archive_mode()`
- Validates that files are available for archiving
- Enters archive creation mode
- Displays prompt for filename input
- Logs what will be archived

##### `exit_create_archive_mode()`
- Exits archive creation mode
- Clears input pattern
- Triggers screen redraw

##### `handle_create_archive_input(key)`
- Handles keyboard input during archive creation
- Supports:
  - ESC: Cancel operation
  - Enter: Create archive
  - Backspace: Remove characters
  - Printable characters: Add to filename

##### `perform_create_archive()`
- Main archive creation logic
- Validates filename and format
- Determines source files and destination path
- Calls appropriate archive creation method
- Handles errors and reports results

##### `detect_archive_format(filename)`
- Detects archive format from file extension
- Returns: 'zip', 'tar.gz', 'tgz', or None
- Case-insensitive matching

##### `create_zip_archive(archive_path, files_to_archive)`
- Creates ZIP archives using zipfile module
- Handles both files and directories
- Preserves directory structure
- Uses ZIP_DEFLATED compression

##### `create_tar_archive(archive_path, files_to_archive)`
- Creates TAR.GZ archives using tarfile module
- Handles both files and directories
- Uses gzip compression
- Preserves directory structure and permissions

### User Interface Integration

#### Status Bar Display
When in archive creation mode, the status bar shows:
```
Archive filename: [user_input]_
```
With help text: `ESC:cancel Enter:create (.zip/.tar.gz/.tgz)`

#### Main Loop Integration
Added archive mode handling to the main event loop:
1. Input handler in mode processing section
2. Key binding handler in regular key processing
3. Mode exclusion in dialog conflict prevention

### Error Handling

The implementation includes comprehensive error handling:
- **Empty filename**: Prevents creation with empty names
- **Unsupported formats**: Validates file extensions
- **File system errors**: Catches and reports I/O exceptions
- **Permission errors**: Handles access denied scenarios
- **Missing files**: Validates source files exist

### Archive Behavior

#### File Selection Logic
1. If files are selected (multi-selection), archive all selected items
2. If no files selected, archive the file/directory under cursor
3. Validates all source files exist before proceeding

#### Directory Handling
- **ZIP**: Recursively adds directory contents with preserved structure
- **TAR.GZ**: Uses tarfile's built-in directory handling
- Both formats maintain relative paths and directory hierarchy

#### Destination Logic
- Archives are always created in the inactive (non-focused) pane's directory
- Allows easy organization: source in one pane, archives in another
- Automatically refreshes destination pane to show new archive

## Testing

### Test Coverage
Created comprehensive test suite in `test_archive_functionality.py`:
- Archive format detection
- ZIP creation and verification
- TAR.GZ creation and verification
- Content validation

### Test Results
All tests pass successfully:
- ✓ Format detection for all supported extensions
- ✓ ZIP archive creation with proper file inclusion
- ✓ TAR.GZ archive creation with directory structure
- ✓ Content verification and cleanup

## Usage Examples

### Creating a ZIP Archive
1. Select multiple files in left pane
2. Press P
3. Enter: `backup.zip`
4. Press Enter
5. Archive appears in right pane

### Creating a TAR.GZ Archive
1. Position cursor on directory
2. Press P  
3. Enter: `project.tar.gz`
4. Press Enter
5. Compressed archive created in opposite pane

### Supported Extensions
- `project.zip` → ZIP format
- `backup.tar.gz` → TAR.GZ format  
- `archive.tgz` → TAR.GZ format (alternative extension)

## Configuration

Users can customize the key binding by modifying their `~/.tfm/config.py`:
```python
KEY_BINDINGS = {
    'create_archive': ['p'],  # Remove 'P' if desired
    # or use different keys:
    'create_archive': ['z', 'Z'],  # Use Z instead
}
```

## Future Enhancements

Potential improvements for future versions:
- Support for additional formats (7z, rar, bz2)
- Compression level selection
- Progress indication for large archives
- Archive extraction feature
- Archive preview/listing feature
- Batch archive operations

## Files Modified

1. **src/tfm_config.py** - Added key binding configuration
2. **src/_config.py** - Added key binding to user template
3. **src/tfm_main.py** - Core implementation
   - Added imports
   - Added state variables
   - Added archive creation methods
   - Added UI integration
   - Added key handling

## Compatibility

- **Python Version**: Requires Python 3.6+ (uses pathlib)
- **Dependencies**: Uses standard library modules (zipfile, tarfile)
- **Platform**: Cross-platform (tested on macOS, should work on Linux/Windows)
- **Terminal**: Works with any curses-compatible terminal

This feature integrates seamlessly with existing TFM functionality and follows established patterns for mode-based operations and user interaction.