"""
TTK Test Utilities

This module provides helper classes and utilities for testing TTK applications
in callback mode. The EventCapture class simplifies event testing by capturing
events delivered via callbacks and providing synchronous access methods.
"""

import time
from typing import Optional, List, Tuple, Union
from ttk.renderer import EventCallback
from ttk.input_event import KeyEvent, CharEvent, SystemEvent


class EventCapture(EventCallback):
    """
    Helper class for capturing events in callback mode tests.
    
    This class implements the EventCallback interface and captures all events
    delivered via callbacks. It provides helper methods to synchronously retrieve
    events for testing purposes.
    
    Usage:
        backend = CoreGraphicsBackend()
        capture = EventCapture()
        backend.set_event_callback(capture)
        
        # Simulate event
        simulate_key_press(backend, 'a')
        
        # Get captured event
        event = capture.get_next_event(backend)
        assert event[0] == 'key'
        assert event[1].char == 'a'
    """
    
    def __init__(self):
        """Initialize the event capture."""
        self.events: List[Tuple[str, Union[KeyEvent, CharEvent, SystemEvent]]] = []
        self.should_quit = False
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """
        Handle a key event by capturing it.
        
        Args:
            event: KeyEvent to capture
        
        Returns:
            False (event not consumed, allows further processing)
        """
        self.events.append(('key', event))
        return False
    
    def on_char_event(self, event: CharEvent) -> bool:
        """
        Handle a character event by capturing it.
        
        Args:
            event: CharEvent to capture
        
        Returns:
            False (event not consumed, allows further processing)
        """
        self.events.append(('char', event))
        return False
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """
        Handle a system event by capturing it.
        
        Args:
            event: SystemEvent to capture
        
        Returns:
            False (event not consumed, allows further processing)
        """
        self.events.append(('system', event))
        return False
    
    def should_close(self) -> bool:
        """
        Check if the application should quit.
        
        Returns:
            True if should quit, False otherwise
        """
        return self.should_quit
    
    def get_next_event(self, backend, timeout_ms: int = 100) -> Optional[Tuple[str, Union[KeyEvent, CharEvent, SystemEvent]]]:
        """
        Get the next event synchronously (for tests).
        
        This method clears the event buffer, processes one event loop iteration,
        and returns the first captured event. This provides a synchronous way
        to retrieve events in tests.
        
        Args:
            backend: Renderer backend to process events from
            timeout_ms: Maximum time to wait for events in milliseconds (default: 100)
        
        Returns:
            Tuple of (event_type, event) where event_type is 'key', 'char', or 'system',
            or None if no event was captured within the timeout
        
        Example:
            event = capture.get_next_event(backend)
            if event:
                event_type, event_data = event
                if event_type == 'key':
                    print(f"Key: {event_data.key_code}")
        """
        self.events.clear()
        backend.run_event_loop_iteration(timeout_ms)
        return self.events[0] if self.events else None
    
    def wait_for_event(self, backend, event_type: str, timeout_ms: int = 1000) -> Optional[Tuple[str, Union[KeyEvent, CharEvent, SystemEvent]]]:
        """
        Wait for a specific event type.
        
        This method repeatedly processes event loop iterations until an event
        of the specified type is captured or the timeout expires.
        
        Args:
            backend: Renderer backend to process events from
            event_type: Type of event to wait for ('key', 'char', or 'system')
            timeout_ms: Maximum time to wait in milliseconds (default: 1000)
        
        Returns:
            Tuple of (event_type, event) if found, or None if timeout expires
        
        Example:
            # Wait for a character event
            event = capture.wait_for_event(backend, 'char', timeout_ms=500)
            if event:
                event_type, char_event = event
                print(f"Character: {char_event.char}")
        """
        start = time.time()
        while time.time() - start < timeout_ms / 1000:
            backend.run_event_loop_iteration(10)
            for evt in self.events:
                if evt[0] == event_type:
                    return evt
        return None
    
    def clear_events(self) -> None:
        """
        Clear all captured events.
        
        This is useful when you want to discard previously captured events
        before testing a new scenario.
        """
        self.events.clear()
    
    def get_all_events(self) -> List[Tuple[str, Union[KeyEvent, CharEvent, SystemEvent]]]:
        """
        Get all captured events.
        
        Returns:
            List of all captured events as (event_type, event) tuples
        """
        return self.events.copy()
    
    def has_event_type(self, event_type: str) -> bool:
        """
        Check if any captured event matches the specified type.
        
        Args:
            event_type: Type of event to check for ('key', 'char', or 'system')
        
        Returns:
            True if at least one event of the specified type was captured
        """
        return any(evt[0] == event_type for evt in self.events)
