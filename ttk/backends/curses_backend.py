"""
TTK Curses Backend Module

This module implements the Renderer interface using Python's curses library
for terminal-based display. It provides all drawing operations, input handling,
and window management for terminal applications.
"""

import curses
from typing import Tuple, Optional

from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import Event, KeyEvent, CharEvent, SystemEvent, KeyCode, SystemEventType, ModifierKey


# Terminal-specific key codes for Shift+Arrow combinations
# These codes vary by terminal emulator and may not work in all environments
# The backend translates these to standard KeyEvent with SHIFT modifier
_KEY_SHIFT_UP_1 = 337      # Shift+Up in some terminals
_KEY_SHIFT_DOWN_1 = 336    # Shift+Down in some terminals  
_KEY_SHIFT_UP_2 = 393      # Alternative Shift+Up code
_KEY_SHIFT_DOWN_2 = 402    # Alternative Shift+Down code
_KEY_SHIFT_LEFT_1 = 545    # Shift+Left in some terminals
_KEY_SHIFT_RIGHT_1 = 560   # Shift+Right in some terminals
_KEY_SHIFT_LEFT_2 = 393    # Alternative Shift+Left code
_KEY_SHIFT_RIGHT_2 = 402   # Alternative Shift+Right code


class CursesBackend(Renderer):
    """
    Curses-based rendering backend for terminal applications.
    
    This backend uses Python's curses library to provide text-based rendering
    in terminal windows. It supports all standard terminal features including
    colors, text attributes, and keyboard input.
    
    The backend handles curses initialization and cleanup, translates curses
    key codes to the abstract TTK's KeyEvent format, and provides graceful handling
    of out-of-bounds drawing operations.
    """
    
    def __init__(self):
        """
        Initialize the CursesBackend.
        
        Note: This does not initialize curses itself. Call initialize() to
        set up the curses environment.
        """
        self.stdscr = None
        self.color_pairs_initialized = set()
        self.fullcolor_mode = False
        self.next_color_index = 16  # Start after basic 16 colors
        self.rgb_to_color_cache = {}  # Cache RGB -> color index mappings
        self.event_callback = None  # EventCallback instance for callback-based event delivery
    
    def initialize(self) -> None:
        """
        Initialize curses and set up the terminal.
        
        This method:
        - Initializes the curses library
        - Sets up color support (fullcolor if available, 8/16 colors otherwise)
        - Configures terminal modes (no echo, cbreak, keypad)
        - Hides the cursor by default
        - Sets black background for the terminal
        
        Raises:
            RuntimeError: If curses initialization fails
        """
        try:
            self.stdscr = curses.initscr()
            curses.start_color()
            
            # Check if terminal supports fullcolor mode (256+ colors and color redefinition)
            self.fullcolor_mode = (
                curses.COLORS >= 256 and 
                curses.can_change_color()
            )
            
            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(True)
            curses.curs_set(0)  # Hide cursor by default
            
            # Initialize color pair 1 with white on black for default background
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            self.color_pairs_initialized.add(1)
            
            # Set black background for the entire terminal window
            # This ensures all areas have black background, not terminal default
            self.stdscr.bkgd(' ', curses.color_pair(1))
        except Exception as e:
            raise RuntimeError(f"Failed to initialize curses: {e}")
    
    def shutdown(self) -> None:
        """
        Clean up curses and restore terminal.
        
        This method restores the terminal to its original state by:
        - Disabling keypad mode
        - Re-enabling echo
        - Restoring normal terminal mode (nocbreak)
        - Calling endwin() to clean up curses
        
        This method handles cleanup gracefully even if exceptions occur.
        """
        try:
            if self.stdscr:
                self.stdscr.keypad(False)
                curses.echo()
                curses.nocbreak()
                curses.endwin()
        except (curses.error, OSError) as e:
            # Ignore errors during cleanup - terminal may already be in bad state
            print(f"Warning: Error during curses shutdown: {e}")
    
    def suspend(self) -> None:
        """
        Suspend curses to allow external programs to run.
        
        This method calls curses.endwin() to restore the terminal to normal mode,
        allowing external programs to use the terminal. The curses state is preserved
        and can be restored by calling resume().
        """
        try:
            if self.stdscr:
                curses.endwin()
        except (curses.error, OSError) as e:
            print(f"Warning: Error suspending curses: {e}")
    
    def resume(self) -> None:
        """
        Resume curses after external program execution.
        
        This method restores the curses display after suspend() was called.
        It refreshes the screen to restore the previous display state.
        """
        try:
            if self.stdscr:
                # Refresh the screen to restore curses mode
                self.stdscr.refresh()
        except (curses.error, OSError) as e:
            print(f"Warning: Error resuming curses: {e}")
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get terminal dimensions.
        
        Returns:
            Tuple[int, int]: A tuple of (rows, columns) representing the
                terminal size in character cells.
        """
        height, width = self.stdscr.getmaxyx()
        return (height, width)
    
    def clear(self) -> None:
        """
        Clear the terminal.
        
        This fills the entire terminal with spaces using black background.
        Changes are not visible until refresh() is called.
        """
        self.stdscr.clear()
    
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Clear a rectangular region.
        
        This method clears the specified region by moving to each row and
        clearing to the end of the line. Coordinates outside the window bounds
        are handled gracefully.
        
        Args:
            row: Starting row position (0-based)
            col: Starting column position (0-based)
            height: Height of the region in rows
            width: Width of the region in columns
            
        Raises:
            ValueError: If height or width is negative
        """
        if height < 0 or width < 0:
            raise ValueError("Height and width must be non-negative")
        
        max_rows, max_cols = self.get_dimensions()
        for r in range(row, min(row + height, max_rows)):
            try:
                self.stdscr.move(r, col)
                # Clear from current position to end of specified width
                self.stdscr.addstr(' ' * min(width, max_cols - col))
            except curses.error:
                # Ignore out-of-bounds errors
                pass
    
    def draw_text(self, row: int, col: int, text: str,
                  color_pair: int = 0, attributes: int = 0) -> None:
        """
        Draw text using curses.
        
        This method draws text at the specified position with the given color
        and attributes. Text that extends beyond the window is clipped.
        Out-of-bounds coordinates are handled gracefully.
        
        Args:
            row: Row position (0-based)
            col: Column position (0-based)
            text: Text string to draw
            color_pair: Color pair index (0-255)
            attributes: Bitwise OR of TextAttribute values
            
        Raises:
            ValueError: If color_pair is outside the range 0-255
        """
        if not 0 <= color_pair <= 255:
            raise ValueError(f"Color pair must be in range 0-255, got {color_pair}")
        
        try:
            # Build curses attributes
            attr = curses.color_pair(color_pair)
            if attributes & TextAttribute.BOLD:
                attr |= curses.A_BOLD
            if attributes & TextAttribute.UNDERLINE:
                attr |= curses.A_UNDERLINE
            if attributes & TextAttribute.REVERSE:
                attr |= curses.A_REVERSE
            
            self.stdscr.addstr(row, col, text, attr)
        except curses.error:
            # Ignore out-of-bounds errors
            pass
    
    def draw_hline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """
        Draw horizontal line.
        
        Args:
            row: Row position
            col: Starting column position
            char: Character to use for the line
            length: Length in characters
            color_pair: Color pair index (0-255)
            
        Raises:
            ValueError: If length is negative or color_pair is outside 0-255
        """
        if length < 0:
            raise ValueError("Length must be non-negative")
        if not 0 <= color_pair <= 255:
            raise ValueError(f"Color pair must be in range 0-255, got {color_pair}")
        
        # Use draw_text for Unicode characters (like box-drawing chars)
        # curses.hline() doesn't handle Unicode properly
        self.draw_text(row, col, char[0] * length, color_pair)
    
    def draw_vline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """
        Draw vertical line.
        
        Args:
            row: Starting row position
            col: Column position
            char: Character to use for the line
            length: Length in characters
            color_pair: Color pair index (0-255)
            
        Raises:
            ValueError: If length is negative or color_pair is outside 0-255
        """
        if length < 0:
            raise ValueError("Length must be non-negative")
        if not 0 <= color_pair <= 255:
            raise ValueError(f"Color pair must be in range 0-255, got {color_pair}")
        
        # Draw vertical line by drawing character at each row
        # curses.vline() doesn't handle Unicode properly
        for i in range(length):
            self.draw_text(row + i, col, char[0], color_pair)
    
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """
        Draw rectangle.
        
        This method draws either a filled rectangle (using spaces) or an
        outlined rectangle (using box-drawing characters).
        
        Args:
            row: Top-left row position
            col: Top-left column position
            height: Height in rows
            width: Width in columns
            color_pair: Color pair index (0-255)
            filled: If True, fill the rectangle; if False, draw outline
            
        Raises:
            ValueError: If height or width is negative, or color_pair is outside 0-255
        """
        if height < 0 or width < 0:
            raise ValueError("Height and width must be non-negative")
        if not 0 <= color_pair <= 255:
            raise ValueError(f"Color pair must be in range 0-255, got {color_pair}")
        
        if filled:
            # Fill rectangle with spaces
            for r in range(row, row + height):
                self.draw_text(r, col, ' ' * width, color_pair)
        else:
            # Draw outline using box-drawing characters
            if height > 0 and width > 0:
                # Draw corners and edges
                if height == 1:
                    # Single row - just draw horizontal line with corners
                    if width == 1:
                        self.draw_text(row, col, '┌', color_pair)
                    elif width == 2:
                        self.draw_text(row, col, '┌┐', color_pair)
                    else:
                        line = '┌' + '─' * (width - 2) + '┐'
                        self.draw_text(row, col, line, color_pair)
                elif width == 1:
                    # Single column - just draw vertical line with corners
                    self.draw_text(row, col, '┌', color_pair)
                    for r in range(row + 1, row + height - 1):
                        self.draw_text(r, col, '│', color_pair)
                    self.draw_text(row + height - 1, col, '└', color_pair)
                else:
                    # Full rectangle with all corners and edges
                    # Top edge
                    top_line = '┌' + '─' * (width - 2) + '┐'
                    self.draw_text(row, col, top_line, color_pair)
                    
                    # Middle rows with left and right edges
                    for r in range(row + 1, row + height - 1):
                        self.draw_text(r, col, '│', color_pair)
                        self.draw_text(r, col + width - 1, '│', color_pair)
                    
                    # Bottom edge
                    bottom_line = '└' + '─' * (width - 2) + '┘'
                    self.draw_text(row + height - 1, col, bottom_line, color_pair)
    
    def refresh(self) -> None:
        """
        Refresh the terminal.
        
        This makes all pending drawing operations visible by updating the display.
        """
        self.stdscr.refresh()
    
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Refresh a region (curses refreshes entire window).
        
        Note: The curses backend refreshes the entire window regardless of
        the specified region, as curses does not support partial refresh.
        
        Args:
            row: Starting row (ignored)
            col: Starting column (ignored)
            height: Height in rows (ignored)
            width: Width in columns (ignored)
        """
        self.stdscr.refresh()
    
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        """
        Initialize color pair.
        
        This method initializes a color pair with the specified RGB colors.
        In fullcolor mode, it creates custom colors with exact RGB values.
        In 8/16 color mode, it approximates RGB colors to the nearest terminal color.
        
        Args:
            pair_id: Color pair index (1-255, 0 is reserved)
            fg_color: Foreground color as (R, G, B) tuple (0-255 each)
            bg_color: Background color as (R, G, B) tuple (0-255 each)
            
        Raises:
            ValueError: If pair_id is 0 or outside 1-255, or if RGB values are invalid
        """
        if pair_id == 0:
            raise ValueError("Color pair 0 is reserved and cannot be initialized")
        if not 1 <= pair_id <= 255:
            raise ValueError(f"Color pair ID must be in range 1-255, got {pair_id}")
        
        # Validate RGB values
        for color, name in [(fg_color, "Foreground"), (bg_color, "Background")]:
            if len(color) != 3:
                raise ValueError(f"{name} color must be a 3-tuple")
            for component in color:
                if not 0 <= component <= 255:
                    raise ValueError(f"{name} color components must be in range 0-255")
        
        # Skip if already initialized
        if pair_id in self.color_pairs_initialized:
            return
        
        # Convert RGB to curses color (fullcolor or approximated)
        fg = self._rgb_to_curses_color(fg_color)
        bg = self._rgb_to_curses_color(bg_color)
        
        curses.init_pair(pair_id, fg, bg)
        self.color_pairs_initialized.add(pair_id)
    
    def clear_color_cache(self) -> None:
        """
        Clear the color pair cache to allow reinitialization.
        
        This method clears the internal cache of initialized color pairs,
        allowing them to be reinitialized with new colors. This is useful
        when switching color schemes.
        
        Note: This does not clear color pair 1 (default white on black)
        to maintain terminal background consistency.
        """
        # Keep color pair 1 (default background)
        self.color_pairs_initialized = {1}
        # Clear RGB to color cache to allow new color definitions
        self.rgb_to_color_cache.clear()
        # Reset color index for fullcolor mode
        self.next_color_index = 16
    
    def update_background(self, bg_color: Tuple[int, int, int]) -> None:
        """
        Update the terminal background color.
        
        This method updates the background color of the entire terminal window.
        It should be called after color scheme changes to ensure all areas
        (including those where no characters are drawn) have the correct background.
        
        Args:
            bg_color: Background color as (R, G, B) tuple (0-255 each)
        """
        try:
            # Convert RGB to curses color
            bg = self._rgb_to_curses_color(bg_color)
            
            # Reinitialize color pair 1 with new background
            curses.init_pair(1, curses.COLOR_WHITE, bg)
            
            # Apply the new background to the entire terminal
            self.stdscr.bkgd(' ', curses.color_pair(1))
        except (curses.error, OSError) as e:
            print(f"Warning: Could not update background: {e}")
    
    def set_fullcolor_mode(self, enabled: bool) -> None:
        """
        Enable or disable fullcolor mode.
        
        When fullcolor mode is enabled, colors are rendered using exact RGB values
        (if the terminal supports it). When disabled, colors are approximated to
        the nearest 8/16 basic terminal colors.
        
        This is useful for testing color approximation or working with terminals
        that have issues with custom color definitions.
        
        Args:
            enabled: True to enable fullcolor mode, False to use 8/16 color approximation
        """
        self.fullcolor_mode = enabled
    
    def get_fullcolor_mode(self) -> bool:
        """
        Check if fullcolor mode is currently enabled.
        
        Returns:
            bool: True if fullcolor mode is enabled, False if using 8/16 color approximation
        """
        return self.fullcolor_mode
    
    def _rgb_to_curses_color(self, rgb: Tuple[int, int, int]) -> int:
        """
        Convert RGB to curses color code.
        
        In fullcolor mode, creates a custom color with exact RGB values.
        In 8/16 color mode, approximates RGB to the nearest terminal color.
        
        Args:
            rgb: RGB color tuple (R, G, B) with values 0-255
            
        Returns:
            int: Curses color code
        """
        # Check cache first
        if rgb in self.rgb_to_color_cache:
            return self.rgb_to_color_cache[rgb]
        
        if self.fullcolor_mode:
            color_index = self._create_fullcolor(rgb)
        else:
            color_index = self._approximate_to_basic_color(rgb)
        
        # Cache the result
        self.rgb_to_color_cache[rgb] = color_index
        return color_index
    
    def _create_fullcolor(self, rgb: Tuple[int, int, int]) -> int:
        """
        Create a custom color with exact RGB values in fullcolor mode.
        
        Args:
            rgb: RGB color tuple (R, G, B) with values 0-255
            
        Returns:
            int: Color index for the newly created color
        """
        # Check if we've run out of color slots
        if self.next_color_index >= curses.COLORS:
            # Fallback to approximation if we run out of color slots
            return self._approximate_to_basic_color(rgb)
        
        try:
            color_index = self.next_color_index
            self.next_color_index += 1
            
            # Convert RGB from 0-255 to curses range 0-1000
            r = int((rgb[0] / 255.0) * 1000)
            g = int((rgb[1] / 255.0) * 1000)
            b = int((rgb[2] / 255.0) * 1000)
            
            # Initialize the custom color
            curses.init_color(color_index, r, g, b)
            return color_index
        except (curses.error, ValueError, OSError) as e:
            # If init_color fails, fallback to approximation
            print(f"Warning: Failed to create custom color RGB{rgb}: {e}")
            return self._approximate_to_basic_color(rgb)
    
    def _approximate_to_basic_color(self, rgb: Tuple[int, int, int]) -> int:
        """
        Approximate RGB to one of the 8 basic terminal colors.
        
        This maps RGB colors to the 8 basic terminal colors, attempting to
        preserve the visual appearance as much as possible.
        
        Args:
            rgb: RGB color tuple (R, G, B) with values 0-255
            
        Returns:
            int: Curses color code (0-7)
        """
        r, g, b = rgb
        
        # Calculate brightness
        brightness = (r + g + b) / 3
        
        # Very dark colors (near black)
        if brightness < 30:
            return curses.COLOR_BLACK
        
        # Very bright colors (near white)
        if brightness > 200:
            return curses.COLOR_WHITE
        
        # Calculate saturation and dominant color
        max_component = max(r, g, b)
        min_component = min(r, g, b)
        saturation = max_component - min_component
        
        # Low saturation (gray tones) - map based on brightness
        if saturation < 40:
            # Dark gray (like 51,63,76 or 80,80,80) -> map to white for visibility
            if brightness < 100:
                return curses.COLOR_WHITE
            # Medium gray (like 128,128,128) -> map to white
            elif brightness < 180:
                return curses.COLOR_WHITE
            # Light gray (like 220,220,220) -> map to white
            else:
                return curses.COLOR_WHITE
        
        # Saturated colors - determine dominant hue
        # Yellow-ish colors (like 204,204,120 for directories)
        if r > 180 and g > 180 and b < 150:
            return curses.COLOR_YELLOW
        # Green colors (like 51,229,51 for executables or 0,255,0 for strings)
        elif g > max(r, b) + 50:
            return curses.COLOR_GREEN
        # Blue colors (like 40,80,160 for selected or 100,200,255 for system logs)
        elif b > max(r, g) + 30:
            return curses.COLOR_BLUE
        # Cyan colors (like 0,255,255 for built-ins)
        elif g > 180 and b > 180 and r < 100:
            return curses.COLOR_CYAN
        # Magenta colors (like 255,0,255 for operators)
        elif r > 180 and b > 180 and g < 100:
            return curses.COLOR_MAGENTA
        # Red colors (like 255,0,0 for errors)
        elif r > max(g, b) + 50:
            return curses.COLOR_RED
        # Yellow (for numbers like 255,255,0)
        elif r > 180 and g > 180:
            return curses.COLOR_YELLOW
        
        # Default to white for unclassified colors
        return curses.COLOR_WHITE
    
    def get_event(self, timeout_ms: int = -1) -> Optional[Event]:
        """
        Get event from terminal (polling mode - for backward compatibility).
        
        This method retrieves the next event from the terminal using polling.
        It supports blocking, non-blocking, and timeout modes.
        
        When callbacks are enabled via set_event_callback(), this method processes
        events and delivers them via callbacks, then returns None. This allows
        existing code to continue using get_event() while new code can use callbacks.
        
        Args:
            timeout_ms: Timeout in milliseconds
                       -1: Block indefinitely
                        0: Non-blocking
                       >0: Wait up to timeout_ms milliseconds
        
        Returns:
            Optional[Event]: Event if input is available and callbacks are disabled,
                            None if timeout or if callbacks are enabled
        """
        if self.event_callback:
            # Callbacks enabled - process events but deliver via callbacks
            self._process_events(timeout_ms)
            return None
        else:
            # Callbacks disabled - use traditional polling
            if timeout_ms >= 0:
                self.stdscr.timeout(timeout_ms)
            else:
                self.stdscr.timeout(-1)
            
            try:
                key = self.stdscr.getch()
                if key == -1:
                    return None
                
                return self._translate_curses_key(key)
            except curses.error as e:
                # Timeout or input error
                return None
    
    def _translate_curses_key(self, key: int) -> Event:
        """
        Translate curses key code to Event.
        
        This method maps curses key codes to the abstract Event format,
        handling special keys, printable characters, and modifier keys.
        Terminal-specific Shift+Arrow combinations are translated to
        standard KeyEvent with SHIFT modifier.
        
        Args:
            key: Curses key code
            
        Returns:
            Event: Translated event (KeyEvent or SystemEvent)
        """
        modifiers = ModifierKey.NONE
        
        # Handle resize event separately (it's a system event, not a key event)
        if key == curses.KEY_RESIZE:
            return SystemEvent(event_type=SystemEventType.RESIZE)
        
        # Handle terminal-specific Shift+Arrow combinations
        # These vary by terminal emulator, so we check multiple codes
        if key in (_KEY_SHIFT_UP_1, _KEY_SHIFT_UP_2):
            return KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.SHIFT)
        elif key in (_KEY_SHIFT_DOWN_1, _KEY_SHIFT_DOWN_2):
            return KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.SHIFT)
        elif key in (_KEY_SHIFT_LEFT_1, _KEY_SHIFT_LEFT_2):
            return KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.SHIFT)
        elif key in (_KEY_SHIFT_RIGHT_1, _KEY_SHIFT_RIGHT_2):
            return KeyEvent(key_code=KeyCode.RIGHT, modifiers=ModifierKey.SHIFT)
        
        # Map curses keys to KeyCode
        key_map = {
            curses.KEY_UP: KeyCode.UP,
            curses.KEY_DOWN: KeyCode.DOWN,
            curses.KEY_LEFT: KeyCode.LEFT,
            curses.KEY_RIGHT: KeyCode.RIGHT,
            curses.KEY_HOME: KeyCode.HOME,
            curses.KEY_END: KeyCode.END,
            curses.KEY_PPAGE: KeyCode.PAGE_UP,
            curses.KEY_NPAGE: KeyCode.PAGE_DOWN,
            curses.KEY_DC: KeyCode.DELETE,
            curses.KEY_IC: KeyCode.INSERT,
            curses.KEY_BACKSPACE: KeyCode.BACKSPACE,
        }
        
        # Function keys
        for i in range(12):
            key_map[curses.KEY_F1 + i] = KeyCode.F1 + i
        
        if key in key_map:
            return KeyEvent(key_code=key_map[key], modifiers=modifiers)
        
        # Printable character
        if 32 <= key <= 126:
            return KeyEvent(key_code=key, modifiers=modifiers, char=chr(key))
        
        # Special characters
        if key == 10 or key == 13:
            return KeyEvent(key_code=KeyCode.ENTER, modifiers=modifiers)
        elif key == 27:
            return KeyEvent(key_code=KeyCode.ESCAPE, modifiers=modifiers)
        elif key == 9:
            return KeyEvent(key_code=KeyCode.TAB, modifiers=modifiers)
        elif key == 127:
            return KeyEvent(key_code=KeyCode.BACKSPACE, modifiers=modifiers)
        
        # Default: return the key code as-is
        return KeyEvent(key_code=key, modifiers=modifiers)
    
    def set_cursor_visibility(self, visible: bool) -> None:
        """
        Set cursor visibility.
        
        Args:
            visible: True to show cursor, False to hide it
        """
        try:
            curses.curs_set(1 if visible else 0)
        except curses.error as e:
            # Some terminals don't support cursor visibility control
            print(f"Warning: Cannot set cursor visibility: {e}")
    
    def move_cursor(self, row: int, col: int) -> None:
        """
        Move cursor position.
        
        Args:
            row: Row position
            col: Column position
        """
        try:
            self.stdscr.move(row, col)
        except curses.error:
            # Ignore out-of-bounds errors
            pass
    
    def set_menu_bar(self, menu_structure: dict) -> None:
        """
        Set menu bar structure (no-op for terminal backend).
        
        Menu bars are only supported in desktop mode. This method is a no-op
        for the curses backend.
        
        Args:
            menu_structure: Menu structure dictionary (ignored)
        """
        # No-op: Terminal backend does not support native menu bars
        pass
    
    def update_menu_item_state(self, item_id: str, enabled: bool) -> None:
        """
        Update menu item state (no-op for terminal backend).
        
        Menu bars are only supported in desktop mode. This method is a no-op
        for the curses backend.
        
        Args:
            item_id: Menu item identifier (ignored)
            enabled: Enabled state (ignored)
        """
        # No-op: Terminal backend does not support native menu bars
        pass
    
    def run_event_loop(self) -> None:
        """
        Run the event loop with callback-based event delivery.
        
        This method runs an event loop that continuously polls for keyboard input
        and delivers events via the registered callback. The loop continues until
        the callback returns False for a system event or an exception occurs.
        
        This method requires that set_event_callback() has been called to register
        a callback. If no callback is registered, this method does nothing.
        
        The event loop:
        1. Polls for keyboard input using getch()
        2. Translates input to KeyEvent
        3. Delivers KeyEvent via on_key_event() callback
        4. If not consumed, translates to CharEvent (if applicable)
        5. Delivers CharEvent via on_char_event() callback
        
        Note: This is the callback-based event system. For polling-based event
        handling, use get_event() instead.
        """
        if not self.event_callback:
            # No callback registered - nothing to do
            return
        
        # Run event loop until interrupted
        while True:
            try:
                # Poll for keyboard input (blocking)
                event = self.get_event(timeout_ms=-1)
                
                if event is None:
                    continue
                
                # Handle system events
                if isinstance(event, SystemEvent):
                    consumed = self.event_callback.on_system_event(event)
                    if not consumed:
                        # System event not consumed - continue loop
                        continue
                    # System event consumed - continue loop
                    continue
                
                # Handle key events
                if isinstance(event, KeyEvent):
                    consumed = self.event_callback.on_key_event(event)
                    
                    if not consumed:
                        # KeyEvent not consumed - try to translate to CharEvent
                        char_event = self._translate_key_to_char(event)
                        if char_event:
                            self.event_callback.on_char_event(char_event)
                
            except KeyboardInterrupt:
                # Allow Ctrl+C to break the loop
                break
            except Exception as e:
                # Log error but continue loop
                print(f"Error in event loop: {e}")
                continue
    
    def _process_events(self, timeout_ms: int = -1) -> None:
        """
        Process one event cycle and deliver via callbacks.
        
        This method is used by get_event() when callbacks are enabled. It polls
        for one event, translates it, and delivers it via the registered callback.
        If the KeyEvent is not consumed, it translates it to CharEvent and delivers
        that as well.
        
        This allows get_event() to maintain backward compatibility while supporting
        the callback-based event system.
        
        Args:
            timeout_ms: Timeout in milliseconds
                       -1: Block indefinitely
                        0: Non-blocking
                       >0: Wait up to timeout_ms milliseconds
        """
        if not self.event_callback:
            return
        
        # Set timeout for getch()
        if timeout_ms >= 0:
            self.stdscr.timeout(timeout_ms)
        else:
            self.stdscr.timeout(-1)
        
        try:
            # Poll for keyboard input
            key = self.stdscr.getch()
            if key == -1:
                return
            
            # Translate to event
            event = self._translate_curses_key(key)
            if event is None:
                return
            
            # Handle system events
            if isinstance(event, SystemEvent):
                self.event_callback.on_system_event(event)
                return
            
            # Handle key events
            if isinstance(event, KeyEvent):
                consumed = self.event_callback.on_key_event(event)
                
                if not consumed:
                    # KeyEvent not consumed - try to translate to CharEvent
                    char_event = self._translate_key_to_char(event)
                    if char_event:
                        self.event_callback.on_char_event(char_event)
        
        except curses.error:
            # Timeout or input error - ignore
            pass
    
    def _translate_key_to_char(self, event: KeyEvent) -> Optional['CharEvent']:
        """
        Translate a KeyEvent to CharEvent if it represents a printable character.
        
        This method checks if a KeyEvent represents a printable character without
        command modifiers (Ctrl, Alt, Cmd). If so, it creates a CharEvent for
        text input. Shift modifier is allowed for uppercase letters.
        
        Args:
            event: KeyEvent that was not consumed by the application
        
        Returns:
            CharEvent if the KeyEvent represents a printable character,
            None otherwise
        """
        # Only translate if no command modifiers (Ctrl, Alt, Cmd)
        # Shift is allowed for uppercase letters
        if event.modifiers & (ModifierKey.CONTROL | ModifierKey.ALT | ModifierKey.COMMAND):
            return None
        
        # Only translate if has printable character in char field
        if event.char and len(event.char) == 1 and event.char.isprintable():
            return CharEvent(char=event.char)
        
        return None
