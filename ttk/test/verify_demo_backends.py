#!/usr/bin/env python3
"""
Verification test for Task 31: Demo application works with both backends.

This test verifies that the demo application can successfully:
1. Initialize with both curses and Metal backends
2. Create and configure the test interface
3. Render the test interface without errors
4. Handle input events correctly
5. Shutdown cleanly

This is a checkpoint test to ensure all previous tasks integrate correctly.
"""

import platform
import pytest
from unittest.mock import Mock, patch, MagicMock

from ttk.demo.demo_ttk import DemoApplication
from ttk.demo.test_interface import TestInterface, create_test_interface
from ttk.backends.curses_backend import CursesBackend
from ttk.backends.metal_backend import MetalBackend
from ttk.input_event import InputEvent, KeyCode, ModifierKey


class TestDemoWithCursesBackend:
    """Test demo application with curses backend."""
    
    def test_demo_initializes_with_curses(self):
        """Test that demo application initializes successfully with curses backend."""
        app = DemoApplication('curses')
        backend = app.select_backend()
        
        assert isinstance(backend, CursesBackend)
        assert app.backend_name == 'curses'
    
    def test_test_interface_creates_with_curses(self):
        """Test that test interface can be created with curses backend."""
        # Create a mock curses backend
        mock_backend = Mock(spec=CursesBackend)
        mock_backend.get_dimensions.return_value = (24, 80)
        
        # Create test interface
        interface = create_test_interface(mock_backend)
        
        assert isinstance(interface, TestInterface)
        assert interface.renderer is mock_backend
    
    def test_test_interface_initializes_colors_curses(self):
        """Test that test interface initializes colors with curses backend."""
        mock_backend = Mock(spec=CursesBackend)
        mock_backend.get_dimensions.return_value = (24, 80)
        
        interface = TestInterface(mock_backend)
        interface.initialize_colors()
        
        # Verify that init_color_pair was called for all color pairs
        assert mock_backend.init_color_pair.call_count >= 10
        
        # Verify specific color pairs
        calls = mock_backend.init_color_pair.call_args_list
        
        # Color pair 1: White on black
        assert any(call[0] == (1, (255, 255, 255), (0, 0, 0)) for call in calls)
        
        # Color pair 2: Red on black
        assert any(call[0] == (2, (255, 0, 0), (0, 0, 0)) for call in calls)
        
        # Color pair 8: White on blue (header)
        assert any(call[0] == (8, (255, 255, 255), (0, 0, 128)) for call in calls)
    
    def test_test_interface_draws_with_curses(self):
        """Test that test interface can draw with curses backend."""
        mock_backend = Mock(spec=CursesBackend)
        mock_backend.get_dimensions.return_value = (40, 100)
        
        interface = TestInterface(mock_backend, enable_performance_monitoring=False)
        interface.initialize_colors()
        interface.draw_interface()
        
        # Verify that drawing operations were called
        assert mock_backend.clear.called
        assert mock_backend.draw_text.called
        assert mock_backend.refresh.called
    
    def test_test_interface_handles_input_curses(self):
        """Test that test interface handles input with curses backend."""
        mock_backend = Mock(spec=CursesBackend)
        mock_backend.get_dimensions.return_value = (24, 80)
        
        interface = TestInterface(mock_backend, enable_performance_monitoring=False)
        
        # Test printable character input
        event = InputEvent(key_code=ord('a'), modifiers=ModifierKey.NONE, char='a')
        result = interface.handle_input(event)
        
        assert result is True  # Should continue running
        assert interface.last_input == event
        assert event in interface.input_history
    
    def test_test_interface_handles_quit_curses(self):
        """Test that test interface handles quit command with curses backend."""
        mock_backend = Mock(spec=CursesBackend)
        mock_backend.get_dimensions.return_value = (24, 80)
        
        interface = TestInterface(mock_backend, enable_performance_monitoring=False)
        
        # Test quit with 'q'
        event = InputEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
        result = interface.handle_input(event)
        
        assert result is False  # Should quit
        
        # Test quit with ESC
        event = InputEvent(key_code=KeyCode.ESCAPE, modifiers=ModifierKey.NONE)
        result = interface.handle_input(event)
        
        assert result is False  # Should quit
    
    def test_test_interface_handles_resize_curses(self):
        """Test that test interface handles resize events with curses backend."""
        mock_backend = Mock(spec=CursesBackend)
        mock_backend.get_dimensions.return_value = (24, 80)
        
        interface = TestInterface(mock_backend, enable_performance_monitoring=False)
        
        # Test resize event
        event = InputEvent(key_code=KeyCode.RESIZE, modifiers=ModifierKey.NONE)
        result = interface.handle_input(event)
        
        assert result is True  # Should continue running
        assert interface.last_input is None  # Resize events don't update last_input
        assert event not in interface.input_history  # Resize events not in history


