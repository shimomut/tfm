# TFM Archive Operations System

## Overview

The TFM Archive Operations System provides comprehensive archive creation and extraction capabilities with full cross-storage support. This modular system allows users to create archives from files in any supported storage (local, S3, etc.) and save them to any supported storage destination.

## Architecture

The archive operations are implemented using a clean modular architecture with separation of concerns:

### Core Components

#### ArchiveOperations Class (`src/tfm_archive.py`)
- **Purpose**: Core archive functionality with cross-storage support
- **Responsibilities**:
  - Archive format detection
  - Archive creation (ZIP, TAR.GZ, TAR.BZ2, TAR.XZ, etc.)
  - Archive extraction with overwrite handling
  - Cross-storage operations (local ↔ remote)
  - Archive content listing
  - Cache invalidation integration

#### ArchiveUI Class (`src/tfm_archive.py`)
- **Purpose**: UI-specific archive operations for the file manager
- **Responsibilities**:
  - Archive creation mode handling
  - User confirmation dialogs
  - Progress tracking integration
  - File selection logic
  - Error handling and user feedback
  - Integration with FileManager's UI components

#### FileManager Integration
- **Delegation**: FileManager delegates archive operations to specialized classes
- **Backward Compatibility**: All existing method signatures preserved
- **UI Integration**: Seamless integration with TFM's interface

## Supported Archive Formats

### Multi-file Archives
- **ZIP** (.zip) - Cross-platform compatibility, good compression
- **TAR** (.tar) - Uncompressed archive, preserves Unix permissions
- **TAR.GZ** (.tar.gz, .tgz) - Good compression, widely supported
- **TAR.BZ2** (.tar.bz2, .tbz2) - Better compression than gzip
- **TAR.XZ** (.tar.xz, .txz) - Best compression, slower processing

### Single-file Compression
- **GZIP** (.gz) - Fast compression for single files
- **BZIP2** (.bz2) - Better compression for single files
- **XZ** (.xz) - Best compression for single files

## Cross-Storage Support

The archive operations support all combinations of source and destination storage types:

- **Local to Local** - Traditional archive operations
- **S3 to S3** - Create archives from S3 files, save to S3
- **Local to S3** - Archive local files, save archive to S3
- **S3 to Local** - Archive S3 files, save archive locally

### Cross-Storage Implementation

Cross-storage operations use temporary files when necessary:

1. **Source files** are downloaded to temporary storage if remote
2. **Archive operations** are performed locally for reliability
3. **Result archives** are uploaded to destination if remote
4. **Temporary files** are automatically cleaned up

## User Interface Integration

### Key Bindings

- **P** or **p** - Create archive from selected files
- **U** or **u** - Extract selected archive file

### Archive Creation Workflow

1. **File Selection**: Select files/directories to archive using **Space**
2. **Initiate Creation**: Press **P** to create archive
3. **Filename Input**: Enter archive filename with appropriate extension
4. **Pre-population**: For single files/directories, filename is pre-populated with basename + dot
5. **Creation**: Archive is created in the other pane's directory
6. **Progress Tracking**: Real-time progress display for large operations

### Archive Extraction Workflow

1. **Navigate**: Navigate to an archive file
2. **Initiate Extraction**: Press **U** to extract
3. **Destination**: Archive extracts to new directory in other pane
4. **Conflict Handling**: Confirmation dialog for existing directories
5. **Progress Tracking**: Progress display for large archives

## Technical Implementation

### Archive Creation

#### Format Detection
```python
def detect_archive_format(filename):
    """Detect archive format from file extension"""
    ext = filename.lower()
    if ext.endswith('.zip'):
        return 'zip'
    elif ext.endswith('.tar.gz') or ext.endswith('.tgz'):
        return 'tar.gz'
    elif ext.endswith('.tar.bz2') or ext.endswith('.tbz2'):
        return 'tar.bz2'
    elif ext.endswith('.tar.xz') or ext.endswith('.txz'):
        return 'tar.xz'
    return None
```

