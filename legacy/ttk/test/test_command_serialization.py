"""
Tests for TTK command serialization functionality.

This module tests the serialization of rendering commands to dictionary format,
ensuring all parameters are correctly captured and can be used to reproduce commands.
"""

import pytest
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
)


class TestCommandDataclasses:
    """Test command dataclass creation and structure."""
    
    def test_draw_text_command_creation(self):
        """Test creating a DrawTextCommand."""
        cmd = DrawTextCommand(row=5, col=10, text="Hello", color_pair=1, attributes=3)
        assert cmd.command_type == "draw_text"
        assert cmd.row == 5
        assert cmd.col == 10
        assert cmd.text == "Hello"
        assert cmd.color_pair == 1
        assert cmd.attributes == 3
    
    def test_draw_hline_command_creation(self):
        """Test creating a DrawHLineCommand."""
        cmd = DrawHLineCommand(row=2, col=5, char="-", length=20, color_pair=2)
        assert cmd.command_type == "draw_hline"
        assert cmd.row == 2
        assert cmd.col == 5
        assert cmd.char == "-"
        assert cmd.length == 20
        assert cmd.color_pair == 2
    
    def test_draw_vline_command_creation(self):
        """Test creating a DrawVLineCommand."""
        cmd = DrawVLineCommand(row=1, col=3, char="|", length=10, color_pair=1)
        assert cmd.command_type == "draw_vline"
        assert cmd.row == 1
        assert cmd.col == 3
        assert cmd.char == "|"
        assert cmd.length == 10
        assert cmd.color_pair == 1
    
    def test_draw_rect_command_creation(self):
        """Test creating a DrawRectCommand."""
        cmd = DrawRectCommand(row=0, col=0, height=5, width=10, color_pair=3, filled=True)
        assert cmd.command_type == "draw_rect"
        assert cmd.row == 0
        assert cmd.col == 0
        assert cmd.height == 5
        assert cmd.width == 10
        assert cmd.color_pair == 3
        assert cmd.filled is True
    
    def test_clear_command_creation(self):
        """Test creating a ClearCommand."""
        cmd = ClearCommand()
        assert cmd.command_type == "clear"
    
    def test_clear_region_command_creation(self):
        """Test creating a ClearRegionCommand."""
        cmd = ClearRegionCommand(row=2, col=3, height=4, width=5)
        assert cmd.command_type == "clear_region"
        assert cmd.row == 2
        assert cmd.col == 3
        assert cmd.height == 4
        assert cmd.width == 5
    
    def test_refresh_command_creation(self):
        """Test creating a RefreshCommand."""
        cmd = RefreshCommand()
        assert cmd.command_type == "refresh"
    
    def test_refresh_region_command_creation(self):
        """Test creating a RefreshRegionCommand."""
        cmd = RefreshRegionCommand(row=1, col=2, height=3, width=4)
        assert cmd.command_type == "refresh_region"
        assert cmd.row == 1
        assert cmd.col == 2
        assert cmd.height == 3
        assert cmd.width == 4
    
    def test_init_color_pair_command_creation(self):
        """Test creating an InitColorPairCommand."""
        cmd = InitColorPairCommand(pair_id=5, fg_color=(255, 0, 0), bg_color=(0, 0, 255))
        assert cmd.command_type == "init_color_pair"
        assert cmd.pair_id == 5
        assert cmd.fg_color == (255, 0, 0)
        assert cmd.bg_color == (0, 0, 255)
    
    def test_set_cursor_visibility_command_creation(self):
        """Test creating a SetCursorVisibilityCommand."""
        cmd = SetCursorVisibilityCommand(visible=True)
        assert cmd.command_type == "set_cursor_visibility"
        assert cmd.visible is True
    
    def test_move_cursor_command_creation(self):
        """Test creating a MoveCursorCommand."""
        cmd = MoveCursorCommand(row=10, col=20)
        assert cmd.command_type == "move_cursor"
        assert cmd.row == 10
        assert cmd.col == 20


