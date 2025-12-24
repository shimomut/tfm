# Menu Bar Feature

## Overview

TFM's Desktop mode includes a native menu bar that provides familiar desktop application functionality. The menu bar appears at the top of the application window (macOS) or at the top of the window itself (Windows, when supported), giving you quick access to common file operations, editing commands, view options, and navigation tools.

The menu bar integrates seamlessly with your operating system, providing a native look and feel with full keyboard shortcut support.

## Platform Support

- **macOS**: Fully supported with native menu bar integration
- **Windows**: Planned for future release
- **Terminal Mode**: Menu bar is not available in terminal mode (use key bindings instead)

## Accessing the Menu Bar

### Launching Desktop Mode

To use TFM with the menu bar:

```bash
# Launch TFM in desktop mode (auto-detects best backend)
python tfm.py --desktop

# Or explicitly specify the CoreGraphics backend (macOS)
python tfm.py --backend coregraphics
```

When TFM launches in desktop mode, the menu bar automatically appears at the top of the window.

### Using the Menu Bar

You can interact with the menu bar in two ways:

1. **Click menus**: Click on a menu name (File, Edit, View, Go) to open the dropdown
2. **Keyboard shortcuts**: Press keyboard shortcuts to execute actions directly

## Available Menus

### File Menu

The File menu provides operations for creating, managing, and working with files and folders.

#### Menu Items

- **New File** (Cmd+N / Ctrl+N)
  - Creates a new empty file in the current directory
  - Opens a dialog to enter the filename
  - Available at all times

- **New Folder** (Cmd+Shift+N / Ctrl+Shift+N)
  - Creates a new folder in the current directory
  - Opens a dialog to enter the folder name
  - Available at all times

- **Open** (Cmd+O / Ctrl+O)
  - Opens the selected file or navigates into the selected folder
  - Uses the default application for the file type
  - Available at all times

- **Delete** (Cmd+D / Ctrl+D)
  - Deletes the selected files or folders
  - Prompts for confirmation before deletion
  - **Requires**: One or more files selected
  - Disabled when no files are selected

- **Rename** (Cmd+R / Ctrl+R)
  - Renames the selected file or folder
  - Opens a dialog to enter the new name
  - **Requires**: Exactly one file selected
  - Disabled when no files are selected

- **Quit** (Cmd+Q / Ctrl+Q)
  - Exits TFM
  - Saves application state before quitting
  - Available at all times

### Edit Menu

The Edit menu provides clipboard operations and selection management.

#### Menu Items

- **Copy** (Cmd+C / Ctrl+C)
  - Copies selected files to the clipboard
  - Files can be pasted in the same or different directory
  - **Requires**: One or more files selected
  - Disabled when no files are selected

- **Cut** (Cmd+X / Ctrl+X)
  - Cuts selected files to the clipboard
  - Files will be moved when pasted
  - **Requires**: One or more files selected
  - Disabled when no files are selected

- **Paste** (Cmd+V / Ctrl+V)
  - Pastes files from the clipboard to the current directory
  - Performs copy or move depending on whether files were copied or cut
  - **Requires**: Files in clipboard
  - Disabled when clipboard is empty

- **Select All** (Cmd+A / Ctrl+A)
  - Selects all files in the current directory
  - Useful for bulk operations
  - Available at all times

### View Menu

The View menu controls how files are displayed and sorted.

#### Menu Items

- **Show Hidden Files** (Cmd+H / Ctrl+H)
  - Toggles visibility of hidden files (files starting with `.`)
  - Checkmark indicates current state
  - Available at all times

- **Sort By Name**
  - Sorts files alphabetically by name
  - Default sort order
  - Available at all times

- **Sort By Size**
  - Sorts files by size (largest first)
  - Useful for finding large files
  - Available at all times

- **Sort By Date**
  - Sorts files by modification date (newest first)
  - Useful for finding recently modified files
  - Available at all times

- **Sort By Extension**
  - Sorts files by file extension
  - Groups files of the same type together
  - Available at all times

