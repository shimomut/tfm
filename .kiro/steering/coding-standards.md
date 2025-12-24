---
inclusion: always
---

# TFM Python Coding Standards

## Import Best Practices

**Before adding any import statement**, check if the module is already imported at the module level to avoid redundant imports.

## Logging Standards

### Mandatory Logger Usage

**All TFM source files MUST use the unified logging system.** Direct use of `print()` statements is prohibited in production code.

### Logger Initialization Pattern

**For class-based code:**

```python
# At module level
from tfm_log_manager import getLogger

class MyComponent:
    def __init__(self, ...):
        # Initialize logger with descriptive component name
        self.logger = getLogger("ComponentName")
        # ... rest of initialization
    
    def some_method(self):
        # Use logger instead of print()
        self.logger.error(f"Error: {msg}")
        self.logger.warning(f"Warning: {msg}")
        self.logger.info(f"Info: {msg}")
```

**For module-level code:**

```python
# At module level
from tfm_log_manager import getLogger

logger = getLogger("ModuleName")

# Use logger for module-level messages
logger.info("Module starting")

def some_function():
    logger.info("Function called")
```

### Logger Naming Conventions

- **Descriptive**: Name should clearly indicate the component's purpose
- **Concise**: Keep names under 15 characters when possible
- **PascalCase**: Use PascalCase for multi-word names (e.g., "FileOp", "UILayer")
- **Consistent**: Use consistent naming across related components

Examples: "Main", "FileOp", "Archive", "Cache", "UILayer", "ExtProg", "ColorTest"

### Log Level Guidelines

Choose the appropriate log level based on message severity:

- **ERROR**: Operation failures, data loss, critical issues, exceptions
- **WARNING**: Potential issues, degraded functionality, user should be aware
- **INFO**: Normal operation, user actions, status updates (most common)
- **DEBUG**: Detailed diagnostic information (rarely used in TFM)

### Migration Pattern Examples

**Before migration:**
```python
class FileManager:
    def copy_file(self, src, dst):
        print(f"Copying {src} to {dst}")
        try:
            shutil.copy2(src, dst)
            print("Copy completed successfully")
        except Exception as e:
            print(f"Error: Copy failed: {e}")
```

**After migration:**
```python
from tfm_log_manager import getLogger

class FileManager:
    def __init__(self):
        self.logger = getLogger("FileOp")
    
    def copy_file(self, src, dst):
        self.logger.info(f"Copying {src} to {dst}")
        try:
            shutil.copy2(src, dst)
            self.logger.info("Copy completed successfully")
        except Exception as e:
            self.logger.error(f"Copy failed: {e}")
```

### Common Mistakes to Avoid

❌ **Don't use print() statements:**
```python
print("Operation completed")  # WRONG
```

✅ **Do use logger:**
```python
self.logger.info("Operation completed")  # CORRECT
```

❌ **Don't keep conditional logger checks:**
```python
if self.logger:  # WRONG - logger is always available
    self.logger.info("Message")
```

✅ **Do use logger directly:**
```python
self.logger.info("Message")  # CORRECT
```

❌ **Don't change message content during migration:**
```python
# Before
print(f"Processing {filename}")
# After - WRONG
self.logger.info(f"Now processing file: {filename}")  # Changed message!
```

✅ **Do preserve exact message content:**
```python
# Before
print(f"Processing {filename}")
# After - CORRECT
self.logger.info(f"Processing {filename}")
```

## Exception Handling Standards

- **Catch specific exception types** when possible rather than bare `except:` clauses
- When catching all exceptions is necessary, use `except Exception as e:` and **always log an error message** with context
- **Use logger.error() in exception handlers** to ensure errors are properly logged

Example:
```python
try:
    risky_operation()
except FileNotFoundError as e:
    self.logger.error(f"File not found: {e}")
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
```

## File Permissions Standards

**Python files should NOT have executable permissions.** Always run Python scripts by explicitly invoking the Python interpreter:

```bash
# ✅ Correct
python3 script.py

# ❌ Avoid
chmod +x script.py
./script.py
```

Shell scripts in `tools/` directory can have executable permissions.

## References

- **Logging Migration Guide**: `doc/dev/LOGGING_MIGRATION_GUIDE.md`
- **Logging Feature Documentation**: `doc/LOGGING_FEATURE.md`
- **Log Manager Implementation**: `src/tfm_log_manager.py`
