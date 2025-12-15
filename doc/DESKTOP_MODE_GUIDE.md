# TFM Desktop Mode Guide

## Overview

TFM can run as a native macOS desktop application with GPU acceleration, providing a modern windowed experience while maintaining the same powerful keyboard-driven interface you know from terminal mode.

## Quick Start

### Installation

```bash
# Install PyObjC (one-time setup)
pip install pyobjc-framework-Cocoa

# Run in desktop mode
python3 tfm.py --desktop
```

### First Launch

When you launch TFM in desktop mode:
1. A native macOS window appears
2. The interface looks identical to terminal mode
3. All keyboard shortcuts work the same way
4. You can resize the window or go full-screen

## Features

### Native macOS Experience

- **Resizable Window**: Drag window edges to resize
- **Full-Screen Mode**: Click the green button or use macOS full-screen shortcut
- **Window Controls**: Standard macOS minimize, maximize, close buttons
- **Menu Bar Integration**: Native macOS menu bar (when focused)

### Performance Benefits

- **High-Quality Rendering**: Smooth rendering using CoreGraphics
- **Better Responsiveness**: Immediate input handling
- **Smooth Scrolling**: No tearing or lag when navigating large directories
- **Lower CPU Usage**: GPU handles rendering, freeing up CPU

### Visual Improvements

- **True RGB Colors**: Accurate color reproduction
- **Better Fonts**: Crisp font rendering with anti-aliasing
- **Customizable Fonts**: Choose your preferred monospace font
- **Adjustable Size**: Change font size for better readability


## Configuration

### Setting Desktop Mode as Default

Edit `~/.tfm/config.py`:

```python
# Use desktop mode by default
PREFERRED_BACKEND = 'coregraphics'
```

Now `python3 tfm.py` will launch in desktop mode automatically.

### Customizing Appearance

```python
# Font settings
DESKTOP_FONT_NAME = 'Menlo'         # Font name (see available fonts below)
DESKTOP_FONT_SIZE = 14              # Font size in points (10-24 recommended)

# Window settings
DESKTOP_WINDOW_WIDTH = 1200         # Initial width in pixels
DESKTOP_WINDOW_HEIGHT = 800         # Initial height in pixels
```

### Available Fonts

Common monospace fonts on macOS:

**Built-in Fonts**:
- `Menlo` (default) - Apple's default monospace font, excellent readability
- `Monaco` - Classic Mac monospace font, slightly more compact
- `Courier New` - Traditional monospace font, widely compatible

**Optional Fonts** (if installed):
- `SF Mono` - San Francisco Mono, modern Apple font
- `Fira Code` - Popular programming font with ligatures
- `JetBrains Mono` - Modern programming font, excellent for code
- `Source Code Pro` - Adobe's programming font
- `Hack` - Designed specifically for source code

To check installed fonts, open `Font Book.app` and filter by "Fixed Width" (monospace).

### Font Size Guidelines

- **Small** (10-12pt): More content visible, requires good eyesight
- **Medium** (13-15pt): Balanced readability and content density (recommended)
- **Large** (16-20pt): Better for presentations or accessibility
- **Extra Large** (21-24pt): Maximum readability, less content visible

### Window Size Guidelines

