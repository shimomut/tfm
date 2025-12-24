# Logging System Migration Guide

## Overview

This guide helps developers migrate from TFM's legacy `add_message()` logging to the new Python standard `logging` module-based system. The migration can be done incrementally, as both systems work side-by-side during the transition.

## Quick Start

### Before (Legacy)

```python
class FileOperations:
    def __init__(self, log_manager):
        self.log_manager = log_manager
    
    def copy_file(self, source, dest):
        self.log_manager.add_message(f"Copying {source} to {dest}", "USER")
        try:
            # ... copy operation ...
            self.log_manager.add_message("Copy completed", "USER")
        except Exception as e:
            self.log_manager.add_message(f"Copy failed: {e}", "ERROR")
```

### After (New System)

```python
class FileOperations:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.logger = log_manager.getLogger("FileOp")
    
    def copy_file(self, source, dest):
        self.logger.info(f"Copying {source} to {dest}")
        try:
            # ... copy operation ...
            self.logger.info("Copy completed")
        except Exception as e:
            self.logger.error(f"Copy failed: {e}")
```

## Migration Steps

### Step 1: Get a Logger

Add logger initialization to your class:

```python
class MyComponent:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        # Add this line
        self.logger = log_manager.getLogger("ComponentName")
```

Choose a descriptive logger name:
- **"Main"**: Main application
- **"FileOp"**: File operations
- **"DirDiff"**: Directory diff viewer
- **"Archive"**: Archive operations
- **"Search"**: Search operations
- **"YourComponent"**: Your component name

### Step 2: Replace add_message() Calls

Replace `add_message()` with appropriate log level methods:

| Legacy | New | Log Level |
|--------|-----|-----------|
| `add_message(msg, "USER")` | `logger.info(msg)` | INFO |
| `add_message(msg, "ERROR")` | `logger.error(msg)` | ERROR |
| `add_message(msg, "WARNING")` | `logger.warning(msg)` | WARNING |
| `add_message(msg, "DEBUG")` | `logger.debug(msg)` | DEBUG |
| `add_message(msg)` | `logger.info(msg)` | INFO |

### Step 3: Update Exception Handling

**Before:**
```python
try:
    risky_operation()
except Exception as e:
    self.log_manager.add_message(f"Error: {e}", "ERROR")
```

**After:**
```python
try:
    risky_operation()
except Exception as e:
    self.logger.error(f"Error: {e}")
    # Or with full traceback
    self.logger.exception("Operation failed")
```

### Step 4: Test Your Changes

Run your component and verify:
- Messages appear in the log pane
- Message formatting is correct
- Log levels are appropriate
- No errors or warnings

## Common Patterns

### Pattern 1: Simple Messages

**Before:**
```python
self.log_manager.add_message("Operation started")
self.log_manager.add_message("Operation completed")
```

**After:**
```python
self.logger.info("Operation started")
self.logger.info("Operation completed")
```

### Pattern 2: Formatted Messages

**Before:**
```python
self.log_manager.add_message(f"Processing {filename} ({i}/{total})")
```

**After:**
```python
self.logger.info(f"Processing {filename} ({i}/{total})")
```

### Pattern 3: Error Messages

**Before:**
```python
self.log_manager.add_message(f"Error: {error_msg}", "ERROR")
```

**After:**
```python
self.logger.error(f"Error: {error_msg}")
```

### Pattern 4: Warning Messages

**Before:**
```python
self.log_manager.add_message(f"Warning: {warning_msg}", "WARNING")
```

**After:**
```python
self.logger.warning(f"Warning: {warning_msg}")
```

### Pattern 5: Debug Messages

**Before:**
```python
if debug_mode:
    self.log_manager.add_message(f"Debug: {debug_info}", "DEBUG")
```

**After:**
```python
self.logger.debug(f"Debug: {debug_info}")
# Note: No need for if statement, level filtering handles this
```

### Pattern 6: Progress Updates

**Before:**
```python
for i, item in enumerate(items):
    self.log_manager.add_message(f"Processing {item} ({i+1}/{len(items)})")
```

**After:**
```python
for i, item in enumerate(items):
    self.logger.info(f"Processing {item} ({i+1}/{len(items)})")
```

### Pattern 7: Exception Logging

