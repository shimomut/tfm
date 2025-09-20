# Color Schemes Feature

## Overview

TFM now supports multiple color schemes to provide better visual experience in different environments. The system includes two built-in color schemes:

- **Dark** - Optimized for dark terminal backgrounds (default)
- **Light** - Optimized for light terminal backgrounds

## Features

### Built-in Color Schemes

#### Dark Scheme
- Dark blue-gray backgrounds for headers, footers, and status bars
- Bright colors for file types (yellow directories, green executables)
- Light gray text for regular files
- Optimized for dark terminal backgrounds

#### Light Scheme  
- Pure white backgrounds for all UI elements
- Pure black text for all foreground elements
- High contrast monochrome design
- Optimized for light terminal backgrounds
- Simple and clean appearance

### Color Elements

Both schemes define colors for:
- **File Types**: Directories, executables, regular files
- **Selection**: Selected items highlighting
- **Interface**: Headers, footers, status bar, pane boundaries
- **Logs**: System messages, stdout, stderr
- **Syntax Highlighting**: Keywords, strings, comments, numbers, operators, built-ins
- **Search**: Match highlighting, current match highlighting

### RGB and Fallback Support

- **RGB Colors**: Full 24-bit color support for terminals that support it
- **Fallback Colors**: Standard 8/16 color fallbacks for basic terminals
- **Automatic Detection**: System automatically detects terminal capabilities

## Usage

### Runtime Color Scheme Toggle

Press `t` to toggle between Dark and Light color schemes while TFM is running.

### Configuration

Set the default color scheme in your configuration file (`~/.tfm/config.py`):

```python
class Config:
    # Color settings
    COLOR_SCHEME = 'dark'  # 'dark' or 'light'
```

### Key Binding Customization

Customize the color scheme toggle key in your configuration:

```python
KEY_BINDINGS = {
    'toggle_color_scheme': ['t'],  # Change to your preferred key
    # ... other bindings
}
```

## API Reference

### Functions

#### `get_available_color_schemes()`
Returns a list of available color scheme names.

#### `get_current_color_scheme()`
Returns the name of the currently active color scheme.

#### `set_color_scheme(scheme_name)`
Sets the color scheme to the specified name. Does not reinitialize colors.

#### `toggle_color_scheme()`
Toggles between 'dark' and 'light' schemes. Returns the new scheme name.

#### `init_colors(color_scheme=None)`
Initializes curses colors with the specified or current color scheme.

#### `print_current_color_scheme()`
Prints information about the current color scheme to stdout.

#### `print_all_color_schemes()`
Prints information about all available color schemes to stdout.

### Color Scheme Structure

Each color scheme is defined as a dictionary with color definitions:

```python
COLOR_SCHEMES = {
    'scheme_name': {
        'COLOR_NAME': {
            'color_num': 100,           # Curses color number
            'rgb': (red, green, blue)   # RGB values 0-255
        },
        # ... more colors
    }
}
```

## Implementation Details

### Color Initialization

1. Color scheme is loaded from configuration on startup
2. `init_colors()` is called with the configured scheme
3. RGB colors are defined if terminal supports them
4. Fallback colors are used for basic terminals
5. Color pairs are initialized for all UI elements

### Runtime Switching

1. User presses toggle key (`t` by default)
2. `toggle_color_scheme()` updates the global scheme variable
3. `init_colors()` is called to reinitialize all color pairs
4. Screen is marked for full redraw
5. New colors take effect immediately

### Terminal Compatibility

- **RGB Terminals**: Use full 24-bit color definitions
- **256-Color Terminals**: Use RGB colors mapped to available palette
- **16-Color Terminals**: Use standard curses color constants
- **8-Color Terminals**: Use basic color fallbacks

## Customization

### Adding New Color Schemes

To add a new color scheme, extend the `COLOR_SCHEMES` dictionary in `tfm_colors.py`:

```python
COLOR_SCHEMES['my_scheme'] = {
    'DIRECTORY_FG': {
        'color_num': 101,
        'rgb': (255, 128, 0)  # Orange directories
    },
    # ... define all required colors
}
```

### Modifying Existing Schemes

Edit the RGB values in the `COLOR_SCHEMES` dictionary to customize colors:

```python
COLOR_SCHEMES['dark']['DIRECTORY_FG']['rgb'] = (255, 255, 0)  # Yellow directories
```

### Custom Fallback Colors

Modify `FALLBACK_COLOR_SCHEMES` for terminals without RGB support:

```python
FALLBACK_COLOR_SCHEMES['dark']['DIRECTORY_FG'] = curses.COLOR_YELLOW
```

## Troubleshooting

### Colors Not Changing
- Ensure your terminal supports color changes
- Check that `USE_COLORS = True` in configuration
- Verify terminal has sufficient color support

### Wrong Colors Displayed
- Terminal may not support RGB colors (using fallbacks)
- Check terminal color capabilities with `get_color_capabilities()`
- Some terminals may require specific color settings

### Performance Issues
- Color initialization is fast but full screen redraws may be slower
- Consider reducing toggle frequency in scripts
- RGB color calculation is minimal overhead

## Utilities

### Color Scheme Information Tool

Use the `show_color_schemes.py` script to view color scheme information without starting TFM:

```bash
# Show all color schemes
python3 show_color_schemes.py

# Show current scheme only
python3 show_color_schemes.py current

# List available schemes
python3 show_color_schemes.py list

# Set specific scheme
python3 show_color_schemes.py light
```

### In-Application Information

- **Color Palette**: Press 'c' in debug mode to see the color palette with current scheme info
- **Log Output**: When toggling color schemes with 't', detailed information is printed to the log
- **Initialization Messages**: TFM displays whether RGB or fallback colors are being used
- **Help System**: Color scheme toggle is documented in the help dialog ('?' key)

### Color Initialization Messages

TFM automatically detects your terminal's color capabilities and displays informative messages:

- **RGB Support**: There is no message in this case.
- **No RGB Support**: `"Terminal does not support RGB colors - using fallback colors for dark scheme"`
- **RGB Failed**: `"RGB color initialization failed - using fallback colors for dark scheme"`
- **Default Colors Set**: `"Set terminal default colors: fg=0, bg=7"`
- **Default Colors Failed**: `"Warning: Could not set terminal default background color"`

These messages help users understand:
- Whether they're getting full 24-bit colors or basic 8/16 colors
- If terminal default background is properly set for blank spaces
- Why colors might look different on different terminals
- When troubleshooting color-related issues

### Background Color Handling

TFM properly handles terminal background colors to ensure consistent appearance:

- **Default Colors**: Uses `curses.assume_default_colors()` to set terminal defaults
- **Blank Spaces**: Ensures blank areas match the color scheme background
- **Light Scheme**: White background for all blank spaces and uncolored areas
- **Dark Scheme**: Black background for all blank spaces and uncolored areas
- **Fallback**: Uses color pair 0 if default color setting is not supported

## Related Files

- `src/tfm_colors.py` - Color scheme definitions and functions
- `src/tfm_config.py` - Configuration system with color scheme support
- `src/_config.py` - Default configuration template
- `src/tfm_main.py` - Main application with color scheme integration
- `show_color_schemes.py` - Standalone color scheme information tool