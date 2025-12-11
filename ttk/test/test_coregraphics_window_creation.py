"""
Tests for CoreGraphics backend window creation and setup.

This module tests the window creation functionality including:
- Window dimension calculation from grid size and character dimensions
- NSWindow creation with proper style mask
- Window title setting
- Window control configuration (close, minimize, resize)
"""

import sys
import pytest

# Skip all tests if not on macOS
pytestmark = pytest.mark.skipif(
    sys.platform != 'darwin',
    reason="CoreGraphics backend only available on macOS"
)

# Try to import CoreGraphics backend
try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
    import Cocoa
except ImportError:
    COCOA_AVAILABLE = False
    CoreGraphicsBackend = None
    Cocoa = None

# Skip if PyObjC not available
pytestmark = pytest.mark.skipif(
    not COCOA_AVAILABLE,
    reason="PyObjC not installed"
)


class TestWindowCreation:
    """Test window creation and setup functionality."""
    
    def test_window_creation_basic(self):
        """Test that window is created successfully."""
        backend = CoreGraphicsBackend(window_title="Test Window")
        backend.initialize()
        
        try:
            # Verify window was created
            assert backend.window is not None
            assert isinstance(backend.window, Cocoa.NSWindow)
        finally:
            backend.shutdown()
    
    def test_window_title_set(self):
        """Test that window title is set correctly."""
        title = "My Test Application"
        backend = CoreGraphicsBackend(window_title=title)
        backend.initialize()
        
        try:
            # Verify window title matches
            assert backend.window.title() == title
        finally:
            backend.shutdown()
    
    def test_window_dimensions_calculated(self):
        """Test that window dimensions are calculated from grid and character size."""
        rows, cols = 30, 100
        backend = CoreGraphicsBackend(rows=rows, cols=cols)
        backend.initialize()
        
        try:
            # Get window content size
            content_rect = backend.window.contentView().frame()
            window_width = content_rect.size.width
            window_height = content_rect.size.height
            
            # Verify dimensions match grid * character size
            expected_width = cols * backend.char_width
            expected_height = rows * backend.char_height
            
            # Allow small rounding differences
            assert abs(window_width - expected_width) < 2
            assert abs(window_height - expected_height) < 2
        finally:
            backend.shutdown()
    
    def test_window_style_mask_includes_close(self):
        """Test that window has close button."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            style_mask = backend.window.styleMask()
            # Check that closable flag is set
            assert style_mask & Cocoa.NSWindowStyleMaskClosable
        finally:
            backend.shutdown()
    
    def test_window_style_mask_includes_minimize(self):
        """Test that window has minimize button."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            style_mask = backend.window.styleMask()
            # Check that miniaturizable flag is set
            assert style_mask & Cocoa.NSWindowStyleMaskMiniaturizable
        finally:
            backend.shutdown()
    
    def test_window_style_mask_includes_resize(self):
        """Test that window is resizable."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            style_mask = backend.window.styleMask()
            # Check that resizable flag is set
            assert style_mask & Cocoa.NSWindowStyleMaskResizable
        finally:
            backend.shutdown()
    
    def test_window_style_mask_includes_title_bar(self):
        """Test that window has title bar."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            style_mask = backend.window.styleMask()
            # Check that titled flag is set
            assert style_mask & Cocoa.NSWindowStyleMaskTitled
        finally:
            backend.shutdown()
    
    def test_get_dimensions_returns_grid_size(self):
        """Test that get_dimensions returns correct grid size."""
        rows, cols = 25, 90
        backend = CoreGraphicsBackend(rows=rows, cols=cols)
        backend.initialize()
        
        try:
            dimensions = backend.get_dimensions()
            assert dimensions == (rows, cols)
        finally:
            backend.shutdown()
    
    def test_get_dimensions_positive_integers(self):
        """Test that get_dimensions returns positive integers."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            rows, cols = backend.get_dimensions()
            assert isinstance(rows, int)
            assert isinstance(cols, int)
            assert rows > 0
            assert cols > 0
        finally:
            backend.shutdown()
    
    def test_window_visible_after_initialization(self):
        """Test that window is visible after initialization."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            # Window should be visible (isVisible returns True)
            assert backend.window.isVisible()
        finally:
            backend.shutdown()
    
    def test_multiple_window_titles(self):
        """Test creating windows with different titles."""
        titles = ["Window 1", "Test App", "CoreGraphics Demo"]
        
        for title in titles:
            backend = CoreGraphicsBackend(window_title=title)
            backend.initialize()
            
            try:
                assert backend.window.title() == title
            finally:
                backend.shutdown()
    
    def test_window_content_view_set(self):
        """Test that window has a content view."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            content_view = backend.window.contentView()
            assert content_view is not None
            assert backend.view is not None
        finally:
            backend.shutdown()


class TestGridInitialization:
    """Test character grid initialization."""
    
    def test_grid_initialized(self):
        """Test that character grid is initialized."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            assert backend.grid is not None
            assert isinstance(backend.grid, list)
            assert len(backend.grid) == backend.rows
        finally:
            backend.shutdown()
    
    def test_grid_dimensions_match(self):
        """Test that grid dimensions match specified rows and cols."""
        rows, cols = 30, 100
        backend = CoreGraphicsBackend(rows=rows, cols=cols)
        backend.initialize()
        
        try:
            assert len(backend.grid) == rows
            for row in backend.grid:
                assert len(row) == cols
        finally:
            backend.shutdown()
    
    def test_grid_cells_initialized_empty(self):
        """Test that grid cells are initialized with space character."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            # Check a few cells
            for row_idx in range(min(5, backend.rows)):
                for col_idx in range(min(5, backend.cols)):
                    cell = backend.grid[row_idx][col_idx]
                    assert isinstance(cell, tuple)
                    assert len(cell) == 3
                    char, color_pair, attributes = cell
                    assert char == ' '
                    assert color_pair == 0
                    assert attributes == 0
        finally:
            backend.shutdown()
    
    def test_default_color_pair_initialized(self):
        """Test that default color pair (0) is initialized."""
        backend = CoreGraphicsBackend()
        backend.initialize()
        
        try:
            assert 0 in backend.color_pairs
            fg, bg = backend.color_pairs[0]
            # Default should be white on black
            assert fg == (255, 255, 255)
            assert bg == (0, 0, 0)
        finally:
            backend.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
