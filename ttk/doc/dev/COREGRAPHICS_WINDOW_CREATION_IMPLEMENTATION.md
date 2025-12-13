# CoreGraphics Window Creation Implementation

## Overview

This document describes the implementation of window creation and setup for the CoreGraphics backend (Task 4). The implementation creates native macOS windows using NSWindow with proper configuration for standard window controls.

## Implementation Details

### Window Creation Method (`_create_window`)

The `_create_window` method implements the following functionality:

1. **Dimension Calculation**: Calculates window dimensions from grid size and character dimensions
   ```python
   window_width = self.cols * self.char_width
   window_height = self.rows * self.char_height
   ```

2. **Window Frame**: Creates an NSRect frame positioned at (100, 100) with calculated dimensions

3. **Style Mask Configuration**: Sets up window style with all standard macOS controls:
   - `NSWindowStyleMaskTitled`: Window has a title bar
   - `NSWindowStyleMaskClosable`: Window has a close button
   - `NSWindowStyleMaskMiniaturizable`: Window has a minimize button
   - `NSWindowStyleMaskResizable`: Window can be resized

4. **Window Creation**: Creates NSWindow using `initWithContentRect_styleMask_backing_defer_`
   - Uses `NSBackingStoreBuffered` for efficient rendering
   - Validates window creation and raises RuntimeError if it fails

5. **Window Title**: Sets the window title from the initialization parameter

6. **Content View**: Creates and sets a placeholder NSView as the content view

7. **Window Display**: Makes the window visible using `makeKeyAndOrderFront_`

### Grid Initialization Method (`_initialize_grid`)

The `_initialize_grid` method creates the character grid data structure:

- Creates a 2D list with dimensions `rows x cols`
- Each cell is a tuple: `(char, color_pair, attributes)`
- All cells initialized to: `(' ', 0, 0)` (space, default color, no attributes)

### Dimension Query Method (`get_dimensions`)

Returns the current grid dimensions as a tuple `(rows, cols)`.

### Initialization Flow

The `initialize()` method now performs the complete initialization sequence:

1. Load and validate font (`_load_font`)
2. Calculate character dimensions (`_calculate_char_dimensions`)
3. Create window and view (`_create_window`)
4. Initialize character grid (`_initialize_grid`)
5. Set up default color pair (0: white on black)

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 1.1**: Creates a native macOS window using NSWindow ✓
- **Requirement 7.1**: Sets window title from initialization parameter ✓
- **Requirement 7.2**: Supports standard macOS window controls (close, minimize, resize) ✓
- **Requirement 2.1**: Creates character grid storing character, color pair, and attributes ✓
- **Requirement 4.5**: Initializes default color pair (0) with white on black ✓

## Testing

### Verification Script

Created `test/verify_coregraphics_window_creation.py` which tests:

1. **Basic Window Creation**: Verifies window is created and is an NSWindow instance
2. **Window Title**: Verifies title is set correctly
3. **Window Dimensions**: Verifies dimensions are calculated from grid size and character dimensions
4. **Window Style Mask**: Verifies all window controls are enabled (title bar, close, minimize, resize)
5. **get_dimensions()**: Verifies method returns correct grid dimensions
6. **Grid Initialization**: Verifies grid is created with correct dimensions and initialized cells
7. **Default Color Pair**: Verifies color pair 0 is initialized to white on black
8. **Window Visibility**: Verifies window is visible after initialization

### Test Results

All 8 tests pass successfully:

```
Test 1: Basic window creation ✓
Test 2: Window title ✓
Test 3: Window dimensions ✓
Test 4: Window style mask ✓
Test 5: get_dimensions() ✓
Test 6: Grid initialization ✓
Test 7: Default color pair ✓
Test 8: Window visibility ✓
```

### Unit Tests

Created `test/test_coregraphics_window_creation.py` with comprehensive pytest tests:

- **TestWindowCreation**: 12 tests covering window creation, title, dimensions, style mask, and visibility
- **TestGridInitialization**: 4 tests covering grid initialization and default color pair

## Code Quality

### Error Handling

- Validates window creation and raises RuntimeError with diagnostic information if it fails
- Follows the project's exception handling policy with specific exception types

### Documentation

- Added comprehensive docstrings for all new methods
- Included inline comments explaining PyObjC method name translations
- Documented the coordinate system and dimension calculations

### Code Organization

- Follows the established pattern from font loading implementation
- Methods are logically organized and single-purpose
- Clear separation between initialization steps

## Integration

The window creation functionality integrates seamlessly with the existing backend:

1. Called from `initialize()` after font loading and dimension calculation
2. Prepares the window for future rendering operations
3. Sets up the grid data structure for drawing operations
4. Establishes the default color pair for text rendering

## Next Steps

With window creation complete, the next tasks are:

- **Task 5**: Implement character grid initialization (already done as part of this task)
- **Task 6**: Implement TTKView custom NSView class
- **Task 7**: Implement TTKView drawRect_ rendering method

The window and grid are now ready for the rendering implementation.

## Files Modified

- `ttk/backends/coregraphics_backend.py`: Added window creation and grid initialization methods
- `ttk/test/test_coregraphics_window_creation.py`: Added comprehensive unit tests
- `ttk/test/verify_coregraphics_window_creation.py`: Added verification script

## Character Dimensions

The implementation uses the character dimensions calculated in Task 3:

- Character width: 8 pixels (for Menlo 14pt)
- Character height: 19 pixels (with 20% line spacing)

For a default 80x24 grid, this produces a window of 640x456 pixels.

## Window Positioning

Windows are positioned at (100, 100) on the screen, providing a reasonable default position that:
- Doesn't obscure the menu bar
- Leaves room for multiple windows
- Is consistent across launches

Future enhancements could add:
- Remembering last window position
- Centering windows on screen
- Multi-monitor support

## Conclusion

Task 4 is complete. The CoreGraphics backend can now create native macOS windows with proper configuration, calculate dimensions correctly, and initialize the character grid data structure. All tests pass and the implementation follows the design document specifications.
