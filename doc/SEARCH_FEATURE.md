# TFM Incremental Search Feature

## Overview

TFM now includes an incremental search mode that allows users to quickly find files using Python's fnmatch pattern syntax. The search is case-insensitive and updates results in real-time as you type.

## How to Use

1. **Enter Search Mode**: Press `F` key while in the file manager
2. **Type Pattern**: Start typing your search pattern using fnmatch syntax
3. **Navigate Results**: Use ↑/↓ arrow keys to move between matches
4. **Exit Search**: Press `Enter` to accept current position or `ESC` to cancel

## Pattern Syntax

The search uses Python's fnmatch module with multi-pattern support:

### Single Pattern Wildcards
- `*` - Matches any number of characters (including zero)
- `?` - Matches exactly one character
- `[seq]` - Matches any character in seq
- `[!seq]` - Matches any character not in seq

### Multi-Pattern Search
- **Space-separated patterns**: All patterns must match the filename
- **Contains matching**: Each pattern is automatically wrapped with `*` for substring matching
- **Example**: `test config` finds files containing both "test" AND "config"

## Examples

### Single Pattern Examples
| Pattern | Description | Matches |
|---------|-------------|---------|
| `*.py` | Python files | main.py, setup.py, test.py |
| `*.txt` | Text files | readme.txt, notes.txt |
| `*test*` | Files containing "test" | test_file.py, my_test.txt |
| `M*` | Files starting with "M" | Makefile, main.py |
| `???.*` | Files with 3-character names | app.js, run.sh |
| `config.*` | Config files | config.json, config.yaml |

### Multi-Pattern Examples
| Pattern | Description | Matches |
|---------|-------------|---------|
| `test config` | Files containing both "test" AND "config" | test_config.py, config_test.txt |
| `*.py test` | Python files containing "test" | test_main.py, my_test.py |
| `ab*c 12?3` | Files matching both patterns | abc_1203_file.txt |
| `main *.js` | JavaScript files containing "main" | main_app.js, main.min.js |
| `config *.json *.yaml` | Config files in JSON or YAML format | config.json, app_config.yaml |

## Features

- **Real-time matching**: Results update as you type
- **Multi-pattern support**: Space-separated patterns (all must match)
- **Contains matching**: Patterns automatically match substrings
- **Visual feedback**: Matching files are underlined in the file list
- **Match counter**: Shows current match position (e.g., "2/5 matches")
- **Cursor positioning**: Automatically moves to the nearest match
- **Wrap-around navigation**: Cycles through matches with ↑/↓ keys
- **Case-insensitive**: Search works regardless of case

## Search Mode Interface

When in search mode, the status bar shows:
```
Search: test config_ (2/5 matches)    ESC:exit Enter:accept ↑↓:navigate Space:multi-pattern
```

- The `_` indicates the cursor position
- Match count shows current position and total matches
- Help text shows available commands including multi-pattern support
- Empty search shows: `Search: _ (enter patterns separated by spaces)`

## Integration

The search feature integrates seamlessly with TFM's existing functionality:

- Works in both left and right panes
- Respects the current directory context
- Maintains file selection state
- Compatible with hidden file toggle (`.` key)
- Does not interfere with other TFM operations

## Technical Details

- Uses Python's `fnmatch` module for pattern matching
- Case-insensitive matching (converts both pattern and filenames to lowercase)
- Skips parent directory entries (`..`) in search results
- Efficient real-time updates with minimal performance impact
- Proper cursor positioning and scroll handling
- Robust exception handling ensures stdout/stderr are restored on crashes