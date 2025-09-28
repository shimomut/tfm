# S3 Copy Fix Implementation

## Problem Description

When attempting to copy files from the local filesystem to S3 using TFM, users encountered the error:
```
Permission denied: Cannot write to s3://shimomut-files/test1/dir1/
```

This error occurred because TFM was using `shutil.copy2()` for all copy operations, which only works with local filesystem paths and cannot handle S3 URIs.

## Root Cause Analysis

1. **TFM Copy Operation Flow**:
   - User selects files and presses copy key (c/C)
   - `copy_selected_files()` method is called
   - `perform_copy_operation()` method uses `shutil.copy2(source_file, dest_path)`
   - `shutil.copy2()` fails when `dest_path` is an S3 URI

2. **Missing Cross-Storage Support**:
   - The Path system supported S3 paths for navigation and reading
   - But copy operations were hardcoded to use `shutil.copy2()`
   - No mechanism existed for cross-storage copying (local ↔ S3)

## Solution Implementation

### 1. New `copy_to()` Method in Path Class

Added a new `copy_to()` method to the `Path` class in `src/tfm_path.py`:

```python
def copy_to(self, destination: 'Path', overwrite: bool = False) -> bool:
    """
    Copy this file or directory to the destination path.
    
    This method handles cross-storage copying (e.g., local to S3, S3 to local).
    """
```

**Key Features**:
- Automatic storage type detection
- Cross-storage copy support
- Proper error handling
- Overwrite control
- Directory recursion support

### 2. Cross-Storage Copy Logic

The method implements different strategies based on source and destination storage types:

#### Local to Local
- Uses `shutil.copy2()` for optimal performance
- Preserves file metadata and timestamps

#### Local to S3
- Reads file content using local file I/O
- Uploads to S3 using `write_bytes()` method
- Handles binary data correctly

#### S3 to Local
- Downloads from S3 using `read_bytes()` method
- Writes to local filesystem
- Creates parent directories as needed

#### S3 to S3
- Downloads from source S3 location
- Uploads to destination S3 location
- Could be optimized with S3 copy operations in the future

### 3. Updated TFM Copy Operations

Modified `src/tfm_main.py` to use the new copy method:

**Before**:
```python
shutil.copy2(source_file, dest_path)
```

**After**:
```python
source_file.copy_to(dest_path, overwrite=overwrite)
```

### 4. Directory Copy Support

Enhanced directory copying to handle cross-storage scenarios:
- Local directory copying still uses the optimized `_copy_directory_with_progress()` method
- Cross-storage directory copying uses the new recursive `_copy_directory_cross_storage()` method
- Progress tracking works for both scenarios

## Error Handling Improvements

### Specific Exception Types
The new implementation provides specific error handling:

- `FileNotFoundError`: Source file/directory doesn't exist
- `FileExistsError`: Destination exists and overwrite=False
- `PermissionError`: Insufficient permissions for operation
- `OSError`: General I/O errors with descriptive messages

### Graceful Degradation
- If S3 operations fail, clear error messages are provided
- Local operations continue to work as before
- No breaking changes to existing functionality

## Benefits

### 1. Cross-Storage Compatibility
- Copy files between local filesystem and S3
- Copy files between different S3 buckets
- Seamless user experience regardless of storage type

### 2. Improved Error Messages
- Clear, actionable error messages
- Specific error types for different failure scenarios
- Better debugging information

### 3. Consistent API
- Same copy interface for all storage types
- Overwrite control works consistently
- Progress tracking works for all scenarios

### 4. Performance Optimization
- Local-to-local copies still use fast `shutil.copy2()`
- Only cross-storage operations use the slower read/write approach
- Caching in S3 operations reduces API calls

## Usage Examples

### Basic File Copy
```python
from tfm_path import Path

# Local to S3
local_file = Path("/home/user/document.txt")
s3_dest = Path("s3://my-bucket/documents/document.txt")
local_file.copy_to(s3_dest, overwrite=True)

# S3 to local
s3_file = Path("s3://my-bucket/data/report.pdf")
local_dest = Path("/home/user/downloads/report.pdf")
s3_file.copy_to(local_dest)
```

### Directory Copy
```python
# Copy entire directory to S3
local_dir = Path("/home/user/project")
s3_dir = Path("s3://my-bucket/backups/project")
local_dir.copy_to(s3_dir, overwrite=True)
```

### Error Handling
```python
try:
    source.copy_to(destination, overwrite=False)
except FileNotFoundError:
    print("Source file not found")
except FileExistsError:
    print("Destination already exists")
except PermissionError:
    print("Permission denied")
except OSError as e:
    print(f"Copy failed: {e}")
```

## Testing

### Unit Tests
- Created `test/test_s3_copy_fix.py` with comprehensive test coverage
- Tests for all copy scenarios (local↔local, local↔S3, S3↔S3)
- Error condition testing
- Mock-based testing for S3 operations

### Demo Script
- Created `demo/demo_s3_copy_fix.py` to demonstrate functionality
- Shows before/after comparison
- Includes error handling examples
- Provides usage guidance

## Future Enhancements

### 1. S3-to-S3 Optimization
- Use S3 copy operations instead of download/upload
- Reduce bandwidth usage and improve performance

### 2. Progress Callbacks
- Add progress callback support for large file transfers
- Better integration with TFM's progress manager

### 3. Metadata Preservation
- Preserve file timestamps where possible
- Handle S3 metadata and tags

### 4. Parallel Transfers
- Support parallel uploads/downloads for large files
- Multipart upload support for S3

## Backward Compatibility

- All existing functionality continues to work unchanged
- Local file operations use the same optimized paths
- No breaking changes to the TFM user interface
- Existing key bindings and workflows remain the same

## Configuration

No additional configuration is required. The fix works automatically when:
1. AWS credentials are properly configured
2. `boto3` library is installed for S3 support
3. User has appropriate S3 permissions

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   - Configure AWS CLI: `aws configure`
   - Set environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - Use IAM roles for EC2 instances

2. **Permission Denied on S3**
   - Check S3 bucket permissions
   - Verify IAM user/role has s3:PutObject permissions
   - Check bucket policies and ACLs

3. **boto3 Not Available**
   - Install boto3: `pip install boto3`
   - Ensure it's in the Python path used by TFM

### Debug Information

Enable debug logging to see detailed copy operation information:
- S3 API calls and responses
- File transfer progress
- Error details and stack traces