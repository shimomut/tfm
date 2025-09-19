# TFM Text Viewer Feature

## Overview

TFM now includes a built-in text file viewer with syntax highlighting support for popular file formats. The viewer provides a clean, efficient way to view text files without leaving the file manager.

## Features

### ✅ Syntax Highlighting
- **Automatic detection** of file types based on extension and content
- **Pygments integration** for professional syntax highlighting
- **Graceful fallback** when pygments is not available
- **Support for 20+ file formats** including Python, JavaScript, JSON, Markdown, YAML, and more

### ✅ Navigation Controls
- **Vertical scrolling**: `↑↓` arrow keys or `j/k` (vim-style)
- **Horizontal scrolling**: `←→` arrow keys or `h/l` (vim-style)
- **Page navigation**: `Page Up/Down` for faster scrolling
- **Jump to start/end**: `Home/End` keys
- **Smooth scrolling** with proper boundary handling

### ✅ Display Options
- **Line numbers**: Toggle with `n` key (on by default)
- **Line wrapping**: Toggle with `w` key (off by default)
- **Syntax highlighting**: Toggle with `s` key (on by default if pygments available)
- **Clean interface** with file info and status indicators

### ✅ File Format Support

#### Programming Languages
- Python (`.py`)
- JavaScript (`.js`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`, `.hpp`)
- Go (`.go`)
- Rust (`.rs`)
- PHP (`.php`)
- Ruby (`.rb`)
- Shell scripts (`.sh`, `.bash`, `.zsh`)

#### Markup & Documentation
- HTML (`.html`)
- XML (`.xml`)
- Markdown (`.md`)
- reStructuredText (`.rst`)

#### Data Formats
- JSON (`.json`)
- YAML (`.yml`, `.yaml`)
- CSV (`.csv`)
- TSV (`.tsv`)

#### Configuration Files
- INI files (`.ini`, `.cfg`, `.conf`)
- TOML (`.toml`)
- Various config files (`Dockerfile`, `Makefile`, etc.)

## Usage

### Opening Files
1. **Navigate** to a text file in TFM
2. **Press Enter** to open in text viewer (automatic for text files)
3. **Press `v`** to explicitly open in text viewer
4. **Non-text files** will show file info instead

### Viewer Controls
| Key | Action |
|-----|--------|
| `q` or `ESC` | Exit viewer and return to TFM |
| `↑↓` or `j/k` | Scroll up/down |
| `←→` or `h/l` | Scroll left/right |
| `Page Up/Down` | Page scrolling |
| `Home/End` | Jump to start/end of file |
| `n` | Toggle line numbers on/off |
| `w` | Toggle line wrapping on/off |
| `s` | Toggle syntax highlighting on/off |

### Status Information
The viewer header shows:
- **File name** and path
- **Syntax highlighting status** (ON/OFF)
- **Line numbers status** (ON/OFF)  
- **Line wrapping status** (ON/OFF)
- **Available controls** for quick reference

## Installation & Dependencies

### Core Functionality
The text viewer works with **no external dependencies** - it uses Python's built-in libraries and the curses interface.

### Enhanced Syntax Highlighting
For **full syntax highlighting support**, install pygments:

```bash
pip install pygments
```

**Without pygments**: The viewer still works perfectly but displays files as plain text without syntax coloring.

**With pygments**: Full syntax highlighting for 20+ file formats with professional color schemes.

## Technical Details

### File Detection
The viewer uses a multi-step approach to identify text files:

1. **Extension matching** against known text file extensions
2. **Filename matching** for common files without extensions (README, Makefile, etc.)
3. **Content analysis** - reads first 1KB to detect binary vs text content
4. **Encoding detection** - tries UTF-8, Latin-1, and CP1252 encodings

### Performance
- **Lazy loading** - only loads visible content into memory
- **Efficient scrolling** - smooth navigation even for large files
- **Memory conscious** - handles files larger than available RAM
- **Fast startup** - minimal delay when opening files

### Error Handling
- **Graceful fallbacks** for unsupported files or encoding issues
- **Permission handling** - clear messages for access denied scenarios
- **Binary file detection** - prevents display of binary content as garbled text
- **Robust error recovery** - viewer errors don't crash TFM

## Integration with TFM

### Seamless Experience
- **Automatic detection** - Enter key opens text files in viewer, directories navigate normally
- **Consistent interface** - viewer uses same color scheme and key patterns as TFM
- **State preservation** - returns to exact same TFM state after viewing
- **Log integration** - viewer actions logged to TFM's log pane

### Configuration
The text viewer respects TFM's configuration system:
- **Key bindings** can be customized in `~/.tfm/config.py`
- **Color schemes** integrate with TFM's color system
- **Behavior settings** follow TFM's configuration patterns

## Examples

### Viewing Python Code
```python
# test_syntax.py - automatically highlighted
def hello_world():
    """A simple function"""
    message = "Hello, World!"
    print(f"Message: {message}")
    return True
```

### Viewing JSON Data
```json
{
  "name": "TFM Text Viewer",
  "features": ["syntax highlighting", "line numbers"],
  "supported": true
}
```

### Viewing Configuration Files
```ini
# config.ini - automatically detected and highlighted
[section]
key = value
debug = true
```

## Future Enhancements

Planned improvements for future versions:
- **Search functionality** within viewed files
- **Bookmarks** for large files
- **Split view** for comparing files
- **Custom color themes** for syntax highlighting
- **Plugin system** for additional file format support

## Troubleshooting

### Common Issues

**Q: Syntax highlighting not working**
A: Install pygments with `pip install pygments`

**Q: File shows as binary when it should be text**
A: Check file encoding - viewer supports UTF-8, Latin-1, and CP1252

**Q: Large files are slow to open**
A: This is expected - the viewer loads content progressively for better performance

**Q: Colors look wrong in terminal**
A: Ensure your terminal supports colors and try different TFM color schemes

### Getting Help
- Check TFM's main help with `?` key
- Review configuration in `~/.tfm/config.py`
- Check the log pane for error messages
- Verify file permissions and encoding

---

The TFM text viewer provides a powerful, integrated solution for viewing and examining text files without leaving your file management workflow. Whether you're browsing code, checking configuration files, or reading documentation, the viewer offers a smooth, efficient experience with professional syntax highlighting.