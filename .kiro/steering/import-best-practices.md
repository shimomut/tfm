# Python Import Best Practices

## Core Principles

### 1. Always Check Existing Imports First
- **Before adding any import statement**, check if the module is already imported at the module level
- Avoid redundant imports that duplicate existing module-level imports
- This prevents unnecessary code duplication and maintains clean code

### 2. Module-Level Imports Only
- **All imports should be at the top of the file** (module level)
- Never import modules within functions unless absolutely necessary for conditional imports
- This improves performance and makes dependencies explicit

### 3. Import Order and Organization
- Standard library imports first
- Third-party imports second  
- Local/project imports last
- Separate each group with a blank line

## Common Mistakes to Avoid

### ❌ Redundant Imports
```python
import os
import sys
from pathlib import Path

def some_function():
    import os  # BAD - os already imported at module level
    import sys  # BAD - sys already imported at module level
    return os.getcwd()
```

### ❌ Function-Level Imports (Usually)
```python
def process_file():
    import json  # BAD - should be at module level
    import os    # BAD - should be at module level
    # ... function code
```

### ✅ Correct Approach
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

## When Function-Level Imports Are Acceptable

### Conditional Imports
```python
def get_platform_specific_tool():
    if sys.platform == 'win32':
        import winsound  # OK - conditional import
        return winsound
    else:
        import subprocess  # OK - conditional import  
        return subprocess
```

### Optional Dependencies
```python
def enhanced_feature():
    try:
        import optional_library  # OK - optional dependency
        return optional_library.do_something()
    except ImportError:
        return fallback_implementation()
```

## Pre-Implementation Checklist

Before adding any import statement:

1. **Check module-level imports** - Is this module already imported?
2. **Verify necessity** - Is this import actually needed?
3. **Consider placement** - Should this be at module level or is it truly conditional?
4. **Remove duplicates** - Are there any redundant imports to clean up?

## Code Review Guidelines

When reviewing code:

- [ ] **Check for redundant imports** - Are any imports duplicating module-level imports?
- [ ] **Verify import placement** - Are imports at the appropriate level?
- [ ] **Look for unused imports** - Are all imports actually used?
- [ ] **Check import organization** - Are imports properly grouped and ordered?

## Examples of Good Import Practices

### Simple Module
```python
import os
import sys
from pathlib import Path

def main():
    current_dir = Path.cwd()
    home_dir = Path.home()
    return str(current_dir), str(home_dir)
```

### Module with Conditional Imports
```python
import os
import sys
from pathlib import Path

# Platform-specific imports at module level when possible
if sys.platform == 'win32':
    import msvcrt
else:
    import termios

def get_char():
    if sys.platform == 'win32':
        return msvcrt.getch()
    else:
        # Use termios for Unix-like systems
        return sys.stdin.read(1)
```

### Module with Optional Dependencies
```python
import os
import sys
from pathlib import Path

# Try to import optional dependencies at module level
try:
    import colorama
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

def print_colored(text, color='white'):
    if HAS_COLORAMA:
        # Use colorama if available
        print(getattr(colorama.Fore, color.upper()) + text + colorama.Style.RESET_ALL)
    else:
        # Fallback to plain text
        print(text)
```

## Benefits of Following These Practices

1. **Performance** - Module-level imports are loaded once, not on every function call
2. **Clarity** - Dependencies are explicit and visible at the top of the file
3. **Maintainability** - Easy to see what modules a file depends on
4. **Debugging** - Import errors are caught early, not buried in function calls
5. **Code Quality** - Cleaner, more professional code structure

## Tools and IDE Support

Most IDEs and linters will help identify:
- Unused imports
- Import order issues
- Redundant imports

Configure your development environment to highlight these issues automatically.