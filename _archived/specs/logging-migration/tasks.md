# Implementation Plan: Logging Migration

## Overview

This plan breaks down the logging migration into discrete, actionable tasks. The migration follows a file-by-file approach, starting with high-priority files and progressing through all remaining TFM source files. Each task involves replacing print() statements with appropriate logger calls while preserving all functionality.

## Tasks

- [x] 1. Set up migration infrastructure
  - Create migration tracking document
  - Set up verification scripts
  - Document migration pattern
  - _Requirements: 8.1, 10.1, 10.2_

- [x] 2. Complete tfm_main.py migration
  - [x] 2.1 Migrate remaining print() statements in tfm_main.py
    - Replace all 183 remaining print() statements with logger calls
    - Use existing logger (already initialized as "Main")
    - Categorize messages by severity (error/warning/info)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3_

  - [ ]* 2.2 Write property test for message content preservation
    - **Property 4: Message Content Preservation**
    - **Validates: Requirements 2.5, 7.1, 7.3**

  - [x] 2.3 Verify tfm_main.py compiles successfully
    - Run Python compilation check
    - Fix any syntax errors
    - _Requirements: 5.1, 5.2_

- [x] 3. Checkpoint - Verify tfm_main.py migration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Migrate tfm_external_programs.py
  - [x] 4.1 Add logger initialization to tfm_external_programs.py
    - Add getLogger import at module level
    - Initialize self.logger in __init__ with name "ExtProg"
    - _Requirements: 3.1, 3.2, 3.5_

  - [x] 4.2 Replace print() statements in tfm_external_programs.py
    - Replace all 59 print() statements with logger calls
    - Categorize messages appropriately
    - Remove any "if self.logger:" checks
    - _Requirements: 2.1, 2.6, 4.1, 4.2, 4.3_

  - [ ]* 4.3 Write property test for log level categorization
    - **Property 5: Correct Log Level Categorization**
    - **Validates: Requirements 2.2, 2.3, 2.4, 4.1, 4.2, 4.3**

  - [x] 4.4 Verify tfm_external_programs.py compiles successfully
    - Run compilation check
    - Fix any errors
    - _Requirements: 5.1_

- [x] 5. Migrate tfm_color_tester.py
  - [x] 5.1 Add logger initialization to tfm_color_tester.py
    - Add getLogger import at module level
    - Initialize logger with name "ColorTest"
    - _Requirements: 3.1, 3.2, 3.5_

  - [x] 5.2 Replace print() statements in tfm_color_tester.py
    - Replace all 39 print() statements with logger calls
    - Categorize messages appropriately
    - _Requirements: 2.1, 4.1, 4.2, 4.3_

  - [ ]* 5.3 Write property test for logger initialization
    - **Property 6: Logger Initialization Presence**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 5.4 Verify tfm_color_tester.py compiles successfully
    - Run compilation check
    - _Requirements: 5.1_

- [x] 6. Checkpoint - Verify high-priority files
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Identify and prioritize remaining files
  - [x] 7.1 Scan remaining tfm_*.py files for print() statements
    - Count print() statements in each file
    - Identify files already migrated
    - Create prioritized list
    - _Requirements: 1.1, 1.4, 1.5_

  - [ ]* 7.2 Write property test for file discovery
    - **Property 1: Complete File Discovery**
    - **Validates: Requirements 1.1, 1.2**

  - [ ]* 7.3 Write property test for print statement counting
    - **Property 2: Accurate Print Statement Counting**
    - **Validates: Requirements 1.4**

  - [x] 7.4 Update progress document with remaining files
    - List all remaining files
    - Document print() counts
    - _Requirements: 8.1, 8.2_

- [x] 8. Migrate remaining files (Batch 1)
  - [ ] 8.1 Migrate next 3-5 files with highest print() counts
    - Add logger initialization if needed
    - Replace all print() statements
    - Use appropriate log levels
    - Verify compilation
    - _Requirements: 2.1, 3.1, 3.2, 4.1, 4.2, 4.3, 5.1_

  - [ ]* 8.2 Write property test for complete replacement
    - **Property 3: Complete Print Statement Replacement**
    - **Validates: Requirements 2.1**

  - [ ]* 8.3 Write property test for no duplicate imports
    - **Property 7: No Duplicate Imports**
    - **Validates: Requirements 3.4**

  - [ ] 8.4 Update progress document
    - Mark files as completed
    - Update statement counts
    - _Requirements: 8.2, 8.3_

- [x] 9. Migrate remaining files (Batch 2)
  - [x] 9.1 Migrate next batch of files
    - Continue with remaining files
    - Follow same pattern as Batch 1
    - _Requirements: 2.1, 3.1, 3.2, 4.1, 4.2, 4.3, 5.1_

  - [ ]* 9.2 Write property test for conditional check removal
    - **Property 8: Conditional Logger Check Removal**
    - **Validates: Requirements 2.6**

  - [ ]* 9.3 Write property test for compilation success
    - **Property 9: Successful Compilation**
    - **Validates: Requirements 5.1**

  - [x] 9.4 Update progress document
    - Mark files as completed
    - _Requirements: 8.2, 8.3_

- [x] 10. Checkpoint - Verify batch migrations
  - Ensure all tests pass, ask the user if questions arise.

