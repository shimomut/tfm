# TFM Curses Boundary Fix

## Problem

When entering search mode (pressing `F`), TFM was crashing with the error:
```
_curses.error: addwstr() returned ERR
```

This error occurs when trying to write to the last column of the terminal screen, which causes curses to attempt to wrap to the next line and fail.

## Root Cause

The issue was in the `draw_status()` method where we were:
1. Creating a status line string with exactly `width` characters
2. Writing it starting at position (status_y, 0)
3. This would attempt to write to the last column (width-1), causing the curses error

## Solution

### 1. Safe String Length
Changed all full-width string drawing to use `width - 1` instead of `width`:

```python
# Before (problematic)
status_line = " " * width
self.stdscr.addstr(status_y, 0, status_line, get_status_color())

# After (safe)
status_line = " " * (width - 1)
self.safe_addstr(status_y, 0, status_line, get_status_color())
```

### 2. Safe Drawing Method
Added a `safe_addstr()` method that handles boundary conditions:

```python
def safe_addstr(self, y, x, text, attr=curses.A_NORMAL):
    """Safely add string to screen, handling boundary conditions"""
    try:
        height, width = self.stdscr.getmaxyx()
        
        # Check bounds
        if y < 0 or y >= height or x < 0 or x >= width:
            return
            
        # Truncate text if it would exceed screen width
        max_len = width - x - 1  # Leave space to avoid last column
        if max_len <= 0:
            return
            
        truncated_text = text[:max_len] if len(text) > max_len else text
        self.stdscr.addstr(y, x, truncated_text, attr)
    except curses.error:
        pass  # Ignore curses errors
```

### 3. Updated All Status Drawing
- Search mode status display
- Normal mode status display  
- Header area clearing
- Debug mode line clearing

### 4. Improved Text Positioning
- Added overlap detection for help text
- Better spacing calculations
- Safer right-alignment logic

## Files Modified

- `tfm_main.py` - Fixed curses boundary issues in multiple drawing methods

## Testing

The fix was verified with:
- Normal terminal sizes (80x24, 120x30)
- Very narrow terminals (20x10)
- Search mode with long patterns
- Status display with long control text

## Benefits

- ✅ No more crashes when entering search mode
- ✅ Graceful handling of narrow terminals
- ✅ Robust text truncation and positioning
- ✅ Safe drawing throughout the application
- ✅ Better error handling for curses operations

The search functionality now works reliably across different terminal sizes and configurations.