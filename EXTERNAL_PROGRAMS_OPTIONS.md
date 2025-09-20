# External Programs Options

## Overview

TFM's external programs feature now supports program-specific options that control how programs are executed and how TFM behaves after program completion.

## Options Format

Each program entry in the `PROGRAMS` list can include an optional `options` dictionary:

```python
{
    'name': 'Program Name',
    'command': ['command', 'arg1', 'arg2'],
    'options': {
        'option_name': value,
        # ... more options
    }
}
```

## Available Options

### auto_return

**Type**: Boolean  
**Default**: False  
**Description**: Controls whether TFM automatically returns to the file manager interface after program execution.

- `True`: Automatically returns to TFM after the program completes (with a 1-second delay to show completion status)
- `False`: Waits for user to press Enter before returning to TFM (default behavior)

**Use Cases**:
- Quick information commands (git status, disk usage, file listings)
- Programs that launch GUI applications and return immediately
- Automated scripts that don't require user interaction after completion

## Configuration Examples

### Basic Programs (No Options)
```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
    {'name': 'Python REPL', 'command': ['python3']},
]
```

### Programs with Auto Return
```python
PROGRAMS = [
    # Quick information commands
    {'name': 'Git Status (Quick)', 'command': ['git', 'status', '--short'], 'options': {'auto_return': True}},
    {'name': 'Disk Usage', 'command': ['du', '-sh', '*'], 'options': {'auto_return': True}},
    {'name': 'File Count', 'command': ['find', '.', '-type', 'f', '|', 'wc', '-l'], 'options': {'auto_return': True}},
    
    # GUI applications that return immediately
    {'name': 'Compare Directories', 'command': ['./compare_script.sh'], 'options': {'auto_return': True}},
    {'name': 'Open in VS Code', 'command': ['code', '.'], 'options': {'auto_return': True}},
    
    # Interactive programs (no auto_return)
    {'name': 'Git Interactive Add', 'command': ['git', 'add', '-i']},
    {'name': 'Text Editor', 'command': ['vim', 'README.md']},
]
```

### Mixed Configuration
```python
PROGRAMS = [
    # Standard programs that wait for user input
    {'name': 'Git Log', 'command': ['git', 'log', '--oneline', '-20']},
    {'name': 'System Monitor', 'command': ['htop']},
    
    # Quick status commands with auto return
    {'name': 'Git Status', 'command': ['git', 'status', '--short'], 'options': {'auto_return': True}},
    {'name': 'Network Status', 'command': ['ping', '-c', '3', 'google.com'], 'options': {'auto_return': True}},
    
    # GUI applications with auto return
    {'name': 'File Manager', 'command': ['open', '.'], 'options': {'auto_return': True}},
    {'name': 'BeyondCompare Dirs', 'command': ['./bcompare_dirs_wrapper.sh'], 'options': {'auto_return': True}},
]
```

## Behavior Details

### Without auto_return (Default)
1. Program executes
2. Program output is displayed
3. "Press Enter to return to TFM..." message appears
4. User must press Enter to return to TFM
5. TFM interface is restored

### With auto_return: True
1. Program executes
2. Program output is displayed
3. "Auto-returning to TFM..." message appears
4. 1-second delay (to show completion status)
5. Automatically returns to TFM interface

## Best Practices

### Use auto_return: True for:
- **Quick information commands**: Commands that display brief information and exit
- **GUI applications**: Programs that launch a GUI and return immediately
- **Status checks**: Commands that show system/project status
- **File operations**: Commands that perform quick file operations

### Don't use auto_return for:
- **Interactive programs**: Programs that require user input (editors, REPLs, interactive tools)
- **Long-running commands**: Commands that produce lots of output that users need time to read
- **Error-prone commands**: Commands where users might need to see error messages

### Examples by Category

#### Good for auto_return
```python
{'name': 'Git Status', 'command': ['git', 'status', '--short'], 'options': {'auto_return': True}},
{'name': 'Disk Space', 'command': ['df', '-h'], 'options': {'auto_return': True}},
{'name': 'Open Finder', 'command': ['open', '.'], 'options': {'auto_return': True}},
{'name': 'Quick Backup', 'command': ['./backup.sh'], 'options': {'auto_return': True}},
```

#### Better without auto_return
```python
{'name': 'Git Log', 'command': ['git', 'log', '--oneline', '-50']},  # Lots of output to read
{'name': 'Vim Editor', 'command': ['vim']},  # Interactive
{'name': 'System Monitor', 'command': ['htop']},  # Interactive
{'name': 'Git Interactive Rebase', 'command': ['git', 'rebase', '-i']},  # Interactive
```

## Migration from Old Format

### Old Format (Still Supported)
```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status']},
]
```

### New Format with Options
```python
PROGRAMS = [
    {'name': 'Git Status', 'command': ['git', 'status'], 'options': {'auto_return': True}},
]
```

The old format continues to work exactly as before. The `options` field is completely optional.

## Testing Options

To test your options configuration:

1. **Check parsing**: Run `python3 test_auto_return.py` to verify options are parsed correctly
2. **Test in TFM**: Start TFM and test programs with different option settings
3. **Verify behavior**: Ensure auto_return programs return automatically while others wait for input

## Future Options

The options system is designed to be extensible. Future options might include:

- `working_directory`: Override the working directory for program execution
- `timeout`: Set a maximum execution time for programs
- `background`: Run programs in the background
- `confirm_before_run`: Ask for confirmation before executing
- `show_output`: Control whether program output is displayed

## Troubleshooting

### Options Not Working
- Verify the options dictionary syntax is correct
- Check that the option name is spelled correctly (`auto_return`, not `autoreturn`)
- Ensure the option value is the correct type (Boolean for `auto_return`)

### Programs Still Wait for Input
- Check that `auto_return` is set to `True` (not `"true"` or `1`)
- Verify the program entry includes the `options` dictionary
- Test with a simple command to isolate the issue

### Syntax Errors in Configuration
- Use proper Python dictionary syntax
- Ensure all quotes and brackets are properly matched
- Test configuration changes with the test scripts before using in TFM