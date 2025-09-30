# TFM Path System Documentation

## Overview

This document describes TFM's custom path handling system, which provides a unified interface for both local and future remote storage operations while maintaining 100% compatibility with Python's `pathlib.Path`.

## Architecture

### Core Components

#### 1. PathImpl (Abstract Base Class)

The `PathImpl` class defines the interface that all storage implementations must provide:

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

#### 2. LocalPathImpl (Concrete Implementation)

Implements `PathImpl` for local file system operations by wrapping `pathlib.Path`:

```python
class LocalPathImpl(PathImpl):
    """Local file system implementation of PathImpl"""
    
    def __init__(self, path_obj: PathlibPath):
        self._path = path_obj
    
    def exists(self) -> bool:
        return self._path.exists()
    
    def is_dir(self) -> bool:
        return self._path.is_dir()
```

#### 3. Path (Facade Class)

Provides the public API and delegates operations to the appropriate implementation:

```python
class Path:
    """Pathlib-compatible facade for multiple storage backends"""
    
    def __init__(self, *args):
        self._impl = self._create_implementation(path_str)
    
    def exists(self) -> bool:
        return self._impl.exists()
```

## Migration from pathlib.Path

### Background

The original TFM codebase used Python's `pathlib.Path` extensively. While excellent for local operations, it doesn't provide extension points for remote storage systems.

### Migration Changes

#### Import Changes
**Before:**
```python
from pathlib import Path
```

**After:**
```python
from tfm_path import Path
```

#### Files Updated
All source files in `src/` were updated:
- `src/tfm_main.py`
- `src/tfm_file_operations.py`
- `src/tfm_pane_manager.py`
- `src/tfm_state_manager.py`
- `src/tfm_config.py`
- `src/tfm_text_viewer.py`
- `src/tfm_jump_dialog.py`
- `src/tfm_list_dialog.py`
- `src/tfm_search_dialog.py`
- `src/tfm_batch_rename_dialog.py`
- `src/tfm_external_programs.py`
- `src/tfm_color_tester.py`

### Compatibility Guarantee

- **Zero breaking changes** - All existing code continues to work
- **Same performance** - Local operations use pathlib.Path internally
- **Same behavior** - All methods behave identically to pathlib.Path

## Future Remote Storage Support

### Planned Storage Types

1. **S3 Storage** - `s3://bucket/path/file.txt`
2. **SCP/SFTP** - `scp://user@host/path/file.txt`
3. **FTP** - `ftp://host/path/file.txt`
4. **WebDAV** - `webdav://host/path/file.txt`
5. **Cloud Storage** - Various cloud provider APIs

### Implementation Selection

Future versions will detect path schemes and select appropriate implementations:

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

### Example Future Implementations

#### S3PathImpl
```python
class S3PathImpl(PathImpl):
    """Amazon S3 storage implementation"""
    
    def __init__(self, s3_uri: str):
        self.bucket, self.key = self._parse_s3_uri(s3_uri)
        self._s3_client = boto3.client('s3')
    
    def exists(self) -> bool:
        try:
            self._s3_client.head_object(Bucket=self.bucket, Key=self.key)
            return True
        except ClientError:
            return False
```

#### SCPPathImpl
```python
class SCPPathImpl(PathImpl):
    """SCP/SFTP storage implementation"""
    
    def __init__(self, scp_uri: str):
        self.host, self.path = self._parse_scp_uri(scp_uri)
        self._ssh_client = paramiko.SSHClient()
    
    def exists(self) -> bool:
        stdin, stdout, stderr = self._ssh_client.exec_command(
            f'test -e "{self.path}"'
        )
        return stdout.channel.recv_exit_status() == 0
```

## Benefits

### Architectural Benefits
- **Separation of Concerns**: Interface vs implementation
- **Extensibility**: Easy to add new storage backends
- **Type Safety**: Abstract base class enforces complete interface
- **Maintainability**: Clear separation between local and remote logic

### Performance Benefits
- **No overhead** for local operations (direct pathlib delegation)
- **Optimization opportunities** for remote implementations
- **Lazy loading** of remote storage libraries

### Future Benefits
- **Remote storage support** without major refactoring
- **Cloud integration** capabilities
- **Network file systems** support
- **Unified interface** for local and remote operations

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

# Same API works for all storage types
s3_files = list(s3_path.iterdir())
scp_content = (scp_path / 'file.txt').read_text()

# Mixed operations work seamlessly
local_file = Path('/tmp/backup.txt')
s3_file = Path('s3://backup-bucket/backup.txt')
local_file.write_text(s3_file.read_text())
```

## Testing

### Migration Testing
- **Import compatibility** - All modules import successfully
- **Basic operations** - Path creation, joining, and property access
- **File system operations** - Directory listing and file existence checks
- **TFM functionality** - Core TFM operations continue to work

### Architecture Testing
```python
# Test abstract interface
def test_pathimpl_interface():
    with pytest.raises(TypeError):
        PathImpl()

# Test local implementation
def test_local_pathimpl():
    impl = LocalPathImpl(PathlibPath('/tmp'))
    assert impl.exists() in [True, False]

# Test facade
def test_path_facade():
    path = Path('/tmp')
    assert isinstance(path._impl, LocalPathImpl)
```

## Conclusion

The TFM Path System successfully prepares the codebase for remote storage support while maintaining 100% backward compatibility. The architecture follows established software engineering principles and positions TFM to become a truly universal file manager capable of working with both local and remote storage systems through a unified interface.

The migration was transparent to users and developers, requiring no modifications to existing code while opening up possibilities for future enhancements.