# Event Handling Feature

## Overview

TFM uses a sophisticated event handling system that distinguishes between command keys and text input. This allows keyboard shortcuts to work reliably while also supporting natural text entry in dialogs and input fields.

## Key Concepts

### Two Types of Input

TFM handles two distinct types of keyboard input:

1. **Command Keys**: Keyboard shortcuts for file manager operations
   - Examples: Q to quit, A to select all, arrows for navigation
   - Handled immediately by the file manager
   - Work globally throughout the application

2. **Text Input**: Characters typed into text fields
   - Examples: Typing filenames, search queries, directory paths
   - Handled by text input widgets (dialogs, search boxes)
   - Only active when a text field has focus

### How It Works

When you press a key:

1. **Command Check**: TFM first checks if it's a command key
   - If it matches a command (like Q for quit), the command executes
   - If it doesn't match any command, it continues to step 2

2. **Text Input**: If not a command, TFM checks if it's text input
   - If a text field is active, the character is inserted
   - If no text field is active, the key press is ignored

This two-step process ensures that:
- Commands work everywhere (Q always quits)
- Text input works in dialogs (you can type 'q' in a filename)
- No conflicts between commands and text entry

## User Experience

### Command Mode (Default)

When no dialog is open, TFM is in command mode:

- **Q**: Quit the application
- **A**: Select all files
- **Arrow keys**: Navigate file list
- **Enter**: Open file or directory
- **F3**: View file
- **F4**: Edit file
- **F5**: Copy files
- **F6**: Move/rename files
- **F7**: Create directory
- **F8**: Delete files

### Text Input Mode (Dialogs)

When a dialog is open with a text field:

- **Printable characters**: Typed into the text field
- **Arrow keys**: Move cursor within text
- **Home/End**: Jump to start/end of text
- **Backspace/Delete**: Remove characters
- **Enter**: Confirm and close dialog
- **Escape**: Cancel and close dialog

### Mixed Mode (Search)

Some features like search combine both modes:

- **/** (slash): Enter search mode
- **Type characters**: Build search query
- **Backspace**: Remove characters from query
- **Enter**: Execute search
- **Escape**: Cancel search

## Examples

### Example 1: Renaming a File

1. Select a file and press **F6** (rename)
2. Dialog opens with current filename
3. Type new filename (e.g., "report.txt")
   - Characters are inserted into text field
   - Q doesn't quit, it types 'q'
4. Press **Enter** to confirm
   - File is renamed
   - Dialog closes, back to command mode

### Example 2: Creating a Directory

1. Press **F7** (create directory)
2. Dialog opens with empty text field
3. Type directory name (e.g., "projects")
4. Press **Enter** to confirm
   - Directory is created
   - Dialog closes

### Example 3: Searching for Files

1. Press **/** (start search)
2. Type search query (e.g., "*.txt")
3. Press **Enter** to search
   - Files matching pattern are highlighted
   - Back to command mode

## Technical Details

### Event Flow

```
Keyboard Input
    ↓
Command Handler
    ├── Command matched? → Execute command
    └── Not matched? → Continue
    ↓
Text Input Handler
    ├── Text field active? → Insert character
    └── Not active? → Ignore
```

### Modifier Keys

Modifier keys (Ctrl, Alt, Cmd) always create commands, never text input:

- **Ctrl+C**: Copy (command)
- **Ctrl+V**: Paste (command)
- **Ctrl+A**: Select all (command)
- **Alt+key**: Menu shortcuts (command)

Shift is special:
- **Shift+A**: Types uppercase 'A' (text input)
- **Shift+1**: Types '!' (text input)
- **Shift+Arrow**: Extends selection (command)

### Special Keys

Special keys are always commands, never text input:

- **Arrow keys**: Navigation
- **Function keys (F1-F12)**: Commands
- **Home/End**: Navigation or text cursor movement
- **Page Up/Down**: Scrolling
- **Tab**: Focus navigation
- **Enter**: Confirm or open
- **Escape**: Cancel or close

## Best Practices

### For Users

1. **Learn the commands**: Memorize common shortcuts (Q, A, F3-F8)
2. **Use Enter to confirm**: Always press Enter in dialogs
3. **Use Escape to cancel**: Press Escape to close dialogs without changes
4. **Watch the status bar**: Shows current mode and available commands

### For Developers

1. **Use isinstance checks**: Always check event type before handling
2. **Return consumption status**: Return True when command is handled
3. **Handle both event types**: Text widgets should handle both KeyEvent and CharEvent
4. **Test with dialogs**: Ensure commands don't interfere with text input

## Troubleshooting

### Problem: Command keys don't work

**Cause**: A dialog might be open and capturing input

**Solution**: Press Escape to close any open dialogs

### Problem: Can't type certain characters

**Cause**: Character might be bound to a command

**Solution**: Check if you're in a text field. If not, open a dialog first.

### Problem: Text appears in wrong place

**Cause**: Wrong text field has focus

**Solution**: Click or tab to the correct text field

## See Also

- [Key Bindings Selection Feature](KEY_BINDINGS_SELECTION_FEATURE.md) - Customize keyboard shortcuts
- [Text Editor Feature](TEXT_EDITOR_FEATURE.md) - Built-in text editor
- [Jump Dialog Feature](JUMP_DIALOG_FEATURE.md) - Quick directory navigation
- [Search Animation Feature](SEARCH_ANIMATION_FEATURE.md) - File search functionality
