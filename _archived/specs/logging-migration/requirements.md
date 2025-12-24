# Requirements Document

## Introduction

This specification defines the requirements for migrating all TFM source code from using print() statements to the new unified logging system. The logging infrastructure has been established (module-level getLogger() function), and several files have been migrated as proof-of-concept. This spec covers the systematic migration of all remaining TFM source files.

## Glossary

- **TFM**: Terminal File Manager - the main application
- **TTK**: Terminal Toolkit - the underlying UI library (out of scope for this migration)
- **Logger**: A Python logging.Logger instance configured with TFM handlers
- **getLogger**: Module-level function in tfm_log_manager that returns configured loggers
- **Print Statement**: Direct calls to Python's print() function
- **Log Level**: Categorization of log messages (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Requirements

### Requirement 1: Identify All TFM Source Files

**User Story:** As a developer, I want to identify all TFM source files that need migration, so that I can systematically update the codebase.

#### Acceptance Criteria

1. THE System SHALL identify all Python files in the src/ directory with the tfm_*.py naming pattern
2. THE System SHALL exclude TTK library files from the migration scope
3. THE System SHALL categorize files by migration status (completed, in-progress, not-started)
4. THE System SHALL count the number of print() statements in each file
5. THE System SHALL prioritize files by number of print() statements and importance

### Requirement 2: Migrate Print Statements to Logger Calls

**User Story:** As a developer, I want to replace all print() statements with appropriate logger calls, so that all output goes through the unified logging system.

#### Acceptance Criteria

1. WHEN a file contains print() statements, THE System SHALL replace them with logger method calls
2. THE System SHALL use self.logger.error() for error messages
3. THE System SHALL use self.logger.warning() for warning messages
4. THE System SHALL use self.logger.info() for informational messages
5. THE System SHALL preserve the original message content and formatting
6. THE System SHALL remove any conditional checks like "if self.logger:" since logger is always available

### Requirement 3: Initialize Logger in Each Class

**User Story:** As a developer, I want each class to have a properly initialized logger, so that logging is available throughout the class.

#### Acceptance Criteria

1. WHEN a class needs logging, THE System SHALL add "from tfm_log_manager import getLogger" at module level
2. THE System SHALL initialize self.logger in the __init__ method using getLogger("ComponentName")
3. THE System SHALL use descriptive component names that identify the module's purpose
4. THE System SHALL ensure the import statement is not duplicated if already present
5. THE System SHALL follow the established naming convention (e.g., "Main", "FileOp", "Archive")

### Requirement 4: Categorize Log Messages by Severity

**User Story:** As a developer, I want log messages properly categorized by severity, so that users can filter and understand message importance.

#### Acceptance Criteria

1. WHEN a message indicates an error condition, THE System SHALL use logger.error()
2. WHEN a message indicates a warning or potential issue, THE System SHALL use logger.warning()
3. WHEN a message provides general information, THE System SHALL use logger.info()
4. WHEN a message provides debugging information, THE System SHALL use logger.debug()
5. THE System SHALL maintain consistent categorization across all files

### Requirement 5: Verify Code Compilation

**User Story:** As a developer, I want to verify that migrated files compile successfully, so that I don't introduce syntax errors.

#### Acceptance Criteria

1. WHEN a file is migrated, THE System SHALL verify it compiles without errors
2. WHEN compilation fails, THE System SHALL report the specific errors
3. THE System SHALL use Python's ast module or getDiagnostics tool for verification
4. THE System SHALL not proceed to the next file until current file compiles successfully

### Requirement 6: Handle Files Without Classes

**User Story:** As a developer, I want to handle module-level code that doesn't use classes, so that all code patterns are supported.

#### Acceptance Criteria

1. WHEN a file has module-level print() statements outside classes, THE System SHALL create a module-level logger
2. THE System SHALL use the pattern: logger = getLogger("ModuleName") at module level
3. THE System SHALL replace print() with logger.info(), logger.error(), etc. at module level
4. THE System SHALL handle both class-based and module-level logging patterns

### Requirement 7: Preserve Existing Functionality

**User Story:** As a developer, I want the migration to preserve all existing functionality, so that no behavioral changes occur.

#### Acceptance Criteria

1. THE System SHALL only change the logging mechanism, not the message content
2. THE System SHALL preserve all conditional logic around print statements
3. THE System SHALL maintain the same message formatting and string interpolation
4. THE System SHALL not alter program flow or control structures
5. THE System SHALL preserve comments and documentation

### Requirement 8: Track Migration Progress

**User Story:** As a developer, I want to track migration progress across all files, so that I know what work remains.

#### Acceptance Criteria

1. THE System SHALL maintain a progress document listing all files and their status
2. THE System SHALL update the progress document after each file migration
3. THE System SHALL report the total number of print() statements replaced
4. THE System SHALL identify any files that cannot be automatically migrated
5. THE System SHALL provide a summary of completed vs remaining work

### Requirement 9: Handle Special Cases

**User Story:** As a developer, I want special cases handled appropriately, so that edge cases don't break the migration.

#### Acceptance Criteria

1. WHEN a print() statement is in a lambda or nested function, THE System SHALL handle it appropriately
2. WHEN a print() statement uses complex formatting, THE System SHALL preserve the formatting
3. WHEN a file already has partial logger usage, THE System SHALL complete the migration consistently
4. WHEN a print() statement is in exception handling, THE System SHALL use appropriate log level
5. THE System SHALL handle print() statements with file= parameter by removing the parameter

### Requirement 10: Document Migration Pattern

**User Story:** As a developer, I want clear documentation of the migration pattern, so that future code follows the same approach.

#### Acceptance Criteria

1. THE System SHALL document the standard migration pattern in a design document
2. THE System SHALL provide examples of before/after code
3. THE System SHALL document the logger naming conventions
4. THE System SHALL document how to choose appropriate log levels
5. THE System SHALL document any exceptions or special cases
