# Mouse Event Support Feature

## Overview

TFM supports mouse interaction in both Desktop mode (CoreGraphics backend on macOS) and Terminal mode (curses backend in supported terminals). You can use your mouse to switch between file panes by clicking on them, making navigation faster and more intuitive.

## Availability

### Desktop Mode (Full Support)

- **Platform**: macOS with CoreGraphics backend
- **Supported Events**: All mouse events including clicks, double-clicks, movement, and scroll wheel
- **Launch Command**: `python tfm.py --desktop` or `python tfm.py --backend coregraphics`

### Terminal Mode (Limited Support)

- **Platform**: Terminal emulators that support mouse events
- **Supported Events**: Mouse button clicks only (no movement or scroll wheel)
- **Launch Command**: `python tfm.py` (default terminal mode)
- **Compatibility**: Works in most modern terminal emulators (iTerm2, Terminal.app, xterm, etc.)

### Graceful Degradation

If your terminal doesn't support mouse events, TFM automatically falls back to keyboard-only operation without errors. You can always use the Tab key to switch between panes.

## Features

### Pane Focus Switching

The primary mouse feature is the ability to switch focus between the left and right file panes by clicking on them.

#### How It Works

1. **Click on left pane** → Focus switches to left pane
2. **Click on right pane** → Focus switches to right pane
3. **Visual feedback** → Active pane is highlighted, inactive pane is dimmed

#### Visual Indicators

When you click on a pane:
- **Active pane**: Brighter colors, cursor visible
- **Inactive pane**: Dimmed colors, no cursor
- **Immediate response**: Focus changes instantly on click

