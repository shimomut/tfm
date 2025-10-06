# Narrow Terminal Dialog Rendering Fix

## Overview

This document describes the fix for dialog rendering issues when the terminal becomes horizontally narrow. The issue affected multiple dialog components:

- BatchRenameDialog
- DrivesDialog  
- ListDialog
- JumpDialog
- SearchDialog

## Problem Description

### Root Cause

The dialogs had width calculation issues that caused rendering problems in narrow terminals:

1. **Width Calculation**: Dialog width was calculated as `max(min_width, int(terminal_width * width_ratio))`, which could result in dialogs wider than the terminal when `min_width` exceeded the terminal width.

2. **Centering Issues**: The centering calculation `start_x = (terminal_width - dialog_width) // 2` could result in negative values when the dialog was wider than the terminal.

3. **Boundary Violations**: Drawing operations attempted to draw outside the terminal bounds, causing rendering failures.

### Symptoms

- Dialogs would stop rendering correctly in narrow terminals (< 40 characters wide)
- Dialog borders and content could extend beyond screen boundaries
- Text and UI elements would disappear or be positioned incorrectly
- In extreme cases, dialogs would fail to render entirely

## Solution

### 1. Safe Dialog Dimension Calculation

Updated the width calculation logic to ensure dialogs never exceed terminal bounds:

```python
# Before (problematic)
dialog_width = max(min_width, int(width * width_ratio))
dialog_height = max(min_height, int(height * height_ratio))
start_y = (height - dialog_height) // 2
start_x = (width - dialog_width) // 2

# After (fixed)
desired_width = int(width * width_ratio)
desired_height = int(height * height_ratio)

# Apply minimum constraints, but never exceed terminal size
dialog_width = max(min_width, desired_width)
dialog_width = min(dialog_width, width)  # Never exceed terminal width

dialog_height = max(min_height, desired_height)
dialog_height = min(dialog_height, height)  # Never exceed terminal height

# Calculate safe centering
start_y = max(0, (height - dialog_height) // 2)
start_x = max(0, (width - dialog_width) // 2)
```

### 2. Safe Border Drawing

Enhanced border drawing to handle truncation when lines would exceed terminal width:

```python
# Top border with safe truncation
if start_y >= 0 and start_y < height:
    top_line = "┌" + "─" * max(0, dialog_width - 2) + "┐"
    # Truncate if line would exceed terminal width
    if start_x + len(top_line) > width:
        top_line = top_line[:width - start_x]
    if top_line:
        safe_addstr_func(start_y, start_x, top_line, border_color)
```

### 3. Safe Title Positioning

Improved title positioning with truncation support:

```python
# Draw title with safe positioning
if title and start_y >= 0 and start_y < height:
    title_text = f" {title} "
    title_width = get_width(title_text)
    
    # Truncate title if it's too wide for the dialog
    if title_width > dialog_width:
        title_text = truncate_text(title_text, dialog_width - 2, "...")
        title_width = get_width(title_text)
    
    title_x = start_x + (dialog_width - title_width) // 2
    # Ensure title fits within terminal bounds
    if title_x >= 0 and title_x < width and title_x + title_width <= width:
        safe_addstr_func(start_y, title_x, title_text, border_color)
```

### 4. Enhanced Boundary Checking

Added comprehensive boundary checking for all drawing operations:

- Y position bounds: `y >= 0 and y < height`
- X position bounds: `x >= 0 and x < width`
- Text length bounds: `x + len(text) <= width`

## Files Modified

### Core Dialog Components

1. **src/tfm_base_list_dialog.py**
   - Fixed `draw_dialog_frame()` method
   - Enhanced boundary checking for all drawing operations
   - Improved title positioning and truncation

2. **src/tfm_batch_rename_dialog.py**
   - Fixed dialog dimension calculation in `draw()` method
   - Enhanced border drawing with safe truncation
   - Improved help text positioning for narrow terminals

### Dialog Inheritance

The fix in `BaseListDialog` automatically benefits all dialogs that inherit from it:
- `ListDialog`
- `DrivesDialog` 
- `JumpDialog`
- `SearchDialog`

## Testing

### Test Coverage

Created comprehensive tests to verify the fix:

1. **test/test_dialog_width_calculation_fix.py**
   - Tests safe dialog dimension calculation logic
   - Verifies width never exceeds terminal bounds
   - Tests text truncation and border line creation
   - Tests title positioning logic

2. **test/test_all_dialogs_narrow_terminal_fix.py**
   - Tests all dialog types in narrow terminals
   - Verifies drawing operations stay within bounds
   - Tests extreme terminal sizes

### Test Cases

The fix handles various terminal sizes:
- Extremely narrow: 10-20 characters wide
- Narrow: 25-35 characters wide  
- Small: 40-50 characters wide
- Normal: 80+ characters wide

## Backward Compatibility

The fix maintains full backward compatibility:
- No changes to public APIs
- No changes to dialog behavior in normal-sized terminals
- All existing functionality preserved
- Existing tests continue to pass

## Performance Impact

The fix has minimal performance impact:
- Additional boundary checks are simple comparisons
- Text truncation only occurs when necessary
- No significant computational overhead

## Benefits

1. **Improved Usability**: Dialogs now work correctly in narrow terminals
2. **Better Responsive Design**: Dialogs adapt gracefully to terminal size
3. **Enhanced Robustness**: Prevents rendering failures and crashes
4. **Consistent Experience**: All dialogs behave consistently across terminal sizes

## Configuration

The fix respects existing configuration parameters:
- `LIST_DIALOG_WIDTH_RATIO`: Preferred width as ratio of terminal width
- `LIST_DIALOG_HEIGHT_RATIO`: Preferred height as ratio of terminal height  
- `LIST_DIALOG_MIN_WIDTH`: Minimum desired width (now capped at terminal width)
- `LIST_DIALOG_MIN_HEIGHT`: Minimum desired height (now capped at terminal height)

## Future Considerations

1. **Responsive Content**: Consider adapting dialog content layout for very narrow terminals
2. **Minimum Usable Width**: Define minimum terminal width for optimal user experience
3. **Mobile Support**: These fixes lay groundwork for potential mobile terminal support
4. **Accessibility**: Enhanced boundary checking improves screen reader compatibility

## Related Issues

This fix addresses the core issue described in the user request:
> "When terminal becomes horizontally narrow, some Dialogs stop rendering correctly"

The fix ensures all dialogs (BatchRenameDialog, DrivesDialog, ListDialog, JumpDialog, SearchDialog) render correctly regardless of terminal width.