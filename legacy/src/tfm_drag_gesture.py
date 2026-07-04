"""
Drag gesture detection for TFM.

This module provides drag gesture detection from mouse events, distinguishing
between clicks and drag operations based on movement distance and time thresholds.
"""

from dataclasses import dataclass
from typing import Optional
import time
from tfm_log_manager import getLogger


@dataclass
class DragGestureState:
    """Tracks the state of a potential drag gesture."""
    button_down: bool = False
    start_x: int = 0
    start_y: int = 0
    start_time: float = 0.0
    current_x: int = 0
    current_y: int = 0
    dragging: bool = False


class DragGestureDetector:
    """Detects drag gestures from mouse events."""
    
    # Thresholds for drag detection
    DRAG_DISTANCE_THRESHOLD = 5  # pixels
    DRAG_TIME_THRESHOLD = 0.15  # seconds
    
    def __init__(self):
        self.state = DragGestureState()
        self.logger = getLogger("DragGesture")
    
    def handle_button_down(self, x: int, y: int) -> None:
        """
        Handle mouse button down event.
        
        Args:
            x: Mouse x coordinate
            y: Mouse y coordinate
        """
        self.state.button_down = True
        self.state.start_x = x
        self.state.start_y = y
        self.state.current_x = x
        self.state.current_y = y
        self.state.start_time = time.time()
        self.state.dragging = False
    
    def handle_move(self, x: int, y: int) -> bool:
        """
        Handle mouse move event.
        
        Args:
            x: Mouse x coordinate
            y: Mouse y coordinate
            
        Returns:
            True if drag gesture detected, False otherwise
        """
        if not self.state.button_down:
            return False
        
        self.state.current_x = x
        self.state.current_y = y
        
        # Calculate distance from start
        dx = x - self.state.start_x
        dy = y - self.state.start_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        # Check if drag threshold exceeded
        if distance >= self.DRAG_DISTANCE_THRESHOLD:
            if not self.state.dragging:
                self.state.dragging = True
                self.logger.info(f"Drag gesture detected (distance: {distance:.1f})")
                return True
        
        return False
    
    def handle_button_up(self) -> bool:
        """
        Handle mouse button up event.
        
        Returns:
            True if this was a drag gesture, False if it was a click
        """
        was_dragging = self.state.dragging
        self.reset()
        return was_dragging
    
    def reset(self) -> None:
        """Reset gesture state."""
        self.state = DragGestureState()
    
    def is_dragging(self) -> bool:
        """Check if currently in drag state."""
        return self.state.dragging
