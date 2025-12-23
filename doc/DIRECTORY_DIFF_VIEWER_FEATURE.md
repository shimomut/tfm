# Directory Diff Viewer Feature

## Overview

The Directory Diff Viewer is a powerful feature that allows you to compare two directories recursively, displaying all differences in an interactive tree-structured view. This feature is particularly useful for:

- Comparing backup directories with current directories
- Verifying synchronization between directories
- Identifying changes after updates or migrations
- Reviewing differences before merging directory structures

## Opening the Directory Diff Viewer

To compare two directories:

1. Navigate to the directories you want to compare using the left and right panes
2. Press **Ctrl+D** to open the Directory Diff Viewer

The viewer uses **progressive scanning** to provide immediate feedback:

- **Instant Display**: Top-level items appear within 100ms
- **Background Scanning**: Subdirectories are scanned progressively in the background
- **Responsive UI**: You can navigate and explore while scanning continues
- **Smart Prioritization**: Visible items are scanned before hidden ones

## Understanding the Display

### Tree Structure

The Directory Diff Viewer presents results in a hierarchical tree structure:

- **Directories** are shown with expand/collapse indicators (`[+]` when collapsed, `[-]` when expanded)
- **Files** are shown without indicators
- **Indentation** indicates nesting level

### Side-by-Side Layout

The display is split into two columns:

- **Left column**: Shows items from the left directory
- **Right column**: Shows items from the right directory
- **Matching items** appear in the same row
- **Missing items** show as blank spaces with gray background

### Color Coding

Different types of differences are highlighted with distinct background colors:

- **Only in Left** (orange/yellow): Item exists only in the left directory
- **Only in Right** (orange/yellow): Item exists only in the right directory
- **Content Different** (red): File exists in both locations but content differs
- **Contains Difference** (blue): Directory contains descendant differences
- **Identical** (default): Item is the same in both locations
- **Pending** (neutral): Item has not been scanned or compared yet

### Pending Status Indicators

During progressive scanning, you may see pending status indicators:

- **`...`** after directory names: Directory contents not yet scanned
- **`[scanning...]`**: Directory is currently being scanned
- **`[pending]`** for files: File content not yet compared

These indicators disappear as scanning progresses. You can expand directories marked with `...` to trigger immediate scanning.

## Navigation and Controls

### Basic Navigation

- **Up/Down Arrow**: Move cursor through visible tree nodes
- **Page Up/Page Down**: Scroll one page at a time
- **Home**: Jump to first node
- **End**: Jump to last node

### Expanding and Collapsing

- **Right Arrow** or **Enter**: Expand a collapsed directory
  - If directory is not yet scanned, it will be scanned immediately (on-demand scanning)
  - Scanning happens in the main thread for instant feedback
- **Left Arrow**: Collapse an expanded directory

### Viewing File Differences

When the cursor is on a file marked as "Content Different":

- Press **Enter** or **D**: Open the file diff viewer to see line-by-line differences
- Press **Escape** or **Q**: Return to the directory diff viewer

### Filtering

- **I**: Toggle display of identical files (hide/show)
  - When hidden, only differences are shown
  - Status bar indicates filter state

### Closing the Viewer

- **Escape** or **Q**: Close the directory diff viewer and return to the file manager

## Progress Feedback

### Progressive Scanning

The Directory Diff Viewer uses progressive scanning for optimal performance:

1. **Immediate Display**: Top-level items appear instantly (< 100ms)
2. **Background Processing**: Subdirectories are scanned in worker threads
3. **Priority System**: Visible items are scanned before off-screen items
4. **On-Demand Scanning**: Expanding unscanned directories triggers immediate scanning

### During Scanning

While directories are being scanned in the background:

- A progress indicator shows scanning status with animation
- Status bar displays "Scanning... (N pending)" or "Comparing... (N pending)"
- Tree updates progressively as new items are discovered
- You can navigate and explore already-scanned portions
- Press **Escape** to cancel the scan and close the viewer

### After Scanning

Once scanning completes:

- Status bar shows "Scan complete"
- All pending indicators are resolved
- Statistics show total files, differences, and errors
- You can navigate and explore the complete results

## Status Bar Information

The status bar at the bottom displays:

