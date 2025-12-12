# CoreGraphics Backend Error Handling Implementation

## Overview

This document describes the error handling implementation for the CoreGraphics backend, covering both initialization errors and runtime operation failures. The implementation ensures that errors are caught gracefully with informative messages while preventing crashes.

## Implementation Details

### Initialization Error Handling

#### PyObjC Availability Check (Requirement 12.1)

**Location**: `CoreGraphicsBackend.__init__()`

**Implementation**:
```python
if not COCOA_AVAILABLE:
    raise RuntimeError(
        "PyObjC is required for CoreGraphics backend. "
        "Install with: pip install pyobjc-framework-Cocoa"
    )
```

**Behavior**:
- Checks the `COCOA_AVAILABLE` flag set during module import
- Raises `RuntimeError` with clear installation instructions
- Prevents backend instantiation when PyObjC is not available

**Error Message Format**:
- States the requirement clearly
- Provides exact installation command
- Specifies the required package name

#### Font Validation (Requirement 12.2)

**Location**: `CoreGraphicsBackend._load_font()`

**Implementation**:
```python
self.font = Cocoa.NSFont.fontWithName_size_(self.font_name, self.font_size)
if not self.font:
    raise ValueError(
        f"Font '{self.font_name}' not found. "
        f"Use a valid monospace font like 'Menlo', 'Monaco', or 'Courier'."
    )
```

**Behavior**:
- Attempts to load the specified font using NSFont
- Checks if font loading succeeded (returns None on failure)
- Raises `ValueError` with the invalid font name
- Suggests valid alternative monospace fonts

**Error Message Format**:
- Includes the invalid font name for debugging
- Provides specific suggestions for valid fonts
- Explains the requirement (monospace fonts)

#### Window Creation Validation (Requirement 12.5)

**Location**: `CoreGraphicsBackend._create_window()`

**Implementation**:
```python
self.window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
    frame,
    style_mask,
    Cocoa.NSBackingStoreBuffered,
    False
)

if not self.window:
    raise RuntimeError(
        "Failed to create window. Check system resources and permissions."
    )
```

**Behavior**:
- Attempts to create NSWindow with calculated dimensions
- Verifies window creation succeeded
- Raises `RuntimeError` with diagnostic guidance
- Suggests checking system resources and permissions

**Error Message Format**:
- States the failure clearly
- Provides troubleshooting hints
- Indicates potential causes (resources, permissions)

### Runtime Error Handling

#### Color Pair Validation (Requirement 12.3)

**Location**: `CoreGraphicsBackend.init_color_pair()`

**Implementation**:
```python
# Validate color pair ID is in range 1-255
if pair_id < 1 or pair_id > 255:
    raise ValueError(
        f"Color pair ID must be 1-255, got {pair_id}. "
        f"Color pair 0 is reserved for default colors."
    )

# Validate RGB components are in range 0-255
for component in fg_color:
    if component < 0 or component > 255:
        raise ValueError(
            f"RGB components must be 0-255, got {component} in foreground color"
        )

for component in bg_color:
    if component < 0 or component > 255:
        raise ValueError(
            f"RGB components must be 0-255, got {component} in background color"
        )
```

**Behavior**:
- Validates color pair ID is in valid range (1-255)
- Validates all RGB components are in valid range (0-255)
- Raises `ValueError` with specific invalid value
- Explains valid ranges and special cases (pair 0 reserved)

**Error Message Format**:
- States the valid range clearly
- Includes the invalid value for debugging
- Distinguishes between foreground and background colors
- Explains special cases (color pair 0)

#### Drawing Operation Failures (Requirement 12.4)

**Location**: All drawing methods (`draw_text`, `clear`, `clear_region`, `draw_hline`, `draw_vline`, `draw_rect`, `refresh`, `refresh_region`)

**Implementation Pattern**:
```python
def draw_text(self, row: int, col: int, text: str,
              color_pair: int = 0, attributes: int = 0) -> None:
    try:
        # Drawing operation logic...
    except Exception as e:
        # Log warning but continue execution without crashing
        print(f"Warning: draw_text failed at ({row}, {col}): {e}")
```

**Behavior**:
- Wraps drawing operations in try-except blocks
- Catches all exceptions to prevent crashes
- Prints warning message with context
- Continues execution without raising exception
- Includes operation name and parameters in warning

**Error Message Format**:
- Starts with "Warning:" to indicate non-fatal error
- Includes operation name for identification
- Includes relevant parameters (coordinates, dimensions)
- Includes exception details for debugging

## Error Handling Strategy

### Exception Types