**Before:**
```python
try:
    operation()
except PermissionError as e:
    self.log_manager.add_message(f"Permission denied: {e}", "ERROR")
except FileNotFoundError as e:
    self.log_manager.add_message(f"File not found: {e}", "ERROR")
```

**After:**
```python
try:
    operation()
except PermissionError as e:
    self.logger.error(f"Permission denied: {e}")
except FileNotFoundError as e:
    self.logger.error(f"File not found: {e}")
```

## Real-World Examples

### Example 1: tfm_main.py

**Before:**
```python
class FileManager:
    def __init__(self, config):
        self.log_manager = LogManager(config)
        self.log_manager.add_message("TFM started", "USER")
    
    def quit(self):
        self.log_manager.add_message("TFM shutting down", "USER")
```

**After:**
```python
class FileManager:
    def __init__(self, config):
        self.log_manager = LogManager(config)
        self.logger = self.log_manager.getLogger("Main")
        self.logger.info("TFM started")
    
    def quit(self):
        self.logger.info("TFM shutting down")
```

### Example 2: tfm_file_operations.py

**Before:**
```python
def copy_file(self, source, dest):
    self.log_manager.add_message(f"Copying {source.name} to {dest}", "USER")
    try:
        shutil.copy2(source, dest)
        self.log_manager.add_message("Copy completed successfully", "USER")
    except PermissionError:
        self.log_manager.add_message("Permission denied", "ERROR")
    except Exception as e:
        self.log_manager.add_message(f"Copy failed: {e}", "ERROR")
```

**After:**
```python
def copy_file(self, source, dest):
    self.logger.info(f"Copying {source.name} to {dest}")
    try:
        shutil.copy2(source, dest)
        self.logger.info("Copy completed successfully")
    except PermissionError:
        self.logger.error("Permission denied")
    except Exception as e:
        self.logger.error(f"Copy failed: {e}")
```

### Example 3: tfm_archive.py

**Before:**
```python
def extract_archive(self, archive_path, dest_dir):
    self.log_manager.add_message(f"Extracting {archive_path.name}", "USER")
    try:
        # ... extraction logic ...
        self.log_manager.add_message("Extraction completed", "USER")
    except Exception as e:
        self.log_manager.add_message(f"Extraction failed: {e}", "ERROR")
```

**After:**
```python
def extract_archive(self, archive_path, dest_dir):
    self.logger.info(f"Extracting {archive_path.name}")
    try:
        # ... extraction logic ...
        self.logger.info("Extraction completed")
    except Exception as e:
        self.logger.error(f"Extraction failed: {e}")
```

## Log Level Guidelines

### When to Use Each Level

**DEBUG** - Detailed diagnostic information:
```python
self.logger.debug(f"Variable state: {variable}")
self.logger.debug(f"Function called with args: {args}")
self.logger.debug(f"Cache hit: {cache_key}")
```

**INFO** - General informational messages:
```python
self.logger.info("File operation started")
self.logger.info("Configuration loaded")
self.logger.info("Connection established")
```

**WARNING** - Warning messages for unexpected situations:
```python
self.logger.warning("Large file detected, may take time")
self.logger.warning("Deprecated feature used")
self.logger.warning("Disk space low")
```

**ERROR** - Error messages for failures:
```python
self.logger.error("Permission denied")
self.logger.error("File not found")
self.logger.error("Network connection failed")
```

**CRITICAL** - Critical errors requiring immediate attention:
```python
self.logger.critical("Disk full, cannot continue")
self.logger.critical("Database connection lost")
self.logger.critical("Configuration file corrupted")
```

## Backward Compatibility

### Using Both Systems

During migration, both systems work together:

```python
class MyComponent:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.logger = log_manager.getLogger("MyComponent")
    
    def operation(self):
        # Old code still works
        self.log_manager.add_message("Legacy message", "USER")
        
        # New code works too
        self.logger.info("New message")
```

### Gradual Migration

Migrate one component at a time:

1. Start with new components
2. Migrate high-traffic components
3. Migrate remaining components
4. Remove legacy calls when all code is migrated

## Testing Your Migration

### Verification Checklist