- **Refresh** (Cmd+R / Ctrl+R)
  - Refreshes the current directory view
  - Reloads file list from disk
  - Available at all times

### Go Menu

The Go menu provides navigation shortcuts to common locations.

#### Menu Items

- **Parent Directory** (Cmd+Up / Ctrl+Up)
  - Navigates to the parent directory
  - **Requires**: Not at root directory
  - Disabled when at the root of the filesystem

- **Home** (Cmd+Shift+H / Ctrl+Shift+H)
  - Navigates to your home directory
  - Quick way to return home from anywhere
  - Available at all times

- **Favorites** (Cmd+F / Ctrl+F)
  - Opens the favorites dialog
  - Shows your saved favorite directories
  - Available at all times

- **Recent Locations** (Cmd+Shift+R / Ctrl+Shift+R)
  - Opens the recent locations dialog
  - Shows directories you've recently visited
  - Available at all times

## Menu Item States

Menu items can be in one of two states:

### Enabled (Normal)

- Menu item text appears in normal color
- Item can be selected with mouse or keyboard
- Action will execute when selected

### Disabled (Grayed Out)

- Menu item text appears grayed out
- Item cannot be selected
- Indicates the action is not currently available

### When Items Are Disabled

Menu items are automatically disabled when their requirements are not met:

| Menu Item | Disabled When |
|-----------|---------------|
| Delete, Rename | No files are selected |
| Copy, Cut | No files are selected |
| Paste | Clipboard is empty |
| Parent Directory | Already at root directory |

The menu bar automatically updates item states as you work, so you always see which actions are available.

## Keyboard Shortcuts

Every menu item with a keyboard shortcut displays the shortcut to the right of the item name. This helps you learn shortcuts as you use the application.

### Shortcut Format

- **macOS**: Uses Command (⌘) symbol
  - Example: ⌘N for New File
  - Example: ⌘⇧N for New Folder (Shift modifier)

- **Windows**: Uses Ctrl notation (when supported)
  - Example: Ctrl+N for New File
  - Example: Ctrl+Shift+N for New Folder

### Using Shortcuts

Press the keyboard shortcut to execute the action immediately without opening the menu:

1. Press the key combination (e.g., Cmd+C)
2. The action executes instantly
3. No menu opens or closes

This is the fastest way to perform common operations.

### Complete Shortcut Reference

The following tables provide a complete reference of all keyboard shortcuts available in TFM's Desktop mode. Shortcuts automatically adapt to your platform (Command key on macOS, Ctrl key on Windows).

#### File Menu Shortcuts

| Shortcut | Action | Description | Requirements |
|----------|--------|-------------|--------------|
| Cmd+N / Ctrl+N | New File | Create a new file in the current directory | None |
| Cmd+Shift+N / Ctrl+Shift+N | New Folder | Create a new folder in the current directory | None |
| Cmd+O / Ctrl+O | Open | Open the selected file or folder | None |
| Cmd+D / Ctrl+D | Delete | Delete selected files | Files selected |
| Cmd+R / Ctrl+R | Rename | Rename selected file | Single file selected |
| Cmd+Q / Ctrl+Q | Quit | Exit TFM | None |

#### Edit Menu Shortcuts

| Shortcut | Action | Description | Requirements |
|----------|--------|-------------|--------------|
| Cmd+C / Ctrl+C | Copy | Copy selected files to clipboard | Files selected |
| Cmd+X / Ctrl+X | Cut | Cut selected files to clipboard | Files selected |
| Cmd+V / Ctrl+V | Paste | Paste files from clipboard | Clipboard has content |
| Cmd+A / Ctrl+A | Select All | Select all files in current directory | None |

#### View Menu Shortcuts

| Shortcut | Action | Description | Requirements |
|----------|--------|-------------|--------------|
| Cmd+H / Ctrl+H | Show Hidden Files | Toggle visibility of hidden files | None |
| Cmd+R / Ctrl+R | Refresh | Refresh the current directory view | None |

#### Go Menu Shortcuts

