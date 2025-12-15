# Text Viewer TAB Character Feature

## Overview

The TFM text viewer provides comprehensive TAB character handling with automatic expansion, dynamic width adjustment, and horizontal scrolling support. TABs are automatically expanded to spaces at appropriate column positions, and users can dynamically adjust the tab width without reloading files.

## Features

### Automatic TAB Expansion

- **TAB characters are expanded to spaces** when files are loaded
- Default tab width is **4 spaces** per TAB character
- TABs align to proper column positions (0, 4, 8, 12, 16, ...)
- Works with all file types and syntax highlighting

### Dynamic Tab Width Adjustment

- **Press 't' key** to cycle through tab widths: 2 → 4 → 8 → 2
- **Immediate feedback** - No file reload required
- **Status bar indicator** - Shows current tab width as `TAB:n`
- **Preserves original content** - TAB characters remain unchanged in the file

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

### Adjusting Tab Width

While viewing a file:

1. Press **'t'** key to cycle through tab widths
2. Watch the status bar indicator change: `TAB:2` → `TAB:4` → `TAB:8`
3. The display updates immediately with the new tab width
4. Continue pressing 't' to cycle through widths

### Supported File Types

TAB expansion works with all text file types:
- Source code files (Python, JavaScript, C, Java, etc.)
- Configuration files (YAML, JSON, INI, etc.)
- Makefiles and build scripts
- Log files
- Any text file containing TAB characters

## Column-Aware Alignment

TABs expand to the next tab stop based on the current column position:

```
Input:  "a\tb\tc"
Output: "a   b   c"  (tabs at columns 4, 8)

Input:  "ab\tcd\tef"
Output: "ab  cd  ef"  (tabs at columns 4, 8)

Input:  "abc\tdef"
Output: "abc def"    (tab at column 4)
```

### Tab Width Examples

**Tab width = 2:**
```
"a\tb"     → "a b"      (tab fills column 1 to reach column 2)
"abc\td"   → "abc d"    (tab fills column 3 to reach column 4)
```

**Tab width = 4:**
```
"a\tb"     → "a   b"    (tab fills columns 1-3 to reach column 4)
"abc\td"   → "abc d"    (tab fills column 3 to reach column 4)
"abcd\te"  → "abcd    e" (tab fills columns 4-7 to reach column 8)
```

**Tab width = 8:**
```
"a\tb"     → "a       b"  (tab fills columns 1-7 to reach column 8)
"abc\td"   → "abc     d"  (tab fills columns 3-7 to reach column 8)
```

## Technical Details

### Tab Width Configuration

The default tab width is 4 spaces, which can be dynamically changed:

- **2 spaces**: Compact display, good for deeply nested code
- **4 spaces**: Default, balanced readability
- **8 spaces**: Traditional tab width, maximum indentation visibility

### Column Position Calculation

TABs expand to reach the next tab stop:
- Tab stops are at positions: 0, 4, 8, 12, 16, ... (with tab_width=4)
- Spaces added = `tab_width - (current_column % tab_width)`
- Wide characters are properly accounted for in column calculations

### Tab Preservation and Re-expansion

**File Loading:**
1. Original content with tab characters is preserved in `original_lines`
2. Tabs are expanded to spaces based on current `tab_width` setting
3. Expanded content is stored in `lines` for display

**Tab Width Change:**
1. Tab width cycles to the next value (2 → 4 → 8 → 2)
2. Tabs are re-expanded from `original_lines` using the new width
3. Syntax highlighting is reapplied to the newly expanded content
4. Display updates immediately

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
- **Flexible tab width** - Adjust to your preference without reloading

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

Displays as (with tab_width=4):
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

- **t** : Cycle tab width (2 → 4 → 8 → 2)
- **← →** : Scroll horizontally through wide lines
- **↑ ↓** : Scroll vertically through file
- **PgUp/PgDn** : Page up/down
- **Home** : Jump to start of file
- **End** : Jump to end of file
- **q** or **Enter** : Exit viewer

## Use Cases

### Code Review
Quickly adjust tab width to match your preferred indentation style when reviewing code from different projects.

### Mixed Tab Styles
View files with different tab conventions by adjusting the display width to match the intended formatting.

### Accessibility
Users with visual preferences can adjust tab width for better readability.

### Deeply Nested Code
Use tab_width=2 for compact display of deeply nested code structures.

## Configuration

### Default Settings

- Tab width: 4 spaces (can be changed with 't' key)
- TAB expansion: Always enabled
- Horizontal scrolling: Available when lines exceed screen width
- Original content: Preserved for re-expansion

### Future Enhancements

Potential future improvements:
- Configurable default tab width in user settings
- Option to show TAB characters visually (→)
- Per-file-type tab width settings
- Remember tab width preference per file

## Testing

The TAB handling feature includes comprehensive tests:

```bash
# Run TAB handling tests
python3 test/test_text_viewer_tab_handling.py

# Run TAB width tests
python3 test/test_text_viewer_tab_width.py

# Run demo
python3 demo/demo_text_viewer_tab_handling.py
python3 demo/demo_text_viewer_tab_width.py
```

## Related Features

- **Horizontal Scrolling**: Enabled for all text files
- **Syntax Highlighting**: Works with expanded TABs (toggle with 's' key)
- **Wide Character Support**: TAB expansion accounts for display width
- **Line Wrapping**: Can be toggled with 'w' key (disables horizontal scroll)
- **Line Numbers**: Toggle with 'n' key

## Troubleshooting

### TABs Still Look Wrong

If TABs don't display correctly:
1. Verify the file actually contains TAB characters (not spaces)
2. Check if syntax highlighting is interfering (toggle with 's' key)
3. Try different tab width settings by pressing 't' key
4. Check the status bar to see current tab width

### Horizontal Scrolling Not Working

If horizontal scrolling doesn't work:
1. Ensure line wrapping is disabled (toggle with 'w' key)
2. Verify lines are actually wider than the screen
3. Check that TABs were properly expanded

### Tab Width Not Changing

If pressing 't' doesn't change tab width:
1. Verify you're in the text viewer (not file list)
2. Check the status bar for `TAB:n` indicator
3. Ensure the file contains TAB characters to see the effect

## Implementation Notes

For developers working on the text viewer:

- TAB expansion happens in `TextViewer.expand_tabs()` method
- Expansion occurs during file loading, before syntax highlighting
- Column positions use display width calculations for wide characters
- Horizontal scrolling uses the expanded text for rendering
- Original lines are preserved in `original_lines` for re-expansion
- Tab width changes trigger `refresh_tab_expansion()` method
- Syntax highlighting is reapplied after tab width changes

## Related Documentation

- Text Viewer System: `doc/dev/TEXT_VIEWER_SYSTEM.md`
- Wide Character Support: `doc/WIDE_CHARACTER_SUPPORT_FEATURE.md`
- TFM User Guide: `doc/TFM_USER_GUIDE.md`
