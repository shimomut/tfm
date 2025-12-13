#!/usr/bin/env python3
"""
Unit tests for curses backend fullcolor support.

Tests:
- Fullcolor mode detection
- Custom color creation
- Fallback to 8/16 color approximation
- Color caching
- Color pair initialization
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ttk.backends.curses_backend import CursesBackend


class TestCursesFullcolor(unittest.TestCase):
    """Test cases for curses backend fullcolor support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = CursesBackend()
        self.backend.stdscr = Mock()
    
    def test_initialization_with_fullcolor(self):
        """Test backend initialization detects fullcolor mode."""
        import curses as curses_module
        
        with patch('curses.initscr') as mock_initscr, \
             patch('curses.start_color'), \
             patch('curses.noecho'), \
             patch('curses.cbreak'), \
             patch('curses.curs_set'), \
             patch('curses.init_pair'), \
             patch('curses.color_pair', return_value=1), \
             patch('curses.can_change_color', return_value=True):
            
            # Set COLORS directly on the module
            curses_module.COLORS = 256
            try:
                mock_stdscr = Mock()
                mock_stdscr.keypad = Mock()
                mock_stdscr.bkgd = Mock()
                mock_initscr.return_value = mock_stdscr
                
                self.backend.initialize()
                
                self.assertTrue(self.backend.fullcolor_mode)
                self.assertEqual(self.backend.next_color_index, 16)
            finally:
                # Clean up
                if hasattr(curses_module, 'COLORS'):
                    delattr(curses_module, 'COLORS')
    
    def test_initialization_without_fullcolor(self):
        """Test backend initialization falls back to 8/16 color mode."""
        import curses as curses_module
        
        with patch('curses.initscr') as mock_initscr, \
             patch('curses.start_color'), \
             patch('curses.noecho'), \
             patch('curses.cbreak'), \
             patch('curses.curs_set'), \
             patch('curses.init_pair'), \
             patch('curses.color_pair', return_value=1), \
             patch('curses.can_change_color', return_value=False):
            
            # Set COLORS directly on the module
            curses_module.COLORS = 8
            try:
                mock_stdscr = Mock()
                mock_stdscr.keypad = Mock()
                mock_stdscr.bkgd = Mock()
                mock_initscr.return_value = mock_stdscr
                
                self.backend.initialize()
                
                self.assertFalse(self.backend.fullcolor_mode)
            finally:
                # Clean up
                if hasattr(curses_module, 'COLORS'):
                    delattr(curses_module, 'COLORS')
    
    def test_create_fullcolor(self):
        """Test custom color creation in fullcolor mode."""
        import curses as curses_module
        
        self.backend.fullcolor_mode = True
        self.backend.next_color_index = 16
        
        with patch('curses.init_color') as mock_init_color:
            # Set COLORS directly on the module
            curses_module.COLORS = 256
            try:
                rgb = (128, 64, 192)
                color_index = self.backend._create_fullcolor(rgb)
                
                # Should return next available index
                self.assertEqual(color_index, 16)
                self.assertEqual(self.backend.next_color_index, 17)
                
                # Should call init_color with converted values
                mock_init_color.assert_called_once()
                args = mock_init_color.call_args[0]
                self.assertEqual(args[0], 16)  # color index
                # RGB values should be converted to 0-1000 range
                self.assertAlmostEqual(args[1], 502, delta=5)  # 128/255 * 1000
                self.assertAlmostEqual(args[2], 251, delta=5)  # 64/255 * 1000
                self.assertAlmostEqual(args[3], 753, delta=5)  # 192/255 * 1000
            finally:
                # Clean up
                if hasattr(curses_module, 'COLORS'):
                    delattr(curses_module, 'COLORS')
    
    def test_approximate_to_basic_color(self):
        """Test RGB approximation to 8 basic colors."""
        self.backend.fullcolor_mode = False
        
        with patch('curses.COLOR_RED', 1), \
             patch('curses.COLOR_GREEN', 2), \
             patch('curses.COLOR_BLUE', 4), \
             patch('curses.COLOR_WHITE', 7), \
             patch('curses.COLOR_BLACK', 0):
            
            # Test pure colors
            self.assertEqual(self.backend._approximate_to_basic_color((255, 0, 0)), 1)  # Red
            self.assertEqual(self.backend._approximate_to_basic_color((0, 255, 0)), 2)  # Green
            self.assertEqual(self.backend._approximate_to_basic_color((0, 0, 255)), 4)  # Blue
            
            # Test near-white
            self.assertEqual(self.backend._approximate_to_basic_color((220, 220, 220)), 7)  # White
            
            # Test near-black
            self.assertEqual(self.backend._approximate_to_basic_color((10, 10, 10)), 0)  # Black
    
    def test_color_caching(self):
        """Test that colors are cached correctly."""
        import curses as curses_module
        
        self.backend.fullcolor_mode = True
        self.backend.next_color_index = 16
        
        with patch('curses.init_color'):
            # Set COLORS directly on the module
            curses_module.COLORS = 256
            try:
                rgb = (100, 150, 200)
                
                # First call should create color
                color1 = self.backend._rgb_to_curses_color(rgb)
                self.assertEqual(self.backend.next_color_index, 17)
                
                # Second call should use cache
                color2 = self.backend._rgb_to_curses_color(rgb)
                self.assertEqual(color1, color2)
                self.assertEqual(self.backend.next_color_index, 17)  # No new color created
                
                # Cache should contain the RGB
                self.assertIn(rgb, self.backend.rgb_to_color_cache)
                self.assertEqual(self.backend.rgb_to_color_cache[rgb], color1)
            finally:
                # Clean up
                if hasattr(curses_module, 'COLORS'):
                    delattr(curses_module, 'COLORS')
    
    def test_color_pair_initialization_fullcolor(self):
        """Test color pair initialization uses fullcolor."""
        import curses as curses_module
        
        self.backend.fullcolor_mode = True
        self.backend.next_color_index = 16
        
        with patch('curses.init_color'), \
             patch('curses.init_pair') as mock_init_pair:
            # Set COLORS directly on the module
            curses_module.COLORS = 256
            try:
                fg_rgb = (255, 128, 64)
                bg_rgb = (32, 32, 32)
                
                self.backend.init_color_pair(10, fg_rgb, bg_rgb)
                
                # Should have created two custom colors
                self.assertEqual(self.backend.next_color_index, 18)
                
                # Should have initialized the pair
                mock_init_pair.assert_called_once()
                self.assertIn(10, self.backend.color_pairs_initialized)
            finally:
                # Clean up
                if hasattr(curses_module, 'COLORS'):
                    delattr(curses_module, 'COLORS')
    
    def test_color_pair_initialization_fallback(self):
        """Test color pair initialization falls back to approximation."""
        self.backend.fullcolor_mode = False
        
        with patch('curses.init_pair') as mock_init_pair, \
             patch('curses.COLOR_RED', 1), \
             patch('curses.COLOR_BLACK', 0):
            
            fg_rgb = (255, 0, 0)  # Red
            bg_rgb = (0, 0, 0)    # Black
            
            self.backend.init_color_pair(10, fg_rgb, bg_rgb)
            
            # Should use approximated colors
            mock_init_pair.assert_called_once_with(10, 1, 0)
            self.assertIn(10, self.backend.color_pairs_initialized)
    
    def test_color_pair_skip_if_initialized(self):
        """Test that already initialized pairs are skipped."""
        self.backend.fullcolor_mode = True
        self.backend.color_pairs_initialized.add(10)
        
        with patch('curses.init_pair') as mock_init_pair:
            self.backend.init_color_pair(10, (255, 0, 0), (0, 0, 0))
            
            # Should not call init_pair again
            mock_init_pair.assert_not_called()
    
    def test_fullcolor_exhaustion_fallback(self):
        """Test fallback when running out of color slots."""
        import curses as curses_module
        
        self.backend.fullcolor_mode = True
        
        # Set COLORS directly on the module
        curses_module.COLORS = 256
        try:
            # Set next_color_index to max
            self.backend.next_color_index = 256
            
            with patch('curses.COLOR_WHITE', 7):
                # Should fallback to approximation
                color = self.backend._create_fullcolor((220, 220, 220))
                self.assertEqual(color, 7)  # Should approximate to white
        finally:
            # Clean up
            if hasattr(curses_module, 'COLORS'):
                delattr(curses_module, 'COLORS')
    
    def test_rgb_validation(self):
        """Test RGB value validation."""
        with self.assertRaises(ValueError):
            # Invalid RGB tuple length
            self.backend.init_color_pair(10, (255, 0), (0, 0, 0))
        
        with self.assertRaises(ValueError):
            # RGB value out of range
            self.backend.init_color_pair(10, (300, 0, 0), (0, 0, 0))
        
        with self.assertRaises(ValueError):
            # Negative RGB value
            self.backend.init_color_pair(10, (-10, 0, 0), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
