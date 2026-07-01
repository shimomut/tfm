"""
Test curses backend drawing operations.

This module tests the drawing operations implemented in the CursesBackend class,
including text rendering, line drawing, rectangle drawing, and region operations.
"""

import curses
from unittest.mock import Mock, MagicMock, patch
from ttk.backends.curses_backend import CursesBackend
from ttk.renderer import TextAttribute


def test_draw_text_basic():
    """Test basic text drawing."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.color_pair', return_value=0):
        # Test basic text drawing
        backend.draw_text(0, 0, "Hello", color_pair=0, attributes=0)
        backend.stdscr.addstr.assert_called_once()
    
    print("✓ test_draw_text_basic passed")


def test_draw_text_with_attributes():
    """Test text drawing with attributes."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    # Mock curses.color_pair
    with patch('curses.color_pair', return_value=0):
        with patch('curses.A_BOLD', 1):
            with patch('curses.A_UNDERLINE', 2):
                with patch('curses.A_REVERSE', 4):
                    # Test with BOLD attribute
                    backend.draw_text(0, 0, "Bold", color_pair=1, 
                                    attributes=TextAttribute.BOLD)
                    assert backend.stdscr.addstr.called
                    
                    # Test with combined attributes
                    backend.stdscr.reset_mock()
                    backend.draw_text(0, 0, "Bold+Underline", color_pair=1,
                                    attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
                    assert backend.stdscr.addstr.called
    
    print("✓ test_draw_text_with_attributes passed")


def test_draw_text_handles_curses_error():
    """Test that draw_text handles curses.error gracefully."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    backend.stdscr.addstr.side_effect = curses.error("Out of bounds")
    
    # Should not raise exception
    backend.draw_text(1000, 1000, "Out of bounds")
    
    print("✓ test_draw_text_handles_curses_error passed")


def test_draw_hline():
    """Test horizontal line drawing."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.color_pair', return_value=0):
        backend.draw_hline(5, 10, '-', 20, color_pair=0)
        backend.stdscr.hline.assert_called_once()
    
    print("✓ test_draw_hline passed")


def test_draw_hline_handles_curses_error():
    """Test that draw_hline handles curses.error gracefully."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    backend.stdscr.hline.side_effect = curses.error("Out of bounds")
    
    with patch('curses.color_pair', return_value=0):
        # Should not raise exception
        backend.draw_hline(1000, 1000, '-', 20)
    
    print("✓ test_draw_hline_handles_curses_error passed")


def test_draw_vline():
    """Test vertical line drawing."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.color_pair', return_value=0):
        backend.draw_vline(5, 10, '|', 15, color_pair=0)
        backend.stdscr.vline.assert_called_once()
    
    print("✓ test_draw_vline passed")


def test_draw_vline_handles_curses_error():
    """Test that draw_vline handles curses.error gracefully."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    backend.stdscr.vline.side_effect = curses.error("Out of bounds")
    
    with patch('curses.color_pair', return_value=0):
        # Should not raise exception
        backend.draw_vline(1000, 1000, '|', 15)
    
    print("✓ test_draw_vline_handles_curses_error passed")


def test_draw_rect_filled():
    """Test filled rectangle drawing."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.color_pair', return_value=0):
        backend.draw_rect(5, 10, 8, 20, color_pair=0, filled=True)
        # Should call draw_text for each row
        assert backend.stdscr.addstr.call_count == 8
    
    print("✓ test_draw_rect_filled passed")


def test_draw_rect_outline():
    """Test outlined rectangle drawing."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.color_pair', return_value=0):
        backend.draw_rect(5, 10, 8, 20, color_pair=0, filled=False)
        # Should call hline and vline for edges
        assert backend.stdscr.hline.call_count == 2  # Top and bottom
        assert backend.stdscr.vline.call_count == 2  # Left and right
    
    print("✓ test_draw_rect_outline passed")


def test_clear():
    """Test clearing the entire window."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    backend.clear()
    backend.stdscr.clear.assert_called_once()
    
    print("✓ test_clear passed")


def test_clear_region():
    """Test clearing a rectangular region."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    backend.stdscr.getmaxyx.return_value = (24, 80)
    
    backend.clear_region(5, 10, 3, 20)
    # Should move and add spaces for each row
    assert backend.stdscr.move.call_count == 3
    assert backend.stdscr.addstr.call_count == 3
    
    print("✓ test_clear_region passed")


def test_clear_region_handles_curses_error():
    """Test that clear_region handles curses.error gracefully."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    backend.stdscr.getmaxyx.return_value = (24, 80)
    backend.stdscr.move.side_effect = curses.error("Out of bounds")
    
    # Should not raise exception
    backend.clear_region(1000, 1000, 3, 20)
    
    print("✓ test_clear_region_handles_curses_error passed")


def test_refresh():
    """Test refreshing the display."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    backend.refresh()
    backend.stdscr.refresh.assert_called_once()
    
    print("✓ test_refresh passed")


def test_refresh_region():
    """Test refreshing a region (curses refreshes entire window)."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    backend.refresh_region(5, 10, 8, 20)
    # Curses backend refreshes entire window
    backend.stdscr.refresh.assert_called_once()
    
    print("✓ test_refresh_region passed")


def test_validation_errors():
    """Test that invalid parameters raise appropriate errors."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    backend.stdscr.getmaxyx.return_value = (24, 80)
    
    # Test negative height/width for clear_region
    try:
        backend.clear_region(0, 0, -1, 10)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "non-negative" in str(e)
    
    # Test negative length for draw_hline
    try:
        backend.draw_hline(0, 0, '-', -1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "non-negative" in str(e)
    
    # Test negative length for draw_vline
    try:
        backend.draw_vline(0, 0, '|', -1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "non-negative" in str(e)
    
    # Test negative height/width for draw_rect
    try:
        backend.draw_rect(0, 0, -1, 10)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "non-negative" in str(e)
    
    # Test invalid color_pair for draw_text
    try:
        backend.draw_text(0, 0, "test", color_pair=256)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "0-255" in str(e)
    
    print("✓ test_validation_errors passed")


if __name__ == '__main__':
    print("Running curses drawing operations tests...\n")
    
    test_draw_text_basic()
    test_draw_text_with_attributes()
    test_draw_text_handles_curses_error()
    test_draw_hline()
    test_draw_hline_handles_curses_error()
    test_draw_vline()
    test_draw_vline_handles_curses_error()
    test_draw_rect_filled()
    test_draw_rect_outline()
    test_clear()
    test_clear_region()
    test_clear_region_handles_curses_error()
    test_refresh()
    test_refresh_region()
    test_validation_errors()
    
    print("\n✅ All curses drawing operations tests passed!")
