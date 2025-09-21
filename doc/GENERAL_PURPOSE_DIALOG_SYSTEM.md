# General Purpose Dialog System

## Overview

The General Purpose Dialog System provides a flexible, reusable dialog framework for TFM that handles various types of user input dialogs. It centralizes dialog functionality and provides consistent behavior across different dialog types.

## Features

### Core Capabilities
- **Status Line Input**: Single-line text input in the status bar area
- **Flexible Prompts**: Customizable prompt text and help messages
- **Width Management**: Intelligent width calculation and help text positioning
- **Input Validation**: Built-in validation and error handling
- **Consistent Styling**: Unified appearance across all dialogs

### Dialog Types
- **File/Directory Creation**: Create new files and directories
- **Rename Operations**: Rename files and directories
- **Filter Input**: Set file filters for display
- **Archive Creation**: Specify archive names and formats
- **General Text Input**: Any single-line text input need

## Class Structure

### DialogType Constants
```python
class DialogType:
    STATUS_LINE_INPUT = "status_line_input"
```

### GeneralPurposeDialog Class
```python
class GeneralPurposeDialog:
    def __init__(self, config)
    def show_status_line_input(self, prompt_text, initial_text="", help_text="")
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func)
    def exit()
```

## Usage Examples

### Basic Text Input
```python
dialog = GeneralPurposeDialog(config)
dialog.show_status_line_input(
    prompt_text="Enter filename: ",
    initial_text="",
    help_text="Enter the name for the new file"
)
```

### Rename Dialog
```python
dialog.show_status_line_input(
    prompt_text=f"Rename '{original_name}' to: ",
    initial_text=current_name,
    help_text="Enter new name or press ESC to cancel"
)
```

### Filter Dialog
```python
dialog.show_status_line_input(
    prompt_text="Filter: ",
    initial_text=current_filter,
    help_text="Enter pattern to filter files (wildcards: * ?)"
)
```

## Helper Functions

### DialogHelpers Class
The `DialogHelpers` class provides pre-configured dialog setups for common use cases:

#### Filter Dialog
```python
DialogHelpers.create_filter_dialog(dialog, current_filter="")
```

#### Rename Dialog
```python
DialogHelpers.create_rename_dialog(dialog, original_name, current_name="")
```

#### Create Directory Dialog
```python
DialogHelpers.create_create_directory_dialog(dialog)
```

#### Create File Dialog
```python
DialogHelpers.create_create_file_dialog(dialog)
```

#### Create Archive Dialog
```python
DialogHelpers.create_create_archive_dialog(dialog)
```

## Technical Features

### Width Management
- **Intelligent Calculation**: Automatically calculates optimal field width
- **Help Text Positioning**: Smart positioning to avoid overlap
- **Minimum Width Guarantee**: Ensures usable input space even in narrow terminals
- **Graceful Degradation**: Hides help text when space is insufficient

### Input Handling
- **SingleLineTextEdit Integration**: Uses the robust text editing component
- **Key Processing**: Handles Enter, ESC, and text input keys
- **Validation**: Built-in validation for different input types
- **Error Handling**: Graceful error handling and user feedback

### Visual Design
- **Consistent Styling**: Uses TFM color scheme and styling
- **Status Bar Integration**: Seamlessly integrates with status bar area
- **Help Text Display**: Optional help text with intelligent positioning
- **Responsive Layout**: Adapts to different terminal sizes

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.general_dialog = GeneralPurposeDialog(self.config)

# Show dialog
self.general_dialog.show_status_line_input(
    prompt_text="Enter name: ",
    help_text="Type the new name"
)

# Handle input in main loop
if self.general_dialog.mode:
    result = self.general_dialog.handle_input(key)
    if result == 'submit':
        text = self.general_dialog.text_editor.get_text()
        # Process the input
    elif result == 'cancel':
        self.general_dialog.exit()
```

### Drawing Integration
```python
# In main draw loop
if self.general_dialog.mode:
    self.general_dialog.draw(self.stdscr, self.safe_addstr)
```

## Configuration

### Customizable Aspects
- **Prompt Text**: Fully customizable prompt messages
- **Help Text**: Optional help text for user guidance
- **Initial Text**: Pre-populate input fields
- **Validation**: Custom validation logic
- **Styling**: Inherits from TFM color configuration

### Width Calculation Settings
The dialog system automatically handles width calculations but respects:
- Terminal width constraints
- Help text space requirements
- Minimum usable input width (prompt + 5 characters)

## Benefits

### Code Reuse
- **Centralized Logic**: All dialog functionality in one place
- **Consistent Behavior**: Same input handling across all dialogs
- **Reduced Duplication**: Eliminates repeated dialog code
- **Easy Maintenance**: Single point of maintenance for dialog features

### User Experience
- **Consistent Interface**: Familiar behavior across all input dialogs
- **Intelligent Layout**: Optimal use of available screen space
- **Helpful Guidance**: Optional help text for user assistance
- **Responsive Design**: Works well on various terminal sizes

### Developer Experience
- **Simple API**: Easy to use for new dialog types
- **Helper Functions**: Pre-configured dialogs for common cases
- **Flexible Configuration**: Customizable for specific needs
- **Good Documentation**: Clear examples and usage patterns

## Error Handling

### Input Validation
- **Length Limits**: Configurable maximum input length
- **Character Validation**: Filter invalid characters
- **Empty Input Handling**: Appropriate handling of empty inputs
- **Special Character Support**: Proper handling of special characters

### Edge Cases
- **Narrow Terminals**: Graceful degradation in constrained spaces
- **Long Prompts**: Intelligent handling of long prompt text
- **Help Text Overflow**: Smart positioning to prevent overlap
- **Terminal Resize**: Responsive to terminal size changes

## Future Enhancements

### Potential Improvements
- **Multi-line Input**: Support for multi-line text input
- **Input History**: Remember previous inputs for convenience
- **Auto-completion**: Suggest completions based on context
- **Input Validation**: Real-time validation with visual feedback
- **Custom Styling**: Per-dialog styling options

### Advanced Features
- **Modal Dialogs**: Full-screen modal dialog support
- **Form Dialogs**: Multi-field form input support
- **Progress Dialogs**: Integration with progress tracking
- **Confirmation Dialogs**: Yes/No confirmation dialog support

## Testing

### Test Coverage
- **Width Calculations**: Verify correct width calculations
- **Help Text Positioning**: Test help text placement
- **Edge Cases**: Narrow terminals and long inputs
- **Input Handling**: Key processing and validation
- **Integration**: Integration with main application

### Test Files
- `test_general_purpose_dialog_width_fix.py`: Width calculation tests
- `test_dialog_width_edge_cases.py`: Edge case handling
- `demo_dialog_improvements.py`: Interactive demonstration

## Conclusion

The General Purpose Dialog System provides a robust, flexible foundation for all text input dialogs in TFM. It ensures consistent behavior, optimal space utilization, and excellent user experience across all dialog types while simplifying development and maintenance of dialog functionality.