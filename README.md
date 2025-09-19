# TUI File Manager v0.10

A powerful terminal-based file manager built with Python's curses library. Navigate your filesystem with keyboard shortcuts in a clean, intuitive dual-pane interface with comprehensive file operations.

## Features

### Core Interface
- **Dual Pane Interface**: Left and right panes for easy file operations between directories
- **Log Pane**: Bottom pane captures stdout and stderr output with timestamps
- **Pane Switching**: Use Tab to switch between panes, active pane highlighted in header
- **Resizable Panes**: Adjust pane sizes with Ctrl+Left/Right and Ctrl+U/D
- **Status Bar**: Shows current path, file count, and operation status

![TFM Main Interface](doc/images/main-screen.png)

### Navigation & Display
- **Directory Navigation**: Browse directories with arrow keys or vim-style navigation (j/k)
- **File Information**: View file sizes, modification dates, and permissions
- **Hidden Files**: Toggle visibility of hidden files with 'h'
- **Sorting**: Multiple sort options (name, size, date, type)
- **Color Coding**: 
  - Blue/bold for directories
  - Green for executable files
  - Yellow highlight for selected items in active pane
  - Underline for selected items in inactive pane
  - Red text for stderr messages in log pane

### File Operations
- **Copy Files**: Copy files/directories between panes with 'C' key
- **Move Files**: Move files/directories between panes with 'M' key
- **Delete Files**: Delete files/directories with 'K' key (with confirmation)
- **Rename Files**: Rename files/directories with 'R' key
- **Create Files**: Create new text files with 'Shift+E' and auto-edit
- **Create Directories**: Create new directories with 'M' key (when no selection)
- **Multi-Selection**: Select multiple files with Space bar for batch operations
- **Conflict Resolution**: Interactive dialogs for handling existing files

### Text Handling
- **Text File Viewer**: Built-in text viewer with syntax highlighting for 20+ file formats
- **Text Editor Integration**: Edit files directly with your preferred text editor (vim, nano, etc.)
- **Syntax Highlighting**: Support for Python, JavaScript, JSON, Markdown, YAML, and more
- **Line Numbers**: Toggle line numbers in text viewer
- **Search in Files**: Search functionality within viewed text files

### Advanced Features
- **Sub-shell Mode**: Suspend TFM and enter shell with environment variables for current state
- **Favorite Directories**: Quick access to frequently used directories with 'J' key
- **Searchable Lists**: Filter and search through files and directories
- **Configuration System**: Fully customizable key bindings and settings
- **Help System**: Comprehensive help dialog accessible with '?' key
- **Log Management**: Scroll through log messages, auto-scrolls to newest
- **Cross-platform**: Works on macOS, Linux, and Windows (with proper terminal support)

## File Operations

TFM provides comprehensive file management capabilities with intuitive keyboard shortcuts:

### Basic Operations
- **Copy**: Select files with Space, press 'C' to copy to opposite pane
- **Move**: Select files with Space, press 'M' to move to opposite pane  
- **Delete**: Select files with Space, press 'K' to delete (with confirmation)
- **Rename**: Navigate to file, press 'R' to rename in-place

### Advanced Operations
- **Multi-Selection**: Use Space to select multiple files for batch operations
- **Conflict Resolution**: Interactive dialogs handle existing files during copy/move
- **Directory Operations**: All operations work on directories (recursive)
- **Symbolic Links**: Proper handling of symbolic links (preserved during operations)

### File Creation
- **New Files**: Press 'Shift+E' to create and immediately edit new text files
- **New Directories**: Press 'M' with no selection to create new directories
- **Auto-Editor**: New files automatically open in your configured text editor

### Safety Features
- **Confirmation Dialogs**: All destructive operations require confirmation
- **Permission Checks**: Operations validate permissions before execution
- **Error Handling**: Clear error messages for failed operations
- **Undo Protection**: Parent directory (..) cannot be accidentally modified

## Favorite Directories

Quick access to frequently used directories:

- **Access**: Press 'J' to open favorites dialog
- **Search**: Type to filter favorites by name or path
- **Customize**: Edit `~/.tfm/config.py` to add your own favorites
- **Default Locations**: Includes common directories (Home, Documents, Downloads, etc.)

