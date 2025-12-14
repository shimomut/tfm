# Text Viewer Tab Width Feature

## Overview

The text viewer now supports dynamic tab width adjustment, allowing users to change how tab characters are displayed without reloading the file.

## Usage

### Key Binding

Press `t` to cycle through tab widths:
- 2 spaces
- 4 spaces (default)
- 8 spaces

### Status Bar Indicator

The current tab width is displayed in the status bar as `TAB:n` where `n` is the number of spaces per tab.

Example: `TAB:4` indicates tabs are displayed as 4 spaces.

## How It Works

### Tab Preservation

When a file is loaded:
1. Original content with tab characters is preserved in `original_lines`
2. Tabs are expanded to spaces based on current `tab_width` setting
3. Expanded content is stored in `lines` for display

### Dynamic Tab Width Change

When the user presses `t`:
1. Tab width cycles to the next value (2 → 4 → 8 → 2)
2. Tabs are re-expanded from `original_lines` using the new width
3. Syntax highlighting is reapplied to the newly expanded content
4. Display updates immediately

### Tab Expansion Algorithm

Tabs are expanded respecting column positions:
- Each tab advances to the next tab stop
- Tab stops occur at multiples of `tab_width`
- Wide characters are properly accounted for in column calculations

Example with `tab_width=4`:
```
"a\tb"     → "a   b"    (tab fills columns 1-3 to reach column 4)
"ab\tc"    → "ab  c"    (tab fills columns 2-3 to reach column 4)
"abc\td"   → "abc d"    (tab fills column 3 to reach column 4)
"abcd\te"  → "abcd    e" (tab fills columns 4-7 to reach column 8)
```

## Implementation Details

### Key Components

1. **`original_lines`** - List of strings with tab characters preserved
2. **`lines`** - List of strings with tabs expanded to spaces
3. **`tab_width`** - Current tab width setting (2, 4, or 8)
4. **`expand_tabs(line)`** - Expands tabs in a single line
5. **`refresh_tab_expansion()`** - Re-expands all lines with current tab width

### Code Flow

```
File Load:
  read_text() → original_lines (with tabs)
  → expand_tabs() → lines (with spaces)
  → apply_syntax_highlighting()

Tab Width Change:
  Press 't' → cycle tab_width
  → refresh_tab_expansion()
    → expand_tabs() on original_lines
    → apply_syntax_highlighting()
  → redraw display
```

## Benefits

1. **Immediate feedback** - No file reload required
2. **Preserves original content** - Tab characters remain unchanged in the file
3. **Works with syntax highlighting** - Highlighting is reapplied after tab expansion
4. **Respects column alignment** - Tabs align to proper tab stops
5. **Handles wide characters** - Correctly accounts for multi-column characters

## Use Cases

### Code Review
Quickly adjust tab width to match your preferred indentation style when reviewing code from different projects.

### Mixed Tab Styles
View files with different tab conventions by adjusting the display width to match the intended formatting.

### Accessibility
Users with visual preferences can adjust tab width for better readability.

## Technical Notes

### Why Preserve Original Lines?

The original implementation expanded tabs during file load, making it impossible to change tab width without reloading the file. By preserving the original content with tabs, we can re-expand them with different widths on demand.

### Syntax Highlighting Integration

When tab width changes:
1. Tabs are re-expanded from original content
2. Expanded content is joined into a single string
3. Pygments lexer tokenizes the expanded content
4. Tokens are converted to highlighted line segments

This ensures syntax highlighting remains accurate after tab width changes.

### Performance Considerations

Tab re-expansion is fast even for large files because:
- Only the tab expansion and syntax highlighting steps are repeated
- File I/O is not involved
- The operation completes in milliseconds for typical files

## Related Features

- **Line Numbers** (`n` key) - Toggle line number display
- **Line Wrapping** (`w` key) - Toggle line wrapping
- **Syntax Highlighting** (`s` key) - Toggle syntax highlighting

All these features work together seamlessly with tab width adjustment.
