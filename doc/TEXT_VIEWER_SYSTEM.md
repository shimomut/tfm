# Text Viewer System Documentation

## Overview

TFM includes a comprehensive built-in text file viewer with syntax highlighting, search functionality, and remote file support. The viewer provides a clean, efficient way to view text files from both local and remote storage without leaving the file manager.

## Core Features

### ✅ Syntax Highlighting
- **Automatic detection** of file types based on extension and content
- **Pygments integration** for professional syntax highlighting
- **Graceful fallback** when pygments is not available
- **Support for 20+ file formats** including Python, JavaScript, JSON, Markdown, YAML, and more

### ✅ Navigation Controls
- **Vertical scrolling**: `↑↓` arrow keys
- **Horizontal scrolling**: `←→` arrow keys
- **Page navigation**: `Page Up/Down` for faster scrolling
- **Jump to start/end**: `Home/End` keys
- **Smooth scrolling** with proper boundary handling

### ✅ Display Options
- **Line numbers**: Toggle with `n` key (on by default)
- **Line wrapping**: Toggle with `w` key (off by default)
- **Syntax highlighting**: Toggle with `s` key (on by default if pygments available)
- **Status bar**: Shows current position, file size, format, and active options
- **Clean interface** with comprehensive information display

### ✅ Search Functionality
- **Incremental search**: Press `f` to search within the current file
- **Real-time highlighting**: Search matches highlighted as you type
- **Case-insensitive**: Finds matches regardless of case
- **Navigation**: Use `↑↓` to move between matches
- **Visual feedback**: Current match highlighted differently from other matches
- **Match counter**: Shows current match position and total matches

### ✅ Remote File Support
- **Unified file access** using tfm_path abstraction layer
- **Transparent handling** of different storage backends (local, S3, etc.)
- **Remote file detection** with scheme display in header
- **Enhanced error handling** for network and permission issues

## File Format Support