## Help System

TFM includes a comprehensive help dialog that provides quick access to all key bindings and features:

- **Access**: Press `?` to open the help dialog
- **Content**: Organized sections covering navigation, file operations, search, sorting, and more
- **Navigation**: Scroll through help content with arrow keys, Page Up/Down, Home/End
- **Always Available**: Accessible from any screen in TFM
- **Context-Sensitive**: Shows relevant shortcuts for current mode

The help dialog is your quick reference guide - no need to memorize all key bindings!

## Key Bindings

### Navigation
| Key | Action |
|-----|--------|
| `↑/k` | Move selection up in active pane |
| `↓/j` | Move selection down in active pane |
| `Tab` | Switch between left and right panes |
| `→` | Switch to right pane (from left) OR go to parent (in right pane) |
| `←` | Switch to left pane (from right) OR go to parent (in left pane) |
| `Enter` | Enter directory or view text file with syntax highlighting |
| `Backspace` | Go to parent directory |
| `Home` | Go to first item in active pane |
| `End` | Go to last item in active pane |
| `Page Up` | Move up 10 items in active pane |
| `Page Down` | Move down 10 items in active pane |

### File Operations
| Key | Action |
|-----|--------|
| `Space` | Select/deselect file (for multi-selection) |
| `c/C` | Copy selected files to opposite pane |
| `m/M` | Move selected files to opposite pane (or create directory if no selection) |
| `k/K` | Delete selected files (with confirmation) |
| `r/R` | Rename selected file |
| `e` | Edit selected file with configured text editor |
| `E` | Create new text file and edit |
| `v` | View selected file in text viewer |

### Display & Search
| Key | Action |
|-----|--------|
| `h` | Toggle hidden files visibility |
| `f` | Search/filter files in current directory |
| `s` | Sort files (cycle through sort options) |
| `J` | Open favorite directories dialog |
| `?` | Show help dialog with all key bindings |

### Pane Management
| Key | Action |
|-----|--------|
| `Ctrl+←/→` | Adjust horizontal pane sizes |
| `Ctrl+U/D` | Adjust vertical pane sizes (log pane) |
| `l` | Scroll log pane up (older messages) |
| `L` | Scroll log pane down (newer messages) |

### System
| Key | Action |
|-----|--------|
| `q` | Quit application |
| `x/X` | Enter sub-shell mode with environment variables |
| `t` | Test log output (demonstrates stdout/stderr capture) |

## Text Viewer

TFM includes a built-in text file viewer with syntax highlighting support. When you press `Enter` on a text file or use the `v` key, the file opens in the integrated viewer.

### Text Viewer Features
- **Syntax highlighting** for 20+ file formats (Python, JavaScript, JSON, Markdown, YAML, etc.)
- **Line numbers** (toggle with `n`)
- **Horizontal scrolling** (arrow keys)
- **Status bar** showing position, file size, format, and active options
- **Multiple encoding support** (UTF-8, Latin-1, CP1252)
- **Automatic file type detection**

### Text Viewer Controls
| Key | Action |
|-----|--------|
| `q` or `ESC` | Exit viewer |
| `↑↓` or `j/k` | Scroll up/down |
| `←→` or `h/l` | Scroll left/right |
| `Page Up/Down` | Page scrolling |
| `Home/End` | Jump to start/end |
| `n` | Toggle line numbers |
| `w` | Toggle line wrapping |
| `s` | Toggle syntax highlighting |
| `/` | Search within file |

### Supported File Formats
- **Programming Languages**: Python, JavaScript, Java, C/C++, Go, Rust, PHP, Ruby, Shell
- **Markup Languages**: HTML, XML, Markdown, reStructuredText
- **Data Formats**: JSON, YAML, CSV, TSV, TOML
- **Configuration Files**: INI, Dockerfile, Makefile, and more

### Enhanced Syntax Highlighting
For full syntax highlighting, install pygments:
```bash
pip install pygments
```
The viewer works without pygments but displays plain text only.

## Sub-shell Mode

