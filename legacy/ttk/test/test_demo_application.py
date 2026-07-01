"""
Unit tests for TTK demo application.

Tests the demo application structure including:
- Command-line argument parsing
- Backend selection logic
- Application initialization and shutdown
"""

import platform
import sys
import pytest

from ttk.demo.demo_ttk import DemoApplication, parse_arguments
from ttk.backends.curses_backend import CursesBackend
from ttk.backends.coregraphics_backend import CoreGraphicsBackend


class TestDemoApplication:
    """Test suite for DemoApplication class."""
    
    def test_init_with_auto_backend(self):
        """Test initialization with auto backend selection."""
        app = DemoApplication('auto')
        assert app.backend_name == 'auto'
        assert app.renderer is None
        assert app.running is False
    
    def test_init_with_curses_backend(self):
        """Test initialization with curses backend."""
        app = DemoApplication('curses')
        assert app.backend_name == 'curses'
        assert app.renderer is None
        assert app.running is False
    
    def test_init_with_coregraphics_backend(self):
        """Test initialization with coregraphics backend."""
        app = DemoApplication('coregraphics')
        assert app.backend_name == 'coregraphics'
        assert app.renderer is None
        assert app.running is False
    
    def test_select_backend_curses(self):
        """Test selecting curses backend."""
        app = DemoApplication('curses')
        backend = app.select_backend()
        assert isinstance(backend, CursesBackend)
    
    def test_select_backend_coregraphics(self):
        """Test selecting coregraphics backend."""
        app = DemoApplication('coregraphics')
        backend = app.select_backend()
        assert isinstance(backend, CoreGraphicsBackend)
    
    def test_select_backend_auto_detection(self):
        """Test auto backend detection."""
        app = DemoApplication('auto')
        backend = app.select_backend()
        
        # Should select coregraphics on macOS, curses elsewhere
        if platform.system() == 'Darwin':
            assert isinstance(backend, CoreGraphicsBackend)
            assert app.backend_name == 'coregraphics'
        else:
            assert isinstance(backend, CursesBackend)
            assert app.backend_name == 'curses'
    
    def test_select_backend_invalid(self):
        """Test error handling for invalid backend."""
        app = DemoApplication('invalid')
        
        with pytest.raises(ValueError) as exc_info:
            app.select_backend()
        
        assert "Unknown backend: invalid" in str(exc_info.value)
        assert "Valid options are: curses, coregraphics, auto" in str(exc_info.value)
    
    def test_select_backend_coregraphics_on_non_macos(self, monkeypatch):
        """Test error when selecting coregraphics backend on non-macOS."""
        # Mock platform.system to return non-Darwin
        monkeypatch.setattr(platform, 'system', lambda: 'Linux')
        
        app = DemoApplication('coregraphics')
        
        with pytest.raises(ValueError) as exc_info:
            app.select_backend()
        
        assert "CoreGraphics backend is only available on macOS" in str(exc_info.value)
        assert "Use --backend curses" in str(exc_info.value)


class TestCommandLineArguments:
    """Test suite for command-line argument parsing."""
    
    def test_parse_arguments_default(self, monkeypatch):
        """Test default argument parsing."""
        monkeypatch.setattr(sys, 'argv', ['demo_ttk.py'])
        args = parse_arguments()
        assert args.backend == 'auto'
    
    def test_parse_arguments_curses(self, monkeypatch):
        """Test parsing curses backend argument."""
        monkeypatch.setattr(sys, 'argv', ['demo_ttk.py', '--backend', 'curses'])
        args = parse_arguments()
        assert args.backend == 'curses'
    
    def test_parse_arguments_coregraphics(self, monkeypatch):
        """Test parsing coregraphics backend argument."""
        monkeypatch.setattr(sys, 'argv', ['demo_ttk.py', '--backend', 'coregraphics'])
        args = parse_arguments()
        assert args.backend == 'coregraphics'
    
    def test_parse_arguments_auto(self, monkeypatch):
        """Test parsing auto backend argument."""
        monkeypatch.setattr(sys, 'argv', ['demo_ttk.py', '--backend', 'auto'])
        args = parse_arguments()
        assert args.backend == 'auto'


class TestApplicationLifecycle:
    """Test suite for application lifecycle management."""
    
    def test_running_flag_before_init(self):
        """Test that running flag is False before initialization."""
        app = DemoApplication('curses')
        assert app.running is False
    
    def test_run_without_initialization(self):
        """Test that run() raises error if not initialized."""
        app = DemoApplication('curses')
        
        with pytest.raises(RuntimeError) as exc_info:
            app.run()
        
        assert "Application not initialized" in str(exc_info.value)
        assert "Call initialize() first" in str(exc_info.value)
    
    def test_shutdown_without_renderer(self):
        """Test that shutdown works even without renderer."""
        app = DemoApplication('curses')
        # Should not raise any errors
        app.shutdown()
        assert app.running is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
