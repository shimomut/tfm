"""
Unit tests for TTK utility functions.

Tests platform detection, color conversion, and parameter validation functions.
"""

import platform
import pytest
from ttk.utils import (
    get_recommended_backend,
    rgb_to_normalized,
    normalized_to_rgb,
    rgb_to_hex,
    hex_to_rgb,
    validate_rgb,
    validate_color_pair_id,
    validate_coordinates,
    validate_dimensions,
    clamp,
    clamp_rgb,
)


class TestPlatformDetection:
    """Tests for platform detection functions."""
    
    def test_get_recommended_backend_returns_string(self):
        """Test that get_recommended_backend returns a string."""
        backend = get_recommended_backend()
        assert isinstance(backend, str)
        assert backend in ['curses', 'metal']
    
    def test_get_recommended_backend_darwin(self, monkeypatch):
        """Test that macOS (Darwin) recommends metal backend."""
        monkeypatch.setattr(platform, 'system', lambda: 'Darwin')
        assert get_recommended_backend() == 'metal'
    
    def test_get_recommended_backend_linux(self, monkeypatch):
        """Test that Linux recommends curses backend."""
        monkeypatch.setattr(platform, 'system', lambda: 'Linux')
        assert get_recommended_backend() == 'curses'
    
    def test_get_recommended_backend_windows(self, monkeypatch):
        """Test that Windows recommends curses backend."""
        monkeypatch.setattr(platform, 'system', lambda: 'Windows')
        assert get_recommended_backend() == 'curses'


