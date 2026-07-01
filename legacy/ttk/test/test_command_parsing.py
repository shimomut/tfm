"""
Tests for TTK command parsing functionality.

This module tests the parse_command() function and all command-specific
parsing functions to ensure they correctly reconstruct commands from
serialized dictionaries and properly validate input.
"""

import pytest
from ttk.serialization import (
    parse_command,
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
)


class TestParseDrawText:
    """Tests for parsing draw_text commands."""
    
    def test_parse_draw_text_minimal(self):
        """Test parsing draw_text with minimal required fields."""
        data = {
            'command_type': 'draw_text',
            'row': 5,
            'col': 10,
            'text': 'Hello'
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, DrawTextCommand)
        assert cmd.row == 5
        assert cmd.col == 10
        assert cmd.text == 'Hello'
        assert cmd.color_pair == 0
        assert cmd.attributes == 0
    
    def test_parse_draw_text_full(self):
        """Test parsing draw_text with all fields."""
        data = {
            'command_type': 'draw_text',
            'row': 5,
            'col': 10,
            'text': 'Hello',
            'color_pair': 3,
            'attributes': 7
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, DrawTextCommand)
        assert cmd.row == 5
        assert cmd.col == 10
        assert cmd.text == 'Hello'
        assert cmd.color_pair == 3
        assert cmd.attributes == 7
    
    def test_parse_draw_text_missing_row(self):
        """Test that missing row field raises ValueError."""
        data = {
            'command_type': 'draw_text',
            'col': 10,
            'text': 'Hello'
        }
        with pytest.raises(ValueError, match="Missing required fields: row"):
            parse_command(data)
    
    def test_parse_draw_text_wrong_type(self):
        """Test that wrong field type raises TypeError."""
        data = {
            'command_type': 'draw_text',
            'row': '5',  # Should be int
            'col': 10,
            'text': 'Hello'
        }
        with pytest.raises(TypeError, match="Field 'row' must be int"):
            parse_command(data)


class TestParseDrawHLine:
    """Tests for parsing draw_hline commands."""
    
    def test_parse_draw_hline_minimal(self):
        """Test parsing draw_hline with minimal fields."""
        data = {
            'command_type': 'draw_hline',
            'row': 3,
            'col': 5,
            'char': '-',
            'length': 10
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, DrawHLineCommand)
        assert cmd.row == 3
        assert cmd.col == 5
        assert cmd.char == '-'
        assert cmd.length == 10
        assert cmd.color_pair == 0
    
    def test_parse_draw_hline_full(self):
        """Test parsing draw_hline with all fields."""
        data = {
            'command_type': 'draw_hline',
            'row': 3,
            'col': 5,
            'char': '-',
            'length': 10,
            'color_pair': 2
        }
        cmd = parse_command(data)
        
        assert cmd.color_pair == 2


class TestParseDrawVLine:
    """Tests for parsing draw_vline commands."""
    
    def test_parse_draw_vline_minimal(self):
        """Test parsing draw_vline with minimal fields."""
        data = {
            'command_type': 'draw_vline',
            'row': 3,
            'col': 5,
            'char': '|',
            'length': 10
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, DrawVLineCommand)
        assert cmd.row == 3
        assert cmd.col == 5
        assert cmd.char == '|'
        assert cmd.length == 10
        assert cmd.color_pair == 0


class TestParseDrawRect:
    """Tests for parsing draw_rect commands."""
    
    def test_parse_draw_rect_minimal(self):
        """Test parsing draw_rect with minimal fields."""
        data = {
            'command_type': 'draw_rect',
            'row': 2,
            'col': 3,
            'height': 5,
            'width': 10
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, DrawRectCommand)
        assert cmd.row == 2
        assert cmd.col == 3
        assert cmd.height == 5
        assert cmd.width == 10
        assert cmd.color_pair == 0
        assert cmd.filled is False
    
    def test_parse_draw_rect_filled(self):
        """Test parsing draw_rect with filled=True."""
        data = {
            'command_type': 'draw_rect',
            'row': 2,
            'col': 3,
            'height': 5,
            'width': 10,
            'filled': True
        }
        cmd = parse_command(data)
        
        assert cmd.filled is True


