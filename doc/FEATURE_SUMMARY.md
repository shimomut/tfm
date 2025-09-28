# TFM Feature Summary

## Version 0.97 - Complete Feature List

This document provides a comprehensive overview of all features available in TFM (Terminal File Manager) version 0.97.

## Core Interface Features

### Dual Pane System
- **Left and Right Panes**: Independent file browsing with synchronized operations
- **Active Pane Highlighting**: Visual indication of currently focused pane
- **Tab Switching**: Quick pane switching with Tab key
- **Pane Synchronization**: Sync directories and cursor positions between panes
- **Resizable Layout**: Adjustable pane boundaries with bracket keys

### Navigation System
- **Arrow Key Navigation**: Intuitive file and directory browsing
- **Directory Entry**: Enter directories with Enter key
- **Parent Directory**: Backspace to go up one level
- **Home/End Navigation**: Jump to first/last file in list
- **Page Navigation**: Page Up/Down for large directories

### Display and Visualization
- **File Information**: Size, date, permissions display
- **Hidden Files Toggle**: Show/hide hidden files with '.' key
- **Color Schemes**: Dark and Light themes with runtime switching
- **Status Bar**: Current path, file count, operation status
- **Log Pane**: Bottom pane for system messages and output

## File Operations

### Basic Operations
- **Copy Files**: Copy selected files between panes (C key)
- **Move Files**: Move selected files between panes (M key)
- **Delete Files**: Delete selected files with confirmation (K key)
- **Rename Files**: Single file rename (R key)
- **Create Files**: Create new text files with editor integration (E key)
- **Create Directories**: Create new directories (F7 or M with no selection)

### Advanced Operations
- **Batch Rename**: Regex-based renaming for multiple files
- **Multi-Selection**: Select multiple files with Space bar
- **Select All**: Select all files (a) or all items including directories (A)
- **Archive Creation**: Create ZIP, TAR.GZ, TGZ archives (P key)
- **Archive Extraction**: Extract archives to opposite pane (U key)
- **File Comparison**: Compare selected files between panes

### Safety Features
- **Confirmation Dialogs**: User confirmation for destructive operations
- **Conflict Resolution**: Handle file name conflicts during operations
- **Permission Checks**: Validate file system permissions
- **Undo Prevention**: Clear warnings about irreversible operations

## Search and Filtering

### Search Capabilities
- **Incremental Search**: Real-time file filtering as you type (f key)
- **Threaded Filename Search**: Non-blocking search with live results (F key)
- **Content Search**: Search within file contents with grep functionality (G key)
- **Pattern Filtering**: fnmatch patterns like *.py, test_*, etc. (; key)
- **Search Cancellation**: Automatic cancellation when patterns change

### Filter Management
- **Active Filters**: Visual indication of applied filters
- **Filter Clearing**: Clear filters from current pane (: key)
- **Result Limiting**: Configurable maximum results to prevent memory issues
- **Search Animation**: Progress indicators for long-running searches

## Text Handling

### Built-in Text Viewer
- **Syntax Highlighting**: Support for 20+ file formats
- **Line Numbers**: Toggle line numbers display
- **Horizontal Scrolling**: Navigate wide text files
- **Search in Files**: Find functionality within viewed files
- **Multiple Encodings**: UTF-8, Latin-1, CP1252 support
- **File Format Detection**: Automatic file type recognition

### Supported File Formats
- **Programming Languages**: Python, JavaScript, Java, C/C++, Go, Rust, PHP, Ruby, Shell
- **Markup Languages**: HTML, XML, Markdown, reStructuredText
- **Data Formats**: JSON, YAML, CSV, TSV, TOML
- **Configuration Files**: INI, Dockerfile, Makefile

### Text Editor Integration
- **External Editor**: Configurable text editor support (vim, nano, code, etc.)
- **Direct Editing**: Edit files with 'e' key
- **New File Creation**: Create and edit new files with 'E' key

## Cloud Storage Integration

### AWS S3 Support
- **S3 URI Navigation**: Navigate using s3://bucket-name/path format
- **Seamless Integration**: S3 objects appear as regular files
- **Full Operations**: All file operations work with S3 objects
- **Mixed Operations**: Copy/move between local and S3 storage
- **Virtual Directories**: S3 prefix-based directory simulation

### S3 Features
- **Pathlib Compatibility**: Standard pathlib operations on S3 paths
- **Intelligent Caching**: TTL-based caching for optimal performance
- **Batch Operations**: Multi-select operations on S3 objects
- **Text Editing**: Edit S3 text files directly
- **Archive Operations**: Create/extract archives with S3 objects

### Requirements
- **boto3**: AWS SDK for Python
- **AWS Credentials**: Configured via AWS CLI, environment variables, or IAM roles

## System Integration

### Sub-shell Mode
- **Environment Variables**: Access to TFM state in shell
- **Directory Variables**: TFM_LEFT_DIR, TFM_RIGHT_DIR, TFM_THIS_DIR, TFM_OTHER_DIR
- **Selection Variables**: TFM_LEFT_SELECTED, TFM_RIGHT_SELECTED, etc.
- **Shell Prompt**: [TFM] indicator in shell prompt

### External Programs
- **Custom Commands**: Configurable external program integration
- **Environment Access**: Programs receive TFM environment variables
- **Auto-return Option**: Automatic return to TFM after program execution
- **Script Integration**: Support for shell scripts and executables

