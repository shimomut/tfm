# Info Dialog Component

## Overview

The Info Dialog Component provides a scrollable, modal information display system for TFM. It's used to show detailed information, help content, file details, and other multi-line content that requires user review.

## Features

### Core Capabilities
- **Scrollable Content**: Full scrolling support for long content
- **Modal Display**: Overlay dialog that captures user attention
- **Flexible Content**: Supports any list of text lines
- **Navigation Controls**: Comprehensive navigation with keyboard shortcuts
- **Responsive Design**: Adapts to different terminal sizes

### Navigation Features
- **Vertical Scrolling**: Line-by-line and page-by-page scrolling
- **Quick Navigation**: Home/End keys for instant positioning
- **Smooth Operation**: Responsive scrolling with proper bounds checking
- **Visual Feedback**: Clear indication of scroll position and content

## Class Structure

### InfoDialog Class
```python
class InfoDialog:
    def __init__(self, config)
    def show(self, title, info_lines)
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func)
    def exit()
```

### Key Methods
- **`show(title, info_lines)`**: Display dialog with title and content
- **`handle_input(key)`**: Process keyboard input for navigation
- **`draw(stdscr, safe_addstr_func)`**: Render the dialog
- **`exit()`**: Close the dialog and return to main interface

## Usage Examples

### Basic Information Display
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

### File Details Display
```python
file_info = [
    f"Name: {file.name}",
    f"Size: {file.stat().st_size} bytes",
    f"Modified: {datetime.fromtimestamp(file.stat().st_mtime)}",
    f"Permissions: {oct(file.stat().st_mode)[-3:]}"
]
info_dialog.show("File Details", file_info)
```

### Help Content Display
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

## Navigation Controls

### Keyboard Shortcuts
- **↑/↓ Arrow Keys**: Scroll up/down one line
- **Page Up/Page Down**: Scroll up/down one page (10 lines)
- **Home**: Jump to top of content
- **End**: Jump to bottom of content
- **q/ESC**: Close dialog and return to main interface

### Scrolling Behavior
- **Smooth Scrolling**: Line-by-line navigation for precise control
- **Page Scrolling**: Quick navigation through long content
- **Bounds Checking**: Prevents scrolling beyond content limits
- **Position Tracking**: Maintains scroll position during navigation

## Helper Functions

### InfoDialogHelpers Class
Pre-configured dialog setups for common use cases:

#### Help Dialog
```python
InfoDialogHelpers.show_help_dialog(info_dialog)
```
Displays comprehensive TFM help with all key bindings and usage information.

#### File Details Dialog
```python
InfoDialogHelpers.show_file_details(info_dialog, files_to_show, current_pane)
```
Shows detailed information about selected files including size, permissions, and timestamps.

#### Color Scheme Information
```python
InfoDialogHelpers.show_color_scheme_info(info_dialog)
```
Displays current color scheme information and available options.

## Visual Design

### Dialog Layout
```
┌─────────────────────────────────────┐
│ Dialog Title                        │
├─────────────────────────────────────┤
│ Content line 1                      │
│ Content line 2                      │
│ Content line 3                      │
│ ...                                 │
│ Content line N                      │
├─────────────────────────────────────┤
│ Navigation: ↑↓=Scroll q/ESC=Close   │
└─────────────────────────────────────┘
```

### Styling Features
- **Border**: Clean border with title integration
- **Content Area**: Scrollable content with proper spacing
- **Status Line**: Navigation help at bottom
- **Color Integration**: Uses TFM color scheme
- **Responsive Size**: Adapts to terminal dimensions

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.info_dialog = InfoDialog(self.config)

# Show dialog
self.info_dialog.show("Title", content_lines)

# Handle input in main loop
if self.info_dialog.mode:
    if self.info_dialog.handle_input(key):
        self.needs_full_redraw = True
    return True  # Input consumed
```

### Drawing Integration
```python
# In main draw loop
if self.info_dialog.mode:
    self.info_dialog.draw(self.stdscr, self.safe_addstr)