- [ ] Logger is initialized in `__init__`
- [ ] All `add_message()` calls replaced
- [ ] Appropriate log levels used
- [ ] Exception handling updated
- [ ] Messages appear in log pane
- [ ] Message formatting is correct
- [ ] No errors or warnings

### Test Cases

```python
def test_logging_migration():
    """Test that new logging works correctly."""
    log_manager = LogManager(config)
    logger = log_manager.getLogger("Test")
    
    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Verify messages appear
    messages = log_manager.get_messages()
    assert len(messages) > 0
```

## Common Issues

### Issue 1: Messages Not Appearing

**Problem:** Logger messages don't appear in log pane.

**Solution:** Check log level configuration:
```python
# Set level to DEBUG to see all messages
log_manager.set_default_level(logging.DEBUG)
```

### Issue 2: Wrong Message Format

**Problem:** Messages have unexpected format.

**Solution:** Verify you're using logger methods, not print():
```python
# Wrong
print("Message")

# Right
self.logger.info("Message")
```

### Issue 3: Logger Not Found

**Problem:** `AttributeError: 'MyComponent' object has no attribute 'logger'`

**Solution:** Initialize logger in `__init__`:
```python
def __init__(self, log_manager):
    self.log_manager = log_manager
    self.logger = log_manager.getLogger("MyComponent")
```

### Issue 4: Too Many Messages

**Problem:** Log pane fills up too quickly.

**Solution:** Use appropriate log levels:
```python
# Don't use INFO for every iteration
for item in large_list:
    self.logger.debug(f"Processing {item}")  # Use DEBUG

# Use INFO for summary
self.logger.info(f"Processed {len(large_list)} items")
```

## Best Practices

### 1. Use Descriptive Logger Names

```python
# Good
logger = log_manager.getLogger("FileOp")
logger = log_manager.getLogger("DirDiff")

# Bad
logger = log_manager.getLogger("log")
logger = log_manager.getLogger("x")
```

### 2. Choose Appropriate Log Levels

```python
# Good
self.logger.info("Operation completed")
self.logger.error("Operation failed")

# Bad
self.logger.debug("Operation completed")  # Too low
self.logger.critical("Minor warning")     # Too high
```

### 3. Write Clear Messages

```python
# Good
self.logger.info(f"Copied {source} to {dest}")
self.logger.error(f"Permission denied: {path}")

# Bad
self.logger.info("Done")
self.logger.error("Error")
```

### 4. Use Exception Logging

```python
# Good
try:
    operation()
except Exception as e:
    self.logger.exception("Operation failed")

# Bad
try:
    operation()
except Exception as e:
    self.logger.error(str(e))  # Loses traceback
```

### 5. Avoid Logging in Loops

```python
# Bad
for item in large_list:
    self.logger.info(f"Processing {item}")

# Good
self.logger.info(f"Processing {len(large_list)} items")
# ... process items ...
self.logger.info("Processing completed")
```

## Migration Timeline

### Phase 1: New Code (Immediate)
- All new code uses `getLogger()`
- No new `add_message()` calls

### Phase 2: High-Traffic Components (Week 1)
- Migrate `tfm_main.py`
- Migrate `tfm_file_operations.py`
- Migrate `tfm_directory_diff_viewer.py`

### Phase 3: Remaining Components (Week 2)
- Migrate `tfm_archive.py`
- Migrate other components
- Update tests

### Phase 4: Cleanup (Week 3)
- Remove unused `add_message()` calls
- Update documentation
- Final testing

## Getting Help

### Resources

- **Design Document**: `.kiro/specs/logging-system-refactor/design.md`
- **Requirements**: `.kiro/specs/logging-system-refactor/requirements.md`
- **Developer Guide**: `doc/dev/LOGGING_SYSTEM_REFACTOR_GUIDE.md`
- **Tests**: `test/test_*.py` (logging-related tests)

### Questions?

If you encounter issues during migration:

1. Check this guide for common patterns
2. Review the design document for architecture details
3. Look at migrated code for examples
4. Run tests to verify behavior

## Conclusion

Migrating to the new logging system is straightforward:

1. Get a logger with `getLogger()`
2. Replace `add_message()` with logger methods
3. Use appropriate log levels
4. Test your changes

The new system provides better structure, standard patterns, and more flexibility while maintaining all existing functionality.
