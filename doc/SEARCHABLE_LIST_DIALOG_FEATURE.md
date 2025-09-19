# Searchable List Dialog Feature

## Overview

A new searchable list dialog has been added to the TUI File Manager (TFM) that allows users to select from a list of items with incremental search capabilities. This dialog provides a user-friendly way to choose from large lists by allowing real-time filtering as the user types.

## Features

### Core Functionality
- **Scrollable List**: Display multiple items in a scrollable list format
- **Incremental Search**: Filter items in real-time as the user types
- **Keyboard Navigation**: Full keyboard navigation support
- **Visual Selection**: Clear visual indication of the selected item
- **Configurable Appearance**: Customizable dialog dimensions and styling

### Navigation Controls
- **↑/↓ Arrow Keys**: Navigate up/down through the list
- **Page Up/Page Down**: Fast scrolling through large lists
- **Home/End**: Jump to first/last item
- **Enter**: Select the current item
- **ESC**: Cancel selection and close dialog
- **Typing**: Add characters to search filter
- **Backspace**: Remove characters from search filter

### Visual Elements
- **Title Bar**: Displays the dialog title
- **Search Box**: Shows current search pattern with cursor indicator
- **Item List**: Scrollable list with selection indicator (►)
- **Scroll Bar**: Visual scroll position indicator for large lists
- **Status Line**: Shows current position and filter information
- **Help Text**: Keyboard shortcuts displayed at bottom

## Implementation Details

### State Variables
```python
# List dialog state
self.list_dialog_mode = False           # Whether dialog is active
self.list_dialog_title = ""             # Dialog title
self.list_dialog_items = []             # Original list of items
self.list_dialog_filtered_items = []    # Filtered items based on search
self.list_dialog_selected = 0           # Index of selected item in filtered list
self.list_dialog_scroll = 0             # Scroll offset for the list
self.list_dialog_search = ""            # Current search pattern
self.list_dialog_callback = None        # Callback function for selection
```

### Key Methods

#### `show_list_dialog(title, items, callback)`
Shows the searchable list dialog.

**Parameters:**
- `title`: String - The title to display at the top of the dialog
- `items`: List - List of items to choose from (strings or objects with __str__ method)
- `callback`: Function - Function to call with the selected item (or None if cancelled)

**Example:**
```python
def selection_callback(selected_item):
    if selected_item:
        print(f"You selected: {selected_item}")
    else:
        print("Selection cancelled")

fm.show_list_dialog("Choose a File", file_list, selection_callback)
```

#### `handle_list_dialog_input(key)`
Handles keyboard input while the dialog is active.

#### `draw_list_dialog()`
Renders the dialog overlay on the screen.

### Configuration Options

The dialog appearance can be customized through configuration variables:

```python
LIST_DIALOG_WIDTH_RATIO = 0.6      # Dialog width as ratio of screen width
LIST_DIALOG_HEIGHT_RATIO = 0.7     # Dialog height as ratio of screen height
LIST_DIALOG_MIN_WIDTH = 40          # Minimum dialog width in characters
LIST_DIALOG_MIN_HEIGHT = 15         # Minimum dialog height in lines
```

## Integration with TFM

### Event Loop Integration
The list dialog is integrated into the main event loop with proper exclusivity handling:

```python
# Handle list dialog mode input
if self.list_dialog_mode:
    if self.handle_list_dialog_input(key):
        continue  # List dialog mode handled the key
```

### Dialog Exclusivity
The dialog respects the existing dialog exclusivity system, preventing conflicts with other dialogs:

```python
if self.dialog_mode or self.info_dialog_mode or self.list_dialog_mode or ...:
    continue  # Skip regular key processing
```

### Rendering Integration
The dialog is rendered through the existing status drawing system:

```python
# If in list dialog mode, show list dialog
if self.list_dialog_mode:
    self.draw_list_dialog()
    return
```

## Usage Examples

### Basic File Selection
```python
files = ["config.json", "main.py", "utils.py", "README.md"]

def file_selected(filename):
    if filename:
        print(f"Opening file: {filename}")
        # Open the selected file
    else:
        print("File selection cancelled")

fm.show_list_dialog("Select File to Open", files, file_selected)
```

### Directory Navigation
```python
directories = ["/home/user/Documents", "/home/user/Downloads", "/var/log"]

def directory_selected(path):
    if path:
        # Change to selected directory
        fm.get_current_pane()['path'] = Path(path)
        fm.needs_full_redraw = True

fm.show_list_dialog("Navigate to Directory", directories, directory_selected)
```

### Command Selection
```python
commands = ["git status", "git log", "git diff", "git push"]

def command_selected(cmd):
    if cmd:
        # Execute selected command
        os.system(cmd)

fm.show_list_dialog("Run Git Command", commands, command_selected)
```

## Testing

### Test Key Binding
A test key binding has been added for demonstration purposes:
- **L key**: Shows a demo list dialog with sample fruit names

### Test Scripts
Two test scripts are provided:

1. **test_list_dialog.py**: Basic functionality test
2. **demo_list_dialog.py**: Comprehensive demo with multiple scenarios

### Running Tests
```bash
# Basic test
python3 test_list_dialog.py

# Comprehensive demo
python3 demo_list_dialog.py

# Test within TFM (press 'L' key)
python3 tfm.py
```

## Benefits

1. **User-Friendly**: Intuitive keyboard navigation and search
2. **Efficient**: Quick filtering for large lists
3. **Flexible**: Works with any list of string-representable items
4. **Consistent**: Follows TFM's existing dialog patterns
5. **Accessible**: Full keyboard control, no mouse required
6. **Responsive**: Real-time search feedback

## Future Enhancements

Potential improvements for future versions:
- Multi-column display for wide items
- Custom item formatting/rendering
- Multiple selection support
- Fuzzy search algorithms
- Category/grouping support
- Custom key bindings per dialog
- Sorting options within dialog

## Technical Notes

- The dialog uses the same color scheme as other TFM dialogs
- Search is case-insensitive substring matching
- The dialog automatically adjusts scroll position to keep selection visible
- Memory efficient - only stores references to original items
- Thread-safe callback execution
- Proper cleanup on dialog exit