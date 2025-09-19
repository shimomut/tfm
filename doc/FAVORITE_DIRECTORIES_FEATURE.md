# Favorite Directories Feature

## Overview

The Favorite Directories feature allows users to quickly navigate to frequently used directories through a searchable list dialog. Users can configure their favorite directories in the configuration file and access them with a single key press.

## Features

### Core Functionality
- **Quick Access**: Press 'J' key to open the favorites dialog
- **Searchable List**: Use the searchable list dialog to filter favorites
- **Instant Navigation**: Select a directory to immediately navigate to it
- **Configurable**: Customize your favorite directories in the config file
- **Path Expansion**: Supports `~` for home directory expansion
- **Validation**: Only shows directories that actually exist

### User Experience
- **Fast Navigation**: No need to manually navigate through directory trees
- **Search Support**: Type to quickly find the directory you want
- **Visual Feedback**: Clear display of directory names and paths
- **Error Handling**: Graceful handling of missing or invalid directories

## Configuration

### Default Favorites

The system comes with sensible default favorite directories:

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

### Customizing Favorites

Edit your `~/.tfm/config.py` file to customize favorites:

```python
class Config:
    # ... other settings ...
    
    # Favorite directories - customize your frequently used directories
    FAVORITE_DIRECTORIES = [
        {'name': 'Home', 'path': '~'},
        {'name': 'Work Projects', 'path': '~/work'},
        {'name': 'Personal Projects', 'path': '~/personal'},
        {'name': 'Scripts', 'path': '~/bin'},
        {'name': 'Web Server', 'path': '/var/www'},
        {'name': 'Logs', 'path': '/var/log'},
        {'name': 'System Config', 'path': '/etc'},
        # Add your own favorites here
    ]
```

### Configuration Format

Each favorite directory entry must have:
- **name**: Display name for the directory
- **path**: Actual path to the directory (supports `~` expansion)

```python
{'name': 'Display Name', 'path': '/actual/path'}
```

### Key Binding

The default key binding for favorites is:
```python
'favorites': ['j', 'J']
```

You can customize this in your config file:
```python
KEY_BINDINGS = {
    # ... other bindings ...
    'favorites': ['j', 'J', 'f'],  # Add 'f' as alternative
}
```

## Usage

### Opening Favorites Dialog
1. Press **J** key (or your configured key)
2. The searchable list dialog opens showing all favorites

### Navigating Favorites
1. Use **↑/↓** arrow keys to navigate through the list
2. Use **Page Up/Down** for fast scrolling
3. Use **Home/End** to jump to first/last item
4. **Type** to search/filter directories by name or path
5. **Backspace** to modify search filter

### Selecting Directory
1. Press **Enter** to navigate to the selected directory
2. Press **ESC** to cancel and close the dialog

### Visual Display
The dialog shows favorites in the format:
```
Name (Full/Path/To/Directory)
```

For example:
```
Home (/Users/username)
Projects (/Users/username/Projects)
Web Server (/var/www)
```

## Implementation Details

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

### Integration Points

#### Key Binding System
```python
elif self.is_key_for_action(key, 'favorites'):
    self.show_favorite_directories()
```

#### Searchable List Dialog
The feature leverages the existing searchable list dialog system:
- Consistent UI with other dialogs
- Full keyboard navigation support
- Search/filter capabilities
- Proper integration with main event loop

#### Pane Management
```python
# Updates current pane to selected directory
current_pane['path'] = target_path
current_pane['selected_index'] = 0
current_pane['scroll_offset'] = 0
current_pane['selected_files'].clear()
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

## Benefits

### Productivity
- **Fast Navigation**: Jump to any favorite directory instantly
- **No Manual Navigation**: Avoid clicking through directory trees
- **Search Support**: Quickly find the directory you need
- **Persistent**: Favorites persist across TFM sessions

### Usability
- **Intuitive**: Simple key press to access favorites
- **Visual**: Clear display of directory names and paths
- **Consistent**: Uses familiar searchable list dialog interface
- **Flexible**: Fully customizable through configuration

### Reliability
- **Robust**: Handles missing directories gracefully
- **Validated**: Only shows directories that actually exist
- **Safe**: No risk of navigating to invalid locations
- **Fallback**: Always has sensible defaults available

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

### Common Issues

#### "No favorite directories configured"
- Check your `~/.tfm/config.py` file
- Ensure `FAVORITE_DIRECTORIES` is properly defined
- Verify the configuration syntax is correct

#### Favorites not showing up
- Check that directory paths exist
- Verify path permissions
- Look for warning messages in the log pane

#### Key binding not working
- Check `KEY_BINDINGS['favorites']` in your config
- Ensure no conflicts with other key bindings
- Try the default 'J' key

### Debug Steps
1. Check configuration loading messages in log pane
2. Verify favorite directories exist on filesystem
3. Test with default configuration
4. Check file permissions for config directory

## Examples

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

The Favorite Directories feature provides a powerful and efficient way to navigate your filesystem, making TFM even more productive for daily file management tasks.