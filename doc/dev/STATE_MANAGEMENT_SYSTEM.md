# State Management System

## Overview

The State Management System provides persistent application state across TFM sessions. It saves and restores user preferences, window geometry, cursor positions, and other session data to provide a seamless user experience.

## Architecture

### Core Classes

**StateManager (Base Class)**
- Abstract base class defining state management interface
- Provides common functionality for state persistence
- Handles serialization and deserialization
- Manages state file I/O

**TFMStateManager (Concrete Implementation)**
- TFM-specific state management implementation
- Manages file manager state (cursor positions, paths)
- Handles window geometry persistence
- Stores user preferences and history

### State Categories

The system manages several categories of state:

1. **Window State**: Position, size, maximized status
2. **Navigation State**: Current directories, cursor positions
3. **View State**: Sort order, hidden files visibility
4. **History State**: Recent directories, search history
5. **Preference State**: User preferences and settings

## Implementation Details

### State Storage Format

State is stored in JSON format for human readability:

```json
{
  "version": "1.0",
  "window": {
    "x": 100,
    "y": 100,
    "width": 800,
    "height": 600,
    "maximized": false
  },
  "panes": {
    "left": {
      "path": "/home/user/documents",
      "cursor": 5,
      "scroll": 0
    },
    "right": {
      "path": "/home/user/downloads",
      "cursor": 2,
      "scroll": 0
    }
  },
  "preferences": {
    "show_hidden": false,
    "sort_by": "name",
    "color_scheme": "default"
  }
}
```

### State File Location

State files are stored in platform-specific locations:

- **Linux/macOS**: `~/.config/tfm/state.json`
- **Windows**: `%APPDATA%\tfm\state.json`

### State Lifecycle

**Initialization**:
1. Load state file on startup
2. Validate state data
3. Apply defaults for missing values
4. Restore application state

**Runtime**:
1. Track state changes
2. Debounce frequent updates
3. Queue state saves

**Shutdown**:
1. Collect current state
2. Serialize to JSON
3. Write to state file
4. Handle write errors gracefully

## Key Methods

### StateManager Base Class

```python
class StateManager:
    def load_state(self) -> dict:
        """Load state from persistent storage."""
        
    def save_state(self, state: dict) -> bool:
        """Save state to persistent storage."""
        
    def get_default_state(self) -> dict:
        """Return default state values."""
        
    def validate_state(self, state: dict) -> bool:
        """Validate state data integrity."""
```

### TFMStateManager Methods

```python
class TFMStateManager(StateManager):
    def save_window_geometry(self, x, y, width, height):
        """Save window position and size."""
        
    def restore_window_geometry(self) -> tuple:
        """Restore window position and size."""
        
    def save_pane_state(self, pane_id, path, cursor, scroll):
        """Save pane navigation state."""
        
    def restore_pane_state(self, pane_id) -> dict:
        """Restore pane navigation state."""
        
    def save_preference(self, key, value):
        """Save user preference."""
        
    def get_preference(self, key, default=None):
        """Get user preference with default."""
```

## State Persistence Strategy

### Debouncing

To avoid excessive disk writes:

- **Delay Writes**: Wait 1 second after last change
- **Batch Updates**: Combine multiple changes
- **Cancel Pending**: Cancel pending write on new change

### Error Handling

The system handles various error conditions:

- **File Not Found**: Create new state file with defaults
- **Parse Errors**: Use defaults, backup corrupted file
- **Write Errors**: Log error, continue with in-memory state
- **Permission Errors**: Fall back to temporary location

### Migration

State format versioning supports migration:

```python
def migrate_state(old_state, old_version, new_version):
    """Migrate state from old version to new version."""
    if old_version < "1.1":
        # Add new fields with defaults
        old_state["new_field"] = default_value
    return old_state
```

## Integration Points

### Window Manager Integration

The state manager integrates with window management:

- **Geometry Persistence**: Save/restore window position and size
- **Maximized State**: Remember maximized/normal state
- **Multi-Monitor**: Handle multi-monitor configurations

### File Manager Integration

Integrates with file manager components:

- **Pane State**: Save/restore pane paths and cursors
- **Tab State**: Save/restore tab configurations
- **Selection State**: Remember selections across sessions

### Configuration System

Works alongside the configuration system:

- **Preferences**: Store user preferences
- **Overrides**: State can override config defaults
- **Separation**: State (runtime) vs Config (settings)

## Performance Considerations

### Memory Usage

- **Lazy Loading**: Load state only when needed
- **Minimal Storage**: Store only essential state
- **Cleanup**: Remove stale state data

### Disk I/O

- **Async Writes**: Write state asynchronously
- **Atomic Writes**: Use atomic file operations
- **Backup**: Keep backup of last good state

## Security Considerations

### Sensitive Data

- **No Passwords**: Never store passwords in state
- **Path Privacy**: Consider privacy of stored paths
- **Permissions**: Restrict state file permissions

### Data Validation

- **Input Validation**: Validate all loaded state data
- **Type Checking**: Ensure correct data types
- **Range Checking**: Validate numeric ranges

## Testing Considerations

Key areas for testing:

- **Save/Restore**: Verify state persists correctly
- **Defaults**: Test default state generation
- **Migration**: Test version migration
- **Error Handling**: Test error conditions
- **Corruption**: Test corrupted state file handling
- **Concurrent Access**: Test multiple instances

## Related Documentation

- [Window Geometry Persistence Feature](../WINDOW_GEOMETRY_PERSISTENCE_FEATURE.md) - User documentation
- [Configuration System](CONFIGURATION_SYSTEM.md) - Configuration management
- [Project Structure](PROJECT_STRUCTURE.md) - File locations

## Future Enhancements

Potential improvements:

- **Cloud Sync**: Sync state across devices
- **Profile Support**: Multiple state profiles
- **Undo/Redo**: State history with undo
- **Export/Import**: Export state for backup
- **Encryption**: Encrypt sensitive state data
- **Compression**: Compress large state files
