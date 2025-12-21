#!/usr/bin/env python3
"""
Visual equivalence testing for C++ rendering backend.

This test harness renders the same content using both PyObjC and C++ implementations
to offscreen bitmap contexts, then compares the pixel data to verify visual equivalence.

Requirements tested:
- 13.2: Compare images pixel-by-pixel and calculate difference percentage
- 13.3: Render with PyObjC and C++ to CGBitmapContext
"""

import sys
import os
import struct

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check if we're on macOS
try:
    import Cocoa
    import Quartz
    from CoreText import (
        CTLineCreateWithAttributedString,
        CTLineDraw
    )
    MACOS_AVAILABLE = True
except ImportError:
    MACOS_AVAILABLE = False
    print("Warning: PyObjC not available, skipping visual equivalence tests")


class OffscreenRenderer:
    """
    Harness for rendering to offscreen bitmap contexts.
    
    This class creates CGBitmapContext objects that can be used for rendering
    without displaying on screen, allowing pixel-perfect comparison between
    PyObjC and C++ rendering implementations.
    """
    
    def __init__(self, width, height):
        """
        Initialize offscreen renderer.
        
        Args:
            width: Width in pixels
            height: Height in pixels
        """
        self.width = width
        self.height = height
        self.bytes_per_pixel = 4  # RGBA
        self.bytes_per_row = width * self.bytes_per_pixel
        self.buffer_size = height * self.bytes_per_row
        
    def create_bitmap_context(self):
        """
        Create a CGBitmapContext for offscreen rendering.
        
        Returns:
            CGContextRef: Bitmap context for rendering
            bytearray: Buffer containing pixel data
        """
        if not MACOS_AVAILABLE:
            return None, None
            
        # Create buffer for pixel data
        buffer = bytearray(self.buffer_size)
        
        # Create color space (sRGB)
        color_space = Quartz.CGColorSpaceCreateWithName(Quartz.kCGColorSpaceSRGB)
        
        # Create bitmap context
        # Format: RGBA, 8 bits per component, premultiplied alpha
        context = Quartz.CGBitmapContextCreate(
            buffer,                                    # data
            self.width,                                # width
            self.height,                               # height
            8,                                         # bitsPerComponent
            self.bytes_per_row,                        # bytesPerRow
            color_space,                               # colorSpace
            Quartz.kCGImageAlphaPremultipliedLast     # bitmapInfo
        )
        
        if context is None:
            raise RuntimeError("Failed to create CGBitmapContext")
        
        # Fill with black background
        Quartz.CGContextSetRGBFillColor(context, 0.0, 0.0, 0.0, 1.0)
        Quartz.CGContextFillRect(context, Quartz.CGRectMake(0, 0, self.width, self.height))
        
        return context, buffer
    
    def render_with_pyobjc(self, grid, color_pairs, char_width, char_height, 
                          rows, cols, cursor_visible=False, cursor_row=0, 
                          cursor_col=0, marked_text=None):
        """
        Render using PyObjC implementation.
        
        Args:
            grid: 2D list of (char, color_pair, attributes) tuples
            color_pairs: Dict mapping pair ID to ((r,g,b), (r,g,b)) tuples
            char_width: Character width in pixels
            char_height: Character height in pixels
            rows: Number of rows
            cols: Number of columns
            cursor_visible: Whether cursor is visible
            cursor_row: Cursor row position
            cursor_col: Cursor column position
            marked_text: IME marked text (optional)
            
        Returns:
            bytearray: Pixel data buffer
        """
        if not MACOS_AVAILABLE:
            return None
            
        context, buffer = self.create_bitmap_context()
        
        # Render using PyObjC implementation
        self._render_pyobjc_impl(
            context, grid, color_pairs, char_width, char_height,
            rows, cols, cursor_visible, cursor_row, cursor_col, marked_text
        )
        
        return buffer
    
    def render_with_cpp(self, grid, color_pairs, char_width, char_height,
                       rows, cols, cursor_visible=False, cursor_row=0,
                       cursor_col=0, marked_text=None):
        """
        Render using C++ implementation.
        
        Args:
            grid: 2D list of (char, color_pair, attributes) tuples
            color_pairs: Dict mapping pair ID to ((r,g,b), (r,g,b)) tuples
            char_width: Character width in pixels
            char_height: Character height in pixels
            rows: Number of rows
            cols: Number of columns
            cursor_visible: Whether cursor is visible
            cursor_row: Cursor row position
            cursor_col: Cursor column position
            marked_text: IME marked text (optional)
            
        Returns:
            bytearray: Pixel data buffer
        """
        if not MACOS_AVAILABLE:
            return None
            
        try:
            import cpp_renderer
        except ImportError:
            print("Warning: cpp_renderer not available")
            return None
        
        context, buffer = self.create_bitmap_context()
        
        # Convert CGContext to integer pointer for C++
        # Use objc module to get the pointer value
        import objc
        context_ptr = objc.pyobjc_id(context)
        
        # Render using C++ implementation
        dirty_rect = (0.0, 0.0, float(self.width), float(self.height))
        
        cpp_renderer.render_frame(
            context=context_ptr,
            grid=grid,
            color_pairs=color_pairs,
            dirty_rect=dirty_rect,
            char_width=char_width,
            char_height=char_height,
            rows=rows,
            cols=cols,
            offset_x=0.0,
            offset_y=0.0,
            cursor_visible=cursor_visible,
            cursor_row=cursor_row,
            cursor_col=cursor_col,
            marked_text=marked_text or ""
        )
        
        return buffer
    
    def _render_pyobjc_impl(self, context, grid, color_pairs, char_width, 
                           char_height, rows, cols, cursor_visible, cursor_row,
                           cursor_col, marked_text):
        """
        PyObjC rendering implementation.
        
        This is a simplified version of the PyObjC rendering logic from
        CoreGraphicsBackend for testing purposes.
        """
        # Create font
        font_name = "Menlo"
        font_size = 12.0
        font = Cocoa.NSFont.fontWithName_size_(font_name, font_size)
        if font is None:
            font = Cocoa.NSFont.monospacedSystemFontOfSize_weight_(font_size, 0.0)
        
        # Render backgrounds
        for row in range(rows):
            for col in range(cols):
                if row >= len(grid) or col >= len(grid[row]):
                    continue
                    
                cell = grid[row][col]
                char, color_pair_id, attributes = cell
                
                # Get background color
                if color_pair_id in color_pairs:
                    fg_rgb, bg_rgb = color_pairs[color_pair_id]
                    bg_r, bg_g, bg_b = bg_rgb
                else:
                    bg_r, bg_g, bg_b = (0, 0, 0)
                
                # Draw background
                x = col * char_width
                y = (rows - row - 1) * char_height  # Flip Y coordinate
                
                Quartz.CGContextSetRGBFillColor(
                    context,
                    bg_r / 255.0,
                    bg_g / 255.0,
                    bg_b / 255.0,
                    1.0
                )
                Quartz.CGContextFillRect(
                    context,
                    Quartz.CGRectMake(x, y, char_width, char_height)
                )
        
        # Render characters
        for row in range(rows):
            for col in range(cols):
                if row >= len(grid) or col >= len(grid[row]):
                    continue
                    
                cell = grid[row][col]
                char, color_pair_id, attributes = cell
                
                # Skip spaces and empty strings
                if not char or char == ' ':
                    continue
                
                # Get foreground color
                if color_pair_id in color_pairs:
                    fg_rgb, bg_rgb = color_pairs[color_pair_id]
                    fg_r, fg_g, fg_b = fg_rgb
                else:
                    fg_r, fg_g, fg_b = (255, 255, 255)
                
                # Create color
                fg_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    fg_r / 255.0,
                    fg_g / 255.0,
                    fg_b / 255.0,
                    1.0
                )
                
                # Apply attributes
                attrs = {Cocoa.NSFontAttributeName: font}
                attrs[Cocoa.NSForegroundColorAttributeName] = fg_color
                
                # BOLD attribute (bit 0)
                if attributes & 1:
                    bold_font = Cocoa.NSFontManager.sharedFontManager().convertFont_toHaveTrait_(
                        font, Cocoa.NSBoldFontMask
                    )
                    if bold_font:
                        attrs[Cocoa.NSFontAttributeName] = bold_font
                
                # UNDERLINE attribute (bit 1)
                if attributes & 2:
                    attrs[Cocoa.NSUnderlineStyleAttributeName] = Cocoa.NSUnderlineStyleSingle
                
                # Create attributed string
                attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
                    char, attrs
                )
                
                # Draw character
                x = col * char_width
                y = (rows - row - 1) * char_height  # Flip Y coordinate
                
                # Save graphics state
                Quartz.CGContextSaveGState(context)
                
                # Set text position
                Quartz.CGContextSetTextPosition(context, x, y)
                
                # Draw using CoreText
                line = CTLineCreateWithAttributedString(attr_string)
                CTLineDraw(line, context)
                
                # Restore graphics state
                Quartz.CGContextRestoreGState(context)
        
        # Render cursor if visible
        if cursor_visible:
            x = cursor_col * char_width
            y = (rows - cursor_row - 1) * char_height
            
            Quartz.CGContextSetRGBFillColor(context, 1.0, 1.0, 1.0, 0.5)
            Quartz.CGContextFillRect(
                context,
                Quartz.CGRectMake(x, y, char_width, char_height)
            )
        
        # Render marked text if present
        if marked_text:
            x = cursor_col * char_width
            y = (rows - cursor_row - 1) * char_height
            
            # Create underlined attributed string
            attrs = {
                Cocoa.NSFontAttributeName: font,
                Cocoa.NSForegroundColorAttributeName: Cocoa.NSColor.whiteColor(),
                Cocoa.NSUnderlineStyleAttributeName: Cocoa.NSUnderlineStyleSingle
            }
            
            attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
                marked_text, attrs
            )
            
            Quartz.CGContextSaveGState(context)
            Quartz.CGContextSetTextPosition(context, x, y)
            
            line = CTLineCreateWithAttributedString(attr_string)
            CTLineDraw(line, context)
            
            Quartz.CGContextRestoreGState(context)


