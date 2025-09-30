# TFM S3 Support System

## Overview

TFM provides comprehensive AWS S3 support through an extended Path implementation, allowing users to navigate, browse, and manipulate S3 buckets and objects using the same interface as local file operations. The system includes intelligent caching for performance optimization and modular architecture for maintainability.

## Features

### Core S3 Support
- **S3 URI Format**: `s3://bucket-name/key/path`
- **Seamless Integration**: S3 paths work alongside local paths
- **Pathlib Compatibility**: All standard pathlib operations supported
- **Cross-Storage Operations**: Copy/move between local and S3 storage

### Supported Operations

#### Navigation and Browsing
- Navigate to S3 buckets: `s3://my-bucket/`
- Browse S3 objects like local files
- List bucket contents and nested "directories"
- Support for S3 prefix-based directory simulation

#### File Operations
- **Read Operations**: `read_text()`, `read_bytes()`, `open()`
- **Write Operations**: `write_text()`, `write_bytes()`, `open('w')`
- **File Info**: `stat()`, `exists()`, `is_file()`, `is_dir()`
- **File Management**: `unlink()`, `rename()`, `touch()`

#### Path Manipulation
- **Path Building**: `joinpath()`, `/` operator
- **Name Changes**: `with_name()`, `with_suffix()`, `with_stem()`
- **Path Properties**: `name`, `stem`, `suffix`, `parent`, `parts`

#### Directory Operations
- **Listing**: `iterdir()`, `glob()`, `rglob()`
- **Creation**: `mkdir()` (creates directory markers)
- **Removal**: `rmdir()` (removes empty directories)

### Performance Caching System

#### Intelligent Caching
- **Automatic caching** of all S3 API calls (head_object, list_objects_v2, get_object, etc.)
- **Configurable TTL** with default of 60 seconds
- **Thread-safe operations** using RLock for concurrent access
- **LRU eviction** to manage memory usage with configurable max entries

#### Cache Invalidation
- **Automatic invalidation** on write operations (put_object, delete_object, etc.)
- **Partial invalidation** for specific keys or buckets
- **Parent directory invalidation** when files are modified
- **Prefix-based invalidation** for related cache entries

#### Performance Benefits
- **Reduced API calls** by up to 90% for repeated operations
- **Faster directory listings** with paginated cache support
- **Improved file stat operations** through cached head_object calls
- **Better user experience** with reduced latency

## Architecture

### Modular Design
The S3 support is implemented using a clean modular architecture:

```
src/
├── tfm_path.py          # Core path implementation (PathImpl, LocalPathImpl, Path)
├── tfm_s3.py           # S3 implementation (S3PathImpl, S3Cache, utilities)
└── _config.py          # Configuration (includes S3 tools)
```

### Core Components

#### S3PathImpl Class (`src/tfm_s3.py`)
- **Purpose**: Implements all PathImpl abstract methods for S3 operations
- **Key Features**:
  - Full pathlib-compatible interface
  - boto3 integration for AWS S3 operations
  - Lazy S3 client initialization
  - Integrated caching system
  - Proper error handling for AWS-specific errors

#### S3Cache Class
```python
class S3Cache:
    def __init__(self, default_ttl: int = 60, max_entries: int = 1000)
    def get(self, operation: str, bucket: str, key: str = "", **kwargs) -> Optional[Any]
    def put(self, operation: str, bucket: str, key: str = "", data: Any = None, ttl: Optional[int] = None, **kwargs)
    def invalidate_bucket(self, bucket: str)
    def invalidate_key(self, bucket: str, key: str)
    def invalidate_prefix(self, bucket: str, prefix: str)
    def clear(self)
    def get_stats(self) -> Dict[str, Any]
```

#### Path Factory Pattern (`src/tfm_path.py`)
```python
def _create_implementation(self, path_str: str) -> PathImpl:
    if path_str.startswith('s3://'):
        try:
            from .tfm_s3 import S3PathImpl  # Dynamic import
        except ImportError:
            from tfm_s3 import S3PathImpl   # Fallback for direct execution
        return S3PathImpl(path_str)
    return LocalPathImpl(PathlibPath(path_str))
```

### Cache Architecture
```
S3Cache
├── _cache: Dict[str, Dict[str, Any]]  # Main cache storage
├── _lock: threading.RLock             # Thread safety
├── default_ttl: int                   # Default cache TTL
└── max_entries: int                   # Maximum cache entries
```

## Installation and Configuration

### Dependencies
```bash
pip install boto3
```

### AWS Configuration
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment Variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2