class TestParseClear:
    """Tests for parsing clear commands."""
    
    def test_parse_clear(self):
        """Test parsing clear command."""
        data = {'command_type': 'clear'}
        cmd = parse_command(data)
        
        assert isinstance(cmd, ClearCommand)


class TestParseClearRegion:
    """Tests for parsing clear_region commands."""
    
    def test_parse_clear_region(self):
        """Test parsing clear_region command."""
        data = {
            'command_type': 'clear_region',
            'row': 5,
            'col': 10,
            'height': 3,
            'width': 20
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, ClearRegionCommand)
        assert cmd.row == 5
        assert cmd.col == 10
        assert cmd.height == 3
        assert cmd.width == 20


class TestParseRefresh:
    """Tests for parsing refresh commands."""
    
    def test_parse_refresh(self):
        """Test parsing refresh command."""
        data = {'command_type': 'refresh'}
        cmd = parse_command(data)
        
        assert isinstance(cmd, RefreshCommand)


class TestParseRefreshRegion:
    """Tests for parsing refresh_region commands."""
    
    def test_parse_refresh_region(self):
        """Test parsing refresh_region command."""
        data = {
            'command_type': 'refresh_region',
            'row': 5,
            'col': 10,
            'height': 3,
            'width': 20
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, RefreshRegionCommand)
        assert cmd.row == 5
        assert cmd.col == 10
        assert cmd.height == 3
        assert cmd.width == 20


class TestParseInitColorPair:
    """Tests for parsing init_color_pair commands."""
    
    def test_parse_init_color_pair_tuple(self):
        """Test parsing init_color_pair with tuple colors."""
        data = {
            'command_type': 'init_color_pair',
            'pair_id': 5,
            'fg_color': (255, 128, 64),
            'bg_color': (0, 0, 0)
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, InitColorPairCommand)
        assert cmd.pair_id == 5
        assert cmd.fg_color == (255, 128, 64)
        assert cmd.bg_color == (0, 0, 0)
    
    def test_parse_init_color_pair_list(self):
        """Test parsing init_color_pair with list colors."""
        data = {
            'command_type': 'init_color_pair',
            'pair_id': 5,
            'fg_color': [255, 128, 64],
            'bg_color': [0, 0, 0]
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, InitColorPairCommand)
        assert cmd.pair_id == 5
        assert cmd.fg_color == (255, 128, 64)
        assert cmd.bg_color == (0, 0, 0)
    
    def test_parse_init_color_pair_invalid_fg_length(self):
        """Test that invalid fg_color length raises ValueError."""
        data = {
            'command_type': 'init_color_pair',
            'pair_id': 5,
            'fg_color': (255, 128),  # Only 2 elements
            'bg_color': (0, 0, 0)
        }
        with pytest.raises(ValueError, match="fg_color must be a 3-element"):
            parse_command(data)
    
    def test_parse_init_color_pair_invalid_fg_type(self):
        """Test that invalid fg_color element type raises TypeError."""
        data = {
            'command_type': 'init_color_pair',
            'pair_id': 5,
            'fg_color': (255, '128', 64),  # String element
            'bg_color': (0, 0, 0)
        }
        with pytest.raises(TypeError, match="fg_color elements must be integers"):
            parse_command(data)


class TestParseSetCursorVisibility:
    """Tests for parsing set_cursor_visibility commands."""
    
    def test_parse_set_cursor_visibility_true(self):
        """Test parsing set_cursor_visibility with visible=True."""
        data = {
            'command_type': 'set_cursor_visibility',
            'visible': True
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, SetCursorVisibilityCommand)
        assert cmd.visible is True
    
    def test_parse_set_cursor_visibility_false(self):
        """Test parsing set_cursor_visibility with visible=False."""
        data = {
            'command_type': 'set_cursor_visibility',
            'visible': False
        }
        cmd = parse_command(data)
        
        assert cmd.visible is False


