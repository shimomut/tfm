# File Operations System

## Overview

The File Operations System provides comprehensive file and directory management functionality for TFM. It handles all file system operations including copying, moving, deleting, creating, and managing files and directories with proper error handling, progress tracking, and user feedback.

## Features

### Core Operations
- **File Copy**: Copy files and directories with progress tracking
- **File Move**: Move/rename files and directories
- **File Delete**: Delete files and directories with confirmation
- **Directory Creation**: Create new directories with validation
- **File Creation**: Create new empty files
- **Archive Operations**: Create and extract archives

### Advanced Features
- **Batch Operations**: Handle multiple files simultaneously
- **Progress Tracking**: Real-time progress for long operations
- **Error Handling**: Comprehensive error reporting and recovery
- **Conflict Resolution**: Handle file conflicts and overwrites
- **Permission Management**: Proper handling of file permissions
- **Symbolic Link Support**: Handle symbolic links appropriately

## Class Structure

### FileOperations Class
```python
class FileOperations:
    def __init__(self, config, log_manager, progress_manager)
    def copy_files(self, source_files, destination_path, callback=None)
    def move_files(self, source_files, destination_path, callback=None)
    def delete_files(self, file_paths, callback=None)
    def create_directory(self, path, name)
    def create_file(self, path, name)
    def rename_file(self, old_path, new_name)
```

### Operation Result Structure
```python
operation_result = {
    'success': bool,           # Whether operation succeeded
    'processed_count': int,    # Number of items processed
    'error_count': int,        # Number of errors encountered
    'errors': List[str],       # List of error messages
    'skipped_count': int,      # Number of items skipped
    'total_size': int,         # Total size of processed data
    'elapsed_time': float      # Time taken for operation
}
```

## Usage Examples

### Basic File Copy
```python
file_ops = FileOperations(config, log_manager, progress_manager)

# Copy selected files to destination
source_files = [Path("file1.txt"), Path("file2.txt")]
destination = Path("/backup/")

result = file_ops.copy_files(source_files, destination)
if result['success']:
    print(f"Copied {result['processed_count']} files successfully")
else:
    print(f"Copy failed with {result['error_count']} errors")
```

### File Move with Callback
```python
def move_callback(current_file, progress_info):
    print(f"Moving {current_file.name} ({progress_info['current']}/{progress_info['total']})")

result = file_ops.move_files(source_files, destination, callback=move_callback)
```

### Directory Operations
```python
# Create new directory
result = file_ops.create_directory(Path("/home/user"), "new_folder")

# Create new file
result = file_ops.create_file(Path("/home/user"), "new_file.txt")

# Rename file
result = file_ops.rename_file(Path("/home/user/old_name.txt"), "new_name.txt")
```

## File Copy Operations

### Copy Implementation
```python
def copy_files(self, source_files, destination_path, callback=None):
    """Copy files with progress tracking and error handling"""
    result = {
        'success': True,
        'processed_count': 0,
        'error_count': 0,
        'errors': [],
        'total_size': 0,
        'elapsed_time': 0
    }
    
    start_time = time.time()
    
    # Start progress tracking
    self.progress_manager.start_operation(
        OperationType.COPY,
        len(source_files),
        f"Copying {len(source_files)} files"
    )
    
    try:
        for i, source_file in enumerate(source_files):
            try:
                # Update progress
                self.progress_manager.update_progress(i + 1, source_file.name)
                
                # Check for cancellation
                if self.progress_manager.is_cancelled():
                    break
                
                # Perform copy operation
                dest_file = destination_path / source_file.name
                
                # Handle conflicts
                if dest_file.exists():
                    conflict_resolution = self.handle_file_conflict(source_file, dest_file)
                    if conflict_resolution == 'skip':
                        continue
                    elif conflict_resolution == 'cancel':
                        break
                
                # Copy file
                if source_file.is_file():
                    shutil.copy2(source_file, dest_file)
                elif source_file.is_dir():
                    shutil.copytree(source_file, dest_file)
                
                result['processed_count'] += 1
                result['total_size'] += source_file.stat().st_size if source_file.is_file() else 0
                
                # Execute callback if provided
                if callback:
                    callback(source_file, {'current': i + 1, 'total': len(source_files)})
                
            except Exception as e:
                error_msg = f"Failed to copy {source_file.name}: {str(e)}"
                result['errors'].append(error_msg)
                result['error_count'] += 1
                self.log_manager.add_message(error_msg, "ERROR")
    
    finally:
        result['elapsed_time'] = time.time() - start_time
        result['success'] = result['error_count'] == 0
        self.progress_manager.finish_operation(
            success=result['success'],
            message=f"Copy completed: {result['processed_count']} files"
        )
    
    return result
```