def compare_buffers(buffer1, buffer2, width, height, tolerance=0):
    """
    Compare two pixel buffers and calculate difference percentage.
    
    This function implements pixel-by-pixel comparison of two RGBA buffers,
    calculating the percentage of pixels that differ beyond the specified tolerance.
    
    Args:
        buffer1: First pixel buffer (bytearray) in RGBA format
        buffer2: Second pixel buffer (bytearray) in RGBA format
        width: Image width in pixels
        height: Image height in pixels
        tolerance: Maximum allowed difference per channel (0-255)
                  Allows for minor anti-aliasing differences
        
    Returns:
        tuple: (difference_percentage, different_pixels, total_pixels, max_diff)
               - difference_percentage: Percentage of pixels that differ (0.0-100.0)
               - different_pixels: Number of pixels that differ beyond tolerance
               - total_pixels: Total number of pixels compared
               - max_diff: Maximum channel difference found across all pixels
    
    Validates: Requirements 13.2 (pixel-by-pixel comparison and difference calculation)
    """
    if buffer1 is None or buffer2 is None:
        return None, None, None, None
    
    if len(buffer1) != len(buffer2):
        raise ValueError(f"Buffers have different sizes: {len(buffer1)} vs {len(buffer2)}")
    
    bytes_per_pixel = 4  # RGBA
    total_pixels = width * height
    different_pixels = 0
    max_diff = 0
    
    for i in range(0, len(buffer1), bytes_per_pixel):
        # Extract RGBA values
        r1, g1, b1, a1 = buffer1[i:i+4]
        r2, g2, b2, a2 = buffer2[i:i+4]
        
        # Calculate per-channel differences
        r_diff = abs(r1 - r2)
        g_diff = abs(g1 - g2)
        b_diff = abs(b1 - b2)
        a_diff = abs(a1 - a2)
        
        # Track maximum difference
        max_channel_diff = max(r_diff, g_diff, b_diff, a_diff)
        max_diff = max(max_diff, max_channel_diff)
        
        # Check if pixel differs beyond tolerance
        if (r_diff > tolerance or
            g_diff > tolerance or
            b_diff > tolerance or
            a_diff > tolerance):
            different_pixels += 1
    
    difference_percentage = (different_pixels / total_pixels) * 100.0
    
    return difference_percentage, different_pixels, total_pixels, max_diff


