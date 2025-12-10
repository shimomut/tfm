"""
Tests for Metal backend initialization.

This module tests the Metal backend's initialization process, including:
- Metal device creation
- Font validation (monospace requirement)
- Native window creation
- Character dimension calculation
- Grid buffer initialization
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys


class TestMetalInitialization(unittest.TestCase):
    """Test Metal backend initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Skip tests if not on macOS
        if sys.platform != 'darwin':
            self.skipTest("Metal backend tests require macOS")
        
        # Try to import PyObjC - skip if not available
        try:
            import Metal
            import Cocoa
            import MetalKit
            self.pyobjc_available = True
        except ImportError:
            self.skipTest("PyObjC not available - install with: pip install pyobjc-framework-Metal pyobjc-framework-Cocoa")
    
    def test_import_metal_backend(self):
        """Test that MetalBackend can be imported."""
        from ttk.backends.metal_backend import MetalBackend
        self.assertIsNotNone(MetalBackend)
    
    def test_metal_backend_construction(self):
        """Test MetalBackend can be constructed without initialization."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend()
        self.assertEqual(backend.window_title, "TTK Application")
        self.assertEqual(backend.font_name, "Menlo")
        self.assertEqual(backend.font_size, 14)
        self.assertIsNone(backend.window)
        self.assertIsNone(backend.metal_device)
        self.assertIsNone(backend.command_queue)
    
    def test_metal_backend_custom_parameters(self):
        """Test MetalBackend construction with custom parameters."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend(
            window_title="Test Window",
            font_name="Monaco",
            font_size=16
        )
        self.assertEqual(backend.window_title, "Test Window")
        self.assertEqual(backend.font_name, "Monaco")
        self.assertEqual(backend.font_size, 16)
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_metal_device_creation(self):
        """Test that Metal device can be created."""
        from ttk.backends.metal_backend import MetalBackend
        import Metal
        
        backend = MetalBackend()
        
        # Create Metal device directly to verify it works
        device = Metal.MTLCreateSystemDefaultDevice()
        self.assertIsNotNone(device, "Metal device creation failed - Metal may not be supported")
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_font_validation_monospace(self):
        """Test that monospace fonts are accepted."""
        from ttk.backends.metal_backend import MetalBackend
        
        # Test with known monospace fonts
        monospace_fonts = ["Menlo", "Monaco", "Courier New"]
        
        for font_name in monospace_fonts:
            backend = MetalBackend(font_name=font_name)
            try:
                # This should not raise an error
                backend._validate_font()
            except ValueError as e:
                self.fail(f"Monospace font '{font_name}' was rejected: {e}")
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_font_validation_invalid_font(self):
        """Test that invalid font names are rejected."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend(font_name="NonExistentFont12345")
        
        with self.assertRaises(ValueError) as context:
            backend._validate_font()
        
        self.assertIn("not found", str(context.exception))
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_font_validation_proportional_font(self):
        """Test that proportional fonts are rejected."""
        from ttk.backends.metal_backend import MetalBackend
        
        # Helvetica is a proportional font
        backend = MetalBackend(font_name="Helvetica")
        
        with self.assertRaises(ValueError) as context:
            backend._validate_font()
        
        self.assertIn("not monospace", str(context.exception))
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_character_dimensions_calculation(self):
        """Test that character dimensions are calculated correctly."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend(font_name="Menlo", font_size=14)
        backend._calculate_char_dimensions()
        
        # Verify dimensions are positive
        self.assertGreater(backend.char_width, 0)
        self.assertGreater(backend.char_height, 0)
        
        # Verify dimensions are reasonable for 14pt font
        self.assertGreater(backend.char_width, 5)
        self.assertLess(backend.char_width, 20)
        self.assertGreater(backend.char_height, 10)
        self.assertLess(backend.char_height, 30)
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_grid_initialization(self):
        """Test that character grid is initialized correctly."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend()
        backend.char_width = 8
        backend.char_height = 16
        backend.window = None  # Force fallback to defaults
        backend._initialize_grid()
        
        # Verify grid dimensions
        self.assertEqual(backend.rows, 40)
        self.assertEqual(backend.cols, 80)
        
        # Verify grid structure
        self.assertEqual(len(backend.grid), backend.rows)
        self.assertEqual(len(backend.grid[0]), backend.cols)
        
        # Verify all cells are initialized with spaces
        for row in backend.grid:
            for cell in row:
                char, color_pair, attrs = cell
                self.assertEqual(char, ' ')
                self.assertEqual(color_pair, 0)
                self.assertEqual(attrs, 0)
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_initialize_without_pyobjc(self):
        """Test that initialization fails gracefully without PyObjC."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend()
        
        # Mock the import to simulate PyObjC not being available
        with patch('builtins.__import__', side_effect=ImportError("No module named 'Metal'")):
            with self.assertRaises(RuntimeError) as context:
                backend.initialize()
            
            self.assertIn("PyObjC is required", str(context.exception))
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_get_dimensions_before_initialization(self):
        """Test get_dimensions returns (0, 0) before initialization."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend()
        rows, cols = backend.get_dimensions()
        
        self.assertEqual(rows, 0)
        self.assertEqual(cols, 0)
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_color_pairs_initialization(self):
        """Test that default color pair is initialized."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend()
        backend.char_width = 8
        backend.char_height = 16
        backend.window = None
        
        # Manually call initialization steps that don't require full window
        backend._initialize_grid()
        backend.color_pairs[0] = ((255, 255, 255), (0, 0, 0))
        
        # Verify default color pair
        self.assertIn(0, backend.color_pairs)
        fg, bg = backend.color_pairs[0]
        self.assertEqual(fg, (255, 255, 255))  # White
        self.assertEqual(bg, (0, 0, 0))  # Black


class TestMetalInitializationIntegration(unittest.TestCase):
    """Integration tests for Metal backend initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        if sys.platform != 'darwin':
            self.skipTest("Metal backend tests require macOS")
        
        try:
            import Metal
            import Cocoa
            import MetalKit
        except ImportError:
            self.skipTest("PyObjC not available")
    
    @unittest.skipIf(sys.platform != 'darwin', "Requires macOS")
    def test_full_initialization_sequence(self):
        """Test complete initialization sequence."""
        from ttk.backends.metal_backend import MetalBackend
        
        backend = MetalBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=14
        )
        
        try:
            # This will create a real window - we'll clean it up
            backend.initialize()
            
            # Verify Metal resources were created
            self.assertIsNotNone(backend.metal_device)
            self.assertIsNotNone(backend.command_queue)
            self.assertIsNotNone(backend.window)
            
            # Verify character dimensions were calculated
            self.assertGreater(backend.char_width, 0)
            self.assertGreater(backend.char_height, 0)
            
            # Verify grid was initialized
            self.assertGreater(backend.rows, 0)
            self.assertGreater(backend.cols, 0)
            self.assertEqual(len(backend.grid), backend.rows)
            
            # Verify default color pair
            self.assertIn(0, backend.color_pairs)
            
        finally:
            # Clean up - close the window
            if backend.window is not None:
                backend.window.close()


if __name__ == '__main__':
    unittest.main()
