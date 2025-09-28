#!/usr/bin/env python3
"""
TFM S3 Support - AWS S3 implementation for TFM Path system

This module provides S3PathImpl and related classes for AWS S3 operations
within the TFM path system.
"""

import os
import stat
import fnmatch
import io
import time
import threading
import hashlib
import json
from datetime import datetime
from typing import Iterator, List, Dict, Any, Optional, Tuple

# Import the PathImpl base class
try:
    from .tfm_path import PathImpl
except ImportError:
    from tfm_path import PathImpl

# AWS S3 support - import boto3 with fallback
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception


class S3Cache:
    """
    Caching system for S3 API calls to improve response times.
    
    Features:
    - Configurable cache TTL (default 60 seconds)
    - Thread-safe operations
    - Partial cache invalidation
    - LRU-style cache management
    """
    
    def __init__(self, default_ttl: int = 60, max_entries: int = 1000):
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def _generate_cache_key(self, operation: str, bucket: str, key: str = "", **kwargs) -> str:
        """Generate a unique cache key for the operation and parameters"""
        # Create a deterministic key from operation parameters
        params = {
            'operation': operation,
            'bucket': bucket,
            'key': key,
            **kwargs
        }
        # Sort parameters for consistent key generation
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()
    
    def get(self, operation: str, bucket: str, key: str = "", **kwargs) -> Optional[Any]:
        """Get cached result if available and not expired"""
        cache_key = self._generate_cache_key(operation, bucket, key, **kwargs)
        
        with self._lock:
            if cache_key not in self._cache:
                return None
            
            entry = self._cache[cache_key]
            current_time = time.time()
            
            # Check if entry has expired
            if current_time - entry['timestamp'] > entry['ttl']:
                del self._cache[cache_key]
                return None
            
            # Update access time for LRU behavior
            entry['last_access'] = current_time
            return entry['data']
    
    def put(self, operation: str, bucket: str, key: str = "", data: Any = None, ttl: Optional[int] = None, **kwargs):
        """Store result in cache with optional custom TTL"""
        cache_key = self._generate_cache_key(operation, bucket, key, **kwargs)
        current_time = time.time()
        
        with self._lock:
            # Enforce max entries limit using LRU eviction
            if len(self._cache) >= self.max_entries and cache_key not in self._cache:
                self._evict_lru()
            
            self._cache[cache_key] = {
                'data': data,
                'timestamp': current_time,
                'last_access': current_time,
                'ttl': ttl or self.default_ttl,
                'bucket': bucket,
                'key': key,
                'operation': operation
            }
    
    def invalidate_bucket(self, bucket: str):
        """Invalidate all cache entries for a specific bucket"""
        with self._lock:
            keys_to_remove = []
            for cache_key, entry in self._cache.items():
                if entry['bucket'] == bucket:
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self._cache[key]
    
    def invalidate_key(self, bucket: str, key: str):
        """Invalidate cache entries for a specific S3 key and its parent directories"""
        with self._lock:
            keys_to_remove = []
            for cache_key, entry in self._cache.items():
                if entry['bucket'] == bucket:
                    # Invalidate exact key matches
                    if entry['key'] == key:
                        keys_to_remove.append(cache_key)
                    # Invalidate parent directory listings
                    elif entry['operation'] in ['list_objects_v2', 'head_bucket'] and key.startswith(entry['key']):
                        keys_to_remove.append(cache_key)
                    # Invalidate child directory listings if we're modifying a parent
                    elif entry['key'].startswith(key.rstrip('/') + '/'):
                        keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self._cache[key]
    
    def invalidate_prefix(self, bucket: str, prefix: str):
        """Invalidate all cache entries with keys starting with the given prefix"""
        with self._lock:
            keys_to_remove = []
            for cache_key, entry in self._cache.items():
                if entry['bucket'] == bucket and entry['key'].startswith(prefix):
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self._cache[key]
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def _evict_lru(self):
        """Evict the least recently used cache entry"""
        if not self._cache:
            return
        
        # Find the entry with the oldest last_access time
        oldest_key = min(self._cache.keys(), 
                        key=lambda k: self._cache[k]['last_access'])
        del self._cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        with self._lock:
            current_time = time.time()
            expired_count = sum(1 for entry in self._cache.values() 
                              if current_time - entry['timestamp'] > entry['ttl'])
            
            return {
                'total_entries': len(self._cache),
                'expired_entries': expired_count,
                'max_entries': self.max_entries,
                'default_ttl': self.default_ttl
            }


