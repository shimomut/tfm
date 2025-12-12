# CoreGraphics Backend Drawing Operations Implementation

## Overview

This document describes the implementation of drawing operations for the CoreGraphics backend. The drawing operations provide the core functionality for updating the character grid and triggering visual updates.

## Implementation Date

December 11, 2025

## Implemented Methods

### 1. draw_text()

Updates character grid cells with text, color pair, and attributes.

**Features:**
- Places each character in a separate grid cell
- Supports color pairs and text attributes
- Handles out-of-bounds coordinates gracefully
- Truncates text at grid edge

**Implementation:**
```python
def draw_text(self, row: int, col: int, text: str,
              color_pair: int = 0, attributes: int = 0) -> None:
    # Ignore if starting position is out of bounds
    if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
        return
    
    # Draw each character in the text
    for i, char in enumerate(text):
        current_col = col + i
        
        # Stop if we've reached the right edge of the grid
        if current_col >= self.cols:
            break
        
        # Update the grid cell
        self.grid[row][current_col] = (char, color_pair, attributes)
```

### 2. clear()

Resets all cells in the character grid to spaces with default color pair.

**Features:**
- Clears entire grid
- Resets to space character with color pair 0 and no attributes
- Fast operation using nested loops

**Implementation:**
```python
def clear(self) -> None:
    # Reset all cells to space with default color pair and no attributes
    for row in range(self.rows):
        for col in range(self.cols):
            self.grid[row][col] = (' ', 0, 0)
```

### 3. clear_region()

Resets cells in a specified rectangular region.

**Features:**
- Clears only specified region
- Clamps coordinates to valid ranges
- Handles out-of-bounds coordinates gracefully

**Implementation:**
```python
def clear_region(self, row: int, col: int, height: int, width: int) -> None:
    # Clamp coordinates to valid ranges
    start_row = max(0, min(row, self.rows - 1))
    start_col = max(0, min(col, self.cols - 1))
    end_row = max(0, min(row + height, self.rows))
    end_col = max(0, min(col + width, self.cols))
    
    # Clear cells in the specified region
    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            self.grid[r][c] = (' ', 0, 0)
```

### 4. draw_hline()

Draws a horizontal line using a specified character.

**Features:**
- Draws horizontal line from left to right
- Supports custom line character (typically '-' or '─')
- Handles out-of-bounds row gracefully
- Truncates at grid edge

**Implementation:**
```python
def draw_hline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Ignore if row is out of bounds
    if row < 0 or row >= self.rows:
        return
    
    # Clamp starting column to valid range
    start_col = max(0, col)
    
    # Calculate ending column (clamped to grid width)
    end_col = min(col + length, self.cols)
    
    # Draw the horizontal line
    for c in range(start_col, end_col):
        self.grid[row][c] = (char, color_pair, 0)
```

### 5. draw_vline()

Draws a vertical line using a specified character.

**Features:**
- Draws vertical line from top to bottom
- Supports custom line character (typically '|' or '│')
- Handles out-of-bounds column gracefully
- Truncates at grid edge

**Implementation:**
```python
def draw_vline(self, row: int, col: int, char: str,
               length: int, color_pair: int = 0) -> None:
    # Ignore if column is out of bounds
    if col < 0 or col >= self.cols:
        return
    
    # Clamp starting row to valid range
    start_row = max(0, row)
    
    # Calculate ending row (clamped to grid height)
    end_row = min(row + length, self.rows)
    
    # Draw the vertical line
    for r in range(start_row, end_row):
        self.grid[r][col] = (char, color_pair, 0)
```

### 6. draw_rect()

Draws either a filled or outlined rectangle.

**Features:**
- Supports both filled and outlined rectangles
- Uses Unicode box-drawing characters for outlines (┌ ┐ └ ┘ ─ │)
- Handles out-of-bounds coordinates by clamping
- Handles edge cases (1x1, 1xN, Nx1 rectangles)
- Validates dimensions (ignores zero or negative dimensions)

**Implementation:**
```python
def draw_rect(self, row: int, col: int, height: int, width: int,
              color_pair: int = 0, filled: bool = False) -> None:
    # Ignore if dimensions are invalid
    if height <= 0 or width <= 0:
        return
    
    # Clamp coordinates to valid ranges
    start_row = max(0, row)
    start_col = max(0, col)
    end_row = min(row + height, self.rows)
    end_col = min(col + width, self.cols)
    
    # Recalculate actual dimensions after clamping
    actual_height = end_row - start_row
    actual_width = end_col - start_col
    
    # Ignore if clamping resulted in zero dimensions
    if actual_height <= 0 or actual_width <= 0:
        return
    
    if filled:
        # Draw filled rectangle
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                self.grid[r][c] = (' ', color_pair, 0)
    else:
        # Draw outlined rectangle with box-drawing characters
        # (Special handling for 1x1, 1xN, Nx1 cases)
        # ...
```

### 7. refresh()

Triggers a full window redraw.

**Features:**
- Marks entire view as needing display
- Integrates with Cocoa event loop
- Non-blocking operation

**Implementation:**
```python
def refresh(self) -> None:
    if self.view:
        self.view.setNeedsDisplay_(True)
```

### 8. refresh_region()

Triggers a partial window redraw for a specific region.

**Features:**
- More efficient than full refresh for small changes
- Calculates pixel coordinates from character coordinates
- Marks only specified region as needing display

