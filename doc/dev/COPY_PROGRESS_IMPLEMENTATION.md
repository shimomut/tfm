# Copy Progress Implementation

## Overview

This document describes the technical implementation of the enhanced copy progress tracking system in TFM. The system provides real-time progress updates for file copy operations through background threading, fine-grained file tracking, and byte-level progress for large files.

## Architecture

### Component Overview

```
FileOperationsUI
    └─> perform_copy_operation()
        └─> [Background Thread]
            ├─> _copy_directory_with_progress()
            ├─> _copy_file_with_progress()
            └─> ProgressManager
                ├─> update_progress()
                ├─> update_file_byte_progress()
                └─> ProgressAnimator
```

### Key Components

#### 1. FileOperationsUI (`tfm_file_operations.py`)

Main class handling file operations with UI integration.

**Key Methods:**
- `perform_copy_operation()`: Spawns background thread for copy operation
- `_copy_file_with_progress()`: Copies single file with byte-level progress
- `_copy_directory_with_progress()`: Recursively copies directory with file-level progress
- `_copy_directory_cross_storage_with_progress()`: Handles cross-storage directory copies
- `_count_files_recursively()`: Counts total files for progress calculation
- `_progress_callback()`: Callback for progress updates to refresh UI

#### 2. ProgressManager (`tfm_progress_manager.py`)

Manages progress state and provides formatted progress information.

**Key Methods:**
- `start_operation()`: Initializes progress tracking
- `update_progress()`: Updates file-level progress
- `update_file_byte_progress()`: Updates byte-level progress for current file
- `finish_operation()`: Cleans up progress state
- `get_progress_text()`: Formats progress for display
- `get_progress_percentage()`: Calculates overall percentage

**State Management:**
```python
current_operation = {
    'type': OperationType,           # COPY, MOVE, DELETE, etc.
    'total_items': int,              # Total files to process
    'processed_items': int,          # Files processed so far
    'current_item': str,             # Current filename
    'description': str,              # Operation description
    'errors': int,                   # Error count
    'file_byte_progress': int        # Current file byte progress (0-100)
}
```

#### 3. ProgressAnimator (`tfm_progress_manager.py`)

Provides animated spinner for visual feedback.

**Animation Frames:**
```python
frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
```

**Frame Update Logic:**
- Updates every 80ms
- Cycles through 10 frames
- Resets on operation start/finish

## Threading Model

### Background Thread Execution

Copy operations use two daemon threads to prevent UI blocking and ensure smooth animation:

```python
def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):
    def copy_thread():
        # Start animation refresh thread
        animation_stop_event = threading.Event()
        animation_thread = threading.Thread(
            target=self._animation_refresh_loop,
            args=(animation_stop_event,),
            daemon=True
        )
        animation_thread.start()
        
        try:
            # Actual copy logic here
            pass
        finally:
            # Stop animation thread
            animation_stop_event.set()
    
    thread = threading.Thread(target=copy_thread, daemon=True)
    thread.start()
```

**Thread Characteristics:**

1. **Copy Thread**:
   - **Daemon thread**: Automatically terminates when main thread exits
   - **Non-blocking**: UI remains responsive during operation
   - **Single-threaded copy**: Files copied sequentially for safety
   - **Progress callbacks**: Thread-safe updates to UI

2. **Animation Thread**:
   - **Daemon thread**: Automatically terminates with copy thread
   - **Independent refresh**: Updates animation every 100ms
   - **Continuous animation**: Keeps spinner moving even without progress updates
   - **Event-based stop**: Clean shutdown via threading.Event

### Thread Safety

**Progress Updates:**
- Progress manager state updated from background thread
- Callbacks invoke UI refresh from background thread
- Curses operations protected by try-except blocks
- No shared mutable state between threads

**UI Refresh:**
```python
def _progress_callback(self, progress_data):
    try:
        self.file_manager.draw_status()
        self.file_manager.stdscr.refresh()
    except Exception as e:
        print(f"Warning: Progress callback display update failed: {e}")
```

### Operation Control

**Input Blocking:**
```python
# In main event loop (tfm_main.py)
if hasattr(self, 'operation_in_progress') and self.operation_in_progress:
    # Only allow ESC key to cancel operation
    if key == 27:  # ESC key
        self.operation_cancelled = True
        print("Cancelling operation...")
    # Ignore all other keys during operation
else:
    # Handle normal key input
    self.handle_key_input(key)
```

**Cancellation Checks:**
```python
# In copy operation loop
for source_file in files_to_copy:
    # Check for cancellation
    if self.file_manager.operation_cancelled:
        print("Copy operation cancelled by user")
        break
    
    # Copy file...
```

**Cancellation Points:**
1. Between files in top-level loop
2. Between files in directory traversal
3. Every 1MB chunk in large file copies
4. Partial files removed on cancellation

