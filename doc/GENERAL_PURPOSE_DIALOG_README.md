# GeneralPurposeDialog Class

A new reusable dialog system for TFM that can replace the existing individual dialog modes with a unified, flexible approach.

## Files Created

### Core Implementation
- **`src/tfm_general_purpose_dialog.py`** - Main dialog class and helper functions
- **`test_general_purpose_dialog.py`** - Comprehensive test suite
- **`demo_general_purpose_dialog.py`** - Interactive demo showing all dialog types
- **`integration_example.py`** - Detailed integration guide for TFM

## Features

### Current Capabilities
- **Status Line Input Dialogs** - Single-line text input with prompt and help text
- **Flexible Text Editing** - Full cursor control, text manipulation
- **Callback System** - Confirm and cancel callbacks for custom handling
- **Helper Functions** - Pre-configured dialogs for common TFM operations

### Dialog Types Supported
- Filter mode (`*.py`, `test_*`, etc.)
- Rename mode (single file renaming)
- Create directory mode
- Create file mode  
- Create archive mode (`.zip`, `.tar.gz`, `.tgz`)

## Usage Examples

### Basic Usage
```python
from tfm_general_purpose_dialog import GeneralPurposeDialog, DialogHelpers

# Create dialog instance
dialog = GeneralPurposeDialog(config)

# Show a simple input dialog
dialog.show_status_line_input(
    prompt="Enter name: ",
    help_text="ESC:cancel Enter:confirm",
    initial_text="default",
    callback=lambda text: print(f"Got: {text}"),
    cancel_callback=lambda: print("Cancelled")
)

# Handle input in main loop
if dialog.handle_key(key):
    continue  # Dialog handled the key

# Draw dialog
if dialog.is_active:
    dialog.draw(stdscr, safe_addstr_func)
```

### Using Helper Functions
```python
# Filter dialog
DialogHelpers.create_filter_dialog(dialog, current_filter="*.py")
dialog.callback = self.on_filter_confirm
dialog.cancel_callback = self.on_filter_cancel

# Rename dialog
DialogHelpers.create_rename_dialog(dialog, "old_name.txt", "new_name.txt")
dialog.callback = lambda text: self.rename_file(text)

# Create directory dialog
DialogHelpers.create_create_directory_dialog(dialog)
dialog.callback = lambda text: self.create_directory(text)
```

## Migration Benefits

### Code Reduction
- **~500+ lines removed** - Eliminates repetitive dialog code
- **5 separate editors → 1** - Single text editor instance
- **Unified input handling** - One key handler for all dialogs

### Consistency
- **Same look and feel** - All dialogs use identical styling
- **Consistent behavior** - Same key bindings across all dialog types
- **Uniform help text** - Standardized help text positioning

### Maintainability  
- **Single source of truth** - Dialog bugs fixed in one place
- **Easy to extend** - Add new dialog types without code duplication
- **Clear separation** - Dialog logic separated from main application

### Future Extensibility
- **Overlay dialogs** - Can add multi-line, centered overlay dialogs
- **Choice dialogs** - Yes/No, multiple choice dialogs
- **Validation** - Input validation can be added centrally
- **Dialog history** - Remember previous inputs across sessions

## Integration Steps

### 1. Add Import
```python
from tfm_general_purpose_dialog import GeneralPurposeDialog, DialogHelpers
```

### 2. Replace State Variables
```python
# OLD: Multiple dialog states
self.filter_mode = False
self.filter_editor = SingleLineTextEdit()
# ... (4 more similar blocks)

# NEW: Single dialog instance  
self.general_dialog = GeneralPurposeDialog(self.config)
```

### 3. Replace Mode Entry Methods
```python
# OLD: enter_filter_mode()
def enter_filter_mode(self):
    self.filter_mode = True
    # ... setup code

# NEW: 
def enter_filter_mode(self):
    current_pane = self.get_current_pane()
    DialogHelpers.create_filter_dialog(self.general_dialog, current_pane['filter_pattern'])
    self.general_dialog.callback = self.on_filter_confirm
    self.general_dialog.cancel_callback = self.on_filter_cancel
```

### 4. Add Callback Methods
```python
def on_filter_confirm(self, filter_text):
    # Apply filter logic
    self.general_dialog.hide()
    
def on_filter_cancel(self):
    self.general_dialog.hide()
```

### 5. Replace Drawing Code
```python
# OLD: Multiple if blocks for each dialog type
if self.filter_mode:
    # ... draw filter dialog
elif self.rename_mode:
    # ... draw rename dialog
# ... (3 more similar blocks)

# NEW: Single draw call
if self.general_dialog.is_active:
    self.general_dialog.draw(self.stdscr, self.safe_addstr)
    return
```

### 6. Replace Input Handling
```python
# OLD: Multiple input handlers
if self.filter_mode:
    if self.handle_filter_input(key):
        continue
# ... (4 more similar blocks)

# NEW: Single input handler
if self.general_dialog.is_active:
    if self.general_dialog.handle_key(key):
        continue
```

## Testing

Run the test suite to verify functionality:
```bash
python3 test_general_purpose_dialog.py
```

Try the interactive demo:
```bash
python3 demo_general_purpose_dialog.py
```

## Architecture

### Class Structure
```
GeneralPurposeDialog
├── DialogType (constants)
├── show_status_line_input()
├── handle_key()
├── draw()
└── hide()

DialogHelpers (static methods)
├── create_filter_dialog()
├── create_rename_dialog()
├── create_create_directory_dialog()
├── create_create_file_dialog()
└── create_create_archive_dialog()
```

### Key Components
- **SingleLineTextEdit** - Reused for text input functionality
- **Callback system** - Flexible handling of confirm/cancel actions
- **Helper functions** - Pre-configured common dialog patterns
- **Type safety** - DialogType constants prevent errors

## Future Enhancements

### Planned Features
- **Overlay dialogs** - Centered, multi-line dialogs
- **Choice dialogs** - Yes/No, multiple choice options
- **Progress dialogs** - Show operation progress
- **Input validation** - Real-time input validation
- **Dialog themes** - Customizable dialog appearance

### Extension Points
- New dialog types can be added to `DialogType`
- Custom drawing methods for different dialog layouts
- Plugin system for custom dialog behaviors
- Integration with TFM's configuration system

This implementation provides a solid foundation for TFM's dialog system while maintaining backward compatibility and enabling future enhancements.