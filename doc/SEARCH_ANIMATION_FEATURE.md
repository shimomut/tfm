# Progress Animation Feature

## Overview

TFM shows animated progress indicators during long-running operations like searching files. These animations let you know that TFM is working and provide visual feedback during operations.

## Animation Styles

You can choose from several animation styles:

1. **Spinner** - Classic spinning indicator (default)
   - Shows: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`
   - Best for general use

2. **Dots** - Minimalist dot animation
   - Shows: `⠁ ⠂ ⠄ ⡀ ⢀ ⠠ ⠐ ⠈`
   - Good for low-distraction environments

3. **Progress** - Progress bar style
   - Shows: `▏ ▎ ▍ ▌ ▋ ▊ ▉ █`
   - Visual representation of activity

4. **Bounce** - Simple bouncing dot
   - Shows: `⠁ ⠂ ⠄ ⠂`
   - Minimal and rhythmic

5. **Pulse** - Pulsing circle
   - Shows: `● ◐ ◑ ◒ ◓ ◔ ◕ ○`
   - Calming and smooth

6. **Wave** - Wave-like bars
   - Shows: `▁ ▂ ▃ ▄ ▅ ▆ ▇ █ ▇ ▆ ▅ ▄ ▃ ▂`
   - Dynamic and engaging

7. **Clock** - Clock face animation
   - Shows: `🕐 🕑 🕒 🕓 🕔 🕕 🕖 🕗 🕘 🕙 🕚 🕛`
   - Clear progression indication

8. **Arrow** - Rotating arrow
   - Shows: `← ↖ ↑ ↗ → ↘ ↓ ↙`
   - Clear motion indication

## Configuration

Add these settings to your TFM configuration file (`~/.tfm/config.py`):

```python
class Config(DefaultConfig):
    # Choose your animation style
    PROGRESS_ANIMATION_PATTERN = 'spinner'  # Default: 'spinner'
    PROGRESS_ANIMATION_SPEED = 0.2          # Default: 0.2 seconds
```

### Settings

- **PROGRESS_ANIMATION_PATTERN**: Choose your animation style
  - Options: `'spinner'`, `'dots'`, `'progress'`, `'bounce'`, `'pulse'`, `'wave'`, `'clock'`, `'arrow'`
  - Default: `'spinner'`

- **PROGRESS_ANIMATION_SPEED**: How fast the animation moves
  - Default: `0.2` seconds between frames
  - Smaller numbers = faster animation
  - Larger numbers = slower animation
  - Recommended: `0.1` to `0.5`

## How It Works

Animations run automatically during operations like searching. You don't need to do anything - just start a search and you'll see the animation.

### What You'll See

**Spinner Animation:**
```
Searching ⠋ (15 found)
Searching ⠙ (28 found)
Searching ⠹ (42 found)
```

**Dots Animation:**
```
Searching ⠁ (15 found)
Searching ⠂ (28 found)
Searching ⠄ (42 found)
```

**Progress Animation:**
```
Searching [█░░░░░░░] (15 found)
Searching [██░░░░░░] (28 found)
Searching [███░░░░░] (42 found)
```

## When You'll See Animations

- **File Search**: When searching for files by name
- **Content Search**: When searching inside files
- **Long Operations**: During any operation that takes time

## Troubleshooting

### Animation Not Showing
- Check that your terminal supports Unicode characters
- Try a different animation pattern (spinner works best)
- Make sure the animation speed isn't too slow

### Animation Too Fast or Slow
- Adjust the `PROGRESS_ANIMATION_SPEED` setting
- Try values between 0.1 (fast) and 0.5 (slow)

### Characters Look Wrong
- Some terminals don't support all Unicode characters
- Try the 'spinner' pattern - it has the best compatibility
- Consider upgrading to a modern terminal

## Tips

- The 'spinner' pattern works in most terminals
- Slower speeds (0.3-0.5) are easier on the eyes
- Faster speeds (0.1-0.2) feel more responsive
- The animation doesn't affect search speed or performance