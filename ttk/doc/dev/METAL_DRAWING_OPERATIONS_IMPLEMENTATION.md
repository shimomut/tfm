# Metal Backend Drawing Operations Implementation

## Overview

This document describes the implementation of drawing operations in the Metal backend for TTK. These operations update the character grid buffer, which is later rendered to the screen using Metal's GPU-accelerated rendering pipeline.

## Implementation Details

### Character Grid Buffer

The Metal backend maintains a 2D character grid where each cell stores:
- `char` (str): The character to display
- `color_pair` (int): Color pair index (0-255)
- `attributes` (int): Text attributes as bitwise flags

```python
self.grid = [
    [(' ', 0, 0) for _ in range(self.cols)]
    for _ in range(self.rows)
]
```

### Drawing Operations

All drawing operations update this grid buffer. Changes are not visible until `refresh()` or `refresh_region()` is called.

#### draw_text()

Draws text at a specified position with color and attributes.

**Implementation:**
```python
def draw_text(self, row: int, col: int, text: str,
              color_pair: int = 0, attributes: int = 0) -> None:
    # Handle out-of-bounds gracefully
    if row < 0 or row >= self.rows:
        return
    
    # Draw each character, stopping at grid boundary
    for i, char in enumerate(text):
        c = col + i
        if c < 0:
            continue
        if c >= self.cols:
            break
        self.grid[row][c] = (char, color_pair, attributes)
```

**Key Features:**
- Out-of-bounds rows are ignored (no crash)
- Text that extends beyond the right edge is clipped
- Negative column positions skip characters until reaching column 0
- Each character is stored with its color pair and attributes

**Example:**
```python
backend.draw_text(0, 0, "Hello", color_pair=1, attributes=TextAttribute.BOLD)
# Draws "Hello" at top-left with color pair 1 and bold attribute
```

#### draw_hline()

Draws a horizontal line using a specified character.

**Implementation:**
```python
def draw_hline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Use draw_text to draw the line
    if char:
        line_text = char[0] * length
        self.draw_text(row, col, line_text, color_pair)
```

**Key Features:**
- Implemented using `draw_text()` for consistency
- Creates a string of repeated characters
- Inherits out-of-bounds handling from `draw_text()`
- Empty character strings are handled gracefully

**Example:**
```python
backend.draw_hline(5, 10, '-', 20, color_pair=2)
# Draws a 20-character horizontal line at row 5, starting at column 10
```

#### draw_vline()

Draws a vertical line using a specified character.

**Implementation:**
```python
def draw_vline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Handle out-of-bounds gracefully
    if col < 0 or col >= self.cols or not char:
        return
    
    # Draw each character vertically
    for i in range(length):
        r = row + i
        if r < 0:
            continue
        if r >= self.rows:
            break
        self.grid[r][col] = (char[0], color_pair, 0)
```

**Key Features:**
- Out-of-bounds columns are rejected early
- Lines that extend beyond the bottom edge are clipped
- Negative row positions skip characters until reaching row 0
- Empty character strings are handled gracefully

**Example:**
```python
backend.draw_vline(0, 5, '|', 10, color_pair=1)
# Draws a 10-character vertical line at column 5, starting at row 0
```

#### draw_rect()

Draws a rectangle, either filled or outlined.

**Implementation:**
```python
def draw_rect(self, row: int, col: int, height: int, width: int,
              color_pair: int = 0, filled: bool = False) -> None:
    if filled:
        # Fill the rectangle with spaces
        for r in range(row, min(row + height, self.rows)):
            if r >= 0:
                self.draw_text(r, col, ' ' * width, color_pair)
    else:
        # Draw outline
        if height > 0 and width > 0:
            # Top edge
            self.draw_hline(row, col, '-', width, color_pair)
            # Bottom edge
            if height > 1:
                self.draw_hline(row + height - 1, col, '-', width, color_pair)
            # Left edge
            self.draw_vline(row, col, '|', height, color_pair)
            # Right edge
            if width > 1:
                self.draw_vline(row, col + width - 1, '|', height, color_pair)
```

**Key Features:**
- Filled rectangles use spaces with the specified color pair
- Outlined rectangles use '-' for horizontal edges and '|' for vertical edges
- Corners may have either '-' or '|' depending on draw order
- Zero dimensions are handled gracefully
- Out-of-bounds rectangles are clipped by underlying operations

**Example:**
```python
# Draw filled rectangle
backend.draw_rect(2, 5, 4, 10, color_pair=3, filled=True)

# Draw outlined rectangle
backend.draw_rect(10, 20, 5, 15, color_pair=1, filled=False)
```

