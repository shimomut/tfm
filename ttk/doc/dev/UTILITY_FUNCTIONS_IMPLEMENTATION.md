# TTK Utility Functions Implementation

## Overview

This document describes the implementation of utility functions in the TTK library. These functions provide platform detection, color conversion, and parameter validation capabilities that are used throughout the library.

## Implementation Location

- **Module**: `ttk/utils/utils.py`
- **Public API**: Exported through `ttk/utils/__init__.py`
- **Tests**: `ttk/test/test_utils.py`
- **Demo**: `ttk/test/demo_utils.py`

## Platform Detection

### `get_recommended_backend() -> str`

Returns the recommended rendering backend for the current platform.

**Implementation Details:**
- Uses Python's `platform.system()` to detect the operating system
- Returns `'metal'` for macOS (Darwin)
- Returns `'curses'` for all other platforms (Linux, Windows, etc.)

**Usage Example:**
```python
from ttk.utils import get_recommended_backend

backend_name = get_recommended_backend()
if backend_name == 'metal':
    from ttk.backends.metal_backend import MetalBackend
    renderer = MetalBackend()
else:
    from ttk.backends.curses_backend import CursesBackend
    renderer = CursesBackend()
```

**Design Rationale:**
- Provides a simple, platform-agnostic way to select the appropriate backend
- Encapsulates platform detection logic in one place
- Makes it easy to add support for new platforms in the future

## Color Conversion Functions

### `rgb_to_normalized(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]`

Converts RGB values from 0-255 range to normalized 0.0-1.0 range.

**Implementation Details:**
- Validates input using `validate_rgb()`
- Divides each component by 255.0
- Returns tuple of floats

**Use Cases:**
- Metal backend rendering (Metal uses normalized colors)
- Graphics APIs that expect normalized color values
- Color interpolation calculations

### `normalized_to_rgb(normalized: Tuple[float, float, float]) -> Tuple[int, int, int]`

Converts normalized color values from 0.0-1.0 range to RGB 0-255 range.

**Implementation Details:**
- Validates that all components are in 0.0-1.0 range
- Multiplies each component by 255 and converts to int
- Returns tuple of integers

**Use Cases:**
- Converting Metal backend colors back to RGB
- Processing color calculations that use normalized values

### `rgb_to_hex(rgb: Tuple[int, int, int]) -> str`

Converts RGB color to hexadecimal string representation.

**Implementation Details:**
- Validates input using `validate_rgb()`
- Formats each component as 2-digit uppercase hexadecimal
- Returns string in format `#RRGGBB`

**Use Cases:**
- Debugging and logging color values
- Exporting color schemes
- Integration with web-based tools

### `hex_to_rgb(hex_color: str) -> Tuple[int, int, int]`

Converts hexadecimal color string to RGB tuple.

**Implementation Details:**
- Strips leading `#` if present
- Validates string length (must be 6 characters)
- Parses each pair of characters as hexadecimal
- Handles both uppercase and lowercase hex digits
- Returns tuple of integers

**Use Cases:**
- Importing color schemes from configuration files
- Parsing user-provided color values
- Integration with web-based tools

### Round-Trip Guarantee

The color conversion functions guarantee round-trip consistency:
```python
original = (255, 128, 64)
hex_color = rgb_to_hex(original)
result = hex_to_rgb(hex_color)
assert result == original  # Always true
```

## Parameter Validation Functions

### `validate_rgb(rgb: Tuple[int, int, int]) -> None`

Validates that RGB color values are in the valid range 0-255.

**Implementation Details:**
- Checks that input is a tuple of exactly 3 elements
- Checks that all elements are integers
- Checks that all values are in range 0-255
- Raises `TypeError` for type errors
- Raises `ValueError` for range errors

**Error Messages:**
- Clear, descriptive error messages that include the invalid values
- Helps developers quickly identify and fix issues

### `validate_color_pair_id(pair_id: int) -> None`

Validates that a color pair ID is in the valid range 0-255.

**Implementation Details:**
- Checks that input is an integer
- Checks that value is in range 0-255
- Color pair 0 is reserved for default colors
- Raises `TypeError` for type errors
- Raises `ValueError` for range errors

**Design Note:**
- Matches curses color pair limitations (256 pairs)
- Ensures consistency across backends

### `validate_coordinates(row: int, col: int) -> None`

Validates that coordinates are non-negative integers.

**Implementation Details:**
- Checks that both row and col are integers
- Checks that both values are >= 0
- Raises `TypeError` for type errors
- Raises `ValueError` for negative values

**Design Rationale:**
- Coordinates use 0-based indexing with (0, 0) at top-left
- Negative coordinates are never valid in the character grid system

### `validate_dimensions(width: int, height: int) -> None`

Validates that dimensions are positive integers.

**Implementation Details:**
- Checks that both width and height are integers
- Checks that both values are > 0 (not just >= 0)
- Raises `TypeError` for type errors
- Raises `ValueError` for zero or negative values

**Design Rationale:**
- Zero-sized rectangles or regions are meaningless
- Enforces positive dimensions to prevent logic errors

## Clamping Functions

### `clamp(value: int, min_value: int, max_value: int) -> int`

Clamps a value to be within a specified range.

**Implementation Details:**
- Returns `max(min_value, min(value, max_value))`
- Simple, efficient implementation
- Works with any comparable types (though typed for int)

**Use Cases:**
- Ensuring values stay within valid bounds
- Preventing overflow in calculations
- Implementing safe arithmetic operations

