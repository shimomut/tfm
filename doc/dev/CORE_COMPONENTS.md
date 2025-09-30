# TFM Core Components

## Overview

The TFM Core Components provide the fundamental building blocks for TFM's user interface and functionality. These components work together to create a cohesive, efficient file management experience with consistent behavior across all dialogs and interfaces.

## Component Architecture

### Component Hierarchy

```
TFM Core Components
├── PaneManager - Dual-pane interface management
├── ListDialog - Searchable list selection interface
├── InfoDialog - Scrollable information display
├── SearchDialog - File and content search functionality
└── QuickChoiceBar - Status bar choice dialogs
```

### Design Principles

- **Modularity**: Each component handles a specific aspect of the UI
- **Consistency**: Uniform behavior and appearance across components
- **Reusability**: Components can be used in multiple contexts
- **Performance**: Optimized for responsive user interaction
- **Extensibility**: Easy to extend and customize for specific needs

## PaneManager Component

### Overview
The PaneManager Component handles TFM's dual-pane interface, managing navigation between left and right panes, directory synchronization, and pane-specific operations.

### Core Capabilities
- **Dual Pane Management**: Independent left and right pane operations
- **Active Pane Tracking**: Maintains current active pane state
- **Directory Navigation**: Handles directory changes and navigation
- **Pane Synchronization**: Sync directories between panes
- **File Selection Management**: Manages selected files per pane

### Class Structure
```python
class PaneManager:
    def __init__(self, config)
    def get_current_pane()
    def get_inactive_pane()
    def switch_active_pane()
    def sync_panes(direction)
    def navigate_to_directory(pane, path)
    def get_pane_width(total_width, left_ratio)
```

### Pane Data Structure
```python
pane_data = {
    'path': Path,           # Current directory path
    'files': List[Path],    # List of files in directory
    'selected_index': int,  # Currently selected file index
    'scroll_offset': int,   # Scroll position in file list
    'selected_files': Set,  # Set of selected file paths
    'sort_mode': str,       # Current sort mode
    'sort_reverse': bool,   # Sort direction
    'filter_pattern': str   # Current filter pattern
}
```

### Usage Examples

#### Basic Pane Operations
```python
pane_manager = PaneManager(config)

# Get current active pane
current = pane_manager.get_current_pane()
print(f"Current directory: {current['path']}")

# Switch to other pane
pane_manager.switch_active_pane()

# Get inactive pane
other = pane_manager.get_inactive_pane()
```

#### Pane Synchronization
```python
# Sync current pane directory to other pane
pane_manager.sync_panes('current_to_other')

# Sync other pane directory to current pane  
pane_manager.sync_panes('other_to_current')
```

### Key Features
- **Cross-Pane Operations**: Efficient file operations between directories
- **Quick Comparison**: Easy comparison of directory contents
- **Flexible Layout**: Adjustable pane width ratios
- **State Persistence**: Maintains pane state during operations

## ListDialog Component

### Overview
The ListDialog Component provides a searchable, selectable list interface for TFM, enabling users to quickly find and select items from lists using incremental search and keyboard navigation.

### Core Capabilities
- **Searchable Lists**: Real-time incremental search through list items
- **Keyboard Navigation**: Full keyboard control for selection and navigation
- **Modal Interface**: Focused interaction with clear visual separation
- **Flexible Content**: Supports any list of selectable items
- **Callback System**: Configurable actions for item selection

### Class Structure
```python
class ListDialog:
    def __init__(self, config)
    def show(self, title, items, callback, custom_key_handler=None, custom_help_text=None)
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func)
    def exit()
```

### Usage Examples

#### Basic List Selection
```python
list_dialog = ListDialog(config)

items = ["Option 1", "Option 2", "Option 3", "Option 4"]

def selection_callback(selected_item):
    print(f"Selected: {selected_item}")

list_dialog.show("Choose Option", items, selection_callback)
```