class TestParseMoveCursor:
    """Tests for parsing move_cursor commands."""
    
    def test_parse_move_cursor(self):
        """Test parsing move_cursor command."""
        data = {
            'command_type': 'move_cursor',
            'row': 10,
            'col': 20
        }
        cmd = parse_command(data)
        
        assert isinstance(cmd, MoveCursorCommand)
        assert cmd.row == 10
        assert cmd.col == 20


class TestParseCommandValidation:
    """Tests for general parse_command validation."""
    
    def test_parse_command_not_dict(self):
        """Test that non-dict input raises TypeError."""
        with pytest.raises(TypeError, match="Expected dict, got str"):
            parse_command("not a dict")
    
    def test_parse_command_missing_command_type(self):
        """Test that missing command_type raises ValueError."""
        data = {'row': 5, 'col': 10}
        with pytest.raises(ValueError, match="Missing required field 'command_type'"):
            parse_command(data)
    
    def test_parse_command_unknown_type(self):
        """Test that unknown command_type raises ValueError."""
        data = {'command_type': 'unknown_command'}
        with pytest.raises(ValueError, match="Unknown command_type: unknown_command"):
            parse_command(data)


class TestRoundTripSerialization:
    """Tests for serialization round-trip (serialize -> parse -> serialize)."""
    
    def test_round_trip_draw_text(self):
        """Test that draw_text survives serialization round-trip."""
        from ttk.serialization import serialize_command
        
        original = DrawTextCommand(
            row=5,
            col=10,
            text='Hello',
            color_pair=3,
            attributes=7
        )
        
        # Serialize
        serialized = serialize_command(original)
        
        # Parse
        parsed = parse_command(serialized)
        
        # Verify
        assert parsed == original
    
    def test_round_trip_draw_rect(self):
        """Test that draw_rect survives serialization round-trip."""
        from ttk.serialization import serialize_command
        
        original = DrawRectCommand(
            row=2,
            col=3,
            height=5,
            width=10,
            color_pair=2,
            filled=True
        )
        
        serialized = serialize_command(original)
        parsed = parse_command(serialized)
        
        assert parsed == original
    
    def test_round_trip_init_color_pair(self):
        """Test that init_color_pair survives serialization round-trip."""
        from ttk.serialization import serialize_command
        
        original = InitColorPairCommand(
            pair_id=5,
            fg_color=(255, 128, 64),
            bg_color=(0, 0, 0)
        )
        
        serialized = serialize_command(original)
        parsed = parse_command(serialized)
        
        assert parsed == original
    
    def test_round_trip_all_commands(self):
        """Test that all command types survive round-trip."""
        from ttk.serialization import serialize_command
        
        commands = [
            DrawTextCommand(row=1, col=2, text='test', color_pair=1, attributes=2),
            DrawHLineCommand(row=3, col=4, char='-', length=10, color_pair=1),
            DrawVLineCommand(row=5, col=6, char='|', length=10, color_pair=1),
            DrawRectCommand(row=7, col=8, height=5, width=10, color_pair=1, filled=True),
            ClearCommand(),
            ClearRegionCommand(row=9, col=10, height=3, width=5),
            RefreshCommand(),
            RefreshRegionCommand(row=11, col=12, height=3, width=5),
            InitColorPairCommand(pair_id=1, fg_color=(255, 0, 0), bg_color=(0, 0, 0)),
            SetCursorVisibilityCommand(visible=True),
            MoveCursorCommand(row=13, col=14),
        ]
        
        for original in commands:
            serialized = serialize_command(original)
            parsed = parse_command(serialized)
            assert parsed == original, f"Round-trip failed for {type(original).__name__}"
