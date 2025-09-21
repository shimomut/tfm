# Progress Manager System

## Overview

The Progress Manager System provides comprehensive progress tracking and display for long-running operations in TFM. It offers real-time progress updates, operation prioritization, and user-friendly progress visualization for file operations like copying, moving, deleting, and archive creation.

## Features

### Core Capabilities
- **Real-time Progress**: Live progress updates during operations
- **Multiple Operation Types**: Support for various file operations
- **Priority Management**: Handle multiple concurrent operations
- **Visual Progress Display**: Clear progress bars and status information
- **Cancellation Support**: User can cancel long-running operations

### Advanced Features
- **Throttled Updates**: Efficient progress updates to prevent UI flooding
- **Operation Queuing**: Manage multiple operations with priorities
- **Detailed Statistics**: File counts, sizes, and timing information
- **Error Tracking**: Track and report operation errors
- **Completion Callbacks**: Execute actions when operations complete

## Class Structure

### OperationType Enum
```python
class OperationType(Enum):
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    ARCHIVE_CREATE = "archive_create"
    ARCHIVE_EXTRACT = "archive_extract"
```

### ProgressManager Class
```python
class ProgressManager:
    def __init__()
    def start_operation(self, operation_type, total_items, description="")
    def update_progress(self, current_item, item_name="")
    def finish_operation(self, success=True, message="")
    def cancel_operation()
    def is_operation_active()
    def get_progress_info()
```

## Usage Examples

### Basic Progress Tracking
```python
progress_manager = ProgressManager()

# Start a copy operation
progress_manager.start_operation(
    OperationType.COPY, 
    total_items=100, 
    description="Copying files to backup"
)

# Update progress during operation
for i, file in enumerate(files):
    progress_manager.update_progress(i + 1, file.name)
    copy_file(file)

# Finish operation
progress_manager.finish_operation(success=True, message="Copy completed")
```

### Archive Creation Progress
```python
# Start archive creation
progress_manager.start_operation(
    OperationType.ARCHIVE_CREATE,
    total_items=len(files_to_archive),
    description="Creating backup.tar.gz"
)

# Update progress for each file
for i, file in enumerate(files_to_archive):
    progress_manager.update_progress(i + 1, file.name)
    add_to_archive(file)

# Complete operation
progress_manager.finish_operation(success=True, message="Archive created successfully")
```

### Delete Operation with Error Handling
```python
progress_manager.start_operation(
    OperationType.DELETE,
    total_items=len(files_to_delete),
    description="Deleting selected files"
)

errors = []
for i, file in enumerate(files_to_delete):
    try:
        progress_manager.update_progress(i + 1, file.name)
        delete_file(file)
    except Exception as e:
        errors.append(f"Failed to delete {file.name}: {e}")

# Finish with error information
success = len(errors) == 0
message = "Deletion completed" if success else f"Completed with {len(errors)} errors"
progress_manager.finish_operation(success=success, message=message)
```

## Progress Display Features

### Visual Progress Bar
```
┌─────────────────────────────────────┐
│ Copying files to backup             │
│ ████████████████░░░░░░░░░░░░ 67%    │
│ Processing: document.pdf (45/67)    │
│ Elapsed: 00:02:15  ETA: 00:01:05   │
└─────────────────────────────────────┘
```

### Status Information
- **Operation Description**: Clear description of current operation
- **Progress Percentage**: Visual percentage completion
- **Current Item**: Name of file/item being processed
- **Item Counter**: Current item number and total count
- **Timing Information**: Elapsed time and estimated completion time

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.progress_manager = ProgressManager()

# Check for active operations in main loop
if self.progress_manager.is_operation_active():
    # Handle progress display and user input
    if key == 27:  # ESC key
        self.progress_manager.cancel_operation()
```

### File Operations Integration
```python
def copy_files_with_progress(self, source_files, destination):
    """Copy files with progress tracking"""
    self.progress_manager.start_operation(
        OperationType.COPY,
        len(source_files),
        f"Copying {len(source_files)} files"
    )
    
    for i, source_file in enumerate(source_files):
        if self.progress_manager.is_cancelled():
            break
            
        self.progress_manager.update_progress(i + 1, source_file.name)
        copy_file(source_file, destination)
    
    self.progress_manager.finish_operation()
```

## Progress Update Strategies

### Throttled Updates
```python
class ProgressManager:
    def __init__(self):
        self.last_update_time = 0
        self.update_threshold = 0.1  # Update at most every 100ms
    
    def update_progress(self, current_item, item_name=""):
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_threshold:
            self._do_update(current_item, item_name)
            self.last_update_time = current_time
```

### Batch Updates
```python
# For very fast operations, batch updates
batch_size = 10
for i, file in enumerate(files):
    process_file(file)
    
    # Update progress every 10 files
    if i % batch_size == 0 or i == len(files) - 1:
        progress_manager.update_progress(i + 1, file.name)
```

## Operation Management

### Priority System
```python
class OperationPriority:
    HIGH = 1      # User-initiated operations
    NORMAL = 2    # Regular file operations
    LOW = 3       # Background operations
    
# Start high-priority operation
progress_manager.start_operation(
    OperationType.COPY,
    total_items=files_count,
    priority=OperationPriority.HIGH
)
```

### Cancellation Handling
```python
def long_running_operation(self):
    """Example of cancellation-aware operation"""
    for i, item in enumerate(items):
        # Check for cancellation before each item
        if self.progress_manager.is_cancelled():
            self.cleanup_partial_operation()
            return False
        
        self.progress_manager.update_progress(i + 1, item.name)
        process_item(item)
    
    return True