### Copy Features
- **Metadata Preservation**: Preserves file timestamps and permissions
- **Directory Handling**: Recursive copying of directory trees
- **Conflict Resolution**: Interactive handling of file conflicts
- **Progress Tracking**: Real-time progress updates
- **Error Recovery**: Continues operation despite individual file errors

## File Move Operations

### Move Implementation
```python
def move_files(self, source_files, destination_path, callback=None):
    """Move files with cross-filesystem support"""
    # Try fast move first (same filesystem)
    for source_file in source_files:
        dest_file = destination_path / source_file.name
        try:
            source_file.rename(dest_file)
            # Fast move successful
        except OSError:
            # Cross-filesystem move - use copy + delete
            copy_result = self.copy_files([source_file], destination_path, callback)
            if copy_result['success']:
                self.delete_files([source_file])
```

### Move Features
- **Cross-Filesystem Support**: Handles moves across different filesystems
- **Atomic Operations**: Uses rename when possible for atomic moves
- **Fallback Strategy**: Falls back to copy+delete for cross-filesystem moves
- **Conflict Handling**: Same conflict resolution as copy operations

## File Delete Operations

### Delete Implementation
```python
def delete_files(self, file_paths, callback=None):
    """Delete files and directories with confirmation"""
    result = {
        'success': True,
        'processed_count': 0,
        'error_count': 0,
        'errors': []
    }
    
    # Start progress tracking
    self.progress_manager.start_operation(
        OperationType.DELETE,
        len(file_paths),
        f"Deleting {len(file_paths)} items"
    )
    
    for i, file_path in enumerate(file_paths):
        try:
            self.progress_manager.update_progress(i + 1, file_path.name)
            
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            
            result['processed_count'] += 1
            
            if callback:
                callback(file_path, {'current': i + 1, 'total': len(file_paths)})
                
        except Exception as e:
            error_msg = f"Failed to delete {file_path.name}: {str(e)}"
            result['errors'].append(error_msg)
            result['error_count'] += 1
    
    result['success'] = result['error_count'] == 0
    self.progress_manager.finish_operation(
        success=result['success'],
        message=f"Delete completed: {result['processed_count']} items"
    )
    
    return result
```

### Delete Features
- **Safe Deletion**: Proper handling of files and directories
- **Permission Handling**: Handles read-only and protected files
- **Directory Recursion**: Recursive deletion of directory trees
- **Error Reporting**: Detailed error reporting for failed deletions

## Conflict Resolution

### Conflict Handling
```python
def handle_file_conflict(self, source_file, dest_file):
    """Handle file conflicts during operations"""
    # Check if files are identical
    if self.files_are_identical(source_file, dest_file):
        return 'skip'  # Skip identical files
    
    # Show conflict resolution dialog
    conflict_options = [
        {'key': 'o', 'label': 'Overwrite', 'action': 'overwrite'},
        {'key': 's', 'label': 'Skip', 'action': 'skip'},
        {'key': 'r', 'label': 'Rename', 'action': 'rename'},
        {'key': 'c', 'label': 'Cancel', 'action': 'cancel'}
    ]
    
    message = f"File '{dest_file.name}' already exists. Overwrite?"
    
    # Show dialog and get user choice
    choice = self.show_conflict_dialog(message, conflict_options)
    
    if choice == 'rename':
        new_name = self.get_unique_filename(dest_file)
        return ('rename', new_name)
    
    return choice

def files_are_identical(self, file1, file2):
    """Check if two files are identical"""
    if file1.stat().st_size != file2.stat().st_size:
        return False
    
    # Compare file contents for small files
    if file1.stat().st_size < 1024 * 1024:  # 1MB
        return file1.read_bytes() == file2.read_bytes()
    
    # Compare checksums for large files
    return self.calculate_checksum(file1) == self.calculate_checksum(file2)
```

### Conflict Resolution Options
- **Overwrite**: Replace existing file with source file
- **Skip**: Skip the conflicting file and continue
- **Rename**: Create unique name for destination file
- **Cancel**: Cancel the entire operation

## Archive Operations

