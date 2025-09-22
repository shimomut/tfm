# List Dialog Component

## Overview

The List Dialog Component provides a searchable, selectable list interface for TFM. It enables users to quickly find and select items from lists using incremental search and keyboard navigation.

## Features

### Core Capabilities
- **Searchable Lists**: Real-time incremental search through list items
- **Keyboard Navigation**: Full keyboard control for selection and navigation
- **Modal Interface**: Focused interaction with clear visual separation
- **Flexible Content**: Supports any list of selectable items
- **Callback System**: Configurable actions for item selection

### Search Features
- **Incremental Search**: Real-time filtering as you type
- **Case-Insensitive**: Search ignores case for better usability
- **Substring Matching**: Finds items containing the search term
- **Search Highlighting**: Visual indication of search terms
- **Quick Clear**: Easy search term clearing

## Class Structure

### ListDialog Class
```python
class ListDialog:
    def __init__(self, config)
    def show(self, title, items, callback, custom_key_handler=None)
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func)
    def exit()
```

### Key Methods
- **`show(title, items, callback, custom_key_handler=None)`**: Display list with title, selection callback, and optional custom key handler
- **`handle_input(key)`**: Process keyboard input for navigation and search
- **`draw(stdscr, safe_addstr_func)`**: Render the dialog
- **`exit()`**: Close the dialog and return to main interface

### Custom Key Handler
The `custom_key_handler` parameter allows dialogs to handle special keys:
- **Function signature**: `custom_key_handler(key) -> bool`
- **Return True**: Key was handled, stop further processing
- **Return False**: Key not handled, continue with default processing
- **Use cases**: TAB switching, special navigation, custom shortcuts

## Usage Examples

### Basic List Selection
```python
list_dialog = ListDialog(config)

items = ["Option 1", "Option 2", "Option 3", "Option 4"]

def selection_callback(selected_item):
    print(f"Selected: {selected_item}")

list_dialog.show("Choose Option", items, selection_callback)
```

### File List Selection
```python
files = [f.name for f in Path(".").iterdir() if f.is_file()]

def file_callback(filename):
    print(f"Opening file: {filename}")

list_dialog.show("Select File", files, file_callback)
```

### Program Selection
```python
programs = [
    "Git Status",
    "System Information", 
    "Disk Usage",
    "Process List"
]

def program_callback(program_name):
    execute_program(program_name)

list_dialog.show("External Programs", programs, program_callback)
```

### Custom Key Handler Example (Cursor History TAB Switching)
```python
def show_cursor_history_with_tab_switching(pane_name):
    history_paths = get_pane_history(pane_name)
    
    def on_history_selected(selected_path):
        navigate_to_path(selected_path)
    
    def handle_custom_keys(key):
        if key == 9:  # TAB key
            # Switch to other pane's history
            other_pane = 'right' if pane_name == 'left' else 'left'
            list_dialog.exit()
            show_cursor_history_with_tab_switching(other_pane)
            return True
        return False
    
    title = f"History - {pane_name.title()} (TAB: Switch to {'Right' if pane_name == 'left' else 'Left'})"
    list_dialog.show(title, history_paths, on_history_selected, handle_custom_keys)
```

## Navigation Controls

### Keyboard Shortcuts
- **↑/↓ Arrow Keys**: Navigate up/down through list items
- **Page Up/Page Down**: Navigate by pages through long lists
- **Home/End**: Jump to first/last item in list
- **Enter**: Select current item and execute callback
- **ESC**: Cancel selection and close dialog
- **TAB**: Custom key handling (e.g., switch between pane histories)
- **Printable Characters**: Add to search term for filtering

### Search Controls
- **Type Characters**: Build search term to filter list
- **Backspace**: Remove last character from search term
- **Delete**: Clear entire search term
- **Arrow Keys**: Navigate through filtered results

## Helper Functions

### ListDialogHelpers Class
Pre-configured list dialogs for common TFM use cases:

#### Demo List
```python
ListDialogHelpers.show_demo(list_dialog)
```
Shows a demonstration list with sample items.

#### Favorite Directories
```python
ListDialogHelpers.show_favorite_directories(list_dialog, pane_manager, print_func)
```
Displays favorite directories for quick navigation.

#### External Programs
```python
ListDialogHelpers.show_programs_dialog(list_dialog, execute_program_func, print_func)
```
Shows configured external programs for execution.

#### Compare Selection
```python
ListDialogHelpers.show_compare_selection(list_dialog, current_pane, other_pane, print_func)
```
Provides file comparison options based on pane contents.

## Visual Design

### Dialog Layout
```
┌─────────────────────────────────────┐
│ Dialog Title                        │
├─────────────────────────────────────┤
│ Search: search_term_here            │
├─────────────────────────────────────┤
│ > Selected Item                     │
│   Other Item 1                      │
│   Other Item 2                      │
│   Other Item 3                      │
│   ...                               │
├─────────────────────────────────────┤
│ ↑↓=Navigate Enter=Select ESC=Cancel │
└─────────────────────────────────────┘
```

### Visual Features
- **Selection Indicator**: Clear visual indication of selected item
- **Search Display**: Shows current search term
- **Scroll Indicators**: Visual cues for scrollable content
- **Status Information**: Navigation help and item count
- **Color Integration**: Uses TFM color scheme

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.list_dialog = ListDialog(self.config)

