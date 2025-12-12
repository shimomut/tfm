"""
Test CoreGraphics Backend API Compliance

This test suite verifies that the CoreGraphics backend properly implements
the Renderer abstract interface and maintains API compatibility.

Tests cover:
- Inheritance from Renderer base class
- Implementation of all abstract methods
- Method signature compliance
- Exception type consistency
- Backend compatibility with Renderer-based applications

Requirements tested: 17.1, 17.2, 17.3, 17.4, 17.5
"""

import sys
import inspect
from typing import get_type_hints

# Skip tests if not on macOS
if sys.platform != 'darwin':
    import pytest
    pytestmark = pytest.skip("CoreGraphics backend only available on macOS")

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from ttk.renderer import Renderer, TextAttribute
    from ttk.input_event import InputEvent
    COREGRAPHICS_AVAILABLE = True
except ImportError:
    COREGRAPHICS_AVAILABLE = False
    import pytest
    pytestmark = pytest.skip("CoreGraphics backend not available")


class TestInheritance:
    """Test that CoreGraphicsBackend properly inherits from Renderer."""
    
    def test_inherits_from_renderer(self):
        """Verify CoreGraphicsBackend inherits from Renderer base class."""
        # Requirement 17.1: Backend SHALL inherit from abstract Renderer base class
        assert issubclass(CoreGraphicsBackend, Renderer), \
            "CoreGraphicsBackend must inherit from Renderer"
    
    def test_is_instance_of_renderer(self):
        """Verify CoreGraphicsBackend instances are Renderer instances."""
        backend = CoreGraphicsBackend(
            window_title="Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        assert isinstance(backend, Renderer), \
            "CoreGraphicsBackend instance must be an instance of Renderer"


class TestAbstractMethodImplementation:
    """Test that all abstract methods from Renderer are implemented."""
    
    def test_all_abstract_methods_implemented(self):
        """Verify all abstract methods from Renderer are implemented."""
        # Requirement 17.2: All abstract methods SHALL be implemented
        
        # Get all abstract methods from Renderer
        abstract_methods = set()
        for name, method in inspect.getmembers(Renderer, predicate=inspect.isfunction):
            if getattr(method, '__isabstractmethod__', False):
                abstract_methods.add(name)
        
        # Verify each abstract method is implemented in CoreGraphicsBackend
        for method_name in abstract_methods:
            assert hasattr(CoreGraphicsBackend, method_name), \
                f"CoreGraphicsBackend must implement abstract method '{method_name}'"
            
            method = getattr(CoreGraphicsBackend, method_name)
            assert callable(method), \
                f"'{method_name}' must be callable"
            
            # Verify it's not still abstract
            assert not getattr(method, '__isabstractmethod__', False), \
                f"'{method_name}' is still marked as abstract"
    
    def test_initialize_implemented(self):
        """Verify initialize() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'initialize')
        assert callable(CoreGraphicsBackend.initialize)
    
    def test_shutdown_implemented(self):
        """Verify shutdown() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'shutdown')
        assert callable(CoreGraphicsBackend.shutdown)
    
    def test_get_dimensions_implemented(self):
        """Verify get_dimensions() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'get_dimensions')
        assert callable(CoreGraphicsBackend.get_dimensions)
    
    def test_clear_implemented(self):
        """Verify clear() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'clear')
        assert callable(CoreGraphicsBackend.clear)
    
    def test_clear_region_implemented(self):
        """Verify clear_region() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'clear_region')
        assert callable(CoreGraphicsBackend.clear_region)
    
    def test_draw_text_implemented(self):
        """Verify draw_text() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'draw_text')
        assert callable(CoreGraphicsBackend.draw_text)
    
    def test_draw_hline_implemented(self):
        """Verify draw_hline() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'draw_hline')
        assert callable(CoreGraphicsBackend.draw_hline)
    
    def test_draw_vline_implemented(self):
        """Verify draw_vline() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'draw_vline')
        assert callable(CoreGraphicsBackend.draw_vline)
    
    def test_draw_rect_implemented(self):
        """Verify draw_rect() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'draw_rect')
        assert callable(CoreGraphicsBackend.draw_rect)
    
    def test_refresh_implemented(self):
        """Verify refresh() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'refresh')
        assert callable(CoreGraphicsBackend.refresh)
    
    def test_refresh_region_implemented(self):
        """Verify refresh_region() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'refresh_region')
        assert callable(CoreGraphicsBackend.refresh_region)
    
    def test_init_color_pair_implemented(self):
        """Verify init_color_pair() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'init_color_pair')
        assert callable(CoreGraphicsBackend.init_color_pair)
    
    def test_get_input_implemented(self):
        """Verify get_input() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'get_input')
        assert callable(CoreGraphicsBackend.get_input)
    
    def test_set_cursor_visibility_implemented(self):
        """Verify set_cursor_visibility() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'set_cursor_visibility')
        assert callable(CoreGraphicsBackend.set_cursor_visibility)
    
    def test_move_cursor_implemented(self):
        """Verify move_cursor() method is implemented."""
        assert hasattr(CoreGraphicsBackend, 'move_cursor')
        assert callable(CoreGraphicsBackend.move_cursor)