1. **RuntimeError**: Used for system-level failures
   - PyObjC not available
   - Window creation failure
   - Indicates environmental or system issues

2. **ValueError**: Used for invalid input values
   - Invalid font name
   - Color pair ID out of range
   - RGB component out of range
   - Indicates programming errors or invalid configuration

3. **Exception**: Catch-all for drawing operations
   - Prevents crashes from unexpected errors
   - Allows application to continue running
   - Logs warnings for debugging

### Error Message Guidelines

All error messages follow these principles:

1. **Clear Statement**: State what went wrong clearly
2. **Context**: Include relevant values and parameters
3. **Guidance**: Provide troubleshooting hints or valid alternatives
4. **Actionable**: Tell the user what they can do to fix it

### Graceful Degradation

Drawing operations are designed to fail gracefully:

1. **No Crashes**: Exceptions are caught and logged
2. **Continue Execution**: Application keeps running
3. **Warning Messages**: Errors are reported but not fatal
4. **Coordinate Validation**: Out-of-bounds coordinates are handled before operations

## Testing

### Test Coverage

The error handling implementation is tested in `test/test_coregraphics_error_handling.py`:

1. **test_pyobjc_not_available_raises_runtime_error**
   - Verifies RuntimeError when PyObjC is not available
   - Checks error message includes installation instructions

2. **test_invalid_font_raises_value_error**
   - Verifies ValueError when font is not found
   - Checks error message includes font name and suggestions

3. **test_window_creation_failure_raises_runtime_error**
   - Verifies RuntimeError when window creation fails
   - Checks error message includes diagnostic guidance

4. **test_color_pair_id_out_of_range_raises_value_error**
   - Verifies ValueError for invalid color pair IDs
   - Tests both too low (0) and too high (256) values
   - Checks error message explains valid range

5. **test_rgb_component_out_of_range_raises_value_error**
   - Verifies ValueError for invalid RGB components
   - Tests both foreground and background colors
   - Tests both too low and too high values

6. **test_drawing_operations_handle_failures_gracefully**
   - Verifies drawing operations don't crash on errors
   - Checks warning messages are printed
   - Tests all drawing methods

7. **test_refresh_operations_handle_failures_gracefully**
   - Verifies refresh operations don't crash on errors
   - Checks warning messages are printed
   - Tests both full and region refresh

### Test Strategy

Tests use mocking to simulate error conditions:
- Mock PyObjC modules to simulate unavailability
- Mock NSFont to return None (font not found)
- Mock NSWindow to return None (window creation failure)
- Corrupt internal state to trigger drawing failures
- Mock view methods to raise exceptions

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 12.1**: PyObjC availability check with installation instructions
- **Requirement 12.2**: Font validation with clear error message
- **Requirement 12.3**: Color pair and RGB validation with range information
- **Requirement 12.4**: Drawing operation failures handled with warnings
- **Requirement 12.5**: Window creation validation with diagnostic information

## Design Decisions

### Why RuntimeError for System Issues?

RuntimeError is used for environmental issues (PyObjC missing, window creation failure) because:
- These are not programming errors
- They indicate system or environment problems
- They require external action to fix (install PyObjC, check resources)

### Why ValueError for Invalid Inputs?

ValueError is used for invalid input values because:
- These are programming errors or configuration issues
- They indicate incorrect usage of the API
- They can be fixed by changing the input values

### Why Catch-All Exception for Drawing?

Drawing operations use catch-all exception handling because:
- Drawing should never crash the application
- Many different exceptions could occur (IndexError, KeyError, etc.)
- The application should continue running even if drawing fails
- Warnings provide debugging information without crashing

### Why Print Instead of Logging?

Print statements are used for warnings because:
- TTK is a library and shouldn't require a logging framework
- Print statements work in all environments
- Applications can redirect stdout if needed
- Simple and straightforward for debugging

## Future Enhancements

Potential improvements for error handling:

1. **Optional Logging Integration**: Allow applications to provide a logger
2. **Error Callbacks**: Allow applications to register error handlers
3. **Error Statistics**: Track error frequency for debugging
4. **Retry Logic**: Automatically retry failed operations
5. **Fallback Rendering**: Use simpler rendering when operations fail

## Related Documentation

- [CoreGraphics Backend Implementation](COREGRAPHICS_BACKEND_IMPLEMENTATION.md)
- [CoreGraphics Initialization](COREGRAPHICS_INITIALIZATION_IMPLEMENTATION.md)
- [CoreGraphics Drawing Operations](COREGRAPHICS_DRAWING_OPERATIONS_IMPLEMENTATION.md)
- [Requirements Document](../../.kiro/specs/coregraphics-backend/requirements.md)
