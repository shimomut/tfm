# Archive Virtual Directory Implementation

## Overview

This document provides comprehensive technical documentation for the archive virtual directory feature in TFM (TUI File Manager). This feature enables users to browse archive contents as virtual directories without extracting files to disk, using a PathImpl-based architecture that integrates seamlessly with TFM's existing file management infrastructure.

## Architecture

### High-Level Design

The archive support follows TFM's established pattern for virtual filesystems, implementing the PathImpl interface to provide transparent access to archive contents:

```
┌─────────────────────────────────────────────────────────────┐
│                     TFM Main Application                     │
│  (tfm_main.py, tfm_pane_manager.py, tfm_file_operations.py) │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─ Uses Path abstraction
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      Path Facade                             │
│                    (tfm_path.py)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┬──────────────┐
         │             │             │              │
┌────────▼────────┐ ┌──▼──────────┐ ┌▼────────────┐ ┌▼──────────────┐
│ LocalPathImpl   │ │ S3PathImpl  │ │ ArchivePath │ │ Future impls  │
│ (tfm_path.py)   │ │ (tfm_s3.py) │ │ Impl        │ │ (SCP, FTP...) │
│                 │ │             │ │ (tfm_       │ │               │
│ Local files     │ │ S3 objects  │ │ archive.py) │ │               │
└─────────────────┘ └─────────────┘ └─────────────┘ └───────────────┘
```

### Archive Path URI Format

Archive paths use a special URI scheme to distinguish them from regular paths:

```
archive://<absolute_path_to_archive>#<internal_path>

Examples:
archive:///home/user/data.zip#
archive:///home/user/data.zip#folder/
archive:///home/user/data.zip#folder/file.txt
archive:///home/user/backup.tar.gz#logs/app.log
```

The `#` separator distinguishes the archive file path from the internal path within the archive.


## Core Components

### 1. ArchiveEntry Data Class

The `ArchiveEntry` dataclass provides a unified representation of archive entries across different formats:

```python
@dataclass
class ArchiveEntry:
    """Represents an entry (file or directory) within an archive"""
    name: str                    # Entry name (filename or dirname)
    internal_path: str           # Full path within archive
    is_dir: bool                 # Whether this is a directory
    size: int                    # Uncompressed size in bytes
    compressed_size: int         # Compressed size in bytes
    mtime: float                 # Modification time as timestamp
    mode: int                    # File permissions (Unix-style)
    archive_type: str            # Archive format ('zip', 'tar', 'tar.gz', etc.)
```

**Key Methods:**

- `to_stat_result()`: Converts the entry to an `os.stat_result` object for compatibility with code expecting filesystem stat results
- `from_zip_info(zip_info, archive_type)`: Factory method to create an entry from a `zipfile.ZipInfo` object
- `from_tar_info(tar_info, archive_type)`: Factory method to create an entry from a `tarfile.TarInfo` object

**Design Rationale:**

The dataclass approach provides:
- Type safety with Python's type hints
- Immutability by default (frozen=False allows caching optimizations)
- Clean separation between archive formats through factory methods
- Compatibility with existing filesystem code through `to_stat_result()`


### 2. ArchiveHandler Class Hierarchy

The `ArchiveHandler` base class defines the interface for archive access, with format-specific implementations:

```python
class ArchiveHandler:
    """Base class for handling archive file access"""
    
    def __init__(self, archive_path: Path):
        self._archive_path = archive_path
        self._archive_obj = None
        self._entry_cache: Dict[str, ArchiveEntry] = {}
        self._directory_cache: Dict[str, List[str]] = {}
        self._is_open = False
        self._last_access = 0.0
    
    def open(self): ...
    def close(self): ...
    def list_entries(self, internal_path: str = "") -> List[ArchiveEntry]: ...
    def get_entry_info(self, internal_path: str) -> Optional[ArchiveEntry]: ...
    def extract_to_bytes(self, internal_path: str) -> bytes: ...
    def extract_to_file(self, internal_path: str, target_path: Path): ...
```

**Implementations:**

1. **ZipHandler**: Handles ZIP archives using Python's `zipfile` module
   - Supports lazy loading for large archives (>1000 entries)
   - Caches directory structure for fast navigation
   - Creates virtual directory entries for implicit directories

2. **TarHandler**: Handles TAR archives (including compressed variants)
   - Supports tar, tar.gz, tar.bz2, tar.xz formats
   - Uses `tarfile` module with appropriate compression modes
   - Handles both explicit and implicit directory entries

**Key Features:**