class TestSerializeCommand:
    """Test the generic serialize_command function."""
    
    def test_serialize_draw_text_command(self):
        """Test serializing a DrawTextCommand."""
        cmd = DrawTextCommand(row=5, col=10, text="Test", color_pair=1, attributes=2)
        result = serialize_command(cmd)
        
        assert result['command_type'] == 'draw_text'
        assert result['row'] == 5
        assert result['col'] == 10
        assert result['text'] == 'Test'
        assert result['color_pair'] == 1
        assert result['attributes'] == 2
    
    def test_serialize_clear_command(self):
        """Test serializing a ClearCommand."""
        cmd = ClearCommand()
        result = serialize_command(cmd)
        
        assert result['command_type'] == 'clear'
        assert len(result) == 1  # Only command_type field
    
    def test_serialize_init_color_pair_command(self):
        """Test serializing an InitColorPairCommand."""
        cmd = InitColorPairCommand(pair_id=3, fg_color=(100, 150, 200), bg_color=(10, 20, 30))
        result = serialize_command(cmd)
        
        assert result['command_type'] == 'init_color_pair'
        assert result['pair_id'] == 3
        assert result['fg_color'] == (100, 150, 200)
        assert result['bg_color'] == (10, 20, 30)


class TestSerializationHelpers:
    """Test the convenience serialization helper functions."""
    
    def test_serialize_draw_text(self):
        """Test serialize_draw_text helper."""
        result = serialize_draw_text(row=3, col=7, text="Hello World", color_pair=2, attributes=1)
        
        assert result['command_type'] == 'draw_text'
        assert result['row'] == 3
        assert result['col'] == 7
        assert result['text'] == 'Hello World'
        assert result['color_pair'] == 2
        assert result['attributes'] == 1
    
    def test_serialize_draw_text_defaults(self):
        """Test serialize_draw_text with default parameters."""
        result = serialize_draw_text(row=0, col=0, text="Test")
        
        assert result['command_type'] == 'draw_text'
        assert result['row'] == 0
        assert result['col'] == 0
        assert result['text'] == 'Test'
        assert result['color_pair'] == 0
        assert result['attributes'] == 0
    
    def test_serialize_draw_hline(self):
        """Test serialize_draw_hline helper."""
        result = serialize_draw_hline(row=5, col=10, char="-", length=30, color_pair=1)
        
        assert result['command_type'] == 'draw_hline'
        assert result['row'] == 5
        assert result['col'] == 10
        assert result['char'] == '-'
        assert result['length'] == 30
        assert result['color_pair'] == 1
    
    def test_serialize_draw_vline(self):
        """Test serialize_draw_vline helper."""
        result = serialize_draw_vline(row=2, col=15, char="|", length=20, color_pair=3)
        
        assert result['command_type'] == 'draw_vline'
        assert result['row'] == 2
        assert result['col'] == 15
        assert result['char'] == '|'
        assert result['length'] == 20
        assert result['color_pair'] == 3
    
    def test_serialize_draw_rect(self):
        """Test serialize_draw_rect helper."""
        result = serialize_draw_rect(row=1, col=2, height=10, width=20, color_pair=2, filled=True)
        
        assert result['command_type'] == 'draw_rect'
        assert result['row'] == 1
        assert result['col'] == 2
        assert result['height'] == 10
        assert result['width'] == 20
        assert result['color_pair'] == 2
        assert result['filled'] is True
    
    def test_serialize_draw_rect_defaults(self):
        """Test serialize_draw_rect with default parameters."""
        result = serialize_draw_rect(row=0, col=0, height=5, width=10)
        
        assert result['command_type'] == 'draw_rect'
        assert result['color_pair'] == 0
        assert result['filled'] is False
    
    def test_serialize_clear(self):
        """Test serialize_clear helper."""
        result = serialize_clear()
        
        assert result['command_type'] == 'clear'
    
    def test_serialize_clear_region(self):
        """Test serialize_clear_region helper."""
        result = serialize_clear_region(row=5, col=10, height=3, width=8)
        
        assert result['command_type'] == 'clear_region'
        assert result['row'] == 5
        assert result['col'] == 10
        assert result['height'] == 3
        assert result['width'] == 8
    
    def test_serialize_refresh(self):
        """Test serialize_refresh helper."""
        result = serialize_refresh()
        
        assert result['command_type'] == 'refresh'
    
    def test_serialize_refresh_region(self):
        """Test serialize_refresh_region helper."""
        result = serialize_refresh_region(row=2, col=4, height=6, width=12)
        
        assert result['command_type'] == 'refresh_region'
        assert result['row'] == 2
        assert result['col'] == 4
        assert result['height'] == 6
        assert result['width'] == 12
    
    def test_serialize_init_color_pair(self):
        """Test serialize_init_color_pair helper."""
        result = serialize_init_color_pair(pair_id=10, fg_color=(255, 128, 64), bg_color=(32, 16, 8))
        
        assert result['command_type'] == 'init_color_pair'
        assert result['pair_id'] == 10
        assert result['fg_color'] == (255, 128, 64)
        assert result['bg_color'] == (32, 16, 8)
    
    def test_serialize_set_cursor_visibility(self):
        """Test serialize_set_cursor_visibility helper."""
        result = serialize_set_cursor_visibility(visible=True)
        
        assert result['command_type'] == 'set_cursor_visibility'
        assert result['visible'] is True
        
        result = serialize_set_cursor_visibility(visible=False)
        assert result['visible'] is False
    
    def test_serialize_move_cursor(self):
        """Test serialize_move_cursor helper."""
        result = serialize_move_cursor(row=15, col=25)
        
        assert result['command_type'] == 'move_cursor'
        assert result['row'] == 15
        assert result['col'] == 25


