# Design Document

## Overview

This design document specifies the architectural changes needed to achieve complete storage-agnostic code in TFM by extending the PathImpl interface with strategic virtual methods. The refactoring eliminates all storage-specific conditionals from UI and dialog code, replacing them with polymorphic method calls that delegate behavior to storage-specific implementations.

### Current Architecture Problems

The current codebase contains storage-specific conditionals scattered across 4 source files:
- `tfm_file_operations.py`: Archive path detection for operation validation
- `tfm_text_viewer.py`: Scheme checks for title formatting
- `tfm_info_dialog.py`: Archive path detection for metadata display
- `tfm_search_dialog.py`: Archive path detection for search strategy and display

These conditionals create tight coupling between UI code and storage implementations, making it difficult to add new storage types and violating the open/closed principle.

### Target Architecture

The refactored architecture achieves complete storage agnosticism by:
1. Adding 7 strategic virtual methods to the PathImpl interface
2. Implementing these methods in all PathImpl subclasses (LocalPathImpl, ArchivePathImpl, S3PathImpl)
3. Refactoring UI/dialog code to use virtual methods instead of conditionals
4. Removing all storage-specific helper methods and imports from UI code

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    UI/Dialog Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Text Viewer  │  │ Info Dialog  │  │Search Dialog │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         │  Storage-agnostic method calls:    │              │
│         │  - get_display_prefix()            │              │
│         │  - get_extended_metadata()         │              │
│         │  - get_search_strategy()           │              │
│         │  - supports_file_editing()         │              │
│         └─────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Path Layer                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Path (Facade)                           │  │
│  │  Delegates to PathImpl:                              │  │
│  │  + get_display_prefix() -> str                       │  │
│  │  + get_display_title() -> str                        │  │
│  │  + get_extended_metadata() -> dict                   │  │
│  │  + get_search_strategy() -> str                      │  │
│  │  + requires_extraction_for_reading() -> bool         │  │
│  │  + supports_streaming_read() -> bool                 │  │
│  │  + should_cache_for_search() -> bool                 │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│         ┌───────────┼───────────┐                          │
│         ▼           ▼           ▼                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│  │  Local   │ │ Archive  │ │   S3     │                  │
│  │PathImpl  │ │PathImpl  │ │PathImpl  │                  │
│  │          │ │          │ │          │                  │
│  │ Each implements virtual methods with                  │
│  │ storage-specific behavior                             │
│  └──────────┘ └──────────┘ └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Sequence Diagram: Display Title in Text Viewer

```
TextViewer          Path           PathImpl (Archive/Local/S3)
    │                │                      │
    │ get_display_   │                      │
    │ prefix()       │                      │
    ├───────────────>│                      │
    │                │ get_display_prefix() │
    │                ├─────────────────────>│
    │                │                      │
    │                │  "ARCHIVE: " / "" /  │
    │                │  "S3: "              │
    │                │<─────────────────────┤
    │  prefix        │                      │
    │<───────────────┤                      │
    │                │                      │
    │ get_display_   │                      │
    │ title()        │                      │
    ├───────────────>│                      │
    │                │ get_display_title()  │
    │                ├─────────────────────>│
    │                │                      │
    │                │  formatted title     │
    │                │<─────────────────────┤
    │  title         │                      │
    │<───────────────┤                      │
    │                │                      │
    │ Display:       │                      │
    │ prefix + title │                      │
    └────────────────┴──────────────────────┘
```

## Components and Interfaces

### PathImpl Abstract Base Class (Extended)

The PathImpl interface will be extended with 7 new abstract methods:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