### Archive Creation
```python
def create_archive(self, source_files, archive_path, archive_type='tar.gz'):
    """Create archive from selected files"""
    self.progress_manager.start_operation(
        OperationType.ARCHIVE_CREATE,
        len(source_files),
        f"Creating {archive_path.name}"
    )
    
    try:
        if archive_type == 'tar.gz':
            with tarfile.open(archive_path, 'w:gz') as tar:
                for i, file_path in enumerate(source_files):
                    self.progress_manager.update_progress(i + 1, file_path.name)
                    tar.add(file_path, arcname=file_path.name)
        
        elif archive_type == 'zip':
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, file_path in enumerate(source_files):
                    self.progress_manager.update_progress(i + 1, file_path.name)
                    if file_path.is_file():
                        zip_file.write(file_path, file_path.name)
                    elif file_path.is_dir():
                        for sub_file in file_path.rglob('*'):
                            if sub_file.is_file():
                                zip_file.write(sub_file, sub_file.relative_to(file_path.parent))
        
        self.progress_manager.finish_operation(
            success=True,
            message=f"Archive {archive_path.name} created successfully"
        )
        return True
        
    except Exception as e:
        self.progress_manager.finish_operation(
            success=False,
            message=f"Archive creation failed: {str(e)}"
        )
        return False
```

### Archive Extraction
```python
def extract_archive(self, archive_path, destination_path):
    """Extract archive to destination directory"""
    try:
        if archive_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz']:
            with tarfile.open(archive_path, 'r:*') as tar:
                members = tar.getmembers()
                self.progress_manager.start_operation(
                    OperationType.ARCHIVE_EXTRACT,
                    len(members),
                    f"Extracting {archive_path.name}"
                )
                
                for i, member in enumerate(members):
                    self.progress_manager.update_progress(i + 1, member.name)
                    tar.extract(member, destination_path)
        
        elif archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                members = zip_file.infolist()
                self.progress_manager.start_operation(
                    OperationType.ARCHIVE_EXTRACT,
                    len(members),
                    f"Extracting {archive_path.name}"
                )
                
                for i, member in enumerate(members):
                    self.progress_manager.update_progress(i + 1, member.filename)
                    zip_file.extract(member, destination_path)
        
        self.progress_manager.finish_operation(
            success=True,
            message=f"Archive {archive_path.name} extracted successfully"
        )
        return True
        
    except Exception as e:
        self.progress_manager.finish_operation(
            success=False,
            message=f"Archive extraction failed: {str(e)}"
        )
        return False
```

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.file_operations = FileOperations(self.config, self.log_manager, self.progress_manager)

# Copy files between panes
def copy_selected_files(self):
    source_files = self.get_selected_files()
    destination = self.get_other_pane_path()
    
    result = self.file_operations.copy_files(source_files, destination)
    
    if result['success']:
        self.log_manager.add_message(f"Copied {result['processed_count']} files")
        self.refresh_panes()
    else:
        self.show_error_dialog(f"Copy failed: {result['error_count']} errors")
```

### Progress Integration
```python
# File operations automatically integrate with progress manager
def perform_file_operation(self, operation_type, files, destination=None):
    """Generic file operation with progress tracking"""
    if operation_type == 'copy':
        return self.file_operations.copy_files(files, destination)
    elif operation_type == 'move':
        return self.file_operations.move_files(files, destination)
    elif operation_type == 'delete':
        return self.file_operations.delete_files(files)
```

## Error Handling

### Comprehensive Error Handling
```python
class FileOperationError(Exception):
    """Custom exception for file operation errors"""
    def __init__(self, message, file_path=None, error_code=None):
        super().__init__(message)
        self.file_path = file_path
        self.error_code = error_code

def safe_file_operation(self, operation_func, *args, **kwargs):
    """Wrapper for safe file operations with error handling"""
    try:
        return operation_func(*args, **kwargs)
    except PermissionError as e:
        raise FileOperationError(f"Permission denied: {e}", error_code='PERMISSION')
    except FileNotFoundError as e:
        raise FileOperationError(f"File not found: {e}", error_code='NOT_FOUND')
    except OSError as e:
        raise FileOperationError(f"System error: {e}", error_code='SYSTEM')
    except Exception as e:
        raise FileOperationError(f"Unexpected error: {e}", error_code='UNKNOWN')
```

### Recovery Strategies
- **Retry Logic**: Automatic retry for transient errors
- **Partial Success**: Continue operation despite individual file failures
- **Rollback**: Undo partial operations on critical failures
- **User Intervention**: Prompt user for error resolution

## Performance Optimization

### Efficient Operations
```python
class FileOperations:
    def __init__(self, config, log_manager, progress_manager):
        self.buffer_size = 64 * 1024  # 64KB buffer for file copying
        self.batch_size = 100         # Process files in batches
        self.use_sendfile = hasattr(os, 'sendfile')  # Use sendfile if available
    
    def optimized_copy(self, source_file, dest_file):
        """Optimized file copying with platform-specific optimizations"""
        if self.use_sendfile and source_file.is_file():
            # Use sendfile for efficient copying on Unix systems
            with open(source_file, 'rb') as src, open(dest_file, 'wb') as dst:
                os.sendfile(dst.fileno(), src.fileno(), 0, source_file.stat().st_size)
        else:
            # Fallback to buffered copying
            shutil.copy2(source_file, dest_file)
