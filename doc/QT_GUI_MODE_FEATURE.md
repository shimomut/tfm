# Qt GUI Mode Feature

## Overview

TFM (TUI File Manager) now supports both Terminal User Interface (TUI) and Graphical User Interface (GUI) modes. The GUI mode provides a modern, window-based interface while maintaining the same powerful dual-pane file management workflow you know from TUI mode.

## Launching GUI Mode

### Basic Launch

To launch TFM in GUI mode, use the `tfm_qt.py` entry point:

```bash
python tfm_qt.py
```

Or if installed via pip:

```bash
tfm-qt
```

### Launch with Specific Directories

You can specify starting directories for both panes:

```bash
python tfm_qt.py /path/to/left/dir /path/to/right/dir
```

### TUI Mode (Traditional)

To launch in traditional terminal mode:

```bash
python tfm.py
```

Or:

```bash
tfm
```

## GUI-Specific Features

### Mouse Support

The GUI mode provides full mouse support for intuitive file management:

#### File Selection
- **Single Click**: Toggle selection of a file
- **Ctrl+Click**: Add files to selection (multi-select)
- **Shift+Click**: Select range of files between last selected and clicked file
- **Double Click**: Navigate into directory or open file

#### Pane Switching
- **Click on Pane**: Switch focus to that pane
- **Click on Header**: Switch focus to that pane

#### Context Menus
- **Right-Click on File**: Show context menu with file operations
- **Right-Click on Pane**: Show pane-specific options

### Drag and Drop

GUI mode supports drag-and-drop operations:

#### Within TFM
- **Drag files between panes**: Copy or move files (hold Shift for move)
- **Drag to reorder**: Reorder files in custom sort mode

#### External Applications
- **Drag files from TFM**: Drag files to external applications
- **Drag files to TFM**: Drop files into a pane to copy them

### Toolbar

The toolbar provides quick access to common operations:

- **Copy**: Copy selected files to other pane
- **Move**: Move selected files to other pane
- **Delete**: Delete selected files
- **Rename**: Rename selected file
- **New Folder**: Create new directory
- **Refresh**: Refresh current pane
- **Search**: Open search dialog

You can show/hide the toolbar in configuration.

### Menu Bar

The menu bar organizes all TFM features:

#### File Menu
- New File
- New Folder
- Rename
- Delete
- Copy
- Move
- Exit

#### Edit Menu
- Select All
- Deselect All
- Invert Selection
- Preferences

#### View Menu
- Show/Hide Toolbar
- Show/Hide Status Bar
- Show/Hide Log Pane
- Toggle Dual Pane
- Refresh

#### Tools Menu
- Search
- Batch Rename
- External Programs
- File Associations

#### Help Menu
- Keyboard Shortcuts
- About TFM

### Dialogs

GUI mode provides native dialogs for all operations:

- **Confirmation Dialogs**: Yes/No/Cancel options with clear messaging
- **Input Dialogs**: Text input with validation and default values
- **List Selection Dialogs**: Searchable lists with multi-select support
- **Info Dialogs**: Scrollable information display
- **Progress Dialogs**: Real-time progress with cancellation support

## Keyboard Shortcuts in GUI Mode

All TUI keyboard shortcuts work in GUI mode. Here are the most commonly used:

### Navigation
- **Tab**: Switch between left and right panes
- **Arrow Keys**: Navigate file list
- **Home**: Jump to first file
- **End**: Jump to last file
- **Page Up/Down**: Scroll one page
- **Backspace**: Go to parent directory

### File Operations
- **F5**: Copy selected files to other pane
- **F6**: Move selected files to other pane
- **F7**: Create new directory
- **F8**: Delete selected files
- **Shift+F4**: Create new file
- **Shift+F6**: Rename selected file

### Selection
- **Insert**: Toggle selection of current file
- **+**: Select files by pattern
- **-**: Deselect files by pattern
- *****: Invert selection
- **Ctrl+A**: Select all files

### View
- **Ctrl+L**: Toggle log pane
- **Ctrl+R**: Refresh current pane
- **.** (dot): Toggle hidden files

### Application
- **Ctrl+Q** or **Cmd+Q**: Quit TFM
- **F1**: Show help
- **F10**: Show menu bar (if hidden)

### External Programs
- **F2**: Launch configured external program #1
- **F3**: Launch configured external program #2
- **F4**: Launch configured external program #3
- (Additional function keys for more programs)

## Configuration Options

GUI mode adds several configuration options to `~/.tfm/config.py`:

### Window Geometry

```python
# Window size (width, height in pixels)
GUI_WINDOW_WIDTH = 1200
GUI_WINDOW_HEIGHT = 800

# Window position (x, y in pixels, None = center)
GUI_WINDOW_X = None
GUI_WINDOW_Y = None
```

The window automatically saves its size and position when you resize or move it.

### Font Settings

```python
# Font family for file listings
GUI_FONT_FAMILY = 'Monospace'

# Font size in points
GUI_FONT_SIZE = 10
```

### UI Elements