# Option 3: IAM Roles (for EC2 instances)
# Automatically detected when running on AWS infrastructure
```

### Cache Configuration
```python
from tfm_s3 import configure_s3_cache, get_s3_cache_stats

# Configure cache with custom settings
configure_s3_cache(ttl=120, max_entries=2000)

# Check cache statistics
stats = get_s3_cache_stats()
print(f"Cache entries: {stats['total_entries']}")
```

## Usage Examples

### Basic Path Operations
```python
from tfm_path import Path

# Create S3 paths
bucket = Path('s3://my-bucket/')
file_path = Path('s3://my-bucket/documents/report.pdf')

# Path properties
print(file_path.name)        # 'report.pdf'
print(file_path.suffix)     # '.pdf'
print(file_path.parent)     # 's3://my-bucket/documents/'

# Path manipulation
new_file = file_path.with_name('summary.pdf')
csv_file = file_path.with_suffix('.csv')
```

### File Operations with Automatic Caching
```python
# All operations automatically use caching
s3_path = Path('s3://my-bucket/my-file.txt')

# First call hits API and caches result
exists1 = s3_path.exists()  # API call made

# Second call uses cached result
exists2 = s3_path.exists()  # No API call

# Write operation invalidates cache
s3_path.write_text("new content")  # Cache invalidated

# Next call hits API again
exists3 = s3_path.exists()  # API call made
```

### Directory Operations
```python
# List bucket contents (cached)
bucket = Path('s3://my-bucket/')
for item in bucket.iterdir():
    print(f"Found: {item}")

# Create directory (marker)
new_dir = Path('s3://my-bucket/new-folder/')
new_dir.mkdir()

# Search with patterns (uses cached listings)
for pdf_file in bucket.glob('*.pdf'):
    print(f"PDF: {pdf_file}")
```

### Cache Management
```python
from tfm_s3 import clear_s3_cache, get_s3_cache

# Clear all cache entries
clear_s3_cache()

# Get cache instance for advanced operations
cache = get_s3_cache()
cache.invalidate_bucket('my-bucket')

# Manual invalidation
cache.invalidate_key('bucket', 'path/to/file.txt')
cache.invalidate_prefix('bucket', 'path/to/')
```

## TFM Integration

### Navigation
- Navigate to S3 buckets in TFM: `s3://bucket-name/`
- Browse S3 objects like local directories
- Use standard TFM navigation keys
- Cached directory listings for fast browsing

### File Operations
- Copy files between local and S3 storage
- Move and rename S3 objects
- Delete S3 objects with confirmation dialogs
- All operations benefit from intelligent caching

### External Programs
- TFM environment variables work with S3 paths
- `TFM_THIS_DIR` can be an S3 path: `s3://bucket/folder/`
- `TFM_THIS_SELECTED` can include S3 objects
- External scripts can process S3 paths using boto3

### Search and Filter
- Search within S3 buckets using TFM's search functionality
- Filter S3 objects by name patterns
- Content search (if objects are text files)
- Cached search results for improved performance

## Performance Optimization

### Caching Benefits
Based on typical S3 operations:

| Operation | Without Cache | With Cache | Improvement |
|-----------|---------------|------------|-------------|
| exists() | 150-300ms | 1-5ms | 95-98% |
| stat() | 150-300ms | 1-5ms | 95-98% |
| iterdir() | 200-500ms | 10-50ms | 80-95% |
| read_text() | 200-400ms | 50-100ms | 50-75% |

### Memory Usage
- Typical cache entry: 1-10KB
- Default max entries: 1000
- Estimated memory usage: 1-10MB
- LRU eviction prevents unbounded growth

### Configuration Options
```python
# Global configuration
configure_s3_cache(
    ttl=60,          # Default TTL in seconds
    max_entries=1000 # Maximum cache entries
)

# Per-operation TTL
s3_path._cached_api_call(
    'head_object',
    ttl=300,  # 5 minutes
    Bucket='my-bucket',
    Key='my-key'
)
```

## Implementation Details