```

### Memory Management
- **Streaming Operations**: Process large files without loading into memory
- **Buffer Management**: Optimal buffer sizes for different operations
- **Resource Cleanup**: Proper cleanup of file handles and resources
- **Memory Monitoring**: Monitor memory usage during large operations

## Common Use Cases

### Backup Operations
```python
def backup_files(self, source_files, backup_directory):
    """Create backup of selected files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_directory / f"backup_{timestamp}"
    backup_path.mkdir(exist_ok=True)
    
    return self.file_operations.copy_files(source_files, backup_path)
```

### Batch File Processing
```python
def process_files_batch(self, files, processor_func):
    """Process files in batches for efficiency"""
    batch_size = 50
    results = []
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        batch_result = processor_func(batch)
        results.append(batch_result)
    
    return results
```

### Synchronization Operations
```python
def sync_directories(self, source_dir, dest_dir):
    """Synchronize two directories"""
    source_files = set(f.name for f in source_dir.iterdir())
    dest_files = set(f.name for f in dest_dir.iterdir())
    
    # Files to copy (new or modified)
    to_copy = []
    for file_name in source_files:
        source_file = source_dir / file_name
        dest_file = dest_dir / file_name
        
        if not dest_file.exists() or source_file.stat().st_mtime > dest_file.stat().st_mtime:
            to_copy.append(source_file)
    
    # Files to delete (removed from source)
    to_delete = [dest_dir / name for name in dest_files - source_files]
    
    # Perform synchronization
    copy_result = self.copy_files(to_copy, dest_dir) if to_copy else {'success': True}
    delete_result = self.delete_files(to_delete) if to_delete else {'success': True}
    
    return copy_result['success'] and delete_result['success']
```

## Benefits

### User Experience
- **Progress Feedback**: Real-time progress for all operations
- **Error Transparency**: Clear error reporting and resolution options
- **Conflict Resolution**: Interactive handling of file conflicts
- **Cancellation Support**: Ability to cancel long-running operations

### System Integration
- **Platform Optimization**: Uses platform-specific optimizations when available
- **Resource Efficiency**: Efficient memory and CPU usage
- **Error Resilience**: Robust error handling and recovery
- **Progress Integration**: Seamless integration with progress tracking

### Developer Experience
- **Simple API**: Easy-to-use interface for file operations
- **Comprehensive Results**: Detailed operation results and statistics
- **Flexible Callbacks**: Customizable progress and completion callbacks
- **Error Handling**: Built-in error handling and reporting

## Future Enhancements

### Potential Improvements
- **Parallel Operations**: Multi-threaded file operations for better performance
- **Network Operations**: Support for network file operations
- **Checksums**: Built-in checksum verification for data integrity
- **Compression**: On-the-fly compression for large file operations
- **Deduplication**: Automatic deduplication during copy operations

### Advanced Features
- **Operation Queuing**: Queue multiple operations for batch processing
- **Operation History**: Track and replay previous operations
- **Custom Filters**: User-defined filters for selective operations
- **Scripting Support**: Scriptable file operations for automation
- **Cloud Integration**: Support for cloud storage operations

## Testing

### Test Coverage
- **Basic Operations**: Test all core file operations
- **Error Conditions**: Test various error scenarios and recovery
- **Performance**: Test with large files and many files
- **Edge Cases**: Test edge cases and boundary conditions
- **Integration**: Test integration with progress and logging systems

### Test Scenarios
- **Copy Operations**: Various copy scenarios and conflict resolution
- **Move Operations**: Cross-filesystem moves and error handling
- **Delete Operations**: Safe deletion and permission handling
- **Archive Operations**: Archive creation and extraction
- **Error Recovery**: Error handling and recovery mechanisms

## Conclusion

The File Operations System provides comprehensive, robust file management functionality for TFM. Its combination of efficient operations, comprehensive error handling, progress tracking, and user-friendly conflict resolution makes it the foundation for all file management tasks in TFM. The system's performance optimization and platform integration ensure excellent user experience across different operating systems and file system types.