class TestColorConversion:
    """Tests for color conversion functions."""
    
    def test_rgb_to_normalized_basic(self):
        """Test basic RGB to normalized conversion."""
        assert rgb_to_normalized((255, 255, 255)) == (1.0, 1.0, 1.0)
        assert rgb_to_normalized((0, 0, 0)) == (0.0, 0.0, 0.0)
        assert rgb_to_normalized((255, 0, 0)) == (1.0, 0.0, 0.0)
    
    def test_rgb_to_normalized_mid_values(self):
        """Test RGB to normalized with mid-range values."""
        r, g, b = rgb_to_normalized((128, 64, 192))
        assert 0.5 <= r <= 0.51  # ~0.502
        assert 0.25 <= g <= 0.26  # ~0.251
        assert 0.75 <= b <= 0.76  # ~0.753
    
    def test_rgb_to_normalized_invalid_values(self):
        """Test that invalid RGB values raise ValueError."""
        with pytest.raises(ValueError):
            rgb_to_normalized((256, 0, 0))
        with pytest.raises(ValueError):
            rgb_to_normalized((0, -1, 0))
        with pytest.raises(ValueError):
            rgb_to_normalized((0, 0, 300))
    
    def test_normalized_to_rgb_basic(self):
        """Test basic normalized to RGB conversion."""
        assert normalized_to_rgb((1.0, 1.0, 1.0)) == (255, 255, 255)
        assert normalized_to_rgb((0.0, 0.0, 0.0)) == (0, 0, 0)
        assert normalized_to_rgb((1.0, 0.0, 0.0)) == (255, 0, 0)
    
    def test_normalized_to_rgb_mid_values(self):
        """Test normalized to RGB with mid-range values."""
        assert normalized_to_rgb((0.5, 0.25, 0.75)) == (127, 63, 191)
    
    def test_normalized_to_rgb_invalid_values(self):
        """Test that invalid normalized values raise ValueError."""
        with pytest.raises(ValueError):
            normalized_to_rgb((1.5, 0.0, 0.0))
        with pytest.raises(ValueError):
            normalized_to_rgb((0.0, -0.1, 0.0))
        with pytest.raises(ValueError):
            normalized_to_rgb((0.0, 0.0, 2.0))
    
    def test_rgb_to_hex_basic(self):
        """Test basic RGB to hex conversion."""
        assert rgb_to_hex((255, 255, 255)) == '#FFFFFF'
        assert rgb_to_hex((0, 0, 0)) == '#000000'
        assert rgb_to_hex((255, 0, 0)) == '#FF0000'
        assert rgb_to_hex((0, 255, 0)) == '#00FF00'
        assert rgb_to_hex((0, 0, 255)) == '#0000FF'
    
    def test_rgb_to_hex_mixed_values(self):
        """Test RGB to hex with mixed values."""
        assert rgb_to_hex((255, 128, 0)) == '#FF8000'
        assert rgb_to_hex((64, 128, 192)) == '#4080C0'
    
    def test_rgb_to_hex_invalid_values(self):
        """Test that invalid RGB values raise ValueError."""
        with pytest.raises(ValueError):
            rgb_to_hex((256, 0, 0))
        with pytest.raises(ValueError):
            rgb_to_hex((0, -1, 0))
    
    def test_hex_to_rgb_basic(self):
        """Test basic hex to RGB conversion."""
        assert hex_to_rgb('#FFFFFF') == (255, 255, 255)
        assert hex_to_rgb('#000000') == (0, 0, 0)
        assert hex_to_rgb('#FF0000') == (255, 0, 0)
        assert hex_to_rgb('#00FF00') == (0, 255, 0)
        assert hex_to_rgb('#0000FF') == (0, 0, 255)
    
    def test_hex_to_rgb_without_hash(self):
        """Test hex to RGB conversion without # prefix."""
        assert hex_to_rgb('FFFFFF') == (255, 255, 255)
        assert hex_to_rgb('FF8000') == (255, 128, 0)
    
    def test_hex_to_rgb_lowercase(self):
        """Test hex to RGB with lowercase letters."""
        assert hex_to_rgb('#ffffff') == (255, 255, 255)
        assert hex_to_rgb('#ff8000') == (255, 128, 0)
    
    def test_hex_to_rgb_invalid_format(self):
        """Test that invalid hex strings raise ValueError."""
        with pytest.raises(ValueError):
            hex_to_rgb('#FFF')  # Too short
        with pytest.raises(ValueError):
            hex_to_rgb('#FFFFFFF')  # Too long
        with pytest.raises(ValueError):
            hex_to_rgb('#GGGGGG')  # Invalid hex characters
    
    def test_rgb_hex_round_trip(self):
        """Test that RGB -> hex -> RGB preserves values."""
        original = (255, 128, 64)
        hex_color = rgb_to_hex(original)
        result = hex_to_rgb(hex_color)
        assert result == original