def save_buffer_as_png(buffer, width, height, filename):
    """
    Save a pixel buffer as a PNG file for debugging.
    
    This is a helper function for visual debugging when tests fail.
    It allows developers to inspect the actual rendered output.
    
    Args:
        buffer: Pixel buffer (bytearray) in RGBA format
        width: Image width in pixels
        height: Image height in pixels
        filename: Output PNG filename
    """
    if not MACOS_AVAILABLE:
        return
    
    try:
        # Create color space
        color_space = Quartz.CGColorSpaceCreateWithName(Quartz.kCGColorSpaceSRGB)
        
        # Create bitmap context from buffer
        context = Quartz.CGBitmapContextCreate(
            buffer,
            width,
            height,
            8,
            width * 4,
            color_space,
            Quartz.kCGImageAlphaPremultipliedLast
        )
        
        # Create image from context
        image = Quartz.CGBitmapContextCreateImage(context)
        
        # Save to file
        url = Cocoa.NSURL.fileURLWithPath_(filename)
        dest = Quartz.CGImageDestinationCreateWithURL(
            url,
            "public.png",
            1,
            None
        )
        
        Quartz.CGImageDestinationAddImage(dest, image, None)
        Quartz.CGImageDestinationFinalize(dest)
        
        print(f"  Saved debug image: {filename}")
        
    except Exception as e:
        print(f"  Warning: Could not save debug image: {e}")


