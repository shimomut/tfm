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

### Retro themes with screen effects

Beyond the standard palettes (Dark+, Light+, Monokai, Dracula, Nord, Solarized,
Gruvbox), TFM ships four **retro hardware** themes, each pairing a period-correct
palette with a recommended *screen effect*:

- **8bit** — a saturated NES-era palette behind a CRT-TV look (chunky scanlines, a
  soft glow, a slight vignette and rolling band).
- **Sci-Fi** — an emissive cyan HUD with amber highlights behind a holographic
  look (heavy glow and bloom, a light scanline, an interference roll).
- **Pocket LCD** — the four-shade pea-green of a classic pocket handheld as a
  *flat reflective LCD*: no glow at all, and a dot-matrix pixel grid (fine dark
  gaps on both axes, so the screen reads as discrete square pixels) with a soft
  bezel vignette — no CRT scanlines.
- **Segment LCD** — a blue negative/backlit digital display (dashboard / clock)
  with a gentle backlit glow.

Select any of them from **View → Theme** or by cycling with `T`.

The screen effect is composited over the whole frame and is only rendered by the
**GUI backend** (`tfm.py --backend gui` on macOS/Windows) — a terminal has no
sub-cell pixels to filter and shows the palette alone. The effect turns on when
you switch to the theme and off when you switch away. You can add your own themes
(with or without an effect) via the `THEMES` dict in `~/.tfm/config.py`; see
[Configuration](CONFIGURATION_FEATURE.md).

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

TFM starts on the **Dark+** theme and remembers whichever theme you last switched
to (with `T`, or **View → Theme**) across restarts — there is no single
default-scheme setting. To add or customize themes, use the `THEMES` dict in
`~/.tfm/config.py` (see [Configuration](CONFIGURATION_FEATURE.md)).

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

- **In TFM**: Press '?' for help, which mentions the 'T' key
- **Command line**: Run `python3 show_color_schemes.py` to see all available schemes
- **Log messages**: TFM shows what type of colors your terminal supports

The color scheme feature makes TFM look good in any terminal environment!