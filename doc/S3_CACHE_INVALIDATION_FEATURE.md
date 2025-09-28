# S3 Cache Invalidation Feature

## Overview

This document describes the S3 cache invalidation feature implemented in TFM to ensure that S3 directory listings are properly refreshed after file and archive operations.

## Problem Statement

TFM uses caching for S3 operations to improve performance by reducing API calls to AWS S3. However, after performing file operations (copy, move, delete, create) or archive operations (create, extract), the cached directory listings could become stale, showing outdated information to users.

## Solution

The S3 Cache Invalidation feature automatically invalidates relevant cache entries after file and archive operations, ensuring that directory listings are refreshed and show the current state of S3 buckets.

## Architecture

### Components

1. **CacheManager** (`src/tfm_cache_manager.py`)
   - Central component responsible for cache invalidation logic
   - Handles different types of operations (copy, move, delete, create, archive)
   - Groups paths by storage scheme for efficient processing

2. **S3Cache** (`src/tfm_s3.py`)
   - Existing S3 caching system with invalidation methods
   - Provides `invalidate_key()` method for targeted cache invalidation
   - Thread-safe cache operations

3. **Integration Points**
   - FileManager main operations (copy, move, delete, create)
   - Archive operations (create, extract)
   - File/directory creation operations

### Cache Invalidation Strategy

The cache invalidation follows these principles:

1. **Targeted Invalidation**: Only invalidate cache entries that are affected by the operation
2. **Parent Directory Invalidation**: Invalidate parent directory listings when files are modified
3. **Hierarchical Invalidation**: Invalidate all relevant levels of the directory hierarchy
4. **Error Resilience**: Handle cache invalidation errors gracefully without breaking file operations

## Implementation Details

### Cache Invalidation Patterns

#### Copy Operations
- Invalidate destination directory cache
- Invalidate specific destination file paths
- Invalidate parent directories of destination paths

#### Move Operations
- Invalidate source parent directory cache
- Invalidate destination directory cache
- Invalidate specific source and destination file paths

#### Delete Operations
- Invalidate parent directory cache of deleted items
- Invalidate the deleted paths themselves

#### Archive Operations
- Invalidate archive file path cache
- Invalidate archive parent directory cache
- Invalidate source file parent directories (for creation)
- Invalidate extraction destination directory (for extraction)

#### Create Operations
- Invalidate created file/directory path cache
- Invalidate parent directory cache

### Key Methods

#### CacheManager Methods

```python
def invalidate_cache_for_copy_operation(self, source_paths: List[Path], destination_dir: Path)
def invalidate_cache_for_move_operation(self, source_paths: List[Path], destination_dir: Path)
def invalidate_cache_for_delete_operation(self, deleted_paths: List[Path])
def invalidate_cache_for_archive_operation(self, archive_path: Path, source_paths: List[Path] = None)
def invalidate_cache_for_create_operation(self, created_path: Path)
```

#### S3Cache Methods

```python
def invalidate_key(self, bucket: str, key: str)
def invalidate_prefix(self, bucket: str, prefix: str)
def invalidate_bucket(self, bucket: str)
```

## Integration Points

### FileManager Integration

The cache invalidation is integrated into the main file operation methods:

1. **perform_copy_operation()**: Calls `invalidate_cache_for_copy_operation()`
2. **perform_move_operation()**: Calls `invalidate_cache_for_move_operation()`
3. **perform_delete_operation()**: Calls `invalidate_cache_for_delete_operation()`
4. **on_create_directory_confirm()**: Calls `invalidate_cache_for_create_operation()`
5. **on_create_file_confirm()**: Calls `invalidate_cache_for_create_operation()`
6. **perform_create_archive()**: Calls `invalidate_cache_for_archive_operation()`

### Archive Operations Integration

The ArchiveOperations class is updated to accept a cache_manager parameter and calls cache invalidation methods:

1. **create_archive()**: Calls `invalidate_cache_for_archive_operation()` after successful creation
2. **extract_archive()**: Calls `invalidate_cache_for_directory()` after successful extraction

## Error Handling

The cache invalidation system includes robust error handling:

1. **Graceful Degradation**: Cache invalidation errors do not prevent file operations from completing
2. **Logging**: Errors are logged as warnings for debugging purposes
3. **Non-S3 Path Handling**: Non-S3 paths are safely ignored without errors
4. **Exception Isolation**: Cache invalidation exceptions are caught and handled locally

## Performance Considerations

1. **Selective Invalidation**: Only invalidates cache entries that are actually affected
2. **Batch Processing**: Groups invalidation operations by bucket for efficiency
3. **Minimal Overhead**: Cache invalidation adds minimal overhead to file operations
4. **Thread Safety**: All cache operations are thread-safe

## Testing

### Unit Tests

The feature includes comprehensive unit tests (`test/test_s3_cache_invalidation.py`):

- Test cache invalidation for each operation type
- Test error handling scenarios
- Test non-S3 path handling
- Test mock S3 cache interactions

### Demo Script

A demo script (`demo/demo_s3_cache_invalidation.py`) demonstrates:

- Cache invalidation for different operation types
- Error handling behavior
- Local vs S3 path handling
- Mock cache interactions

## Usage Examples

### Copy Operation
```python
# After copying files, cache is automatically invalidated
file_manager.perform_copy_operation(source_files, destination_dir)
# Cache invalidation happens automatically before refresh
```

### Move Operation
```python
# After moving files, both source and destination caches are invalidated
file_manager.perform_move_operation(source_files, destination_dir)
# Directory listings will show updated state
```

### Archive Creation
```python
# After creating archive, relevant directory caches are invalidated
archive_operations.create_archive(source_files, archive_path, 'zip')
# Archive will appear in directory listing immediately
```

## Benefits

1. **Accurate Directory Listings**: Users always see the current state of S3 directories
2. **Improved User Experience**: No need to manually refresh or wait for cache expiration
3. **Automatic Operation**: Cache invalidation happens transparently
4. **Performance Optimized**: Only invalidates necessary cache entries
5. **Error Resilient**: File operations continue even if cache invalidation fails

## Configuration

The cache invalidation feature works with existing S3 cache configuration:

- `S3_CACHE_TTL`: Controls cache entry lifetime (default: 60 seconds)
- Cache invalidation works independently of TTL settings
- No additional configuration required

## Future Enhancements

Potential future improvements:

1. **Batch Invalidation**: Group multiple invalidation operations for better performance
2. **Smart Invalidation**: More intelligent detection of which cache entries need invalidation
3. **Metrics**: Add metrics to track cache invalidation effectiveness
4. **Configuration**: Allow fine-tuning of invalidation behavior

## Conclusion

The S3 Cache Invalidation feature ensures that TFM users always see accurate directory listings after file and archive operations, improving the overall user experience while maintaining the performance benefits of S3 caching.