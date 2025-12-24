# Date Format Implementation

## Overview

This document describes the implementation of flexible date-time formatting in TFM's file list panes. The feature provides two format variations (short, full) that users can toggle between via the View Options menu.

## Architecture

### Components

1. **Configuration** (`tfm_config.py`)
   - Stores default date format preference
   - Provides `DATE_FORMAT` setting

2. **Constants** (`tfm_const.py`)
   - Defines format type constants
   - Provides format identifiers

3. **File Operations** (`tfm_file_operations.py`)
   - Implements date formatting logic
   - Provides `_format_date()` method

4. **Main Application** (`tfm_main.py`)
   - Handles format cycling in View Options menu
   - Updates display when format changes

## Implementation Details

### Constants Definition

**File:** `src/tfm_const.py`

```python
# File list date format options
DATE_FORMAT_FULL = 'full'        # YYYY-MM-DD HH:mm:ss
DATE_FORMAT_SHORT = 'short'      # YY-MM-DD HH:mm
```

These constants provide type-safe format identifiers used throughout the codebase.

### Configuration Setting

**File:** `src/tfm_config.py`

```python
class DefaultConfig:
    # Display settings
    DATE_FORMAT = 'short'  # 'short' or 'full'
```

The default configuration sets short format as the default. Users can override this in `~/.tfm/config.py`.

### Date Formatting Logic

**File:** `src/tfm_file_operations.py`

```python
def _format_date(self, timestamp):
    """Format date/time based on configured format.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        str: Formatted date/time string
    """
    from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT
    
    dt = datetime.fromtimestamp(timestamp)
    date_format = getattr(self.config, 'DATE_FORMAT', 'short')
    
    if date_format == DATE_FORMAT_FULL:
        # YYYY-MM-DD HH:mm:ss
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:  # DATE_FORMAT_SHORT (default)
        # YY-MM-DD HH:mm
        return dt.strftime("%y-%m-%d %H:%M")
```

**Key design decisions:**

1. **Lazy import of constants** - Constants are imported within the method to avoid circular dependencies
2. **Fallback to 'short'** - Uses `getattr()` with default to handle missing config
3. **ISO 8601 format** - Uses hyphens for date separators (international standard)
4. **Simple logic** - Two formats only, no complex date comparison needed

### Integration with File Info

**File:** `src/tfm_file_operations.py`

```python
def get_file_info(self, path):
    """Get file information for display"""
    try:
        stat_info = path.stat()
        
        # Format size...
        
        # Format date based on configured format
        date_str = self._format_date(stat_info.st_mtime)
        
        return size_str, date_str
    except (OSError, PermissionError):
        return "---", "---"
```

The `get_file_info()` method calls `_format_date()` to format the modification timestamp. This ensures consistent formatting across all file list displays.

### Column Width Calculation

**File:** `src/tfm_main.py`

```python
def draw_pane(self, pane_data, start_x, pane_width, is_active):
    """Draw a single pane"""
    # ...
    
    # Get dynamic date column width based on current format
    datetime_width = self.get_date_column_width()
    size_width = 8
    
    # Calculate filename width: usable_width - (marker + spaces + size + date)
    name_width = usable_width - (12 + datetime_width)
    
    # Format line with proper column alignment
    line = f"{marker} {padded_name} {size_str:>8} {date_str}"
```

The `draw_pane()` method calls `get_date_column_width()` to determine the appropriate column width for the current format. This ensures the filename column adjusts to give the date column exactly the space it needs.

### View Options Menu Integration

**File:** `src/tfm_main.py`

```python
def show_view_options(self):
    """Show view options dialog with toggle options"""
    def handle_view_option(option):
        # ... other options ...
        
        elif option == "Cycle date format":
            from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT
            current_format = getattr(self.config, 'DATE_FORMAT', 'short')
            
            # Toggle between formats: short <-> full
            if current_format == DATE_FORMAT_SHORT:
                new_format = DATE_FORMAT_FULL
                format_name = "Full (YYYY-MM-DD HH:mm:ss)"
            else:  # DATE_FORMAT_FULL
                new_format = DATE_FORMAT_SHORT
                format_name = "Short (YY-MM-DD HH:mm)"
            
            # Update config
            self.config.DATE_FORMAT = new_format
            print(f"Date format: {format_name}")
            self.needs_full_redraw = True
    
    # Define the view options
    options = [
        "Toggle hidden files",
        "Toggle color scheme (dark/light)", 
        "Toggle fallback color scheme",
        "Cycle date format"
    ]
    
    self.show_list_dialog("View Options", options, handle_view_option)
```

**Key implementation details:**

1. **Toggle behavior** - Short ↔ Full (simple two-state toggle)
2. **Runtime config update** - Directly modifies `self.config.DATE_FORMAT`
3. **User feedback** - Prints format name to status line
4. **Display update** - Sets `needs_full_redraw = True` to refresh file lists

## Format Specifications

### strftime Patterns

| Format | Pattern | Example | Description |
|--------|---------|---------|-------------|
| Short | `%y-%m-%d %H:%M` | `24-12-17 14:30` | 2-digit year, no seconds |
| Full | `%Y-%m-%d %H:%M:%S` | `2024-12-17 14:30:45` | 4-digit year, full timestamp |

### Character Width

| Format | Column Width | Actual Content Width | Notes |
|--------|--------------|---------------------|-------|
| Short | 14 | 14 | `YY-MM-DD HH:MM` |
| Full | 19 | 19 | `YYYY-MM-DD HH:MM:SS` |