```python
# Show/hide toolbar
GUI_SHOW_TOOLBAR = True

# Show/hide menu bar
GUI_SHOW_MENUBAR = True

# Enable drag and drop
GUI_ENABLE_DRAG_DROP = True
```

### Color Schemes

GUI mode uses the same color scheme configuration as TUI mode:

```python
# Color scheme: 'dark' or 'light'
COLOR_SCHEME = 'dark'

# File type colors (same as TUI)
COLOR_DIRECTORY = 'blue'
COLOR_EXECUTABLE = 'green'
COLOR_ARCHIVE = 'red'
# ... etc
```

You can change themes dynamically without restarting TFM.

## Feature Comparison: TUI vs GUI

| Feature | TUI Mode | GUI Mode |
|---------|----------|----------|
| Dual-pane layout | ✓ | ✓ |
| Keyboard shortcuts | ✓ | ✓ |
| Mouse support | Limited | Full |
| Drag and drop | ✗ | ✓ |
| Context menus | ✗ | ✓ |
| Toolbar | ✗ | ✓ |
| Menu bar | ✗ | ✓ |
| File operations | ✓ | ✓ |
| External programs | ✓ | ✓ |
| S3 support | ✓ | ✓ |
| Search | ✓ | ✓ |
| Batch rename | ✓ | ✓ |
| Progress indicators | Text | Graphical |
| Window persistence | N/A | ✓ |
| Remote terminal | ✓ | ✗ |

## Tips and Tricks

### Efficient Workflow

1. **Use keyboard for speed**: Even in GUI mode, keyboard shortcuts are faster for common operations
2. **Use mouse for precision**: Mouse is great for selecting specific files or ranges
3. **Combine both**: Use keyboard to navigate, mouse to select
4. **Learn the shortcuts**: Press F1 to see all available keyboard shortcuts

### Window Management

- **Resize panes**: Drag the splitter between panes to adjust widths
- **Maximize**: Double-click title bar to maximize window
- **Remember position**: Window automatically remembers size and position

### Selection Techniques

- **Quick select**: Click first file, Shift+click last file to select range
- **Add to selection**: Ctrl+click to add individual files
- **Select all**: Ctrl+A to select all files in current pane
- **Invert**: Press * to invert selection

### External Programs

- **Quick launch**: Use function keys (F2, F3, F4) for frequently used programs
- **Context menu**: Right-click for program-specific options
- **Environment variables**: External programs receive TFM context automatically

## Troubleshooting

### GUI Won't Launch

**Problem**: Error message about Qt not being installed

**Solution**: Install Qt dependencies:
```bash
pip install PySide6
```

### Window Appears Off-Screen

**Problem**: Saved window position is off-screen after monitor change

**Solution**: Delete window geometry from config:
```python
GUI_WINDOW_X = None
GUI_WINDOW_Y = None
```

Or delete the entire config file to reset all settings.

### Font Too Small/Large

**Problem**: Text is hard to read

**Solution**: Adjust font size in configuration:
```python
GUI_FONT_SIZE = 12  # Increase for larger text
```

### Keyboard Shortcuts Not Working

**Problem**: Some keyboard shortcuts don't work

**Solution**: 
1. Check if another application is capturing the shortcut
2. Try using the menu bar to access the function
3. Check configuration for custom key bindings

### Drag and Drop Not Working

**Problem**: Cannot drag files

**Solution**: Enable drag and drop in configuration:
```python
GUI_ENABLE_DRAG_DROP = True
```

## Advanced Usage

### Custom Themes

You can create custom color schemes by defining colors in your configuration:

```python
# Custom color scheme
CUSTOM_COLORS = {
    'directory': '#4A90E2',
    'executable': '#7ED321',
    'archive': '#D0021B',
    'selected': '#F5A623',
    'cursor': '#50E3C2',
}
```

### Multiple Windows

You can launch multiple TFM GUI instances:

```bash
python tfm_qt.py /path/one /path/two &
python tfm_qt.py /path/three /path/four &
```

Each instance is independent with its own configuration.

### Integration with Desktop Environment

#### Linux
Create a desktop entry in `~/.local/share/applications/tfm.desktop`:

```ini
[Desktop Entry]
Name=TFM File Manager
Comment=Dual-pane file manager
Exec=tfm-qt
Icon=folder
Terminal=false
Type=Application
Categories=System;FileManager;
```

#### macOS
Create an application bundle or use Automator to create an app wrapper.

#### Windows
Create a shortcut to `tfm_qt.py` and pin it to taskbar.

## Getting Help

- **In-app help**: Press F1 to show keyboard shortcuts
- **Documentation**: See README.md for general TFM documentation
- **Issues**: Report bugs on the project's issue tracker
- **Configuration**: See `_config.py` for all available options

## See Also

- [TFM User Guide](TFM_USER_GUIDE.md) - Complete guide to TFM features
- [File Associations](FILE_ASSOCIATIONS_FEATURE.md) - Configure file type handlers
- [External Programs](EXTERNAL_PROGRAMS_FEATURE.md) - Integrate external tools
- [S3 Support](doc/S3_SUPPORT_FEATURE.md) - Working with cloud storage