**Implementation:**
```python
def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
    if self.view:
        # Calculate pixel coordinates for the region
        x = col * self.char_width
        y = (self.rows - row - height) * self.char_height
        pixel_width = width * self.char_width
        pixel_height = height * self.char_height
        
        # Create NSRect for the region
        region_rect = Cocoa.NSMakeRect(x, y, pixel_width, pixel_height)
        
        # Mark the region as needing display
        self.view.setNeedsDisplayInRect_(region_rect)
```

## Out-of-Bounds Handling

All drawing operations handle out-of-bounds coordinates gracefully:

1. **Complete rejection**: If the starting position is completely out of bounds, the operation is ignored
2. **Clamping**: If the operation extends beyond the grid, coordinates are clamped to valid ranges
3. **Truncation**: If text or lines extend beyond the edge, they are truncated at the boundary
4. **No crashes**: Invalid coordinates never cause exceptions or crashes

This ensures robust operation even with incorrect input.

## Box-Drawing Characters

The outlined rectangle implementation uses Unicode box-drawing characters:

- `┌` (U+250C): Top-left corner
- `┐` (U+2510): Top-right corner
- `└` (U+2514): Bottom-left corner
- `┘` (U+2518): Bottom-right corner
- `─` (U+2500): Horizontal line
- `│` (U+2502): Vertical line

These characters provide clean, professional-looking borders that work well with monospace fonts.

## Testing

### Unit Tests

Comprehensive unit tests verify all drawing operations:

- `test_draw_text_updates_grid`: Verifies text is placed correctly
- `test_draw_text_with_color_and_attributes`: Verifies color pairs and attributes
- `test_draw_text_out_of_bounds_row`: Verifies row bounds checking
- `test_draw_text_out_of_bounds_col`: Verifies column bounds checking
- `test_draw_text_truncates_at_edge`: Verifies truncation behavior
- `test_clear_resets_all_cells`: Verifies full clear
- `test_clear_region_resets_specified_cells`: Verifies partial clear
- `test_clear_region_handles_out_of_bounds`: Verifies bounds handling
- `test_draw_hline_draws_horizontal_line`: Verifies horizontal lines
- `test_draw_hline_handles_out_of_bounds_row`: Verifies row bounds
- `test_draw_hline_truncates_at_edge`: Verifies truncation
- `test_draw_vline_draws_vertical_line`: Verifies vertical lines
- `test_draw_vline_handles_out_of_bounds_col`: Verifies column bounds
- `test_draw_vline_truncates_at_edge`: Verifies truncation
- `test_draw_rect_filled`: Verifies filled rectangles
- `test_draw_rect_outlined`: Verifies outlined rectangles
- `test_draw_rect_handles_out_of_bounds`: Verifies bounds handling
- `test_draw_rect_with_invalid_dimensions`: Verifies dimension validation

All tests pass successfully.

### Verification Script

A verification script (`verify_coregraphics_drawing_operations.py`) demonstrates all drawing operations and confirms they work correctly.

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 2.2**: Text drawing updates character grid at specified positions
- **Requirement 2.5**: Out-of-bounds coordinates are handled gracefully without crashing
- **Requirement 10.1**: Grid clearing resets all cells to spaces
- **Requirement 10.2**: Text drawing only updates affected cells

## Performance Considerations

### Efficient Operations

1. **Selective updates**: Only modified cells are updated in the grid
2. **Skip empty cells**: The rendering code skips empty cells for performance
3. **Regional refresh**: `refresh_region()` allows updating only changed areas
4. **Simple data structure**: Grid is a simple 2D list for fast access

### Typical Performance

- `draw_text()`: O(n) where n is text length
- `clear()`: O(rows × cols) - typically ~2000 cells for 80×24
- `clear_region()`: O(height × width) - only clears specified area
- `draw_hline()`: O(length)
- `draw_vline()`: O(length)
- `draw_rect()`: O(height × width) for filled, O(2×(height + width)) for outlined
- `refresh()`: Triggers Cocoa redraw (handled by OS)

All operations complete in microseconds for typical grid sizes.

## Integration with Rendering

The drawing operations update the character grid, which is then rendered by the `TTKView.drawRect_()` method:

1. Application calls drawing operations (e.g., `draw_text()`)
2. Grid cells are updated with new characters, colors, and attributes
3. Application calls `refresh()` or `refresh_region()`
4. Cocoa event loop triggers `drawRect_()`
5. `drawRect_()` iterates through grid and renders each cell
6. Visual output appears on screen

This separation between grid updates and rendering provides flexibility and performance.

## Future Enhancements

Potential improvements for future versions:

1. **Dirty region tracking**: Track which cells have changed to optimize rendering
2. **Batch operations**: Combine multiple drawing operations before refresh
3. **Custom box-drawing styles**: Support different border styles
4. **Pattern fills**: Support pattern fills for rectangles
5. **Clipping regions**: Support clipping to arbitrary regions

These enhancements would maintain backward compatibility while improving performance and functionality.

## Conclusion

The drawing operations implementation provides a complete, robust set of methods for updating the character grid. All operations handle edge cases gracefully, perform efficiently, and integrate seamlessly with the CoreGraphics rendering pipeline.

The implementation satisfies all requirements and passes comprehensive tests, providing a solid foundation for TTK applications running on macOS.