class PathImpl(ABC):
    # ... existing methods ...
    
    # Display Methods
    @abstractmethod
    def get_display_prefix(self) -> str:
        """Return a prefix for display purposes.
        
        Returns:
            str: Display prefix (e.g., 'ARCHIVE: ', 'S3: ', '')
                 Empty string for local files
                 Non-empty string with trailing space for special storage types
        """
        pass
    
    @abstractmethod
    def get_display_title(self) -> str:
        """Return a formatted title for display in viewers/dialogs.
        
        Returns:
            str: Formatted path string appropriate for display
                 For archives: full URI (archive://path#internal)
                 For local: standard path string
                 For S3: S3 URI
        """
        pass
    
    # Content Reading Strategy Methods
    @abstractmethod
    def requires_extraction_for_reading(self) -> bool:
        """Return True if content must be extracted before reading.
        
        This affects how content is accessed - whether it can be read
        directly or must be extracted to memory/disk first.
        
        Returns:
            bool: True if extraction required (archives, S3)
                  False if direct access possible (local files)
        """
        pass
    
    @abstractmethod
    def supports_streaming_read(self) -> bool:
        """Return True if file can be read line-by-line without full extraction.
        
        This affects memory usage during operations like search.
        
        Returns:
            bool: True if can use open() and iterate (local files)
                  False if must read_text() entire content (archives, S3)
        """
        pass
    
    @abstractmethod
    def get_search_strategy(self) -> str:
        """Return recommended search strategy.
        
        Returns:
            str: One of:
                 'streaming' - Read line by line (local files)
                 'extracted' - Must extract entire content (archives)
                 'buffered' - Download to buffer (S3)
        """
        pass
    
    @abstractmethod
    def should_cache_for_search(self) -> bool:
        """Return True if content should be cached during search operations.
        
        Returns:
            bool: True if caching recommended (archives, S3)
                  False if direct access is efficient (local files)
        """
        pass
    
    # Metadata Method
    @abstractmethod
    def get_extended_metadata(self) -> Dict[str, any]:
        """Return storage-specific metadata for display in info dialogs.
        
        Returns:
            dict: Metadata dictionary with keys:
                - 'type': str - Storage type ('local', 'archive', 's3')
                - 'details': List[Tuple[str, str]] - List of (label, value) pairs
                - 'format_hint': str - Display format hint ('standard', 'archive', 'remote')
        
        Example for archive:
            {
                'type': 'archive',
                'details': [
                    ('Archive', 'data.zip'),
                    ('Internal Path', 'folder/file.txt'),
                    ('Compressed Size', '1.2 MB'),
                    ('Uncompressed Size', '3.4 MB')
                ],
                'format_hint': 'archive'
            }
        """
        pass
