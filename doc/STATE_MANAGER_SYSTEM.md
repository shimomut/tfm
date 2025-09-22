# TFM State Manager System

## Overview

The TFM State Manager provides persistent application state management using SQLite database. It safely handles multiple TFM instances accessing the same state database and automatically creates the database at `~/.tfm/state.db`.

## Features

### Core Capabilities
- **Persistent State Storage**: Saves application state across TFM sessions
- **Multi-Instance Safety**: Handles concurrent access from multiple TFM processes
- **Automatic Database Creation**: Creates and initializes database automatically
- **Thread-Safe Operations**: Uses proper locking for concurrent access
- **Graceful Error Handling**: Continues operation even if state operations fail
- **Session Management**: Tracks active TFM instances and cleans up stale sessions

### State Types Managed
- **Pane State**: Directory paths, selection, scroll position, sort settings, filters
- **Window Layout**: Pane width ratios, log pane height
- **Recent Directories**: History of visited directories for quick navigation
- **Search History**: Previously used search terms for auto-completion
- **Path Cursor History**: Cursor positions for each visited directory path
- **Session Information**: Active TFM instances with heartbeat tracking

## Architecture

### Database Schema

```sql
-- Application state table
CREATE TABLE app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,           -- JSON serialized data
    updated_at REAL NOT NULL,      -- Unix timestamp
    instance_id TEXT               -- TFM instance identifier
);

-- Session tracking table
CREATE TABLE sessions (
    instance_id TEXT PRIMARY KEY,
    pid INTEGER NOT NULL,          -- Process ID
    started_at REAL NOT NULL,      -- Session start time
    last_seen REAL NOT NULL,       -- Last heartbeat time
    hostname TEXT                  -- Machine hostname
);
```

### Class Hierarchy

```
StateManager (Base class)
├── Basic state operations (get/set/delete)
├── Database connection management
├── JSON serialization/deserialization
├── Thread-safe operations
└── Error handling

TFMStateManager (TFM-specific)
├── Inherits from StateManager
├── Session management
├── TFM-specific convenience methods
├── Pane state operations
├── Window layout management
└── History management
```

## Usage

### Basic State Operations

```python
from tfm_state_manager import get_state_manager

# Get the global state manager
state_manager = get_state_manager()

# Save simple values
state_manager.set_state("user_preference", "dark_theme")

# Save complex data
pane_data = {
    'path': '/home/user',
    'selected_index': 5,
    'sort_mode': 'size'
}
state_manager.set_state("left_pane", pane_data)

# Load values
theme = state_manager.get_state("user_preference", "light_theme")
pane_info = state_manager.get_state("left_pane")
```

### TFM-Specific Operations

```python
# Save pane state
pane_data = {
    'path': current_pane['path'],
    'selected_index': current_pane['selected_index'],
    'scroll_offset': current_pane['scroll_offset'],
    'sort_mode': current_pane['sort_mode'],
    'sort_reverse': current_pane['sort_reverse'],
    'filter_pattern': current_pane['filter_pattern'],
    'selected_files': list(current_pane['selected_files'])
}
state_manager.save_pane_state('left', pane_data)

# Load pane state
loaded_state = state_manager.load_pane_state('left')
if loaded_state and Path(loaded_state['path']).exists():
    current_pane['path'] = Path(loaded_state['path'])
    current_pane['sort_mode'] = loaded_state['sort_mode']
    # ... restore other settings

# Window layout
state_manager.save_window_layout(0.6, 0.25)  # 60% left pane, 25% log
layout = state_manager.load_window_layout()

# Recent directories
state_manager.add_recent_directory('/home/user/projects')
recent_dirs = state_manager.load_recent_directories()

# Search history
state_manager.add_search_term('*.py')
search_history = state_manager.load_search_history()

# Path cursor history
state_manager.save_path_cursor_position('/home/user/projects', 'main.py')
cursor_filename = state_manager.load_path_cursor_position('/home/user/projects')
all_cursor_positions = state_manager.get_all_path_cursor_positions()
state_manager.clear_path_cursor_history()  # Clear all cursor positions
```

### Session Management