#### Custom Key Handler Example
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
    
    title = f"History - {pane_name.title()}"
    other_pane_name = 'Right' if pane_name == 'left' else 'Left'
    help_text = f"↑↓:select  Enter:choose  TAB:switch to {other_pane_name}  Type:search  ESC:cancel"
    list_dialog.show(title, history_paths, on_history_selected, handle_custom_keys, help_text)
```

### Navigation Controls
- **↑/↓ Arrow Keys**: Navigate up/down through list items
- **Page Up/Page Down**: Navigate by pages through long lists
- **Home/End**: Jump to first/last item in list
- **Enter**: Select current item and execute callback
- **ESC**: Cancel selection and close dialog
- **Type Characters**: Build search term to filter list

### Key Features
- **Real-time Search**: Incremental filtering as you type
- **Custom Key Handling**: Support for dialog-specific key operations
- **Helper Functions**: Pre-configured dialogs for common use cases
- **Performance Optimized**: Efficient handling of large lists

## InfoDialog Component

### Overview
The InfoDialog Component provides a scrollable, modal information display system for TFM, used to show detailed information, help content, file details, and other multi-line content.

### Core Capabilities
- **Scrollable Content**: Full scrolling support for long content
- **Modal Display**: Overlay dialog that captures user attention
- **Flexible Content**: Supports any list of text lines
- **Navigation Controls**: Comprehensive navigation with keyboard shortcuts
- **Responsive Design**: Adapts to different terminal sizes

### Class Structure
```python
class InfoDialog:
    def __init__(self, config)
    def show(self, title, info_lines)
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func)
    def exit()
```

### Usage Examples

#### Basic Information Display
```python
info_dialog = InfoDialog(config)
info_lines = [
    "TFM Version 2.0",
    "Terminal File Manager",
    "",
    "Features:",
    "- Dual pane interface",
    "- File operations",
    "- Search functionality"
]
info_dialog.show("About TFM", info_lines)
```

#### Help Content Display
```python
help_content = [
    "TFM Help",
    "========",
    "",
    "Navigation:",
    "  ↑/↓     - Move cursor up/down",
    "  ←/→     - Switch between panes",
    "  Enter   - Enter directory",
    "",
    "File Operations:",
    "  Space   - Select/deselect file",
    "  c/C     - Copy files",
    "  m/M     - Move files"
]
info_dialog.show("Help", help_content)
```

### Navigation Controls
- **↑/↓ Arrow Keys**: Scroll up/down one line
- **Page Up/Page Down**: Scroll up/down one page (10 lines)
- **Home**: Jump to top of content
- **End**: Jump to bottom of content
- **q/ESC**: Close dialog and return to main interface

### Key Features
- **Smooth Scrolling**: Line-by-line and page-by-page navigation
- **Content Formatting**: Preserves original text formatting
- **Helper Functions**: Pre-configured dialogs for common information display
- **Performance Optimized**: Lazy rendering for large content

## SearchDialog Component

### Overview
The SearchDialog Component provides comprehensive search functionality for TFM, enabling users to search for files by name patterns and content using grep-like functionality.

### Core Capabilities
- **Filename Search**: Search for files by name patterns with wildcards
- **Content Search**: Search within file contents using grep functionality
- **Real-time Results**: Live search results as you type
- **Pattern Matching**: Support for wildcards and regular expressions
- **Result Navigation**: Easy navigation to search results

### Class Structure
```python
class SearchDialog:
    def __init__(self, config)
    def show_filename_search(self, initial_pattern="")
    def show_content_search(self, initial_pattern="")
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func)
    def exit()
```

### Search Result Structure
```python
search_result = {
    'file_path': Path,      # Path to the found file
    'match_type': str,      # Type of match (filename/content)
    'line_number': int,     # Line number for content matches
    'match_text': str,      # Matching text or context
    'highlight_start': int, # Start position of highlight
    'highlight_end': int    # End position of highlight
}
```

### Usage Examples

#### Filename Search
```python
search_dialog = SearchDialog(config)

# Show filename search dialog
search_dialog.show_filename_search(initial_pattern="*.py")

# Handle results in callback
def handle_filename_result(result):
    navigate_to_file(result['file_path'])