def test_simple_text_rendering():
    """Test visual equivalence for simple text rendering."""
    if not MACOS_AVAILABLE:
        print("Skipping test_simple_text_rendering (macOS not available)")
        return True
    
    print("\nTesting simple text rendering:")
    
    # Create test grid
    grid = [
        [('H', 0, 0), ('e', 0, 0), ('l', 0, 0), ('l', 0, 0), ('o', 0, 0)]
    ]
    
    color_pairs = {
        0: ((255, 255, 255), (0, 0, 0))  # White on black
    }
    
    # Render dimensions
    char_width = 10.0
    char_height = 20.0
    rows = 1
    cols = 5
    width = int(cols * char_width)
    height = int(rows * char_height)
    
    # Create renderer
    renderer = OffscreenRenderer(width, height)
    
    # Render with both implementations
    buffer_pyobjc = renderer.render_with_pyobjc(
        grid, color_pairs, char_width, char_height, rows, cols
    )
    
    buffer_cpp = renderer.render_with_cpp(
        grid, color_pairs, char_width, char_height, rows, cols
    )
    
    if buffer_cpp is None:
        print("✗ C++ renderer not available")
        return False
    
    # Compare buffers
    diff_pct, diff_pixels, total_pixels, max_diff = compare_buffers(
        buffer_pyobjc, buffer_cpp, width, height, tolerance=1
    )
    
    print(f"  Difference: {diff_pct:.2f}% ({diff_pixels}/{total_pixels} pixels)")
    print(f"  Max channel difference: {max_diff}")
    
    # Allow small differences due to anti-aliasing
    if diff_pct < 5.0:
        print("✓ Visual equivalence verified (within tolerance)")
        return True
    else:
        print(f"✗ Visual difference too large: {diff_pct:.2f}%")
        # Save debug images if available
        save_buffer_as_png(buffer_pyobjc, width, height, "/tmp/test_simple_pyobjc.png")
        save_buffer_as_png(buffer_cpp, width, height, "/tmp/test_simple_cpp.png")
        return False