# Show dialog
def callback(selected_item):
    # Handle selection
    pass

self.list_dialog.show("Title", items, callback)

# Handle input in main loop
if self.list_dialog.mode:
    if self.list_dialog.handle_input(key):
        self.needs_full_redraw = True
    return True  # Input consumed
```

### Drawing Integration
```python
# In main draw loop
if self.list_dialog.mode:
    self.list_dialog.draw(self.stdscr, self.safe_addstr)
```

## Technical Implementation

### Search Algorithm
- **Real-time Filtering**: Filters list as user types
- **Case-Insensitive Matching**: Uses lowercase comparison
- **Substring Search**: Finds items containing search term
- **Efficient Updates**: Minimal recalculation during search
- **Preserved Order**: Maintains original item order in results

### Performance Optimization
- **Lazy Rendering**: Only renders visible items
- **Efficient Search**: Optimized search algorithm for large lists
- **Minimal Updates**: Only redraws when necessary
- **Memory Efficient**: Handles large lists without excessive memory use

### Navigation Management
- **Scroll Tracking**: Maintains scroll position during navigation
- **Bounds Checking**: Prevents navigation beyond list limits
- **Selection Persistence**: Maintains selection during search
- **Smooth Scrolling**: Responsive navigation experience

## Common Use Cases

### Directory Navigation
```python
directories = [d.name for d in Path(".").iterdir() if d.is_directory()]

def navigate_callback(dirname):
    os.chdir(dirname)
    refresh_panes()

list_dialog.show("Navigate to Directory", directories, navigate_callback)
```

### Configuration Options
```python
options = [
    "Show Hidden Files: ON",
    "Show Hidden Files: OFF",
    "Sort by Name",
    "Sort by Size", 
    "Sort by Date"
]

def config_callback(option):
    apply_configuration(option)

list_dialog.show("Configuration", options, config_callback)
```

### Action Selection
```python
actions = [
    "Copy to Other Pane",
    "Move to Other Pane",
    "Delete Selected",
    "Create Archive",
    "Extract Archive"
]

def action_callback(action):
    execute_action(action)

list_dialog.show("File Actions", actions, action_callback)
```

## Search Functionality

### Search Features
- **Incremental**: Updates results as you type
- **Flexible**: Matches anywhere in item text
- **Fast**: Responsive even with large lists
- **Visual**: Clear indication of search state
- **Clearable**: Easy to clear and start over

### Search Examples
```
Original List: ["apple", "banana", "cherry", "date", "elderberry"]

Search "a":     ["apple", "banana", "date"]
Search "an":    ["banana"]  
Search "e":     ["apple", "cherry", "date", "elderberry"]
Search "berry": ["elderberry"]
```

## Error Handling

### Input Validation
- **Empty Lists**: Handles empty item lists gracefully
- **Invalid Callbacks**: Safe handling of callback errors
- **Long Items**: Proper truncation of very long item names
- **Special Characters**: Safe handling of special characters in items

### Display Edge Cases
- **Small Terminals**: Graceful degradation in constrained spaces
- **Large Lists**: Efficient handling of very long lists
- **Terminal Resize**: Responsive to terminal size changes
- **Drawing Errors**: Safe error handling during rendering

## Benefits

### User Experience
- **Quick Selection**: Fast item finding with search
- **Intuitive Interface**: Familiar keyboard navigation
- **Visual Clarity**: Clear indication of selection and search state
- **Efficient Workflow**: Minimal keystrokes for common tasks

### Developer Experience
- **Simple API**: Easy to use for any list selection need
- **Flexible Callbacks**: Configurable actions for selections
- **Helper Functions**: Pre-built dialogs for common cases
- **Integration Ready**: Easy integration with existing code

### Performance
- **Responsive**: Fast response even with large lists
- **Memory Efficient**: Handles large datasets efficiently
- **Smooth Navigation**: Fluid user interaction
- **Optimized Rendering**: Efficient screen updates

## Future Enhancements

### Potential Improvements
- **Multi-Selection**: Support for selecting multiple items
- **Custom Sorting**: User-configurable sort options
- **Item Icons**: Visual icons or indicators for different item types
- **Grouping**: Organize items into categories or groups
- **History**: Remember recent selections

### Advanced Features
- **Fuzzy Search**: More sophisticated search algorithms
- **Regular Expressions**: Regex-based search patterns
- **Custom Rendering**: Configurable item display formats
- **Keyboard Shortcuts**: Custom shortcuts for common actions
- **Context Menus**: Right-click or context-sensitive actions

## Testing

### Test Coverage
- **Search Functionality**: Verify search filtering works correctly
- **Navigation**: Test all navigation controls
- **Selection**: Verify callback execution
- **Edge Cases**: Empty lists, large lists, small terminals
- **Integration**: Integration with main application

### Test Scenarios
- **Basic Selection**: Simple item selection and callback
- **Search Operations**: Various search patterns and results
- **Navigation Patterns**: Different navigation sequences
- **Error Conditions**: Invalid inputs and error handling
- **Performance**: Large list handling and responsiveness

## Conclusion

The List Dialog Component provides a powerful, user-friendly interface for item selection in TFM. Its combination of search functionality, keyboard navigation, and flexible configuration makes it ideal for any scenario requiring user selection from a list of options. The component's efficiency and ease of use significantly enhance the overall TFM user experience.