```python
# Sessions are automatically managed
# Get active sessions
sessions = state_manager.get_active_sessions()
for session in sessions:
    print(f"Instance: {session['instance_id']}")
    print(f"PID: {session['pid']}")
    print(f"Host: {session['hostname']}")

# Update heartbeat (done automatically in main loop)
state_manager.update_session_heartbeat()

# Cleanup (done automatically on exit)
state_manager.cleanup_session()
```

## Integration with TFM

### Initialization

The state manager is initialized in `FileManager.__init__()`:

```python
self.state_manager = get_state_manager()
self.load_application_state()
```

### State Loading

Application state is loaded during startup:

```python
def load_application_state(self):
    # Load window layout
    layout = self.state_manager.load_window_layout()
    if layout:
        self.pane_manager.left_pane_ratio = layout['left_pane_ratio']
        self.log_height_ratio = layout['log_height_ratio']
    
    # Load pane states
    left_state = self.state_manager.load_pane_state('left')
    if left_state and Path(left_state['path']).exists():
        self.pane_manager.left_pane['path'] = Path(left_state['path'])
        # ... restore other pane settings
```

### State Saving

Application state is saved during shutdown:

```python
def save_application_state(self):
    # Save window layout
    self.state_manager.save_window_layout(
        self.pane_manager.left_pane_ratio,
        self.log_height_ratio
    )
    
    # Save pane states
    self.state_manager.save_pane_state('left', self.pane_manager.left_pane)
    self.state_manager.save_pane_state('right', self.pane_manager.right_pane)
    
    # Add current directories to recent directories
    self.state_manager.add_recent_directory(str(self.pane_manager.left_pane['path']))
    self.state_manager.add_recent_directory(str(self.pane_manager.right_pane['path']))
```

### Search History Integration

Search terms are automatically saved to history:

```python
def handle_search_dialog_input(self, key):
    # ... handle search input
    if action == 'navigate':
        # Save search term to history
        search_term = self.search_dialog.pattern_editor.text.strip()
        if search_term:
            self.add_search_to_history(search_term)
```

### Cursor History Integration

The PaneManager now uses persistent cursor history instead of in-memory storage:

```python
# PaneManager initialization with state manager
self.pane_manager = PaneManager(self.config, left_startup_path, right_startup_path, self.state_manager)

# Cursor positions are automatically saved when navigating
def save_cursor_position(self, pane_data):
    current_file = pane_data['files'][pane_data['selected_index']]
    current_dir = str(pane_data['path'])
    
    if self.state_manager:
        cursor_history = self.state_manager.get_state("path_cursor_history", {})
        cursor_history[current_dir] = current_file.name
        self.state_manager.set_state("path_cursor_history", cursor_history)

# Cursor positions are automatically restored when entering directories
def restore_cursor_position(self, pane_data, display_height):
    current_dir = str(pane_data['path'])
    
    if self.state_manager:
        cursor_history = self.state_manager.get_state("path_cursor_history", {})
        if current_dir in cursor_history:
            target_filename = cursor_history[current_dir]
            # ... find and restore cursor to target_filename
```

## Multi-Instance Safety

### Concurrency Handling

The state manager uses several mechanisms to handle multiple TFM instances safely:

1. **WAL Mode**: SQLite Write-Ahead Logging for better concurrency
2. **Connection Timeouts**: 30-second timeout for database operations
3. **Retry Logic**: Exponential backoff for locked database situations
4. **Thread Locking**: RLock for thread-safe operations within a process
5. **Graceful Degradation**: Operations continue even if state saving fails

### Database Configuration

```python
# Enable WAL mode for better concurrency
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.execute('PRAGMA temp_store=MEMORY')
conn.execute('PRAGMA mmap_size=268435456')  # 256MB
```

### Error Recovery

```python
@contextmanager
def _get_connection(self):
    for attempt in range(self._retry_attempts):
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=self._connection_timeout)
            yield conn
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < self._retry_attempts - 1:
                time.sleep(self._retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                raise
```

## Performance Considerations

### Optimization Features
- **Connection Pooling**: Reuses database connections efficiently
- **Batch Operations**: `get_all_states()` for bulk retrieval
- **Indexed Queries**: Database indexes on frequently queried columns
- **Memory Storage**: Temporary data stored in memory
- **Lazy Loading**: State loaded only when needed

