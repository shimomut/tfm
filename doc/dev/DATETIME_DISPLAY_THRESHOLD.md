# Dynamic Datetime Display Threshold

## Overview

This document describes the dynamic threshold logic that determines when datetime information is displayed or hidden in the file list panes based on available pane width and configured date format.

## Core Principle

The datetime column is **dynamically shown or hidden** based on whether there is sufficient space to display all file information legibly. The threshold adjusts automatically based on the configured date format width.

## Threshold Calculation

### Formula

```
min_width_for_datetime = marker(2) + space(1) + min_name(16) + space(1) + ext(4) + space(1) + size(8) + space(1) + datetime_width
                       = 34 + datetime_width
```

### Components

- **Selection marker**: 2 characters (`● ` or `  `)
- **Minimum filename**: 16 characters (ensures readable filenames)
- **Extension**: 4 characters (typical extension length)
- **File size**: 8 characters (right-aligned, e.g., `  1.5M`)
- **Datetime**: Variable width based on format
- **Spacing**: 1 character between each column

### Date Format Widths

| Format | Example | Width | Minimum Pane Width |
|--------|---------|-------|-------------------|
| Short  | `24-12-18 14:30` | 14 chars | 48 chars |
| Full   | `2024-12-18 14:30:45` | 19 chars | 53 chars |

## Display Logic

### When Datetime is Shown

Datetime is displayed when:
```python
pane_width >= min_width_for_datetime
```

**Short format**: `pane_width >= 48`
**Full format**: `pane_width >= 53`

Display format:
```
● filename.ext   1.5M 24-12-18 14:30
```

### When Datetime is Hidden

Datetime is hidden when:
```python
pane_width < min_width_for_datetime
```

**Short format**: `pane_width < 48`
**Full format**: `pane_width < 53`

Display format:
```
● filename.ext   1.5M
```

## Implementation

### Code Location

File: `src/tfm_main.py`
Method: `draw_file_line()`

### Key Code

```python
# Calculate datetime width based on current format
datetime_width = self.get_date_column_width()  # Returns 14 or 19

# Calculate minimum width needed to show datetime
# marker(2) + space(1) + min_name(16) + space(1) + ext(4) + space(1) + size(8) + space(1) + datetime
min_width_for_datetime = 2 + 1 + 16 + 1 + 4 + 1 + 8 + 1 + datetime_width  # = 34 + datetime_width

if pane_width < min_width_for_datetime:
    # Hide datetime - format: "● basename ext size"
    # ...
else:
    # Show datetime - format: "● basename ext size datetime"
    # ...
```

## Benefits

### 1. Format-Aware Threshold

The threshold automatically adjusts when users switch between date formats:
- Short format (14 chars) → threshold = 48 characters
- Full format (19 chars) → threshold = 53 characters

This ensures consistent behavior regardless of format choice.

### 2. Optimal Space Usage

- **Wide panes**: Show all information including datetime
- **Narrow panes**: Prioritize filename visibility by hiding datetime
- **Very narrow panes**: Gracefully degrade to minimal display

### 3. Readable Filenames

The 16-character minimum filename width ensures:
- Most filenames remain readable even when truncated
- Consistent column alignment
- Professional appearance

## Practical Examples

### Terminal Width Scenarios

| Pane Width | Short Format | Full Format |
|-----------|--------------|-------------|
| 40 chars  | Hide datetime | Hide datetime |
| 45 chars  | Hide datetime | Hide datetime |
| 48 chars  | **Show datetime** | Hide datetime |
| 50 chars  | Show datetime | Hide datetime |
| 53 chars  | Show datetime | **Show datetime** |
| 60 chars  | Show datetime | Show datetime |
| 80 chars  | Show datetime | Show datetime |

### Split Pane Scenarios

**80-column terminal with 50/50 split:**
- Each pane: 40 characters
- Result: Both panes hide datetime (too narrow)

**120-column terminal with 50/50 split:**
- Each pane: 60 characters
- Result: Both panes show datetime (sufficient width)

**100-column terminal with 60/40 split:**
- Left pane: 60 characters → shows datetime
- Right pane: 40 characters → hides datetime

## User Experience

### Automatic Adaptation

Users don't need to manually configure datetime visibility. The system automatically:
1. Detects available pane width
2. Checks current date format width
3. Shows or hides datetime accordingly
4. Maintains optimal readability

### Format Switching

When users cycle date formats (via menu or keyboard shortcut):
1. System recalculates threshold
2. Redraws file list with new threshold
3. Datetime may appear or disappear based on new width requirements

### Pane Resizing

When users adjust pane ratios:
1. System recalculates each pane's width
2. Applies threshold independently to each pane
3. Left and right panes may show different information based on their widths

## Configuration

### Date Format Setting

Users can configure the date format in `src/_config.py`:

```python
DATE_FORMAT = 'short'  # Options: 'short' or 'full'
```

Or cycle formats at runtime using:
- Menu: `Options → Cycle date format`
- The threshold automatically adjusts to the new format

### Minimum Filename Width

The minimum filename width (16 characters) is hardcoded in the threshold calculation. To adjust:

```python
# In src/tfm_main.py, line ~1035
min_width_for_datetime = 2 + 1 + 16 + 1 + 4 + 1 + 8 + 1 + datetime_width
#                                  ^^
#                                  Adjust this value
```

**Considerations when changing:**
- **Smaller value** (e.g., 12): Shows datetime in narrower panes, but filenames may be too truncated
- **Larger value** (e.g., 20): Requires wider panes to show datetime, but ensures more readable filenames

## Testing

### Test Script

Location: `temp/test_dynamic_datetime_threshold.py`

Run test:
```bash
python temp/test_dynamic_datetime_threshold.py
```

### Test Coverage

The test verifies:
1. Correct threshold calculation for both formats
2. Datetime visibility at various pane widths
3. Comparison between short and full format thresholds
4. Practical terminal width scenarios

## Related Features

- **Date Format Configuration**: `src/tfm_config.py`
- **Date Formatting Logic**: `src/tfm_file_operations.py` (`_format_date()`)
- **Column Width Calculation**: `src/tfm_main.py` (`get_date_column_width()`)
- **File Line Drawing**: `src/tfm_main.py` (`draw_file_line()`)

## Future Enhancements

### Potential Improvements

1. **Configurable minimum filename width**: Allow users to set their preferred minimum
2. **Progressive disclosure**: Show abbreviated datetime (e.g., just date) in medium-width panes
3. **Smart truncation**: Prioritize showing datetime for recently modified files
4. **User preference**: Allow users to force datetime on/off regardless of width

### Backward Compatibility

The old fixed threshold (60 characters) has been replaced with the dynamic calculation. This change:
- **Improves** behavior for short format users (shows datetime at 48+ instead of 60+)
- **Maintains** similar behavior for full format users (53 vs 60)
- **Preserves** all existing functionality
- **Requires** no configuration changes

## Summary

The dynamic datetime threshold provides an intelligent, format-aware system for managing file list display. It automatically adapts to:
- Current date format width (14 or 19 characters)
- Available pane width
- User preferences for date format

This ensures optimal readability and space usage across different terminal sizes and configurations.
