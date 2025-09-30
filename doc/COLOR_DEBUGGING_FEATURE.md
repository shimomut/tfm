# TFM Color Debugging Feature

## Overview

The TFM Color Debugging feature helps you diagnose and fix color display issues. If TFM shows colors on one computer but only black and white on another, this feature can help you understand why and fix the problem.

## Common Color Issues

- TFM shows full colors on some computers but not others
- Colors appear washed out or incorrect
- Only black and white text is visible
- Colors change unexpectedly between terminal sessions

## Quick Diagnosis

To check your color support, run:

```bash
python tfm.py --color-test info
```

This shows your terminal's color capabilities and current settings.

## Testing Modes

### Basic Information (`info`)
Shows your terminal's color support without starting TFM:
```bash
python tfm.py --color-test info
```

### Interactive Testing (`interactive`)
Test colors interactively with a live preview:
```bash
python tfm.py --color-test interactive
```

### Full Capabilities Test (`capabilities`)
Test all color features your terminal supports:
```bash
python tfm.py --color-test capabilities
```

### Other Test Modes
- `schemes` - View all available color schemes
- `rgb-test` - Test full RGB color support
- `fallback-test` - Test basic color compatibility



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

## Common Solutions

### Only Black and White Colors

If you see no colors at all:

1. **Check your terminal type:**
   ```bash
   echo $TERM
   ```
   Should show something like `xterm-256color`

2. **Set color support:**
   ```bash
   export TERM=xterm-256color
   ```

3. **Try a different terminal** - some terminals have better color support

### Colors Look Wrong

If colors appear but look incorrect:

1. **Test different color schemes** using the interactive mode
2. **Check if your terminal supports RGB colors**
3. **Try the fallback color mode**

### Different Behavior on Different Computers

Run the `info` test on both computers and compare:
- Terminal type (`TERM` variable)
- Color support capabilities
- Available color schemes

## Terminal Compatibility

### Best Color Support
- iTerm2 (macOS)
- Terminal.app (macOS)
- GNOME Terminal (Linux)
- Windows Terminal

### Basic Color Support
- xterm
- Most SSH clients
- Basic terminal emulators

### Limited Support
- Very old terminals
- Some embedded systems

## Getting Help

If you're still having color issues:

1. Run `python tfm.py --color-test info` and note the output
2. Try the interactive mode to test different settings
3. Check if other color-enabled programs work in your terminal
4. Consider switching to a terminal with better color support