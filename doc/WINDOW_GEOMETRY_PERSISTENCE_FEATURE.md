# Window Geometry Persistence Feature

## Overview

When running TFM in desktop mode (CoreGraphics backend on macOS), the application automatically remembers your window's size and position. The next time you launch TFM, your window will appear exactly where you left it, at the same size.

This feature works seamlessly in the background - no configuration or manual saving required.

## How It Works

### Automatic Save
Every time you resize or move the TFM window, the new geometry is automatically saved. There's no need to manually save your preferences or use any special commands.

### Automatic Restore
When you launch TFM, the window automatically appears at the last saved size and position. If this is your first time launching TFM, the window will appear at the default size and position.

### Multi-Monitor Support
If you use multiple monitors, TFM remembers which monitor your window was on and restores it to that monitor. If that monitor is no longer available (e.g., you disconnected it), TFM will intelligently place the window on your primary monitor.

## Usage

### Normal Operation
Simply use TFM as you normally would:

1. **Resize the window** - Drag the window edges or corners to your preferred size
2. **Move the window** - Drag the title bar to position the window where you want it
3. **Quit TFM** - Close the application normally
4. **Relaunch TFM** - Your window will appear at the same size and position

That's it! No additional steps required.

### First Launch
On your first launch of TFM, the window will appear at the default size (1200x800 pixels) positioned near the top-left of your screen. After you adjust it to your preference, TFM will remember your settings.

## Resetting Window Geometry

If your window becomes positioned in an undesirable location (for example, off-screen after a monitor configuration change), you can reset it to the default size and position.

### Using the Demo Script
Run the reset demo script:

```bash
python demo/demo_window_geometry_persistence.py
```

This script demonstrates the reset functionality and allows you to test it interactively.

### Manual Reset (Advanced)
If you need to manually reset the window geometry, you can clear the saved preferences:

```bash
# On macOS, clear the saved window frame
defaults delete com.yourcompany.tfm "NSWindow Frame TFMMainWindow"
```

The next time you launch TFM, it will use the default window size and position.

## Multi-Monitor Scenarios

### Moving Between Monitors
When you move the TFM window to a different monitor, the position is saved relative to that monitor. TFM will restore the window to the same monitor on your next launch.

### Disconnecting Monitors
If you disconnect a monitor that TFM was previously displayed on:
- TFM will automatically detect that the saved position is no longer valid
- The window will be repositioned to a visible location on your primary monitor
- Your window size preference is preserved

### Changing Monitor Arrangements
If you rearrange your monitors (change their relative positions):
- TFM will attempt to restore the window to the saved position
- If the position is off-screen, macOS will automatically adjust it to be visible
- You may need to reposition the window to your preferred location

## Troubleshooting

### Window Appears in Wrong Location

**Problem**: The window appears in an unexpected location after changing monitor setup.

**Solution**: 
1. Move the window to your preferred location
2. The new position will be saved automatically
3. Alternatively, use the reset functionality to start fresh

### Window Size is Too Small/Large

**Problem**: The window is too small or too large for your current screen.

**Solution**:
1. Resize the window to your preferred size
2. The new size will be saved automatically
3. Alternatively, reset to default size using the demo script

### Window is Off-Screen

**Problem**: The window is positioned off-screen and you can't see it.

**Solution**:
macOS should automatically detect this and reposition the window. If it doesn't:
1. Use the manual reset command (see "Manual Reset" above)
2. Or run the demo script to reset the geometry

### Feature Not Working

**Problem**: Window geometry is not being saved/restored.

**Possible Causes**:
1. **Not running in desktop mode** - This feature only works with the CoreGraphics backend (desktop mode on macOS). It does not work in terminal mode.
2. **Permissions issue** - TFM may not have permission to write to user defaults.

**Solution**:
1. Verify you're running TFM in desktop mode: `python tfm.py --backend coregraphics`
2. Check console output for any warning messages about persistence failures
3. Try resetting the window geometry using the demo script

### Corrupted Preferences

**Problem**: TFM fails to launch or behaves strangely related to window positioning.

**Solution**:
Clear the saved preferences using the manual reset command:
```bash
defaults delete com.yourcompany.tfm "NSWindow Frame TFMMainWindow"
```

## Technical Details

### Where Settings Are Stored
Window geometry is stored in macOS's user defaults system (NSUserDefaults). This is the standard location for application preferences on macOS.

### What Is Saved
The following information is saved:
- Window width (in pixels)
- Window height (in pixels)
- Window X position (horizontal position on screen)
- Window Y position (vertical position on screen)

### When Settings Are Saved
Settings are saved automatically:
- Immediately after you resize the window
- Immediately after you move the window
- When you quit the application

### Backend Compatibility
This feature is only available when running TFM in desktop mode with the CoreGraphics backend on macOS. It is not available in terminal mode (curses backend) as terminal windows are managed by your terminal emulator, not by TFM.

## Frequently Asked Questions

### Q: Can I disable this feature?
**A:** Currently, the feature is always enabled in desktop mode. If you prefer not to use it, you can manually reset the window geometry each time you launch TFM, though this is not recommended.

### Q: Does this work on Linux or Windows?
**A:** No, this feature is currently macOS-specific and only works with the CoreGraphics backend. Terminal mode on all platforms does not support window geometry persistence as the terminal emulator controls the window.

### Q: Will my settings sync across multiple Macs?
**A:** No, window geometry settings are stored locally on each Mac. If you use TFM on multiple Macs, each will maintain its own window geometry preferences.

### Q: What happens if I use TFM on different sized monitors?
**A:** TFM saves the absolute window size in pixels. If you move to a smaller monitor, the window may be larger than the screen. macOS will typically adjust the window to fit, but you may want to resize it for optimal viewing.

### Q: Can I save different window sizes for different tasks?
**A:** Currently, TFM saves a single window geometry. If you want different sizes for different tasks, you would need to resize the window each time you switch tasks.

## Related Features

- **Desktop Mode**: Window geometry persistence is part of TFM's desktop mode functionality
- **Configuration System**: Default window size can be configured in `src/_config.py`
- **State Management**: Window geometry is separate from TFM's file manager state (cursor positions, etc.)

## See Also

- [Desktop Mode Guide](DESKTOP_MODE_GUIDE.md) - Complete guide to using TFM in desktop mode
- [TFM User Guide](TFM_USER_GUIDE.md) - General TFM usage instructions
- Developer documentation: `doc/dev/WINDOW_GEOMETRY_PERSISTENCE_IMPLEMENTATION.md`