### IDE Integration
- **VSCode Integration**: Direct directory and file opening in VS Code
- **Beyond Compare**: File and directory comparison integration
- **Git Integration**: Git status and log commands
- **Custom Tools**: Framework for adding custom development tools

## Advanced Features

### Directory Management
- **Favorite Directories**: Customizable bookmarks with quick access (J key)
- **Jump Dialog**: Intelligent directory scanning and navigation
- **Directory History**: Per-pane history with configurable limits (H key)
- **Command Line Directories**: Override startup directories with --left/--right

### Progress and Animation
- **Progress Tracking**: Visual progress for long operations
- **Configurable Animations**: Multiple animation patterns (spinner, dots, progress bar, etc.)
- **Animation Speed**: Adjustable animation frame rates
- **Background Operations**: Non-blocking operations with progress display

### State Management
- **State Persistence**: Automatic saving of pane positions and settings
- **Cursor Restoration**: Restore cursor positions on startup
- **History Management**: Configurable history limits and cleanup
- **Session Recovery**: Restore previous session state

## Configuration System

### Configuration File
- **Location**: ~/.tfm/config.py
- **Auto-creation**: Generated from template on first run
- **Python-based**: Full Python configuration flexibility
- **Live Validation**: Error reporting with fallback to defaults

### Customizable Settings
- **Key Bindings**: Complete keyboard shortcut customization
- **Color Schemes**: Dark/Light themes with custom colors
- **Display Options**: Pane ratios, log height, hidden files
- **Behavior Settings**: Confirmations, sorting, file operations
- **Performance Tuning**: Search limits, caching, animation settings

### Key Binding System
- **Selection-aware Bindings**: Actions can require specific selection states
- **Multiple Key Support**: Assign multiple keys to the same action
- **Context-sensitive Operations**: Different behavior based on selection state
- **Comprehensive Coverage**: All TFM features have configurable bindings

## Remote Monitoring

### Log Monitoring
- **Network Streaming**: Stream logs to remote terminals
- **Multiple Clients**: Support for multiple monitoring connections
- **Color-coded Output**: Different log sources in different colors
- **JSON Format**: Structured data for easy parsing

### Client Features
- **TFM Log Client**: Dedicated monitoring client (tfm_log_client.py)
- **Network Connectivity**: Connect to local or remote TFM instances
- **Graceful Handling**: Manages connection errors and disconnections
- **Keyboard Interrupt**: Clean exit with Ctrl+C

## Sorting and Organization

### Sort Options
- **Multiple Criteria**: Name, size, date, extension, type
- **Quick Sort Keys**: Number keys (1-4) for common sort options
- **Reverse Sorting**: Toggle reverse order for any sort criteria
- **Sort Menu**: Interactive sorting menu with search (S key)

### File Organization
- **Extension Separation**: Optional separate extension column
- **File Type Recognition**: Intelligent file type detection
- **Directory Prioritization**: Directories listed before files
- **Case-sensitive Sorting**: Configurable case sensitivity

## Help and Documentation

### Built-in Help
- **Help Dialog**: Comprehensive help accessible with '?' key
- **Organized Sections**: Navigation, operations, search, sorting coverage
- **Scrollable Content**: Navigate help with arrow keys and page keys
- **Context-sensitive**: Shows relevant shortcuts for current mode

### Documentation
- **Feature Documentation**: Detailed guides for each feature
- **Implementation Summaries**: Development progress tracking
- **User Guides**: Usage instructions and examples
- **Technical Specifications**: System design and architecture

## Performance Features

### Optimization
- **Threaded Operations**: Non-blocking search and file operations
- **Intelligent Caching**: S3 and remote operation caching
- **Lazy Loading**: On-demand resource loading
- **Memory Management**: Configurable limits for large operations

### Scalability
- **Large Directories**: Efficient handling of thousands of files
- **Remote Storage**: Optimized S3 operations with caching
- **Search Performance**: Configurable result limits and threading
- **Memory Usage**: Bounded memory consumption with cleanup

## Platform Support

### Operating Systems
- **macOS**: Full support with native terminal
- **Linux**: Full support with standard terminals
- **Windows**: Supported with Windows Terminal or compatible terminals

### Terminal Compatibility
- **Curses Support**: Works with any curses-compatible terminal
- **Color Support**: Automatic color capability detection
- **Key Mapping**: Handles various terminal key mappings
- **Resize Handling**: Dynamic terminal resize support

## Command Line Interface

### Basic Usage
```bash
python3 tfm.py                    # Start with default settings
tfm                               # If installed via pip
```

### Advanced Options
```bash
--left PATH                       # Specify left pane directory
--right PATH                      # Specify right pane directory
--remote-log-port PORT           # Enable remote log monitoring
--color-test MODE                # Run color debugging tests
--version                        # Show version information
--help                           # Show help message
```

### Color Testing
```bash
--color-test info                # Show current color information
--color-test schemes             # List available color schemes
--color-test diagnose            # Diagnose color issues
--color-test interactive         # Interactive color tester
```

This comprehensive feature list represents the current state of TFM version 0.97, showcasing its evolution from a simple file manager to a sophisticated terminal-based file management system with cloud integration and extensive customization capabilities.