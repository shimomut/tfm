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
- **Yellow**: Lines that were changed (modified, inserted, or replaced)
- **Gray**: Dummy/blank lines inserted for alignment (when one side has no content)
- **Bright Blue**: Currently focused difference (when using n/p navigation)

When navigating between differences using `n` (next) and `p` (previous), the focused difference block is highlighted with a bright blue background, making it stand out from other changes. Note that dummy alignment lines (gray) are not highlighted when focused - only real content lines receive the focus highlight.

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

#### Difference Navigation
- `n`: Jump to next difference
- `p`: Jump to previous difference

The currently focused difference is highlighted with a distinct blue background color, making it easy to see which change you're reviewing. The status bar shows your position (e.g., "Diff 3/16") indicating you're viewing the 3rd difference out of 16 total differences.

#### Display Options
- `#`: Toggle line numbers on/off
- `s`: Toggle syntax highlighting on/off (if pygments is available)
- `t`: Cycle through tab widths (2, 4, 8 spaces)
- `w`: Toggle whitespace ignore mode (ignore spaces and tabs when comparing)

#### Exit
- `q`: Quit the diff viewer
- `Enter`: Quit the diff viewer
- `Escape`: Quit the diff viewer

### Status Bar Information

The status bar at the bottom shows:

- **Current line / Total lines**: Your position in the diff
- **Scroll percentage**: How far through the diff you are
- **Diff position**: Current difference number and total (e.g., "Diff 3/16")
- **Equal lines**: Number of identical lines
- **Changed lines**: Number of lines with differences
- **Active options**: Shows which features are enabled (NUM for line numbers, SYNTAX for syntax highlighting, TAB:4 for tab width, IGNORE-WS for whitespace ignore mode)

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
- **Yellow lines**: Content was changed (modified, inserted, or replaced)
- **Gray lines**: Dummy/blank lines for alignment (no actual content)
- **White lines**: Content is identical
- **Bright blue lines**: Currently focused difference (use n/p to navigate)

Note: Dummy alignment lines (shown in gray) appear when one side of the diff has no corresponding content. These are not highlighted when focused - only lines with actual content receive the focus highlight.

### Navigating Between Differences

The diff viewer automatically tracks all differences in the files. Use `n` and `p` to jump between them:

1. Press `n` to jump to the next difference
2. Press `p` to jump to the previous difference
3. The focused difference is highlighted with a bright blue background
4. The status bar shows your position (e.g., "Diff 3/16")

This makes it easy to review changes one at a time without manually scrolling through the entire file.

### Ignoring Whitespace Differences

The diff viewer includes a whitespace ignore mode that's useful when comparing files with formatting differences:

**What it does:**
- Ignores all space and tab characters when comparing lines
- Focuses on actual content changes, not formatting
- Useful for comparing code with different indentation styles
- **Important**: Original text with all whitespace is always displayed - only the comparison logic changes

**How to use:**
1. Press `w` to toggle whitespace ignore mode
2. The status bar shows "IGNORE-WS" when enabled
3. The diff is automatically recomputed
4. Press `w` again to disable

**How it works:**
- Lines are compared after stripping all spaces and tabs
- If lines match after stripping, they're shown as equal (white/regular background)
- If lines differ after stripping, they're shown as different (yellow background)
- The original text with all whitespace is always displayed
- Character-level highlighting still works, but compares non-whitespace characters only
- Whitespace characters are shown but not highlighted as differences

**Common use cases:**
- Comparing code formatted with different tab widths
- Reviewing changes where only spacing was modified
- Comparing files with trailing whitespace differences
- Checking if two files are functionally identical despite formatting

**Example:**
```python
# File 1
def hello():
    print("Hello")

# File 2 (extra spaces and tabs)
def hello():
	print("Hello")  
```

Without whitespace ignore: Shows as different (yellow background)
With whitespace ignore: Shows as identical (white/regular background)

Note: The actual text displayed always includes all spaces and tabs - only the background color changes to indicate whether the lines are considered different.

### Keyboard Shortcuts Summary

| Key | Action |
|-----|--------|
| `=` | Launch diff viewer (from file manager) |
| `↑`/`↓` | Scroll vertically |
| `←`/`→` | Scroll horizontally |
| `n` | Jump to next difference |
| `p` | Jump to previous difference |
| `PgUp`/`PgDn` | Page up/down |
| `Home`/`End` | Jump to start/end |
| `#` | Toggle line numbers |
| `s` | Toggle syntax highlighting |
| `t` | Cycle tab width (2/4/8) |
| `w` | Toggle whitespace ignore mode |
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
