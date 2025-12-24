# Design Document: Logging Migration

## Overview

This document describes the design for migrating all TFM source code from using print() statements to the unified logging system. The migration is a code transformation process that systematically replaces print() calls with appropriate logger method calls while preserving all functionality and message content.

The logging infrastructure already exists (tfm_log_manager with module-level getLogger() function), and several files have been successfully migrated as proof-of-concept. This design covers the systematic migration of all remaining TFM source files.

## Architecture

### High-Level Approach

The migration follows a file-by-file approach with these phases:

1. **Discovery**: Identify all TFM source files and count print() statements
2. **Prioritization**: Order files by importance and print() statement count
3. **Transformation**: Replace print() statements with logger calls
4. **Verification**: Ensure migrated files compile successfully
5. **Tracking**: Update progress documentation

### Migration Scope

**In Scope:**
- All files in `src/` directory matching pattern `tfm_*.py`
- Both class-based and module-level print() statements
- All print() statement variations (f-strings, .format(), % formatting)

**Out of Scope:**
- TTK library files (ttk/ directory)
- Demo scripts (demo/ directory)
- Test files (test/ directory)
- Temporary files (temp/ directory)
- Files explicitly marked as no-logging-needed (e.g., tfm_directory_diff_viewer.py)

## Components and Interfaces

### File Discovery Component

**Purpose**: Identify all TFM source files that need migration

**Interface**:
```python
def discover_tfm_files(src_dir: str) -> List[FileInfo]:
    """
    Discover all TFM source files in the given directory.
    
    Args:
        src_dir: Path to the source directory
        
    Returns:
        List of FileInfo objects containing file path and metadata
    """
    pass

class FileInfo:
    path: str
    print_count: int
    migration_status: str  # 'completed', 'in-progress', 'not-started'
    priority: int
```

**Behavior**:
- Scans src/ directory for tfm_*.py files
- Excludes TTK library files
- Counts print() statements in each file
- Determines migration status by checking for logger usage
- Assigns priority based on file importance and print() count

### Print Statement Analyzer

**Purpose**: Analyze print() statements to determine appropriate log level

**Interface**:
```python
def analyze_print_statement(statement: str, context: str) -> LogLevel:
    """
    Analyze a print statement to determine appropriate log level.
    
    Args:
        statement: The print() statement content
        context: Surrounding code context (for exception handling detection)
        
    Returns:
        LogLevel enum (ERROR, WARNING, INFO, DEBUG)
    """
    pass

class LogLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
```

**Categorization Rules**:
- **ERROR**: Message contains "error", "failed", "exception", or is in except block
- **WARNING**: Message contains "warning", "warn", "deprecated", "potential"
- **INFO**: Default for general messages, status updates, user actions
- **DEBUG**: Message contains "debug", "trace", or detailed diagnostic info

### Code Transformer

**Purpose**: Transform print() statements to logger calls

**Interface**:
```python
def transform_file(file_path: str) -> TransformResult:
    """
    Transform all print() statements in a file to logger calls.
    
    Args:
        file_path: Path to the file to transform
        
    Returns:
        TransformResult with success status and details
    """
    pass

class TransformResult:
    success: bool
    statements_replaced: int
    errors: List[str]
    logger_name: str
```

**Transformation Pattern**:

For class-based code:
```python
# Before
class MyComponent:
    def __init__(self):
        pass
    
    def some_method(self):
        print(f"Error: {msg}")
        if self.logger:
            self.logger.info("Status")

# After
from tfm_log_manager import getLogger

class MyComponent:
    def __init__(self):
        self.logger = getLogger("MyComp")
    
    def some_method(self):
        self.logger.error(f"Error: {msg}")
        self.logger.info("Status")
```

For module-level code:
```python
# Before
print("Module starting")

def some_function():
    print("Function called")

# After
from tfm_log_manager import getLogger

logger = getLogger("ModuleName")
logger.info("Module starting")

def some_function():
    logger.info("Function called")
```

### Compilation Verifier

**Purpose**: Verify that transformed files compile successfully

**Interface**:
```python
def verify_compilation(file_path: str) -> CompilationResult:
    """
    Verify that a file compiles without errors.
    
    Args:
        file_path: Path to the file to verify
        
    Returns:
        CompilationResult with success status and any errors
    """
    pass

class CompilationResult:
    success: bool
    errors: List[CompilationError]
    
class CompilationError:
    line: int
    message: str
```

**Verification Method**:
- Use Python's `ast.parse()` to check syntax
- Use `py_compile.compile()` for bytecode compilation
- Use getDiagnostics tool for IDE-level verification

### Progress Tracker

**Purpose**: Track and report migration progress

