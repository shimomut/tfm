"""
Test CoreGraphics backend drag-and-drop implementation.

This test verifies that the CoreGraphics backend properly implements
the drag-and-drop interface methods.
"""

import sys
import os

# Add parent directory to path to allow importing ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest


class TestCoreGraphicsDragAndDropInterface:
    """Test CoreGraphics backend drag-and-drop interface implementation."""
    
    def test_supports_drag_and_drop_returns_true(self):
        """Test that CoreGraphics backend supports drag-and-drop."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        # Create backend instance (don't initialize - just test interface)
        backend = CoreGraphicsBackend()
        
        # CoreGraphics backend should support drag-and-drop
        assert backend.supports_drag_and_drop() == True
    
    def test_start_drag_session_exists(self):
        """Test that start_drag_session method exists and is callable."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        backend = CoreGraphicsBackend()
        
        # Method should exist and be callable
        assert hasattr(backend, 'start_drag_session')
        assert callable(backend.start_drag_session)
    
    def test_set_drag_completion_callback_exists(self):
        """Test that set_drag_completion_callback method exists and is callable."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        backend = CoreGraphicsBackend()
        
        # Method should exist and be callable
        assert hasattr(backend, 'set_drag_completion_callback')
        assert callable(backend.set_drag_completion_callback)
    
    def test_set_drag_completion_callback_stores_callback(self):
        """Test that set_drag_completion_callback stores the callback."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        backend = CoreGraphicsBackend()
        
        # Create a test callback
        callback_called = []
        def test_callback(completed):
            callback_called.append(completed)
        
        # Set the callback
        backend.set_drag_completion_callback(test_callback)
        
        # Verify callback is stored
        assert hasattr(backend, 'drag_completion_callback')
        assert backend.drag_completion_callback == test_callback
    
    def test_start_drag_session_returns_false_without_initialization(self):
        """Test that start_drag_session returns False when backend not initialized."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        backend = CoreGraphicsBackend()
        
        # Should return False when view is not initialized
        result = backend.start_drag_session(
            ["file:///tmp/test.txt"],
            "test.txt"
        )
        
        assert result == False
    
    def test_internal_callback_invokes_user_callback(self):
        """Test that internal callback properly invokes user callback."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        backend = CoreGraphicsBackend()
        
        # Create a test callback
        callback_results = []
        def test_callback(completed):
            callback_results.append(completed)
        
        # Set the callback
        backend.set_drag_completion_callback(test_callback)
        
        # Simulate internal callback invocation (as C++ extension would do)
        backend._on_drag_completed_internal(True)
        
        # Verify user callback was invoked with correct parameter
        assert len(callback_results) == 1
        assert callback_results[0] == True
        
        # Test cancellation
        backend._on_drag_completed_internal(False)
        assert len(callback_results) == 2
        assert callback_results[1] == False
    
    def test_internal_callback_handles_missing_user_callback(self):
        """Test that internal callback handles case when user callback not set."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        backend = CoreGraphicsBackend()
        
        # Don't set a user callback
        # Internal callback should not crash
        try:
            backend._on_drag_completed_internal(True)
            # Should succeed without error
        except Exception as e:
            pytest.fail(f"Internal callback should not raise exception: {e}")
    
    def test_internal_callback_handles_callback_exceptions(self):
        """Test that internal callback handles exceptions from user callback."""
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        except ImportError:
            pytest.skip("CoreGraphics backend not available (PyObjC not installed)")
        
        backend = CoreGraphicsBackend()
        
        # Create a callback that raises an exception
        def bad_callback(completed):
            raise ValueError("Test exception")
        
        backend.set_drag_completion_callback(bad_callback)
        
        # Internal callback should catch and handle the exception
        try:
            backend._on_drag_completed_internal(True)
            # Should succeed without propagating the exception
        except ValueError:
            pytest.fail("Internal callback should catch user callback exceptions")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
