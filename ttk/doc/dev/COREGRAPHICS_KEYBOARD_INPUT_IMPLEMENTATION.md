# CoreGraphics Backend Keyboard Input Implementation

## Overview

This document describes the implementation of keyboard input handling for the CoreGraphics backend. The implementation provides full support for keyboard events with timeout modes, modifier key detection, and event translation to TTK's unified KeyEvent format.

## Implementation Summary

The keyboard input handling consists of three main components:

1. **`get_input(timeout_ms)`** - Main entry point for retrieving keyboard events
2. **`_translate_event(event)`** - Translates NSEvent to KeyEvent
3. **`_extract_modifiers(event)`** - Extracts modifier key flags

## Architecture

### Event Flow

```
Application calls get_input(timeout_ms)
    ↓
Calculate timeout date based on timeout_ms
    ↓
Call NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_
    ↓
Wait for event (blocking, non-blocking, or with timeout)
    ↓
Receive NSEvent (or None if timeout)
    ↓
Dispatch event with NSApp.sendEvent_
    ↓
Translate NSEvent to KeyEvent
    ↓
Return KeyEvent to application
```

### Timeout Modes

The implementation supports three timeout modes:

1. **Blocking Mode** (`timeout_ms=-1`)
   - Uses `NSDate.distantFuture()` to wait indefinitely
   - Blocks until a keyboard event is available
   - Used for applications that wait for user input

2. **Non-Blocking Mode** (`timeout_ms=0`)
   - Uses `None` as the date to return immediately
   - Returns `None` if no event is available
   - Used for polling input without blocking

3. **Timed Mode** (`timeout_ms>0`)
   - Uses `NSDate.dateWithTimeIntervalSinceNow_(timeout_seconds)`
   - Waits up to the specified timeout for an event
   - Returns `None` if timeout expires without input

## Implementation Details

### get_input Method

```python
def get_input(self, timeout_ms: int = -1) -> Optional[KeyEvent]:
    """
    Get the next input event from the macOS event system.
    
    Args:
        timeout_ms: Timeout in milliseconds.
                   -1: Block indefinitely until input is available
                    0: Non-blocking, return immediately if no input
                   >0: Wait up to timeout_ms milliseconds for input
    
    Returns:
        Optional[KeyEvent]: An KeyEvent object if input is available,
                             or None if the timeout expires with no input.
    """
```

**Key Implementation Points:**

1. **Get NSApplication Instance**
   ```python
   app = Cocoa.NSApplication.sharedApplication()
   ```

2. **Calculate Timeout Date**
   ```python
   if timeout_ms < 0:
       until_date = Cocoa.NSDate.distantFuture()
   elif timeout_ms == 0:
       until_date = None
   else:
       timeout_seconds = timeout_ms / 1000.0
       until_date = Cocoa.NSDate.dateWithTimeIntervalSinceNow_(timeout_seconds)
   ```

3. **Define Event Mask**
   ```python
   event_mask = (
       Cocoa.NSEventMaskKeyDown |
       Cocoa.NSEventMaskKeyUp |
       Cocoa.NSEventMaskFlagsChanged
   )
   ```

4. **Poll for Event**
   ```python
   event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
       event_mask,
       until_date,
       Cocoa.NSDefaultRunLoopMode,
       True  # dequeue the event
   )
   ```

5. **Dispatch Event**
   ```python
   if event is not None:
       app.sendEvent_(event)
   ```

6. **Translate and Return**
   ```python
   return self._translate_event(event)
   ```

### Event Translation

The `_translate_event` method converts NSEvent objects to KeyEvent objects:

**Key Code Mapping:**

```python
key_map = {
    # Arrow keys
    123: KeyCode.LEFT,
    124: KeyCode.RIGHT,
    125: KeyCode.DOWN,
    126: KeyCode.UP,
    
    # Function keys
    122: KeyCode.F1,
    120: KeyCode.F2,
    99: KeyCode.F3,
    118: KeyCode.F4,
    96: KeyCode.F5,
    97: KeyCode.F6,
    98: KeyCode.F7,
    100: KeyCode.F8,
    101: KeyCode.F9,
    109: KeyCode.F10,
    103: KeyCode.F11,
    111: KeyCode.F12,
    
    # Editing keys
    51: KeyCode.BACKSPACE,
    117: KeyCode.DELETE,
    115: KeyCode.HOME,
    119: KeyCode.END,
    116: KeyCode.PAGE_UP,
    121: KeyCode.PAGE_DOWN,
    
    # Special keys
    36: KeyCode.ENTER,
    76: KeyCode.ENTER,  # Numeric keypad
    53: KeyCode.ESCAPE,
    48: KeyCode.TAB,
}
```

**Character Handling:**

For printable characters, the implementation:
1. Extracts the character from `event.characters()`
2. Handles special characters that come through as printable (e.g., '\r', '\t', '\x1b')
3. Returns the character code and character string for regular printable characters

### Modifier Key Extraction

The `_extract_modifiers` method extracts modifier key flags:

