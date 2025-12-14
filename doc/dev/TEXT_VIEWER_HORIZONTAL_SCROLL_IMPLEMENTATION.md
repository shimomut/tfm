# Text Viewer Horizontal Scrolling Implementation

## Overview

This document describes the implementation of TAB character handling and horizontal scrolling in the TFM text viewer, including the bug fix that resolved incorrect character positioning.

## Problem Statement

The text viewer had two related issues:
1. **TAB characters were not expanded**, causing display issues with horizontal scrolling
2. **Horizontal scrolling had a positioning bug** that caused incorrect text display at certain offsets

## Solution

### 1. TAB Expansion

Added automatic TAB expansion during file loading:

```python
def expand_tabs(self, line: str) -> str:
    """Expand tab characters to spaces, respecting column positions."""
    if '\t' not in line:
        return line
    
    result = []
    col = 0
    
    for char in line:
        if char == '\t':
            # Calculate spaces needed to reach next tab stop
            spaces_to_add = self.tab_width - (col % self.tab_width)
            result.append(' ' * spaces_to_add)
            col += spaces_to_add
        else:
            result.append(char)
            col += get_display_width(char)
    
    return ''.join(result)
```

**Key features:**
- Column-aware expansion (tabs align to 0, 4, 8, 12, ... with tab_width=4)
- Wide character support (uses display width for column calculation)
- Applied before syntax highlighting

### 2. Horizontal Scrolling Bug Fix

**The Bug:**

The original code used `text.index(char)` to find the position to start displaying text:

```python
# BUGGY CODE
for char in text:
    char_width = get_display_width(char)
    if skip_width + char_width > start_offset_cols:
        visible_text = text[text.index(char):]  # BUG: finds FIRST occurrence
        break
    skip_width += char_width
```

**Problem:** `text.index(char)` finds the FIRST occurrence of the character in the string, not the current position. This caused incorrect positioning when:
- Text contained repeated characters (like "0123456789" repeated)
- Horizontal offset pointed to a character that appeared earlier in the string

**The Fix:**

Track the character index explicitly:

```python
# FIXED CODE
char_index = 0
for char in text:
    char_width = get_display_width(char)
    if skip_width + char_width > start_offset_cols:
        visible_text = text[char_index:]  # CORRECT: uses actual position
        break
    skip_width += char_width
    char_index += 1
```

**Result:** Horizontal scrolling now works correctly at all offsets, regardless of text content.

## Implementation Details

### File Loading Process

1. Read file content with encoding detection
2. Split into lines
3. **Expand TABs in each line** (new step)
4. Apply syntax highlighting to expanded content
5. Store both plain lines and highlighted lines

### Rendering Process

1. Calculate display dimensions and available width
2. Get lines to display (with wrapping if enabled)
3. For each visible line:
   - Draw line number (if enabled)
   - **Apply horizontal scrolling to content**
   - Draw text segments with proper colors
   - Handle search highlighting

### Horizontal Scrolling Algorithm

For each text segment in a line:

1. **Check if segment is before offset:**
   ```python
   if current_display_col + text_display_width <= horizontal_offset:
       current_display_col += text_display_width
       continue  # Skip entire segment
   ```

2. **Calculate visible portion:**
   ```python
   start_offset_cols = max(0, horizontal_offset - current_display_col)
   ```

3. **Find starting character (if partial segment):**
   ```python
   if start_offset_cols > 0:
       skip_width = 0
       char_index = 0
       for char in text:
           char_width = get_display_width(char)
           if skip_width + char_width > start_offset_cols:
               visible_text = text[char_index:]  # Use char_index, not text.index()
               break
           skip_width += char_width
           char_index += 1
   ```

4. **Truncate to fit available width:**
   ```python
   remaining_width = content_width - (display_x - x_pos)
   if visible_text_width > remaining_width:
       visible_text = truncate_to_width(visible_text, remaining_width, "")
   ```

5. **Draw the visible text**

## Testing

### TAB Expansion Tests

Tests verify:
- TABs are completely removed from text
- Column alignment is correct (0, 4, 8, 12, ...)
- Different tab widths work correctly (2, 4, 8)
- Wide characters are handled properly

### Horizontal Scrolling Tests

Tests verify:
- Scrolling works at various offsets (0, 5, 10, 20, 30, 40)
- Text is correctly positioned at each offset
- Works with and without syntax highlighting
- Handles repeated characters correctly

## Performance Considerations

### TAB Expansion
- **When:** During file loading (one-time cost)
- **Impact:** Minimal - only processes lines containing TABs
- **Optimization:** Early return if no TABs in line

### Horizontal Scrolling
- **When:** Every frame when scrolling
- **Impact:** Low - only processes visible lines
- **Optimization:** 
  - Skips entire segments before offset
  - Stops processing when line is full
  - Uses display width calculations efficiently

## Edge Cases Handled

1. **Empty lines:** Handled gracefully
2. **Lines with only TABs:** Expanded to spaces
3. **Mixed TABs and wide characters:** Column calculation accounts for both
4. **Very long lines:** Truncated to fit display width
5. **Repeated characters:** Fixed by using char_index instead of text.index()
6. **Syntax highlighting segments:** Works with multiple colored segments per line

## Future Enhancements

Potential improvements:
1. **Configurable tab width** in user settings
2. **Visual TAB indicators** (show → character)
3. **Per-file-type tab width** settings
4. **Smart tab detection** (detect if file uses tabs or spaces)
5. **Tab/space conversion** option

## Related Components

- `tfm_wide_char_utils.py`: Display width calculations
- `tfm_colors.py`: Color definitions for syntax highlighting
- `tfm_scrollbar.py`: Vertical scrollbar rendering
- Syntax highlighting: Pygments integration

## Code Locations

- TAB expansion: `TextViewer.expand_tabs()` method
- Horizontal scrolling: `TextViewer.draw_content()` method
- File loading: `TextViewer.load_file()` method
- Tests: `test/test_text_viewer_tab_handling.py`, `test/test_horizontal_scroll_behavior.py`

## Debugging Tips

To debug horizontal scrolling issues:

1. **Check highlighted_lines structure:**
   ```python
   print(f"Line segments: {len(highlighted_line)}")
   for text, color in highlighted_line:
       print(f"  Segment: '{text[:30]}...' (width: {get_display_width(text)})")
   ```

2. **Track column positions:**
   ```python
   print(f"current_display_col: {current_display_col}")
   print(f"horizontal_offset: {self.horizontal_offset}")
   print(f"start_offset_cols: {start_offset_cols}")
   ```

3. **Verify character indexing:**
   ```python
   print(f"char_index: {char_index}, char: '{char}'")
   print(f"visible_text: '{visible_text[:40]}'")
   ```

## References

- Wide character handling: Unicode East Asian Width specification
- TAB expansion: POSIX terminal behavior
- Display width: wcwidth library concepts
