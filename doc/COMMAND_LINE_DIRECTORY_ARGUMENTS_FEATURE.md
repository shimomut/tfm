# Command Line Directory Arguments Feature

## Overview

TFM now supports command line arguments `--left` and `--right` to specify initial directory paths for the left and right panes respectively. This feature allows users to start TFM with specific directories already loaded, improving workflow efficiency.

## Usage

### Basic Syntax

```bash
python tfm.py [--left PATH] [--right PATH]
```

### Examples

#### Specify both panes
```bash
python tfm.py --left /home/user/projects --right /home/user/documents
```

#### Specify only left pane (right pane uses default home directory)
```bash
python tfm.py --left /home/user/projects
```

#### Specify only right pane (left pane uses default current directory)
```bash
python tfm.py --right /home/user/documents
```

#### Use relative paths
```bash
python tfm.py --left . --right ..
python tfm.py --left ./src --right ./test
```

#### Combine with other options
```bash
python tfm.py --left ./src --right ./test --remote-log-port 8888
```

## Features

### History Override Behavior
- **Command line directories take precedence over saved history**
- When `--left` is specified, the left pane will not restore its previous directory from history
- When `--right` is specified, the right pane will not restore its previous directory from history
- Other pane settings (sort mode, sort direction, filter patterns) are still restored from history
- This allows users to start TFM with specific directories while preserving other preferences

### Directory Validation
- If a specified directory doesn't exist or isn't a directory, TFM will:
  - Log a warning message
  - Fall back to the default directory (current directory for left, home directory for right)
  - Continue normal operation

### Path Support
- **Absolute paths**: `/home/user/projects`, `/tmp`, `/var/log`
- **Relative paths**: `.`, `..`, `./src`, `../docs`
- **Home directory expansion**: `~/projects` (handled by shell)

### Default Behavior
- **Without arguments**: Left pane starts in current directory, right pane in home directory
- **With --left only**: Right pane uses home directory
- **With --right only**: Left pane uses current directory

## Implementation Details

### Command Line Parsing
- Arguments are parsed in `tfm.py` using `argparse`
- Both arguments are optional with `type=str`
- Help text clearly describes the default behavior

### Directory Initialization
- Paths are converted to `Path` objects in `FileManager.__init__()`
- Existence and directory validation occurs before PaneManager initialization
- Invalid paths trigger warning messages and fallback to defaults
- Command line argument flags (`cmdline_left_dir_provided`, `cmdline_right_dir_provided`) are tracked

### Integration with State Management
- Command line directories override saved history/state
- When `--left` is specified, the left pane ignores saved history and uses the command line path
- When `--right` is specified, the right pane ignores saved history and uses the command line path
- Other pane settings (sort mode, filters) are still restored from history when available
- Panes without command line arguments restore normally from saved state

### History Override Logic
The `load_application_state()` method implements the override logic:

```python
# Left pane restoration logic
if left_state and Path(left_state['path']).exists() and not self.cmdline_left_dir_provided:
    # Restore path from history
    self.pane_manager.left_pane['path'] = Path(left_state['path'])
elif self.cmdline_left_dir_provided:
    # Keep command line directory, but restore other settings
    if left_state:
        self.pane_manager.left_pane['sort_mode'] = left_state.get('sort_mode', 'name')
        # ... other settings
```

This ensures that:
- Command line directories always take precedence over saved state
- Other pane preferences (sorting, filters) are preserved when possible
- The behavior is consistent and predictable

## Error Handling

### Invalid Directories
```
Warning: Left directory '/nonexistent/path' does not exist, using current directory
Warning: Right directory '/invalid/path' does not exist, using home directory
```

### Permission Issues
- If directories exist but aren't readable, TFM will attempt to use them
- File listing errors are handled by existing TFM error handling mechanisms

## Testing

### Unit Tests
- `test/test_command_line_arguments.py` provides comprehensive test coverage
- Tests argument parsing, validation, and integration scenarios

### Demo Script
- `demo/demo_command_line_directories.py` creates sample directories and demonstrates usage
- Shows practical examples and expected behavior

## Backward Compatibility

- Fully backward compatible - existing TFM usage continues to work unchanged
- No breaking changes to existing command line interface
- Optional arguments don't affect default behavior when not specified

## Use Cases

### Development Workflows
```bash
# Compare source and test directories
python tfm.py --left ./src --right ./test

# Review project and documentation
python tfm.py --left ./project --right ./docs

# Compare different branches (after checkout)
python tfm.py --left ./current --right ./backup
```

### System Administration
```bash
# Monitor logs and configuration
python tfm.py --left /var/log --right /etc

# Compare system directories
python tfm.py --left /usr/local --right /opt
```

### File Organization
```bash
# Organize downloads and documents
python tfm.py --left ~/Downloads --right ~/Documents

# Sort media files
python tfm.py --left ~/Pictures --right ~/Videos
```

## Future Enhancements

Potential future improvements could include:
- Support for more than two panes with additional arguments
- Bookmark integration with named directory shortcuts
- Configuration file support for default directory preferences
- Tab completion for directory paths in shell environments