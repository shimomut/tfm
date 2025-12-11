"""
Tests for Metal backend shutdown functionality.

This module tests the shutdown() method of the MetalBackend class,
verifying proper cleanup of all Metal resources, window closure,
and state reset.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from ttk.backends.metal_backend import MetalBackend


class TestMetalShutdown:
    """Test suite for Metal backend shutdown functionality."""
    
    def test_shutdown_closes_window(self):
        """Test that shutdown closes the native window."""
        backend = MetalBackend()
        
        # Mock the window
        mock_window = Mock()
        backend.window = mock_window
        
        # Call shutdown
        backend.shutdown()
        
        # Verify window.close() was called
        mock_window.close.assert_called_once()
        
        # Verify window reference is cleared
        assert backend.window is None
    
    def test_shutdown_handles_window_close_error(self):
        """Test that shutdown handles errors when closing window."""
        backend = MetalBackend()
        
        # Mock window that raises error on close
        mock_window = Mock()
        mock_window.close.side_effect = RuntimeError("Window already closed")
        backend.window = mock_window
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Window reference should still be cleared
        assert backend.window is None
    
    def test_shutdown_handles_attribute_error(self):
        """Test that shutdown handles AttributeError during window close."""
        backend = MetalBackend()
        
        # Mock window that raises AttributeError
        mock_window = Mock()
        mock_window.close.side_effect = AttributeError("No close method")
        backend.window = mock_window
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Window reference should still be cleared
        assert backend.window is None
    
    def test_shutdown_clears_metal_view(self):
        """Test that shutdown clears metal_view reference."""
        backend = MetalBackend()
        
        # Set metal_view
        backend.metal_view = Mock()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify metal_view is cleared
        assert backend.metal_view is None
    
    def test_shutdown_releases_render_pipeline(self):
        """Test that shutdown releases the render pipeline."""
        backend = MetalBackend()
        
        # Set render pipeline
        backend.render_pipeline = Mock()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify render pipeline is released
        assert backend.render_pipeline is None
    
    def test_shutdown_releases_command_queue(self):
        """Test that shutdown releases the command queue."""
        backend = MetalBackend()
        
        # Set command queue
        backend.command_queue = Mock()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify command queue is released
        assert backend.command_queue is None
    
    def test_shutdown_releases_metal_device(self):
        """Test that shutdown releases the Metal device."""
        backend = MetalBackend()
        
        # Set Metal device
        backend.metal_device = Mock()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify Metal device is released
        assert backend.metal_device is None
    
    def test_shutdown_clears_character_grid(self):
        """Test that shutdown clears the character grid buffer."""
        backend = MetalBackend()
        
        # Set up grid with some data
        backend.grid = [
            [('a', 0, 0), ('b', 0, 0)],
            [('c', 0, 0), ('d', 0, 0)]
        ]
        
        # Call shutdown
        backend.shutdown()
        
        # Verify grid is cleared
        assert backend.grid == []
    
    def test_shutdown_clears_color_pairs(self):
        """Test that shutdown clears color pair storage."""
        backend = MetalBackend()
        
        # Set up color pairs
        backend.color_pairs = {
            0: ((255, 255, 255), (0, 0, 0)),
            1: ((255, 0, 0), (0, 0, 0)),
            2: ((0, 255, 0), (0, 0, 0))
        }
        
        # Call shutdown
        backend.shutdown()
        
        # Verify color pairs are cleared
        assert backend.color_pairs == {}
    
    def test_shutdown_resets_dimensions(self):
        """Test that shutdown resets dimension values."""
        backend = MetalBackend()
        
        # Set dimensions
        backend.rows = 40
        backend.cols = 120
        backend.char_width = 10
        backend.char_height = 20
        
        # Call shutdown
        backend.shutdown()
        
        # Verify dimensions are reset
        assert backend.rows == 0
        assert backend.cols == 0
        assert backend.char_width == 0
        assert backend.char_height == 0
    
    def test_shutdown_resets_cursor_state(self):
        """Test that shutdown resets cursor state."""
        backend = MetalBackend()
        
        # Set cursor state
        backend.cursor_visible = True
        backend.cursor_row = 10
        backend.cursor_col = 20
        
        # Call shutdown
        backend.shutdown()
        
        # Verify cursor state is reset
        assert backend.cursor_visible is False
        assert backend.cursor_row == 0
        assert backend.cursor_col == 0
    
    def test_shutdown_without_initialization(self):
        """Test that shutdown works even if initialize() was never called."""
        backend = MetalBackend()
        
        # Call shutdown without initializing
        # Should not raise any exceptions
        backend.shutdown()
        
        # Verify all resources are in clean state
        assert backend.window is None
        assert backend.metal_device is None
        assert backend.command_queue is None
        assert backend.render_pipeline is None
        assert backend.grid == []
        assert backend.color_pairs == {}
        assert backend.rows == 0
        assert backend.cols == 0
    
    def test_shutdown_multiple_times(self):
        """Test that shutdown can be called multiple times safely."""
        backend = MetalBackend()
        
        # Set up some resources
        backend.window = Mock()
        backend.metal_device = Mock()
        backend.grid = [['a', 'b'], ['c', 'd']]
        
        # Call shutdown first time
        backend.shutdown()
        
        # Call shutdown second time - should not raise exception
        backend.shutdown()
        
        # Verify state is still clean
        assert backend.window is None
        assert backend.metal_device is None
        assert backend.grid == []
    
    def test_shutdown_clears_all_resources_together(self):
        """Test that shutdown clears all resources in one call."""
        backend = MetalBackend()
        
        # Set up all resources
        backend.window = Mock()
        backend.metal_view = Mock()
        backend.render_pipeline = Mock()
        backend.command_queue = Mock()
        backend.metal_device = Mock()
        backend.grid = [['a', 'b']]
        backend.color_pairs = {0: ((255, 255, 255), (0, 0, 0))}
        backend.rows = 40
        backend.cols = 120
        backend.char_width = 10
        backend.char_height = 20
        backend.cursor_visible = True
        backend.cursor_row = 5
        backend.cursor_col = 10
        
        # Call shutdown once
        backend.shutdown()
        
        # Verify all resources are cleared
        assert backend.window is None
        assert backend.metal_view is None
        assert backend.render_pipeline is None
        assert backend.command_queue is None
        assert backend.metal_device is None
        assert backend.grid == []
        assert backend.color_pairs == {}
        assert backend.rows == 0
        assert backend.cols == 0
        assert backend.char_width == 0
        assert backend.char_height == 0
        assert backend.cursor_visible is False
        assert backend.cursor_row == 0
        assert backend.cursor_col == 0
    
    def test_shutdown_with_partial_initialization(self):
        """Test shutdown when only some resources were initialized."""
        backend = MetalBackend()
        
        # Partially initialize - only some resources
        backend.metal_device = Mock()
        backend.command_queue = Mock()
        # window and render_pipeline remain None
        
        # Shutdown should handle this gracefully
        backend.shutdown()
        
        # Verify all resources are cleared
        assert backend.metal_device is None
        assert backend.command_queue is None
        assert backend.window is None
        assert backend.render_pipeline is None
    
    def test_shutdown_preserves_configuration(self):
        """Test that shutdown preserves initial configuration parameters."""
        backend = MetalBackend(
            window_title="Test Window",
            font_name="Monaco",
            font_size=16
        )
        
        # Set up resources
        backend.window = Mock()
        backend.metal_device = Mock()
        
        # Call shutdown
        backend.shutdown()
        
        # Verify configuration is preserved
        assert backend.window_title == "Test Window"
        assert backend.font_name == "Monaco"
        assert backend.font_size == 16
    
    def test_shutdown_handles_unexpected_exception(self):
        """Test that shutdown handles unexpected exceptions during cleanup."""
        backend = MetalBackend()
        
        # Mock window that raises unexpected exception
        mock_window = Mock()
        mock_window.close.side_effect = ValueError("Unexpected error")
        backend.window = mock_window
        
        # Shutdown should not raise exception
        backend.shutdown()
        
        # Window reference should still be cleared
        assert backend.window is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
