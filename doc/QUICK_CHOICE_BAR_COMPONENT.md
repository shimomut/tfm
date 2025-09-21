# Quick Choice Bar Component

## Overview

The Quick Choice Bar Component provides a streamlined interface for presenting users with quick decision dialogs in TFM's status bar area. It handles confirmation dialogs, error messages, and simple choice selections without requiring full modal dialogs.

## Features

### Core Capabilities
- **Status Bar Integration**: Displays choices directly in the status bar
- **Keyboard Navigation**: Full keyboard control for choice selection
- **Flexible Choices**: Support for various choice types and configurations
- **Callback System**: Configurable actions for each choice selection
- **Visual Highlighting**: Clear indication of selected choice

### Dialog Types
- **Confirmation Dialogs**: Yes/No confirmations for operations
- **Error Dialogs**: Error message display with acknowledgment
- **Info Dialogs**: Information messages with OK button
- **Custom Choices**: User-defined choice sets for specific needs
- **Overwrite Dialogs**: File overwrite confirmation with options

## Class Structure

### QuickChoiceBar Class
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

## Usage Examples

### Basic Confirmation Dialog
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

### File Overwrite Dialog
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

### Error Acknowledgment
```python
def error_callback(action):
    # Just acknowledge the error
    pass

choices = [
    {'key': 'o', 'label': 'OK', 'action': 'acknowledge', 'default': True}
]

quick_choice_bar.show("Error: Permission denied", choices, error_callback)
```

## Helper Functions

### QuickChoiceBarHelpers Class
Pre-configured dialogs for common use cases:

#### Overwrite Dialog
```python
QuickChoiceBarHelpers.show_overwrite_dialog(quick_choice_bar, filename, callback)
```
Shows a standard file overwrite confirmation dialog.

#### Error Dialog
```python
QuickChoiceBarHelpers.show_error_dialog(quick_choice_bar, error_message, callback)
```
Displays an error message with OK acknowledgment.

#### Info Dialog
```python
QuickChoiceBarHelpers.show_info_dialog(quick_choice_bar, info_message, callback)
```
Shows an information message with OK button.

#### Confirmation Dialogs
```python
# Delete confirmation
QuickChoiceBarHelpers.show_delete_confirmation(quick_choice_bar, item_count, callback)

# Copy confirmation  
QuickChoiceBarHelpers.show_copy_confirmation(quick_choice_bar, file_count, callback)

# Move confirmation
QuickChoiceBarHelpers.show_move_confirmation(quick_choice_bar, file_count, callback)
```

## Visual Design

### Status Bar Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Delete 5 selected files? [Y]es [N]o                        │
└─────────────────────────────────────────────────────────────┘
```

### Choice Highlighting
- **Default Choice**: Highlighted with brackets `[Y]es`
- **Available Choices**: Clearly marked with key letters
- **Selected Choice**: Visual indication of current selection
- **Message**: Clear message text explaining the choice

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.quick_choice_bar = QuickChoiceBar(self.config)

# Show dialog
def callback(action):
    handle_user_choice(action)

self.quick_choice_bar.show(message, choices, callback)

# Handle input in main loop
if self.quick_choice_bar.mode:
    if self.quick_choice_bar.handle_input(key):
        self.needs_full_redraw = True
    return True  # Input consumed
```

### Drawing Integration
```python
# In main draw loop
if self.quick_choice_bar.mode:
    status_y = height - 1
    self.quick_choice_bar.draw(self.stdscr, self.safe_addstr, status_y, width)
```

## Choice Configuration

### Standard Choice Types
```python
# Yes/No confirmation
YES_NO_CHOICES = [
    {'key': 'y', 'label': 'Yes', 'action': 'confirm', 'default': True},
    {'key': 'n', 'label': 'No', 'action': 'cancel'}
]

# OK acknowledgment
OK_CHOICE = [
    {'key': 'o', 'label': 'OK', 'action': 'acknowledge', 'default': True}
]

# Overwrite options
OVERWRITE_CHOICES = [
    {'key': 'o', 'label': 'Overwrite', 'action': 'overwrite'},
    {'key': 's', 'label': 'Skip', 'action': 'skip'},
    {'key': 'a', 'label': 'All', 'action': 'overwrite_all'},
    {'key': 'c', 'label': 'Cancel', 'action': 'cancel', 'default': True}
]
```

