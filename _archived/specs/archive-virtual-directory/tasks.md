# Implementation Plan

## Completed Work

- [x] 1. Create archive module foundation
  - Created `src/tfm_archive.py` with ArchiveOperations and ArchiveUI classes
  - Implemented archive format detection and validation
  - Added support for .zip, .tar, .tar.gz, .tgz, .tar.bz2, .tar.xz formats
  - Integrated with cross-storage operations (local, S3)
  - _Requirements: 1.3, 7.1, 7.2_

- [x] 2. Implement archive creation and extraction
  - Implemented create_archive with cross-storage support
  - Implemented extract_archive with cross-storage support
  - Added progress tracking for archive operations
  - Integrated with FileManager UI for archive creation/extraction
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

## Remaining Work - Virtual Directory Browsing

- [x] 3. Implement ArchiveEntry data class
  - Create ArchiveEntry dataclass with all required fields (name, internal_path, is_dir, size, compressed_size, mtime, mode, archive_type)
  - Implement helper methods for ArchiveEntry (to_stat_result, from_zip_info, from_tar_info)
  - _Requirements: 1.2, 6.5_

- [x] 4. Implement ArchiveHandler class
  - Create ArchiveHandler class with initialization and archive opening logic
  - Implement archive format-specific handlers (ZipHandler, TarHandler)
  - Implement list_entries method for listing directory contents within archives
  - Implement get_entry_info method for retrieving entry metadata
  - Implement extract_to_bytes method for in-memory extraction
  - Implement extract_to_file method for filesystem extraction
  - Add proper error handling for corrupt archives and missing entries
  - _Requirements: 1.1, 1.2, 1.5, 3.1, 3.2, 7.1_

- [ ]* 4.1 Write property test for file extraction content preservation
  - **Property 6: File extraction preserves content**
  - **Validates: Requirements 3.1**

- [ ]* 4.2 Write property test for metadata preservation
  - **Property 7: Metadata preservation during extraction**
  - **Validates: Requirements 3.2**

- [x] 5. Implement ArchiveCache class
  - Create ArchiveCache class with LRU eviction policy
  - Implement get_handler method with lazy initialization
  - Implement cache invalidation methods
  - Add thread safety with locks
  - Implement cache statistics and monitoring
  - _Requirements: Performance optimization_

- [x] 6. Implement ArchivePathImpl class
  - Create ArchivePathImpl class inheriting from PathImpl
  - Implement URI parsing (_parse_uri, _normalize_internal_path)
  - Implement all PathImpl abstract methods for archive paths
  - Implement path properties (name, stem, suffix, parent, parts, etc.)
  - Implement path manipulation methods (joinpath, with_name, with_suffix, etc.)
  - Implement file system query methods (exists, is_dir, is_file, stat, etc.)
  - Implement directory operations (iterdir, glob, rglob, match)
  - Implement file I/O operations (open, read_text, read_bytes)
  - Add metadata caching to avoid repeated archive reads
  - Use ArchiveHandler and ArchiveCache for archive access
  - _Requirements: 1.1, 1.2, 2.2, 2.3, 2.5, 4.1, 5.1, 6.2, 6.4, 6.5_

- [ ]* 6.1 Write property test for archive internal navigation
  - **Property 4: Archive internal navigation consistency**
  - **Validates: Requirements 2.2, 2.3**

- [ ]* 6.2 Write property test for path display completeness
  - **Property 5: Archive path display completeness**
  - **Validates: Requirements 2.5, 6.2**

- [ ]* 6.3 Write property test for directory indicator consistency
  - **Property 13: Directory indicator consistency**
  - **Validates: Requirements 6.4**

- [ ]* 6.4 Write property test for uncompressed size display
  - **Property 14: Uncompressed size display**
  - **Validates: Requirements 6.5**

