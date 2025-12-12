"""
TTK CoreGraphics Backend

This module implements a macOS CoreGraphics (Quartz 2D) rendering backend for TTK.
It enables TTK applications to run as native macOS desktop applications with
high-quality text rendering while maintaining full compatibility with the abstract
Renderer API.

The CoreGraphics backend uses Apple's Cocoa and CoreGraphics frameworks through
PyObjC to provide native macOS text rendering quality with minimal code complexity
(~300 lines vs ~1000+ for Metal).

Requirements:
    - macOS operating system
    - PyObjC framework (install with: pip install pyobjc-framework-Cocoa)

Architecture:
    - CoreGraphicsBackend: Main backend class implementing the Renderer interface
    - TTKView: Custom NSView subclass for rendering the character grid
    - Character grid: 2D array storing (char, color_pair, attributes) tuples
    - Color pairs: Dictionary mapping pair IDs to (fg_rgb, bg_rgb) tuples

Key Features:
    - Native macOS window with NSWindow
    - High-quality text rendering with NSAttributedString
    - Monospace font support with fixed character dimensions
    - Full color pair support (0-255)
    - Text attributes (bold, underline, reverse video)
    - Keyboard input handling with modifier key detection
    - Coordinate system transformation (top-left origin)

PyObjC Method Name Translation:
    PyObjC translates Objective-C method names to Python by replacing colons with
    underscores. Each colon in an Objective-C method name becomes an underscore
    followed by the parameter in Python.
    
    Examples:
        Objective-C: initWithFrame:
        PyObjC: initWithFrame_(frame)
        
        Objective-C: initWithFrame:backend:
        PyObjC: initWithFrame_backend_(frame, backend)
        
        Objective-C: setTitle:
        PyObjC: setTitle_(title)
        
        Objective-C: nextEventMatchingMask:untilDate:inMode:dequeue:
        PyObjC: nextEventMatchingMask_untilDate_inMode_dequeue_(mask, date, mode, dequeue)

Coordinate System:
    TTK uses a top-left origin coordinate system where (0, 0) is the top-left corner,
    row 0 is at the top, and row increases downward. CoreGraphics uses a bottom-left
    origin where (0, 0) is the bottom-left corner and y increases upward.
    
    This backend handles the coordinate transformation automatically:
        x_pixel = col * char_width
        y_pixel = (rows - row - 1) * char_height
    
    This ensures that TTK applications work identically across all backends without
    needing to know about the underlying coordinate system differences.

Example Usage:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    
    # Create and initialize the backend
    backend = CoreGraphicsBackend(
        window_title="My TTK App",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize a color pair (white on blue)
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))
    
    # Draw some text
    backend.draw_text(0, 0, "Hello, World!", color_pair=1)
    backend.refresh()
    
    # Get keyboard input
    event = backend.get_input(timeout_ms=-1)  # Block until input
    if event:
        print(f"Key pressed: {event.char}")
    
    # Clean up
    backend.shutdown()
"""

# Check PyObjC availability
try:
    import Cocoa
    import Quartz
    import objc
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False

# Import TTK base classes
from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import InputEvent, KeyCode, ModifierKey
from typing import Tuple, Optional, List, Dict


