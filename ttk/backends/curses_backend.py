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
from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton


# Curses key code to TTK KeyCode mapping (ANSI layout)
#
# KEYBOARD LAYOUT SUPPORT
# =======================
#
# Default Layout: ANSI (American National Standards Institute)
# The ANSI layout is the standard US keyboard layout and is used by default.
# This mapping works with most terminal emulators using ANSI keyboard layout.
#
# Supported Layouts:
# - ANSI: Fully supported (default)
#
# Adding New Keyboard Layouts:
# ----------------------------
# To add support for other keyboard layouts (e.g., AZERTY, QWERTZ), follow these steps:
#
# 1. Create a new mapping dictionary (e.g., CURSES_AZERTY_KEY_MAP or CURSES_QWERTZ_KEY_MAP)
#    following the same structure as CURSES_ANSI_KEY_MAP below.
#
# 2. Map curses key codes (ASCII values and curses.KEY_* constants) to TTK KeyCode values.
#    The ASCII values differ between layouts because keys produce different characters.
#    For example:
#      - ANSI:   ord('a') = KEY_A
#      - AZERTY: ord('q') = KEY_A (Q key is in A position on AZERTY)
#      - QWERTZ: ord('a') = KEY_A (same as ANSI)
#
# 3. Update the _get_key_map() method in CursesBackend to return your
#    new mapping dictionary when the corresponding layout is selected.
#
# Mapping Table Structure:
# ------------------------
# Each entry maps a curses key code (integer) to a TTK KeyCode value:
#   {
#       curses_key_code: KeyCode.TTK_KEY_NAME,
#       ...
#   }
#
# Key Categories:
# - Letter keys: Map both lowercase and uppercase to same KeyCode (e.g., 'a' and 'A' -> KEY_A)
# - Digit keys: Map to KEY_0 through KEY_9 (physical keys)
# - Symbol keys (unshifted): Map to KEY_MINUS, KEY_EQUAL, etc.
# - Symbol keys (shifted): Map to same physical key as unshifted version
# - Shifted digit symbols: Map to digit keys (e.g., '!' -> KEY_1, '@' -> KEY_2)
# - Special keys: Map curses.KEY_* constants to TTK KeyCode values
#
# Important Notes:
# - KeyCode values represent physical keys, not characters
# - Both lowercase and uppercase letters map to the same KeyCode
# - Shift modifier is detected separately for uppercase letters
# - Symbol variants (e.g., ! vs 1, @ vs 2) map to the same physical key
# - The char field in KeyEvent contains the actual character typed
#
# Future Layout Support:
# ----------------------
# When adding AZERTY or QWERTZ support, consider these differences:
#
# AZERTY (French) Layout:
# - Q and A keys are swapped
# - W and Z keys are swapped
# - M key is to the right of L
# - Different symbol key positions
# - Reference: https://en.wikipedia.org/wiki/AZERTY
#
# QWERTZ (German) Layout:
# - Y and Z keys are swapped
# - Different symbol key positions
# - Reference: https://en.wikipedia.org/wiki/QWERTZ
#
CURSES_ANSI_KEY_MAP = {
    # Letter keys (lowercase ASCII codes)
    ord('a'): KeyCode.KEY_A,
    ord('b'): KeyCode.KEY_B,
    ord('c'): KeyCode.KEY_C,
    ord('d'): KeyCode.KEY_D,
    ord('e'): KeyCode.KEY_E,
    ord('f'): KeyCode.KEY_F,
    ord('g'): KeyCode.KEY_G,
    ord('h'): KeyCode.KEY_H,
    ord('i'): KeyCode.KEY_I,
    ord('j'): KeyCode.KEY_J,
    ord('k'): KeyCode.KEY_K,
    ord('l'): KeyCode.KEY_L,
    ord('m'): KeyCode.KEY_M,
    ord('n'): KeyCode.KEY_N,
    ord('o'): KeyCode.KEY_O,
    ord('p'): KeyCode.KEY_P,
    ord('q'): KeyCode.KEY_Q,
    ord('r'): KeyCode.KEY_R,
    ord('s'): KeyCode.KEY_S,
    ord('t'): KeyCode.KEY_T,
    ord('u'): KeyCode.KEY_U,
    ord('v'): KeyCode.KEY_V,
    ord('w'): KeyCode.KEY_W,
    ord('x'): KeyCode.KEY_X,
    ord('y'): KeyCode.KEY_Y,
    ord('z'): KeyCode.KEY_Z,
    
    # Uppercase letters (map to same KeyCode, Shift handled separately)
    ord('A'): KeyCode.KEY_A,
    ord('B'): KeyCode.KEY_B,
    ord('C'): KeyCode.KEY_C,
    ord('D'): KeyCode.KEY_D,
    ord('E'): KeyCode.KEY_E,
    ord('F'): KeyCode.KEY_F,
    ord('G'): KeyCode.KEY_G,
    ord('H'): KeyCode.KEY_H,
    ord('I'): KeyCode.KEY_I,
    ord('J'): KeyCode.KEY_J,
    ord('K'): KeyCode.KEY_K,
    ord('L'): KeyCode.KEY_L,
    ord('M'): KeyCode.KEY_M,
    ord('N'): KeyCode.KEY_N,
    ord('O'): KeyCode.KEY_O,
    ord('P'): KeyCode.KEY_P,
    ord('Q'): KeyCode.KEY_Q,
    ord('R'): KeyCode.KEY_R,
    ord('S'): KeyCode.KEY_S,
    ord('T'): KeyCode.KEY_T,
    ord('U'): KeyCode.KEY_U,
    ord('V'): KeyCode.KEY_V,
    ord('W'): KeyCode.KEY_W,
    ord('X'): KeyCode.KEY_X,
    ord('Y'): KeyCode.KEY_Y,
    ord('Z'): KeyCode.KEY_Z,
    
    # Digit keys
    ord('0'): KeyCode.KEY_0,
    ord('1'): KeyCode.KEY_1,
    ord('2'): KeyCode.KEY_2,
    ord('3'): KeyCode.KEY_3,
    ord('4'): KeyCode.KEY_4,
    ord('5'): KeyCode.KEY_5,
    ord('6'): KeyCode.KEY_6,
    ord('7'): KeyCode.KEY_7,
    ord('8'): KeyCode.KEY_8,
    ord('9'): KeyCode.KEY_9,
    
    # Symbol keys (unshifted)
    ord('-'): KeyCode.KEY_MINUS,
    ord('='): KeyCode.KEY_EQUAL,
    ord('['): KeyCode.KEY_LEFT_BRACKET,
    ord(']'): KeyCode.KEY_RIGHT_BRACKET,
    ord('\\'): KeyCode.KEY_BACKSLASH,
    ord(';'): KeyCode.KEY_SEMICOLON,
    ord("'"): KeyCode.KEY_QUOTE,
    ord(','): KeyCode.KEY_COMMA,
    ord('.'): KeyCode.KEY_PERIOD,
    ord('/'): KeyCode.KEY_SLASH,
    ord('`'): KeyCode.KEY_GRAVE,
    
    # Symbol keys (shifted - map to same physical key)
    ord('_'): KeyCode.KEY_MINUS,
    ord('+'): KeyCode.KEY_EQUAL,
    ord('{'): KeyCode.KEY_LEFT_BRACKET,
    ord('}'): KeyCode.KEY_RIGHT_BRACKET,
    ord('|'): KeyCode.KEY_BACKSLASH,
    ord(':'): KeyCode.KEY_SEMICOLON,
    ord('"'): KeyCode.KEY_QUOTE,
    ord('<'): KeyCode.KEY_COMMA,
    ord('>'): KeyCode.KEY_PERIOD,
    ord('?'): KeyCode.KEY_SLASH,
    ord('~'): KeyCode.KEY_GRAVE,
    
    # Shifted digit symbols
    ord('!'): KeyCode.KEY_1,
    ord('@'): KeyCode.KEY_2,
    ord('#'): KeyCode.KEY_3,
    ord('$'): KeyCode.KEY_4,
    ord('%'): KeyCode.KEY_5,
    ord('^'): KeyCode.KEY_6,
    ord('&'): KeyCode.KEY_7,
    ord('*'): KeyCode.KEY_8,
    ord('('): KeyCode.KEY_9,
    ord(')'): KeyCode.KEY_0,
    
    # Space
    ord(' '): KeyCode.SPACE,
    
    # Special keys (existing mappings)
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
    
    # Function keys
    curses.KEY_F1: KeyCode.F1,
    curses.KEY_F2: KeyCode.F2,
    curses.KEY_F3: KeyCode.F3,
    curses.KEY_F4: KeyCode.F4,
    curses.KEY_F5: KeyCode.F5,
    curses.KEY_F6: KeyCode.F6,
    curses.KEY_F7: KeyCode.F7,
    curses.KEY_F8: KeyCode.F8,
    curses.KEY_F9: KeyCode.F9,
    curses.KEY_F10: KeyCode.F10,
    curses.KEY_F11: KeyCode.F11,
    curses.KEY_F12: KeyCode.F12,
    
    # Special characters
    10: KeyCode.ENTER,
    13: KeyCode.ENTER,
    27: KeyCode.ESCAPE,
    9: KeyCode.TAB,
    127: KeyCode.BACKSPACE,
}

