# Design Document

## Overview

This design document describes the implementation of archive file support for TFM (TUI File Manager). The feature enables users to browse archive contents as virtual directories without extracting files to disk. The implementation follows TFM's existing PathImpl pattern used for S3 support, creating an ArchivePathImpl that integrates seamlessly with the existing file manager infrastructure.

The design leverages Python's standard library modules (`zipfile`, `tarfile`) for archive handling, ensuring no additional dependencies are required. Archive contents are presented as virtual directories that can be navigated, searched, and operated on using TFM's existing UI and operations.

## Architecture

### High-Level Architecture

The archive support follows TFM's established pattern for virtual filesystems:

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

### Archive Path Format

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

## Components and Interfaces

### 1. ArchivePathImpl Class

The core implementation that provides archive access through the PathImpl interface.

```python
class ArchivePathImpl(PathImpl):
    """Archive file implementation of PathImpl"""
    
    def __init__(self, archive_uri: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize with archive URI and optional metadata
        
        Args:
            archive_uri: URI in format archive://path/to/file.zip#internal/path
            metadata: Optional cached metadata to avoid archive reads
        """
        
    def _parse_uri(self):
        """Parse archive URI into archive path and internal path components"""
        
    def _get_archive_handler(self) -> 'ArchiveHandler':
        """Get or create cached archive handler for this archive file"""
        
    def _normalize_internal_path(self, path: str) -> str:
        """Normalize internal archive paths (handle / vs no /)"""
```

### 2. ArchiveHandler Class

Manages archive file access and caching of archive contents.

```python
class ArchiveHandler:
    """Handles reading and caching of archive contents"""
    
    def __init__(self, archive_path: Path):
        """Initialize handler for specific archive file"""
        
    def open(self):
        """Open the archive file and cache its structure"""
        
    def close(self):
        """Close the archive file"""
        
    def list_entries(self, internal_path: str = "") -> List[ArchiveEntry]:
        """List entries at the given internal path"""
        
    def get_entry_info(self, internal_path: str) -> Optional[ArchiveEntry]:
        """Get information about a specific entry"""
        
    def extract_to_bytes(self, internal_path: str) -> bytes:
        """Extract a file's contents to memory"""
        
    def extract_to_file(self, internal_path: str, target_path: Path):
        """Extract a file to the filesystem"""
```

### 3. ArchiveEntry Data Class

Represents a single entry within an archive.

```python
@dataclass
class ArchiveEntry:
    """Represents an entry in an archive"""
    name: str                    # Entry name (filename or dirname)
    internal_path: str           # Full path within archive
    is_dir: bool                 # Whether this is a directory
    size: int                    # Uncompressed size in bytes
    compressed_size: int         # Compressed size in bytes
    mtime: float                 # Modification time as timestamp
    mode: int                    # File permissions
    archive_type: str            # 'zip', 'tar', 'tar.gz', etc.
```

### 4. ArchiveCache Class

Caches opened archives and their directory structures to improve performance.

```python
class ArchiveCache:
    """Cache for opened archives and their structures"""
    
    def __init__(self, max_open: int = 5, ttl: int = 300):
        """
        Initialize cache
        
        Args:
            max_open: Maximum number of archives to keep open
            ttl: Time-to-live for cached structures in seconds
        """
        
    def get_handler(self, archive_path: Path) -> ArchiveHandler:
        """Get or create handler for archive"""
        
    def invalidate(self, archive_path: Path):
        """Invalidate cache for specific archive"""
        
    def clear(self):
        """Clear all cached archives"""
```

### 5. Archive Format Detection

```python
def detect_archive_format(path: Path) -> Optional[str]:
    """
    Detect archive format from file extension and magic bytes
    
    Returns:
        Archive type string ('zip', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz') or None
    """
    
def is_archive_file(path: Path) -> bool:
    """Check if a path represents a supported archive file"""
```

### 6. Integration with Path Factory

Modify the Path class's `_create_implementation` method to detect archive URIs:

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

### 7. FileManager Integration

Modify the FileManager class to handle ENTER key on archive files:

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

## Data Models

### ArchiveEntry

```python
@dataclass
class ArchiveEntry:
    """Represents an entry in an archive"""
    name: str                    # Entry name
    internal_path: str           # Full path within archive  
    is_dir: bool                 # Directory flag
    size: int                    # Uncompressed size
    compressed_size: int         # Compressed size
    mtime: float                 # Modification timestamp
    mode: int                    # File permissions
    archive_type: str            # Archive format
```

