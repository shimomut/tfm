# Wide Character Utilities - TTK Developer Documentation

## Overview

The `ttk.wide_char_utils` module provides utilities for handling wide (double-width) Unicode characters, particularly East Asian characters (Chinese, Japanese, Korean). These utilities ensure proper display width calculation and text manipulation across both terminal and desktop backends.

## Purpose

Wide characters occupy 2 display columns instead of 1, which affects:
- Text alignment and padding
- Column width calculations
- Text truncation and wrapping
- Cursor positioning

This module provides backend-agnostic utilities that work consistently across TTK's curses and CoreGraphics backends.

## Core Functions

### Character Width Detection

```python
from ttk.wide_char_utils import _is_wide_character, get_display_width

# Check if a single character is wide
is_wide = _is_wide_character('あ')  # True
is_wide = _is_wide_character('A')   # False

# Calculate display width of a string
width = get_display_width("hello")      # 5
width = get_display_width("こんにちは")  # 10
width = get_display_width("hello世界")  # 9
```

### Text Manipulation

```python
from ttk.wide_char_utils import truncate_to_width, pad_to_width, split_at_width

# Truncate text to fit width
text = truncate_to_width("hello world", 8)  # "hello w…"

# Pad text to exact width
text = pad_to_width("test", 10, align='left')    # "test      "
text = pad_to_width("test", 10, align='right')   # "      test"
text = pad_to_width("test", 10, align='center')  # "   test   "

# Split text at width boundary
left, right = split_at_width("hello world", 6)  # ("hello ", "world")
```

### Safe Wrappers

All functions have safe wrapper versions that handle errors gracefully:

```python
from ttk.wide_char_utils import (
    safe_is_wide_character,
    safe_get_display_width,
    safe_truncate_to_width,
    safe_pad_to_width,
    safe_split_at_width
)

# These functions never raise exceptions, falling back to sensible defaults
width = safe_get_display_width(None)  # Returns 0
```

## Configuration

### Unicode Mode

The module supports three Unicode handling modes:

- **full**: Full Unicode support with wide character handling (default for desktop backends)
- **basic**: Basic Unicode but treats all characters as single-width
- **ascii**: ASCII-only fallback mode

```python
from ttk.wide_char_utils import set_unicode_mode

# Set mode explicitly
set_unicode_mode('full')
set_unicode_mode('auto')  # Auto-detect based on terminal capabilities
```

### Application Configuration

Applications can provide configuration by passing values as arguments:

```python
from ttk.wide_char_utils import initialize_from_config

# Initialize with explicit configuration values
initialize_from_config(
    unicode_mode='full',           # or 'basic', 'ascii', 'auto', None
    force_fallback=False,          # Force ASCII mode if True
    show_warnings=True,            # Show Unicode warnings
    terminal_detection=True,       # Auto-detect terminal support
    fallback_char='?'              # Character for unrepresentable chars
)

# Or use defaults (all parameters are optional)
initialize_from_config()
```

Note: Caching is always enabled via `@lru_cache` decorators and cannot be disabled at runtime. The cache is automatically cleared when `initialize_from_config()` is called to ensure fresh behavior with new settings.

## Backend Integration

### General Pattern

TTK backends should not need to interact with wide character utilities directly. Applications using TTK should configure the Unicode mode based on their needs:

```python
from ttk.wide_char_utils import set_unicode_mode

# Desktop applications
set_unicode_mode('full')

# Terminal applications
set_unicode_mode('auto')  # Auto-detects terminal capabilities
```

### CoreGraphics Backend

The CoreGraphics backend imports and uses `_is_wide_character` directly:

```python
from ttk.wide_char_utils import _is_wide_character

# In draw_text()
for char in text:
    is_wide = _is_wide_character(char)
    # Store is_wide flag with character in grid
```

### Curses Backend

The curses backend can use the utilities for text layout calculations but relies on curses' built-in wide character support for rendering.

## Performance Optimization

The module uses LRU caching for performance:

```python
from ttk.wide_char_utils import clear_display_width_cache, get_cache_info

# Get cache statistics
stats = get_cache_info()
print(stats['display_width_cache'])
print(stats['is_wide_char_cache'])

# Clear caches to free memory
clear_display_width_cache()
```

## Migration from TFM

The wide character utilities were moved from TFM to TTK because:

1. **Common utility**: Multiple TTK-based applications need wide character support
2. **Backend consistency**: TTK should ensure width calculations match rendering behavior
3. **Reduced redundancy**: Eliminates duplicate implementations (e.g., CoreGraphics backend had its own `_is_wide_character`)

### For TFM Developers

TFM maintains a compatibility shim at `src/tfm_wide_char_utils.py` that re-exports all functions from TTK. Existing TFM code continues to work without changes:

```python
# Old import (still works via shim)
from tfm_wide_char_utils import get_display_width

# New import (recommended for new code)
from ttk.wide_char_utils import get_display_width
```

### For New TTK Applications

Import directly from TTK:

```python
from ttk.wide_char_utils import (
    get_display_width,
    truncate_to_width,
    pad_to_width,
    set_unicode_mode
)

# Set Unicode mode based on your application's needs
set_unicode_mode('full')  # For desktop applications
set_unicode_mode('auto')  # For terminal applications (auto-detect)
```

## Testing

The module includes comprehensive tests at `ttk/test/test_wide_char_utils.py`:

```bash
PYTHONPATH=.:ttk python3 -m pytest ttk/test/test_wide_char_utils.py -v
```

## References

- **Unicode East Asian Width**: UAX #11 (https://unicode.org/reports/tr11/)
- **NFC Normalization**: Handles macOS NFD decomposition correctly
- **TTK Backends**: `ttk/backends/coregraphics_backend.py`, `ttk/backends/curses_backend.py`
