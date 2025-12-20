# IME Support Implementation

## Overview

This document describes the implementation of Input Method Editor (IME) support in the CoreGraphics backend for TTK. IME support enables users to input text in languages that require composition, such as Japanese (Hiragana, Katakana, Kanji), Chinese (Pinyin), and Korean (Hangul).

The implementation follows the macOS NSTextInputClient protocol and integrates with the existing TTK event system to deliver composed text as CharEvents to the application.

## Architecture

### Protocol Conformance

The TTKView class explicitly declares conformance to the NSTextInputClient protocol:

```python
class TTKView(Cocoa.NSView, protocols=[objc.protocolNamed('NSTextInputClient')]):
```

**Critical Implementation Detail**: The protocol must be declared in the class definition using the `protocols` parameter. Attempting to add protocol conformance after class creation (e.g., `TTKView.pyobjc_protocols = [...]`) does not work properly with PyObjC.

### NSTextInputContext Management

The NSTextInputContext is the bridge between macOS IME system and the application:

1. **Creation**: Created in `initWithFrame_backend_()` and stored in `self._input_context`
   ```python
   self._input_context = Cocoa.NSTextInputContext.alloc().initWithClient_(self)
   ```

2. **Activation**: Activated when view becomes first responder
   ```python
   def becomeFirstResponder(self):
       result = objc.super(TTKView, self).becomeFirstResponder()
       if result:
           input_context = self.inputContext()
           if input_context:
               input_context.activate()
       return result
   ```

3. **Deactivation**: Deactivated when view loses focus, clearing any active composition
   ```python
   def resignFirstResponder(self):
       input_context = self.inputContext()
       if input_context:
           input_context.deactivate()
       if self.hasMarkedText():
           self.unmarkText()
       return objc.super(TTKView, self).resignFirstRespononder()
   ```

### IME State Tracking

Three instance variables track the current composition state:

```python
self.marked_text = ""  # Current composition text
self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)  # Composition range
self.selected_range = Cocoa.NSMakeRange(0, 0)  # Selection within composition
```

- **marked_text**: The current composition string (e.g., "あああ" during Japanese input)
- **marked_range**: Location and length of composition; location is NSNotFound when no composition is active
- **selected_range**: Selection within the composition text (used by some IME systems)

## Key Event Flow

### Normal Operation (No IME Composition)

1. User presses key
2. `keyDown_()` called by macOS
3. Translate NSEvent to KeyEvent
4. Deliver KeyEvent to application via `on_key_event()`
5. If consumed by application, return
6. If not consumed, call `interpretKeyEvents_()` to allow IME or character input

### During IME Composition

1. User presses key with IME active
2. `keyDown_()` called by macOS
3. Check if composition is active via `hasMarkedText()`
4. If composition active, pass directly to `interpretKeyEvents_()`
5. macOS calls `setMarkedText_selectedRange_replacementRange_()` to update composition
6. User continues typing, step 5 repeats with updated composition
7. User presses Enter to commit
8. macOS calls `insertText_replacementRange_()` with final text
9. Generate CharEvent for each character and deliver to application

### Key Consumption During Composition

When IME composition is active, certain keys are consumed by the IME system:
- **Enter**: Commits composition (does not generate KeyEvent)
- **Arrow keys**: Navigate within composition (does not generate KeyEvent)
- **Space**: Cycles through candidate characters (does not generate KeyEvent)
- **Escape**: Cancels composition (does not generate KeyEvent)

Command keys (Cmd+C, Cmd+V, etc.) are delivered to the application even during composition.

## NSTextInputClient Protocol Methods

### Core State Methods

#### hasMarkedText()
Returns True if IME composition is active.

```python
def hasMarkedText(self) -> bool:
    return self.marked_range.location != Cocoa.NSNotFound
```

#### markedRange()
Returns the range of composition text.

```python
def markedRange(self):
    return self.marked_range
```

#### selectedRange()
Returns the selection within composition text.

```python
def selectedRange(self):
    return self.selected_range
```

#### validAttributesForMarkedText()
Returns empty array for basic IME support without custom attributes.

```python
def validAttributesForMarkedText(self):
    return []
```

### Composition Handling Methods

#### setMarkedText_selectedRange_replacementRange_()
Called repeatedly during composition to update marked text.

**Flow**:
1. Extract plain text from NSString or NSAttributedString
2. Update `marked_text` instance variable
3. Update `marked_range` based on text length
4. Store `selected_range` parameter
5. Trigger redraw via `setNeedsDisplay_(True)`

**Example**: User types 'a' with Japanese IME
- First call: `setMarkedText("あ", ...)`
- Second call: `setMarkedText("ああ", ...)`
- Third call: `setMarkedText("あああ", ...)`

#### unmarkText()
Clears composition state without committing text.

**Called when**:
- User presses Escape during composition
- Focus changes while composition is active
- Dialog closes with active composition

**Flow**:
1. Clear `marked_text` to empty string
2. Reset `marked_range` to NSNotFound location
3. Reset `selected_range` to zero-length
4. Trigger redraw via `setNeedsDisplay_(True)`

