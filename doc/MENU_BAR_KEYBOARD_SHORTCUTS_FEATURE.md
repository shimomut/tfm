# Menu Bar Keyboard Shortcuts Feature

## Overview

TFM's Desktop mode includes full keyboard shortcut support for menu operations. Keyboard shortcuts allow you to execute menu actions quickly without opening menus, providing a faster and more efficient workflow.

## Platform-Specific Shortcuts

Keyboard shortcuts automatically adapt to your operating system:

- **macOS**: Uses the Command (⌘) key as the primary modifier
- **Windows**: Uses the Ctrl key as the primary modifier (when Windows support is added)

This ensures shortcuts feel natural and follow platform conventions.

## Available Keyboard Shortcuts

### File Menu

| Shortcut | Action | Description |
|----------|--------|-------------|
| Cmd+N (macOS) / Ctrl+N (Windows) | New File | Create a new file in the current directory |
| Cmd+Shift+N (macOS) / Ctrl+Shift+N (Windows) | New Folder | Create a new folder in the current directory |
| Cmd+O (macOS) / Ctrl+O (Windows) | Open | Open the selected file or folder |
| Cmd+D (macOS) / Ctrl+D (Windows) | Delete | Delete selected files (requires selection) |
| Cmd+R (macOS) / Ctrl+R (Windows) | Rename | Rename selected file (requires single selection) |
| Cmd+Q (macOS) / Ctrl+Q (Windows) | Quit | Exit TFM |

### Edit Menu

| Shortcut | Action | Description |
|----------|--------|-------------|
| Cmd+C (macOS) / Ctrl+C (Windows) | Copy | Copy selected files to clipboard (requires selection) |
| Cmd+X (macOS) / Ctrl+X (Windows) | Cut | Cut selected files to clipboard (requires selection) |
| Cmd+V (macOS) / Ctrl+V (Windows) | Paste | Paste files from clipboard (requires clipboard content) |
| Cmd+A (macOS) / Ctrl+A (Windows) | Select All | Select all files in current directory |

### View Menu

| Shortcut | Action | Description |
|----------|--------|-------------|
| Cmd+H (macOS) / Ctrl+H (Windows) | Show Hidden Files | Toggle visibility of hidden files |
| Cmd+R (macOS) / Ctrl+R (Windows) | Refresh | Refresh the current directory view |

### Go Menu

| Shortcut | Action | Description |
|----------|--------|-------------|
| Cmd+Up (macOS) / Ctrl+Up (Windows) | Parent Directory | Navigate to parent directory (disabled at root) |
| Cmd+Shift+H (macOS) / Ctrl+Shift+H (Windows) | Home | Navigate to home directory |
| Cmd+F (macOS) / Ctrl+F (Windows) | Favorites | Open favorites dialog |
| Cmd+Shift+R (macOS) / Ctrl+Shift+R (Windows) | Recent Locations | Open recent locations dialog |

## How Keyboard Shortcuts Work

### Immediate Execution

When you press a keyboard shortcut:

1. The shortcut is recognized by the operating system's native menu system
2. A menu event is generated and sent to TFM
3. TFM executes the corresponding action immediately
4. No menu needs to be opened or displayed

This provides the fastest possible response time for common operations.

### Context-Aware Shortcuts

Some shortcuts are only active when certain conditions are met:

- **Selection-dependent shortcuts** (Copy, Cut, Delete, Rename) only work when files are selected
- **Clipboard-dependent shortcuts** (Paste) only work when the clipboard has content
- **Navigation shortcuts** (Parent Directory) may be disabled in certain contexts (e.g., at root)

When a shortcut is disabled, pressing it has no effect. The menu bar visually indicates which items are currently enabled or disabled.

### Shortcut Display

Keyboard shortcuts are displayed in the menu bar next to their corresponding menu items. This helps you learn and remember shortcuts as you use the application.

## Usage Tips

### Learning Shortcuts

1. **Check the menus**: Open menus to see which shortcuts are available
2. **Start with common operations**: Learn shortcuts for frequently used actions first
3. **Practice regularly**: Use shortcuts instead of clicking menu items to build muscle memory

### Efficient Workflow

Combine keyboard shortcuts with other TFM features for maximum efficiency:

- Use **Cmd+A** to select all files, then **Cmd+C** to copy them
- Use **Cmd+H** to toggle hidden files when you need to see system files
- Use **Cmd+Up** to quickly navigate up the directory tree
- Use **Cmd+Shift+H** to return to your home directory from anywhere

### Shortcut Conflicts

If a keyboard shortcut conflicts with another application or system shortcut:

1. The menu shortcut takes priority when TFM is the active application
2. System-level shortcuts (like Cmd+Tab on macOS) always take precedence
3. You can still access the menu item by clicking it in the menu bar

## Platform Differences

### macOS

- Uses Command (⌘) key as primary modifier
- Shortcuts follow macOS Human Interface Guidelines
- Native menu bar integration provides system-standard behavior
- Shortcuts work even when menus are not visible

### Windows (Future)

- Will use Ctrl key as primary modifier
- Shortcuts will follow Windows design guidelines
- Native menu integration will provide Windows-standard behavior

## Troubleshooting

### Shortcut Not Working

If a keyboard shortcut doesn't work:

1. **Check if the menu item is enabled**: Open the menu to see if the item is grayed out
2. **Verify the shortcut**: Make sure you're pressing the correct key combination
3. **Check for conflicts**: Another application might be intercepting the shortcut
4. **Restart TFM**: In rare cases, restarting may resolve the issue

### Wrong Modifier Key

If shortcuts show the wrong modifier key (Cmd vs Ctrl):

1. This should not happen - shortcuts automatically adapt to your platform
2. If it does occur, please report it as a bug

## Technical Details

### Shortcut Format

Shortcuts are specified in a platform-independent format:

- Format: `Modifier+Key` (e.g., `Cmd+N`, `Ctrl+C`)
- Multiple modifiers: `Modifier1+Modifier2+Key` (e.g., `Cmd+Shift+N`)
- Supported modifiers: `Cmd`, `Ctrl`, `Shift`, `Alt`/`Option`

The MenuManager automatically converts these to the appropriate platform-specific format.

### Implementation

Keyboard shortcuts are implemented at the native operating system level:

- **macOS**: Uses NSMenuItem key equivalents and modifier masks
- **Windows**: Will use Win32 menu accelerators (when implemented)

This ensures shortcuts work reliably and feel native to the platform.

## See Also

- [Desktop Mode Guide](DESKTOP_MODE_GUIDE.md) - Overview of Desktop mode features
- [Menu Bar Feature](MENU_BAR_FEATURE.md) - Complete menu bar documentation
- [Key Bindings](KEY_BINDINGS_FEATURE.md) - Terminal mode key bindings

## Related Features

- **Menu Bar**: Native menu bar with File, Edit, View, and Go menus
- **Desktop Mode**: Native desktop application mode for macOS
- **Key Bindings**: Alternative keyboard shortcuts for terminal mode
