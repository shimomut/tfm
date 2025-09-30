# Favorite Directories Implementation

## Overview

The Favorite Directories feature allows users to quickly navigate to frequently used directories through a searchable list dialog. This document covers the implementation details for developers.

## Architecture

### File Structure
- **Configuration**: `src/tfm_config.py` - Configuration loading and validation
- **Main Logic**: `src/tfm_main.py` - Dialog display and navigation logic
- **Templates**: `src/_config.py` - Default configuration template

### Key Components

#### Configuration Loading
```python
def get_favorite_directories():
    """Get the list of favorite directories from configuration"""
    # Loads from user config or falls back to defaults
    # Validates paths and expands ~ to home directory
    # Returns list of valid directories only
```

#### Dialog Display
```python
def show_favorite_directories(self):
    """Show favorite directories using the searchable list dialog"""
    # Creates display items with name and path
    # Handles selection and navigation
    # Updates current pane path on selection
```

#### Path Handling
- **Expansion**: `~` is expanded to user's home directory
- **Validation**: Only existing directories are shown
- **Resolution**: Paths are resolved to absolute paths
- **Error Handling**: Invalid paths are logged but don't break functionality

## Integration Points

### Key Binding System
```python
elif self.is_key_for_action(key, 'favorites'):
    self.show_favorite_directories()
```

### Searchable List Dialog
The feature leverages the existing searchable list dialog system:
- Consistent UI with other dialogs
- Full keyboard navigation support
- Search/filter capabilities
- Proper integration with main event loop

### Pane Management
```python
# Updates current pane to selected directory
current_pane['path'] = target_path
current_pane['selected_index'] = 0
current_pane['scroll_offset'] = 0
current_pane['selected_files'].clear()
```

## Configuration Format

Each favorite directory entry must have:
- **name**: Display name for the directory
- **path**: Actual path to the directory (supports `~` expansion)

```python
{'name': 'Display Name', 'path': '/actual/path'}
```

### Default Configuration
```python
FAVORITE_DIRECTORIES = [
    {'name': 'Home', 'path': '~'},
    {'name': 'Documents', 'path': '~/Documents'},
    {'name': 'Downloads', 'path': '~/Downloads'},
    {'name': 'Desktop', 'path': '~/Desktop'},
    {'name': 'Projects', 'path': '~/Projects'},
    {'name': 'Root', 'path': '/'},
    {'name': 'Temp', 'path': '/tmp'},
    {'name': 'Config', 'path': '~/.config'},
]
```

## Error Handling

### Missing Directories
- Directories that don't exist are filtered out
- Warning messages are logged for missing directories
- System continues to work with remaining valid directories

### Invalid Configuration
- Malformed favorite entries are skipped
- Falls back to default favorites if user config is invalid
- Graceful degradation ensures feature always works

### Path Resolution Errors
- Invalid paths are caught and logged
- System continues with other valid favorites
- User is informed of any issues

## Testing

### Configuration Tests
```bash
python3 test/test_favorites_config.py
```

Tests:
- Configuration loading
- Path expansion
- Key binding setup
- Edge case handling

### Interactive Tests
```bash
python3 test_favorites.py
python3 demo_favorites.py
```

Features tested:
- Dialog display
- Navigation
- Search functionality
- Directory selection

### Manual Testing
1. Start TFM: `python3 src/tfm_main.py`
2. Press **J** to open favorites
3. Test navigation and search
4. Select a directory to verify navigation works

## Implementation Examples

### Basic Setup
```python
# Simple favorites for a developer
FAVORITE_DIRECTORIES = [
    {'name': 'Home', 'path': '~'},
    {'name': 'Projects', 'path': '~/dev'},
    {'name': 'Scripts', 'path': '~/bin'},
    {'name': 'Temp', 'path': '/tmp'},
]
```

### Advanced Setup
```python
# Comprehensive favorites for system administration
FAVORITE_DIRECTORIES = [
    # User directories
    {'name': 'Home', 'path': '~'},
    {'name': 'Documents', 'path': '~/Documents'},
    {'name': 'Downloads', 'path': '~/Downloads'},
    
    # Development
    {'name': 'Projects', 'path': '~/projects'},
    {'name': 'Git Repos', 'path': '~/git'},
    {'name': 'Scripts', 'path': '~/bin'},
    
    # System directories
    {'name': 'Root', 'path': '/'},
    {'name': 'System Config', 'path': '/etc'},
    {'name': 'System Logs', 'path': '/var/log'},
    {'name': 'Web Root', 'path': '/var/www'},
    {'name': 'Applications', 'path': '/Applications'},
    
    # Temporary and cache
    {'name': 'Temp', 'path': '/tmp'},
    {'name': 'User Cache', 'path': '~/.cache'},
    {'name': 'User Config', 'path': '~/.config'},
]
```

## Future Enhancements

### Potential Improvements
- **Dynamic Favorites**: Add/remove favorites from within TFM
- **Recent Directories**: Automatically track recently visited directories
- **Favorite Groups**: Organize favorites into categories
- **Import/Export**: Share favorite configurations
- **Bookmarks**: Quick single-key access to specific favorites
- **Path Variables**: Support for environment variables in paths

### Advanced Features
- **Network Paths**: Support for remote directories
- **Conditional Favorites**: Show different favorites based on context
- **Favorite Actions**: Associate actions with favorite directories
- **Smart Suggestions**: Suggest favorites based on usage patterns

## Troubleshooting

### Debug Steps
1. Check configuration loading messages in log pane
2. Verify favorite directories exist on filesystem
3. Test with default configuration
4. Check file permissions for config directory

### Common Implementation Issues
- Path expansion not working correctly
- Configuration loading failures
- Dialog integration problems
- Key binding conflicts