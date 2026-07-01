# Command Pretty-Printing Implementation

## Overview

This document describes the implementation of the command pretty-printing functionality in TTK. The `pretty_print_command()` function formats rendering commands in a human-readable way with indentation and parameter names, making it easy to debug, log, and understand command sequences.

## Implementation Details

### Location

The pretty-printing functionality is implemented in:
- **Module**: `ttk/serialization/command_serializer.py`
- **Function**: `pretty_print_command()`
- **Helper**: `_format_value()`

### Function Signature

```python
def pretty_print_command(command: Union[Command, Dict[str, Any]], indent: int = 0) -> str:
    """
    Format a rendering command in a human-readable way for debugging.
    
    Args:
        command: A command dataclass instance or serialized command dictionary
        indent: Number of spaces to indent the output (default: 0)
    
    Returns:
        str: A formatted, human-readable string representation of the command
    """
```

### Key Features

1. **Flexible Input**: Accepts both command dataclass instances and serialized dictionaries
2. **Custom Indentation**: Supports configurable indentation for nested display
3. **Consistent Formatting**: Parameters are sorted alphabetically for predictable output
4. **Type-Aware Formatting**: Different value types are formatted appropriately:
   - Strings are quoted
   - Booleans are lowercase
   - RGB tuples are formatted as `(R, G, B)`
   - Other values use default string representation

### Output Format

The output follows this structure:

```
command_type:
  parameter1: value1
  parameter2: value2
  ...
```

Example:

```
draw_text:
  attributes: 3
  col: 10
  color_pair: 1
  row: 5
  text: "Hello, World!"
```

### Implementation Strategy

1. **Convert to Dictionary**: If the input is a dataclass, serialize it first
2. **Extract Command Type**: Get the command type from the dictionary
3. **Format Header**: Create the command type line with appropriate indentation
4. **Sort Parameters**: Sort parameters alphabetically (excluding command_type)
5. **Format Each Parameter**: Use `_format_value()` to format each parameter value
6. **Combine Lines**: Join all lines with newlines

### Value Formatting Rules

The `_format_value()` helper function applies these formatting rules:

| Value Type | Formatting Rule | Example |
|------------|----------------|---------|
| String | Quoted with double quotes | `"Hello"` |
| Boolean | Lowercase | `true`, `false` |
| RGB Tuple | Parentheses with commas | `(255, 128, 0)` |
| Other Tuple/List | Parentheses with commas | `(1, 2, 3)` |
| Other Types | Default string representation | `42`, `3.14` |

### Indentation Support

The `indent` parameter controls the base indentation level:
- Command type is indented by `indent` spaces
- Parameters are indented by `indent + 2` spaces

Example with `indent=4`:

```
    draw_text:
      row: 5
      col: 10
      text: "Hello"
```

## Usage Examples

### Basic Usage

```python
from ttk.serialization import DrawTextCommand, pretty_print_command

# Create a command
cmd = DrawTextCommand(
    row=5,
    col=10,
    text="Hello, World!",
    color_pair=1,
    attributes=3
)

# Pretty print it
print(pretty_print_command(cmd))
```

Output:
```
draw_text:
  attributes: 3
  col: 10
  color_pair: 1
  row: 5
  text: "Hello, World!"
```

### From Serialized Dictionary

```python
from ttk.serialization import pretty_print_command

# Serialized command dictionary
data = {
    'command_type': 'draw_rect',
    'row': 0,
    'col': 0,
    'height': 10,
    'width': 20,
    'color_pair': 2,
    'filled': True
}

# Pretty print it
print(pretty_print_command(data))
```

Output:
```
draw_rect:
  col: 0
  color_pair: 2
  filled: true
  height: 10
  row: 0
  width: 20
```

### With Custom Indentation

```python
from ttk.serialization import MoveCursorCommand, pretty_print_command

cmd = MoveCursorCommand(row=10, col=20)

# Indent by 4 spaces
print(pretty_print_command(cmd, indent=4))
```

Output:
```
    move_cursor:
      col: 20
      row: 10
```

### Command Sequence

```python
from ttk.serialization import (
    ClearCommand,
    DrawTextCommand,
    RefreshCommand,
    pretty_print_command
)

commands = [
    ClearCommand(),
    DrawTextCommand(row=0, col=0, text="Title", color_pair=1, attributes=1),
    DrawTextCommand(row=1, col=0, text="Content", color_pair=0, attributes=0),
    RefreshCommand(),
]

for i, cmd in enumerate(commands, 1):
    print(f"Command {i}:")
    print(pretty_print_command(cmd, indent=2))
    print()
```

## Use Cases

### 1. Debugging

Pretty-print commands during development to understand what's being rendered:

```python
def debug_render(self, command):
    print(f"Rendering: {pretty_print_command(command)}")
    self.execute_command(command)
```

### 2. Logging

Log commands in a readable format for troubleshooting:

```python
import logging

logger = logging.getLogger(__name__)

def log_command(command):
    logger.debug(f"Command:\n{pretty_print_command(command, indent=2)}")
```

### 3. Testing

Verify command sequences in tests:

```python
def test_rendering_sequence():
    commands = recorder.get_commands()
    
    # Print for visual inspection
    for cmd in commands:
        print(pretty_print_command(cmd))
    
    # Verify command types
    assert commands[0].command_type == 'clear'
    assert commands[1].command_type == 'draw_text'
```

### 4. Documentation

Generate documentation showing example command sequences:

```python
def generate_example_docs():
    examples = [
        DrawTextCommand(row=0, col=0, text="Example", color_pair=1),
        DrawRectCommand(row=2, col=0, height=5, width=10, filled=False),
    ]
    
    for cmd in examples:
        print("```")
        print(pretty_print_command(cmd))
        print("```")
```

## Integration with Serialization

The pretty-printing function integrates seamlessly with the serialization system:

```python
from ttk.serialization import (
    DrawTextCommand,
    serialize_command,
    pretty_print_command
)

# Create command
cmd = DrawTextCommand(row=5, col=10, text="Test")

# Serialize it
serialized = serialize_command(cmd)

# Pretty print from either form
print(pretty_print_command(cmd))        # From dataclass
print(pretty_print_command(serialized))  # From dictionary

# Both produce identical output
```

## Performance Considerations

- **Lightweight**: Pretty-printing is a simple string formatting operation
- **No Side Effects**: Does not modify the input command
- **Memory Efficient**: Builds output string incrementally
- **Fast Enough**: Suitable for debugging and logging (not performance-critical)

## Testing

The pretty-printing functionality is tested in:
- **Demo**: `ttk/test/demo_command_pretty_print.py`
- **Tests**: `ttk/test/test_command_pretty_print.py`

Test coverage includes:
- All command types
- Custom indentation
- Dictionary input
- Dataclass input
- Special characters in strings
- RGB color tuples
- Boolean formatting
- Consistency with serialization

## Future Enhancements

Potential improvements for future versions:

1. **Color Output**: Add ANSI color codes for terminal output
2. **Compact Mode**: Option for single-line output
3. **JSON Format**: Option to output as formatted JSON
4. **Filtering**: Option to hide default parameter values
5. **Diff Mode**: Show differences between two commands

## Requirements Satisfied

This implementation satisfies:
- **Requirement 13.4**: "WHEN pretty-printing commands THEN the system SHALL format them in a human-readable way for debugging"

The pretty-printing functionality provides:
- Human-readable formatting with indentation
- Parameter names clearly labeled
- Consistent output format
- Support for all command types
- Flexible indentation for nested display
