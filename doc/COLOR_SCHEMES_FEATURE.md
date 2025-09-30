# Color Schemes Feature

## Overview

TFM supports different color schemes to look good in different terminal environments. You can choose between:

- **Dark** - Designed for dark terminal backgrounds (default)
- **Light** - Designed for light terminal backgrounds

## Available Color Schemes

### Dark Scheme (Default)
- Dark backgrounds with bright colored text
- Yellow directories, green executable files
- Good for dark terminal backgrounds
- Easy on the eyes in low-light environments

### Light Scheme  
- White backgrounds with black text
- High contrast, clean appearance
- Good for light terminal backgrounds
- Professional, minimal look

## What Gets Colored

Both color schemes change:
- **File Types**: Different colors for directories, executables, and regular files
- **Selected Items**: Highlighting for selected files
- **Interface**: Headers, footers, status bar, and pane borders
- **Log Messages**: Different colors for different types of messages
- **Text Viewer**: Syntax highlighting when viewing code files
- **Search Results**: Highlighting for search matches

## How to Use

### Switch Color Schemes

Press `t` to toggle between Dark and Light color schemes while TFM is running. The change happens immediately.

### Set Default Color Scheme

Set your preferred default in your configuration file (`~/.tfm/config.py`):

```python
class Config:
    # Choose your default color scheme
    COLOR_SCHEME = 'dark'  # Options: 'dark' or 'light'
```

### Change the Toggle Key

If you want to use a different key to switch color schemes:

```python
KEY_BINDINGS = {
    'toggle_color_scheme': ['t'],  # Change 't' to your preferred key
    # ... other bindings
}
```

## Terminal Compatibility

TFM automatically detects what your terminal supports:

- **Modern Terminals**: Get full 24-bit colors (millions of colors)
- **Older Terminals**: Get basic 8 or 16 colors (still looks good)
- **All Terminals**: Color schemes work everywhere

## Troubleshooting

### Colors Don't Change When Pressing 't'
- Make sure your terminal supports colors
- Check that colors are enabled in your configuration
- Try restarting TFM

### Colors Look Wrong
- Your terminal might not support full RGB colors (this is normal)
- TFM automatically uses simpler colors that work in your terminal
- Try a different terminal if you want more colors

### Colors Are Too Bright/Dark
- Switch between dark and light schemes with 't'
- Dark scheme works better with dark terminal backgrounds
- Light scheme works better with light terminal backgrounds

## Tips

- **Dark terminals**: Use the dark color scheme (default)
- **Light terminals**: Use the light color scheme (press 't' to switch)
- **SSH connections**: Colors work over SSH too
- **Screen/tmux**: Colors work in terminal multiplexers
- **Different terminals**: Try both schemes to see which looks better

## Getting More Information

You can see detailed color information:

- **In TFM**: Press '?' for help, which mentions the 't' key
- **Command line**: Run `python3 show_color_schemes.py` to see all available schemes
- **Log messages**: TFM shows what type of colors your terminal supports

The color scheme feature makes TFM look good in any terminal environment!