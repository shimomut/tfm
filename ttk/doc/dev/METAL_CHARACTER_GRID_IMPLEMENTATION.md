# Metal Character Grid Implementation

## Overview

This document describes the implementation of the character grid buffer in the Metal backend. The character grid is a 2D data structure that stores the content to be rendered in the native macOS window, with each cell representing one character position on the screen.

## Architecture

### Grid Structure

The character grid is implemented as a 2D list (list of lists) where:
- The outer list represents rows (vertical dimension)
- Each inner list represents columns (horizontal dimension)
- Each cell is a tuple containing three elements: `(char, color_pair, attributes)`

```python
# Grid structure
self.grid = [
    [(' ', 0, 0), (' ', 0, 0), ...],  # Row 0
    [(' ', 0, 0), (' ', 0, 0), ...],  # Row 1
    ...
]
```

### Cell Format

Each grid cell is a 3-tuple:
1. **char** (str): The character to display (single character string)
2. **color_pair** (int): Color pair index (0-255)
3. **attributes** (int): Text attributes as bitwise flags (TextAttribute enum values)

Example cell values:
```python
(' ', 0, 0)                    # Space with default colors, no attributes
('A', 1, 0)                    # 'A' with color pair 1, no attributes
('B', 2, TextAttribute.BOLD)   # 'B' with color pair 2, bold attribute
```

## Coordinate System

### Requirements Satisfied

- **Requirement 8.1**: Character-based coordinate system with row and column indices
- **Requirement 8.2**: Origin (0, 0) at top-left corner

### Coordinate Mapping

```
(0,0)  (0,1)  (0,2)  ...  (0,cols-1)
(1,0)  (1,1)  (1,2)  ...  (1,cols-1)
(2,0)  (2,1)  (2,2)  ...  (2,cols-1)
...
(rows-1,0)  ...  ...  (rows-1,cols-1)
```

Grid access: `self.grid[row][col]` where:
- `row`: 0-based row index (0 = top)
- `col`: 0-based column index (0 = left)

## Implementation Details

### Grid Initialization

The `_initialize_grid()` method performs the following steps:

1. **Calculate Grid Dimensions**
   - Get window content size from the native macOS window
   - Divide window width by character width to get columns
   - Divide window height by character height to get rows
   - Use `max(1, ...)` to ensure minimum 1x1 grid

2. **Create Grid Structure**
   - Create a 2D list with calculated dimensions
   - Initialize each cell with `(' ', 0, 0)` (space, default color, no attributes)

3. **Fallback Behavior**
   - If window is not created, use default dimensions (40 rows x 80 columns)
   - Handles initialization before window creation gracefully

### Code Example

```python
def _initialize_grid(self) -> None:
    """
    Initialize the character grid buffer.
    
    Creates a 2D grid based on the window size and character dimensions.
    Each cell in the grid stores:
    - char: The character to display (string)
    - color_pair: The color pair index (int)
    - attributes: Text attributes as bitwise flags (int)
    
    The grid is initialized with spaces using default colors.
    """
    # Get window content size
    if self.window is None or self.metal_view is None:
        # Fallback to reasonable defaults if window not created
        self.rows = 40
        self.cols = 80
    else:
        try:
            import Cocoa
            content_rect = self.window.contentView().frame()
            window_width = int(content_rect.size.width)
            window_height = int(content_rect.size.height)
            
            # Calculate grid dimensions
            self.cols = max(1, window_width // self.char_width)
            self.rows = max(1, window_height // self.char_height)
        except Exception:
            # Fallback to reasonable defaults
            self.rows = 40
            self.cols = 80
    
    # Create grid: list of rows, each row is list of (char, color_pair, attrs) tuples
    self.grid = [
        [(' ', 0, 0) for _ in range(self.cols)]
        for _ in range(self.rows)
    ]
```

## Dimension Calculation

### Character Dimensions

Character dimensions are calculated in `_calculate_char_dimensions()`:
- **char_width**: Width of one character in pixels
- **char_height**: Height of one character in pixels

These are measured from the monospace font using Core Text.

### Grid Dimensions

Grid dimensions are calculated from window size:
```python
cols = window_width // char_width
rows = window_height // char_height
```

Example:
- Window: 1200x800 pixels
- Character: 10x20 pixels
- Grid: 120 columns x 40 rows

## Usage in Drawing Operations

Drawing operations update the grid buffer:

```python
def draw_text(self, row: int, col: int, text: str,
              color_pair: int = 0, attributes: int = 0) -> None:
    """Draw text by updating grid cells."""
    for i, char in enumerate(text):
        if col + i < self.cols and row < self.rows:
            self.grid[row][col + i] = (char, color_pair, attributes)
```

The grid is then rendered to the screen during `refresh()` operations.

## Memory Considerations

### Memory Usage

For a typical desktop window:
- Grid size: 120 columns x 40 rows = 4,800 cells
- Each cell: 3-tuple (char, int, int)
- Approximate memory: ~50-100 KB per grid

This is negligible for modern systems and allows for efficient updates.

### Performance

Grid operations are O(1) for:
- Reading a cell: `self.grid[row][col]`
- Writing a cell: `self.grid[row][col] = (char, color_pair, attrs)`

Full grid iteration is O(rows * cols) but only performed during full refresh.

## Integration with Rendering Pipeline

### Rendering Flow

1. **Application draws** → Updates grid cells
2. **Application calls refresh()** → Renders grid to screen
3. **Metal backend** → Converts grid to GPU draw calls

### Partial Updates

The grid supports partial updates through `refresh_region()`:
- Only specified region of grid is rendered
- Improves performance for localized changes
- Reduces GPU workload

## Testing

### Test Coverage

The implementation is tested in `ttk/test/test_metal_character_grid.py`:

1. **Structure Tests**
   - Grid is 2D list structure
   - Cells are 3-tuples
   - Correct dimensions

2. **Initialization Tests**
   - Cells initialized with spaces
   - Default color pair (0)
   - No attributes (0)

3. **Dimension Tests**
   - Calculated from window size
   - Fallback dimensions work
   - Minimum dimensions enforced

4. **Coordinate System Tests**
   - Origin at top-left (0,0)
   - Character-based coordinates
   - All corners accessible

### Running Tests

```bash
python -m pytest ttk/test/test_metal_character_grid.py -v
```

All tests pass, confirming correct implementation.

## Future Enhancements

### Potential Optimizations

1. **Dirty Region Tracking**
   - Track which cells have changed
   - Only render changed regions
   - Further improve performance

2. **Double Buffering**
   - Maintain two grids (front and back)
   - Swap on refresh
   - Reduce tearing artifacts

3. **Sparse Grid**
   - Use dictionary for non-default cells
   - Reduce memory for mostly-empty grids
   - Trade memory for lookup time

### Image Support

When image rendering is added (Requirement 18):
- Grid may need to support image cells
- Cell format could be extended: `(content, color_pair, attributes, image_data)`
- Coordinate system remains character-based for compatibility

## Related Components

- **MetalBackend**: Main backend class containing the grid
- **_calculate_char_dimensions()**: Calculates character size for grid dimensions
- **_create_native_window()**: Creates window that determines grid size
- **Drawing operations**: Update grid cells (draw_text, draw_rect, etc.)
- **Rendering pipeline**: Converts grid to GPU draw calls

## References

- Design Document: `.kiro/specs/desktop-app-mode/design.md`
- Requirements: `.kiro/specs/desktop-app-mode/requirements.md` (8.1, 8.2)
- Implementation: `ttk/backends/metal_backend.py`
- Tests: `ttk/test/test_metal_character_grid.py`