**State Management:**
```python
# FileManager initialization
self.operation_in_progress = False  # Blocks input when True
self.operation_cancelled = False    # Signals cancellation

# Operation start
self.file_manager.operation_in_progress = True
self.file_manager.operation_cancelled = False

# Operation end (in finally block)
self.file_manager.operation_in_progress = False
```

## Progress Tracking Levels

### 1. File-Level Progress

Tracks individual files being copied:

```python
processed_files += 1
self.progress_manager.update_progress(display_name, processed_files)
```

**Features:**
- Updates for every file
- Shows relative paths for subdirectory files
- Handles symbolic links separately
- Counts skipped files for accurate progress

### 2. Byte-Level Progress

Tracks bytes copied for large files (>1MB) and displays in human-readable format:

```python
chunk_size = 1024 * 1024  # 1MB chunks
bytes_copied = 0

with open(str(source_file), 'rb') as src:
    with open(str(dest_file), 'wb') as dst:
        while True:
            chunk = src.read(chunk_size)
            if not chunk:
                break
            dst.write(chunk)
            bytes_copied += len(chunk)
            
            # Update with actual bytes, not percentage
            self.progress_manager.update_file_byte_progress(bytes_copied, file_size)
```

**Display Format:**
- Converts bytes to human-readable format: B, K, M, G, T
- Example: `15M/32.0G` shows 15 megabytes of 32 gigabytes copied
- Only shown for files >1MB that require multiple read/write operations
- Format function rounds appropriately for each unit

**Thresholds:**
- Small files (≤1MB): Simple copy, no byte progress displayed
- Large files (>1MB): Chunked copy with byte progress in format like "15M/32.0G"
- Chunk size: 1MB for optimal I/O performance

### 3. Directory-Level Progress

Recursively tracks all files in directories:

```python
for root, dirs, files in os.walk(source_dir):
    for file_name in files:
        processed_files += 1
        display_name = str(rel_path / file_name)
        self.progress_manager.update_progress(display_name, processed_files)
        # Copy file...
```

**Features:**
- Shows relative paths from top-level directory
- Handles nested subdirectories
- Tracks symbolic links to directories
- Maintains accurate file count

## Progress Throttling

### Callback Throttling

Prevents excessive UI updates:

```python
callback_throttle_ms = 50  # Minimum 50ms between callbacks

current_time = time.time() * 1000
if current_time - self.last_callback_time >= self.callback_throttle_ms:
    self.progress_callback(self.current_operation)
    self.last_callback_time = current_time
```

**Benefits:**
- Reduces CPU usage for UI updates
- Prevents screen flicker
- Maintains smooth animation
- Balances responsiveness with performance

### Animation Refresh Loop

Separate thread ensures continuous animation:

```python
def _animation_refresh_loop(self, stop_event):
    """Background loop to refresh animation periodically"""
    while not stop_event.is_set():
        # Refresh animation to keep spinner moving
        self.progress_manager.refresh_animation()
        
        # Sleep for 100ms to keep animation smooth
        time.sleep(0.1)
```

**Animation Refresh Mechanism:**
- Runs in separate daemon thread
- Calls `refresh_animation()` every 100ms
- Forces UI callback to update display
- Independent of progress updates
- Ensures smooth animation during long operations

### Animation Frame Updates

Animation frames update based on time:

```python
# In ProgressAnimator (from tfm_progress_animator.py)
animation_speed = 0.08  # 80ms per frame

if current_time - self.last_update_time >= self.animation_speed:
    self.frame_index = (self.frame_index + 1) % len(pattern)
    self.last_update_time = current_time
```

## File Counting

### Recursive File Counting

Counts all files before starting operation:

```python
def _count_files_recursively(self, paths):
    total_files = 0
    for path in paths:
        if path.is_file() or path.is_symlink():
            total_files += 1
        elif path.is_dir():
            try:
                for root, dirs, files in os.walk(path):
                    total_files += len(files)
                    # Count symlinks to directories
                    for d in dirs:
                        dir_path = Path(root) / d
                        if dir_path.is_symlink():
                            total_files += 1
            except (PermissionError, OSError):
                total_files += 1
    return total_files
```

**Considerations:**
- Counts files before copying starts
- Includes symbolic links as files
- Handles permission errors gracefully
- Used for accurate percentage calculation

## Cross-Storage Support

### Local to Local

Optimized path using `os.walk()`:

```python
def _copy_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
    for root, dirs, files in os.walk(source_dir):
        for file_name in files:
            # Copy with progress...
```

**Features:**
- Direct file system access
- Efficient directory traversal
- Byte-level progress for large files
- Preserves file metadata

### Cross-Storage (e.g., Local to S3)

Uses Path abstraction with progress:

```python
def _copy_directory_cross_storage_with_progress(self, source_dir, dest_dir, 
                                                processed_files, total_files, overwrite=False):
    for item in source_dir.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(source_dir)
            dest_item = dest_dir / rel_path
            
            processed_files += 1
            self.progress_manager.update_progress(str(rel_path), processed_files)
            
            item.copy_to(dest_item, overwrite=overwrite)
```

