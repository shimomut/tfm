# CoreGraphics Backend Color Pair Management Implementation

## Overview

This document describes the implementation of color pair management for the CoreGraphics backend. Color pairs are used to specify foreground and background colors for text rendering in TTK applications.

## Implementation Summary

The color pair management system provides:
- Storage of RGB color pairs in a dictionary
- Validation of color pair IDs (1-255)
- Validation of RGB components (0-255)
- Default color pair (0) for white on black
- Support for 256 total color pairs (0-255)

## Data Structure

### Color Pair Storage

Color pairs are stored in a dictionary attribute of the `CoreGraphicsBackend` class:

```python
self.color_pairs: Dict[int, Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = {}
```

**Structure:**
- Key: Color pair ID (integer, 0-255)
- Value: Tuple of (foreground_rgb, background_rgb)
  - Each RGB is a tuple of (r, g, b) with values 0-255

**Example:**
```python
# Color pair 1: White text on blue background
color_pairs[1] = ((255, 255, 255), (0, 0, 255))

# Color pair 2: Red text on black background
color_pairs[2] = ((255, 0, 0), (0, 0, 0))
```

### Default Color Pair

Color pair 0 is reserved for default colors and is initialized during backend initialization:

```python
# In initialize() method
self.color_pairs[0] = ((255, 255, 255), (0, 0, 0))  # White on black
```

This default pair cannot be modified through `init_color_pair()` as it validates that pair_id >= 1.

## Method Implementation

### init_color_pair()

The `init_color_pair()` method initializes or updates a color pair with RGB values.

**Signature:**
```python
def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                   bg_color: Tuple[int, int, int]) -> None
```

**Parameters:**
- `pair_id`: Color pair ID (must be 1-255)
- `fg_color`: Foreground RGB color as (r, g, b) tuple (0-255 each)
- `bg_color`: Background RGB color as (r, g, b) tuple (0-255 each)

**Validation Steps:**

1. **Color Pair ID Validation:**
   ```python
   if pair_id < 1 or pair_id > 255:
       raise ValueError(
           f"Color pair ID must be 1-255, got {pair_id}. "
           f"Color pair 0 is reserved for default colors."
       )
   ```

2. **Foreground RGB Validation:**
   ```python
   for component in fg_color:
       if component < 0 or component > 255:
           raise ValueError(
               f"RGB components must be 0-255, got {component} in foreground color"
           )
   ```

3. **Background RGB Validation:**
   ```python
   for component in bg_color:
       if component < 0 or component > 255:
           raise ValueError(
               f"RGB components must be 0-255, got {component} in background color"
           )
   ```

4. **Storage:**
   ```python
   self.color_pairs[pair_id] = (fg_color, bg_color)
   ```

**Error Handling:**

The method raises `ValueError` with descriptive messages for:
- Color pair ID < 1 or > 255
- Any RGB component < 0 or > 255
- Separate error messages for foreground vs background validation

## Usage in Rendering

Color pairs are used during rendering in the `TTKView.drawRect_()` method:

```python
# Get foreground and background colors from color pair
if color_pair in self.backend.color_pairs:
    fg_rgb, bg_rgb = self.backend.color_pairs[color_pair]
else:
    # Use default colors if color pair not found
    fg_rgb, bg_rgb = self.backend.color_pairs[0]

# Handle reverse video attribute by swapping colors
if attributes & TextAttribute.REVERSE:
    fg_rgb, bg_rgb = bg_rgb, fg_rgb

# Create NSColor objects for rendering
bg_color = Cocoa.NSColor.colorWithRed_green_blue_alpha_(
    bg_rgb[0] / 255.0,
    bg_rgb[1] / 255.0,
    bg_rgb[2] / 255.0,
    1.0
)

fg_color = Cocoa.NSColor.colorWithRed_green_blue_alpha_(
    fg_rgb[0] / 255.0,
    fg_rgb[1] / 255.0,
    fg_rgb[2] / 255.0,
    1.0
)
```

## Requirements Validation

