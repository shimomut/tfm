# TFM Path Migration Documentation

## Overview

This document describes the migration from Python's standard `pathlib.Path` to TFM's custom `tfm_path.Path` class, which prepares the codebase for future remote storage support.

## Background

The original TFM codebase used Python's `pathlib.Path` extensively throughout the source code. While `pathlib.Path` is excellent for local file operations, it doesn't provide a clean way to extend support for remote storage systems like S3, SCP, SFTP, or other cloud storage providers.

## Solution

We created a new `tfm_path.Path` class that:

1. **Maintains 100% compatibility** with the existing `pathlib.Path` API
2. **Wraps `pathlib.Path`** internally for all local operations
3. **Provides extension points** for future remote storage implementations
4. **Requires no changes** to existing TFM code that uses Path objects

## Implementation Details

### File Structure

- **`src/tfm_path.py`** - New Path class implementation
- **All source files** - Updated to import from `tfm_path` instead of `pathlib`

### Key Features

#### 1. Full pathlib.Path Compatibility

The new `Path` class implements all methods and properties from `pathlib.Path`:

```python
from tfm_path import Path

# All these work exactly as before
p = Path('/home/user/documents')
print(p.name)           # 'documents'
print(p.parent)         # Path('/home/user')
print(p.suffix)         # ''
print(p.exists())       # True/False

# Path operations
files = list(p.iterdir())
new_path = p / 'subfolder' / 'file.txt'
absolute = p.absolute()
```

#### 2. Class Methods

All pathlib class methods are supported:

```python
home = Path.home()      # User's home directory
cwd = Path.cwd()        # Current working directory
```

#### 3. Operators and Magic Methods

All operators work as expected:

```python
path1 = Path('/home')
path2 = path1 / 'user' / 'documents'  # Path joining
str_path = str(path2)                 # String conversion
are_equal = path1 == Path('/home')    # Equality comparison
```

#### 4. File Operations

All file I/O operations are supported:

```python
path = Path('file.txt')
content = path.read_text()
path.write_text('new content')
path.mkdir(parents=True, exist_ok=True)
```

### Extension Points for Remote Storage

The new Path class includes methods that prepare for remote storage support:

```python
# Future remote storage methods
path.is_remote()        # Returns False for local paths
path.get_scheme()       # Returns 'file' for local paths
path.as_uri()          # Returns file:// URI
```

## Migration Changes

### Import Changes

**Before:**
```python
from pathlib import Path
```

**After:**
```python
from tfm_path import Path
```

### Files Updated

All source files in `src/` were updated to use the new import:

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

### No Functional Changes

- **Zero breaking changes** - All existing code continues to work
- **Same performance** - Local operations use pathlib.Path internally
- **Same behavior** - All methods behave identically to pathlib.Path

## Future Remote Storage Support

The new architecture enables future support for remote storage:

### Planned Remote Storage Types

1. **S3 Storage** - `s3://bucket/path/file.txt`
2. **SCP/SFTP** - `scp://user@host/path/file.txt`
3. **FTP** - `ftp://host/path/file.txt`
4. **WebDAV** - `webdav://host/path/file.txt`
5. **Cloud Storage** - Various cloud provider APIs

### Implementation Strategy

Future remote storage support will be implemented by:

1. **Detecting path schemes** - Parse URIs to determine storage type
2. **Storage-specific backends** - Implement remote operations for each type
3. **Transparent operation** - Existing TFM code continues to work unchanged
4. **Caching and optimization** - Local caching for remote file listings

### Example Future Usage

```python
# Local path (current behavior)
local_path = Path('/home/user/file.txt')

# Future remote paths (same API)
s3_path = Path('s3://mybucket/path/file.txt')
scp_path = Path('scp://user@server:/home/user/file.txt')

# Same operations work for both
print(local_path.name)  # 'file.txt'
print(s3_path.name)     # 'file.txt'

local_files = list(local_path.parent.iterdir())
s3_files = list(s3_path.parent.iterdir())
```

## Testing

The migration has been tested to ensure:

1. **Import compatibility** - All modules import successfully
2. **Basic operations** - Path creation, joining, and property access
3. **File system operations** - Directory listing and file existence checks
4. **TFM functionality** - Core TFM operations continue to work

## Benefits

### Immediate Benefits

1. **Cleaner architecture** - Centralized path handling
2. **Future-ready** - Prepared for remote storage without major refactoring
3. **Maintainable** - Single point of control for path operations
4. **Compatible** - No disruption to existing functionality

### Future Benefits

1. **Remote storage support** - Access files on remote systems
2. **Cloud integration** - Work with cloud storage providers
3. **Network file systems** - Support for various network protocols
4. **Unified interface** - Same API for local and remote operations

## Conclusion

The migration to `tfm_path.Path` successfully prepares TFM for remote storage support while maintaining 100% backward compatibility. The change is transparent to users and developers, requiring no modifications to existing code while opening up possibilities for future enhancements.

This architectural improvement positions TFM to become a truly universal file manager capable of working with both local and remote storage systems through a unified, consistent interface.