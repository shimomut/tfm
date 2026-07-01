"""
TTK Command Serializer Module

This module provides functionality for serializing and deserializing rendering
commands. This enables testing and debugging of the rendering API independently
of any backend implementation, as well as recording and replaying command sequences.

The serialization format uses dictionaries that can be easily converted to JSON
or other text formats for storage and transmission.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, Optional, Union


@dataclass
class DrawTextCommand:
    """Represents a draw_text command with all its parameters."""
    command_type: str = "draw_text"
    row: int = 0
    col: int = 0
    text: str = ""
    color_pair: int = 0
    attributes: int = 0


@dataclass
class DrawHLineCommand:
    """Represents a draw_hline command with all its parameters."""
    command_type: str = "draw_hline"
    row: int = 0
    col: int = 0
    char: str = ""
    length: int = 0
    color_pair: int = 0


@dataclass
class DrawVLineCommand:
    """Represents a draw_vline command with all its parameters."""
    command_type: str = "draw_vline"
    row: int = 0
    col: int = 0
    char: str = ""
    length: int = 0
    color_pair: int = 0


@dataclass
class DrawRectCommand:
    """Represents a draw_rect command with all its parameters."""
    command_type: str = "draw_rect"
    row: int = 0
    col: int = 0
    height: int = 0
    width: int = 0
    color_pair: int = 0
    filled: bool = False


@dataclass
class ClearCommand:
    """Represents a clear command."""
    command_type: str = "clear"


@dataclass
class ClearRegionCommand:
    """Represents a clear_region command with all its parameters."""
    command_type: str = "clear_region"
    row: int = 0
    col: int = 0
    height: int = 0
    width: int = 0


@dataclass
class RefreshCommand:
    """Represents a refresh command."""
    command_type: str = "refresh"


@dataclass
class RefreshRegionCommand:
    """Represents a refresh_region command with all its parameters."""
    command_type: str = "refresh_region"
    row: int = 0
    col: int = 0
    height: int = 0
    width: int = 0


@dataclass
class InitColorPairCommand:
    """Represents an init_color_pair command with all its parameters."""
    command_type: str = "init_color_pair"
    pair_id: int = 0
    fg_color: Tuple[int, int, int] = (0, 0, 0)
    bg_color: Tuple[int, int, int] = (0, 0, 0)


@dataclass
class SetCursorVisibilityCommand:
    """Represents a set_cursor_visibility command with all its parameters."""
    command_type: str = "set_cursor_visibility"
    visible: bool = False


@dataclass
class MoveCursorCommand:
    """Represents a move_cursor command with all its parameters."""
    command_type: str = "move_cursor"
    row: int = 0
    col: int = 0


# Type alias for all command types
Command = Union[
    DrawTextCommand,
    DrawHLineCommand,
    DrawVLineCommand,
    DrawRectCommand,
    ClearCommand,
    ClearRegionCommand,
    RefreshCommand,
    RefreshRegionCommand,
    InitColorPairCommand,
    SetCursorVisibilityCommand,
    MoveCursorCommand
]


def serialize_command(command: Command) -> Dict[str, Any]:
    """
    Serialize a rendering command to a dictionary format.
    
    This function converts a command dataclass into a dictionary that can be
    easily serialized to JSON or other text formats. The dictionary includes
    all parameters needed to reproduce the command.
    
    Args:
        command: A command dataclass instance (DrawTextCommand, DrawRectCommand, etc.)
    
    Returns:
        Dict[str, Any]: A dictionary representation of the command with all parameters.
                       The dictionary always includes a 'command_type' field that
                       identifies the type of command.
    
    Example:
        >>> cmd = DrawTextCommand(row=5, col=10, text="Hello", color_pair=1, attributes=3)
        >>> serialized = serialize_command(cmd)
        >>> serialized
        {'command_type': 'draw_text', 'row': 5, 'col': 10, 'text': 'Hello', 
         'color_pair': 1, 'attributes': 3}
    """
    # Convert dataclass to dictionary
    result = asdict(command)
    
    # Ensure command_type is always present
    if 'command_type' not in result:
        result['command_type'] = command.command_type
    
    return result


def serialize_draw_text(row: int, col: int, text: str, 
                       color_pair: int = 0, attributes: int = 0) -> Dict[str, Any]:
    """
    Serialize a draw_text command.
    
    Args:
        row: Row position
        col: Column position
        text: Text to draw
        color_pair: Color pair index (0-255)
        attributes: Bitwise OR of TextAttribute values
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = DrawTextCommand(
        row=row,
        col=col,
        text=text,
        color_pair=color_pair,
        attributes=attributes
    )
    return serialize_command(cmd)


