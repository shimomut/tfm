# Text Diff Viewer Feature

## Overview

The Text Diff Viewer is a side-by-side comparison tool that displays differences between two text files. It provides a visual representation of changes, making it easy to identify additions, deletions, and modifications.

## How to Use

### Selecting Files

You can select two files for comparison in several ways:

1. **Both files in left pane**: Select two files in the left pane using Space
2. **Both files in right pane**: Select two files in the right pane using Space
3. **One file in each pane**: Select one file in the left pane and one file in the right pane

### Launching the Diff Viewer

Once you have exactly two text files selected:

1. Press `=` (equals key) to launch the diff viewer
2. The viewer will open showing both files side-by-side

### Requirements

- Exactly 2 files must be selected (no more, no less)
- Both files must be regular files (not directories)
- Both files must be text files (not binary files)

### Error Messages

- **"No files selected"**: You haven't selected any files
- **"Only 1 file selected"**: You need to select one more file
- **"Selected X files"**: You have too many files selected (need exactly 2)
- **"Selected items include directories"**: One or more selected items are directories
- **"'filename' is not a text file"**: One of the selected files is binary

## Diff Viewer Interface

### Display Layout

```
┌─────────────────────────────────────────────────────────────┐
│ original.py              │ modified.py                       │
│ Controls: q/Enter:quit ↑↓:scroll ←→:h-scroll PgUp/PgDn:page │
├──────────────────────────┼──────────────────────────────────┤
│ Line 1 content           │ Line 1 content                    │
│ Line 2 original          │ Line 2 modified                   │
│ Line 3 content           │ Line 3 content                    │
│ Line 4 only in left      │                                   │
│                          │ Line 5 only in right              │
├──────────────────────────┴──────────────────────────────────┤
│ Line 5/10 (50%) | Equal: 6 | Changed: 4                     │
└─────────────────────────────────────────────────────────────┘
```

### Color Coding

The diff viewer uses colors to indicate the type of change:

- **White/Regular**: Lines that are identical in both files
- **Red**: Lines that were deleted (only in left file)
- **Blue/Cyan**: Lines that were inserted (only in right file)
- **Green/Yellow**: Lines that were modified (different in both files)

### Navigation Controls

#### Vertical Scrolling
- `↑` (Up Arrow): Scroll up one line
- `↓` (Down Arrow): Scroll down one line
- `Page Up`: Scroll up one page
- `Page Down`: Scroll down one page
- `Home`: Jump to the beginning
- `End`: Jump to the end

#### Horizontal Scrolling
- `←` (Left Arrow): Scroll left one column
- `→` (Right Arrow): Scroll right one column

#### Exit
- `q`: Quit the diff viewer
- `Enter`: Quit the diff viewer
- `Escape`: Quit the diff viewer

### Status Bar Information

The status bar at the bottom shows:

- **Current line / Total lines**: Your position in the diff
- **Scroll percentage**: How far through the diff you are
- **Equal lines**: Number of identical lines
- **Changed lines**: Number of lines with differences

## Use Cases

### Code Review
Compare different versions of source code to review changes:
- Review pull request changes
- Compare before/after refactoring
- Verify bug fixes

### Configuration Management
Compare configuration files:
- Check differences between environments (dev vs prod)
- Verify configuration changes
- Audit configuration updates

### Document Comparison
Compare text documents:
- Review document revisions
- Compare different versions of documentation
- Track changes in text files

### Log Analysis
Compare log files:
- Compare logs from different time periods
- Identify changes in system behavior
- Debug issues by comparing good vs bad logs

## Tips and Best Practices

### Efficient File Selection

1. **Same directory comparison**: 
   - Navigate to the directory containing both files
   - Select both files with Space
   - Press `=` to compare

2. **Different directory comparison**:
   - Navigate to first file's directory in left pane
   - Select the file with Space
   - Switch to right pane with Tab
   - Navigate to second file's directory
   - Select the file with Space
   - Press `=` to compare

3. **Quick comparison**:
   - Use the cursor to highlight the first file
   - Press Space to select it
   - Move cursor to second file
   - Press Space to select it
   - Press `=` to compare

### Working with Large Files

- Use Page Up/Down for faster navigation
- Use Home/End to jump to beginning/end
- Horizontal scrolling helps with long lines
- The scroll bar shows your position in the file

### Understanding Changes

- **Red lines (left only)**: Content was removed
- **Green lines (right only)**: Content was added
- **Yellow lines (both sides)**: Content was modified
- **White lines**: Content is identical

### Keyboard Shortcuts Summary

| Key | Action |
|-----|--------|
| `=` | Launch diff viewer (from file manager) |
| `↑`/`↓` | Scroll vertically |
| `←`/`→` | Scroll horizontally |
| `PgUp`/`PgDn` | Page up/down |
| `Home`/`End` | Jump to start/end |
| `q`/`Enter`/`Esc` | Exit viewer |

## Technical Details

### Diff Algorithm

The diff viewer uses Python's `difflib.SequenceMatcher` to compute differences:
- Line-by-line comparison
- Identifies equal, replaced, deleted, and inserted lines
- Efficient algorithm for large files

### File Format Support

Supported file types:
- Plain text files (`.txt`)
- Source code files (`.py`, `.js`, `.java`, `.c`, etc.)
- Configuration files (`.conf`, `.ini`, `.yaml`, etc.)
- Markup files (`.html`, `.xml`, `.md`, etc.)
- Any UTF-8 encoded text file

Unsupported file types:
- Binary files (executables, images, etc.)
- Compressed files (`.zip`, `.gz`, etc.)
- Database files

### Encoding Support

The diff viewer attempts to read files using multiple encodings:
1. UTF-8 (preferred)
2. Latin-1 (fallback)
3. CP1252 (Windows fallback)

Binary files are automatically detected and rejected.

## Troubleshooting

### "No viewer configured" Error
- This error shouldn't occur for diff viewer
- Make sure you're pressing `=` (equals key)
- Verify exactly 2 files are selected

### Files Not Displaying Correctly
- Check if files are text files (not binary)
- Try viewing files individually first with `v`
- Check file encoding (UTF-8 recommended)

### Performance Issues
- Very large files (>10MB) may be slow
- Consider comparing smaller sections
- Use horizontal scrolling for very wide lines

### Selection Issues
- Make sure exactly 2 files are selected
- Use `End` key to unselect all, then reselect
- Check status bar for selection count

## Examples

### Example 1: Compare Two Python Files

```
1. Navigate to your project directory
2. Select file1.py with Space
3. Select file2.py with Space
4. Press = to view diff
5. Use ↑/↓ to review changes
6. Press q to exit
```

### Example 2: Compare Config Files Across Panes

```
1. Left pane: Navigate to /etc/config/
2. Select config.ini with Space
3. Press Tab to switch to right pane
4. Right pane: Navigate to /backup/config/
5. Select config.ini with Space
6. Press = to view diff
7. Review differences
8. Press q to exit
```

### Example 3: Compare Before/After Edits

```
1. Select original_file.txt
2. Select modified_file.txt
3. Press = to compare
4. Red lines show deletions
5. Green lines show additions
6. Yellow lines show modifications
7. Press q when done
```

## Integration with TFM

The diff viewer integrates seamlessly with TFM:

- Uses the same color scheme as TFM
- Follows TFM's keyboard navigation patterns
- Respects TFM's file selection system
- Works with both local and remote files (if supported)

## Future Enhancements

Potential future improvements:

- Inline diff view (single column with +/- markers)
- Word-level diff highlighting
- Syntax highlighting in diff view
- Export diff to patch file
- Three-way merge support
- Diff statistics and summary