TFM's sub-shell mode allows you to temporarily suspend the interface and enter a shell environment with pre-configured environment variables that provide access to the current state of both file panes and selected files.

### Activation
- Press `x` or `X` to enter sub-shell mode
- TFM suspends and starts a new shell session
- Type `exit` to return to TFM

### Environment Variables
When entering sub-shell mode, these environment variables are automatically set:

#### Directory Variables
- `LEFT_DIR`: Absolute path of the left file pane directory
- `RIGHT_DIR`: Absolute path of the right file pane directory  
- `THIS_DIR`: Absolute path of the currently focused pane directory
- `OTHER_DIR`: Absolute path of the non-focused pane directory

#### Selected Files Variables
- `LEFT_SELECTED`: Space-separated list of selected file names in the left pane
- `RIGHT_SELECTED`: Space-separated list of selected file names in the right pane
- `THIS_SELECTED`: Space-separated list of selected file names in the focused pane
- `OTHER_SELECTED`: Space-separated list of selected file names in the non-focused pane

### Usage Examples

```bash
# List files in both panes
ls -la "$LEFT_DIR" "$RIGHT_DIR"

# Copy selected files from current pane to other pane
for file in $THIS_SELECTED; do
    cp "$THIS_DIR/$file" "$OTHER_DIR/"
done

# Compare directory sizes
du -sh "$LEFT_DIR" "$RIGHT_DIR"

# Find files in both directories
find "$LEFT_DIR" "$RIGHT_DIR" -name "*.py"

# Archive selected files
if [ -n "$THIS_SELECTED" ]; then
    cd "$THIS_DIR"
    tar -czf selected_files.tar.gz $THIS_SELECTED
fi
```

### Test Scripts
- `python3 test_subshell.py` - Test environment variables
- `python3 demo_subshell.py` - See usage examples
- `bash examples_subshell.sh` - Interactive shell examples

## Searchable Dialogs

TFM features powerful searchable list dialogs for various operations:

### Features
- **Real-time Filtering**: Type to filter items as you search
- **Keyboard Navigation**: Full keyboard control with arrow keys
- **Fast Scrolling**: Page Up/Down for large lists
- **Visual Selection**: Clear indication of selected item
- **Cancel Support**: ESC to cancel any dialog

### Used For
- **Favorite Directories**: Quick navigation to bookmarked locations
- **File Operations**: Conflict resolution during copy/move operations
- **Future Features**: Extensible system for new dialog types

## Installation & Usage

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

### Using Make
```bash
# Run TFM
make run

# Run tests
make test

# Install package
make install
```

### Dependencies
- **Required**: Python 3.6+ with curses library (built-in on Unix systems)
- **Optional**: `pygments` for enhanced syntax highlighting
  ```bash
  pip install pygments
  ```

### System Requirements
- Python 3.6+
- Terminal with curses support (most Unix terminals, Windows Terminal, etc.)
- Write permissions for configuration directory (`~/.tfm/`)

## Configuration

TFM uses a flexible configuration system that allows you to customize key bindings, colors, and behavior.

### Configuration Files
- **User Config**: `~/.tfm/config.py` - Your personal customizations
- **Default Template**: `src/_config.py` - Template for creating user config
- **System Defaults**: `src/tfm_config.py` - Built-in default settings

### Customizable Settings
- **Key Bindings**: Remap any key to any action
- **Favorite Directories**: Quick access to frequently used locations
- **Text Editor**: Choose your preferred editor (vim, nano, emacs, etc.)
- **Colors**: Customize the color scheme
- **Pane Sizes**: Default pane ratios and minimum sizes

### Example Configuration
```python
class Config:
    # Text editor for file editing
    TEXT_EDITOR = 'nano'  # or 'vim', 'emacs', 'code', etc.
    
    # Favorite directories for quick access
    FAVORITE_DIRECTORIES = [
        {'name': 'Home', 'path': '~'},
        {'name': 'Projects', 'path': '~/dev'},
        {'name': 'Documents', 'path': '~/Documents'},
    ]
    
    # Custom key bindings
    KEY_BINDINGS = {
        'copy_files': ['c', 'C'],
        'move_files': ['m', 'M'],
        'delete_files': ['k', 'K'],
        'rename_file': ['r', 'R'],
        'favorites': ['j', 'J'],
        # ... other bindings
    }
```

