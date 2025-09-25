# TFM Color Debugging Feature

## Overview

The TFM Color Debugging feature provides comprehensive tools to diagnose and troubleshoot color rendering issues across different terminals and environments. This feature was added to help users understand why TFM might render with colors on one laptop but only in black and white on another.

## Problem Statement

Users reported inconsistent color behavior between different systems:
- TFM renders with full colors on some laptops
- TFM renders only in black and white on other laptops
- Need to understand terminal capabilities and color support differences

## Solution

Added a `--color-test` command line argument with multiple testing modes to diagnose color issues without starting the full TFM interface.

## Usage

```bash
python tfm.py --color-test <mode>
```

### Available Modes

#### `info` - Basic Information
Shows basic color and terminal information without requiring curses initialization.

```bash
python tfm.py --color-test info
```

**Output includes:**
- Terminal environment variables (TERM, COLORTERM, etc.)
- Available color schemes
- RGB and fallback color definitions count
- Current color scheme

#### `schemes` - Color Scheme Details
Lists all available color schemes with detailed RGB and fallback color values.

```bash
python tfm.py --color-test schemes
```

**Output includes:**
- Complete color scheme definitions
- RGB values for each color
- Fallback color mappings
- Key color comparisons between schemes

#### `capabilities` - Terminal Capabilities Test
Tests terminal color support capabilities using curses.

```bash
python tfm.py --color-test capabilities
```

**Features:**
- Terminal color count and pair support
- RGB color support detection
- Basic color test display
- TFM file color testing
- Interface color testing

#### `rgb-test` - RGB Color Test
Forces RGB color mode to test RGB functionality specifically.

```bash
python tfm.py --color-test rgb-test
```

**Features:**
- Forces RGB mode even if fallback is normally used
- RGB gradient test
- Current scheme RGB value display
- RGB color initialization testing

#### `fallback-test` - Fallback Color Test
Forces fallback color mode to test basic color compatibility.

```bash
python tfm.py --color-test fallback-test
```

**Features:**
- Forces fallback mode even if RGB is supported
- Basic color mapping display
- Fallback color testing with file samples
- Compatibility verification

#### `interactive` - Interactive Color Tester
Provides an interactive interface to test different color settings live.

```bash
python tfm.py --color-test interactive
```

**Features:**
- Live color scheme switching
- Fallback mode toggling
- Sample file manager display
- Real-time color testing
- Detailed information display

## Implementation Details

### File Structure

```
src/tfm_color_tester.py     # Main color testing module
test/test_color_debugging.py # Test suite for color debugging
demo/demo_color_debugging.py # Demo script showing usage
doc/COLOR_DEBUGGING_FEATURE.md # This documentation
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

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: Only Black and White Colors
**Symptoms:** TFM displays only in black and white, no colors visible.

**Diagnosis:**
```bash
python tfm.py --color-test capabilities
```

**Possible Causes:**
1. Terminal doesn't support colors at all
2. TERM environment variable not set correctly
3. Color support disabled in terminal

**Solutions:**
1. Set `TERM=xterm-256color`
2. Check terminal color settings
3. Try different terminal emulator

#### Issue: Basic Colors Work, RGB Colors Don't
**Symptoms:** Some colors visible but not the full color scheme.

**Diagnosis:**
```bash
python tfm.py --color-test rgb-test
python tfm.py --color-test fallback-test
```

**Explanation:** Terminal supports 8/16 colors but not RGB (24-bit) colors. This is normal for many terminals.

**Solution:** TFM automatically falls back to basic colors. This is expected behavior.

#### Issue: Different Behavior on Different Laptops
**Symptoms:** Colors work on one system but not another.

**Diagnosis:**
Run on both systems:
```bash
python tfm.py --color-test info
python tfm.py --color-test capabilities
```

**Compare:**
- Terminal environment variables
- Color support capabilities
- Available color count

### Environment Variables

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

### Terminal Compatibility

#### Excellent Support (RGB + Fallback)
- iTerm2
- Terminal.app (macOS)
- GNOME Terminal
- Konsole
- Windows Terminal

#### Good Support (Fallback Colors)
- xterm
- PuTTY
- Most SSH clients
- Basic terminal emulators

#### Limited Support
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