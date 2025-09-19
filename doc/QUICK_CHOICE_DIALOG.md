# Quick Choice Dialog System

The TFM file manager now includes a flexible quick choice dialog system that can be used for any type of user selection interface.

## Overview

The quick choice dialog system generalizes the previous confirmation dialog to support any number of choices with custom text, quick keys, and return values.

## API

### Core Methods

#### `show_dialog(message, choices, callback)`
Shows a quick choice dialog with custom options.

**Parameters:**
- `message`: The message to display to the user
- `choices`: List of choice dictionaries (see format below)
- `callback`: Function to call with the selected choice's value

#### `show_confirmation(message, callback)` 
Backward-compatible method that shows a Yes/No/Cancel dialog.

**Parameters:**
- `message`: The confirmation message
- `callback`: Function to call with True (Yes), False (No), or None (Cancel)

### Choice Format

Each choice is a dictionary with the following keys:

```python
{
    "text": "Display Text",    # Required: Text shown in the dialog
    "key": "q",               # Optional: Quick key for instant selection
    "value": "return_value"   # Required: Value passed to callback when selected
}
```

## Usage Examples

### 1. Basic Yes/No/Cancel (Backward Compatible)

```python
def handle_quit(confirmed):
    if confirmed:
        self.quit_application()
    elif confirmed is False:
        print("Quit cancelled")
    # confirmed is None for Cancel - no action needed

self.show_confirmation("Are you sure you want to quit?", handle_quit)
```

### 2. File Operations Menu

```python
choices = [
    {"text": "Copy", "key": "c", "value": "copy"},
    {"text": "Move", "key": "m", "value": "move"},
    {"text": "Delete", "key": "d", "value": "delete"},
    {"text": "Cancel", "key": "x", "value": None}
]

def handle_operation(operation):
    if operation == "copy":
        # Implement copy logic
    elif operation == "move":
        # Implement move logic
    elif operation == "delete":
        # Implement delete logic
    # operation is None for Cancel

self.show_dialog("Choose operation:", choices, handle_operation)
```

### 3. Sort Options

```python
choices = [
    {"text": "Name", "key": "n", "value": "name"},
    {"text": "Size", "key": "s", "value": "size"},
    {"text": "Date", "key": "d", "value": "date"},
    {"text": "Type", "key": "t", "value": "type"}
]

def handle_sort(sort_type):
    if sort_type:
        self.sort_files_by(sort_type)

self.show_dialog("Sort by:", choices, handle_sort)
```

### 4. Priority Levels

```python
choices = [
    {"text": "Low", "key": "l", "value": 1},
    {"text": "Medium", "key": "m", "value": 2},
    {"text": "High", "key": "h", "value": 3},
    {"text": "Critical", "key": "c", "value": 4}
]

def handle_priority(level):
    if level:
        self.set_priority(level)

self.show_dialog("Set priority:", choices, handle_priority)
```

## User Interface

### Navigation
- **←→ or h/l**: Navigate between choices
- **Enter**: Confirm selected choice
- **Quick keys**: Instantly select choice (if defined)
- **ESC**: Cancel dialog

### Visual Feedback
- Selected choice is highlighted with bold and standout formatting
- Quick keys are shown in the help text
- Help text adapts based on available quick keys

## Key Features

### 1. Flexible Choice Values
- Return values can be any Python type (bool, string, int, object, etc.)
- Use `None` for cancel/no-action choices

### 2. Quick Key Support
- Optional single-character quick keys for instant selection
- Case-insensitive matching
- Automatically shown in help text

### 3. Dynamic Help Text
- Help text automatically adapts to show available quick keys
- Shows standard navigation options
- Compact display that fits in status bar

### 4. Input Isolation
- All keyboard input is captured during dialog mode
- Prevents accidental actions in file lists
- Clean exit on ESC or selection

### 5. Backward Compatibility
- Existing `show_confirmation()` calls continue to work
- Same callback signature for Yes/No/Cancel dialogs

## Implementation Examples in TFM

The file manager includes two example implementations:

### File Operations Menu (M key)
Press 'M' to show operations for the currently selected file:
- Copy, Move, Delete, Rename, Properties, Cancel

### Sort Menu (S key)  
Press 'S' to show sorting options:
- Name, Size, Date, Type, Reverse, Cancel

## Benefits

1. **Consistency**: All quick choice interactions use the same interface
2. **Flexibility**: Easy to add new menus and options
3. **Usability**: Quick keys and keyboard navigation
4. **Maintainability**: Single system handles all quick choice types
5. **Extensibility**: Easy to add new dialog types

## Future Enhancements

Potential future improvements:
- Multi-select dialogs (checkboxes)
- Input dialogs (text entry)
- Nested menus
- Custom styling per choice
- Icons or symbols in choices