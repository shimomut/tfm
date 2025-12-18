# Menu Bar Demo Guide

## Overview

The menu bar demo (`demo/demo_menu_bar.py`) provides a comprehensive demonstration of TFM's menu bar functionality in desktop mode. This interactive demo showcases all aspects of the menu bar feature including menu structure, selection handling, state updates, and keyboard shortcuts.

## Requirements

- macOS operating system
- PyObjC framework installed (`pip install pyobjc-framework-Cocoa`)
- TFM with CoreGraphics backend support

## Running the Demo

```bash
python demo/demo_menu_bar.py
```

The demo will launch a native macOS window with an interactive demonstration of the menu bar features.

## Demo Sections

### 1. Menu Structure

The first section demonstrates the complete menu structure:

- **File Menu**: New File, New Folder, Open, Delete, Rename, Quit
- **Edit Menu**: Copy, Cut, Paste, Select All
- **View Menu**: Show Hidden Files, Sort By options, Refresh
- **Go Menu**: Parent Directory, Home, Favorites, Recent Locations

**What to test:**
- Click on each menu in the menu bar
- Verify all menu items are present
- Check that keyboard shortcuts are displayed next to menu items

### 2. Menu Selection and Action Execution

This section demonstrates how menu selections trigger actions:

**What to test:**
- Click "File" → "New File" to see the action executed
- Click "Edit" → "Select All" to see the action executed
- Click "View" → "Show Hidden Files" to see the action executed
- Click "Go" → "Home" to see the action executed

**Expected behavior:**
- Each menu selection should display an action message
- The menu should close after selection
- The action description should appear on screen

### 3. Menu State Updates

This section demonstrates dynamic menu state updates based on application state:

**Test scenarios:**

1. **No files selected:**
   - Copy, Cut, Delete, Rename should be DISABLED
   - Paste should be DISABLED (clipboard empty)
   - Select All should be ENABLED

2. **Files selected:**
   - Copy, Cut, Delete, Rename should be ENABLED
   - Paste should still be DISABLED (clipboard empty)
   - Select All should be ENABLED

3. **Files copied:**
   - Copy, Cut should be ENABLED
   - Paste should be ENABLED (clipboard has files)
   - Select All should be ENABLED

4. **At root directory:**
   - Parent Directory should be DISABLED
   - Home, Favorites, Recent Locations should be ENABLED

**What to test:**
- Open the Edit menu and verify menu item states
- Follow the prompts to simulate selecting files
- Verify menu items become enabled/disabled appropriately
- Check the Go menu when at root directory

### 4. Keyboard Shortcuts

This section demonstrates keyboard shortcut functionality:

**Available shortcuts:**
- `Cmd+N` - New File
- `Cmd+Shift+N` - New Folder
- `Cmd+C` - Copy
- `Cmd+V` - Paste
- `Cmd+A` - Select All
- `Cmd+H` - Toggle Hidden Files
- `Cmd+Q` - Quit

**What to test:**
- Press each keyboard shortcut
- Verify the action is executed without opening the menu
- Check that the shortcut and action are displayed on screen
- Press `Cmd+Q` to quit the demo

## Expected Results

After completing the demo, you should have verified:

✓ Menu bar appears at the top of the window
✓ All four menus (File, Edit, View, Go) are present
✓ Menu items are properly organized with separators
✓ Keyboard shortcuts are displayed next to menu items
✓ Menu selections execute corresponding actions
✓ Menu items are enabled/disabled based on application state
✓ Keyboard shortcuts work without opening menus
✓ Menu state updates reflect application state changes

## Troubleshooting

### Demo won't start

**Problem:** Demo fails to launch or shows import errors

**Solutions:**
1. Verify PyObjC is installed: `pip install pyobjc-framework-Cocoa`
2. Check that you're running on macOS
3. Ensure the virtual environment is activated: `source .venv/bin/activate`
4. Verify TFM source files are present in the `src/` directory

### Menu bar not visible

**Problem:** Window opens but menu bar is not visible

**Solutions:**
1. Check that you're running on macOS (menu bar only works on macOS)
2. Verify the CoreGraphics backend is being used
3. Check console output for error messages
4. Try restarting the demo

### Keyboard shortcuts not working

**Problem:** Pressing keyboard shortcuts doesn't trigger actions

**Solutions:**
1. Verify you're using the Command (⌘) key, not Control
2. Check that the window has focus
3. Try clicking in the window first to ensure it's active
4. Check console output for error messages

### Menu items not updating

**Problem:** Menu items don't enable/disable as expected

**Solutions:**
1. Follow the demo prompts carefully
2. Wait for each state update to complete
3. Check that you're opening the correct menu
4. Verify the state change message appears on screen

## Integration with TFM

This demo uses the same menu system that TFM uses in desktop mode. The menu structure, state management, and event handling are identical to the production implementation.

To use the menu bar in TFM:

```bash
# Launch TFM in desktop mode
python tfm.py --desktop

# Or explicitly specify the CoreGraphics backend
python tfm.py --backend coregraphics
```

## Related Documentation

- [Menu Bar Keyboard Shortcuts Feature](MENU_BAR_KEYBOARD_SHORTCUTS_FEATURE.md) - End-user documentation
- [Keyboard Shortcuts Implementation](dev/KEYBOARD_SHORTCUTS_IMPLEMENTATION.md) - Developer documentation
- [Desktop Mode Guide](DESKTOP_MODE_GUIDE.md) - General desktop mode documentation

## Demo Source Code

The demo source code is located at `demo/demo_menu_bar.py` and demonstrates:

1. **Menu Structure Creation**: How to create and configure menu structure
2. **Menu State Management**: How to update menu item states dynamically
3. **Event Handling**: How to handle MenuEvent objects
4. **Keyboard Shortcuts**: How keyboard shortcuts are processed
5. **Mock File Manager**: How to create a mock file manager for testing

The demo can serve as a reference for understanding how the menu bar system works and how to integrate it into applications.
