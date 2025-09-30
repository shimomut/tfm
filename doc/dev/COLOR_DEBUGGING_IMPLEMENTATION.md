# TFM Color Debugging Implementation

## Overview

The TFM Color Debugging feature provides comprehensive tools to diagnose and troubleshoot color rendering issues across different terminals and environments. This document covers the implementation details for developers.

## Implementation Details

### File Structure

```
src/tfm_color_tester.py     # Main color testing module
test/test_color_debugging.py # Test suite for color debugging
demo/demo_color_debugging.py # Demo script showing usage
doc/COLOR_DEBUGGING_FEATURE.md # User documentation
doc/dev/COLOR_DEBUGGING_IMPLEMENTATION.md # This developer documentation
```

### Key Functions

#### `run_color_test(test_mode)`
Main entry point for color testing functionality.

#### `print_basic_info()`
Displays basic color information without curses.

#### `test_color_capabilities(stdscr)`
Tests terminal color capabilities with curses interface.

#### `interactive_color_tester(stdscr)`
Provides interactive color testing interface.

### Integration with Main TFM

The color testing feature is integrated into the main TFM entry point (`tfm.py`) through argument parsing:

```python
parser.add_argument(
    '--color-test',
    type=str,
    metavar='MODE',
    choices=['info', 'schemes', 'capabilities', 'rgb-test', 'fallback-test', 'interactive'],
    help='Run color debugging tests'
)
```

When `--color-test` is specified, the color testing module runs instead of the main TFM interface.

## Available Test Modes

### `info` - Basic Information
Shows basic color and terminal information without requiring curses initialization.

**Output includes:**
- Terminal environment variables (TERM, COLORTERM, etc.)
- Available color schemes
- RGB and fallback color definitions count
- Current color scheme

### `schemes` - Color Scheme Details
Lists all available color schemes with detailed RGB and fallback color values.

**Output includes:**
- Complete color scheme definitions
- RGB values for each color
- Fallback color mappings
- Key color comparisons between schemes

### `capabilities` - Terminal Capabilities Test
Tests terminal color support capabilities using curses.

**Features:**
- Terminal color count and pair support
- RGB color support detection
- Basic color test display
- TFM file color testing
- Interface color testing

### `rgb-test` - RGB Color Test
Forces RGB color mode to test RGB functionality specifically.

**Features:**
- Forces RGB mode even if fallback is normally used
- RGB gradient test
- Current scheme RGB value display
- RGB color initialization testing

### `fallback-test` - Fallback Color Test
Forces fallback color mode to test basic color compatibility.

**Features:**
- Forces fallback mode even if RGB is supported
- Basic color mapping display
- Fallback color testing with file samples
- Compatibility verification

### `interactive` - Interactive Color Tester
Provides an interactive interface to test different color settings live.

**Features:**
- Live color scheme switching
- Fallback mode toggling
- Sample file manager display
- Real-time color testing
- Detailed information display

## Environment Variables

Key environment variables that affect color support:

- `TERM` - Terminal type identifier
  - `xterm` - Basic xterm
  - `xterm-256color` - 256-color support
  - `screen-256color` - Screen with 256 colors
  
- `COLORTERM` - Color support indicator
  - `truecolor` - 24-bit RGB support
  - `24bit` - 24-bit RGB support
  
- `TERM_PROGRAM` - Terminal application name
  - `iTerm.app` - iTerm2 on macOS
  - `Apple_Terminal` - Terminal.app on macOS
  - `vscode` - VS Code integrated terminal

## Terminal Compatibility

### Excellent Support (RGB + Fallback)
- iTerm2
- Terminal.app (macOS)
- GNOME Terminal
- Konsole
- Windows Terminal

### Good Support (Fallback Colors)
- xterm
- PuTTY
- Most SSH clients
- Basic terminal emulators

### Limited Support
- Very old terminals
- Some embedded systems
- Text-only environments

## Testing

### Automated Tests

Run the test suite:
```bash
python -m pytest test/test_color_debugging.py -v
```

### Manual Testing

1. **Basic functionality:**
   ```bash
   python tfm.py --color-test info
   ```

2. **Interactive testing:**
   ```bash
   python tfm.py --color-test interactive
   ```

3. **Cross-platform testing:**
   Test on different terminals and operating systems.

### Demo Script

Run the demo to see all features:
```bash
python demo/demo_color_debugging.py
```

## Future Enhancements

Potential improvements for the color debugging feature:

1. **Color Scheme Editor**
   - Interactive color scheme creation
   - Custom RGB value testing
   - Scheme export/import

2. **Terminal Detection**
   - Automatic terminal type detection
   - Recommended settings per terminal
   - Terminal-specific optimizations

3. **Color Blindness Support**
   - Color blindness simulation
   - Alternative color schemes
   - Accessibility testing

4. **Performance Testing**
   - Color rendering performance
   - Memory usage analysis
   - Optimization recommendations

## Related Files

- `src/tfm_colors.py` - Core color system
- `src/tfm_const.py` - Color constants
- `src/tfm_config.py` - Configuration system
- `tfm.py` - Main entry point

## References

- [Terminal Color Support](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors)
- [Curses Color Documentation](https://docs.python.org/3/library/curses.html#curses.init_color)
- [Terminal Compatibility Guide](https://github.com/termstandard/colors)