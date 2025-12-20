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
    def get_event(self, timeout_ms: int = -1) -> Optional['Event']:
        """
        Get the next event (keyboard, mouse, system, or menu event).
        
        This method retrieves the next event from the event queue. Events can be
        keyboard input, mouse actions, system events (like window resize), or
        menu selection events (in desktop mode). It can operate in blocking mode
        (wait indefinitely), non-blocking mode (return immediately), or with a timeout.
        
        Args:
            timeout_ms: Timeout in milliseconds.
                       -1 (default): Block indefinitely until an event is available
                        0: Non-blocking, return immediately if no event
                       >0: Wait up to timeout_ms milliseconds for an event
        
        Returns:
            Optional[Event]: An Event object (KeyEvent, MouseEvent, SystemEvent,
                            or MenuEvent) if an event is available, or None if
                            the timeout expires with no event.
                                 
        Note: The Event types are defined in the ttk.input_event module.
              MenuEvent objects are only generated in desktop mode when a user
              selects a menu item from the native menu bar.
        
        Example:
            # Blocking wait for event
            event = renderer.get_event()
            
            # Non-blocking check for event
            event = renderer.get_event(timeout_ms=0)
            if event is not None:
                # Process event
                pass
            
            # Wait up to 100ms for event
            event = renderer.get_event(timeout_ms=100)
            
            # Handle different event types
            from ttk.input_event import KeyEvent, MenuEvent
            event = renderer.get_event()
            if isinstance(event, MenuEvent):
                print(f"Menu item selected: {event.item_id}")
            elif isinstance(event, KeyEvent):
                print(f"Key pressed: {event.key_code}")
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
    
    def get_input(self, timeout_ms: int = -1) -> Optional['Event']:
        """
        Deprecated: Use get_event() instead.
        
        This method is provided for backward compatibility and simply calls
        get_event(). New code should use get_event() directly.
        """
        return self.get_event(timeout_ms)
    
    def set_event_callback(self, callback: Optional[EventCallback]) -> None:
        """
        Set the event callback for event delivery.
        
        This method enables callback-based event delivery instead of polling.
        When a callback is set, events are delivered via the callback methods
        (on_key_event, on_char_event, on_system_event) instead of being
        returned by get_event().
        
        Args:
            callback: EventCallback instance or None to disable callbacks
        
        Example:
            class MyCallback(EventCallback):
                def on_key_event(self, event):
                    print(f"Key pressed: {event.key_code}")
                    return True  # Event consumed
            
            renderer.set_event_callback(MyCallback())
        """
        self.event_callback = callback
    
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
