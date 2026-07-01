"""
Test CoreGraphics backend initialization.

This test verifies that the CoreGraphicsBackend class can be instantiated
with the correct parameters and that all instance variables are properly
initialized.
"""

import sys
import pytest

# Try to import the backend
try:
    from backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
except ImportError as e:
    pytest.skip(f"CoreGraphics backend not available: {e}", allow_module_level=True)


class TestCoreGraphicsInitialization:
    """Test CoreGraphicsBackend initialization."""
    
    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        if not COCOA_AVAILABLE:
            pytest.skip("PyObjC not available")
        
        backend = CoreGraphicsBackend()
        
        # Verify default parameters
        assert backend.window_title == "TTK Application"
        assert backend.font_name == "Menlo"
        assert backend.font_size == 14
        assert backend.rows == 24
        assert backend.cols == 80
        
        # Verify instance variables are initialized
        assert backend.window is None
        assert backend.view is None
        assert backend.font is None
        assert backend.char_width == 0
        assert backend.char_height == 0
        assert backend.grid == []
        assert backend.color_pairs == {}
    
    def test_initialization_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        if not COCOA_AVAILABLE:
            pytest.skip("PyObjC not available")
        
        backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Monaco",
            font_size=16,
            rows=30,
            cols=100
        )
        
        # Verify custom parameters
        assert backend.window_title == "Test Window"
        assert backend.font_name == "Monaco"
        assert backend.font_size == 16
        assert backend.rows == 30
        assert backend.cols == 100
        
        # Verify instance variables are initialized
        assert backend.window is None
        assert backend.view is None
        assert backend.font is None
        assert backend.char_width == 0
        assert backend.char_height == 0
        assert backend.grid == []
        assert backend.color_pairs == {}
    
    def test_pyobjc_not_available_error(self):
        """Test that RuntimeError is raised when PyObjC is not available."""
        # This test can only run if PyObjC is actually not available
        # We'll skip it if PyObjC is available
        if COCOA_AVAILABLE:
            pytest.skip("PyObjC is available, cannot test missing dependency")
        
        with pytest.raises(RuntimeError) as exc_info:
            CoreGraphicsBackend()
        
        assert "PyObjC is required" in str(exc_info.value)
        assert "pip install pyobjc-framework-Cocoa" in str(exc_info.value)
    
    def test_inherits_from_renderer(self):
        """Test that CoreGraphicsBackend inherits from Renderer."""
        if not COCOA_AVAILABLE:
            pytest.skip("PyObjC not available")
        
        # Check that the backend has the Renderer base class
        backend = CoreGraphicsBackend()
        # Verify it has all the abstract methods from Renderer
        assert hasattr(backend, 'initialize')
        assert hasattr(backend, 'shutdown')
        assert hasattr(backend, 'get_dimensions')
        assert hasattr(backend, 'clear')
        assert hasattr(backend, 'draw_text')
        assert hasattr(backend, 'refresh')
        assert hasattr(backend, 'init_color_pair')
        assert hasattr(backend, 'get_input')
        
        # Check the class hierarchy
        assert 'Renderer' in [base.__name__ for base in type(backend).__mro__]
    
    def test_instance_variable_types(self):
        """Test that instance variables have correct types."""
        if not COCOA_AVAILABLE:
            pytest.skip("PyObjC not available")
        
        backend = CoreGraphicsBackend()
        
        # Check types
        assert isinstance(backend.window_title, str)
        assert isinstance(backend.font_name, str)
        assert isinstance(backend.font_size, int)
        assert isinstance(backend.rows, int)
        assert isinstance(backend.cols, int)
        assert isinstance(backend.grid, list)
        assert isinstance(backend.color_pairs, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