- **Lazy Loading**: Large archives (>1000 entries) only cache directory structure initially, loading individual entries on demand
- **Virtual Directories**: Creates directory entries for paths that don't have explicit entries in the archive
- **Cross-Storage Support**: Downloads remote archives to temporary files for processing
- **Context Manager Support**: Implements `__enter__` and `__exit__` for safe resource management


### 3. ArchiveCache Class

The `ArchiveCache` class manages opened archives with LRU eviction and TTL-based expiration:

```python
class ArchiveCache:
    """Cache for opened archives and their structures"""
    
    def __init__(self, max_open: int = 5, ttl: int = 300):
        self._max_open = max_open
        self._ttl = ttl
        self._handlers: Dict[str, ArchiveHandler] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # Performance metrics
        self._cache_hits = 0
        self._cache_misses = 0
        self._evictions = 0
        self._total_open_time = 0.0
```

**Caching Strategy:**

1. **LRU Eviction**: When the cache reaches `max_open` archives, the least recently used archive is closed and evicted
2. **TTL Expiration**: Archives not accessed for `ttl` seconds are automatically expired and closed
3. **Thread Safety**: All cache operations are protected by a reentrant lock (`RLock`)
4. **Performance Metrics**: Tracks cache hits, misses, evictions, and average open time

**Configuration:**

The cache can be configured through `tfm_config.py`:
```python
ARCHIVE_CACHE_MAX_OPEN = 5    # Maximum open archives
ARCHIVE_CACHE_TTL = 300        # Time-to-live in seconds
```

**Cache Statistics:**

The `get_stats()` method provides monitoring data:
- `open_archives`: Number of currently open archives
- `cache_hits`: Number of cache hits
- `cache_misses`: Number of cache misses
- `hit_rate`: Cache hit rate (0.0 to 1.0)
- `evictions`: Number of LRU evictions performed
- `avg_open_time`: Average time to open an archive


### 4. ArchivePathImpl Class

The `ArchivePathImpl` class implements the `PathImpl` interface for archive paths:

```python
class ArchivePathImpl(PathImpl):
    """Archive file implementation of PathImpl"""
    
    def __init__(self, archive_uri: str, metadata: Optional[Dict[str, Any]] = None):
        self._uri = archive_uri
        self._metadata = metadata or {}
        self._parse_uri()
        self._cache = get_archive_cache()
        self._property_cache = {}
```

**Key Responsibilities:**

1. **URI Parsing**: Splits archive URI into archive path and internal path components
2. **Path Properties**: Implements all PathImpl properties (name, stem, suffix, parent, parts, etc.)
3. **Path Manipulation**: Provides methods for path operations (joinpath, with_name, with_suffix, etc.)
4. **File System Queries**: Implements exists(), is_dir(), is_file(), stat(), etc.
5. **Directory Operations**: Supports iterdir(), glob(), rglob() for directory traversal
6. **File I/O**: Provides open(), read_text(), read_bytes() for file access

**Property Caching:**

To avoid repeated computation, frequently accessed properties are cached:
```python
self._property_cache = {
    'name': 'file.txt',
    'parts': ('/path/to/archive.zip', '#', 'folder', 'file.txt')
}
```

**Metadata Caching:**

Archive entries are cached to avoid repeated archive reads:
```python
self._metadata = {
    'entry': ArchiveEntry(...)  # Cached entry information
}
```


## Error Handling

### Exception Hierarchy

The implementation defines a hierarchy of custom exceptions for precise error handling:

```python
class ArchiveError(Exception):
    """Base exception for archive operations"""
    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(message)
        self.user_message = user_message or message

class ArchiveFormatError(ArchiveError):
    """Unsupported or invalid archive format"""

class ArchiveCorruptedError(ArchiveError):
    """Archive file is corrupted"""

class ArchiveExtractionError(ArchiveError):
    """Error during file extraction"""

class ArchiveNavigationError(ArchiveError):
    """Error navigating within archive"""

class ArchivePermissionError(ArchiveError):
    """Permission denied for archive operation"""

class ArchiveDiskSpaceError(ArchiveError):
    """Insufficient disk space for archive operation"""
```

**Design Rationale:**

Each exception type includes both a technical message (for logging) and a user-friendly message (for display):

```python
raise ArchiveCorruptedError(
    f"Corrupted ZIP archive: {e}",  # Technical message
    f"Archive '{self._archive_path.name}' is corrupted or invalid"  # User message
)
```

### Error Recovery Strategies

