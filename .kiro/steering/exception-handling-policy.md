# TFM Exception Handling Policy

## Overview

This document establishes the exception handling standards for the TFM (TUI File Manager) project to improve debugging, maintainability, and error reporting.

## Core Principles

### 1. Specific Exception Handling
- **Always catch specific exception types** when possible rather than using bare `except:` clauses
- This allows for targeted error handling and better debugging information
- Common specific exceptions to catch:
  - `FileNotFoundError` - for file operations
  - `PermissionError` - for access-related issues
  - `OSError` - for system-level operations
  - `ValueError` - for invalid values
  - `KeyError` - for dictionary access
  - `IndexError` - for list/array access
  - `curses.error` - for curses-related operations

### 2. Fallback Exception Handling
When catching all exceptions is necessary (e.g., for stability in UI operations):
- Use `except Exception as e:` instead of bare `except:`
- **Always log or print a warning/error message** with context
- Include the exception details when helpful for debugging

### 3. Exception Handling Patterns

#### ✅ Preferred Pattern - Specific Exceptions
```python
try:
    file_path.stat()
except FileNotFoundError:
    print(f"File not found: {file_path}")
    return None
except PermissionError:
    print(f"Permission denied accessing: {file_path}")
    return None
```

#### ✅ Acceptable Pattern - Broad Exception with Logging
```python
try:
    complex_ui_operation()
except Exception as e:
    print(f"Warning: UI operation failed: {e}")
    # Continue with fallback behavior
```

#### ❌ Avoid - Silent Bare Except
```python
try:
    some_operation()
except:
    pass  # Silent failure - hard to debug
```

#### ✅ Better - Logged Bare Except (when necessary)
```python
try:
    some_operation()
except Exception as e:
    print(f"Warning: Operation failed: {e}")
    # or use logging if available
```

### 4. Context-Specific Guidelines

#### File Operations
```python
try:
    with open(file_path, 'r') as f:
        content = f.read()
except FileNotFoundError:
    print(f"File not found: {file_path}")
except PermissionError:
    print(f"Permission denied: {file_path}")
except UnicodeDecodeError:
    print(f"Cannot decode file as text: {file_path}")
except OSError as e:
    print(f"System error reading {file_path}: {e}")
```

#### Curses Operations
```python
try:
    stdscr.addstr(y, x, text, color)
except curses.error as e:
    print(f"Warning: Could not draw text at ({y}, {x}): {e}")
    # Continue without drawing
```

#### Network Operations
```python
try:
    client_socket.send(data)
except ConnectionError:
    print("Connection lost to remote client")
    self.remove_client(client_socket)
except OSError as e:
    print(f"Network error: {e}")
```

### 5. Logging Integration
- When the `LogManager` is available, prefer logging over print statements
- Use appropriate log levels:
  - `ERROR` for serious issues that affect functionality
  - `WARNING` for recoverable issues
  - `INFO` for informational messages

```python
try:
    risky_operation()
except SpecificError as e:
    self.log_manager.add_message(f"Operation failed: {e}", "ERROR")
```

### 6. Migration Strategy
When updating existing code:
1. Identify bare `except:` clauses
2. Determine what specific exceptions are likely
3. Replace with specific exception handling
4. Add appropriate error messages
5. Test to ensure the error handling works as expected

### 7. Testing Exception Handling
- Include tests that verify exception handling behavior
- Ensure error messages are helpful and informative
- Test both expected and unexpected error conditions

## Implementation Priority

1. **High Priority**: File operations, network operations, critical UI components
2. **Medium Priority**: Configuration loading, state management
3. **Low Priority**: Non-critical UI drawing operations (where silent failure is acceptable)

## Benefits

- **Improved Debugging**: Specific error messages help identify issues quickly
- **Better User Experience**: Informative error messages instead of silent failures
- **Maintainability**: Clear error handling makes code easier to understand and modify
- **Reliability**: Proper exception handling prevents unexpected crashes

## Module Import Guidelines

### 8. Import Modules at Module Level
- **Always import modules at the top of the file** (module level), not within functions or methods
- This improves performance by avoiding repeated imports during function calls
- Makes dependencies clear and explicit

#### ❌ Avoid - Imports Within Functions
```python
def some_function():
    import time  # Bad - imports on every function call
    import os
    time.sleep(1)
```

#### ✅ Preferred - Module Level Imports
```python
import time
import os

def some_function():
    time.sleep(1)  # Good - module already imported
```

#### Exception Handling Context
When fixing exception handling, also check for and fix any imports within functions:
```python
# Before
def handle_client(self):
    try:
        import time
        time.sleep(1)
    except Exception:
        pass

# After - move import to module level
import time  # At top of file

def handle_client(self):
    try:
        time.sleep(1)
    except (OSError, ConnectionError) as e:
        print(f"Client handling error: {e}")
```

## Review Checklist

When reviewing code changes:
- [ ] Are bare `except:` clauses avoided?
- [ ] Are specific exception types caught when possible?
- [ ] Do broad exception handlers include error logging?
- [ ] Are error messages informative and include context?
- [ ] Is the error handling appropriate for the operation's criticality?
- [ ] Are all module imports at the module level (not within functions)?
- [ ] Are there any redundant imports that can be removed?