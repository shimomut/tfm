# Compare & Select Feature Enhancement: Directory Support

## Overview

The Compare & Select feature (W/w key) has been enhanced to handle both files and directories, not just files. This allows users to select matching items of both types based on comparison criteria with the other pane.

## Key Binding

- **W/w**: Show compare selection dialog

## Enhanced Functionality

### What Changed

**Before**: Only compared and selected files, ignoring directories entirely.

**After**: Compares and selects both files and directories based on the selected criteria.

### Comparison Criteria

The feature offers three comparison modes that now work for both files and directories:

#### 1. By Filename
- **Files**: Matches files with the same name
- **Directories**: Matches directories with the same name
- **Type Safety**: Files only match with files, directories only match with directories

#### 2. By Filename and Size
- **Files**: Matches files with the same name and file size
- **Directories**: Matches directories with the same name (size is not applicable for directories)
- **Type Safety**: Maintains file vs directory distinction

#### 3. By Filename, Size, and Timestamp
- **Files**: Matches files with the same name, size, and modification time (within 1 second tolerance)
- **Directories**: Matches directories with the same name and modification time (within 1 second tolerance)
- **Type Safety**: Files and directories are compared separately

## Usage Examples

### Example 1: Selecting Matching Files and Directories

**Left Pane Contents:**
```
file1.txt
file2.txt
documents/
images/
config.json
```

**Right Pane Contents:**
```
file1.txt
file3.txt
documents/
videos/
config.json
```

**Action**: Press `W` → Select "By filename"

**Result**: Selects `file1.txt`, `documents/`, and `config.json` in the left pane (3 items: 2 files and 1 directory)

### Example 2: Type Safety

**Left Pane Contents:**
```
data (file)
logs/
```

**Right Pane Contents:**
```
data/ (directory)
logs/
```

**Action**: Press `W` → Select "By filename"

**Result**: Only selects `logs/` because:
- `data` (file) doesn't match `data/` (directory) - different types
- `logs/` (directory) matches `logs/` (directory) - same type and name

## User Interface Improvements

### Enhanced Feedback Messages

The feature now provides more descriptive feedback about what was selected:

- **Mixed Selection**: "Selected 5 items (3 files and 2 directories) matching by filename"
- **Files Only**: "Selected 3 files matching by filename and size"
- **Directories Only**: "Selected 2 directories matching by filename, size, and timestamp"

### Updated Help Text

The help dialog now shows: "Compare selection (select files/directories matching other pane)"

## Technical Implementation

### Key Changes

1. **Expanded Item Processing**: Both `file_path.is_file()` and `file_path.is_dir()` are now processed
2. **Type-Safe Matching**: Items are only matched if they are the same type (file vs file, directory vs directory)
3. **Directory-Appropriate Comparisons**: 
   - Size comparison is skipped for directories (always considered matching)
   - Timestamp comparison works for both files and directories
4. **Enhanced Error Handling**: Robust handling of permission errors and missing files/directories
5. **Improved User Feedback**: Detailed messages showing counts of files and directories selected

### Size Handling for Directories

- **"By filename and size"**: Directories are matched by name only (size is not meaningful for directories)
- **"By filename, size, and timestamp"**: Directories are matched by name and timestamp only

### Error Resilience

The implementation includes comprehensive error handling:
- Permission errors when accessing file/directory stats
- Missing files or directories
- Unexpected filesystem errors
- Graceful degradation when stats cannot be obtained

## Benefits

1. **Consistency**: Users can now select both files and directories using the same interface
2. **Efficiency**: Batch operations on mixed content types (files and directories)
3. **Flexibility**: Useful for synchronization tasks involving directory structures
4. **Safety**: Type-safe matching prevents accidental mismatches between files and directories

## Use Cases

### Directory Synchronization
Compare directory structures between panes and select matching directories for batch operations.

### Mixed Content Management
Select both files and directories that exist in both panes for copying, moving, or other operations.

### Backup Verification
Identify which files and directories exist in both source and backup locations.

### Project Comparison
Compare project structures and select common elements between different versions or branches.

## Backward Compatibility

This enhancement is fully backward compatible:
- Existing workflows continue to work unchanged
- File-only selections work exactly as before
- No changes to key bindings or basic operation
- All existing comparison criteria work the same way for files

## Testing

The feature includes comprehensive testing:
- Verification of file and directory selection
- Type safety testing (files don't match directories with same name)
- Error handling validation
- User feedback message verification

See `test/test_compare_selection_directories.py` for detailed test cases.