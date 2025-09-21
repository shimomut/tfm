# Pane Manager Component

## Overview

The Pane Manager Component handles TFM's dual-pane interface, managing navigation between left and right panes, directory synchronization, and pane-specific operations. It provides the core functionality for TFM's dual-pane file management paradigm.

## Features

### Core Capabilities
- **Dual Pane Management**: Independent left and right pane operations
- **Active Pane Tracking**: Maintains current active pane state
- **Directory Navigation**: Handles directory changes and navigation
- **Pane Synchronization**: Sync directories between panes
- **File Selection Management**: Manages selected files per pane

### Advanced Features
- **Path History**: Maintains navigation history for each pane
- **Startup Configuration**: Configurable startup directories
- **Cross-Pane Operations**: Operations between left and right panes
- **State Persistence**: Maintains pane state during operations
- **Flexible Layout**: Adjustable pane width ratios

## Class Structure

### PaneManager Class
```python
class PaneManager:
    def __init__(self, config)
    def get_current_pane()
    def get_inactive_pane()
    def switch_active_pane()
    def sync_panes(direction)
    def navigate_to_directory(pane, path)
    def get_pane_width(total_width, left_ratio)
```

### Pane Data Structure
```python
pane_data = {
    'path': Path,           # Current directory path
    'files': List[Path],    # List of files in directory
    'selected_index': int,  # Currently selected file index
    'scroll_offset': int,   # Scroll position in file list
    'selected_files': Set,  # Set of selected file paths
    'sort_mode': str,       # Current sort mode
    'sort_reverse': bool,   # Sort direction
    'filter_pattern': str   # Current filter pattern
}
```

## Usage Examples

### Basic Pane Operations
```python
pane_manager = PaneManager(config)

# Get current active pane
current = pane_manager.get_current_pane()
print(f"Current directory: {current['path']}")

# Switch to other pane
pane_manager.switch_active_pane()

# Get inactive pane
other = pane_manager.get_inactive_pane()
```

### Directory Navigation
```python
# Navigate current pane to new directory
new_path = Path("/home/user/documents")
pane_manager.navigate_to_directory(current_pane, new_path)

# Navigate other pane
pane_manager.navigate_to_directory(other_pane, new_path)
```

### Pane Synchronization
```python
# Sync current pane directory to other pane
pane_manager.sync_panes('current_to_other')

# Sync other pane directory to current pane  
pane_manager.sync_panes('other_to_current')
```

## Pane Management Features

### Active Pane Tracking
- **Current Pane**: Always knows which pane is active
- **Pane Switching**: Easy switching between left and right panes
- **State Maintenance**: Preserves pane state during switches
- **Visual Indication**: Clear visual indication of active pane

### Directory Operations
- **Navigation**: Change directories in either pane
- **Path Validation**: Ensures valid directory paths
- **Error Handling**: Graceful handling of navigation errors
- **History Tracking**: Maintains navigation history

### File Selection Management
- **Per-Pane Selection**: Independent file selection per pane
- **Selection Persistence**: Maintains selections during navigation
- **Cross-Pane Operations**: Operations using selections from both panes
- **Selection Clearing**: Automatic and manual selection clearing

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.pane_manager = PaneManager(self.config)

# Access current pane
current_pane = self.pane_manager.get_current_pane()

# Handle pane switching
if key == curses.KEY_RIGHT:
    if self.pane_manager.active_pane == 'left':
        self.pane_manager.switch_active_pane()
```

### File Operations Integration
```python
# Get files from both panes for operations
source_files = self.pane_manager.get_current_pane()['selected_files']
destination_path = self.pane_manager.get_inactive_pane()['path']

# Perform cross-pane operation
copy_files(source_files, destination_path)
```

## Pane Layout Management

### Width Calculation
```python
def get_pane_width(self, total_width, left_ratio):
    """Calculate pane widths based on total width and ratio"""
    left_width = int(total_width * left_ratio)
    right_width = total_width - left_width - 1  # -1 for separator
    return left_width, right_width
```

### Adjustable Ratios
- **Default Ratio**: Configurable default pane width ratio
- **Runtime Adjustment**: User can adjust pane widths during use
- **Minimum Widths**: Ensures both panes remain usable
- **Responsive Layout**: Adapts to terminal size changes

## Synchronization Features

### Directory Sync Options
```python
# Sync current pane to other pane
pane_manager.sync_panes('current_to_other')

# Sync other pane to current pane
pane_manager.sync_panes('other_to_current')

# Bidirectional sync (both panes to same directory)
pane_manager.sync_panes('bidirectional')
```

### Sync Benefits
- **Quick Navigation**: Rapidly navigate both panes to same location
- **Comparison**: Easy comparison of directory contents
- **Batch Operations**: Prepare for cross-pane operations
- **Workflow Efficiency**: Streamlined file management workflow

## State Management

### Pane State Persistence
- **Directory State**: Maintains current directory per pane
- **Selection State**: Preserves file selections per pane
- **View State**: Maintains scroll position and view settings
- **Sort State**: Preserves sort settings per pane

### State Restoration
```python
# Save current state
saved_state = {
    'left_pane': dict(self.left_pane),
    'right_pane': dict(self.right_pane),
    'active_pane': self.active_pane
}

# Restore state later
self.left_pane.update(saved_state['left_pane'])
self.right_pane.update(saved_state['right_pane'])
self.active_pane = saved_state['active_pane']
```

## Configuration Integration

### Startup Configuration
```python
class Config:
    STARTUP_LEFT_PATH = "~/projects"      # Left pane startup directory
    STARTUP_RIGHT_PATH = "~/downloads"    # Right pane startup directory
    DEFAULT_LEFT_PANE_RATIO = 0.5        # Default pane width ratio
