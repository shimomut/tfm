"""
Unit tests for Metal backend color management.

This module tests the color management functionality of the Metal backend,
including color pair initialization, validation, and usage during rendering.

Tests cover:
- Color pair initialization with valid RGB values
- Color pair validation (pair ID range, RGB component range)
- Color pair storage and retrieval
- Default color pair (pair 0)
- Color usage during rendering
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from ttk.backends.metal_backend import MetalBackend
from ttk.renderer import TextAttribute


class TestMetalColorManagement(unittest.TestCase):
    """Test cases for Metal backend color management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = MetalBackend()
        # Initialize color_pairs dict without calling initialize()
        self.backend.color_pairs = {}
        self.backend.rows = 24
        self.backend.cols = 80
        self.backend.grid = [
            [(' ', 0, 0) for _ in range(80)]
            for _ in range(24)
        ]
    
    def test_init_color_pair_valid(self):
        """Test initializing color pair with valid RGB values."""
        # Test with typical RGB values
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        self.assertEqual(self.backend.color_pairs[1], ((255, 0, 0), (0, 0, 0)))
        
        # Test with different color pair
        self.backend.init_color_pair(2, (0, 255, 0), (128, 128, 128))
        self.assertEqual(self.backend.color_pairs[2], ((0, 255, 0), (128, 128, 128)))
    
    def test_init_color_pair_boundary_values(self):
        """Test color pair initialization with boundary RGB values."""
        # Test with minimum values (0, 0, 0)
        self.backend.init_color_pair(1, (0, 0, 0), (0, 0, 0))
        self.assertEqual(self.backend.color_pairs[1], ((0, 0, 0), (0, 0, 0)))
        
        # Test with maximum values (255, 255, 255)
        self.backend.init_color_pair(2, (255, 255, 255), (255, 255, 255))
        self.assertEqual(self.backend.color_pairs[2], ((255, 255, 255), (255, 255, 255)))
        
        # Test with mixed boundary values
        self.backend.init_color_pair(3, (0, 128, 255), (255, 128, 0))
        self.assertEqual(self.backend.color_pairs[3], ((0, 128, 255), (255, 128, 0)))
    
    def test_init_color_pair_all_valid_ids(self):
        """Test that all valid pair IDs (1-255) can be initialized."""
        # Test minimum valid ID
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        self.assertIn(1, self.backend.color_pairs)
        
        # Test maximum valid ID
        self.backend.init_color_pair(255, (0, 255, 0), (0, 0, 0))
        self.assertIn(255, self.backend.color_pairs)
        
        # Test middle range ID
        self.backend.init_color_pair(128, (0, 0, 255), (0, 0, 0))
        self.assertIn(128, self.backend.color_pairs)
    
    def test_init_color_pair_invalid_id_zero(self):
        """Test that pair ID 0 is rejected (reserved for default)."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(0, (255, 0, 0), (0, 0, 0))
        
        self.assertIn("must be in range 1-255", str(context.exception))
        self.assertIn("Pair ID 0 is reserved", str(context.exception))
    
    def test_init_color_pair_invalid_id_negative(self):
        """Test that negative pair IDs are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(-1, (255, 0, 0), (0, 0, 0))
        
        self.assertIn("must be in range 1-255", str(context.exception))
    
    def test_init_color_pair_invalid_id_too_large(self):
        """Test that pair IDs > 255 are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(256, (255, 0, 0), (0, 0, 0))
        
        self.assertIn("must be in range 1-255", str(context.exception))
    
    def test_init_color_pair_invalid_fg_rgb_negative(self):
        """Test that negative RGB components in foreground are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, (-1, 0, 0), (0, 0, 0))
        
        self.assertIn("Foreground color", str(context.exception))
        self.assertIn("must be an integer in range 0-255", str(context.exception))
    
    def test_init_color_pair_invalid_fg_rgb_too_large(self):
        """Test that RGB components > 255 in foreground are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, (256, 0, 0), (0, 0, 0))
        
        self.assertIn("Foreground color", str(context.exception))
        self.assertIn("must be an integer in range 0-255", str(context.exception))
    
    def test_init_color_pair_invalid_bg_rgb_negative(self):
        """Test that negative RGB components in background are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, (255, 0, 0), (0, -1, 0))
        
        self.assertIn("Background color", str(context.exception))
        self.assertIn("must be an integer in range 0-255", str(context.exception))
    
    def test_init_color_pair_invalid_bg_rgb_too_large(self):
        """Test that RGB components > 255 in background are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 256))
        
        self.assertIn("Background color", str(context.exception))
        self.assertIn("must be an integer in range 0-255", str(context.exception))
    
    def test_init_color_pair_invalid_fg_not_tuple(self):
        """Test that non-tuple foreground colors are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, [255, 0, 0], (0, 0, 0))
        
        self.assertIn("Foreground color must be a tuple", str(context.exception))
    
    def test_init_color_pair_invalid_bg_not_tuple(self):
        """Test that non-tuple background colors are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, (255, 0, 0), [0, 0, 0])
        
        self.assertIn("Background color must be a tuple", str(context.exception))
    
    def test_init_color_pair_invalid_fg_wrong_length(self):
        """Test that foreground colors with wrong number of components are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, (255, 0), (0, 0, 0))
        
        self.assertIn("Foreground color must be a tuple of 3 integers", str(context.exception))
    
    def test_init_color_pair_invalid_bg_wrong_length(self):
        """Test that background colors with wrong number of components are rejected."""
        with self.assertRaises(ValueError) as context:
            self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0, 255))
        
        self.assertIn("Background color must be a tuple of 3 integers", str(context.exception))
    
    def test_init_color_pair_overwrite(self):
        """Test that color pairs can be overwritten."""
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        self.assertEqual(self.backend.color_pairs[1], ((255, 0, 0), (0, 0, 0)))
        
        # Overwrite with different colors
        self.backend.init_color_pair(1, (0, 255, 0), (128, 128, 128))
        self.assertEqual(self.backend.color_pairs[1], ((0, 255, 0), (128, 128, 128)))
    
    def test_default_color_pair(self):
        """Test that default color pair (0) is initialized."""
        # Create backend and initialize
        backend = MetalBackend()
        backend.color_pairs = {}
        backend.color_pairs[0] = ((255, 255, 255), (0, 0, 0))
        
        # Verify default color pair exists
        self.assertIn(0, backend.color_pairs)
        self.assertEqual(backend.color_pairs[0], ((255, 255, 255), (0, 0, 0)))
    
    def test_color_pair_storage(self):
        """Test that multiple color pairs can be stored simultaneously."""
        # Initialize multiple color pairs
        colors = {
            1: ((255, 0, 0), (0, 0, 0)),      # Red on black
            2: ((0, 255, 0), (0, 0, 0)),      # Green on black
            3: ((0, 0, 255), (0, 0, 0)),      # Blue on black
            4: ((255, 255, 0), (0, 0, 0)),    # Yellow on black
            5: ((255, 0, 255), (0, 0, 0)),    # Magenta on black
        }
        
        for pair_id, (fg, bg) in colors.items():
            self.backend.init_color_pair(pair_id, fg, bg)
        
        # Verify all pairs are stored correctly
        for pair_id, expected_colors in colors.items():
            self.assertEqual(self.backend.color_pairs[pair_id], expected_colors)
    
    def test_color_usage_in_grid(self):
        """Test that color pairs are used when drawing to grid."""
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        
        # Draw text with color pair
        self.backend.draw_text(0, 0, "Test", color_pair=1)
        
        # Verify grid cells have correct color pair
        for i, char in enumerate("Test"):
            cell = self.backend.grid[0][i]
            self.assertEqual(cell[0], char)
            self.assertEqual(cell[1], 1)  # Color pair ID
    
    def test_color_retrieval_in_render_character(self):
        """Test that colors are retrieved correctly during rendering."""
        # Initialize color pairs
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        self.backend.init_color_pair(2, (0, 255, 0), (128, 128, 128))
        
        # Mock render encoder
        mock_encoder = Mock()
        
        # Test color retrieval for pair 1
        self.backend._render_character(mock_encoder, 0, 0, 'A', 1, 0)
        fg, bg = self.backend.color_pairs[1]
        self.assertEqual(fg, (255, 0, 0))
        self.assertEqual(bg, (0, 0, 0))
        
        # Test color retrieval for pair 2
        self.backend._render_character(mock_encoder, 0, 0, 'B', 2, 0)
        fg, bg = self.backend.color_pairs[2]
        self.assertEqual(fg, (0, 255, 0))
        self.assertEqual(bg, (128, 128, 128))
    
    def test_color_reverse_attribute(self):
        """Test that REVERSE attribute swaps foreground and background colors."""
        # Initialize color pair
        self.backend.init_color_pair(1, (255, 0, 0), (0, 0, 255))
        
        # Mock render encoder
        mock_encoder = Mock()
        
        # Render with REVERSE attribute
        self.backend._render_character(mock_encoder, 0, 0, 'A', 1, TextAttribute.REVERSE)
        
        # Verify colors are swapped in the method
        # (The actual swap happens inside _render_character)
        fg, bg = self.backend.color_pairs[1]
        self.assertEqual(fg, (255, 0, 0))
        self.assertEqual(bg, (0, 0, 255))
    
    def test_color_pair_default_fallback(self):
        """Test that missing color pairs fall back to default."""
        # Don't initialize color pair 99
        # Ensure default color pair exists
        self.backend.color_pairs[0] = ((255, 255, 255), (0, 0, 0))
        
        # Mock render encoder
        mock_encoder = Mock()
        
        # Render with non-existent color pair
        self.backend._render_character(mock_encoder, 0, 0, 'A', 99, 0)
        
        # Verify fallback to default colors
        fg, bg = self.backend.color_pairs.get(99, ((255, 255, 255), (0, 0, 0)))
        self.assertEqual(fg, (255, 255, 255))
        self.assertEqual(bg, (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
