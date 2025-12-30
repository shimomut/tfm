# NFD Normalization Implementation

## Overview

This document describes the implementation of NFD (Normalization Form D) to NFC (Normalization Form C) conversion in TFM and TTK to handle macOS filesystem filename encoding correctly.

## Problem Statement

macOS filesystems use NFD normalization for filenames, where characters like "が" are decomposed into:
- Base character: "か" (U+304B)
- Combining mark: "゙" (U+3099 - combining katakana-hiragana voiced sound mark)

This decomposition causes layout issues in TFM because:
1. The string length becomes 2 instead of 1
2. Width calculation treats them as separate characters
3. The combining mark may be counted as having width, causing misalignment

### Example

```python
# NFC (Normalization Form C) - Composed
char_nfc = "が"  # Single character U+304C
len(char_nfc)    # 1
display_width    # Should be 2 (wide character)

# NFD (Normalization Form D) - Decomposed (macOS default)
char_nfd = "が"  # Base + combining mark
len(char_nfd)    # 2
display_width    # Was incorrectly calculated
```

## Solution

Convert NFD to NFC at the rendering layer to ensure consistent width calculation and display.

### Implementation Locations

#### 1. TTK CoreGraphics Backend (`ttk/backends/coregraphics_backend.py`)

**Function: `_is_wide_character()`**
- Does NOT normalize to NFC (optimization)
- Assumes input is a single character (length 1)
- All callers guarantee this constraint:
  - `draw_text()` - normalizes entire string to NFC, then iterates through single chars
  - `draw_hline()` - validates char length is 1 (raises ValueError otherwise)
  - `draw_vline()` - validates char length is 1 (raises ValueError otherwise)

```python
def _is_wide_character(char: str) -> bool:
    # No normalization needed - callers ensure single-char input
    if len(char) != 1:
        return False
    # ... rest of implementation
```

**Method: `CoreGraphicsBackend.draw_text()`**
- Added NFC normalization before rendering
- Ensures text is displayed with correct width
- Normalizes once at string level, not per-character

```python
def draw_text(self, row: int, col: int, text: str, ...):
    # Normalize to NFC to handle macOS NFD decomposition
    text = unicodedata.normalize('NFC', text)
    # ... iterate through chars and call _is_wide_character()
```

**Methods: `draw_hline()` and `draw_vline()`**
- Added validation to ensure char parameter is a single character
- Raises ValueError if len(char) != 1
- This prevents NFD-decomposed characters (which have length > 1) from being passed to `_is_wide_character()`

```python
def draw_hline(self, row: int, col: int, char: str, ...):
    if len(char) != 1:
        raise ValueError(f"char must be a single character, got length {len(char)}")
    # ... rest of implementation
```

#### 2. TTK Curses Backend (`ttk/backends/curses_backend.py`)

**Method: `CursesBackend.draw_text()`**
- Added NFC normalization before rendering
- Ensures text is displayed with correct width in terminal
- Normalizes once at string level before passing to curses

```python
def draw_text(self, row: int, col: int, text: str, ...):
    # Normalize to NFC to handle macOS NFD decomposition
    text = unicodedata.normalize('NFC', text)
    # ... pass to curses for rendering
```

#### 3. TFM Wide Character Utils (`src/tfm_wide_char_utils.py`)

**Function: `_cached_get_display_width()`**
- Added NFC normalization before width calculation
- Ensures accurate display width for all text
- Normalization happens once at the string level, not per-character
- Calls internal `_is_wide_character()` for each character

**Note on `_cached_is_wide_character()` and `_is_wide_character()`**
- `_cached_is_wide_character()` does NOT normalize (optimization)
- Relies on caller (`_cached_get_display_width()`) to normalize the entire string first
- This avoids redundant normalization for each character
- `_is_wide_character()` is the internal function that calls `_cached_is_wide_character()`
- It is not part of the public API and is only used internally within the module

### Why This Approach?

1. **Automatic handling**: Normalization happens transparently at the rendering layer
2. **No API changes**: Existing code continues to work without modification
3. **Performance**: Normalization is cached via `@lru_cache` decorators
4. **Correctness**: Handles both NFC and NFD inputs correctly

## Testing

Test file: `test/test_nfd_normalization.py`

Tests verify:
1. NFD and NFC forms have identical display widths
2. Wide character detection works for both forms
3. Mixed NFD/NFC strings are handled correctly
4. Realistic filename scenarios work properly

Run tests:
```bash
PYTHONPATH=.:src:ttk python3 test/test_nfd_normalization.py
```

## Technical Details

### Unicode Normalization Forms

- **NFC (Canonical Composition)**: Characters are composed into single code points
  - Example: "が" = U+304C (single character)
  
- **NFD (Canonical Decomposition)**: Characters are decomposed into base + combining marks
  - Example: "が" = U+304B + U+3099 (base + combining mark)

### macOS Filesystem Behavior

macOS HFS+ and APFS filesystems automatically convert filenames to NFD:
- Files created with NFC names are stored as NFD
- `os.listdir()` and similar functions return NFD strings
- This is transparent to most applications but affects display width

### Performance Considerations

- Normalization is applied at rendering time, not during filesystem operations
- Results are cached via `@lru_cache` to minimize overhead
- Cache sizes: 1024 for `_is_wide_character`, 2048 for `_get_display_width`
- **Optimization in TFM**: Normalization happens once per string in `_cached_get_display_width()`, not per-character in `_cached_is_wide_character()`
- **Optimization in TTK**: Normalization happens once per string in `draw_text()`, not per-character in `_is_wide_character()`
- **Validation in TTK**: `draw_hline()` and `draw_vline()` validate single-character input, preventing NFD characters (length > 1) from reaching `_is_wide_character()`

## Related Files

- `ttk/backends/coregraphics_backend.py` - CoreGraphics rendering implementation
- `ttk/backends/curses_backend.py` - Curses backend (NFD normalization added to draw_text)
- `src/tfm_wide_char_utils.py` - Width calculation utilities
  - `_is_wide_character()` - Internal function for wide character detection
  - `_cached_is_wide_character()` - Cached version used by `_is_wide_character()`
  - Note: `_is_wide_character` is internal-only and NOT included in fallback function dictionaries
- `test/test_nfd_normalization.py` - Test suite

## References

- Unicode Standard Annex #15: Unicode Normalization Forms
  https://unicode.org/reports/tr15/
  
- Apple Technical Note TN1150: HFS Plus Volume Format
  https://developer.apple.com/library/archive/technotes/tn/tn1150.html
  
- Python unicodedata module documentation
  https://docs.python.org/3/library/unicodedata.html

## Future Considerations

1. **Other backends**: If additional rendering backends are added, they should also normalize to NFC
2. **Performance monitoring**: Track cache hit rates to ensure normalization overhead is minimal
3. **Edge cases**: Monitor for any Unicode edge cases that may require special handling
