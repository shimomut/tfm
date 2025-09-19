# TFM Configuration System

TFM includes a comprehensive configuration system that allows users to customize behavior, key bindings, and appearance through a Python configuration file.

## Configuration File Location

**User Config**: `~/.tfm/config.py`
**Template File**: `_config.py` (in TFM installation directory)

- **Auto-Creation**: If the config file doesn't exist, TFM automatically creates one from the template on first launch
- **Template-Based**: Default configuration is maintained in a separate `_config.py` template file
- **Python Format**: Configuration is stored as a Python class for flexibility and validation
- **User Directory**: User config located in the user's home directory for per-user customization
- **Clean Separation**: Template and user config are separate for easier maintenance

## Configuration Structure

### Config Class Format

```python
class Config:
    """User configuration for TFM"""
    
    # Display settings
    SHOW_HIDDEN_FILES = False
    DEFAULT_LEFT_PANE_RATIO = 0.5
    DEFAULT_LOG_HEIGHT_RATIO = 0.25
    
    # Sorting settings
    DEFAULT_SORT_MODE = 'name'
    DEFAULT_SORT_REVERSE = False
    
    # ... more settings
```

## Available Configuration Options

### Display Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `SHOW_HIDDEN_FILES` | bool | `False` | Show hidden files by default |
| `DEFAULT_LEFT_PANE_RATIO` | float | `0.5` | Left pane width ratio (0.1-0.9) |
| `DEFAULT_LOG_HEIGHT_RATIO` | float | `0.25` | Log pane height ratio (0.1-0.5) |

### Sorting Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `DEFAULT_SORT_MODE` | str | `'name'` | Default sort mode: 'name', 'size', 'date' |
| `DEFAULT_SORT_REVERSE` | bool | `False` | Default reverse sort order |

### Color Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `USE_COLORS` | bool | `True` | Enable color display |
| `COLOR_SCHEME` | str | `'default'` | Color scheme: 'default', 'dark', 'light' |

### Behavior Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `CONFIRM_DELETE` | bool | `True` | Show confirmation for delete operations |
| `CONFIRM_QUIT` | bool | `True` | Show confirmation when quitting |
| `AUTO_REFRESH` | bool | `True` | Auto-refresh file lists |

### Directory Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `STARTUP_LEFT_PATH` | str/None | `None` | Left pane startup path (None = current dir) |
| `STARTUP_RIGHT_PATH` | str/None | `None` | Right pane startup path (None = home dir) |

### Performance Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `MAX_LOG_MESSAGES` | int | `1000` | Maximum log messages to keep |
| `REFRESH_INTERVAL` | float | `1.0` | File refresh interval in seconds |

### Info Dialog Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `INFO_DIALOG_WIDTH_RATIO` | float | `0.8` | Info dialog width as screen ratio |
| `INFO_DIALOG_HEIGHT_RATIO` | float | `0.8` | Info dialog height as screen ratio |
| `INFO_DIALOG_MIN_WIDTH` | int | `20` | Minimum dialog width |
| `INFO_DIALOG_MIN_HEIGHT` | int | `10` | Minimum dialog height |

## Key Bindings Configuration

### Customizable Key Bindings

```python
KEY_BINDINGS = {
    'quit': ['q', 'Q'],
    'help': ['?', 'h'],
    'toggle_hidden': ['H'],
    'search': ['f', 'F'],
    'file_operations': ['m', 'M'],
    'sort_menu': ['s', 'S'],
    'file_details': ['i', 'I'],
    'quick_sort_name': ['1'],
    'quick_sort_size': ['2'],
    'quick_sort_date': ['3'],
    'select_file': [' '],  # Space
    'select_all_files': ['a'],
    'select_all_items': ['A'],
    'sync_panes': ['o', 'O'],
}
```

### Key Binding Features

- **Multiple Keys**: Each action can have multiple key bindings
- **Case Sensitive**: Separate bindings for uppercase/lowercase
- **Special Keys**: Support for space and other special characters
- **Validation**: Invalid key bindings are ignored with warnings

## File Associations (Future Use)

```python
FILE_ASSOCIATIONS = {
    '.txt': 'text_editor',
    '.py': 'python_editor',
    '.md': 'markdown_viewer',
    '.jpg': 'image_viewer',
    '.png': 'image_viewer',
    '.pdf': 'pdf_viewer',
}
```

## Configuration Management

### Automatic Loading

1. **Startup Check**: TFM checks for `~/.tfm/config.py` on launch
2. **Auto-Creation**: Creates default config from `_config.py` template if file doesn't exist
3. **Template-Based**: Uses separate template file for clean default configuration
4. **Error Handling**: Falls back to built-in defaults if config is invalid
5. **Validation**: Validates configuration values and reports errors

### Configuration API

```python
import tfm_config

# Get current configuration
config = tfm_config.get_config()

# Reload configuration from file
tfm_config.reload_config()

# Check key bindings
is_bound = tfm_config.is_key_bound_to('q', 'quit')

# Get startup paths
left_path, right_path = tfm_config.get_startup_paths()
```

## Customization Examples

### Example 1: Change Default Directories

```python
class Config:
    # Start left pane in projects directory
    STARTUP_LEFT_PATH = "~/projects"
    
    # Start right pane in downloads
    STARTUP_RIGHT_PATH = "~/Downloads"
```

### Example 2: Customize Key Bindings