def test_colored_text_rendering():
    """Test visual equivalence for colored text."""
    if not MACOS_AVAILABLE:
        print("Skipping test_colored_text_rendering (macOS not available)")
        return True
    
    print("\nTesting colored text rendering:")
    
    # Create test grid with multiple colors
    grid = [
        [('R', 1, 0), ('G', 2, 0), ('B', 3, 0)]
    ]
    
    color_pairs = {
        0: ((255, 255, 255), (0, 0, 0)),    # White on black
        1: ((255, 0, 0), (0, 0, 0)),        # Red on black
        2: ((0, 255, 0), (0, 0, 0)),        # Green on black
        3: ((0, 0, 255), (0, 0, 0))         # Blue on black
    }
    
    # Render dimensions
    char_width = 10.0
    char_height = 20.0
    rows = 1
    cols = 3
    width = int(cols * char_width)
    height = int(rows * char_height)
    
    # Create renderer
    renderer = OffscreenRenderer(width, height)
    
    # Render with both implementations
    buffer_pyobjc = renderer.render_with_pyobjc(
        grid, color_pairs, char_width, char_height, rows, cols
    )
    
    buffer_cpp = renderer.render_with_cpp(
        grid, color_pairs, char_width, char_height, rows, cols
    )
    
    if buffer_cpp is None:
        print("✗ C++ renderer not available")
        return False
    
    # Compare buffers
    diff_pct, diff_pixels, total_pixels, max_diff = compare_buffers(
        buffer_pyobjc, buffer_cpp, width, height, tolerance=1
    )
    
    print(f"  Difference: {diff_pct:.2f}% ({diff_pixels}/{total_pixels} pixels)")
    print(f"  Max channel difference: {max_diff}")
    
    if diff_pct < 5.0:
        print("✓ Visual equivalence verified (within tolerance)")
        return True
    else:
        print(f"✗ Visual difference too large: {diff_pct:.2f}%")
        save_buffer_as_png(buffer_pyobjc, width, height, "/tmp/test_colored_pyobjc.png")
        save_buffer_as_png(buffer_cpp, width, height, "/tmp/test_colored_cpp.png")
        return False


def test_background_colors():
    """Test visual equivalence for background colors."""
    if not MACOS_AVAILABLE:
        print("Skipping test_background_colors (macOS not available)")
        return True
    
    print("\nTesting background colors:")
    
    # Create test grid with different backgrounds
    grid = [
        [('X', 1, 0), ('Y', 2, 0), ('Z', 3, 0)]
    ]
    
    color_pairs = {
        1: ((255, 255, 255), (255, 0, 0)),    # White on red
        2: ((0, 0, 0), (0, 255, 0)),          # Black on green
        3: ((255, 255, 0), (0, 0, 255))       # Yellow on blue
    }
    
    # Render dimensions
    char_width = 10.0
    char_height = 20.0
    rows = 1
    cols = 3
    width = int(cols * char_width)
    height = int(rows * char_height)
    
    # Create renderer
    renderer = OffscreenRenderer(width, height)
    
    # Render with both implementations
    buffer_pyobjc = renderer.render_with_pyobjc(
        grid, color_pairs, char_width, char_height, rows, cols
    )
    
    buffer_cpp = renderer.render_with_cpp(
        grid, color_pairs, char_width, char_height, rows, cols
    )
    
    if buffer_cpp is None:
        print("✗ C++ renderer not available")
        return False
    
    # Compare buffers
    diff_pct, diff_pixels, total_pixels, max_diff = compare_buffers(
        buffer_pyobjc, buffer_cpp, width, height, tolerance=1
    )
    
    print(f"  Difference: {diff_pct:.2f}% ({diff_pixels}/{total_pixels} pixels)")
    print(f"  Max channel difference: {max_diff}")
    
    if diff_pct < 5.0:
        print("✓ Visual equivalence verified (within tolerance)")
        return True
    else:
        print(f"✗ Visual difference too large: {diff_pct:.2f}%")
        save_buffer_as_png(buffer_pyobjc, width, height, "/tmp/test_background_pyobjc.png")
        save_buffer_as_png(buffer_cpp, width, height, "/tmp/test_background_cpp.png")
        return False