1. **Archive Access Failures**: Display error message, remain in current directory
2. **Extraction Failures**: Display error with specific file/reason, continue with other files
3. **Navigation Failures**: Return to archive root or exit archive
4. **Resource Exhaustion**: Close least recently used archives, retry operation


## Performance Optimizations

### 1. Lazy Loading for Large Archives

For archives with more than 1000 entries, the ZipHandler implements lazy loading:

```python
# Process all entries
infolist = self._archive_obj.infolist()
is_large_archive = len(infolist) > 1000

# For large archives, only cache directory structure initially
if not is_large_archive or entry.is_dir or normalized_path.count('/') < 2:
    # Cache the entry (all entries for small archives, only shallow for large)
    self._entry_cache[normalized_path] = entry
```

**Benefits:**
- Reduces initial open time for large archives
- Minimizes memory usage
- Entries are loaded on-demand when accessed

### 2. Directory Structure Caching

Both handlers maintain a directory cache for fast navigation:

```python
self._directory_cache: Dict[str, List[str]] = {
    '': ['folder1', 'folder2', 'file.txt'],
    'folder1': ['subfolder', 'file1.txt'],
    'folder2': ['file2.txt']
}
```

**Benefits:**
- O(1) lookup for directory contents
- Avoids scanning entire archive for each directory listing
- Supports efficient parent-child relationships

### 3. Property Caching

Frequently accessed properties are cached to avoid repeated computation:

```python
@property
def name(self) -> str:
    if 'name' in self._property_cache:
        return self._property_cache['name']
    
    # Compute name...
    self._property_cache['name'] = result
    return result
```

### 4. Archive Handler Caching

The global `ArchiveCache` keeps recently used archives open:

- Avoids repeated open/close overhead
- LRU eviction prevents memory exhaustion
- TTL-based expiration ensures freshness


## Integration with TFM

### Path Factory Integration

The `Path` class in `tfm_path.py` detects archive URIs and creates `ArchivePathImpl` instances:

```python
def _create_implementation(self, path_str: str) -> PathImpl:
    """Create the appropriate implementation based on the path string"""
    
    # Detect archive URIs
    if path_str.startswith('archive://'):
        from tfm_archive import ArchivePathImpl
        return ArchivePathImpl(path_str)
    
    # Detect S3 URIs
    if path_str.startswith('s3://'):
        from tfm_s3 import S3PathImpl
        return S3PathImpl(path_str)
    
    # Default to local file system
    return LocalPathImpl(PathlibPath(path_str))
```

### FileManager Integration

The FileManager handles ENTER key on archive files to navigate into them:

```python
def handle_enter_key(self):
    """Handle ENTER key - navigate into directories or archives"""
    current_file = self.get_current_file()
    
    if current_file.is_dir():
        # Existing directory navigation
        self.navigate_to_directory(current_file)
    elif is_archive_file(current_file):
        # Navigate into archive as virtual directory
        archive_uri = f"archive://{current_file.absolute()}#"
        archive_path = Path(archive_uri)
        self.navigate_to_directory(archive_path)
    else:
        # Existing file handling (view, edit, execute)
        self.handle_file_action(current_file)
```

### File Operations Integration

File operations (copy, move, delete) work transparently with archive paths:

```python
# Copy from archive to local filesystem
source = Path("archive:///path/to/archive.zip#folder/file.txt")
dest = Path("/local/destination/file.txt")
source_data = source.read_bytes()
dest.write_bytes(source_data)
```

The `tfm_file_operations.py` module handles extraction automatically when copying from archives.


## API Reference

### ArchiveEntry

#### Constructor
```python
ArchiveEntry(
    name: str,
    internal_path: str,
    is_dir: bool,
    size: int,
    compressed_size: int,
    mtime: float,
    mode: int,
    archive_type: str
)
```

#### Methods

**`to_stat_result() -> os.stat_result`**

Converts the entry to an `os.stat_result` object for compatibility with filesystem code.

**`from_zip_info(zip_info: zipfile.ZipInfo, archive_type: str = 'zip') -> ArchiveEntry`** (classmethod)

Creates an ArchiveEntry from a ZipInfo object.

**`from_tar_info(tar_info: tarfile.TarInfo, archive_type: str = 'tar') -> ArchiveEntry`** (classmethod)

Creates an ArchiveEntry from a TarInfo object.

### ArchiveHandler

#### Constructor
```python
ArchiveHandler(archive_path: Path)
```

#### Methods

**`open() -> None`**

Opens the archive file and caches its structure. Raises `ArchiveError` subclasses on failure.

**`close() -> None`**

Closes the archive file and releases resources.