def serialize_draw_hline(row: int, col: int, char: str, 
                        length: int, color_pair: int = 0) -> Dict[str, Any]:
    """
    Serialize a draw_hline command.
    
    Args:
        row: Row position
        col: Starting column position
        char: Character to use for the line
        length: Length in characters
        color_pair: Color pair index (0-255)
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = DrawHLineCommand(
        row=row,
        col=col,
        char=char,
        length=length,
        color_pair=color_pair
    )
    return serialize_command(cmd)


def serialize_draw_vline(row: int, col: int, char: str, 
                        length: int, color_pair: int = 0) -> Dict[str, Any]:
    """
    Serialize a draw_vline command.
    
    Args:
        row: Starting row position
        col: Column position
        char: Character to use for the line
        length: Length in characters
        color_pair: Color pair index (0-255)
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = DrawVLineCommand(
        row=row,
        col=col,
        char=char,
        length=length,
        color_pair=color_pair
    )
    return serialize_command(cmd)


def serialize_draw_rect(row: int, col: int, height: int, width: int,
                       color_pair: int = 0, filled: bool = False) -> Dict[str, Any]:
    """
    Serialize a draw_rect command.
    
    Args:
        row: Top-left row position
        col: Top-left column position
        height: Height in character rows
        width: Width in character columns
        color_pair: Color pair index (0-255)
        filled: Whether to fill the rectangle
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = DrawRectCommand(
        row=row,
        col=col,
        height=height,
        width=width,
        color_pair=color_pair,
        filled=filled
    )
    return serialize_command(cmd)


def serialize_clear() -> Dict[str, Any]:
    """
    Serialize a clear command.
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = ClearCommand()
    return serialize_command(cmd)


def serialize_clear_region(row: int, col: int, height: int, width: int) -> Dict[str, Any]:
    """
    Serialize a clear_region command.
    
    Args:
        row: Starting row position
        col: Starting column position
        height: Height in character rows
        width: Width in character columns
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = ClearRegionCommand(
        row=row,
        col=col,
        height=height,
        width=width
    )
    return serialize_command(cmd)


def serialize_refresh() -> Dict[str, Any]:
    """
    Serialize a refresh command.
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = RefreshCommand()
    return serialize_command(cmd)


def serialize_refresh_region(row: int, col: int, height: int, width: int) -> Dict[str, Any]:
    """
    Serialize a refresh_region command.
    
    Args:
        row: Starting row position
        col: Starting column position
        height: Height in character rows
        width: Width in character columns
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = RefreshRegionCommand(
        row=row,
        col=col,
        height=height,
        width=width
    )
    return serialize_command(cmd)


def serialize_init_color_pair(pair_id: int, fg_color: Tuple[int, int, int],
                              bg_color: Tuple[int, int, int]) -> Dict[str, Any]:
    """
    Serialize an init_color_pair command.
    
    Args:
        pair_id: Color pair index (1-255)
        fg_color: Foreground color as (R, G, B) tuple
        bg_color: Background color as (R, G, B) tuple
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = InitColorPairCommand(
        pair_id=pair_id,
        fg_color=fg_color,
        bg_color=bg_color
    )
    return serialize_command(cmd)


