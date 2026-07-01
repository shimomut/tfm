"""
Test Curses backend drag-and-drop graceful degradation.

This test verifies that the Curses backend properly implements the
drag-and-drop interface with graceful degradation (returns False).
"""

import sys
import os

# Add parent directory to path to allow importing ttk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ttk.backends.curses_backend import CursesBackend


class TestCursesDragAndDropGracefulDegradation:
    """Test cases for Curses backend drag-and-drop graceful degradation."""
    
    def test_curses_supports_drag_and_drop_returns_false(self):
        """Test that Curses backend reports no drag-and-drop support."""
        backend = CursesBackend()
        assert backend.supports_drag_and_drop() == False
    
    def test_curses_start_drag_session_returns_false(self, capsys):
        """Test that Curses backend start_drag_session returns False and logs message."""
        backend = CursesBackend()
        
        # Attempt to start drag session
        result = backend.start_drag_session(
            ["file:///tmp/test.txt"],
            "test.txt"
        )
        
        # Should return False
        assert result == False
        
        # Should log informational message
        captured = capsys.readouterr()
        assert "Drag-and-drop not supported in terminal mode" in captured.out
    
    def test_curses_set_drag_completion_callback_is_noop(self):
        """Test that Curses backend set_drag_completion_callback is a no-op."""
        backend = CursesBackend()
        
        # Should not raise exception
        callback_called = False
        
        def test_callback(completed):
            nonlocal callback_called
            callback_called = True
        
        # Set callback (should be no-op)
        backend.set_drag_completion_callback(test_callback)
        
        # Callback should never be invoked since drag-and-drop not supported
        assert callback_called == False
    
    def test_curses_drag_methods_work_without_initialization(self):
        """Test that drag methods can be called without initializing curses."""
        backend = CursesBackend()
        
        # Should not raise exception even without initialize()
        assert backend.supports_drag_and_drop() == False
        assert backend.start_drag_session([], "test") == False
        backend.set_drag_completion_callback(lambda completed: None)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
