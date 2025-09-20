# SingleLineTextEdit Class Implementation

## Overview

The `SingleLineTextEdit` class is a reusable component that generalizes text editing and caret control functionality for single-line text input fields. It was created to replace the manual text editing logic in the batch rename dialog and can be used throughout the TFM application for consistent text input behavior.

## Features

### Core Text Editing
- **Text Management**: Insert, delete, and modify text content
- **Cursor Control**: Move cursor left, right, home, end with proper bounds checking
- **Key Handling**: Comprehensive key processing for common editing operations
- **Visual Feedback**: Cursor highlighting with reversed colors

### Advanced Features
- **Text Scrolling**: Automatic horizontal scrolling for long text that exceeds display width
- **Length Limits**: Optional maximum text length constraints
- **Safe Rendering**: Boundary-safe text rendering that handles screen edge cases
- **Flexible Display**: Customizable labels and active/inactive states

## Class Interface

### Constructor
```python
SingleLineTextEdit(initial_text="", max_length=None)
```

### Core Methods

#### Text Access
- `get_text()` - Get current text content
- `set_text(text)` - Set text content and adjust cursor
- `clear()` - Clear all text and reset cursor

#### Cursor Control
- `get_cursor_pos()` - Get current cursor position
- `set_cursor_pos(pos)` - Set cursor position with bounds checking
- `move_cursor_left()` - Move cursor left one position
- `move_cursor_right()` - Move cursor right one position
- `move_cursor_home()` - Move cursor to beginning
- `move_cursor_end()` - Move cursor to end

#### Text Editing
- `insert_char(char)` - Insert character at cursor position
- `delete_char_at_cursor()` - Delete character at cursor
- `backspace()` - Delete character before cursor

#### Input Processing
- `handle_key(key)` - Process key input and update text/cursor
- `draw(stdscr, y, x, max_width, label, is_active)` - Render the text field

## Key Handling

The class handles the following key types:

### Navigation Keys
- **Left Arrow** (260, KEY_LEFT) - Move cursor left
- **Right Arrow** (261, KEY_RIGHT) - Move cursor right  
- **Home** (262, KEY_HOME) - Move to beginning
- **End** (269, KEY_END) - Move to end
- **Up Arrow** (259, KEY_UP) - Move to beginning (when `handle_vertical_nav=True`)
- **Down Arrow** (258, KEY_DOWN) - Move to end (when `handle_vertical_nav=True`)

### Editing Keys
- **Backspace** (127, 8, 263, KEY_BACKSPACE) - Delete before cursor
- **Delete** (330, KEY_DC) - Delete at cursor
- **Printable Characters** (32-126) - Insert character

### Vertical Navigation Control
The `handle_key()` method accepts an optional `handle_vertical_nav` parameter:
- When `False` (default): Up/Down keys are not handled, allowing parent dialogs to use them for field navigation
- When `True`: Up/Down keys move cursor to beginning/end of text

### Compatibility
The class handles both curses constants and numeric key codes for maximum compatibility across different terminal environments.

## Usage Examples

### Basic Usage
```python
from src.tfm_single_line_text_edit import SingleLineTextEdit

# Create editor with initial text
editor = SingleLineTextEdit("Hello World")

# Handle user input
if editor.handle_key(key):
    # Key was processed, update display
    needs_redraw = True

# Render the editor
editor.draw(stdscr, y=10, x=5, max_width=50, 
           label="Input: ", is_active=True)
```

### Batch Rename Dialog Integration with Up/Down Navigation
```python
class BatchRenameDialog:
    def __init__(self):
        self.regex_editor = SingleLineTextEdit()
        self.destination_editor = SingleLineTextEdit()
        self.active_field = 'regex'
    
    def handle_input(self, key):
        if key == 9:  # Tab - switch fields
            self.active_field = 'destination' if self.active_field == 'regex' else 'regex'
        elif key == 259:  # Up arrow - move to regex field
            self.active_field = 'regex'
        elif key == 258:  # Down arrow - move to destination field
            self.active_field = 'destination'
        else:
            # Let active editor handle the key (Up/Down not handled by editor)
            active_editor = self.get_active_editor()
            return active_editor.handle_key(key)
    
    def draw(self, stdscr):
        # Draw regex field
        self.regex_editor.draw(stdscr, 5, 10, 60, "Regex: ", 
                              is_active=(self.active_field == 'regex'))
        
        # Draw destination field
        self.destination_editor.draw(stdscr, 6, 10, 60, "Dest:  ", 
                                   is_active=(self.active_field == 'destination'))
```