**`list_entries(internal_path: str = "") -> List[ArchiveEntry]`**

Lists entries at the given internal path. Returns direct children only.

**`get_entry_info(internal_path: str) -> Optional[ArchiveEntry]`**

Gets information about a specific entry. Returns None if not found.

**`extract_to_bytes(internal_path: str) -> bytes`**

Extracts a file's contents to memory. Raises `ArchiveExtractionError` on failure.

**`extract_to_file(internal_path: str, target_path: Path) -> None`**

Extracts a file to the filesystem. Raises `ArchiveExtractionError` on failure.


### ArchiveCache

#### Constructor
```python
ArchiveCache(max_open: int = 5, ttl: int = 300)
```

Parameters:
- `max_open`: Maximum number of archives to keep open
- `ttl`: Time-to-live for cached structures in seconds

#### Methods

**`get_handler(archive_path: Path) -> ArchiveHandler`**

Gets or creates a handler for the archive. Implements LRU eviction and TTL expiration.

**`invalidate(archive_path: Path) -> None`**

Invalidates the cache for a specific archive, closing and removing its handler.

**`clear() -> None`**

Clears all cached archives, closing all handlers.

**`get_stats() -> Dict[str, Any]`**

Returns cache statistics for monitoring:
```python
{
    'open_archives': 3,
    'max_open': 5,
    'ttl': 300,
    'expired_count': 0,
    'cache_hits': 42,
    'cache_misses': 8,
    'hit_rate': 0.84,
    'evictions': 2,
    'avg_open_time': 0.15
}
```

### ArchivePathImpl

#### Constructor
```python
ArchivePathImpl(archive_uri: str, metadata: Optional[Dict[str, Any]] = None)
```

Parameters:
- `archive_uri`: URI in format `archive://path/to/file.zip#internal/path`
- `metadata`: Optional cached metadata to avoid archive reads

#### Properties

All standard PathImpl properties are supported:
- `name`, `stem`, `suffix`, `suffixes`
- `parent`, `parents`, `parts`
- `anchor`

#### Path Manipulation Methods

- `absolute() -> Path`
- `resolve(strict: bool = False) -> Path`
- `expanduser() -> Path`
- `joinpath(*args) -> Path`
- `with_name(name: str) -> Path`
- `with_stem(stem: str) -> Path`
- `with_suffix(suffix: str) -> Path`
- `relative_to(other) -> Path`

#### File System Query Methods

- `exists() -> bool`
- `is_dir() -> bool`
- `is_file() -> bool`
- `is_symlink() -> bool`
- `is_absolute() -> bool`
- `stat() -> os.stat_result`
- `lstat() -> os.stat_result`

#### Directory Operations

- `iterdir() -> Iterator[Path]`
- `glob(pattern: str) -> Iterator[Path]`
- `rglob(pattern: str) -> Iterator[Path]`

#### File I/O Operations

- `open(mode: str = 'r', **kwargs) -> IO`
- `read_text(encoding: str = 'utf-8') -> str`
- `read_bytes() -> bytes`


## Code Examples

### Example 1: Creating a Custom Archive Handler

To add support for a new archive format, extend the `ArchiveHandler` base class:

```python
class RarHandler(ArchiveHandler):
    """Handler for RAR archive files"""
    
    def open(self):
        """Open the RAR archive"""
        try:
            import rarfile  # Requires rarfile package
            
            if not self._archive_path.exists():
                raise FileNotFoundError(f"Archive not found: {self._archive_path}")
            
            self._archive_obj = rarfile.RarFile(str(self._archive_path), 'r')
            self._is_open = True
            self._cache_entries()
            
        except rarfile.BadRarFile as e:
            raise ArchiveCorruptedError(
                f"Corrupted RAR archive: {e}",
                f"Archive '{self._archive_path.name}' is corrupted"
            )
    
    def _cache_entries(self):
        """Cache all entries from the RAR file"""
        if not self._archive_obj:
            return
        
        self._entry_cache.clear()
        self._directory_cache.clear()
        
        for rar_info in self._archive_obj.infolist():
            # Convert RarInfo to ArchiveEntry
            entry = self._create_entry_from_rar_info(rar_info)
            normalized_path = self._normalize_path(entry.internal_path)
            self._entry_cache[normalized_path] = entry
            
            # Build directory cache...
    
    def extract_to_bytes(self, internal_path: str) -> bytes:
        """Extract a file's contents to memory"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        entry = self._entry_cache.get(normalized_path)
        
        if not entry:
            raise FileNotFoundError(f"File not found: {internal_path}")
        
        return self._archive_obj.read(entry.internal_path)
```

