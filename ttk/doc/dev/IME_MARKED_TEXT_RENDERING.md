# IME Marked Text Rendering Implementation

## Overview

This document describes the implementation of IME (Input Method Editor) marked text rendering with background rectangles in the CoreGraphics backend. Marked text is the composition text shown while typing with an IME (e.g., Japanese, Chinese, Korean input methods).

The implementation uses the same font cascade and glyph layout logic as regular text rendering to ensure visual consistency.

## Visual Design

The marked text rendering provides visual feedback during IME composition:

1. **Background rectangles**: Each character in the marked text has a background rectangle
2. **Unselected portion**: Dark gray background (RGB 60, 60, 60)
3. **Selected portion**: Lighter gray background (RGB 100, 100, 100)
4. **Text**: White text with underline (standard IME appearance)
5. **Font cascade**: Uses the same font cascade as regular text for missing glyphs
6. **Glyph layout**: Proper glyph advance calculation and centering within cells
7. **Wide character support**: Correctly handles CJK double-width characters

## Architecture

### Python Layer (coregraphics_backend.py)

The Python backend extracts the marked text and selected range from the NSTextInputClient protocol:

```python
# Get marked text if present
marked_text = getattr(self, 'marked_text', None) or ""

# Get selected range within marked text (for IME)
selected_range = getattr(self, 'selected_range', None)
if selected_range is not None:
    selected_range_location = int(selected_range.location)
    selected_range_length = int(selected_range.length)
else:
    selected_range_location = 0
    selected_range_length = 0

# Pass to C++ renderer
self.backend._cpp_renderer.render_frame(
    # ... other parameters ...
    marked_text,
    selected_range_location,
    selected_range_length,
    # ... other parameters ...
)
```

### C++ Layer (coregraphics_render.cpp)

The C++ renderer implements the actual drawing using the same logic as regular text:

1. **Parameter parsing**: Accepts `marked_text`, `selected_range_location`, and `selected_range_length`
2. **UTF-8 to UTF-16 conversion**: Converts marked text to UniChar array
3. **Font cascade**: Tries base font first, then cascade list fonts for missing glyphs
4. **Glyph advance calculation**: Gets actual glyph advances from the font
5. **Wide character detection**: Detects CJK and other wide characters
6. **Background rendering**: Draws rectangles for each character position
7. **Glyph positioning**: Centers glyphs within cells using actual advances
8. **Text rendering**: Uses CTFontDrawGlyphs for proper rendering
9. **Underline drawing**: Draws underline below baseline

#### Key Implementation Details

```cpp
// Font cascade for missing glyphs (same as regular text)
bool all_glyphs_found = CTFontGetGlyphsForCharacters(base_font, characters.data(), glyphs.data(), length);

if (!all_glyphs_found) {
    // Try cascade list fonts
    CFArrayRef cascade_list = (CFArrayRef)CTFontDescriptorCopyAttribute(
        descriptor,
        kCTFontCascadeListAttribute
    );
    // ... iterate through cascade fonts ...
}

// Get actual glyph advances (same as regular text)
std::vector<CGSize> advances(length);
CTFontGetAdvancesForGlyphs(
    font_to_use,
    kCTFontOrientationHorizontal,
    glyphs.data(),
    advances.data(),
    length
);

// Wide character detection
bool is_wide = (ch >= 0x3000 && ch <= 0x9FFF) ||  // CJK
               (ch >= 0xAC00 && ch <= 0xD7AF) ||  // Hangul
               (ch >= 0xFF00 && ch <= 0xFFEF);    // Fullwidth

CGFloat cell_width = is_wide ? (char_width * 2.0f) : char_width;

// Center glyph within cell (same as regular text)
CGFloat centering_offset = (cell_width - glyph_advance) / 2.0f;
positions[i].x = glyph_x + centering_offset;
positions[i].y = baseline_y;

// Draw glyphs
CTFontDrawGlyphs(
    font_to_use,
    glyphs.data(),
    positions.data(),
    length,
    context
);
```

## Consistency with Regular Text

The marked text rendering now uses the exact same logic as regular text rendering:

1. **Font cascade**: Same cascade list and fallback logic
2. **Glyph advances**: Same CTFontGetAdvancesForGlyphs calculation
3. **Wide character detection**: Same detection logic for CJK characters
4. **Glyph centering**: Same centering within cells
5. **Rendering method**: Same CTFontDrawGlyphs for proper rendering

This ensures that marked text looks identical to committed text in terms of font, spacing, and alignment.

## Testing

To test the marked text rendering:

1. Run TFM in desktop mode: `python3 tfm.py --desktop`
2. Switch to an IME (e.g., Japanese Hiragana input)
3. Start typing - you should see:
   - Dark gray background for the composition text
   - Lighter gray background for the selected portion (if any)
   - White text with underline
   - Proper font cascade for missing glyphs
   - Correct spacing for wide characters
4. Press Space to convert - the selected portion should change
5. Press Enter to commit - the marked text should disappear

## Related Files

- `ttk/backends/coregraphics_backend.py`: Python backend implementation
- `ttk/backends/coregraphics_render.cpp`: C++ rendering implementation
- `ttk/demo/demo_marked_text_background.py`: Demo script for testing
