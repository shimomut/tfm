# Text Viewer Incremental Search Feature

## Overview

The TFM text viewer now includes incremental search functionality that allows users to quickly find and navigate to text within the currently viewed file. The search is case-insensitive and provides real-time highlighting of matches.

## How to Use

### Starting a Search
- Press `f` or `F` while viewing a text file to enter search mode
- The header will change to show the search interface

### Search Interface
When in search mode, the header displays:
```
Search: [your pattern] (current_match/total_matches) [ESC:exit ↑↓:navigate]
```

### Search Controls
- **Type characters**: Add to search pattern (incremental search)
- **Backspace**: Remove last character from search pattern
- **↑ or k**: Go to previous match
- **↓ or j**: Go to next match
- **Enter**: Exit search mode and stay at current position
- **ESC**: Exit search mode and stay at current position

### Visual Feedback
- **Search matches**: Highlighted with dark yellow background
- **Current match**: Highlighted with orange background (stands out from other matches)
- **Match counter**: Shows current match position and total matches (e.g., "2/5")

## Features

### Incremental Search
- Search results update in real-time as you type
- No need to press Enter to start searching
- Case-insensitive matching

### Smart Navigation
- When entering search mode, automatically finds the closest match to your current position
- Use arrow keys to cycle through matches
- Matches wrap around (after last match, goes to first)

### Visual Highlighting
- All matches are highlighted with a distinct background color
- Current match has a different, more prominent highlight
- Search interface is clearly visible in the header

### Integration with Text Viewer
- Search works seamlessly with all text viewer features
- Line numbers, syntax highlighting, and horizontal scrolling all work during search
- Search state is preserved until you exit search mode

## Implementation Details

### Search Algorithm
- Uses simple substring matching (case-insensitive)
- Searches through the plain text lines (not syntax-highlighted content)
- Maintains a list of matching line indices for efficient navigation

### Color System
- Uses dedicated color pairs for search highlighting:
  - `COLOR_SEARCH_MATCH`: Dark yellow background for regular matches
  - `COLOR_SEARCH_CURRENT`: Orange background for current match
- Supports both RGB terminals and fallback colors

### Performance
- Search is performed on the already-loaded file content
- No file re-reading required during search
- Efficient line-by-line matching with early termination

## Key Bindings Summary

| Key | Action |
|-----|--------|
| `f` or `F` | Enter search mode |
| `ESC` | Exit search mode |
| `Enter` | Exit search mode |
| `Backspace` | Remove last search character |
| `↑` or `k` | Previous match |
| `↓` or `j` | Next match |
| Any printable character | Add to search pattern |

## Examples

### Basic Search
1. Open a text file in the viewer
2. Press `f` to start searching
3. Type "function" to find all occurrences of "function"
4. Use ↑/↓ to navigate between matches
5. Press ESC to exit search

### Incremental Refinement
1. Start search with `f`
2. Type "def" - shows all lines containing "def"
3. Add " " (space) - shows lines with "def "
4. Add "main" - shows lines with "def main"
5. Navigate through specific matches

## Technical Notes

- Search patterns are treated as literal strings (no regex)
- Search is performed on the original file lines, not the syntax-highlighted versions
- Horizontal scrolling is maintained during search
- Search highlighting takes precedence over syntax highlighting for matched text
- Empty search patterns show no matches (safe behavior)

## Future Enhancements

Potential improvements for future versions:
- Regular expression support
- Case-sensitive search option
- Whole word matching
- Search history
- Replace functionality
- Multi-file search integration