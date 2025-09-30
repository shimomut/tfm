# TFM User Guide

## Table of Contents

- [Getting Started](#getting-started)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Core Features](#core-features)
- [File Operations](#file-operations)
- [Navigation](#navigation)
- [Search and Filtering](#search-and-filtering)
- [Text Viewing and Editing](#text-viewing-and-editing)
- [AWS S3 Integration](#aws-s3-integration)
- [Advanced Features](#advanced-features)
- [Customization](#customization)
- [Command Line Options](#command-line-options)
- [Troubleshooting](#troubleshooting)
- [Feature Documentation](#feature-documentation)

---

## Getting Started

TFM (Terminal File Manager) is a powerful dual-pane file manager for the terminal that provides efficient file management with cloud storage integration, advanced search capabilities, and extensive customization options.

### What Makes TFM Special

- **Dual-pane interface** for efficient file operations between directories
- **AWS S3 integration** for seamless cloud storage management
- **Advanced search** with content search and filtering
- **Extensible** with external programs and custom key bindings
- **Cross-platform** support for macOS, Linux, and Windows

---

## Installation

### System Requirements

#### Minimum Requirements
- **Python 3.9+**: Core language requirement
- **Terminal**: Any terminal with curses support
- **Operating System**: macOS, Linux, or Windows with compatible terminal

#### Recommended Setup
- **Python 3.11+**: For best performance and compatibility
- **Modern Terminal**: Terminal.app (macOS), GNOME Terminal (Linux), Windows Terminal (Windows)
- **UTF-8 Support**: For proper character display

### Installation Methods

#### Method 1: Direct Run (Recommended for Testing)
```bash
# Clone or download TFM
git clone https://github.com/shimomut/tfm.git
cd tfm

# Run directly
python3 tfm.py
```

#### Method 2: Package Installation
```bash
# Install from source directory
cd tfm
python3 setup.py install

# Run installed version
tfm
```

#### Method 3: Development Installation
```bash
# Install in development mode (changes reflected immediately)
cd tfm
pip install -e .

# Run from anywhere
tfm
```

### Optional Dependencies

#### Enhanced Syntax Highlighting
```bash
pip install pygments
```
**Benefits**: 
- Syntax highlighting for 20+ file formats
- Better code viewing experience
- Automatic file type detection

#### AWS S3 Support
```bash
pip install boto3
```
**Benefits**:
- Navigate S3 buckets with s3:// URIs
- Full file operations on S3 objects
- Seamless local/cloud integration

**Setup AWS Credentials**:
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2

# Option 3: IAM roles (for EC2 instances)
# No additional setup required
```

### Platform-Specific Setup

#### macOS
```bash
# Ensure Python 3 is installed
python3 --version

# Install optional dependencies
pip3 install pygments boto3

# Run TFM
python3 tfm.py
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Install optional dependencies
pip3 install pygments boto3

# Run TFM
python3 tfm.py
```

#### Windows
```bash
# Install dependencies (including windows-curses)
pip install pygments boto3 windows-curses

# Run TFM
python tfm.py
```

### Verification

#### Test Basic Functionality
```bash
# Run TFM
python3 tfm.py

# Test basic navigation
# - Use arrow keys to navigate
# - Press Tab to switch panes
# - Press ? for help
# - Press q to quit
```

#### Test Color Support
```bash
# Test color capabilities
python3 tfm.py --color-test info

# Interactive color testing
python3 tfm.py --color-test interactive
```

---

## Basic Usage

### First Launch
When you first run TFM, you'll see:
- **Left Pane**: Current directory
- **Right Pane**: Home directory
- **Log Pane**: System messages at the bottom
- **Status Bar**: Current path and file information

### Essential Keys
- **Tab**: Switch between left and right panes
- **Arrow Keys**: Navigate files and directories
- **Enter**: Enter directory or view text file
- **Backspace**: Go to parent directory
- **?**: Show help dialog
- **q**: Quit TFM

---

## Core Features

### Dual Pane System
- **Left and Right Panes**: Independent file browsing with synchronized operations
- **Active Pane Highlighting**: Visual indication of currently focused pane
- **Tab Switching**: Quick pane switching with Tab key
- **Pane Synchronization**: Sync directories and cursor positions between panes
- **Resizable Layout**: Adjustable pane boundaries with bracket keys

**See detailed documentation**: [Status Bar Feature](STATUS_BAR_FEATURE.md)

### Display and Visualization
- **File Information**: Size, date, permissions display
- **Hidden Files Toggle**: Show/hide hidden files with '.' key
- **Color Schemes**: Dark and Light themes with runtime switching
- **Status Bar**: Current path, file count, operation status
- **Log Pane**: Bottom pane for system messages and output

**See detailed documentation**: [Color Schemes Feature](COLOR_SCHEMES_FEATURE.md)

---

## File Operations

### Basic Operations
```
Space    - Select/deselect file
c/C      - Copy selected files to other pane
m/M      - Move selected files to other pane
k/K      - Delete selected files
r/R      - Rename file (or batch rename multiple)
e        - Edit file with external editor
E        - Create new file and edit
F7       - Create new directory
```

**See detailed documentation**: 
- [Create File Feature](CREATE_FILE_FEATURE.md)
- [Create Directory Feature](CREATE_DIRECTORY_FEATURE.md)
- [Cross-Storage Move Feature](CROSS_STORAGE_MOVE_FEATURE.md)

### Multi-Selection
1. Use **Space** to select individual files
2. Use **a** to select all files
3. Use **A** to select all items (files + directories)
4. Perform operations on selected files

**See detailed documentation**: [Key Bindings Selection Feature](KEY_BINDINGS_SELECTION_FEATURE.md)

### Advanced Operations
- **Batch Rename**: Regex-based renaming for multiple files
- **Archive Creation**: Create ZIP, TAR.GZ, TGZ archives (P key)
- **Archive Extraction**: Extract archives to opposite pane (U key)
- **File Comparison**: Compare selected files between panes

**See detailed documentation**: [Batch Rename Feature](BATCH_RENAME_FEATURE.md)

### Safety Features
- **Confirmation Dialogs**: User confirmation for destructive operations
- **Conflict Resolution**: Handle file name conflicts during operations
- **Permission Checks**: Validate file system permissions
- **Undo Prevention**: Clear warnings about irreversible operations

---

## Navigation

### Directory Navigation
```
↑↓       - Move up/down in file list
←→       - Switch panes or enter/exit directories
Enter    - Enter directory or view file
Backspace - Go to parent directory
Home/End - Go to first/last file
Page Up/Down - Navigate by page
```

### Quick Navigation
```
j        - Show favorite directories
J        - Jump to directory dialog
h/H      - Show directory history
o        - Sync current pane to other pane
O        - Sync other pane to current pane
```

**See detailed documentation**: 
- [Favorite Directories Feature](FAVORITE_DIRECTORIES_FEATURE.md)
- [Command Line Directory Arguments Feature](COMMAND_LINE_DIRECTORY_ARGUMENTS_FEATURE.md)

---

## Search and Filtering

### Search Methods
```
f        - Incremental search (filter as you type)
F        - Threaded filename search dialog
G        - Content search (grep) dialog
;        - Filter by pattern (*.py, test_*, etc.)
:        - Clear current filter
```

### Search Tips
- **Incremental search**: Start typing to filter files immediately
- **Pattern filtering**: Use wildcards like `*.txt` or `test_*`
- **Content search**: Search inside files with progress tracking
- **ESC**: Cancel any search operation

**See detailed documentation**: [Search Animation Feature](SEARCH_ANIMATION_FEATURE.md)

---

## Text Viewing and Editing

### Built-in Text Viewer
```
v/V      - View text file in built-in viewer
Enter    - View text file (same as v)
```

### Text Viewer Controls
```
q/ESC    - Exit viewer
↑↓       - Scroll up/down
←→       - Scroll left/right
Page Up/Down - Page scrolling
Home/End - Jump to start/end
n        - Toggle line numbers
w        - Toggle line wrapping
s        - Toggle syntax highlighting
/        - Search within file
```

### External Editor
```
e        - Edit existing file
E        - Create new file and edit
```

Configure your preferred editor in `~/.tfm/config.py`:
```python
TEXT_EDITOR = 'vim'  # or 'nano', 'code', etc.
```

**See detailed documentation**: [Text Editor Feature](TEXT_EDITOR_FEATURE.md)

---

## AWS S3 Integration

### Setup
1. Install boto3: `pip install boto3`
2. Configure AWS credentials (AWS CLI, environment variables, or IAM roles)
3. Navigate to S3 buckets using s3:// URIs

### S3 Navigation
```bash
# Navigate to S3 bucket
s3://my-bucket/

# Navigate to specific path
s3://my-bucket/path/to/files/
```

### S3 Operations
- All standard file operations work with S3 objects
- Copy between local and S3 storage
- Edit S3 text files directly
- Create/extract archives with S3 objects

### S3 Examples
```bash
# Copy local files to S3
# 1. Select files in left pane (local directory)
# 2. Navigate right pane to s3://bucket/path
# 3. Press 'c' to copy

# Edit S3 text file
# 1. Navigate to s3://bucket/file.txt
# 2. Press 'e' to edit or 'v' to view
```

---

## Advanced Features

### Sub-shell Mode
Press **z** to enter sub-shell mode with environment variables:
- `TFM_LEFT_DIR`: Left pane directory
- `TFM_RIGHT_DIR`: Right pane directory
- `TFM_THIS_DIR`: Current pane directory
- `TFM_OTHER_DIR`: Other pane directory
- `TFM_THIS_SELECTED`: Selected files in current pane

### External Programs
Press **x** to show external programs menu. Programs have access to TFM environment variables.

**See detailed documentation**: [External Programs Feature](EXTERNAL_PROGRAMS_FEATURE.md)

### Remote Log Monitoring
```bash
# Start TFM with remote monitoring
python3 tfm.py --remote-log-port 8888

# Connect from another terminal
python3 tools/tfm_log_client.py localhost 8888
```

**See detailed documentation**: [Remote Log Monitoring Feature](REMOTE_LOG_MONITORING_FEATURE.md)

### Pane Layout
```
[        - Make left pane smaller
]        - Make left pane larger
-        - Reset pane split to 50/50
{        - Make log pane larger (Shift+[)
}        - Make log pane smaller (Shift+])
_        - Reset log pane height (Shift+-)
```

### Progress Animation
TFM shows animated progress indicators during long-running operations like searching files.

**See detailed documentation**: [Log Redraw Trigger Feature](LOG_REDRAW_TRIGGER_FEATURE.md)

---

## Customization

### Configuration File
TFM creates `~/.tfm/config.py` on first run. Access it via:
- Press **Z** → Settings Menu → Edit Configuration
- Or edit `~/.tfm/config.py` directly

### Key Bindings
Customize any key binding in your config file:
```python
KEY_BINDINGS = {
    'quit': ['q'],  # Remove 'Q' binding
    'search': ['/', 'f'],  # Add '/' for search
    'copy_files': {'keys': ['c', 'C', 'y'], 'selection': 'required'},
    # ... customize any action
}
```

### Color Schemes
```python
COLOR_SCHEME = 'dark'  # or 'light'
```

Switch at runtime with **t** key.

**See detailed documentation**: [Color Schemes Feature](COLOR_SCHEMES_FEATURE.md)

### Favorite Directories
```python
FAVORITE_DIRECTORIES = [
    {'name': 'Projects', 'path': '~/dev'},
    {'name': 'Documents', 'path': '~/Documents'},
    {'name': 'S3 Bucket', 'path': 's3://my-bucket/'},
]
```

**See detailed documentation**: [Favorite Directories Feature](FAVORITE_DIRECTORIES_FEATURE.md)

### External Programs
```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
    {'name': 'Open in VSCode', 'command': ['code', '.'], 
     'options': {'auto_return': True}},
]
```

**See detailed documentation**: [External Programs Feature](EXTERNAL_PROGRAMS_FEATURE.md)

---

## Command Line Options

### Basic Usage
```bash
python3 tfm.py                    # Default startup
python3 tfm.py --left ~/projects  # Specify left pane
python3 tfm.py --right ~/docs     # Specify right pane
```

### Advanced Options
```bash
--remote-log-port 8888            # Enable remote monitoring
--color-test info                 # Test color support
--version                         # Show version
--help                           # Show help
```

**See detailed documentation**: [Command Line Directory Arguments Feature](COMMAND_LINE_DIRECTORY_ARGUMENTS_FEATURE.md)

---

## Troubleshooting

### Common Issues

#### Colors not working
Try `--color-test diagnose` to check terminal support

**See detailed documentation**: [Color Debugging Feature](COLOR_DEBUGGING_FEATURE.md)

#### Keys not responding
Check terminal key mappings and ESCDELAY setting

#### S3 access denied
Verify AWS credentials and bucket permissions

#### File operations failing
Check file permissions and disk space

### Getting Help
- Press **?** for built-in help
- Check feature documentation below
- Use `--help` command line option
- Enable remote logging for debugging

**See detailed documentation**: [Help Dialog Feature](HELP_DIALOG_FEATURE.md)

---

## Feature Documentation

For detailed information about specific features, see these dedicated guides:

### File Operations
- [Batch Rename Feature](BATCH_RENAME_FEATURE.md) - Regex-based renaming for multiple files
- [Create Directory Feature](CREATE_DIRECTORY_FEATURE.md) - Creating new directories
- [Create File Feature](CREATE_FILE_FEATURE.md) - Creating and editing new files
- [Cross-Storage Move Feature](CROSS_STORAGE_MOVE_FEATURE.md) - Moving files between storage types
- [File Details Feature](FILE_DETAILS_FEATURE.md) - Viewing detailed file information

### Navigation and Search
- [Favorite Directories Feature](FAVORITE_DIRECTORIES_FEATURE.md) - Quick directory bookmarks
- [Search Animation Feature](SEARCH_ANIMATION_FEATURE.md) - Progress indicators during search
- [Command Line Directory Arguments Feature](COMMAND_LINE_DIRECTORY_ARGUMENTS_FEATURE.md) - Startup directory options

### Interface and Display
- [Color Debugging Feature](COLOR_DEBUGGING_FEATURE.md) - Diagnosing color display issues
- [Color Schemes Feature](COLOR_SCHEMES_FEATURE.md) - Dark and light themes
- [Help Dialog Feature](HELP_DIALOG_FEATURE.md) - Built-in help system
- [Key Bindings Selection Feature](KEY_BINDINGS_SELECTION_FEATURE.md) - Customizable keyboard shortcuts
- [Log Redraw Trigger Feature](LOG_REDRAW_TRIGGER_FEATURE.md) - Real-time log updates
- [Status Bar Feature](STATUS_BAR_FEATURE.md) - Status information display

### Integration and Extensions
- [Beyond Compare Integration](BEYONDCOMPARE_INTEGRATION.md) - File comparison tool integration
- [External Programs Feature](EXTERNAL_PROGRAMS_FEATURE.md) - Custom program integration
- [Remote Log Monitoring Feature](REMOTE_LOG_MONITORING_FEATURE.md) - Network log streaming
- [Text Editor Feature](TEXT_EDITOR_FEATURE.md) - External editor integration
- [VSCode Integration](VSCODE_INTEGRATION.md) - Visual Studio Code integration

---

## Tips and Tricks

### Efficiency Tips
1. **Use Tab frequently**: Quick pane switching is key to efficiency
2. **Learn multi-selection**: Select multiple files with Space, then operate
3. **Use incremental search**: Press 'f' and start typing to filter files
4. **Customize key bindings**: Adapt TFM to your workflow
5. **Use favorites**: Set up bookmarks for frequently accessed directories

### Workflow Examples

#### File Organization
1. Navigate to source directory in left pane
2. Navigate to destination in right pane
3. Select files with Space
4. Press 'c' to copy or 'm' to move

#### Development Workflow
1. Set up favorites for project directories
2. Use external programs for git operations
3. Edit files with 'e' key
4. Use content search to find code

#### S3 Data Management
1. Navigate to local directory in left pane
2. Navigate to s3://bucket/path in right pane
3. Copy files between local and cloud storage
4. Edit S3 configuration files directly

---

This comprehensive user guide covers all aspects of using TFM effectively. For technical implementation details, see the developer documentation in the `doc/dev/` directory.