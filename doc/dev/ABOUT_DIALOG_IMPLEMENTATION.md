# About Dialog Implementation

## Overview

The About Dialog is implemented as a UILayer component that displays application information with an animated Matrix-style background. This document describes the implementation details for developers.

## Architecture

### Components

1. **MatrixColumn**: Manages a single column of falling characters
2. **AboutDialog**: Main dialog component implementing UILayer interface

### File Structure

- `src/tfm_about_dialog.py`: Main implementation
- `test/test_about_dialog.py`: Unit and integration tests
- `demo/demo_about_menu.py`: Standalone demo application

## MatrixColumn Class

### Purpose

Represents a single column of falling Matrix-style characters with independent animation state.

### Key Attributes

- `x`: Column x position on screen
- `y`: Current y position (can be negative for off-screen)
- `speed`: Fall speed (characters per frame)
- `length`: Trail length (number of visible characters)
- `chars`: List of random characters for this column

### Animation Logic

```python
def update(self, dt):
    """Update column position based on time delta"""
    self.y += self.speed
    
    # Reset when column goes off screen
    if self.y - self.length > self.height:
        self.y = random.randint(-self.height // 2, 0)
        # Randomize speed and length for variety
```

### Character Selection

Uses full-width katakana characters (zenkaku) from Unicode range U+30A0 to U+30FF for an authentic Matrix aesthetic.

## AboutDialog Class

### UILayer Interface Implementation

Implements all required UILayer methods:

- `handle_key_event()`: Any key closes the dialog
- `handle_char_event()`: Any character closes the dialog
- `handle_system_event()`: Handles resize and close events
- `handle_mouse_event()`: Mouse button down closes the dialog
- `render()`: Draws the dialog and animation
- `is_full_screen()`: Returns True (covers entire screen)
- `mark_dirty()`: Marks for redraw
- `should_close()`: Returns True when dialog should close

### Animation System

#### Initialization

```python
def show(self):
    height, width = self.renderer.get_dimensions()
    self.matrix_columns = []
    # Create columns without spacing (every column)
    for x in range(0, width):
        self.matrix_columns.append(MatrixColumn(x, height))
```

#### Update Loop

```python
def _draw_matrix_background(self, height, width):
    current_time = time.time()
    dt = current_time - self.last_update_time
    
    # Update all columns
    for column in self.matrix_columns:
        column.update(dt)
    
    # Draw visible characters with brightness variation
    for column in self.matrix_columns:
        for y, char, brightness in column.get_visible_chars():
            # Use TextAttribute.BOLD/NORMAL/DIM based on brightness
            # Head (bottom, i=0) is brightest, tail (top) is dimmest
```

### Rendering Pipeline

1. **Background**: Draw Matrix animation across entire screen
2. **Dialog Box**: Draw centered dialog with border
3. **Content**: Draw logo, version, and info text
4. **Cleanup**: Mark as not needing redraw

### Color Scheme

- **Matrix characters**: Green (color pair 2)
- **Dialog border**: Status color with BOLD attribute
- **Dialog background**: Status color (solid to hide Matrix behind content)
- **Logo**: Regular file color with BOLD attribute
- **GitHub URL**: Status color with UNDERLINE attribute

## Integration with TFM

### Menu System

The About dialog is triggered from the menu system:

```python
# In tfm_main.py
def _action_show_about(self):
    """Show About TFM dialog with Matrix-style animation."""
    self.about_dialog.show()
    self.push_layer(self.about_dialog)
```

### Initialization

```python
# In FileManager.__init__()
self.about_dialog = AboutDialog(self.config, renderer)
```

### Menu Configuration

Defined in `tfm_menu_manager.py`:
- `APP_ABOUT`: macOS application menu
- `HELP_ABOUT`: Help menu (all platforms)

## Performance Considerations

### Animation Optimization

- Columns update independently
- Only visible characters are drawn
- Uses cached time delta for smooth animation
- Automatically adjusts to screen size changes

### Memory Management

- Matrix columns are created on show, destroyed on exit
- Character lists are small (5-15 characters per column)
- No persistent animation state when dialog is closed

## Testing

### Unit Tests

- `TestMatrixColumn`: Tests column animation logic
- `TestAboutDialog`: Tests dialog functionality
- `TestAboutDialogIntegration`: Tests complete lifecycle

### Test Coverage

- Initialization and cleanup
- Event handling (keyboard, character, system, mouse)
- Animation updates
- Resize handling
- UILayer interface compliance

### Running Tests

```bash
PYTHONPATH=.:src:ttk python -m pytest test/test_about_dialog.py -v
```

## Demo Application

The demo application (`demo/demo_about_menu.py`) provides a standalone way to test the About dialog:

```bash
PYTHONPATH=.:src:ttk python demo/demo_about_menu.py
```

**Note**: This is a TUI application and will block execution. Do not run in automated scripts.

## Future Enhancements

Potential improvements:

1. **Configurable animation speed**: Allow users to adjust animation speed
2. **Alternative effects**: Support different background animations
3. **Color themes**: Match Matrix colors to current color scheme
4. **Performance mode**: Disable animation on slow terminals
5. **Additional info**: Show build date, Python version, etc.

## References

- UILayer interface: `src/tfm_ui_layer.py`
- Menu system: `src/tfm_menu_manager.py`
- TTK rendering: `ttk/` directory
- Constants: `src/tfm_const.py`
