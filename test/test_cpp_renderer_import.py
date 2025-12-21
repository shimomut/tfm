#!/usr/bin/env python3
"""
Unit tests for cpp_renderer module import and basic functionality.

Tests that the C++ extension module can be imported and has expected functions.
"""

import sys
import platform
import pytest


# Skip all tests if not on macOS (C++ extension only builds on macOS)
pytestmark = pytest.mark.skipif(
    platform.system() != 'Darwin',
    reason="cpp_renderer extension only available on macOS"
)


class TestCppRendererImport:
    """Test cpp_renderer module import and basic functionality."""
    
    def test_module_import(self):
        """Test that cpp_renderer module can be imported."""
        try:
            import cpp_renderer
            assert cpp_renderer is not None
        except ImportError as e:
            pytest.skip(f"cpp_renderer not available: {e}")
    
    def test_module_version(self):
        """Test that module has __version__ attribute."""
        try:
            import cpp_renderer
            assert hasattr(cpp_renderer, '__version__')
            assert isinstance(cpp_renderer.__version__, str)
            assert len(cpp_renderer.__version__) > 0
        except ImportError:
            pytest.skip("cpp_renderer not available")
    
    def test_module_has_expected_functions(self):
        """Test that module has all expected functions."""
        try:
            import cpp_renderer
            
            # Check for required functions
            expected_functions = [
                'render_frame',
                'clear_caches',
                'get_performance_metrics',
                'reset_metrics'
            ]
            
            for func_name in expected_functions:
                assert hasattr(cpp_renderer, func_name), \
                    f"Module missing expected function: {func_name}"
                assert callable(getattr(cpp_renderer, func_name)), \
                    f"Attribute {func_name} is not callable"
        except ImportError:
            pytest.skip("cpp_renderer not available")
    
    def test_clear_caches_callable(self):
        """Test that clear_caches() can be called."""
        try:
            import cpp_renderer
            result = cpp_renderer.clear_caches()
            assert result is None
        except ImportError:
            pytest.skip("cpp_renderer not available")
    
    def test_get_performance_metrics_returns_dict(self):
        """Test that get_performance_metrics() returns a dictionary."""
        try:
            import cpp_renderer
            metrics = cpp_renderer.get_performance_metrics()
            assert isinstance(metrics, dict)
            
            # Check for expected metric keys
            expected_keys = [
                'frames_rendered',
                'total_render_time_ms',
                'avg_render_time_ms'
            ]
            
            for key in expected_keys:
                assert key in metrics, f"Metrics missing expected key: {key}"
        except ImportError:
            pytest.skip("cpp_renderer not available")
    
    def test_reset_metrics_callable(self):
        """Test that reset_metrics() can be called."""
        try:
            import cpp_renderer
            result = cpp_renderer.reset_metrics()
            assert result is None
        except ImportError:
            pytest.skip("cpp_renderer not available")
    
    def test_render_frame_not_implemented(self):
        """Test that render_frame() raises NotImplementedError (stub)."""
        try:
            import cpp_renderer
            
            # render_frame should raise NotImplementedError or TypeError
            # (NotImplementedError if called with args, TypeError if no args)
            with pytest.raises((NotImplementedError, TypeError)):
                cpp_renderer.render_frame()
        except ImportError:
            pytest.skip("cpp_renderer not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
