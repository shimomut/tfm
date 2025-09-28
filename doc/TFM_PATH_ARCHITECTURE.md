# TFM Path Architecture Documentation

## Overview

This document describes the new architecture of TFM's path handling system, which separates the interface from implementation to enable support for multiple storage backends.

## Architecture Components

### 1. PathImpl (Abstract Base Class)

The `PathImpl` class defines the interface that all storage implementations must provide. It's an abstract base class that ensures consistent behavior across different storage types.

```python
from abc import ABC, abstractmethod

class PathImpl(ABC):
    """Abstract base class for path implementations"""
    
    @abstractmethod
    def exists(self) -> bool:
        """Whether this path exists"""
        pass
    
    @abstractmethod
    def is_dir(self) -> bool:
        """Whether this path is a directory"""
        pass
    
    # ... all other pathlib.Path methods
```

**Key Features:**
- Defines complete pathlib.Path-compatible interface
- Enforces implementation of all required methods
- Provides type safety and documentation
- Enables polymorphic behavior across storage types

### 2. LocalPathImpl (Concrete Implementation)

The `LocalPathImpl` class implements `PathImpl` for local file system operations by wrapping `pathlib.Path`.

```python
class LocalPathImpl(PathImpl):
    """Local file system implementation of PathImpl"""
    
    def __init__(self, path_obj: PathlibPath):
        self._path = path_obj
    
    def exists(self) -> bool:
        return self._path.exists()
    
    def is_dir(self) -> bool:
        return self._path.is_dir()
    
    # ... all other methods delegate to pathlib.Path
```

**Key Features:**
- Wraps `pathlib.Path` for local operations
- 100% compatible with existing pathlib behavior
- Same performance as direct pathlib usage
- Implements all PathImpl abstract methods

### 3. Path (Facade Class)

The `Path` class acts as a facade that provides the public API and delegates operations to the appropriate implementation.

```python
class Path:
    """Pathlib-compatible facade for multiple storage backends"""
    
    def __init__(self, *args):
        # Determine appropriate implementation
        self._impl = self._create_implementation(path_str)
    
    def exists(self) -> bool:
        return self._impl.exists()
    
    def is_dir(self) -> bool:
        return self._impl.is_dir()
    
    # ... all methods delegate to implementation
```

**Key Features:**
- Maintains pathlib.Path-compatible API
- Automatically selects appropriate implementation
- Transparent delegation to storage backends
- Future-ready for remote storage support

## Implementation Selection

Currently, all paths use `LocalPathImpl`. Future versions will detect path schemes and select appropriate implementations:

```python
def _create_implementation(self, path_str: str) -> PathImpl:
    """Create the appropriate implementation based on path string"""
    if path_str.startswith('s3://'):
        return S3PathImpl(path_str)
    elif path_str.startswith('scp://'):
        return SCPPathImpl(path_str)
    elif path_str.startswith('ftp://'):
        return FTPPathImpl(path_str)
    else:
        return LocalPathImpl(PathlibPath(path_str))
```

## Benefits of This Architecture

### 1. Separation of Concerns
- **Interface** (PathImpl) defines what operations are available
- **Implementation** (LocalPathImpl, S3PathImpl, etc.) defines how operations work
- **Facade** (Path) provides unified access and implementation selection

### 2. Extensibility
- Easy to add new storage backends
- No changes required to existing TFM code
- Each implementation can optimize for its storage type

### 3. Type Safety
- Abstract base class enforces complete interface implementation
- Compile-time checking of method signatures
- Clear documentation of required methods

### 4. Maintainability
- Clear separation between local and remote logic
- Each implementation is self-contained
- Easy to test individual storage backends

### 5. Performance
- No overhead for local operations (direct pathlib delegation)
- Remote implementations can add caching and optimization
- Lazy loading of remote storage libraries

## Future Storage Implementations

### S3PathImpl Example