class TestMethodSignatures:
    """Test that method signatures match the Renderer interface."""
    
    def test_initialize_signature(self):
        """Verify initialize() has correct signature."""
        # Requirement 17.2: Method signatures SHALL match Renderer interface
        sig = inspect.signature(CoreGraphicsBackend.initialize)
        params = list(sig.parameters.keys())
        assert params == ['self'], \
            f"initialize() signature mismatch: expected ['self'], got {params}"
    
    def test_shutdown_signature(self):
        """Verify shutdown() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.shutdown)
        params = list(sig.parameters.keys())
        assert params == ['self'], \
            f"shutdown() signature mismatch: expected ['self'], got {params}"
    
    def test_get_dimensions_signature(self):
        """Verify get_dimensions() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.get_dimensions)
        params = list(sig.parameters.keys())
        assert params == ['self'], \
            f"get_dimensions() signature mismatch: expected ['self'], got {params}"
    
    def test_clear_signature(self):
        """Verify clear() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.clear)
        params = list(sig.parameters.keys())
        assert params == ['self'], \
            f"clear() signature mismatch: expected ['self'], got {params}"
    
    def test_clear_region_signature(self):
        """Verify clear_region() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.clear_region)
        params = list(sig.parameters.keys())
        assert params == ['self', 'row', 'col', 'height', 'width'], \
            f"clear_region() signature mismatch: expected ['self', 'row', 'col', 'height', 'width'], got {params}"
    
    def test_draw_text_signature(self):
        """Verify draw_text() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.draw_text)
        params = list(sig.parameters.keys())
        assert params == ['self', 'row', 'col', 'text', 'color_pair', 'attributes'], \
            f"draw_text() signature mismatch"
        
        # Check default values
        assert sig.parameters['color_pair'].default == 0
        assert sig.parameters['attributes'].default == 0
    
    def test_draw_hline_signature(self):
        """Verify draw_hline() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.draw_hline)
        params = list(sig.parameters.keys())
        assert params == ['self', 'row', 'col', 'char', 'length', 'color_pair'], \
            f"draw_hline() signature mismatch"
        
        # Check default value
        assert sig.parameters['color_pair'].default == 0
    
    def test_draw_vline_signature(self):
        """Verify draw_vline() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.draw_vline)
        params = list(sig.parameters.keys())
        assert params == ['self', 'row', 'col', 'char', 'length', 'color_pair'], \
            f"draw_vline() signature mismatch"
        
        # Check default value
        assert sig.parameters['color_pair'].default == 0
    
    def test_draw_rect_signature(self):
        """Verify draw_rect() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.draw_rect)
        params = list(sig.parameters.keys())
        assert params == ['self', 'row', 'col', 'height', 'width', 'color_pair', 'filled'], \
            f"draw_rect() signature mismatch"
        
        # Check default values
        assert sig.parameters['color_pair'].default == 0
        assert sig.parameters['filled'].default == False
    
    def test_refresh_signature(self):
        """Verify refresh() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.refresh)
        params = list(sig.parameters.keys())
        assert params == ['self'], \
            f"refresh() signature mismatch: expected ['self'], got {params}"
    
    def test_refresh_region_signature(self):
        """Verify refresh_region() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.refresh_region)
        params = list(sig.parameters.keys())
        assert params == ['self', 'row', 'col', 'height', 'width'], \
            f"refresh_region() signature mismatch"
    
    def test_init_color_pair_signature(self):
        """Verify init_color_pair() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.init_color_pair)
        params = list(sig.parameters.keys())
        assert params == ['self', 'pair_id', 'fg_color', 'bg_color'], \
            f"init_color_pair() signature mismatch"
    
    def test_get_input_signature(self):
        """Verify get_input() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.get_input)
        params = list(sig.parameters.keys())
        assert params == ['self', 'timeout_ms'], \
            f"get_input() signature mismatch"
        
        # Check default value
        assert sig.parameters['timeout_ms'].default == -1
    
    def test_set_cursor_visibility_signature(self):
        """Verify set_cursor_visibility() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.set_cursor_visibility)
        params = list(sig.parameters.keys())
        assert params == ['self', 'visible'], \
            f"set_cursor_visibility() signature mismatch"
    
    def test_move_cursor_signature(self):
        """Verify move_cursor() has correct signature."""
        sig = inspect.signature(CoreGraphicsBackend.move_cursor)
        params = list(sig.parameters.keys())
        assert params == ['self', 'row', 'col'], \
            f"move_cursor() signature mismatch"


class TestExceptionTypes:
    """Test that the backend uses consistent exception types."""
    
    def test_invalid_font_raises_value_error(self):
        """Verify invalid font name raises ValueError."""
        # Requirement 17.4: SHALL use same exception types as other backends
        try:
            backend = CoreGraphicsBackend(
                window_title="Test",
                font_name="NonExistentFont12345",
                font_size=14,
                rows=24,
                cols=80
            )
            backend.initialize()
            assert False, "Should have raised ValueError for invalid font"
        except ValueError as e:
            assert "font" in str(e).lower() or "NonExistentFont12345" in str(e)
        except Exception as e:
            assert False, f"Should raise ValueError, not {type(e).__name__}"
    
    def test_invalid_color_pair_id_raises_value_error(self):
        """Verify invalid color pair ID raises ValueError."""
        backend = CoreGraphicsBackend(
            window_title="Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Test color pair ID 0 (reserved)
            backend.init_color_pair(0, (255, 255, 255), (0, 0, 0))
            assert False, "Should have raised ValueError for color pair 0"
        except ValueError:
            pass
        except Exception as e:
            assert False, f"Should raise ValueError, not {type(e).__name__}"
        finally:
            backend.shutdown()
    
    def test_invalid_rgb_component_raises_value_error(self):
        """Verify invalid RGB component raises ValueError."""
        backend = CoreGraphicsBackend(
            window_title="Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        backend.initialize()
        
        try:
            # Test RGB component > 255
            backend.init_color_pair(1, (256, 0, 0), (0, 0, 0))
            assert False, "Should have raised ValueError for RGB > 255"
        except ValueError:
            pass
        except Exception as e:
            assert False, f"Should raise ValueError, not {type(e).__name__}"
        finally:
            backend.shutdown()
    
    def test_pyobjc_missing_raises_runtime_error(self):
        """Verify missing PyObjC raises RuntimeError with instructions."""
        # This test verifies the error handling code path
        # We can't actually test it without uninstalling PyObjC,
        # but we can verify the code structure exists
        import ttk.backends.coregraphics_backend as cg_module
        
        # Verify COCOA_AVAILABLE flag exists
        assert hasattr(cg_module, 'COCOA_AVAILABLE')
        
        # Verify the module checks this flag
        source = inspect.getsource(cg_module.CoreGraphicsBackend.initialize)
        assert 'COCOA_AVAILABLE' in source or 'RuntimeError' in source, \
            "initialize() should check COCOA_AVAILABLE and raise RuntimeError"


class TestRendererCompatibility:
    """Test that the backend works with Renderer-based applications."""
    
    def test_can_be_used_as_renderer(self):
        """Verify backend can be used anywhere Renderer is expected."""
        # Requirement 17.3: SHALL work with any Renderer-based application
        
        def use_renderer(renderer: Renderer):
            """Example function that expects a Renderer."""
            renderer.initialize()
            rows, cols = renderer.get_dimensions()
            renderer.clear()
            renderer.draw_text(0, 0, "Test")
            renderer.refresh()
            renderer.shutdown()
            return rows, cols
        
        backend = CoreGraphicsBackend(
            window_title="Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        
        # This should work without any type errors
        rows, cols = use_renderer(backend)
        assert rows == 24
        assert cols == 80
    
    def test_polymorphic_usage(self):
        """Verify backend supports polymorphic usage."""
        # Create backend as Renderer type
        backend: Renderer = CoreGraphicsBackend(
            window_title="Test",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        
        # All Renderer methods should be accessible
        backend.initialize()
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))
        backend.draw_text(0, 0, "Hello", color_pair=1)
        backend.refresh()
        backend.shutdown()
    
    def test_backend_switching(self):
        """Verify applications can switch backends without code changes."""
        # Requirement 17.5: Applications should work with any backend
        
        def create_backend(backend_type: str) -> Renderer:
            """Factory function that creates different backends."""
            if backend_type == "coregraphics":
                return CoreGraphicsBackend(
                    window_title="Test",
                    font_name="Menlo",
                    font_size=14,
                    rows=24,
                    cols=80
                )
            else:
                raise ValueError(f"Unknown backend: {backend_type}")
        
        # Application code that works with any backend
        backend = create_backend("coregraphics")
        backend.initialize()
        
        # Use standard Renderer interface
        rows, cols = backend.get_dimensions()
        assert rows == 24
        assert cols == 80
        
        backend.clear()
        backend.draw_text(0, 0, "Backend-agnostic code")
        backend.refresh()
        backend.shutdown()


class TestInitializationParameters:
    """Test that initialization parameters match API documentation."""
    
    def test_accepts_standard_parameters(self):
        """Verify backend accepts standard initialization parameters."""
        # Requirement 17.5: SHALL accept same initialization parameters
        
        # Test with all parameters
        backend = CoreGraphicsBackend(
            window_title="My Application",
            font_name="Menlo",
            font_size=14,
            rows=30,
            cols=100
        )
        backend.initialize()
        
        rows, cols = backend.get_dimensions()
        assert rows == 30
        assert cols == 100
        
        backend.shutdown()
    
    def test_default_parameters(self):
        """Verify backend works with default parameters."""
        # Test with minimal parameters
        backend = CoreGraphicsBackend(
            window_title="Test",
            font_name="Menlo",
            font_size=14
        )
        backend.initialize()
        
        # Should have default dimensions
        rows, cols = backend.get_dimensions()
        assert rows > 0
        assert cols > 0
        
        backend.shutdown()


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
