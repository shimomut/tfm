# TFM Archive Operations Feature

## Overview

The TFM Archive Operations feature provides comprehensive archive creation and extraction capabilities with full cross-storage support. This allows users to create archives from files in any supported storage (local, S3, etc.) and save them to any supported storage destination.

## Features

### Supported Archive Formats

#### Multi-file Archives
- **ZIP** (.zip) - Cross-platform compatibility, good compression
- **TAR** (.tar) - Uncompressed archive, preserves Unix permissions
- **TAR.GZ** (.tar.gz, .tgz) - Good compression, widely supported
- **TAR.BZ2** (.tar.bz2, .tbz2) - Better compression than gzip
- **TAR.XZ** (.tar.xz, .txz) - Best compression, slower processing

#### Single-file Compression
- **GZIP** (.gz) - Fast compression for single files
- **BZIP2** (.bz2) - Better compression for single files
- **XZ** (.xz) - Best compression for single files

### Cross-Storage Support

The archive operations support all combinations of source and destination storage types:

- **Local to Local** - Traditional archive operations
- **S3 to S3** - Create archives from S3 files, save to S3
- **Local to S3** - Archive local files, save archive to S3
- **S3 to Local** - Archive S3 files, save archive locally

### Key Capabilities

1. **Archive Creation**
   - Create archives from selected files and directories
   - Support for multiple archive formats
   - Progress tracking for large operations
   - Cross-storage source files

2. **Archive Extraction**
   - Extract archives to any supported storage
   - Overwrite protection with user confirmation
   - Progress tracking for large archives
   - Preserve directory structure and file permissions

3. **Archive Information**
   - List archive contents without extraction
   - Display file sizes and types
   - Support for all archive formats

## User Interface Integration

### Key Bindings

- **P** or **p** - Create archive from selected files
- **U** or **u** - Extract selected archive file

### Workflow

#### Creating Archives

1. Select files/directories to archive using **Space**
2. Press **P** to create archive
3. Enter archive filename with appropriate extension
4. Archive is created in the other pane's directory

#### Extracting Archives

1. Navigate to an archive file
2. Press **U** to extract
3. Confirm extraction destination
4. Archive is extracted with progress tracking

## Technical Implementation

### Architecture

The archive operations are implemented using a modular architecture:

- **tfm_archive.py** - Core archive operations module
- **ArchiveOperations class** - Main interface for archive operations
- **Cross-storage abstraction** - Uses tfm_path for storage independence

### Cross-Storage Implementation

Cross-storage operations use temporary files when necessary:

1. **Source files** are downloaded to temporary storage if remote
2. **Archive operations** are performed locally for reliability
3. **Result archives** are uploaded to destination if remote
4. **Temporary files** are automatically cleaned up

### Error Handling

- Comprehensive error handling for all operations
- Graceful degradation for unsupported formats
- Automatic cleanup of temporary files
- User-friendly error messages

## Configuration

### Archive Settings

```python
# In src/_config.py
CONFIRM_EXTRACT_ARCHIVE = True  # Show confirmation before extraction
```

### Built-in Integration

Archive operations are fully integrated into TFM's interface through the existing key bindings and menu system.

## Usage Examples

### Creating a ZIP Archive

1. Select files with **Space**
2. Press **P**
3. Enter filename: `backup.zip`
4. Archive is created in other pane

### Extracting to S3

1. Navigate to archive file
2. Use external program "Extract Archive"
3. Choose option 2 (other pane directory)
4. If other pane is S3, archive extracts to S3

### Cross-Storage Archive Creation

1. Navigate to S3 bucket in left pane
2. Select S3 files with **Space**
3. Navigate to local directory in right pane
4. Press **P** to create local archive from S3 files

## Performance Considerations

### Large Archives

- Progress tracking for operations with many files
- Streaming operations to minimize memory usage
- Temporary file cleanup to prevent disk space issues

### Remote Storage

- Efficient batch operations for S3
- Temporary file staging for cross-storage operations
- Network error handling and retry logic

### Compression

- Format selection based on speed vs. compression trade-offs
- Parallel compression where supported
- Memory-efficient streaming for large files

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure write permissions to destination
   - Check file ownership and access rights

2. **Disk Space**
   - Verify sufficient space for archives and temporary files
   - Monitor disk usage during large operations

3. **Network Issues**
   - Check AWS credentials for S3 operations
   - Verify network connectivity for remote storage

4. **Format Support**
   - Ensure required compression tools are installed
   - Check archive format compatibility

### Error Messages

- **"Unsupported archive format"** - Use supported extensions
- **"Permission denied"** - Check file/directory permissions
- **"No space left on device"** - Free up disk space
- **"Archive already exists"** - Choose different name or confirm overwrite

## Security Considerations

### File Permissions

- Archive operations preserve Unix file permissions where supported
- Extraction respects umask settings
- Cross-storage operations may modify permissions

### Path Traversal Protection

- Archive extraction validates file paths
- Prevents extraction outside target directory
- Handles malicious archive contents safely

### Temporary Files

- Temporary files use secure temporary directories
- Automatic cleanup prevents information leakage
- Proper file permissions on temporary files

## Future Enhancements

### Planned Features

1. **Encryption Support**
   - Password-protected archives
   - GPG encryption integration
   - Secure key management

2. **Advanced Compression**
   - Multi-threaded compression
   - Compression level selection
   - Format-specific optimizations

3. **Incremental Archives**
   - Differential archive creation
   - Timestamp-based updates
   - Backup rotation support

4. **Archive Verification**
   - Integrity checking
   - Checksum validation
   - Corruption detection

### Integration Improvements

1. **Preview Support**
   - Archive content preview in file viewer
   - Thumbnail generation for archives
   - Quick content search

2. **Batch Operations**
   - Multiple archive processing
   - Automated archive workflows
   - Scheduled archive operations

3. **Cloud Integration**
   - Additional cloud storage providers
   - Cloud-native archive formats
   - Serverless archive processing

## API Reference

### ArchiveOperations Class

```python
class ArchiveOperations:
    def __init__(self, log_manager=None)
    
    def create_archive(self, source_paths: List[Path], archive_path: Path, 
                      format_type: str = 'tar.gz') -> bool
    
    def extract_archive(self, archive_path: Path, destination_dir: Path, 
                       overwrite: bool = False) -> bool
    
    def list_archive_contents(self, archive_path: Path) -> List[Tuple[str, int, str]]
    
    def is_archive(self, path: Path) -> bool
    
    def get_archive_format(self, filename: str) -> Optional[dict]
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

## Testing

### Test Coverage

- Unit tests for all archive formats
- Integration tests for cross-storage operations
- Error handling and edge case testing
- Performance testing for large archives

### Running Tests

```bash
# Run archive operation tests
python test/test_archive_operations.py

# Run demo script
python demo/demo_archive_operations.py
```

### Test Scenarios

1. **Format Support** - All supported archive formats
2. **Cross-Storage** - All storage combinations
3. **Error Handling** - Invalid files, permissions, disk space
4. **Large Files** - Performance and memory usage
5. **Edge Cases** - Empty archives, special characters, long paths

## Conclusion

The TFM Archive Operations feature provides a comprehensive, cross-storage archive solution that integrates seamlessly with TFM's file management capabilities. With support for multiple formats, progress tracking, and robust error handling, it enables efficient archive management across local and remote storage systems.