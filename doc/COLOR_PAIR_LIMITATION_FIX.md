# TFM Color Pair Limitation Fix (32767 Issue)

## Problem Description

Some terminals report exactly **32767 color pairs** available, which is a known limitation that can cause RGB color initialization to fail. This results in TFM displaying only black and white instead of full colors.

### Symptoms
- `python tfm.py --color-test capabilities` shows "Color pairs: 32767"
- Colors work in some modes but not others
- RGB colors fail to initialize properly
- Terminal supports colors but TFM shows black and white

### Root Cause
The 32767 limit is a signed 16-bit integer limitation (2^15 - 1) in some terminal implementations or curses libraries. When TFM tries to initialize RGB colors, this limitation can cause:

1. **Color pair allocation failures** - Not enough pairs for RGB colors
2. **RGB color detection issues** - Terminal reports RGB support but can't actually use it
3. **Initialization timing problems** - RGB setup fails during color pair allocation

## Solutions

### Solution 1: Automatic Fallback (Recommended)

TFM now automatically detects the 32767 limitation and switches to fallback colors:

```python
# This is now built into TFM's color system
# No user action required - it happens automatically
```

**Test it:**
```bash
python tfm.py --color-test color-pairs
python tfm.py  # Should now show colors
```

### Solution 2: Force Fallback Mode

Manually force fallback colors if automatic detection doesn't work:

```bash
# Test fallback colors
python tfm.py --color-test fallback-test

# If colors work, make it permanent by adding to TFM config:
# ~/.tfm/config.py
FORCE_FALLBACK_COLORS = True
```

### Solution 3: Environment Variables

Try different terminal configurations:

```bash
# Option 1: Standard 256-color mode
export TERM=xterm-256color
export COLORTERM=256color

# Option 2: Screen-based terminals
export TERM=screen-256color

# Option 3: Disable RGB, use 256 colors
unset COLORTERM
export TERM=xterm-256color

# Test after each change:
python tfm.py --color-test capabilities
```

### Solution 4: Terminal-Specific Fixes

#### For Screen/Tmux:
```bash
# Add to ~/.screenrc:
termcapinfo xterm 'Co#256:AB=\E[48;5;%dm:AF=\E[38;5;%dm'

# Or start screen with:
screen -T xterm-256color
```

#### For SSH/Remote Sessions:
```bash
# On local machine, ensure TERM is forwarded:
ssh -o SendEnv=TERM user@host

# On remote machine:
export TERM=xterm-256color
```

#### For Different Terminals:
- **iTerm2**: Check Preferences → Profiles → Terminal → Report Terminal Type
- **Terminal.app**: Should work automatically
- **VS Code**: Set `"terminal.integrated.env.osx": {"TERM": "xterm-256color"}`
- **PuTTY**: Connection → Data → Terminal-type string: `xterm-256color`

## Diagnostic Tools

### Quick Check:
```bash
python tools/fix_color_pair_limitation.py
```

### Comprehensive Testing:
```bash
# Test color pair limitations
python tfm.py --color-test color-pairs

# Test different modes
python tfm.py --color-test capabilities
python tfm.py --color-test fallback-test
python tfm.py --color-test rgb-test

# Interactive testing
python tfm.py --color-test interactive
# Press 'P' to check color pair limitations
```

### Manual Verification:
```bash
# Check current capabilities
python -c "import curses; curses.wrapper(lambda s: print(f'Colors: {curses.COLORS}, Pairs: {curses.COLOR_PAIRS}'))"

# Test TFM
python tfm.py  # Should show colors now
```

## Technical Details

### The 32767 Limitation
- **Value**: 32767 = 2^15 - 1 (signed 16-bit integer max)
- **Cause**: Some curses implementations use signed 16-bit integers for color pair counts
- **Effect**: Limits available color pairs, can break RGB color allocation

### TFM's Color Usage
- **Basic colors**: Pairs 1-26 (file types, interface elements)
- **RGB colors**: Custom color numbers 100-150+ (when supported)
- **Background**: Pair 63 (for background color application)

### Fallback Strategy
When 32767 limitation is detected:
1. **Disable RGB colors** - Use standard terminal colors instead
2. **Use basic color pairs** - Stick to pairs 1-26
3. **Map RGB to standard** - Convert RGB definitions to closest standard colors

## Configuration Options

### Permanent Fallback Mode
Create `~/.tfm/config.py`:
```python
# Force fallback colors (disables RGB)
FORCE_FALLBACK_COLORS = True

# Use dark scheme with fallback colors
COLOR_SCHEME = 'dark'

# Reduce color complexity
SEPARATE_EXTENSIONS = False
```

### Conditional Fallback
```python
# Auto-detect and use fallback when needed
# (This is now the default behavior)
```

## Verification

After applying fixes, verify with:

```bash
# 1. Check capabilities
python tfm.py --color-test capabilities

# 2. Test color pairs
python tfm.py --color-test color-pairs

# 3. Test main application
python tfm.py

# 4. Compare modes
python tfm.py --color-test interactive
```

**Expected results:**
- Color pairs should show as working despite limitation
- Main TFM should display colors (may be basic colors instead of RGB)
- Both `--color-test` and main TFM should show consistent colors

## Troubleshooting

### If colors still don't work:
1. **Check terminal support**: `echo $TERM` and `echo $COLORTERM`
2. **Test basic colors**: `python tfm.py --color-test capabilities`
3. **Try different terminal**: Test in different terminal emulator
4. **Check SSH forwarding**: Ensure TERM is properly forwarded over SSH

### If only some colors work:
1. **Use fallback mode**: `python tfm.py --color-test fallback-test`
2. **Check color count**: May need to reduce color complexity
3. **Test incrementally**: Start with basic colors, add complexity gradually

### If performance is slow:
1. **Reduce color pairs**: Use simpler color scheme
2. **Disable RGB**: Force fallback mode
3. **Check terminal**: Some terminals are slow with many color pairs

## Related Issues

- **Issue**: Colors work in `--color-test` but not main TFM
  **Solution**: Fixed by initialization timing (separate issue)

- **Issue**: Colors work on one laptop but not another
  **Solution**: Check color pair counts on both systems

- **Issue**: Colors work locally but not over SSH
  **Solution**: Ensure TERM forwarding and consistent environment

## References

- [Curses Color Documentation](https://docs.python.org/3/library/curses.html#curses.init_color)
- [Terminal Color Standards](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors)
- [Screen Color Configuration](https://www.gnu.org/software/screen/manual/screen.html#Colors)