#### clear()

Clears the entire character grid.

**Implementation:**
```python
def clear(self) -> None:
    for row in range(self.rows):
        for col in range(self.cols):
            self.grid[row][col] = (' ', 0, 0)
```

**Key Features:**
- Fills entire grid with spaces
- Uses color pair 0 (default colors)
- No attributes applied
- Simple nested loop for clarity

**Example:**
```python
backend.clear()
# Clears entire window
```

#### clear_region()

Clears a rectangular region of the grid.

**Implementation:**
```python
def clear_region(self, row: int, col: int, height: int, width: int) -> None:
    # Handle out-of-bounds gracefully by clipping to valid range
    for r in range(row, min(row + height, self.rows)):
        for c in range(col, min(col + width, self.cols)):
            if r >= 0 and c >= 0:
                self.grid[r][c] = (' ', 0, 0)
```

**Key Features:**
- Clips region to grid boundaries
- Handles negative coordinates by checking >= 0
- Fills region with spaces using default colors
- Zero dimensions are handled gracefully

**Example:**
```python
backend.clear_region(5, 10, 3, 20)
# Clears a 3x20 region starting at row 5, column 10
```

## Out-of-Bounds Handling

All drawing operations handle out-of-bounds coordinates gracefully:

1. **Complete out-of-bounds**: Operations that are entirely outside the grid are ignored
2. **Partial out-of-bounds**: Operations that partially extend beyond the grid are clipped
3. **No crashes**: Invalid coordinates never cause exceptions

This design ensures stability even when application code provides incorrect coordinates.

## Coordinate System

The Metal backend uses a character-based coordinate system:

- **Origin**: (0, 0) is at the top-left corner
- **Row axis**: Increases downward (0 = top, rows-1 = bottom)
- **Column axis**: Increases rightward (0 = left, cols-1 = right)
- **Units**: All coordinates are in character cells, not pixels

## Performance Considerations

### Buffer-Based Rendering

Drawing operations only update the in-memory grid buffer. This provides several benefits:

1. **Fast operations**: No GPU calls during drawing
2. **Batch rendering**: Multiple operations can be batched before refresh
3. **Partial updates**: Only changed regions need to be rendered
4. **Predictable performance**: Drawing operations have O(n) complexity where n is the number of characters

### Memory Usage

The grid buffer uses minimal memory:
- Each cell: 3 values (char, color_pair, attributes)
- Typical 80x40 grid: ~3,200 cells
- Memory overhead: Negligible compared to GPU resources

## Testing

The implementation includes comprehensive unit tests covering:

1. **Basic functionality**: Each operation works correctly
2. **Out-of-bounds handling**: Invalid coordinates don't crash
3. **Edge cases**: Empty strings, zero dimensions, etc.
4. **Coordinate system**: Origin and axis directions are correct
5. **Attribute handling**: Color pairs and attributes are stored correctly
6. **Overwriting**: New content replaces old content

All tests use mocked PyObjC modules to avoid requiring actual macOS frameworks.

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 3.2**: Metal backend drawing operations update grid buffer
- **Requirement 4.1**: Support for text drawing with color and attributes
- **Requirement 4.2**: Support for rectangle drawing (filled and outlined)
- **Requirement 4.3**: Support for horizontal and vertical lines
- **Requirement 4.5**: Support for clearing entire window and regions
- **Requirement 8.5**: Graceful handling of out-of-bounds coordinates

## Future Enhancements

The current implementation provides the foundation for:

1. **GPU rendering**: Converting grid buffer to Metal draw calls (Task 16)
2. **Partial updates**: Optimized rendering of changed regions only
3. **Advanced attributes**: Support for additional text styling
4. **Image rendering**: Future support for image primitives

## Related Documentation

- [Metal Initialization Implementation](METAL_INITIALIZATION_IMPLEMENTATION.md)
- [Metal Font Validation Implementation](METAL_FONT_VALIDATION_IMPLEMENTATION.md)
- [Metal Character Grid Implementation](METAL_CHARACTER_GRID_IMPLEMENTATION.md)
- [TTK Renderer API Reference](../API_REFERENCE.md) (when created)

## References

- TTK Design Document: `.kiro/specs/desktop-app-mode/design.md`
- TTK Requirements: `.kiro/specs/desktop-app-mode/requirements.md`
- Metal Backend Source: `ttk/backends/metal_backend.py`
- Unit Tests: `ttk/test/test_metal_drawing_operations.py`
