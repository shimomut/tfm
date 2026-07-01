# TTK Coordinate System and Color Management

This document provides detailed information about TTK's coordinate system and color management.

## Table of Contents

- [Coordinate System](#coordinate-system)
- [Color Management](#color-management)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

## Coordinate System

### Character-Based Coordinates

TTK uses a character-based coordinate system where all positions and dimensions are specified in character cells, not pixels. This abstraction allows the same code to work across different backends and display resolutions.

### Origin and Axes

```
(0,0) ─────────────────────> Columns (x-axis)
  │
  │    Character Grid
  │
  │    Each cell contains one character
  │
  ▼
Rows (y-axis)
```

- **Origin**: (0, 0) is at the top-left corner
- **Rows**: Increase downward (0 is top, higher numbers are lower)
- **Columns**: Increase rightward (0 is left, higher numbers are right)
- **Units**: All coordinates are in character cells

### Coordinate Examples

```
     Col 0   Col 1   Col 2   Col 3   Col 4
Row 0  (0,0)  (0,1)  (0,2)  (0,3)  (0,4)
Row 1  (1,0)  (1,1)  (1,2)  (1,3)  (1,4)
Row 2  (2,0)  (2,1)  (2,2)  (2,3)  (2,4)
Row 3  (3,0)  (3,1)  (3,2)  (3,3)  (3,4)
```

### Window Dimensions

Get the current window size in character cells:

```python
rows, cols = renderer.get_dimensions()
print(f"Window size: {rows} rows x {cols} columns")
```

**Example dimensions:**
- Terminal: 24 rows x 80 columns (typical)
- Desktop window: 40 rows x 120 columns (depends on window size and font)

### Drawing at Specific Positions

```python
# Draw at top-left corner
renderer.draw_text(0, 0, "Top-left")

# Draw at top-right corner
rows, cols = renderer.get_dimensions()
text = "Top-right"
renderer.draw_text(0, cols - len(text), text)

# Draw at bottom-left corner
renderer.draw_text(rows - 1, 0, "Bottom-left")

# Draw at bottom-right corner
text = "Bottom-right"
renderer.draw_text(rows - 1, cols - len(text), text)

# Draw centered
text = "Centered"
center_row = rows // 2
center_col = (cols - len(text)) // 2
renderer.draw_text(center_row, center_col, text)
```

### Regions and Rectangles

Regions are specified with:
- **row**: Starting row (top edge)
- **col**: Starting column (left edge)
- **height**: Height in rows
- **width**: Width in columns

```python
# Clear a 10x20 region starting at (5, 10)
renderer.clear_region(row=5, col=10, height=10, width=20)

# Draw a rectangle from (2, 2) to (11, 31)
renderer.draw_rect(row=2, col=2, height=10, width=30, filled=False)
```

### Out-of-Bounds Handling

TTK handles out-of-bounds coordinates gracefully:

```python
rows, cols = renderer.get_dimensions()

# These won't crash, but won't draw anything visible
renderer.draw_text(rows + 10, cols + 10, "Out of bounds")
renderer.draw_text(-5, -5, "Negative coordinates")

# Partial drawing: only visible portion is drawn
renderer.draw_text(rows - 1, cols - 5, "This text extends beyond window")
```

**Behavior:**
- **Curses backend**: Ignores out-of-bounds drawing
- **CoreGraphics backend**: Clips to window boundaries
- **No exceptions**: Out-of-bounds drawing never crashes

### Coordinate Validation

Validate coordinates before drawing:

```python
def is_valid_position(row: int, col: int, rows: int, cols: int) -> bool:
    """Check if position is within window bounds."""
    return 0 <= row < rows and 0 <= col < cols

rows, cols = renderer.get_dimensions()
if is_valid_position(10, 20, rows, cols):
    renderer.draw_text(10, 20, "Valid position")
```

### Relative Positioning

Calculate positions relative to other elements:

```python
# Draw a box with text inside
box_row, box_col = 5, 10
box_height, box_width = 10, 40

# Draw box
renderer.draw_rect(box_row, box_col, box_height, box_width, filled=False)

# Draw text inside box (1 row and 2 columns from edges)
text_row = box_row + 1
text_col = box_col + 2
renderer.draw_text(text_row, text_col, "Text inside box")

# Draw centered text in box
text = "Centered in box"
text_row = box_row + box_height // 2
text_col = box_col + (box_width - len(text)) // 2
renderer.draw_text(text_row, text_col, text)
```

## Color Management

### Color Pairs

TTK uses color pairs—combinations of foreground and background colors. Each color pair has:
- **ID**: Integer from 0 to 255
- **Foreground color**: RGB tuple (R, G, B) where each component is 0-255
- **Background color**: RGB tuple (R, G, B) where each component is 0-255

### Initializing Color Pairs

```python
# Color pair 1: White text on blue background
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))

# Color pair 2: Yellow text on black background
renderer.init_color_pair(2, (255, 255, 0), (0, 0, 0))

# Color pair 3: Green text on dark green background
renderer.init_color_pair(3, (0, 255, 0), (0, 64, 0))

# Color pair 4: Red text on white background
renderer.init_color_pair(4, (255, 0, 0), (255, 255, 255))
```

### Using Color Pairs

Reference color pairs by ID when drawing:

```python
renderer.draw_text(0, 0, "White on blue", color_pair=1)
renderer.draw_text(1, 0, "Yellow on black", color_pair=2)
renderer.draw_text(2, 0, "Green on dark green", color_pair=3)
renderer.draw_text(3, 0, "Red on white", color_pair=4)
```

### Default Color Pair

Color pair 0 is reserved for default colors:

```python
# Use default terminal/window colors
renderer.draw_text(0, 0, "Default colors", color_pair=0)
```

**Note:** Color pair 0 doesn't need initialization—it's automatically set to default colors.

### RGB Color Values

RGB colors use values from 0 to 255 for each component:

```python
# Pure colors
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

# Mixed colors
yellow = (255, 255, 0)
cyan = (0, 255, 255)
magenta = (255, 0, 255)

# Grayscale
black = (0, 0, 0)
white = (255, 255, 255)
gray = (128, 128, 128)
dark_gray = (64, 64, 64)
light_gray = (192, 192, 192)

# Custom colors
orange = (255, 165, 0)
purple = (128, 0, 128)
brown = (165, 42, 42)
```

### Color Pair Limits

- **Maximum pairs**: 256 (IDs 0-255)
- **Reserved**: Color pair 0 is reserved for defaults
- **Available**: Color pairs 1-255 for custom colors

```python
# Initialize many color pairs
for i in range(1, 256):
    # Create a gradient of colors
    r = (i * 255) // 255
    g = 128
    b = 255 - r
    renderer.init_color_pair(i, (r, g, b), (0, 0, 0))
```

### Backend Color Differences

#### Curses Backend

The curses backend approximates RGB colors to terminal colors:

- **8-color terminals**: Maps to basic colors (black, red, green, yellow, blue, magenta, cyan, white)
- **256-color terminals**: Better approximation but still limited
- **True color terminals**: Best RGB approximation

```python
# This color may be approximated in terminal
renderer.init_color_pair(1, (255, 128, 64), (32, 32, 32))
```

#### CoreGraphics Backend

The CoreGraphics backend supports full RGB colors:

- **True RGB**: Exact color reproduction
- **No approximation**: Colors appear exactly as specified
- **Consistent**: Same colors across different displays

```python
# This color will be exact in CoreGraphics backend
renderer.init_color_pair(1, (255, 128, 64), (32, 32, 32))
```

### Color Utilities

TTK provides utilities for color conversion:

```python
from ttk.utils.color_utils import rgb_to_hex, hex_to_rgb

# Convert RGB to hex
hex_color = rgb_to_hex(255, 128, 0)  # Returns: '#FF8000'

# Convert hex to RGB
r, g, b = hex_to_rgb('#FF8000')  # Returns: (255, 128, 0)

# Use in color pair initialization
renderer.init_color_pair(1, hex_to_rgb('#FFFFFF'), hex_to_rgb('#0000FF'))
```

### Color Schemes

Organize colors into schemes:

```python
class ColorScheme:
    """Color scheme for application."""
    
    # Color pair IDs
    NORMAL = 1
    HIGHLIGHT = 2
    ERROR = 3
    SUCCESS = 4
    WARNING = 5
    
    @staticmethod
    def initialize(renderer):
        """Initialize all color pairs."""
        # Normal: white on dark gray
        renderer.init_color_pair(ColorScheme.NORMAL, 
                                (255, 255, 255), (40, 40, 40))
        
        # Highlight: black on cyan
        renderer.init_color_pair(ColorScheme.HIGHLIGHT,
                                (0, 0, 0), (0, 255, 255))
        
        # Error: white on red
        renderer.init_color_pair(ColorScheme.ERROR,
                                (255, 255, 255), (255, 0, 0))
        
        # Success: white on green
        renderer.init_color_pair(ColorScheme.SUCCESS,
                                (255, 255, 255), (0, 128, 0))
        
        # Warning: black on yellow
        renderer.init_color_pair(ColorScheme.WARNING,
                                (0, 0, 0), (255, 255, 0))

# Usage
ColorScheme.initialize(renderer)
renderer.draw_text(0, 0, "Normal text", color_pair=ColorScheme.NORMAL)
renderer.draw_text(1, 0, "Error!", color_pair=ColorScheme.ERROR)
```

## Best Practices

### 1. Cache Window Dimensions

Don't call `get_dimensions()` repeatedly in tight loops:

```python
# ❌ Bad: Calls get_dimensions() many times
for i in range(100):
    rows, cols = renderer.get_dimensions()
    renderer.draw_text(i % rows, 0, f"Line {i}")

# ✅ Good: Cache dimensions
rows, cols = renderer.get_dimensions()
for i in range(100):
    renderer.draw_text(i % rows, 0, f"Line {i}")
```

### 2. Initialize Color Pairs Once

Initialize color pairs at startup, not every frame:

```python
# ❌ Bad: Initializes every frame
def draw_frame():
    renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))
    renderer.draw_text(0, 0, "Text", color_pair=1)

# ✅ Good: Initialize once at startup
def initialize():
    renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))

def draw_frame():
    renderer.draw_text(0, 0, "Text", color_pair=1)
```

### 3. Use Relative Positioning

Calculate positions relative to window size for responsive layouts:

```python
def draw_centered_box(renderer, height, width):
    """Draw a centered box that adapts to window size."""
    rows, cols = renderer.get_dimensions()
    
    # Calculate centered position
    row = (rows - height) // 2
    col = (cols - width) // 2
    
    # Draw box
    renderer.draw_rect(row, col, height, width, filled=False)
```

### 4. Handle Window Resize

Update layout when window is resized:

```python
from ttk import KeyCode

def main_loop(renderer):
    rows, cols = renderer.get_dimensions()
    
    while True:
        draw_ui(renderer, rows, cols)
        renderer.refresh()
        
        event = renderer.get_input()
        
        if event.key_code == KeyCode.RESIZE:
            # Window was resized, update dimensions
            rows, cols = renderer.get_dimensions()
            # Redraw with new dimensions
        elif event.key_code == KeyCode.ESCAPE:
            break
```

### 5. Validate Color Values

Validate RGB values before initialization:

```python
def safe_init_color_pair(renderer, pair_id, fg, bg):
    """Initialize color pair with validation."""
    # Validate pair ID
    if not (0 <= pair_id <= 255):
        raise ValueError(f"Invalid color pair ID: {pair_id}")
    
    # Validate RGB values
    for color in [fg, bg]:
        for component in color:
            if not (0 <= component <= 255):
                raise ValueError(f"Invalid RGB value: {component}")
    
    renderer.init_color_pair(pair_id, fg, bg)
```

## Common Pitfalls

### 1. Forgetting to Refresh

Changes aren't visible until you call `refresh()`:

```python
# ❌ Bad: No refresh, nothing appears
renderer.draw_text(0, 0, "Hello")

# ✅ Good: Refresh to display
renderer.draw_text(0, 0, "Hello")
renderer.refresh()
```

### 2. Using Pixel Coordinates

TTK uses character coordinates, not pixels:

```python
# ❌ Bad: Thinking in pixels
renderer.draw_text(100, 200, "Text")  # This is row 100, column 200!

# ✅ Good: Think in character cells
rows, cols = renderer.get_dimensions()
renderer.draw_text(rows // 2, cols // 2, "Text")
```

### 3. Assuming Fixed Window Size

Window size can change (terminal resize, window resize):

```python
# ❌ Bad: Assumes 80 columns
renderer.draw_text(0, 70, "Right side")

# ✅ Good: Use actual dimensions
rows, cols = renderer.get_dimensions()
renderer.draw_text(0, cols - 10, "Right side")
```

### 4. Not Handling Out-of-Bounds

Always validate or handle out-of-bounds gracefully:

```python
# ❌ Bad: May draw outside window
renderer.draw_text(row, col, very_long_text)

# ✅ Good: Truncate to fit
rows, cols = renderer.get_dimensions()
max_length = cols - col
if len(very_long_text) > max_length:
    very_long_text = very_long_text[:max_length]
renderer.draw_text(row, col, very_long_text)
```

### 5. Reusing Color Pair IDs

Don't reuse color pair IDs for different colors:

```python
# ❌ Bad: Reusing ID 1 for different colors
renderer.init_color_pair(1, (255, 0, 0), (0, 0, 0))  # Red
# ... later ...
renderer.init_color_pair(1, (0, 255, 0), (0, 0, 0))  # Green (overwrites red!)

# ✅ Good: Use different IDs
renderer.init_color_pair(1, (255, 0, 0), (0, 0, 0))  # Red
renderer.init_color_pair(2, (0, 255, 0), (0, 0, 0))  # Green
```

## Summary

- **Coordinates**: Character-based, (0, 0) at top-left
- **Dimensions**: Get with `get_dimensions()`, cache when possible
- **Out-of-bounds**: Handled gracefully, no crashes
- **Color pairs**: 256 available (0-255), initialize once
- **RGB values**: 0-255 for each component
- **Backend differences**: Curses approximates, CoreGraphics is exact
- **Best practice**: Validate inputs, handle resize, use relative positioning