| Shortcut | Action | Description | Requirements |
|----------|--------|-------------|--------------|
| Cmd+Up / Ctrl+Up | Parent Directory | Navigate to parent directory | Not at root |
| Cmd+Shift+H / Ctrl+Shift+H | Home | Navigate to home directory | None |
| Cmd+F / Ctrl+F | Favorites | Open favorites dialog | None |
| Cmd+Shift+R / Ctrl+Shift+R | Recent Locations | Open recent locations dialog | None |

### How Keyboard Shortcuts Work

#### Immediate Execution

When you press a keyboard shortcut:

1. The shortcut is recognized by the operating system's native menu system
2. A menu event is generated and sent to TFM
3. TFM executes the corresponding action immediately
4. No menu needs to be opened or displayed

This provides the fastest possible response time for common operations.

#### Context-Aware Shortcuts

Some shortcuts are only active when certain conditions are met:

- **Selection-dependent shortcuts** (Copy, Cut, Delete, Rename) only work when files are selected
- **Clipboard-dependent shortcuts** (Paste) only work when the clipboard has content
- **Navigation shortcuts** (Parent Directory) may be disabled in certain contexts (e.g., at root)

When a shortcut is disabled, pressing it has no effect. The menu bar visually indicates which items are currently enabled or disabled.

#### Learning Shortcuts

1. **Check the menus**: Open menus to see which shortcuts are available
2. **Start with common operations**: Learn shortcuts for frequently used actions first
3. **Practice regularly**: Use shortcuts instead of clicking menu items to build muscle memory
4. **Watch the display**: Shortcuts are shown next to menu items to help you learn

#### Shortcut Conflicts

If a keyboard shortcut conflicts with another application or system shortcut:

1. The menu shortcut takes priority when TFM is the active application
2. System-level shortcuts (like Cmd+Tab on macOS) always take precedence
3. You can still access the menu item by clicking it in the menu bar

### Technical Details

#### Shortcut Format

Shortcuts are specified in a platform-independent format:

- Format: `Modifier+Key` (e.g., `Cmd+N`, `Ctrl+C`)
- Multiple modifiers: `Modifier1+Modifier2+Key` (e.g., `Cmd+Shift+N`)
- Supported modifiers: `Cmd`, `Ctrl`, `Shift`, `Alt`/`Option`

The MenuManager automatically converts these to the appropriate platform-specific format.

#### Implementation

Keyboard shortcuts are implemented at the native operating system level:

- **macOS**: Uses NSMenuItem key equivalents and modifier masks
- **Windows**: Will use Win32 menu accelerators (when implemented)

This ensures shortcuts work reliably and feel native to the platform.

## Usage Examples

### Example 1: Creating a New File

**Using the menu:**
1. Click "File" in the menu bar
2. Click "New File"
3. Enter the filename in the dialog
4. Press Enter to create the file

**Using the keyboard shortcut:**
1. Press Cmd+N (macOS) or Ctrl+N (Windows)
2. Enter the filename in the dialog
3. Press Enter to create the file

### Example 2: Copying Files

**Using the menu:**
1. Select one or more files in the file list
2. Click "Edit" in the menu bar
3. Click "Copy"
4. Navigate to the destination directory
5. Click "Edit" → "Paste"

**Using keyboard shortcuts:**
1. Select one or more files in the file list
2. Press Cmd+C (macOS) or Ctrl+C (Windows)
3. Navigate to the destination directory
4. Press Cmd+V (macOS) or Ctrl+V (Windows)

### Example 3: Sorting Files

**Using the menu:**
1. Click "View" in the menu bar
2. Hover over or click "Sort By"
3. Click your preferred sort option (Name, Size, Date, Extension)

The file list immediately updates to show files in the new sort order.

### Example 4: Navigating to Home

**Using the menu:**
1. Click "Go" in the menu bar
2. Click "Home"

**Using the keyboard shortcut:**
1. Press Cmd+Shift+H (macOS) or Ctrl+Shift+H (Windows)

You're instantly taken to your home directory.

## Tips and Best Practices