### S3 Operation Mapping
- **Directories** → Key prefixes with '/' delimiter
- **Files** → S3 objects with keys
- **Paths** → S3 URIs (s3://bucket/key)
- **Listing** → list_objects_v2 with prefix/delimiter (cached)
- **Stat** → head_object for metadata (cached)

### Thread Safety
The entire system is thread-safe:
- Uses `threading.RLock` for all cache operations
- Supports concurrent read/write operations
- Safe for use in multi-threaded TFM environment

### Error Handling
- **Credential Errors**: Clear messages when AWS credentials missing
- **Permission Errors**: Proper handling of access denied scenarios
- **Network Errors**: Graceful handling of connection issues
- **S3 Errors**: Specific handling for NoSuchBucket, NoSuchKey, etc.
- **Cache Failures**: Cache failures don't affect S3 operations

### Cache Invalidation Strategies
```python
def _invalidate_cache_for_write(self, key: Optional[str] = None):
    target_key = key or self._key
    
    # Invalidate the specific key
    self._cache.invalidate_key(self._bucket, target_key)
    
    # Invalidate parent directory listings
    if '/' in target_key:
        parent_key = '/'.join(target_key.split('/')[:-1]) + '/'
        self._cache.invalidate_key(self._bucket, parent_key)
    
    # Invalidate bucket root listing if top-level key
    if '/' not in target_key.strip('/'):
        self._cache.invalidate_key(self._bucket, '')
```

## Monitoring and Statistics

### Available Statistics
```python
stats = get_s3_cache_stats()
# Returns:
{
    'total_entries': int,      # Current cache entries
    'expired_entries': int,    # Expired but not cleaned entries
    'max_entries': int,        # Maximum allowed entries
    'default_ttl': int         # Default TTL in seconds
}
```

### Best Practices
- **Short-lived data**: 30-60 seconds TTL
- **Stable data**: 300-600 seconds TTL
- **Read-heavy workloads**: Longer TTL
- **Write-heavy workloads**: Shorter TTL
- Monitor `expired_entries` for cache efficiency

## Limitations

### S3 Constraints
- **No Symbolic Links**: S3 doesn't support symlinks
- **No Hard Links**: S3 doesn't support hard links
- **No File Permissions**: chmod() is a no-op
- **No True Directories**: Directory operations are simulated

### Performance Considerations
- **Network Latency**: S3 operations slower than local file operations
- **API Rate Limits**: AWS S3 has request rate limits
- **Large Listings**: Very large buckets may be slow to browse initially

### AWS Costs
- **API Requests**: Each operation incurs AWS charges (reduced by caching)
- **Data Transfer**: Downloading/uploading data has costs
- **Storage**: S3 storage charges apply

## Security Considerations

### Credentials
- **Never Hardcode**: Don't embed AWS credentials in code
- **Use IAM Roles**: Preferred method for AWS infrastructure
- **Least Privilege**: Grant minimal required permissions

### Permissions
- **Bucket Access**: Requires appropriate S3 bucket permissions
- **Object Access**: Requires read/write permissions for objects
- **Cross-Account**: May require additional configuration

## Troubleshooting

### Common Issues

#### Credentials Not Found
```
Error: AWS credentials not found
Solution: Configure AWS credentials using 'aws configure' or environment variables
```

#### Permission Denied
```
Error: Access Denied
Solution: Check IAM permissions for the S3 bucket and objects
```

#### High Memory Usage
```python
# Reduce cache size
configure_s3_cache(max_entries=500)

# Or clear cache periodically
clear_s3_cache()
```

#### Stale Data
```python
# Reduce TTL for frequently changing data
configure_s3_cache(ttl=30)

# Or manually invalidate
cache = get_s3_cache()
cache.invalidate_bucket('frequently-changing-bucket')
```

### Debug Information
Enable debug logging to monitor cache behavior:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Cache operations will be logged
s3_path.exists()  # Logs cache hit/miss information
```

## Testing

### Test Coverage
- **Unit Tests**: All S3PathImpl methods and S3Cache functionality
- **Integration Tests**: Real AWS operations (when credentials available)
- **Compatibility Tests**: Local path functionality preserved
- **Cache Tests**: Cache invalidation, expiration, and LRU eviction

### Running Tests
```bash
# Unit tests (no AWS credentials required)
python test/test_s3_path.py
python test/test_s3_caching.py

# Integration tests (requires AWS credentials)
python test/test_s3_integration.py
```

## Future Enhancements

### Planned Features
1. **Persistent cache** - Disk-based cache for session persistence
2. **Multi-part upload** - Support for large file uploads
3. **Presigned URLs** - Generate shareable links
4. **S3 Select** - Query data directly in S3
5. **Versioning** - Support for S3 object versioning
6. **Progress indicators** - Show upload/download progress

### Additional Storage Backends
The modular architecture enables easy addition of new storage backends:
- **tfm_scp.py**: SCP/SFTP support
- **tfm_ftp.py**: FTP support
- **tfm_azure.py**: Azure Blob Storage
- **tfm_gcs.py**: Google Cloud Storage

## Related Documentation
- [TFM Path Architecture](TFM_PATH_ARCHITECTURE.md)
- [External Programs Policy](../external-programs-policy.md)
- [S3 Fixes and Optimizations](S3_FIXES_AND_OPTIMIZATIONS.md)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)