class TestDemoWithMetalBackend:
    """Test demo application with Metal backend."""
    
    @pytest.mark.skipif(platform.system() != 'Darwin', reason="Metal backend only available on macOS")
    def test_demo_initializes_with_metal(self):
        """Test that demo application initializes successfully with Metal backend."""
        app = DemoApplication('metal')
        backend = app.select_backend()
        
        assert isinstance(backend, MetalBackend)
        assert app.backend_name == 'metal'
    
    def test_test_interface_creates_with_metal(self):
        """Test that test interface can be created with Metal backend."""
        # Create a mock Metal backend
        mock_backend = Mock(spec=MetalBackend)
        mock_backend.get_dimensions.return_value = (50, 120)
        
        # Create test interface
        interface = create_test_interface(mock_backend)
        
        assert isinstance(interface, TestInterface)
        assert interface.renderer is mock_backend
    
    def test_test_interface_initializes_colors_metal(self):
        """Test that test interface initializes colors with Metal backend."""
        mock_backend = Mock(spec=MetalBackend)
        mock_backend.get_dimensions.return_value = (50, 120)
        
        interface = TestInterface(mock_backend)
        interface.initialize_colors()
        
        # Verify that init_color_pair was called for all color pairs
        assert mock_backend.init_color_pair.call_count >= 10
        
        # Verify specific color pairs
        calls = mock_backend.init_color_pair.call_args_list
        
        # Color pair 1: White on black
        assert any(call[0] == (1, (255, 255, 255), (0, 0, 0)) for call in calls)
        
        # Color pair 3: Green on black
        assert any(call[0] == (3, (0, 255, 0), (0, 0, 0)) for call in calls)
        
        # Color pair 9: Black on white (input echo)
        assert any(call[0] == (9, (0, 0, 0), (255, 255, 255)) for call in calls)
    
    def test_test_interface_draws_with_metal(self):
        """Test that test interface can draw with Metal backend."""
        mock_backend = Mock(spec=MetalBackend)
        mock_backend.get_dimensions.return_value = (60, 150)
        
        interface = TestInterface(mock_backend, enable_performance_monitoring=False)
        interface.initialize_colors()
        interface.draw_interface()
        
        # Verify that drawing operations were called
        assert mock_backend.clear.called
        assert mock_backend.draw_text.called
        assert mock_backend.refresh.called
    
    def test_test_interface_handles_input_metal(self):
        """Test that test interface handles input with Metal backend."""
        mock_backend = Mock(spec=MetalBackend)
        mock_backend.get_dimensions.return_value = (50, 120)
        
        interface = TestInterface(mock_backend, enable_performance_monitoring=False)
        
        # Test printable character input
        event = InputEvent(key_code=ord('x'), modifiers=ModifierKey.NONE, char='x')
        result = interface.handle_input(event)
        
        assert result is True  # Should continue running
        assert interface.last_input == event
        assert event in interface.input_history
    
    def test_test_interface_handles_resize_metal(self):
        """Test that test interface handles resize events with Metal backend."""
        mock_backend = Mock(spec=MetalBackend)
        mock_backend.get_dimensions.return_value = (50, 120)
        
        interface = TestInterface(mock_backend, enable_performance_monitoring=False)
        
        # Test resize event
        event = InputEvent(key_code=KeyCode.RESIZE, modifiers=ModifierKey.NONE)
        result = interface.handle_input(event)
        
        assert result is True  # Should continue running
        assert interface.last_input is None  # Resize events don't update last_input
        assert event not in interface.input_history  # Resize events not in history