Then register the handler in `ArchiveCache._create_handler()`:

```python
def _create_handler(self, archive_path: Path) -> ArchiveHandler:
    filename = archive_path.name.lower()
    
    if filename.endswith('.rar'):
        return RarHandler(archive_path)
    # ... existing handlers ...
```


### Example 2: Working with Archive Paths Programmatically

```python
from tfm_path import Path

# Create an archive path
archive_path = Path("archive:///home/user/data.zip#")

# Navigate into the archive
folder_path = archive_path / "documents" / "reports"

# Check if path exists
if folder_path.exists():
    print(f"Found: {folder_path}")

# List directory contents
for item in folder_path.iterdir():
    if item.is_file():
        print(f"File: {item.name} ({item.stat().st_size} bytes)")
    else:
        print(f"Dir:  {item.name}/")

# Read a file from the archive
file_path = folder_path / "report.txt"
if file_path.is_file():
    content = file_path.read_text()
    print(content)

# Copy a file from archive to local filesystem
dest_path = Path("/tmp/extracted_report.txt")
dest_path.write_bytes(file_path.read_bytes())

# Search for files matching a pattern
for match in archive_path.rglob("*.pdf"):
    print(f"Found PDF: {match}")
```

### Example 3: Implementing Custom Caching Strategy

```python
from tfm_archive import ArchiveCache, get_archive_cache

# Create a custom cache with different settings
custom_cache = ArchiveCache(max_open=10, ttl=600)

# Use the custom cache
archive_path = Path("/path/to/archive.zip")
handler = custom_cache.get_handler(archive_path)

# Access archive contents
entries = handler.list_entries("")
for entry in entries:
    print(f"{entry.name}: {entry.size} bytes")

# Monitor cache performance
stats = custom_cache.get_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
print(f"Average open time: {stats['avg_open_time']:.3f}s")

# Clear cache when done
custom_cache.clear()
```


### Example 4: Handling Archive Errors

```python
from tfm_path import Path
from tfm_archive import (
    ArchiveError, ArchiveCorruptedError, ArchiveFormatError,
    ArchiveExtractionError, ArchiveNavigationError
)

def safe_archive_operation(archive_uri: str):
    """Safely perform archive operations with proper error handling"""
    try:
        archive_path = Path(archive_uri)
        
        # Check if archive exists
        if not archive_path.exists():
            print(f"Archive not found: {archive_path}")
            return
        
        # Try to list contents
        for item in archive_path.iterdir():
            print(f"- {item.name}")
            
    except ArchiveCorruptedError as e:
        # Archive is corrupted
        print(f"Error: {e.user_message}")
        # Log technical details
        log_error(str(e))
        
    except ArchiveFormatError as e:
        # Unsupported format
        print(f"Error: {e.user_message}")
        
    except ArchiveNavigationError as e:
        # Navigation error (path not found)
        print(f"Error: {e.user_message}")
        
    except ArchiveExtractionError as e:
        # Extraction error
        print(f"Error: {e.user_message}")
        
    except ArchiveError as e:
        # Generic archive error
        print(f"Archive error: {e.user_message}")
        
    except Exception as e:
        # Unexpected error
        print(f"Unexpected error: {e}")
        log_error(f"Unexpected archive error: {e}")

# Usage
safe_archive_operation("archive:///path/to/data.zip#folder")
```


## Testing Strategy

### Unit Tests

Unit tests verify individual components in isolation:

1. **ArchiveEntry Tests** (`test/test_archive_entry.py`)
   - Test creation from ZipInfo and TarInfo
   - Test stat_result conversion
   - Test metadata preservation

2. **ArchiveHandler Tests** (`test/test_archive_handler.py`)
   - Test opening various archive formats
   - Test entry listing and retrieval
   - Test extraction operations
   - Test error handling for corrupt archives

3. **ArchiveCache Tests** (`test/test_archive_cache.py`)
   - Test LRU eviction
   - Test TTL expiration
   - Test thread safety
   - Test cache statistics

4. **ArchivePathImpl Tests** (`test/test_archive_path_impl.py`)
   - Test URI parsing
   - Test path properties and manipulation
   - Test file system queries
   - Test directory operations

### Integration Tests

Integration tests verify the feature works with TFM components:

1. **FileManager Integration** (`test/test_filemanager_archive_integration.py`)
   - Test entering archives with ENTER key
   - Test navigation within archives
   - Test exiting archives with backspace