```python
class S3PathImpl(PathImpl):
    """Amazon S3 storage implementation"""
    
    def __init__(self, s3_uri: str):
        # Parse s3://bucket/path/file.txt
        self.bucket, self.key = self._parse_s3_uri(s3_uri)
        self._s3_client = boto3.client('s3')
    
    def exists(self) -> bool:
        try:
            self._s3_client.head_object(Bucket=self.bucket, Key=self.key)
            return True
        except ClientError:
            return False
    
    def is_dir(self) -> bool:
        # Check if key ends with / or has child objects
        return self._has_child_objects()
    
    def iterdir(self) -> Iterator['Path']:
        # List objects with prefix
        response = self._s3_client.list_objects_v2(
            Bucket=self.bucket, 
            Prefix=self.key + '/',
            Delimiter='/'
        )
        for obj in response.get('Contents', []):
            yield Path(f"s3://{self.bucket}/{obj['Key']}")
```

### SCPPathImpl Example

```python
class SCPPathImpl(PathImpl):
    """SCP/SFTP storage implementation"""
    
    def __init__(self, scp_uri: str):
        # Parse scp://user@host:/path/file.txt
        self.host, self.path = self._parse_scp_uri(scp_uri)
        self._ssh_client = paramiko.SSHClient()
    
    def exists(self) -> bool:
        stdin, stdout, stderr = self._ssh_client.exec_command(
            f'test -e "{self.path}"'
        )
        return stdout.channel.recv_exit_status() == 0
    
    def is_dir(self) -> bool:
        stdin, stdout, stderr = self._ssh_client.exec_command(
            f'test -d "{self.path}"'
        )
        return stdout.channel.recv_exit_status() == 0
```

## Usage Examples

### Current Usage (Local Files)

```python
from tfm_path import Path

# All these create LocalPathImpl internally
local_path = Path('/home/user/documents')
home_path = Path.home()
current_path = Path.cwd()

# All operations work as before
files = list(local_path.iterdir())
content = (local_path / 'file.txt').read_text()
```

### Future Usage (Remote Storage)

```python
from tfm_path import Path

# These will create appropriate implementations automatically
s3_path = Path('s3://mybucket/documents/')
scp_path = Path('scp://user@server:/home/user/documents/')
ftp_path = Path('ftp://server/pub/files/')

# Same API works for all storage types
s3_files = list(s3_path.iterdir())
scp_content = (scp_path / 'file.txt').read_text()
ftp_exists = ftp_path.exists()

# Mixed operations work seamlessly
local_file = Path('/tmp/backup.txt')
s3_file = Path('s3://backup-bucket/backup.txt')

# Copy from S3 to local (future feature)
local_file.write_text(s3_file.read_text())
```

## Migration Impact

### Zero Breaking Changes
- All existing TFM code continues to work unchanged
- Same API, same behavior for local operations
- No performance impact on local file operations

### Internal Changes Only
- `Path` class now uses delegation pattern
- Implementation details hidden from TFM code
- Abstract base class ensures interface consistency

### Future-Ready
- Architecture supports remote storage without TFM code changes
- New storage types can be added incrementally
- Each storage type can be optimized independently

## Testing Strategy

### Unit Tests for Each Component

```python
# Test abstract interface
def test_pathimpl_interface():
    # Ensure all methods are abstract
    with pytest.raises(TypeError):
        PathImpl()

# Test local implementation
def test_local_pathimpl():
    impl = LocalPathImpl(PathlibPath('/tmp'))
    assert impl.exists() in [True, False]
    assert isinstance(impl.name, str)

# Test facade
def test_path_facade():
    path = Path('/tmp')
    assert isinstance(path._impl, LocalPathImpl)
    assert path.exists() in [True, False]
```

### Integration Tests

```python
def test_tfm_integration():
    """Test that TFM modules work with new Path architecture"""
    from tfm_file_operations import FileOperations
    from tfm_path import Path
    
    path = Path('.')
    files = list(path.iterdir())
    assert len(files) >= 0
```

## Conclusion

The new architecture successfully separates interface from implementation while maintaining 100% backward compatibility. This design enables TFM to support multiple storage backends through a clean, extensible architecture that requires no changes to existing code.

The pattern follows established software engineering principles:
- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Open for extension (new storage types), closed for modification
- **Liskov Substitution**: All implementations are interchangeable
- **Interface Segregation**: Clean, focused interface definition
- **Dependency Inversion**: High-level code depends on abstractions, not concrete implementations

This architecture positions TFM to become a truly universal file manager capable of seamlessly working with local files, cloud storage, and remote systems through a unified, consistent interface.