#### ZIP Archive Creation
```python
def create_zip_archive(self, archive_path, files_to_archive):
    """Create ZIP archive with progress tracking"""
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_archive:
            if file_path.is_file():
                zipf.write(file_path, file_path.name)
            elif file_path.is_dir():
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        file_full_path = Path(root) / file
                        arcname = file_full_path.relative_to(file_path.parent)
                        zipf.write(file_full_path, arcname)
                        # Progress update
                        self.update_progress(file_full_path, processed, total)
```

#### TAR Archive Creation
```python
def create_tar_archive(self, archive_path, files_to_archive, compression='gz'):
    """Create TAR archive with specified compression"""
    mode = f'w:{compression}' if compression else 'w'
    with tarfile.open(archive_path, mode) as tarf:
        for file_path in files_to_archive:
            arcname = file_path.name
            tarf.add(file_path, arcname=arcname)
            # Progress update
            self.update_progress(file_path, processed, total)
```

### Archive Extraction

#### Directory Naming
The extraction directory is named using the archive's base name:
- `demo_project.zip` → `demo_project/`
- `backup.tar.gz` → `backup/`
- `source.tgz` → `source/`

#### ZIP Extraction
```python
def extract_zip_archive(self, archive_file, extract_dir):
    """Extract ZIP archive to specified directory"""
    with zipfile.ZipFile(archive_file, 'r') as zipf:
        zipf.extractall(extract_dir)
```

#### TAR Extraction
```python
def extract_tar_archive(self, archive_file, extract_dir):
    """Extract TAR archive to specified directory"""
    with tarfile.open(archive_file, 'r:*') as tarf:
        tarf.extractall(extract_dir)
```

### Progress Tracking

#### Real-time Progress Updates
When creating or extracting large archives, TFM displays real-time progress information:

- **Current File**: Shows the name of the file currently being processed
- **Progress Counter**: Displays processed/total files (e.g., "45/120")
- **Percentage**: Shows completion percentage (e.g., "37%")
- **Status Format**: `Creating archive... 45/120 (37%) - filename.txt`

#### Progress Implementation
```python
def update_archive_progress(self, current_file, processed, total):
    """Update progress display during archive operations"""
    if self.progress_manager:
        percentage = int((processed / total) * 100) if total > 0 else 0
        status = f"Processing... {processed}/{total} ({percentage}%) - {current_file.name}"
        self.progress_manager.update_status(status)
        self.force_refresh()
```

## Error Handling

### Comprehensive Error Handling

The system includes robust error handling for all operations:

#### Archive Creation Errors
- **Empty filename**: Prevents creation with empty names
- **Unsupported formats**: Validates file extensions
- **File system errors**: Catches and reports I/O exceptions
- **Permission errors**: Handles access denied scenarios
- **Missing files**: Validates source files exist

#### Archive Extraction Errors
- **Non-archive files**: Shows error message for unsupported file types
- **Directories**: Shows error message if a directory is selected instead of a file
- **Extraction errors**: Shows error message and cleans up partially created directories
- **Permission errors**: Shows appropriate error messages

#### Cross-Storage Errors
- **Network issues**: Handles connectivity problems for remote storage
- **Authentication**: Proper handling of credential issues
- **Temporary file cleanup**: Ensures cleanup even on failures

### Exception Handling Pattern
```python
try:
    # Archive operation
    result = self.perform_archive_operation()
except FileNotFoundError as e:
    self.show_error(f"File not found: {e}")
except PermissionError as e:
    self.show_error(f"Permission denied: {e}")
except OSError as e:
    self.show_error(f"Archive operation failed: {e}")
except Exception as e:
    self.show_error(f"Unexpected error: {e}")
finally:
    # Cleanup temporary files
    self.cleanup_temporary_files()
```

## Configuration

### Archive Settings

```python
# In src/_config.py
CONFIRM_EXTRACT_ARCHIVE = True  # Show confirmation before extraction

# Key bindings
KEY_BINDINGS = {
    'create_archive': ['p', 'P'],
    'extract_archive': ['u', 'U'],
}
```