This implementation satisfies the following requirements:

### Requirement 4.1 - Color Pair Storage
✓ Color pairs are stored with RGB values for foreground and background colors
✓ Dictionary structure allows efficient lookup by pair ID

### Requirement 4.2 - 256 Color Pair Support
✓ Supports color pair IDs 0-255 (256 total pairs)
✓ All valid IDs can be initialized and stored

### Requirement 12.3 - Color Pair ID Validation
✓ Validates color pair IDs are in range 1-255
✓ Raises ValueError with clear error message for out-of-range IDs
✓ Includes valid range information in error message

## Testing

### Unit Tests

The implementation is tested in `test/test_coregraphics_color_management.py`:

**Test Coverage:**
- ✓ Color pair storage and retrieval
- ✓ Multiple color pairs
- ✓ Color pair overwriting
- ✓ Default color pair (0) existence
- ✓ Color pair ID validation (too low, too high)
- ✓ Foreground RGB validation (negative, too high)
- ✓ Background RGB validation (negative, too high)
- ✓ Boundary value testing (0, 255)
- ✓ All valid IDs (1-255) can be initialized

**Test Results:**
```
12 passed in 5.92s
```

### Verification Script

The verification script `test/verify_coregraphics_color_management.py` demonstrates:
- Single and multiple color pair storage
- Default color pair verification
- Color pair ID validation
- RGB component validation
- Color pair overwriting
- All 255 valid IDs initialization

## Design Decisions

### Dictionary Storage

**Decision:** Use a dictionary to store color pairs rather than a list or array.

**Rationale:**
- Efficient O(1) lookup by pair ID
- Sparse storage (only stores initialized pairs)
- Natural mapping from ID to color values
- Easy to check if a pair exists

### Separate Foreground/Background Validation

**Decision:** Validate foreground and background RGB components separately with distinct error messages.

**Rationale:**
- Clearer error messages for debugging
- Helps developers identify which color (fg or bg) has invalid values
- Follows principle of providing actionable error information

### Reserved Color Pair 0

**Decision:** Reserve color pair 0 for default colors and prevent modification.

**Rationale:**
- Ensures a fallback color pair always exists
- Matches curses backend convention
- Provides consistent default behavior
- Prevents accidental modification of defaults

### RGB Range 0-255

**Decision:** Use 0-255 range for RGB components rather than 0.0-1.0 floats.

**Rationale:**
- Matches standard RGB color representation
- Easier for developers to specify colors
- Consistent with curses backend API
- Conversion to NSColor's 0.0-1.0 range happens internally

## Performance Considerations

### Storage Efficiency

- Dictionary storage is memory-efficient for sparse color pair usage
- Only initialized color pairs consume memory
- Typical applications use 10-20 color pairs, not all 256

### Lookup Performance

- O(1) dictionary lookup during rendering
- No performance impact from validation (only during initialization)
- Color pair lookup happens once per non-empty cell during rendering

## Future Enhancements

### Potential Improvements

1. **Color Pair Caching:**
   - Cache NSColor objects to avoid repeated creation
   - Would improve rendering performance for frequently used colors

2. **Color Validation:**
   - Add validation for color contrast (accessibility)
   - Warn about low-contrast color combinations

3. **Color Schemes:**
   - Support for predefined color schemes
   - Easy switching between light/dark themes

4. **Extended Color Support:**
   - Support for alpha channel (transparency)
   - Support for color spaces beyond RGB

## Related Documentation

- [CoreGraphics Backend Design](../../.kiro/specs/coregraphics-backend/design.md)
- [CoreGraphics Backend Requirements](../../.kiro/specs/coregraphics-backend/requirements.md)
- [TTK API Reference](../API_REFERENCE.md)

## References

- Requirements: 4.1, 4.2, 12.3
- Design Properties: Property 4 (Color Pair Storage Integrity), Property 15 (Color Pair Range Validation)
- Test File: `test/test_coregraphics_color_management.py`
- Verification Script: `test/verify_coregraphics_color_management.py`
