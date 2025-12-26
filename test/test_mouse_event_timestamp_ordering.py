"""
Test mouse event timestamp ordering.

This test verifies that MouseEvent objects maintain monotonic timestamp ordering
as required by Requirement 8.2.
"""

import time
from ttk.ttk_mouse_event import (
    MouseEvent, MouseEventType, MouseButton,
    validate_event_ordering, reset_timestamp_tracking
)


def test_timestamp_auto_initialization():
    """Test that timestamp is automatically initialized if not provided."""
    # Reset timestamp tracking for clean test
    reset_timestamp_tracking()
    
    event = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=5,
        row=10,
        sub_cell_x=0.5,
        sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=0.0  # Will be auto-initialized
    )
    
    # Timestamp should be set to current time
    assert event.timestamp > 0.0
    assert event.timestamp <= time.time()


def test_timestamp_monotonic_ordering():
    """Test that timestamps are monotonically non-decreasing."""
    # Reset timestamp tracking for clean test
    reset_timestamp_tracking()
    
    # Create sequence of events
    events = []
    for i in range(5):
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=i,
            row=i,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT
        )
        events.append(event)
        # Small delay to ensure different timestamps
        time.sleep(0.001)
    
    # Verify timestamps are monotonically non-decreasing
    for i in range(1, len(events)):
        assert events[i].timestamp >= events[i-1].timestamp, \
            f"Event {i} timestamp {events[i].timestamp} < event {i-1} timestamp {events[i-1].timestamp}"


def test_timestamp_correction_for_out_of_order():
    """Test that out-of-order timestamps are corrected to maintain monotonic ordering."""
    # Reset timestamp tracking for clean test
    reset_timestamp_tracking()
    
    # Create first event with current time
    event1 = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=0,
        row=0,
        sub_cell_x=0.5,
        sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=time.time()
    )
    
    # Try to create second event with earlier timestamp
    earlier_time = event1.timestamp - 1.0
    event2 = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=1,
        row=1,
        sub_cell_x=0.5,
        sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=earlier_time
    )
    
    # Second event timestamp should be corrected to be >= first event
    assert event2.timestamp >= event1.timestamp, \
        f"Out-of-order timestamp not corrected: {event2.timestamp} < {event1.timestamp}"


def test_validate_event_ordering_function():
    """Test the validate_event_ordering utility function."""
    # Reset timestamp tracking for clean test
    reset_timestamp_tracking()
    
    # Create properly ordered events
    events = []
    base_time = time.time()
    for i in range(3):
        event = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            column=i,
            row=i,
            sub_cell_x=0.5,
            sub_cell_y=0.5,
            button=MouseButton.LEFT,
            timestamp=base_time + i * 0.1
        )
        events.append(event)
    
    # Should validate as properly ordered
    assert validate_event_ordering(events) == True
    
    # Empty list should validate
    assert validate_event_ordering([]) == True
    
    # Single event should validate
    assert validate_event_ordering([events[0]]) == True


def test_explicit_timestamp_preserved():
    """Test that explicitly provided timestamps are preserved if they maintain ordering."""
    # Reset timestamp tracking for clean test
    reset_timestamp_tracking()
    
    # Create event with explicit timestamp
    explicit_time = time.time() + 100.0  # Future timestamp
    event = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=0,
        row=0,
        sub_cell_x=0.5,
        sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=explicit_time
    )
    
    # Explicit timestamp should be preserved
    assert event.timestamp == explicit_time


def test_reset_timestamp_tracking():
    """Test that reset_timestamp_tracking() resets the tracking state."""
    # Create an event to set the last timestamp
    event1 = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=0,
        row=0,
        sub_cell_x=0.5,
        sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=time.time()
    )
    
    # Reset tracking
    reset_timestamp_tracking()
    
    # Create new event with earlier timestamp - should be allowed after reset
    earlier_time = event1.timestamp - 10.0
    event2 = MouseEvent(
        event_type=MouseEventType.BUTTON_DOWN,
        column=1,
        row=1,
        sub_cell_x=0.5,
        sub_cell_y=0.5,
        button=MouseButton.LEFT,
        timestamp=earlier_time
    )
    
    # After reset, earlier timestamp should be preserved
    assert event2.timestamp == earlier_time