### Built-in Integration

Archive operations are fully integrated into TFM's interface through the existing key bindings and menu system.

## Performance Considerations

### Large Archives

- **Progress tracking** for operations with many files
- **Streaming operations** to minimize memory usage
- **Temporary file cleanup** to prevent disk space issues
- **Memory-efficient processing** for large files

### Remote Storage

- **Efficient batch operations** for S3
- **Temporary file staging** for cross-storage operations
- **Network error handling** and retry logic
- **Cache invalidation** for updated directories

### Compression Optimization

- **Format selection** based on speed vs. compression trade-offs
- **Parallel compression** where supported by the format
- **Memory-efficient streaming** for large files
- **Progress feedback** during long operations

## Cache Integration

### Automatic Cache Invalidation

The archive system integrates with TFM's caching system to ensure directory listings are updated after operations:

#### Archive Creation
- Invalidates destination directory cache
- Invalidates source file parent directories
- Updates directory listings automatically

#### Archive Extraction
- Invalidates extraction destination directory
- Creates new directory entries in cache
- Refreshes affected panes

#### Implementation
```python
def invalidate_cache_for_archive_operation(self, archive_path, source_paths=None):
    """Invalidate cache entries affected by archive operations"""
    if self.cache_manager:
        # Invalidate archive file path
        self.cache_manager.invalidate_cache_for_create_operation(archive_path)
        
        # Invalidate source file parent directories
        if source_paths:
            for source_path in source_paths:
                parent_dir = source_path.parent
                self.cache_manager.invalidate_cache_for_directory(parent_dir)
```

## API Reference

### ArchiveOperations Class

```python
class ArchiveOperations:
    def __init__(self, log_manager=None, cache_manager=None, progress_manager=None)
    
    def create_archive(self, source_paths: List[Path], archive_path: Path, 
                      format_type: str = 'tar.gz') -> bool
    
    def extract_archive(self, archive_path: Path, destination_dir: Path, 
                       overwrite: bool = False) -> bool
    
    def list_archive_contents(self, archive_path: Path) -> List[Tuple[str, int, str]]
    
    def is_archive(self, path: Path) -> bool
    
    def get_archive_format(self, filename: str) -> Optional[dict]
```

### ArchiveUI Class

```python
class ArchiveUI:
    def __init__(self, file_manager)
    
    def enter_create_archive_mode(self)
    
    def on_create_archive_confirm(self, filename: str)
    
    def extract_selected_archive(self)
    
    def get_archive_basename(self, filename: str) -> str
```

### Supported Format Types

- `'zip'` - ZIP archive
- `'tar'` - Uncompressed TAR
- `'tar.gz'` - GZIP compressed TAR
- `'tar.bz2'` - BZIP2 compressed TAR
- `'tar.xz'` - XZ compressed TAR
- `'gzip'` - Single file GZIP compression
- `'bzip2'` - Single file BZIP2 compression
- `'xz'` - Single file XZ compression

## Usage Examples

### Creating a ZIP Archive

1. Select files with **Space**
2. Press **P**
3. Enter filename: `backup.zip`
4. Archive is created in other pane

### Extracting to S3

1. Navigate to archive file
2. Press **U** to extract
3. If other pane is S3, archive extracts to S3
4. Progress tracking shows extraction status

### Cross-Storage Archive Creation

1. Navigate to S3 bucket in left pane
2. Select S3 files with **Space**
3. Navigate to local directory in right pane
4. Press **P** to create local archive from S3 files
5. Files are downloaded, archived, and uploaded as needed

## Testing

### Test Coverage

- **Unit tests** for all archive formats
- **Integration tests** for cross-storage operations
- **Error handling** and edge case testing
- **Performance testing** for large archives
- **UI interaction** testing

### Running Tests