search_dialog.set_result_callback(handle_filename_result)
```

#### Content Search
```python
# Show content search dialog
search_dialog.show_content_search(initial_pattern="function")

# Handle content search results
def handle_content_result(result):
    open_file_at_line(result['file_path'], result['line_number'])

search_dialog.set_result_callback(handle_content_result)
```

### Search Types

#### Filename Search Examples
```
Pattern: "*.py"          → Finds all Python files
Pattern: "test_*"        → Finds files starting with "test_"
Pattern: "*config*"      → Finds files containing "config"
Pattern: "README.??"     → Finds README.md, README.txt, etc.
```

#### Content Search Examples
```
Pattern: "function"      → Finds lines containing "function"
Pattern: "def \\w+"      → Finds function definitions (regex)
Pattern: "TODO|FIXME"    → Finds TODO or FIXME comments
Pattern: "import .*"     → Finds import statements
```

### Key Features
- **Incremental Search**: Updates results as search pattern changes
- **Case Sensitivity Options**: Toggle case-sensitive search
- **Performance Optimized**: Efficient search with caching and limits
- **Background Search**: Non-blocking search execution

## QuickChoiceBar Component

### Overview
The QuickChoiceBar Component provides a streamlined interface for presenting users with quick decision dialogs in TFM's status bar area, handling confirmation dialogs, error messages, and simple choice selections.

### Core Capabilities
- **Status Bar Integration**: Displays choices directly in the status bar
- **Keyboard Navigation**: Full keyboard control for choice selection
- **Flexible Choices**: Support for various choice types and configurations
- **Callback System**: Configurable actions for each choice selection
- **Visual Highlighting**: Clear indication of selected choice

### Class Structure
```python
class QuickChoiceBar:
    def __init__(self, config)
    def show(self, message, choices, callback)
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func, y, width)
    def exit()
```

### Choice Structure
```python
choice = {
    'key': 'y',           # Key to press for this choice
    'label': 'Yes',       # Display label for the choice
    'action': 'confirm',  # Action identifier for callback
    'default': True       # Whether this is the default choice
}
```

### Usage Examples

#### Basic Confirmation Dialog
```python
quick_choice_bar = QuickChoiceBar(config)

def confirm_callback(action):
    if action == 'confirm':
        perform_operation()
    elif action == 'cancel':
        cancel_operation()

choices = [
    {'key': 'y', 'label': 'Yes', 'action': 'confirm', 'default': True},
    {'key': 'n', 'label': 'No', 'action': 'cancel'}
]

quick_choice_bar.show("Delete selected files?", choices, confirm_callback)
```

#### File Overwrite Dialog
```python
def overwrite_callback(action):
    if action == 'overwrite':
        overwrite_file()
    elif action == 'skip':
        skip_file()
    elif action == 'cancel':
        cancel_operation()

choices = [
    {'key': 'o', 'label': 'Overwrite', 'action': 'overwrite'},
    {'key': 's', 'label': 'Skip', 'action': 'skip'},
    {'key': 'c', 'label': 'Cancel', 'action': 'cancel', 'default': True}
]

quick_choice_bar.show(f"File '{filename}' exists. Overwrite?", choices, overwrite_callback)
```

### Visual Design
```
┌─────────────────────────────────────────────────────────────┐
│ Delete 5 selected files? [Y]es [N]o                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Features
- **Non-Intrusive**: Uses status bar instead of modal dialogs
- **Quick Decisions**: Fast, keyboard-driven choice selection
- **Helper Functions**: Pre-configured dialogs for common scenarios
- **Default Selection**: Support for default choices with Enter key

## Component Integration

### Main Application Integration

All components integrate seamlessly with TFM's main application:

```python
# In FileManager class initialization
self.pane_manager = PaneManager(self.config)
self.list_dialog = ListDialog(self.config)
self.info_dialog = InfoDialog(self.config)
self.search_dialog = SearchDialog(self.config)
self.quick_choice_bar = QuickChoiceBar(self.config)

# Input handling in main loop
if self.list_dialog.mode:
    if self.list_dialog.handle_input(key):
        self.needs_full_redraw = True
    return True

if self.info_dialog.mode:
    if self.info_dialog.handle_input(key):
        self.needs_full_redraw = True
    return True

# Drawing integration
if self.list_dialog.mode:
    self.list_dialog.draw(self.stdscr, self.safe_addstr)
elif self.info_dialog.mode:
    self.info_dialog.draw(self.stdscr, self.safe_addstr)
elif self.search_dialog.mode:
    self.search_dialog.draw(self.stdscr, self.safe_addstr)

if self.quick_choice_bar.mode:
    status_y = height - 1
    self.quick_choice_bar.draw(self.stdscr, self.safe_addstr, status_y, width)
```

### Component Communication

Components communicate through well-defined interfaces:

```python
# PaneManager provides context for other components
current_pane = self.pane_manager.get_current_pane()
search_path = current_pane['path']

# SearchDialog uses pane context for search operations
self.search_dialog.set_search_path(search_path)

# ListDialog can trigger pane navigation
def navigate_callback(selected_path):
    self.pane_manager.navigate_to_directory(current_pane, selected_path)

# QuickChoiceBar confirms operations affecting panes
def confirm_callback(action):
    if action == 'confirm':
        self.pane_manager.perform_operation()
```

## Helper Functions

Each component provides helper functions for common use cases:

### ListDialogHelpers
```python
# Pre-configured list dialogs
ListDialogHelpers.show_demo(list_dialog)
ListDialogHelpers.show_favorite_directories(list_dialog, pane_manager, print_func)
ListDialogHelpers.show_programs_dialog(list_dialog, execute_program_func, print_func)
ListDialogHelpers.show_compare_selection(list_dialog, current_pane, other_pane, print_func)
```

### InfoDialogHelpers
```python
# Pre-configured information dialogs
InfoDialogHelpers.show_help_dialog(info_dialog)
InfoDialogHelpers.show_file_details(info_dialog, files_to_show, current_pane)
InfoDialogHelpers.show_color_scheme_info(info_dialog)
```

### SearchDialogHelpers
```python
# Search utility functions
SearchDialogHelpers.navigate_to_result(result, pane_manager, file_operations, print_func)
SearchDialogHelpers.format_search_results(raw_results, search_type)
SearchDialogHelpers.execute_filename_search(pattern, search_path)
SearchDialogHelpers.execute_content_search(pattern, search_path, case_sensitive)
```

### QuickChoiceBarHelpers
```python
# Pre-configured choice dialogs
QuickChoiceBarHelpers.show_overwrite_dialog(quick_choice_bar, filename, callback)
QuickChoiceBarHelpers.show_error_dialog(quick_choice_bar, error_message, callback)
QuickChoiceBarHelpers.show_delete_confirmation(quick_choice_bar, item_count, callback)
```

## Performance Optimization

### Efficient Rendering
All components implement performance optimizations:

- **Lazy Rendering**: Only renders visible content
- **Minimal Updates**: Only redraws when content changes
- **Efficient Algorithms**: Optimized search and navigation algorithms
- **Memory Management**: Proper cleanup and resource management

### Responsive Design
- **Terminal Adaptation**: Components adapt to different terminal sizes
- **Graceful Degradation**: Handles constrained spaces appropriately
- **Responsive Updates**: Quick response to user input
- **Smooth Navigation**: Fluid user interaction

## Error Handling

### Consistent Error Handling
All components implement robust error handling:

```python
# Input validation
def safe_operation(self, input_data):
    try:
        return self.perform_operation(input_data)
    except SpecificError as e:
        self.show_error(f"Operation failed: {e}")
        return None
    except Exception as e:
        self.show_error(f"Unexpected error: {e}")
        return None
```

### Recovery Mechanisms
- **Graceful Degradation**: Components continue to function with reduced capability
- **State Recovery**: Automatic recovery from error states
- **User Feedback**: Clear error messages and guidance
- **Fallback Behavior**: Safe fallback options for critical operations

