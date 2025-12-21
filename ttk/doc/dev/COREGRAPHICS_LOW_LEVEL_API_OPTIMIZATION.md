# CoreGraphics Low-Level API Optimization

## Overview

The CoreGraphics backend has been optimized to use low-level CoreGraphics and CoreText APIs instead of high-level NS (Cocoa) APIs. This optimization reduces overhead from the Cocoa wrapper layer and improves rendering performance.

## Problem Statement

The original implementation used high-level Cocoa APIs:
- `NSRectFill()` for drawing background rectangles
- `NSAttributedString.drawAtPoint_()` for drawing text
- `NSColor.setFill()` for setting fill colors

While these APIs are convenient and easy to use, they add overhead through the Cocoa wrapper layer. Each call involves:
1. Objective-C method dispatch
2. NSColor object creation and management
3. NSAttributedString layout and rendering overhead
4. Additional abstraction layers

For a terminal application rendering 1,920 cells per frame (24x80 grid), this overhead accumulates significantly.

## Solution

Replace high-level NS APIs with low-level CoreGraphics and CoreText APIs:

### 1. Background Rendering: NSRectFill → CGContextFillRect

**Before:**
```python
bg_color = self.backend._color_cache.get_color(*batch.bg_rgb)
bg_color.setFill()
batch_rect = Cocoa.NSMakeRect(batch.x, batch.y, batch.width, batch.height)
Cocoa.NSRectFill(batch_rect)
```

**After:**
```python
context = Cocoa.NSGraphicsContext.currentContext().CGContext()
r, g, b = batch.bg_rgb
Quartz.CGContextSetRGBFillColor(context, r/255.0, g/255.0, b/255.0, 1.0)
batch_rect = Quartz.CGRectMake(batch.x, batch.y, batch.width, batch.height)
Quartz.CGContextFillRect(context, batch_rect)
```

**Benefits:**
- Eliminates NSColor object creation overhead
- Direct color setting with normalized RGB values
- Fewer method calls and object allocations

### 2. Text Rendering: NSAttributedString.drawAtPoint_ → CTLineDraw

**Before:**
```python
attr_string = self.backend._attr_string_cache.get_attributed_string(
    char, font_key, start_fg_rgb, has_underline
)
attr_string.drawAtPoint_(Cocoa.NSMakePoint(x_pos, y))
```

**After:**
```python
context = Cocoa.NSGraphicsContext.currentContext().CGContext()

# Concatenate all characters in the batch into a single string
batch_text = ''.join(batch_chars)
x_pos = start_col_batch * char_width + offset_x

# Get cached NSAttributedString for the entire batch
attr_string = self.backend._attr_string_cache.get_attributed_string(
    batch_text, font_key, start_fg_rgb, has_underline
)
line = CTLineCreateWithAttributedString(attr_string)

# CTLineDraw uses baseline positioning, adjust y coordinate
baseline_y = y + (char_height - self.backend.font_ascent)

Quartz.CGContextSaveGState(context)
Quartz.CGContextSetTextPosition(context, x_pos, baseline_y)
CTLineDraw(line, context)  # Draw entire batch in one call
Quartz.CGContextRestoreGState(context)
```

**Benefits:**
- Direct CoreText rendering without NSAttributedString overhead
- Batch rendering: draws multiple characters with same attributes in one call
- Significantly reduces CTLineDraw calls (from ~1920 to ~50-200 per frame)
- Better performance for repeated character drawing

**Important Note:**
CTLineDraw uses baseline positioning (where the baseline is the reference point for text),
while NSAttributedString.drawAtPoint_ uses top-left corner positioning. The y-coordinate
is adjusted using: `baseline_y = y + (char_height - font_ascent)` where:
- `y` is the bottom of the cell in CoreGraphics coordinates
- `char_height - font_ascent` is the distance from cell bottom to baseline

### 3. Attribute Dictionary: NS Constants → CoreText Constants

**Before:**
```python
text_attributes = {
    Cocoa.NSFontAttributeName: font,
    Cocoa.NSForegroundColorAttributeName: color
}
if underline:
    text_attributes[Cocoa.NSUnderlineStyleAttributeName] = Cocoa.NSUnderlineStyleSingle
```

**After:**
```python
text_attributes = {
    kCTFontAttributeName: font,
    kCTForegroundColorAttributeName: color.CGColor()
}
if underline:
    text_attributes[kCTUnderlineStyleAttributeName] = kCTUnderlineStyleSingle
```

**Benefits:**
- Uses CoreText constants directly (kCT* instead of NS*)
- CGColor instead of NSColor for better CoreGraphics integration
- Reduced conversion overhead between Cocoa and CoreGraphics

## Implementation Details

### Import Changes

Added CoreText imports at module level:

```python
from CoreText import (
    CTLineCreateWithAttributedString,
    CTLineDraw,
    kCTFontAttributeName,
    kCTForegroundColorAttributeName,
    kCTUnderlineStyleAttributeName,
    kCTUnderlineStyleSingle
)
```

### Context Management

All low-level drawing operations require a CoreGraphics context:

```python
context = Cocoa.NSGraphicsContext.currentContext().CGContext()
```

This context is obtained once per drawing phase and reused for all operations in that phase.

### State Management

CoreGraphics requires explicit state management:

```python
Quartz.CGContextSaveGState(context)
# ... drawing operations ...
Quartz.CGContextRestoreGState(context)
```

