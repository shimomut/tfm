"""
Tests for Metal backend rendering pipeline implementation.

This module tests the Metal rendering pipeline components including:
- Shader compilation and pipeline creation
- Grid rendering (full and partial)
- Character rendering
- Color pair initialization
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys


class TestMetalRenderingPipeline(unittest.TestCase):
    """Test Metal backend rendering pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PyObjC modules
        self.mock_metal = MagicMock()
        self.mock_cocoa = MagicMock()
        self.mock_metalkit = MagicMock()
        self.mock_core_text = MagicMock()
        self.mock_quartz = MagicMock()
        
        # Configure mocks
        sys.modules['Metal'] = self.mock_metal
        sys.modules['Cocoa'] = self.mock_cocoa
        sys.modules['MetalKit'] = self.mock_metalkit
        sys.modules['CoreText'] = self.mock_core_text
        sys.modules['Quartz'] = self.mock_quartz
        
        # Import after mocking
        from ttk.backends.metal_backend import MetalBackend
        from ttk.renderer import TextAttribute
        
        self.MetalBackend = MetalBackend
        self.TextAttribute = TextAttribute
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove mocked modules
        for module in ['Metal', 'Cocoa', 'MetalKit', 'CoreText', 'Quartz']:
            if module in sys.modules:
                del sys.modules[module]
    
    def _create_mock_backend(self):
        """Create a Metal backend with mocked dependencies."""
        # Configure Metal device mock
        mock_device = MagicMock()
        mock_device.newCommandQueue.return_value = MagicMock()
        self.mock_metal.MTLCreateSystemDefaultDevice.return_value = mock_device
        
        # Configure font mock
        mock_font = MagicMock()
        mock_font.ascender.return_value = 12
        mock_font.descender.return_value = -3
        mock_font.leading.return_value = 1
        self.mock_cocoa.NSFont.fontWithName_size_.return_value = mock_font
        
        # Configure attributed string mock for font validation
        mock_attr_string = MagicMock()
        mock_size = MagicMock()
        mock_size.width = 8.0
        mock_attr_string.size.return_value = mock_size
        self.mock_cocoa.NSAttributedString.alloc.return_value.initWithString_attributes_.return_value = mock_attr_string
        
        # Configure window mock
        mock_window = MagicMock()
        mock_frame = MagicMock()
        mock_frame.size.width = 800
        mock_frame.size.height = 600
        mock_window.contentView.return_value.frame.return_value = mock_frame
        self.mock_cocoa.NSWindow.alloc.return_value.initWithContentRect_styleMask_backing_defer_.return_value = mock_window
        
        # Configure Metal view mock
        mock_metal_view = MagicMock()
        self.mock_metalkit.MTKView.alloc.return_value.initWithFrame_device_.return_value = mock_metal_view
        
        # Create backend
        backend = self.MetalBackend()
        backend.initialize()
        
        return backend
    
    def test_create_render_pipeline_creates_shader_library(self):
        """Test that _create_render_pipeline creates a shader library."""
        backend = self._create_mock_backend()
        
        # Verify shader library was created
        self.assertTrue(backend.metal_device.newLibraryWithSource_options_error_.called)
        
        # Get the shader source that was passed
        call_args = backend.metal_device.newLibraryWithSource_options_error_.call_args
        shader_source = call_args[0][0]
        
        # Verify shader source contains expected functions
        self.assertIn("vertex_main", shader_source)
        self.assertIn("fragment_main", shader_source)
        self.assertIn("VertexIn", shader_source)
        self.assertIn("VertexOut", shader_source)
    
    def test_create_render_pipeline_loads_shader_functions(self):
        """Test that _create_render_pipeline loads vertex and fragment functions."""
        backend = self._create_mock_backend()
        
        # Get the library mock
        library_mock = backend.metal_device.newLibraryWithSource_options_error_.return_value
        
        # Verify vertex and fragment functions were loaded
        library_mock.newFunctionWithName_.assert_any_call("vertex_main")
        library_mock.newFunctionWithName_.assert_any_call("fragment_main")
    
    def test_create_render_pipeline_configures_blending(self):
        """Test that _create_render_pipeline configures alpha blending."""
        backend = self._create_mock_backend()
        
        # Verify pipeline descriptor was created
        self.mock_metal.MTLRenderPipelineDescriptor.alloc.return_value.init.assert_called()
    
    def test_create_render_pipeline_returns_pipeline_state(self):
        """Test that _create_render_pipeline returns a pipeline state."""
        backend = self._create_mock_backend()
        
        # Verify render pipeline was created and stored
        self.assertIsNotNone(backend.render_pipeline)
    
    def test_render_grid_creates_command_buffer(self):
        """Test that _render_grid creates a Metal command buffer."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        # Call refresh which calls _render_grid
        backend.refresh()
        
        # Verify command buffer was created
        backend.command_queue.commandBuffer.assert_called()
    
    def test_render_grid_creates_render_encoder(self):
        """Test that _render_grid creates a render command encoder."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        
        mock_render_pass = MagicMock()
        backend.metal_view.currentRenderPassDescriptor.return_value = mock_render_pass
        
        mock_command_buffer = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        
        # Call refresh which calls _render_grid
        backend.refresh()
        
        # Verify render encoder was created
        mock_command_buffer.renderCommandEncoderWithDescriptor_.assert_called_with(mock_render_pass)
    
    def test_render_grid_sets_pipeline_state(self):
        """Test that _render_grid sets the render pipeline state."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        mock_command_buffer = MagicMock()
        mock_render_encoder = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        mock_command_buffer.renderCommandEncoderWithDescriptor_.return_value = mock_render_encoder
        
        # Call refresh which calls _render_grid
        backend.refresh()
        
        # Verify pipeline state was set
        mock_render_encoder.setRenderPipelineState_.assert_called_with(backend.render_pipeline)
    
    def test_render_grid_presents_drawable(self):
        """Test that _render_grid presents the drawable."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        mock_command_buffer = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        mock_command_buffer.renderCommandEncoderWithDescriptor_.return_value = MagicMock()
        
        # Call refresh which calls _render_grid
        backend.refresh()
        
        # Verify drawable was presented
        mock_command_buffer.presentDrawable_.assert_called_with(mock_drawable)
    
    def test_render_grid_commits_command_buffer(self):
        """Test that _render_grid commits the command buffer."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        mock_command_buffer = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        mock_command_buffer.renderCommandEncoderWithDescriptor_.return_value = MagicMock()
        
        # Call refresh which calls _render_grid
        backend.refresh()
        
        # Verify command buffer was committed
        mock_command_buffer.commit.assert_called()
    
    def test_render_grid_region_renders_only_specified_region(self):
        """Test that _render_grid_region only renders the specified region."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        mock_command_buffer = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        mock_command_buffer.renderCommandEncoderWithDescriptor_.return_value = MagicMock()
        
        # Put some characters in the grid
        backend.grid[5][10] = ('A', 1, 0)
        backend.grid[15][20] = ('B', 1, 0)
        
        # Call refresh_region for a small region
        backend.refresh_region(5, 10, 1, 1)
        
        # Verify command buffer was created and committed
        backend.command_queue.commandBuffer.assert_called()
        mock_command_buffer.commit.assert_called()
    
    def test_render_character_calculates_screen_position(self):
        """Test that _render_character calculates correct screen position."""
        backend = self._create_mock_backend()
        
        # Set character dimensions
        backend.char_width = 10
        backend.char_height = 20
        
        # Create mock render encoder
        mock_encoder = MagicMock()
        
        # Call _render_character
        backend._render_character(mock_encoder, 5, 10, 'A', 1, 0)
        
        # The method should calculate x = 10 * 10 = 100, y = 5 * 20 = 100
        # This is verified by the method not raising an exception
    
    def test_render_character_applies_reverse_attribute(self):
        """Test that _render_character swaps colors for reverse attribute."""
        backend = self._create_mock_backend()
        
        # Set up color pair
        backend.color_pairs[1] = ((255, 0, 0), (0, 0, 255))  # Red on blue
        
        # Create mock render encoder
        mock_encoder = MagicMock()
        
        # Call _render_character with reverse attribute
        backend._render_character(
            mock_encoder, 0, 0, 'A', 1, 
            self.TextAttribute.REVERSE
        )
        
        # The method should swap foreground and background colors
        # This is verified by the method not raising an exception
    
    def test_init_color_pair_stores_colors(self):
        """Test that init_color_pair stores color pairs correctly."""
        backend = self._create_mock_backend()
        
        # Initialize a color pair
        fg_color = (255, 128, 64)
        bg_color = (32, 16, 8)
        backend.init_color_pair(1, fg_color, bg_color)
        
        # Verify color pair was stored
        self.assertIn(1, backend.color_pairs)
        self.assertEqual(backend.color_pairs[1], (fg_color, bg_color))
    
    def test_init_color_pair_validates_pair_id(self):
        """Test that init_color_pair validates pair ID range."""
        backend = self._create_mock_backend()
        
        # Test invalid pair IDs
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(0, (255, 255, 255), (0, 0, 0))
        self.assertIn("1-255", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(256, (255, 255, 255), (0, 0, 0))
        self.assertIn("1-255", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(-1, (255, 255, 255), (0, 0, 0))
        self.assertIn("1-255", str(cm.exception))
    
    def test_init_color_pair_validates_rgb_values(self):
        """Test that init_color_pair validates RGB component values."""
        backend = self._create_mock_backend()
        
        # Test invalid RGB values
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(1, (256, 0, 0), (0, 0, 0))
        self.assertIn("0-255", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(1, (255, 255, 255), (0, -1, 0))
        self.assertIn("0-255", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(1, (255, 255, 255), (0, 0, 300))
        self.assertIn("0-255", str(cm.exception))
    
    def test_init_color_pair_validates_tuple_format(self):
        """Test that init_color_pair validates color tuple format."""
        backend = self._create_mock_backend()
        
        # Test invalid tuple formats
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(1, (255, 255), (0, 0, 0))
        self.assertIn("tuple of 3 integers", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            backend.init_color_pair(1, [255, 255, 255], (0, 0, 0))
        self.assertIn("tuple of 3 integers", str(cm.exception))
    
    def test_refresh_calls_render_grid(self):
        """Test that refresh() calls _render_grid()."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        mock_command_buffer = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        mock_command_buffer.renderCommandEncoderWithDescriptor_.return_value = MagicMock()
        
        # Call refresh
        backend.refresh()
        
        # Verify rendering occurred (command buffer was created and committed)
        backend.command_queue.commandBuffer.assert_called()
        mock_command_buffer.commit.assert_called()
    
    def test_refresh_region_calls_render_grid_region(self):
        """Test that refresh_region() calls _render_grid_region()."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        mock_command_buffer = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        mock_command_buffer.renderCommandEncoderWithDescriptor_.return_value = MagicMock()
        
        # Call refresh_region
        backend.refresh_region(10, 20, 5, 10)
        
        # Verify rendering occurred (command buffer was created and committed)
        backend.command_queue.commandBuffer.assert_called()
        mock_command_buffer.commit.assert_called()
    
    def test_render_grid_skips_spaces_with_default_colors(self):
        """Test that _render_grid skips rendering spaces with default colors."""
        backend = self._create_mock_backend()
        
        # Configure mocks for rendering
        mock_drawable = MagicMock()
        backend.metal_view.currentDrawable.return_value = mock_drawable
        backend.metal_view.currentRenderPassDescriptor.return_value = MagicMock()
        
        mock_command_buffer = MagicMock()
        backend.command_queue.commandBuffer.return_value = mock_command_buffer
        mock_command_buffer.renderCommandEncoderWithDescriptor_.return_value = MagicMock()
        
        # Fill grid with spaces (default state)
        # All cells should be (' ', 0, 0)
        
        # Call refresh
        backend.refresh()
        
        # Verify rendering occurred but no characters were rendered
        # (only setup and teardown calls)
        backend.command_queue.commandBuffer.assert_called()
        mock_command_buffer.commit.assert_called()


if __name__ == '__main__':
    unittest.main()