### `clamp_rgb(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]`

Clamps RGB values to valid 0-255 range.

**Implementation Details:**
- Applies `clamp()` to each component independently
- Returns new tuple with clamped values
- Does not validate input (accepts any integers)

**Use Cases:**
- Color calculations that might overflow (brightness adjustments)
- Blending operations
- Safe color arithmetic without exceptions

**Example:**
```python
# Brightness adjustment that might overflow
base_color = (200, 150, 100)
brightness_boost = 100
result = clamp_rgb(tuple(c + brightness_boost for c in base_color))
# result = (255, 250, 200) - safely clamped
```

## Error Handling Strategy

### Validation vs. Clamping

The library provides both validation and clamping functions:

**Validation Functions:**
- Raise exceptions for invalid input
- Use when input should always be valid
- Helps catch bugs early in development
- Examples: `validate_rgb()`, `validate_coordinates()`

**Clamping Functions:**
- Silently fix out-of-range values
- Use when overflow is expected/acceptable
- Prevents crashes in production
- Examples: `clamp()`, `clamp_rgb()`

**When to Use Each:**
- **Validation**: For API boundaries, user input, configuration
- **Clamping**: For internal calculations, color arithmetic, safe operations

### Exception Types

The validation functions use appropriate exception types:

- `TypeError`: Wrong type (e.g., float instead of int, list instead of tuple)
- `ValueError`: Wrong value (e.g., out of range, negative when positive required)

This follows Python conventions and makes error handling predictable.

## Testing Strategy

### Unit Tests

The utility functions have comprehensive unit tests covering:

1. **Platform Detection:**
   - Returns valid backend name
   - Correct backend for each platform (mocked)

2. **Color Conversion:**
   - Basic conversions (black, white, primary colors)
   - Mid-range values
   - Round-trip consistency
   - Invalid input handling
   - Edge cases (0, 255, boundaries)

3. **Validation:**
   - Valid inputs pass without exception
   - Invalid ranges raise ValueError
   - Invalid types raise TypeError
   - Error messages are descriptive

4. **Clamping:**
   - Values within range unchanged
   - Values below range clamped to minimum
   - Values above range clamped to maximum
   - RGB clamping works component-wise

### Test Coverage

All utility functions have 100% code coverage, including:
- Normal operation paths
- Error handling paths
- Edge cases and boundary conditions

## Performance Considerations

### Efficiency

The utility functions are designed for efficiency:

1. **Simple Operations:**
   - Color conversions are simple arithmetic
   - Validation is straightforward checks
   - No complex algorithms or data structures

2. **No Caching:**
   - Functions are pure (no side effects)
   - Results are not cached (not needed for simple operations)
   - Each call is independent

3. **Minimal Overhead:**
   - Validation adds minimal overhead
   - Clamping is a simple min/max operation
   - Platform detection is called once at startup

### When to Skip Validation

In performance-critical inner loops, you may skip validation:

```python
# Outside loop: validate once
validate_rgb(base_color)

# Inside loop: skip validation for performance
for i in range(1000):
    # Direct operations without validation
    r, g, b = base_color
    # ... fast operations ...
```

However, this should only be done when profiling shows validation is a bottleneck.

## Integration with Other Components

### Backend Usage

Both backends use utility functions:

**Curses Backend:**
- Uses `validate_rgb()` in `init_color_pair()`
- Uses `validate_coordinates()` in drawing operations
- Uses `validate_color_pair_id()` for color pair management

**Metal Backend:**
- Uses `rgb_to_normalized()` for Metal color conversion
- Uses `validate_rgb()` in `init_color_pair()`
- Uses `validate_coordinates()` in drawing operations
- Uses `clamp_rgb()` for safe color calculations

### Serialization Usage

Command serialization uses validation:
- Validates parameters before serialization
- Ensures only valid commands are serialized
- Prevents invalid commands from being parsed

## Future Enhancements

### Potential Additions

1. **Color Space Conversions:**
   - HSV/HSL color space support
   - Color temperature conversions
   - Gamma correction utilities

2. **Advanced Validation:**
   - Range validation with custom bounds
   - Validation decorators for functions
   - Batch validation for multiple values

3. **Color Utilities:**
   - Color blending functions
   - Color distance calculations
   - Palette generation utilities

4. **Platform Detection:**
   - More granular platform detection
   - Version detection for platform-specific features
   - Capability detection (GPU, terminal features)

### Backward Compatibility

Any future additions will maintain backward compatibility:
- Existing functions will not change signatures
- New functions will be added alongside existing ones
- Deprecation warnings before removing old functions

## Related Documentation

- **User Guide**: See `ttk/doc/API_REFERENCE.md` for public API documentation
- **Backend Implementation**: See `ttk/doc/dev/CURSES_BACKEND_IMPLEMENTATION.md` and `ttk/doc/dev/METAL_BACKEND_IMPLEMENTATION.md`
- **Testing**: See `ttk/test/test_utils.py` for test examples
- **Demo**: Run `python ttk/test/demo_utils.py` for interactive demonstration

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 16.1**: Generic library naming and terminology
- **Requirement 16.2**: Platform-agnostic API design
- **Requirement 7.1**: Color pair initialization support
- **Requirement 8.5**: Graceful handling of out-of-bounds operations

The utility functions provide essential infrastructure for the TTK library while maintaining simplicity, efficiency, and ease of use.