- [x] 7. Integrate ArchivePathImpl with Path factory
  - Modify Path._create_implementation in tfm_path.py to detect archive:// URIs
  - Add import for ArchivePathImpl
  - Test Path creation with archive URIs (archive:///path/to/file.zip#internal/path)
  - _Requirements: 1.1_

- [ ]* 7.1 Write property test for archive navigation history
  - **Property 2: Archive navigation preserves history**
  - **Validates: Requirements 1.4**

- [ ]* 7.2 Write property test for corrupt archive handling
  - **Property 3: Corrupt archive handling**
  - **Validates: Requirements 1.5, 7.1, 7.2**

- [ ]* 7.3 Write property test for archive entry round trip
  - **Property 1: Archive entry round trip**
  - **Validates: Requirements 1.1, 1.2, 1.3**

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Integrate archive virtual directory browsing with FileManager
  - Modify FileManager.handle_enter_key to detect archive files and create archive:// URIs
  - Add logic to navigate into archives as virtual directories
  - Update path display to show archive name and internal path clearly
  - Add visual indicator for archive browsing in status bar
  - Support backspace navigation within archives and exiting archives
  - _Requirements: 1.1, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2_

- [x] 10. Implement archive file viewing support
  - Modify text viewer integration to handle archive:// paths
  - Implement temporary file extraction for viewing files within archives
  - Add cleanup logic for temporary files after viewer closes
  - Update viewer title to show full archive path
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 10.1 Write property test for archive file viewing
  - **Property 10: Archive file viewing round trip**
  - **Validates: Requirements 4.1**

- [ ]* 10.2 Write property test for temporary file cleanup
  - **Property 11: Temporary file cleanup**
  - **Validates: Requirements 4.3**

- [x] 11. Implement archive copy operations from virtual directories
  - Extend file operations to handle archive:// source paths
  - Implement single file extraction during copy from archive
  - Implement recursive directory extraction during copy from archive
  - Add progress feedback for extraction operations
  - Handle cross-storage copies (archive to S3, archive to local)
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 11.1 Write property test for cross-storage copy
  - **Property 8: Cross-storage copy correctness**
  - **Validates: Requirements 3.3**

- [ ]* 11.2 Write property test for recursive directory extraction
  - **Property 9: Recursive directory extraction completeness**
  - **Validates: Requirements 3.4**

- [ ]* 11.3 Write property test for batch operations
  - **Property 15: Batch operation completeness**
  - **Validates: Requirements 8.2**

- [x] 12. Implement archive search support
  - Extend search dialog to work with archive:// paths
  - Implement archive-scoped search (only search within current archive)
  - Update search results to show full archive paths
  - Implement navigation to search results within archives
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 12.1 Write property test for archive search
  - **Property 12: Archive search scope correctness**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [x] 13. Implement archive metadata display
  - Extend file details dialog to show archive entry metadata
  - Display uncompressed size, compressed size, compression ratio
  - Show archive type and internal path
  - _Requirements: 6.5, 8.3_

- [ ]* 13.1 Write property test for metadata display
  - **Property 16: Metadata display completeness**
  - **Validates: Requirements 8.3**

- [x] 14. Implement archive sorting support
  - Ensure sort operations work correctly with archive entries
  - Test all sort modes (name, size, date, type, ext) with archives
  - Verify directories-first sorting works in archives
  - _Requirements: 8.4_

- [ ]* 14.1 Write property test for sort consistency
  - **Property 17: Sort order consistency**
  - **Validates: Requirements 8.4**

- [x] 15. Add archive support to dual-pane operations
  - Test archive browsing in left and right panes
  - Test copy operations between archive and filesystem panes
  - Test copy operations between two archive panes
  - Verify pane synchronization works with archives
  - _Requirements: 8.5_

- [x] 16. Implement comprehensive error handling
  - Add error handling for all archive virtual directory operations
  - Implement user-friendly error messages for navigation failures
  - Add logging for all archive browsing operations
  - Test error recovery scenarios (corrupt archives, missing entries)
  - _Requirements: 1.5, 3.5, 4.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Performance optimization
  - Verify archive caching with LRU eviction is working efficiently
  - Add lazy loading for archive directory structures
  - Optimize memory usage for large archives
  - Profile and optimize hot paths in ArchivePathImpl
  - _Requirements: Performance_

- [x] 19. Create end-user documentation
  - Create `doc/ARCHIVE_VIRTUAL_DIRECTORY_FEATURE.md` with user guide
  - Document how to browse archives as virtual directories
  - Document navigation within archives (ENTER, backspace)
  - Provide usage examples and key bindings
  - Add troubleshooting section for archive browsing
  - _Requirements: All user-facing requirements_

- [x] 20. Create developer documentation
  - Create `doc/dev/ARCHIVE_VIRTUAL_DIRECTORY_IMPLEMENTATION.md` with technical details
  - Document ArchivePathImpl architecture and design
  - Document ArchiveHandler and ArchiveCache implementation
  - Provide code examples for extending archive support
  - Document caching strategy and performance considerations
  - Add API reference for archive classes
  - _Requirements: All requirements_

- [x] 21. Final integration testing
  - Test virtual directory browsing for all archive formats (.zip, .tar, .tar.gz, .tgz, .tar.bz2, .tar.xz)
  - Test navigation within large archives (>1GB)
  - Test with deeply nested directory structures within archives
  - Test with archives containing many files (>10,000)
  - Test with special characters in filenames within archives
  - Test on all supported platforms (Linux, macOS, Windows)
  - _Requirements: All requirements_

- [x] 22. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