```

## Technical Implementation

### Content Management
- **Line Storage**: Efficient storage of content lines
- **Scroll Tracking**: Maintains current scroll position
- **Bounds Calculation**: Dynamic calculation of scroll limits
- **Content Formatting**: Preserves original text formatting

### Performance Optimization
- **Lazy Rendering**: Only renders visible content
- **Efficient Scrolling**: Minimal screen updates during scrolling
- **Memory Management**: Efficient handling of large content
- **Responsive Updates**: Quick response to user input

### Terminal Compatibility
- **Size Adaptation**: Works with various terminal sizes
- **Safe Drawing**: Boundary-safe text rendering
- **Color Support**: Graceful degradation without color support
- **Character Encoding**: Proper handling of Unicode content

## Common Use Cases

### System Information
```python
system_info = [
    f"Operating System: {platform.system()}",
    f"Python Version: {platform.python_version()}",
    f"Terminal Size: {os.get_terminal_size()}",
    f"Current Directory: {os.getcwd()}"
]
info_dialog.show("System Information", system_info)
```

### Error Display
```python
error_details = [
    "Operation Failed",
    "================",
    "",
    f"Error: {error_message}",
    f"File: {filename}",
    f"Time: {datetime.now()}",
    "",
    "Possible solutions:",
    "- Check file permissions",
    "- Verify disk space",
    "- Try again later"
]
info_dialog.show("Error Details", error_details)
```

### Configuration Display
```python
config_info = [
    "Current Configuration",
    "====================",
    "",
    f"Show Hidden Files: {config.SHOW_HIDDEN_FILES}",
    f"Default Sort: {config.DEFAULT_SORT_MODE}",
    f"Color Scheme: {config.COLOR_SCHEME}",
    f"Confirm Operations: {config.CONFIRM_DELETE}"
]
info_dialog.show("Configuration", config_info)
```

## Error Handling

### Content Validation
- **Empty Content**: Handles empty or None content gracefully
- **Long Lines**: Proper handling of very long text lines
- **Special Characters**: Safe rendering of special characters
- **Unicode Support**: Proper Unicode text handling

### Display Edge Cases
- **Small Terminals**: Graceful handling of very small terminals
- **Large Content**: Efficient handling of very long content
- **Terminal Resize**: Responsive to terminal size changes
- **Drawing Errors**: Safe error handling during rendering

## Benefits

### User Experience
- **Clear Information Display**: Easy-to-read information presentation
- **Intuitive Navigation**: Familiar keyboard shortcuts
- **Modal Focus**: Clear separation from main interface
- **Comprehensive Content**: Support for detailed information

### Developer Experience
- **Simple API**: Easy to use for displaying information
- **Flexible Content**: Accepts any list of strings
- **Helper Functions**: Pre-configured dialogs for common cases
- **Integration Ready**: Easy integration with existing code

### Maintenance
- **Centralized Logic**: All info dialog functionality in one place
- **Consistent Behavior**: Same navigation across all info dialogs
- **Reusable Component**: Single component for all information display needs
- **Easy Testing**: Isolated component for focused testing

## Future Enhancements

### Potential Improvements
- **Search Within Content**: Find text within displayed information
- **Content Formatting**: Rich text formatting support
- **Export Options**: Save displayed information to file
- **Print Support**: Print information content
- **Bookmarks**: Mark and jump to specific content sections

### Advanced Features
- **Hyperlinks**: Clickable links within content
- **Syntax Highlighting**: Code syntax highlighting in content
- **Image Support**: Display simple ASCII art or diagrams
- **Interactive Elements**: Expandable sections or interactive content

## Testing

### Test Coverage
- **Content Display**: Verify correct content rendering
- **Navigation**: Test all navigation controls
- **Edge Cases**: Small terminals and large content
- **Integration**: Integration with main application
- **Error Handling**: Error conditions and edge cases

### Test Files
- Tests are integrated into the main TFM test suite
- Interactive demos available for manual testing
- Automated tests cover core functionality

## Conclusion

The Info Dialog Component provides a robust, user-friendly way to display detailed information in TFM. It offers excellent navigation capabilities, responsive design, and easy integration, making it the ideal solution for any information display needs in the application.