### Learning the Menu System

1. **Explore the menus**: Click through each menu to see what's available
2. **Notice the shortcuts**: Pay attention to keyboard shortcuts displayed in menus
3. **Start with common operations**: Learn shortcuts for actions you use frequently
4. **Watch for disabled items**: Grayed-out items show you what conditions are needed

### Efficient Workflows

1. **Use keyboard shortcuts**: Much faster than clicking through menus
2. **Combine operations**: Select All (Cmd+A) → Copy (Cmd+C) → Navigate → Paste (Cmd+V)
3. **Toggle hidden files**: Use Cmd+H to quickly show/hide system files
4. **Quick navigation**: Use Go menu shortcuts to jump to common locations

### Understanding Menu States

- **Check before clicking**: Grayed-out items won't work
- **Select files first**: Many operations require a selection
- **Watch the Edit menu**: Shows whether clipboard has content
- **Check Go menu**: Shows whether you can go up a directory

## Troubleshooting

### Menu Bar Not Visible

**Problem**: TFM launches but no menu bar appears

**Solutions**:
1. Verify you're running in desktop mode: `python tfm.py --desktop`
2. Check that you're on macOS (Windows support coming soon)
3. Ensure the CoreGraphics backend is available
4. Check the terminal for error messages

### Menu Items Grayed Out

**Problem**: Menu items are disabled when you expect them to work

**Solutions**:
1. **For Copy/Cut/Delete/Rename**: Select one or more files first
2. **For Paste**: Copy or cut files first to populate the clipboard
3. **For Parent Directory**: Check if you're already at the root directory
4. Try refreshing the view with Cmd+R

### Keyboard Shortcuts Not Working

**Problem**: Pressing keyboard shortcuts doesn't execute actions

**Solutions**:
1. Verify you're using the correct modifier key (Cmd on macOS, Ctrl on Windows)
2. Check that the menu item is enabled (not grayed out)
3. Ensure TFM window has focus (click in the window first)
4. Check for conflicts with system-level shortcuts
5. Try using the menu item directly to verify it works

### Menu Doesn't Open

**Problem**: Clicking a menu name doesn't open the dropdown

**Solutions**:
1. Try clicking again - may be a timing issue
2. Check that the window has focus
3. Try using a keyboard shortcut instead
4. Restart TFM if the problem persists

## Differences from Terminal Mode

TFM's terminal mode uses key bindings instead of a menu bar:

| Feature | Desktop Mode | Terminal Mode |
|---------|--------------|---------------|
| Menu Bar | Native menu bar | Not available |
| Shortcuts | Cmd/Ctrl based | Single key bindings |
| Visual Feedback | Menu items show state | Status bar shows state |
| Discovery | Browse menus | Press ? for help |

Both modes provide the same functionality, just with different interfaces optimized for their environment.

## Related Features

- **Desktop Mode**: Native desktop application mode for macOS
- **Keyboard Shortcuts**: Fast access to menu actions
- **File Operations**: Core file management functionality
- **Navigation**: Directory navigation and favorites

## See Also

- [Desktop Mode Guide](DESKTOP_MODE_GUIDE.md) - Overview of desktop mode features
- [Menu Bar Demo](dev/MENU_BAR_DEMO.md) - Interactive demonstration of menu bar features
- [Key Bindings Selection Feature](KEY_BINDINGS_SELECTION_FEATURE.md) - Terminal mode key bindings

## Future Enhancements

Planned improvements for the menu bar feature:

- **Windows Support**: Native menu bar for Windows desktop mode
- **Customizable Menus**: User-defined menu items and shortcuts
- **Context Menus**: Right-click menus for files and folders
- **Recent Files**: Dynamic list of recently opened files
- **Checkmark Items**: Visual indicators for toggle states (like Show Hidden Files)
- **Menu Icons**: Icons next to menu items for visual recognition
- **Submenu Support**: Nested submenus for complex operations

## Feedback

If you encounter issues with the menu bar or have suggestions for improvements, please report them through the project's issue tracker.
