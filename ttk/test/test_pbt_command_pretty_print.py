"""
Property-based tests for command pretty-printing.

Feature: desktop-app-mode
Property 11: Pretty-print completeness
Validates: Requirements 13.4

Property: For any rendering command, pretty-printing should produce a 
non-empty string representation without raising exceptions.
"""

from hypothesis import given, strategies as st
from ttk.serialization import (
    DrawTextCommand,
    DrawRectCommand,
    DrawHLineCommand,
    DrawVLineCommand,
    ClearCommand,
    ClearRegionCommand,
    RefreshCommand,
    RefreshRegionCommand,
    InitColorPairCommand,
    SetCursorVisibilityCommand,
    MoveCursorCommand,
    pretty_print_command,
)


# Strategy for generating valid RGB tuples
rgb_strategy = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
)

# Strategy for generating valid coordinates
coord_strategy = st.integers(min_value=0, max_value=1000)

# Strategy for generating valid dimensions
dimension_strategy = st.integers(min_value=1, max_value=1000)

# Strategy for generating valid color pair IDs
color_pair_strategy = st.integers(min_value=0, max_value=255)

# Strategy for generating valid text attributes
attribute_strategy = st.integers(min_value=0, max_value=7)

# Strategy for generating text strings
text_strategy = st.text(min_size=1, max_size=100)

# Strategy for generating single characters
char_strategy = st.characters(min_codepoint=32, max_codepoint=126)


@given(
    row=coord_strategy,
    col=coord_strategy,
    text=text_strategy,
    color_pair=color_pair_strategy,
    attributes=attribute_strategy,
)
def test_pretty_print_draw_text_command(row, col, text, color_pair, attributes):
    """
    Property: Pretty-printing DrawTextCommand produces non-empty string without exceptions.
    """
    cmd = DrawTextCommand(
        row=row, col=col, text=text, color_pair=color_pair, attributes=attributes
    )
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "draw_text" in result


@given(
    row=coord_strategy,
    col=coord_strategy,
    height=dimension_strategy,
    width=dimension_strategy,
    color_pair=color_pair_strategy,
    filled=st.booleans(),
)
def test_pretty_print_draw_rect_command(row, col, height, width, color_pair, filled):
    """
    Property: Pretty-printing DrawRectCommand produces non-empty string without exceptions.
    """
    cmd = DrawRectCommand(
        row=row, col=col, height=height, width=width, color_pair=color_pair, filled=filled
    )
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "draw_rect" in result


@given(
    row=coord_strategy,
    col=coord_strategy,
    char=char_strategy,
    length=dimension_strategy,
    color_pair=color_pair_strategy,
)
def test_pretty_print_draw_hline_command(row, col, char, length, color_pair):
    """
    Property: Pretty-printing DrawHLineCommand produces non-empty string without exceptions.
    """
    cmd = DrawHLineCommand(
        row=row, col=col, char=char, length=length, color_pair=color_pair
    )
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "draw_hline" in result


@given(
    row=coord_strategy,
    col=coord_strategy,
    char=char_strategy,
    length=dimension_strategy,
    color_pair=color_pair_strategy,
)
def test_pretty_print_draw_vline_command(row, col, char, length, color_pair):
    """
    Property: Pretty-printing DrawVLineCommand produces non-empty string without exceptions.
    """
    cmd = DrawVLineCommand(
        row=row, col=col, char=char, length=length, color_pair=color_pair
    )
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "draw_vline" in result


@given(st.none())
def test_pretty_print_clear_command(_):
    """
    Property: Pretty-printing ClearCommand produces non-empty string without exceptions.
    """
    cmd = ClearCommand()
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "clear" in result


@given(
    row=coord_strategy,
    col=coord_strategy,
    height=dimension_strategy,
    width=dimension_strategy,
)
def test_pretty_print_clear_region_command(row, col, height, width):
    """
    Property: Pretty-printing ClearRegionCommand produces non-empty string without exceptions.
    """
    cmd = ClearRegionCommand(row=row, col=col, height=height, width=width)
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "clear_region" in result


@given(st.none())
def test_pretty_print_refresh_command(_):
    """
    Property: Pretty-printing RefreshCommand produces non-empty string without exceptions.
    """
    cmd = RefreshCommand()
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "refresh" in result


@given(
    row=coord_strategy,
    col=coord_strategy,
    height=dimension_strategy,
    width=dimension_strategy,
)
def test_pretty_print_refresh_region_command(row, col, height, width):
    """
    Property: Pretty-printing RefreshRegionCommand produces non-empty string without exceptions.
    """
    cmd = RefreshRegionCommand(row=row, col=col, height=height, width=width)
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "refresh_region" in result


@given(
    pair_id=color_pair_strategy,
    fg_color=rgb_strategy,
    bg_color=rgb_strategy,
)
def test_pretty_print_init_color_pair_command(pair_id, fg_color, bg_color):
    """
    Property: Pretty-printing InitColorPairCommand produces non-empty string without exceptions.
    """
    cmd = InitColorPairCommand(pair_id=pair_id, fg_color=fg_color, bg_color=bg_color)
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "init_color_pair" in result


@given(visible=st.booleans())
def test_pretty_print_set_cursor_visibility_command(visible):
    """
    Property: Pretty-printing SetCursorVisibilityCommand produces non-empty string without exceptions.
    """
    cmd = SetCursorVisibilityCommand(visible=visible)
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "set_cursor_visibility" in result


@given(row=coord_strategy, col=coord_strategy)
def test_pretty_print_move_cursor_command(row, col):
    """
    Property: Pretty-printing MoveCursorCommand produces non-empty string without exceptions.
    """
    cmd = MoveCursorCommand(row=row, col=col)
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "move_cursor" in result


@given(
    row=coord_strategy,
    col=coord_strategy,
    text=text_strategy,
    color_pair=color_pair_strategy,
    attributes=attribute_strategy,
)
def test_pretty_print_serialized_dict(row, col, text, color_pair, attributes):
    """
    Property: Pretty-printing serialized command dict produces non-empty string without exceptions.
    """
    cmd_dict = {
        "type": "draw_text",
        "row": row,
        "col": col,
        "text": text,
        "color_pair": color_pair,
        "attributes": attributes,
    }
    result = pretty_print_command(cmd_dict)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "draw_text" in result
