# TFM Application Overview

## Current Version: 0.98

TFM (Terminal File Manager) is a sophisticated terminal-based file manager built with Python's curses library. It provides a dual-pane interface with comprehensive file operations, cloud storage integration, and extensive customization capabilities.

## Core Architecture

### Main Components

#### Application Core
- **tfm_main.py**: Main FileManager class and application logic
- **tfm_config.py**: Configuration system with user customization support
- **tfm_const.py**: Application constants and key definitions
- **tfm_colors.py**: Color scheme management and terminal color support

#### Path and Storage Systems
- **tfm_path.py**: Extended Path implementation supporting local and S3 paths
- **tfm_s3.py**: AWS S3 integration with full pathlib compatibility
- **tfm_cache_manager.py**: Intelligent caching system for remote operations

#### User Interface Components
- **tfm_text_viewer.py**: Built-in text viewer with syntax highlighting
- **tfm_base_list_dialog.py**: Base class for searchable list dialogs
- **tfm_list_dialog.py**: Searchable list selection dialog
- **tfm_search_dialog.py**: File and content search functionality
- **tfm_batch_rename_dialog.py**: Regex-based batch renaming
- **tfm_info_dialog.py**: Scrollable information display
- **tfm_general_purpose_dialog.py**: Flexible dialog system
- **tfm_quick_choice_bar.py**: Status bar quick selection
- **tfm_single_line_text_edit.py**: Single-line text editor component

#### Management Systems
- **tfm_pane_manager.py**: Dual pane management and navigation
- **tfm_log_manager.py**: Logging system with remote monitoring
- **tfm_file_operations.py**: File system operations handler
- **tfm_progress_manager.py**: Progress tracking for long operations
- **tfm_state_manager.py**: Application state persistence
- **tfm_key_bindings.py**: Key binding management system

#### Integration and Extensions
- **tfm_external_programs.py**: External program execution framework
- **tfm_archive.py**: Archive creation and extraction (ZIP, TAR.GZ, TGZ)

## Key Features

### File Management
- **Dual Pane Interface**: Left and right panes for efficient file operations
- **Comprehensive Operations**: Copy, move, delete, rename, create files and directories
- **Batch Operations**: Multi-selection with space bar, regex-based batch renaming
- **Archive Support**: Create and extract ZIP, TAR.GZ, TGZ archives
- **Safety Features**: Confirmation dialogs, conflict resolution, permission checks

### Navigation and Search
- **Smart Navigation**: Arrow keys, Tab switching, directory history
- **Incremental Search**: Real-time filtering as you type
- **Threaded Search**: Non-blocking filename and content search
- **Pattern Filtering**: fnmatch patterns (*.py, test_*, etc.)
- **Jump Dialog**: Intelligent directory scanning with search
- **Favorite Directories**: Customizable bookmarks with quick access

### Text Handling
- **Built-in Text Viewer**: Syntax highlighting for 20+ file formats
- **External Editor Integration**: Configurable text editor support
- **Encoding Support**: UTF-8, Latin-1, CP1252 with automatic detection
- **Search in Files**: Find functionality within viewed text files

### Cloud Storage Integration
- **AWS S3 Support**: Full S3 integration with s3:// URI support
- **Seamless Operations**: All file operations work with S3 objects
- **Intelligent Caching**: TTL-based caching for optimal performance
- **Virtual Directories**: S3 prefix-based directory simulation
- **Mixed Operations**: Copy/move between local and S3 storage

### System Integration
- **Sub-shell Mode**: Environment variables for current state access
- **External Programs**: Configurable external command integration
- **VSCode Integration**: Direct directory and file opening
- **Beyond Compare Integration**: File and directory comparison
- **Remote Log Monitoring**: Network-based log streaming

### Customization
- **Configuration System**: Comprehensive Python-based configuration
- **Key Bindings**: Fully customizable keyboard shortcuts
- **Color Schemes**: Dark/Light themes with runtime switching
- **Progress Animations**: Configurable animation patterns
- **Behavior Settings**: Confirmations, display options, performance tuning

## Command Line Interface

### Basic Usage
```bash
python3 tfm.py                    # Start with default settings
tfm                               # If installed via pip
```

### Directory Specification
```bash
python3 tfm.py --left /projects --right /documents
python3 tfm.py --left . --right ..
```

### Remote Monitoring
```bash
python3 tfm.py --remote-log-port 8888
python3 tools/tfm_log_client.py localhost 8888
```

### Color Testing
```bash
python3 tfm.py --color-test info        # Show current colors
python3 tfm.py --color-test schemes      # List color schemes
python3 tfm.py --color-test diagnose     # Diagnose color issues
```

## Configuration System

### Configuration File
- **Location**: `~/.tfm/config.py`
- **Template**: `src/_config.py`
- **Auto-creation**: Generated from template on first run
- **Live Validation**: Error reporting with fallback to defaults

### Configurable Settings
- **Display**: Color schemes, pane ratios, hidden files
- **Behavior**: Confirmations, sorting, file operations
- **Performance**: Search limits, caching, animation speed
- **Key Bindings**: Complete keyboard customization
- **Directories**: Startup paths, favorites, history limits
- **Programs**: External command integration

## Development Architecture

### Modular Design
- **Component-based**: Each feature in separate module
- **Dialog System**: Reusable UI components
- **Manager Pattern**: Specialized managers for different concerns
- **Event-driven**: Key binding system with configurable actions

### Error Handling
- **Specific Exceptions**: Targeted exception handling
- **Graceful Degradation**: Fallback behavior for missing dependencies
- **User Feedback**: Clear error messages and recovery options

### Testing Framework
- **Unit Tests**: Component-level testing
- **Integration Tests**: Feature interaction testing
- **Demo Scripts**: Interactive feature demonstrations
- **Verification Scripts**: Quick feature validation

## Dependencies

### Required
- **Python 3.9+**: Core language requirement
- **curses**: Terminal UI library (built-in on Unix systems)

### Optional
- **pygments**: Enhanced syntax highlighting
- **boto3**: AWS S3 support
- **windows-curses**: Windows terminal support

## Platform Support
- **macOS**: Full support with native terminal
- **Linux**: Full support with standard terminals
- **Windows**: Supported with Windows Terminal or compatible terminals

## Performance Characteristics

### Optimizations
- **Threaded Operations**: Non-blocking search and file operations
- **Intelligent Caching**: S3 and remote operation caching
- **Lazy Loading**: On-demand resource loading
- **Memory Management**: Configurable limits for large operations

### Scalability
- **Large Directories**: Efficient handling of thousands of files
- **Remote Storage**: Optimized S3 operations with caching
- **Search Performance**: Configurable result limits and threading
- **Memory Usage**: Bounded memory consumption with cleanup

## Security Considerations

### File Operations
- **Permission Checks**: Validates file system permissions
- **Confirmation Dialogs**: User confirmation for destructive operations
- **Path Validation**: Prevents directory traversal attacks

### Cloud Integration
- **AWS Credentials**: Uses standard AWS credential chain
- **Secure Connections**: HTTPS for all S3 operations
- **Access Control**: Respects S3 bucket policies and IAM permissions

## Future Extensibility

### Plugin Architecture
- **External Programs**: Framework for custom tool integration
- **Dialog System**: Extensible UI component system
- **Path System**: Pluggable storage backend support

### Integration Points
- **Configuration**: Python-based configuration for flexibility
- **Key Bindings**: Programmable keyboard shortcuts
- **Color Schemes**: Customizable appearance system
- **Progress System**: Extensible progress tracking

This overview provides a comprehensive understanding of TFM's current architecture, capabilities, and design principles as of version 0.98.