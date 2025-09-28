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
from datetime import datetime
from typing import Iterator, List

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
    
    def __init__(self, s3_client, bucket, key, mode, encoding=None):
        self._s3_client = s3_client
        self._bucket = bucket
        self._key = key
        self._mode = mode
        self._encoding = encoding or 'utf-8'
        self._buffer = io.BytesIO() if 'b' in mode else io.StringIO()
        self._closed = False
    
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
    
    def __init__(self, s3_uri: str):
        """Initialize with an S3 URI (s3://bucket/key)"""
        if not HAS_BOTO3:
            raise ImportError("boto3 is required for S3 support. Install with: pip install boto3")
        
        self._uri = s3_uri
        self._parse_uri()
        self._s3_client = None
    
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
        return self._key.split('/')[-1] if '/' in self._key else self._key
    
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
            # At bucket level, parent is the S3 root
            return Path('s3://')
        
        if '/' not in self._key:
            # Key is at bucket root
            return Path(f's3://{self._bucket}/')
        
        parent_key = '/'.join(self._key.split('/')[:-1])
        return Path(f's3://{self._bucket}/{parent_key}/')
    
    @property
    def parents(self):
        """A sequence providing access to the logical ancestors of the path"""
        parents = []
        current = self.parent
        while str(current) != 's3://':
            parents.append(current)
            current = current.parent
        
        # Import Path here to avoid circular imports
        try:
            from .tfm_path import Path
        except ImportError:
            from tfm_path import Path
        parents.append(Path('s3://'))
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
                self._client.head_bucket(Bucket=self._bucket)
                return True
            else:
                # Check if object exists
                self._client.head_object(Bucket=self._bucket, Key=self._key)
                return True
        except ClientError as e:
            if e.response['Error']['Code'] in ['404', 'NoSuchBucket', 'NoSuchKey']:
                return False
            raise
    
    def is_dir(self) -> bool:
        """Whether this path is a directory"""
        if not self._key:
            # Bucket is always a directory
            return True
        
        # In S3, directories are represented by keys ending with '/'
        # or by the presence of objects with this key as a prefix
        if self._key.endswith('/'):
            return True
        
        try:
            # Check if there are objects with this key as a prefix
            response = self._client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=self._key + '/',
                MaxKeys=1
            )
            return response.get('KeyCount', 0) > 0
        except ClientError:
            return False
    
    def is_file(self) -> bool:
        """Whether this path is a regular file"""
        if not self._key:
            return False  # Bucket is not a file
        
        if self._key.endswith('/'):
            return False  # Directory marker
        
        try:
            self._client.head_object(Bucket=self._bucket, Key=self._key)
            return True
        except ClientError:
            return False
    
    def is_symlink(self) -> bool:
        """Whether this path is a symbolic link"""
        return False  # S3 doesn't have symlinks
    
    def is_absolute(self) -> bool:
        """Whether this path is absolute"""
        return True  # S3 paths are always absolute
    
    def stat(self):
        """Return the result of os.stat() on this path"""
        try:
            if not self._key:
                # Bucket stat
                return S3StatResult(size=0, mtime=0, is_dir=True)
            
            response = self._client.head_object(Bucket=self._bucket, Key=self._key)
            size = response.get('ContentLength', 0)
            mtime = response.get('LastModified', datetime.now()).timestamp()
            return S3StatResult(size=size, mtime=mtime, is_dir=self.is_dir())
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
            
            paginator = self._client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self._bucket,
                Prefix=prefix,
                Delimiter=delimiter
            )
            
            for page in page_iterator:
                # Yield directories (common prefixes)
                for prefix_info in page.get('CommonPrefixes', []):
                    dir_key = prefix_info['Prefix'].rstrip('/')
                    yield Path(f's3://{self._bucket}/{dir_key}/')
                
                # Yield files (objects)
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key != prefix:  # Don't include the directory itself
                        yield Path(f's3://{self._bucket}/{key}')
        
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
            return S3WriteFile(self._client, self._bucket, self._key, mode, encoding)
        else:
            # Read mode
            try:
                response = self._client.get_object(Bucket=self._bucket, Key=self._key)
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
            response = self._client.get_object(Bucket=self._bucket, Key=self._key)
            content = response['Body'].read()
            return content.decode(encoding or 'utf-8', errors or 'strict')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"S3 object not found: {self._uri}")
            raise OSError(f"Failed to read S3 object: {e}")
    
    def read_bytes(self) -> bytes:
        """Open the file in bytes mode, read it, and close the file"""
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=self._key)
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
            return len(data)
        except ClientError as e:
            raise OSError(f"Failed to write S3 object: {e}")
    
    def write_bytes(self, data: bytes) -> int:
        """Open the file in bytes mode, write to it, and close the file"""
        try:
            self._client.put_object(Bucket=self._bucket, Key=self._key, Body=data)
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
            except ClientError:
                pass  # Directory marker might not exist
        except ClientError as e:
            raise OSError(f"Failed to remove S3 directory: {e}")
    
    def unlink(self, missing_ok=False):
        """Remove this file or symbolic link"""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=self._key)
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
            else:
                raise OSError("Cannot rename S3 object to non-S3 path")
            
            # Delete original
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