# Global S3 cache instance
_s3_cache = None


def get_s3_cache() -> S3Cache:
    """Get or create the global S3 cache instance"""
    global _s3_cache
    if _s3_cache is None:
        _s3_cache = S3Cache()
    return _s3_cache


class S3StatResult:
    """Mock stat result for S3 objects"""
    def __init__(self, size=0, mtime=0, is_dir=False):
        self.st_size = size
        self.st_mtime = mtime
        self.st_mode = stat.S_IFDIR | 0o755 if is_dir else stat.S_IFREG | 0o644
        self.st_uid = 0
        self.st_gid = 0
        self.st_atime = mtime
        self.st_ctime = mtime
        self.st_nlink = 1
        self.st_ino = 0
        self.st_dev = 0


class S3WriteFile:
    """File-like object for writing to S3"""
    
    def __init__(self, s3_client, bucket, key, mode, encoding=None, cache_invalidate_callback=None):
        self._s3_client = s3_client
        self._bucket = bucket
        self._key = key
        self._mode = mode
        self._encoding = encoding or 'utf-8'
        self._buffer = io.BytesIO() if 'b' in mode else io.StringIO()
        self._closed = False
        self._cache_invalidate_callback = cache_invalidate_callback
    
    def write(self, data):
        if self._closed:
            raise ValueError("I/O operation on closed file")
        return self._buffer.write(data)
    
    def writelines(self, lines):
        for line in lines:
            self.write(line)
    
    def flush(self):
        pass  # No-op for S3
    
    def close(self):
        if not self._closed:
            # Upload the content to S3
            if 'b' in self._mode:
                content = self._buffer.getvalue()
            else:
                content = self._buffer.getvalue().encode(self._encoding)
            
            self._s3_client.put_object(
                Bucket=self._bucket,
                Key=self._key,
                Body=content
            )
            
            # Invalidate cache after successful write
            if self._cache_invalidate_callback:
                self._cache_invalidate_callback(self._key)
            
            self._closed = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class S3PathImpl(PathImpl):
    """
    AWS S3 implementation of PathImpl.
    
    This class provides S3 operations while implementing the PathImpl interface.
    S3 paths are expected in the format: s3://bucket-name/key/path
    """
    
    @classmethod
    def create_path_with_metadata(cls, s3_uri: str, metadata: Dict[str, Any]) -> 'Path':
        """Create a Path object with S3PathImpl that has metadata
        
        Args:
            s3_uri: S3 URI in format s3://bucket/key
            metadata: Metadata dict with file/directory information
            
        Returns:
            Path object with S3PathImpl implementation containing metadata
        """
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        # Create S3PathImpl with metadata
        s3_impl = cls(s3_uri, metadata=metadata)
        
        # Create Path object and set implementation
        path_obj = Path.__new__(Path)
        path_obj._impl = s3_impl
        return path_obj
    
    def __init__(self, s3_uri: str, metadata: Optional[Dict[str, Any]] = None):
        """Initialize with an S3 URI (s3://bucket/key) and optional metadata
        
        Args:
            s3_uri: S3 URI in format s3://bucket/key
            metadata: Optional metadata dict with keys:
                - is_dir: bool - whether this is a directory
                - is_file: bool - whether this is a file  
                - size: int - file size in bytes
                - last_modified: datetime - last modification time
                - etag: str - S3 ETag
                - storage_class: str - S3 storage class
        """
        if not HAS_BOTO3:
            raise ImportError("boto3 is required for S3 support. Install with: pip install boto3")
        
        self._uri = s3_uri
        self._parse_uri()
        self._s3_client = None
        
        # Store metadata to avoid API calls
        self._metadata = metadata or {}
        self._is_dir_cached = self._metadata.get('is_dir')
        self._is_file_cached = self._metadata.get('is_file')
        self._size_cached = self._metadata.get('size')
        self._mtime_cached = self._metadata.get('last_modified')
        self._etag_cached = self._metadata.get('etag')
        self._storage_class_cached = self._metadata.get('storage_class')
    
    def _parse_uri(self):
        """Parse S3 URI into bucket and key components"""
        if not self._uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI: {self._uri}")
        
        # Remove s3:// prefix
        path_part = self._uri[5:]
        
        if '/' in path_part:
            self._bucket, self._key = path_part.split('/', 1)
        else:
            self._bucket = path_part
            self._key = ''
    
    @property
    def _client(self):
        """Lazy initialization of S3 client"""
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client('s3')
            except NoCredentialsError:
                raise RuntimeError("AWS credentials not found. Configure AWS credentials using AWS CLI, environment variables, or IAM roles.")
        return self._s3_client
    
    @property
    def _cache(self) -> S3Cache:
        """Get the S3 cache instance"""
        return get_s3_cache()
    
    def _cached_api_call(self, operation: str, cache_key_params: Dict[str, Any] = None, 
                        ttl: Optional[int] = None, cache_key_override: Optional[str] = None, **api_params) -> Any:
        """
        Execute an S3 API call with caching support.
        
        Args:
            operation: The boto3 client method name (e.g., 'head_object', 'list_objects_v2')
            cache_key_params: Parameters to include in cache key generation
            ttl: Custom TTL for this cache entry
            cache_key_override: Override the S3 key used for cache key generation
            **api_params: Parameters to pass to the boto3 API call
        
        Returns:
            The API response, either from cache or fresh API call
        """
        if cache_key_params is None:
            cache_key_params = {}
        
        # Use override key if provided, otherwise use instance key
        cache_key = cache_key_override if cache_key_override is not None else self._key
        
        # Try to get from cache first
        cached_result = self._cache.get(
            operation=operation,
            bucket=self._bucket,
            key=cache_key,
            **cache_key_params
        )
        
        if cached_result is not None:
            return cached_result
        
        # Cache miss - make the API call
        try:
            client_method = getattr(self._client, operation)
            result = client_method(**api_params)
            
            # Store in cache
            self._cache.put(
                operation=operation,
                bucket=self._bucket,
                key=cache_key,
                data=result,
                ttl=ttl,
                **cache_key_params
            )
            
            return result
        except Exception as e:
            # Don't cache errors, let them propagate
            raise
    
    def _invalidate_cache_for_write(self, key: Optional[str] = None):
        """Invalidate cache entries that might be affected by a write operation"""
        target_key = key or self._key
        
        # Invalidate the specific key
        self._cache.invalidate_key(self._bucket, target_key)
        
        # Also invalidate parent directory listings
        if '/' in target_key:
            parent_key = '/'.join(target_key.split('/')[:-1]) + '/'
            self._cache.invalidate_key(self._bucket, parent_key)
        
        # Invalidate bucket root listing if this is a top-level key
        if '/' not in target_key.strip('/'):
            self._cache.invalidate_key(self._bucket, '')
    
    def __str__(self) -> str:
        """String representation of the path"""
        return self._uri
    
    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if isinstance(other, S3PathImpl):
            return self._uri == other._uri
        elif isinstance(other, str):
            return self._uri == other
        return False
    
    def __hash__(self) -> int:
        """Hash support for use in sets and dicts"""
        return hash(self._uri)
    
    def __lt__(self, other) -> bool:
        """Less than comparison for sorting"""
        if isinstance(other, S3PathImpl):
            return self._uri < other._uri
        return self._uri < str(other)
    
    # Properties
    @property
    def name(self) -> str:
        """The final component of the path"""
        if not self._key:
            return self._bucket
        # Strip trailing slash before splitting to handle directory keys properly
        key_without_slash = self._key.rstrip('/')
        return key_without_slash.split('/')[-1] if '/' in key_without_slash else key_without_slash
    
    @property
    def stem(self) -> str:
        """The final component without its suffix"""
        name = self.name
        if '.' in name:
            return name.rsplit('.', 1)[0]
        return name
    
    @property
    def suffix(self) -> str:
        """The file extension of the final component"""
        name = self.name
        if '.' in name:
            return '.' + name.rsplit('.', 1)[1]
        return ''
    
    @property
    def suffixes(self) -> List[str]:
        """A list of the path's suffixes"""
        name = self.name
        if '.' not in name:
            return []
        parts = name.split('.')[1:]  # Skip the first part (stem)
        return ['.' + part for part in parts]
    
    @property
    def parent(self) -> 'Path':
        """The logical parent of the path"""
        # Import Path here to avoid circular imports
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        if not self._key:
            # At bucket level, bucket is its own parent (root level)
            return Path(f's3://{self._bucket}/')
        
        # Strip trailing slash to handle directory keys properly
        key_without_trailing_slash = self._key.rstrip('/')
        
        if '/' not in key_without_trailing_slash:
            # Key is at bucket root
            return Path(f's3://{self._bucket}/')
        
        parent_key = '/'.join(key_without_trailing_slash.split('/')[:-1])
        if parent_key:
            return Path(f's3://{self._bucket}/{parent_key}/')
        else:
            # Parent is bucket root
            return Path(f's3://{self._bucket}/')
    
    @property
    def parents(self):
        """A sequence providing access to the logical ancestors of the path"""
        parents = []
        current = self.parent
        bucket_root = f's3://{self._bucket}/'
        
        # Add parents until we reach the bucket root
        while str(current) != bucket_root:
            parents.append(current)
            current = current.parent
            
        # Add the bucket root as the final parent
        if str(current) == bucket_root and str(self) != bucket_root:
            parents.append(current)
        
        return parents
    
    @property
    def parts(self) -> tuple:
        """A tuple giving access to the path's components"""
        parts = ['s3://', self._bucket]
        if self._key:
            parts.extend(self._key.split('/'))
        return tuple(parts)
    
    @property
    def anchor(self) -> str:
        """The concatenation of the drive and root"""
        return 's3://'
    
    # Path manipulation methods
    def absolute(self) -> 'Path':
        """Return an absolute version of this path"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        return Path(self._uri)  # S3 paths are always absolute
    
    def resolve(self, strict: bool = False) -> 'Path':
        """Make the path absolute, resolving any symlinks"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        return Path(self._uri)  # S3 doesn't have symlinks
    
    def expanduser(self) -> 'Path':
        """Return a new path with expanded ~ and ~user constructs"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        return Path(self._uri)  # S3 doesn't have user directories
    
    def joinpath(self, *args) -> 'Path':
        """Combine this path with one or several arguments"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        if not args:
            return Path(self._uri)
        
        # Join the arguments with forward slashes
        additional_path = '/'.join(str(arg) for arg in args)
        
        if self._key:
            new_key = f"{self._key.rstrip('/')}/{additional_path}"
        else:
            new_key = additional_path
        
        return Path(f's3://{self._bucket}/{new_key}')
    
    def with_name(self, name: str) -> 'Path':
        """Return a new path with the name changed"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        if not self._key:
            # At bucket level, change bucket name
            return Path(f's3://{name}/')
        
        if '/' in self._key:
            parent_key = '/'.join(self._key.split('/')[:-1])
            return Path(f's3://{self._bucket}/{parent_key}/{name}')
        else:
            return Path(f's3://{self._bucket}/{name}')
    
    def with_stem(self, stem: str) -> 'Path':
        """Return a new path with the stem changed"""
        suffix = self.suffix
        return self.with_name(stem + suffix)
    
    def with_suffix(self, suffix: str) -> 'Path':
        """Return a new path with the suffix changed"""
        stem = self.stem
        return self.with_name(stem + suffix)
    
    def relative_to(self, other) -> 'Path':
        """Return a version of this path relative to the other path"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        other_str = str(other)
        if not self._uri.startswith(other_str):
            raise ValueError(f"{self._uri} is not relative to {other_str}")
        
        relative_part = self._uri[len(other_str):].lstrip('/')
        return Path(relative_part) if relative_part else Path('.')
    
    # File system query methods
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
    
    def is_dir(self) -> bool:
        """Whether this path is a directory"""
        # Use cached metadata if available
        if self._is_dir_cached is not None:
            return self._is_dir_cached
        
        if not self._key:
            # Bucket is always a directory
            return True
        
        # In S3, directories are represented by keys ending with '/'
        # or by the presence of objects with this key as a prefix
        if self._key.endswith('/'):
            self._is_dir_cached = True
            return True
        
        try:
            # Check if there are objects with this key as a prefix
            response = self._cached_api_call(
                'list_objects_v2',
                cache_key_params={'prefix_check': self._key + '/'},
                Bucket=self._bucket,
                Prefix=self._key + '/',
                MaxKeys=1
            )
            result = response.get('KeyCount', 0) > 0
            self._is_dir_cached = result
            return result
        except ClientError:
            self._is_dir_cached = False
            return False
    
    def is_file(self) -> bool:
        """Whether this path is a regular file"""
        # Use cached metadata if available
        if self._is_file_cached is not None:
            return self._is_file_cached
        
        if not self._key:
            self._is_file_cached = False
            return False  # Bucket is not a file
        
        if self._key.endswith('/'):
            self._is_file_cached = False
            return False  # Directory marker
        
        try:
            self._cached_api_call('head_object', Bucket=self._bucket, Key=self._key)
            self._is_file_cached = True
            return True
        except ClientError:
            self._is_file_cached = False
            return False
    
    def is_symlink(self) -> bool:
        """Whether this path is a symbolic link"""
        return False  # S3 doesn't have symlinks
    
    def is_absolute(self) -> bool:
        """Whether this path is absolute"""
        return True  # S3 paths are always absolute
    
    def stat(self):
        """Return the result of os.stat() on this path"""
        if not self._key:
            # Bucket stat
            return S3StatResult(size=0, mtime=0, is_dir=True)
        
        # Use cached metadata if available
        if self._size_cached is not None and self._mtime_cached is not None:
            size = self._size_cached
            mtime = self._mtime_cached.timestamp() if hasattr(self._mtime_cached, 'timestamp') else self._mtime_cached
            is_dir = self.is_dir()  # This will use cached value if available
            return S3StatResult(size=size, mtime=mtime, is_dir=is_dir)
        
        # Check if this is a directory first (avoids unnecessary head_object calls for virtual directories)
        if self.is_dir():
            # This is a directory - get virtual directory stats
            size, mtime = self._get_virtual_directory_stats()
            return S3StatResult(size=size, mtime=mtime, is_dir=True)
        
        # This should be a file - try head_object
        try:
            response = self._cached_api_call('head_object', cache_key_override=self._key, Bucket=self._bucket, Key=self._key)
            size = response.get('ContentLength', 0)
            mtime = response.get('LastModified', datetime.now()).timestamp()
            
            # Cache the results for future use
            self._size_cached = size
            self._mtime_cached = mtime
            self._is_file_cached = True
            self._is_dir_cached = False
            
            return S3StatResult(size=size, mtime=mtime, is_dir=False)
        except ClientError as e:
            if e.response['Error']['Code'] in ['404', 'NoSuchKey']:
                raise FileNotFoundError(f"S3 object not found: {self._uri}")
            raise OSError(f"Failed to stat S3 object: {e}")
    
    def lstat(self):
        """Return the result of os.lstat() on this path"""
        return self.stat()  # S3 doesn't have symlinks, so lstat == stat
    
    # Directory operations
    def iterdir(self) -> Iterator['Path']:
        """Iterate over the files in this directory"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        try:
            if not self._key:
                # List objects in bucket root
                prefix = ''
                delimiter = '/'
            else:
                # List objects under this key
                prefix = self._key.rstrip('/') + '/'
                delimiter = '/'
            
            # For directory listings, we'll cache each page separately
            # This allows for better cache utilization with large directories
            paginator = self._client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self._bucket,
                Prefix=prefix,
                Delimiter=delimiter
            )
            
            page_num = 0
            for page in page_iterator:
                # Try to get this page from cache
                cache_key_params = {
                    'prefix': prefix,
                    'delimiter': delimiter,
                    'page': page_num
                }
                
                cached_page = self._cache.get(
                    operation='list_objects_v2_page',
                    bucket=self._bucket,
                    key=self._key,
                    **cache_key_params
                )
                
                if cached_page is None:
                    # Cache this page
                    self._cache.put(
                        operation='list_objects_v2_page',
                        bucket=self._bucket,
                        key=self._key,
                        data=page,
                        **cache_key_params
                    )
                    cached_page = page
                
                # Yield directories (common prefixes)
                for prefix_info in cached_page.get('CommonPrefixes', []):
                    dir_key = prefix_info['Prefix'].rstrip('/')
                    
                    # Create directory with metadata
                    dir_metadata = {
                        'is_dir': True,
                        'is_file': False,
                        'size': 0,
                        'last_modified': datetime.now(),  # Virtual directories use current time
                        'etag': '',
                        'storage_class': ''
                    }
                    
                    # Create Path with metadata
                    yield S3PathImpl.create_path_with_metadata(f's3://{self._bucket}/{dir_key}/', dir_metadata)
                
                # Yield files (objects) and cache their stat information
                for obj in cached_page.get('Contents', []):
                    key = obj['Key']
                    if key != prefix:  # Don't include the directory itself
                        # Extract metadata from S3 object
                        size = obj.get('Size', 0)
                        last_modified = obj.get('LastModified')
                        etag = obj.get('ETag', '')
                        storage_class = obj.get('StorageClass', 'STANDARD')
                        
                        # Determine if this is a directory marker (key ends with '/')
                        is_dir = key.endswith('/')
                        is_file = not is_dir
                        
                        # Create file metadata
                        file_metadata = {
                            'is_dir': is_dir,
                            'is_file': is_file,
                            'size': size,
                            'last_modified': last_modified or datetime.now(),
                            'etag': etag,
                            'storage_class': storage_class
                        }
                        
                        # Create a mock head_object response for caching (for backward compatibility)
                        head_response = {
                            'ContentLength': size,
                            'LastModified': last_modified or datetime.now(),
                            'ETag': etag,
                            'StorageClass': storage_class
                        }
                        
                        # Cache this as a head_object response to avoid future API calls
                        self._cache.put(
                            operation='head_object',
                            bucket=self._bucket,
                            key=key,  # Use the file's actual key, not self._key
                            data=head_response,
                            ttl=300  # Cache for 5 minutes
                        )
                        
                        # Create Path with metadata
                        yield S3PathImpl.create_path_with_metadata(f's3://{self._bucket}/{key}', file_metadata)
                
                page_num += 1
        
        except ClientError as e:
            raise OSError(f"Failed to list S3 directory: {e}")
    
    def glob(self, pattern: str) -> Iterator['Path']:
        """Iterate over this subtree and yield all existing files matching pattern"""
        # Simple implementation - list all files and filter
        try:
            for path in self.iterdir():
                if fnmatch.fnmatch(path.name, pattern):
                    yield path
        except OSError:
            return
    
    def rglob(self, pattern: str) -> Iterator['Path']:
        """Recursively iterate over this subtree and yield all existing files matching pattern"""
        # Recursive glob implementation
        def _rglob_recursive(path):
            try:
                for item in path.iterdir():
                    if fnmatch.fnmatch(item.name, pattern):
                        yield item
                    if item.is_dir():
                        yield from _rglob_recursive(item)
            except OSError:
                return
        
        yield from _rglob_recursive(self)
    
    def match(self, pattern: str) -> bool:
        """Return True if this path matches the given pattern"""
        return fnmatch.fnmatch(self.name, pattern)
    
    # File I/O operations
    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """Open the file pointed to by this path"""
        if 'w' in mode or 'a' in mode:
            # Write mode - return a file-like object that uploads on close
            # Pass the cache invalidation callback to the write file
            return S3WriteFile(self._client, self._bucket, self._key, mode, encoding, 
                             cache_invalidate_callback=self._invalidate_cache_for_write)
        else:
            # Read mode - use caching for get_object calls
            try:
                response = self._cached_api_call('get_object', Bucket=self._bucket, Key=self._key)
                content = response['Body'].read()
                
                if 'b' in mode:
                    return io.BytesIO(content)
                else:
                    text_content = content.decode(encoding or 'utf-8')
                    return io.StringIO(text_content)
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    raise FileNotFoundError(f"S3 object not found: {self._uri}")
                raise OSError(f"Failed to open S3 object: {e}")
    
    def read_text(self, encoding=None, errors=None) -> str:
        """Open the file in text mode, read it, and close the file"""
        try:
            response = self._cached_api_call('get_object', Bucket=self._bucket, Key=self._key)
            content = response['Body'].read()
            return content.decode(encoding or 'utf-8', errors or 'strict')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"S3 object not found: {self._uri}")
            raise OSError(f"Failed to read S3 object: {e}")
    
    def read_bytes(self) -> bytes:
        """Open the file in bytes mode, read it, and close the file"""
        try:
            response = self._cached_api_call('get_object', Bucket=self._bucket, Key=self._key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"S3 object not found: {self._uri}")
            raise OSError(f"Failed to read S3 object: {e}")
    
    def write_text(self, data: str, encoding=None, errors=None, newline=None) -> int:
        """Open the file in text mode, write to it, and close the file"""
        try:
            content = data.encode(encoding or 'utf-8', errors or 'strict')
            self._client.put_object(Bucket=self._bucket, Key=self._key, Body=content)
            # Invalidate cache after write
            self._invalidate_cache_for_write()
            return len(data)
        except ClientError as e:
            raise OSError(f"Failed to write S3 object: {e}")
    
    def write_bytes(self, data: bytes) -> int:
        """Open the file in bytes mode, write to it, and close the file"""
        try:
            self._client.put_object(Bucket=self._bucket, Key=self._key, Body=data)
            # Invalidate cache after write
            self._invalidate_cache_for_write()
            return len(data)
        except ClientError as e:
            raise OSError(f"Failed to write S3 object: {e}")
    
    # File system modification operations
    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """Create a new directory at this given path"""
        # In S3, directories are implicit. Create a directory marker if needed.
        if not self._key:
            # Can't create a bucket this way
            raise OSError("Cannot create S3 bucket using mkdir. Use AWS CLI or boto3 directly.")
        
        directory_key = self._key.rstrip('/') + '/'
        
        try:
            # Check if directory already exists
            if self.exists() and not exist_ok:
                raise FileExistsError(f"S3 directory already exists: {self._uri}")
            
            # Create directory marker
            self._client.put_object(Bucket=self._bucket, Key=directory_key, Body=b'')
            # Invalidate cache after directory creation
            self._invalidate_cache_for_write(directory_key)
        except ClientError as e:
            raise OSError(f"Failed to create S3 directory: {e}")
    
    def rmdir(self):
        """Remove this directory"""
        if not self._key:
            raise OSError("Cannot remove S3 bucket using rmdir. Use AWS CLI or boto3 directly.")
        
        try:
            # Check if directory is empty
            response = self._client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=self._key.rstrip('/') + '/',
                MaxKeys=1
            )
            
            if response.get('KeyCount', 0) > 0:
                raise OSError(f"Directory not empty: {self._uri}")
            
            # Remove directory marker if it exists
            directory_key = self._key.rstrip('/') + '/'
            try:
                self._client.delete_object(Bucket=self._bucket, Key=directory_key)
                # Invalidate cache after directory removal
                self._invalidate_cache_for_write(directory_key)
            except ClientError:
                pass  # Directory marker might not exist
        except ClientError as e:
            raise OSError(f"Failed to remove S3 directory: {e}")
    
    def rmtree(self):
        """Remove this directory and all its contents recursively"""
        if not self._key:
            raise OSError("Cannot remove S3 bucket using rmtree. Use AWS CLI or boto3 directly.")
        
        try:
            # List all objects with this prefix
            prefix = self._key.rstrip('/') + '/'
            
            # Use paginator to handle large directories
            paginator = self._client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self._bucket,
                Prefix=prefix
            )
            
            objects_to_delete = []
            
            for page in page_iterator:
                for obj in page.get('Contents', []):
                    objects_to_delete.append({'Key': obj['Key']})
                    
                    # Delete in batches of 1000 (S3 limit)
                    if len(objects_to_delete) >= 1000:
                        self._delete_objects_batch(objects_to_delete)
                        objects_to_delete = []
            
            # Delete remaining objects
            if objects_to_delete:
                self._delete_objects_batch(objects_to_delete)
            
            # Remove directory marker if it exists
            directory_key = self._key.rstrip('/') + '/'
            try:
                self._client.delete_object(Bucket=self._bucket, Key=directory_key)
            except ClientError:
                pass  # Directory marker might not exist
            
            # Invalidate cache after directory removal
            self._invalidate_cache_for_write()
            
        except ClientError as e:
            raise OSError(f"Failed to remove S3 directory tree: {e}")
    
    def _delete_objects_batch(self, objects_to_delete):
        """Delete a batch of S3 objects"""
        if not objects_to_delete:
            return
        
        try:
            response = self._client.delete_objects(
                Bucket=self._bucket,
                Delete={
                    'Objects': objects_to_delete,
                    'Quiet': True
                }
            )
            
            # Check for errors
            if 'Errors' in response and response['Errors']:
                error_messages = []
                for error in response['Errors']:
                    error_messages.append(f"Key: {error['Key']}, Error: {error['Message']}")
                raise OSError(f"Failed to delete some objects: {'; '.join(error_messages)}")
                
        except ClientError as e:
            raise OSError(f"Failed to delete objects batch: {e}")
    
    def _get_virtual_directory_stats(self) -> Tuple[int, float]:
        """
        Get generated stats for virtual directories (directories without actual S3 objects).
        Returns (size, mtime) where size is 0 and mtime is current time or cached value.
        
        Note: With the metadata caching optimization, this method is now mainly a fallback
        for virtual directories that weren't created with cached metadata.
        """
        # For virtual directories, size is always 0
        size = 0
        
        # Use cached modification time if available
        if self._mtime_cached is not None:
            mtime = self._mtime_cached.timestamp() if hasattr(self._mtime_cached, 'timestamp') else self._mtime_cached
            return size, mtime
        
        # Fallback: use current time for virtual directories without cached metadata
        # This is much simpler and faster than making API calls to find the latest child timestamp
        mtime = time.time()
        
        # Cache the result for future use
        self._size_cached = size
        self._mtime_cached = mtime
        
        return size, mtime
    
    def unlink(self, missing_ok=False):
        """Remove this file or symbolic link"""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=self._key)
            # Invalidate cache after deletion
            self._invalidate_cache_for_write()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey' and missing_ok:
                return
            raise OSError(f"Failed to delete S3 object: {e}")
    
    def rename(self, target) -> 'Path':
        """Rename this file or directory to the given target"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        # S3 doesn't have rename, so we copy and delete
        target_path = Path(target) if not isinstance(target, Path) else target
        
        try:
            # Copy to new location
            if isinstance(target_path._impl, S3PathImpl):
                copy_source = {'Bucket': self._bucket, 'Key': self._key}
                self._client.copy_object(
                    CopySource=copy_source,
                    Bucket=target_path._impl._bucket,
                    Key=target_path._impl._key
                )
                # Invalidate cache for target location
                target_path._impl._invalidate_cache_for_write()
            else:
                raise OSError("Cannot rename S3 object to non-S3 path")
            
            # Delete original (this will invalidate cache for source)
            self.unlink()
            return target_path
        except ClientError as e:
            raise OSError(f"Failed to rename S3 object: {e}")
    
    def replace(self, target) -> 'Path':
        """Replace this file or directory with the given target"""
        return self.rename(target)  # Same as rename for S3
    
    def symlink_to(self, target, target_is_directory=False):
        """Make this path a symlink pointing to the target path"""
        raise OSError("S3 does not support symbolic links")
    
    def hardlink_to(self, target):
        """Make this path a hard link pointing to the same file as target"""
        raise OSError("S3 does not support hard links")
    
    def touch(self, mode=0o666, exist_ok=True):
        """Create this file with the given access mode, if it doesn't exist"""
        if self.exists() and not exist_ok:
            raise FileExistsError(f"S3 object already exists: {self._uri}")
        
        try:
            self._client.put_object(Bucket=self._bucket, Key=self._key, Body=b'')
            # Invalidate cache after touch
            self._invalidate_cache_for_write()
        except ClientError as e:
            raise OSError(f"Failed to touch S3 object: {e}")
    
    def chmod(self, mode):
        """Change the permissions of the path"""
        # S3 doesn't have traditional file permissions
        # This is a no-op for compatibility
        pass
    
    # Storage-specific methods
    def is_remote(self) -> bool:
        """Return True if this path represents a remote resource"""
        return True
    
    def get_scheme(self) -> str:
        """Return the scheme of the path (e.g., 'file', 's3', 'scp')"""
        return 's3'
    
    def as_uri(self) -> str:
        """Return the path as a URI"""
        return self._uri
    
    # Compatibility methods
    def samefile(self, other_path) -> bool:
        """Return whether other_path is the same or not as this file"""
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        
        if isinstance(other_path, Path):
            return str(self) == str(other_path)
        return str(self) == str(other_path)
    
    def as_posix(self) -> str:
        """Return the string representation with forward slashes"""
        return self._uri


# Cache management functions
def configure_s3_cache(ttl: int = 60, max_entries: int = 1000):
    """Configure the global S3 cache settings"""
    global _s3_cache
    _s3_cache = S3Cache(default_ttl=ttl, max_entries=max_entries)


def clear_s3_cache():
    """Clear all entries from the S3 cache"""
    cache = get_s3_cache()
    cache.clear()


def get_s3_cache_stats() -> Dict[str, Any]:
    """Get S3 cache statistics"""
    cache = get_s3_cache()
    return cache.get_stats()