def test_cursor_rendering():
    """Test visual equivalence for cursor rendering."""
    if not MACOS_AVAILABLE:
        print("Skipping test_cursor_rendering (macOS not available)")
        return True
    
    print("\nTesting cursor rendering:")
    
    # Create test grid
    grid = [
        [('A', 0, 0), ('B', 0, 0), ('C', 0, 0)]
    ]
    
    color_pairs = {
        0: ((255, 255, 255), (0, 0, 0))
    }
    
    # Render dimensions
    char_width = 10.0
    char_height = 20.0
    rows = 1
    cols = 3
    width = int(cols * char_width)
    height = int(rows * char_height)
    
    # Create renderer
    renderer = OffscreenRenderer(width, height)
    
    # Render with cursor visible
    buffer_pyobjc = renderer.render_with_pyobjc(
        grid, color_pairs, char_width, char_height, rows, cols,
        cursor_visible=True, cursor_row=0, cursor_col=1
    )
    
    buffer_cpp = renderer.render_with_cpp(
        grid, color_pairs, char_width, char_height, rows, cols,
        cursor_visible=True, cursor_row=0, cursor_col=1
    )
    
    if buffer_cpp is None:
        print("✗ C++ renderer not available")
        return False
    
    # Compare buffers
    diff_pct, diff_pixels, total_pixels, max_diff = compare_buffers(
        buffer_pyobjc, buffer_cpp, width, height, tolerance=1
    )
    
    print(f"  Difference: {diff_pct:.2f}% ({diff_pixels}/{total_pixels} pixels)")
    print(f"  Max channel difference: {max_diff}")
    
    if diff_pct < 5.0:
        print("✓ Visual equivalence verified (within tolerance)")
        return True
    else:
        print(f"✗ Visual difference too large: {diff_pct:.2f}%")
        save_buffer_as_png(buffer_pyobjc, width, height, "/tmp/test_cursor_pyobjc.png")
        save_buffer_as_png(buffer_cpp, width, height, "/tmp/test_cursor_cpp.png")
        return False


def main():
    """Run all visual equivalence tests."""
    print("=" * 60)
    print("Visual Equivalence Testing")
    print("=" * 60)
    
    if not MACOS_AVAILABLE:
        print("\n✗ PyObjC not available - skipping all tests")
        print("Install with: pip install pyobjc-framework-Cocoa")
        return True  # Don't fail on non-macOS systems
    
    tests = [
        ("Simple text rendering", test_simple_text_rendering),
        ("Colored text rendering", test_colored_text_rendering),
        ("Background colors", test_background_colors),
        ("Cursor rendering", test_cursor_rendering)
    ]
    
    failed = []
    for name, test_func in tests:
        try:
            if not test_func():
                failed.append(name)
        except Exception as e:
            print(f"✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            failed.append(name)
    
    print("\n" + "=" * 60)
    if not failed:
        print("✓ All visual equivalence tests passed!")
    else:
        print(f"✗ {len(failed)} test(s) failed:")
        for name in failed:
            print(f"  - {name}")
    print("=" * 60)
    
    return len(failed) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