**Interface**:
```python
def update_progress(file_path: str, result: TransformResult) -> None:
    """
    Update the progress document with migration results.
    
    Args:
        file_path: Path to the migrated file
        result: Transformation result
    """
    pass

def get_progress_summary() -> ProgressSummary:
    """
    Get a summary of migration progress.
    
    Returns:
        ProgressSummary with statistics
    """
    pass

class ProgressSummary:
    total_files: int
    completed_files: int
    remaining_files: int
    total_statements_replaced: int
    completion_percentage: float
```

## Data Models

### File Migration State

```python
class FileMigrationState:
    """Represents the migration state of a single file."""
    
    file_path: str
    original_print_count: int
    migration_status: str  # 'completed', 'in-progress', 'not-started', 'failed'
    logger_name: Optional[str]
    statements_replaced: int
    compilation_status: bool
    errors: List[str]
    timestamp: datetime
```

### Migration Configuration

```python
class MigrationConfig:
    """Configuration for the migration process."""
    
    src_directory: str = "src/"
    file_pattern: str = "tfm_*.py"
    exclude_patterns: List[str] = ["ttk/"]
    progress_file: str = "temp/LOGGING_MIGRATION_PROGRESS.md"
    verify_compilation: bool = True
    stop_on_error: bool = True
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Complete File Discovery

*For any* source directory containing TFM files, the discovery process should identify all and only files matching the pattern `tfm_*.py` in the `src/` directory, excluding TTK library files.

**Validates: Requirements 1.1, 1.2**

### Property 2: Accurate Print Statement Counting

*For any* Python file, the count of print() statements should match the actual number of print() function calls in the file, excluding those in comments or string literals.

**Validates: Requirements 1.4**

### Property 3: Complete Print Statement Replacement

*For any* file that undergoes migration, all print() statements should be replaced with logger method calls, with zero print() statements remaining (excluding those in comments or strings).

**Validates: Requirements 2.1**

### Property 4: Message Content Preservation

*For any* print() statement that is transformed, the message content and formatting should be identical before and after transformation, only the function call should change.

**Validates: Requirements 2.5, 7.1, 7.3**

### Property 5: Correct Log Level Categorization

*For any* message containing error indicators (like "error", "failed", "exception"), the transformation should use `logger.error()`, and similarly for warning and info messages.

**Validates: Requirements 2.2, 2.3, 2.4, 4.1, 4.2, 4.3**

### Property 6: Logger Initialization Presence

*For any* class that uses logging, the class should have `self.logger = getLogger("ComponentName")` in its `__init__` method and the import statement at module level.

**Validates: Requirements 3.1, 3.2**

### Property 7: No Duplicate Imports

*For any* migrated file, there should be exactly one import statement for `getLogger` from `tfm_log_manager`, with no duplicates.

**Validates: Requirements 3.4**

### Property 8: Conditional Logger Check Removal

*For any* migrated file, there should be no remaining conditional checks like `if self.logger:` since the logger is always available.

**Validates: Requirements 2.6**

### Property 9: Successful Compilation

*For any* file that completes migration, the file should compile without syntax errors when checked with Python's ast module.

**Validates: Requirements 5.1**

### Property 10: Module-Level Logger Pattern

*For any* file with module-level print() statements, the migrated file should have a module-level logger initialized as `logger = getLogger("ModuleName")`.

**Validates: Requirements 6.1, 6.2**

### Property 11: Control Flow Preservation

*For any* file that undergoes migration, all conditional logic, loops, and control structures around logging statements should remain unchanged.

**Validates: Requirements 7.2, 7.4**

### Property 12: Comment Preservation

*For any* file that undergoes migration, all comments should remain in their original locations and content.

**Validates: Requirements 7.5**

### Property 13: Progress Tracking Accuracy

*For any* completed migration, the progress document should accurately reflect the number of files migrated and statements replaced.

**Validates: Requirements 8.2, 8.3, 8.5**

### Property 14: Exception Context Awareness

*For any* print() statement within an exception handler (except block), the transformation should use `logger.error()` as the default log level.

**Validates: Requirements 9.4**

### Property 15: File Parameter Removal

*For any* print() statement with a `file=` parameter, the transformation should remove the parameter since logger calls don't use it.

**Validates: Requirements 9.5**

## Error Handling

### Compilation Errors

**Strategy**: Stop migration of current file and report errors

**Handling**:
- Parse compilation errors to extract line numbers and messages
- Log errors to progress document
- Mark file as 'failed' in migration state
- Do not proceed to next file until current file is fixed
- Provide clear error messages to developer

### Transformation Errors

**Strategy**: Handle edge cases gracefully

**Edge Cases**:
1. **Lambda functions with print()**: Transform to use module-level logger
2. **Nested functions with print()**: Ensure logger is accessible in scope
3. **Complex f-strings**: Preserve all formatting including nested expressions
4. **Print with multiple arguments**: Convert to single f-string or concatenation
5. **Print with sep/end parameters**: Preserve formatting in logger call

**Example**:
```python
# Before
print("Value:", value, sep=", ", end="\\n\\n")