# Set of shifted characters for ANSI layout
# These characters require the Shift key to be pressed
# Used to detect Shift modifier in _translate_curses_key
CURSES_ANSI_SHIFTED_CHARS = frozenset({
    # Uppercase letters
    ord('A'), ord('B'), ord('C'), ord('D'), ord('E'), ord('F'), ord('G'), ord('H'),
    ord('I'), ord('J'), ord('K'), ord('L'), ord('M'), ord('N'), ord('O'), ord('P'),
    ord('Q'), ord('R'), ord('S'), ord('T'), ord('U'), ord('V'), ord('W'), ord('X'),
    ord('Y'), ord('Z'),
    
    # Shifted symbol keys
    ord('_'),  # Shift + -
    ord('+'),  # Shift + =
    ord('{'),  # Shift + [
    ord('}'),  # Shift + ]
    ord('|'),  # Shift + \
    ord(':'),  # Shift + ;
    ord('"'),  # Shift + '
    ord('<'),  # Shift + ,
    ord('>'),  # Shift + .
    ord('?'),  # Shift + /
    ord('~'),  # Shift + `
    
    # Shifted digit symbols
    ord('!'),  # Shift + 1
    ord('@'),  # Shift + 2
    ord('#'),  # Shift + 3
    ord('$'),  # Shift + 4
    ord('%'),  # Shift + 5
    ord('^'),  # Shift + 6
    ord('&'),  # Shift + 7
    ord('*'),  # Shift + 8
    ord('('),  # Shift + 9
    ord(')'),  # Shift + 0
})


