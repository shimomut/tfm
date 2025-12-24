# Logging Quick Reference

## Getting Started

### Initialize Logger

```python
class MyComponent:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.logger = log_manager.getLogger("ComponentName")
```

### Basic Logging

```python
self.logger.debug("Debug message")
self.logger.info("Info message")
self.logger.warning("Warning message")
self.logger.error("Error message")
self.logger.critical("Critical message")
```

## Common Patterns

### File Operations

```python
self.logger.info(f"Copying {source} to {dest}")
try:
    shutil.copy2(source, dest)
    self.logger.info("Copy completed successfully")
except PermissionError:
    self.logger.error("Permission denied")
except Exception as e:
    self.logger.error(f"Copy failed: {e}")
```

### Exception Logging

```python
try:
    risky_operation()
except Exception as e:
    self.logger.exception("Operation failed")  # Includes traceback
```

### Progress Updates

```python
self.logger.info(f"Processing {len(items)} items")
for i, item in enumerate(items):
    # Process item
    if i % 10 == 0:  # Log every 10 items
        self.logger.debug(f"Processed {i}/{len(items)}")
self.logger.info("Processing completed")
```

### Conditional Logging

```python
# No need for if statement - level filtering handles this
self.logger.debug(f"Variable state: {variable}")

# Only log if expensive to compute
if self.logger.isEnabledFor(logging.DEBUG):
    expensive_debug_info = compute_debug_info()
    self.logger.debug(f"Debug info: {expensive_debug_info}")
```

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Detailed diagnostic info | `logger.debug(f"Cache hit: {key}")` |
| INFO | General informational | `logger.info("Operation completed")` |
| WARNING | Unexpected situations | `logger.warning("Large file detected")` |
| ERROR | Error conditions | `logger.error("Permission denied")` |
| CRITICAL | Critical errors | `logger.critical("Disk full")` |

## Configuration

### Set Log Level

```python
# Global default
log_manager.set_default_level(logging.DEBUG)

# Per-logger
log_manager.set_logger_level("FileOp", logging.DEBUG)
```

### Configure Handlers

```python
log_manager.configure_handlers(
    log_pane_enabled=True,
    stream_output_enabled=True,
    remote_enabled=False
)
```

## Migration from Legacy

| Legacy | New |
|--------|-----|
| `add_message(msg, "USER")` | `logger.info(msg)` |
| `add_message(msg, "ERROR")` | `logger.error(msg)` |
| `add_message(msg, "WARNING")` | `logger.warning(msg)` |
| `add_message(msg, "DEBUG")` | `logger.debug(msg)` |

## Logger Names

Standard logger names in TFM:

- **"Main"**: Main application
- **"FileOp"**: File operations
- **"DirDiff"**: Directory diff viewer
- **"Archive"**: Archive operations
- **"Search"**: Search operations

## Best Practices

### DO

✅ Use descriptive logger names
```python
logger = log_manager.getLogger("FileOp")
```

✅ Choose appropriate log levels
```python
logger.info("Operation completed")
logger.error("Operation failed")
```

✅ Write clear messages
```python
logger.info(f"Copied {source} to {dest}")
```

✅ Use exception logging
```python
logger.exception("Operation failed")
```

### DON'T

❌ Use generic logger names
```python
logger = log_manager.getLogger("log")
```

❌ Use wrong log levels
```python
logger.debug("Operation completed")  # Too low
logger.critical("Minor warning")     # Too high
```

❌ Write vague messages
```python
logger.info("Done")
logger.error("Error")
```

❌ Log in tight loops
```python
for item in large_list:
    logger.info(f"Processing {item}")  # Too many messages
```

## Testing

### Basic Test

```python
def test_logging():
    log_manager = LogManager(config)
    logger = log_manager.getLogger("Test")
    
    logger.info("Test message")
    
    messages = log_manager.get_messages()
    assert any("Test message" in msg for msg in messages)
```

### Mock Logger

```python
from unittest.mock import Mock

def test_component():
    mock_logger = Mock()
    component = MyComponent(mock_logger)
    
    component.do_something()
    
    mock_logger.info.assert_called_once()
```

## Troubleshooting

### Messages Not Appearing

Check log level:
```python
log_manager.set_default_level(logging.DEBUG)
```

### Too Many Messages

Reduce verbosity:
```python
log_manager.set_default_level(logging.WARNING)
```

### Performance Issues

Check if logging in loops:
```python
# Bad
for item in items:
    logger.info(f"Processing {item}")

# Good
logger.info(f"Processing {len(items)} items")
```

## Remote Monitoring

### Enable

```python
log_manager.configure_handlers(remote_enabled=True)
```

### Connect

```bash
telnet localhost 9999
```

### Message Format

```json
{
    "timestamp": "14:23:45",
    "source": "FileOp",
    "level": "INFO",
    "message": "Operation completed"
}
```

## Advanced Features

### Thread Safety

```python
# Safe to use from multiple threads
def worker():
    logger = log_manager.getLogger("Worker")
    logger.info("Worker started")
```

### Handler Failure Isolation

```python
# If one handler fails, others continue
logger.info("This reaches all working handlers")
```

### Dynamic Reconfiguration

```python
# Change configuration at runtime
log_manager.configure_handlers(
    log_pane_enabled=False,
    stream_output_enabled=True
)
```

## Resources

- **Developer Guide**: `doc/dev/LOGGING_SYSTEM_REFACTOR.md`
- **Migration Guide**: `doc/dev/LOGGING_MIGRATION_GUIDE.md`
- **User Guide**: `doc/LOGGING_FEATURE.md`
- **Design Document**: `.kiro/specs/logging-system-refactor/design.md`
- **Requirements**: `.kiro/specs/logging-system-refactor/requirements.md`

## Examples

### Complete Component

```python
class FileOperations:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.logger = log_manager.getLogger("FileOp")
    
    def copy_file(self, source, dest):
        self.logger.info(f"Copying {source.name} to {dest}")
        try:
            shutil.copy2(source, dest)
            self.logger.info("Copy completed successfully")
        except PermissionError:
            self.logger.error("Permission denied")
            raise
        except Exception as e:
            self.logger.exception("Copy failed")
            raise
    
    def delete_file(self, path):
        self.logger.info(f"Deleting {path.name}")
        try:
            path.unlink()
            self.logger.info("Delete completed successfully")
        except FileNotFoundError:
            self.logger.warning("File not found")
        except Exception as e:
            self.logger.exception("Delete failed")
            raise
```

### Error Handling

```python
def process_files(self, files):
    self.logger.info(f"Processing {len(files)} files")
    
    success_count = 0
    error_count = 0
    
    for i, file in enumerate(files):
        try:
            self.process_file(file)
            success_count += 1
            
            if (i + 1) % 10 == 0:
                self.logger.debug(f"Processed {i + 1}/{len(files)}")
        
        except Exception as e:
            error_count += 1
            self.logger.error(f"Failed to process {file.name}: {e}")
    
    self.logger.info(
        f"Processing completed: {success_count} succeeded, "
        f"{error_count} failed"
    )
```

### Configuration Example

```python
from tfm_logging_handlers import LoggingConfig
import logging

config = LoggingConfig(
    log_pane_enabled=True,
    max_log_messages=1000,
    stream_output_enabled=None,  # Auto-detect
    remote_monitoring_enabled=False,
    default_log_level=logging.INFO,
    logger_levels={
        "FileOp": logging.DEBUG,
        "Archive": logging.WARNING
    }
)

log_manager = LogManager(config)
```
