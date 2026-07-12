# Jump Dialog Feature

## Overview

The Jump Dialog provides fast directory navigation by searching your filesystem for directories. It's ideal for quickly jumping to deeply nested directories without manually navigating through the directory tree.

## Key Binding

- **J** (Shift+j) - Open the jump dialog

## Features

### Fast Directory Search

The jump dialog scans your filesystem and presents a searchable list of directories:

- Searches from the current directory downward
- Shows directory paths relative to search root
- Incremental search as you type
- Keyboard navigation through results

### Intelligent Filtering

- Type to filter directories by name or path
- Case-insensitive search
- Matches anywhere in the path
- Updates results in real-time

### Performance Optimization

- Bounded directory scan (internal cap; keeps the dialog responsive)
- Background scanning with progress indicator
- Cancellable search operation
- Efficient directory traversal

## Usage

### Basic Usage

1. Press **Shift-J** to open the jump dialog
2. Wait for directory scanning to complete
3. Start typing to filter directories
4. Use arrow keys to select a directory
5. Press **Enter** to navigate to the selected directory
6. Press **Escape** or **q** to cancel

### Search Tips

**Search by directory name:**
```
Type: "projects"
Matches: ~/Documents/projects, ~/work/projects, etc.
```

**Search by path component:**
```
Type: "work/src"
Matches: ~/work/src, ~/backup/work/src, etc.
```

**Search for hidden directories:**
```
Type: ".config"
Matches: ~/.config, ~/backup/.config, etc.
```

### Keyboard Shortcuts

- **Up/Down Arrows** - Navigate through results
- **Page Up/Page Down** - Scroll by page
- **Home/End** - Jump to first/last result
- **Enter** - Navigate to selected directory
- **Escape** or **q** - Cancel and close dialog
- **Backspace** - Remove search characters
- **Any letter/number** - Add to search filter

## Configuration

### Maximum Directories

The number of directories scanned is bounded internally to keep the dialog
responsive; it is not a user-configurable setting.

**Considerations:**
- Higher values: More complete results, slower scanning
- Lower values: Faster scanning, may miss deep directories
- Adjust based on your filesystem size and performance needs

### Search Root

The jump dialog searches from the current directory:

- Navigate to a higher-level directory for broader search
- Navigate to a specific subdirectory for focused search
- Use root (/) for system-wide search (may be slow)

## Performance Tips

### For Large Filesystems

1. **Start from a specific directory:**
   - Navigate to ~/Documents before opening jump dialog
   - Avoids scanning entire home directory

2. **Start from a more specific directory:**
   - Fewer directories to scan means faster results

3. **Use favorites for common directories:**
   - Press **J** for favorites dialog
   - Faster than jump dialog for known locations

### For Network Filesystems

- Jump dialog may be slow on network mounts
- Consider using favorites or manual navigation
- Start from a closer parent directory to reduce the scan

## Comparison with Other Navigation Features

### Jump Dialog (J) vs Favorites (j)

**Jump Dialog:**
- Searches entire directory tree
- Finds any directory, even if not visited before
- Slower (requires filesystem scan)
- Best for: Finding unknown or rarely used directories

**Favorites:**
- Shows pre-configured favorite directories
- Instant access (no scanning)
- Faster (no filesystem scan)
- Best for: Frequently accessed directories

### Jump Dialog vs Manual Navigation

**Jump Dialog:**
- Fast access to deep directories
- No need to remember exact path
- Search by partial name
- Best for: Deep directory structures

**Manual Navigation:**
- Full control over navigation path
- See directory contents along the way
- Better for browsing
- Best for: Exploring directory structure

## Troubleshooting

### Slow Directory Scanning

**Problem:** Jump dialog takes a long time to scan directories

**Solutions:**
1. Use the search filter to narrow results
2. Start from a more specific directory
3. Use favorites for frequently accessed directories
4. Exclude large directories (not currently supported)

### Directory Not Found

**Problem:** Expected directory doesn't appear in results

**Solutions:**
1. The directory may be beyond the internal scan cap — start from a closer parent
2. Verify directory exists and is accessible
3. Check search filter isn't too restrictive
4. Try starting from a higher-level directory

### Permission Denied Errors

**Problem:** Some directories show permission errors

**Solution:** This is normal - jump dialog skips directories you don't have permission to access

### Search Not Working

**Problem:** Typing doesn't filter results

**Solutions:**
1. Ensure dialog is active (not in background)
2. Check keyboard input is working
3. Try clearing search with Escape and typing again

## Related Features

- **Favorite Directories** (j) - Quick access to pre-configured directories
- **Drives Dialog** (D) - Access storage locations and S3 buckets
- **History Navigation** (H) - Navigate to previously visited directories

## See Also

- [Favorite Directories Feature](FAVORITE_DIRECTORIES_FEATURE.md)
- [Drives Dialog Feature](DRIVES_DIALOG_FEATURE.md)
<!-- TODO: Create HISTORY_NAVIGATION_FEATURE.md -->
<!-- - History Navigation Feature -->