## Project Structure

```
tfm/
├── src/                    # Source code
│   ├── tfm_main.py        # Main application logic and FileManager class
│   ├── tfm_config.py      # Configuration system and defaults
│   ├── tfm_const.py       # Constants and version information
│   ├── tfm_colors.py      # Color management and terminal colors
│   ├── tfm_text_viewer.py # Text file viewer with syntax highlighting
│   └── _config.py         # User configuration template
├── test/                   # Test files and demos
│   ├── test_*.py          # Unit and integration tests
│   ├── demo_*.py          # Interactive feature demonstrations
│   └── verify_*.py        # Feature verification scripts
├── doc/                    # Documentation
│   ├── *.md               # Feature documentation and guides
│   └── PROJECT_STRUCTURE.md # Detailed project organization
├── tfm.py                  # Main entry point
├── setup.py               # Package setup for pip installation
├── Makefile               # Build automation and common tasks
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Architecture

### Core Components
- **FileManager Class**: Main application controller in `tfm_main.py`
- **Configuration System**: User-customizable settings in `tfm_config.py`
- **Color Management**: Terminal color support in `tfm_colors.py`
- **Text Viewer**: Built-in file viewer in `tfm_text_viewer.py`
- **Dialog System**: User interaction dialogs for operations

### Key Features
- **Modular Design**: Clean separation between components
- **Event-Driven**: Keyboard input drives all operations
- **State Management**: Proper state handling for all modes and dialogs
- **Error Handling**: Comprehensive error reporting and recovery
- **Extensible**: Easy to add new features and operations

## Development & Testing

TFM includes comprehensive testing and development tools:

### Running Tests
```bash
# Run all tests
make test

# Run specific feature tests
python3 test/test_copy_integration.py
python3 test/test_move_integration.py
python3 test/test_delete_integration.py

# Interactive demos
python3 test/demo_favorites.py
python3 test/demo_create_file.py
```

### Development Setup
```bash
# Development installation
make dev-install

# Run from source
python3 tfm.py

# Clean temporary files
make clean
```

## Troubleshooting

### Common Issues

**Terminal Display Problems**
- Ensure your terminal supports curses
- Try resizing the terminal window
- Check terminal color support

**Key Binding Conflicts**
- Customize key bindings in `~/.tfm/config.py`
- Check for terminal-specific key mappings
- Use the help dialog (?) to verify current bindings

**Permission Errors**
- Ensure write permissions for target directories
- Check file ownership and permissions
- Run with appropriate user privileges

**Configuration Issues**
- Delete `~/.tfm/config.py` to reset to defaults
- Check configuration syntax in your custom config
- Refer to `src/_config.py` for template

### Getting Help
- Press `?` in TFM for built-in help
- Check documentation in the `doc/` directory
- Review test files for usage examples

## Contributing

TFM welcomes contributions! The project structure makes it easy to add new features:

### Adding Features
1. Implement in `src/` directory
2. Add tests in `test/` directory  
3. Document in `doc/` directory
4. Update README.md if needed

### Code Style
- Follow existing patterns and conventions
- Add comprehensive error handling
- Include tests for new functionality
- Document new features thoroughly

## License

TFM is released under the MIT License. See LICENSE file for details.

## Changelog

### v0.10 (Current)
- ✅ Comprehensive file operations (copy, move, delete, rename)
- ✅ Create files and directories
- ✅ Favorite directories with searchable dialog
- ✅ Enhanced text viewer with syntax highlighting
- ✅ Searchable list dialog system
- ✅ Sub-shell mode with environment variables
- ✅ Improved configuration system
- ✅ Comprehensive help system
- ✅ Extensive test coverage
- ✅ Modular project structure

### Previous Versions
- v0.9: Text viewer and editor integration
- v0.8: Help dialog and improved navigation
- v0.7: Color system and UI improvements
- v0.6: Basic dual-pane functionality

---

**TFM - Terminal File Manager**: Efficient, keyboard-driven file management for the terminal.