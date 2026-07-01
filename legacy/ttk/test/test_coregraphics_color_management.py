"""
Test CoreGraphics backend color pair management.

This test module verifies that the CoreGraphics backend correctly implements
color pair management including:
- Storing RGB color pairs
- Validating color pair IDs (1-255)
- Validating RGB components (0-255)
- Storing color pairs in dictionary
"""

import sys
import pytest

# Check if PyObjC is available
try:
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False

# Skip all tests if PyObjC is not available
pytestmark = pytest.mark.skipif(
    not COCOA_AVAILABLE,
    reason="PyObjC not available - CoreGraphics backend requires macOS with PyObjC"
)

from ttk.backends.coregraphics_backend import CoreGraphicsBackend


class TestColorPairManagement:
    """Test color pair management functionality."""
    
    def test_init_color_pair_stores_colors(self):
        """Test that init_color_pair stores RGB values correctly."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Initialize a color pair with white on blue
        fg_color = (255, 255, 255)
        bg_color = (0, 0, 255)
        backend.init_color_pair(1, fg_color, bg_color)
        
        # Verify the color pair was stored
        assert 1 in backend.color_pairs
        stored_fg, stored_bg = backend.color_pairs[1]
        assert stored_fg == fg_color
        assert stored_bg == bg_color
        
        backend.shutdown()
    
    def test_init_color_pair_multiple_pairs(self):
        """Test storing multiple color pairs."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Initialize multiple color pairs
        pairs = {
            1: ((255, 0, 0), (0, 0, 0)),      # Red on black
            2: ((0, 255, 0), (0, 0, 0)),      # Green on black
            3: ((0, 0, 255), (255, 255, 255)), # Blue on white
            100: ((128, 128, 128), (64, 64, 64)), # Gray on dark gray
            255: ((255, 255, 0), (128, 0, 128))   # Yellow on purple
        }
        
        for pair_id, (fg, bg) in pairs.items():
            backend.init_color_pair(pair_id, fg, bg)
        
        # Verify all pairs were stored correctly
        for pair_id, (fg, bg) in pairs.items():
            assert pair_id in backend.color_pairs
            stored_fg, stored_bg = backend.color_pairs[pair_id]
            assert stored_fg == fg
            assert stored_bg == bg
        
        backend.shutdown()
    
    def test_init_color_pair_overwrites_existing(self):
        """Test that initializing a color pair overwrites existing values."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Initialize a color pair
        backend.init_color_pair(1, (255, 0, 0), (0, 0, 0))
        
        # Overwrite with different colors
        new_fg = (0, 255, 0)
        new_bg = (255, 255, 255)
        backend.init_color_pair(1, new_fg, new_bg)
        
        # Verify the new colors are stored
        stored_fg, stored_bg = backend.color_pairs[1]
        assert stored_fg == new_fg
        assert stored_bg == new_bg
        
        backend.shutdown()
    
    def test_default_color_pair_exists(self):
        """Test that color pair 0 (default) is initialized."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Verify default color pair exists
        assert 0 in backend.color_pairs
        
        # Verify default is white on black
        fg, bg = backend.color_pairs[0]
        assert fg == (255, 255, 255)
        assert bg == (0, 0, 0)
        
        backend.shutdown()
    
    def test_init_color_pair_validates_id_too_low(self):
        """Test that color pair ID < 1 raises ValueError."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Try to initialize color pair 0 (reserved)
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(0, (255, 255, 255), (0, 0, 0))
        
        assert "Color pair ID must be 1-255" in str(exc_info.value)
        assert "got 0" in str(exc_info.value)
        
        # Try negative ID
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(-1, (255, 255, 255), (0, 0, 0))
        
        assert "Color pair ID must be 1-255" in str(exc_info.value)
        
        backend.shutdown()
    
    def test_init_color_pair_validates_id_too_high(self):
        """Test that color pair ID > 255 raises ValueError."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Try to initialize color pair 256
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(256, (255, 255, 255), (0, 0, 0))
        
        assert "Color pair ID must be 1-255" in str(exc_info.value)
        assert "got 256" in str(exc_info.value)
        
        # Try much larger ID
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1000, (255, 255, 255), (0, 0, 0))
        
        assert "Color pair ID must be 1-255" in str(exc_info.value)
        
        backend.shutdown()
    
    def test_init_color_pair_validates_fg_rgb_negative(self):
        """Test that negative RGB components in foreground raise ValueError."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Try negative red component
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (-1, 255, 255), (0, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        assert "foreground color" in str(exc_info.value)
        
        # Try negative green component
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, -10, 255), (0, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        # Try negative blue component
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, -255), (0, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        backend.shutdown()
    
    def test_init_color_pair_validates_fg_rgb_too_high(self):
        """Test that RGB components > 255 in foreground raise ValueError."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Try red component > 255
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (256, 255, 255), (0, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        assert "foreground color" in str(exc_info.value)
        
        # Try green component > 255
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 300, 255), (0, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        # Try blue component > 255
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, 1000), (0, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        backend.shutdown()
    
    def test_init_color_pair_validates_bg_rgb_negative(self):
        """Test that negative RGB components in background raise ValueError."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Try negative red component
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, 255), (-1, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        assert "background color" in str(exc_info.value)
        
        # Try negative green component
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, 255), (0, -50, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        # Try negative blue component
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, 255), (0, 0, -128))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        backend.shutdown()
    
    def test_init_color_pair_validates_bg_rgb_too_high(self):
        """Test that RGB components > 255 in background raise ValueError."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Try red component > 255
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, 255), (256, 0, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        assert "background color" in str(exc_info.value)
        
        # Try green component > 255
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, 255), (0, 500, 0))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        # Try blue component > 255
        with pytest.raises(ValueError) as exc_info:
            backend.init_color_pair(1, (255, 255, 255), (0, 0, 999))
        
        assert "RGB components must be 0-255" in str(exc_info.value)
        
        backend.shutdown()
    
    def test_init_color_pair_boundary_values(self):
        """Test color pair initialization with boundary RGB values."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Test minimum valid values (0, 0, 0)
        backend.init_color_pair(1, (0, 0, 0), (0, 0, 0))
        fg, bg = backend.color_pairs[1]
        assert fg == (0, 0, 0)
        assert bg == (0, 0, 0)
        
        # Test maximum valid values (255, 255, 255)
        backend.init_color_pair(2, (255, 255, 255), (255, 255, 255))
        fg, bg = backend.color_pairs[2]
        assert fg == (255, 255, 255)
        assert bg == (255, 255, 255)
        
        # Test mixed boundary values
        backend.init_color_pair(3, (0, 255, 0), (255, 0, 255))
        fg, bg = backend.color_pairs[3]
        assert fg == (0, 255, 0)
        assert bg == (255, 0, 255)
        
        backend.shutdown()
    
    def test_init_color_pair_all_valid_ids(self):
        """Test that all valid color pair IDs (1-255) can be initialized."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        # Initialize all valid color pair IDs
        for pair_id in range(1, 256):
            # Use pair_id to generate unique colors
            r = pair_id % 256
            g = (pair_id * 2) % 256
            b = (pair_id * 3) % 256
            backend.init_color_pair(pair_id, (r, g, b), (255 - r, 255 - g, 255 - b))
        
        # Verify all pairs were stored
        for pair_id in range(1, 256):
            assert pair_id in backend.color_pairs
        
        # Verify we have 256 color pairs total (0-255)
        assert len(backend.color_pairs) == 256
        
        backend.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
