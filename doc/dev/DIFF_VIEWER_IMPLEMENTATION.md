# Text Diff Viewer Implementation

## Overview

The Text Diff Viewer is a side-by-side comparison tool integrated into TFM that displays differences between two text files. This document describes the technical implementation details.

## Architecture

### Core Components

#### 1. DiffViewer Class (`src/tfm_diff_viewer.py`)

The main viewer class that handles:
- File loading with encoding detection
- Diff computation using Python's `difflib`
- Side-by-side rendering
- User interaction and navigation

**Key Methods:**
- `__init__()`: Initialize viewer with two file paths
- `load_files()`: Load both files with encoding fallback
- `compute_diff()`: Generate line-by-line diff using SequenceMatcher
- `draw_header()`: Render header with file names
- `draw_content()`: Render side-by-side diff with color coding
- `draw_status_bar()`: Display statistics and position
- `handle_key()`: Process keyboard input
- `run()`: Main event loop

#### 2. Integration with FileManager (`src/tfm_main.py`)

**Method: `diff_selected_files()`**
- Collects selected files from both panes
- Validates exactly 2 files are selected
- Checks both are text files
- Launches the diff viewer

**Key Binding:**
- `=` (equals key) - Launches diff viewer when 2 files selected

### File Selection Logic

The diff viewer supports three selection patterns:

1. **Both files in left pane**: User selects 2 files in left pane
2. **Both files in right pane**: User selects 2 files in right pane  
3. **One file per pane**: User selects 1 file in left, 1 in right

Selection validation:
```python
# Collect from both panes
left_selected = [Path(f) for f in self.pane_manager.left_pane['selected_files']]
right_selected = [Path(f) for f in self.pane_manager.right_pane['selected_files']]
all_selected = left_selected + right_selected

# Filter to files only (not directories)
selected_files = [f for f in all_selected if f.exists() and f.is_file()]

# Validate exactly 2 files
if len(selected_files) != 2:
    # Show appropriate error message
    return
```

## Diff Algorithm

### SequenceMatcher

Uses Python's `difflib.SequenceMatcher` for line-by-line comparison:

```python
matcher = difflib.SequenceMatcher(None, file1_lines, file2_lines)

for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == 'equal':
        # Lines are identical
    elif tag == 'replace':
        # Lines are different
    elif tag == 'delete':
        # Lines only in file1
    elif tag == 'insert':
        # Lines only in file2
```

### Diff Line Format

Each diff line is stored as a tuple:
```python
(line1: str, line2: str, status: str)
```

Where status is one of:
- `'equal'`: Lines are identical
- `'replace'`: Lines are different
- `'delete'`: Line only in left file
- `'insert'`: Line only in right file

## Rendering

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Header (2 lines)                                            │
├──────────────────────────┬──────────────────────────────────┤
│ Left File Content        │ Right File Content               │
│ (scrollable)             │ (scrollable)                     │
├──────────────────────────┴──────────────────────────────────┤
│ Status Bar (1 line)                                         │
└─────────────────────────────────────────────────────────────┘
```

### Color Coding

Colors indicate change type:
- **White/Regular** (`COLOR_REGULAR_FILE`): Equal lines
- **Red** (`COLOR_ERROR`): Deleted lines (left only)
- **Blue/Cyan** (`COLOR_DIRECTORIES`): Inserted lines (right only)
- **Green/Yellow** (`COLOR_EXECUTABLES`): Modified lines (different)

### Scrolling

**Vertical Scrolling:**
- Synchronized across both panes
- Uses `scroll_offset` to track position
- Respects display height boundaries

**Horizontal Scrolling:**
- Synchronized across both panes
- Uses `horizontal_offset` for column position
- Handles wide characters correctly

## File Loading

### Encoding Detection

Multi-stage encoding detection:

1. **Binary Detection**: Check for null bytes in first 1024 bytes
2. **UTF-8**: Try UTF-8 encoding first (most common)
3. **Latin-1**: Fallback for Western European text
4. **CP1252**: Fallback for Windows text files
5. **Error Handling**: Display error message if all fail

```python
def _load_file(self, file_path: Path) -> List[str]:
    # Check for binary file
    chunk = file_path.read_bytes()
    if b'\x00' in chunk[:1024]:
        return ["[Binary file - cannot display as text]"]
    
    # Try encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            content = file_path.read_text(encoding=encoding)
            return content.splitlines()
        except UnicodeDecodeError:
            continue
```

### Error Handling

Specific exception handling for different error types:
- `FileNotFoundError`: File doesn't exist
- `PermissionError`: Access denied
- `OSError`: System-level errors
- `UnicodeDecodeError`: Encoding issues

## Navigation Controls

### Keyboard Bindings

| Key | Action |
|-----|--------|
| `↑` | Scroll up one line |
| `↓` | Scroll down one line |
| `←` | Scroll left one column |
| `→` | Scroll right one column |
| `Page Up` | Scroll up one page |
| `Page Down` | Scroll down one page |
| `Home` | Jump to beginning |
| `End` | Jump to end |
| `q` | Quit viewer |
| `Enter` | Quit viewer |
| `Escape` | Quit viewer |

### Event Handling

```python
def handle_key(self, event: KeyEvent) -> bool:
    """Returns True to continue, False to exit"""
    if event.key_code == KeyCode.DOWN:
        max_scroll = max(0, len(self.diff_lines) - display_height)
        if self.scroll_offset < max_scroll:
            self.scroll_offset += 1
    # ... other key handlers
    return True  # Continue running
