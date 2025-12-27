# Font Rendering Consistency Fix

## Problem

Font rendering appeared different between CLI mode (`python3 tfm.py --desktop`) and app bundle mode (`open TFM.app`):

- **Line spacing**: App bundle had noticeably more vertical space between lines
- **Window title bar**: App bundle had a taller title bar (32px vs 28px)
- **Overall appearance**: Text looked more spread out in app bundle

Both modes used identical configuration from `~/.tfm/config.py`, but the visual output was inconsistent.

## Root Cause

The CoreGraphics backend's `_calculate_char_dimensions()` method used `NSAttributedString.size()` to measure character height. This method returns the height including implicit paragraph style line spacing, which varies between execution contexts:

**CLI mode:**
- `NSAttributedString.size()` returned height = 14.00 pixels
- Font metrics (ascender - descender) = 13.97 pixels
- Difference: +0.03 pixels (minimal line spacing)

**App bundle mode:**
- `NSAttributedString.size()` returned height = 18.00 pixels
- Font metrics (ascender - descender) = 13.97 pixels  
- Difference: +4.03 pixels (significant extra line spacing!)

The 4-pixel difference in character height caused:
1. More vertical space between text lines
2. Different window dimensions for the same grid size
3. Inconsistent visual appearance

The title bar height difference (28px vs 32px) was a secondary effect of the different window dimensions being calculated from the inflated character height.

## Solution

Changed `_calculate_char_dimensions()` to use font metrics directly instead of relying on `NSAttributedString.size()`:

```python
# OLD: Used NSAttributedString.size() for both width and height
size = test_string.size()
self.char_width = int(size.width)
self.char_height = int(size.height)  # Inconsistent across contexts!

# NEW: Use font metrics for height
size = test_string.size()
metrics_height = self.font.ascender() - self.font.descender()
self.char_width = int(size.width)    # Still use NSAttributedString for width
self.char_height = int(metrics_height)  # Use font metrics for height
```

This approach:
- Uses `NSAttributedString.size().width` for character width (accurate for character advance)
- Uses `font.ascender() - font.descender()` for character height (consistent across contexts)
- Eliminates implicit line spacing that varies between execution environments
- Ensures box-drawing characters connect seamlessly (no gaps)

## Results

After the fix:
- **CLI and app bundle modes now render identically**
- Character height is consistent: ~14 pixels (from font metrics)
- Line spacing is consistent: no extra space
- Window title bar height is consistent
- Box-drawing characters connect properly in both modes

## Technical Details

### Why NSAttributedString.size() Varies

`NSAttributedString.size()` calculates the size needed to draw the attributed string, which includes:
1. The actual glyph bounds
2. Implicit paragraph style settings (line spacing, line height multiplier)
3. Layout manager defaults

These implicit settings can differ based on:
- Application bundle vs command-line execution context
- NSApplication initialization state
- System text rendering preferences
- macOS version and configuration

### Why Font Metrics Are Reliable

Font metrics (`ascender`, `descender`, `leading`) are intrinsic properties of the font file itself and don't vary based on execution context. They represent:
- **Ascender**: Distance from baseline to top of tallest glyph
- **Descender**: Distance from baseline to bottom of lowest glyph (negative value)
- **Leading**: Additional space between lines (typically 0 for monospace fonts)

For monospace terminal rendering, we want:
- Height = ascender - descender (no extra line spacing)
- This ensures characters fill their grid cells completely
- Box-drawing characters connect seamlessly

## Files Modified

- `ttk/backends/coregraphics_backend.py`: Updated `_calculate_char_dimensions()` method

## Testing

Verified the fix by:
1. Running CLI mode: `python3 tfm.py --desktop`
2. Running app bundle: `open macos_app/build/TFM.app`
3. Comparing visual appearance (line spacing, character height)
4. Verifying box-drawing characters connect properly
5. Checking window dimensions are consistent

## References

- Apple NSFont documentation: https://developer.apple.com/documentation/appkit/nsfont
- Apple NSAttributedString documentation: https://developer.apple.com/documentation/foundation/nsattributedstring
- Typography metrics: https://developer.apple.com/library/archive/documentation/TextFonts/Conceptual/CocoaTextArchitecture/FontHandling/FontHandling.html
