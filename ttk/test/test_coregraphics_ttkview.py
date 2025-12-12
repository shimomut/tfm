"""
Test TTKView custom NSView class implementation.

This test verifies that the TTKView class is properly implemented as an NSView
subclass with the required methods for backend integration and keyboard input.

Requirements tested:
- 8.1: TTKView is created as NSView subclass
- 8.5: TTKView stores backend reference via initWithFrame_backend_
- 6.5: TTKView implements acceptsFirstResponder to return True
"""

import sys
import pytest

# Skip all tests if not on macOS
pytestmark = pytest.mark.skipif(
    sys.platform != 'darwin',
    reason="CoreGraphics backend only available on macOS"
)

try:
    import Cocoa
    import objc
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False

if COCOA_AVAILABLE:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, TTKView


@pytest.mark.skipif(not COCOA_AVAILABLE, reason="PyObjC not available")
class TestTTKView:
    """Test suite for TTKView class."""
    
    def test_ttkview_is_nsview_subclass(self):
        """
        Test that TTKView is a proper NSView subclass.
        
        Requirement 8.1: TTKView class is created as NSView subclass
        """
        # Verify TTKView is a subclass of NSView
        assert issubclass(TTKView, Cocoa.NSView), \
            "TTKView must be a subclass of NSView"
    
    def test_ttkview_initialization(self):
        """
        Test that TTKView can be initialized with frame and backend.
        
        Requirement 8.5: TTKView implements initWithFrame_backend_ to store backend reference
        """
        # Create a mock backend (just needs to be an object)
        backend = CoreGraphicsBackend()
        
        # Create a frame
        frame = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Initialize the view
        view = TTKView.alloc().initWithFrame_backend_(frame, backend)
        
        # Verify view was created
        assert view is not None, "TTKView should be successfully initialized"
        
        # Verify backend reference is stored
        assert hasattr(view, 'backend'), "TTKView should store backend reference"
        assert view.backend is backend, "TTKView should store the correct backend reference"
    
    def test_ttkview_accepts_first_responder(self):
        """
        Test that TTKView accepts first responder status for keyboard input.
        
        Requirement 6.5: TTKView implements acceptsFirstResponder to return True
        """
        # Create a mock backend
        backend = CoreGraphicsBackend()
        
        # Create a frame
        frame = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Initialize the view
        view = TTKView.alloc().initWithFrame_backend_(frame, backend)
        
        # Verify acceptsFirstResponder returns True
        assert view.acceptsFirstResponder() is True, \
            "TTKView must return True from acceptsFirstResponder to receive keyboard input"
    
    def test_ttkview_has_drawrect_method(self):
        """
        Test that TTKView has a drawRect_ method for rendering.
        
        This verifies the method exists, even if it's not fully implemented yet.
        """
        # Create a mock backend
        backend = CoreGraphicsBackend()
        
        # Create a frame
        frame = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Initialize the view
        view = TTKView.alloc().initWithFrame_backend_(frame, backend)
        
        # Verify drawRect_ method exists
        assert hasattr(view, 'drawRect_'), "TTKView must have drawRect_ method"
        assert callable(view.drawRect_), "drawRect_ must be callable"
    
    def test_ttkview_integration_with_backend(self):
        """
        Test that TTKView integrates properly with CoreGraphicsBackend.
        
        This test verifies that when a backend is initialized, it creates
        a TTKView instance and sets it as the window's content view.
        """
        # Create backend
        backend = CoreGraphicsBackend(window_title="Test Window")
        
        # Initialize backend (creates window and view)
        backend.initialize()
        
        try:
            # Verify view was created
            assert backend.view is not None, "Backend should create a view"
            
            # Verify view is a TTKView instance
            assert isinstance(backend.view, TTKView), \
                "Backend should create a TTKView instance"
            
            # Verify view has backend reference
            assert backend.view.backend is backend, \
                "View should have reference to backend"
            
            # Verify view is set as window's content view
            assert backend.window.contentView() is backend.view, \
                "View should be set as window's content view"
            
        finally:
            # Clean up
            if backend.window:
                backend.window.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