### Archive Handler State

```python
class ArchiveHandler:
    _archive_path: Path          # Path to archive file
    _archive_obj: Any            # zipfile.ZipFile or tarfile.TarFile
    _entry_cache: Dict[str, ArchiveEntry]  # Cached entry information
    _directory_cache: Dict[str, List[str]]  # Cached directory listings
    _is_open: bool               # Whether archive is currently open
    _last_access: float          # Timestamp of last access
```

### Archive Cache State

```python
class ArchiveCache:
    _handlers: Dict[str, ArchiveHandler]  # Path -> Handler mapping
    _access_times: Dict[str, float]       # Path -> Last access time
    _max_open: int                        # Maximum open archives
    _ttl: int                             # Cache TTL in seconds
    _lock: threading.RLock                # Thread safety
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

Before defining the correctness properties, let's identify and eliminate redundancy:

**Redundant Properties Identified:**
- Properties 2.2 and 2.3 (navigation within archives) can be combined into a single comprehensive navigation property
- Properties 6.2 and 6.4 (path display formatting) overlap and can be consolidated
- Properties 5.1, 5.3, and 5.4 (search behavior) can be combined into a comprehensive search property

**Consolidated Properties:**
After reflection, we'll define properties that provide unique validation value without redundancy.

### Correctness Properties

Property 1: Archive entry round trip
*For any* supported archive file, opening it and listing its contents should produce entries that match the actual archive structure
**Validates: Requirements 1.1, 1.2, 1.3**

Property 2: Archive navigation preserves history
*For any* archive file, entering the archive and then navigating back should return to the original filesystem directory
**Validates: Requirements 1.4**

Property 3: Corrupt archive handling
*For any* corrupted or invalid archive file, attempting to open it should display an error and leave the current directory unchanged
**Validates: Requirements 1.5, 7.1, 7.2**

Property 4: Archive internal navigation consistency
*For any* directory within an archive, navigating into it and then back should return to the parent location within the archive
**Validates: Requirements 2.2, 2.3**

Property 5: Archive path display completeness
*For any* location within an archive, the displayed path should contain both the archive filename and the internal path
**Validates: Requirements 2.5, 6.2**

Property 6: File extraction preserves content
*For any* file within an archive, extracting it to a target location should produce a file with identical contents
**Validates: Requirements 3.1**

Property 7: Metadata preservation during extraction
*For any* file extracted from an archive, the extracted file's modification time and permissions should match the archive entry's metadata where the target filesystem supports it
**Validates: Requirements 3.2**

Property 8: Cross-storage copy correctness
*For any* file in an archive, copying it to S3 should result in an S3 object with identical contents
**Validates: Requirements 3.3**

Property 9: Recursive directory extraction completeness
*For any* directory within an archive, extracting it should produce all contained files and subdirectories with correct structure
**Validates: Requirements 3.4**

Property 10: Archive file viewing round trip
*For any* text file within an archive, viewing it should display the same contents as extracting and reading the file
**Validates: Requirements 4.1**

Property 11: Temporary file cleanup
*For any* file viewed from an archive, after closing the viewer, no temporary files should remain on disk
**Validates: Requirements 4.3**

Property 12: Archive search scope correctness
*For any* search pattern and archive location, search results should only include files within that archive location that match the pattern
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

Property 13: Directory indicator consistency
*For any* archive entry that is a directory, it should be displayed with the same directory indicators as filesystem directories
**Validates: Requirements 6.4**

Property 14: Uncompressed size display
*For any* file entry in an archive, the displayed size should be the uncompressed size, not the compressed size
**Validates: Requirements 6.5**

Property 15: Batch operation completeness
*For any* set of selected files in an archive, a batch copy operation should extract all selected files to the target location
**Validates: Requirements 8.2**

Property 16: Metadata display completeness
*For any* archive entry, requesting file details should display name, size, modification time, and permissions
**Validates: Requirements 8.3**

Property 17: Sort order consistency
*For any* sort mode, archive entries should be sorted using the same criteria as filesystem entries
**Validates: Requirements 8.4**

## Error Handling

### Error Categories

1. **Archive Access Errors**
   - Corrupted archive files
   - Unsupported archive formats
   - Permission denied reading archive
   - Archive file not found

2. **Extraction Errors**
   - Insufficient disk space
   - Permission denied writing to target
   - Invalid internal path
   - Extraction failure (corrupt entry)

3. **Navigation Errors**
   - Invalid internal path
   - Entry not found in archive
   - Archive closed unexpectedly

4. **Resource Errors**
   - Too many open archives
   - Memory exhaustion
   - Temporary directory unavailable

### Error Handling Strategy

```python
class ArchiveError(Exception):
    """Base exception for archive operations"""
    pass