**Features:**
- Works with any storage backend
- Uses Path abstraction layer
- File-level progress only (no byte progress)
- Handles different storage schemes

## Error Handling

### File-Level Errors

Errors tracked but don't stop operation:

```python
try:
    self._copy_file_with_progress(source_file, dest_path, overwrite)
except PermissionError as e:
    print(f"Permission denied copying {source_file.name}: {e}")
    error_count += 1
    self.progress_manager.increment_errors()
    processed_files += 1  # Still count for progress
except Exception as e:
    print(f"Error copying {source_file.name}: {e}")
    error_count += 1
    self.progress_manager.increment_errors()
    processed_files += 1  # Still count for progress
```

**Error Handling Strategy:**
- Catch specific exceptions (PermissionError, FileNotFoundError)
- Log errors with context
- Increment error counter
- Continue with remaining files
- Update progress even for failed files

### Progress Callback Errors

UI update errors don't crash operation:

```python
def _progress_callback(self, progress_data):
    try:
        self.file_manager.draw_status()
        self.file_manager.stdscr.refresh()
    except Exception as e:
        print(f"Warning: Progress callback display update failed: {e}")
```

## Performance Considerations

### Memory Usage

- **File list**: Stored in memory for counting
- **Progress state**: Single dictionary, minimal overhead
- **Chunk buffer**: 1MB buffer for large file copying
- **Thread overhead**: Single background thread

### I/O Performance

- **Chunk size**: 1MB chunks balance memory and I/O efficiency
- **Sequential copying**: Files copied one at a time
- **No parallel I/O**: Avoids contention and complexity
- **Metadata preservation**: Uses `shutil.copystat()` for efficiency

### UI Performance

- **Throttled updates**: Maximum 20 updates/second (50ms throttle)
- **Minimal redraws**: Only status bar updated, not full screen
- **Animation efficiency**: Frame updates independent of file progress
- **String formatting**: Efficient truncation for long filenames

## Integration Points

### FileManager Integration

Progress displayed in status bar:

```python
def draw_status(self):
    # ... other status info ...
    
    # Show progress if operation is active
    if self.progress_manager.is_operation_active():
        progress_text = self.progress_manager.get_progress_text(max_width)
        # Display progress_text in status bar
```

### Cache Invalidation

Cache updated after successful copy:

```python
if copied_count > 0:
    self.cache_manager.invalidate_cache_for_copy_operation(files_to_copy, destination_dir)
```

### UI Refresh

Full refresh after operation completes:

```python
self.file_manager.refresh_files()
self.file_manager.needs_full_redraw = True
```

## Testing

### Unit Testing

Test individual components:

```python
def test_progress_manager():
    pm = ProgressManager()
    pm.start_operation(OperationType.COPY, 100, "test")
    pm.update_progress("file1.txt", 1)
    assert pm.get_progress_percentage() == 1
```

### Integration Testing

Test complete copy operation:

```python
def test_copy_with_progress():
    # Create test files
    # Perform copy operation
    # Verify progress updates
    # Verify files copied correctly
```

### Demo Scripts

See `demo/demo_copy_progress_threading.py` for complete example.

## Future Enhancements

### Potential Improvements

1. **Parallel copying**: Copy multiple files simultaneously
2. **Transfer speed**: Calculate and display MB/s
3. **ETA calculation**: Estimate time remaining
4. **Pause/resume**: Allow pausing long operations
5. **Progress history**: Log all operations for review
6. **Bandwidth limiting**: Throttle copy speed for network operations
7. **Compression progress**: Show compression ratio for archives
8. **Verification progress**: Show progress during copy verification

### Performance Optimizations

1. **Adaptive chunk size**: Adjust based on file size and speed
2. **Read-ahead buffering**: Pre-read next chunk while writing current
3. **Parallel I/O**: Use separate threads for reading and writing
4. **Memory mapping**: Use mmap for very large files
5. **Zero-copy**: Use sendfile() on supported platforms

## Debugging

### Progress Not Updating

Check:
1. Is operation running in background thread?
2. Is progress callback being called?
3. Is UI refresh working?
4. Are there exceptions in the callback?

### Incorrect Progress Percentage

Check:
1. Is file counting accurate?
2. Are skipped files being counted?
3. Are errors being counted?
4. Is processed_files being incremented correctly?

### Animation Not Smooth

Check:
1. Is frame duration appropriate (80ms)?
2. Is callback throttling too aggressive?
3. Is UI refresh blocking?
4. Are there performance issues?

## References

- `src/tfm_file_operations.py`: Main implementation
- `src/tfm_progress_manager.py`: Progress tracking and animation
- `demo/demo_copy_progress_threading.py`: Complete demo
- `doc/COPY_PROGRESS_FEATURE.md`: User documentation
