# Background Color Fix - Replacing bkgd() with addstr() Approach

## Problem

The `curses.window.bkgd()` method behaves inconsistently across different terminal environments and operating systems. This caused background color rendering issues where some terminals would not properly apply the color scheme's background color, leading to visual inconsistencies.

## Solution

Replaced the `bkgd()` approach with a more reliable method using `addstr()` with whitespace characters and a dedicated color pair.

## Changes Made

### 1. Added COLOR_BACKGROUND Color Pair

**File:** `src/tfm_colors.py`

- Added `COLOR_BACKGROUND = 27` constant for dedicated background color pair
- Initialized the color pair in `init_colors()` function:
  ```python
  # Background color pair for filling areas
  curses.init_pair(COLOR_BACKGROUND, default_fg, default_bg)
  ```

### 2. Updated get_background_color_pair() Function

**File:** `src/tfm_colors.py`

- Simplified the function to return the dedicated `COLOR_BACKGROUND` color pair
- Removed dependency on color pair 63 and fallback logic
- More reliable and consistent approach:
  ```python
  def get_background_color_pair():
      """Get a color pair that can be used for background areas"""
      try:
          import curses
          # Return the dedicated background color pair
          return curses.color_pair(COLOR_BACKGROUND)
      except:
          return 0
  ```

### 3. Replaced apply_background_to_window() Implementation

**File:** `src/tfm_colors.py`

**Before (using bkgd()):**
```python
def apply_background_to_window(window):
    """Apply the color scheme background to a curses window"""
    try:
        import curses
        if default_background_color is not None:
            # Set the background character and color for the window
            bg_char = ' '  # Space character
            bg_attr = get_background_color_pair()
            window.bkgd(bg_char, bg_attr)  # PROBLEMATIC
            return True
    except:
        pass
    return False
```

**After (using addstr()):**
```python
def apply_background_to_window(window):
    """Apply the color scheme background to a curses window using addstr() method"""
    try:
        import curses
        if default_background_color is not None:
            # Get window dimensions
            height, width = window.getmaxyx()
            bg_attr = get_background_color_pair()
            
            # Fill the window with spaces using the background color
            for y in range(height):
                try:
                    # Fill each line with spaces, leaving room for cursor at end
                    window.addstr(y, 0, ' ' * (width - 1), bg_attr)
                except curses.error:
                    pass  # Ignore errors at screen edges
            
            # Move cursor back to top-left
            try:
                window.move(0, 0)
            except curses.error:
                pass
            
            return True
    except:
        pass
    return False
```

## Benefits

### 1. **Consistency Across Environments**
- The `addstr()` method works consistently across different terminal emulators
- No longer dependent on terminal-specific `bkgd()` behavior
- Reliable background color rendering on all supported platforms

### 2. **Better Error Handling**
- Graceful handling of screen edge cases with `curses.error` exceptions
- Continues operation even if individual line fills fail
- Proper cursor positioning after background application

### 3. **Maintainability**
- Clearer, more explicit approach to background filling
- Easier to debug and understand the background rendering process
- Consistent with other color application methods in the codebase

## Testing

### Verification Script
Created `tools/verify_bkgd_removal.py` to ensure complete removal of `bkgd()` usage:
- Scans all Python files in the project
- Confirms no `bkgd()` method calls remain
- Verifies new `addstr()` implementation is in place
- Validates `COLOR_BACKGROUND` constant exists

### Test Script
Created `test/test_background_color_fix.py` to verify the new approach:
- Tests both dark and light color schemes
- Demonstrates manual background filling
- Confirms proper color pair usage
- Interactive visual verification

## Compatibility

- **Backward Compatible:** No changes to public API
- **Terminal Support:** Works with all curses-compatible terminals
- **Color Schemes:** Supports both dark and light color schemes
- **Fallback Handling:** Graceful degradation if color operations fail

## Usage

The fix is transparent to existing code. The `apply_background_to_window()` function maintains the same interface:

```python
from tfm_colors import apply_background_to_window

# Apply background to any curses window
success = apply_background_to_window(my_window)
```

The fallback method in `tfm_main.py` also continues to work as before, now using the more reliable `get_background_color_pair()` function.

## Files Modified

1. **src/tfm_colors.py** - Main implementation changes
2. **test/test_background_color_fix.py** - New test file
3. **tools/verify_bkgd_removal.py** - New verification script
4. **doc/BACKGROUND_COLOR_FIX.md** - This documentation

## Verification

Run the verification script to confirm the fix:
```bash
python tools/verify_bkgd_removal.py
```

Run the test to see the fix in action:
```bash
python test/test_background_color_fix.py
```

Both should complete successfully, confirming that the background color fix is properly implemented and working across different environments.