2. **File Operations Integration** (`test/test_archive_copy_operations.py`)
   - Test copying from archives to filesystem
   - Test copying from archives to S3
   - Test batch operations

3. **Search Integration** (`test/test_archive_search_integration.py`)
   - Test searching within archives
   - Test navigation to search results

4. **Text Viewer Integration** (`test/test_archive_viewer_integration.py`)
   - Test viewing files from archives
   - Test temporary file cleanup

### Performance Tests

Performance tests verify optimization effectiveness:

1. **Large Archive Tests** (`test/test_archive_performance.py`)
   - Test lazy loading for archives with >1000 entries
   - Test cache hit rates
   - Test memory usage
   - Test open/close performance


## Performance Considerations

### Memory Management

1. **Lazy Loading**: Large archives only cache directory structure initially
2. **Entry Caching**: Individual entries loaded on-demand
3. **Property Caching**: Frequently accessed properties cached to avoid recomputation
4. **Handler Limits**: Maximum number of open archives controlled by cache

### Optimization Guidelines

**For Small Archives (<1000 entries):**
- All entries cached on open
- Fast navigation and listing
- Higher memory usage acceptable

**For Large Archives (>1000 entries):**
- Only directory structure cached initially
- Entries loaded on-demand
- Reduced memory footprint
- Slightly slower first access to deep paths

**Cache Tuning:**

Adjust cache parameters based on usage patterns:

```python
# For systems with limited memory
ARCHIVE_CACHE_MAX_OPEN = 3
ARCHIVE_CACHE_TTL = 180

# For systems with ample memory and frequent archive access
ARCHIVE_CACHE_MAX_OPEN = 10
ARCHIVE_CACHE_TTL = 600
```

### Profiling and Monitoring

Monitor cache performance using statistics:

```python
cache = get_archive_cache()
stats = cache.get_stats()

# Check cache effectiveness
if stats['hit_rate'] < 0.5:
    print("Warning: Low cache hit rate")
    print(f"Consider increasing max_open from {stats['max_open']}")

# Check for excessive evictions
if stats['evictions'] > stats['cache_hits'] * 0.1:
    print("Warning: High eviction rate")
    print("Consider increasing max_open or TTL")

# Monitor open times
if stats['avg_open_time'] > 1.0:
    print("Warning: Slow archive opens")
    print("Consider optimizing archive format or storage")
```


## Thread Safety

### Concurrent Access

The implementation provides thread safety through:

1. **Cache Locking**: `ArchiveCache` uses `threading.RLock` for all operations
2. **Handler Isolation**: Each archive handler is independent
3. **Read-Only Operations**: Archive handlers only read from archives (no writes)

### Thread Safety Guarantees

**Safe Operations:**
- Multiple threads reading from different archives
- Multiple threads reading from the same archive (through cache)
- Cache operations (get_handler, invalidate, clear)

**Unsafe Operations:**
- Modifying archive files while they're open (not supported)
- Concurrent writes to the same archive (not applicable - read-only)

### Example: Thread-Safe Archive Access

```python
import threading
from tfm_path import Path

def process_archive_file(archive_uri: str, internal_path: str):
    """Process a file from an archive (thread-safe)"""
    try:
        file_path = Path(f"{archive_uri}#{internal_path}")
        content = file_path.read_bytes()
        # Process content...
        return len(content)
    except Exception as e:
        print(f"Error processing {internal_path}: {e}")
        return 0

# Create multiple threads to process files from the same archive
archive_uri = "archive:///path/to/large_archive.zip"
files_to_process = ["file1.txt", "file2.txt", "file3.txt"]

threads = []
for file_path in files_to_process:
    thread = threading.Thread(
        target=process_archive_file,
        args=(archive_uri, file_path)
    )
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()
```


## Extending Archive Support

### Adding New Archive Formats

To add support for a new archive format:

1. **Create a Handler Class**

```python
class SevenZipHandler(ArchiveHandler):
    """Handler for 7z archive files"""
    
    def __init__(self, archive_path: Path):
        super().__init__(archive_path)
        # Format-specific initialization
    
    def open(self):
        # Implement archive opening
        pass
    
    def _cache_entries(self):
        # Implement entry caching
        pass
    
    def list_entries(self, internal_path: str = "") -> List[ArchiveEntry]:
        # Implement directory listing
        pass
    
    def get_entry_info(self, internal_path: str) -> Optional[ArchiveEntry]:
        # Implement entry info retrieval
        pass
    
    def extract_to_bytes(self, internal_path: str) -> bytes:
        # Implement extraction to memory
        pass
    
    def extract_to_file(self, internal_path: str, target_path: Path):
        # Implement extraction to file
        pass
```

