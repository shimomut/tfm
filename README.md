# TUI File Manager v0.10

A terminal-based file manager built with Python's curses library. Navigate your filesystem with keyboard shortcuts in a clean, intuitive interface.

## Features

- **Dual Pane Interface**: Left and right panes for easy file operations between directories
- **Log Pane**: Bottom pane captures stdout and stderr output with timestamps
- **Pane Switching**: Use Tab to switch between panes, active pane highlighted in header
- **Directory Navigation**: Browse directories with arrow keys or vim-style navigation (j/k)
- **File Information**: View file sizes and modification dates
- **Hidden Files**: Toggle visibility of hidden files with 'h'
- **Color Coding**: 
  - Blue/bold for directories
  - Green for executable files
  - Yellow highlight for selected items in active pane
  - Underline for selected items in inactive pane
  - Red text for stderr messages in log pane
- **Log Management**: Scroll through log messages, auto-scrolls to newest
- **Text File Viewer**: Built-in text viewer with syntax highlighting for 20+ file formats
- **Keyboard Navigation**: Full keyboard control with intuitive shortcuts
- **Cross-platform**: Works on macOS, Linux, and Windows (with proper terminal support)

## Controls

| Key | Action |
|-----|--------|
| `↑/k` | Move selection up in active pane |
| `↓/j` | Move selection down in active pane |
| `Tab` | Switch between left and right panes |
| `→` | Switch to right pane (from left) OR go to parent (in right pane) |
| `←` | Switch to left pane (from right) OR go to parent (in left pane) |
| `Enter` | Enter directory or view text file with syntax highlighting |
| `v` | View selected file in text viewer (same as Enter for text files) |
| `Backspace` | Go to parent directory |
| `l` | Scroll log pane up (older messages) |
| `L` | Scroll log pane down (newer messages) |
| `t` | Test log output (demonstrates stdout/stderr capture) |
| `h` | Toggle hidden files visibility |
| `Home` | Go to first item in active pane |
| `End` | Go to last item in active pane |
| `Page Up` | Move up 10 items in active pane |
| `Page Down` | Move down 10 items in active pane |
| `q` | Quit application |

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

### Enhanced Syntax Highlighting
For full syntax highlighting, install pygments:
```bash
pip install pygments
```
The viewer works without pygments but displays plain text only.

## Installation & Usage

1. Ensure you have Python 3.6+ installed
2. Run the file manager:
   ```bash
   python3 tfm_main.py
   ```

No additional dependencies required - uses Python's built-in `curses` library.

## Requirements

- Python 3.6+
- Terminal with curses support (most Unix terminals, Windows Terminal, etc.)

## File Structure

```
tfm_main.py           # Main application
tfm_const.py          # Constants and configuration
tfm_colors.py         # Color definitions and management
tfm_config.py         # Configuration system
tfm_text_viewer.py    # Text file viewer with syntax highlighting
_config.py            # Default configuration template
requirements.txt      # Dependencies (pygments optional)
README.md             # This file
TEXT_VIEWER_FEATURE.md # Detailed text viewer documentation
```

The application starts in your current working directory and allows you to navigate through your filesystem using keyboard controls.

## Architecture

The application is split into two main files:
- `tfm_main.py`: Contains the main application logic and UI components
- `tfm_const.py`: Contains all constants, configuration values, and version information

This modular approach makes it easy to maintain and update configuration without touching the main application code.