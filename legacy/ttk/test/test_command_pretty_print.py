"""
Tests for command pretty-printing functionality.

This module tests the pretty_print_command function to ensure it formats
commands in a human-readable way with proper indentation and parameter names.
"""

from ttk.serialization import (
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
    pretty_print_command,
    serialize_command
)


def test_pretty_print_draw_text():
    """Test pretty printing of draw_text command."""
    cmd = DrawTextCommand(
        row=5,
        col=10,
        text="Hello World",
        color_pair=1,
        attributes=3
    )
    
    result = pretty_print_command(cmd)
    
    # Check that output contains command type
    assert "draw_text:" in result
    
    # Check that all parameters are present
    assert "row: 5" in result
    assert "col: 10" in result
    assert 'text: "Hello World"' in result
    assert "color_pair: 1" in result
    assert "attributes: 3" in result
    
    # Check indentation (parameters should be indented)
    lines = result.split('\n')
    assert lines[0] == "draw_text:"
    assert lines[1].startswith("  ")  # Parameters indented by 2 spaces
    
    print("✓ test_pretty_print_draw_text passed")


def test_pretty_print_draw_rect():
    """Test pretty printing of draw_rect command."""
    cmd = DrawRectCommand(
        row=0,
        col=0,
        height=10,
        width=20,
        color_pair=2,
        filled=True
    )
    
    result = pretty_print_command(cmd)
    
    assert "draw_rect:" in result
    assert "row: 0" in result
    assert "col: 0" in result
    assert "height: 10" in result
    assert "width: 20" in result
    assert "color_pair: 2" in result
    assert "filled: true" in result  # Boolean should be lowercase
    
    print("✓ test_pretty_print_draw_rect passed")


def test_pretty_print_init_color_pair():
    """Test pretty printing of init_color_pair command with RGB tuples."""
    cmd = InitColorPairCommand(
        pair_id=5,
        fg_color=(255, 128, 0),
        bg_color=(0, 0, 0)
    )
    
    result = pretty_print_command(cmd)
    
    assert "init_color_pair:" in result
    assert "pair_id: 5" in result
    assert "bg_color: (0, 0, 0)" in result
    assert "fg_color: (255, 128, 0)" in result
    
    print("✓ test_pretty_print_init_color_pair passed")


def test_pretty_print_clear():
    """Test pretty printing of clear command (no parameters)."""
    cmd = ClearCommand()
    
    result = pretty_print_command(cmd)
    
    assert "clear:" in result
    # Clear command has no parameters, so should just be the command type
    lines = result.split('\n')
    assert len(lines) == 1
    
    print("✓ test_pretty_print_clear passed")


def test_pretty_print_from_dict():
    """Test pretty printing from a serialized dictionary."""
    data = {
        'command_type': 'draw_hline',
        'row': 3,
        'col': 5,
        'char': '-',
        'length': 15,
        'color_pair': 1
    }
    
    result = pretty_print_command(data)
    
    assert "draw_hline:" in result
    assert "row: 3" in result
    assert "col: 5" in result
    assert 'char: "-"' in result
    assert "length: 15" in result
    assert "color_pair: 1" in result
    
    print("✓ test_pretty_print_from_dict passed")


def test_pretty_print_with_indent():
    """Test pretty printing with custom indentation."""
    cmd = MoveCursorCommand(row=10, col=20)
    
    result = pretty_print_command(cmd, indent=4)
    
    # Command type should be indented by 4 spaces
    assert result.startswith("    move_cursor:")
    
    # Parameters should be indented by 6 spaces (4 + 2)
    lines = result.split('\n')
    for line in lines[1:]:
        assert line.startswith("      ")
    
    print("✓ test_pretty_print_with_indent passed")


def test_pretty_print_all_command_types():
    """Test pretty printing for all command types."""
    commands = [
        DrawTextCommand(row=1, col=2, text="test", color_pair=0, attributes=0),
        DrawHLineCommand(row=3, col=4, char='-', length=10, color_pair=0),
        DrawVLineCommand(row=5, col=6, char='|', length=8, color_pair=0),
        DrawRectCommand(row=7, col=8, height=5, width=10, color_pair=0, filled=False),
        ClearCommand(),
        ClearRegionCommand(row=9, col=10, height=3, width=4),
        RefreshCommand(),
        RefreshRegionCommand(row=11, col=12, height=2, width=3),
        InitColorPairCommand(pair_id=1, fg_color=(255, 255, 255), bg_color=(0, 0, 0)),
        SetCursorVisibilityCommand(visible=True),
        MoveCursorCommand(row=13, col=14)
    ]
    
    for cmd in commands:
        result = pretty_print_command(cmd)
        # Each command should produce non-empty output
        assert len(result) > 0
        # Each command should have its command type
        assert cmd.command_type in result
    
    print("✓ test_pretty_print_all_command_types passed")


def test_pretty_print_special_characters():
    """Test pretty printing with special characters in text."""
    cmd = DrawTextCommand(
        row=0,
        col=0,
        text='Text with "quotes" and\nnewlines',
        color_pair=0,
        attributes=0
    )
    
    result = pretty_print_command(cmd)
    
    # Text should be quoted
    assert 'text: "' in result
    
    print("✓ test_pretty_print_special_characters passed")


def test_pretty_print_consistency():
    """Test that pretty printing is consistent with serialization."""
    cmd = DrawRectCommand(
        row=5,
        col=10,
        height=15,
        width=20,
        color_pair=3,
        filled=True
    )
    
    # Pretty print from command
    result1 = pretty_print_command(cmd)
    
    # Pretty print from serialized dictionary
    serialized = serialize_command(cmd)
    result2 = pretty_print_command(serialized)
    
    # Both should produce the same output
    assert result1 == result2
    
    print("✓ test_pretty_print_consistency passed")


def run_all_tests():
    """Run all pretty print tests."""
    print("\nRunning command pretty-printing tests...")
    print("=" * 60)
    
    test_pretty_print_draw_text()
    test_pretty_print_draw_rect()
    test_pretty_print_init_color_pair()
    test_pretty_print_clear()
    test_pretty_print_from_dict()
    test_pretty_print_with_indent()
    test_pretty_print_all_command_types()
    test_pretty_print_special_characters()
    test_pretty_print_consistency()
    
    print("=" * 60)
    print("All pretty-printing tests passed! ✓")


if __name__ == '__main__':
    run_all_tests()
