"""
TTK Curses Backend Module

This module implements the Renderer interface using Python's curses library
for terminal-based display. It provides all drawing operations, input handling,
and window management for terminal applications.
"""

import curses
from typing import Tuple, Optional

from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import InputEvent, KeyCode, ModifierKey


class CursesBackend(Renderer):
    """
    Curses-based rendering backend for terminal applications.
    
    This backend uses Python's curses library to provide text-based rendering
    in terminal windows. It supports all standard terminal features including
    colors, text attributes, and keyboard input.
    
    The backend handles curses initialization and cleanup, translates curses
    key codes to the abstract InputEvent format, and provides graceful handling
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
    
    def initialize(self) -> None:
        """
        Initialize curses and set up the terminal.
        
        This method:
        - Initializes the curses library
        - Sets up color support
        - Configures terminal modes (no echo, cbreak, keypad)
        - Hides the cursor by default
        - Sets black background for the terminal
        
        Raises:
            RuntimeError: If curses initialization fails
        """
        try:
            self.stdscr = curses.initscr()
            curses.start_color()
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
        except Exception:
            # Ignore errors during cleanup
            pass
    
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
        
        try:
            self.stdscr.hline(row, col, ord(char[0]), length,
                            curses.color_pair(color_pair))
        except curses.error:
            # Ignore out-of-bounds errors
            pass
    
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
        
        try:
            self.stdscr.vline(row, col, ord(char[0]), length,
                            curses.color_pair(color_pair))
        except curses.error:
            # Ignore out-of-bounds errors
            pass
    
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """
        Draw rectangle.
        
        This method draws either a filled rectangle (using spaces) or an
        outlined rectangle (using line characters).
        
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
            # Draw outline
            if height > 0 and width > 0:
                # Top and bottom edges
                if width > 0:
                    self.draw_hline(row, col, '-', width, color_pair)
                    if height > 1:
                        self.draw_hline(row + height - 1, col, '-', width, color_pair)
                
                # Left and right edges
                if height > 0:
                    self.draw_vline(row, col, '|', height, color_pair)
                    if width > 1:
                        self.draw_vline(row, col + width - 1, '|', height, color_pair)
    
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
        The curses backend approximates RGB colors to the nearest terminal color.
        
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
        
        # Convert RGB to curses color (simplified - use closest terminal color)
        fg = self._rgb_to_curses_color(fg_color)
        bg = self._rgb_to_curses_color(bg_color)
        
        curses.init_pair(pair_id, fg, bg)
        self.color_pairs_initialized.add(pair_id)
    
    def _rgb_to_curses_color(self, rgb: Tuple[int, int, int]) -> int:
        """
        Convert RGB to curses color code.
        
        This is a simplified mapping to the 8 basic terminal colors.
        More sophisticated implementations could use 256-color mode.
        
        Args:
            rgb: RGB color tuple (R, G, B) with values 0-255
            
        Returns:
            int: Curses color code
        """
        r, g, b = rgb
        
        # Simple color mapping based on RGB values
        if r < 128 and g < 128 and b < 128:
            return curses.COLOR_BLACK
        elif r > 200 and g > 200 and b > 200:
            return curses.COLOR_WHITE
        elif r > g and r > b:
            return curses.COLOR_RED
        elif g > r and g > b:
            return curses.COLOR_GREEN
        elif b > r and b > g:
            return curses.COLOR_BLUE
        elif r > 128 and g > 128:
            return curses.COLOR_YELLOW
        elif r > 128 and b > 128:
            return curses.COLOR_MAGENTA
        elif g > 128 and b > 128:
            return curses.COLOR_CYAN
        return curses.COLOR_WHITE
    
    def get_input(self, timeout_ms: int = -1) -> Optional[InputEvent]:
        """
        Get input from terminal.
        
        This method retrieves the next input event from the terminal.
        It supports blocking, non-blocking, and timeout modes.
        
        Args:
            timeout_ms: Timeout in milliseconds
                       -1: Block indefinitely
                        0: Non-blocking
                       >0: Wait up to timeout_ms milliseconds
        
        Returns:
            Optional[InputEvent]: InputEvent if input is available, None if timeout
        """
        if timeout_ms >= 0:
            self.stdscr.timeout(timeout_ms)
        else:
            self.stdscr.timeout(-1)
        
        try:
            key = self.stdscr.getch()
            if key == -1:
                return None
            
            return self._translate_curses_key(key)
        except curses.error:
            return None
    
    def _translate_curses_key(self, key: int) -> InputEvent:
        """
        Translate curses key code to InputEvent.
        
        This method maps curses key codes to the abstract InputEvent format,
        handling special keys, printable characters, and modifier keys.
        
        Args:
            key: Curses key code
            
        Returns:
            InputEvent: Translated input event
        """
        modifiers = ModifierKey.NONE
        
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
            curses.KEY_RESIZE: KeyCode.RESIZE,
        }
        
        # Function keys
        for i in range(12):
            key_map[curses.KEY_F1 + i] = KeyCode.F1 + i
        
        if key in key_map:
            return InputEvent(key_code=key_map[key], modifiers=modifiers)
        
        # Printable character
        if 32 <= key <= 126:
            return InputEvent(key_code=key, modifiers=modifiers, char=chr(key))
        
        # Special characters
        if key == 10 or key == 13:
            return InputEvent(key_code=KeyCode.ENTER, modifiers=modifiers)
        elif key == 27:
            return InputEvent(key_code=KeyCode.ESCAPE, modifiers=modifiers)
        elif key == 9:
            return InputEvent(key_code=KeyCode.TAB, modifiers=modifiers)
        elif key == 127:
            return InputEvent(key_code=KeyCode.BACKSPACE, modifiers=modifiers)
        
        # Default: return the key code as-is
        return InputEvent(key_code=key, modifiers=modifiers)
    
    def set_cursor_visibility(self, visible: bool) -> None:
        """
        Set cursor visibility.
        
        Args:
            visible: True to show cursor, False to hide it
        """
        try:
            curses.curs_set(1 if visible else 0)
        except curses.error:
            # Some terminals don't support cursor visibility control
            pass
    
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