**Common Resolutions**:
- **Laptop** (13-15"): 1200x800 or 1400x900
- **Desktop** (24-27"): 1600x1000 or 1800x1200
- **Large Display** (32"+): 2000x1400 or larger

The window size is just the initial size - you can resize it anytime.

## Usage

### Launching Desktop Mode

```bash
# Method 1: Use --desktop flag
python3 tfm.py --desktop

# Method 2: Use --backend flag
python3 tfm.py --backend coregraphics

# Method 3: Set as default in config
# Then just run:
python3 tfm.py
```

### Switching Between Modes

You can easily switch between terminal and desktop modes:

```bash
# Terminal mode
python3 tfm.py --backend curses

# Desktop mode
python3 tfm.py --backend coregraphics
```

All your settings, favorites, and history are shared between modes.


### Keyboard Shortcuts

All keyboard shortcuts work identically in desktop mode:

- **Navigation**: Arrow keys, Tab, Enter, Backspace
- **File Operations**: c/C (copy), m/M (move), k/K (delete), r/R (rename)
- **Selection**: Space, a (all files), A (all items)
- **Search**: f (incremental), F (filename), G (content)
- **Help**: ? (help dialog)
- **Quit**: q/Q

See the [User Guide](TFM_USER_GUIDE.md) for complete keyboard reference.

### Window Management

**Resizing**:
- Drag window edges or corners
- Window content adjusts automatically
- Minimum size enforced for usability

**Full-Screen**:
- Click green button in title bar
- Or use macOS keyboard shortcut (usually Ctrl+Cmd+F)
- Exit full-screen the same way

**Multiple Windows**:
- Currently, TFM supports one window at a time
- Launch multiple instances for multiple windows

## Troubleshooting

### Desktop Mode Won't Start

**Problem**: Desktop mode doesn't launch or falls back to terminal mode.

**Solutions**:
1. Verify you're on macOS:
   ```bash
   uname -s  # Should show "Darwin"
   ```

2. Install PyObjC:
   ```bash
   pip install pyobjc-framework-Cocoa
   ```

3. Verify installation:
   ```bash
   python3 -c "import objc; print('PyObjC installed successfully')"
   ```

4. Check Python version:
   ```bash
   python3 --version  # Should be 3.9 or higher
   ```

### Window Doesn't Appear

**Problem**: Desktop mode starts but no window appears.

**Solutions**:
1. Check console output for error messages
2. Try terminal mode first to verify TFM works:
   ```bash
   python3 tfm.py --backend curses
   ```
3. Check macOS version (10.13+ required)
4. Restart your Mac and try again

### Font Not Found

**Problem**: Error message about font not being available.

**Solutions**:
1. Check font name spelling (case-sensitive):
   ```python
   DESKTOP_FONT_NAME = 'Menlo'  # Correct
   DESKTOP_FONT_NAME = 'menlo'  # Wrong - case matters
   ```

2. Verify font is installed:
   - Open `Font Book.app`
   - Search for the font name
   - Check "Fixed Width" category for monospace fonts

3. Use a default font:
   ```python
   DESKTOP_FONT_NAME = 'Menlo'  # Always available on macOS
   ```

4. Remove font setting to use default:
   ```python
   # Comment out or remove this line
   # DESKTOP_FONT_NAME = 'CustomFont'
   ```


### Performance Issues

**Problem**: Desktop mode feels slow or laggy.

**Solutions**:
1. Check Activity Monitor:
   - Open Activity Monitor
   - Look for TFM process
   - Check CPU and GPU usage

2. Reduce window size:
   ```python
   DESKTOP_WINDOW_WIDTH = 1000   # Smaller window
   DESKTOP_WINDOW_HEIGHT = 700
   ```

3. Try a different font:
   ```python
   DESKTOP_FONT_NAME = 'Monaco'  # Simpler font
   ```

4. Close other applications to free resources

5. Desktop mode should run at 60 FPS - if not, check for:
   - Other GPU-intensive applications
   - macOS version (older versions may be slower)
   - Available system memory

### Colors Look Wrong

**Problem**: Colors appear different from terminal mode.

**Explanation**: Desktop mode uses true RGB colors, which may look different from terminal mode's limited color palette. This is expected and provides more accurate colors.

**Solutions**:
1. Adjust color scheme in configuration
2. Try different color schemes with `Z` key
3. Colors should be more accurate in desktop mode, not worse

### Text Rendering Issues

**Problem**: Text appears blurry or misaligned.

**Solutions**:
1. Try a different font size:
   ```python
   DESKTOP_FONT_SIZE = 14  # Try different sizes
   ```

2. Use a different font:
   ```python
   DESKTOP_FONT_NAME = 'Monaco'  # Try different fonts
   ```

3. Check display scaling settings in macOS System Preferences

4. Ensure you're using a monospace font (fixed-width)

## Comparison: Terminal vs Desktop Mode

| Feature | Terminal Mode | Desktop Mode |
|---------|--------------|--------------|
| **Platform** | All (macOS, Linux, Windows) | macOS only |
| **Dependencies** | Python + curses | Python + PyObjC |
| **Window** | Terminal window | Native macOS window |
| **Rendering** | Terminal-based | GPU-accelerated |
| **Performance** | Good | Excellent (60 FPS) |
| **Colors** | Terminal palette | True RGB |
| **Fonts** | Terminal font | Customizable |
| **Resizing** | Terminal resize | Native window resize |
| **Full-Screen** | Terminal full-screen | Native full-screen |
| **Keyboard** | Identical | Identical |
| **Features** | All features | All features |

## Best Practices

### When to Use Desktop Mode

**Recommended for**:
- Daily use on macOS
- Better visual experience
- Smoother performance
- Customized fonts and colors
- Presentations or screen sharing

### When to Use Terminal Mode

**Recommended for**:
- SSH sessions
- Remote servers
- Non-macOS systems
- Minimal dependencies
- Integration with terminal workflows

### Switching Strategies

**Flexible Approach**:
- Use desktop mode for local work
- Use terminal mode for remote work
- Keep both options available

**Configuration**:
```python
# Set desktop as default
PREFERRED_BACKEND = 'coregraphics'

# Override with command line when needed:
# python3 tfm.py --backend curses  # Force terminal mode
```

## Advanced Topics

### Custom Launch Scripts

Create a launcher script for easy access:

```bash
#!/bin/bash
# ~/bin/tfm-desktop

python3 /path/to/tfm/tfm.py --desktop "$@"
```

Make it executable:
```bash
chmod +x ~/bin/tfm-desktop
```

Now you can run:
```bash
tfm-desktop --left ~/projects --right ~/documents
```

### Integration with macOS

**Dock Integration**:
- Desktop mode appears in Dock when running
- Can right-click for options
- Shows in Cmd+Tab app switcher

**Spotlight Integration**:
- Create an Automator application
- Add "Run Shell Script" action
- Use: `python3 /path/to/tfm/tfm.py --desktop`
- Save as "TFM" in Applications folder

## Getting Help

If you encounter issues not covered here:

1. Check console output for error messages
2. Try terminal mode to isolate desktop-specific issues
3. Review the [User Guide](TFM_USER_GUIDE.md)
4. Check [TTK Integration](dev/TTK_INTEGRATION.md) for technical details
5. Report issues on GitHub with:
   - macOS version
   - Python version
   - PyObjC version
   - Console output
   - Steps to reproduce

## Summary

Desktop mode provides a modern, native macOS experience while maintaining TFM's powerful keyboard-driven interface. With GPU acceleration, true RGB colors, and customizable fonts, it offers an enhanced experience for macOS users while remaining fully compatible with terminal mode.

Key benefits:
- ✅ Native macOS window
- ✅ 60 FPS GPU acceleration
- ✅ True RGB colors
- ✅ Customizable fonts
- ✅ Identical functionality
- ✅ Easy switching between modes

Try desktop mode today and experience TFM in a whole new way!
