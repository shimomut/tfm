# KeyCode Enhancement Migration Guide

This guide helps you migrate existing TTK applications to use the enhanced KeyCode enum with comprehensive printable character support.

## Table of Contents

- [Overview](#overview)
- [What Changed](#what-changed)
- [Backward Compatibility](#backward-compatibility)
- [Migration Scenarios](#migration-scenarios)
- [Keyboard Layout Selection](#keyboard-layout-selection)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

TTK's KeyCode enum has been enhanced to include all printable characters (letters, digits, symbols) in addition to the existing special keys. This enhancement provides:

- **Consistent key handling** across all key types
- **Physical key representation** (KeyCode values represent physical keys, not characters)
- **Modifier-based variants** (case and symbols handled by Shift modifier)
- **Keyboard layout support** (ANSI layout with extensibility for JIS and ISO)
- **Full backward compatibility** (existing code continues to work)

## What Changed

### New KeyCode Entries

The KeyCode enum now includes:

**Letter Keys (Range: 2000-2025)**
```python
KeyCode.KEY_A = 2000
KeyCode.KEY_B = 2001
# ... through ...
KeyCode.KEY_Z = 2025
```

**Digit Keys (Range: 2100-2109)**
```python
KeyCode.KEY_0 = 2100
KeyCode.KEY_1 = 2101
# ... through ...
KeyCode.KEY_9 = 2109
```

**Symbol Keys (Range: 2200-2299)**
```python
KeyCode.KEY_MINUS = 2200      # - and _
KeyCode.KEY_EQUAL = 2201      # = and +
KeyCode.KEY_LEFT_BRACKET = 2202   # [ and {
KeyCode.KEY_RIGHT_BRACKET = 2203  # ] and }
KeyCode.KEY_BACKSLASH = 2204      # \ and |
KeyCode.KEY_SEMICOLON = 2205      # ; and :
KeyCode.KEY_QUOTE = 2206          # ' and "
KeyCode.KEY_COMMA = 2207          # , and <
KeyCode.KEY_PERIOD = 2208         # . and >
KeyCode.KEY_SLASH = 2209          # / and ?
KeyCode.KEY_GRAVE = 2210          # ` and ~
```

**Space Key**
```python
KeyCode.SPACE = 32  # Using Unicode code point
```

### Key Concepts

1. **Physical Keys**: KeyCode values represent physical keys on the keyboard
2. **Modifier Handling**: Case (uppercase/lowercase) is handled by the Shift modifier flag
3. **Symbol Variants**: Symbol variants (e.g., ! vs 1, @ vs 2) are handled by the Shift modifier
4. **Same KeyCode**: Both shifted and unshifted versions of a key use the same KeyCode

### Unchanged

- All existing special key codes remain unchanged (arrows, function keys, etc.)
- KeyEvent structure remains the same
- Event callback interface remains the same
- Backend initialization remains the same

## Backward Compatibility

### Existing Code Continues to Work

All existing TTK applications will continue to work without modifications:

```python
# This still works exactly as before
if event.key_code == KeyCode.UP:
    move_cursor_up()
elif event.key_code == KeyCode.ENTER:
    execute_command()
elif event.key_code == KeyCode.F1:
    show_help()
```

### Character Code Comparisons

If your code compares against character code points, it will continue to work:

```python
# This still works (legacy approach)
if event.key_code == ord('q'):
    quit_application()
```

However, we recommend migrating to the new KeyCode values for consistency.

## Migration Scenarios

### Scenario 1: Checking for Specific Letters

**Before (using character codes):**
```python
if event.key_code == ord('q'):
    quit_application()
elif event.key_code == ord('h'):
    show_help()
elif event.key_code == ord('j'):
    move_down()
elif event.key_code == ord('k'):
    move_up()
```

**After (using KeyCode enum):**
```python
if event.key_code == KeyCode.KEY_Q:
    quit_application()
elif event.key_code == KeyCode.KEY_H:
    show_help()
elif event.key_code == KeyCode.KEY_J:
    move_down()
elif event.key_code == KeyCode.KEY_K:
    move_up()
```

**Benefits:**
- More readable and self-documenting
- Works consistently across backends
- Easier to maintain and refactor

### Scenario 2: Handling Case-Sensitive Input

**Before (checking character):**
```python
if event.char == 'a':
    action_lowercase_a()
elif event.char == 'A':
    action_uppercase_a()
```

**After (using KeyCode with modifier check):**
```python
if event.key_code == KeyCode.KEY_A:
    if event.has_modifier(ModifierKey.SHIFT):
        action_uppercase_a()
    else:
        action_lowercase_a()
```

**Benefits:**
- Distinguishes between physical key and character
- Handles modifier keys explicitly
- More robust for keyboard shortcuts

### Scenario 3: Digit and Symbol Keys

**Before (using character codes):**
```python
# Checking for digit '5'
if event.key_code == ord('5'):
    select_item_5()

# Checking for symbol '%' (Shift+5)
if event.char == '%':
    show_percentage()
```

**After (using KeyCode enum):**
```python
# Checking for digit '5' key
if event.key_code == KeyCode.KEY_5:
    if event.has_modifier(ModifierKey.SHIFT):
        show_percentage()  # % symbol
    else:
        select_item_5()    # 5 digit
```

**Benefits:**
- Single check for the physical key
- Explicit modifier handling
- Clearer intent

### Scenario 4: Symbol Keys

**Before (using character codes):**
```python
if event.char == '-':
    zoom_out()
elif event.char == '=':
    zoom_in()
elif event.char == '/':
    start_search()
```

**After (using KeyCode enum):**
```python
if event.key_code == KeyCode.KEY_MINUS:
    zoom_out()
elif event.key_code == KeyCode.KEY_EQUAL:
    zoom_in()
elif event.key_code == KeyCode.KEY_SLASH:
    start_search()
```

**Benefits:**
- Consistent with other key handling
- Works regardless of keyboard layout
- More maintainable

### Scenario 5: Space Key

**Before (using character code):**
```python
if event.key_code == ord(' '):
    toggle_selection()
```

**After (using KeyCode enum):**
```python
if event.key_code == KeyCode.SPACE:
    toggle_selection()
```

**Benefits:**
- More readable
- Consistent with other special keys
- Self-documenting

## Keyboard Layout Selection

### Default Behavior

By default, both backends use the ANSI keyboard layout (standard US layout):

```python
# Default: ANSI layout
backend = CoreGraphicsBackend()
backend = CursesBackend()
```

### Explicit Layout Selection

You can explicitly specify the keyboard layout:

```python
# macOS CoreGraphics backend
backend = CoreGraphicsBackend(keyboard_layout='ANSI')

# Curses backend
backend = CursesBackend(keyboard_layout='ANSI')
```

### Future Layout Support

JIS (Japanese) and ISO (European) layouts are not yet implemented but the architecture supports them:

```python
# Future: JIS layout (not yet implemented)
backend = CoreGraphicsBackend(keyboard_layout='JIS')
# Raises: NotImplementedError

# Future: ISO layout (not yet implemented)
backend = CoreGraphicsBackend(keyboard_layout='ISO')
# Raises: NotImplementedError
```

## Best Practices

### 1. Use KeyCode Enum Values

Always use KeyCode enum values instead of character codes:

```python
# ✅ Good
if event.key_code == KeyCode.KEY_Q:
    quit()

# ❌ Avoid
if event.key_code == ord('q'):
    quit()
```

### 2. Check Modifiers Explicitly

When case or symbol variants matter, check modifiers explicitly:

```python
# ✅ Good
if event.key_code == KeyCode.KEY_A:
    if event.has_modifier(ModifierKey.SHIFT):
        handle_uppercase_a()
    else:
        handle_lowercase_a()

# ❌ Avoid
if event.char == 'A':
    handle_uppercase_a()
elif event.char == 'a':
    handle_lowercase_a()
```

### 3. Use Physical Key Representation

Think in terms of physical keys, not characters:

```python
# ✅ Good - represents the physical '5' key
if event.key_code == KeyCode.KEY_5:
    if event.has_modifier(ModifierKey.SHIFT):
        handle_percent_symbol()
    else:
        handle_digit_five()

# ❌ Avoid - mixes physical key and character concepts
if event.char == '5':
    handle_digit_five()
if event.char == '%':
    handle_percent_symbol()
```

### 4. Document Keyboard Shortcuts

Use KeyCode names in documentation for clarity:

```python
# ✅ Good
"""
Keyboard Shortcuts:
- KeyCode.KEY_Q: Quit application
- KeyCode.KEY_H: Show help
- KeyCode.KEY_J: Move down
- KeyCode.KEY_K: Move up
- KeyCode.SPACE: Toggle selection
"""

# ❌ Avoid
"""
Keyboard Shortcuts:
- 'q': Quit application
- 'h': Show help
- 'j': Move down
- 'k': Move up
- ' ': Toggle selection
"""
```

### 5. Handle Both KeyEvent and CharEvent

For text input, handle both KeyEvent (commands) and CharEvent (text):

```python
class TextEditor:
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle commands."""
        if event.key_code == KeyCode.KEY_S and event.has_modifier(ModifierKey.CONTROL):
            self.save()
            return True
        elif event.key_code == KeyCode.LEFT:
            self.move_cursor_left()
            return True
        return False
    
    def on_char_event(self, event: CharEvent) -> bool:
        """Handle text input."""
        self.insert_char(event.char)
        return True
```

## Examples

### Example 1: File Manager Navigation

**Before:**
```python
def handle_key(self, event):
    if event.key_code == ord('j'):
        self.move_cursor_down()
    elif event.key_code == ord('k'):
        self.move_cursor_up()
    elif event.key_code == ord('h'):
        self.go_to_parent_directory()
    elif event.key_code == ord('l'):
        self.enter_directory()
    elif event.key_code == ord('q'):
        self.quit()
```

**After:**
```python
def handle_key(self, event):
    if event.key_code == KeyCode.KEY_J:
        self.move_cursor_down()
    elif event.key_code == KeyCode.KEY_K:
        self.move_cursor_up()
    elif event.key_code == KeyCode.KEY_H:
        self.go_to_parent_directory()
    elif event.key_code == KeyCode.KEY_L:
        self.enter_directory()
    elif event.key_code == KeyCode.KEY_Q:
        self.quit()
```

### Example 2: Text Editor with Shortcuts

**Before:**
```python
def handle_key(self, event):
    # Ctrl+S to save
    if event.char == 's' and event.has_modifier(ModifierKey.CONTROL):
        self.save()
    # Ctrl+C to copy
    elif event.char == 'c' and event.has_modifier(ModifierKey.CONTROL):
        self.copy()
    # Ctrl+V to paste
    elif event.char == 'v' and event.has_modifier(ModifierKey.CONTROL):
        self.paste()
```

**After:**
```python
def handle_key(self, event):
    # Ctrl+S to save
    if event.key_code == KeyCode.KEY_S and event.has_modifier(ModifierKey.CONTROL):
        self.save()
    # Ctrl+C to copy
    elif event.key_code == KeyCode.KEY_C and event.has_modifier(ModifierKey.CONTROL):
        self.copy()
    # Ctrl+V to paste
    elif event.key_code == KeyCode.KEY_V and event.has_modifier(ModifierKey.CONTROL):
        self.paste()
```

### Example 3: Search Dialog

**Before:**
```python
def handle_key(self, event):
    if event.char == '/':
        self.start_search()
    elif event.key_code == KeyCode.ENTER:
        self.execute_search()
    elif event.key_code == KeyCode.ESCAPE:
        self.cancel_search()
```

**After:**
```python
def handle_key(self, event):
    if event.key_code == KeyCode.KEY_SLASH:
        self.start_search()
    elif event.key_code == KeyCode.ENTER:
        self.execute_search()
    elif event.key_code == KeyCode.ESCAPE:
        self.cancel_search()
```

### Example 4: Number Selection

**Before:**
```python
def handle_key(self, event):
    if event.char in '123456789':
        index = int(event.char) - 1
        self.select_item(index)
```

**After:**
```python
def handle_key(self, event):
    # Map KEY_1 through KEY_9 to indices 0-8
    digit_keys = {
        KeyCode.KEY_1: 0,
        KeyCode.KEY_2: 1,
        KeyCode.KEY_3: 2,
        KeyCode.KEY_4: 3,
        KeyCode.KEY_5: 4,
        KeyCode.KEY_6: 5,
        KeyCode.KEY_7: 6,
        KeyCode.KEY_8: 7,
        KeyCode.KEY_9: 8,
    }
    
    if event.key_code in digit_keys:
        index = digit_keys[event.key_code]
        self.select_item(index)
```

## See Also

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Event System](EVENT_SYSTEM.md) - Event handling guide
- [User Guide](USER_GUIDE.md) - Getting started with TTK
- [Backend Implementation Guide](BACKEND_IMPLEMENTATION_GUIDE.md) - How to implement backends
