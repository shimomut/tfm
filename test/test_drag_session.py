"""
Tests for drag session manager.

Run with: PYTHONPATH=.:src:ttk pytest test/test_drag_session.py -v
"""

import pytest

from tfm_drag_session import DragSessionManager, DragState


class MockBackend:
    """Mock backend for testing."""
    
    def __init__(self, supports_drag=True, start_success=True):
        self.supports_drag = supports_drag
        self.start_success = start_success
        self.started_urls = None
        self.started_text = None
        self.drag_completion_callback = None
    
    def supports_drag_and_drop(self):
        return self.supports_drag
    
    def start_drag_session(self, urls, drag_image_text):
        self.started_urls = urls
        self.started_text = drag_image_text
        return self.start_success
    
    def set_drag_completion_callback(self, callback):
        self.drag_completion_callback = callback


class TestDragSessionManager:
    """Test DragSessionManager class."""
    
    def test_initial_state(self):
        """Test initial state of manager."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        assert manager.state == DragState.IDLE
        assert not manager.is_dragging()
    
    def test_start_drag_success(self):
        """Test successful drag start."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        urls = ["file:///path/to/file.txt"]
        result = manager.start_drag(urls, "1 file")
        
        assert result
        assert manager.is_dragging()
        assert manager.state == DragState.DRAGGING
        assert backend.started_urls == urls
        assert backend.started_text == "1 file"
    
    def test_start_drag_with_callback(self):
        """Test drag start with completion callback."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        callback_called = []
        def callback(completed):
            callback_called.append(completed)
        
        urls = ["file:///path/to/file.txt"]
        result = manager.start_drag(urls, "1 file", completion_callback=callback)
        
        assert result
        assert manager.completion_callback == callback
    
    def test_start_drag_fails_without_backend_support(self):
        """Test drag start fails when backend doesn't support it."""
        backend = MockBackend(supports_drag=False)
        manager = DragSessionManager(backend)
        
        urls = ["file:///path/to/file.txt"]
        result = manager.start_drag(urls, "1 file")
        
        assert not result
        assert not manager.is_dragging()
    
    def test_start_drag_fails_when_backend_fails(self):
        """Test drag start fails when backend fails."""
        backend = MockBackend(start_success=False)
        manager = DragSessionManager(backend)
        
        urls = ["file:///path/to/file.txt"]
        result = manager.start_drag(urls, "1 file")
        
        assert not result
        assert not manager.is_dragging()
    
    def test_start_drag_fails_when_already_dragging(self):
        """Test that starting drag while dragging fails."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        urls = ["file:///path/to/file.txt"]
        manager.start_drag(urls, "1 file")
        
        # Try to start another drag
        result = manager.start_drag(urls, "1 file")
        
        assert not result
    
    def test_handle_drag_completed(self):
        """Test handling drag completion."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        callback_called = []
        def callback(completed):
            callback_called.append(completed)
        
        urls = ["file:///path/to/file.txt"]
        manager.start_drag(urls, "1 file", completion_callback=callback)
        
        manager.handle_drag_completed()
        
        assert manager.state == DragState.IDLE
        assert not manager.is_dragging()
        assert callback_called == [True]
        assert manager.current_urls is None
        assert manager.completion_callback is None
    
    def test_handle_drag_cancelled(self):
        """Test handling drag cancellation."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        callback_called = []
        def callback(completed):
            callback_called.append(completed)
        
        urls = ["file:///path/to/file.txt"]
        manager.start_drag(urls, "1 file", completion_callback=callback)
        
        manager.handle_drag_cancelled()
        
        assert manager.state == DragState.IDLE
        assert not manager.is_dragging()
        assert callback_called == [False]
        assert manager.current_urls is None
        assert manager.completion_callback is None
    
    def test_completion_without_callback(self):
        """Test completion without callback doesn't crash."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        urls = ["file:///path/to/file.txt"]
        manager.start_drag(urls, "1 file")
        
        # Should not crash
        manager.handle_drag_completed()
        
        assert manager.state == DragState.IDLE
    
    def test_cancellation_without_callback(self):
        """Test cancellation without callback doesn't crash."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        urls = ["file:///path/to/file.txt"]
        manager.start_drag(urls, "1 file")
        
        # Should not crash
        manager.handle_drag_cancelled()
        
        assert manager.state == DragState.IDLE
    
    def test_completion_when_not_dragging_does_nothing(self):
        """Test that completion when not dragging does nothing."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        # Should not crash
        manager.handle_drag_completed()
        
        assert manager.state == DragState.IDLE
    
    def test_cancellation_when_not_dragging_does_nothing(self):
        """Test that cancellation when not dragging does nothing."""
        backend = MockBackend()
        manager = DragSessionManager(backend)
        
        # Should not crash
        manager.handle_drag_cancelled()
        
        assert manager.state == DragState.IDLE
