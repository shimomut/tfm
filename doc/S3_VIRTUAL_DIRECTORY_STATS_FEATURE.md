# S3 Virtual Directory Stats Feature

## Overview

This feature improves the display of S3 virtual directories in TFM by providing meaningful size and timestamp information instead of showing "---" for both values.

## Problem

When browsing S3 objects in TFM, directories such as "s3://bucket/path/to/dir/" are often displayed with:
- Size: "---" 
- Date: "---"

This occurs because these directories don't have actual S3 directory objects (keys ending with "/"). Instead, they are "virtual directories" that exist only because there are S3 objects with that prefix.

## Solution

The feature implements "generated" size and timestamp values for virtual directories:

### Size
- **Always "0B"** for virtual directories
- This is logical since virtual directories don't consume storage space themselves

### Timestamp  
- **Latest modification time** among all child objects
- Provides meaningful temporal information about when the directory was last updated
- Falls back to current time if no children exist or timestamps are unavailable

## Implementation Details

### Core Changes

1. **Enhanced `stat()` method** in `S3PathImpl`:
   - Detects when a directory is virtual (no actual S3 object exists)
   - Calls `_get_virtual_directory_stats()` for virtual directories
   - Returns appropriate `S3StatResult` with generated values

2. **New `_get_virtual_directory_stats()` method**:
   - Lists objects under the directory prefix
   - Finds the latest `LastModified` timestamp among all children
   - Handles pagination for large directories (>1000 objects)
   - Uses caching to optimize performance
   - Returns (size=0, latest_timestamp)

### Caching Strategy

- Virtual directory stats are cached for 30 seconds
- Separate cache entries for different directory prefixes
- Cache invalidation works with existing S3 cache system
- Pagination results are processed efficiently

### Error Handling

- Graceful fallback to current time if API calls fail
- No exceptions thrown for permission errors
- Maintains existing behavior for actual S3 directory objects

## Performance Considerations

### Optimization Features

1. **Caching**: Directory stats cached for 30 seconds to avoid repeated API calls
2. **Efficient Pagination**: Uses S3 paginator for large directories
3. **Limited Scope**: Only processes objects needed for timestamp calculation
4. **Fallback Strategy**: Quick defaults if API calls fail

### API Call Patterns

- **Small directories** (<1000 objects): Single `list_objects_v2` call
- **Large directories** (>1000 objects): Paginated calls to find latest timestamp
- **Cache hits**: No API calls needed
- **Error cases**: Minimal API overhead with quick fallbacks

## User Experience Improvements

### Before
```
s3://bucket/reports/2024/     ---      ---
s3://bucket/data/processed/   ---      ---
s3://bucket/logs/application/ ---      ---
```

### After
```
s3://bucket/reports/2024/     0B       2024-06-30 17:45:30
s3://bucket/data/processed/   0B       2024-09-15 09:22:15
s3://bucket/logs/application/ 0B       2024-09-28 14:30:45
```

### Benefits

1. **Better Navigation**: Users can see when directories were last updated
2. **Consistent Display**: No more "---" placeholders in directory listings
3. **Logical Sizing**: 0B size makes sense for virtual directories
4. **Temporal Context**: Latest child timestamp provides meaningful information

## Technical Specifications

### Method Signatures

```python
def _get_virtual_directory_stats(self) -> Tuple[int, float]:
    """
    Get generated stats for virtual directories.
    Returns (size, mtime) where size is 0 and mtime is latest child timestamp.
    """
```

### Cache Configuration

- **TTL**: 30 seconds for virtual directory stats
- **Key Format**: Includes operation, bucket, prefix, and virtual_dir_stats flag
- **Invalidation**: Integrated with existing S3 cache invalidation system

### API Usage

- **Primary**: `list_objects_v2` with prefix filtering
- **Pagination**: `get_paginator('list_objects_v2')` for large directories
- **Caching**: Leverages existing `_cached_api_call` infrastructure

## Compatibility

### Backward Compatibility
- No breaking changes to existing API
- Existing behavior preserved for actual S3 directory objects
- Graceful degradation if new functionality fails

### Integration Points
- Works with existing TFM path system
- Compatible with S3 caching infrastructure
- Integrates with file browser display logic

## Testing

### Test Coverage
- Virtual directories with children
- Empty virtual directories  
- Large directories requiring pagination
- Error handling scenarios
- Cache behavior verification
- Integration with `stat()` method

### Demo Scripts
- Interactive demonstration of functionality
- Performance comparison examples
- Edge case handling examples

## Future Enhancements

### Potential Improvements
1. **Configurable Cache TTL**: Allow users to adjust cache duration
2. **Size Aggregation Option**: Optionally show total size of all children
3. **Recursive Timestamp**: Consider subdirectory timestamps
4. **Performance Metrics**: Add timing information for large directories

### Monitoring
- Cache hit/miss ratios for virtual directory stats
- API call patterns and performance metrics
- User experience feedback on directory browsing

## Configuration

### Default Settings
```python
# Cache TTL for virtual directory stats
VIRTUAL_DIR_STATS_TTL = 30  # seconds

# Maximum objects to check in single API call
MAX_OBJECTS_PER_CALL = 1000
```

### Customization Options
- Cache TTL can be adjusted via S3 cache configuration
- Pagination size follows S3 API defaults
- Error handling behavior is consistent with existing S3 operations