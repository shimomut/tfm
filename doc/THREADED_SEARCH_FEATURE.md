# Threaded Search Feature

## Overview

The SearchDialog component has been enhanced with threading support to provide non-blocking, asynchronous search operations. This improvement addresses performance issues when searching through large directory structures or files.

## Key Features

### Asynchronous Search Operations
- Search operations run in background threads
- UI remains responsive during search
- Results appear in real-time as they are found
- Multiple search types supported (filename and content)

### Search Cancellation and Restart
- Automatic search cancellation when pattern changes
- Manual cancellation when dialog is closed or ESC is pressed
- Clean thread termination with proper resource cleanup
- Search restart when typing new patterns

### Thread Safety
- Thread-safe access to search results using locks
- Safe navigation and selection during active searches
- Proper synchronization between UI and search threads
- No race conditions or data corruption

### Configurable Result Limiting
- Maximum search results limit to prevent memory issues
- Configurable via `MAX_SEARCH_RESULTS` in config
- Default limit: 10,000 results
- Real-time indication when limit is reached

## Technical Implementation

### Threading Architecture
```python
# Search thread management
self.search_thread = None
self.search_lock = threading.Lock()
self.cancel_search = threading.Event()
```

### Thread-Safe Result Access
```python
# All result access is protected by locks
with self.search_lock:
    results = self.results.copy()
    current_selected = self.selected
```

### Search Cancellation
```python
def _cancel_current_search(self):
    """Cancel the current search operation"""
    if self.search_thread and self.search_thread.is_alive():
        self.cancel_search.set()
        self.search_thread.join(timeout=0.1)
```

## Configuration

### MAX_SEARCH_RESULTS
Controls the maximum number of search results to prevent memory exhaustion:

```python
class Config:
    MAX_SEARCH_RESULTS = 10000  # Adjust based on system resources
```

## User Experience Improvements

### Real-Time Results
- Results appear as they are found
- No need to wait for complete search
- Progress indication shows current result count
- Immediate feedback for search patterns

### Responsive Navigation
- Arrow keys work during active searches
- Page up/down navigation available
- Home/End keys for quick navigation
- Selection highlighting maintained

### Search Type Switching
- Tab key switches between filename and content search
- Search automatically restarts with new type
- Previous results cleared when switching

### Visual Feedback
- "Searching..." indicator during active searches
- Animated progress indicators (configurable patterns)
- Result count with progress information
- Limit reached notification
- Thread status indication

### Animated Progress Indicators
- Three animation patterns: spinner, dots, progress bar
- Configurable animation speed
- Visual feedback during search operations
- Thread-safe animation updates
- See [SEARCH_ANIMATION_FEATURE.md](SEARCH_ANIMATION_FEATURE.md) for details

## Performance Benefits

### Before Threading
- UI blocked during search operations
- Long delays for large directory structures
- No way to cancel slow searches
- Memory could grow unbounded

### After Threading
- UI remains responsive at all times
- Search results appear incrementally
- Instant search cancellation
- Memory usage controlled by result limit

## Error Handling

### Thread Safety
- All exceptions caught in worker threads
- No crashes from thread synchronization issues
- Graceful degradation on thread errors
- Proper cleanup on abnormal termination

### Resource Management
- Threads properly joined on exit
- File handles closed correctly
- Memory freed when searches cancelled
- No resource leaks

## Testing

### Comprehensive Test Suite
- Thread safety verification
- Search cancellation testing
- Result limiting validation
- Concurrent access testing
- Performance benchmarking

### Test Coverage
- Filename search threading
- Content search threading
- Pattern change handling
- Navigation during search
- Thread synchronization

## Usage Examples

### Basic Threaded Search
```python
# Initialize search dialog
search_dialog = SearchDialog(config)
search_dialog.show('filename')

# Set pattern and start search
search_dialog.pattern_editor.text = "*.py"
search_dialog.perform_search(search_root)

# Results appear automatically as found
# Navigation works immediately
```

### Search Cancellation
```python
# Cancel current search
search_dialog._cancel_current_search()

# Or exit dialog (automatically cancels)
search_dialog.exit()
```

## Migration Notes

### API Compatibility
- All existing SearchDialog APIs remain unchanged
- No breaking changes to calling code
- Configuration additions are optional
- Backward compatibility maintained

### Performance Considerations
- Slightly higher memory usage due to threading
- Better overall performance for large searches
- CPU usage distributed across threads
- I/O operations no longer block UI

## Future Enhancements

### Potential Improvements
- Search result caching
- Incremental search refinement
- Search history and bookmarks
- Advanced search filters
- Regular expression support improvements

### Scalability
- Support for very large file systems
- Distributed search across network drives
- Search result streaming for massive datasets
- Memory-mapped file searching

## Troubleshooting

### Common Issues
1. **High memory usage**: Reduce MAX_SEARCH_RESULTS
2. **Slow searches**: Check file system performance
3. **Thread errors**: Verify Python threading support
4. **UI freezing**: Ensure proper lock usage

### Debug Information
- Thread status available in search dialog
- Result count and limit information
- Search pattern and type display
- Performance timing available

## Conclusion

The threaded search feature significantly improves TFM's usability when working with large directory structures. The implementation provides a responsive user interface while maintaining thread safety and resource management best practices.