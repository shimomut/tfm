# Implementation Plan

- [x] 1. Add virtual methods to PathImpl interface
  - Add 7 new abstract methods to PathImpl base class in tfm_path.py
  - Include comprehensive docstrings for each method
  - Define return types and expected behavior
  - _Requirements: 1.4, 8.1, 8.4_

- [x] 2. Implement display methods in LocalPathImpl
  - Implement get_display_prefix() returning empty string
  - Implement get_display_title() returning path string
  - Add helper methods for formatting if needed
  - _Requirements: 2.4_

- [ ]* 2.1 Write property test for LocalPathImpl display methods
  - **Property 3: Local path display has no prefix**
  - **Property 4: Local path display title**
  - **Validates: Requirements 2.4**

- [x] 3. Implement content reading methods in LocalPathImpl
  - Implement requires_extraction_for_reading() returning False
  - Implement supports_streaming_read() returning True
  - Implement get_search_strategy() returning 'streaming'
  - Implement should_cache_for_search() returning False
  - _Requirements: 5.2, 6.4_

- [ ]* 3.1 Write property test for LocalPathImpl content reading methods
  - **Property 15: Local content reading flags**
  - **Property 11: Local search strategy**
  - **Validates: Requirements 5.2, 6.4**

- [x] 4. Implement metadata method in LocalPathImpl
  - Implement get_extended_metadata() returning structured dict
  - Add helper methods for formatting size, permissions, time
  - Include Type, Size, Permissions, Modified fields
  - _Requirements: 4.3_

- [ ]* 4.1 Write property test for LocalPathImpl metadata
  - **Property 9: Local metadata structure**
  - **Validates: Requirements 4.3**

- [x] 5. Implement display methods in ArchivePathImpl
  - Implement get_display_prefix() returning 'ARCHIVE: '
  - Implement get_display_title() returning full archive URI
  - _Requirements: 2.3_

- [ ]* 5.1 Write property test for ArchivePathImpl display methods
  - **Property 1: Display prefix consistency**
  - **Property 2: Display title format for archives**
  - **Validates: Requirements 2.3**

- [x] 6. Implement content reading methods in ArchivePathImpl
  - Implement requires_extraction_for_reading() returning True
  - Implement supports_streaming_read() returning False
  - Implement get_search_strategy() returning 'extracted'
  - Implement should_cache_for_search() returning True
  - _Requirements: 5.3, 6.3_

- [ ]* 6.1 Write property test for ArchivePathImpl content reading methods
  - **Property 14: Archive content reading flags**
  - **Property 12: Archive search strategy**
  - **Validates: Requirements 5.3, 6.3**

- [x] 7. Implement metadata method in ArchivePathImpl
  - Implement get_extended_metadata() returning structured dict
  - Add helper methods for formatting compression type, archive time
  - Include Archive, Internal Path, Compressed Size, Uncompressed Size, Compression, Modified fields
  - _Requirements: 4.2_

- [ ]* 7.1 Write property test for ArchivePathImpl metadata
  - **Property 8: Archive metadata structure**
  - **Validates: Requirements 4.2**

- [x] 8. Implement display methods in S3PathImpl
  - Implement get_display_prefix() returning 'S3: '
  - Implement get_display_title() returning S3 URI
  - _Requirements: 2.5_

- [ ]* 8.1 Write property test for S3PathImpl display methods
  - **Property 5: S3 path display prefix**
  - **Property 6: S3 path display title**
  - **Validates: Requirements 2.5**

- [x] 9. Implement content reading methods in S3PathImpl
  - Implement requires_extraction_for_reading() returning True
  - Implement supports_streaming_read() returning False
  - Implement get_search_strategy() returning 'buffered'
  - Implement should_cache_for_search() returning True
  - _Requirements: 5.4, 6.5_

- [ ]* 9.1 Write property test for S3PathImpl content reading methods
  - **Property 16: S3 content reading flags**
  - **Property 13: S3 search strategy**
  - **Validates: Requirements 5.4, 6.5**

- [x] 10. Implement metadata method in S3PathImpl
  - Implement get_extended_metadata() returning structured dict
  - Include Bucket, Key, Storage Class, Last Modified fields
  - _Requirements: 4.4_

- [ ]* 10.1 Write property test for S3PathImpl metadata
  - **Property 10: S3 metadata structure**
  - **Validates: Requirements 4.4**