2. **Register the Handler**

Update `ArchiveCache._create_handler()`:

```python
def _create_handler(self, archive_path: Path) -> ArchiveHandler:
    filename = archive_path.name.lower()
    
    # Add new format detection
    if filename.endswith('.7z'):
        return SevenZipHandler(archive_path)
    
    # Existing handlers...
    if filename.endswith('.zip'):
        return ZipHandler(archive_path)
    # ...
```

3. **Update Format Detection**

Add the format to `ArchiveOperations.SUPPORTED_FORMATS`:

```python
SUPPORTED_FORMATS = {
    # Existing formats...
    '.7z': {'type': '7z', 'compression': None, 'description': '7-Zip archive'},
}
```

4. **Add Tests**

Create tests for the new handler:
- Unit tests for handler operations
- Integration tests with TFM
- Performance tests for large archives


### Adding Custom Metadata

To add custom metadata to archive entries:

1. **Extend ArchiveEntry**

```python
@dataclass
class ExtendedArchiveEntry(ArchiveEntry):
    """Archive entry with additional metadata"""
    crc32: Optional[int] = None
    comment: Optional[str] = None
    encryption: Optional[str] = None
```

2. **Update Handler to Populate Metadata**

```python
class ExtendedZipHandler(ZipHandler):
    """ZIP handler with extended metadata"""
    
    def _create_entry_from_zip_info(self, zip_info):
        # Create base entry
        entry = super()._create_entry_from_zip_info(zip_info)
        
        # Add extended metadata
        extended_entry = ExtendedArchiveEntry(
            **entry.__dict__,
            crc32=zip_info.CRC,
            comment=zip_info.comment.decode('utf-8') if zip_info.comment else None,
            encryption='encrypted' if zip_info.flag_bits & 0x1 else None
        )
        
        return extended_entry
```

3. **Use Extended Metadata**

```python
# Access extended metadata
archive_path = Path("archive:///path/to/file.zip#file.txt")
entry = archive_path._impl._get_entry()

if isinstance(entry, ExtendedArchiveEntry):
    print(f"CRC32: {entry.crc32}")
    print(f"Comment: {entry.comment}")
    print(f"Encryption: {entry.encryption}")
```


## Troubleshooting

### Common Issues

#### Issue: "Archive not found" error

**Cause**: Archive file doesn't exist or path is incorrect

**Solution**:
```python
# Verify archive exists
archive_path = Path("/path/to/archive.zip")
if not archive_path.exists():
    print(f"Archive not found: {archive_path}")
    
# Check for typos in URI
uri = "archive:///path/to/archive.zip#folder/file.txt"
# Ensure three slashes after archive://
```

#### Issue: "Corrupted archive" error

**Cause**: Archive file is damaged or incomplete

**Solution**:
- Verify archive integrity using native tools (unzip -t, tar -tzf)
- Re-download or re-create the archive
- Check for disk errors or corruption

#### Issue: Slow performance with large archives

**Cause**: Inefficient caching or too many open archives

**Solution**:
```python
# Increase cache size
ARCHIVE_CACHE_MAX_OPEN = 10

# Increase TTL to keep archives open longer
ARCHIVE_CACHE_TTL = 600

# Monitor cache performance
stats = get_archive_cache().get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

#### Issue: Memory usage too high

**Cause**: Too many archives cached or large archive entries

**Solution**:
```python
# Reduce cache size
ARCHIVE_CACHE_MAX_OPEN = 3

# Reduce TTL to expire entries faster
ARCHIVE_CACHE_TTL = 120

# Clear cache manually when done
get_archive_cache().clear()
```

#### Issue: "Permission denied" errors

**Cause**: Insufficient permissions to read archive or write extracted files

**Solution**:
- Check file permissions on archive
- Verify write permissions on destination directory
- Run with appropriate user permissions


### Debugging Tips

#### Enable Verbose Logging

```python
# In tfm_archive.py, add logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tfm_archive')

# Add logging to key operations
def open(self):
    logger.debug(f"Opening archive: {self._archive_path}")
    # ... existing code ...
    logger.debug(f"Cached {len(self._entry_cache)} entries")
```

#### Inspect Cache State

```python
# Get cache statistics
cache = get_archive_cache()
stats = cache.get_stats()