## Benefits of Refactoring

### Code Reduction
The batch rename dialog refactoring demonstrates significant code reduction:
- **Original**: ~120 lines of text editing logic
- **Refactored**: ~40 lines using SingleLineTextEdit
- **Reduction**: 67% fewer lines of code

### Eliminated Complexity
**Before Refactoring:**
```python
# Multiple variables to track
self.batch_rename_regex = ""
self.batch_rename_destination = ""
self.batch_rename_regex_cursor = 0
self.batch_rename_destination_cursor = 0

# Complex key handling with duplicate logic
if key == curses.KEY_LEFT:
    if self.batch_rename_input_mode == 'regex':
        if self.batch_rename_regex_cursor > 0:
            self.batch_rename_regex_cursor -= 1
    else:
        if self.batch_rename_destination_cursor > 0:
            self.batch_rename_destination_cursor -= 1
# ... 100+ more lines of similar logic
```

**After Refactoring:**
```python
# Clean, encapsulated editors
self.regex_editor = SingleLineTextEdit()
self.destination_editor = SingleLineTextEdit()

# Simple key handling
active_editor = self.get_active_editor()
return active_editor.handle_key(key)
```

### Improved Maintainability
- **Centralized Logic**: All text editing behavior in one class
- **Consistent Behavior**: Same editing experience across all dialogs
- **Easy Testing**: SingleLineTextEdit can be tested independently
- **Reusability**: Can be used for any single-line text input

## Visual Features

### Cursor Highlighting
The class provides visual cursor feedback using reversed colors:
- **Active Field**: Cursor shown with reversed background
- **Inactive Field**: No cursor highlighting
- **Empty Field**: Cursor shown as reversed space at beginning

### Text Scrolling
For text longer than the display width:
- **Smart Scrolling**: Keeps cursor visible in the display window
- **Cursor Near Start**: Shows text from beginning
- **Cursor Near End**: Shows text from end
- **Cursor in Middle**: Centers view around cursor

### Example Display
```
Regex Pattern: [old_file_name_pattern_here_]
Destination:   new_file_name_pattern
```
The `[_]` represents the cursor position with reversed highlighting.

## Integration Points

### Existing TFM Dialogs
The SingleLineTextEdit class can replace manual text editing in:
- **Batch Rename Dialog** ✅ (Primary use case with Up/Down navigation)
- **File Rename Dialog** (Future enhancement)
- **Create File Dialog** (Future enhancement)
- **Create Directory Dialog** (Future enhancement)
- **Search Dialog** (Future enhancement)
- **Filter Dialog** (Future enhancement)

### Navigation Patterns
- **Single Field Dialogs**: Use `handle_vertical_nav=True` for Up/Down cursor movement
- **Multi-Field Dialogs**: Use `handle_vertical_nav=False` (default) and handle Up/Down at dialog level for field navigation

### Color Integration
The class integrates with TFM's color system:
- Uses `get_status_color()` for consistent theming
- Supports bold highlighting for active fields
- Handles reversed colors for cursor display

## Testing

The class includes comprehensive test coverage:
- **Basic Functionality**: Text insertion, deletion, cursor movement
- **Key Handling**: All supported key types and edge cases
- **Boundary Conditions**: Empty text, cursor limits, screen boundaries
- **Length Constraints**: Maximum length enforcement
- **Set Operations**: Text and cursor position setting

Run tests with:
```bash
python test_single_line_text_edit.py
```

## Future Enhancements

### Potential Features
- **Multi-line Support**: Extend to handle multi-line text editing
- **Selection Support**: Text selection and clipboard operations
- **Undo/Redo**: Command pattern for edit history
- **Input Validation**: Real-time validation with error highlighting
- **Auto-completion**: Suggestion dropdown for common inputs
- **History**: Previous input recall with up/down arrows

### Performance Optimizations
- **Lazy Rendering**: Only redraw when text changes
- **Efficient Scrolling**: Minimize screen updates during scrolling
- **Memory Management**: Optimize for large text inputs

## Conclusion

The SingleLineTextEdit class successfully generalizes text editing functionality, providing:
- **Significant code reduction** (67% fewer lines)
- **Improved maintainability** through encapsulation
- **Consistent user experience** across dialogs
- **Comprehensive testing** for reliability
- **Reusable design** for future enhancements

This refactoring demonstrates the value of extracting common functionality into reusable components, making the codebase cleaner, more maintainable, and easier to extend.