## Testing

### Comprehensive Test Coverage

Each component includes thorough testing:

#### Unit Tests
- **Core Functionality**: Test all basic component operations
- **Edge Cases**: Test boundary conditions and error scenarios
- **Integration**: Test component integration with main application
- **Performance**: Test performance with large datasets

#### Test Scenarios
- **Basic Operations**: Simple component usage patterns
- **Complex Interactions**: Multi-step component interactions
- **Error Conditions**: Invalid inputs and error handling
- **Performance**: Large data handling and responsiveness

### Test Files
```
test/
├── test_pane_manager.py
├── test_list_dialog.py
├── test_info_dialog.py
├── test_search_dialog.py
├── test_quick_choice_bar.py
└── test_component_integration.py
```

## Benefits

### User Experience Benefits
- **Consistent Interface**: Uniform behavior across all components
- **Intuitive Navigation**: Familiar keyboard shortcuts and patterns
- **Responsive Interaction**: Quick response to user input
- **Visual Clarity**: Clear indication of state and available actions

### Developer Benefits
- **Modular Design**: Easy to understand and maintain
- **Reusable Components**: Components can be used in multiple contexts
- **Extensible Architecture**: Easy to add new features and functionality
- **Comprehensive Testing**: Well-tested components reduce bugs

### Technical Benefits
- **Performance Optimized**: Efficient algorithms and rendering
- **Memory Efficient**: Proper resource management
- **Error Resilient**: Robust error handling and recovery
- **Scalable**: Handles large datasets and complex operations

## Future Enhancements

### Planned Improvements

#### Enhanced Functionality
- **Multi-Selection**: Support for multiple item selection in ListDialog
- **Rich Text**: Enhanced text formatting in InfoDialog
- **Advanced Search**: More sophisticated search algorithms in SearchDialog
- **Custom Layouts**: Configurable component layouts and appearance

#### Performance Optimizations
- **Virtualization**: Virtual scrolling for very large lists
- **Caching**: Enhanced caching for frequently accessed data
- **Background Processing**: More background operations for responsiveness
- **Memory Optimization**: Further memory usage optimizations

#### User Experience
- **Accessibility**: Enhanced accessibility features
- **Customization**: More user customization options
- **Themes**: Support for custom themes and styling
- **Animation**: Smooth animations and transitions

### Advanced Features

#### Component Extensions
- **Plugin System**: Support for component plugins and extensions
- **Custom Components**: Framework for creating custom components
- **Component Scripting**: Scriptable component behavior
- **Remote Components**: Support for remote component interfaces

#### Integration Enhancements
- **External Tools**: Better integration with external tools
- **Network Support**: Enhanced network operation support
- **Cloud Integration**: Integration with cloud storage services
- **Collaboration**: Multi-user collaboration features

## Conclusion

The TFM Core Components provide a robust, efficient, and user-friendly foundation for TFM's file management capabilities. Their modular design, consistent behavior, and comprehensive functionality make them essential building blocks for creating an effective terminal-based file manager.

### Key Achievements

- ✅ **Modular Architecture**: Clean separation of concerns with reusable components
- ✅ **Consistent Interface**: Uniform behavior and appearance across all components
- ✅ **Performance Optimized**: Efficient algorithms and responsive user interaction
- ✅ **Comprehensive Functionality**: Full-featured components for all common use cases
- ✅ **Robust Error Handling**: Graceful error handling and recovery mechanisms
- ✅ **Extensive Testing**: Thorough test coverage ensuring reliability
- ✅ **Easy Integration**: Seamless integration with main application and each other

The components work together to create a cohesive, powerful file management experience that is both efficient for power users and accessible for newcomers to terminal-based file management.

## Related Documentation

- [Dialog System](DIALOG_SYSTEM.md) - General dialog framework and rendering system
- [TFM Application Overview](TFM_APPLICATION_OVERVIEW.md) - Overall application architecture
- [S3 Support System](S3_SUPPORT_SYSTEM.md) - S3 integration with components