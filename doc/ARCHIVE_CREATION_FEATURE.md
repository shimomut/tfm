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
- **Destination**: Archive is saved in the inactive (non-focused) pane's directory
- **Format Detection**: Automatic based on filename extension

### User Workflow
1. Navigate to desired directory in one pane
2. Select files/directories to archive (using Space key) or position cursor on single item
3. Press P key to enter archive creation mode
4. **NEW**: For single files/directories, filename is pre-populated with basename + dot (e.g., "document.txt" → "document.")
5. Enter or complete filename with appropriate extension (.zip, .tar.gz, or .tgz)
6. Press Enter to create archive or ESC to cancel
7. Archive appears in the inactive pane's directory

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
- **NEW**: Determines default filename for single file/directory selections
- Enters archive creation mode with pre-populated filename
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
- **NEW**: Provides real-time progress updates during creation

##### `create_tar_archive(archive_path, files_to_archive)`
- Creates TAR.GZ archives using tarfile module
- Handles both files and directories
- Uses gzip compression
- Preserves directory structure and permissions
- **NEW**: Provides real-time progress updates during creation

##### `update_archive_progress(current_file, processed, total)`
- **MIGRATED**: Legacy method that now delegates to the unified ProgressManager
- Maintains compatibility while using the new progress system
- Forces screen refresh to show real-time updates
- Progress formatting now handled by ProgressManager

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
3. Enter: `backup.zip` (no default for multiple files)
4. Press Enter
5. Archive appears in inactive pane

### Creating a TAR.GZ Archive from Single Directory
1. Position cursor on directory named "project"
2. Press P  
3. Dialog shows: `Archive filename: project.` (pre-populated)
4. Type: `tar.gz` to complete as `project.tar.gz`
5. Press Enter
6. Compressed archive created in inactive pane

### Creating Archive from Single File
1. Position cursor on file "document.txt"
2. Press P
3. Dialog shows: `Archive filename: document.` (pre-populated)
4. Type: `zip` to complete as `document.zip`
5. Press Enter
6. Archive created in inactive pane

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

## Progress Indication

### Real-time Progress Updates
When creating large archives, TFM now displays real-time progress information in the status bar:

- **Current File**: Shows the name of the file currently being processed
- **Progress Counter**: Displays processed/total files (e.g., "45/120")
- **Percentage**: Shows completion percentage (e.g., "37%")
- **Status Format**: `Creating archive... 45/120 (37%) - filename.txt`

### Progress Features
- **File Count Calculation**: Pre-scans directories to provide accurate total file counts
- **Real-time Updates**: Status bar updates for each file processed
- **Long Filename Handling**: Truncates long filenames to fit in the status bar
- **Automatic Cleanup**: Progress display clears when archive creation completes or fails

### Implementation Details
The progress system works by:
1. **Pre-scanning**: Counts all files that will be archived before starting
2. **Progress Tracking**: Updates a counter for each file processed
3. **Status Display**: Shows progress in the status bar with current filename
4. **Screen Refresh**: Forces screen updates to show progress in real-time

This enhancement significantly improves user experience when creating large archives, providing clear feedback about the operation's progress and estimated completion.

## Future Enhancements

Potential improvements for future versions:
- Support for additional formats (7z, rar, bz2)
- Compression level selection
- Archive extraction feature
- Archive preview/listing feature
- Batch archive operations
- Progress indication for archive extraction

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