- [-] 11. Handle module-level print() statements
  - [x] 11.1 Identify files with module-level print() statements
    - Scan for print() outside class definitions
    - List affected files
    - _Requirements: 6.1_

  - [x] 11.2 Add module-level loggers
    - Add logger = getLogger("ModuleName") at module level
    - Replace module-level print() statements
    - _Requirements: 6.2, 6.3_

  - [ ]* 11.3 Write property test for module-level logger pattern
    - **Property 10: Module-Level Logger Pattern**
    - **Validates: Requirements 6.1, 6.2**

  - [x] 11.4 Verify compilation
    - Check all affected files compile
    - _Requirements: 5.1_

- [x] 12. Handle special cases and edge cases
  - [x] 12.1 Handle print() in lambda functions
    - Identify lambda functions with print()
    - Transform to use module-level logger
    - _Requirements: 9.1_

  - [x] 12.2 Handle print() with complex formatting
    - Preserve f-strings, .format(), % formatting
    - Verify formatting works correctly
    - _Requirements: 9.2_

  - [x] 12.3 Handle print() in exception handlers
    - Ensure logger.error() is used in except blocks
    - _Requirements: 9.4_

  - [ ]* 12.4 Write property test for exception context awareness
    - **Property 14: Exception Context Awareness**
    - **Validates: Requirements 9.4**

  - [x] 12.5 Handle print() with file= parameter
    - Remove file= parameter from print() statements
    - _Requirements: 9.5_

  - [ ]* 12.6 Write property test for file parameter removal
    - **Property 15: File Parameter Removal**
    - **Validates: Requirements 9.5**

- [x] 13. Comprehensive verification
  - [x] 13.1 Search for remaining print() statements
    - Run grep search across all tfm_*.py files
    - Verify no print() statements remain (except in comments/strings)
    - _Requirements: 2.1_

  - [ ]* 13.2 Write property test for control flow preservation
    - **Property 11: Control Flow Preservation**
    - **Validates: Requirements 7.2, 7.4**

  - [ ]* 13.3 Write property test for comment preservation
    - **Property 12: Comment Preservation**
    - **Validates: Requirements 7.5**

  - [x] 13.4 Verify all files compile
    - Run compilation check on all migrated files
    - Fix any errors
    - _Requirements: 5.1_

  - [x] 13.5 Run smoke tests
    - Start TFM and verify basic functionality
    - Check log pane for messages
    - Verify no errors or crashes
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 14. Checkpoint - Final verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Update documentation
  - [x] 15.1 Update coding standards
    - Document mandatory logger usage
    - Add migration pattern examples
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 15.2 Create migration completion report
    - Document total files migrated
    - Document total statements replaced
    - List any exceptions or special cases
    - _Requirements: 8.3, 8.5, 10.5_

  - [ ]* 15.3 Write property test for progress tracking accuracy
    - **Property 13: Progress Tracking Accuracy**
    - **Validates: Requirements 8.2, 8.3, 8.5**

  - [x] 15.4 Update developer documentation
    - Update LOGGING_SYSTEM.md with migration info
    - Document logger naming conventions
    - _Requirements: 10.3, 10.4_

- [-] 16. Final cleanup
  - [x] 16.1 Archive temporary migration files
    - Move temp/LOGGING_MIGRATION_PROGRESS.md to archive
    - Clean up any backup files
    - _Requirements: 8.1_

  - [x] 16.2 Update spec status
    - Mark logging-migration spec as COMPLETE
    - Update README if needed
    - _Requirements: 8.1_

  - [-] 16.3 Commit changes
    - Create descriptive commit message
    - Tag commit as logging-migration-complete
    - _Requirements: 8.1_

- [ ] 17. Final checkpoint - Migration complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The migration is manual, not automated - each file requires careful review
- Stop and verify after each file to catch errors early
- Update progress document after each file or batch

## Migration Pattern Reference

### Standard Pattern for Classes

```python
# At module level
from tfm_log_manager import getLogger

class MyComponent:
    def __init__(self, ...):
        # Initialize logger
        self.logger = getLogger("ComponentName")
    
    def some_method(self):
        # Replace print() with appropriate logger call
        # Old: print(f"Error: {msg}")
        self.logger.error(f"Error: {msg}")
        
        # Old: print(f"Warning: {msg}")
        self.logger.warning(f"Warning: {msg}")
        
        # Old: print(f"Info: {msg}")
        self.logger.info(f"Info: {msg}")
```

### Pattern for Module-Level Code

```python
# At module level
from tfm_log_manager import getLogger

logger = getLogger("ModuleName")

# Replace module-level print() statements
# Old: print("Starting module")
logger.info("Starting module")
```

### Logger Naming Conventions

- Use descriptive, concise names
- Use PascalCase for multi-word names
- Examples: "Main", "FileOp", "Archive", "Cache", "UILayer", "ExtProg", "ColorTest"
- Keep names under 15 characters when possible

### Log Level Guidelines

- **ERROR**: Operation failed, data loss, or critical issue
- **WARNING**: Potential issue, degraded functionality, or user should be aware
- **INFO**: Normal operation, user actions, status updates
- **DEBUG**: Detailed information for troubleshooting (rarely used in TFM)