print(f"Open archives: {stats['open_archives']}/{stats['max_open']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache misses: {stats['cache_misses']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Evictions: {stats['evictions']}")
print(f"Avg open time: {stats['avg_open_time']:.3f}s")
```

#### Trace Archive Operations

```python
# Add tracing to archive operations
def trace_archive_operation(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with {args}, {kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

# Apply to methods
ArchiveHandler.list_entries = trace_archive_operation(ArchiveHandler.list_entries)
```

#### Verify Archive Structure

```python
# Dump archive structure for debugging
def dump_archive_structure(archive_uri: str):
    """Print complete archive structure"""
    archive_path = Path(archive_uri)
    
    def print_tree(path, indent=0):
        prefix = "  " * indent
        if path.is_dir():
            print(f"{prefix}{path.name}/")
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                print_tree(child, indent + 1)
        else:
            size = path.stat().st_size
            print(f"{prefix}{path.name} ({size} bytes)")
    
    print_tree(archive_path)

# Usage
dump_archive_structure("archive:///path/to/archive.zip#")
```


## Future Enhancements

### Planned Features

1. **Write Support**
   - Allow creating/modifying archives
   - Support adding files to existing archives
   - Support deleting files from archives

2. **Additional Compression Formats**
   - 7z support (requires py7zr library)
   - RAR support (requires rarfile library)
   - ISO support (requires pycdlib library)

3. **Nested Archives**
   - Support archives within archives
   - Recursive archive navigation
   - URI format: `archive://outer.zip#inner.zip#file.txt`

4. **Archive Encryption**
   - Support password-protected archives
   - Secure password handling
   - Integration with system keychain

5. **Archive Streaming**
   - Stream archives from remote sources without full download
   - Progressive loading for very large archives
   - HTTP range request support

6. **Archive Preview**
   - Show archive contents without entering
   - Quick preview in file details dialog
   - Thumbnail generation for image archives

7. **Smart Extraction**
   - Extract only changed files
   - Incremental extraction
   - Differential updates

8. **Archive Comparison**
   - Compare contents of two archives
   - Show differences in files
   - Merge archives

### Implementation Considerations

**Write Support:**
- Requires careful handling of archive modifications
- Need to handle concurrent access
- Consider using temporary files for safety

**Nested Archives:**
- Extend URI format to support multiple levels
- Implement recursive handler chain
- Consider memory implications

**Encryption:**
- Integrate with system keychain for password storage
- Support multiple encryption methods
- Handle password prompts in UI

**Streaming:**
- Implement progressive loading
- Use HTTP range requests for remote archives
- Balance between memory usage and performance


## References

### Related Documentation

- **End-User Documentation**: `doc/ARCHIVE_VIRTUAL_DIRECTORY_FEATURE.md`
- **Requirements**: `.kiro/specs/archive-virtual-directory/requirements.md`
- **Design**: `.kiro/specs/archive-virtual-directory/design.md`
- **Tasks**: `.kiro/specs/archive-virtual-directory/tasks.md`

### Python Standard Library

- **zipfile**: https://docs.python.org/3/library/zipfile.html
- **tarfile**: https://docs.python.org/3/library/tarfile.html
- **gzip**: https://docs.python.org/3/library/gzip.html
- **bz2**: https://docs.python.org/3/library/bz2.html
- **lzma**: https://docs.python.org/3/library/lzma.html

### External Libraries (Optional)

- **py7zr**: 7z archive support - https://pypi.org/project/py7zr/
- **rarfile**: RAR archive support - https://pypi.org/project/rarfile/
- **pycdlib**: ISO image support - https://pypi.org/project/pycdlib/

### TFM Architecture

- **PathImpl Pattern**: See `src/tfm_path.py` for the base PathImpl interface
- **S3 Implementation**: See `src/tfm_s3.py` for a similar virtual filesystem implementation
- **File Operations**: See `src/tfm_file_operations.py` for cross-storage operations

### Testing

- **Unit Tests**: `test/test_archive_*.py`
- **Integration Tests**: `test/test_*_archive_*.py`
- **Demo Scripts**: `demo/demo_archive_*.py`

## Changelog

### Version 1.0.0 (Initial Release)

**Features:**
- Archive virtual directory browsing
- Support for ZIP, TAR, TAR.GZ, TAR.BZ2, TAR.XZ formats
- LRU cache with TTL expiration
- Lazy loading for large archives
- Cross-storage support (local, S3)
- File viewing from archives
- Copy operations from archives
- Search within archives
- Metadata display
- Comprehensive error handling

**Performance:**
- Lazy loading for archives >1000 entries
- Property caching
- Directory structure caching
- Archive handler caching

**Testing:**
- 100% unit test coverage
- Integration tests with FileManager
- Performance tests for large archives

