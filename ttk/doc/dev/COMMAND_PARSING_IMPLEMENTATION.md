# Command Parsing Implementation

## Overview

This document describes the implementation of command parsing functionality in the TTK library. Command parsing is the inverse operation of command serialization - it reconstructs command dataclass instances from dictionary representations.

## Purpose

Command parsing enables:
- **Testing**: Reconstruct commands from test data for verification
- **Debugging**: Parse commands from log files or debug output
- **Recording/Replay**: Reconstruct command sequences from stored data
- **Network Communication**: Receive commands over network connections
- **Configuration**: Load command sequences from configuration files

## Architecture

### Core Function

The main entry point is `parse_command()`:

```python
def parse_command(data: Dict[str, Any]) -> Command:
    """
    Parse a serialized command dictionary back into a command dataclass.
    
    Validates structure and parameters, then reconstructs the appropriate
    command dataclass instance.
    """
```

### Command-Specific Parsers

Each command type has a dedicated parser function:

- `_parse_draw_text()` - Parse draw_text commands
- `_parse_draw_hline()` - Parse draw_hline commands
- `_parse_draw_vline()` - Parse draw_vline commands
- `_parse_draw_rect()` - Parse draw_rect commands
- `_parse_clear()` - Parse clear commands
- `_parse_clear_region()` - Parse clear_region commands
- `_parse_refresh()` - Parse refresh commands
- `_parse_refresh_region()` - Parse refresh_region commands
- `_parse_init_color_pair()` - Parse init_color_pair commands
- `_parse_set_cursor_visibility()` - Parse set_cursor_visibility commands
- `_parse_move_cursor()` - Parse move_cursor commands

### Validation Helpers

Two helper functions provide validation:

```python
def _validate_required_fields(data: Dict[str, Any], fields: list) -> None:
    """Validate that all required fields are present."""

def _validate_field_type(data: Dict[str, Any], field: str, 
                        expected_type: type, default: Any = None) -> None:
    """Validate that a field has the expected type."""
```

## Implementation Details

### Parsing Flow

1. **Input Validation**: Verify input is a dictionary
2. **Command Type Extraction**: Get and validate `command_type` field
3. **Dispatch**: Route to appropriate command-specific parser
4. **Field Validation**: Validate required fields and types
5. **Construction**: Create and return command dataclass instance

### Error Handling

The parser raises specific exceptions for different error conditions:

- `TypeError`: Input is not a dictionary, or field has wrong type
- `ValueError`: Missing `command_type`, unknown command type, missing required fields, or invalid field values

### Type Coercion

The parser handles some type coercion for compatibility:

- **Color tuples**: Accepts both lists and tuples, converts to tuples
  - JSON arrays become lists, so this enables JSON compatibility
  - Example: `[255, 0, 0]` → `(255, 0, 0)`

### Optional Fields

Optional fields are handled with default values:

```python
# Example: color_pair is optional, defaults to 0
color_pair=data.get('color_pair', 0)
```

## Command-Specific Details

### DrawTextCommand

Required fields:
- `row` (int): Row position
- `col` (int): Column position
- `text` (str): Text to draw

Optional fields:
- `color_pair` (int): Color pair index (default: 0)
- `attributes` (int): Text attributes (default: 0)

### DrawHLineCommand / DrawVLineCommand

Required fields:
- `row` (int): Row position
- `col` (int): Column position
- `char` (str): Character to use
- `length` (int): Length in characters

Optional fields:
- `color_pair` (int): Color pair index (default: 0)

### DrawRectCommand

Required fields:
- `row` (int): Top-left row
- `col` (int): Top-left column
- `height` (int): Height in rows
- `width` (int): Width in columns

Optional fields:
- `color_pair` (int): Color pair index (default: 0)
- `filled` (bool): Whether to fill (default: False)

### ClearCommand / RefreshCommand

No required fields (command type only).

### ClearRegionCommand / RefreshRegionCommand

Required fields:
- `row` (int): Starting row
- `col` (int): Starting column
- `height` (int): Height in rows
- `width` (int): Width in columns

### InitColorPairCommand

