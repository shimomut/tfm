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

The viewer will scan both directories recursively and display a unified tree structure showing all files and subdirectories.

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

## Navigation and Controls

### Basic Navigation

- **Up/Down Arrow**: Move cursor through visible tree nodes
- **Page Up/Page Down**: Scroll one page at a time
- **Home**: Jump to first node
- **End**: Jump to last node

### Expanding and Collapsing

- **Right Arrow** or **Enter**: Expand a collapsed directory
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

### During Scanning

While directories are being scanned:

- A progress indicator shows scanning status
- Current operation is displayed in the status bar
- Press **Escape** to cancel the scan

### After Scanning

Once scanning completes:

- The tree structure is displayed
- Status bar shows statistics (total files, differences, errors)
- You can navigate and explore the results

## Status Bar Information

The status bar at the bottom displays:

- **Current position**: Line number and total lines
- **Statistics**: Number of files scanned, differences found
- **Filter state**: Whether identical files are hidden
- **Error count**: Number of inaccessible files or directories (if any)

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

### Example 1: Comparing Backup Directories

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

### Example 2: Verifying Synchronization

```
Left: /source/code
Right: /mirror/code

Status: 1,234 files scanned, 5 differences found

Navigate to differences using arrow keys, press Enter to view file diffs.
```

## Tips and Best Practices

1. **Use filtering**: Hide identical files to focus on differences
2. **Check error count**: Review the status bar for permission or I/O errors
3. **Navigate efficiently**: Use Page Up/Down for large directory trees
4. **Verify changes**: Open file diff viewer for content-different files to see exact changes
5. **Cancel long scans**: Press Escape if scanning takes too long

## Limitations

- Very large directories (10,000+ files) may take time to scan
- Binary file comparison is byte-by-byte (no semantic diff)
- Symbolic links are followed (may cause issues with circular links)
- Remote directories may be slower to scan depending on connection speed

## Troubleshooting

### Viewer is slow to open

- Large directories take time to scan recursively
- Check the progress indicator for status
- Consider canceling and comparing smaller subdirectories

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
