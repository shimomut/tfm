# Command Serialization Implementation

## Overview

This document describes the implementation of command serialization for the TTK library. Command serialization enables testing and debugging of the rendering API independently of any backend implementation by converting rendering commands to a dictionary format that can be easily serialized to JSON or other text formats.

## Implementation Details

### Module Structure

The command serialization functionality is implemented in `ttk/serialization/command_serializer.py` and includes:

1. **Command Dataclasses**: Dataclass definitions for each rendering command type
2. **Serialization Functions**: Functions to convert commands to dictionary format
3. **Helper Functions**: Convenience functions for creating and serializing commands

### Command Dataclasses

Each rendering operation has a corresponding dataclass that captures all parameters:

- `DrawTextCommand` - Text rendering with position, text, color, and attributes
- `DrawHLineCommand` - Horizontal line drawing
- `DrawVLineCommand` - Vertical line drawing
- `DrawRectCommand` - Rectangle drawing (filled or outlined)
- `ClearCommand` - Clear entire window
- `ClearRegionCommand` - Clear rectangular region
- `RefreshCommand` - Refresh entire window
- `RefreshRegionCommand` - Refresh rectangular region
- `InitColorPairCommand` - Initialize color pair with RGB values
- `SetCursorVisibilityCommand` - Control cursor visibility
- `MoveCursorCommand` - Move cursor position

All command dataclasses include a `command_type` field that identifies the command type.

### Serialization Format

Commands are serialized to dictionaries with the following structure:

```python
{
    'command_type': 'draw_text',  # Command type identifier
    'row': 5,                      # Position parameters
    'col': 10,
    'text': 'Hello',               # Command-specific parameters
    'color_pair': 1,
    'attributes': 3
}
```

The dictionary format:
- Always includes a `command_type` field
- Includes all parameters needed to reproduce the command
- Uses simple Python types (int, str, bool, tuple) for easy serialization
- Can be directly converted to JSON for storage or transmission

### Core Functions

#### `serialize_command(command: Command) -> Dict[str, Any]`

Generic serialization function that converts any command dataclass to a dictionary:

```python
cmd = DrawTextCommand(row=5, col=10, text="Hello", color_pair=1, attributes=3)
serialized = serialize_command(cmd)
# Returns: {'command_type': 'draw_text', 'row': 5, 'col': 10, ...}
```

#### Helper Functions

Convenience functions for each command type that create and serialize in one step:

- `serialize_draw_text(row, col, text, color_pair=0, attributes=0)`
- `serialize_draw_hline(row, col, char, length, color_pair=0)`
- `serialize_draw_vline(row, col, char, length, color_pair=0)`
- `serialize_draw_rect(row, col, height, width, color_pair=0, filled=False)`
- `serialize_clear()`
- `serialize_clear_region(row, col, height, width)`
- `serialize_refresh()`
- `serialize_refresh_region(row, col, height, width)`
- `serialize_init_color_pair(pair_id, fg_color, bg_color)`
- `serialize_set_cursor_visibility(visible)`
- `serialize_move_cursor(row, col)`

Example usage:

```python
# Direct serialization
result = serialize_draw_text(row=3, col=7, text="Hello", color_pair=2)
# Returns: {'command_type': 'draw_text', 'row': 3, 'col': 7, 'text': 'Hello', ...}
```

## Usage Examples

### Basic Serialization

```python
from ttk.serialization import serialize_draw_text, serialize_draw_rect

# Serialize a text drawing command
text_cmd = serialize_draw_text(row=5, col=10, text="Status: OK", color_pair=1)

# Serialize a rectangle drawing command
rect_cmd = serialize_draw_rect(row=0, col=0, height=10, width=20, filled=True)
```

### Recording Command Sequences

```python
from ttk.serialization import (
    serialize_clear,
    serialize_draw_text,
    serialize_draw_rect,
    serialize_refresh
)

# Record a sequence of rendering commands
commands = []
commands.append(serialize_clear())
commands.append(serialize_draw_rect(row=0, col=0, height=5, width=40, color_pair=1, filled=True))
commands.append(serialize_draw_text(row=2, col=10, text="Title", color_pair=2))
commands.append(serialize_refresh())

# Commands can now be saved to JSON, replayed, or analyzed
import json
json_output = json.dumps(commands, indent=2)
```

### Testing with Serialization

```python
from ttk.serialization import DrawTextCommand, serialize_command

# Create a command for testing
cmd = DrawTextCommand(
    row=10,
    col=20,
    text="Test",
    color_pair=3,
    attributes=1
)

# Serialize for comparison
serialized = serialize_command(cmd)

# Verify all parameters are captured
assert serialized['row'] == 10
assert serialized['col'] == 20
assert serialized['text'] == "Test"
```

## Design Decisions

### Why Dataclasses?

Dataclasses provide:
- Type hints for all parameters
- Automatic `__init__` generation
- Built-in `asdict()` for easy serialization
- Clear structure and documentation

### Why Dictionary Format?

Dictionaries are:
- Easy to serialize to JSON
- Human-readable when pretty-printed
- Simple to parse and validate
- Compatible with many testing frameworks

### Parameter Completeness

All command parameters are captured in serialization to ensure:
- Commands can be fully reproduced
- No information is lost during serialization
- Testing can verify exact command parameters
- Command sequences can be replayed accurately

## Testing

The implementation includes comprehensive tests in `ttk/test/test_command_serialization.py`:

- **Command Creation Tests**: Verify dataclass creation and structure
- **Serialization Tests**: Verify correct dictionary output
- **Helper Function Tests**: Verify convenience functions work correctly
- **Completeness Tests**: Verify all parameters are captured
- **Edge Case Tests**: Test boundary values, empty strings, Unicode, etc.

All 38 tests pass successfully, providing confidence in the implementation.

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 13.1**: Commands can be serialized to text format (dictionary/JSON)
- **Requirement 13.2**: Serialization includes all parameters needed to reproduce commands
- All drawing operations are supported (draw_text, draw_rect, draw_hline, draw_vline, clear, refresh, etc.)
- Color pair initialization is supported
- Cursor control commands are supported

## Future Enhancements

The serialization system is designed to support future additions:

1. **Command Parsing**: Deserialize dictionaries back to command objects (Task 23)
2. **Pretty Printing**: Human-readable command formatting (Task 24)
3. **Command Recording**: Capture command sequences from live rendering
4. **Command Replay**: Execute recorded command sequences
5. **Command Validation**: Verify command parameters are valid
6. **Command Optimization**: Analyze and optimize command sequences

## Integration with TTK

The serialization module is fully integrated with TTK:

- Exported from `ttk.serialization` package
- Uses TTK's type system (TextAttribute, color pairs, etc.)
- Compatible with all rendering backends
- Independent of backend implementation details

## Conclusion

The command serialization implementation provides a solid foundation for testing, debugging, and analyzing TTK rendering commands. The dictionary-based format is simple, flexible, and easy to work with, while the dataclass-based design ensures type safety and clear documentation.