#### insertText_replacementRange_()
Commits composition and generates CharEvents.

**Flow**:
1. Clear marked text state by calling `unmarkText()`
2. Extract plain text from NSString or NSAttributedString
3. Generate CharEvent for each character in the text
4. Deliver CharEvent via `backend.event_callback.on_char_event()`
5. Trigger redraw via `setNeedsDisplay_(True)`

**Example**: User commits "あああ"
```python
# insertText called with "あああ"
for char in "あああ":
    char_event = CharEvent(char=char)
    backend.event_callback.on_char_event(char_event)
# Result: Three CharEvents delivered to application
```

### Positioning Methods

#### firstRectForCharacterRange_actualRange_()
Provides screen coordinates for IME candidate window positioning.

**Coordinate System Transformation**:
- TTK uses top-left origin: (0, 0) at top-left, row increases downward
- CoreGraphics uses bottom-left origin: (0, 0) at bottom-left, y increases upward

**Transformation formula**:
```python
x_pixel = col * char_width
y_pixel = (rows - row - 1) * char_height
```

**Flow**:
1. Get cursor position from `backend.cursor_row` and `backend.cursor_col`
2. Convert to pixel coordinates using `char_width` and `char_height`
3. Apply coordinate system transformation (TTK to CoreGraphics)
4. Create NSRect at cursor position with character dimensions
5. Convert from view coordinates to window coordinates
6. Convert from window coordinates to screen coordinates
7. Fill `actual_range` parameter if provided (with error handling)
8. Return screen rectangle

**PyObjC Pointer Handling**: The `actual_range` parameter is an output pointer that can cause PyObjC errors. The implementation wraps the assignment in try-except to handle this gracefully:

```python
if actual_range is not None:
    try:
        actual_range[0] = char_range
    except (TypeError, AttributeError):
        # actual_range is optional - macOS will use char_range if not set
        pass
```

#### attributedSubstringForProposedRange_actualRange_()
Provides font information for IME composition text.

**Flow**:
1. Check if `backend.font` exists
2. Create attributes dictionary with NSFontAttributeName set to `backend.font`
3. Create NSAttributedString with single space character and attributes
4. Fill `actual_range` parameter if provided
5. Return attributed string (or None if font is not available)

This ensures the IME composition text matches the application's font size and style.

### Command Handling Methods

#### doCommandBySelector_()
Handles special keys that don't produce text (arrow keys, delete, function keys).

**Flow**:
1. Get current NSEvent
2. Translate to KeyEvent
3. Deliver KeyEvent to application via `on_key_event()`

#### characterIndexForPoint_()
Returns character index for a given screen position.

For TFM, this feature is not supported (clicking to position cursor in composition text), so the method returns NSNotFound.

## Cursor Position Tracking

### Backend Implementation

The CoreGraphicsBackend tracks cursor position for IME positioning:

```python
# In __init__
self.cursor_row = 0
self.cursor_col = 0

def set_cursor_position(self, row, col):
    """Set cursor position with bounds checking."""
    self.cursor_row = max(0, min(row, self.rows - 1))
    self.cursor_col = max(0, min(col, self.cols - 1))
```

### Integration with TTK

The `set_caret_position()` method was updated to actually update cursor position:

```python
def set_caret_position(self, x, y):
    """Set caret position for IME positioning."""
    # Note: x is column, y is row in TTK convention
    self.set_cursor_position(y, x)
```

This fixes both marked text rendering and candidate window positioning by ensuring the backend always knows where the cursor is.

## Composition Text Rendering

Marked text is rendered in `drawRect_()` after cursor drawing:

1. Check if composition is active via `hasMarkedText()`
2. Get cursor position from backend
3. Render composition text at cursor position
4. Use yellow background (RGB: 255, 255, 200) for visual feedback
5. Add underline to match macOS IME conventions

**Debug Output**: When `TFM_DEBUG=1`, the rendering code outputs debug information about marked text position and content.

## Error Handling

### Bounds Checking

The `set_cursor_position()` method clamps cursor position to valid range:

```python
self.cursor_row = max(0, min(row, self.rows - 1))
self.cursor_col = max(0, min(col, self.cols - 1))
```

### Null Checks

All IME methods include null checks for critical objects:

- `insertText_()`: Checks if `event_callback` exists before generating CharEvent
- `firstRectForCharacterRange_()`: Checks if window exists before coordinate conversion
- `attributedSubstringForProposedRange_()`: Checks if `backend.font` exists

### PyObjC Pointer Warnings

The implementation suppresses harmless PyObjC pointer warnings:

```python
import warnings
warnings.filterwarnings('ignore', category=objc.ObjCPointerWarning)
```

These warnings are expected PyObjC behavior when working with output parameters and don't affect functionality.

## Debug Mode Support

IME implementation integrates with TFM's debug mode:

