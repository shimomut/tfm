"""
TTK Renderer Module

This module defines the abstract Renderer base class that all rendering backends
must implement. It provides the core interface for drawing operations, input
handling, and window management.
"""

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ttk.input_event import KeyEvent, CharEvent, SystemEvent
    from ttk.ttk_mouse_event import MouseEvent


class TextAttribute(IntEnum):
    """
    Text rendering attributes that can be applied to text.
    
    Attributes can be combined using bitwise OR to apply multiple attributes
    simultaneously. For example: TextAttribute.BOLD | TextAttribute.UNDERLINE
    """
    NORMAL = 0      # Normal text with no special attributes
    BOLD = 1        # Bold/emphasized text
    UNDERLINE = 2   # Underlined text
    REVERSE = 4     # Reverse video (swap foreground and background colors)


class EventCallback:
    """
    Callback interface for event delivery.
    
    Backends call these methods to deliver events to the application.
    The application implements these methods to handle events.
    """
    
    def on_key_event(self, event: 'KeyEvent') -> bool:
        """
        Handle a key event.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
    
    def on_char_event(self, event: 'CharEvent') -> bool:
        """
        Handle a character event.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
    
    def on_system_event(self, event: 'SystemEvent') -> bool:
        """
        Handle a system event (resize, close, etc.).
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
    
    def on_menu_event(self, event: 'MenuEvent') -> bool:
        """
        Handle a menu event.
        
        Args:
            event: MenuEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False