```

### LocalPathImpl Implementation

```python
class LocalPathImpl(PathImpl):
    def get_display_prefix(self) -> str:
        return ''  # No prefix for local files
    
    def get_display_title(self) -> str:
        return str(self._path)
    
    def requires_extraction_for_reading(self) -> bool:
        return False  # Direct file access
    
    def supports_streaming_read(self) -> bool:
        return True  # Can use open() and iterate
    
    def get_search_strategy(self) -> str:
        return 'streaming'  # Memory-efficient line-by-line
    
    def should_cache_for_search(self) -> bool:
        return False  # Direct access is efficient
    
    def get_extended_metadata(self) -> Dict[str, any]:
        stat_info = self._path.stat()
        details = [
            ('Type', 'Directory' if self.is_dir() else 'File'),
            ('Size', self._format_size(stat_info.st_size)),
            ('Permissions', self._format_permissions(stat_info.st_mode)),
            ('Modified', self._format_time(stat_info.st_mtime))
        ]
        return {
            'type': 'local',
            'details': details,
            'format_hint': 'standard'
        }
    
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def _format_permissions(self, mode: int) -> str:
        """Format permissions as rwxrwxrwx"""
        import stat
        perms = []
        for who in ['USR', 'GRP', 'OTH']:
            for what in ['R', 'W', 'X']:
                if mode & getattr(stat, f'S_I{what}{who}'):
                    perms.append(what.lower())
                else:
                    perms.append('-')
        return ''.join(perms)
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp as readable date/time"""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
```

### ArchivePathImpl Implementation

```python
class ArchivePathImpl(PathImpl):
    def get_display_prefix(self) -> str:
        return 'ARCHIVE: '
    
    def get_display_title(self) -> str:
        return self._uri  # Full archive://path#internal format
    
    def requires_extraction_for_reading(self) -> bool:
        return True  # Must extract from archive
    
    def supports_streaming_read(self) -> bool:
        return False  # Must read_text() entire content
    
    def get_search_strategy(self) -> str:
        return 'extracted'  # Must extract entire content
    
    def should_cache_for_search(self) -> bool:
        return True  # Cache extracted content
    
    def get_extended_metadata(self) -> Dict[str, any]:
        entry = self._get_entry()
        details = [
            ('Archive', self._archive_path.name),
            ('Internal Path', self._internal_path),
            ('Type', 'Directory' if entry.is_dir else 'File'),
            ('Compressed Size', self._format_size(entry.compress_size)),
            ('Uncompressed Size', self._format_size(entry.file_size)),
            ('Compression', self._get_compression_name(entry.compress_type)),
            ('Modified', self._format_archive_time(entry.date_time))
        ]
        return {
            'type': 'archive',
            'details': details,
            'format_hint': 'archive'
        }
    
    def _get_compression_name(self, compress_type: int) -> str:
        """Convert compression type code to name"""
        compression_names = {
            0: 'Stored',
            8: 'Deflated',
            12: 'BZIP2',
            14: 'LZMA'
        }
        return compression_names.get(compress_type, f'Unknown ({compress_type})')
    
    def _format_archive_time(self, date_time: tuple) -> str:
        """Format archive entry date_time tuple"""
        import datetime
        dt = datetime.datetime(*date_time)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
```

### S3PathImpl Implementation

```python
class S3PathImpl(PathImpl):
    def get_display_prefix(self) -> str:
        return 'S3: '
    
    def get_display_title(self) -> str:
        return self._uri  # S3 URI
    
    def requires_extraction_for_reading(self) -> bool:
        return True  # Must download from S3
    
    def supports_streaming_read(self) -> bool:
        return False  # Must download entire object
    
    def get_search_strategy(self) -> str:
        return 'buffered'  # Download to buffer
    
    def should_cache_for_search(self) -> bool:
        return True  # Cache downloaded content
    
    def get_extended_metadata(self) -> Dict[str, any]:
        metadata = self._get_s3_metadata()
        details = [
            ('Bucket', self._bucket),
            ('Key', self._key),
            ('Type', 'Directory' if self.is_dir() else 'Object'),
            ('Size', self._format_size(metadata.get('ContentLength', 0))),
            ('Storage Class', metadata.get('StorageClass', 'STANDARD')),
            ('Last Modified', str(metadata.get('LastModified', 'Unknown')))
        ]
        return {
            'type': 's3',
            'details': details,
            'format_hint': 'remote'
        }
```

### Path Facade (Delegation)

The Path class delegates to PathImpl:

```python
class Path:
    def __init__(self, path_impl: PathImpl):
        self._impl = path_impl
    
    # Delegate new methods
    def get_display_prefix(self) -> str:
        return self._impl.get_display_prefix()
    
    def get_display_title(self) -> str:
        return self._impl.get_display_title()
    
    def requires_extraction_for_reading(self) -> bool:
        return self._impl.requires_extraction_for_reading()
    
    def supports_streaming_read(self) -> bool:
        return self._impl.supports_streaming_read()
    
    def get_search_strategy(self) -> str:
        return self._impl.get_search_strategy()
    
    def should_cache_for_search(self) -> bool:
        return self._impl.should_cache_for_search()
    
    def get_extended_metadata(self) -> Dict[str, any]:
        return self._impl.get_extended_metadata()
```

## Data Models

### Extended Metadata Structure

```python
{
    'type': str,              # Storage type: 'local', 'archive', 's3'
    'details': [              # List of (label, value) tuples
        (str, str),           # e.g., ('Size', '1.2 MB')
        (str, str),           # e.g., ('Modified', '2024-01-15 10:30:00')
        ...
    ],
    'format_hint': str        # Display format: 'standard', 'archive', 'remote'
}
```

### Search Strategy Values

```python
'streaming'   # Read line by line (local files)
'extracted'   # Extract entire content (archives)
'buffered'    # Download to buffer (S3)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Display prefix consistency

*For any* ArchivePathImpl instance, calling get_display_prefix() should return "ARCHIVE: " (with trailing space)
**Validates: Requirements 2.3**

### Property 2: Display title format for archives

*For any* ArchivePathImpl instance, calling get_display_title() should return the full archive URI in the format "archive://path#internal"
**Validates: Requirements 2.3**

### Property 3: Local path display has no prefix

*For any* LocalPathImpl instance, calling get_display_prefix() should return an empty string
**Validates: Requirements 2.4**

### Property 4: Local path display title

*For any* LocalPathImpl instance, calling get_display_title() should return the standard path string representation
**Validates: Requirements 2.4**

### Property 5: S3 path display prefix

*For any* S3PathImpl instance, calling get_display_prefix() should return "S3: " (with trailing space)
**Validates: Requirements 2.5**

### Property 6: S3 path display title

*For any* S3PathImpl instance, calling get_display_title() should return the S3 URI
**Validates: Requirements 2.5**

### Property 7: Storage-agnostic error messages

*For any* path that does not support file editing, when validation fails, the error message should not contain storage-specific terms like "archive", "s3", or "local"
**Validates: Requirements 3.4, 7.6**

### Property 8: Archive metadata structure

*For any* ArchivePathImpl instance, calling get_extended_metadata() should return a dict with 'type' == 'archive' and 'details' containing entries for 'Archive', 'Internal Path', 'Compressed Size', and 'Uncompressed Size'
**Validates: Requirements 4.2**

### Property 9: Local metadata structure

*For any* LocalPathImpl instance, calling get_extended_metadata() should return a dict with 'type' == 'local' and 'details' containing entries for 'Type', 'Size', 'Permissions', and 'Modified'
**Validates: Requirements 4.3**

### Property 10: S3 metadata structure

*For any* S3PathImpl instance, calling get_extended_metadata() should return a dict with 'type' == 's3' and 'details' containing entries for 'Bucket', 'Key', 'Storage Class', and 'Last Modified'
**Validates: Requirements 4.4**

### Property 11: Local search strategy

*For any* LocalPathImpl instance, calling get_search_strategy() should return 'streaming'
**Validates: Requirements 5.2**

### Property 12: Archive search strategy

*For any* ArchivePathImpl instance, calling get_search_strategy() should return 'extracted'
**Validates: Requirements 5.3**

### Property 13: S3 search strategy

*For any* S3PathImpl instance, calling get_search_strategy() should return 'buffered'
**Validates: Requirements 5.4**

### Property 14: Archive content reading flags

*For any* ArchivePathImpl instance, requires_extraction_for_reading() should return True and supports_streaming_read() should return False
**Validates: Requirements 6.3**

### Property 15: Local content reading flags

*For any* LocalPathImpl instance, requires_extraction_for_reading() should return False and supports_streaming_read() should return True
**Validates: Requirements 6.4**

### Property 16: S3 content reading flags

*For any* S3PathImpl instance, requires_extraction_for_reading() should return True and supports_streaming_read() should return False
**Validates: Requirements 6.5**

## Error Handling

### Virtual Method Implementation Errors

**Error**: Attempting to instantiate a PathImpl subclass that doesn't implement all abstract methods
**Handling**: Python's ABC mechanism will raise TypeError at instantiation time
**Recovery**: Developer must implement all required abstract methods

### Invalid Metadata Structure

**Error**: get_extended_metadata() returns a dict missing required keys
**Handling**: UI code should handle missing keys gracefully with default values
**Recovery**: Log warning and display available metadata

### Invalid Search Strategy

**Error**: get_search_strategy() returns an unrecognized strategy string
**Handling**: Fall back to 'extracted' strategy (safest, works for all types)
**Recovery**: Log warning about unknown strategy

### Display Method Errors

**Error**: get_display_prefix() or get_display_title() raises an exception
**Handling**: Catch exception and fall back to str(path)
**Recovery**: Log error and use default string representation

## Testing Strategy

### Unit Testing Approach

Unit tests will verify that each PathImpl subclass correctly implements the virtual methods:

**LocalPathImpl Tests**:
- Test get_display_prefix() returns empty string
- Test get_display_title() returns path string
- Test get_search_strategy() returns 'streaming'
- Test requires_extraction_for_reading() returns False
- Test supports_streaming_read() returns True
- Test should_cache_for_search() returns False
- Test get_extended_metadata() returns correct structure with 'local' type

**ArchivePathImpl Tests**:
- Test get_display_prefix() returns 'ARCHIVE: '
- Test get_display_title() returns full archive URI
- Test get_search_strategy() returns 'extracted'
- Test requires_extraction_for_reading() returns True
- Test supports_streaming_read() returns False
- Test should_cache_for_search() returns True
- Test get_extended_metadata() returns correct structure with 'archive' type
- Test metadata includes archive-specific fields (compressed size, etc.)

**S3PathImpl Tests**:
- Test get_display_prefix() returns 'S3: '
- Test get_display_title() returns S3 URI
- Test get_search_strategy() returns 'buffered'
- Test requires_extraction_for_reading() returns True
- Test supports_streaming_read() returns False
- Test should_cache_for_search() returns True
- Test get_extended_metadata() returns correct structure with 's3' type
- Test metadata includes S3-specific fields (bucket, key, storage class)

**Path Facade Tests**:
- Test that Path correctly delegates all new methods to PathImpl
- Test with mock PathImpl to verify delegation

### Property-Based Testing Approach

Property-based tests will use Hypothesis to verify properties hold across many generated inputs:

**Property Test 1: Display prefix consistency**
- Generate random archive paths
- Verify get_display_prefix() always returns "ARCHIVE: "
- **Validates: Property 1, Requirements 2.3**

**Property Test 2: Display title format**
- Generate random archive paths with various internal paths
- Verify get_display_title() always returns valid archive:// URI format
- **Validates: Property 2, Requirements 2.3**

**Property Test 3: Local path display**
- Generate random local paths
- Verify get_display_prefix() always returns empty string
- Verify get_display_title() matches str(path)
- **Validates: Properties 3-4, Requirements 2.4**

**Property Test 4: Metadata structure validity**
- Generate random paths of each type
- Verify get_extended_metadata() always returns dict with required keys
- Verify 'details' is always a list of (str, str) tuples
- **Validates: Properties 8-10, Requirements 4.2-4.4**

**Property Test 5: Search strategy consistency**
- Generate random paths of each type
- Verify get_search_strategy() always returns one of: 'streaming', 'extracted', 'buffered'
- Verify LocalPathImpl always returns 'streaming'
- Verify ArchivePathImpl always returns 'extracted'
- Verify S3PathImpl always returns 'buffered'
- **Validates: Properties 11-13, Requirements 5.2-5.4**

**Property Test 6: Content reading flags consistency**
- Generate random paths of each type
- Verify requires_extraction_for_reading() and supports_streaming_read() are boolean
- Verify LocalPathImpl: extraction=False, streaming=True
- Verify ArchivePathImpl: extraction=True, streaming=False
- Verify S3PathImpl: extraction=True, streaming=False
- **Validates: Properties 14-16, Requirements 6.3-6.5**

**Property Test 7: Error message storage-agnosticism**
- Generate random paths that don't support operations
- Trigger validation errors
- Verify error messages don't contain storage-specific terms
- **Validates: Property 7, Requirements 3.4, 7.6**

### Integration Testing Approach

Integration tests will verify that UI components work correctly with the polymorphic methods:

**Text Viewer Integration**:
- Test displaying local files shows no prefix
- Test displaying archive files shows "ARCHIVE: " prefix
- Test displaying S3 files shows "S3: " prefix
- Test title formatting for all storage types

**Info Dialog Integration**:
- Test metadata display for local files
- Test metadata display for archive entries
- Test metadata display for S3 objects
- Verify unified code path works for all types

**Search Dialog Integration**:
- Test search in local directories uses streaming strategy
- Test search in archives uses extracted strategy
- Test search in S3 uses buffered strategy
- Test search context display for all storage types

**File Operations Integration**:
- Test operation validation uses capability methods
- Test error messages are storage-agnostic
- Test validation works for all storage types

### Refactoring Validation Tests

Tests to verify the refactoring was successful:

**Code Quality Tests**:
- Static analysis to verify no storage-specific conditionals in UI code
- Verify no imports of ArchivePathImpl in UI files
- Verify no string parsing of URIs in UI code
- Verify no `_is_archive_path()` methods exist

**Behavioral Equivalence Tests**:
- Compare behavior before and after refactoring
- Verify all existing functionality still works
- Verify no regressions in any workflows

## Implementation Notes

### Phased Implementation

The implementation should follow a phased approach to minimize risk:

**Phase 1: Add Virtual Methods**
1. Add abstract methods to PathImpl
2. Implement in LocalPathImpl
3. Implement in ArchivePathImpl
4. Implement in S3PathImpl
5. Add delegation methods to Path facade
6. Write unit tests for all implementations

**Phase 2: Refactor UI Code**
1. Refactor tfm_file_operations.py (use existing capability methods)
2. Refactor tfm_text_viewer.py (use display methods)
3. Refactor tfm_info_dialog.py (use metadata method)
4. Refactor tfm_search_dialog.py (use search strategy methods)
5. Test each file after refactoring

**Phase 3: Cleanup**
1. Remove storage-specific helper methods
2. Remove storage-specific imports
3. Update error messages to be storage-agnostic
4. Run full test suite

### Backward Compatibility

This refactoring maintains complete backward compatibility:
- All existing PathImpl methods remain unchanged
- New methods are additions, not modifications
- Existing code continues to work during transition
- No breaking changes to public APIs

### Performance Considerations

The refactoring should have minimal performance impact:
- Virtual method calls have negligible overhead in Python
- No additional object allocations
- Search strategies may improve performance (each storage optimizes its own approach)
- Metadata caching can be added if needed

### Future Extensibility

The new architecture makes it trivial to add new storage types:
1. Create new PathImpl subclass
2. Implement all abstract methods
3. Register with Path factory
4. Zero changes needed to UI code

Example new storage types that would work immediately:
- SFTP paths
- WebDAV paths
- FTP paths
- HTTP/HTTPS read-only paths
- Database virtual file systems
- Custom virtual file systems

## Migration Guide

### For Developers Adding New Storage Types

1. Create a new PathImpl subclass
2. Implement all abstract methods (ABC will enforce this)
3. Implement the 7 new virtual methods:
   - `get_display_prefix()` - Return display prefix or empty string
   - `get_display_title()` - Return formatted title
   - `requires_extraction_for_reading()` - Return True if extraction needed
   - `supports_streaming_read()` - Return True if can stream
   - `get_search_strategy()` - Return 'streaming', 'extracted', or 'buffered'
   - `should_cache_for_search()` - Return True if caching recommended
   - `get_extended_metadata()` - Return metadata dict with required structure
4. Write unit tests for your implementation
5. No UI code changes needed!

### For Developers Maintaining UI Code

1. Never check storage type or scheme in UI code
2. Always use virtual methods to get storage-specific behavior
3. Use capability methods (supports_file_editing, etc.) for validation
4. Keep error messages storage-agnostic
5. Trust that PathImpl implementations provide correct behavior

## Success Criteria

The refactoring is successful when:

1. ✅ All 16 correctness properties pass property-based tests
2. ✅ Zero storage-specific conditionals in UI/dialog code
3. ✅ All existing tests pass (no regressions)
4. ✅ All new unit tests pass
5. ✅ All integration tests pass
6. ✅ Static analysis confirms no storage-specific imports in UI code
7. ✅ Code review confirms architectural goals achieved
8. ✅ Performance is equivalent or better than before
9. ✅ Documentation is complete and accurate
10. ✅ Mock storage implementation works with zero UI changes