- Enable with `--debug` flag or `TFM_DEBUG=1` environment variable
- Provides dual output to both log pane and terminal
- Shows IME method calls, coordinate transformations, and state changes
- Helps troubleshoot IME issues during development

See `doc/dev/DEBUG_MODE_IMPLEMENTATION.md` for details on debug mode.

## Supported Languages

The implementation supports all IME-based input methods:

- **Japanese**: Hiragana, Katakana, Kanji conversion
- **Chinese**: Pinyin input with character selection
- **Korean**: Hangul composition
- **Other**: Any language using macOS IME system

## Testing

### Demo Script

`demo/demo_japanese_ime_test.py` - Interactive demo for testing Japanese IME input

### Test Files

Created during development (in `temp/` directory):
- `test_ime_protocol_conformance.py` - Verifies all NSTextInputClient methods
- `test_nstextinputcontext_activation.py` - Tests input context activation
- `test_ime_key_consumption.py` - Tests key consumption during composition
- `test_ime_setmarkedtext_verification.py` - Interactive test with real IME

### Manual Testing Steps

1. Switch to Japanese IME (Hiragana mode)
2. Run demo script: `python demo/demo_japanese_ime_test.py`
3. Click on the window to focus
4. Type characters (e.g., 'a', 'i', 'u')
5. Watch composition text appear with yellow background
6. Press Enter to commit
7. Verify CharEvents are generated

## Critical Implementation Lessons

### 1. Protocol Declaration Syntax

**Problem**: Protocol conformance added after class creation doesn't work.

**Solution**: Declare protocol in class definition:
```python
class TTKView(Cocoa.NSView, protocols=[objc.protocolNamed('NSTextInputClient')]):
```

### 2. Class Caching Issues

**Problem**: Using `objc.lookUpClass('TTKView')` returns old class versions without updated methods.

**Solution**: Always create fresh class definition, don't reuse from Objective-C runtime.

### 3. First Responder Activation

**Problem**: IME doesn't work without proper first responder setup.

**Solution**: Activate input context in `becomeFirstResponder()` and deactivate in `resignFirstResponder()`.

### 4. Cursor Position Tracking

**Problem**: IME candidate window appears at wrong position.

**Solution**: Implement `set_cursor_position()` and update it from `set_caret_position()`.

### 5. Key Event Flow

**Problem**: Application key bindings interfere with IME composition.

**Solution**: Check `hasMarkedText()` in `keyDown_()` and pass directly to `interpretKeyEvents_()` during composition. This ensures IME gets priority during composition while still delivering KeyEvents to the application when composition is not active.

### 6. Callback Requirement

**Problem**: IME doesn't work without event callback set.

**Solution**: TTK requires event callback to be set via `set_event_callback()` before running the event loop. IME events are delivered via `on_key_event()` and `on_char_event()` callback methods.

## Integration with TTK Event System

The IME implementation integrates seamlessly with TTK's callback-only event system:

1. **KeyEvent**: Delivered via `on_key_event()` for keys that don't start composition
2. **CharEvent**: Generated when composition is committed via `insertText_()` and delivered via `on_char_event()`
3. **Event Callback**: Uses the required `backend.event_callback` interface

**Callback Requirement**: The event callback must be set via `set_event_callback()` before running the event loop. IME functionality requires callback mode - there is no polling mode support.

This allows TFM and other TTK applications to handle IME input without any changes to their event handling code, as long as they implement the EventCallback interface.

## Future Enhancements

Potential improvements not yet implemented:

1. **Multi-level composition**: Support for complex IME systems with multiple composition stages
2. **Composition text styling**: Custom attributes for marked text (colors, fonts)
3. **Inline candidate window**: Display candidates within the text area
4. **Composition history**: Track and replay composition sequences
5. **Language-specific optimizations**: Tuning for specific IME systems

## References

- Apple NSTextInputClient Protocol: https://developer.apple.com/documentation/appkit/nstextinputclient
- PyObjC Documentation: https://pyobjc.readthedocs.io/
- TFM Debug Mode: `doc/dev/DEBUG_MODE_IMPLEMENTATION.md`
- TTK Event System: `doc/dev/EVENT_HANDLING_IMPLEMENTATION.md`

## Related Files

### Implementation
- `ttk/backends/coregraphics_backend.py` - Core IME implementation
  - Lines ~2970: TTKView class declaration with protocol conformance
  - Lines ~3027: IME state tracking initialization
  - Lines ~3322: NSTextInputContext creation
  - Lines ~3335: inputContext() method
  - Lines ~3400: keyDown_() method with IME key consumption
  - Lines ~3450: NSTextInputClient protocol methods
  - Lines ~3661: becomeFirstResponder/resignFirstResponder

### Testing
- `demo/demo_japanese_ime_test.py` - Interactive IME demo
- `temp/test_ime_*.py` - Various IME test scripts

### Documentation
- `temp/IME_IMPLEMENTATION_COMPLETE.md` - Implementation summary
- `temp/IME_SUCCESS.md` - Root cause analysis and fixes
- `temp/IME_VERIFICATION_COMPLETE.md` - Verification results
