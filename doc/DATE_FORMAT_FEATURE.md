# Date Format Feature

## Overview

TFM provides flexible date-time formatting in file list panes with two display variations. Users can toggle between formats using the View Options menu or configure a default format in their configuration file.

## Date Format Variations

### 1. Short Format (Default)
**Format:** `YY-MM-DD HH:mm`

The short format provides a balanced view with date and time but without seconds.

**Benefits:**
- Good compromise between detail and space
- Always shows both date and time
- Two-digit year saves space
- Suitable for most use cases
- Uses ISO 8601 date format with hyphens

**Example:**
```
Filename                Size      Date/Time
report.txt              2.5K      24-12-17 14:30
notes.txt               1.2K      24-12-17 09:15
backup.zip              45M       24-12-16 18:20
archive.tar.gz          120M      24-11-20 10:05
```

### 2. Full Format
**Format:** `YYYY-MM-DD HH:mm:ss`

The full format always displays complete date and time information with seconds.

**Benefits:**
- Most detailed timestamp information
- Includes seconds for precise tracking
- Four-digit year for clarity
- Best for detailed file analysis
- Uses ISO 8601 date format with hyphens

**Example:**
```
Filename                Size      Date/Time
report.txt              2.5K      2024-12-17 14:30:45
notes.txt               1.2K      2024-12-17 09:15:22
backup.zip              45M       2024-12-16 18:20:10
archive.tar.gz          120M      2024-11-20 10:05:33
```

## Using Date Formats

### Changing Format While Running TFM

1. Press `z` to open the **View Options** menu
2. Select **"Cycle date format"**
3. The format toggles between: **Short ↔ Full**
4. The file list updates immediately to show the new format

**Visual feedback:**
```
Date format: Short (YY-MM-DD HH:mm)
Date format: Full (YYYY-MM-DD HH:mm:ss)
```

### Setting Default Format

To configure your preferred default format, add this to your `~/.tfm/config.py`:

```python
class Config:
    # Date format for file list panes
    DATE_FORMAT = 'short'  # Options: 'short', 'full'
```

**Configuration options:**
- `'short'` - Short format (default): YY-MM-DD HH:mm
- `'full'` - Full format: YYYY-MM-DD HH:mm:ss

## Use Cases

### Short Format - Best For:
- General file browsing (default)
- Consistent date/time display
- Moderate detail needs
- Balanced information density
- Cross-day file comparisons

### Full Format - Best For:
- Detailed file analysis
- Comparing precise timestamps
- Debugging time-sensitive issues
- Archival and backup verification
- When seconds matter

## Technical Details

### Automatic Column Width Adjustment

The date column width automatically adjusts when you change formats:

- **Short format:** 14 characters wide (for `YY-MM-DD HH:mm`)
- **Full format:** 19 characters wide (for `YYYY-MM-DD HH:mm:ss`)

This ensures:
- Proper column alignment for each format
- Optimal use of screen space
- Smooth visual transitions when switching formats

The filename column automatically adjusts to give the date column the space it needs.

### Format Specifications

| Format | Pattern | Example | Width |
|--------|---------|---------|-------|
| Short | `%y-%m-%d %H:%M` | `24-12-17 14:30` | 14 chars |
| Full | `%Y-%m-%d %H:%M:%S` | `2024-12-17 14:30:45` | 19 chars |

Both formats use ISO 8601 date format with hyphens for consistency and international compatibility.

## Keyboard Reference

| Key | Action |
|-----|--------|
| `z` | Open View Options menu |
| Select "Cycle date format" | Change date format |

## Configuration Example

Complete configuration example in `~/.tfm/config.py`:

```python
class Config:
    # Display settings
    SHOW_HIDDEN_FILES = False
    DATE_FORMAT = 'short'  # 'short' or 'full'
    
    # Other settings...
    DEFAULT_SORT_MODE = 'name'
    COLOR_SCHEME = 'dark'
```

## Tips

1. **Short format is the default** - It provides the best balance for most users
2. **Use Full format for debugging** - When you need precise timestamps with seconds
3. **Format persists during session** - Your choice remains until you quit TFM
4. **Set default in config** - Save your preferred format for all sessions
5. **Toggle with z key** - Quick access through View Options menu

## Related Features

- **Sort by date** - Press `4` to sort files by modification date
- **File details** - Press `i` to see detailed file information including full timestamp
- **View options** - Press `z` to access other view customization options

## See Also

- View Options Menu
- [Configuration Guide](CONFIGURATION_FEATURE.md)
- Keyboard Shortcuts