Both formats use ISO 8601 date format with hyphens for international compatibility.

### Dynamic Column Width Adjustment

The file list automatically adjusts the date column width when the format changes:

```python
def get_date_column_width(self):
    """Calculate the date column width based on current date format setting."""
    date_format = getattr(self.config, 'DATE_FORMAT', 'short')
    
    if date_format == DATE_FORMAT_FULL:
        return 19  # YYYY-MM-DD HH:mm:ss
    else:  # DATE_FORMAT_SHORT (default)
        return 14  # YY-MM-DD HH:mm
```

This ensures:
- **Proper alignment** - Columns stay aligned regardless of format
- **Optimal space usage** - Each format uses only the space it needs
- **Smooth transitions** - Switching formats updates layout immediately

## Testing

### Unit Tests

**File:** `test/test_date_format.py`

Tests cover:
- All three format variations
- Format cycling behavior
- Edge cases (midnight, date boundaries)
- Today vs. not-today logic

### Demo Script

**File:** `demo/demo_date_format.py`

Demonstrates:
- Visual comparison of all formats
- Format cycling sequence
- Real file examples with different timestamps

## Performance Considerations

### Timestamp Conversion

```python
dt = datetime.fromtimestamp(timestamp)
```

This conversion happens for every file in the list. Performance impact:
- **Negligible for typical directories** (< 1000 files)
- **Acceptable for large directories** (1000-10000 files)
- **Cached by OS** - `stat()` results are typically cached

### Date Comparison (Auto Format)

```python
today = datetime.now().date()
file_date = dt.date()
if file_date == today:
    # ...
```

The date comparison adds minimal overhead:
- Two `date()` object creations
- One equality comparison
- No string operations until format selection

**Optimization opportunity:** Cache `today` value if formatting many files in a single refresh.

## Error Handling

### Missing Configuration

```python
date_format = getattr(self.config, 'DATE_FORMAT', 'auto')
```

Uses `getattr()` with default to handle:
- Missing `DATE_FORMAT` attribute
- Old configuration files
- Runtime config modifications

### Invalid Timestamps

The `get_file_info()` method catches exceptions:

```python
try:
    stat_info = path.stat()
    date_str = self._format_date(stat_info.st_mtime)
    return size_str, date_str
except (OSError, PermissionError):
    return "---", "---"
```

Invalid or inaccessible files show `"---"` for the date.

## Future Enhancements

### Potential Improvements

1. **Custom format strings**
   - Allow users to define custom strftime patterns
   - Add to configuration: `DATE_FORMAT_CUSTOM = "%d/%m/%y %H:%M"`

2. **Locale-aware formatting**
   - Use locale-specific date formats
   - Support international date conventions

3. **Relative time display**
   - "2 hours ago", "yesterday", "last week"
   - Similar to `ls -lh` with relative times

4. **Column width optimization**
   - Auto-adjust column width based on format
   - Maintain alignment with variable-width auto format

5. **Format persistence**
   - Save format choice to session state
   - Restore on next launch

### Implementation Considerations

**Custom formats:**
```python
# In config
DATE_FORMAT = 'custom'
DATE_FORMAT_CUSTOM = "%d/%m/%y %H:%M"

# In _format_date()
elif date_format == 'custom':
    custom_format = getattr(self.config, 'DATE_FORMAT_CUSTOM', '%Y-%m-%d %H:%M')
    return dt.strftime(custom_format)
```

**Locale support:**
```python
import locale
locale.setlocale(locale.LC_TIME, '')  # Use system locale
return dt.strftime('%x %X')  # Locale-specific date and time
```

## Related Code

### Other Date Formatting

The codebase has other date formatting locations:

1. **Log timestamps** (`tfm_log_manager.py`)
   - Uses `LOG_TIME_FORMAT = "%H:%M:%S"`
   - Separate from file list formatting

2. **Archive timestamps** (`tfm_archive.py`)
   - Uses `'%Y-%m-%d %H:%M:%S'` format
   - Could be unified with file list formatting

3. **File details dialog** (`tfm_path.py`)
   - Uses `_format_time()` method
   - Shows full timestamp in details view

### Consistency Opportunities

Consider unifying date formatting across:
- File list panes (this implementation)
- File details dialog
- Archive file listings
- Search results

## Dependencies

### Required Modules

```python
from datetime import datetime
from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT, DATE_FORMAT_AUTO
```

### Configuration Dependencies

- `tfm_config.DefaultConfig.DATE_FORMAT`
- User config: `~/.tfm/config.py`

### Runtime Dependencies

- `FileOperations.config` - Configuration object
- `stat_info.st_mtime` - File modification timestamp

## Debugging

### Enable Debug Output

Add debug prints to `_format_date()`:

```python
def _format_date(self, timestamp):
    dt = datetime.fromtimestamp(timestamp)
    date_format = getattr(self.config, 'DATE_FORMAT', 'auto')
    
    # Debug output
    print(f"DEBUG: Formatting {dt} with format {date_format}")
    
    # ... rest of method
```

### Test Format Changes

```python
# In Python REPL
from tfm_file_operations import FileOperations
from tfm_config import DefaultConfig

config = DefaultConfig()
config.DATE_FORMAT = 'full'  # or 'short', 'auto'

file_ops = FileOperations(config)
result = file_ops._format_date(1702828800)  # Test timestamp
print(result)
```

## See Also

- [Date Format Feature Documentation](../DATE_FORMAT_FEATURE.md)
- View Options Implementation
- [Configuration System](CONFIGURATION_SYSTEM.md)
- File Operations Module
