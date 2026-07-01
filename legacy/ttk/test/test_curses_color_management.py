"""
Test curses backend color management.

This module tests the color management functionality implemented in the CursesBackend class,
including color pair initialization, RGB to curses color conversion, and color pair tracking.
"""

import curses
from unittest.mock import Mock, patch
from ttk.backends.curses_backend import CursesBackend


def test_init_color_pair_basic():
    """Test basic color pair initialization."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.init_pair') as mock_init_pair:
        # Initialize a color pair
        backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        
        # Should call curses.init_pair
        mock_init_pair.assert_called_once()
        
        # Should track the initialized pair
        assert 1 in backend.color_pairs_initialized
    
    print("✓ test_init_color_pair_basic passed")


def test_init_color_pair_avoids_reinitialization():
    """Test that color pairs are not re-initialized."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.init_pair') as mock_init_pair:
        # Initialize a color pair
        backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        assert mock_init_pair.call_count == 1
        
        # Try to initialize the same pair again
        backend.init_color_pair(1, (0, 255, 0), (255, 255, 255))
        
        # Should not call init_pair again
        assert mock_init_pair.call_count == 1
    
    print("✓ test_init_color_pair_avoids_reinitialization passed")


def test_init_color_pair_validation():
    """Test color pair initialization validation."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    # Test pair_id = 0 (reserved)
    try:
        backend.init_color_pair(0, (255, 0, 0), (0, 0, 0))
        assert False, "Should have raised ValueError for pair_id=0"
    except ValueError as e:
        assert "reserved" in str(e)
    
    # Test pair_id out of range (too low)
    try:
        backend.init_color_pair(-1, (255, 0, 0), (0, 0, 0))
        assert False, "Should have raised ValueError for negative pair_id"
    except ValueError as e:
        assert "1-255" in str(e)
    
    # Test pair_id out of range (too high)
    try:
        backend.init_color_pair(256, (255, 0, 0), (0, 0, 0))
        assert False, "Should have raised ValueError for pair_id=256"
    except ValueError as e:
        assert "1-255" in str(e)
    
    # Test invalid RGB tuple length
    try:
        backend.init_color_pair(1, (255, 0), (0, 0, 0))
        assert False, "Should have raised ValueError for invalid RGB tuple"
    except ValueError as e:
        assert "3-tuple" in str(e)
    
    # Test RGB component out of range (negative)
    try:
        backend.init_color_pair(1, (-1, 0, 0), (0, 0, 0))
        assert False, "Should have raised ValueError for negative RGB component"
    except ValueError as e:
        assert "0-255" in str(e)
    
    # Test RGB component out of range (too high)
    try:
        backend.init_color_pair(1, (255, 0, 0), (0, 0, 256))
        assert False, "Should have raised ValueError for RGB component > 255"
    except ValueError as e:
        assert "0-255" in str(e)
    
    print("✓ test_init_color_pair_validation passed")


def test_rgb_to_curses_color_black():
    """Test RGB to curses color conversion for black."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_BLACK', 0):
        # Dark colors should map to black
        assert backend._rgb_to_curses_color((0, 0, 0)) == curses.COLOR_BLACK
        assert backend._rgb_to_curses_color((50, 50, 50)) == curses.COLOR_BLACK
        assert backend._rgb_to_curses_color((127, 127, 127)) == curses.COLOR_BLACK
    
    print("✓ test_rgb_to_curses_color_black passed")


def test_rgb_to_curses_color_white():
    """Test RGB to curses color conversion for white."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_WHITE', 7):
        # Bright colors should map to white
        assert backend._rgb_to_curses_color((255, 255, 255)) == curses.COLOR_WHITE
        assert backend._rgb_to_curses_color((201, 201, 201)) == curses.COLOR_WHITE
        assert backend._rgb_to_curses_color((250, 250, 250)) == curses.COLOR_WHITE
    
    print("✓ test_rgb_to_curses_color_white passed")


def test_rgb_to_curses_color_red():
    """Test RGB to curses color conversion for red."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_RED', 1):
        # Red-dominant colors should map to red
        assert backend._rgb_to_curses_color((255, 0, 0)) == curses.COLOR_RED
        assert backend._rgb_to_curses_color((200, 50, 50)) == curses.COLOR_RED
        assert backend._rgb_to_curses_color((180, 100, 100)) == curses.COLOR_RED
    
    print("✓ test_rgb_to_curses_color_red passed")