class ArchiveFormatError(ArchiveError):
    """Unsupported or invalid archive format"""
    pass

class ArchiveCorruptedError(ArchiveError):
    """Archive file is corrupted"""
    pass

class ArchiveExtractionError(ArchiveError):
    """Error during file extraction"""
    pass

class ArchiveNavigationError(ArchiveError):
    """Error navigating within archive"""
    pass
```

### Error Recovery

- **Archive access failures**: Display error message, remain in current directory
- **Extraction failures**: Display error with specific file/reason, continue with other files
- **Navigation failures**: Return to archive root or exit archive
- **Resource exhaustion**: Close least recently used archives, retry operation

### Logging

All archive operations should log:
- Archive file path
- Operation type (open, extract, list, etc.)
- Success/failure status
- Error details if failed
- Performance metrics (time, size)

## Testing Strategy

### Unit Testing

Unit tests will verify specific behaviors and edge cases:

1. **Archive Format Detection**
   - Test detection of each supported format by extension
   - Test detection by magic bytes
   - Test rejection of unsupported formats

2. **Path Parsing**
   - Test parsing of archive URIs
   - Test handling of special characters in paths
   - Test normalization of internal paths

3. **Entry Listing**
   - Test listing root directory
   - Test listing nested directories
   - Test empty directories
   - Test archives with no directory entries

4. **Metadata Extraction**
   - Test size calculation
   - Test timestamp conversion
   - Test permission extraction

5. **Error Handling**
   - Test corrupt archive handling
   - Test missing file handling
   - Test permission errors

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using the Hypothesis library for Python:

**Configuration**: Each property test will run a minimum of 100 iterations to ensure thorough coverage.

**Test Tagging**: Each property-based test will be tagged with a comment explicitly referencing the correctness property from this design document using the format: `# Feature: archive-virtual-directory, Property {number}: {property_text}`

**Property Test Implementations**:

1. **Property 1: Archive entry round trip**
   - Generate random archive files with random contents
   - Open each archive and list contents
   - Verify listed entries match actual archive structure
   - Tag: `# Feature: archive-virtual-directory, Property 1: Archive entry round trip`

2. **Property 2: Archive navigation preserves history**
   - Generate random archive files
   - Enter each archive and navigate back
   - Verify current directory matches original
   - Tag: `# Feature: archive-virtual-directory, Property 2: Archive navigation preserves history`

3. **Property 3: Corrupt archive handling**
   - Generate corrupted archive files
   - Attempt to open each
   - Verify error is displayed and directory unchanged
   - Tag: `# Feature: archive-virtual-directory, Property 3: Corrupt archive handling`

4. **Property 4: Archive internal navigation consistency**
   - Generate archives with nested directories
   - Navigate into random directories and back
   - Verify return to correct parent location
   - Tag: `# Feature: archive-virtual-directory, Property 4: Archive internal navigation consistency`

5. **Property 5: Archive path display completeness**
   - Generate archives and navigate to random locations
   - Check path display for each location
   - Verify both archive name and internal path are shown
   - Tag: `# Feature: archive-virtual-directory, Property 5: Archive path display completeness`

6. **Property 6: File extraction preserves content**
   - Generate archives with random file contents
   - Extract random files
   - Verify extracted contents match original
   - Tag: `# Feature: archive-virtual-directory, Property 6: File extraction preserves content`

7. **Property 7: Metadata preservation during extraction**
   - Generate archives with files having specific metadata
   - Extract files and check metadata
   - Verify mtime and permissions match
   - Tag: `# Feature: archive-virtual-directory, Property 7: Metadata preservation during extraction`

8. **Property 8: Cross-storage copy correctness**
   - Generate archives with random files
   - Copy files to S3
   - Verify S3 objects have identical contents
   - Tag: `# Feature: archive-virtual-directory, Property 8: Cross-storage copy correctness`

9. **Property 9: Recursive directory extraction completeness**
   - Generate archives with nested directory structures
   - Extract random directories
   - Verify all files and subdirectories are extracted
   - Tag: `# Feature: archive-virtual-directory, Property 9: Recursive directory extraction completeness`

10. **Property 10: Archive file viewing round trip**
    - Generate archives with text files
    - View files through viewer
    - Verify displayed content matches file content
    - Tag: `# Feature: archive-virtual-directory, Property 10: Archive file viewing round trip`

