# Text Viewer Implementation

## Overview

The Text Viewer is a feature-rich component for viewing text files within TFM. It provides syntax highlighting, search functionality, horizontal scrolling, and efficient handling of large files.

## Architecture

### Core Class: TextViewer

The `TextViewer` class is the main component that manages:

- **File Loading**: Reading and caching file content
- **Display Rendering**: Rendering visible lines with syntax highlighting
- **Navigation**: Scrolling, jumping, and searching
- **Input Handling**: Keyboard and mouse input processing

### Key Features

**Syntax Highlighting**
- Automatic language detection based on file extension
- Support for multiple programming languages
- Configurable color schemes
- Fallback to plain text for unknown types

**Large File Handling**
- Efficient line-based loading
- Viewport-based rendering (only visible lines)
- Memory-efficient caching
- Smooth scrolling for files with millions of lines

**Search Functionality**
- Incremental search (isearch)
- Case-sensitive and case-insensitive modes
- Forward and backward search
- Highlight all matches
- Jump to next/previous match

**Horizontal Scrolling**
- Support for long lines
- Smooth horizontal navigation
- Automatic scroll to show search matches
- Configurable tab width

## Implementation Details

### File Loading Strategy

```python
# Pseudo-code for file loading
def load_file(path):
    # Read file in chunks
    with open(path, 'r') as f:
        lines = []
        for line in f:
            lines.append(line.rstrip('\n'))
            
    # Cache lines for fast access
    self.lines = lines
    self.total_lines = len(lines)
```

### Viewport Rendering

The viewer only renders visible lines:

1. **Calculate Viewport**: Determine which lines are visible
2. **Render Lines**: Render only those lines
3. **Apply Highlighting**: Apply syntax highlighting to visible text
4. **Handle Scrolling**: Update viewport on scroll

### Syntax Highlighting Integration

The viewer integrates with Python's `pygments` library:

- **Lexer Selection**: Choose lexer based on file extension
- **Token Generation**: Generate tokens for visible lines
- **Color Mapping**: Map tokens to TFM color attributes
- **Fallback**: Use plain text if pygments unavailable

### Search Implementation

**Incremental Search (isearch)**:
- Search as user types
- Highlight current match
- Show match count
- Navigate between matches

**Search Algorithm**:
```python
# Pseudo-code for search
def search(pattern, start_line):
    for line_num in range(start_line, total_lines):
        line = self.lines[line_num]
        if pattern in line:
            return (line_num, line.index(pattern))
    return None
```

## Key Methods

### Navigation Methods

- `scroll_up()`: Scroll up one line
- `scroll_down()`: Scroll down one line
- `page_up()`: Scroll up one page
- `page_down()`: Scroll down one page
- `goto_line(n)`: Jump to specific line
- `goto_top()`: Jump to beginning
- `goto_bottom()`: Jump to end

### Search Methods

- `start_search()`: Begin incremental search
- `search_next()`: Find next match
- `search_previous()`: Find previous match
- `cancel_search()`: Exit search mode

### Display Methods

- `render()`: Render current viewport
- `refresh()`: Force full redraw
- `update_status()`: Update status line

## Integration Points

### File Manager Integration

The Text Viewer integrates with the main file manager:

- **Launch**: Opened via F3 key or menu
- **File Selection**: Uses current file selection
- **Return**: Returns to file manager on exit
- **State**: Remembers last position per file

### Configuration System

Respects configuration options:

- `text_viewer.syntax_highlighting`: Enable/disable highlighting
- `text_viewer.tab_width`: Tab character width
- `text_viewer.wrap_lines`: Line wrapping (future)
- `color_scheme`: Color scheme for highlighting

### Remote File Support

Supports viewing remote files:

- **S3 Files**: Download and cache S3 objects
- **Archive Files**: Extract and view archive contents
- **Temporary Files**: Clean up after viewing

## Performance Considerations

### Memory Management

- **Line Caching**: Cache only loaded lines
- **Viewport Limiting**: Render only visible content
- **Lazy Loading**: Load file on demand
- **Cleanup**: Release resources on close

### Rendering Optimization

- **Dirty Region Tracking**: Only redraw changed areas
- **Batch Updates**: Group multiple updates
- **Efficient Highlighting**: Cache highlighted tokens
- **Minimal Redraws**: Avoid unnecessary screen updates

## Error Handling

The viewer handles various error conditions:

- **File Not Found**: Display error message
- **Permission Denied**: Show permission error
- **Encoding Errors**: Try alternative encodings
- **Large Files**: Warn about memory usage
- **Binary Files**: Detect and refuse binary files

## Key Bindings

Default key bindings for text viewer:

- `Up/Down`: Scroll one line
- `PgUp/PgDn`: Scroll one page
- `Home/End`: Jump to top/bottom
- `Left/Right`: Horizontal scroll
- `/`: Start forward search
- `?`: Start backward search
- `n`: Next search match
- `N`: Previous search match
- `q/Esc`: Exit viewer

## Testing Considerations

Key areas for testing:

- **Large Files**: Files with millions of lines
- **Long Lines**: Lines with thousands of characters
- **Various Encodings**: UTF-8, Latin-1, etc.
- **Syntax Highlighting**: Different file types
- **Search Performance**: Search in large files
- **Memory Usage**: No memory leaks
- **Edge Cases**: Empty files, single-line files

## Related Documentation

- [Text Viewer Feature](../TEXT_VIEWER_TAB_FEATURE.md) - User documentation
- [View File Behavior Feature](../VIEW_FILE_BEHAVIOR_FEATURE.md) - File viewing behavior
- [Color Schemes Implementation](COLOR_SCHEMES_IMPLEMENTATION.md) - Color system
- [Dialog System](DIALOG_SYSTEM.md) - Dialog framework

## Future Enhancements

Potential improvements:

- **Line Wrapping**: Soft wrap long lines
- **Binary Viewer**: Hex view for binary files
- **Diff Mode**: Side-by-side diff view
- **Bookmarks**: Mark and jump to bookmarks
- **Regex Search**: Regular expression search
- **Multi-file Tabs**: View multiple files simultaneously
- **Edit Mode**: Basic text editing capabilities
