"""
TTK Serialization Package

This package provides functionality for serializing and deserializing rendering
commands, enabling testing and debugging of the rendering API independently of
any backend implementation.

Features:
- Command serialization to text format
- Command parsing and reconstruction
- Pretty-printing for debugging
- Command recording and replay
"""

from ttk.serialization.command_serializer import (
    # Command dataclasses
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
    MoveCursorCommand,
    Command,
    # Serialization functions
    serialize_command,
    serialize_draw_text,
    serialize_draw_hline,
    serialize_draw_vline,
    serialize_draw_rect,
    serialize_clear,
    serialize_clear_region,
    serialize_refresh,
    serialize_refresh_region,
    serialize_init_color_pair,
    serialize_set_cursor_visibility,
    serialize_move_cursor,
    # Parsing functions
    parse_command,
    # Pretty-printing functions
    pretty_print_command,
)

__all__ = [
    # Command dataclasses
    'DrawTextCommand',
    'DrawHLineCommand',
    'DrawVLineCommand',
    'DrawRectCommand',
    'ClearCommand',
    'ClearRegionCommand',
    'RefreshCommand',
    'RefreshRegionCommand',
    'InitColorPairCommand',
    'SetCursorVisibilityCommand',
    'MoveCursorCommand',
    'Command',
    # Serialization functions
    'serialize_command',
    'serialize_draw_text',
    'serialize_draw_hline',
    'serialize_draw_vline',
    'serialize_draw_rect',
    'serialize_clear',
    'serialize_clear_region',
    'serialize_refresh',
    'serialize_refresh_region',
    'serialize_init_color_pair',
    'serialize_set_cursor_visibility',
    'serialize_move_cursor',
    # Parsing functions
    'parse_command',
    # Pretty-printing functions
    'pretty_print_command',
]