```

### Runtime Configuration
- **Pane Ratios**: Adjustable pane width ratios
- **Default Directories**: Configurable startup directories
- **Behavior Settings**: Configurable pane behavior options
- **Key Bindings**: Configurable pane navigation keys

## Advanced Operations

### Cross-Pane File Operations
```python
def copy_selected_to_other_pane(self):
    """Copy selected files from current pane to other pane"""
    source_pane = self.get_current_pane()
    dest_pane = self.get_inactive_pane()
    
    selected_files = source_pane['selected_files']
    destination_path = dest_pane['path']
    
    return copy_files(selected_files, destination_path)
```

### Pane Comparison
```python
def compare_pane_contents(self):
    """Compare contents of both panes"""
    left_files = set(f.name for f in self.left_pane['files'])
    right_files = set(f.name for f in self.right_pane['files'])
    
    common = left_files & right_files
    left_only = left_files - right_files
    right_only = right_files - left_files
    
    return common, left_only, right_only
```

## Error Handling

### Navigation Errors
- **Invalid Paths**: Graceful handling of invalid directory paths
- **Permission Errors**: Proper handling of access denied errors
- **Missing Directories**: Fallback behavior for missing directories
- **Network Issues**: Handling of network path problems

### State Recovery
```python
def safe_navigate(self, pane, path):
    """Safely navigate to directory with error handling"""
    try:
        original_path = pane['path']
        self.navigate_to_directory(pane, path)
        return True
    except Exception as e:
        # Restore original path on error
        pane['path'] = original_path
        self.log_manager.add_message(f"Navigation failed: {e}", "ERROR")
        return False
```

## Performance Optimization

### Efficient Operations
- **Lazy Loading**: Load directory contents only when needed
- **Caching**: Cache directory listings for performance
- **Minimal Updates**: Only update changed pane data
- **Efficient Comparisons**: Optimized pane comparison operations

### Memory Management
- **Selective Loading**: Load only necessary file information
- **Cleanup**: Automatic cleanup of old pane data
- **Efficient Storage**: Optimized data structures for pane information
- **Resource Management**: Proper resource cleanup

## Common Use Cases

### File Management Workflow
```python
# 1. Navigate to source directory
pane_manager.navigate_to_directory(current_pane, source_dir)

# 2. Select files to operate on
current_pane['selected_files'].add(file_path)

# 3. Navigate other pane to destination
pane_manager.navigate_to_directory(other_pane, dest_dir)

# 4. Perform cross-pane operation
copy_selected_files()
```

### Directory Comparison
```python
# 1. Navigate both panes to directories to compare
pane_manager.navigate_to_directory(left_pane, dir1)
pane_manager.navigate_to_directory(right_pane, dir2)

# 2. Compare contents
common, left_only, right_only = compare_pane_contents()

# 3. Display comparison results
show_comparison_results(common, left_only, right_only)
```

### Synchronized Navigation
```python
# 1. Navigate to base directory
pane_manager.navigate_to_directory(current_pane, base_dir)

# 2. Sync other pane to same location
pane_manager.sync_panes('current_to_other')

# 3. Navigate subdirectories in parallel
navigate_subdirectory(left_pane, "subdir1")
navigate_subdirectory(right_pane, "subdir2")
```

## Benefits

### User Experience
- **Intuitive Interface**: Familiar dual-pane file manager interface
- **Efficient Navigation**: Quick switching and synchronization
- **Visual Clarity**: Clear indication of active pane and selections
- **Flexible Layout**: Adjustable pane sizes for different workflows

### Productivity
- **Cross-Pane Operations**: Efficient file operations between directories
- **Quick Comparison**: Easy comparison of directory contents
- **Batch Operations**: Select files in one pane, operate on another
- **Workflow Optimization**: Streamlined file management tasks

### Technical Benefits
- **Modular Design**: Clean separation of pane management logic
- **State Management**: Robust state tracking and persistence
- **Error Resilience**: Graceful error handling and recovery
- **Performance**: Efficient operations and memory usage

## Future Enhancements

### Potential Improvements
- **Multiple Panes**: Support for more than two panes
- **Pane Tabs**: Tabbed interface for multiple directory sets
- **Pane History**: Navigation history with back/forward buttons
- **Pane Bookmarks**: Quick access to frequently used directories
- **Custom Layouts**: User-configurable pane layouts

### Advanced Features
- **Pane Profiles**: Save and restore pane configurations
- **Network Panes**: Support for remote directory access
- **Virtual Panes**: Special panes for search results or archives
- **Pane Scripting**: Scriptable pane operations and automation
- **Collaborative Panes**: Shared panes for team collaboration

## Testing

### Test Coverage
- **Pane Operations**: Test all basic pane operations
- **Navigation**: Test directory navigation and error handling
- **Synchronization**: Test pane sync operations
- **State Management**: Test state persistence and restoration
- **Integration**: Test integration with main application

### Test Scenarios
- **Basic Navigation**: Simple directory navigation
- **Cross-Pane Operations**: File operations between panes
- **Error Conditions**: Invalid paths and permission errors
- **State Persistence**: Maintaining state during operations
- **Performance**: Large directory handling

## Conclusion

The Pane Manager Component is fundamental to TFM's dual-pane interface, providing robust pane management, efficient navigation, and seamless cross-pane operations. Its clean design, comprehensive error handling, and performance optimization make it an essential component for effective file management workflows.