class UTF8Accumulator:
    """
    Accumulates UTF-8 byte sequences to form complete Unicode characters.
    
    UTF-8 encoding uses 1-4 bytes per character:
    - 0xxxxxxx: 1-byte character (ASCII)
    - 110xxxxx 10xxxxxx: 2-byte character
    - 1110xxxx 10xxxxxx 10xxxxxx: 3-byte character
    - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx: 4-byte character
    """
    
    def __init__(self):
        """Initialize the UTF-8 accumulator."""
        self.buffer: bytearray = bytearray()
        self.expected_bytes: int = 0
    
    def add_byte(self, byte: int) -> Optional[str]:
        """
        Add a byte to the accumulator.
        
        Args:
            byte: Integer value of the byte (0-255)
        
        Returns:
            Complete Unicode character if sequence is complete, None otherwise
        """
        # First byte - determine expected length
        if self.expected_bytes == 0:
            if byte < 0x80:  # ASCII (1 byte)
                return chr(byte)
            elif (byte & 0xE0) == 0xC0:  # 2-byte sequence
                self.expected_bytes = 2
                self.buffer.append(byte)
            elif (byte & 0xF0) == 0xE0:  # 3-byte sequence
                self.expected_bytes = 3
                self.buffer.append(byte)
            elif (byte & 0xF8) == 0xF0:  # 4-byte sequence
                self.expected_bytes = 4
                self.buffer.append(byte)
            else:
                # Invalid start byte - discard
                self.reset()
                return None
        else:
            # Continuation byte - should start with 10xxxxxx
            if (byte & 0xC0) != 0x80:
                # Invalid continuation byte - discard buffer
                self.reset()
                return None
            
            self.buffer.append(byte)
            
            # Check if sequence is complete
            if len(self.buffer) == self.expected_bytes:
                try:
                    char = self.buffer.decode('utf-8')
                    self.reset()
                    return char
                except UnicodeDecodeError:
                    # Invalid sequence - discard
                    self.reset()
                    return None
        
        return None
    
    def reset(self):
        """Reset the accumulator state."""
        self.buffer.clear()
        self.expected_bytes = 0
    
    def is_accumulating(self) -> bool:
        """Check if currently accumulating a multi-byte sequence."""
        return len(self.buffer) > 0


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
    
    def __init__(self, keyboard_layout='ANSI'):
        """
        Initialize the CursesBackend.
        
        Args:
            keyboard_layout: Keyboard layout type ('ANSI', etc.)
                           Default: 'ANSI'
        
        Note: This does not initialize curses itself. Call initialize() to
        set up the curses environment.
        """
        self.stdscr = None
        self.color_pairs_initialized = set()
        self.fullcolor_mode = False
        self.next_color_index = 16  # Start after basic 16 colors
        self.rgb_to_color_cache = {}  # Cache RGB -> color index mappings
        self.event_callback = None  # EventCallback instance for callback-based event delivery
        self.utf8_accumulator = UTF8Accumulator()  # UTF-8 byte accumulator for multi-byte characters
        self.caret_x = 0  # Stored caret X position
        self.caret_y = 0  # Stored caret Y position
        self.mouse_enabled = False  # Whether mouse events are enabled
        self.mouse_available = False  # Whether terminal supports mouse events
        self.keyboard_layout = keyboard_layout  # Keyboard layout type
        self._key_map, self._shifted_chars = self._get_key_map(keyboard_layout)  # Initialize key mapping
    
    def _get_key_map(self, layout: str) -> Tuple[dict, frozenset]:
        """
        Get the appropriate key map and shifted characters set for the keyboard layout.
        
        Args:
            layout: Keyboard layout type ('ANSI', etc.)
        
        Returns:
            tuple: (Key mapping dictionary, Set of shifted character codes)
        
        Raises:
            ValueError: If layout is unknown
        """
        if layout == 'ANSI':
            return CURSES_ANSI_KEY_MAP, CURSES_ANSI_SHIFTED_CHARS
        else:
            raise ValueError(f"Unknown keyboard layout: {layout}")
    
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
    
    def set_event_callback(self, callback: 'EventCallback') -> None:
        """
        Set the event callback for event delivery (REQUIRED).
        
        This method enables callback-based event delivery. All events are delivered
        via the callback methods instead of being returned by polling methods.
        
        Args:
            callback: EventCallback instance (required, not optional)
        
        Raises:
            ValueError: If callback is None
        """
        if callback is None:
            raise ValueError("Event callback cannot be None")
        self.event_callback = callback
    
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
        
        Note: Uses erase() instead of clear() to avoid forcing a complete
        screen redraw, which can cause flickering.
        """
        self.stdscr.erase()
    
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
        The caret position set by set_caret_position() is automatically restored
        before refreshing, so applications don't need to call set_caret_position()
        again before each refresh.
        """
        # Restore the caret position before refreshing
        # This ensures the caret is at the correct position for IME composition text
        try:
            self.stdscr.move(self.caret_y, self.caret_x)
        except curses.error:
            # Position out of bounds - ignore
            pass
        
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
    
    def run_event_loop_iteration(self, timeout_ms: int = -1) -> None:
        """
        Process one iteration of the event loop.
        
        Processes pending terminal events and delivers them via callbacks.
        Returns after processing events or timeout.
        
        Args:
            timeout_ms: Maximum time to wait for events (-1 = indefinite)
        
        Raises:
            RuntimeError: If event callback not set
        """
        if self.event_callback is None:
            raise RuntimeError("Event callback not set. Call set_event_callback() first.")
        
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
            
            # Handle resize event separately (it's a system event, not a key event)
            if key == curses.KEY_RESIZE:
                event = SystemEvent(event_type=SystemEventType.RESIZE)
                self.event_callback.on_system_event(event)
                return
            
            # Handle mouse events
            if key == curses.KEY_MOUSE:
                if self.mouse_enabled:
                    try:
                        # Get mouse event details
                        _, x, y, _, bstate = curses.getmouse()
                        
                        # Map curses button state to our event type and button
                        event_type = self._map_curses_event_type(bstate)
                        button = self._map_curses_button(bstate)
                        
                        if event_type is not None:
                            # Create and deliver mouse event via callback
                            mouse_event = MouseEvent(
                                event_type=event_type,
                                column=x,
                                row=y,
                                sub_cell_x=0.5,  # Center of cell
                                sub_cell_y=0.5,  # Center of cell
                                button=button,
                                timestamp=0.0  # Will be set by MouseEvent.__post_init__
                            )
                            self.event_callback.on_mouse_event(mouse_event)
                    except (curses.error, ValueError):
                        # Error getting mouse event - ignore
                        pass
                return
            
            # Special keys (> 255) are not UTF-8 bytes - handle them directly
            if key > 255:
                # This is a special key (arrow, function key, etc.)
                key_event = self._translate_curses_key(key)
                if isinstance(key_event, KeyEvent):
                    self.event_callback.on_key_event(key_event)
                elif isinstance(key_event, SystemEvent):
                    self.event_callback.on_system_event(key_event)
                return
            
            # Try to accumulate as UTF-8 byte (only for 0-255 range)
            char = self.utf8_accumulator.add_byte(key)
            
            if char is not None:
                # Complete character formed
                if len(char) == 1 and ord(char) < 128:
                    # ASCII - generate KeyEvent (for command matching)
                    # Use the original key byte for translation
                    key_event = self._translate_curses_key(key)
                    consumed = False
                    if isinstance(key_event, KeyEvent):
                        consumed = self.event_callback.on_key_event(key_event)
                    
                    # If not consumed, translate to CharEvent
                    if not consumed and isinstance(key_event, KeyEvent):
                        char_event = self._translate_key_to_char(key_event)
                        if char_event:
                            self.event_callback.on_char_event(char_event)
                else:
                    # Multi-byte Unicode - generate CharEvent directly
                    # Skip KeyEvent generation for multi-byte characters
                    char_event = CharEvent(char=char)
                    self.event_callback.on_char_event(char_event)
            # else: still accumulating, wait for more bytes
        
        except curses.error:
            # Timeout or input error - ignore
            pass
    
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
        
        # Detect Shift modifier using the shifted characters set
        if key in self._shifted_chars:
            modifiers = ModifierKey.SHIFT
        
        # Look up key in key map
        if key in self._key_map:
            ttk_key_code = self._key_map[key]
            
            # Determine character representation
            char = chr(key) if 32 <= key <= 126 else None
            
            return KeyEvent(
                key_code=ttk_key_code,
                modifiers=modifiers,
                char=char
            )
        
        # Fallback for unmapped printable ASCII (32-126)
        if 32 <= key <= 126:
            return KeyEvent(
                key_code=key,
                modifiers=modifiers,
                char=chr(key)
            )
        
        # Completely unmapped key - return None wrapped in KeyEvent
        # (Return KeyEvent with the raw key code for compatibility)
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
    
    def set_caret_position(self, x: int, y: int) -> None:
        """
        Set the terminal caret position.
        
        This method stores the caret position, which will be automatically
        restored by refresh(). The caret position can be set even when hidden,
        which is useful for IME (Input Method Editor) composition text positioning.
        
        Applications no longer need to call this method immediately before refresh()
        - the position is remembered and automatically restored.
        
        Args:
            x: Column position (0-based, 0 is left)
            y: Row position (0-based, 0 is top)
        
        Note: Coordinates outside the window bounds are handled gracefully
        during refresh().
        """
        # Store the caret position for automatic restoration during refresh()
        self.caret_x = x
        self.caret_y = y
    
    def run_event_loop(self) -> None:
        """
        Run the event loop with callback-based event delivery.
        
        This method runs an event loop that continuously processes events
        and delivers them via the registered callback. The loop continues until
        interrupted or an exception occurs.
        
        Raises:
            RuntimeError: If event callback not set
        """
        if self.event_callback is None:
            raise RuntimeError("Event callback not set. Call set_event_callback() first.")
        
        # Run event loop until interrupted
        while True:
            try:
                # Process one iteration (blocking)
                self.run_event_loop_iteration(timeout_ms=-1)
                
            except KeyboardInterrupt:
                # Allow Ctrl+C to break the loop
                break
            except Exception as e:
                # Log error but continue loop
                print(f"Error in event loop: {e}")
                continue
    
    
    def supports_mouse(self) -> bool:
        """
        Query whether this backend supports mouse events.
        
        This method checks if the terminal has mouse capability. The check
        is performed during initialization and cached.
        
        Returns:
            bool: True if mouse events are available, False otherwise.
        """
        if self.stdscr is None:
            return False
        
        try:
            # Check if terminal has mouse capability
            # curses.has_key() is not reliable for KEY_MOUSE, so we check
            # if mousemask is available and try to enable it
            return hasattr(curses, 'mousemask') and hasattr(curses, 'getmouse')
        except (AttributeError, curses.error):
            return False
    
    def get_supported_mouse_events(self) -> set:
        """
        Query which mouse event types are supported.
        
        The curses backend typically only supports button clicks. Movement
        and wheel events are generally not available in terminal mode.
        
        Returns:
            set: Set of MouseEventType values supported by this backend.
        """
        if not self.supports_mouse():
            return set()
        
        # Curses typically only supports button down and button up events
        return {
            MouseEventType.BUTTON_DOWN,
            MouseEventType.BUTTON_UP
        }
    
    def enable_mouse_events(self) -> bool:
        """
        Enable mouse event capture in curses.
        
        This method enables mouse event tracking if the terminal supports it.
        If mouse events are not supported, it returns False and the application
        should continue without mouse support.
        
        Returns:
            bool: True if mouse events were successfully enabled, False otherwise.
        """
        if not self.supports_mouse():
            return False
        
        if self.mouse_enabled:
            # Already enabled
            return True
        
        try:
            # Enable all mouse events
            # ALL_MOUSE_EVENTS includes button presses, releases, and clicks
            # REPORT_MOUSE_POSITION enables position reporting
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            self.mouse_enabled = True
            self.mouse_available = True
            return True
        except (curses.error, AttributeError) as e:
            # Mouse not supported or error enabling
            self.mouse_enabled = False
            self.mouse_available = False
            return False
    
    def poll_mouse_event(self) -> Optional[MouseEvent]:
        """
        Poll for mouse events from curses.
        
        This method checks if a mouse event is available and returns it.
        If no mouse event is pending, it returns None immediately.
        
        Returns:
            Optional[MouseEvent]: MouseEvent if one is available, None otherwise.
        """
        if not self.mouse_enabled:
            return None
        
        try:
            # Check if there's a pending character
            # Use nodelay mode to avoid blocking
            self.stdscr.nodelay(True)
            ch = self.stdscr.getch()
            self.stdscr.nodelay(False)
            
            if ch == -1:
                # No input available
                return None
            
            if ch != curses.KEY_MOUSE:
                # Not a mouse event - put it back for other handlers
                curses.ungetch(ch)
                return None
            
            # Get mouse event details
            _, x, y, _, bstate = curses.getmouse()
            
            # Map curses button state to our event type and button
            event_type = self._map_curses_event_type(bstate)
            button = self._map_curses_button(bstate)
            
            if event_type is None:
                # Unsupported event type
                return None
            
            # Curses coordinates are already in text grid units
            # Sub-cell positioning not available in curses - use center of cell
            return MouseEvent(
                event_type=event_type,
                column=x,
                row=y,
                sub_cell_x=0.5,  # Center of cell
                sub_cell_y=0.5,  # Center of cell
                button=button,
                timestamp=0.0  # Will be set by MouseEvent.__post_init__
            )
        except (curses.error, ValueError):
            # Error getting mouse event - ignore
            return None
    
    def _map_curses_event_type(self, bstate: int) -> Optional[MouseEventType]:
        """
        Map curses button state to MouseEventType.
        
        Args:
            bstate: Curses button state bitmask
            
        Returns:
            Optional[MouseEventType]: Mapped event type, or None if unsupported
        """
        # Check for button press events
        if (bstate & curses.BUTTON1_PRESSED or
            bstate & curses.BUTTON2_PRESSED or
            bstate & curses.BUTTON3_PRESSED):
            return MouseEventType.BUTTON_DOWN
        
        # Check for button release events
        if (bstate & curses.BUTTON1_RELEASED or
            bstate & curses.BUTTON2_RELEASED or
            bstate & curses.BUTTON3_RELEASED):
            return MouseEventType.BUTTON_UP
        
        # Check for button click events (press + release)
        if (bstate & curses.BUTTON1_CLICKED or
            bstate & curses.BUTTON2_CLICKED or
            bstate & curses.BUTTON3_CLICKED):
            # Treat clicks as button down for simplicity
            return MouseEventType.BUTTON_DOWN
        
        # Unsupported event type
        return None
    
    def _map_curses_button(self, bstate: int) -> MouseButton:
        """
        Map curses button state to MouseButton.
        
        Args:
            bstate: Curses button state bitmask
            
        Returns:
            MouseButton: Mapped button identifier
        """
        # Check for button 1 (left button) events
        if (bstate & curses.BUTTON1_PRESSED or
            bstate & curses.BUTTON1_RELEASED or
            bstate & curses.BUTTON1_CLICKED):
            return MouseButton.LEFT
        
        # Check for button 2 (middle button) events
        if (bstate & curses.BUTTON2_PRESSED or
            bstate & curses.BUTTON2_RELEASED or
            bstate & curses.BUTTON2_CLICKED):
            return MouseButton.MIDDLE
        
        # Check for button 3 (right button) events
        if (bstate & curses.BUTTON3_PRESSED or
            bstate & curses.BUTTON3_RELEASED or
            bstate & curses.BUTTON3_CLICKED):
            return MouseButton.RIGHT
        
        # Default to NONE if no button detected
        return MouseButton.NONE
    
    
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
    
    def supports_drag_and_drop(self) -> bool:
        """
        Query whether this backend supports drag-and-drop operations.
        
        The Curses backend does not support drag-and-drop as it runs in
        terminal mode where native drag-and-drop is not available. Applications
        should check this method and gracefully disable drag-and-drop features
        when running in terminal mode.
        
        Returns:
            bool: Always False for Curses backend (terminal mode)
        
        Platform Support:
            - macOS (CoreGraphics): True - uses native NSDraggingSession
            - Terminal (Curses): False - drag-and-drop not supported
            - Windows (future): True - will use IDropSource/IDataObject
            - Linux (future): True - will use X11/Wayland drag protocols
        
        Example:
            if renderer.supports_drag_and_drop():
                print("Drag-and-drop enabled")
                # Enable drag gesture detection
            else:
                print("Drag-and-drop not available")
                # Use keyboard-only file operations
        """
        return False
    
    def start_drag_session(self, file_urls: list, drag_image_text: str) -> bool:
        """
        Start a drag-and-drop session (not supported in terminal mode).
        
        This method always returns False for the Curses backend as drag-and-drop
        is not available in terminal mode. Applications should check
        supports_drag_and_drop() before attempting to start a drag session.
        
        The method logs an informational message to help with debugging if
        it's called unexpectedly.
        
        Args:
            file_urls: List of file:// URLs to drag (ignored)
            drag_image_text: Text to display in drag image (ignored)
        
        Returns:
            bool: Always False (drag-and-drop not supported in terminal mode)
        
        Note: Applications should use keyboard-based file operations (copy, move)
        instead of drag-and-drop when running in terminal mode.
        
        Example:
            # Check support before attempting drag
            if renderer.supports_drag_and_drop():
                renderer.start_drag_session(urls, "3 files")
            else:
                print("Use keyboard shortcuts for file operations")
        """
        # Log informational message for debugging
        print("CursesBackend: Drag-and-drop not supported in terminal mode")
        return False
    
    def set_drag_completion_callback(self, callback) -> None:
        """
        Set callback for drag-and-drop completion (no-op in terminal mode).
        
        This method is a no-op for the Curses backend as drag-and-drop is not
        supported in terminal mode. The callback is never invoked.
        
        Args:
            callback: Callback function (ignored)
        
        Note: This method is provided for interface compatibility but has no
        effect in terminal mode.
        """
        # No-op: Terminal backend does not support drag-and-drop
        pass