def test_rgb_to_curses_color_green():
    """Test RGB to curses color conversion for green."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_GREEN', 2):
        # Green-dominant colors should map to green
        assert backend._rgb_to_curses_color((0, 255, 0)) == curses.COLOR_GREEN
        assert backend._rgb_to_curses_color((50, 200, 50)) == curses.COLOR_GREEN
        assert backend._rgb_to_curses_color((100, 180, 100)) == curses.COLOR_GREEN
    
    print("✓ test_rgb_to_curses_color_green passed")


def test_rgb_to_curses_color_blue():
    """Test RGB to curses color conversion for blue."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_BLUE', 4):
        # Blue-dominant colors should map to blue
        assert backend._rgb_to_curses_color((0, 0, 255)) == curses.COLOR_BLUE
        assert backend._rgb_to_curses_color((50, 50, 200)) == curses.COLOR_BLUE
        assert backend._rgb_to_curses_color((100, 100, 180)) == curses.COLOR_BLUE
    
    print("✓ test_rgb_to_curses_color_blue passed")


def test_rgb_to_curses_color_yellow():
    """Test RGB to curses color conversion for yellow."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_YELLOW', 3):
        # Yellow (red + green) colors should map to yellow
        assert backend._rgb_to_curses_color((255, 255, 0)) == curses.COLOR_YELLOW
        assert backend._rgb_to_curses_color((200, 200, 50)) == curses.COLOR_YELLOW
        assert backend._rgb_to_curses_color((180, 180, 100)) == curses.COLOR_YELLOW
    
    print("✓ test_rgb_to_curses_color_yellow passed")


def test_rgb_to_curses_color_magenta():
    """Test RGB to curses color conversion for magenta."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_MAGENTA', 5):
        # Magenta (red + blue) colors should map to magenta
        assert backend._rgb_to_curses_color((255, 0, 255)) == curses.COLOR_MAGENTA
        assert backend._rgb_to_curses_color((200, 50, 200)) == curses.COLOR_MAGENTA
        assert backend._rgb_to_curses_color((180, 100, 180)) == curses.COLOR_MAGENTA
    
    print("✓ test_rgb_to_curses_color_magenta passed")


def test_rgb_to_curses_color_cyan():
    """Test RGB to curses color conversion for cyan."""
    backend = CursesBackend()
    
    with patch('curses.COLOR_CYAN', 6):
        # Cyan (green + blue) colors should map to cyan
        assert backend._rgb_to_curses_color((0, 255, 255)) == curses.COLOR_CYAN
        assert backend._rgb_to_curses_color((50, 200, 200)) == curses.COLOR_CYAN
        assert backend._rgb_to_curses_color((100, 180, 180)) == curses.COLOR_CYAN
    
    print("✓ test_rgb_to_curses_color_cyan passed")


def test_color_pair_tracking():
    """Test that color pairs are properly tracked."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    # Initially, only pair 0 should be tracked (from initialize)
    assert 0 not in backend.color_pairs_initialized  # Not initialized yet
    
    with patch('curses.init_pair'):
        # Initialize several color pairs
        backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        backend.init_color_pair(2, (0, 255, 0), (0, 0, 0))
        backend.init_color_pair(3, (0, 0, 255), (0, 0, 0))
        
        # All should be tracked
        assert 1 in backend.color_pairs_initialized
        assert 2 in backend.color_pairs_initialized
        assert 3 in backend.color_pairs_initialized
        
        # Pair 4 should not be tracked
        assert 4 not in backend.color_pairs_initialized
    
    print("✓ test_color_pair_tracking passed")


def test_init_color_pair_with_curses_colors():
    """Test that init_color_pair correctly converts RGB to curses colors."""
    backend = CursesBackend()
    backend.stdscr = Mock()
    
    with patch('curses.init_pair') as mock_init_pair:
        with patch('curses.COLOR_RED', 1):
            with patch('curses.COLOR_BLACK', 0):
                # Initialize a red on black color pair
                backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
                
                # Should call init_pair with converted colors
                mock_init_pair.assert_called_once_with(1, curses.COLOR_RED, curses.COLOR_BLACK)
    
    print("✓ test_init_color_pair_with_curses_colors passed")


if __name__ == '__main__':
    print("Running curses color management tests...\n")
    
    test_init_color_pair_basic()
    test_init_color_pair_avoids_reinitialization()
    test_init_color_pair_validation()
    test_rgb_to_curses_color_black()
    test_rgb_to_curses_color_white()
    test_rgb_to_curses_color_red()
    test_rgb_to_curses_color_green()
    test_rgb_to_curses_color_blue()
    test_rgb_to_curses_color_yellow()
    test_rgb_to_curses_color_magenta()
    test_rgb_to_curses_color_cyan()
    test_color_pair_tracking()
    test_init_color_pair_with_curses_colors()
    
    print("\n✅ All curses color management tests passed!")