### Performance Characteristics
- **2000 operations**: ~5 seconds (set/get pairs)
- **1000 bulk retrieval**: ~0.01 seconds
- **Concurrent access**: Handles multiple instances without conflicts
- **Memory usage**: Minimal overhead, JSON serialization

## Error Handling

### Graceful Degradation
- **Database Unavailable**: Operations return default values
- **Serialization Errors**: Invalid data is rejected, operation continues
- **Permission Errors**: Warnings logged, application continues
- **Corruption Recovery**: Database recreated if corrupted

### Error Examples

```python
# Serialization error handling
try:
    serialized = json.dumps(value)
except (TypeError, ValueError) as e:
    print(f"Warning: Could not serialize value: {e}")
    return False

# Database error handling
try:
    with self._get_connection() as conn:
        # ... database operations
except Exception as e:
    print(f"Warning: Database operation failed: {e}")
    return default_value
```

## Configuration

### Database Location
- **Default**: `~/.tfm/state.db`
- **Custom**: Can be overridden in StateManager constructor
- **Auto-Creation**: Directory created automatically if needed

### Limits and Defaults
- **Recent Directories**: 50 entries (configurable)
- **Search History**: 100 entries (configurable)
- **Session Timeout**: 5 minutes (300 seconds)
- **Connection Timeout**: 30 seconds
- **Retry Attempts**: 3 with exponential backoff

## Testing

### Test Coverage
- **Unit Tests**: Basic state operations, serialization, error handling
- **Integration Tests**: TFM-specific operations, multi-instance scenarios
- **Concurrency Tests**: Multiple threads accessing same database
- **Performance Tests**: Large datasets, bulk operations
- **Error Tests**: Database corruption, permission errors, invalid data

### Running Tests

```bash
# Run basic state manager tests
python test/test_state_manager.py

# Run integration tests
python test/test_state_integration.py
```

## Future Enhancements

### Planned Features
- **State Versioning**: Track state changes over time
- **Backup/Restore**: Export/import state data
- **Compression**: Compress large state data
- **Encryption**: Encrypt sensitive state data
- **Cloud Sync**: Synchronize state across machines
- **State Analytics**: Usage patterns and statistics

### Migration Support
- **Schema Versioning**: Handle database schema changes
- **Data Migration**: Convert old state formats
- **Backward Compatibility**: Support older TFM versions

## Troubleshooting

### Common Issues

1. **Database Locked**
   - Multiple instances accessing database simultaneously
   - Solution: Automatic retry with exponential backoff

2. **Permission Denied**
   - Cannot create `~/.tfm/` directory
   - Solution: Check home directory permissions

3. **Serialization Errors**
   - Complex objects that can't be JSON serialized
   - Solution: Graceful error handling, operation continues

4. **Stale Sessions**
   - Old session entries not cleaned up
   - Solution: Automatic cleanup of sessions older than 5 minutes

### Debug Information

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check active sessions
sessions = state_manager.get_active_sessions()
print(f"Active sessions: {len(sessions)}")

# Check database file
db_path = Path.home() / '.tfm' / 'state.db'
print(f"Database exists: {db_path.exists()}")
print(f"Database size: {db_path.stat().st_size if db_path.exists() else 0} bytes")
```

## Security Considerations

### Data Protection
- **Local Storage**: Data stored locally, not transmitted
- **File Permissions**: Database file uses standard file permissions
- **No Sensitive Data**: Only application state, no passwords or keys
- **JSON Serialization**: Human-readable format, no binary data

### Access Control
- **User-Level**: Each user has their own state database
- **Process-Level**: Multiple TFM instances share state safely
- **No Network Access**: Purely local file-based storage

## Conclusion

The TFM State Manager provides robust, persistent state management that enhances the user experience by remembering application state across sessions. Its multi-instance safety features ensure reliable operation even when multiple TFM processes are running simultaneously.

The system is designed to be transparent to the user - it works automatically in the background, gracefully handling errors and ensuring that TFM continues to function even if state operations fail.