11. **Property 11: Temporary file cleanup**
    - View files from archives
    - Close viewer
    - Verify no temporary files remain
    - Tag: `# Feature: archive-virtual-directory, Property 11: Temporary file cleanup`

12. **Property 12: Archive search scope correctness**
    - Generate archives with various files
    - Search with random patterns
    - Verify results only include matching files from archive
    - Tag: `# Feature: archive-virtual-directory, Property 12: Archive search scope correctness`

13. **Property 13: Directory indicator consistency**
    - Generate archives with directories
    - List archive contents
    - Verify directories have same indicators as filesystem dirs
    - Tag: `# Feature: archive-virtual-directory, Property 13: Directory indicator consistency`

14. **Property 14: Uncompressed size display**
    - Generate compressed archives
    - List contents
    - Verify displayed sizes are uncompressed
    - Tag: `# Feature: archive-virtual-directory, Property 14: Uncompressed size display`

15. **Property 15: Batch operation completeness**
    - Generate archives with multiple files
    - Select random subsets of files
    - Batch copy selected files
    - Verify all selected files are extracted
    - Tag: `# Feature: archive-virtual-directory, Property 15: Batch operation completeness`

16. **Property 16: Metadata display completeness**
    - Generate archives with various entries
    - Request details for random entries
    - Verify all metadata fields are displayed
    - Tag: `# Feature: archive-virtual-directory, Property 16: Metadata display completeness`

17. **Property 17: Sort order consistency**
    - Generate archives with various files
    - Apply different sort modes
    - Verify sort order matches filesystem sorting
    - Tag: `# Feature: archive-virtual-directory, Property 17: Sort order consistency`

### Integration Testing

Integration tests will verify the feature works correctly with existing TFM components:

1. **Pane Manager Integration**
   - Test archive browsing in dual-pane mode
   - Test switching between archive and filesystem panes
   - Test cursor history with archives

2. **File Operations Integration**
   - Test copy from archive to filesystem
   - Test copy from archive to S3
   - Test copy from archive to archive
   - Test batch operations on archive files

3. **Text Viewer Integration**
   - Test viewing text files from archives
   - Test viewer with large files from archives
   - Test viewer with various encodings

4. **Search Dialog Integration**
   - Test search within archives
   - Test search results navigation
   - Test search with various patterns

5. **Progress Manager Integration**
   - Test progress display during extraction
   - Test progress for large archives
   - Test cancellation of extraction operations

### Test Data Generation

For property-based testing, we'll need generators for:

1. **Archive Files**: Generate valid archives in various formats with random contents
2. **Directory Structures**: Generate nested directory hierarchies
3. **File Contents**: Generate text and binary file contents
4. **Metadata**: Generate realistic file permissions and timestamps
5. **Corrupt Archives**: Generate intentionally corrupted archives for error testing

## Implementation Notes

### Performance Considerations

1. **Archive Caching**: Keep recently accessed archives open to avoid repeated open/close overhead
2. **Lazy Loading**: Only read archive directory structure when needed
3. **Streaming Extraction**: For large files, stream directly to target without loading into memory
4. **Background Operations**: Extract large files in background threads with progress feedback

### Memory Management

1. **Limit Open Archives**: Close least recently used archives when limit reached
2. **Stream Large Files**: Don't load entire files into memory
3. **Clear Caches**: Provide mechanism to clear archive caches
4. **Temporary File Cleanup**: Ensure temporary files are always cleaned up

### Thread Safety

1. **Archive Handler Locking**: Use locks to prevent concurrent access to same archive
2. **Cache Locking**: Protect cache data structures with locks
3. **Extraction Threads**: Coordinate extraction threads to avoid conflicts

### Compatibility

1. **Python Version**: Require Python 3.7+ for dataclasses and typing support
2. **Standard Library**: Use only standard library modules (zipfile, tarfile)
3. **Platform Support**: Test on Linux, macOS, and Windows
4. **Archive Formats**: Support common formats available in standard library

## Future Enhancements

Potential future improvements not included in initial implementation:

1. **Write Support**: Allow creating/modifying archives
2. **Compression Formats**: Add support for 7z, rar, etc. (requires external libraries)
3. **Archive Preview**: Show archive contents without entering
4. **Smart Extraction**: Extract only changed files
5. **Archive Comparison**: Compare contents of two archives
6. **Nested Archives**: Support archives within archives
7. **Archive Encryption**: Support password-protected archives
8. **Archive Streaming**: Stream archives from remote sources