class CoreGraphicsBackend(Renderer):
    """
    CoreGraphics rendering backend for macOS.
    
    This backend implements the Renderer interface using Apple's CoreGraphics
    and Cocoa frameworks to provide native macOS desktop application support
    for TTK applications.
    
    The backend maintains a character grid and renders it using NSAttributedString
    for high-quality text rendering. It handles coordinate system transformation
    to match TTK's top-left origin convention.
    """
    
    def __init__(self, window_title: str = "TTK Application",
                 font_name: str = "Menlo", font_size: int = 14,
                 rows: int = 24, cols: int = 80):
        """
        Initialize the CoreGraphics backend.
        
        Args:
            window_title: Title for the window
            font_name: Name of the monospace font to use (default: "Menlo")
            font_size: Font size in points (default: 14)
            rows: Initial grid height in characters (default: 24)
            cols: Initial grid width in characters (default: 80)
        
        Raises:
            RuntimeError: If PyObjC is not installed
        """
        if not COCOA_AVAILABLE:
            raise RuntimeError(
                "PyObjC is required for CoreGraphics backend. "
                "Install with: pip install pyobjc-framework-Cocoa"
            )
        
        self.window_title = window_title
        self.font_name = font_name
        self.font_size = font_size
        self.rows = rows
        self.cols = cols
        
        # These will be initialized in initialize()
        self.window = None
        self.window_delegate = None
        self.view = None
        self.font = None
        self.char_width = 0
        self.char_height = 0
        self.grid: List[List[Tuple]] = []
        self.color_pairs: Dict[int, Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = {}
        
        # Cursor state
        self.cursor_visible = False
        self.cursor_row = 0
        self.cursor_col = 0
        
        # Window state
        self.should_close = False
    
    def initialize(self) -> None:
        """
        Initialize the rendering backend and create the window.
        
        This method:
        1. Sets up the NSApplication as a proper GUI application
        2. Loads and validates the monospace font
        3. Calculates character dimensions
        4. Creates the window and view
        5. Initializes the character grid
        6. Sets up default color pairs
        
        Raises:
            ValueError: If the specified font is not found
            RuntimeError: If window creation fails
        """
        # Set up NSApplication as a proper GUI application
        app = Cocoa.NSApplication.sharedApplication()
        
        # Set activation policy to regular application (shows in Dock, can be focused)
        # This is critical for receiving keyboard events
        app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyRegular)
        
        # Load and validate font
        self._load_font()
        
        # Calculate character dimensions
        self._calculate_char_dimensions()
        
        # Create window and view
        self._create_window()
        
        # Initialize character grid
        self._initialize_grid()
        
        # Initialize default color pair (0: white on black)
        self.color_pairs[0] = ((255, 255, 255), (0, 0, 0))
    
    def _load_font(self) -> None:
        """
        Load the monospace font.
        
        Raises:
            ValueError: If the font is not found
        """
        self.font = Cocoa.NSFont.fontWithName_size_(self.font_name, self.font_size)
        if not self.font:
            raise ValueError(
                f"Font '{self.font_name}' not found. "
                f"Use a valid monospace font like 'Menlo', 'Monaco', or 'Courier'."
            )
    
    def _calculate_char_dimensions(self) -> None:
        """
        Calculate fixed character width and height from the font.
        
        Uses the character 'M' (typically the widest in monospace fonts) to
        determine dimensions. Adds 20% line spacing to the height for better
        readability.
        """
        # Create an attributed string with the font to measure character size
        test_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            "M",
            {Cocoa.NSFontAttributeName: self.font}
        )
        
        # Get the size of the character
        size = test_string.size()
        
        # Store character dimensions
        # Width is exact, height gets 20% line spacing
        self.char_width = int(size.width)
        self.char_height = int(size.height * 1.2)
    
    def _create_window(self) -> None:
        """
        Create the NSWindow with calculated dimensions.
        
        Calculates window size from grid dimensions and character size,
        then creates an NSWindow with appropriate style mask for standard
        macOS window controls (close, minimize, resize).
        
        Raises:
            RuntimeError: If window creation fails
        """
        # Calculate window dimensions from grid size and character dimensions
        window_width = self.cols * self.char_width
        window_height = self.rows * self.char_height
        
        # Create window frame (positioned at top-left of screen with some offset)
        # NSMakeRect(x, y, width, height) - x,y is bottom-left corner in screen coordinates
        frame = Cocoa.NSMakeRect(100, 100, window_width, window_height)
        
        # Create style mask with standard window controls
        # NSWindowStyleMaskTitled: Window has a title bar
        # NSWindowStyleMaskClosable: Window has a close button
        # NSWindowStyleMaskMiniaturizable: Window has a minimize button
        # NSWindowStyleMaskResizable: Window can be resized
        style_mask = (Cocoa.NSWindowStyleMaskTitled |
                     Cocoa.NSWindowStyleMaskClosable |
                     Cocoa.NSWindowStyleMaskMiniaturizable |
                     Cocoa.NSWindowStyleMaskResizable)
        
        # Create the window using PyObjC method name translation
        # Objective-C: initWithContentRect:styleMask:backing:defer:
        # PyObjC: initWithContentRect_styleMask_backing_defer_()
        # Each colon in Objective-C becomes an underscore followed by parameter
        self.window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            Cocoa.NSBackingStoreBuffered,  # Use buffered backing store for performance
            False  # Don't defer window creation
        )
        
        # Verify window was created successfully
        if not self.window:
            raise RuntimeError(
                "Failed to create window. Check system resources and permissions."
            )
        
        # Set window title from initialization parameter
        # PyObjC method: setTitle_() corresponds to Objective-C setTitle:
        self.window.setTitle_(self.window_title)
        
        # Create window delegate to handle window events
        self.window_delegate = TTKWindowDelegate.alloc().initWithBackend_(self)
        self.window.setDelegate_(self.window_delegate)
        
        # Create and set up the custom TTKView
        content_rect = self.window.contentView().frame()
        # Use our custom initializer: initWithFrame_backend_()
        # This corresponds to Objective-C: initWithFrame:backend:
        self.view = TTKView.alloc().initWithFrame_backend_(content_rect, self)
        self.window.setContentView_(self.view)
        
        # Show the window and make it the key window (receives keyboard input)
        # makeKeyAndOrderFront_() corresponds to Objective-C makeKeyAndOrderFront:
        # The parameter (None) is the sender, which we don't need
        self.window.makeKeyAndOrderFront_(None)
        
        # Make the view the first responder to receive keyboard events
        self.window.makeFirstResponder_(self.view)
        
        # Activate the application to bring it to front
        app = Cocoa.NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
    
    def _initialize_grid(self) -> None:
        """
        Initialize the character grid.
        
        Creates a 2D list where each cell contains a tuple of:
        (char: str, color_pair: int, attributes: int)
        
        All cells are initialized to space character with default color pair (0)
        and no attributes.
        """
        # Create 2D grid initialized with empty cells
        # Each cell is (char, color_pair, attributes)
        self.grid = [
            [(' ', 0, 0) for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
    
    def shutdown(self) -> None:
        """
        Clean up resources and close the window.
        
        This method performs cleanup in the following order:
        1. Close the native window
        2. Clear the view reference
        3. Clear the font reference
        4. Clear the character grid
        5. Clear color pair storage
        6. Reset dimensions
        7. Reset cursor state
        
        This method handles cleanup gracefully even if some resources
        were not fully initialized. It's safe to call shutdown() multiple
        times or even if initialize() was never called.
        
        All cleanup operations are wrapped in try-except blocks to ensure
        that errors in one cleanup step don't prevent other cleanup steps
        from executing.
        
        Example:
            backend = CoreGraphicsBackend()
            backend.initialize()
            # ... use backend ...
            backend.shutdown()
        """
        # Close the native window
        if self.window is not None:
            try:
                self.window.close()
            except (AttributeError, RuntimeError) as e:
                # Window may already be closed or in invalid state
                print(f"Warning: Error closing window during shutdown: {e}")
            except Exception as e:
                # Catch any other unexpected errors during cleanup
                print(f"Warning: Unexpected error closing window: {e}")
            finally:
                self.window = None
        
        # Clear view reference
        self.view = None
        
        # Clear font reference
        self.font = None
        
        # Clear character grid
        self.grid = []
        
        # Clear color pair storage
        self.color_pairs = {}
        
        # Reset dimensions
        self.rows = 0
        self.cols = 0
        self.char_width = 0
        self.char_height = 0
        
        # Reset cursor state
        self.cursor_visible = False
        self.cursor_row = 0
        self.cursor_col = 0
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get window dimensions in character cells.
        
        Returns:
            Tuple[int, int]: (rows, cols) - Current grid dimensions
        """
        return (self.rows, self.cols)
    
    def clear(self) -> None:
        """
        Clear the entire window.
        
        Resets all cells in the character grid to space character with
        default color pair (0) and no attributes. This effectively clears
        the entire display.
        
        The actual visual update occurs when refresh() is called.
        """
        try:
            # Reset all cells to space with default color pair and no attributes
            for row in range(self.rows):
                for col in range(self.cols):
                    self.grid[row][col] = (' ', 0, 0)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: clear failed: {e}")
    
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Clear a rectangular region of the window.
        
        Resets all cells in the specified rectangular region to space character
        with default color pair (0) and no attributes.
        
        Handles out-of-bounds coordinates gracefully by clamping to valid ranges.
        
        Args:
            row: Starting row (top of region)
            col: Starting column (left of region)
            height: Height of region in characters
            width: Width of region in characters
        """
        try:
            # Clamp coordinates to valid ranges
            start_row = max(0, min(row, self.rows - 1))
            start_col = max(0, min(col, self.cols - 1))
            end_row = max(0, min(row + height, self.rows))
            end_col = max(0, min(col + width, self.cols))
            
            # Clear cells in the specified region
            for r in range(start_row, end_row):
                for c in range(start_col, end_col):
                    self.grid[r][c] = (' ', 0, 0)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: clear_region failed at ({row}, {col}, {height}, {width}): {e}")
    
    def draw_text(self, row: int, col: int, text: str,
                  color_pair: int = 0, attributes: int = 0) -> None:
        """
        Draw text at the specified position.
        
        Updates the character grid cells with the provided text, color pair,
        and attributes. Each character in the text is placed in a separate
        grid cell, starting at the specified position and extending to the right.
        
        Handles out-of-bounds coordinates gracefully by ignoring characters
        that would be placed outside the grid.
        
        Args:
            row: Row position (0-based from top)
            col: Column position (0-based from left)
            text: Text string to draw
            color_pair: Color pair ID to use (default: 0)
            attributes: Text attributes (bold, underline, reverse) as bitwise OR
        """
        try:
            # Ignore if starting position is out of bounds
            if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
                return
            
            # Draw each character in the text
            for i, char in enumerate(text):
                current_col = col + i
                
                # Stop if we've reached the right edge of the grid
                if current_col >= self.cols:
                    break
                
                # Update the grid cell with the character, color pair, and attributes
                self.grid[row][current_col] = (char, color_pair, attributes)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: draw_text failed at ({row}, {col}): {e}")
    
    def draw_hline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a horizontal line.
        
        Draws a horizontal line using the specified character, starting at
        the given position and extending to the right for the specified length.
        
        Handles out-of-bounds coordinates gracefully by clamping to valid ranges.
        
        Args:
            row: Row position for the line
            col: Starting column position
            char: Character to use for the line (typically '-' or '─')
            length: Length of the line in characters
            color_pair: Color pair ID to use (default: 0)
        """
        try:
            # Ignore if row is out of bounds
            if row < 0 or row >= self.rows:
                return
            
            # Clamp starting column to valid range
            start_col = max(0, col)
            
            # Calculate ending column (clamped to grid width)
            end_col = min(col + length, self.cols)
            
            # Draw the horizontal line
            for c in range(start_col, end_col):
                self.grid[row][c] = (char, color_pair, 0)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: draw_hline failed at ({row}, {col}): {e}")
    
    def draw_vline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a vertical line.
        
        Draws a vertical line using the specified character, starting at
        the given position and extending downward for the specified length.
        
        Handles out-of-bounds coordinates gracefully by clamping to valid ranges.
        
        Args:
            row: Starting row position
            col: Column position for the line
            char: Character to use for the line (typically '|' or '│')
            length: Length of the line in characters
            color_pair: Color pair ID to use (default: 0)
        """
        try:
            # Ignore if column is out of bounds
            if col < 0 or col >= self.cols:
                return
            
            # Clamp starting row to valid range
            start_row = max(0, row)
            
            # Calculate ending row (clamped to grid height)
            end_row = min(row + length, self.rows)
            
            # Draw the vertical line
            for r in range(start_row, end_row):
                self.grid[r][col] = (char, color_pair, 0)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: draw_vline failed at ({row}, {col}): {e}")
    
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """
        Draw a rectangle.
        
        Draws either a filled rectangle or an outlined rectangle using
        box-drawing characters.
        
        For outlined rectangles, uses Unicode box-drawing characters:
        - Corners: ┌ ┐ └ ┘
        - Horizontal edges: ─
        - Vertical edges: │
        
        For filled rectangles, fills the entire area with space characters
        using the specified color pair (which will show as a colored block
        due to the background color).
        
        Handles out-of-bounds coordinates gracefully by clamping to valid ranges.
        
        Args:
            row: Starting row (top of rectangle)
            col: Starting column (left of rectangle)
            height: Height of rectangle in characters
            width: Width of rectangle in characters
            color_pair: Color pair ID to use (default: 0)
            filled: If True, draw filled rectangle; if False, draw outline only
        """
        try:
            # Ignore if dimensions are invalid
            if height <= 0 or width <= 0:
                return
            
            # Clamp coordinates to valid ranges
            start_row = max(0, row)
            start_col = max(0, col)
            end_row = min(row + height, self.rows)
            end_col = min(col + width, self.cols)
            
            # Recalculate actual dimensions after clamping
            actual_height = end_row - start_row
            actual_width = end_col - start_col
            
            # Ignore if clamping resulted in zero dimensions
            if actual_height <= 0 or actual_width <= 0:
                return
            
            if filled:
                # Draw filled rectangle by filling all cells with space character
                # The background color from the color pair will show through
                for r in range(start_row, end_row):
                    for c in range(start_col, end_col):
                        self.grid[r][c] = (' ', color_pair, 0)
            else:
                # Draw outlined rectangle using box-drawing characters
                # For rectangles with height or width of 1 or 2, we need special handling
                
                if actual_height == 1:
                    # Single row rectangle - just draw horizontal line
                    for c in range(start_col, end_col):
                        self.grid[start_row][c] = ('─', color_pair, 0)
                elif actual_width == 1:
                    # Single column rectangle - just draw vertical line
                    for r in range(start_row, end_row):
                        self.grid[r][start_col] = ('│', color_pair, 0)
                else:
                    # Normal rectangle with at least 2x2 dimensions
                    
                    # Draw top edge
                    # Top-left corner
                    self.grid[start_row][start_col] = ('┌', color_pair, 0)
                    
                    # Top edge
                    for c in range(start_col + 1, end_col - 1):
                        self.grid[start_row][c] = ('─', color_pair, 0)
                    
                    # Top-right corner
                    self.grid[start_row][end_col - 1] = ('┐', color_pair, 0)
                    
                    # Draw left and right edges (if there are rows between top and bottom)
                    for r in range(start_row + 1, end_row - 1):
                        # Left edge
                        self.grid[r][start_col] = ('│', color_pair, 0)
                        
                        # Right edge
                        self.grid[r][end_col - 1] = ('│', color_pair, 0)
                    
                    # Draw bottom edge
                    # Bottom-left corner
                    self.grid[end_row - 1][start_col] = ('└', color_pair, 0)
                    
                    # Bottom edge
                    for c in range(start_col + 1, end_col - 1):
                        self.grid[end_row - 1][c] = ('─', color_pair, 0)
                    
                    # Bottom-right corner
                    self.grid[end_row - 1][end_col - 1] = ('┘', color_pair, 0)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: draw_rect failed at ({row}, {col}, {height}, {width}): {e}")
    
    def refresh(self) -> None:
        """
        Refresh the entire window to display all pending changes.
        
        Marks the entire view as needing display, which triggers the Cocoa
        event loop to call drawRect_ on the next display cycle. This causes
        all pending changes to the character grid to be rendered to the screen.
        """
        try:
            if self.view:
                self.view.setNeedsDisplay_(True)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: refresh failed: {e}")
    
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Refresh a specific region of the window.
        
        Marks a specific rectangular region of the view as needing display.
        This is more efficient than refreshing the entire window when only
        a small region has changed.
        
        Args:
            row: Starting row of the region
            col: Starting column of the region
            height: Height of the region in characters
            width: Width of the region in characters
        """
        try:
            if self.view:
                # Calculate pixel coordinates for the region
                x = col * self.char_width
                y = (self.rows - row - height) * self.char_height
                pixel_width = width * self.char_width
                pixel_height = height * self.char_height
                
                # Create NSRect for the region
                region_rect = Cocoa.NSMakeRect(x, y, pixel_width, pixel_height)
                
                # Mark the region as needing display
                self.view.setNeedsDisplayInRect_(region_rect)
        except Exception as e:
            # Log warning but continue execution without crashing
            print(f"Warning: refresh_region failed at ({row}, {col}, {height}, {width}): {e}")
    
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        """
        Initialize a color pair with RGB values.
        
        Color pairs are used to specify foreground and background colors for text
        rendering. Each color pair has a unique ID (1-255) and stores RGB values
        for both foreground and background colors.
        
        Color pair 0 is reserved for default colors (white on black) and cannot
        be modified.
        
        Args:
            pair_id: Color pair ID (must be 1-255)
            fg_color: Foreground RGB color as (r, g, b) tuple (0-255 each)
            bg_color: Background RGB color as (r, g, b) tuple (0-255 each)
        
        Raises:
            ValueError: If pair_id is out of range (< 1 or > 255)
            ValueError: If any RGB component is out of range (< 0 or > 255)
        
        Example:
            # Initialize color pair 1 with white text on blue background
            backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))
        """
        # Validate color pair ID is in range 1-255
        if pair_id < 1 or pair_id > 255:
            raise ValueError(
                f"Color pair ID must be 1-255, got {pair_id}. "
                f"Color pair 0 is reserved for default colors."
            )
        
        # Validate RGB components are in range 0-255
        for component in fg_color:
            if component < 0 or component > 255:
                raise ValueError(
                    f"RGB components must be 0-255, got {component} in foreground color"
                )
        
        for component in bg_color:
            if component < 0 or component > 255:
                raise ValueError(
                    f"RGB components must be 0-255, got {component} in background color"
                )
        
        # Store color pair in dictionary
        self.color_pairs[pair_id] = (fg_color, bg_color)
    
    def get_input(self, timeout_ms: int = -1) -> Optional[InputEvent]:
        """
        Get the next input event from the macOS event system.
        
        This method polls the macOS event queue for keyboard events and
        translates them into TTK's unified InputEvent format. It supports
        blocking, non-blocking, and timed input modes.
        
        Args:
            timeout_ms: Timeout in milliseconds.
                       -1: Block indefinitely until input is available
                        0: Non-blocking, return immediately if no input
                       >0: Wait up to timeout_ms milliseconds for input
        
        Returns:
            Optional[InputEvent]: An InputEvent object if input is available,
                                 or None if the timeout expires with no input.
        
        Example:
            # Non-blocking check for input
            event = backend.get_input(timeout_ms=0)
            if event:
                print(f"Got key: {event.key_code}")
            
            # Blocking wait for input
            event = backend.get_input(timeout_ms=-1)
            print(f"User pressed: {event.char}")
        """
        # Check if window should close
        if self.should_close:
            # Return a special quit event (Q key)
            return InputEvent(
                key_code=ord('Q'),
                modifiers=ModifierKey.NONE,
                char='Q'
            )
        
        # Get the shared application instance
        app = Cocoa.NSApplication.sharedApplication()
        
        # Calculate timeout date based on timeout_ms
        if timeout_ms < 0:
            # Blocking mode - use distant future (wait indefinitely)
            until_date = Cocoa.NSDate.distantFuture()
        elif timeout_ms == 0:
            # Non-blocking mode - use None to return immediately
            until_date = None
        else:
            # Timed mode - calculate date from now + timeout
            timeout_seconds = timeout_ms / 1000.0
            # PyObjC method: dateWithTimeIntervalSinceNow_()
            # Corresponds to Objective-C: dateWithTimeIntervalSinceNow:
            until_date = Cocoa.NSDate.dateWithTimeIntervalSinceNow_(timeout_seconds)
        
        # Define event mask for all events we care about
        event_mask = (
            Cocoa.NSEventMaskKeyDown |
            Cocoa.NSEventMaskKeyUp |
            Cocoa.NSEventMaskFlagsChanged |
            Cocoa.NSEventMaskLeftMouseDown |
            Cocoa.NSEventMaskLeftMouseUp |
            Cocoa.NSEventMaskRightMouseDown |
            Cocoa.NSEventMaskRightMouseUp |
            Cocoa.NSEventMaskMouseMoved |
            Cocoa.NSEventMaskLeftMouseDragged |
            Cocoa.NSEventMaskRightMouseDragged |
            Cocoa.NSEventMaskMouseEntered |
            Cocoa.NSEventMaskMouseExited |
            Cocoa.NSEventMaskScrollWheel |
            Cocoa.NSEventMaskAppKitDefined |
            Cocoa.NSEventMaskSystemDefined |
            Cocoa.NSEventMaskApplicationDefined |
            Cocoa.NSEventMaskPeriodic |
            Cocoa.NSEventMaskCursorUpdate
        )
        
        # Poll for next event using PyObjC method name translation
        # Objective-C: nextEventMatchingMask:untilDate:inMode:dequeue:
        # PyObjC: nextEventMatchingMask_untilDate_inMode_dequeue_()
        # Each colon becomes an underscore followed by the parameter
        # Use NSDefaultRunLoopMode for normal event processing
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            event_mask,
            until_date,
            Cocoa.NSDefaultRunLoopMode,
            True  # dequeue the event (remove it from the queue)
        )
        
        # If no event available, return None
        if event is None:
            return None
        
        # Dispatch the event to ensure proper handling by the system
        # This allows the event to be processed by the normal Cocoa event chain
        # PyObjC method: sendEvent_() corresponds to Objective-C sendEvent:
        app.sendEvent_(event)
        
        # Update the display after processing events
        app.updateWindows()
        
        # Translate the NSEvent to InputEvent
        return self._translate_event(event)
    
    def _translate_event(self, event) -> Optional[InputEvent]:
        """
        Translate a macOS NSEvent to a TTK InputEvent.
        
        This method converts macOS-specific keyboard events into TTK's unified
        InputEvent format. It handles:
        - Keyboard events: Maps macOS key codes to TTK KeyCode values
        - Modifier keys: Extracts Shift, Control, Alt, Command states
        - Printable characters: Preserves character information
        
        Args:
            event: NSEvent object from macOS event system
        
        Returns:
            Optional[InputEvent]: Translated InputEvent, or None if the event
                                 type is not supported or cannot be translated.
        """
        if event is None:
            return None
        
        # Get event type
        event_type = event.type()
        
        # Only handle key down events (ignore key up and flags changed)
        if event_type != Cocoa.NSEventTypeKeyDown:
            return None
        
        # Get the key code (hardware-dependent but consistent on macOS)
        key_code = event.keyCode()
        
        # Get modifier flags
        modifiers = self._extract_modifiers(event)
        
        # Get the character string
        chars = event.characters()
        char = chars[0] if chars and len(chars) > 0 else None
        
        # Map macOS key codes to TTK KeyCode values
        # These are standard macOS virtual key codes
        key_map = {
            # Arrow keys
            123: KeyCode.LEFT,
            124: KeyCode.RIGHT,
            125: KeyCode.DOWN,
            126: KeyCode.UP,
            
            # Function keys
            122: KeyCode.F1,
            120: KeyCode.F2,
            99: KeyCode.F3,
            118: KeyCode.F4,
            96: KeyCode.F5,
            97: KeyCode.F6,
            98: KeyCode.F7,
            100: KeyCode.F8,
            101: KeyCode.F9,
            109: KeyCode.F10,
            103: KeyCode.F11,
            111: KeyCode.F12,
            
            # Editing keys
            51: KeyCode.BACKSPACE,  # Delete key (backspace)
            117: KeyCode.DELETE,     # Forward delete
            115: KeyCode.HOME,
            119: KeyCode.END,
            116: KeyCode.PAGE_UP,
            121: KeyCode.PAGE_DOWN,
            
            # Special keys
            36: KeyCode.ENTER,       # Return key
            76: KeyCode.ENTER,       # Enter key (numeric keypad)
            53: KeyCode.ESCAPE,
            48: KeyCode.TAB,
        }
        
        # Check if this is a special key
        if key_code in key_map:
            ttk_key_code = key_map[key_code]
            return InputEvent(
                key_code=ttk_key_code,
                modifiers=modifiers,
                char=None  # Special keys don't have printable characters
            )
        
        # Handle printable characters
        if char and len(char) == 1:
            # Handle special characters that might come through as printable
            if char == '\r' or char == '\n':
                return InputEvent(
                    key_code=KeyCode.ENTER,
                    modifiers=modifiers,
                    char=None
                )
            elif char == '\t':
                return InputEvent(
                    key_code=KeyCode.TAB,
                    modifiers=modifiers,
                    char=None
                )
            elif char == '\x1b':  # Escape
                return InputEvent(
                    key_code=KeyCode.ESCAPE,
                    modifiers=modifiers,
                    char=None
                )
            elif char == '\x7f':  # Delete/Backspace
                return InputEvent(
                    key_code=KeyCode.BACKSPACE,
                    modifiers=modifiers,
                    char=None
                )
            else:
                # Regular printable character
                code_point = ord(char)
                return InputEvent(
                    key_code=code_point,
                    modifiers=modifiers,
                    char=char
                )
        
        # Unknown key - return None
        return None
    
    def _extract_modifiers(self, event) -> int:
        """
        Extract modifier key flags from an NSEvent.
        
        This method examines the modifier flags in a macOS event and
        translates them to TTK's ModifierKey flags. It handles:
        - Shift key (NSEventModifierFlagShift)
        - Control key (NSEventModifierFlagControl)
        - Alt/Option key (NSEventModifierFlagOption)
        - Command key (NSEventModifierFlagCommand)
        
        Args:
            event: NSEvent object with modifier flags
        
        Returns:
            int: Bitwise OR of ModifierKey flags
        """
        modifiers = ModifierKey.NONE
        
        # Get modifier flags from the event
        modifier_flags = event.modifierFlags()
        
        # Map NSEvent modifier flags to TTK ModifierKey flags
        if modifier_flags & Cocoa.NSEventModifierFlagShift:
            modifiers |= ModifierKey.SHIFT
        
        if modifier_flags & Cocoa.NSEventModifierFlagControl:
            modifiers |= ModifierKey.CONTROL
        
        if modifier_flags & Cocoa.NSEventModifierFlagOption:
            modifiers |= ModifierKey.ALT
        
        if modifier_flags & Cocoa.NSEventModifierFlagCommand:
            modifiers |= ModifierKey.COMMAND
        
        return modifiers
    
    def set_cursor_visibility(self, visible: bool) -> None:
        """
        Set cursor visibility.
        
        Controls whether the text cursor is visible in the window. When visible,
        the cursor is drawn as a block at the current cursor position during
        rendering. The cursor position is set using move_cursor().
        
        Args:
            visible: True to show the cursor, False to hide it.
        
        Example:
            # Hide the cursor (typical for most applications)
            backend.set_cursor_visibility(False)
            
            # Show the cursor at a specific position
            backend.set_cursor_visibility(True)
            backend.move_cursor(5, 10)
            backend.refresh()
        """
        self.cursor_visible = visible
        # Trigger a redraw to show/hide the cursor
        if self.view:
            self.view.setNeedsDisplay_(True)
    
    def move_cursor(self, row: int, col: int) -> None:
        """
        Move the cursor to the specified position.
        
        Sets the cursor position in the character grid. The cursor is only
        visible if set_cursor_visibility(True) has been called. Coordinates
        are clamped to valid grid bounds to prevent out-of-bounds errors.
        
        Args:
            row: Row position (0-based, 0 is top)
            col: Column position (0-based, 0 is left)
        
        Example:
            # Position cursor at row 5, column 10
            backend.set_cursor_visibility(True)
            backend.move_cursor(5, 10)
            backend.refresh()
        """
        # Clamp coordinates to valid grid bounds
        self.cursor_row = max(0, min(row, self.rows - 1))
        self.cursor_col = max(0, min(col, self.cols - 1))
        
        # Trigger a redraw if cursor is visible
        if self.cursor_visible and self.view:
            self.view.setNeedsDisplay_(True)


# Define TTKWindowDelegate class for handling window events
if COCOA_AVAILABLE:
    try:
        # Try to get existing class first
        TTKWindowDelegate = objc.lookUpClass('TTKWindowDelegate')
    except objc.nosuchclass_error:
        # Class doesn't exist yet, create it
        class TTKWindowDelegate(Cocoa.NSObject):
            """
            Window delegate for handling window events.
            
            This delegate handles window close events and resize events,
            allowing the application to respond appropriately.
            """
            
            def initWithBackend_(self, backend):
                """
                Initialize the window delegate with a backend reference.
                
                Args:
                    backend: Reference to the CoreGraphicsBackend instance
                
                Returns:
                    self: The initialized delegate instance
                """
                self = objc.super(TTKWindowDelegate, self).init()
                if self is None:
                    return None
                
                self.backend = backend
                return self
            
            def windowShouldClose_(self, sender):
                """
                Handle window close button click.
                
                This method is called when the user clicks the window close button.
                We set a flag to indicate the window should close, which will be
                picked up by get_input().
                
                Args:
                    sender: The window that is requesting to close
                
                Returns:
                    bool: True to allow the window to close
                """
                self.backend.should_close = True
                return True
            
            def windowDidResize_(self, notification):
                """
                Handle window resize events.
                
                This method is called when the window is resized. We recalculate
                the grid dimensions based on the new window size and reinitialize
                the character grid.
                
                Args:
                    notification: NSNotification containing resize information
                """
                # Get the new content view size
                content_rect = self.backend.window.contentView().frame()
                new_width = int(content_rect.size.width)
                new_height = int(content_rect.size.height)
                
                # Calculate new grid dimensions
                new_cols = max(1, new_width // self.backend.char_width)
                new_rows = max(1, new_height // self.backend.char_height)
                
                # Only update if dimensions actually changed
                if new_cols != self.backend.cols or new_rows != self.backend.rows:
                    # Store old grid
                    old_grid = self.backend.grid
                    old_rows = self.backend.rows
                    old_cols = self.backend.cols
                    
                    # Update dimensions
                    self.backend.cols = new_cols
                    self.backend.rows = new_rows
                    
                    # Create new grid
                    new_grid = [
                        [(' ', 0, 0) for _ in range(new_cols)]
                        for _ in range(new_rows)
                    ]
                    
                    # Copy old content to new grid (as much as fits)
                    for row in range(min(old_rows, new_rows)):
                        for col in range(min(old_cols, new_cols)):
                            new_grid[row][col] = old_grid[row][col]
                    
                    # Update grid
                    self.backend.grid = new_grid
                    
                    # Trigger redraw
                    self.backend.view.setNeedsDisplay_(True)
else:
    # Provide a dummy class when PyObjC is not available
    class TTKWindowDelegate:
        """Dummy TTKWindowDelegate class when PyObjC is not available."""
        pass

# Define TTKView class with proper PyObjC registration
# Use try/except to handle the case where the class is already registered
if COCOA_AVAILABLE:
    try:
        # Try to get existing class first
        TTKView = objc.lookUpClass('TTKView')
    except objc.nosuchclass_error:
        # Class doesn't exist yet, create it
        class TTKView(Cocoa.NSView):
            """
            Custom NSView subclass for rendering the TTK character grid.
            
            This view handles the actual drawing operations by iterating through
            the character grid and rendering each cell using NSAttributedString.
            It also handles keyboard focus for input events.
            
            The view stores a reference to the CoreGraphicsBackend to access the
            character grid, font, and color pair information during rendering.
            """
            
            def initWithFrame_backend_(self, frame, backend):
                """
                Initialize the TTK view with a frame and backend reference.
                
                This is a custom initializer that follows PyObjC naming conventions
                for Objective-C methods with multiple parameters.
                
                PyObjC Method Name Translation:
                    Objective-C: initWithFrame:backend:
                    PyObjC: initWithFrame_backend_()
                    
                    Each colon (:) in the Objective-C method name becomes an underscore (_)
                    followed by the parameter in Python. The method name uses underscores
                    to separate parameter names.
                    
                    Examples:
                    - init → init()
                    - initWithFrame: → initWithFrame_()
                    - initWithFrame:backend: → initWithFrame_backend_()
                    - setTitle: → setTitle_()
                    - drawAtPoint: → drawAtPoint_()
                
                Args:
                    frame: NSRect frame for the view
                    backend: Reference to the CoreGraphicsBackend instance
                
                Returns:
                    self: The initialized view instance
                """
                # Call the superclass initializer using objc.super()
                # This is the PyObjC way to call superclass methods
                self = objc.super(TTKView, self).initWithFrame_(frame)
                
                if self is None:
                    return None
                
                # Store reference to backend for accessing grid, font, and colors
                # during rendering in drawRect_()
                self.backend = backend
                
                return self
            
            def drawRect_(self, rect):
                """
                Render the character grid.
                
                This method is called by the Cocoa event loop when the view needs
                to be redrawn. It iterates through the character grid and renders
                each non-empty cell.
                
                PyObjC Method Name Translation:
                    Objective-C: drawRect:
                    PyObjC: drawRect_()
                    The trailing underscore indicates a single parameter method.
                
                The rendering process:
                1. Iterate through each cell in the character grid
                2. Skip empty cells (space with default color pair) for performance
                3. Calculate pixel position using coordinate transformation
                4. Draw background rectangle for the cell
                5. Create NSAttributedString with font, color, and attributes
                6. Draw the character at the calculated position
                
                Args:
                    rect: NSRect indicating the region that needs to be redrawn
                """
                # Get the current graphics context (may be None if not in drawing context)
                graphics_context = Cocoa.NSGraphicsContext.currentContext()
                if graphics_context is None:
                    # Not in a valid drawing context, skip rendering
                    return
                
                # Iterate through each cell in the character grid
                for row in range(self.backend.rows):
                    for col in range(self.backend.cols):
                        # Get cell data: (char, color_pair, attributes)
                        char, color_pair, attributes = self.backend.grid[row][col]
                        
                        # Skip empty cells (space with default color pair) for performance
                        # This optimization significantly improves rendering speed
                        if char == ' ' and color_pair == 0:
                            continue
                        
                        # Calculate pixel position using coordinate transformation
                        # IMPORTANT: Coordinate system transformation
                        # TTK uses top-left origin (0,0) where row 0 is at the top
                        # CoreGraphics uses bottom-left origin where y=0 is at the bottom
                        # 
                        # Transformation formulas:
                        #   x = col * char_width  (no transformation needed for x-axis)
                        #   y = (rows - row - 1) * char_height  (flip y-axis)
                        # 
                        # Example for 24-row grid:
                        #   TTK row 0  → pixel y = (24 - 0 - 1) * char_height = 23 * char_height (top)
                        #   TTK row 23 → pixel y = (24 - 23 - 1) * char_height = 0 * char_height (bottom)
                        x = col * self.backend.char_width
                        y = (self.backend.rows - row - 1) * self.backend.char_height
                        
                        # Get foreground and background colors from color pair
                        if color_pair in self.backend.color_pairs:
                            fg_rgb, bg_rgb = self.backend.color_pairs[color_pair]
                        else:
                            # Use default colors if color pair not found
                            fg_rgb, bg_rgb = self.backend.color_pairs[0]
                        
                        # Handle reverse video attribute by swapping colors
                        if attributes & TextAttribute.REVERSE:
                            fg_rgb, bg_rgb = bg_rgb, fg_rgb
                        
                        # Draw background rectangle for the cell
                        bg_color = Cocoa.NSColor.colorWithRed_green_blue_alpha_(
                            bg_rgb[0] / 255.0,
                            bg_rgb[1] / 255.0,
                            bg_rgb[2] / 255.0,
                            1.0
                        )
                        bg_color.setFill()
                        
                        # Create rectangle for the cell background
                        cell_rect = Cocoa.NSMakeRect(
                            x,
                            y,
                            self.backend.char_width,
                            self.backend.char_height
                        )
                        Cocoa.NSRectFill(cell_rect)
                        
                        # Create foreground color for the character
                        fg_color = Cocoa.NSColor.colorWithRed_green_blue_alpha_(
                            fg_rgb[0] / 255.0,
                            fg_rgb[1] / 255.0,
                            fg_rgb[2] / 255.0,
                            1.0
                        )
                        
                        # Start with the base font
                        font = self.backend.font
                        
                        # Apply bold attribute if present
                        if attributes & TextAttribute.BOLD:
                            # Use NSFontManager to convert font to bold variant
                            font_manager = Cocoa.NSFontManager.sharedFontManager()
                            # PyObjC method: convertFont_toHaveTrait_()
                            # Corresponds to Objective-C: convertFont:toHaveTrait:
                            font = font_manager.convertFont_toHaveTrait_(
                                font,
                                Cocoa.NSBoldFontMask
                            )
                        
                        # Build attributes dictionary for NSAttributedString
                        # NSAttributedString uses a dictionary to specify text styling
                        text_attributes = {
                            Cocoa.NSFontAttributeName: font,
                            Cocoa.NSForegroundColorAttributeName: fg_color
                        }
                        
                        # Apply underline attribute if present
                        if attributes & TextAttribute.UNDERLINE:
                            text_attributes[Cocoa.NSUnderlineStyleAttributeName] = (
                                Cocoa.NSUnderlineStyleSingle
                            )
                        
                        # Create NSAttributedString for the character
                        # PyObjC method: initWithString_attributes_()
                        # Corresponds to Objective-C: initWithString:attributes:
                        attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
                            char,
                            text_attributes
                        )
                        
                        # Draw the character at the calculated position
                        # PyObjC method: drawAtPoint_() corresponds to Objective-C drawAtPoint:
                        attr_string.drawAtPoint_(Cocoa.NSMakePoint(x, y))
                
                # Draw cursor if visible
                if self.backend.cursor_visible:
                    # Calculate cursor pixel position
                    cursor_x = self.backend.cursor_col * self.backend.char_width
                    cursor_y = (self.backend.rows - self.backend.cursor_row - 1) * self.backend.char_height
                    
                    # Draw cursor as a filled rectangle with inverted colors
                    # Use white color for visibility
                    cursor_color = Cocoa.NSColor.colorWithRed_green_blue_alpha_(
                        1.0, 1.0, 1.0, 0.8  # White with slight transparency
                    )
                    cursor_color.setFill()
                    
                    # Create rectangle for the cursor
                    cursor_rect = Cocoa.NSMakeRect(
                        cursor_x,
                        cursor_y,
                        self.backend.char_width,
                        self.backend.char_height
                    )
                    Cocoa.NSRectFill(cursor_rect)
            
            def acceptsFirstResponder(self):
                """
                Indicate that this view can receive keyboard focus.
                
                This method must return True for the view to receive keyboard events.
                Without this, the view would not be able to handle keyboard input,
                which is essential for TTK applications.
                
                Returns:
                    bool: True to receive keyboard input
                """
                return True
else:
    # Provide a dummy class when PyObjC is not available
    class TTKView:
        """Dummy TTKView class when PyObjC is not available."""
        pass