- **Current position**: Line number and total lines
- **Statistics**: Number of files scanned, differences found
- **Scanning status**: "Scanning... (N pending)" or "Comparing... (N pending)" during background operations
- **Filter state**: Whether identical files are hidden
- **Error count**: Number of inaccessible files or directories (if any)
- **Completion status**: "Scan complete" when all scanning is finished

## Error Handling

### Permission Errors

If a directory or file cannot be accessed:

- An error indicator appears next to the item
- The viewer continues processing accessible portions
- Error count is shown in the status bar

### I/O Errors

If file comparison fails:

- The affected file is marked with an error indicator
- Comparison continues for other files
- You can still navigate and view accessible data

### Empty or Identical Directories

If both directories are empty or completely identical:

- An appropriate message is displayed
- Statistics are shown in the status bar
- You can close the viewer normally

## Examples

### Example 1: Progressive Scanning in Action

```
Opening viewer with large directories...

Initial display (< 100ms):
[+] documents/          documents/          (Contains Difference)
[+] images/             images/             ...
[+] videos/             videos/             ...

Status: Scanning... (15 pending)

After expanding documents/:
[-] documents/
    [+] projects/       projects/           (Contains Difference)
    report.txt          report.txt          (Content Different)
    [+] archive/        archive/            ...

Status: Scanning... (12 pending)
```

### Example 2: Comparing Backup Directories

```
Left: /home/user/documents
Right: /backup/documents

Result:
[+] documents/
    [-] projects/
        report.txt          report.txt          (Content Different)
        data.csv            data.csv            (Identical)
        new_file.txt        [blank]             (Only in Left)
        [blank]             old_file.txt        (Only in Right)
```

### Example 3: Verifying Synchronization

```
Left: /source/code
Right: /mirror/code

Status: 1,234 files scanned, 5 differences found

Navigate to differences using arrow keys, press Enter to view file diffs.
```

## Performance Improvements

The progressive scanning architecture provides significant performance benefits:

### Time to First Display

- **< 100ms**: Initial tree display with top-level items
- **No waiting**: Start navigating immediately
- **Responsive UI**: Never blocks during scanning

### Memory Efficiency

- **Lazy loading**: Only scans directories when needed
- **Smart prioritization**: Visible items loaded first
- **One-sided optimization**: Deep one-sided trees scanned on-demand

### Large Directory Handling

- **10,000+ files**: Handles efficiently with progressive scanning
- **Background threads**: Scanning doesn't block UI
- **Incremental updates**: Tree updates as items are discovered

### User Experience

- **Instant feedback**: See results immediately
- **Explore while scanning**: Navigate already-scanned portions
- **Priority-based**: What you see is scanned first
- **On-demand expansion**: Expand directories for instant scanning

## Tips and Best Practices

1. **Instant feedback**: Start navigating immediately - no need to wait for full scan
2. **Use filtering**: Hide identical files to focus on differences
3. **On-demand exploration**: Expand directories as needed - they'll scan instantly
4. **Check error count**: Review the status bar for permission or I/O errors
5. **Navigate efficiently**: Use Page Up/Down for large directory trees
6. **Verify changes**: Open file diff viewer for content-different files to see exact changes
7. **Smart prioritization**: Scroll to areas of interest - they'll be scanned first
8. **Cancel if needed**: Press Escape during scanning to close the viewer

## Limitations

- Binary file comparison is byte-by-byte (no semantic diff)
- Symbolic links are followed (may cause issues with circular links)
- Remote directories may be slower to scan depending on connection speed
- Very deep one-sided directory trees are scanned lazily (only when expanded)

## Troubleshooting

### Viewer opens instantly but shows pending items

- This is normal behavior with progressive scanning
- Background threads are scanning subdirectories
- Navigate to pending items to trigger immediate scanning
- Wait for "Scan complete" message for full results

### Some directories show "..." indicator

- Directory contents have not been scanned yet
- Expand the directory to trigger immediate scanning
- Background scanning will eventually scan all directories
- One-sided directories are scanned lazily (only when expanded)

### Some files show as different but appear identical

- Check file permissions and timestamps
- Binary files may have metadata differences
- Use the file diff viewer to see exact differences

### Permission errors prevent comparison

- Ensure you have read access to both directories
- Run TFM with appropriate permissions
- The viewer will continue with accessible portions

## Related Features

- **File Diff Viewer**: View line-by-line differences for individual files
- **Dual Pane File Manager**: Navigate and manage files in two directories
- **Search Dialog**: Find specific files within directories
