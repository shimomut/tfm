#!/usr/bin/env python3
"""
Test: Dynamic Font Size Adjustment

Tests the dynamic font size adjustment feature in CoreGraphics backend.
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if CoreGraphics backend is available
try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
    BACKEND_AVAILABLE = COCOA_AVAILABLE
except ImportError:
    BACKEND_AVAILABLE = False

# Skip all tests if backend not available
pytestmark = pytest.mark.skipif(
    not BACKEND_AVAILABLE,
    reason="CoreGraphics backend not available (requires macOS and PyObjC)"
)


class TestFontSizeAdjustment:
    """Test font size adjustment functionality."""
    
    def test_increase_font_size(self):
        """Test increasing font size."""
        backend = CoreGraphicsBackend(
            window_title="Font Size Test",
            font_size=12,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Get initial font size
            initial_size = backend.font_size
            assert initial_size == 12
            
            # Increase font size
            result = backend.change_font_size(1)
            assert result is True
            assert backend.font_size == 13
            
            # Increase again
            result = backend.change_font_size(2)
            assert result is True
            assert backend.font_size == 15
            
        finally:
            backend.shutdown()
    
    def test_decrease_font_size(self):
        """Test decreasing font size."""
        backend = CoreGraphicsBackend(
            window_title="Font Size Test",
            font_size=14,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Get initial font size
            initial_size = backend.font_size
            assert initial_size == 14
            
            # Decrease font size
            result = backend.change_font_size(-1)
            assert result is True
            assert backend.font_size == 13
            
            # Decrease again
            result = backend.change_font_size(-2)
            assert result is True
            assert backend.font_size == 11
            
        finally:
            backend.shutdown()
    
    def test_font_size_minimum_limit(self):
        """Test that font size cannot go below 8pt."""
        backend = CoreGraphicsBackend(
            window_title="Font Size Test",
            font_size=10,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Decrease to minimum
            result = backend.change_font_size(-2)
            assert result is True
            assert backend.font_size == 8
            
            # Try to go below minimum (should fail)
            result = backend.change_font_size(-1)
            assert result is False
            assert backend.font_size == 8  # Should stay at minimum
            
        finally:
            backend.shutdown()
    
    def test_font_size_maximum_limit(self):
        """Test that font size cannot go above 72pt."""
        backend = CoreGraphicsBackend(
            window_title="Font Size Test",
            font_size=70,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Increase to maximum
            result = backend.change_font_size(2)
            assert result is True
            assert backend.font_size == 72
            
            # Try to go above maximum (should fail)
            result = backend.change_font_size(1)
            assert result is False
            assert backend.font_size == 72  # Should stay at maximum
            
        finally:
            backend.shutdown()
    
    def test_grid_dimensions_unchanged(self):
        """Test that grid dimensions remain constant after font size change."""
        backend = CoreGraphicsBackend(
            window_title="Font Size Test",
            font_size=12,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Get initial dimensions
            initial_rows, initial_cols = backend.get_dimensions()
            assert initial_rows == 24
            assert initial_cols == 80
            
            # Change font size
            backend.change_font_size(4)
            
            # Verify dimensions unchanged
            new_rows, new_cols = backend.get_dimensions()
            assert new_rows == initial_rows
            assert new_cols == initial_cols
            
        finally:
            backend.shutdown()
    
    def test_character_dimensions_updated(self):
        """Test that character dimensions are recalculated after font size change."""
        backend = CoreGraphicsBackend(
            window_title="Font Size Test",
            font_size=12,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Get initial character dimensions
            initial_char_width = backend.char_width
            initial_char_height = backend.char_height
            
            # Increase font size
            backend.change_font_size(4)
            
            # Verify character dimensions increased
            assert backend.char_width > initial_char_width
            assert backend.char_height > initial_char_height
            
        finally:
            backend.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