### Programming Languages
- Python (`.py`)
- JavaScript (`.js`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`, `.hpp`)
- Go (`.go`)
- Rust (`.rs`)
- PHP (`.php`)
- Ruby (`.rb`)
- Shell scripts (`.sh`, `.bash`, `.zsh`)

### Markup & Documentation
- HTML (`.html`)
- XML (`.xml`)
- Markdown (`.md`)
- reStructuredText (`.rst`)

### Data Formats
- JSON (`.json`)
- YAML (`.yml`, `.yaml`)
- CSV (`.csv`)
- TSV (`.tsv`)

### Configuration Files
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
| `↑↓` | Scroll up/down |
| `←→` | Scroll left/right |
| `Page Up/Down` | Page scrolling |
| `Home/End` | Jump to start/end of file |
| `n` | Toggle line numbers on/off |
| `w` | Toggle line wrapping on/off |
| `s` | Toggle syntax highlighting on/off |
| `f` or `F` | Enter search mode |

### Search Controls
| Key | Action |
|-----|--------|
| `f` or `F` | Enter search mode |
| `ESC` or `Enter` | Exit search mode |
| `Backspace` | Remove last search character |
| `↑` or `k` | Previous match |
| `↓` or `j` | Next match |
| Type characters | Add to search pattern (incremental) |

### Status Information
The viewer interface provides comprehensive status information:

**Header:**
- **File name** and path with storage scheme (e.g., "S3: filename.txt" for remote files)
- **Keyboard controls** for quick reference

**Status Bar (bottom):**
- **Current position**: Line number and scroll percentage
- **File information**: Size and format type
- **Horizontal scroll**: Column position when scrolled
- **Active options**: NUM (line numbers), WRAP (line wrapping), SYNTAX (highlighting)
- **Search status**: Current match position and total matches when searching

## Remote File Support

### Unified File Access
The text viewer uses tfm_path's abstraction layer to support both local and remote files:

- **Transparent handling** of different storage backends
- **Consistent API** regardless of file location
- **Automatic detection** of remote files based on URI scheme

### Supported Remote Storage
Currently supports any storage backend implemented in the tfm_path system:
- **Local files**: Standard filesystem access
- **S3**: AWS S3 buckets (`s3://bucket/key`)
- **Extensible**: New storage backends can be added by implementing `PathImpl`

### Remote File Detection
- Automatically detects remote files based on URI scheme
- Shows remote scheme in the header:
  - Local files: `File: example.txt`
  - S3 files: `S3: example.txt`
  - Other remote: `SCHEME: example.txt`

### Enhanced Error Handling
Specific exception handling for different error types:
- `FileNotFoundError` for missing files
- `PermissionError` for access denied
- `OSError` for general I/O errors
- Network-specific errors for remote files

## Technical Implementation

### File Loading Process

#### 1. Text Reading
Uses `file_path.read_text()` with multiple encoding attempts:
- UTF-8 (primary)
- Latin-1 (fallback)
- CP1252 (Windows fallback)

#### 2. Binary Detection
If text reading fails, attempts `file_path.read_bytes()`:
- Checks for null bytes to identify binary files
- Uses Latin-1 as final fallback for edge cases
- Works with both local and remote files

#### 3. Error Handling
```python
try:
    content = file_path.read_text(encoding='utf-8')
except FileNotFoundError:
    # File doesn't exist
except PermissionError:
    # Access denied
except OSError as e:
    # General I/O error (including network issues)
```

### Syntax Highlighting Implementation
The text viewer uses a **curses-native approach** to syntax highlighting:

1. **Pygments tokenization** - Uses pygments to parse and tokenize source code
2. **Token-to-color mapping** - Maps pygments token types to curses color pairs
3. **Line-by-line rendering** - Renders each line as a sequence of colored text segments
4. **No ANSI escape sequences** - Direct curses color application for proper terminal compatibility

### File Detection
Multi-step approach to identify text files:

1. **Extension matching** against known text file extensions
2. **Filename matching** for common files without extensions (README, Makefile, etc.)
3. **Content analysis** - reads first 1KB to detect binary vs text content
4. **Encoding detection** - tries UTF-8, Latin-1, and CP1252 encodings

### Performance Optimizations

#### Local Files
- **Efficient tokenization** - Pygments tokenization done once per file load
- **Optimized rendering** - Only visible content is rendered to screen
- **Memory conscious** - Handles large files appropriately
- **Fast scrolling** - Smooth navigation with proper color handling

#### Remote Files
- **Caching** - S3 implementation includes built-in caching for metadata and content
- **Network efficiency** - Uses tfm_path's optimized remote operations
- **Minimal data transfer** - Binary detection only reads first 1024 bytes
- **Streaming support** - Through tfm_path abstraction

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

### Remote File Support
Remote file support is provided through the tfm_path system:
- **S3 support**: Requires `boto3` library for AWS S3 access
- **Other backends**: May require additional libraries depending on implementation

## Usage Examples

### Viewing Local Files
```python
from tfm_path import Path
from tfm_text_viewer import view_text_file

# Local file
local_path = Path('/home/user/document.txt')
view_text_file(stdscr, local_path)
```

### Viewing Remote Files
```python
# S3 file
s3_path = Path('s3://my-bucket/document.txt')
view_text_file(stdscr, s3_path)
```

### Text File Detection
```python
from tfm_text_viewer import is_text_file

# Works for both local and remote files
if is_text_file(file_path):
    view_text_file(stdscr, file_path)
```

### Example File Types

#### Python Code
```python
# test_syntax.py - automatically highlighted
def hello_world():
    """A simple function"""
    message = "Hello, World!"
    print(f"Message: {message}")
    return True
```

#### JSON Data
```json
{
  "name": "TFM Text Viewer",
  "features": ["syntax highlighting", "line numbers", "remote support"],
  "supported": true
}
```

#### Configuration Files
```ini
# config.ini - automatically detected and highlighted
[section]
key = value
debug = true
```

## Error Scenarios

### Local File Errors
```
File not found: /path/to/missing.txt
Permission denied: /path/to/restricted.txt
[Binary file - cannot display as text]
```

### Remote File Errors
```
File not found: s3://bucket/missing.txt
Permission denied: s3://private-bucket/restricted.txt
Error reading file: Connection timeout
Network error: Unable to connect to S3
```

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

## Testing

### Comprehensive Test Coverage

#### Unit Tests
- `test/test_text_viewer.py` - Core text viewer functionality
- `test/test_text_viewer_remote.py` - Remote file support
- Syntax highlighting tests
- Search functionality tests
- Error handling verification

#### Integration Tests
- TFM integration testing
- Configuration system integration
- Key binding validation

#### Demo Programs
- `demo/demo_text_viewer.py` - Basic text viewer demonstration
- `demo/demo_text_viewer_remote.py` - Remote file support demonstration
- Interactive examples for all features

### Test Results
```
✅ Core functionality tests passed
✅ Remote file support tests passed
✅ Syntax highlighting tests passed
✅ Search functionality tests passed
✅ Error handling tests passed
✅ Integration tests passed
```

## Future Enhancements

### Planned Features
1. **Regular expression search** for advanced pattern matching
2. **Bookmarks** for large files
3. **Split view** for comparing files
4. **Custom color themes** for syntax highlighting
5. **Plugin system** for additional file format support
6. **Search history** and replace functionality
7. **Streaming support** for very large remote files
8. **Progress indicators** for slow remote file loading

### Extension Points
- New storage backends can be added to tfm_path
- TextViewer automatically supports new backends
- No changes required to TextViewer code for new storage types

## Troubleshooting

### Common Issues

#### Syntax Highlighting
**Q: Syntax highlighting not working**
A: Install pygments with `pip install pygments`

#### File Detection
**Q: File shows as binary when it should be text**
A: Check file encoding - viewer supports UTF-8, Latin-1, and CP1252

#### Performance
**Q: Large files are slow to open**
A: This is expected - the viewer loads content progressively for better performance

#### Display Issues
**Q: Colors look wrong in terminal**
A: Ensure your terminal supports colors and try different TFM color schemes

#### Remote Files
**Q: S3 files not accessible**
A: Ensure AWS credentials are configured and check network connectivity

**Q: Permission denied on remote files**
A: Verify read access to remote resources and check authentication

### Debug Information
Enable debug logging to see detailed error information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help
- Check TFM's main help with `?` key
- Review configuration in `~/.tfm/config.py`
- Check the log pane for error messages
- Verify file permissions and encoding

## Conclusion

The TFM Text Viewer System provides a powerful, integrated solution for viewing and examining text files from both local and remote storage without leaving your file management workflow. Whether you're browsing code, checking configuration files, reading documentation, or accessing files from cloud storage, the viewer offers a smooth, efficient experience with professional syntax highlighting and comprehensive search capabilities.

The system's architecture ensures consistent behavior across all storage types while maintaining high performance and reliability. The unified interface means users can work with local and remote files using the same familiar controls and features.