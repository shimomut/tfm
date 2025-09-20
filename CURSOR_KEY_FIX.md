# Cursor Key Handling Fix for List and Search Dialogs

## Problem
Key events for caret control (Left, Right, Home, End, etc.) were not being passed to `list_dialog_search_editor` and `search_dialog_pattern_editor`, making text editing frustrating for users.

## Root Cause
Both dialog input handlers were explicitly handling specific keys for list navigation but not passing cursor movement keys to the text editors:

- `curses.KEY_LEFT` and `curses.KEY_RIGHT` were not handled at all
- `curses.KEY_HOME` and `curses.KEY_END` were only used for list navigation (go to top/bottom of list)
- Text editors never received these keys for cursor movement

## Solution Applied

### 1. **Added LEFT/RIGHT Arrow Key Handling**
Both dialogs now explicitly handle `curses.KEY_LEFT` and `curses.KEY_RIGHT` and pass them to the text editors:

```python
elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
    # Let the editor handle cursor movement keys
    if self.list_dialog_search_editor.handle_key(key):
        self.needs_full_redraw = True
    return True
```

### 2. **Smart HOME/END Key Handling**
Implemented intelligent handling of `curses.KEY_HOME` and `curses.KEY_END` that prioritizes text editing when there's text in the field:

```python
elif key == curses.KEY_HOME:  # Home - text cursor or list navigation
    # If there's text in search, let editor handle it for cursor movement
    if self.list_dialog_search_editor.text:
        if self.list_dialog_search_editor.handle_key(key):
            self.needs_full_redraw = True
    else:
        # If no search text, use for list navigation
        if self.list_dialog_filtered_items:
            self.list_dialog_selected = 0
            self.list_dialog_scroll = 0
            self.needs_full_redraw = True
    return True
```

## Behavior Changes

### **List Dialog Search (`list_dialog_search_editor`)**
- ✅ **LEFT/RIGHT arrows**: Move cursor within search text
- ✅ **HOME key**: 
  - If search text exists → Move cursor to beginning of text
  - If search text is empty → Go to top of list
- ✅ **END key**: 
  - If search text exists → Move cursor to end of text  
  - If search text is empty → Go to bottom of list

### **Search Dialog Pattern (`search_dialog_pattern_editor`)**
- ✅ **LEFT/RIGHT arrows**: Move cursor within pattern text
- ✅ **HOME key**: 
  - If pattern text exists → Move cursor to beginning of text
  - If pattern text is empty → Go to top of results
- ✅ **END key**: 
  - If pattern text exists → Move cursor to end of text
  - If pattern text is empty → Go to bottom of results

## Files Modified

### `src/tfm_main.py`
- **Lines ~2074-2084**: Added LEFT/RIGHT key handling for list dialog
- **Lines ~2040-2070**: Updated HOME/END key handling for list dialog with smart text/list priority
- **Lines ~4267-4277**: Added LEFT/RIGHT key handling for search dialog  
- **Lines ~4227-4257**: Updated HOME/END key handling for search dialog with smart text/list priority

## Benefits

### **Enhanced User Experience**
- ✅ **Intuitive Text Editing**: Users can now move cursor freely within search/pattern text
- ✅ **Smart Key Behavior**: HOME/END keys work contextually based on whether there's text
- ✅ **Consistent with Other Modes**: Matches behavior of filter, rename, and other text input modes
- ✅ **No Lost Functionality**: List navigation still works when text fields are empty

### **Professional Feel**
- ✅ **Modern Text Editing**: Cursor movement works as expected in any modern application
- ✅ **Reduced Frustration**: Users no longer get stuck when trying to edit text
- ✅ **Better Accessibility**: Proper cursor control improves usability

## Verification

The fix has been verified to:
- ✅ Import successfully without errors
- ✅ Handle LEFT/RIGHT arrow keys for cursor movement
- ✅ Handle HOME/END keys intelligently based on text content
- ✅ Maintain existing list navigation functionality
- ✅ Work consistently across both list dialog and search dialog

## Summary

This fix resolves the cursor key handling issue by:
1. **Adding explicit handling** for LEFT/RIGHT arrow keys
2. **Implementing smart HOME/END behavior** that prioritizes text editing when appropriate
3. **Maintaining backward compatibility** with existing list navigation features
4. **Providing consistent behavior** across both dialog types

Users can now enjoy professional text editing capabilities in both list dialog search and search dialog pattern input fields!