This ensures that state changes (like text position) don't affect subsequent drawing operations.

### Color Conversion

CoreGraphics uses normalized color values (0.0-1.0) instead of 0-255:

```python
# Convert RGB (0-255) to normalized values (0.0-1.0)
Quartz.CGContextSetRGBFillColor(context, r/255.0, g/255.0, b/255.0, 1.0)
```

### CGColor vs NSColor

CoreText attributes require CGColor instead of NSColor:

```python
# Get NSColor from cache
color = self._color_cache.get_color(*color_rgb)

# Convert to CGColor for CoreText
kCTForegroundColorAttributeName: color.CGColor()
```

### Baseline Positioning

CTLineDraw uses baseline positioning, while NSAttributedString.drawAtPoint_ uses top-left corner positioning:

```python
# Calculate font ascent during initialization
self.font_ascent = self.font.ascender()

# Adjust y-coordinate for baseline positioning
baseline_y = y + (char_height - self.font_ascent)
Quartz.CGContextSetTextPosition(context, x_pos, baseline_y)
```

**Why this matters:**
- NSAttributedString.drawAtPoint_ positions text by its top-left corner
- CTLineDraw positions text by its baseline (the line where letters sit)
- In CoreGraphics coordinates (bottom-left origin), `y` is the bottom of the cell
- The baseline is at: `y + (char_height - font_ascent)`
- This accounts for the descender space below the baseline

### Batch Text Rendering

Characters with the same attributes are concatenated and drawn in a single CTLineDraw call:

```python
# Concatenate batch characters into a single string
batch_text = ''.join(batch_chars)

# Get attributed string for the entire batch
attr_string = cache.get_attributed_string(batch_text, font_key, color, underline)

# Draw entire batch with one CTLineDraw call
line = CTLineCreateWithAttributedString(attr_string)
CTLineDraw(line, context)
```

**Performance impact:**
- Reduces CTLineDraw calls from ~1920 to ~50-200 per frame
- Eliminates per-character overhead
- Better cache utilization for repeated strings

## Performance Impact

### Expected Improvements

1. **Background Rendering**: 10-20% faster
   - Eliminates NSColor object creation
   - Direct CoreGraphics API calls
   - Fewer method dispatches

2. **Text Rendering**: 20-35% faster
   - Direct CoreText rendering
   - Batch rendering: multiple characters in one CTLineDraw call
   - Significantly reduces API calls (from ~1920 to ~50-200 per frame)
   - Reduced NSAttributedString overhead
   - Better cache utilization

3. **Overall Frame Time**: 25-45% reduction
   - Cumulative effect of all optimizations
   - Dramatically fewer API calls
   - More efficient use of CoreGraphics pipeline
   - Reduced memory allocations

### Measurement

Performance can be measured using:
- Frame time profiling with `demo_profiling.py`
- Character drawing metrics with `get_character_drawing_metrics()`
- macOS Instruments for detailed profiling

## Compatibility

### Requirements

- macOS operating system
- PyObjC framework with CoreText support
- Python 3.7 or later

### Backward Compatibility

The optimization is transparent to applications using the CoreGraphics backend:
- Same public API
- Same rendering quality
- Same behavior and features

### Testing

The `demo_coregraphics_low_level_api.py` script verifies:
- Background rendering with CGContextFillRect
- Text rendering with CTLineDraw
- Color setting with CGContextSetRGBFillColor
- Wide character support
- Attribute handling (bold, underline)

## Trade-offs

### Advantages

1. **Performance**: Significant reduction in rendering overhead
2. **Efficiency**: Fewer object allocations and method calls
3. **Control**: More direct control over rendering pipeline
4. **Quality**: Same or better rendering quality

### Disadvantages

1. **Complexity**: More verbose code with explicit state management
2. **Maintenance**: Requires understanding of CoreGraphics/CoreText APIs
3. **Debugging**: Lower-level APIs can be harder to debug

## Future Enhancements

Potential further optimizations:

1. **Batch Text Rendering**: Draw multiple characters in a single CTLineDraw call
   - Currently draws each character individually for alignment
   - Could batch characters with same attributes on same row
   - Would require careful position calculation

2. **GPU Acceleration**: Use Metal for rendering
   - CoreGraphics is CPU-based
   - Metal could provide GPU acceleration
   - Would require significant refactoring

3. **Glyph Caching**: Cache CTGlyph objects
   - Currently creates CTLine for each character
   - Could cache glyphs for frequently used characters
   - Would reduce CoreText overhead

4. **Direct CGFont Usage**: Use CGFont instead of NSFont
   - Would eliminate NSFont → CTFont conversion
   - More complex font management
   - Potentially better performance

## References

- **CoreGraphics Programming Guide**: Apple's documentation on CoreGraphics
- **CoreText Programming Guide**: Apple's documentation on CoreText
- **Quartz 2D Programming Guide**: Low-level 2D graphics on macOS
- **PyObjC Documentation**: Python-Objective-C bridge documentation
- **TTK Renderer API**: Abstract renderer interface specification

## Related Documentation

- `COREGRAPHICS_BACKEND_IMPLEMENTATION.md`: Overall backend architecture
- `CHARACTER_DRAWING_OPTIMIZATION.md`: Character batching and caching
- `WINDOW_RESIZE_SNAPPING_IMPLEMENTATION.md`: Window management features
