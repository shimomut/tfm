"""
Drag session lifecycle management for TFM drag-and-drop support.

This module provides the DragSessionManager class which manages the lifecycle
of drag-and-drop operations, including state tracking, backend coordination,
and resource cleanup.
"""

from enum import Enum
from typing import List, Optional, Callable
from tfm_log_manager import getLogger


class DragState(Enum):
    """Drag session states."""
    IDLE = "idle"
    DRAGGING = "dragging"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DragSessionManager:
    """Manages drag-and-drop session lifecycle."""
    
    def __init__(self, backend):
        """
        Initialize drag session manager.
        
        Args:
            backend: TTK backend instance that supports drag-and-drop
        """
        self.backend = backend
        self.state = DragState.IDLE
        self.current_urls: Optional[List[str]] = None
        self.completion_callback: Optional[Callable] = None
        self.logger = getLogger("DragSession")
    
    def start_drag(
        self,
        urls: List[str],
        drag_image_text: str,
        completion_callback: Optional[Callable] = None
    ) -> bool:
        """
        Start a drag session.
        
        Args:
            urls: List of file:// URLs to drag
            drag_image_text: Text to display in drag image
            completion_callback: Called when drag completes (receives bool: True if completed, False if cancelled)
            
        Returns:
            True if drag started successfully, False otherwise
        """
        if self.state != DragState.IDLE:
            self.logger.warning(f"Cannot start drag in state: {self.state}")
            return False
        
        # Check backend support
        if not self.backend.supports_drag_and_drop():
            self.logger.info("Backend does not support drag-and-drop (terminal mode)")
            return False
        
        # Start native drag session
        try:
            success = self.backend.start_drag_session(urls, drag_image_text)
            if not success:
                self.logger.error("Failed to start native drag session - OS rejected the drag operation")
                return False
        except Exception as e:
            self.logger.error(f"Exception starting drag session: {e}")
            return False
        
        self.state = DragState.DRAGGING
        self.current_urls = urls
        self.completion_callback = completion_callback
        self.logger.info(f"Started drag session with {len(urls)} files")
        return True
    
    def handle_drag_completed(self) -> None:
        """Handle drag session completion."""
        if self.state != DragState.DRAGGING:
            return
        
        self.logger.info("Drag session completed")
        self.state = DragState.COMPLETED
        
        if self.completion_callback:
            try:
                self.completion_callback(completed=True)
            except Exception as e:
                self.logger.error(f"Error in completion callback: {e}")
        
        self._cleanup()
    
    def handle_drag_cancelled(self) -> None:
        """Handle drag session cancellation."""
        if self.state != DragState.DRAGGING:
            return
        
        self.logger.info("Drag session cancelled")
        self.state = DragState.CANCELLED
        
        if self.completion_callback:
            try:
                self.completion_callback(completed=False)
            except Exception as e:
                self.logger.error(f"Error in cancellation callback: {e}")
        
        self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up drag session resources."""
        self.current_urls = None
        self.completion_callback = None
        self.state = DragState.IDLE
    
    def is_dragging(self) -> bool:
        """
        Check if drag is in progress.
        
        Returns:
            True if currently dragging, False otherwise
        """
        return self.state == DragState.DRAGGING
    
    def get_state(self) -> DragState:
        """
        Get current drag state.
        
        Returns:
            Current DragState
        """
        return self.state