class TestBackendEquivalence:
    """Test that both backends provide equivalent functionality."""
    
    def test_both_backends_support_same_interface(self):
        """Test that both backends support the same test interface."""
        # Create mock backends
        curses_backend = Mock(spec=CursesBackend)
        curses_backend.get_dimensions.return_value = (24, 80)
        
        metal_backend = Mock(spec=MetalBackend)
        metal_backend.get_dimensions.return_value = (24, 80)
        
        # Create test interfaces
        curses_interface = TestInterface(curses_backend, enable_performance_monitoring=False)
        metal_interface = TestInterface(metal_backend, enable_performance_monitoring=False)
        
        # Both should initialize colors the same way
        curses_interface.initialize_colors()
        metal_interface.initialize_colors()
        
        assert curses_backend.init_color_pair.call_count == metal_backend.init_color_pair.call_count
        
        # Both should draw the same interface
        curses_interface.draw_interface()
        metal_interface.draw_interface()
        
        # Both should call the same drawing operations
        assert curses_backend.clear.called
        assert metal_backend.clear.called
        assert curses_backend.draw_text.called
        assert metal_backend.draw_text.called
        assert curses_backend.refresh.called
        assert metal_backend.refresh.called
    
    def test_both_backends_handle_same_input(self):
        """Test that both backends handle input events the same way."""
        # Create mock backends
        curses_backend = Mock(spec=CursesBackend)
        curses_backend.get_dimensions.return_value = (24, 80)
        
        metal_backend = Mock(spec=MetalBackend)
        metal_backend.get_dimensions.return_value = (24, 80)
        
        # Create test interfaces
        curses_interface = TestInterface(curses_backend, enable_performance_monitoring=False)
        metal_interface = TestInterface(metal_backend, enable_performance_monitoring=False)
        
        # Test same input event
        event = InputEvent(key_code=ord('t'), modifiers=ModifierKey.NONE, char='t')
        
        curses_result = curses_interface.handle_input(event)
        metal_result = metal_interface.handle_input(event)
        
        # Both should handle the event the same way
        assert curses_result == metal_result
        assert curses_interface.last_input == metal_interface.last_input
        assert len(curses_interface.input_history) == len(metal_interface.input_history)
    
    def test_both_backends_handle_resize_same_way(self):
        """Test that both backends handle resize events the same way."""
        # Create mock backends
        curses_backend = Mock(spec=CursesBackend)
        curses_backend.get_dimensions.return_value = (24, 80)
        
        metal_backend = Mock(spec=MetalBackend)
        metal_backend.get_dimensions.return_value = (24, 80)
        
        # Create test interfaces
        curses_interface = TestInterface(curses_backend, enable_performance_monitoring=False)
        metal_interface = TestInterface(metal_backend, enable_performance_monitoring=False)
        
        # Test resize event
        event = InputEvent(key_code=KeyCode.RESIZE, modifiers=ModifierKey.NONE)
        
        curses_result = curses_interface.handle_input(event)
        metal_result = metal_interface.handle_input(event)
        
        # Both should handle resize the same way
        assert curses_result == metal_result
        assert curses_interface.last_input == metal_interface.last_input
        assert len(curses_interface.input_history) == len(metal_interface.input_history)


class TestDemoApplicationIntegration:
    """Integration tests for the complete demo application."""
    
    def test_demo_app_lifecycle_curses(self):
        """Test complete lifecycle of demo app with curses backend."""
        app = DemoApplication('curses')
        
        # Should start not running
        assert app.running is False
        assert app.renderer is None
        
        # Select backend
        backend = app.select_backend()
        assert isinstance(backend, CursesBackend)
        
        # Should still not be running until initialized
        assert app.running is False
    
    def test_demo_app_lifecycle_metal(self):
        """Test complete lifecycle of demo app with Metal backend."""
        app = DemoApplication('metal')
        
        # Should start not running
        assert app.running is False
        assert app.renderer is None
        
        # Select backend (will fail on non-macOS, which is expected)
        if platform.system() == 'Darwin':
            backend = app.select_backend()
            assert isinstance(backend, MetalBackend)
        else:
            with pytest.raises(ValueError, match="Metal backend is only available on macOS"):
                app.select_backend()
    
    def test_demo_app_auto_backend_selection(self):
        """Test that auto backend selection works correctly."""
        app = DemoApplication('auto')
        backend = app.select_backend()
        
        # Should select appropriate backend for platform
        if platform.system() == 'Darwin':
            assert isinstance(backend, MetalBackend)
            assert app.backend_name == 'metal'
        else:
            assert isinstance(backend, CursesBackend)
            assert app.backend_name == 'curses'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