class Renderer(ABC):
    """
    Abstract base class for text grid rendering backends.
    
    This class defines the interface that all rendering backends must implement.
    It provides methods for drawing operations, input handling, window management,
    and color management. Applications should use this interface exclusively,
    without depending on any backend-specific implementation details.
    
    Coordinate System:
        - Origin (0, 0) is at the top-left corner
        - Row increases downward (0 is top)
        - Column increases rightward (0 is left)
        - All positions are specified in character cells, not pixels
    
    Color Pairs:
        - Color pair 0 is reserved for default terminal colors
        - Color pairs 1-255 can be initialized with custom RGB values
        - Each color pair consists of a foreground and background color
    
    Text Attributes:
        - Use TextAttribute enum values
        - Combine multiple attributes with bitwise OR
        - Example: TextAttribute.BOLD | TextAttribute.UNDERLINE
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the rendering backend and create the window.
        
        This method must be called before any other rendering operations.
        It sets up the rendering context, creates the window or terminal
        interface, and prepares the backend for drawing operations.
        
        Raises:
            RuntimeError: If initialization fails
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Clean up resources and close the window.
        
        This method should be called when the application is finished with
        the renderer. It releases all resources, closes windows, and restores
        the terminal state (for curses backend).
        
        This method should handle cleanup gracefully even if exceptions occur.
        """
        pass
    
    @abstractmethod
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get window dimensions in character cells.
        
        Returns:
            Tuple[int, int]: A tuple of (rows, columns) representing the
                character grid size. Both values are positive integers.
                
        Example:
            rows, cols = renderer.get_dimensions()
            # rows = 24, cols = 80 for a typical terminal
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear the entire window.
        
        This method fills the entire window with spaces using the default
        color pair (0). After calling this method, the window will be blank
        and ready for new content to be drawn.
        
        Note: Changes are not visible until refresh() is called.
        """
        pass
    
    @abstractmethod
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Clear a rectangular region of the window.
        
        This method fills the specified rectangular region with spaces using
        the default color pair (0). Coordinates outside the window bounds
        are clipped automatically.
        
        Args:
            row: Starting row position (0-based, 0 is top)
            col: Starting column position (0-based, 0 is left)
            height: Height of the region in character rows (must be positive)
            width: Width of the region in character columns (must be positive)
            
        Raises:
            ValueError: If height or width is negative
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        
        Example:
            # Clear a 10x20 region starting at row 5, column 10
            renderer.clear_region(5, 10, 10, 20)
        """
        pass
    
    @abstractmethod
    def draw_text(self, row: int, col: int, text: str, 
                  color_pair: int = 0, attributes: int = 0) -> None:
        """
        Draw text at the specified position.
        
        This method draws a string of text starting at the given position.
        Text that extends beyond the window width is clipped. Text drawn
        outside the window bounds is ignored without raising an error.
        
        Args:
            row: Row position (0-based, 0 is top)
            col: Column position (0-based, 0 is left)
            text: Text string to draw (may contain any printable characters)
            color_pair: Color pair index (0-255). Use 0 for default colors.
            attributes: Bitwise OR of TextAttribute values for text styling.
                       Use 0 for normal text, or combine attributes like
                       TextAttribute.BOLD | TextAttribute.UNDERLINE
        
        Raises:
            ValueError: If color_pair is outside the range 0-255
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        
        Example:
            # Draw bold, underlined text in color pair 1
            renderer.draw_text(10, 5, "Hello World", 
                             color_pair=1,
                             attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
        """
        pass
    
    @abstractmethod
    def draw_hline(self, row: int, col: int, char: str, 
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a horizontal line.
        
        This method draws a horizontal line using the specified character.
        The line extends from the starting position to the right for the
        specified length. Lines that extend beyond the window width are clipped.
        
        Args:
            row: Row position for the line
            col: Starting column position
            char: Character to use for the line (typically '-', '─', or '═').
                 Only the first character of the string is used.
            length: Length of the line in characters (must be positive)
            color_pair: Color pair index (0-255). Use 0 for default colors.
        
        Raises:
            ValueError: If length is negative or color_pair is outside 0-255
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        
        Example:
            # Draw a 20-character horizontal line at row 5, starting at column 10
            renderer.draw_hline(5, 10, '-', 20, color_pair=1)
        """
        pass
    
    @abstractmethod
    def draw_vline(self, row: int, col: int, char: str, 
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a vertical line.
        
        This method draws a vertical line using the specified character.
        The line extends from the starting position downward for the
        specified length. Lines that extend beyond the window height are clipped.
        
        Args:
            row: Starting row position
            col: Column position for the line
            char: Character to use for the line (typically '|', '│', or '║').
                 Only the first character of the string is used.
            length: Length of the line in characters (must be positive)
            color_pair: Color pair index (0-255). Use 0 for default colors.
        
        Raises:
            ValueError: If length is negative or color_pair is outside 0-255
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        
        Example:
            # Draw a 10-character vertical line at column 5, starting at row 2
            renderer.draw_vline(2, 5, '|', 10, color_pair=1)
        """
        pass
    
    @abstractmethod
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """
        Draw a rectangle.
        
        This method draws either a filled rectangle or an outlined rectangle.
        For filled rectangles, the entire area is filled with spaces in the
        specified color. For outlined rectangles, only the border is drawn
        using line characters.
        
        Args:
            row: Top-left row position
            col: Top-left column position
            height: Height of the rectangle in character rows (must be positive)
            width: Width of the rectangle in character columns (must be positive)
            color_pair: Color pair index (0-255). Use 0 for default colors.
            filled: If True, fill the rectangle with spaces in the specified color.
                   If False, draw only the outline using line characters.
        
        Raises:
            ValueError: If height or width is negative, or color_pair is outside 0-255
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        
        Example:
            # Draw a filled 5x10 rectangle at position (2, 3)
            renderer.draw_rect(2, 3, 5, 10, color_pair=1, filled=True)
            
            # Draw an outlined 8x20 rectangle at position (10, 5)
            renderer.draw_rect(10, 5, 8, 20, color_pair=2, filled=False)
        """
        pass
    
    @abstractmethod
    def refresh(self) -> None:
        """
        Refresh the entire window to display all pending changes.
        
        This method makes all drawing operations visible by updating the
        display. Drawing operations (draw_text, draw_rect, etc.) are buffered
        and not visible until this method is called.
        
        The caret position set by set_caret_position() is automatically restored
        before refreshing, so applications don't need to call set_caret_position()
        immediately before refresh().
        
        For optimal performance, batch multiple drawing operations and call
        refresh() once after all operations are complete.
        
        Example:
            renderer.clear()
            renderer.draw_text(0, 0, "Line 1")
            renderer.draw_text(1, 0, "Line 2")
            renderer.set_caret_position(10, 5)  # For IME
            renderer.refresh()  # Caret position is automatically restored
        """
        pass
    
    @abstractmethod
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Refresh a specific region of the window.
        
        This method updates only the specified rectangular region of the display,
        which can be more efficient than refreshing the entire window when only
        a small area has changed.
        
        Note: Some backends (like curses) may refresh the entire window anyway,
        but this method provides a hint for optimization.
        
        Args:
            row: Starting row of the region to refresh
            col: Starting column of the region to refresh
            height: Height of the region in character rows
            width: Width of the region in character columns
            
        Example:
            # Update only a small status area
            renderer.draw_text(0, 0, "Status: OK")
            renderer.refresh_region(0, 0, 1, 20)
        """
        pass
    
    @abstractmethod
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        """
        Initialize a color pair with RGB values.
        
        This method defines a color pair that can be used in drawing operations.
        Color pairs consist of a foreground color and a background color, both
        specified as RGB tuples.
        
        Color pair 0 is reserved for default terminal colors and cannot be
        initialized. Color pairs 1-255 are available for custom colors.
        
        Args:
            pair_id: Color pair index (1-255). Use 0 for default colors.
                    Color pair 0 is reserved and cannot be initialized.
            fg_color: Foreground color as (R, G, B) tuple.
                     Each component must be in the range 0-255.
            bg_color: Background color as (R, G, B) tuple.
                     Each component must be in the range 0-255.
        
        Raises:
            ValueError: If pair_id is 0 or outside the range 1-255
            ValueError: If any RGB component is outside the range 0-255
            
        Note: The curses backend may approximate RGB colors to the nearest
        terminal color. The CoreGraphics backend uses exact RGB values.
        
        Example:
            # Initialize color pair 1 with white text on blue background
            renderer.init_color_pair(1, (255, 255, 255), (0, 0, 255))
            
            # Initialize color pair 2 with red text on black background
            renderer.init_color_pair(2, (255, 0, 0), (0, 0, 0))
        """
        pass
    

    
    @abstractmethod
    def set_cursor_visibility(self, visible: bool) -> None:
        """
        Set cursor visibility.
        
        This method controls whether the text cursor is visible in the window.
        By default, most applications will want to hide the cursor and draw
        their own cursor representation.
        
        Args:
            visible: True to show the cursor, False to hide it.
            
        Example:
            # Hide the cursor (typical for most applications)
            renderer.set_cursor_visibility(False)
            
            # Show the cursor (useful for text input fields)
            renderer.set_cursor_visibility(True)
        """
        pass
    
    @abstractmethod
    def move_cursor(self, row: int, col: int) -> None:
        """
        Move the cursor to the specified position.
        
        This method sets the cursor position. The cursor is only visible if
        set_cursor_visibility(True) has been called. Coordinates outside the
        window bounds are handled gracefully (typically clamped or ignored).
        
        Args:
            row: Row position (0-based, 0 is top)
            col: Column position (0-based, 0 is left)
            
        Example:
            # Position cursor at row 5, column 10
            renderer.set_cursor_visibility(True)
            renderer.move_cursor(5, 10)
        """
        pass
    

    
    @abstractmethod
    def set_event_callback(self, callback: EventCallback) -> None:
        """
        Set the event callback for event delivery (REQUIRED).
        
        This method enables callback-based event delivery. All events are delivered
        via the callback methods (on_key_event, on_char_event, on_system_event)
        instead of being returned by polling methods.
        
        This method MUST be called before run_event_loop() or run_event_loop_iteration().
        The callback parameter is required and cannot be None.
        
        Args:
            callback: EventCallback instance (required, not optional)
        
        Raises:
            ValueError: If callback is None
        
        Example:
            class MyCallback(EventCallback):
                def on_key_event(self, event):
                    print(f"Key pressed: {event.key_code}")
                    return True  # Event consumed
            
            renderer.set_event_callback(MyCallback())
        """
        pass
    
    @abstractmethod
    def run_event_loop(self) -> None:
        """
        Run the main event loop until application quits.
        
        This method blocks until the application terminates. Events are delivered
        via the EventCallback set with set_event_callback().
        
        The event callback MUST be set before calling this method.
        
        Raises:
            RuntimeError: If event callback not set
        
        Example:
            renderer.set_event_callback(MyCallback())
            renderer.run_event_loop()  # Blocks until application quits
        """
        pass
    
    @abstractmethod
    def run_event_loop_iteration(self, timeout_ms: int = -1) -> None:
        """
        Process one iteration of the event loop.
        
        This method processes pending OS events and delivers them via the
        EventCallback methods (on_key_event, on_char_event, on_system_event).
        It returns after processing events or when the timeout expires.
        
        Events are NOT returned directly from this method. Instead, they are
        delivered asynchronously via the callback methods set with
        set_event_callback().
        
        The event callback MUST be set before calling this method.
        
        Args:
            timeout_ms: Maximum time to wait for events in milliseconds.
                       -1 (default): Wait indefinitely for events
                        0: Non-blocking, process pending events and return immediately
                       >0: Wait up to timeout_ms milliseconds for events
        
        Raises:
            RuntimeError: If event callback not set
        
        Example:
            renderer.set_event_callback(MyCallback())
            
            # Main application loop
            while not should_quit:
                # Process events (delivered via callbacks)
                renderer.run_event_loop_iteration(timeout_ms=16)
                
                # Update application state
                update_application()
                
                # Draw interface
                renderer.refresh()
        """
        pass
    
    @abstractmethod
    def set_menu_bar(self, menu_structure: dict) -> None:
        """
        Set the menu bar structure for desktop mode.
        
        This method configures the native menu bar with the specified menu
        structure. It is only applicable in desktop mode (e.g., macOS CoreGraphics
        backend). Terminal-based backends should implement this as a no-op.
        
        The menu structure defines a hierarchical organization of menus and menu
        items, including labels, keyboard shortcuts, and initial enabled states.
        
        Args:
            menu_structure: Dictionary defining the menu hierarchy with the format:
                {
                    'menus': [
                        {
                            'id': str,           # Unique menu identifier
                            'label': str,        # Display label for the menu
                            'items': [
                                {
                                    'id': str,              # Unique item identifier
                                    'label': str,           # Display label
                                    'shortcut': Optional[str],  # Keyboard shortcut (e.g., 'Cmd+N')
                                    'enabled': bool         # Initial enabled state
                                },
                                {'separator': True},  # Menu separator
                                ...
                            ]
                        },
                        ...
                    ]
                }
        
        Note: This method should be called during application initialization
        after the renderer has been initialized. Changes to the menu structure
        require calling this method again with the updated structure.
        
        Example:
            menu_structure = {
                'menus': [
                    {
                        'id': 'file',
                        'label': 'File',
                        'items': [
                            {
                                'id': 'file.new',
                                'label': 'New File',
                                'shortcut': 'Cmd+N',
                                'enabled': True
                            },
                            {'separator': True},
                            {
                                'id': 'file.quit',
                                'label': 'Quit',
                                'shortcut': 'Cmd+Q',
                                'enabled': True
                            }
                        ]
                    }
                ]
            }
            renderer.set_menu_bar(menu_structure)
        """
        pass
    
    @abstractmethod
    def update_menu_item_state(self, item_id: str, enabled: bool) -> None:
        """
        Update the enabled/disabled state of a menu item.
        
        This method dynamically updates whether a menu item is enabled (selectable)
        or disabled (grayed out). It allows the application to reflect the current
        application state in the menu bar without reconstructing the entire menu.
        
        This is only applicable in desktop mode. Terminal-based backends should
        implement this as a no-op.
        
        Args:
            item_id: Unique identifier for the menu item to update.
                    This must match an 'id' field from the menu structure
                    passed to set_menu_bar().
            enabled: True to enable the menu item (make it selectable),
                    False to disable it (gray it out and prevent selection).
        
        Raises:
            ValueError: If item_id does not correspond to a known menu item.
                       Backends may choose to log a warning instead of raising.
        
        Note: State updates are typically applied immediately and do not require
        a refresh operation. The menu bar will reflect the change the next time
        the user opens the menu.
        
        Example:
            # Disable the "Paste" menu item when clipboard is empty
            renderer.update_menu_item_state('edit.paste', False)
            
            # Enable the "Delete" menu item when files are selected
            renderer.update_menu_item_state('file.delete', True)
        """
        pass
    
    @abstractmethod
    def set_caret_position(self, x: int, y: int) -> None:
        """
        Set the terminal caret position.
        
        This method stores the caret position, which will be automatically
        restored by refresh(). The caret position should match the logical
        cursor position in text input widgets to provide visual feedback
        about where text input will appear.
        
        Applications no longer need to call this method immediately before
        refresh() - the position is remembered and automatically restored.
        
        In terminal mode (curses), this controls the actual terminal cursor.
        In desktop mode (CoreGraphics), this is typically a no-op as the OS
        manages the caret through the NSTextInputClient protocol.
        
        Args:
            x: Column position (0-based, 0 is left)
            y: Row position (0-based, 0 is top)
        
        Note: The caret position can be set even when the caret is hidden.
        This is useful for IME (Input Method Editor) composition text positioning.
        Coordinates outside the window bounds are handled gracefully (typically
        ignored or clamped).
        
        Example:
            # Position caret at column 10, row 5 for IME
            renderer.set_caret_position(10, 5)
            # ... do other drawing operations ...
            renderer.refresh()  # Caret position is automatically restored
        """
        pass
    
    @abstractmethod
    def supports_mouse(self) -> bool:
        """
        Query whether this backend supports mouse events.
        
        This method allows applications to detect mouse support capabilities
        at runtime and adapt their behavior accordingly. Applications should
        call this method during initialization to determine if mouse features
        should be enabled.
        
        Returns:
            bool: True if mouse events are available, False otherwise.
        
        Note: Even if this returns True, specific mouse event types may not
        be supported. Use get_supported_mouse_events() to query which specific
        event types are available.
        
        Example:
            if renderer.supports_mouse():
                renderer.enable_mouse_events()
                print("Mouse support enabled")
            else:
                print("Mouse not supported, using keyboard-only mode")
        """
        pass
    
    @abstractmethod
    def get_supported_mouse_events(self) -> set:
        """
        Query which mouse event types are supported by this backend.
        
        Different backends support different subsets of mouse events. For example,
        the CoreGraphics backend supports all event types (button, move, wheel,
        double-click), while the curses backend typically only supports button
        clicks.
        
        Returns:
            set: Set of MouseEventType values supported by this backend.
                Returns an empty set if mouse events are not supported.
        
        Note: The returned set contains MouseEventType enum values from the
        ttk_mouse_event module. Import MouseEventType to check for specific
        event types.
        
        Example:
            from ttk.ttk_mouse_event import MouseEventType
            
            supported = renderer.get_supported_mouse_events()
            if MouseEventType.WHEEL in supported:
                print("Scroll wheel supported")
            if MouseEventType.DOUBLE_CLICK in supported:
                print("Double-click supported")
        """
        pass
    
    @abstractmethod
    def enable_mouse_events(self) -> bool:
        """
        Enable mouse event capture.
        
        This method activates mouse event tracking in the backend. After calling
        this method successfully, mouse events will be available via
        poll_mouse_event() or delivered through the event callback.
        
        This method should be called after initialize() and before starting the
        event loop. If the backend does not support mouse events, this method
        returns False and the application should continue without mouse support.
        
        Returns:
            bool: True if mouse events were successfully enabled, False otherwise.
        
        Note: This method is idempotent - calling it multiple times has no
        additional effect after the first successful call.
        
        Example:
            renderer.initialize()
            if renderer.supports_mouse():
                if renderer.enable_mouse_events():
                    print("Mouse events enabled successfully")
                else:
                    print("Failed to enable mouse events")
        """
        pass
    
    @abstractmethod
    def poll_mouse_event(self) -> Optional['MouseEvent']:
        """
        Poll for pending mouse events.
        
        This method checks if any mouse events are available and returns the
        next event in the queue. If no events are pending, it returns None
        immediately without blocking.
        
        Mouse events include button presses/releases, mouse movement, scroll
        wheel events, and double-clicks (depending on backend support). Each
        event contains text grid coordinates and sub-cell positioning information.
        
        Returns:
            Optional[MouseEvent]: MouseEvent if one is available, None otherwise.
        
        Note: This method does not block. Applications should call this method
        in their event loop to check for mouse events. If mouse events are not
        enabled or not supported, this method always returns None.
        
        Example:
            from ttk.ttk_mouse_event import MouseEventType
            
            # In event loop
            mouse_event = renderer.poll_mouse_event()
            if mouse_event:
                if mouse_event.event_type == MouseEventType.BUTTON_DOWN:
                    print(f"Click at ({mouse_event.column}, {mouse_event.row})")
                elif mouse_event.event_type == MouseEventType.WHEEL:
                    print(f"Scroll: {mouse_event.scroll_delta_y}")
        """
        pass
    
    def is_desktop_mode(self) -> bool:
        """
        Check if the renderer is running in desktop mode.
        
        Desktop mode typically means a native GUI window (e.g., CoreGraphics on macOS)
        rather than a terminal-based interface (e.g., curses). This affects various
        behaviors such as:
        - Whether to write logs to stdout/stderr (desktop: yes, terminal: no)
        - Whether native menus are available
        - Whether the application can safely write to console streams
        
        Returns:
            bool: True if running in desktop mode (GUI window),
                  False if running in terminal mode (curses)
        
        Note: The default implementation returns False (terminal mode).
        Desktop backends should override this to return True.
        
        Example:
            if renderer.is_desktop_mode():
                # Safe to write to stdout in desktop mode
                print("Debug output")
            else:
                # Terminal mode - writing to stdout would interfere with curses
                pass
        """
        return False