# Archive Extraction Feature Implementation

## Overview

The archive extraction feature allows users to extract archive files using the `U` key. When a supported archive file is selected in the focused pane, pressing `U` will extract its contents to a new directory in the non-focused pane.

## Key Binding

- **Key**: `U` or `u`
- **Action**: `extract_archive`
- **Function**: Extract selected archive file to the other pane

## Supported Archive Formats

The feature supports the following archive formats:

1. **ZIP files** (`.zip`)
2. **TAR.GZ files** (`.tar.gz`) 
3. **TGZ files** (`.tgz`)

## Behavior

### Basic Operation

1. **Selection**: Navigate to an archive file in either pane
2. **Extraction**: Press `U` to extract the archive
3. **Target**: Contents are extracted to the non-focused pane
4. **Directory Creation**: A new directory is created with the archive's base name (without extension)
5. **Refresh**: The target pane is automatically refreshed to show the extracted contents

### Directory Naming

The extraction directory is named using the archive's base name:

- `demo_project.zip` → `demo_project/`
- `backup.tar.gz` → `backup/`
- `source.tgz` → `source/`

### Conflict Handling

If a directory with the same name already exists in the target location:

1. A confirmation dialog appears asking whether to overwrite
2. **Yes**: The existing directory is removed and extraction proceeds
3. **No**: The extraction is cancelled

### Error Handling

The feature handles various error conditions:

- **Non-archive files**: Shows error message for unsupported file types
- **Directories**: Shows error message if a directory is selected instead of a file
- **Extraction errors**: Shows error message and cleans up partially created directories
- **Permission errors**: Shows appropriate error messages

## Implementation Details

### Configuration Changes

#### Key Binding Addition

Added `extract_archive` action to key bindings in both configuration files:

**src/tfm_config.py** (DefaultConfig class):
```python
'extract_archive': ['u', 'U'],
```

**src/_config.py** (user template):
```python
'extract_archive': ['u', 'U'],
```

### Core Functions

#### `extract_selected_archive()`

Main entry point for the extraction feature:
- Validates the selected file is an archive
- Determines extraction directory name
- Handles existing directory conflicts
- Initiates the extraction process

#### `get_archive_basename(filename)`

Extracts the base name from archive filenames:
- Removes `.tar.gz` extension (7 characters)
- Removes `.tgz` extension (4 characters)  
- Removes `.zip` extension (4 characters)
- Falls back to `Path.stem` for other cases

#### `perform_extraction(archive_file, extract_dir, archive_format, other_pane)`

Performs the actual extraction:
- Creates the target directory
- Calls format-specific extraction function
- Handles errors and cleanup
- Refreshes the target pane

#### `extract_zip_archive(archive_file, extract_dir)`

Extracts ZIP archives using Python's `zipfile` module:
```python
with zipfile.ZipFile(archive_file, 'r') as zipf:
    zipf.extractall(extract_dir)
```

#### `extract_tar_archive(archive_file, extract_dir)`

Extracts TAR.GZ/TGZ archives using Python's `tarfile` module:
```python
with tarfile.open(archive_file, 'r:gz') as tarf:
    tarf.extractall(extract_dir)
```

### Integration with Main Loop

The key binding is handled in the main run loop:

```python
elif self.is_key_for_action(key, 'extract_archive'):  # Extract archive
    self.extract_selected_archive()
```

## Usage Examples

### Example 1: ZIP File Extraction

1. Navigate to `project.zip` in the left pane
2. Press `U`
3. A `project/` directory is created in the right pane
4. All ZIP contents are extracted to `project/`

### Example 2: TAR.GZ File Extraction

1. Navigate to `backup.tar.gz` in the right pane
2. Press `U`  
3. A `backup/` directory is created in the left pane
4. All TAR.GZ contents are extracted to `backup/`

### Example 3: Conflict Resolution

1. Navigate to `source.tgz` 
2. Press `U`
3. If `source/` already exists, confirmation dialog appears:
   - "Directory 'source' already exists. Overwrite?"
   - Choose Yes to replace, No to cancel

## Testing

### Automated Tests

The feature includes comprehensive tests in `test/test_extract_archive.py`:

- **Format Detection**: Tests archive format recognition
- **Basename Extraction**: Tests directory name generation
- **ZIP Extraction**: Tests ZIP file extraction functionality
- **TAR Extraction**: Tests TAR.GZ/TGZ extraction functionality
- **Key Binding**: Tests configuration integration

### Demo Archives

Demo archives can be created using `test/demo_extract_archive.py`:

- Creates sample ZIP, TAR.GZ, and TGZ files
- Provides usage instructions
- Demonstrates the feature capabilities

## Dependencies

The feature uses Python standard library modules:

- `zipfile`: For ZIP archive handling
- `tarfile`: For TAR.GZ/TGZ archive handling
- `pathlib.Path`: For path manipulation
- `shutil`: For directory operations

## Error Messages

The feature provides clear error messages for various scenarios:

- `"Selected item is not a file"` - When a directory is selected
- `"'filename' is not a supported archive format"` - For unsupported files
- `"Supported formats: .zip, .tar.gz, .tgz"` - Format guidance
- `"Error extracting archive: {error}"` - For extraction failures
- `"Archive extracted successfully to: {path}"` - Success confirmation

## Future Enhancements

Potential improvements for future versions:

- Support for additional archive formats (RAR, 7Z, etc.)
- Progress indication for large archives
- Selective extraction (choose specific files)
- Archive preview/listing before extraction
- Compression level detection and display
- Batch extraction of multiple archives

## Integration Notes

The feature integrates seamlessly with existing TFM functionality:

- Uses existing confirmation dialog system
- Follows established error handling patterns
- Maintains consistent logging and user feedback
- Respects pane focus and navigation paradigms
- Automatically refreshes affected panes