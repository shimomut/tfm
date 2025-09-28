# TFM User Guide

## Getting Started with TFM

TFM (Terminal File Manager) is a powerful dual-pane file manager for the terminal. This guide will help you get started and make the most of its features.

## Installation

### Quick Start
1. Ensure you have Python 3.6+ installed
2. Clone or download TFM
3. Run the file manager:
   ```bash
   python3 tfm.py
   ```

### Package Installation
```bash
# Install from source
python3 setup.py install

# Run installed version
tfm
```

### Dependencies
```bash
# Optional: Enhanced syntax highlighting
pip install pygments

# Optional: AWS S3 support
pip install boto3
```

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

### Multi-Selection
1. Use **Space** to select individual files
2. Use **a** to select all files
3. Use **A** to select all items (files + directories)
4. Perform operations on selected files

### Archive Operations
```
p/P      - Create archive from selected files
u/U      - Extract archive to other pane
```

Supported formats: ZIP, TAR.GZ, TGZ

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

### Favorite Directories
```python
FAVORITE_DIRECTORIES = [
    {'name': 'Projects', 'path': '~/dev'},
    {'name': 'Documents', 'path': '~/Documents'},
    {'name': 'S3 Bucket', 'path': 's3://my-bucket/'},
]
```

### External Programs
```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
    {'name': 'Open in VSCode', 'command': ['code', '.'], 
     'options': {'auto_return': True}},
]
```

## Advanced Features

### Sub-shell Mode
Press **X** to enter sub-shell mode with environment variables:
- `TFM_LEFT_DIR`: Left pane directory
- `TFM_RIGHT_DIR`: Right pane directory
- `TFM_THIS_DIR`: Current pane directory
- `TFM_OTHER_DIR`: Other pane directory
- `TFM_THIS_SELECTED`: Selected files in current pane

### External Programs
Press **x** to show external programs menu. Programs have access to TFM environment variables.

### Remote Log Monitoring
```bash
# Start TFM with remote monitoring
python3 tfm.py --remote-log-port 8888

# Connect from another terminal
python3 tools/tfm_log_client.py localhost 8888
```

### Pane Layout
```
[        - Make left pane smaller
]        - Make left pane larger
-        - Reset pane split to 50/50
{        - Make log pane larger (Shift+[)
}        - Make log pane smaller (Shift+])
_        - Reset log pane height (Shift+-)
```

## Sorting and Organization

### Sort Options
```
s/S      - Sort menu with search
1        - Quick sort by name
2        - Quick sort by extension
3        - Quick sort by size
4        - Quick sort by date
```

### Display Options
```
.        - Toggle hidden files
t        - Toggle color scheme
T        - Toggle fallback color mode
```

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

### Troubleshooting

#### Common Issues
- **Colors not working**: Try `--color-test diagnose` to check terminal support
- **Keys not responding**: Check terminal key mappings and ESCDELAY setting
- **S3 access denied**: Verify AWS credentials and bucket permissions
- **File operations failing**: Check file permissions and disk space

#### Getting Help
- Press **?** for built-in help
- Check documentation in `doc/` directory
- Use `--help` command line option
- Enable remote logging for debugging

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

## Performance Tuning

### Configuration Options
```python
# Performance settings in config.py
MAX_SEARCH_RESULTS = 10000        # Limit search results
MAX_JUMP_DIRECTORIES = 5000       # Limit jump dialog entries
MAX_HISTORY_ENTRIES = 100         # Limit history entries
PROGRESS_ANIMATION_SPEED = 0.2    # Animation update interval
```

### Large Directory Handling
- TFM handles thousands of files efficiently
- Use filtering to narrow down large directories
- Configure result limits for search operations
- Use threaded operations for better responsiveness

This user guide covers the essential features and workflows of TFM. For detailed technical information, see the feature documentation in the `doc/` directory.