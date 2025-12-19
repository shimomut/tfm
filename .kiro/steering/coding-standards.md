---
inclusion: always
---

# TFM Python Coding Standards

## Overview

This document establishes Python coding standards for the TFM (TUI File Manager) project to ensure consistency, maintainability, and code quality.

---

## Import Best Practices

### Core Principles

#### 1. Always Check Existing Imports First
- **Before adding any import statement**, check if the module is already imported at the module level
- Avoid redundant imports that duplicate existing module-level imports
- This prevents unnecessary code duplication and maintains clean code

#### 2. Module-Level Imports Only
- **All imports should be at the top of the file** (module level)
- Never import modules within functions unless absolutely necessary for conditional imports
- This improves performance and makes dependencies explicit

#### 3. Import Order and Organization
- Standard library imports first
- Third-party imports second  
- Local/project imports last
- Separate each group with a blank line

### Common Mistakes to Avoid

#### ❌ Redundant Imports
```python
import os
import sys
from pathlib import Path

def some_function():
    import os  # BAD - os already imported at module level
    import sys  # BAD - sys already imported at module level
    return os.getcwd()
```

#### ❌ Function-Level Imports (Usually)
```python
def process_file():
    import json  # BAD - should be at module level
    import os    # BAD - should be at module level
    # ... function code
```

#### ✅ Correct Approach
```python
import json
import os
import sys
from pathlib import Path

def some_function():
    return os.getcwd()  # GOOD - uses module-level import

def process_file():
    data = json.loads(content)  # GOOD - uses module-level import
    return data
```

### When Function-Level Imports Are Acceptable

#### Conditional Imports
```python
def get_platform_specific_tool():
    if sys.platform == 'win32':
        import winsound  # OK - conditional import
        return winsound
    else:
        import subprocess  # OK - conditional import  
        return subprocess
```

#### Optional Dependencies
```python
def enhanced_feature():
    try:
        import optional_library  # OK - optional dependency
        return optional_library.do_something()
    except ImportError:
        return fallback_implementation()
```

### Pre-Implementation Checklist

Before adding any import statement:

1. **Check module-level imports** - Is this module already imported?
2. **Verify necessity** - Is this import actually needed?
3. **Consider placement** - Should this be at module level or is it truly conditional?
4. **Remove duplicates** - Are there any redundant imports to clean up?

---

## Exception Handling Standards

### Core Principles

#### 1. Specific Exception Handling
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

#### 2. Fallback Exception Handling
When catching all exceptions is necessary (e.g., for stability in UI operations):
- Use `except Exception as e:` instead of bare `except:`
- **Always log or print a warning/error message** with context
- Include the exception details when helpful for debugging

### Exception Handling Patterns

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

### Context-Specific Guidelines

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

### Logging Integration
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

---

## File Permissions Standards

### Core Principle

**Python files should NOT have executable permissions.** Always run Python scripts by explicitly invoking the Python interpreter.

### Rules

#### 1. Python Files Should Not Be Executable

Python files (`.py`) should be run using the Python interpreter explicitly, not as executable scripts.

##### ❌ Avoid - Making Python Files Executable
```bash
chmod +x script.py
./script.py  # Bad - relies on shebang and executable permission
```

##### ✅ Preferred - Explicit Python Interpreter
```bash
python3 script.py  # Good - explicit interpreter
```

#### 2. Shell Scripts Can Be Executable

Shell scripts (`.sh`) in the `tools/` directory can have executable permissions since they are designed to be run directly.

##### ✅ Acceptable - Executable Shell Scripts
```bash
chmod +x tools/script.sh
./tools/script.sh  # OK for shell scripts
```

#### 3. Main Entry Point

The main entry point `tfm.py` should NOT have executable permissions. Users should run it with:

```bash
python3 tfm.py
```

### Rationale

#### Why Not Make Python Files Executable?

1. **Explicit is better than implicit** - Clearly shows which Python version is being used
2. **Virtual environment compatibility** - Works correctly with activated virtual environments
3. **Cross-platform consistency** - Works the same on all platforms
4. **No shebang dependency** - Doesn't rely on shebang line being correct
5. **Standard Python practice** - Follows Python community conventions

### Examples

#### Demo Scripts
```bash
# ❌ Bad
chmod +x demo/demo_script.py
./demo/demo_script.py

# ✅ Good
python3 demo/demo_script.py
```

#### Test Scripts
```bash
# ❌ Bad
chmod +x test/test_feature.py
./test/test_feature.py

# ✅ Good
python3 test/test_feature.py
```

#### Main Application
```bash
# ❌ Bad
chmod +x tfm.py
./tfm.py

# ✅ Good
python3 tfm.py
```

---

## Code Review Checklist

When reviewing code changes:

### Imports
- [ ] Are any imports duplicating module-level imports?
- [ ] Are imports at the appropriate level?
- [ ] Are all imports actually used?
- [ ] Are imports properly grouped and ordered?

### Exception Handling
- [ ] Are bare `except:` clauses avoided?
- [ ] Are specific exception types caught when possible?
- [ ] Do broad exception handlers include error logging?
- [ ] Are error messages informative and include context?
- [ ] Is the error handling appropriate for the operation's criticality?

### File Permissions
- [ ] Are any Python files being made executable with `chmod +x`?
- [ ] Are Python files being run with explicit interpreter (`python3`)?
- [ ] Are shell scripts in `tools/` directory (if executable)?
- [ ] Is documentation showing correct execution method?

## Benefits

- **Performance** - Module-level imports are loaded once, not on every function call
- **Clarity** - Dependencies are explicit and visible at the top of the file
- **Maintainability** - Easy to see what modules a file depends on and how errors are handled
- **Debugging** - Import errors are caught early, specific error messages help identify issues quickly
- **Consistency** - All Python files are run the same way across the project
- **Reliability** - Proper exception handling prevents unexpected crashes