def serialize_set_cursor_visibility(visible: bool) -> Dict[str, Any]:
    """
    Serialize a set_cursor_visibility command.
    
    Args:
        visible: Whether the cursor should be visible
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = SetCursorVisibilityCommand(visible=visible)
    return serialize_command(cmd)


def serialize_move_cursor(row: int, col: int) -> Dict[str, Any]:
    """
    Serialize a move_cursor command.
    
    Args:
        row: Row position
        col: Column position
    
    Returns:
        Dict[str, Any]: Serialized command dictionary
    """
    cmd = MoveCursorCommand(row=row, col=col)
    return serialize_command(cmd)


def parse_command(data: Dict[str, Any]) -> Command:
    """
    Parse a serialized command dictionary back into a command dataclass.
    
    This function validates the command structure and parameters, then
    reconstructs the appropriate command dataclass instance.
    
    Args:
        data: Dictionary containing serialized command data. Must include
              a 'command_type' field identifying the command type.
    
    Returns:
        Command: The reconstructed command dataclass instance
    
    Raises:
        ValueError: If the command structure is invalid, command_type is missing
                   or unknown, or required parameters are missing/invalid
        TypeError: If parameter types are incorrect
    
    Example:
        >>> data = {'command_type': 'draw_text', 'row': 5, 'col': 10, 
        ...         'text': 'Hello', 'color_pair': 1, 'attributes': 3}
        >>> cmd = parse_command(data)
        >>> isinstance(cmd, DrawTextCommand)
        True
        >>> cmd.text
        'Hello'
    """
    # Validate input is a dictionary
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data).__name__}")
    
    # Validate command_type field exists
    if 'command_type' not in data:
        raise ValueError("Missing required field 'command_type'")
    
    command_type = data['command_type']
    
    # Parse based on command type
    if command_type == 'draw_text':
        return _parse_draw_text(data)
    elif command_type == 'draw_hline':
        return _parse_draw_hline(data)
    elif command_type == 'draw_vline':
        return _parse_draw_vline(data)
    elif command_type == 'draw_rect':
        return _parse_draw_rect(data)
    elif command_type == 'clear':
        return _parse_clear(data)
    elif command_type == 'clear_region':
        return _parse_clear_region(data)
    elif command_type == 'refresh':
        return _parse_refresh(data)
    elif command_type == 'refresh_region':
        return _parse_refresh_region(data)
    elif command_type == 'init_color_pair':
        return _parse_init_color_pair(data)
    elif command_type == 'set_cursor_visibility':
        return _parse_set_cursor_visibility(data)
    elif command_type == 'move_cursor':
        return _parse_move_cursor(data)
    else:
        raise ValueError(f"Unknown command_type: {command_type}")


def _parse_draw_text(data: Dict[str, Any]) -> DrawTextCommand:
    """Parse a draw_text command from dictionary."""
    _validate_required_fields(data, ['row', 'col', 'text'])
    _validate_field_type(data, 'row', int)
    _validate_field_type(data, 'col', int)
    _validate_field_type(data, 'text', str)
    _validate_field_type(data, 'color_pair', int, default=0)
    _validate_field_type(data, 'attributes', int, default=0)
    
    return DrawTextCommand(
        row=data['row'],
        col=data['col'],
        text=data['text'],
        color_pair=data.get('color_pair', 0),
        attributes=data.get('attributes', 0)
    )


def _parse_draw_hline(data: Dict[str, Any]) -> DrawHLineCommand:
    """Parse a draw_hline command from dictionary."""
    _validate_required_fields(data, ['row', 'col', 'char', 'length'])
    _validate_field_type(data, 'row', int)
    _validate_field_type(data, 'col', int)
    _validate_field_type(data, 'char', str)
    _validate_field_type(data, 'length', int)
    _validate_field_type(data, 'color_pair', int, default=0)
    
    return DrawHLineCommand(
        row=data['row'],
        col=data['col'],
        char=data['char'],
        length=data['length'],
        color_pair=data.get('color_pair', 0)
    )


def _parse_draw_vline(data: Dict[str, Any]) -> DrawVLineCommand:
    """Parse a draw_vline command from dictionary."""
    _validate_required_fields(data, ['row', 'col', 'char', 'length'])
    _validate_field_type(data, 'row', int)
    _validate_field_type(data, 'col', int)
    _validate_field_type(data, 'char', str)
    _validate_field_type(data, 'length', int)
    _validate_field_type(data, 'color_pair', int, default=0)
    
    return DrawVLineCommand(
        row=data['row'],
        col=data['col'],
        char=data['char'],
        length=data['length'],
        color_pair=data.get('color_pair', 0)
    )


def _parse_draw_rect(data: Dict[str, Any]) -> DrawRectCommand:
    """Parse a draw_rect command from dictionary."""
    _validate_required_fields(data, ['row', 'col', 'height', 'width'])
    _validate_field_type(data, 'row', int)
    _validate_field_type(data, 'col', int)
    _validate_field_type(data, 'height', int)
    _validate_field_type(data, 'width', int)
    _validate_field_type(data, 'color_pair', int, default=0)
    _validate_field_type(data, 'filled', bool, default=False)
    
    return DrawRectCommand(
        row=data['row'],
        col=data['col'],
        height=data['height'],
        width=data['width'],
        color_pair=data.get('color_pair', 0),
        filled=data.get('filled', False)
    )


def _parse_clear(data: Dict[str, Any]) -> ClearCommand:
    """Parse a clear command from dictionary."""
    return ClearCommand()


def _parse_clear_region(data: Dict[str, Any]) -> ClearRegionCommand:
    """Parse a clear_region command from dictionary."""
    _validate_required_fields(data, ['row', 'col', 'height', 'width'])
    _validate_field_type(data, 'row', int)
    _validate_field_type(data, 'col', int)
    _validate_field_type(data, 'height', int)
    _validate_field_type(data, 'width', int)
    
    return ClearRegionCommand(
        row=data['row'],
        col=data['col'],
        height=data['height'],
        width=data['width']
    )


def _parse_refresh(data: Dict[str, Any]) -> RefreshCommand:
    """Parse a refresh command from dictionary."""
    return RefreshCommand()


def _parse_refresh_region(data: Dict[str, Any]) -> RefreshRegionCommand:
    """Parse a refresh_region command from dictionary."""
    _validate_required_fields(data, ['row', 'col', 'height', 'width'])
    _validate_field_type(data, 'row', int)
    _validate_field_type(data, 'col', int)
    _validate_field_type(data, 'height', int)
    _validate_field_type(data, 'width', int)
    
    return RefreshRegionCommand(
        row=data['row'],
        col=data['col'],
        height=data['height'],
        width=data['width']
    )


def _parse_init_color_pair(data: Dict[str, Any]) -> InitColorPairCommand:
    """Parse an init_color_pair command from dictionary."""
    _validate_required_fields(data, ['pair_id', 'fg_color', 'bg_color'])
    _validate_field_type(data, 'pair_id', int)
    
    # Validate color tuples
    fg_color = data['fg_color']
    bg_color = data['bg_color']
    
    if not isinstance(fg_color, (list, tuple)) or len(fg_color) != 3:
        raise ValueError("fg_color must be a 3-element tuple/list")
    if not isinstance(bg_color, (list, tuple)) or len(bg_color) != 3:
        raise ValueError("bg_color must be a 3-element tuple/list")
    
    if not all(isinstance(x, int) for x in fg_color):
        raise TypeError("fg_color elements must be integers")
    if not all(isinstance(x, int) for x in bg_color):
        raise TypeError("bg_color elements must be integers")
    
    return InitColorPairCommand(
        pair_id=data['pair_id'],
        fg_color=tuple(fg_color),
        bg_color=tuple(bg_color)
    )


def _parse_set_cursor_visibility(data: Dict[str, Any]) -> SetCursorVisibilityCommand:
    """Parse a set_cursor_visibility command from dictionary."""
    _validate_required_fields(data, ['visible'])
    _validate_field_type(data, 'visible', bool)
    
    return SetCursorVisibilityCommand(visible=data['visible'])


def _parse_move_cursor(data: Dict[str, Any]) -> MoveCursorCommand:
    """Parse a move_cursor command from dictionary."""
    _validate_required_fields(data, ['row', 'col'])
    _validate_field_type(data, 'row', int)
    _validate_field_type(data, 'col', int)
    
    return MoveCursorCommand(
        row=data['row'],
        col=data['col']
    )


def _validate_required_fields(data: Dict[str, Any], fields: list) -> None:
    """
    Validate that all required fields are present in the data dictionary.
    
    Args:
        data: Dictionary to validate
        fields: List of required field names
    
    Raises:
        ValueError: If any required field is missing
    """
    missing = [field for field in fields if field not in data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def _validate_field_type(data: Dict[str, Any], field: str, 
                        expected_type: type, default: Any = None) -> None:
    """
    Validate that a field has the expected type.
    
    Args:
        data: Dictionary containing the field
        field: Field name to validate
        expected_type: Expected type for the field
        default: Default value if field is optional (None means required)
    
    Raises:
        TypeError: If the field has the wrong type
    """
    if field not in data:
        if default is None:
            return  # Field is optional and not present
        return  # Will use default value
    
    value = data[field]
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Field '{field}' must be {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )


def pretty_print_command(command: Union[Command, Dict[str, Any]], indent: int = 0) -> str:
    """
    Format a rendering command in a human-readable way for debugging.
    
    This function takes either a command dataclass or a serialized command dictionary
    and formats it with indentation and parameter names for easy reading. This is
    useful for debugging, logging, and understanding command sequences.
    
    Args:
        command: A command dataclass instance or serialized command dictionary
        indent: Number of spaces to indent the output (default: 0)
    
    Returns:
        str: A formatted, human-readable string representation of the command
    
    Example:
        >>> cmd = DrawTextCommand(row=5, col=10, text="Hello", color_pair=1, attributes=3)
        >>> print(pretty_print_command(cmd))
        draw_text:
          row: 5
          col: 10
          text: "Hello"
          color_pair: 1
          attributes: 3
        
        >>> data = {'command_type': 'draw_rect', 'row': 0, 'col': 0, 
        ...         'height': 10, 'width': 20, 'color_pair': 2, 'filled': True}
        >>> print(pretty_print_command(data))
        draw_rect:
          row: 0
          col: 0
          height: 10
          width: 20
          color_pair: 2
          filled: True
    """
    # Convert command to dictionary if it's a dataclass
    if isinstance(command, dict):
        data = command
    else:
        data = serialize_command(command)
    
    # Get command type
    command_type = data.get('command_type', 'unknown')
    
    # Start with command type
    indent_str = ' ' * indent
    lines = [f"{indent_str}{command_type}:"]
    
    # Add parameters with indentation
    param_indent = ' ' * (indent + 2)
    
    # Sort parameters for consistent output (command_type first, then alphabetically)
    params = [(k, v) for k, v in data.items() if k != 'command_type']
    params.sort(key=lambda x: x[0])
    
    for key, value in params:
        formatted_value = _format_value(value)
        lines.append(f"{param_indent}{key}: {formatted_value}")
    
    return '\n'.join(lines)


def _format_value(value: Any) -> str:
    """
    Format a parameter value for pretty printing.
    
    Args:
        value: The value to format
    
    Returns:
        str: Formatted string representation of the value
    """
    if isinstance(value, str):
        # Quote strings for clarity
        return f'"{value}"'
    elif isinstance(value, bool):
        # Use lowercase for booleans
        return str(value).lower()
    elif isinstance(value, (tuple, list)):
        # Format tuples/lists as comma-separated values in parentheses
        if len(value) == 3 and all(isinstance(x, int) for x in value):
            # Special formatting for RGB color tuples
            return f"({value[0]}, {value[1]}, {value[2]})"
        else:
            return f"({', '.join(str(v) for v in value)})"
    else:
        # Default string representation
        return str(value)