```python
class Config:
    KEY_BINDINGS = {
        'quit': ['q'],  # Remove 'Q' binding
        'file_details': ['i', 'I', 'd'],  # Add 'd' for details
        'search': ['/', 'f'],  # Add '/' like vim
        # ... other bindings
    }
```

### Example 3: Adjust Display Settings

```python
class Config:
    # Show hidden files by default
    SHOW_HIDDEN_FILES = True
    
    # Wider left pane (70/30 split)
    DEFAULT_LEFT_PANE_RATIO = 0.7
    
    # Smaller log pane
    DEFAULT_LOG_HEIGHT_RATIO = 0.15
    
    # Disable quit confirmation
    CONFIRM_QUIT = False
```

### Example 4: Performance Tuning

```python
class Config:
    # Keep more log messages
    MAX_LOG_MESSAGES = 5000
    
    # Faster refresh
    REFRESH_INTERVAL = 0.5
    
    # Larger info dialogs
    INFO_DIALOG_WIDTH_RATIO = 0.9
    INFO_DIALOG_HEIGHT_RATIO = 0.9
```

## Configuration Validation

### Automatic Validation

- **Range Checks**: Ratios must be within valid ranges
- **Type Validation**: Settings must be correct types
- **Value Validation**: Enum values are checked
- **Error Reporting**: Invalid settings are reported with warnings

### Validation Rules

- `DEFAULT_LEFT_PANE_RATIO`: Must be between 0.1 and 0.9
- `DEFAULT_LOG_HEIGHT_RATIO`: Must be between 0.1 and 0.5
- `DEFAULT_SORT_MODE`: Must be 'name', 'size', or 'date'
- `COLOR_SCHEME`: Must be 'default', 'dark', or 'light'

## Error Handling

### Configuration Errors

1. **File Not Found**: Creates default configuration
2. **Syntax Errors**: Falls back to built-in defaults
3. **Missing Config Class**: Uses default configuration
4. **Invalid Values**: Uses defaults for invalid settings
5. **Permission Errors**: Reports warning and uses defaults

### Fallback Behavior

- **Graceful Degradation**: TFM always starts even with config errors
- **Built-in Defaults**: Comprehensive default configuration available
- **Error Logging**: Configuration errors are logged to the log pane
- **User Notification**: Clear messages about configuration issues

## Template System

### Configuration Template

TFM uses a template-based configuration system for better maintainability:

- **Template File**: `_config.py` contains the default configuration template
- **Clean Defaults**: Template is maintained separately from user configuration
- **Easy Updates**: Template can be updated without affecting user configs
- **Consistent Creation**: All new user configs are created from the same template

### Template Benefits

1. **Maintainability**: Default configuration is in a separate, version-controlled file
2. **Consistency**: All users get the same default configuration structure
3. **Documentation**: Template includes comprehensive comments and examples
4. **Upgrades**: Template can be updated independently of user configurations

### Template Structure

The `_config.py` template includes:
- Complete configuration class with all available options
- Detailed comments explaining each setting
- Example values and valid ranges
- Organized sections for different setting categories

## Advanced Features

### Dynamic Configuration

- **Runtime Changes**: Some settings can be changed during runtime
- **Configuration Reload**: Reload config without restarting TFM
- **Validation Feedback**: Real-time validation of configuration changes

### Future Enhancements

- **GUI Configuration Editor**: Visual configuration editor
- **Multiple Profiles**: Support for different configuration profiles
- **Plugin System**: Configuration for custom plugins
- **Theme System**: Advanced color theme configuration

## Troubleshooting

### Common Issues

1. **Config File Not Loading**:
   - Check file permissions
   - Verify Python syntax
   - Ensure Config class exists

2. **Invalid Key Bindings**:
   - Check key binding format
   - Ensure keys are single characters
   - Verify action names are correct

3. **Path Issues**:
   - Use absolute paths or ~ for home directory
   - Ensure directories exist
   - Check path permissions

### Debug Mode

Enable debug mode in configuration:

```python
class Config:
    DEBUG_MODE = True
    LOG_LEVEL = 'DEBUG'
```

This provides detailed logging of configuration loading and validation.

## Configuration File Example

Here's a complete example configuration file:

```python
#!/usr/bin/env python3
\"\"\"
TFM User Configuration - Custom Setup
\"\"\"

class Config:
    # Display preferences
    SHOW_HIDDEN_FILES = True
    DEFAULT_LEFT_PANE_RATIO = 0.6
    DEFAULT_LOG_HEIGHT_RATIO = 0.2
    
    # Sorting preferences
    DEFAULT_SORT_MODE = 'date'
    DEFAULT_SORT_REVERSE = True
    
    # Behavior
    CONFIRM_DELETE = True
    CONFIRM_QUIT = False
    
    # Startup directories
    STARTUP_LEFT_PATH = \"~/projects\"
    STARTUP_RIGHT_PATH = \"~/Downloads\"
    
    # Custom key bindings
    KEY_BINDINGS = {
        'quit': ['q'],
        'file_details': ['i', 'd'],
        'search': ['/', 'f'],
        'sort_menu': ['s'],
        'quick_sort_name': ['1'],
        'quick_sort_size': ['2'],
        'quick_sort_date': ['3'],
        'select_file': [' '],
        'select_all_files': ['a'],
        'select_all_items': ['A'],
        'sync_panes': ['o', 'O'],
    }
    
    # Performance
    MAX_LOG_MESSAGES = 2000
    INFO_DIALOG_WIDTH_RATIO = 0.85
```

The configuration system provides extensive customization while maintaining simplicity and reliability through automatic defaults and comprehensive error handling.