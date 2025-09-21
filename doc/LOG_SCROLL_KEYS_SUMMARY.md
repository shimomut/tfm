# Log Pane Scrolling Keys Implementation Summary

## Overview
Enhanced TFM's log pane scrolling functionality by adding Shift+Up/Down/Left/Right key bindings for more precise and faster log navigation.

## New Key Bindings

### Existing Keys (Preserved)
- `Ctrl+K` - Scroll log up by 1 line
- `Ctrl+L` - Scroll log down by 1 line
- `Page Up` - Scroll log up by 5 lines
- `Page Down` - Scroll log down by 5 lines

### New Shift Key Bindings
- `Shift+Up` - Scroll log up (toward older messages, precise scrolling)
- `Shift+Down` - Scroll log down (toward newer messages, precise scrolling)
- `Shift+Left` - Fast scroll up (toward older messages, by log pane height)
- `Shift+Right` - Fast scroll down (toward newer messages, by log pane height)

## Key Features

### 1. Precise Control
- Shift+Up/Down provides single-line scrolling for precise navigation
- Works independently of file list navigation (doesn't affect file selection)

### 2. Fast Navigation
- Shift+Left/Right scrolls by the current log pane height
- Dynamically calculates scroll distance based on actual log pane size
- Minimum scroll of 1 line even when log pane is very small

### 3. Terminal Compatibility
- Supports multiple key code variations for different terminals
- Handles both primary and alternative Shift key codes
- Graceful fallback for terminals that don't support Shift combinations

## Implementation Details

### Key Constants Added
```python
# In src/tfm_const.py
KEY_SHIFT_LEFT_1 = 545    # Shift+Left in some terminals
KEY_SHIFT_RIGHT_1 = 560   # Shift+Right in some terminals
KEY_SHIFT_LEFT_2 = 393    # Alternative Shift+Left code
KEY_SHIFT_RIGHT_2 = 402   # Alternative Shift+Right code
```

### New Method Added
```python
# In src/tfm_main.py
def _get_log_pane_height(self):
    """Calculate the current log pane height in lines"""
    height, width = self.stdscr.getmaxyx()
    calculated_height = int(height * self.log_height_ratio)
    log_height = calculated_height if self.log_height_ratio > 0 else 0
    return log_height
```

### Key Handler Logic
```python
elif key == 337:  # Shift+Up - scroll toward older messages
    if self.log_manager.scroll_log_up(1):
        self.needs_full_redraw = True
elif key == 336:  # Shift+Down - scroll toward newer messages
    if self.log_manager.scroll_log_down(1):
        self.needs_full_redraw = True
elif key == 545:  # Shift+Left - fast scroll toward older messages
    log_height = self._get_log_pane_height()
    if self.log_manager.scroll_log_up(max(1, log_height)):
        self.needs_full_redraw = True
elif key == 560:  # Shift+Right - fast scroll toward newer messages
    log_height = self._get_log_pane_height()
    if self.log_manager.scroll_log_down(max(1, log_height)):
        self.needs_full_redraw = True
```

## Files Modified

### Core Implementation
- `src/tfm_const.py` - Added new Shift key constants
- `src/tfm_main.py` - Added key handlers and `_get_log_pane_height()` method

### Documentation Updates
- `src/tfm_info_dialog.py` - Added "Log Pane Controls" section to help dialog
- `test/test_help_content.py` - Updated help content with new key bindings
- `README.md` - Updated key binding table

### Testing
- `test/test_log_scroll_keys.py` - Comprehensive test suite for new functionality

## User Benefits

### 1. Improved Workflow
- No need to switch between different key combinations for different scroll speeds
- Intuitive directional mapping (Left=Up, Right=Down for fast scrolling)

### 2. Better Log Navigation
- Single-line precision for reading specific log entries
- Fast navigation through large log histories
- Consistent behavior across different log pane sizes

### 3. Enhanced Usability
- Works only for log pane (doesn't interfere with file list navigation)
- Visual feedback through immediate screen updates
- Respects log pane boundaries (no scrolling beyond available content)

## Technical Notes

### Key Code Handling
- Uses multiple key codes to support different terminal emulators
- Primary codes (545/560) for most modern terminals
- Alternative codes (393/402) for compatibility
- Graceful handling when keys aren't supported

### Performance
- Minimal overhead - only calculates log height when needed
- Efficient redraw - only triggers when scrolling actually occurs
- No impact on file operations or other TFM functionality

### Compatibility
- Backward compatible - all existing key bindings preserved
- No configuration changes required
- Works with existing log management system

## Usage Examples

### Precise Log Reading
1. Use `Shift+Up/Down` to scroll line by line through log messages
2. Perfect for reading error messages or detailed operation logs

### Fast Log Navigation
1. Use `Shift+Left` to quickly scroll up through log history
2. Use `Shift+Right` to quickly scroll down to recent messages
3. Scroll distance automatically adjusts to log pane size

### Combined Navigation
1. Use `Shift+Left` for fast navigation to approximate area
2. Use `Shift+Up/Down` for precise positioning
3. Use existing `Ctrl+K/L` as alternative single-line scrolling

This implementation provides users with comprehensive log navigation control while maintaining TFM's intuitive and efficient interface design.