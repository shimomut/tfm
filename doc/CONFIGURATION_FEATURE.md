# TFM Configuration Feature

## Overview

TFM provides a flexible configuration system that allows you to customize the application's behavior, appearance, and features. Configuration is stored in a Python file that is automatically created on first run and can be edited to suit your preferences.

## Configuration File Location

TFM stores its configuration in:

```
~/.config/tfm/config.py
```

On first run, TFM creates this file with default settings. You can edit it with any text editor.

## Quick Start

### Viewing Current Configuration

To see your current configuration:

```bash
cat ~/.config/tfm/config.py
```

### Editing Configuration

Edit the configuration file:

```bash
# Using your preferred editor
nano ~/.config/tfm/config.py
vim ~/.config/tfm/config.py
code ~/.config/tfm/config.py
```

### Applying Changes

Changes take effect the next time you start TFM. No restart of the terminal is needed.

## Configuration Options

### Backend Settings

#### Preferred Backend

Choose which rendering backend TFM should use:

```python
# Backend options:
# 'curses' - Terminal mode (default, works on all platforms)
# 'coregraphics' - Desktop mode (macOS only, requires PyObjC)
PREFERRED_BACKEND = 'curses'
```

- **curses**: Traditional terminal-based interface, works everywhere
- **coregraphics**: Native macOS desktop window with better font rendering

See `doc/DESKTOP_MODE_GUIDE.md` for more details on desktop mode.

### Desktop Mode Settings

Configure desktop mode appearance (macOS only):

#### Font Configuration

```python
# Font cascade list (first available font is used, rest are fallbacks)
DESKTOP_FONT_NAME = ['Menlo', 'Monaco', 'Courier', 'Osaka-Mono', 'Hiragino Sans GB']

# Font size in points (8-72)
DESKTOP_FONT_SIZE = 12
```

The font cascade allows TFM to fall back to alternative fonts if the primary font doesn't support certain characters (e.g., Japanese, emoji).

#### Window Size

```python
# Initial window dimensions in pixels
DESKTOP_WINDOW_WIDTH = 1200
DESKTOP_WINDOW_HEIGHT = 800
```

These settings only apply when using the CoreGraphics backend in desktop mode.

### Display Settings

#### Pane Layout

Configure the default layout of panes:

```python
# Left pane width as ratio of total width (0.1 to 0.9)
DEFAULT_LEFT_PANE_RATIO = 0.5

# Log pane height as ratio of total height (0.1 to 0.5)
DEFAULT_LOG_HEIGHT_RATIO = 0.25
```

You can adjust these at runtime using the `[` `]` keys for pane width and `{` `}` keys for log height.

#### Color Settings

```python
# Enable colored output
USE_COLORS = True

# Color scheme selection
COLOR_SCHEME = 'dark'  # 'dark' or 'light'
```

See `doc/COLOR_SCHEMES_FEATURE.md` for details on available color schemes.

#### File Extension Display

```python
# Show file extensions in a separate column
SEPARATE_EXTENSIONS = True

# Maximum extension length to show separately (longer extensions stay with filename)
MAX_EXTENSION_LENGTH = 5
```

When enabled, file extensions are displayed in their own column for better alignment and readability.

#### Date Format

Customize how dates are displayed:

```python
# Date format options:
# 'short' - Shows "YY-MM-DD HH:mm" (compact format)
# 'full' - Shows "YYYY-MM-DD HH:mm:ss" (detailed format)
DATE_FORMAT = 'short'
```

See `doc/DATE_FORMAT_FEATURE.md` for more details.

#### File Details

Control what information is displayed for files:

```python
# Show hidden files by default
SHOW_HIDDEN_FILES = False
```

Toggle hidden files at runtime with the configured key binding (default: `.` key).

### Sorting Settings

Configure default sorting behavior:

```python
# Default sort mode: 'name', 'size', 'date'
DEFAULT_SORT_MODE = 'name'

# Sort in reverse order
DEFAULT_SORT_REVERSE = False
```

You can change sorting at runtime using the sort menu (`s` key) or quick sort keys (`1`-`4`).

### Behavior Settings

#### Hidden Files

Control visibility of hidden files:

```python
# Show hidden files by default
SHOW_HIDDEN_FILES = False
```

Toggle hidden files at runtime with the configured key binding (default: `.` key).

#### Confirmation Dialogs

Control when confirmation dialogs appear:

```python
# Confirm before deleting files
CONFIRM_DELETE = True

# Confirm before quitting TFM
CONFIRM_QUIT = True

# Confirm before copying files
CONFIRM_COPY = True

# Confirm before moving files
CONFIRM_MOVE = True

# Confirm before extracting archives
CONFIRM_EXTRACT_ARCHIVE = True
```

See `doc/CONFIRMATION_OPTIONS_FEATURE.md` for details.

#### Dual Pane Mode

Configure dual pane behavior:

```python
# Default left pane width ratio (0.1 to 0.9)
DEFAULT_LEFT_PANE_RATIO = 0.5
```

Adjust pane width at runtime using `[` and `]` keys.

See `doc/DUAL_PANE_FEATURE.md` for more details.

### Key Bindings

TFM provides extensive key binding customization:

```python
KEY_BINDINGS = {
    'quit': ['q', 'Q'],
    'help': ['?'],
    'toggle_hidden': ['.'],
    # ... many more bindings
}
```

Each action can have multiple keys assigned. Keys can be:
- Single characters: `'a'`, `'Q'`
- Special keys: `'HOME'`, `'END'`, `'F1'`, etc.

Some bindings support selection-aware behavior:

```python
KEY_BINDINGS = {
    'copy_files': {'keys': ['c', 'C'], 'selection': 'required'},
    'create_directory': {'keys': ['m', 'M'], 'selection': 'none'},
}
```

Selection modes:
- `'any'`: Works regardless of selection (default)
- `'required'`: Only works when items are selected
- `'none'`: Only works when no items are selected

See `doc/KEY_BINDINGS_SELECTION_FEATURE.md` for the complete list and customization guide.

### Favorite Directories

Configure quick-access directories:

```python
FAVORITE_DIRECTORIES = [
    {'name': 'Home', 'path': '~'},
    {'name': 'Documents', 'path': '~/Documents'},
    {'name': 'Projects', 'path': '~/Projects'},
    # Add your own favorites
]
```

Access favorites with the `j` key. Each entry needs a `name` and `path`.

See `doc/FAVORITE_DIRECTORIES_FEATURE.md` for more details.

### Performance Settings

#### Search and Navigation Limits

```python
# Maximum log messages to retain in memory
MAX_LOG_MESSAGES = 1000

# Maximum search results to prevent memory issues
MAX_SEARCH_RESULTS = 10000

# Maximum directories to scan for jump dialog
MAX_JUMP_DIRECTORIES = 5000
```

These limits prevent performance issues when working with large directories or search results.

#### History Settings

```python
# Maximum number of directory history entries to keep
MAX_HISTORY_ENTRIES = 100
```

Access history with the `h` key.

#### Adaptive FPS

Control frame rate adaptation:

```python
# Enable adaptive FPS (reduces CPU usage when idle)
ADAPTIVE_FPS_ENABLED = True

# Active FPS (when user is interacting)
ACTIVE_FPS = 30

# Idle FPS (when no user interaction)
IDLE_FPS = 5

# Time before switching to idle FPS (seconds)
IDLE_TIMEOUT = 2.0
```

#### Caching

Configure caching behavior:

```python
# Enable directory caching
CACHE_ENABLED = True

# Cache timeout (seconds)
CACHE_TIMEOUT = 300

# Maximum cache size (entries)
MAX_CACHE_SIZE = 1000
```

### Progress Animation

Configure progress indicators:

```python
# Animation pattern: 'spinner', 'dots', 'progress', 'bounce', 'pulse', 'wave', 'clock', 'arrow'
PROGRESS_ANIMATION_PATTERN = 'spinner'

# Animation frame update interval in seconds
PROGRESS_ANIMATION_SPEED = 0.2
```

See `doc/PROGRESS_ANIMATION_FEATURE.md` for visual examples of each pattern.

### Logging Settings

#### Log Pane

Configure the log pane:

```python
# Default log pane height ratio (0.1 to 0.5)
DEFAULT_LOG_HEIGHT_RATIO = 0.25

# Maximum log messages to retain
MAX_LOG_MESSAGES = 1000
```

Adjust log pane height at runtime using `{` and `}` keys.

See `doc/LOGGING_FEATURE.md` for more details.

#### Remote Monitoring

Enable remote log monitoring:

```python
# Enable remote monitoring
REMOTE_MONITORING_ENABLED = False

# Remote monitoring port
REMOTE_MONITORING_PORT = 9999
```

See `doc/REMOTE_LOG_MONITORING_FEATURE.md` for details.

