# Double-Click Support

TFM supports double-click mouse events for quick navigation and file operations.

## Overview

Double-clicking provides a faster way to interact with files and directories, offering the same functionality as pressing the Enter key but with a more intuitive mouse-based interface.

## Supported Actions

### File Lists (Main View)

**Double-click on the header (directory path):**
- Navigates to the parent directory
- Same as pressing Backspace
- Switches pane focus if clicking inactive pane header

**Double-click on a directory:**
- Navigates into the directory
- Same as pressing Enter on a directory

**Double-click on a file:**
- Opens the file using the configured file association
- If no association exists, opens text files in the built-in text viewer
- Same as pressing Enter on a file

**Double-click on an archive:**
- Enters the archive as a virtual directory
- Same as pressing Enter on an archive file

### Directory Diff Viewer

**Double-click on a directory:**
- Expands the directory if collapsed
- Collapses the directory if expanded
- Same as pressing Enter on a directory

**Double-click on a file:**
- Opens the file diff viewer to compare the file contents
- Same as pressing Enter on a file

## Behavior Details

### Pane Focus

When double-clicking in an inactive pane:
1. Focus switches to the clicked pane
2. Cursor moves to the clicked item
3. The action (open/navigate) is performed

This allows quick navigation between panes without needing to manually switch focus first.

### Click Position

Double-clicks are position-aware:
- Clicking on a specific item moves the cursor to that item before performing the action
- Clicking outside the file/tree area is ignored
- Clicking in the header, status bar, or log area has no effect

### Timing

The double-click detection is handled by the terminal backend:
- Two clicks within the system's double-click threshold are recognized as a double-click
- The timing threshold is determined by your operating system settings
- On macOS, this is typically 0.5 seconds

## Terminal Requirements

Double-click support requires:
- A terminal that supports mouse events (most modern terminals do)
- Mouse event reporting enabled in TFM (enabled by default)

Supported terminals include:
- iTerm2 (macOS)
- Terminal.app (macOS)
- GNOME Terminal (Linux)
- Konsole (Linux)
- Windows Terminal (Windows)
- And most other modern terminal emulators

## Keyboard Equivalents

All double-click actions have keyboard equivalents:
- Double-click header = Backspace key (go to parent directory)
- Double-click file/directory = Enter key (open/navigate)
- Single click = Arrow keys to move cursor, then Enter

This ensures TFM remains fully functional without a mouse.

## Related Features

- **Mouse Wheel Scrolling**: Scroll through file lists and viewers
- **Click-to-Focus**: Single click to move cursor and switch pane focus
- **File Associations**: Configure which programs open which file types
- **Text Viewer**: Built-in viewer for text files
- **Directory Diff Viewer**: Compare directory contents

## See Also

- `MOUSE_SUPPORT_FEATURE.md` - Overview of all mouse features
- `FILE_ASSOCIATIONS_FEATURE.md` - Configure file opening behavior
- `DIRECTORY_DIFF_FEATURE.md` - Directory comparison tool
