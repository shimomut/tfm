# CoreGraphics TTKView Implementation

## Overview

This document describes the implementation of the TTKView custom NSView class for the CoreGraphics backend. TTKView is a crucial component that handles rendering the character grid and receiving keyboard input.

## Implementation Summary

### TTKView Class

TTKView is implemented as a proper NSView subclass using PyObjC's Objective-C bridge. The class provides:

1. **Custom Initialization**: `initWithFrame_backend_` method that stores a reference to the CoreGraphicsBackend
2. **Keyboard Input Support**: `acceptsFirstResponder` method that returns True to receive keyboard events
3. **Rendering Method**: `drawRect_` method for rendering the character grid (placeholder for now)

### Key Features

#### 1. NSView Subclass
```python
class TTKView(Cocoa.NSView):
    """Custom NSView subclass for rendering the TTK character grid."""
```

The class properly inherits from `Cocoa.NSView`, making it a native macOS view component that integrates with the Cocoa event loop.

#### 2. Custom Initializer

The `initWithFrame_backend_` method follows PyObjC naming conventions for Objective-C methods with multiple parameters:

```python
def initWithFrame_backend_(self, frame, backend):
    """Initialize the TTK view with a frame and backend reference."""
    self = objc.super(TTKView, self).initWithFrame_(frame)
    if self is None:
        return None
    self.backend = backend
    return self
```

This method:
- Calls the superclass initializer using `objc.super()`
- Stores a reference to the CoreGraphicsBackend for accessing the character grid
- Returns the initialized instance

#### 3. Keyboard Input Support

The `acceptsFirstResponder` method enables keyboard input:

```python
def acceptsFirstResponder(self):
    """Indicate that this view can receive keyboard focus."""
    return True
```

Without this method returning True, the view would not receive keyboard events, which are essential for TTK applications.

#### 4. Rendering Method

The `drawRect_` method is the placeholder for rendering:

```python
def drawRect_(self, rect):
    """Render the character grid."""
    pass  # Will be implemented in task 7
```

This method will be fully implemented in the next task to iterate through the character grid and render each cell.

### Backend Integration

The CoreGraphicsBackend's `_create_window` method was updated to create a TTKView instance:

```python
# Create and set up the custom TTKView
content_rect = self.window.contentView().frame()
self.view = TTKView.alloc().initWithFrame_backend_(content_rect, self)
self.window.setContentView_(self.view)
```

This ensures that:
1. The view is created with the correct frame size
2. The view has a reference to the backend
3. The view is set as the window's content view
4. The view is ready to receive keyboard input and render content

## Requirements Satisfied

### Requirement 8.1: TTKView as NSView Subclass
✓ TTKView is properly implemented as a subclass of NSView using PyObjC

### Requirement 8.5: Store Backend Reference
✓ TTKView implements `initWithFrame_backend_` to store a reference to the CoreGraphicsBackend

### Requirement 6.5: Keyboard Input Support
✓ TTKView implements `acceptsFirstResponder` to return True for receiving keyboard input

## Testing

### Unit Tests

The implementation includes comprehensive unit tests in `test/test_coregraphics_ttkview.py`:

1. **test_ttkview_is_nsview_subclass**: Verifies TTKView is a proper NSView subclass
2. **test_ttkview_initialization**: Verifies initialization with frame and backend
3. **test_ttkview_accepts_first_responder**: Verifies keyboard input support
4. **test_ttkview_has_drawrect_method**: Verifies drawRect_ method exists
5. **test_ttkview_integration_with_backend**: Verifies integration with CoreGraphicsBackend

All tests pass successfully.

### Verification Script

A verification script (`test/verify_coregraphics_ttkview.py`) demonstrates the implementation:

```
Tests passed: 5/5

✓ All verifications passed!

TTKView is properly implemented as an NSView subclass with:
  - Custom initializer (initWithFrame_backend_)
  - Backend reference storage
  - Keyboard input support (acceptsFirstResponder)
  - Rendering method (drawRect_)
  - Full integration with CoreGraphicsBackend
```

## PyObjC Considerations

### Method Name Translation

PyObjC translates Objective-C method names to Python:
- `initWithFrame:` becomes `initWithFrame_()`
- `initWithFrame:backend:` becomes `initWithFrame_backend_()`
- Underscores separate parameter names

### Superclass Initialization

The proper way to call superclass methods in PyObjC:
```python
self = objc.super(TTKView, self).initWithFrame_(frame)
```

This ensures the Objective-C runtime properly initializes the view.

### Return Value

Custom initializers must return `self` or `None`:
```python
if self is None:
    return None
return self
```

This follows Objective-C conventions for initialization.

## Next Steps

The next task (Task 7) will implement the `drawRect_` method to:
1. Iterate through the character grid
2. Skip empty cells for performance
3. Calculate pixel positions using coordinate transformation
4. Draw background rectangles for each cell
5. Create NSAttributedString for each character
6. Draw characters at calculated positions

## Files Modified

1. `ttk/backends/coregraphics_backend.py`:
   - Implemented TTKView class as NSView subclass
   - Updated `_create_window` to use TTKView

2. `ttk/test/test_coregraphics_ttkview.py`:
   - Created comprehensive unit tests

3. `ttk/test/verify_coregraphics_ttkview.py`:
   - Created verification script

## Conclusion

The TTKView class is now properly implemented as a custom NSView subclass with all required functionality for backend integration and keyboard input support. The implementation follows PyObjC best practices and integrates seamlessly with the CoreGraphicsBackend.