class TestSerializationCompleteness:
    """Test that serialization captures all necessary parameters."""
    
    def test_all_draw_text_parameters_captured(self):
        """Verify all draw_text parameters are in serialized output."""
        result = serialize_draw_text(row=1, col=2, text="abc", color_pair=3, attributes=4)
        
        required_keys = {'command_type', 'row', 'col', 'text', 'color_pair', 'attributes'}
        assert set(result.keys()) == required_keys
    
    def test_all_draw_rect_parameters_captured(self):
        """Verify all draw_rect parameters are in serialized output."""
        result = serialize_draw_rect(row=1, col=2, height=3, width=4, color_pair=5, filled=True)
        
        required_keys = {'command_type', 'row', 'col', 'height', 'width', 'color_pair', 'filled'}
        assert set(result.keys()) == required_keys
    
    def test_all_init_color_pair_parameters_captured(self):
        """Verify all init_color_pair parameters are in serialized output."""
        result = serialize_init_color_pair(pair_id=1, fg_color=(10, 20, 30), bg_color=(40, 50, 60))
        
        required_keys = {'command_type', 'pair_id', 'fg_color', 'bg_color'}
        assert set(result.keys()) == required_keys


class TestEdgeCases:
    """Test edge cases and special values."""
    
    def test_empty_text_serialization(self):
        """Test serializing draw_text with empty string."""
        result = serialize_draw_text(row=0, col=0, text="")
        assert result['text'] == ""
    
    def test_zero_length_line_serialization(self):
        """Test serializing lines with zero length."""
        result = serialize_draw_hline(row=0, col=0, char="-", length=0)
        assert result['length'] == 0
    
    def test_zero_dimensions_rect_serialization(self):
        """Test serializing rectangle with zero dimensions."""
        result = serialize_draw_rect(row=0, col=0, height=0, width=0)
        assert result['height'] == 0
        assert result['width'] == 0
    
    def test_color_pair_zero_serialization(self):
        """Test serializing with color pair 0 (default)."""
        result = serialize_draw_text(row=0, col=0, text="test", color_pair=0)
        assert result['color_pair'] == 0
    
    def test_max_color_pair_serialization(self):
        """Test serializing with maximum color pair value."""
        result = serialize_draw_text(row=0, col=0, text="test", color_pair=255)
        assert result['color_pair'] == 255
    
    def test_rgb_boundary_values(self):
        """Test serializing RGB values at boundaries."""
        # Minimum values
        result = serialize_init_color_pair(pair_id=1, fg_color=(0, 0, 0), bg_color=(0, 0, 0))
        assert result['fg_color'] == (0, 0, 0)
        assert result['bg_color'] == (0, 0, 0)
        
        # Maximum values
        result = serialize_init_color_pair(pair_id=1, fg_color=(255, 255, 255), bg_color=(255, 255, 255))
        assert result['fg_color'] == (255, 255, 255)
        assert result['bg_color'] == (255, 255, 255)
    
    def test_special_characters_in_text(self):
        """Test serializing text with special characters."""
        special_text = "Hello\nWorld\t!"
        result = serialize_draw_text(row=0, col=0, text=special_text)
        assert result['text'] == special_text
    
    def test_unicode_text_serialization(self):
        """Test serializing text with Unicode characters."""
        unicode_text = "Hello 世界 🌍"
        result = serialize_draw_text(row=0, col=0, text=unicode_text)
        assert result['text'] == unicode_text

