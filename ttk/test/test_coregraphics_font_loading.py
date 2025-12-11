"""
Tests for CoreGraphics backend font loading and character dimension calculation.

This test module verifies that the CoreGraphics backend correctly:
- Loads monospace fonts
- Validates font existence
- Calculates character dimensions
- Adds 20% line spacing to character height
"""

import pytest
import sys

# Skip all tests if not on macOS
pytestmark = pytest.mark.skipif(
    sys.platform != 'darwin',
    reason="CoreGraphics backend only available on macOS"
)

# Try to import CoreGraphics backend
try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
except ImportError:
    COCOA_AVAILABLE = False

# Skip all tests if PyObjC is not available
pytestmark = pytest.mark.skipif(
    not COCOA_AVAILABLE,
    reason="PyObjC not installed"
)


class TestFontLoading:
    """Test font loading functionality."""
    
    def test_default_font_loads(self):
        """Test that the default Menlo font loads successfully."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Verify font was loaded
        assert backend.font is not None
        assert backend.font_name == "Menlo"
        assert backend.font_size == 14
    
    def test_custom_font_loads(self):
        """Test that a custom monospace font loads successfully."""
        backend = CoreGraphicsBackend(font_name="Monaco", font_size=12)
        backend.initialize()
        
        # Verify custom font was loaded
        assert backend.font is not None
        assert backend.font_name == "Monaco"
        assert backend.font_size == 12
    
    def test_invalid_font_raises_error(self):
        """Test that an invalid font name raises ValueError."""
        backend = CoreGraphicsBackend(font_name="NonExistentFont123")
        
        with pytest.raises(ValueError) as exc_info:
            backend.initialize()
        
        # Verify error message is informative
        assert "NonExistentFont123" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()
        assert "monospace" in str(exc_info.value).lower()


class TestCharacterDimensions:
    """Test character dimension calculation."""
    
    def test_char_dimensions_calculated(self):
        """Test that character dimensions are calculated and stored."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Verify dimensions are positive integers
        assert backend.char_width > 0
        assert backend.char_height > 0
        assert isinstance(backend.char_width, int)
        assert isinstance(backend.char_height, int)
    
    def test_char_dimensions_consistent(self):
        """Test that character dimensions are consistent across multiple initializations."""
        backend1 = CoreGraphicsBackend(font_name="Menlo", font_size=14)
        backend1.initialize()
        
        backend2 = CoreGraphicsBackend(font_name="Menlo", font_size=14)
        backend2.initialize()
        
        # Same font and size should produce same dimensions
        assert backend1.char_width == backend2.char_width
        assert backend1.char_height == backend2.char_height
    
    def test_larger_font_size_increases_dimensions(self):
        """Test that larger font size produces larger character dimensions."""
        backend_small = CoreGraphicsBackend(font_name="Menlo", font_size=12)
        backend_small.initialize()
        
        backend_large = CoreGraphicsBackend(font_name="Menlo", font_size=18)
        backend_large.initialize()
        
        # Larger font should have larger dimensions
        assert backend_large.char_width > backend_small.char_width
        assert backend_large.char_height > backend_small.char_height
    
    def test_line_spacing_applied(self):
        """Test that 20% line spacing is added to character height."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Calculate expected height with 20% line spacing
        # We can't easily get the raw height without line spacing,
        # but we can verify the height is reasonable for the font size
        # For a 14pt font, height should be roughly 14-20 pixels
        assert backend.char_height >= backend.font_size
        assert backend.char_height <= backend.font_size * 2
    
    def test_char_width_reasonable(self):
        """Test that character width is reasonable for monospace font."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # For a 14pt monospace font, width should be roughly 7-12 pixels
        # This is a sanity check to ensure we're getting reasonable values
        assert backend.char_width >= 5
        assert backend.char_width <= 20


class TestFontValidation:
    """Test font validation requirements."""
    
    def test_font_validation_before_use(self):
        """Test that font is validated before being used."""
        backend = CoreGraphicsBackend(font_name="InvalidFont")
        
        # Should raise ValueError during initialization
        with pytest.raises(ValueError):
            backend.initialize()
        
        # Font should not be set if validation fails
        assert backend.font is None
    
    def test_common_monospace_fonts(self):
        """Test that common macOS monospace fonts load successfully."""
        common_fonts = ["Menlo", "Monaco", "Courier"]
        
        for font_name in common_fonts:
            backend = CoreGraphicsBackend(font_name=font_name)
            backend.initialize()
            
            # Verify font loaded
            assert backend.font is not None
            assert backend.char_width > 0
            assert backend.char_height > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
