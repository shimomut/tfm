# Archive Operations Refactoring

## Overview

This document describes the refactoring of archive operations from the FileManager class to a separate modular architecture in TFM (TUI File Manager).

## Problem

The FileManager class had grown too large with many archive-related methods mixed in with other functionality. This made the code harder to maintain and violated the single responsibility principle.

## Solution

Refactored archive operations into two separate classes:

### 1. ArchiveOperations Class (src/tfm_archive.py)
- **Purpose**: Core archive functionality with cross-storage support
- **Responsibilities**:
  - Archive format detection
  - Archive creation (ZIP, TAR.GZ, TAR.BZ2, TAR.XZ, etc.)
  - Archive extraction with overwrite handling
  - Cross-storage operations (local ↔ remote)
  - Archive content listing
  - Cache invalidation integration

### 2. ArchiveUI Class (src/tfm_archive.py)
- **Purpose**: UI-specific archive operations for the file manager
- **Responsibilities**:
  - Archive creation mode handling
  - User confirmation dialogs
  - Progress tracking integration
  - File selection logic
  - Error handling and user feedback
  - Integration with FileManager's UI components

## Architecture Changes

### Before Refactoring
```
FileManager
├── enter_create_archive_mode()
├── on_create_archive_confirm()
├── on_create_archive_cancel()
├── perform_create_archive()
├── create_zip_archive()
├── create_tar_archive()
├── extract_selected_archive()
├── perform_extraction()
├── extract_zip_archive()
├── extract_tar_archive()
├── detect_archive_format()
├── get_archive_basename()
└── ... (many other non-archive methods)
```

### After Refactoring
```
FileManager
├── archive_operations: ArchiveOperations
├── archive_ui: ArchiveUI
└── ... (delegated archive methods for backward compatibility)

ArchiveOperations
├── create_archive()
├── extract_archive()
├── is_archive()
├── get_archive_format()
├── list_archive_contents()
└── ... (cross-storage support methods)

ArchiveUI
├── enter_create_archive_mode()
├── on_create_archive_confirm()
├── on_create_archive_cancel()
├── extract_selected_archive()
├── perform_extraction()
├── get_archive_basename()
└── ... (UI integration methods)
```

## Key Improvements

### 1. Separation of Concerns
- **ArchiveOperations**: Pure archive functionality, no UI dependencies
- **ArchiveUI**: UI integration, depends on FileManager for dialogs and display
- **FileManager**: Delegates archive operations, maintains backward compatibility

### 2. Enhanced Cross-Storage Support
- Improved handling of remote storage operations
- Better temporary file management
- Consistent cache invalidation

### 3. Better Error Handling
- Specific exception handling instead of bare except clauses
- Proper cleanup of temporary files
- User-friendly error messages

### 4. Progress Tracking Integration
- Unified progress tracking through ProgressManager
- Better user feedback during long operations
- Consistent progress display across all archive operations

### 5. Backward Compatibility
- All existing method signatures preserved as delegation methods
- No breaking changes to external interfaces
- Legacy methods marked for future removal

## Files Modified

### Core Files
- `src/tfm_archive.py` - Enhanced with ArchiveUI class
- `src/tfm_main.py` - Refactored to use new architecture

### Dependencies
- Added import for ArchiveUI in tfm_main.py
- Enhanced ArchiveOperations constructor to accept progress_manager
- Updated FileManager initialization to create ArchiveUI instance

## Migration Path

### Phase 1: Refactoring (Current)
- Move archive methods to separate classes
- Maintain backward compatibility through delegation
- Update initialization and imports

### Phase 2: Cleanup (Future)
- Remove legacy delegation methods from FileManager
- Update any external code that might call archive methods directly
- Remove deprecated method stubs

### Phase 3: Enhancement (Future)
- Add support for additional archive formats
- Implement archive preview functionality
- Add batch archive operations

## Testing Considerations

### Existing Tests
- All existing archive operation tests should continue to work
- Tests use the same public interface (delegation methods)
- No test changes required for this refactoring

### Bug Fix Applied
- **Issue**: `_count_files_recursively` method was moved to ArchiveUI but still needed by FileManager for copy/move/delete operations
- **Solution**: Restored the method to FileManager class as it's used by multiple non-archive operations
- **Result**: All functionality works correctly without breaking existing operations

### New Test Opportunities
- Unit tests for ArchiveOperations class in isolation
- UI-specific tests for ArchiveUI class
- Cross-storage operation tests
- Error handling and edge case tests

## Benefits

### 1. Maintainability
- Smaller, focused classes with single responsibilities
- Easier to understand and modify archive functionality
- Clear separation between core logic and UI integration

### 2. Testability
- Archive operations can be tested independently
- UI operations can be mocked for testing
- Better test coverage possibilities

### 3. Reusability
- ArchiveOperations can be used by other components
- UI patterns can be applied to other operations
- Cross-storage support is modular and reusable

### 4. Extensibility
- Easy to add new archive formats
- Simple to enhance UI interactions
- Straightforward to add new features

## Configuration

No configuration changes required. All existing configuration options continue to work:

- `CONFIRM_EXTRACT_ARCHIVE` - Controls extraction confirmation dialogs
- Archive format support remains the same
- Progress tracking settings apply automatically

## Performance Impact

### Positive Impacts
- Better memory management with proper cleanup
- More efficient cross-storage operations
- Reduced FileManager class size improves loading

### Neutral Impacts
- Minimal overhead from delegation methods
- Same archive operation performance
- No impact on startup time

## Future Enhancements

### Planned Improvements
1. **Additional Archive Formats**
   - 7-Zip support (.7z)
   - RAR extraction support (.rar)
   - LZ4 compression support

2. **Enhanced UI Features**
   - Archive content preview before extraction
   - Selective extraction (choose files to extract)
   - Archive integrity verification

3. **Performance Optimizations**
   - Streaming archive operations for large files
   - Parallel compression for multi-core systems
   - Smart caching of archive metadata

4. **Integration Improvements**
   - Better integration with external programs
   - Archive operation history
   - Undo/redo support for archive operations

## Conclusion

This refactoring successfully separates archive operations from the main FileManager class while maintaining full backward compatibility. The new architecture is more maintainable, testable, and extensible, setting the foundation for future enhancements to TFM's archive handling capabilities.