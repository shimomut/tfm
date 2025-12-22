# Plan: Merge handle_main_screen_key_event into handle_input

## Summary

Inline the entire `handle_main_screen_key_event()` method (lines 3233-3618, ~385 lines) into `handle_input()` and delete the separate method.

## Current Structure

```python
def handle_input(self, event):
    # Check special modes (isearch, quick_edit_bar, quick_choice_bar)
    if self.isearch_mode:
        ...
    if self.quick_edit_bar.is_active:
        ...
    if self.quick_choice_bar.is_active:
        ...
    
    # Delegate to separate method
    return self.handle_main_screen_key_event(event)

def handle_main_screen_key_event(self, event):
    # 385 lines of main screen key handling
    ...
```

## Target Structure

```python
def handle_input(self, event):
    # Type check
    if not isinstance(event, (KeyEvent, CharEvent)):
        return False
    
    # Check special modes (isearch, quick_edit_bar, quick_choice_bar)
    if self.isearch_mode:
        ...
    if self.quick_edit_bar.is_active:
        ...
    if self.quick_choice_bar.is_active:
        ...
    
    # Handle main screen key events (CharEvents don't reach here)
    if not isinstance(event, KeyEvent):
        return False
    
    # INLINE ALL CONTENT FROM handle_main_screen_key_event HERE
    current_pane = self.get_current_pane()
    
    # Handle Shift+Arrow keys for log scrolling
    if event.key_code == KeyCode.UP and event.modifiers & ModifierKey.SHIFT:
        ...
    # ... (all 385 lines of key handling)
    else:
        return False  # Key was not handled

# DELETE handle_main_screen_key_event() entirely
```

## Implementation Steps

1. **Read handle_main_screen_key_event content** (lines 3233-3618)
   - Skip the method signature and docstring
   - Skip the initial type check (already in handle_input)
   - Keep everything from `current_pane = self.get_current_pane()` onwards

2. **Replace handle_input** (lines 3619-3670)
   - Keep the special mode checks
   - Add CharEvent check before main screen handling
   - Inline all handle_main_screen_key_event content
   - Remove the delegation call

3. **Delete handle_main_screen_key_event** (lines 3233-3618)
   - Remove the entire method

## Benefits

1. **Single Entry Point**: One method for all FileManager input
2. **No Method Call Overhead**: Direct handling without delegation
3. **Easier to Understand**: All input handling in one place
4. **Simpler Code Flow**: No jumping between methods

## File Locations

- **File**: `src/tfm_main.py`
- **handle_main_screen_key_event**: Lines 3233-3618 (~385 lines)
- **handle_input**: Lines 3619-3670 (~51 lines)
- **Total file**: 4032 lines

## Notes

- This is a large refactoring (~385 lines to inline)
- The merged method will be ~430 lines total
- No logic changes, just inlining
- FileManagerLayer already calls handle_input(), so no changes needed there
