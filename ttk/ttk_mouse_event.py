"""
TTK Mouse Event Data Structures

This module provides the core data structures for mouse event handling in TTK,
including event types, button identifiers, and the MouseEvent dataclass with
coordinate transformation utilities.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time


class MouseEventType(Enum):
    """Types of mouse events supported by TTK."""
    BUTTON_DOWN = "button_down"
    BUTTON_UP = "button_up"
    DOUBLE_CLICK = "double_click"
    MOVE = "move"
    WHEEL = "wheel"
    DRAG = "drag"  # For future use


class MouseButton(Enum):
    """Mouse button identifiers."""
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    NONE = 0  # For move events without button


@dataclass
class MouseEvent:
    """
    Represents a mouse event with text grid coordinates.
    
    Coordinates are in text grid units (column, row) with sub-cell
    positioning expressed as fractional values from 0.0 to 1.0.
    
    Attributes:
        event_type: The type of mouse event (button, move, wheel, etc.)
        column: Text grid column position (0-based)
        row: Text grid row position (0-based)
        sub_cell_x: Horizontal position within cell (0.0 = left, 1.0 = right)
        sub_cell_y: Vertical position within cell (0.0 = top, 1.0 = bottom)
        button: Which mouse button was involved
        scroll_delta_x: Horizontal scroll amount (for wheel events)
        scroll_delta_y: Vertical scroll amount (for wheel events)
        timestamp: Unix timestamp for event ordering (monotonic)
        shift: Shift modifier key state
        ctrl: Control modifier key state
        alt: Alt modifier key state
        meta: Meta/Command modifier key state
    """
    event_type: MouseEventType
    column: int
    row: int
    sub_cell_x: float
    sub_cell_y: float
    button: MouseButton
    scroll_delta_x: float = 0.0
    scroll_delta_y: float = 0.0
    timestamp: float = 0.0
    shift: bool = False
    ctrl: bool = False
    alt: bool = False
    meta: bool = False
    
    # Class variable to track last timestamp for monotonic ordering
    _last_timestamp: float = 0.0
    
    def __post_init__(self):
        """
        Initialize and validate timestamp for monotonic ordering.
        
        If timestamp is not provided (0.0), it will be set to the current time.
        The timestamp is then validated to ensure it's monotonically non-decreasing
        relative to the last event timestamp.
        """
        # Initialize timestamp if not provided (default 0.0)
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        
        # Ensure monotonic ordering: timestamp must be >= last timestamp
        # This prevents out-of-order events and ensures proper event sequencing
        if self.timestamp < MouseEvent._last_timestamp:
            # Adjust timestamp to maintain monotonic ordering
            self.timestamp = MouseEvent._last_timestamp
        
        # Update last timestamp for next event
        MouseEvent._last_timestamp = self.timestamp


# Coordinate Transformation Utility Functions

def transform_screen_to_grid(
    screen_x: float,
    screen_y: float,
    cell_width: float,
    cell_height: float
) -> tuple[int, int, float, float]:
    """
    Transform screen coordinates to text grid coordinates with sub-cell positioning.
    
    Args:
        screen_x: X coordinate in screen/window space
        screen_y: Y coordinate in screen/window space
        cell_width: Width of a single text cell in pixels
        cell_height: Height of a single text cell in pixels
        
    Returns:
        Tuple of (column, row, sub_cell_x, sub_cell_y) where:
        - column: Integer grid column (0-based)
        - row: Integer grid row (0-based)
        - sub_cell_x: Fractional position within cell horizontally [0.0, 1.0)
        - sub_cell_y: Fractional position within cell vertically [0.0, 1.0)
    """
    # Calculate grid position
    column = int(screen_x / cell_width)
    row = int(screen_y / cell_height)
    
    # Calculate sub-cell position as fraction
    sub_cell_x = (screen_x % cell_width) / cell_width
    sub_cell_y = (screen_y % cell_height) / cell_height
    
    # Ensure sub-cell values are in valid range [0.0, 1.0)
    sub_cell_x = max(0.0, min(sub_cell_x, 0.999999))
    sub_cell_y = max(0.0, min(sub_cell_y, 0.999999))
    
    return column, row, sub_cell_x, sub_cell_y


def transform_grid_to_screen(
    column: int,
    row: int,
    sub_cell_x: float,
    sub_cell_y: float,
    cell_width: float,
    cell_height: float
) -> tuple[float, float]:
    """
    Transform text grid coordinates to screen coordinates.
    
    Args:
        column: Grid column (0-based)
        row: Grid row (0-based)
        sub_cell_x: Fractional position within cell horizontally [0.0, 1.0)
        sub_cell_y: Fractional position within cell vertically [0.0, 1.0)
        cell_width: Width of a single text cell in pixels
        cell_height: Height of a single text cell in pixels
        
    Returns:
        Tuple of (screen_x, screen_y) in screen/window coordinates
    """
    screen_x = column * cell_width + sub_cell_x * cell_width
    screen_y = row * cell_height + sub_cell_y * cell_height
    
    return screen_x, screen_y


def clamp_coordinates(
    column: int,
    row: int,
    max_columns: int,
    max_rows: int
) -> tuple[int, int]:
    """
    Clamp grid coordinates to valid range.
    
    Args:
        column: Grid column to clamp
        row: Grid row to clamp
        max_columns: Maximum valid column value (exclusive)
        max_rows: Maximum valid row value (exclusive)
        
    Returns:
        Tuple of (clamped_column, clamped_row)
    """
    clamped_column = max(0, min(column, max_columns - 1))
    clamped_row = max(0, min(row, max_rows - 1))
    
    return clamped_column, clamped_row


def validate_sub_cell_position(sub_cell_x: float, sub_cell_y: float) -> bool:
    """
    Validate that sub-cell positions are in valid range.
    
    Args:
        sub_cell_x: Horizontal sub-cell position
        sub_cell_y: Vertical sub-cell position
        
    Returns:
        True if both values are in range [0.0, 1.0), False otherwise
    """
    return (0.0 <= sub_cell_x < 1.0 and 0.0 <= sub_cell_y < 1.0)


def validate_event_ordering(events: list[MouseEvent]) -> bool:
    """
    Validate that a sequence of mouse events has monotonic timestamps.
    
    Checks that each event's timestamp is greater than or equal to the
    previous event's timestamp, ensuring proper event ordering.
    
    Args:
        events: List of MouseEvent objects to validate
        
    Returns:
        True if all timestamps are monotonically non-decreasing, False otherwise
    """
    if len(events) <= 1:
        return True
    
    for i in range(1, len(events)):
        if events[i].timestamp < events[i-1].timestamp:
            return False
    
    return True


def reset_timestamp_tracking() -> None:
    """
    Reset the timestamp tracking for MouseEvent creation.
    
    This is primarily useful for testing to ensure a clean state between
    test cases. In production code, this should rarely be needed.
    """
    MouseEvent._last_timestamp = 0.0
