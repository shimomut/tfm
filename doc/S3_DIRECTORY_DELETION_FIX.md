# S3 Directory Deletion Fix

## Overview

This document describes the fix for the S3 directory deletion issue where attempting to delete S3 directories resulted in a "No files to delete" error.

## Problem Description

When users tried to delete S3 directories (e.g., `s3://bucket/path/to/directory/`), TFM would display the error "No files to delete" even when the directory existed and contained files.

### Root Cause

The issue was caused by two problems in the S3PathImpl class:

1. **`exists()` method limitation**: The `exists()` method only checked for the existence of an actual S3 object with the exact key using `head_object()`. For directories that don't have an explicit directory marker (empty object with key ending in '/'), this would return `False` even though the directory conceptually exists because it has objects underneath it.

2. **Lack of recursive deletion**: TFM's directory deletion logic used `os.walk()` which doesn't work with S3 paths, and the S3 `rmdir()` method only worked for empty directories.

### Error Flow

1. User selects S3 directory for deletion
2. `delete_selected_files()` calls `exists()` on the directory path
3. `exists()` returns `False` because there's no explicit directory marker object
4. Directory is not added to `files_to_delete` list
5. "No files to delete" error is displayed

## Solution

### 1. Fixed `exists()` Method

Modified the `exists()` method in `S3PathImpl` to check if a path is a directory when the direct object check fails:

```python
def exists(self) -> bool:
    """Whether this path exists"""
    try:
        if not self._key:
            # Check if bucket exists
            self._cached_api_call('head_bucket', Bucket=self._bucket)
            return True
        else:
            # Check if object exists
            self._cached_api_call('head_object', Bucket=self._bucket, Key=self._key)
            return True
    except ClientError as e:
        if e.response['Error']['Code'] in ['404', 'NoSuchBucket', 'NoSuchKey']:
            # If direct object doesn't exist, check if it's a directory
            # (i.e., there are objects with this key as a prefix)
            return self.is_dir()
        raise
```

### 2. Added Recursive Deletion Support

Added two new methods to `S3PathImpl`:

#### `rmtree()` Method
Removes a directory and all its contents recursively:

```python
def rmtree(self):
    """Remove this directory and all its contents recursively"""
    # Lists all objects with the directory prefix
    # Deletes objects in batches of 1000 (S3 limit)
    # Removes directory marker if it exists
    # Invalidates cache
```

#### `_delete_objects_batch()` Method
Helper method to delete S3 objects in batches:

```python
def _delete_objects_batch(self, objects_to_delete):
    """Delete a batch of S3 objects"""
    # Uses S3's delete_objects API for efficient batch deletion
    # Handles errors and provides detailed error messages
```

### 3. Enhanced TFM Directory Deletion Logic

Modified `_delete_directory_with_progress()` in the main TFM class to handle S3 paths:

```python
def _delete_directory_with_progress(self, dir_path, processed_files, total_files):
    """Delete directory recursively with fine-grained progress updates"""
    # Check if this is an S3 path
    from tfm_s3 import S3PathImpl
    if isinstance(dir_path._impl, S3PathImpl):
        return self._delete_s3_directory_with_progress(dir_path, processed_files, total_files)
    
    # ... existing local filesystem logic ...
```

Added new `_delete_s3_directory_with_progress()` method:

```python
def _delete_s3_directory_with_progress(self, dir_path, processed_files, total_files):
    """Delete S3 directory recursively with fine-grained progress updates"""
    # Lists all objects in the directory with pagination
    # Provides progress updates for each file
    # Deletes objects in batches for efficiency
    # Handles errors gracefully
```

## Benefits

1. **Fixed "No files to delete" error**: S3 directories are now properly detected as existing
2. **Recursive deletion support**: Can delete directories with contents
3. **Progress tracking**: Shows progress when deleting large directories
4. **Efficient batch deletion**: Uses S3's batch delete API for better performance
5. **Error handling**: Provides detailed error messages for failed deletions
6. **Cache invalidation**: Properly invalidates cache after deletions

## Usage

After this fix, users can delete S3 directories normally:

1. Navigate to S3 directory in TFM
2. Select the directory (or use cursor selection)
3. Press the delete key (default: 'k' or 'K')
4. Confirm deletion when prompted
5. Directory and all contents will be deleted recursively

## Testing

The fix includes comprehensive tests:

- `test/test_s3_directory_deletion_fix.py`: Unit tests for the fix
- `demo/demo_s3_directory_deletion_debug.py`: Debug tool to analyze deletion issues
- `demo/demo_s3_recursive_deletion_test.py`: Test recursive deletion functionality

## Backward Compatibility

This fix is fully backward compatible:

- Existing `rmdir()` behavior unchanged for empty directories
- New `rmtree()` method available for recursive deletion
- Local filesystem deletion logic unchanged
- All existing functionality preserved

## Performance Considerations

- Uses S3's batch delete API (up to 1000 objects per request)
- Implements pagination for large directories
- Provides progress updates to prevent UI freezing
- Efficient cache invalidation to maintain consistency

## Error Handling

The fix includes robust error handling:

- Detailed error messages for S3 API failures
- Graceful handling of permission errors
- Progress tracking continues even when individual files fail
- Proper cleanup of partial deletions