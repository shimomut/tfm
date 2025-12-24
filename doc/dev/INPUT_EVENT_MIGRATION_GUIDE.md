# KeyEvent to KeyEvent/SystemEvent Migration

## Overview

TFM has migrated from using the generic `KeyEvent` class to using specific event types: `KeyEvent` for keyboard input and `SystemEvent` for system-level events like window resize.

## Migration Date

December 14, 2025

## Rationale

The TTK library evolved to provide more specific event types that better represent the nature of different events:

- **KeyEvent**: Represents keyboard input (key presses, modifiers, characters)
- **SystemEvent**: Represents system-level events (resize, close, etc.)
- **MouseEvent**: Represents mouse input (clicks, movement, scrolling)

This separation provides:
1. **Type Safety**: Clearer distinction between event types
2. **Better API**: Each event type has methods specific to its purpose
3. **Maintainability**: Easier to understand and extend event handling

## Changes Made

### 1. Import Statements

**Before:**
```python
from ttk.input_event import KeyEvent, KeyCode, ModifierKey
```

**After:**
```python
from ttk import KeyEvent, KeyCode, ModifierKey, SystemEvent, SystemEventType
```

### 2. Event Type Handling

**Before:**
```python
if event.key_code == KeyCode.RESIZE:
    handle_resize()
```

**After:**
```python
if isinstance(event, SystemEvent) and event.is_resize():
    handle_resize()
```

### 3. Event Creation

**Before:**
```python
event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
```

**After:**
```python
event = KeyEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
```

### 4. Type Hints

**Before:**
```python
def handle_key(self, event: KeyEvent) -> bool:
    pass
```

**After:**
```python
def handle_key(self, event: KeyEvent) -> bool:
    pass
```

## API Compatibility

The `KeyEvent` class maintains the same attributes as the old `KeyEvent`:
- `key_code`: int - KeyCode value or Unicode code point
- `modifiers`: int - Bitwise OR of ModifierKey values
- `char`: Optional[str] - Character for printable keys

Additional methods:
- `is_printable()`: Check if this is a printable character
- `is_special_key()`: Check if this is a special key
- `has_modifier(modifier)`: Check if a specific modifier is pressed

## SystemEvent API

The `SystemEvent` class provides:
- `event_type`: int - SystemEventType value (RESIZE, CLOSE, etc.)
- `is_resize()`: Check if this is a window resize event

For backward compatibility, SystemEvent also provides:
- `key_code` property: Returns event_type
- `modifiers` property: Returns ModifierKey.NONE
- `char` property: Returns None

## Files Updated

### Source Files (15 files)
- `src/tfm_main.py`
- `src/tfm_input_utils.py`
- `src/tfm_input_compat.py`
- `src/tfm_config.py`
- `src/tfm_text_viewer.py`
- `src/tfm_single_line_text_edit.py`
- `src/tfm_quick_choice_bar.py`
- `src/tfm_base_list_dialog.py`
- `src/tfm_general_purpose_dialog.py`
- `src/tfm_info_dialog.py`
- `src/tfm_jump_dialog.py`
- `src/tfm_list_dialog.py`
- `src/tfm_search_dialog.py`
- `src/tfm_batch_rename_dialog.py`
- `src/tfm_drives_dialog.py`

### Test Files (31 files)
All test files in `test/` directory that used KeyEvent

### TTK Library
- `ttk/__init__.py` - Added SystemEventType export

## Backward Compatibility

The `ensure_input_event()` function in `src/tfm_input_compat.py` has been updated to return `KeyEvent` objects instead of `KeyEvent` objects, maintaining backward compatibility with code that passes integer key codes.

## Testing

All test files have been updated to use `KeyEvent` instead of `KeyEvent`. Run the test suite to verify:

```bash
python3 -m pytest test/
```

## Migration Checklist for Future Code

When writing new code or updating existing code:

- [ ] Import `KeyEvent` instead of `KeyEvent`
- [ ] Import `SystemEvent` and `SystemEventType` if handling system events
- [ ] Use `isinstance(event, SystemEvent)` to check for system events
- [ ] Use `event.is_resize()` instead of `event.key_code == KeyCode.RESIZE`
- [ ] Update type hints from `KeyEvent` to `KeyEvent`
- [ ] Update docstrings to reference `KeyEvent` instead of `KeyEvent`

## References

- TTK Event System: `ttk/input_event.py`
- TTK API Documentation: `ttk/doc/API_REFERENCE.md`
- TFM Input Utilities: `src/tfm_input_utils.py`
