# TextViewer Background Color Fix

## Problem Description

The TextViewer component was not properly filling empty areas with the color scheme's background color. Instead, it was using `clrtoeol()` which clears to the end of line with the default terminal background color, causing visual inconsistency with the selected color scheme.

### Symptoms
- Empty areas in text viewer showed default terminal background
- Inconsistent appearance with the rest of the TFM interface
- Color scheme background not applied to text content areas
- Visual "bleeding" of terminal background through the interface

## Root Cause

The issue was in the `draw_content()` method of the `TextViewer` class:

```python
# BEFORE (problematic code)
try:
    self.stdscr.move(y_pos, start_x)
    self.stdscr.clrtoeol()  # This clears with default terminal background
except curses.error:
    pass
```

The `clrtoeol()` function clears to the end of the line using the terminal's default background color, not the color scheme's background color.

## Solution

Replace `clrtoeol()` with explicit background color filling using `addstr()` with the proper color scheme background:

```python
# AFTER (fixed code)
# Get background color for filling empty areas
bg_color_pair = get_background_color_pair()

# Fill the entire line with background color instead of using clrtoeol()
try:
    self.stdscr.addstr(y_pos, start_x, ' ' * (display_width - 1), bg_color_pair)
    self.stdscr.move(y_pos, start_x)
except curses.error:
    pass
```

## Implementation Details

### Changes Made

1. **Import background color function**: Added usage of `get_background_color_pair()` from `tfm_colors.py`

2. **Replace clrtoeol() calls**: Changed from clearing with default background to filling with color scheme background

3. **Consistent color application**: Ensures all empty areas use the same background color as the rest of the interface

### Code Changes

**File**: `src/tfm_text_viewer.py`

**Method**: `draw_content()`

**Before**:
```python
# Move to start of line and clear to end of line (more efficient)
try:
    self.stdscr.move(y_pos, start_x)
    self.stdscr.clrtoeol()
except curses.error:
    pass
```

**After**:
```python
# Get background color for filling empty areas
bg_color_pair = get_background_color_pair()

# Fill the entire line with background color instead of using clrtoeol()
try:
    self.stdscr.addstr(y_pos, start_x, ' ' * (display_width - 1), bg_color_pair)
    self.stdscr.move(y_pos, start_x)
except curses.error:
    pass
```

## Benefits

1. **Visual Consistency**: Text viewer now matches the color scheme background
2. **Professional Appearance**: No more terminal background bleeding through
3. **Better Integration**: Consistent with other TFM components
4. **Color Scheme Support**: Works with both dark and light color schemes

## Testing

### Test File
- `test/test_text_viewer_background_fix.py` - Automated test for the fix

### Demo File  
- `demo/demo_text_viewer_background_fix.py` - Interactive demonstration

### Test Cases Covered
1. Normal text files with various content lengths
2. Empty files
3. Files with syntax highlighting
4. Different scroll positions (vertical and horizontal)
5. Line numbers enabled/disabled
6. Both dark and light color schemes

## Usage

The fix is automatically applied when using the TextViewer. No configuration changes are needed.

### Opening Text Files
```python
from tfm_text_viewer import view_text_file

# The background fix is automatically applied
success = view_text_file(stdscr, file_path)
```

### Direct TextViewer Usage
```python
from tfm_text_viewer import TextViewer

viewer = TextViewer(stdscr, file_path)
viewer.run()  # Background fix is automatically applied
```

## Related Components

This fix works in conjunction with:
- `tfm_colors.py` - Provides `get_background_color_pair()` function
- Color scheme system - Ensures consistent background colors
- Main TFM interface - Maintains visual consistency

## Backward Compatibility

This fix maintains full backward compatibility:
- No API changes
- No configuration changes required
- Works with existing color schemes
- Graceful fallback if color functions unavailable

## Performance Impact

Minimal performance impact:
- Replaces one `clrtoeol()` call with one `addstr()` call per line
- No additional memory allocation
- Same number of screen operations
- Slightly more explicit about color usage (actually beneficial)

## Future Considerations

This fix establishes a pattern for proper background color handling that can be applied to other components if needed. The approach of using `get_background_color_pair()` with explicit `addstr()` calls should be preferred over `clrtoeol()` when background color consistency is important.