Required fields:
- `pair_id` (int): Color pair index
- `fg_color` (tuple/list): Foreground RGB as 3-element tuple/list
- `bg_color` (tuple/list): Background RGB as 3-element tuple/list

Special validation:
- Colors must be 3-element sequences
- All color elements must be integers
- Lists are converted to tuples

### SetCursorVisibilityCommand

Required fields:
- `visible` (bool): Whether cursor should be visible

### MoveCursorCommand

Required fields:
- `row` (int): Row position
- `col` (int): Column position

## Usage Examples

### Basic Parsing

```python
from ttk.serialization import parse_command

# Parse a draw_text command
data = {
    'command_type': 'draw_text',
    'row': 5,
    'col': 10,
    'text': 'Hello',
    'color_pair': 1
}
cmd = parse_command(data)
# Returns: DrawTextCommand(row=5, col=10, text='Hello', color_pair=1, attributes=0)
```

### Error Handling

```python
try:
    cmd = parse_command(data)
except ValueError as e:
    print(f"Invalid command structure: {e}")
except TypeError as e:
    print(f"Invalid field type: {e}")
```

### Round-Trip Serialization

```python
from ttk.serialization import serialize_command, parse_command

# Create command
original = DrawTextCommand(row=5, col=10, text='Hello')

# Serialize
serialized = serialize_command(original)

# Parse back
parsed = parse_command(serialized)

# Verify
assert parsed == original
```

### JSON Compatibility

```python
import json
from ttk.serialization import serialize_command, parse_command

# Serialize to JSON
cmd = DrawRectCommand(row=10, col=20, height=5, width=15)
json_str = json.dumps(serialize_command(cmd))

# Parse from JSON
data = json.loads(json_str)
parsed = parse_command(data)
```

## Testing

The parsing implementation is tested in `ttk/test/test_command_parsing.py`:

- **27 test cases** covering all command types
- **Validation tests** for error conditions
- **Round-trip tests** verifying serialize → parse → serialize
- **Type coercion tests** for color tuples (list vs tuple)

Test coverage: 88% of command_serializer.py (parsing code is fully covered)

## Design Decisions

### Why Separate Parser Functions?

Each command type has its own parser function for:
- **Clarity**: Easy to understand what each parser does
- **Maintainability**: Easy to modify parsing for specific commands
- **Testability**: Easy to test each parser independently
- **Error Messages**: Can provide command-specific error messages

### Why Validation Helpers?

The validation helper functions provide:
- **Consistency**: Same validation logic across all parsers
- **Reusability**: Avoid code duplication
- **Clear Error Messages**: Standardized error reporting
- **Easy Maintenance**: Single place to update validation logic

### Why Type Coercion for Colors?

Color tuple coercion (list → tuple) enables:
- **JSON Compatibility**: JSON arrays become Python lists
- **Flexibility**: Accept both lists and tuples from users
- **Consistency**: Always return tuples for predictable behavior

## Performance Considerations

- **Validation Overhead**: Each field is validated, adding some overhead
- **Type Checking**: Uses `isinstance()` which is fast in Python
- **Dictionary Access**: Uses `dict.get()` for optional fields (efficient)
- **No Regex**: Avoids expensive regular expression matching

For typical use cases (parsing hundreds of commands), performance is excellent.

## Future Enhancements

Potential improvements for future versions:

1. **Schema Validation**: Use JSON Schema for more comprehensive validation
2. **Batch Parsing**: Parse multiple commands in one call
3. **Streaming Parser**: Parse commands from streams (files, network)
4. **Custom Validators**: Allow users to register custom validation functions
5. **Performance Optimization**: Cache validation results for repeated parsing

## Related Documentation

- [Command Serialization Implementation](COMMAND_SERIALIZATION_IMPLEMENTATION.md) - Serialization counterpart
- [TTK API Reference](../API_REFERENCE.md) - Public API documentation
- [Backend Implementation Guide](../BACKEND_IMPLEMENTATION_GUIDE.md) - How backends use commands

## Requirements Satisfied

This implementation satisfies:
- **Requirement 13.3**: Command parsing and reconstruction from serialized format