### Text Editor

Configure the default text editor:

```python
# Text editor (automatically set based on backend mode)
TEXT_EDITOR = 'code' if is_desktop_mode() else 'vim'
```

In terminal mode, defaults to `vim`. In desktop mode, defaults to `code` (VS Code).

You can override this to use your preferred editor:

```python
TEXT_EDITOR = 'nano'  # or 'emacs', 'subl', etc.
```

### External Programs

Configure external program integration:

```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
    {'name': 'Disk Usage', 'command': ['du', '-sh', '*']},
    # Add your own programs
]
```

Each program entry has:
- `name`: Display name in the programs menu
- `command`: List of command and arguments
- `options` (optional): Dictionary with program-specific options
  - `auto_return`: If `True`, returns to TFM without waiting for user input

Access external programs with the `x` key.

See `doc/EXTERNAL_PROGRAMS_FEATURE.md` for more details.

### File Associations

Configure file type associations:

```python
FILE_ASSOCIATIONS = [
    # PDF files
    {
        'pattern': '*.pdf',
        'open|view': ['open', '-a', 'Preview'],
    },
    # Image files
    {
        'pattern': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
        'open|view': ['open', '-a', 'Preview'],
    },
    # Add your own associations
]
```

Each association entry has:
- `pattern`: File pattern(s) to match (single string or list)
- `open|view`: Command for both open and view actions (combined)
- `open`: Command for open action only
- `view`: Command for view action only
- `edit`: Command for edit action

Commands can be:
- List format: `['command', 'arg1', 'arg2']`
- String format: `'command arg1 arg2'`

See `doc/FILE_ASSOCIATIONS_FEATURE.md` for details.

### Archive Support

Configure archive browsing:

```python
# Enable archive virtual directory browsing
ARCHIVE_BROWSING_ENABLED = True

# Supported archive formats
ARCHIVE_FORMATS = ['.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2']
```

See `doc/ARCHIVE_VIRTUAL_DIRECTORY_FEATURE.md` for more details.

### AWS S3 Support

Configure S3 integration:

```python
# S3 cache TTL in seconds
S3_CACHE_TTL = 60
```

The cache TTL controls how long S3 directory listings are cached before being refreshed.

See `doc/S3_SUPPORT_FEATURE.md` for setup and usage.

### Unicode and Wide Character Support

Configure Unicode handling:

```python
# Unicode mode: 'auto', 'full', 'basic', 'ascii'
UNICODE_MODE = 'auto'

# Show warnings for Unicode processing errors
UNICODE_WARNINGS = True

# Fallback character for unrepresentable characters in ASCII mode
UNICODE_FALLBACK_CHAR = '?'

# Enable caching of display width calculations for performance
UNICODE_ENABLE_CACHING = True

# Maximum number of cached width calculations
UNICODE_CACHE_SIZE = 1000

# Enable automatic terminal capability detection
UNICODE_TERMINAL_DETECTION = True

# Force ASCII fallback mode regardless of terminal capabilities
UNICODE_FORCE_FALLBACK = False
```

Unicode modes:
- `'auto'`: Automatically detect terminal capabilities (recommended)
- `'full'`: Full Unicode support with wide character handling
- `'basic'`: Basic Unicode support, treat all characters as single-width
- `'ascii'`: ASCII-only fallback mode for limited terminals

See `doc/WIDE_CHARACTER_SUPPORT_FEATURE.md` for more details.

### Desktop Mode (macOS)

Configure desktop mode settings:

```python
# Backend preference: 'curses' or 'coregraphics'
PREFERRED_BACKEND = 'curses'

# Font cascade for desktop mode
DESKTOP_FONT_NAME = ['Menlo', 'Monaco', 'Courier', 'Osaka-Mono', 'Hiragino Sans GB']

# Font size in points
DESKTOP_FONT_SIZE = 12

# Initial window dimensions
DESKTOP_WINDOW_WIDTH = 1200
DESKTOP_WINDOW_HEIGHT = 800
```

See `doc/DESKTOP_MODE_GUIDE.md` for more details.

### Window Geometry

Configure window size and position persistence:

```python
# Remember window geometry between sessions
REMEMBER_WINDOW_GEOMETRY = True

# Default window size (columns x rows)
DEFAULT_WINDOW_SIZE = (120, 40)
```

See `doc/WINDOW_GEOMETRY_PERSISTENCE_FEATURE.md` for details.

## Configuration Examples