```bash
# Run archive operation tests
python test/test_archive_operations.py

# Run demo script
python demo/demo_archive_operations.py

# Run specific format tests
python test/test_archive_creation.py
python test/test_archive_extraction.py
```

### Test Scenarios

1. **Format Support** - All supported archive formats
2. **Cross-Storage** - All storage combinations
3. **Error Handling** - Invalid files, permissions, disk space
4. **Large Files** - Performance and memory usage
5. **Edge Cases** - Empty archives, special characters, long paths
6. **Progress Tracking** - Progress display accuracy
7. **Cache Integration** - Cache invalidation verification

## Security Considerations

### File Permissions

- Archive operations preserve Unix file permissions where supported
- Extraction respects umask settings
- Cross-storage operations may modify permissions based on destination

### Path Traversal Protection

- Archive extraction validates file paths
- Prevents extraction outside target directory
- Handles malicious archive contents safely

### Temporary Files

- Temporary files use secure temporary directories
- Automatic cleanup prevents information leakage
- Proper file permissions on temporary files

## Troubleshooting

### Common Issues

#### Permission Errors
- Ensure write permissions to destination
- Check file ownership and access rights
- Verify S3 bucket permissions for cross-storage operations

#### Disk Space Issues
- Verify sufficient space for archives and temporary files
- Monitor disk usage during large operations
- Clean up temporary files if operations fail

#### Network Issues (S3)
- Check AWS credentials for S3 operations
- Verify network connectivity for remote storage
- Monitor S3 API rate limits

#### Format Support
- Ensure required compression tools are installed
- Check archive format compatibility
- Verify file extensions match expected formats

### Error Messages

- **"Unsupported archive format"** - Use supported extensions
- **"Permission denied"** - Check file/directory permissions
- **"No space left on device"** - Free up disk space
- **"Archive already exists"** - Choose different name or confirm overwrite
- **"AWS credentials not found"** - Configure AWS credentials for S3 operations

## Future Enhancements

### Planned Features

1. **Additional Archive Formats**
   - 7-Zip support (.7z)
   - RAR extraction support (.rar)
   - LZ4 compression support

2. **Enhanced UI Features**
   - Archive content preview before extraction
   - Selective extraction (choose files to extract)
   - Archive integrity verification

3. **Performance Optimizations**
   - Streaming archive operations for large files
   - Parallel compression for multi-core systems
   - Smart caching of archive metadata

4. **Integration Improvements**
   - Better integration with external programs
   - Archive operation history
   - Undo/redo support for archive operations

### Advanced Features

1. **Encryption Support**
   - Password-protected archives
   - GPG encryption integration
   - Secure key management

2. **Incremental Archives**
   - Differential archive creation
   - Timestamp-based updates
   - Backup rotation support

3. **Cloud Integration**
   - Additional cloud storage providers
   - Cloud-native archive formats
   - Serverless archive processing

## Migration and Compatibility

### Backward Compatibility

- All existing functionality continues to work unchanged
- Legacy method signatures preserved through delegation
- No breaking changes to user interface or key bindings
- Existing configuration options remain valid

### Migration Benefits

- **Maintainability**: Smaller, focused classes with single responsibilities
- **Testability**: Archive operations can be tested independently
- **Reusability**: ArchiveOperations can be used by other components
- **Extensibility**: Easy to add new archive formats and features

## Conclusion

The TFM Archive Operations System provides a comprehensive, modular, and extensible solution for archive management across local and remote storage systems. With support for multiple formats, cross-storage operations, progress tracking, and robust error handling, it enables efficient archive management while maintaining the familiar TFM user experience.

The clean architectural separation between core functionality and UI integration ensures maintainability and extensibility, while the comprehensive testing and error handling provide reliability for production use.

## Related Documentation

- [S3 Support System](S3_SUPPORT_SYSTEM.md) - S3 integration for cross-storage operations
- [TFM Path Architecture](TFM_PATH_ARCHITECTURE.md) - Path system used for cross-storage support
- [External Programs Policy](../external-programs-policy.md) - External program integration