### Custom Choices
```python
# Custom operation choices
CUSTOM_CHOICES = [
    {'key': '1', 'label': 'Option 1', 'action': 'option1'},
    {'key': '2', 'label': 'Option 2', 'action': 'option2'},
    {'key': '3', 'label': 'Option 3', 'action': 'option3'},
    {'key': 'c', 'label': 'Cancel', 'action': 'cancel', 'default': True}
]
```

## Input Handling

### Key Processing
```python
def handle_input(self, key):
    """Handle keyboard input for choice selection"""
    # Check for ESC key (cancel)
    if key == 27:
        self.callback('cancel')
        self.exit()
        return True
    
    # Check for Enter key (select default)
    if key in [10, 13]:  # Enter keys
        default_choice = self.get_default_choice()
        if default_choice:
            self.callback(default_choice['action'])
            self.exit()
            return True
    
    # Check for specific choice keys
    for choice in self.choices:
        if key == ord(choice['key'].lower()) or key == ord(choice['key'].upper()):
            self.callback(choice['action'])
            self.exit()
            return True
    
    return False
```

### Default Selection
- **Enter Key**: Selects the default choice (marked with `default: True`)
- **ESC Key**: Always cancels the dialog
- **Choice Keys**: Direct selection by pressing the choice key
- **Case Insensitive**: Accepts both uppercase and lowercase keys

## Advanced Features

### Dynamic Choice Generation
```python
def create_dynamic_choices(self, context):
    """Create choices based on current context"""
    choices = []
    
    if context.get('can_overwrite'):
        choices.append({'key': 'o', 'label': 'Overwrite', 'action': 'overwrite'})
    
    if context.get('can_skip'):
        choices.append({'key': 's', 'label': 'Skip', 'action': 'skip'})
    
    if context.get('can_rename'):
        choices.append({'key': 'r', 'label': 'Rename', 'action': 'rename'})
    
    choices.append({'key': 'c', 'label': 'Cancel', 'action': 'cancel', 'default': True})
    
    return choices
```

### Conditional Choices
```python
def show_conditional_dialog(self, message, base_choices, conditions):
    """Show dialog with choices based on conditions"""
    filtered_choices = []
    
    for choice in base_choices:
        condition = choice.get('condition')
        if condition is None or conditions.get(condition, True):
            filtered_choices.append(choice)
    
    self.show(message, filtered_choices, self.callback)
```

## Error Handling

### Input Validation
- **Invalid Keys**: Ignores keys that don't match any choice
- **Empty Choices**: Handles empty choice lists gracefully
- **Missing Callbacks**: Safe handling of missing callback functions
- **Invalid Actions**: Proper error handling for invalid actions

### Display Edge Cases
```python
def safe_draw(self, stdscr, safe_addstr_func, y, width):
    """Safely draw the choice bar with error handling"""
    try:
        # Calculate message and choices layout
        message_width = len(self.message)
        choices_width = sum(len(f"[{c['key']}]{c['label'][1:]} ") for c in self.choices)
        
        # Truncate if necessary
        if message_width + choices_width > width:
            self.message = self.message[:width - choices_width - 3] + "..."
        
        # Draw message and choices
        self.draw_message_and_choices(stdscr, safe_addstr_func, y, width)
        
    except Exception as e:
        # Fallback to simple message display
        safe_addstr_func(y, 0, f"Error in dialog: {str(e)}", get_status_color())
```

## Performance Optimization

### Efficient Rendering
- **Minimal Updates**: Only redraws when choice selection changes
- **Layout Caching**: Caches layout calculations for performance
- **Efficient Text Processing**: Optimized text truncation and formatting
- **Responsive Updates**: Quick response to user input

