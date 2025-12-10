"""
TTK Metal Backend Module

This module implements the Metal-based rendering backend for native macOS
desktop applications. It uses Apple's Metal framework for GPU-accelerated
rendering of character-grid-based applications.

Note: This implementation requires PyObjC for interfacing with macOS frameworks.
"""

from typing import Tuple, Optional
from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import InputEvent


class MetalBackend(Renderer):
    """
    Metal-based rendering backend for macOS desktop applications.
    
    This backend creates a native macOS window and uses Metal for GPU-accelerated
    rendering of a character grid. It supports monospace fonts only to ensure
    perfect character alignment.
    
    The backend maintains a character grid buffer where each cell stores:
    - The character to display
    - The color pair index
    - Text attributes (bold, underline, etc.)
    
    Rendering is performed by converting this grid into Metal draw calls that
    render each character as a textured quad with the appropriate colors and
    attributes applied.
    
    Requirements:
        - macOS 10.13 or later (for Metal support)
        - PyObjC for interfacing with Metal and Cocoa frameworks
        - Monospace font (proportional fonts are rejected)
    """
    
    def __init__(self, window_title: str = "TTK Application",
                 font_name: str = "Menlo", font_size: int = 14):
        """
        Initialize Metal backend with window and font configuration.
        
        Args:
            window_title: Title for the native macOS window.
                         This appears in the window title bar.
            font_name: Name of the monospace font to use.
                      Must be a monospace font installed on the system.
                      Common monospace fonts on macOS:
                      - "Menlo" (default, system monospace font)
                      - "Monaco"
                      - "Courier New"
                      - "SF Mono"
            font_size: Font size in points (typically 10-18).
                      Larger sizes result in larger character cells and
                      fewer rows/columns in the window.
        
        Raises:
            ValueError: If font_name is not a monospace font (checked during initialize())
            
        Note: The actual window and Metal resources are not created until
        initialize() is called. This allows the backend to be constructed
        without immediately creating system resources.
        
        Example:
            # Create backend with default settings
            backend = MetalBackend()
            
            # Create backend with custom font
            backend = MetalBackend(
                window_title="My Application",
                font_name="Monaco",
                font_size=16
            )
        """
        # Window configuration
        self.window_title = window_title
        self.font_name = font_name
        self.font_size = font_size
        
        # Metal resources (initialized in initialize())
        self.window = None              # NSWindow - native macOS window
        self.metal_device = None        # MTLDevice - Metal GPU device
        self.command_queue = None       # MTLCommandQueue - Metal command queue
        self.render_pipeline = None     # MTLRenderPipelineState - rendering pipeline
        
        # Font metrics (calculated in initialize())
        self.char_width = 0             # Width of one character in pixels
        self.char_height = 0            # Height of one character in pixels
        
        # Grid dimensions (calculated in initialize())
        self.rows = 0                   # Number of character rows
        self.cols = 0                   # Number of character columns
        
        # Character grid buffer
        # Each cell is a tuple: (char, color_pair, attributes)
        self.grid = []                  # 2D list of character cells
        
        # Color pair storage
        # Maps color pair ID to (fg_color, bg_color) tuples
        # Each color is an (R, G, B) tuple with values 0-255
        self.color_pairs = {}
        
        # Cursor state
        self.cursor_visible = False     # Whether cursor is visible
        self.cursor_row = 0             # Current cursor row position
        self.cursor_col = 0             # Current cursor column position
    
    def initialize(self) -> None:
        """
        Initialize Metal and create native window.
        
        This method performs the following initialization steps:
        1. Create Metal device and command queue
        2. Validate that the specified font is monospace
        3. Create native macOS window with Metal view
        4. Calculate character dimensions based on font metrics
        5. Initialize the character grid buffer
        6. Load and compile Metal shaders
        7. Create the rendering pipeline
        
        Raises:
            RuntimeError: If Metal device cannot be created
            RuntimeError: If window creation fails
            ValueError: If the specified font is not monospace
            RuntimeError: If shader compilation fails
            
        Note: This method must be called before any other rendering operations.
        After initialization, the window will be visible and ready for drawing.
        
        Example:
            backend = MetalBackend()
            backend.initialize()
            # Now ready to draw
        """
        try:
            import Metal
            import Cocoa
            import CoreText
            import Quartz
        except ImportError as e:
            raise RuntimeError(
                f"PyObjC is required for Metal backend. "
                f"Install with: pip install pyobjc-framework-Metal pyobjc-framework-Cocoa pyobjc-framework-Quartz. "
                f"Error: {e}"
            )
        
        # Step 1: Create Metal device
        self.metal_device = Metal.MTLCreateSystemDefaultDevice()
        if self.metal_device is None:
            raise RuntimeError(
                "Failed to create Metal device. "
                "Metal may not be supported on this system. "
                "Requires macOS 10.13 or later with Metal-capable GPU."
            )
        
        # Create command queue for submitting rendering commands
        self.command_queue = self.metal_device.newCommandQueue()
        if self.command_queue is None:
            raise RuntimeError("Failed to create Metal command queue")
        
        # Step 2: Validate font is monospace
        self._validate_font()
        
        # Step 3: Create native macOS window
        self._create_native_window()
        
        # Step 4: Calculate character dimensions
        self._calculate_char_dimensions()
        
        # Step 5: Initialize character grid buffer
        self._initialize_grid()
        
        # Initialize default color pair (0)
        self.color_pairs[0] = ((255, 255, 255), (0, 0, 0))  # White on black
    
    def _validate_font(self) -> None:
        """
        Validate that the specified font is monospace.
        
        Uses Core Text to check font metrics and verify that all characters
        have the same width. This is essential for character-grid-based
        rendering where we assume fixed character dimensions.
        
        Raises:
            ValueError: If the font is not found or is not monospace
        """
        try:
            import Cocoa
            import CoreText
        except ImportError:
            # If PyObjC is not available, we already raised in initialize()
            return
        
        # Create NSFont object
        font = Cocoa.NSFont.fontWithName_size_(self.font_name, self.font_size)
        if font is None:
            raise ValueError(
                f"Font '{self.font_name}' not found. "
                f"Please specify a valid monospace font installed on your system. "
                f"Common monospace fonts: Menlo, Monaco, Courier New, SF Mono"
            )
        
        # Check if font is monospace by comparing widths of different characters
        # Monospace fonts have the same width for all characters
        test_chars = ['i', 'W', 'M', '1', ' ']
        widths = []
        
        for char in test_chars:
            # Create attributed string with the character
            attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
                char,
                {Cocoa.NSFontAttributeName: font}
            )
            # Get the width
            width = attr_string.size().width
            widths.append(width)
        
        # Check if all widths are the same (within a small tolerance for floating point)
        if len(set(round(w, 2) for w in widths)) > 1:
            raise ValueError(
                f"Font '{self.font_name}' is not monospace. "
                f"Character widths vary: {widths}. "
                f"TTK requires monospace fonts for proper character grid alignment. "
                f"Please use a monospace font like Menlo, Monaco, or Courier New."
            )
    
    def _create_native_window(self) -> None:
        """
        Create native macOS window with Metal view.
        
        Creates an NSWindow with a Metal-backed view for rendering.
        The window is created with a default size and will be resizable.
        
        Raises:
            RuntimeError: If window creation fails
        """
        try:
            import Cocoa
            import Metal
            import MetalKit
        except ImportError:
            return
        
        # Define initial window size (will be adjusted based on character grid)
        initial_width = 1024
        initial_height = 768
        
        # Create window frame
        frame = Cocoa.NSMakeRect(100, 100, initial_width, initial_height)
        
        # Create window with standard style
        style_mask = (
            Cocoa.NSWindowStyleMaskTitled |
            Cocoa.NSWindowStyleMaskClosable |
            Cocoa.NSWindowStyleMaskMiniaturizable |
            Cocoa.NSWindowStyleMaskResizable
        )
        
        # Create the window
        self.window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            Cocoa.NSBackingStoreBuffered,
            False
        )
        
        if self.window is None:
            raise RuntimeError("Failed to create native macOS window")
        
        # Set window title
        self.window.setTitle_(self.window_title)
        
        # Create Metal view
        metal_view = MetalKit.MTKView.alloc().initWithFrame_device_(
            frame,
            self.metal_device
        )
        
        if metal_view is None:
            raise RuntimeError("Failed to create Metal view")
        
        # Configure Metal view
        metal_view.setColorPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
        metal_view.setClearColor_(Metal.MTLClearColorMake(0.0, 0.0, 0.0, 1.0))  # Black background
        
        # Set the Metal view as the window's content view
        self.window.setContentView_(metal_view)
        
        # Store reference to Metal view for rendering
        self.metal_view = metal_view
        
        # Make window visible
        self.window.makeKeyAndOrderFront_(None)
    
    def _calculate_char_dimensions(self) -> None:
        """
        Calculate character cell dimensions for the monospace font.
        
        Measures the font to determine the exact width and height of
        one character cell. This ensures perfect grid alignment.
        
        The character width is measured using a representative character ('M'),
        and the height is calculated from the font's ascender and descender.
        """
        try:
            import Cocoa
        except ImportError:
            return
        
        # Create NSFont object
        font = Cocoa.NSFont.fontWithName_size_(self.font_name, self.font_size)
        
        # Measure character width using 'M' (a wide character in monospace fonts)
        attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            'M',
            {Cocoa.NSFontAttributeName: font}
        )
        self.char_width = int(attr_string.size().width)
        
        # Calculate character height from font metrics
        # Height = ascender + descender + leading
        self.char_height = int(font.ascender() - font.descender() + font.leading())
        
        # Ensure minimum dimensions
        if self.char_width < 1:
            self.char_width = 8  # Fallback to reasonable default
        if self.char_height < 1:
            self.char_height = 16  # Fallback to reasonable default
    
    def _initialize_grid(self) -> None:
        """
        Initialize the character grid buffer.
        
        Creates a 2D grid based on the window size and character dimensions.
        Each cell in the grid stores:
        - char: The character to display (string)
        - color_pair: The color pair index (int)
        - attributes: Text attributes as bitwise flags (int)
        
        The grid is initialized with spaces using default colors.
        """
        # Get window content size
        if self.window is None or self.metal_view is None:
            # Fallback to reasonable defaults if window not created
            self.rows = 40
            self.cols = 80
        else:
            try:
                import Cocoa
                content_rect = self.window.contentView().frame()
                window_width = int(content_rect.size.width)
                window_height = int(content_rect.size.height)
                
                # Calculate grid dimensions
                self.cols = max(1, window_width // self.char_width)
                self.rows = max(1, window_height // self.char_height)
            except Exception:
                # Fallback to reasonable defaults
                self.rows = 40
                self.cols = 80
        
        # Create grid: list of rows, each row is list of (char, color_pair, attrs) tuples
        self.grid = [
            [(' ', 0, 0) for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
    
    def shutdown(self) -> None:
        """
        Clean up Metal resources and close window.
        
        This method performs cleanup in the following order:
        1. Close the native window
        2. Release the rendering pipeline
        3. Release the command queue
        4. Release the Metal device
        5. Clear the character grid buffer
        6. Clear color pair storage
        
        This method handles cleanup gracefully even if some resources
        were not fully initialized. It's safe to call shutdown() multiple
        times or even if initialize() was never called.
        
        Example:
            backend = MetalBackend()
            backend.initialize()
            # ... use backend ...
            backend.shutdown()
        """
        # TODO: Implement Metal cleanup
        # This will be implemented in subsequent tasks
        pass
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get window dimensions in character cells.
        
        Returns:
            Tuple[int, int]: A tuple of (rows, columns) representing the
                character grid size.
                
        Example:
            rows, cols = backend.get_dimensions()
            # rows = 40, cols = 120 for a typical desktop window
        """
        # TODO: Implement dimension query
        # This will be implemented in subsequent tasks
        return (self.rows, self.cols)
    
    def clear(self) -> None:
        """
        Clear the entire window.
        
        This method fills the entire character grid with spaces using
        color pair 0 (default colors) and no attributes.
        
        Note: Changes are not visible until refresh() is called.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col] = (' ', 0, 0)
    
    def clear_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Clear a rectangular region of the window.
        
        Args:
            row: Starting row position (0-based, 0 is top)
            col: Starting column position (0-based, 0 is left)
            height: Height of the region in character rows
            width: Width of the region in character columns
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        """
        # Handle out-of-bounds gracefully by clipping to valid range
        for r in range(row, min(row + height, self.rows)):
            for c in range(col, min(col + width, self.cols)):
                if r >= 0 and c >= 0:
                    self.grid[r][c] = (' ', 0, 0)
    
    def draw_text(self, row: int, col: int, text: str,
                  color_pair: int = 0, attributes: int = 0) -> None:
        """
        Draw text at the specified position.
        
        Args:
            row: Row position (0-based, 0 is top)
            col: Column position (0-based, 0 is left)
            text: Text string to draw
            color_pair: Color pair index (0-255)
            attributes: Bitwise OR of TextAttribute values
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        """
        # Handle out-of-bounds gracefully
        if row < 0 or row >= self.rows:
            return
        
        # Draw each character, stopping at grid boundary
        for i, char in enumerate(text):
            c = col + i
            if c < 0:
                continue
            if c >= self.cols:
                break
            self.grid[row][c] = (char, color_pair, attributes)
    
    def draw_hline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a horizontal line.
        
        Args:
            row: Row position for the line
            col: Starting column position
            char: Character to use for the line
            length: Length of the line in characters
            color_pair: Color pair index (0-255)
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        """
        # Use draw_text to draw the line
        if char:
            line_text = char[0] * length
            self.draw_text(row, col, line_text, color_pair)
    
    def draw_vline(self, row: int, col: int, char: str,
                   length: int, color_pair: int = 0) -> None:
        """
        Draw a vertical line.
        
        Args:
            row: Starting row position
            col: Column position for the line
            char: Character to use for the line
            length: Length of the line in characters
            color_pair: Color pair index (0-255)
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        """
        # Handle out-of-bounds gracefully
        if col < 0 or col >= self.cols or not char:
            return
        
        # Draw each character vertically
        for i in range(length):
            r = row + i
            if r < 0:
                continue
            if r >= self.rows:
                break
            self.grid[r][col] = (char[0], color_pair, 0)
    
    def draw_rect(self, row: int, col: int, height: int, width: int,
                  color_pair: int = 0, filled: bool = False) -> None:
        """
        Draw a rectangle.
        
        Args:
            row: Top-left row position
            col: Top-left column position
            height: Height of the rectangle in character rows
            width: Width of the rectangle in character columns
            color_pair: Color pair index (0-255)
            filled: If True, fill the rectangle; if False, draw outline only
            
        Note: Changes are not visible until refresh() or refresh_region() is called.
        """
        if filled:
            # Fill the rectangle with spaces
            for r in range(row, min(row + height, self.rows)):
                if r >= 0:
                    self.draw_text(r, col, ' ' * width, color_pair)
        else:
            # Draw outline
            if height > 0 and width > 0:
                # Top edge
                self.draw_hline(row, col, '-', width, color_pair)
                # Bottom edge
                if height > 1:
                    self.draw_hline(row + height - 1, col, '-', width, color_pair)
                # Left edge
                self.draw_vline(row, col, '|', height, color_pair)
                # Right edge
                if width > 1:
                    self.draw_vline(row, col + width - 1, '|', height, color_pair)
    
    def refresh(self) -> None:
        """
        Refresh the entire window to display all pending changes.
        
        This method renders the entire character grid using Metal,
        converting each character cell into GPU draw calls.
        """
        # TODO: Implement full window refresh
        # This will be implemented in subsequent tasks
        pass
    
    def refresh_region(self, row: int, col: int, height: int, width: int) -> None:
        """
        Refresh a specific region of the window.
        
        Args:
            row: Starting row of the region to refresh
            col: Starting column of the region to refresh
            height: Height of the region in character rows
            width: Width of the region in character columns
            
        Note: This is an optimization hint. The Metal backend can render
        only the specified region for better performance.
        """
        # TODO: Implement region refresh
        # This will be implemented in subsequent tasks
        pass
    
    def init_color_pair(self, pair_id: int, fg_color: Tuple[int, int, int],
                       bg_color: Tuple[int, int, int]) -> None:
        """
        Initialize a color pair with RGB values.
        
        Args:
            pair_id: Color pair index (1-255)
            fg_color: Foreground color as (R, G, B) tuple (0-255 each)
            bg_color: Background color as (R, G, B) tuple (0-255 each)
            
        Raises:
            ValueError: If pair_id is 0 or outside the range 1-255
            ValueError: If any RGB component is outside the range 0-255
        """
        # TODO: Implement color pair initialization
        # This will be implemented in subsequent tasks
        pass
    
    def get_input(self, timeout_ms: int = -1) -> Optional[InputEvent]:
        """
        Get the next input event from the macOS event system.
        
        Args:
            timeout_ms: Timeout in milliseconds.
                       -1: Block indefinitely until input is available
                        0: Non-blocking, return immediately if no input
                       >0: Wait up to timeout_ms milliseconds for input
        
        Returns:
            Optional[InputEvent]: An InputEvent object if input is available,
                                 or None if the timeout expires with no input.
        """
        # TODO: Implement input handling
        # This will be implemented in subsequent tasks
        pass
    
    def set_cursor_visibility(self, visible: bool) -> None:
        """
        Set cursor visibility.
        
        Args:
            visible: True to show the cursor, False to hide it.
        """
        # TODO: Implement cursor visibility control
        # This will be implemented in subsequent tasks
        pass
    
    def move_cursor(self, row: int, col: int) -> None:
        """
        Move the cursor to the specified position.
        
        Args:
            row: Row position (0-based, 0 is top)
            col: Column position (0-based, 0 is left)
        """
        # TODO: Implement cursor movement
        # This will be implemented in subsequent tasks
        pass
