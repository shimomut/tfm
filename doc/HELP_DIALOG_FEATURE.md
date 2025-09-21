# Help Dialog Feature (? Key)

TFM now includes a comprehensive help dialog that shows all key bindings and usage information using the **?** key.

## Usage

### Basic Operation

- **? Key** or **h Key**: Show help dialog with all key bindings
- **ESC** or **q**: Close help dialog
- **↑/↓**: Scroll through help content
- **Page Up/Down**: Scroll by page
- **Home/End**: Jump to top/bottom of help

### Help Dialog Content

The help dialog is organized into clear sections:

#### Navigation
- Arrow keys for navigation
- Pane switching and directory navigation
- File selection and movement

#### File Operations
- File selection (Space, Ctrl+Space)
- Bulk operations (a, A for select all)
- File operations menu (m/M)
- Text viewing and editing (v/V, e/E)
- File details (i/I)

#### Search & Sorting
- Search functionality (f/F)
- Sort options and quick sort keys (1/2/3)
- Sort direction toggle (r/R)

#### View Options
- Hidden files toggle (.)
- Pane synchronization (o/O)
- Layout adjustments

#### Log Pane Controls
- Log pane resizing (bracket keys)
- Log scrolling (Shift+Up/Down)

#### General Controls
- Help access (? or h)
- Quit application (q/Q)
- Cancel operations (ESC)

#### Configuration
- Information about configuration files
- Tips for customization

#### Tips Section
- Best practices for using TFM
- Feature highlights and usage tips

## Key Features

### 1. Comprehensive Coverage
- All key bindings documented in one place
- Organized by functional categories
- Clear, concise descriptions

### 2. Scrollable Interface
- Full scrolling support for long content
- Page-based navigation for quick movement
- Home/End keys for instant navigation

### 3. Consistent with Other Dialogs
- Uses the same info dialog system as file details
- Familiar navigation controls
- Consistent visual styling

### 4. Always Accessible
- Available from any screen in TFM
- Multiple key bindings (? and h)
- No prerequisites or special modes required

## Implementation Details

### Dialog System Integration
- Uses existing `show_info_dialog()` infrastructure
- Leverages `handle_info_dialog_input()` for navigation
- Consistent with file details and other info dialogs

### Content Generation
- Dynamic help content generation
- Includes current version and GitHub information
- Organized sections for easy reference

### Key Binding Integration
- Integrated with existing key binding system
- Respects user configuration for help keys
- Works with both '?' and 'h' keys by default

## Configuration

### Key Bindings
The help dialog can be accessed via keys configured in `KEY_BINDINGS`:

```python
KEY_BINDINGS = {
    'help': ['?'],  # ? key shows help
    # ... other bindings
}
```

### Customization
Users can customize which keys trigger the help dialog by modifying the `help` key binding in their configuration file.

## Examples

### Quick Help Access
```
1. Press '?' or 'h' from anywhere in TFM
2. Help dialog opens with full key reference
3. Scroll through sections using arrow keys
4. Press 'q' or ESC to close and return
```

### Finding Specific Information
```
1. Open help dialog with '?'
2. Use Page Down to quickly navigate sections
3. Find the relevant section (e.g., "FILE OPERATIONS")
4. Review the key bindings for that category
5. Close help and use the learned keys
```

## Benefits

### 1. Self-Documenting Interface
- No need to remember all key bindings
- Quick reference always available
- Reduces learning curve for new users

### 2. Comprehensive Reference
- All functionality documented in one place
- Organized by logical categories
- Includes tips and best practices

### 3. Consistent User Experience
- Familiar dialog interface
- Standard navigation controls
- Integrated with existing TFM patterns

### 4. Accessibility
- Always available regardless of current state
- Multiple access keys for convenience
- Clear, readable formatting

## Technical Implementation

### Help Content Structure
The help dialog content is generated dynamically and includes:

- Version and project information
- Categorized key bindings
- Usage tips and best practices
- Configuration guidance

### Dialog Integration
- Uses existing info dialog infrastructure
- Supports full scrolling and navigation
- Consistent visual styling with other dialogs

### Key Binding System
- Integrated with TFM's configurable key binding system
- Supports multiple keys for the same action
- Respects user customizations

## Future Enhancements

Potential improvements for the help system:

1. **Context-Sensitive Help**: Show relevant help based on current mode
2. **Interactive Tutorials**: Step-by-step guides for complex operations
3. **Search Within Help**: Find specific key bindings quickly
4. **Customizable Help Content**: Allow users to add their own help sections

## Troubleshooting

### Help Dialog Not Opening
- Verify key bindings in configuration
- Check that '?' or 'h' keys are properly configured
- Ensure no conflicting key bindings

### Content Not Displaying
- Check terminal size (help requires minimum dimensions)
- Verify all constants are properly imported
- Check for any error messages in log pane

### Navigation Issues
- Use standard dialog navigation (↑↓, Page Up/Down)
- ESC or 'q' to close dialog
- Home/End for quick navigation to top/bottom

The help dialog feature makes TFM more user-friendly by providing comprehensive, always-accessible documentation of all available functionality.