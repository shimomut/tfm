# TFM User Guide

## Table of Contents

- [Getting Started](#getting-started)
- [Installation](#installation)
- [Desktop Mode (macOS)](#desktop-mode-macos)
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
- **Dual-mode operation** - Run in terminal or as native desktop app (macOS)
- **AWS S3 integration** for seamless cloud storage management
- **Advanced search** with content search and filtering
- **Extensible** with external programs and custom key bindings
- **Cross-platform** support for macOS, Linux, and Windows

---

## Installation

### System Requirements

#### Terminal Mode Requirements (All Platforms)
- **Python 3.9+**: Core language requirement (3.11+ recommended)
- **Terminal**: Any terminal with curses support
- **Operating System**: macOS, Linux, or Windows
- **Windows**: `windows-curses` package (automatically installed via setup.py)

#### Desktop Mode Requirements (macOS Only)
- **Python 3.9+**: Core language requirement (3.11+ recommended)
- **macOS**: 10.13 (High Sierra) or later
- **PyObjC**: Install with `pip install pyobjc-framework-Cocoa`

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

# Run directly in terminal mode
python3 tfm.py

# Run in desktop mode (macOS only)
python3 tfm.py --desktop
```

#### Method 2: Package Installation
```bash
# Install from source directory
cd tfm
python3 setup.py install

# Run installed version
tfm                # Terminal mode
tfm --desktop      # Desktop mode (macOS only)
```

#### Method 3: Development Installation
```bash
# Install in editable mode (changes reflected immediately)
cd tfm
pip install -e .

# Run from anywhere
tfm                # Terminal mode
tfm --desktop      # Desktop mode (macOS only)
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

#### Desktop Mode (macOS Only)
```bash
pip install pyobjc-framework-Cocoa
```
**Benefits**:
- Native macOS application window
- GPU-accelerated rendering at 60 FPS
- Resizable window with full-screen support
- True RGB colors with better accuracy
- Customizable fonts and window size

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
# Install windows-curses (required for Windows)
pip install windows-curses

# Install optional dependencies
pip install pygments boto3

# Run TFM
python tfm.py
```

**Note**: The `windows-curses` package is automatically installed when using `python setup.py install` on Windows systems.

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

---

## Desktop Mode (macOS)

TFM can run as a native macOS desktop application with GPU acceleration, providing a modern windowed experience while maintaining the same keyboard-driven interface.

### Quick Start

```bash
# Install PyObjC (one-time setup)
pip install pyobjc-framework-Cocoa

# Run in desktop mode
python3 tfm.py --desktop

# Or use the full backend syntax
python3 tfm.py --backend coregraphics
```

### Features

Desktop mode provides several advantages over terminal mode:

- **Native Window**: Resizable macOS window with standard window controls
- **High-Quality Rendering**: Smooth rendering using CoreGraphics
- **Better Colors**: True RGB color support with accurate color reproduction
- **Font Customization**: Choose your preferred monospace font and size
- **Full-Screen Support**: Native macOS full-screen mode
- **Window Persistence**: Window size and position are remembered

### Configuration

Desktop mode settings are configured in `~/.tfm/config.py`:

```python
# Backend selection
PREFERRED_BACKEND = 'coregraphics'  # Use desktop mode by default

# Desktop mode settings (macOS only)
# Font name - can be a single font or list for cascade fallback
DESKTOP_FONT_NAME = 'Menlo'         # Single font (simple)
# DESKTOP_FONT_NAME = ['Menlo', 'Monaco', 'Courier']  # Multiple fonts with fallback
DESKTOP_FONT_SIZE = 14              # Font size in points
DESKTOP_WINDOW_WIDTH = 1200         # Initial window width in pixels
DESKTOP_WINDOW_HEIGHT = 800         # Initial window height in pixels
```

#### Available Fonts

Common monospace fonts on macOS:
- `Menlo` (default) - Apple's default monospace font
- `Monaco` - Classic Mac monospace font
- `SF Mono` - San Francisco Mono (if installed)
- `Courier New` - Traditional monospace font
- `Fira Code` - Popular programming font (if installed)
- `JetBrains Mono` - Modern programming font (if installed)

### Backend Selection Priority

TFM selects the rendering backend in this order:

1. **Command-line flag**: `--backend` or `--desktop` overrides everything
2. **Configuration file**: `PREFERRED_BACKEND` setting in `~/.tfm/config.py`
3. **Default**: Falls back to terminal mode (`curses` backend)

### Automatic Fallback

If desktop mode is requested but unavailable, TFM automatically falls back to terminal mode:

```bash
# Desktop mode requested but PyObjC not installed
python3 tfm.py --desktop
# Output: Error: PyObjC is required for CoreGraphics backend
#         Install with: pip install pyobjc-framework-Cocoa
#         Falling back to curses backend
```

### Keyboard Shortcuts

All keyboard shortcuts work identically in both terminal and desktop modes. The same key bindings apply regardless of which backend you're using.

For a complete list of all keyboard shortcuts, see the [Keyboard Shortcuts Reference](#keyboard-shortcuts-reference) section. You can also press **?** at any time while using TFM to see the built-in help dialog with all available shortcuts.

### Performance

Desktop mode provides excellent performance:
- **Rendering**: 60 FPS with GPU acceleration
- **Responsiveness**: Immediate input handling
- **Large Directories**: Smooth scrolling even with thousands of files
- **Search Operations**: Non-blocking UI updates

### Troubleshooting Desktop Mode

**Desktop mode doesn't start:**
- Verify you're on macOS (desktop mode is macOS-only)
- Install PyObjC: `pip install pyobjc-framework-Cocoa`
- Check Python version (3.9+ required)

**Window doesn't appear:**
- Check console output for error messages
- Verify PyObjC installation: `python3 -c "import objc; print('OK')"`
- Try terminal mode first to verify TFM works: `python3 tfm.py`

**Font issues:**
- Verify font name is correct (case-sensitive)
- Use `Font Book.app` to check installed fonts
- Fall back to default: Remove `DESKTOP_FONT_NAME` from config

**Performance issues:**
- Desktop mode should run at 60 FPS
- Check Activity Monitor for CPU/GPU usage
- Try reducing window size in configuration

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
- **Wide Character Support**: Proper display of international filenames and Unicode characters

**See detailed documentation**: 
- [Color Schemes Feature](COLOR_SCHEMES_FEATURE.md)
- [Wide Character Support Feature](WIDE_CHARACTER_SUPPORT_FEATURE.md)

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
- **Conflict Resolution**: Handle file name conflicts with Overwrite, Skip, Rename, or Cancel options
- **Rename on Conflict**: Specify alternative filenames when conflicts occur during copy/move/extract
- **Permission Checks**: Validate file system permissions
- **Undo Prevention**: Clear warnings about irreversible operations

**See detailed documentation**: [Rename Conflict Resolution Feature](RENAME_CONFLICT_RESOLUTION_FEATURE.md)

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

### Sorting
```
s/S      - Show sort options menu
1        - Quick sort by name
2        - Quick sort by extension
3        - Quick sort by size
4        - Quick sort by date
```

### Search Tips
- **Incremental search**: Start typing to filter files immediately
- **Pattern filtering**: Use wildcards like `*.txt` or `test_*`
- **Content search**: Search inside files with progress tracking
- **Quick sort**: Use number keys 1-4 for instant sorting
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

TFM provides native AWS S3 integration for seamless cloud storage management. For comprehensive S3 documentation including setup, usage, troubleshooting, and advanced features, see the **[AWS S3 Support Feature Guide](S3_SUPPORT_FEATURE.md)**.

### Quick Start

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
Press **X** (Shift+x) to enter sub-shell mode with environment variables:
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

### File Comparison
```
=        - View diff between two selected text files (requires 2 files selected)
@        - Compare directories recursively (Shift+2)
w/W      - Show file and directory comparison options
```

**See detailed documentation**: [Diff Viewer Feature](DIFF_VIEWER_FEATURE.md), [Directory Diff Viewer Feature](DIRECTORY_DIFF_VIEWER_FEATURE.md)

### View and Display Options
```
z        - Show view options menu
Z        - Show settings and configuration menu
t        - Toggle between dark and light color schemes
T        - Toggle fallback color mode for terminal compatibility
.        - Toggle visibility of hidden files
```

### Progress Animation
TFM shows animated progress indicators during long-running operations like searching files.

**See detailed documentation**: [Log Redraw Trigger Feature](LOG_REDRAW_TRIGGER_FEATURE.md)

### Performance Profiling
Enable performance profiling to investigate rendering and input handling performance:

```bash
# Enable profiling mode
python3 tfm.py --profile
```

When profiling is enabled:
- **FPS measurements** are printed every 5 seconds
- **Profile files** are generated for key events and rendering
- **Profile data** is saved to `profiling_output/` directory

#### Analyzing Profile Files

Use Python's pstats module:
```bash
python3 -m pstats profiling_output/key_profile_*.prof
```

Or use snakeviz for visual analysis:
```bash
pip install snakeviz
snakeviz profiling_output/render_profile_*.prof
```

#### Use Cases
- Investigating slow rendering or key response
- Comparing terminal vs desktop mode performance
- Testing performance optimizations
- Benchmarking on different systems

**See detailed documentation**: [Performance Profiling Feature](PERFORMANCE_PROFILING_FEATURE.md)

---

## Customization

### Configuration File
TFM creates `~/.tfm/config.py` on first run. Access it via:
- Press **Z** → Settings Menu → Edit Configuration
- Or edit `~/.tfm/config.py` directly

**For comprehensive configuration documentation**, see the **[Configuration Feature Guide](CONFIGURATION_FEATURE.md)** which covers all available options, examples, and best practices.

### Key Bindings

TFM supports powerful key binding customization with modifier keys and multiple keys per action:

```python
KEY_BINDINGS = {
    # Simple character keys
    'quit': ['q', 'Q'],
    'help': ['?'],
    
    # KeyCode names for special keys
    'move_up': ['UP', 'k'],
    'move_down': ['DOWN', 'j'],
    
    # Modifier key combinations
    'page_up': ['PAGE_UP', 'Shift-UP'],
    'page_down': ['PAGE_DOWN', 'Shift-DOWN'],
    'jump_to_top': ['Command-UP'],
    'jump_to_bottom': ['Command-DOWN'],
    
    # Selection requirements
    'delete_files': {
        'keys': ['DELETE', 'Command-Backspace'],
        'selection': 'required'  # Only when files selected
    },
    'create_directory': {
        'keys': ['m', 'M'],
        'selection': 'none'  # Only when no files selected
    },
}
```

**Key features:**
- **Modifier keys**: Shift, Control, Alt, Command
- **Multiple keys per action**: Assign several keys to the same action
- **Selection requirements**: Control when actions are available
- **Case-insensitive**: 'ENTER', 'enter', 'Enter' all work
- **Order-independent modifiers**: 'Command-Shift-X' = 'Shift-Command-X'

**See detailed documentation**: [Key Bindings Feature](KEY_BINDINGS_FEATURE.md)

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
python3 tfm.py                    # Default startup (terminal mode)
python3 tfm.py --desktop          # Desktop mode (macOS only)
python3 tfm.py --left ~/projects  # Specify left pane
python3 tfm.py --right ~/docs     # Specify right pane
```

### Backend Selection
```bash
python3 tfm.py --backend curses        # Terminal mode (default)
python3 tfm.py --backend coregraphics  # Desktop mode (macOS)
python3 tfm.py --desktop               # Shorthand for desktop mode
```

### Advanced Options
```bash
--remote-log-port 8888            # Enable remote monitoring
--profile TARGETS                 # Enable performance profiling (see targets below)
--debug                           # Enable debug mode with full stack traces
--version                         # Show version
--help                            # Show help
```

#### Performance Profiling
Enable performance profiling for specific targets:

```bash
python3 tfm.py --profile event              # Profile event loop iterations
python3 tfm.py --profile rendering          # Profile C++ renderer (CoreGraphics only)
python3 tfm.py --profile rendering,event    # Profile multiple targets
```

**Available profiling targets:**
- `event` - Profile event loop iterations using cProfile
- `rendering` - Profile C++ renderer metrics (CoreGraphics backend only)

Profiling data helps identify performance bottlenecks and optimize TFM's responsiveness.

#### Debug Mode
Enable detailed error reporting for troubleshooting:

```bash
python3 tfm.py --debug
```

When debug mode is enabled:
- Full stack traces are printed for uncaught exceptions
- Detailed error information helps diagnose issues
- Useful for reporting bugs or investigating problems

Without debug mode, TFM shows simplified error messages and suggests using `--debug` for details.

### Combined Options
```bash
# Desktop mode with custom directories
python3 tfm.py --desktop --left ~/projects --right ~/docs

# Terminal mode with remote logging
python3 tfm.py --backend curses --remote-log-port 8888

# Desktop mode with profiling
python3 tfm.py --desktop --profile event
```

**See detailed documentation**: [Command Line Directory Arguments Feature](COMMAND_LINE_DIRECTORY_ARGUMENTS_FEATURE.md)

---

## Troubleshooting

### Common Issues

#### Desktop mode not starting (macOS)
- Verify PyObjC is installed: `pip install pyobjc-framework-Cocoa`
- Check Python version: `python3 --version` (3.9+ required)
- Try terminal mode first: `python3 tfm.py`
- Check console output for error messages

#### Desktop mode on non-macOS systems
Desktop mode only works on macOS. On other platforms, TFM automatically falls back to terminal mode.

#### Colors not working
Check your terminal's color support and TERM environment variable

#### Wide characters display incorrectly
Check terminal Unicode support and locale settings

**See detailed documentation**: [Wide Character Support Feature](WIDE_CHARACTER_SUPPORT_FEATURE.md)

#### Keys not responding
Check terminal key mappings and ESCDELAY setting

#### S3 access denied
Verify AWS credentials and bucket permissions

#### File operations failing
Check file permissions and disk space

#### Performance issues
- Desktop mode provides better performance with GPU acceleration
- Install `pygments` for faster syntax highlighting
- Check available memory for large directory operations

### Getting Help
- Press **?** for built-in help
- Check feature documentation below
- Use `--help` command line option
- Enable remote logging for debugging
- Use `--profile` for performance profiling

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
- [Rename Conflict Resolution Feature](RENAME_CONFLICT_RESOLUTION_FEATURE.md) - Handling file name conflicts

### Cloud Storage and Archives
- [AWS S3 Support Feature](S3_SUPPORT_FEATURE.md) - Cloud storage integration and S3 bucket management
- [Archive Virtual Directory Feature](ARCHIVE_VIRTUAL_DIRECTORY_FEATURE.md) - Browse ZIP, TAR, and compressed archives as directories

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
- [Wide Character Support Feature](WIDE_CHARACTER_SUPPORT_FEATURE.md) - International character display

### Configuration and Customization
- [Configuration Feature](CONFIGURATION_FEATURE.md) - Complete configuration reference and customization guide

### Performance and Debugging
- [Performance Profiling Feature](PERFORMANCE_PROFILING_FEATURE.md) - Performance analysis, optimization, and testing

### Integration and Extensions
- [Beyond Compare Integration](BEYONDCOMPARE_INTEGRATION.md) - File comparison tool integration
- [External Programs Feature](EXTERNAL_PROGRAMS_FEATURE.md) - Custom program integration
- [Remote Log Monitoring Feature](REMOTE_LOG_MONITORING_FEATURE.md) - Network log streaming
- [Text Editor Feature](TEXT_EDITOR_FEATURE.md) - External editor integration
- [VSCode Integration](VSCODE_INTEGRATION.md) - Visual Studio Code integration

---

## Keyboard Shortcuts Reference

TFM provides extensive keyboard shortcuts for efficient file management. All shortcuts work identically in both terminal and desktop modes. Press **?** at any time to see the help dialog with all available shortcuts.

### Navigation

| Key | Action |
|-----|--------|
| ↑↓ or j/k | Move cursor up/down |
| ←→ or h/l | Switch between panes |
| Enter | Enter directory or open file |
| Backspace | Go to parent directory |
| Home/End | Go to first/last item |
| Page Up/Down | Scroll by page |
| Tab | Switch active pane |

### File Selection

| Key | Action |
|-----|--------|
| Space | Toggle file selection |
| HOME | Select all items |
| END | Unselect all items |
| a | Toggle all files selection |
| A | Toggle all items selection |
| w, W | Compare selection (select files/directories matching other pane) |

### File Operations

| Key | Action | Selection Required |
|-----|--------|-------------------|
| c, C | Copy selected files | Yes |
| m, M | Move selected files | Yes |
| k, K | Delete selected files | Yes |
| r, R | Rename file/directory | No |
| m, M | Create new directory | No (only when no files selected) |
| E | Create new file | No |

### View and Search

| Key | Action |
|-----|--------|
| v, V | View file content |
| e | Edit file |
| f | Search files (isearch) |
| ; | Filter files by pattern |
| : | Clear file filter |
| F | Filename search dialog |
| J | Jump to path |
| G | Content search dialog (grep) |
| i, I | Show file details |
| = | View diff between two selected text files (requires 2 files selected) |
| @ | Compare directories recursively |

### Pane Operations

| Key | Action |
|-----|--------|
| o | Sync current pane directory to other pane |
| O | Sync other pane directory to current pane |
| [ | Make left pane smaller (adjust boundary left) |
| ] | Make left pane larger (adjust boundary right) |
| - | Reset pane split to 50% \| 50% |

### Log Pane Controls

| Key | Action |
|-----|--------|
| { | Make log pane larger (Shift+[) |
| } | Make log pane smaller (Shift+]) |
| _ | Reset log pane height to default (Shift+-) |
| Shift+Up | Scroll log up (toward older messages) |
| Shift+Down | Scroll log down (toward newer messages) |
| Shift+Left | Fast scroll up (toward older messages) |
| Shift+Right | Fast scroll down (toward newer messages) |

### Sorting

| Key | Action |
|-----|--------|
| s, S | Show sort options menu |
| 1 | Quick sort by filename |
| 2 | Quick sort by file extension |
| 3 | Quick sort by file size |
| 4 | Quick sort by modification date |

### Archive Operations

| Key | Action | Selection Required |
|-----|--------|-------------------|
| p, P | Create archive from selected files | Yes |
| u, U | Extract selected archive | No |

### Other Operations

| Key | Action |
|-----|--------|
| ? | Show help dialog |
| q, Q | Quit TFM |
| Ctrl+R | Refresh file list |
| . | Toggle visibility of hidden files |
| t | Switch color schemes |
| T | Toggle fallback color mode |
| j | Show favorite directories |
| h, H | Show history for current pane |
| d, D | Show drives/storage selection dialog |
| x | Show external programs menu |
| X | Enter subshell (command line) mode |
| z | Show view options menu |
| Z | Show settings and configuration menu |

### Customizing Key Bindings

All key bindings can be customized in your configuration file (`~/.tfm/config.py`). The enhanced key binding system supports:

- **Modifier keys**: Shift, Control, Alt, Command (e.g., 'Shift-UP', 'Command-Q')
- **Multiple keys per action**: Assign several keys to the same action
- **Selection requirements**: Control when actions are available based on file selection
- **Case-insensitive matching**: 'ENTER', 'enter', 'Enter' all work

**Examples:**
```python
KEY_BINDINGS = {
    'page_up': ['PAGE_UP', 'Shift-UP'],  # Two ways to page up
    'jump_to_top': ['Command-UP'],       # Modifier combination
    'delete_files': {
        'keys': ['DELETE', 'Command-Backspace'],
        'selection': 'required'          # Only when files selected
    },
}
```

See the [Configuration](#customization) section and [Key Bindings Feature](KEY_BINDINGS_FEATURE.md) for complete documentation.

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