# After
self.logger.info(f"Value: {value}\\n")
```

### Partial Migration Handling

**Strategy**: Complete partial migrations consistently

**Handling**:
- Detect files with mixed print() and logger usage
- Complete migration of remaining print() statements
- Ensure logger initialization exists
- Verify consistent log level usage across file

### File Access Errors

**Strategy**: Report and skip problematic files

**Handling**:
- Catch file read/write errors
- Log error to progress document
- Mark file as 'failed' with error details
- Continue with next file
- Provide list of failed files at end

## Testing Strategy

### Unit Testing

Unit tests verify specific examples and edge cases:

1. **File Discovery Tests**
   - Test with directory containing only TFM files
   - Test with mixed TFM and TTK files
   - Test with no matching files
   - Test with nested directory structures

2. **Print Statement Analysis Tests**
   - Test error message detection
   - Test warning message detection
   - Test info message detection
   - Test messages in exception handlers
   - Test messages with complex formatting

3. **Transformation Tests**
   - Test simple print() replacement
   - Test print() with f-strings
   - Test print() with .format()
   - Test print() with % formatting
   - Test print() with multiple arguments
   - Test print() in lambda functions
   - Test print() in nested functions
   - Test module-level print() statements

4. **Compilation Verification Tests**
   - Test valid Python syntax
   - Test invalid Python syntax
   - Test files with syntax errors

5. **Progress Tracking Tests**
   - Test progress document creation
   - Test progress document updates
   - Test summary generation

### Property-Based Testing

Property tests verify universal properties across all inputs using a property-based testing library (Hypothesis for Python):

**Configuration**: Each property test should run minimum 100 iterations

**Test Implementation**:

1. **Property 1: Complete File Discovery**
   - Generate random directory structures with TFM and non-TFM files
   - Verify all and only TFM files are discovered
   - **Feature: logging-migration, Property 1: Complete File Discovery**

2. **Property 2: Accurate Print Statement Counting**
   - Generate random Python files with varying numbers of print() statements
   - Verify count matches actual print() calls
   - **Feature: logging-migration, Property 2: Accurate Print Statement Counting**

3. **Property 3: Complete Print Statement Replacement**
   - Generate random Python files with print() statements
   - Transform and verify zero print() statements remain
   - **Feature: logging-migration, Property 3: Complete Print Statement Replacement**

4. **Property 4: Message Content Preservation**
   - Generate random print() statements with various message formats
   - Transform and verify message content is identical
   - **Feature: logging-migration, Property 4: Message Content Preservation**

5. **Property 5: Correct Log Level Categorization**
   - Generate random messages with error/warning/info indicators
   - Verify correct logger method is used
   - **Feature: logging-migration, Property 5: Correct Log Level Categorization**

6. **Property 6: Logger Initialization Presence**
   - Generate random class definitions
   - Transform and verify logger initialization exists
   - **Feature: logging-migration, Property 6: Logger Initialization Presence**

7. **Property 7: No Duplicate Imports**
   - Generate random Python files, some with existing imports
   - Transform and verify exactly one getLogger import
   - **Feature: logging-migration, Property 7: No Duplicate Imports**

8. **Property 8: Conditional Logger Check Removal**
   - Generate random files with "if self.logger:" checks
   - Transform and verify no such checks remain
   - **Feature: logging-migration, Property 8: Conditional Logger Check Removal**

9. **Property 9: Successful Compilation**
   - Generate random valid Python files with print() statements
   - Transform and verify compilation succeeds
   - **Feature: logging-migration, Property 9: Successful Compilation**

10. **Property 10: Module-Level Logger Pattern**
    - Generate random files with module-level print() statements
    - Transform and verify module-level logger exists
    - **Feature: logging-migration, Property 10: Module-Level Logger Pattern**

11. **Property 11: Control Flow Preservation**
    - Generate random files with print() in if/while/for blocks
    - Transform and verify control structures unchanged
    - **Feature: logging-migration, Property 11: Control Flow Preservation**

12. **Property 12: Comment Preservation**
    - Generate random files with comments near print() statements
    - Transform and verify comments remain unchanged
    - **Feature: logging-migration, Property 12: Comment Preservation**

13. **Property 13: Progress Tracking Accuracy**
    - Perform random migrations
    - Verify progress document reflects actual state
    - **Feature: logging-migration, Property 13: Progress Tracking Accuracy**

14. **Property 14: Exception Context Awareness**
    - Generate random files with print() in except blocks
    - Transform and verify logger.error() is used
    - **Feature: logging-migration, Property 14: Exception Context Awareness**

15. **Property 15: File Parameter Removal**
    - Generate random print() statements with file= parameter
    - Transform and verify file= parameter is removed
    - **Feature: logging-migration, Property 15: File Parameter Removal**

### Integration Testing

Integration tests verify the end-to-end migration process:

1. **Full Migration Test**
   - Create test directory with sample TFM files
   - Run complete migration process
   - Verify all files migrated successfully
   - Verify progress document is accurate

2. **Partial Migration Test**
   - Create files with mixed print() and logger usage
   - Run migration
   - Verify complete and consistent migration

3. **Error Recovery Test**
   - Create files with syntax errors
   - Run migration
   - Verify error handling and reporting
   - Verify other files continue to be processed

### Manual Testing

Manual verification for real TFM files:

1. **Smoke Test**: Run TFM after migration and verify basic functionality
2. **Log Output Test**: Verify log messages appear correctly in log pane
3. **Visual Inspection**: Review a sample of migrated files for correctness
4. **Regression Test**: Verify no behavioral changes in application

## Migration Workflow

### Step-by-Step Process

1. **Initialize**
   - Load migration configuration
   - Create progress document if not exists
   - Initialize progress tracker

2. **Discover Files**
   - Scan src/ directory for tfm_*.py files
   - Count print() statements in each file
   - Determine migration status
   - Prioritize files

3. **For Each File (in priority order)**
   - Load file content
   - Analyze print() statements
   - Determine logger name
   - Transform print() to logger calls
   - Add logger initialization if needed
   - Add import statement if needed
   - Remove conditional logger checks
   - Verify compilation
   - If compilation fails: report error and stop
   - If compilation succeeds: save file and update progress
   - Move to next file

4. **Finalize**
   - Generate final progress summary
   - Report any failed files
   - Update documentation

### Prioritization Strategy

Files are prioritized by:

1. **Importance**: Core application files first (tfm_main.py)
2. **Print Count**: Files with more print() statements first
3. **Dependencies**: Files with fewer dependencies first

### Rollback Strategy

If migration causes issues:

1. **Git Revert**: Use git to revert to pre-migration state
2. **File-by-File**: Revert individual files if needed
3. **Backup**: Keep backup of original files during migration

## Logger Naming Conventions

### Naming Rules

1. **Descriptive**: Name should indicate the component's purpose
2. **Concise**: Keep names under 15 characters when possible
3. **PascalCase**: Use PascalCase for multi-word names
4. **Consistent**: Use consistent naming across related components

### Examples

- `Main` - tfm_main.py
- `FileOp` - tfm_file_operations.py
- `Archive` - tfm_archive.py
- `Cache` - tfm_cache_manager.py
- `UILayer` - tfm_ui_layer.py
- `ExtProg` - tfm_external_programs.py
- `ColorTest` - tfm_color_tester.py
- `Search` - tfm_search_dialog.py
- `Progress` - tfm_progress_manager.py
- `Menu` - tfm_menu_manager.py

## Implementation Notes

### AST-Based Transformation

The transformation should use Python's `ast` module for reliable code analysis and transformation:

```python
import ast

