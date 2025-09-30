# Cross-Storage Move Implementation

## Overview

The Cross-Storage Move feature enables TFM to move files and directories between different storage systems seamlessly. This includes moving files between local filesystem and S3, between different S3 buckets, and other remote storage systems.

## Architecture

### Key Classes
- `Path`: Main interface for move operations
- `LocalPathImpl`: Local filesystem implementation
- `S3PathImpl`: AWS S3 implementation
- `FileOperations`: TFM integration layer

### Code Flow
1. User initiates move in TFM
2. `FileOperations.move_selected_files()` called
3. Determines storage types and cross-storage status
4. Calls `Path.move_to()` for each file/directory
5. Progress tracking and error handling
6. UI refresh and user feedback

## Implementation Details

### Same-Storage Moves
When moving files within the same storage system:
1. Uses the native `rename()` operation
2. Atomic operation (instant for most filesystems)
3. No data copying required
4. Preserves file metadata and permissions

### Cross-Storage Moves
When moving files between different storage systems:
1. **Copy Phase**: Copies source to destination using optimized transfer
2. **Verification Phase**: Verifies successful copy (optional)
3. **Delete Phase**: Removes source after successful copy
4. **Cache Management**: Invalidates relevant caches

## Supported Storage Systems

### Currently Supported
- **Local Filesystem** (`file://`) - Standard local files and directories
- **Amazon S3** (`s3://`) - AWS S3 buckets and objects

### Future Support
- **SCP/SSH** (`scp://`) - Remote servers via SSH
- **FTP/SFTP** (`ftp://`, `sftp://`) - FTP servers
- **Other cloud storage** - Azure Blob, Google Cloud Storage

## API Usage Examples

### Basic Move Operations

```python
from tfm_path import Path

# Local to local (same-storage)
local_file = Path("/home/user/document.txt")
local_dest = Path("/tmp/moved_document.txt")
local_file.move_to(local_dest)

# Local to S3 (cross-storage)
local_file = Path("/home/user/data.csv")
s3_dest = Path("s3://my-bucket/data/data.csv")
local_file.move_to(s3_dest)

# S3 to local (cross-storage)
s3_file = Path("s3://my-bucket/reports/report.pdf")
local_dest = Path("/home/user/Downloads/report.pdf")
s3_file.move_to(local_dest)

# S3 to S3 (cross-storage between buckets)
s3_source = Path("s3://source-bucket/file.txt")
s3_dest = Path("s3://dest-bucket/moved-file.txt")
s3_source.move_to(s3_dest)
```

### With Error Handling

```python
from tfm_path import Path

source = Path("s3://my-bucket/large-file.zip")
destination = Path("/home/user/Downloads/large-file.zip")

try:
    success = source.move_to(destination, overwrite=True)
    if success:
        print("Move completed successfully")
    else:
        print("Move failed")
except FileNotFoundError:
    print("Source file not found")
except FileExistsError:
    print("Destination already exists")
except PermissionError:
    print("Permission denied")
except OSError as e:
    print(f"Move failed: {e}")
```

### Directory Moves

```python
from tfm_path import Path

# Move entire directory from local to S3
local_dir = Path("/home/user/project")
s3_dest = Path("s3://backup-bucket/projects/project")

# This will recursively move all files and subdirectories
local_dir.move_to(s3_dest)
```

## Configuration Options

```python
# In _config.py or tfm_config.py
CONFIRM_MOVE = True          # Show confirmation for moves
CONFIRM_CROSS_STORAGE = True # Extra confirmation for cross-storage
SHOW_MOVE_PROGRESS = True    # Show progress for large moves
CROSS_STORAGE_BUFFER_SIZE = 8192  # Buffer size for transfers
```

## Performance Considerations

### Same-Storage Moves
- **Local to Local**: Instant (metadata operation only)
- **S3 to S3 (same bucket)**: Fast (server-side copy + delete)
- **S3 to S3 (different bucket)**: Moderate (copy + delete)

### Cross-Storage Moves
- **Local to S3**: Depends on file size and upload speed
- **S3 to Local**: Depends on file size and download speed
- **Performance optimizations**:
  - Streaming transfers for large files
  - Parallel transfers for directories
  - Resume capability for interrupted transfers

### Memory Usage
- Streaming transfers minimize memory usage
- Large files don't require full buffering in memory
- Directory moves process files individually

## Error Handling

### Common Errors and Solutions

1. **FileNotFoundError**
   - Source file/directory doesn't exist
   - Check path and permissions

2. **FileExistsError**
   - Destination already exists
   - Use `overwrite=True` or choose different destination

3. **PermissionError**
   - Insufficient permissions on source or destination
   - Check file permissions and AWS credentials

4. **OSError**
   - Network issues, disk space, or other system errors
   - Check connectivity and available space

### Recovery Mechanisms
- Partial transfers can be resumed (future feature)
- Failed moves leave source intact
- Detailed error messages for troubleshooting

## Security Considerations

### AWS S3 Security
- Uses AWS credentials from standard locations
- Supports IAM roles and temporary credentials
- Respects S3 bucket policies and ACLs

### Local Filesystem Security
- Respects file system permissions
- Preserves ownership when possible
- Secure temporary file handling

### Data Integrity
- Checksums for cross-storage transfers (future feature)
- Atomic operations where possible
- Verification of successful transfers

## Testing

### Unit Tests
```bash
# Run cross-storage move tests
python test/test_cross_storage_move.py

# Run S3-specific tests (requires AWS credentials)
python test/test_s3_move_operations.py
```

### Demo Scripts
```bash
# Interactive demo
python demo/demo_cross_storage_move.py

# S3 integration demo (requires AWS credentials)
python demo/demo_s3_move_integration.py
```

## Future Enhancements

### Planned Features
1. **Resume capability** for interrupted transfers
2. **Checksum verification** for data integrity
3. **Parallel transfers** for directory moves
4. **Bandwidth throttling** for network transfers
5. **Additional storage backends** (Azure, GCP, etc.)

### Performance Improvements
1. **Streaming transfers** for very large files
2. **Compression** for cross-storage transfers
3. **Caching** for frequently accessed paths
4. **Connection pooling** for S3 operations

### User Experience
1. **Transfer speed display** in progress dialog
2. **Pause/resume** functionality
3. **Background transfers** for large operations
4. **Transfer history** and logging

## Contributing

### Adding New Storage Backends
1. Create new `PathImpl` subclass
2. Implement all required methods
3. Add scheme detection in `Path._create_implementation()`
4. Add tests and documentation
5. Update configuration options

### Testing Guidelines
- Test both same-storage and cross-storage scenarios
- Include error handling tests
- Test with various file sizes and types
- Verify progress tracking accuracy
- Test permission and security scenarios

## Troubleshooting

### S3 Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket/

# Check boto3 installation
python -c "import boto3; print(boto3.__version__)"
```

### Permission Issues
```bash
# Check local file permissions
ls -la /path/to/file

# Check directory permissions
ls -ld /path/to/directory
```

### Network Issues
- Check internet connectivity
- Verify firewall settings
- Test with smaller files first

## Related Documentation
- [S3 Support Feature](S3_SUPPORT_FEATURE.md)
- [Path System Architecture](TFM_PATH_ARCHITECTURE.md)
- [File Operations Guide](FILE_OPERATIONS_GUIDE.md)
- [Progress Tracking System](PROGRESS_TRACKING_SYSTEM.md)