```

## Performance Considerations

### Memory Usage

- Files are loaded entirely into memory
- Diff computation creates additional data structures
- Suitable for files up to ~10MB

### Optimization Opportunities

1. **Lazy Loading**: Load and diff on-demand for large files
2. **Chunked Rendering**: Only render visible lines
3. **Caching**: Cache diff results for repeated views
4. **Streaming**: Stream large files instead of loading entirely

## Testing

### Test Coverage

**Unit Tests** (`test/test_diff_viewer.py`):
- Viewer initialization
- Diff computation
- File loading with errors
- Keyboard navigation
- Binary file detection
- Complex diffs
- Identical files
- Completely different files

**Demo** (`demo/demo_diff_viewer.py`):
- Interactive demonstration
- Sample file generation
- Real-world usage example

### Test Execution

```bash
python3 test/test_diff_viewer.py
```

## Configuration

### Key Binding Configuration

In `src/_config.py`:
```python
KEY_BINDINGS = {
    'diff_files': {'keys': ['='], 'selection': 'required'},
}
```

The `'selection': 'required'` ensures the action only works when files are selected.

## Integration Points

### Dependencies

- `difflib`: Standard library for diff computation
- `tfm_path`: Path abstraction for local/remote files
- `tfm_colors`: Color scheme integration
- `tfm_wide_char_utils`: Wide character support
- `tfm_scrollbar`: Scrollbar rendering
- `ttk`: Terminal toolkit for rendering

### File Manager Integration

1. **Selection System**: Uses `pane_manager.left_pane['selected_files']` and `pane_manager.right_pane['selected_files']`
2. **Text Detection**: Uses `is_text_file()` from `tfm_text_viewer`
3. **Renderer**: Shares TTK renderer with main file manager
4. **Color Scheme**: Uses same color scheme as file manager

## Future Enhancements

### Planned Features

1. **Inline Diff View**: Single column with +/- markers
2. **Word-Level Diff**: Highlight changed words within lines
3. **Syntax Highlighting**: Apply syntax colors to diff
4. **Export to Patch**: Generate unified diff format
5. **Three-Way Merge**: Compare three files simultaneously
6. **Diff Statistics**: Show detailed change statistics
7. **Jump to Next/Previous Change**: Quick navigation between changes
8. **Ignore Whitespace**: Option to ignore whitespace differences

### Technical Improvements

1. **Streaming for Large Files**: Handle files >100MB
2. **Incremental Diff**: Compute diff incrementally
3. **Background Loading**: Load files in background thread
4. **Diff Caching**: Cache computed diffs
5. **Custom Diff Algorithm**: Implement patience diff or histogram diff

## Error Handling

### User-Facing Errors

Clear, actionable error messages:
- "No files selected. Select exactly 2 text files to compare."
- "Only 1 file selected. Select exactly 2 text files to compare."
- "Selected 3 files. Select exactly 2 text files to compare."
- "'filename' is not a text file"

### Internal Error Handling

Follows TFM exception handling policy:
- Specific exception types caught
- Informative error messages
- Graceful degradation
- No silent failures

## Code Quality

### Standards Compliance

- Follows TFM coding standards
- Type hints for public methods
- Comprehensive docstrings
- Specific exception handling
- Module-level imports only

### Documentation

- End-user documentation: `doc/DIFF_VIEWER_FEATURE.md`
- Developer documentation: This file
- Inline code comments for complex logic
- Test documentation in test files

## Troubleshooting

### Common Issues

**Issue**: Diff viewer doesn't launch
- **Cause**: Not exactly 2 files selected
- **Solution**: Check selection count in status bar

**Issue**: Binary file error
- **Cause**: File contains null bytes
- **Solution**: Use hex viewer or binary diff tool

**Issue**: Encoding errors
- **Cause**: Unsupported file encoding
- **Solution**: Convert file to UTF-8

**Issue**: Performance problems
- **Cause**: Very large files
- **Solution**: Use external diff tool for large files

## References

### Related Files

- `src/tfm_diff_viewer.py`: Main implementation
- `src/tfm_main.py`: Integration with file manager
- `src/_config.py`: Configuration and key bindings
- `test/test_diff_viewer.py`: Test suite
- `demo/demo_diff_viewer.py`: Interactive demo
- `doc/DIFF_VIEWER_FEATURE.md`: User documentation

### External Documentation

- Python difflib: https://docs.python.org/3/library/difflib.html
- TTK Renderer API: `ttk/renderer.py`
- TFM Path Abstraction: `src/tfm_path.py`