### Memory Management
```python
def cleanup(self):
    """Clean up resources when dialog closes"""
    self.message = ""
    self.choices = []
    self.callback = None
    self.selected_index = 0
```

## Common Use Cases

### File Operation Confirmations
```python
# Delete confirmation
def confirm_delete(self, file_count):
    message = f"Delete {file_count} selected files?"
    choices = [
        {'key': 'y', 'label': 'Yes', 'action': 'confirm', 'default': True},
        {'key': 'n', 'label': 'No', 'action': 'cancel'}
    ]
    self.quick_choice_bar.show(message, choices, self.handle_delete_choice)

# Copy confirmation
def confirm_copy(self, file_count, destination):
    message = f"Copy {file_count} files to {destination}?"
    choices = [
        {'key': 'y', 'label': 'Yes', 'action': 'confirm', 'default': True},
        {'key': 'n', 'label': 'No', 'action': 'cancel'}
    ]
    self.quick_choice_bar.show(message, choices, self.handle_copy_choice)
```

### Error Handling
```python
def show_operation_error(self, operation, error_message):
    message = f"{operation} failed: {error_message}"
    choices = [
        {'key': 'o', 'label': 'OK', 'action': 'acknowledge', 'default': True}
    ]
    self.quick_choice_bar.show(message, choices, self.handle_error_acknowledgment)
```

### Multi-Option Dialogs
```python
def show_sort_options(self):
    message = "Sort files by:"
    choices = [
        {'key': 'n', 'label': 'Name', 'action': 'sort_name'},
        {'key': 's', 'label': 'Size', 'action': 'sort_size'},
        {'key': 'd', 'label': 'Date', 'action': 'sort_date'},
        {'key': 'c', 'label': 'Cancel', 'action': 'cancel', 'default': True}
    ]
    self.quick_choice_bar.show(message, choices, self.handle_sort_choice)
```

## Benefits

### User Experience
- **Quick Decisions**: Fast, keyboard-driven choice selection
- **Clear Options**: Obvious choice keys and labels
- **Non-Intrusive**: Uses status bar instead of modal dialogs
- **Consistent Interface**: Uniform appearance across all dialogs

### Developer Experience
- **Simple API**: Easy to create and customize dialogs
- **Helper Functions**: Pre-built dialogs for common scenarios
- **Flexible Configuration**: Customizable choices and callbacks
- **Easy Integration**: Seamless integration with main application

### Performance
- **Lightweight**: Minimal overhead for simple dialogs
- **Responsive**: Immediate response to user input
- **Efficient Rendering**: Optimized drawing and updates
- **Memory Efficient**: Low memory usage for dialog state

## Future Enhancements

### Potential Improvements
- **Choice Icons**: Visual icons for different choice types
- **Keyboard Shortcuts**: Additional keyboard shortcuts for common choices
- **Choice Grouping**: Group related choices visually
- **Animation**: Smooth transitions for choice selection
- **Sound Feedback**: Optional audio feedback for choices

### Advanced Features
- **Context Menus**: Right-click context menu integration
- **Choice History**: Remember recent choices for quick access
- **Custom Styling**: User-configurable choice bar appearance
- **Multi-Line Messages**: Support for longer, multi-line messages
- **Progress Integration**: Show progress within choice dialogs

## Testing

### Test Coverage
- **Choice Selection**: Verify correct choice handling
- **Input Processing**: Test all input methods and edge cases
- **Display**: Test layout and rendering in various scenarios
- **Integration**: Test integration with main application
- **Error Handling**: Test error conditions and recovery

### Test Scenarios
- **Basic Choices**: Simple yes/no and OK dialogs
- **Complex Choices**: Multi-option dialogs with various keys
- **Edge Cases**: Long messages, many choices, narrow terminals
- **Error Conditions**: Invalid inputs and error handling
- **Performance**: Response time and rendering efficiency

## Conclusion

The Quick Choice Bar Component provides an efficient, user-friendly interface for quick decision dialogs in TFM. Its lightweight design, flexible configuration, and seamless integration make it ideal for confirmation dialogs, error messages, and simple choice selections without disrupting the user's workflow.