- [x] 11. Add delegation methods to Path facade
  - Add get_display_prefix() delegating to _impl
  - Add get_display_title() delegating to _impl
  - Add requires_extraction_for_reading() delegating to _impl
  - Add supports_streaming_read() delegating to _impl
  - Add get_search_strategy() delegating to _impl
  - Add should_cache_for_search() delegating to _impl
  - Add get_extended_metadata() delegating to _impl
  - _Requirements: 1.2_

- [ ]* 11.1 Write unit tests for Path facade delegation
  - Test that Path correctly delegates all new methods to PathImpl
  - Use mock PathImpl to verify delegation

- [x] 12. Checkpoint - Verify all virtual methods work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Refactor tfm_file_operations.py operation validation
  - Remove _is_archive_path() method entirely
  - Replace archive checks with supports_file_editing() checks
  - Replace archive checks with supports_directory_rename() checks
  - Update error messages to be storage-agnostic (no "archive" mentions)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.1, 7.5_

- [ ]* 13.1 Write property test for storage-agnostic error messages
  - **Property 7: Storage-agnostic error messages**
  - **Validates: Requirements 3.4, 7.6**

- [ ]* 13.2 Write integration tests for file operations validation
  - Test delete validation with local, archive, and S3 paths
  - Test move validation with local, archive, and S3 paths
  - Test copy validation with local, archive, and S3 paths
  - Verify error messages are storage-agnostic

- [x] 14. Refactor tfm_text_viewer.py title display
  - Remove scheme check conditional (if scheme == 'archive')
  - Replace with path.get_display_prefix() + path.get_display_title()
  - _Requirements: 2.1, 2.2, 7.2_

- [ ]* 14.1 Write integration tests for text viewer display
  - Test title display for local files
  - Test title display for archive files
  - Test title display for S3 files
  - Verify formatting is correct for all types

- [x] 15. Refactor tfm_info_dialog.py metadata display
  - Remove is_archive_path string parsing check
  - Remove _add_archive_entry_details() method
  - Remove _add_regular_file_details() method (if exists)
  - Implement unified metadata display using path.get_extended_metadata()
  - Display common fields (Name, Path) followed by storage-specific details
  - _Requirements: 4.1, 4.5, 7.3, 7.5_

- [ ]* 15.1 Write integration tests for info dialog metadata
  - Test metadata display for local files
  - Test metadata display for archive entries
  - Test metadata display for S3 objects
  - Verify all expected fields are shown

- [x] 16. Refactor tfm_search_dialog.py search strategy
  - Remove _is_archive_path() method entirely
  - Remove ArchivePathImpl import
  - Replace search strategy conditionals with path.get_search_strategy()
  - Remove is_archive field from result structure
  - Update title display to use path.get_display_prefix()
  - _Requirements: 5.1, 5.5, 5.6, 5.7, 7.4, 7.5_

- [ ]* 16.1 Write integration tests for search dialog
  - Test search in local directories uses streaming
  - Test search in archives uses extracted strategy
  - Test search in S3 uses buffered strategy
  - Test search context display for all storage types
  - Verify results are correct for all types

- [x] 17. Checkpoint - Verify all refactoring complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Run static analysis to verify no storage-specific conditionals
  - Verify no "if scheme == 'archive'" checks in UI files
  - Verify no "if scheme == 's3'" checks in UI files
  - Verify no string parsing of URIs (startswith('archive://'))
  - Verify no isinstance checks for ArchivePathImpl in UI files
  - Verify no imports of ArchivePathImpl in UI files
  - _Requirements: 1.3, 7.1, 7.2, 7.3, 7.4_

- [x] 19. Run full test suite to verify no regressions
  - Run all existing unit tests
  - Run all existing integration tests
  - Verify all tests pass
  - _Requirements: All_

- [x] 20. Performance validation
  - Benchmark search operations before and after
  - Benchmark metadata display before and after
  - Verify no performance regressions
  - Verify memory usage is reasonable

- [x] 21. Create mock storage implementation for extensibility test
  - Create MockPathImpl implementing all abstract methods
  - Verify UI code works with mock implementation without modifications
  - This validates that new storage types require zero UI changes
  - _Requirements: 1.1_

- [ ]* 21.1 Write integration test with mock storage
  - Test text viewer with mock paths
  - Test info dialog with mock paths
  - Test search dialog with mock paths
  - Test file operations with mock paths
  - Verify everything works without UI modifications

- [x] 22. Update developer documentation
  - Document the 7 new virtual methods in PathImpl
  - Document how to add new storage types
  - Update architecture documentation
  - Add migration guide for developers
  - _Requirements: 8.1, 8.3, 8.4_

- [x] 23. Final checkpoint - Verify all success criteria met
  - Ensure all tests pass, ask the user if questions arise.
