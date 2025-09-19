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
| `Enter` | Enter directory or view file info |
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
tfm_main.py       # Main application
tfm_const.py      # Constants and configuration
requirements.txt  # Dependencies (none required)
README.md         # This file
```

The application starts in your current working directory and allows you to navigate through your filesystem using keyboard controls.

## Architecture

The application is split into two main files:
- `tfm_main.py`: Contains the main application logic and UI components
- `tfm_const.py`: Contains all constants, configuration values, and version information

This modular approach makes it easy to maintain and update configuration without touching the main application code.