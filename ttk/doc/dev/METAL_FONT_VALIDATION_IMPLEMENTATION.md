# Metal Font Validation Implementation

## Overview

This document describes the implementation of font validation for the TTK Metal backend, ensuring that only monospace fonts are accepted for proper character grid alignment.

## Implementation Details

### Font Validation Method

The `_validate_font()` method in `MetalBackend` performs the following checks:

1. **Font Existence Check**: Verifies that the specified font is installed on the system
2. **Monospace Verification**: Tests multiple characters to ensure they all have the same width
3. **Clear Error Messages**: Provides helpful error messages with suggestions for valid fonts

### Validation Process

The validation uses Core Text to measure character widths:

```python
def _validate_font(self) -> None:
    # Create NSFont object
    font = Cocoa.NSFont.fontWithName_size_(self.font_name, self.font_size)
    
    # Check if font exists
    if font is None:
        raise ValueError(f"Font '{self.font_name}' not found...")
    
    # Test multiple characters for consistent width
    test_chars = ['i', 'W', 'M', '1', ' ']
    widths = []
    
    for char in test_chars:
        attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            char, {Cocoa.NSFontAttributeName: font}
        )
        widths.append(attr_string.size().width)
    
    # Verify all widths are the same (within tolerance)
    if len(set(round(w, 2) for w in widths)) > 1:
        raise ValueError(f"Font '{self.font_name}' is not monospace...")
```

### Test Characters

The validation tests these characters to ensure consistent width:
- `'i'` - Narrow character in proportional fonts
- `'W'` - Wide character in proportional fonts
- `'M'` - Another wide character
- `'1'` - Numeric character
- `' '` - Space character

If any of these characters have different widths (rounded to 2 decimal places), the font is rejected.

### Error Messages

The implementation provides two types of error messages:

1. **Font Not Found**:
   ```
   Font 'InvalidFont' not found. Please specify a valid monospace font 
   installed on your system. Common monospace fonts: Menlo, Monaco, 
   Courier New, SF Mono
   ```

2. **Proportional Font**:
   ```
   Font 'Helvetica' is not monospace. Character widths vary: [5.0, 12.0, 
   15.0, 8.0, 6.0]. TTK requires monospace fonts for proper character grid 
   alignment. Please use a monospace font like Menlo, Monaco, or Courier New.
   ```

## Integration

The `_validate_font()` method is called during `initialize()`, immediately after creating the Metal device and before creating the window. This ensures that font validation happens early in the initialization process.

## Testing

Comprehensive unit tests verify:
- Valid monospace fonts are accepted
- Proportional fonts are rejected with clear error messages
- Missing fonts are rejected with helpful suggestions
- Error messages suggest alternative monospace fonts
- Font validation is called during initialization

All tests use mocked PyObjC modules to avoid requiring actual macOS frameworks during testing.

## Requirements Satisfied

- **Requirement 17.2**: Metal backend initializes fonts and checks that font is monospace using Core Text
- **Requirement 17.5**: Proportional fonts are rejected with clear error messages

## Files Modified

- `ttk/backends/metal_backend.py` - Contains the `_validate_font()` implementation
- `ttk/test/test_metal_font_validation.py` - Unit tests for font validation

## Next Steps

The next task (Task 14) will implement the Metal character grid initialization, which will use the validated font metrics to create the character buffer.