### Minimal Configuration

For a minimal, fast configuration:

```python
# Minimal configuration for speed
PREFERRED_BACKEND = 'curses'
COLOR_SCHEME = 'dark'
SHOW_HIDDEN_FILES = False
USE_COLORS = True
MAX_LOG_MESSAGES = 500
```

### Power User Configuration

For maximum features and information:

```python
# Power user configuration
PREFERRED_BACKEND = 'curses'
COLOR_SCHEME = 'dark'
DATE_FORMAT = 'full'
SHOW_HIDDEN_FILES = True
SEPARATE_EXTENSIONS = True
DEFAULT_LEFT_PANE_RATIO = 0.5
DEFAULT_LOG_HEIGHT_RATIO = 0.3
MAX_LOG_MESSAGES = 2000
MAX_SEARCH_RESULTS = 20000
PROGRESS_ANIMATION_PATTERN = 'wave'
```

### Desktop Mode Configuration (macOS)

For desktop mode with custom appearance:

```python
# Desktop mode configuration
PREFERRED_BACKEND = 'coregraphics'
DESKTOP_FONT_NAME = ['SF Mono', 'Menlo', 'Monaco']
DESKTOP_FONT_SIZE = 14
DESKTOP_WINDOW_WIDTH = 1400
DESKTOP_WINDOW_HEIGHT = 900
COLOR_SCHEME = 'light'
TEXT_EDITOR = 'code'
```

### Developer Configuration

For development and debugging:

```python
# Developer configuration
PREFERRED_BACKEND = 'curses'
MAX_LOG_MESSAGES = 5000
UNICODE_WARNINGS = True
UNICODE_MODE = 'full'
PROGRESS_ANIMATION_SPEED = 0.1
```

## Troubleshooting

### Configuration Not Loading

**Problem:** Changes to configuration file don't take effect.

**Solutions:**
1. Check file location: `~/.config/tfm/config.py`
2. Verify Python syntax (no syntax errors)
3. Restart TFM completely
4. Check file permissions (should be readable)

### Syntax Errors

**Problem:** TFM fails to start after editing configuration.

**Solutions:**
1. Check Python syntax in configuration file
2. Look for missing quotes, commas, or brackets
3. Restore default configuration:
   ```bash
   rm ~/.config/tfm/config.py
   # TFM will recreate it on next run
   ```

### Invalid Values

**Problem:** Configuration option doesn't work as expected.

**Solutions:**
1. Check documentation for valid values
2. Verify spelling of option names
3. Check data types (string vs number vs boolean)
4. Review default configuration for examples

### Finding Configuration Options

**Problem:** Can't find a specific configuration option.

**Solutions:**
1. Check this documentation for available options
2. Look at default configuration file
3. Search feature-specific documentation
4. Check `src/_config.py` for all available options

## Best Practices

### Backup Your Configuration

Before making major changes:

```bash
cp ~/.config/tfm/config.py ~/.config/tfm/config.py.backup
```

### Start Small

Make one change at a time and test:

1. Edit one option
2. Save file
3. Restart TFM
4. Verify change works
5. Repeat for next option

### Use Comments

Document your customizations:

```python
# Increased cache size for large directories
MAX_CACHE_SIZE = 5000

# Disabled confirmations for faster workflow
CONFIRM_DELETE = False  # Be careful with this!
```

### Test Changes

After editing configuration:

1. Start TFM
2. Test affected features
3. Check for errors in log pane
4. Verify behavior matches expectations

## Related Documentation

- [Color Schemes](COLOR_SCHEMES_FEATURE.md) - Available color schemes
- [Date Format](DATE_FORMAT_FEATURE.md) - Date display options
- [Logging](LOGGING_FEATURE.md) - Logging configuration
- [External Programs](EXTERNAL_PROGRAMS_FEATURE.md) - External program integration
- [File Associations](FILE_ASSOCIATIONS_FEATURE.md) - File type associations
- [Key Bindings](KEY_BINDINGS_SELECTION_FEATURE.md) - Key binding configuration
- [Desktop Mode](DESKTOP_MODE_GUIDE.md) - Desktop mode settings (macOS)
- [TFM User Guide](TFM_USER_GUIDE.md) - Complete user guide

## Conclusion

TFM's configuration system provides extensive customization options while maintaining sensible defaults. Start with the default configuration and gradually customize options to match your workflow and preferences. Most users will only need to adjust a few settings, while power users can fine-tune every aspect of TFM's behavior.