```python
def _extract_modifiers(self, event) -> int:
    """Extract modifier key flags from an NSEvent."""
    modifiers = ModifierKey.NONE
    modifier_flags = event.modifierFlags()
    
    if modifier_flags & Cocoa.NSEventModifierFlagShift:
        modifiers |= ModifierKey.SHIFT
    
    if modifier_flags & Cocoa.NSEventModifierFlagControl:
        modifiers |= ModifierKey.CONTROL
    
    if modifier_flags & Cocoa.NSEventModifierFlagOption:
        modifiers |= ModifierKey.ALT
    
    if modifier_flags & Cocoa.NSEventModifierFlagCommand:
        modifiers |= ModifierKey.COMMAND
    
    return modifiers
```

## Event Dispatching

The implementation calls `NSApp.sendEvent_()` to ensure proper event handling by the system. This is important because:

1. It allows the event to be processed by the Cocoa event system
2. It ensures proper window focus and event routing
3. It maintains compatibility with macOS event handling conventions

## Key Code Consistency

The implementation uses standard macOS virtual key codes that are consistent across different keyboard layouts. These key codes are hardware-dependent but stable on macOS:

- **Arrow keys**: 123-126
- **Function keys**: 96-122 (various codes)
- **Editing keys**: 51, 115-121
- **Special keys**: 36, 48, 53, 76

This ensures that the same physical key produces the same key code regardless of keyboard layout or language settings.

## Testing

### Unit Tests

The implementation includes comprehensive unit tests in `test_coregraphics_keyboard_input.py`:

1. **Method Existence Tests**
   - Verify `get_input()` method exists
   - Verify `_translate_event()` helper exists
   - Verify `_extract_modifiers()` helper exists

2. **Non-Blocking Mode Test**
   - Verify `get_input(timeout_ms=0)` returns None when no input available

3. **Modifier Extraction Tests**
   - Test extraction of Shift, Control, Alt, Command keys
   - Test extraction of multiple modifiers simultaneously
   - Test no modifiers case

4. **Event Translation Tests**
   - Test translation returns None for None input
   - Test translation of various event types

### Verification Script

The `verify_coregraphics_keyboard_input.py` script provides manual verification:

1. Creates an interactive window
2. Displays keyboard events as they occur
3. Shows key codes, modifiers, and characters
4. Allows testing of all keyboard input scenarios

**Usage:**
```bash
python ttk/test/verify_coregraphics_keyboard_input.py
```

## Requirements Validation

This implementation satisfies the following requirements:

### Requirement 6: Keyboard Input Handling

✅ **6.1**: NSEvent key codes are translated to TTK KeyEvent objects  
✅ **6.2**: Modifier keys (Shift, Control, Alt, Command) are detected and reported  
✅ **6.3**: Special keys (arrows, function keys, Enter, Escape, etc.) have consistent codes  
✅ **6.4**: Supports blocking, non-blocking, and timed input modes  
✅ **6.5**: TTKView implements `acceptsFirstResponder` to receive keyboard focus

### Requirement 13: Cocoa Event Loop Integration

✅ **13.1**: Uses `NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_` for event retrieval  
✅ **13.2**: Dispatches events using `NSApp.sendEvent_` for proper handling  
✅ **13.3**: Supports `NSDate.distantFuture` for blocking indefinitely  
✅ **13.4**: Uses `NSDate.dateWithTimeIntervalSinceNow_` for timed waits  
✅ **13.5**: Returns None from `get_input` without blocking when timeout is 0

## Performance Considerations

The implementation is efficient because:

1. **Direct Event Polling**: Uses native macOS event queue without intermediate buffers
2. **Minimal Translation**: Simple key code mapping with no complex processing
3. **No Busy Waiting**: Proper use of timeout modes prevents CPU spinning
4. **Event Dispatching**: Ensures proper event handling without blocking the event loop

## Compatibility

The implementation is compatible with:

- **macOS Versions**: All versions supporting PyObjC and Cocoa
- **Keyboard Layouts**: Uses hardware key codes that work across layouts
- **Input Methods**: Works with standard keyboard input and input method editors
- **TTK Applications**: Fully compatible with the Renderer interface

## Known Limitations

1. **macOS Only**: Requires macOS and PyObjC (by design)
2. **Key Up Events**: Currently only processes key down events (key up events are ignored)
3. **Flags Changed Events**: Modifier-only events (flags changed) are not processed
4. **Mouse Events**: Not implemented (keyboard focus only)

## Future Enhancements

Potential future improvements:

1. **Mouse Event Support**: Add mouse click and movement event translation
2. **Key Up Events**: Process key up events for applications that need them
3. **Modifier-Only Events**: Handle modifier key press/release events
4. **Input Method Events**: Better support for complex input methods (e.g., Japanese IME)
5. **Window Resize Events**: Detect and report window resize events

## References

- **Apple Documentation**: [NSEvent Class Reference](https://developer.apple.com/documentation/appkit/nsevent)
- **PyObjC Documentation**: [PyObjC Framework](https://pyobjc.readthedocs.io/)
- **TTK Renderer Interface**: `ttk/renderer.py`
- **TTK KeyEvent**: `ttk/input_event.py`

## Conclusion

The keyboard input implementation provides full support for keyboard events with proper timeout handling, modifier key detection, and event translation. It integrates seamlessly with the Cocoa event loop and maintains compatibility with the TTK Renderer interface.
