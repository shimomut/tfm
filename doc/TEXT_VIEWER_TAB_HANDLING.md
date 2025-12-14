# Text Viewer TAB Character Handling and Horizontal Scrolling

## Overview

The TFM text viewer now properly handles TAB characters and horizontal scrolling. TABs are automatically expanded to spaces at appropriate column positions, and horizontal scrolling works correctly for all file types, ensuring accurate display at any scroll position.

## Features

### Automatic TAB Expansion

- **TAB characters are expanded to spaces** when files are loaded
- Default tab width is **4 spaces** per TAB character
- TABs align to proper column positions (0, 4, 8, 12, 16, ...)
- Works with all file types and syntax highlighting

### Column-Aware Alignment

TABs expand to the next tab stop based on the current column position:

```
Input:  "a\tb\tc"
Output: "a   b   c"  (tabs at columns 4, 8)

Input:  "ab\tcd\tef"
Output: "ab  cd  ef"  (tabs at columns 4, 8)

Input:  "abc\tdef"
Output: "abc def"    (tab at column 4)
```

### Horizontal Scrolling Support

- **Horizontal scrolling works correctly** with expanded TABs
- Use arrow keys (← →) to scroll horizontally through wide lines
- No display artifacts or alignment issues
- TAB-indented code displays properly at any scroll position

## Usage

### Viewing Files with TABs

Simply open any text file containing TAB characters:

1. Navigate to a file in TFM
2. Press **Enter** or **F3** to view the file
3. TABs are automatically expanded to spaces
4. Use **← →** arrow keys to scroll horizontally if needed

### Supported File Types

TAB expansion works with all text file types:
- Source code files (Python, JavaScript, C, Java, etc.)
- Configuration files (YAML, JSON, INI, etc.)
- Makefiles and build scripts
- Log files
- Any text file containing TAB characters

## Technical Details

### TAB Width Configuration

The default tab width is 4 spaces, which can be configured in the `TextViewer` class:

```python
viewer.tab_width = 4  # Default
viewer.tab_width = 8  # Alternative common setting
```

### Column Position Calculation

TABs expand to reach the next tab stop:
- Tab stops are at positions: 0, 4, 8, 12, 16, ... (with tab_width=4)
- Spaces added = `tab_width - (current_column % tab_width)`
- Wide characters are properly accounted for in column calculations

### Horizontal Scrolling Implementation

The horizontal scrolling logic properly handles:
- **Character-level positioning**: Uses character index tracking instead of string search
- **Segment-based rendering**: Works with syntax-highlighted text segments
- **Wide character support**: Accounts for display width when calculating positions
- **Accurate offset calculation**: Correctly skips characters based on display columns

Key fix: Changed from `text.index(char)` to `char_index` tracking to avoid finding wrong character positions in text with repeated characters.

### Processing Order

1. File is loaded and split into lines
2. Each line has TABs expanded to spaces
3. Syntax highlighting is applied to expanded content
4. Display rendering uses the expanded text with proper horizontal offset

## Benefits

### Improved Display Quality

- **No display artifacts** when scrolling horizontally
- **Consistent alignment** across all viewing positions
- **Proper indentation** for code and structured text

### Better User Experience

- **Smooth scrolling** through TAB-indented content
- **Readable code** with proper indentation
- **No confusion** from TAB character display issues

### Wide Character Support

- TAB expansion accounts for wide characters (CJK, emoji, etc.)
- Column positions calculated using display width
- Proper alignment even with mixed character widths

## Examples

### Python Code with TABs

```python
def example():
	if True:
		print("Indented with TABs")
		for i in range(10):
			print(i)
```

Displays as:
```python
def example():
    if True:
        print("Indented with TABs")
        for i in range(10):
            print(i)
```

### Makefile with TABs

```makefile
all: build test

build:
	gcc -o program main.c
	
test:
	./program --test
```

Displays with proper TAB alignment at column positions.

### TSV Data with TABs

```
Name	Age	City	Country
Alice	30	NYC	USA
Bob	25	London	UK
```

Displays with columns properly aligned.

## Keyboard Controls

When viewing files with TABs:

- **← →** : Scroll horizontally through wide lines
- **↑ ↓** : Scroll vertically through file
- **PgUp/PgDn** : Page up/down
- **Home** : Jump to start of file
- **End** : Jump to end of file
- **q** or **Enter** : Exit viewer

## Configuration

### Default Settings

- Tab width: 4 spaces
- TAB expansion: Always enabled
- Horizontal scrolling: Available when lines exceed screen width

### Future Enhancements

Potential future improvements:
- Configurable tab width in user settings
- Option to show TAB characters visually (→)
- Per-file-type tab width settings

## Testing

The TAB handling feature includes comprehensive tests:

```bash
# Run TAB handling tests
python3 test/test_text_viewer_tab_handling.py

# Run demo
python3 demo/demo_text_viewer_tab_handling.py
```

## Related Features

- **Horizontal Scrolling**: Enabled for all text files
- **Syntax Highlighting**: Works with expanded TABs
- **Wide Character Support**: TAB expansion accounts for display width
- **Line Wrapping**: Can be toggled with 'w' key (disables horizontal scroll)

## Troubleshooting

### TABs Still Look Wrong

If TABs don't display correctly:
1. Verify the file actually contains TAB characters (not spaces)
2. Check if syntax highlighting is interfering (toggle with 's' key)
3. Try different tab width settings if needed

### Horizontal Scrolling Not Working

If horizontal scrolling doesn't work:
1. Ensure line wrapping is disabled (toggle with 'w' key)
2. Verify lines are actually wider than the screen
3. Check that TABs were properly expanded

## Implementation Notes

For developers working on the text viewer:

- TAB expansion happens in `TextViewer.expand_tabs()` method
- Expansion occurs during file loading, before syntax highlighting
- Column positions use display width calculations for wide characters
- Horizontal scrolling uses the expanded text for rendering