class TestValidation:
    """Tests for parameter validation functions."""
    
    def test_validate_rgb_valid(self):
        """Test that valid RGB values pass validation."""
        validate_rgb((0, 0, 0))  # Should not raise
        validate_rgb((255, 255, 255))  # Should not raise
        validate_rgb((128, 64, 192))  # Should not raise
    
    def test_validate_rgb_invalid_range(self):
        """Test that out-of-range RGB values raise ValueError."""
        with pytest.raises(ValueError):
            validate_rgb((256, 0, 0))
        with pytest.raises(ValueError):
            validate_rgb((0, -1, 0))
        with pytest.raises(ValueError):
            validate_rgb((0, 0, 300))
    
    def test_validate_rgb_invalid_type(self):
        """Test that non-tuple RGB values raise TypeError."""
        with pytest.raises(TypeError):
            validate_rgb([255, 0, 0])  # List instead of tuple
        with pytest.raises(TypeError):
            validate_rgb((255, 0))  # Wrong length
        with pytest.raises(TypeError):
            validate_rgb((255.0, 0, 0))  # Float instead of int
    
    def test_validate_color_pair_id_valid(self):
        """Test that valid color pair IDs pass validation."""
        validate_color_pair_id(0)  # Should not raise
        validate_color_pair_id(128)  # Should not raise
        validate_color_pair_id(255)  # Should not raise
    
    def test_validate_color_pair_id_invalid_range(self):
        """Test that out-of-range color pair IDs raise ValueError."""
        with pytest.raises(ValueError):
            validate_color_pair_id(-1)
        with pytest.raises(ValueError):
            validate_color_pair_id(256)
    
    def test_validate_color_pair_id_invalid_type(self):
        """Test that non-integer color pair IDs raise TypeError."""
        with pytest.raises(TypeError):
            validate_color_pair_id(42.5)
        with pytest.raises(TypeError):
            validate_color_pair_id("42")
    
    def test_validate_coordinates_valid(self):
        """Test that valid coordinates pass validation."""
        validate_coordinates(0, 0)  # Should not raise
        validate_coordinates(10, 20)  # Should not raise
        validate_coordinates(100, 200)  # Should not raise
    
    def test_validate_coordinates_invalid_negative(self):
        """Test that negative coordinates raise ValueError."""
        with pytest.raises(ValueError):
            validate_coordinates(-1, 0)
        with pytest.raises(ValueError):
            validate_coordinates(0, -1)
        with pytest.raises(ValueError):
            validate_coordinates(-1, -1)
    
    def test_validate_coordinates_invalid_type(self):
        """Test that non-integer coordinates raise TypeError."""
        with pytest.raises(TypeError):
            validate_coordinates(10.5, 20)
        with pytest.raises(TypeError):
            validate_coordinates(10, 20.5)
        with pytest.raises(TypeError):
            validate_coordinates("10", 20)
    
    def test_validate_dimensions_valid(self):
        """Test that valid dimensions pass validation."""
        validate_dimensions(1, 1)  # Should not raise
        validate_dimensions(10, 20)  # Should not raise
        validate_dimensions(100, 200)  # Should not raise
    
    def test_validate_dimensions_invalid_zero_or_negative(self):
        """Test that zero or negative dimensions raise ValueError."""
        with pytest.raises(ValueError):
            validate_dimensions(0, 10)
        with pytest.raises(ValueError):
            validate_dimensions(10, 0)
        with pytest.raises(ValueError):
            validate_dimensions(-1, 10)
        with pytest.raises(ValueError):
            validate_dimensions(10, -1)
    
    def test_validate_dimensions_invalid_type(self):
        """Test that non-integer dimensions raise TypeError."""
        with pytest.raises(TypeError):
            validate_dimensions(10.5, 20)
        with pytest.raises(TypeError):
            validate_dimensions(10, 20.5)
        with pytest.raises(TypeError):
            validate_dimensions("10", 20)


class TestClampFunctions:
    """Tests for clamping functions."""
    
    def test_clamp_within_range(self):
        """Test that values within range are unchanged."""
        assert clamp(5, 0, 10) == 5
        assert clamp(0, 0, 10) == 0
        assert clamp(10, 0, 10) == 10
    
    def test_clamp_below_range(self):
        """Test that values below range are clamped to minimum."""
        assert clamp(-5, 0, 10) == 0
        assert clamp(-100, 0, 10) == 0
    
    def test_clamp_above_range(self):
        """Test that values above range are clamped to maximum."""
        assert clamp(15, 0, 10) == 10
        assert clamp(100, 0, 10) == 10
    
    def test_clamp_rgb_valid(self):
        """Test that valid RGB values are unchanged."""
        assert clamp_rgb((128, 64, 192)) == (128, 64, 192)
        assert clamp_rgb((0, 0, 0)) == (0, 0, 0)
        assert clamp_rgb((255, 255, 255)) == (255, 255, 255)
    
    def test_clamp_rgb_out_of_range(self):
        """Test that out-of-range RGB values are clamped."""
        assert clamp_rgb((300, 128, -50)) == (255, 128, 0)
        assert clamp_rgb((-10, 260, 128)) == (0, 255, 128)
        assert clamp_rgb((1000, -1000, 500)) == (255, 0, 255)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