```

## Advanced Features

### Time Estimation
```python
class ProgressManager:
    def calculate_eta(self):
        """Calculate estimated time to completion"""
        if self.current_item <= 0:
            return None
        
        elapsed = time.time() - self.start_time
        rate = self.current_item / elapsed
        remaining_items = self.total_items - self.current_item
        
        return remaining_items / rate if rate > 0 else None
```

### Statistics Tracking
```python
def get_operation_stats(self):
    """Get detailed operation statistics"""
    return {
        'operation_type': self.operation_type,
        'total_items': self.total_items,
        'completed_items': self.current_item,
        'elapsed_time': time.time() - self.start_time,
        'estimated_completion': self.calculate_eta(),
        'items_per_second': self.calculate_rate(),
        'success_rate': self.calculate_success_rate()
    }
```

### Error Reporting
```python
class ProgressManager:
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def report_error(self, error_message, item_name=None):
        """Report an error during operation"""
        error_info = {
            'message': error_message,
            'item': item_name,
            'timestamp': time.time()
        }
        self.errors.append(error_info)
    
    def get_error_summary(self):
        """Get summary of errors encountered"""
        return {
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'recent_errors': self.errors[-5:]  # Last 5 errors
        }
```

## Performance Optimization

### Efficient Updates
- **Throttled Rendering**: Limit UI updates to prevent performance issues
- **Batch Processing**: Group multiple updates for efficiency
- **Minimal Redraws**: Only redraw changed portions of progress display
- **Background Processing**: Non-blocking progress updates

### Memory Management
```python
class ProgressManager:
    def cleanup_completed_operation(self):
        """Clean up resources after operation completion"""
        self.operation_type = None
        self.current_item = 0
        self.total_items = 0
        self.errors.clear()
        self.warnings.clear()
```

## Error Handling

### Operation Failures
```python
def handle_operation_error(self, error, item_name=None):
    """Handle errors during operations"""
    self.report_error(str(error), item_name)
    
    # Decide whether to continue or abort
    if self.is_critical_error(error):
        self.finish_operation(success=False, message=f"Operation failed: {error}")
        return False
    else:
        # Continue with next item
        return True
```

### Recovery Mechanisms
```python
def resume_operation(self, from_item=None):
    """Resume a previously interrupted operation"""
    if from_item is not None:
        self.current_item = from_item
    
    # Continue from where we left off
    remaining_items = self.total_items - self.current_item
    self.description = f"Resuming operation ({remaining_items} items remaining)"
```

## Common Use Cases

### File Copy Operations
```python
def copy_files_with_progress(self, files, destination):
    self.progress_manager.start_operation(
        OperationType.COPY,
        len(files),
        f"Copying {len(files)} files to {destination.name}"
    )
    
    copied_count = 0
    for i, file in enumerate(files):
        try:
            self.progress_manager.update_progress(i + 1, file.name)
            shutil.copy2(file, destination / file.name)
            copied_count += 1
        except Exception as e:
            self.progress_manager.report_error(f"Failed to copy {file.name}: {e}")
    
    success = copied_count == len(files)
    message = f"Copied {copied_count}/{len(files)} files"
    self.progress_manager.finish_operation(success=success, message=message)
```

### Archive Creation
```python
def create_archive_with_progress(self, files, archive_path):
    self.progress_manager.start_operation(
        OperationType.ARCHIVE_CREATE,
        len(files),
        f"Creating archive {archive_path.name}"
    )
    
    with tarfile.open(archive_path, 'w:gz') as tar:
        for i, file in enumerate(files):
            self.progress_manager.update_progress(i + 1, file.name)
            tar.add(file, arcname=file.name)
    
    self.progress_manager.finish_operation(
        success=True,
        message=f"Archive {archive_path.name} created successfully"
    )
```

## Benefits

### User Experience
- **Visual Feedback**: Clear indication of operation progress
- **Time Awareness**: Estimated completion times for planning
- **Cancellation Control**: Ability to cancel long operations
- **Error Visibility**: Clear reporting of operation issues

### System Performance
- **Efficient Updates**: Throttled updates prevent UI flooding
- **Resource Management**: Proper cleanup of operation resources
- **Background Processing**: Non-blocking operation execution
- **Memory Efficiency**: Minimal memory usage for progress tracking

### Developer Experience
- **Simple API**: Easy to integrate progress tracking
- **Flexible Configuration**: Customizable for different operation types
- **Error Handling**: Built-in error reporting and handling
- **Comprehensive Tracking**: Detailed operation statistics

## Future Enhancements

### Potential Improvements
- **Multiple Operations**: Support for concurrent operations
- **Operation History**: Track and display operation history
- **Progress Persistence**: Save and restore operation state
- **Custom Callbacks**: User-defined completion callbacks
- **Progress Notifications**: System notifications for completion

### Advanced Features
- **Network Progress**: Progress tracking for network operations
- **Bandwidth Monitoring**: Track transfer speeds and bandwidth usage
- **Operation Scheduling**: Schedule operations for later execution
- **Progress Analytics**: Detailed analytics and reporting
- **Remote Progress**: Progress tracking for remote operations

## Testing

### Test Coverage
- **Progress Updates**: Verify correct progress calculation
- **Cancellation**: Test operation cancellation functionality
- **Error Handling**: Test error reporting and recovery
- **Performance**: Test with large numbers of files
- **Integration**: Test integration with file operations

### Test Scenarios
- **Basic Operations**: Simple progress tracking scenarios
- **Error Conditions**: Operations with various error conditions
- **Cancellation**: User cancellation at different stages
- **Performance**: Large-scale operations with many files
- **Edge Cases**: Empty operations, single file operations

## Conclusion

The Progress Manager System provides essential progress tracking functionality for TFM, offering users clear visibility into long-running operations while maintaining excellent performance and system responsiveness. Its comprehensive feature set, efficient implementation, and easy integration make it a crucial component for professional file management operations.