class PrintTransformer(ast.NodeTransformer):
    """Transform print() calls to logger calls."""
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            # Transform to logger call
            return self.create_logger_call(node)
        return node
    
    def create_logger_call(self, print_node):
        # Analyze message content
        # Determine log level
        # Create logger method call
        pass
```

### Regex-Based Fallback

For simple cases, regex patterns can be used:

```python
import re

# Pattern for simple print statements
PRINT_PATTERN = r'print\((.*?)\)'

# Pattern for conditional logger checks
LOGGER_CHECK_PATTERN = r'if\s+self\.logger:'
```

### File Backup

Before modifying any file:

```python
import shutil

def backup_file(file_path: str) -> str:
    """Create backup of file before modification."""
    backup_path = f"{file_path}.backup"
    shutil.copy2(file_path, backup_path)
    return backup_path
```

## Success Criteria

The migration is considered successful when:

1. ✅ All TFM source files have been migrated
2. ✅ Zero print() statements remain in TFM source files (excluding comments/strings)
3. ✅ All migrated files compile successfully
4. ✅ All property-based tests pass
5. ✅ TFM runs without errors after migration
6. ✅ Log messages appear correctly in log pane
7. ✅ Progress document shows 100% completion
8. ✅ Documentation is updated

## Future Enhancements

Potential improvements for future iterations:

1. **Automated Log Level Detection**: Use ML/NLP to better categorize messages
2. **Batch Processing**: Migrate multiple files in parallel
3. **Interactive Mode**: Allow developer to review and approve each transformation
4. **Undo/Redo**: Support for undoing individual file migrations
5. **Configuration File**: Allow customization of transformation rules
6. **IDE Integration**: Provide IDE plugin for one-click migration