### Pane Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Left Pane                  │ Right Pane                      │
│ (Click here to focus)      │ (Click here to focus)           │
│                            │                                 │
│ file1.txt                  │ document.pdf                    │
│ file2.txt                  │ image.png                       │
│ directory/                 │ folder/                         │
│                            │                                 │
├─────────────────────────────────────────────────────────────┤
│ Log Pane                                                     │
└─────────────────────────────────────────────────────────────┘
```

Click anywhere within a pane's boundaries to switch focus to that pane.

## Usage Examples

### Example 1: Switching Focus with Mouse

**Scenario**: You're working in the left pane and want to switch to the right pane

**Using the mouse**:
1. Click anywhere in the right pane
2. Focus immediately switches to the right pane
3. The right pane becomes highlighted

**Using the keyboard** (alternative):
1. Press Tab
2. Focus switches to the right pane

### Example 2: Quick Navigation Between Panes

**Scenario**: You're copying files and need to switch between source and destination panes frequently

**Using the mouse**:
1. Click on left pane to select source files
2. Press Space to select files
3. Click on right pane to switch to destination
4. Press 'c' to copy files

This is faster than repeatedly pressing Tab to switch panes.

### Example 3: Working with Dialogs

**Scenario**: A dialog is open (search, help, etc.)

**Behavior**:
- Mouse clicks are handled by the dialog (topmost layer)
- Clicking outside the dialog doesn't switch pane focus
- Close the dialog first (Escape key) to interact with panes

## Keyboard Alternatives

All mouse functionality has keyboard equivalents:

| Mouse Action | Keyboard Alternative |
|--------------|---------------------|
| Click left pane | Tab (until left pane is active) |
| Click right pane | Tab (until right pane is active) |

The Tab key cycles between panes, so you can always use it if mouse support is unavailable or if you prefer keyboard navigation.

## Backend Capabilities

### CoreGraphics Backend (Desktop Mode)

**Full mouse support** with all event types:

| Event Type | Supported | Description |
|------------|-----------|-------------|
| Button Down | ✓ | Mouse button press |
| Button Up | ✓ | Mouse button release |
| Double Click | ✓ | Rapid double press |
| Move | ✓ | Cursor movement |
| Wheel | ✓ | Scroll wheel events |
| Drag | ✓ | Movement with button held (future use) |

**Coordinate precision**:
- Text grid coordinates (column and row)
- Sub-cell positioning (fractional position within character cell)
- Accurate to pixel level

### Curses Backend (Terminal Mode)

**Limited mouse support** with basic events only:

| Event Type | Supported | Description |
|------------|-----------|-------------|
| Button Down | ✓ | Mouse button press |
| Button Up | ✓ | Mouse button release |
| Double Click | ✗ | Not supported |
| Move | ✗ | Not supported |
| Wheel | ✗ | Not supported |
| Drag | ✗ | Not supported |

**Coordinate precision**:
- Text grid coordinates only (column and row)
- No sub-cell positioning
- Character-level accuracy

**Terminal compatibility**:
- Works in most modern terminal emulators
- Automatically disabled if terminal doesn't support mouse events
- No error messages if unsupported

## Technical Details

### Event Routing

Mouse events follow the same routing pattern as keyboard events:

1. **Event captured** by backend (CoreGraphics or curses)
2. **Coordinates transformed** to text grid coordinates
3. **Event delivered** to topmost UI layer only
4. **No propagation** to lower layers in the stack

This means:
- Dialogs receive mouse events when open
- File panes receive mouse events when no dialog is open
- Only one component handles each mouse event

### Coordinate System

Mouse events use a text grid coordinate system:

- **Column**: Horizontal position (0-based, 0 = leftmost column)
- **Row**: Vertical position (0-based, 0 = topmost row)
- **Sub-cell position** (Desktop mode only): Fractional position within a character cell
  - sub_cell_x: 0.0 (left edge) to 1.0 (right edge)
  - sub_cell_y: 0.0 (top edge) to 1.0 (bottom edge)

Example: Clicking at column 10, row 5 with sub-cell position (0.4, 0.8) means:
- Character cell at column 10, row 5
- 40% from the left edge of the cell
- 80% from the top edge of the cell

### Event Timestamps

All mouse events include timestamps for:
- Event ordering (ensuring events are processed in sequence)
- Timing analysis (detecting double-clicks, drags, etc.)
- Future gesture recognition

## Limitations

### Current Limitations

1. **Pane focus switching only**: The initial implementation only supports switching focus between panes
2. **No drag-and-drop**: Dragging files between panes is not yet supported
3. **No context menus**: Right-click context menus are not yet implemented
4. **No file selection**: Clicking on individual files doesn't select them (use keyboard)
5. **No scrolling**: Mouse wheel scrolling is not yet implemented

### Terminal Mode Limitations

1. **Basic events only**: Only button clicks are supported
2. **No sub-cell positioning**: Coordinates are character-level only
3. **Terminal dependent**: Support varies by terminal emulator
4. **No visual feedback**: No mouse cursor changes or hover effects

### Dialog Behavior

When a dialog is open:
- Mouse events go to the dialog, not the file panes
- Clicking outside the dialog doesn't close it or switch pane focus
- Use Escape key to close dialogs

## Troubleshooting

### Mouse Not Working in Desktop Mode

**Problem**: Clicking on panes doesn't switch focus in Desktop mode

**Solutions**:
1. Verify you're running in Desktop mode: `python tfm.py --desktop`
2. Check that the window has focus (click on the window first)
3. Ensure you're clicking within the pane boundaries (not on the border)
4. Check the log pane for error messages
5. Try using Tab key to verify pane switching works

### Mouse Not Working in Terminal Mode

**Problem**: Clicking on panes doesn't switch focus in Terminal mode

**Solutions**:
1. Check if your terminal supports mouse events:
   - iTerm2: Yes (enable in Preferences → Profiles → Terminal → "Report mouse clicks")
   - Terminal.app: Yes (usually enabled by default)
   - xterm: Yes (with `-xrm 'XTerm*VT100.allowMouseOps: true'`)
   - tmux: Requires `set -g mouse on` in `.tmux.conf`
2. Verify mouse reporting is enabled in your terminal settings
3. Try a different terminal emulator
4. Use Tab key as alternative (always works)

### Clicks Not Registering

**Problem**: You click but nothing happens

**Solutions**:
1. **Click within pane boundaries**: Don't click on the border between panes
2. **Close dialogs first**: If a dialog is open, close it with Escape
3. **Check window focus**: Click on the window to ensure it has focus
4. **Try different locations**: Click in the center of the pane, not near edges

### Wrong Pane Gets Focus

**Problem**: Clicking on one pane switches focus to the other pane

**Solutions**:
1. Check pane boundary position (adjust with [ and ] keys if needed)
2. Click further from the center divider
3. Verify window size hasn't changed unexpectedly
4. Restart TFM if the problem persists

### Mouse Works But Keyboard Doesn't

**Problem**: Mouse clicks work but keyboard shortcuts don't

**Solutions**:
1. Ensure the window has keyboard focus (click on it)
2. Check that you're not in a text input mode
3. Verify no dialog is open (press Escape to close)
4. Check for key binding conflicts in your configuration

## Future Enhancements

Planned improvements for mouse support:

### Drag-and-Drop Operations

- **Drag files between panes**: Click and drag files from one pane to another to copy/move
- **Visual feedback**: Show drag cursor and drop target highlighting
- **Modifier keys**: Hold Shift to move, Cmd/Ctrl to copy

### File Selection

- **Click to select**: Click on a file to select it
- **Shift-click for range**: Select a range of files
- **Cmd/Ctrl-click for multi-select**: Add/remove files from selection

### Context Menus

- **Right-click menus**: Context-sensitive menus for files and folders
- **Common operations**: Copy, move, delete, rename, properties
- **Quick access**: Faster than navigating through main menu

### Scroll Wheel Support

- **Scroll file lists**: Use mouse wheel to scroll through long file lists
- **Smooth scrolling**: Pixel-perfect scrolling in Desktop mode
- **Horizontal scrolling**: Shift+wheel for horizontal scrolling

### Enhanced Visual Feedback

- **Hover effects**: Highlight files as you hover over them
- **Cursor changes**: Different cursors for different actions (arrow, hand, etc.)
- **Tooltips**: Show file information on hover

### Double-Click Actions

- **Open files**: Double-click to open files or navigate into folders
- **Configurable**: Set preferred action for double-click
- **Quick access**: Faster than pressing Enter

## Related Features

- **Dual-Pane Interface**: Two file panes for efficient file management
- **Keyboard Navigation**: Complete keyboard control for all operations
- **Desktop Mode**: Native desktop application mode with full mouse support
- **Terminal Mode**: Terminal-based interface with limited mouse support

## See Also

- [Dual-Pane Feature](DUAL_PANE_FEATURE.md) - Overview of dual-pane interface
- [Desktop Mode Guide](DESKTOP_MODE_GUIDE.md) - Complete desktop mode documentation
- [Keyboard Shortcuts](../README.md#keyboard-shortcuts) - All available keyboard shortcuts

## Feedback

If you encounter issues with mouse support or have suggestions for improvements, please report them through the project's issue tracker. Mouse support is a new feature and we're actively working on enhancements based on user feedback.
