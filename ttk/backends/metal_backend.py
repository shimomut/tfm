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
        
        # Step 6: Create rendering pipeline
        self.render_pipeline = self._create_render_pipeline()
        
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
    
    def _create_render_pipeline(self):
        """
        Create Metal rendering pipeline with text shaders.
        
        This method loads and compiles the vertex and fragment shaders
        for text rendering, then creates a render pipeline state object
        that will be used for all rendering operations.
        
        The shaders handle:
        - Character positioning in the grid
        - Color application (foreground and background)
        - Text attributes (bold, underline, reverse)
        
        Returns:
            MTLRenderPipelineState: The compiled rendering pipeline
            
        Raises:
            RuntimeError: If shader compilation or pipeline creation fails
        """
        try:
            import Metal
        except ImportError:
            return None
        
        # Define shader source code
        shader_source = self._get_shader_source()
        
        # Create shader library from source
        try:
            # PyObjC returns (library, error) tuple when error parameter is provided
            result = self.metal_device.newLibraryWithSource_options_error_(
                shader_source, None, None
            )
            # Handle tuple return value (library, error)
            if isinstance(result, tuple):
                library, error = result
                if error is not None:
                    raise RuntimeError(f"Shader compilation error: {error}")
            else:
                library = result
            
            if library is None:
                raise RuntimeError("Failed to create shader library")
        except Exception as e:
            raise RuntimeError(f"Failed to compile shaders: {e}")
        
        # Get vertex and fragment functions
        vertex_function = library.newFunctionWithName_("vertex_main")
        fragment_function = library.newFunctionWithName_("fragment_main")
        
        if vertex_function is None or fragment_function is None:
            raise RuntimeError("Failed to load shader functions")
        
        # Create render pipeline descriptor
        pipeline_descriptor = Metal.MTLRenderPipelineDescriptor.alloc().init()
        pipeline_descriptor.setVertexFunction_(vertex_function)
        pipeline_descriptor.setFragmentFunction_(fragment_function)
        
        # Configure color attachment
        pipeline_descriptor.colorAttachments().objectAtIndexedSubscript_(0).setPixelFormat_(
            Metal.MTLPixelFormatBGRA8Unorm
        )
        
        # Enable blending for text rendering
        color_attachment = pipeline_descriptor.colorAttachments().objectAtIndexedSubscript_(0)
        color_attachment.setBlendingEnabled_(True)
        color_attachment.setRgbBlendOperation_(Metal.MTLBlendOperationAdd)
        color_attachment.setAlphaBlendOperation_(Metal.MTLBlendOperationAdd)
        color_attachment.setSourceRGBBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
        color_attachment.setSourceAlphaBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
        color_attachment.setDestinationRGBBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)
        color_attachment.setDestinationAlphaBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)
        
        # Create render pipeline state
        try:
            pipeline_state = self.metal_device.newRenderPipelineStateWithDescriptor_error_(
                pipeline_descriptor, None
            )
            if pipeline_state is None:
                raise RuntimeError("Failed to create render pipeline state")
            return pipeline_state
        except Exception as e:
            raise RuntimeError(f"Failed to create render pipeline: {e}")
    
    def _get_shader_source(self) -> str:
        """
        Get Metal shader source code for text rendering.
        
        Returns:
            str: Metal Shading Language (MSL) source code
        """
        return """
        #include <metal_stdlib>
        using namespace metal;
        
        // Vertex shader input structure
        struct VertexIn {
            float2 position [[attribute(0)]];
            float2 texCoord [[attribute(1)]];
            float4 color [[attribute(2)]];
        };
        
        // Vertex shader output / Fragment shader input
        struct VertexOut {
            float4 position [[position]];
            float2 texCoord;
            float4 color;
        };
        
        // Vertex shader
        vertex VertexOut vertex_main(VertexIn in [[stage_in]]) {
            VertexOut out;
            out.position = float4(in.position, 0.0, 1.0);
            out.texCoord = in.texCoord;
            out.color = in.color;
            return out;
        }
        
        // Fragment shader
        fragment float4 fragment_main(VertexOut in [[stage_in]],
                                     texture2d<float> texture [[texture(0)]],
                                     sampler textureSampler [[sampler(0)]]) {
            // Sample the texture (character glyph)
            float4 texColor = texture.sample(textureSampler, in.texCoord);
            
            // Apply color modulation
            // The texture alpha channel contains the glyph shape
            // The color contains the foreground color
            return float4(in.color.rgb, in.color.a * texColor.a);
        }
        """
    
    def _render_grid(self):
        """
        Render the entire character grid using Metal.
        
        This method creates a Metal command buffer and render pass,
        then renders each non-space character in the grid as a textured
        quad with the appropriate colors and attributes.
        
        The rendering process:
        1. Create command buffer from command queue
        2. Create render pass descriptor
        3. Begin render pass
        4. For each character in grid:
           - Skip spaces (optimization)
           - Render background quad if needed
           - Render character glyph with foreground color
        5. End render pass
        6. Present drawable
        7. Commit command buffer
        
        Note: This method is called by refresh() to update the display.
        
        WARNING: Metal rendering is not yet implemented. The window will show
        only the clear color (pink/magenta) without any text rendering.
        Use the curses backend for a fully functional demo.
        """
        try:
            import Metal
        except ImportError:
            return
        
        if self.metal_view is None or self.command_queue is None:
            return
        
        # Print warning on first render
        if not hasattr(self, '_render_warning_shown'):
            print("\nWARNING: Metal backend rendering is not yet implemented.")
            print("You will see only a colored background without any text.")
            print("Please use the curses backend instead: make demo-ttk BACKEND=curses")
            print("Or run: python -m ttk.demo.demo_ttk --backend curses\n")
            self._render_warning_shown = True
        
        # Get current drawable
        drawable = self.metal_view.currentDrawable()
        if drawable is None:
            return
        
        # Create command buffer
        command_buffer = self.command_queue.commandBuffer()
        if command_buffer is None:
            return
        
        # Create render pass descriptor
        render_pass_descriptor = self.metal_view.currentRenderPassDescriptor()
        if render_pass_descriptor is None:
            return
        
        # Create render command encoder
        render_encoder = command_buffer.renderCommandEncoderWithDescriptor_(
            render_pass_descriptor
        )
        if render_encoder is None:
            return
        
        # Set render pipeline state
        if self.render_pipeline is not None:
            render_encoder.setRenderPipelineState_(self.render_pipeline)
        
        # Render each character in the grid
        for row in range(self.rows):
            for col in range(self.cols):
                char, color_pair, attrs = self.grid[row][col]
                
                # Skip spaces for optimization (unless they have a background color)
                if char == ' ' and color_pair == 0:
                    continue
                
                # Render this character
                self._render_character(render_encoder, row, col, char, color_pair, attrs)
        
        # End encoding
        render_encoder.endEncoding()
        
        # Present drawable
        command_buffer.presentDrawable_(drawable)
        
        # Commit command buffer
        command_buffer.commit()
    
    def _render_grid_region(self, row: int, col: int, height: int, width: int):
        """
        Render a specific region of the character grid.
        
        This is an optimized version of _render_grid() that only renders
        characters within the specified rectangular region. This is useful
        for partial updates when only a small portion of the screen changes.
        
        Args:
            row: Starting row of the region (0-based)
            col: Starting column of the region (0-based)
            height: Height of the region in character rows
            width: Width of the region in character columns
            
        Note: This method is called by refresh_region() for optimized updates.
        """
        try:
            import Metal
        except ImportError:
            return
        
        if self.metal_view is None or self.command_queue is None:
            return
        
        # Get current drawable
        drawable = self.metal_view.currentDrawable()
        if drawable is None:
            return
        
        # Create command buffer
        command_buffer = self.command_queue.commandBuffer()
        if command_buffer is None:
            return
        
        # Create render pass descriptor
        render_pass_descriptor = self.metal_view.currentRenderPassDescriptor()
        if render_pass_descriptor is None:
            return
        
        # Create render command encoder
        render_encoder = command_buffer.renderCommandEncoderWithDescriptor_(
            render_pass_descriptor
        )
        if render_encoder is None:
            return
        
        # Set render pipeline state
        if self.render_pipeline is not None:
            render_encoder.setRenderPipelineState_(self.render_pipeline)
        
        # Calculate region bounds (clip to grid)
        start_row = max(0, row)
        end_row = min(self.rows, row + height)
        start_col = max(0, col)
        end_col = min(self.cols, col + width)
        
        # Render each character in the region
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                char, color_pair, attrs = self.grid[r][c]
                
                # Skip spaces for optimization (unless they have a background color)
                if char == ' ' and color_pair == 0:
                    continue
                
                # Render this character
                self._render_character(render_encoder, r, c, char, color_pair, attrs)
        
        # End encoding
        render_encoder.endEncoding()
        
        # Present drawable
        command_buffer.presentDrawable_(drawable)
        
        # Commit command buffer
        command_buffer.commit()
    
    def _render_character(self, render_encoder, row: int, col: int,
                         char: str, color_pair: int, attrs: int):
        """
        Render a single character at the specified grid position.
        
        This method renders one character by:
        1. Calculating screen position from grid coordinates
        2. Getting foreground and background colors from color pair
        3. Applying text attributes (bold, underline, reverse)
        4. Rendering background quad with background color
        5. Rendering character glyph with foreground color
        
        Args:
            render_encoder: Metal render command encoder
            row: Character row position in grid
            col: Character column position in grid
            char: Character to render
            color_pair: Color pair index
            attrs: Text attributes (bitwise OR of TextAttribute values)
            
        Note: This is a low-level rendering method called by _render_grid()
        and _render_grid_region(). It assumes the render encoder is already
        configured with the appropriate pipeline state.
        """
        # Calculate screen position in pixels
        x = col * self.char_width
        y = row * self.char_height
        
        # Get colors from color pair
        fg_color, bg_color = self.color_pairs.get(color_pair, ((255, 255, 255), (0, 0, 0)))
        
        # Apply reverse attribute (swap foreground and background)
        if attrs & TextAttribute.REVERSE:
            fg_color, bg_color = bg_color, fg_color
        
        # Convert RGB tuples to normalized float values (0.0-1.0)
        fg_r, fg_g, fg_b = [c / 255.0 for c in fg_color]
        bg_r, bg_g, bg_b = [c / 255.0 for c in bg_color]
        
        # TEMPORARY: Basic rendering using Core Graphics
        # This provides a visible fallback until full Metal rendering is implemented
        try:
            import Quartz
            
            # Get the current graphics context from the Metal view's layer
            if hasattr(self, 'graphics_context') and self.graphics_context:
                ctx = self.graphics_context
                
                # Draw background rectangle
                Quartz.CGContextSetRGBFillColor(ctx, bg_r, bg_g, bg_b, 1.0)
                Quartz.CGContextFillRect(ctx, Quartz.CGRectMake(x, y, self.char_width, self.char_height))
                
                # Draw character
                if char and char != ' ':
                    Quartz.CGContextSetRGBFillColor(ctx, fg_r, fg_g, fg_b, 1.0)
                    
                    # Set font attributes
                    font_size = self.font_size
                    if attrs & TextAttribute.BOLD:
                        font_size *= 1.1  # Slightly larger for bold
                    
                    # Draw the character (simplified - proper text rendering would use CTFont)
                    # This is a minimal implementation to show something on screen
                    pass
        except (ImportError, AttributeError, Exception) as e:
            # Silently fail if Core Graphics is not available or context is invalid
            # Full Metal implementation will replace this
            pass
    
    def shutdown(self) -> None:
        """
        Clean up Metal resources and close window.
        
        This method performs cleanup in the following order:
        1. Close the native window
        2. Clear Metal view reference
        3. Release the rendering pipeline
        4. Release the command queue
        5. Release the Metal device
        6. Clear the character grid buffer
        7. Clear color pair storage
        8. Reset cursor state
        
        This method handles cleanup gracefully even if some resources
        were not fully initialized. It's safe to call shutdown() multiple
        times or even if initialize() was never called.
        
        Example:
            backend = MetalBackend()
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
            self.window = None
        
        # Clear Metal view reference
        if hasattr(self, 'metal_view'):
            self.metal_view = None
        
        # Release rendering pipeline
        self.render_pipeline = None
        
        # Release command queue
        self.command_queue = None
        
        # Release Metal device
        self.metal_device = None
        
        # Clear character grid buffer
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
        self._render_grid()
    
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
        self._render_grid_region(row, col, height, width)
    
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
        # Validate pair_id
        if pair_id < 1 or pair_id > 255:
            raise ValueError(
                f"Color pair ID must be in range 1-255, got {pair_id}. "
                f"Pair ID 0 is reserved for default colors."
            )
        
        # Validate RGB values
        for color, name in [(fg_color, "foreground"), (bg_color, "background")]:
            if not isinstance(color, tuple) or len(color) != 3:
                raise ValueError(
                    f"{name.capitalize()} color must be a tuple of 3 integers (R, G, B), "
                    f"got {color}"
                )
            for component, component_name in zip(color, ['R', 'G', 'B']):
                if not isinstance(component, int) or component < 0 or component > 255:
                    raise ValueError(
                        f"{name.capitalize()} color {component_name} component must be "
                        f"an integer in range 0-255, got {component}"
                    )
        
        # Store color pair
        self.color_pairs[pair_id] = (fg_color, bg_color)
    
    def get_input(self, timeout_ms: int = -1) -> Optional[InputEvent]:
        """
        Get the next input event from the macOS event system.
        
        This method polls the macOS event queue for keyboard, mouse, and
        window events, then translates them into TTK's unified InputEvent
        format.
        
        Args:
            timeout_ms: Timeout in milliseconds.
                       -1: Block indefinitely until input is available
                        0: Non-blocking, return immediately if no input
                       >0: Wait up to timeout_ms milliseconds for input
        
        Returns:
            Optional[InputEvent]: An InputEvent object if input is available,
                                 or None if the timeout expires with no input.
                                 
        Note: This method processes the following event types:
        - Keyboard events (key down, key up)
        - Mouse events (mouse down, mouse up, mouse moved)
        - Window events (resize, focus change)
        
        Example:
            # Non-blocking check for input
            event = backend.get_input(timeout_ms=0)
            if event:
                print(f"Got key: {event.key_code}")
            
            # Blocking wait for input
            event = backend.get_input(timeout_ms=-1)
            print(f"User pressed: {event.char}")
        """
        # Poll macOS event queue
        macos_event = self._poll_macos_event(timeout_ms)
        
        if macos_event is None:
            return None
        
        # Translate macOS event to InputEvent
        return self._translate_macos_event(macos_event)
    
    def _translate_macos_event(self, event) -> Optional[InputEvent]:
        """
        Translate a macOS NSEvent to a TTK InputEvent.
        
        This method converts macOS-specific event objects into TTK's unified
        InputEvent format. It handles:
        - Keyboard events: Maps macOS key codes to TTK KeyCode values
        - Modifier keys: Extracts Shift, Control, Alt, Command states
        - Mouse events: Converts mouse position and button information
        - Window events: Handles resize and other window-related events
        
        Args:
            event: NSEvent object from macOS event system
        
        Returns:
            Optional[InputEvent]: Translated InputEvent, or None if the event
                                 type is not supported or cannot be translated.
                                 
        Note: This method uses the following mappings:
        - macOS key codes -> TTK KeyCode enum values
        - macOS modifier flags -> TTK ModifierKey flags
        - macOS mouse coordinates -> character grid coordinates
        """
        try:
            import Cocoa
            from ttk.input_event import KeyCode, ModifierKey, InputEvent
        except ImportError:
            return None
        
        if event is None:
            return None
        
        # Get event type
        event_type = event.type()
        
        # Handle keyboard events
        if event_type == Cocoa.NSEventTypeKeyDown:
            return self._translate_keyboard_event(event)
        
        # Handle mouse events
        elif event_type in (
            Cocoa.NSEventTypeLeftMouseDown,
            Cocoa.NSEventTypeLeftMouseUp,
            Cocoa.NSEventTypeRightMouseDown,
            Cocoa.NSEventTypeRightMouseUp,
            Cocoa.NSEventTypeOtherMouseDown,
            Cocoa.NSEventTypeOtherMouseUp,
            Cocoa.NSEventTypeMouseMoved,
            Cocoa.NSEventTypeLeftMouseDragged,
            Cocoa.NSEventTypeRightMouseDragged,
            Cocoa.NSEventTypeOtherMouseDragged
        ):
            return self._translate_mouse_event(event)
        
        # Handle window resize events
        # Note: macOS doesn't have a specific resize event type in the event queue
        # Instead, we need to check for window size changes periodically or use delegates
        # For now, we'll check window size on each event and detect changes
        
        # Check if window size has changed (simple resize detection)
        if self.window and self.metal_view:
            try:
                content_rect = self.window.contentView().frame()
                window_width = int(content_rect.size.width)
                window_height = int(content_rect.size.height)
                
                # Calculate what the grid dimensions should be
                expected_cols = max(1, window_width // self.char_width) if self.char_width > 0 else self.cols
                expected_rows = max(1, window_height // self.char_height) if self.char_height > 0 else self.rows
                
                # If dimensions don't match, we have a resize
                if expected_rows != self.rows or expected_cols != self.cols:
                    # Handle the resize
                    self._handle_window_resize()
                    
                    # Return a RESIZE event
                    return InputEvent(
                        key_code=KeyCode.RESIZE,
                        modifiers=ModifierKey.NONE,
                        char=None
                    )
            except Exception:
                pass  # Ignore errors during resize detection
        
        return None
    
    def _translate_keyboard_event(self, event) -> Optional[InputEvent]:
        """
        Translate a macOS keyboard event to InputEvent.
        
        Args:
            event: NSEvent keyboard event
            
        Returns:
            Optional[InputEvent]: Translated keyboard event
        """
        try:
            import Cocoa
            from ttk.input_event import KeyCode, ModifierKey, InputEvent
        except ImportError:
            return None
        
        # Get the key code
        key_code = event.keyCode()
        
        # Get modifier flags
        modifiers = self._extract_modifiers(event)
        
        # Get the character string
        chars = event.characters()
        char = chars[0] if chars and len(chars) > 0 else None
        
        # Map macOS key codes to TTK KeyCode values
        # macOS key codes are hardware-dependent, but these are common values
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
            # Get Unicode code point
            code_point = ord(char)
            
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
                return InputEvent(
                    key_code=code_point,
                    modifiers=modifiers,
                    char=char
                )
        
        # Unknown key - return None
        return None
    
    def _translate_mouse_event(self, event) -> Optional[InputEvent]:
        """
        Translate a macOS mouse event to InputEvent.
        
        Args:
            event: NSEvent mouse event
            
        Returns:
            Optional[InputEvent]: Translated mouse event
        """
        try:
            import Cocoa
            from ttk.input_event import KeyCode, ModifierKey, InputEvent
        except ImportError:
            return None
        
        # Get mouse location in window coordinates
        location = event.locationInWindow()
        
        # Convert pixel coordinates to character grid coordinates
        # Note: macOS uses bottom-left origin, we need top-left
        if self.window and self.metal_view:
            # Get window content height
            content_rect = self.window.contentView().frame()
            window_height = content_rect.size.height
            
            # Convert to top-left origin
            pixel_x = int(location.x)
            pixel_y = int(window_height - location.y)
            
            # Convert to character grid coordinates
            mouse_col = pixel_x // self.char_width if self.char_width > 0 else 0
            mouse_row = pixel_y // self.char_height if self.char_height > 0 else 0
            
            # Clamp to grid bounds
            mouse_col = max(0, min(mouse_col, self.cols - 1))
            mouse_row = max(0, min(mouse_row, self.rows - 1))
        else:
            mouse_col = 0
            mouse_row = 0
        
        # Determine mouse button
        event_type = event.type()
        if event_type in (Cocoa.NSEventTypeLeftMouseDown, Cocoa.NSEventTypeLeftMouseUp, Cocoa.NSEventTypeLeftMouseDragged):
            mouse_button = 1  # Left button
        elif event_type in (Cocoa.NSEventTypeRightMouseDown, Cocoa.NSEventTypeRightMouseUp, Cocoa.NSEventTypeRightMouseDragged):
            mouse_button = 3  # Right button
        elif event_type in (Cocoa.NSEventTypeOtherMouseDown, Cocoa.NSEventTypeOtherMouseUp, Cocoa.NSEventTypeOtherMouseDragged):
            mouse_button = 2  # Middle button
        else:
            mouse_button = None  # Mouse moved without button
        
        # Get modifier flags
        modifiers = self._extract_modifiers(event)
        
        # Create mouse input event
        return InputEvent(
            key_code=KeyCode.MOUSE,
            modifiers=modifiers,
            char=None,
            mouse_row=mouse_row,
            mouse_col=mouse_col,
            mouse_button=mouse_button
        )
    
    def _handle_window_resize(self) -> None:
        """
        Handle window resize events.
        
        This method is called when the window is resized. It:
        1. Recalculates the character grid dimensions based on new window size
        2. Preserves existing grid content where possible
        3. Fills new areas with spaces
        4. Clamps cursor position to new grid bounds
        
        Note: This method is called automatically when a resize event is detected
        in the event polling loop.
        """
        if self.window is None or self.metal_view is None:
            return
        
        # Get new window content size
        # Note: We don't need to import Cocoa here since we're just calling methods
        # on the window object that was already created
        try:
            content_rect = self.window.contentView().frame()
            window_width = int(content_rect.size.width)
            window_height = int(content_rect.size.height)
        except Exception:
            # If we can't get window size, return without resizing
            return
        
        # Calculate new grid dimensions
        new_cols = max(1, window_width // self.char_width) if self.char_width > 0 else 80
        new_rows = max(1, window_height // self.char_height) if self.char_height > 0 else 40
        
        # Check if dimensions actually changed
        if new_rows == self.rows and new_cols == self.cols:
            return
        
        # Create new grid with new dimensions
        new_grid = [
            [(' ', 0, 0) for _ in range(new_cols)]
            for _ in range(new_rows)
        ]
        
        # Copy existing content to new grid (preserve what fits)
        for row in range(min(self.rows, new_rows)):
            for col in range(min(self.cols, new_cols)):
                new_grid[row][col] = self.grid[row][col]
        
        # Update grid and dimensions
        self.grid = new_grid
        self.rows = new_rows
        self.cols = new_cols
        
        # Clamp cursor position to new bounds
        if self.cursor_row >= self.rows:
            self.cursor_row = max(0, self.rows - 1)
        if self.cursor_col >= self.cols:
            self.cursor_col = max(0, self.cols - 1)
    
    def _extract_modifiers(self, event) -> int:
        """
        Extract modifier key flags from a macOS event.
        
        Args:
            event: NSEvent object
            
        Returns:
            int: Bitwise OR of ModifierKey flags
        """
        try:
            import Cocoa
            from ttk.input_event import ModifierKey
        except ImportError:
            return ModifierKey.NONE
        
        modifiers = ModifierKey.NONE
        modifier_flags = event.modifierFlags()
        
        # Check for Shift
        if modifier_flags & Cocoa.NSEventModifierFlagShift:
            modifiers |= ModifierKey.SHIFT
        
        # Check for Control
        if modifier_flags & Cocoa.NSEventModifierFlagControl:
            modifiers |= ModifierKey.CONTROL
        
        # Check for Alt/Option
        if modifier_flags & Cocoa.NSEventModifierFlagOption:
            modifiers |= ModifierKey.ALT
        
        # Check for Command
        if modifier_flags & Cocoa.NSEventModifierFlagCommand:
            modifiers |= ModifierKey.COMMAND
        
        return modifiers
    
    def _poll_macos_event(self, timeout_ms: int):
        """
        Poll the macOS event queue for the next event.
        
        This method uses NSApp (the application object) to poll for events
        from the macOS event system. It handles different timeout modes:
        - Blocking: Wait indefinitely for an event
        - Non-blocking: Return immediately if no event is available
        - Timed: Wait up to the specified timeout for an event
        
        Args:
            timeout_ms: Timeout in milliseconds.
                       -1: Block indefinitely
                        0: Non-blocking
                       >0: Wait up to timeout_ms milliseconds
        
        Returns:
            NSEvent object if an event is available, None otherwise.
            
        Note: This method processes events from the application's event queue,
        which includes keyboard events, mouse events, and window events.
        """
        try:
            import Cocoa
            import Foundation
        except ImportError:
            return None
        
        # Get the shared application instance
        app = Cocoa.NSApplication.sharedApplication()
        
        # Calculate timeout date based on timeout_ms
        if timeout_ms < 0:
            # Blocking mode - use distant future
            until_date = Foundation.NSDate.distantFuture()
        elif timeout_ms == 0:
            # Non-blocking mode - use distant past (return immediately)
            until_date = Foundation.NSDate.distantPast()
        else:
            # Timed mode - calculate date from now + timeout
            timeout_seconds = timeout_ms / 1000.0
            until_date = Foundation.NSDate.dateWithTimeIntervalSinceNow_(timeout_seconds)
        
        # Define event mask for events we're interested in
        # This includes keyboard, mouse, and window events
        event_mask = (
            Cocoa.NSEventMaskKeyDown |
            Cocoa.NSEventMaskKeyUp |
            Cocoa.NSEventMaskFlagsChanged |
            Cocoa.NSEventMaskLeftMouseDown |
            Cocoa.NSEventMaskLeftMouseUp |
            Cocoa.NSEventMaskRightMouseDown |
            Cocoa.NSEventMaskRightMouseUp |
            Cocoa.NSEventMaskOtherMouseDown |
            Cocoa.NSEventMaskOtherMouseUp |
            Cocoa.NSEventMaskMouseMoved |
            Cocoa.NSEventMaskLeftMouseDragged |
            Cocoa.NSEventMaskRightMouseDragged |
            Cocoa.NSEventMaskOtherMouseDragged |
            Cocoa.NSEventMaskScrollWheel
        )
        
        # Poll for next event
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            event_mask,
            until_date,
            Cocoa.NSDefaultRunLoopMode,
            True  # dequeue the event
        )
        
        return event
    
    def set_cursor_visibility(self, visible: bool) -> None:
        """
        Set cursor visibility.
        
        Args:
            visible: True to show the cursor, False to hide it.
            
        Note: The cursor is rendered as part of the character grid during
        refresh operations. This method updates the cursor visibility state,
        and the cursor will be shown or hidden on the next refresh.
        
        Example:
            backend.set_cursor_visibility(True)   # Show cursor
            backend.move_cursor(10, 20)           # Position cursor
            backend.refresh()                      # Cursor now visible at (10, 20)
        """
        self.cursor_visible = visible
    
    def move_cursor(self, row: int, col: int) -> None:
        """
        Move the cursor to the specified position.
        
        Args:
            row: Row position (0-based, 0 is top)
            col: Column position (0-based, 0 is left)
            
        Note: The cursor position is stored and will be rendered during
        the next refresh operation if cursor visibility is enabled.
        The cursor is clamped to valid grid coordinates.
        
        Example:
            backend.move_cursor(5, 10)    # Move cursor to row 5, column 10
            backend.set_cursor_visibility(True)
            backend.refresh()              # Cursor now visible at new position
        """
        # Clamp cursor position to valid grid coordinates
        self.cursor_row = max(0, min(row, self.rows - 1)) if self.rows > 0 else 0
        self.cursor_col = max(0, min(col, self.cols - 1)) if self.cols > 0 else 0
