"""
TTK CoreGraphics Backend

This module implements a macOS CoreGraphics (Quartz 2D) rendering backend for TTK.
It enables TTK applications to run as native macOS desktop applications with
high-quality text rendering while maintaining full compatibility with the abstract
Renderer API.

The CoreGraphics backend uses Apple's Cocoa and CoreGraphics frameworks through
PyObjC to provide native macOS text rendering quality with minimal code complexity.

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
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Set up event callback
    class MyEventCallback:
        def on_key_event(self, event):
            print(f"Key pressed: {event.char}")
            return True
        
        def on_char_event(self, event):
            return True
        
        def on_system_event(self, event):
            pass
        
        def should_close(self):
            return False
    
    callback = MyEventCallback()
    backend.set_event_callback(callback)
    
    # Initialize a color pair (white on blue)
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))
    
    # Draw some text
    backend.draw_text(0, 0, "Hello, World!", color_pair=1)
    backend.refresh()
    
    # Run event loop
    backend.run_event_loop()
    
    # Clean up
    backend.shutdown()
"""

import os
import time
import unicodedata
import warnings
from functools import lru_cache

# Check PyObjC availability
try:
    import Cocoa
    import Quartz
    import objc
    from CoreText import (
        CTLineCreateWithAttributedString,
        CTLineDraw,
        kCTFontAttributeName,
        kCTForegroundColorAttributeName,
        kCTUnderlineStyleAttributeName,
        kCTUnderlineStyleSingle
    )
    COCOA_AVAILABLE = True
    
    # Suppress PyObjC pointer warnings
    # These warnings are informational and occur during normal NSTextInputClient
    # protocol implementation when handling output parameters (like actual_range).
    # The pointer creation is correct and expected behavior.
    try:
        if hasattr(objc, 'ObjCPointerWarning') and isinstance(objc.ObjCPointerWarning, type):
            warnings.filterwarnings('ignore', category=objc.ObjCPointerWarning)
    except (AttributeError, TypeError):
        pass  # ObjCPointerWarning not available or not a proper warning class
except ImportError:
    COCOA_AVAILABLE = False

# Import TTK base classes
from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import Event, KeyEvent, SystemEvent, KeyCode, SystemEventType, ModifierKey
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass


@lru_cache(maxsize=1024)
def _is_wide_character(char: str) -> bool:
    """
    Check if a character is a wide (double-width) character.
    
    Wide characters (zenkaku) take up 2 display columns in terminal output,
    including most East Asian characters (Chinese, Japanese, Korean).
    
    Args:
        char: A single Unicode character
        
    Returns:
        True if the character is wide (double-width), False otherwise
    """
    if len(char) != 1:
        return False
    
    # Fast path for ASCII characters (most common case)
    if ord(char) < 128:
        return False
    
    try:
        # Use East Asian Width property from Unicode database
        width = unicodedata.east_asian_width(char)
        # 'F' = Fullwidth, 'W' = Wide
        return width in ('F', 'W')
    except (UnicodeError, ValueError):
        return False


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
    
    # Window padding multiplier: adds (WINDOW_PADDING_MULTIPLIER * char_height) to window dimensions
    # This creates a pleasant frame around the text grid that edge cells will fill
    WINDOW_PADDING_MULTIPLIER = 0.4
    
    
    def __init__(self, window_title: str = "TTK Application",
                 font_size: int = 12,
                 rows: int = 24, cols: int = 80,
                 frame_autosave_name: Optional[str] = None,
                 font_names: Optional[list] = None,
                 enable_perf_logging: bool = False):
        """
        Initialize the CoreGraphics backend.
        
        Args:
            window_title: Title for the window
            font_size: Font size in points (default: 12)
            rows: Initial grid height in characters (default: 24)
            cols: Initial grid width in characters (default: 80)
            frame_autosave_name: Optional name for NSWindow frame autosave.
                               If provided, enables automatic window geometry persistence.
                               If None, defaults to "TTKApplication".
            font_names: List of font names for cascade fallback (default: ['Menlo']).
                       First font is primary, remaining fonts are cascade fonts.
                       Used by C++ renderer for automatic character fallback.
            enable_perf_logging: Enable C++ renderer performance logging to stderr.
                                When enabled, logs metrics every 60 frames including
                                render time, batching stats, and font cache hit rate.
        
        Raises:
            RuntimeError: If PyObjC is not installed
        """
        if not COCOA_AVAILABLE:
            raise RuntimeError(
                "PyObjC is required for CoreGraphics backend. "
                "Install with: pip install pyobjc-framework-Cocoa"
            )
        
        self.window_title = window_title
        self.font_names = font_names if font_names is not None else ['Menlo']
        self.enable_perf_logging = enable_perf_logging
        
        # Set font size first (needed by monospace fallback)
        self.font_size = font_size
        
        # Automatically add system default monospace font as final fallback
        # This ensures there's always a font available for any character
        self._add_system_monospace_fallback()
        
        # Automatically add system emoji font BEFORE Apple Symbols
        # This ensures emoji characters use color emoji, not grayscale symbols
        # Apple Symbols has grayscale versions of some emoji, so we need to
        # check Apple Color Emoji first
        self._add_system_emoji_fallback()
        
        # Automatically add Apple Symbols font for special Unicode characters
        # This provides coverage for Braille, mathematical symbols, etc.
        # Placed after emoji font to avoid grayscale emoji rendering
        self._add_system_symbols_fallback()
        
        self.rows = rows
        self.cols = cols
        
        # Store frame autosave name (use default if not provided)
        self.frame_autosave_name = frame_autosave_name or "TTKApplication"
        
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
        self.resize_pending = False
        
        # Event callback for callback-based event delivery
        self.event_callback: Optional['EventCallback'] = None
        
        # C++ renderer module (initialized in initialize())
        self._cpp_renderer = None
    
    def _add_system_monospace_fallback(self) -> None:
        """
        Add system default monospace font as final fallback in cascade list.
        
        This ensures there's always a font available for any character, even if
        all user-specified fonts don't have the required glyphs.
        
        The system monospace font is only added if it's not already in the list.
        """
        try:
            # Get system monospace font
            system_font = Cocoa.NSFont.monospacedSystemFontOfSize_weight_(self.font_size, 0.0)
            if system_font:
                system_font_name = system_font.fontName()
                
                # Only add if not already in the list
                if system_font_name not in self.font_names:
                    self.font_names.append(system_font_name)
        except Exception as e:
            # If we can't get system font, just continue with user-specified fonts
            # This is non-critical - user fonts should work for most cases
            print(f"Warning: Could not add system monospace font to cascade: {e}")
    
    def _add_system_emoji_fallback(self) -> None:
        """
        Add system emoji font as final fallback in cascade list.
        
        This ensures emoji characters can be rendered even if user-specified
        fonts don't include emoji glyphs. On macOS, this is "Apple Color Emoji".
        
        The emoji font is only added if it's not already in the list.
        """
        try:
            # macOS system emoji font name
            emoji_font_name = "Apple Color Emoji"
            
            # Only add if not already in the list
            if emoji_font_name not in self.font_names:
                self.font_names.append(emoji_font_name)
        except Exception as e:
            print(f"Warning: Could not add system emoji font to cascade: {e}")
    
    def _add_system_symbols_fallback(self) -> None:
        """
        Add Apple Symbols font as fallback in cascade list.
        
        This ensures special Unicode characters (like Braille, mathematical symbols,
        etc.) can be rendered. Apple Symbols has broad Unicode coverage including
        characters not typically found in monospace fonts.
        
        The symbols font is only added if it's not already in the list.
        """
        try:
            # macOS system symbols font name
            symbols_font_name = "Apple Symbols"
            
            # Only add if not already in the list
            if symbols_font_name not in self.font_names:
                self.font_names.append(symbols_font_name)
        except Exception as e:
            print(f"Warning: Could not add system symbols font to cascade: {e}")
    
    def initialize(self) -> None:
        """
        Initialize the rendering backend and create the window.
        
        This method:
        1. Sets up the NSApplication as a proper GUI application
        2. Loads and validates the monospace font
        3. Calculates character dimensions
        4. Initializes performance optimization caches
        5. Creates the window and view
        6. Initializes the character grid
        7. Sets up default color pairs
        8. Imports C++ renderer module
        
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
        
        # Import C++ renderer module
        try:
            import ttk_coregraphics_render
            self._cpp_renderer = ttk_coregraphics_render
            print("CoreGraphicsBackend: Using C++ rendering implementation")
            
            # Enable performance logging if requested
            if self.enable_perf_logging:
                self._cpp_renderer.enable_perf_logging(True)
                print("CoreGraphicsBackend: C++ performance logging enabled")
        except ImportError as e:
            print(f"CoreGraphicsBackend: C++ renderer module not available: {e}")
            print("CoreGraphicsBackend: Falling back to PyObjC rendering")
            self.USE_CPP_RENDERING = False
        
        # Create window and view
        self._create_window()
        
        # Initialize character grid
        self._initialize_grid()
        
        # Initialize default color pair (0: white on black)
        self.color_pairs[0] = ((255, 255, 255), (0, 0, 0))
    
    def _load_font(self) -> None:
        """
        Load the monospace font.
        
        Uses the first font from font_names list as the primary font.
        
        Raises:
            ValueError: If the font is not found
        """
        font_name = self.font_names[0]
        self.font = Cocoa.NSFont.fontWithName_size_(font_name, self.font_size)
        if not self.font:
            raise ValueError(
                f"Font '{font_name}' not found. "
                f"Use a valid monospace font like 'Menlo', 'Monaco', or 'Courier'."
            )
    
    def _calculate_char_dimensions(self) -> None:
        """
        Calculate fixed character width and height from the font.
        
        Uses the character 'M' (typically the widest in monospace fonts) to
        determine dimensions. No line spacing is added to ensure box-drawing
        characters connect seamlessly.
        
        Also calculates the font ascent for proper baseline positioning when
        using CoreText APIs.
        """
        # Create an attributed string with the font to measure character size
        test_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            "M",
            {Cocoa.NSFontAttributeName: self.font}
        )
        
        # Get the size of the character
        size = test_string.size()
        
        # Store character dimensions
        # Use exact font dimensions without line spacing for seamless box-drawing
        self.char_width = int(size.width)
        self.char_height = int(size.height)
        
        # Get font ascent for baseline positioning
        # CTLineDraw uses baseline positioning, while NSAttributedString.drawAtPoint_
        # uses top-left corner positioning. We need the ascent to convert between them.
        self.font_ascent = self.font.ascender()
    
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
        # Add padding to both width and height for better visual appearance
        window_width = self.cols * self.char_width + (self.WINDOW_PADDING_MULTIPLIER * self.char_height)
        window_height = self.rows * self.char_height + (self.WINDOW_PADDING_MULTIPLIER * self.char_height)
        
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
        
        # Store initial window size before frame restoration
        initial_content_rect = self.window.contentView().frame()
        initial_width = int(initial_content_rect.size.width)
        initial_height = int(initial_content_rect.size.height)
        
        # Enable automatic window frame persistence
        # This tells macOS to automatically save and restore the window's
        # position and size using NSUserDefaults
        # Use the configurable frame autosave name
        try:
            self.window.setFrameAutosaveName_(self.frame_autosave_name)
        except (AttributeError, TypeError) as e:
            # Handle cases where window object doesn't support frame autosave
            # or autosave name is invalid
            print(f"Warning: Could not enable window geometry persistence: {e}")
        except Exception as e:
            # Catch any other unexpected errors
            # Log warning but continue - persistence is non-critical
            print(f"Warning: Unexpected error enabling window geometry persistence: {e}")
        
        # Check if window size changed after frame restoration
        # setFrameAutosaveName_() immediately restores the saved frame if one exists,
        # but this happens before the delegate is set up, so no windowDidResize_
        # notification is sent. We need to manually detect this and set the resize flag.
        restored_content_rect = self.window.contentView().frame()
        restored_width = int(restored_content_rect.size.width)
        restored_height = int(restored_content_rect.size.height)
        
        if restored_width != initial_width or restored_height != initial_height:
            # Window size was restored to a different size
            # Calculate new grid dimensions, accounting for padding
            padding = self.WINDOW_PADDING_MULTIPLIER * self.char_height
            new_cols = max(1, int((restored_width - padding) / self.char_width))
            new_rows = max(1, int((restored_height - padding) / self.char_height))
            
            # Update dimensions if they changed
            if new_cols != self.cols or new_rows != self.rows:
                self.cols = new_cols
                self.rows = new_rows
                # Grid will be initialized with new dimensions in _initialize_grid()
                # Set flag to generate resize event in run_event_loop_iteration()
                self.resize_pending = True
        
        # Create window delegate to handle window events
        self.window_delegate = TTKWindowDelegate.alloc().initWithBackend_(self)
        self.window.setDelegate_(self.window_delegate)
        
        # Create and set up the custom TTKView
        content_rect = self.window.contentView().frame()
        # Use our custom initializer: initWithFrame_backend_()
        # This corresponds to Objective-C: initWithFrame:backend:
        self.view = TTKView.alloc().initWithFrame_backend_(content_rect, self)
        self.window.setContentView_(self.view)
        
        # Note: Resize increments are set dynamically during resize operations
        # (in windowWillStartLiveResize_) to allow macOS window management
        # features like maximize and split view to work properly
        
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
        # Each cell is (char, color_pair, attributes, is_wide)
        self.grid = [
            [(' ', 0, 0, False) for _ in range(self.cols)]
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
    
    def suspend(self) -> None:
        """
        Suspend rendering to allow external programs to run.
        
        For the CoreGraphics backend (GUI application), this is a no-op since
        external programs run in separate windows and don't need the terminal.
        This method exists for interface compatibility with the curses backend.
        """
        pass
    
    def resume(self) -> None:
        """
        Resume rendering after external program execution.
        
        For the CoreGraphics backend (GUI application), this is a no-op since
        external programs run in separate windows and don't affect the GUI state.
        This method exists for interface compatibility with the curses backend.
        """
        pass
    
    def reset_window_geometry(self) -> bool:
        """
        Reset window geometry to default size and position.
        
        This method clears the saved window frame from NSUserDefaults and
        resets the window to the default size and position specified in
        configuration. This is useful for recovering from undesirable window
        states or when the saved geometry becomes problematic.
        
        The method performs the following operations:
        1. Clears the saved frame from NSUserDefaults
        2. Synchronizes NSUserDefaults to ensure changes are persisted
        3. Calculates default window dimensions from grid size and character size
        4. Creates a default frame at position (100, 100)
        5. Applies the default frame to the window
        6. Logs the reset action for debugging purposes
        
        Returns:
            bool: True if reset was successful, False if an error occurred
        
        Example:
            backend = CoreGraphicsBackend()
            backend.initialize()
            
            # ... window is moved/resized by user ...
            
            # Reset to defaults
            success = backend.reset_window_geometry()
            if success:
                print("Window geometry reset successfully")
            else:
                print("Failed to reset window geometry")
        
        Note:
            This method requires that the window has been created (initialize()
            has been called). If called before initialization, it will return
            False with a warning message.
        """
        # Check if window exists
        if self.window is None:
            print("Warning: Cannot reset window geometry - window not initialized")
            return False
        
        try:
            # Clear the saved frame from NSUserDefaults
            user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
            frame_key = f"NSWindow Frame {self.frame_autosave_name}"
            user_defaults.removeObjectForKey_(frame_key)
            
            # Synchronize to ensure changes are persisted immediately
            user_defaults.synchronize()
            
        except (AttributeError, TypeError) as e:
            # Handle cases where NSUserDefaults methods are not available
            # or frame key is invalid
            print(f"Warning: Could not clear saved window frame from NSUserDefaults: {e}")
            # Continue with reset even if clearing fails
        except Exception as e:
            # Catch any other unexpected errors during NSUserDefaults operations
            print(f"Warning: Unexpected error clearing saved window frame: {e}")
            # Continue with reset even if clearing fails
        
        try:
            # Calculate default window dimensions from grid size and character size
            # Add padding to both width and height for better visual appearance
            window_width = self.cols * self.char_width + (self.WINDOW_PADDING_MULTIPLIER * self.char_height)
            window_height = self.rows * self.char_height + (self.WINDOW_PADDING_MULTIPLIER * self.char_height)
            
            # Create default frame at position (100, 100)
            # This matches the default position used in _create_window()
            default_frame = Cocoa.NSMakeRect(100, 100, window_width, window_height)
            
            # Apply default frame to window
            # The second parameter (True) tells the window to redisplay after resizing
            self.window.setFrame_display_(default_frame, True)
            
            # Log the reset action for debugging purposes
            print(f"Window geometry reset to defaults: {window_width}x{window_height} at (100, 100)")
            return True
            
        except (AttributeError, TypeError) as e:
            # Handle cases where window object doesn't support setFrame_display_
            # or frame parameters are invalid
            print(f"Warning: Could not apply default window frame: {e}")
            return False
        except Exception as e:
            # Catch any other unexpected errors during frame application
            print(f"Warning: Unexpected error resetting window geometry: {e}")
            return False
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get window dimensions in character cells.
        
        Returns:
            Tuple[int, int]: (rows, cols) - Current grid dimensions
        """
        return (self.rows, self.cols)
    
    def change_font_size(self, delta: int) -> bool:
        """
        Change the font size by the specified delta.
        
        This method adjusts the font size while keeping the window size constant.
        The grid dimensions (rows, columns) will adjust to fit more or fewer
        characters in the same window size.
        
        Args:
            delta: Amount to change font size (positive to increase, negative to decrease)
        
        Returns:
            bool: True if font size was changed, False if at limits or error occurred
        
        Example:
            # Increase font size by 1 point
            backend.change_font_size(1)
            # Window stays same size, grid shows fewer rows/cols
            
            # Decrease font size by 1 point
            backend.change_font_size(-1)
            # Window stays same size, grid shows more rows/cols
        """
        # Check if window exists
        if self.window is None:
            return False
        
        # Calculate new font size
        new_font_size = self.font_size + delta
        
        # Enforce limits (8-72 points)
        if new_font_size < 8 or new_font_size > 72:
            return False
        
        try:
            # Update font size
            self.font_size = new_font_size
            
            # Reload font with new size
            self._load_font()
            
            # Recalculate character dimensions
            self._calculate_char_dimensions()
            
            # Note: C++ renderer caches will be automatically reinitialized
            # on the next render_frame() call when it detects font size change
            
            # Get current content view size (keep window size constant)
            content_rect = self.window.contentView().frame()
            content_width = int(content_rect.size.width)
            content_height = int(content_rect.size.height)
            
            # Calculate new grid dimensions based on new character size
            # More characters fit with smaller font, fewer with larger font
            padding = self.WINDOW_PADDING_MULTIPLIER * self.char_height
            new_cols = max(1, int((content_width - padding) / self.char_width))
            new_rows = max(1, int((content_height - padding) / self.char_height))
            
            # Update grid dimensions
            old_rows = self.rows
            old_cols = self.cols
            self.rows = new_rows
            self.cols = new_cols
            
            # Resize grid to new dimensions
            old_grid = self.grid
            new_grid = [
                [(' ', 0, 0, False) for _ in range(new_cols)]
                for _ in range(new_rows)
            ]
            
            # Copy old content to new grid (as much as fits)
            for row in range(min(old_rows, new_rows)):
                for col in range(min(old_cols, new_cols)):
                    new_grid[row][col] = old_grid[row][col]
            
            self.grid = new_grid
            
            # Set flag to generate resize event so application knows grid changed
            self.resize_pending = True
            
            # Force view to redraw with new font
            if self.view:
                self.view.setNeedsDisplay_(True)
            
            return True
            
        except Exception as e:
            # If anything fails, try to restore original font size
            self.font_size = new_font_size - delta
            try:
                self._load_font()
                self._calculate_char_dimensions()
            except Exception:
                pass
            return False
    
    def set_event_callback(self, callback: Optional['EventCallback']) -> None:
        """
        Set the event callback for event delivery (REQUIRED).
        
        Events are delivered via the callback methods (on_key_event, on_char_event,
        on_system_event). This enables the callback-based event system required for
        proper CharEvent generation.
        
        The callback is required and cannot be None. All events are delivered via
        the callback methods.
        
        Args:
            callback: EventCallback instance (required, not optional)
        
        Raises:
            ValueError: If callback is None
        
        Example:
            # Enable callback-based event delivery
            callback = TFMEventCallback(app)
            backend.set_event_callback(callback)
        """
        if callback is None:
            raise ValueError("Event callback cannot be None")
        self.event_callback = callback
    
    def run_event_loop(self) -> None:
        """
        Run the NSApplication event loop.
        
        This method starts the macOS NSApplication event loop, which processes
        events and delivers them via the callback system. This is the main event
        loop for desktop mode when using callbacks.
        
        The event loop runs until the application quits (window is closed or
        quit command is issued). Events are delivered via the EventCallback
        methods (on_key_event, on_char_event, on_system_event) set with
        set_event_callback().
        
        This method integrates with the existing window management and event
        handling infrastructure:
        - Window resize events are delivered via on_system_event
        - Window close events are delivered via on_system_event
        - Keyboard events are delivered via keyDown: → on_key_event
        - Character events are delivered via insertText: → on_char_event
        
        Raises:
            RuntimeError: If event callback not set
        
        Example:
            # Set up event callback
            callback = TFMEventCallback(app)
            backend.set_event_callback(callback)
            
            # Run event loop (blocks until application quits)
            backend.run_event_loop()
        
        Note:
            This method blocks until the application quits. It should be called
            after all initialization is complete and the window is ready to
            receive events.
        """
        if self.event_callback is None:
            raise RuntimeError("Event callback not set. Call set_event_callback() first.")
        
        # Get the shared application instance
        app = Cocoa.NSApplication.sharedApplication()
        
        # Run the application event loop
        # This blocks until the application quits
        app.run()
    
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
        if self.event_callback is None:
            raise RuntimeError("Event callback not set. Call set_event_callback() first.")
        
        # Check for pending system events and deliver them via callback
        # These flags are set by window delegate methods (windowDidResize_, windowShouldClose_)
        
        # Check for resize event
        if self.resize_pending:
            self.resize_pending = False
            resize_event = SystemEvent(
                event_type=SystemEventType.RESIZE
            )
            self.event_callback.on_system_event(resize_event)
        
        # Check for close event
        if self.should_close:
            close_event = SystemEvent(
                event_type=SystemEventType.CLOSE
            )
            self.event_callback.on_system_event(close_event)
        
        # Check for pending menu events and deliver them via callback
        if hasattr(self, 'menu_event_queue') and self.menu_event_queue:
            menu_event = self.menu_event_queue.pop(0)
            self.event_callback.on_menu_event(menu_event)
        
        # Get the shared application instance
        app = Cocoa.NSApplication.sharedApplication()
        
        # Calculate timeout date
        if timeout_ms < 0:
            # Wait indefinitely
            date = Cocoa.NSDate.distantFuture()
        elif timeout_ms == 0:
            # Non-blocking
            date = Cocoa.NSDate.distantPast()
        else:
            # Wait for specified timeout
            date = Cocoa.NSDate.dateWithTimeIntervalSinceNow_(timeout_ms / 1000.0)
        
        # Process one event
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            Cocoa.NSAnyEventMask,
            date,
            Cocoa.NSDefaultRunLoopMode,
            True
        )
        
        if event:
            # Send event to the application for processing
            try:
                app.sendEvent_(event)
                # Update the application (process any pending operations)
                app.updateWindows()
            except Exception as e:
                # Some events (like scroll wheel with phase=MayBegin) can cause errors
                # Log and ignore these errors to prevent crashes
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error processing event: {e}")
                # Continue processing other events
                pass
    
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
                    self.grid[row][col] = (' ', 0, 0, False)
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
                    self.grid[r][c] = (' ', 0, 0, False)
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
            
            # Draw each character in the text, accounting for wide characters
            current_col = col
            for char in text:
                # Stop if we've reached the right edge of the grid
                if current_col >= self.cols:
                    break
                
                # Check if this is a wide character (occupies 2 cells)
                is_wide = _is_wide_character(char)
                
                # Update the grid cell with the character, color pair, attributes, and is_wide flag
                self.grid[row][current_col] = (char, color_pair, attributes, is_wide)
                
                # Check if this is a wide character (occupies 2 cells)
                if is_wide:
                    # Move to next column and store empty placeholder
                    current_col += 1
                    if current_col < self.cols:
                        # Store empty string as placeholder for the second cell of wide char
                        self.grid[row][current_col] = ('', color_pair, attributes, False)
                
                # Move to next column
                current_col += 1
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
            is_wide = _is_wide_character(char)
            for c in range(start_col, end_col):
                self.grid[row][c] = (char, color_pair, 0, is_wide)
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
            is_wide = _is_wide_character(char)
            for r in range(start_row, end_row):
                self.grid[r][col] = (char, color_pair, 0, is_wide)
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
                        self.grid[r][c] = (' ', color_pair, 0, False)
            else:
                # Draw outlined rectangle using box-drawing characters
                # For rectangles with height or width of 1 or 2, we need special handling
                
                if actual_height == 1:
                    # Single row rectangle - just draw horizontal line
                    for c in range(start_col, end_col):
                        self.grid[start_row][c] = ('─', color_pair, 0, False)
                elif actual_width == 1:
                    # Single column rectangle - just draw vertical line
                    for r in range(start_row, end_row):
                        self.grid[r][start_col] = ('│', color_pair, 0, False)
                else:
                    # Normal rectangle with at least 2x2 dimensions
                    
                    # Draw top edge
                    # Top-left corner
                    self.grid[start_row][start_col] = ('┌', color_pair, 0, False)
                    
                    # Top edge
                    for c in range(start_col + 1, end_col - 1):
                        self.grid[start_row][c] = ('─', color_pair, 0, False)
                    
                    # Top-right corner
                    self.grid[start_row][end_col - 1] = ('┐', color_pair, 0, False)
                    
                    # Draw left and right edges (if there are rows between top and bottom)
                    for r in range(start_row + 1, end_row - 1):
                        # Left edge
                        self.grid[r][start_col] = ('│', color_pair, 0, False)
                        
                        # Right edge
                        self.grid[r][end_col - 1] = ('│', color_pair, 0, False)
                    
                    # Draw bottom edge
                    # Bottom-left corner
                    self.grid[end_row - 1][start_col] = ('└', color_pair, 0, False)
                    
                    # Bottom edge
                    for c in range(start_col + 1, end_col - 1):
                        self.grid[end_row - 1][c] = ('─', color_pair, 0, False)
                    
                    # Bottom-right corner
                    self.grid[end_row - 1][end_col - 1] = ('┘', color_pair, 0, False)
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
    
    def update_background(self, bg_color: Tuple[int, int, int]) -> None:
        """
        Update the window background color.
        
        This method updates the background color of the entire window view.
        It should be called after color scheme changes to ensure all areas
        (including those where no characters are drawn) have the correct background.
        
        Args:
            bg_color: Background color as (R, G, B) tuple (0-255 each)
        """
        try:
            # Update color pair 0 (default) with new background
            self.color_pairs[0] = (self.color_pairs[0][0], bg_color)
            
            # Convert RGB (0-255) to NSColor (0.0-1.0)
            r = bg_color[0] / 255.0
            g = bg_color[1] / 255.0
            b = bg_color[2] / 255.0
            
            # Create NSColor with RGB values
            ns_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(
                r, g, b, 1.0
            )
            
            # Set the view's background color
            # This ensures areas outside the character grid show the correct color
            if self.view is not None:
                # Set the layer background color for proper rendering
                if not self.view.wantsLayer():
                    self.view.setWantsLayer_(True)
                
                # Convert NSColor to CGColor for layer
                cg_color = ns_color.CGColor()
                self.view.layer().setBackgroundColor_(cg_color)
                
                # Mark view as needing display to apply the change
                self.view.setNeedsDisplay_(True)
                
        except Exception as e:
            print(f"Warning: Could not update background: {e}")
        

    def _translate_event(self, event) -> Optional[KeyEvent]:
        """
        Translate a macOS NSEvent to a TTK KeyEvent.
        
        This method converts macOS-specific keyboard events into TTK's unified
        KeyEvent format. It handles:
        - Keyboard events: Maps macOS key codes to TTK KeyCode values
        - Modifier keys: Extracts Shift, Control, Alt, Command states
        - Printable characters: Preserves character information
        
        Args:
            event: NSEvent object from macOS event system
        
        Returns:
            Optional[KeyEvent]: Translated KeyEvent, or None if the event
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
            return KeyEvent(
                key_code=ttk_key_code,
                modifiers=modifiers,
                char=None  # Special keys don't have printable characters
            )
        
        # Handle printable characters
        if char and len(char) == 1:
            # Handle special characters that might come through as printable
            if char == '\r' or char == '\n':
                return KeyEvent(
                    key_code=KeyCode.ENTER,
                    modifiers=modifiers,
                    char=None
                )
            elif char == '\t':
                return KeyEvent(
                    key_code=KeyCode.TAB,
                    modifiers=modifiers,
                    char=None
                )
            elif char == '\x1b':  # Escape
                return KeyEvent(
                    key_code=KeyCode.ESCAPE,
                    modifiers=modifiers,
                    char=None
                )
            elif char == '\x7f':  # Delete/Backspace
                return KeyEvent(
                    key_code=KeyCode.BACKSPACE,
                    modifiers=modifiers,
                    char=None
                )
            else:
                # Regular printable character
                code_point = ord(char)
                return KeyEvent(
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
    
    def set_cursor_position(self, row: int, col: int) -> None:
        """
        Update cursor position for IME positioning.
        
        This method should be called by text widgets when the cursor moves
        to ensure IME composition appears at the correct location. Unlike
        move_cursor(), this method does not trigger a redraw and is specifically
        designed for IME support.
        
        Coordinates are clamped to valid grid bounds to prevent out-of-bounds
        errors. If the position is significantly out of bounds (more than 10
        rows/cols beyond the grid), a warning is logged.
        
        Args:
            row: Cursor row (0-based, 0 is top)
            col: Cursor column (0-based, 0 is left)
        
        Example:
            # Update cursor position for IME
            backend.set_cursor_position(5, 10)
            
            # IME will now position composition text at row 5, column 10
        """
        # Log warning if position is significantly out of bounds
        if row < -10 or row >= self.rows + 10 or col < -10 or col >= self.cols + 10:
            print(f"Warning: Cursor position ({row}, {col}) is significantly out of bounds "
                  f"for grid size ({self.rows}, {self.cols})")
        
        # Clamp to valid range
        self.cursor_row = max(0, min(row, self.rows - 1))
        self.cursor_col = max(0, min(col, self.cols - 1))
    
    def set_menu_bar(self, menu_structure: dict) -> None:
        """
        Set menu bar structure for desktop mode.
        
        Creates a native macOS menu bar using NSMenu and NSMenuItem APIs.
        Menu items are cached for efficient state updates via update_menu_item_state().
        
        Args:
            menu_structure: Menu structure dictionary with format:
                {
                    'menus': [
                        {
                            'id': str,
                            'label': str,
                            'items': [
                                {
                                    'id': str,
                                    'label': str,
                                    'shortcut': Optional[str],
                                    'enabled': bool
                                },
                                {'separator': True},
                                ...
                            ]
                        },
                        ...
                    ]
                }
        """
        if not menu_structure or 'menus' not in menu_structure:
            return
        
        # Initialize menu event queue if not already done
        if not hasattr(self, 'menu_event_queue'):
            self.menu_event_queue = []
        
        # Initialize menu items cache if not already done
        if not hasattr(self, 'menu_items'):
            self.menu_items = {}
        
        # Create main menu bar
        main_menu = Cocoa.NSMenu.alloc().init()
        
        # Process each top-level menu
        for menu_def in menu_structure.get('menus', []):
            # Create submenu for this top-level menu
            submenu = Cocoa.NSMenu.alloc().initWithTitle_(menu_def['label'])
            
            # Disable auto-enabling - we'll manage states manually
            submenu.setAutoenablesItems_(False)
            
            # Create menu item to hold the submenu
            menu_item = Cocoa.NSMenuItem.alloc().init()
            menu_item.setSubmenu_(submenu)
            
            # Add menu items to the submenu
            for item_def in menu_def.get('items', []):
                if item_def.get('separator'):
                    # Add separator
                    submenu.addItem_(Cocoa.NSMenuItem.separatorItem())
                else:
                    # Create regular menu item
                    item = self._create_menu_item(item_def)
                    submenu.addItem_(item)
                    
                    # Cache the menu item for state updates
                    self.menu_items[item_def['id']] = item
            
            # Add the menu to the main menu bar
            main_menu.addItem_(menu_item)
        
        # Set the main menu for the application
        app = Cocoa.NSApplication.sharedApplication()
        app.setMainMenu_(main_menu)
        
        # Store reference to menu bar
        self.menu_bar = main_menu
    
    def _create_menu_item(self, item_def: dict):
        """
        Create a single NSMenuItem from definition.
        
        Args:
            item_def: Menu item definition dictionary with keys:
                - id: Unique identifier
                - label: Display label
                - shortcut: Optional keyboard shortcut (e.g., 'Cmd+N')
                - enabled: Initial enabled state
        
        Returns:
            NSMenuItem configured with the specified properties
        """
        # Parse keyboard shortcut
        key_equivalent, modifier_mask = self._parse_shortcut(item_def.get('shortcut', ''))
        
        # Create menu item with title, action, and key equivalent
        # Use selector name as string - PyObjC will handle the bridging
        item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            item_def['label'],
            '_menu_item_selected:',  # Selector as string with trailing colon for one argument
            key_equivalent
        )
        
        # Set modifier mask for the shortcut
        if modifier_mask is not None:
            item.setKeyEquivalentModifierMask_(modifier_mask)
        
        # Set initial enabled state
        item.setEnabled_(item_def.get('enabled', True))
        
        # Store the item ID as represented object for callback identification
        item.setRepresentedObject_(item_def['id'])
        
        # Set target to self for the action callback
        item.setTarget_(self)
        
        return item
    
    def _parse_shortcut(self, shortcut: str):
        """
        Parse keyboard shortcut string into macOS key equivalent and modifier mask.
        
        Converts shortcut strings like 'Cmd+N', 'Cmd+Shift+S', 'Ctrl+C' into
        the format required by NSMenuItem.
        
        Args:
            shortcut: Shortcut string (e.g., 'Cmd+N', 'Cmd+Shift+S', 'Ctrl+C')
        
        Returns:
            Tuple of (key_equivalent: str, modifier_mask: int or None)
            - key_equivalent: The key character (e.g., 'n', 's', 'c')
            - modifier_mask: Bitwise OR of NSEventModifierFlag values, or None if no modifiers
        
        Examples:
            'Cmd+N' -> ('n', NSEventModifierFlagCommand)
            'Cmd+Shift+S' -> ('S', NSEventModifierFlagCommand | NSEventModifierFlagShift)
            'Ctrl+C' -> ('c', NSEventModifierFlagControl)
            '' -> ('', None)
        """
        if not shortcut:
            return ('', None)
        
        # Split shortcut into parts
        parts = shortcut.split('+')
        if not parts:
            return ('', None)
        
        # Last part is the key, everything else is modifiers
        key = parts[-1]
        modifiers = parts[:-1]
        
        # Build modifier mask
        modifier_mask = 0
        for mod in modifiers:
            mod_lower = mod.lower()
            if mod_lower == 'cmd' or mod_lower == 'command':
                modifier_mask |= Cocoa.NSEventModifierFlagCommand
            elif mod_lower == 'shift':
                modifier_mask |= Cocoa.NSEventModifierFlagShift
            elif mod_lower == 'ctrl' or mod_lower == 'control':
                modifier_mask |= Cocoa.NSEventModifierFlagControl
            elif mod_lower == 'alt' or mod_lower == 'option':
                modifier_mask |= Cocoa.NSEventModifierFlagOption
        
        # Convert key to lowercase unless Shift is in modifiers
        # (Shift modifier makes the key uppercase automatically)
        if 'shift' not in [m.lower() for m in modifiers]:
            key = key.lower()
        
        return (key, modifier_mask if modifier_mask > 0 else None)
    
    def _menu_item_selected_(self, sender):
        """
        Callback when a menu item is selected.
        
        This method is called by the macOS menu system when a user selects
        a menu item. It creates a MenuEvent and adds it to the event queue.
        
        Args:
            sender: The NSMenuItem that was selected
        """
        # Get the item ID from the represented object
        item_id = sender.representedObject()
        
        if item_id:
            # Create MenuEvent and add to queue
            from ttk.input_event import MenuEvent
            event = MenuEvent(item_id=item_id)
            self.menu_event_queue.append(event)
    
    def update_menu_item_state(self, item_id: str, enabled: bool) -> None:
        """
        Update menu item enabled/disabled state.
        
        Dynamically updates whether a menu item is enabled (selectable) or
        disabled (grayed out) based on application state.
        
        Args:
            item_id: Menu item identifier (must match an ID from set_menu_bar)
            enabled: True to enable, False to disable
        """
        if not hasattr(self, 'menu_items'):
            return
        
        if item_id in self.menu_items:
            self.menu_items[item_id].setEnabled_(enabled)
    
    def set_caret_position(self, x: int, y: int) -> None:
        """
        Set the caret position for IME composition text positioning.
        
        This method updates the cursor position used by the NSTextInputClient
        protocol to position the IME composition overlay and candidate window.
        
        Note: In TTK, x is the column and y is the row (different from typical
        screen coordinates where x is horizontal and y is vertical).
        
        Args:
            x: Column position (0-based)
            y: Row position (0-based)
        """
        # Update cursor position for IME
        # Note: x is column, y is row in TTK convention
        self.set_cursor_position(y, x)
    
    def is_desktop_mode(self) -> bool:
        """
        Check if the renderer is running in desktop mode.
        
        CoreGraphics backend always runs in desktop mode (native GUI window).
        
        Returns:
            bool: Always True for CoreGraphics backend
        """
        return True
    
    def supports_mouse(self) -> bool:
        """
        Query whether this backend supports mouse events.
        
        The CoreGraphics backend provides full mouse support including all
        event types (button, move, wheel, double-click).
        
        Returns:
            bool: Always True for CoreGraphics backend
        """
        return True
    
    def get_supported_mouse_events(self) -> set:
        """
        Query which mouse event types are supported by this backend.
        
        The CoreGraphics backend supports all mouse event types through
        native macOS NSEvent handling.
        
        Returns:
            set: Set of all MouseEventType values
        """
        from ttk.ttk_mouse_event import MouseEventType
        
        return {
            MouseEventType.BUTTON_DOWN,
            MouseEventType.BUTTON_UP,
            MouseEventType.DOUBLE_CLICK,
            MouseEventType.MOVE,
            MouseEventType.WHEEL,
            MouseEventType.DRAG
        }
    
    def enable_mouse_events(self) -> bool:
        """
        Enable mouse event capture.
        
        This method activates mouse event tracking in the CoreGraphics backend.
        After calling this method successfully, mouse events will be delivered
        via the event callback's on_mouse_event() method.
        
        Returns:
            bool: True if mouse events were successfully enabled
        """
        if not hasattr(self, 'mouse_enabled'):
            self.mouse_enabled = False
        
        # Mouse support is always available in CoreGraphics
        self.mouse_enabled = True
        return True
    

    def _transform_mouse_coordinates(self, window_x: float, window_y: float) -> tuple:
        """
        Transform window coordinates to text grid coordinates.
        
        This method converts macOS window coordinates (origin at bottom-left)
        to TTK text grid coordinates (origin at top-left) with sub-cell positioning.
        
        Args:
            window_x: X coordinate in window space (pixels from left edge)
            window_y: Y coordinate in window space (pixels from bottom edge)
            
        Returns:
            Tuple of (column, row, sub_cell_x, sub_cell_y) where:
            - column: Integer grid column (0-based)
            - row: Integer grid row (0-based)
            - sub_cell_x: Fractional position within cell horizontally [0.0, 1.0)
            - sub_cell_y: Fractional position within cell vertically [0.0, 1.0)
        """
        # Get view frame to calculate centering offset
        if self.view is None:
            # No view, use simple transformation
            offset_x = 0.0
            offset_y = 0.0
        else:
            view_frame = self.view.frame()
            view_width = view_frame.size.width
            view_height = view_frame.size.height
            
            grid_width = self.cols * self.char_width
            grid_height = self.rows * self.char_height
            
            offset_x = (view_width - grid_width) / 2.0
            offset_y = (view_height - grid_height) / 2.0
        
        # Adjust for centering offset
        adjusted_x = window_x - offset_x
        adjusted_y = window_y - offset_y
        
        # CoreGraphics uses bottom-left origin, TTK uses top-left origin
        # Convert Y coordinate from bottom-left to top-left
        ttk_y = (self.rows * self.char_height) - adjusted_y
        
        # Calculate grid position
        column = int(adjusted_x / self.char_width)
        row = int(ttk_y / self.char_height)
        
        # Calculate sub-cell position as fraction
        sub_cell_x = (adjusted_x % self.char_width) / self.char_width
        sub_cell_y = (ttk_y % self.char_height) / self.char_height
        
        # Ensure sub-cell values are in valid range [0.0, 1.0)
        sub_cell_x = max(0.0, min(sub_cell_x, 0.999999))
        sub_cell_y = max(0.0, min(sub_cell_y, 0.999999))
        
        # Clamp grid coordinates to valid range
        column = max(0, min(column, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        
        return column, row, sub_cell_x, sub_cell_y
    
    def _handle_mouse_event(self, event) -> None:
        """
        Handle a native macOS mouse event and convert it to a MouseEvent.
        
        This method is called by the TTKView when it receives mouse events.
        It converts the native NSEvent to a TTK MouseEvent and delivers it
        via the event callback.
        
        Args:
            event: NSEvent from macOS event system
        """
        if not hasattr(self, 'mouse_enabled') or not self.mouse_enabled:
            return
        
        # Check if event callback is set
        if not self.event_callback:
            return
        
        from ttk.ttk_mouse_event import MouseEvent, MouseEventType, MouseButton
        import time
        
        # Get event type
        event_type_map = {
            Cocoa.NSEventTypeLeftMouseDown: MouseEventType.BUTTON_DOWN,
            Cocoa.NSEventTypeLeftMouseUp: MouseEventType.BUTTON_UP,
            Cocoa.NSEventTypeRightMouseDown: MouseEventType.BUTTON_DOWN,
            Cocoa.NSEventTypeRightMouseUp: MouseEventType.BUTTON_UP,
            Cocoa.NSEventTypeOtherMouseDown: MouseEventType.BUTTON_DOWN,
            Cocoa.NSEventTypeOtherMouseUp: MouseEventType.BUTTON_UP,
            Cocoa.NSEventTypeMouseMoved: MouseEventType.MOVE,
            Cocoa.NSEventTypeLeftMouseDragged: MouseEventType.DRAG,
            Cocoa.NSEventTypeRightMouseDragged: MouseEventType.DRAG,
            Cocoa.NSEventTypeOtherMouseDragged: MouseEventType.DRAG,
            Cocoa.NSEventTypeScrollWheel: MouseEventType.WHEEL,
        }
        
        ns_event_type = event.type()
        mouse_event_type = event_type_map.get(ns_event_type)
        
        if mouse_event_type is None:
            return
        
        # Get mouse button
        button = MouseButton.NONE
        if ns_event_type in (Cocoa.NSEventTypeLeftMouseDown, Cocoa.NSEventTypeLeftMouseUp, Cocoa.NSEventTypeLeftMouseDragged):
            button = MouseButton.LEFT
        elif ns_event_type in (Cocoa.NSEventTypeRightMouseDown, Cocoa.NSEventTypeRightMouseUp, Cocoa.NSEventTypeRightMouseDragged):
            button = MouseButton.RIGHT
        elif ns_event_type in (Cocoa.NSEventTypeOtherMouseDown, Cocoa.NSEventTypeOtherMouseUp, Cocoa.NSEventTypeOtherMouseDragged):
            # Middle button or other buttons
            button = MouseButton.MIDDLE
        
        # Get mouse location in window coordinates
        location_in_window = event.locationInWindow()
        
        # Transform to text grid coordinates
        column, row, sub_cell_x, sub_cell_y = self._transform_mouse_coordinates(
            location_in_window.x,
            location_in_window.y
        )
        
        # Get scroll deltas for wheel events
        scroll_delta_x = 0.0
        scroll_delta_y = 0.0
        if mouse_event_type == MouseEventType.WHEEL:
            scroll_delta_x = float(event.scrollingDeltaX())
            scroll_delta_y = float(event.scrollingDeltaY())
            
            # Skip scroll events with zero delta (phase events like MayBegin, Ended)
            # These are momentum/gesture tracking events that don't represent actual scrolling
            if scroll_delta_x == 0.0 and scroll_delta_y == 0.0:
                return
        
        # Get modifier keys
        modifier_flags = event.modifierFlags()
        shift = bool(modifier_flags & Cocoa.NSEventModifierFlagShift)
        ctrl = bool(modifier_flags & Cocoa.NSEventModifierFlagControl)
        alt = bool(modifier_flags & Cocoa.NSEventModifierFlagOption)
        meta = bool(modifier_flags & Cocoa.NSEventModifierFlagCommand)
        
        # Check for double-click (only valid for button events, not scroll wheel events)
        button_event_types = (
            Cocoa.NSEventTypeLeftMouseDown,
            Cocoa.NSEventTypeRightMouseDown,
            Cocoa.NSEventTypeOtherMouseDown
        )
        if ns_event_type in button_event_types and event.clickCount() == 2 and mouse_event_type == MouseEventType.BUTTON_DOWN:
            mouse_event_type = MouseEventType.DOUBLE_CLICK
        
        # Create MouseEvent
        mouse_event = MouseEvent(
            event_type=mouse_event_type,
            column=column,
            row=row,
            sub_cell_x=sub_cell_x,
            sub_cell_y=sub_cell_y,
            button=button,
            scroll_delta_x=scroll_delta_x,
            scroll_delta_y=scroll_delta_y,
            timestamp=time.time(),
            shift=shift,
            ctrl=ctrl,
            alt=alt,
            meta=meta
        )
        
        # Deliver mouse event via callback (similar to keyboard events)
        try:
            self.event_callback.on_mouse_event(mouse_event)
        except Exception as e:
            import traceback
            print(f"Error in mouse event callback: {e}")
            traceback.print_exc()


# Define TTKWindowDelegate class for handling window events
if COCOA_AVAILABLE:
    # ALWAYS create a new class to ensure we have the latest implementation
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
                picked up by the event loop. We return False to prevent the window
                from closing immediately, allowing the application to handle the
                close event gracefully through its normal event loop.
                
                Args:
                    sender: The window that is requesting to close
                
                Returns:
                    bool: False to prevent immediate window close, letting the
                         application handle the close event through the event loop
                """
                self.backend.should_close = True
                return False
            
            def windowWillStartLiveResize_(self, notification):
                """
                Handle the start of a live resize operation.
                
                This method is called when the user starts dragging the window
                resize handle. We snap the window to the grid first to ensure
                proper alignment, then enable resize increments for snapping
                during the drag operation.
                
                Args:
                    notification: NSNotification containing resize information
                """
                # Snap window to grid before starting resize
                # This ensures we start from a properly aligned state
                self._snap_window_to_grid()
                
                # Enable resize increments for manual resizing
                # This ensures the window snaps to character grid boundaries during drag
                resize_increment = Cocoa.NSMakeSize(self.backend.char_width, self.backend.char_height)
                self.backend.window.setResizeIncrements_(resize_increment)
            
            def windowDidEndLiveResize_(self, notification):
                """
                Handle the end of a live resize operation.
                
                This method is called when the user finishes dragging the window
                resize handle. We disable resize increments to allow macOS window
                management features (maximized, split view, tiled windows) to work
                properly.
                
                Args:
                    notification: NSNotification containing resize information
                """
                # Disable resize increments to allow macOS window management
                # Setting increments to (1, 1) effectively disables the constraint
                self.backend.window.setResizeIncrements_(Cocoa.NSMakeSize(1.0, 1.0))
            
            def _is_window_snapped_to_edge(self):
                """
                Check if the window is snapped to any monitor edge.
                
                This method compares the window's frame with the screen's visible
                frame to determine if the window is aligned with any edge. This is
                used to detect when the window is in a macOS-managed state (split
                view, tiled, or manually snapped to screen edges).
                
                Returns:
                    bool: True if window is snapped to any edge (left, right, top, or bottom)
                """
                window_frame = self.backend.window.frame()
                screen = self.backend.window.screen()
                
                if not screen:
                    return False
                
                # Get the visible frame (excludes menu bar and dock)
                visible_frame = screen.visibleFrame()
                
                # Define a small tolerance for floating point comparison (1.5 pixel)
                tolerance = 1.5
                
                # Check if window is snapped to any edge
                snapped_left = abs(window_frame.origin.x - visible_frame.origin.x) < tolerance
                snapped_right = abs((window_frame.origin.x + window_frame.size.width) - 
                                    (visible_frame.origin.x + visible_frame.size.width)) < tolerance
                snapped_bottom = abs(window_frame.origin.y - visible_frame.origin.y) < tolerance
                snapped_top = abs((window_frame.origin.y + window_frame.size.height) - 
                                  (visible_frame.origin.y + visible_frame.size.height)) < tolerance
                
                return snapped_left or snapped_right or snapped_bottom or snapped_top
            
            def _snap_window_to_grid(self):
                """
                Snap the window size to the character grid.
                
                This method adjusts the window frame to ensure the content size
                is an exact multiple of the character cell size plus the standard
                padding. This prevents partial character cells from appearing at
                the edges of the window.
                
                The window's top-left position is preserved during snapping.
                Since macOS uses bottom-left origin coordinates, we calculate
                the new bottom-left position to maintain the same top-left.
                
                If the window is snapped to any screen edge (split view, tiled,
                or manually positioned), snapping is skipped to respect the
                macOS window management state.
                
                Called at the start of resize operations to ensure proper
                initial alignment.
                """
                # Skip snapping if window is snapped to any screen edge
                # This preserves macOS window management features (split view, tiling)
                if self._is_window_snapped_to_edge():
                    return
                
                # Get current window frame and content rect
                window_frame = self.backend.window.frame()
                content_rect = self.backend.window.contentView().frame()
                
                # Calculate current content size
                current_width = content_rect.size.width
                current_height = content_rect.size.height
                
                # Calculate padding
                padding = self.backend.WINDOW_PADDING_MULTIPLIER * self.backend.char_height
                
                # Calculate snapped content size
                # First subtract padding to get the grid area, then calculate cols/rows
                grid_width = current_width - padding
                grid_height = current_height - padding
                
                snapped_cols = max(1, int(grid_width / self.backend.char_width))
                snapped_rows = max(1, int(grid_height / self.backend.char_height))
                
                # Now add padding back to get the final content size
                snapped_width = snapped_cols * self.backend.char_width + padding
                snapped_height = snapped_rows * self.backend.char_height + padding
                
                # Check if snapping is needed
                if abs(current_width - snapped_width) < 0.5 and abs(current_height - snapped_height) < 0.5:
                    # Already aligned, no need to snap
                    return
                
                # Calculate the difference between window frame and content rect
                # This accounts for title bar and window decorations
                frame_width_diff = window_frame.size.width - current_width
                frame_height_diff = window_frame.size.height - current_height
                
                # Calculate new window frame size
                new_frame_width = snapped_width + frame_width_diff
                new_frame_height = snapped_height + frame_height_diff
                
                # Calculate height change to adjust origin
                height_change = new_frame_height - window_frame.size.height
                
                # Create new frame with snapped size
                # Adjust origin.y to preserve top-left position (macOS uses bottom-left origin)
                # When height increases, origin.y must decrease to keep top fixed
                new_frame = Cocoa.NSMakeRect(
                    window_frame.origin.x,
                    window_frame.origin.y - height_change,
                    new_frame_width,
                    new_frame_height
                )
                
                # Set the new frame without animation
                self.backend.window.setFrame_display_(new_frame, True)
            
            def windowDidResize_(self, notification):
                """
                Handle window resize events.
                
                This method is called when the window is resized. We recalculate
                the grid dimensions based on the new window size.
                
                The window uses setResizeIncrements_ to snap to character grid
                boundaries during dragging. Additionally, windowWillStartLiveResize_
                and windowDidEndLiveResize_ ensure proper alignment at the start
                and end of resize operations.
                
                Args:
                    notification: NSNotification containing resize information
                """
                # Get the new content view size
                content_rect = self.backend.window.contentView().frame()
                new_width = int(content_rect.size.width)
                new_height = int(content_rect.size.height)
                
                # Calculate new grid dimensions based on content size
                # Account for padding added to window size
                padding = self.backend.WINDOW_PADDING_MULTIPLIER * self.backend.char_height
                new_cols = max(1, int((new_width - padding) / self.backend.char_width))
                new_rows = max(1, int((new_height - padding) / self.backend.char_height))
                
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
                        [(' ', 0, 0, False) for _ in range(new_cols)]
                        for _ in range(new_rows)
                    ]
                    
                    # Copy old content to new grid (as much as fits)
                    for row in range(min(old_rows, new_rows)):
                        for col in range(min(old_cols, new_cols)):
                            new_grid[row][col] = old_grid[row][col]
                    
                    # Update grid
                    self.backend.grid = new_grid
                    
                    # Clear attribute dictionary cache on resize
                    # This ensures cached attribute dictionaries are rebuilt with new dimensions
                    if hasattr(self.backend, '_attr_dict_cache') and self.backend._attr_dict_cache is not None:
                        self.backend._attr_dict_cache.clear()
                    
                    # Clear attributed string cache on resize
                    # This ensures cached NSAttributedString objects are rebuilt with new dimensions
                    if hasattr(self.backend, '_attr_string_cache') and self.backend._attr_string_cache is not None:
                        self.backend._attr_string_cache.clear()
                    
                    # Set flag to generate resize event in run_event_loop_iteration()
                    self.backend.resize_pending = True
                    
                    # Trigger redraw
                    self.backend.view.setNeedsDisplay_(True)
else:
    # Provide a dummy class when PyObjC is not available
    class TTKWindowDelegate:
        """Dummy TTKWindowDelegate class when PyObjC is not available."""
        pass

# Define TTKView class with proper PyObjC registration
# Create TTKView class
if COCOA_AVAILABLE:
    # ALWAYS create a new class to ensure we have the latest implementation
    # Don't try to reuse an old class from the Objective-C runtime
    # This ensures our keyDown_ and other methods are properly registered
    class TTKView(Cocoa.NSView, protocols=[objc.protocolNamed('NSTextInputClient')]):
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
                
                # IME state tracking for NSTextInputClient protocol support
                # These instance variables track the current composition state
                # for Input Method Editor (IME) support on macOS
                self.marked_text = ""  # Current composition text
                self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)  # Composition range
                self.selected_range = Cocoa.NSMakeRange(0, 0)  # Selection within composition
                
                # Create and store the text input context for IME support
                # This is critical for IME to work - without an active input context,
                # the IME system cannot communicate with the view
                self._input_context = Cocoa.NSTextInputContext.alloc().initWithClient_(self)
                
                return self
            
            def drawRect_(self, rect):
                """
                Render the character grid using C++ CoreGraphics implementation.
                
                This method is called by the Cocoa event loop when the view needs
                to be redrawn. It uses the C++ rendering implementation for optimal
                performance with direct CoreGraphics/CoreText API access.
                
                PyObjC Method Name Translation:
                    Objective-C: drawRect:
                    PyObjC: drawRect_()
                    The trailing underscore indicates a single parameter method.
                
                Args:
                    rect: NSRect indicating the region that needs to be redrawn
                """

                # Get the current graphics context (may be None if not in drawing context)
                graphics_context = Cocoa.NSGraphicsContext.currentContext()
                if graphics_context is None:
                    # Not in a valid drawing context, skip rendering
                    return
                
                # Calculate centering offset to center text grid within view
                # When window is resized, content view size may not perfectly match
                # the text grid size (cols * char_width, rows * char_height).
                # Center the grid so white background appears evenly on all sides.
                view_frame = self.frame()
                view_width = view_frame.size.width
                view_height = view_frame.size.height
                
                grid_width = self.backend.cols * self.backend.char_width
                grid_height = self.backend.rows * self.backend.char_height
                
                offset_x = (view_width - grid_width) / 2.0
                offset_y = (view_height - grid_height) / 2.0
                
                # Use C++ rendering
                self._render_with_cpp(rect, offset_x, offset_y)
            
            def _render_with_cpp(self, rect, offset_x: float, offset_y: float):
                """
                Render using C++ implementation.
                
                This method calls the C++ render_frame() function with all necessary
                parameters. The C++ implementation provides direct CoreGraphics/CoreText
                API access for improved performance.
                
                Args:
                    rect: NSRect indicating the region that needs to be redrawn
                    offset_x: Horizontal centering offset in pixels
                    offset_y: Vertical centering offset in pixels
                """
                # Get the CoreGraphics context
                context = Cocoa.NSGraphicsContext.currentContext().CGContext()
                
                # Convert CGContextRef to integer pointer for C++
                # PyObjC wraps CoreFoundation pointers, we need the raw pointer value
                # The C++ function expects unsigned long long (pointer as integer)
                if hasattr(context, '__c_void_p__'):
                    # PyObjC provides __c_void_p__() to get the raw pointer
                    context_ptr = context.__c_void_p__().value
                else:
                    # Fallback: try to convert directly to int
                    context_ptr = int(context)
                
                # Convert NSRect to tuple (x, y, width, height) for C++
                # NSRect is a PyObjC structure, C++ expects a simple tuple
                dirty_rect = (
                    float(rect.origin.x),
                    float(rect.origin.y),
                    float(rect.size.width),
                    float(rect.size.height)
                )
                
                # Get marked text if present
                marked_text = getattr(self, 'marked_text', None) or ""
                
                # Get selected range within marked text (for IME)
                selected_range = getattr(self, 'selected_range', None)
                if selected_range is not None:
                    selected_range_location = int(selected_range.location)
                    selected_range_length = int(selected_range.length)
                else:
                    selected_range_location = 0
                    selected_range_length = 0
                
                # Call C++ render_frame() function
                self.backend._cpp_renderer.render_frame(
                    context_ptr,
                    self.backend.grid,
                    self.backend.color_pairs,
                    dirty_rect,
                    self.backend.char_width,
                    self.backend.char_height,
                    self.backend.rows,
                    self.backend.cols,
                    offset_x,
                    offset_y,
                    self.backend.cursor_visible,
                    self.backend.cursor_row,
                    self.backend.cursor_col,
                    marked_text,
                    selected_range_location,
                    selected_range_length,
                    self.backend.font_ascent,  # Add font_ascent for baseline positioning
                    self.backend.font_names,   # Pass font list to C++ renderer (includes cascade fonts)
                    self.backend.font_size     # Pass font size to C++ renderer
                )
            
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
            
            def canBecomeKeyView(self):
                """
                Indicate that this view can become the key view.
                
                This method must return True for the view to receive keyboard events
                in the responder chain. Without this, even if the view accepts first
                responder, it won't receive keyDown_ events.
                
                Returns:
                    bool: True to allow becoming key view
                """
                return True
            
            @objc.python_method
            def _python_keyDown(self, event):
                """Python implementation of keyDown_ logic."""
                # Check if IME composition is currently active
                has_composition = self.hasMarkedText()
                
                if has_composition:
                    # During IME composition, pass directly to IME system
                    # Don't deliver KeyEvents to application during composition
                    self.interpretKeyEvents_([event])
                    return
                
                # No composition - normal key handling
                # First, translate to KeyEvent and deliver to application
                key_event = self.backend._translate_event(event)
                
                if key_event:
                    # Deliver KeyEvent to application (callback always set)
                    try:
                        consumed = self.backend.event_callback.on_key_event(key_event)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        consumed = False
                    
                    if consumed:
                        # Application consumed the key - don't pass to IME system
                        return
                
                # Key not consumed - pass to IME system for character input
                # This allows IME composition to start
                self.interpretKeyEvents_([event])
            
            def keyDown_(self, event):
                """
                Handle key down event from macOS.
                
                This method is called by macOS when a key is pressed. It handles
                both regular keyboard input and IME composition.
                
                Flow:
                1. If IME composition is active, pass directly to interpretKeyEvents_
                2. Otherwise, translate to KeyEvent and deliver to application
                3. If application doesn't consume it, call interpretKeyEvents_
                
                This allows:
                - IME composition to work without interference
                - Application key bindings to work when not composing
                - Character input to work when keys aren't consumed
                
                Args:
                    event: NSEvent from macOS event system
                """
                
                self._python_keyDown(event)
            
            def inputContext(self):
                """
                Return the text input context for this view.
                
                This method is called by macOS to get the NSTextInputContext for
                handling IME input. We return our custom input context that was
                created in initWithFrame_backend_.
                
                Returns:
                    NSTextInputContext: The input context for IME support
                """
                return self._input_context
            
            def becomeFirstResponder(self):
                """
                Called when the view becomes the first responder (receives focus).
                
                This method activates the NSTextInputContext for the view, which is
                required for IME (Input Method Editor) support. Without activating
                the input context, the IME system cannot communicate with the view.
                
                Returns:
                    bool: True if the view successfully became first responder
                """
                # Call superclass implementation
                result = objc.super(TTKView, self).becomeFirstResponder()
                
                if result:
                    # Activate the text input context for IME support
                    # This is critical - without this, IME will not work
                    input_context = self.inputContext()
                    if input_context:
                        input_context.activate()
                
                return result
            
            def resignFirstResponder(self):
                """
                Called when the view is about to lose first responder status.
                
                This method deactivates the NSTextInputContext and clears any
                active IME composition state.
                
                Returns:
                    bool: True if the view successfully resigned first responder
                """
                # Deactivate the text input context
                input_context = self.inputContext()
                if input_context:
                    input_context.deactivate()
                
                # Clear any active composition
                if self.hasMarkedText():
                    self.unmarkText()
                
                # Call superclass implementation
                return objc.super(TTKView, self).resignFirstResponder()
            
            # NSTextInputClient protocol methods
            # These methods are required for proper text input handling on macOS
            # and enable the callback-based event system with CharEvent generation
            
            def hasMarkedText(self) -> bool:
                """
                Check if there is marked text (IME composition in progress).
                
                This is part of the NSTextInputClient protocol. Returns True if
                there is active composition text (marked text) from the IME.
                
                The marked_range.location is set to NSNotFound when there is no
                composition, and to a valid location (typically 0) when composition
                is active.
                
                Returns:
                    bool: True if there is active composition text, False otherwise
                """
                return self.marked_range.location != Cocoa.NSNotFound
            
            def markedRange(self):
                """
                Get the range of marked text (IME composition).
                
                This is part of the NSTextInputClient protocol. Returns the current
                marked_range which indicates the range of composition text.
                
                When there is no composition, marked_range.location is NSNotFound.
                When composition is active, marked_range contains the location and
                length of the composition text.
                
                Returns:
                    NSRange: The current marked text range
                """
                return self.marked_range
            
            def selectedRange(self):
                """
                Get the range of selected text.
                
                This is part of the NSTextInputClient protocol. Returns the current
                selected_range which indicates the selection within the composition
                text or document.
                
                For TFM, we track the selection within the composition text during
                IME input. When there is no composition, this typically returns a
                zero-length range at the cursor position.
                
                Returns:
                    NSRange: The current selected text range
                """
                return self.selected_range
            
            def validAttributesForMarkedText(self):
                """
                Get valid attributes for marked text (IME composition).
                
                This is part of the NSTextInputClient protocol. Returns an array
                of attribute names that the application supports for marked text.
                
                For basic IME support, we return an empty array to indicate that
                we don't require any special attributes for marked text. macOS
                will use default attributes (underline, highlighting) for the
                composition text.
                
                Returns:
                    NSArray: Empty array (basic support without custom attributes)
                """
                return []
            
            def setMarkedText_selectedRange_replacementRange_(self, string, selected_range, replacement_range):
                """
                Handle composition text updates from IME.
                
                This method is called repeatedly as the user types with IME active.
                We track the composition state and trigger a redraw to display the
                marked text with visual feedback (underline, highlighted background).
                
                This is part of the NSTextInputClient protocol and is called by
                macOS during IME composition to update the marked (composition) text.
                
                Args:
                    string: NSString or NSAttributedString containing composition text
                    selected_range: NSRange indicating selected portion within composition
                    replacement_range: NSRange indicating text to replace (usually NSNotFound)
                """
                
                # Extract plain text if NSAttributedString
                if hasattr(string, 'string'):
                    self.marked_text = str(string.string())
                else:
                    self.marked_text = str(string)
                
                # Update marked range
                if len(self.marked_text) > 0:
                    self.marked_range = Cocoa.NSMakeRange(0, len(self.marked_text))
                else:
                    self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)
                
                # Store selected range within composition
                self.selected_range = selected_range
                
                # Trigger redraw to show marked text
                self.setNeedsDisplay_(True)
            
            def unmarkText(self):
                """
                Cancel composition without committing.
                
                This method is called when:
                1. User presses Escape during composition
                2. Focus changes while composition is active
                3. Dialog closes with active composition
                
                This is part of the NSTextInputClient protocol and clears all
                composition state without generating any CharEvent.
                """
                self.marked_text = ""
                self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)
                self.selected_range = Cocoa.NSMakeRange(0, 0)
                
                # Trigger redraw to clear marked text display
                self.setNeedsDisplay_(True)
            
            def insertText_replacementRange_(self, string, replacement_range):
                """
                Handle character input from macOS text input system.
                
                This method is called by macOS when a key event produces a character
                (after keyDown: was not consumed). It extracts the character from
                the NSString and generates a CharEvent for each character, delivering
                them via the on_char_event callback.
                
                This method is also called when IME composition is committed. In that
                case, we clear the marked text state before generating CharEvent.
                
                This is the second part of the callback-based event system flow:
                1. keyDown: delivers KeyEvent
                2. If not consumed, interpretKeyEvents: is called
                3. macOS translates the key to a character (or commits IME composition)
                4. insertText:replacementRange: is called with the character(s)
                5. Clear marked text state (if IME was active)
                6. Generate CharEvent and deliver via on_char_event
                
                Args:
                    string: NSString or NSAttributedString containing the character(s) to insert
                    replacement_range: NSRange indicating text to replace (usually NSNotFound for append)
                """
                # Clear marked text state (IME composition is being committed)
                self.marked_text = ""
                self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)
                self.selected_range = Cocoa.NSMakeRange(0, 0)
                
                # Trigger redraw to clear marked text display
                self.setNeedsDisplay_(True)
                
                # Extract plain text if NSAttributedString
                if hasattr(string, 'string'):
                    text = str(string.string())
                else:
                    text = str(string)
                
                if not text or len(text) == 0:
                    return
                
                # Import CharEvent here to avoid circular import
                from ttk.input_event import CharEvent
                
                # Create CharEvent for each character
                for char in text:
                    char_event = CharEvent(char=char)
                    
                    # Deliver CharEvent to application (callback always set)
                    self.backend.event_callback.on_char_event(char_event)
            
            def firstRectForCharacterRange_actualRange_(self, char_range, actual_range):
                """
                Provide screen rectangle for composition text positioning.
                
                This method tells macOS where to display the composition text and
                candidate window. We return the screen coordinates of the current
                cursor position.
                
                This is part of the NSTextInputClient protocol and is called by
                macOS to determine where to position the IME composition overlay
                and candidate selection window.
                
                The method performs the following steps:
                1. Get cursor position from backend (cursor_row, cursor_col)
                2. Convert to pixel coordinates using char_width and char_height
                3. Apply coordinate system transformation (TTK to CoreGraphics)
                4. Create NSRect at cursor position with character dimensions
                5. Convert from view coordinates to screen coordinates
                6. Fill actual_range parameter if provided
                7. Return screen rectangle
                
                Coordinate System Transformation:
                    TTK uses top-left origin where (0, 0) is at the top-left corner
                    and row increases downward. CoreGraphics uses bottom-left origin
                    where (0, 0) is at the bottom-left corner and y increases upward.
                    
                    Transformation formula:
                        x_pixel = col * char_width
                        y_pixel = (rows - row - 1) * char_height
                
                Args:
                    char_range: NSRange indicating requested character range
                    actual_range: Pointer to NSRange to fill with actual range (can be NULL/None)
                
                Returns:
                    NSRect in screen coordinates where composition should appear
                """
                try:
                    # Get cursor position from backend
                    # The backend tracks the current text widget's cursor position
                    cursor_row = getattr(self.backend, 'cursor_row', 0)
                    cursor_col = getattr(self.backend, 'cursor_col', 0)
                    
                    # Debug: Print cursor position
                    # Convert to pixel coordinates (TTK to CoreGraphics)
                    # TTK: (0, 0) is top-left, row increases downward
                    # CoreGraphics: (0, 0) is bottom-left, y increases upward
                    x_pixel = cursor_col * self.backend.char_width
                    y_pixel = (self.backend.rows - cursor_row - 1) * self.backend.char_height
                    
                    # Create rect at cursor position with character dimensions
                    # This rect represents where the first character of composition will appear
                    rect = Cocoa.NSMakeRect(
                        x_pixel,
                        y_pixel,
                        self.backend.char_width,
                        self.backend.char_height
                    )
                    
                    # Convert from view coordinates to screen coordinates
                    # Step 1: Convert from view coordinates to window coordinates
                    # Pass None as the second argument to convert to window coordinates
                    window_rect = self.convertRect_toView_(rect, None)
                    
                    # Step 2: Convert from window coordinates to screen coordinates
                    # Check if window exists before conversion
                    window = self.window()
                    if window is not None:
                        screen_rect = window.convertRectToScreen_(window_rect)
                    else:
                        # No window - return zero rect at origin
                        # This shouldn't happen in normal operation, but provides a fallback
                        screen_rect = Cocoa.NSMakeRect(0, 0, 0, 0)
                    
                    # Fill actual_range if provided
                    # actual_range is a pointer that macOS may provide to receive the
                    # actual range we're returning information for
                    # Note: In PyObjC, output parameters can be tricky. We try to set it
                    # but catch any errors since it's optional.
                    if actual_range is not None:
                        try:
                            # Try to set the actual range
                            # PyObjC should handle the pointer conversion automatically
                            actual_range[0] = char_range
                        except (TypeError, AttributeError):
                            # If setting fails, it's okay - actual_range is optional
                            # macOS will use the char_range parameter instead
                            pass
                    
                    return screen_rect
                except Exception:
                    # If anything goes wrong, return a zero rect at origin
                    # This prevents IME from crashing but may position the candidate window incorrectly
                    return Cocoa.NSMakeRect(0, 0, 0, 0)
            
            def attributedSubstringForProposedRange_actualRange_(self, proposed_range, actual_range):
                """
                Provide attributed string for font information.
                
                This method tells macOS what font to use for composition text.
                We return an attributed string with our application font so the
                IME composition matches our text size.
                
                This is part of the NSTextInputClient protocol and is called by
                macOS to determine what font and text attributes to use when
                rendering the IME composition overlay.
                
                The method performs the following steps:
                1. Check if backend.font exists
                2. Create attributes dictionary with NSFontAttributeName set to backend.font
                3. Create NSAttributedString with single space character and attributes
                4. Fill actual_range parameter if provided
                5. Return attributed string (or None if font is not available)
                
                Args:
                    proposed_range: NSRange indicating requested range
                    actual_range: Pointer to NSRange to fill with actual range (can be NULL/None)
                
                Returns:
                    NSAttributedString with font information, or None if font is not available
                """
                # Check if backend.font exists
                if not hasattr(self.backend, 'font') or self.backend.font is None:
                    # No font available - return None
                    # macOS will use default system font for composition
                    print("Warning: IME font information requested but backend.font is not available")
                    return None
                
                # Create attributes dictionary with our font
                # Use a single space character as placeholder
                attrs = {
                    Cocoa.NSFontAttributeName: self.backend.font
                }
                
                # Create NSAttributedString with font information
                attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
                    " ",
                    attrs
                )
                
                # Fill actual_range if provided
                # actual_range is a pointer that macOS may provide to receive the
                # actual range we're returning information for
                if actual_range is not None:
                    # We're returning information for a single character (the space)
                    actual_range[0] = Cocoa.NSMakeRange(0, 1)
                
                return attr_string
            
            def doCommandBySelector_(self, selector):
                """
                Handle command selectors from the text input system.
                
                This method is called by macOS when special keys are pressed that
                don't produce text (arrow keys, delete, function keys, etc.).
                
                For TFM, we need to translate these into KeyEvents and deliver them
                to the application for handling navigation and other commands.
                
                This is part of the NSTextInputClient protocol.
                
                Args:
                    selector: SEL (selector) for the command to execute
                """
                # Get the current event to translate to KeyEvent
                event = Cocoa.NSApp.currentEvent()
                if event and event.type() == Cocoa.NSKeyDown:
                    # Translate to KeyEvent
                    key_event = self.backend._translate_event(event)
                    
                    if key_event:
                        # Deliver KeyEvent to application (callback always set)
                        self.backend.event_callback.on_key_event(key_event)
            
            def characterIndexForPoint_(self, point):
                """
                Return character index for a given point in the view.
                
                This method is called by macOS to determine which character is at
                a given screen position. For TFM, we don't support this feature
                (clicking to position cursor in composition text), so we return
                NSNotFound.
                
                This is part of the NSTextInputClient protocol and is required for
                proper IME support.
                
                Args:
                    point: NSPoint in view coordinates
                
                Returns:
                    NSUInteger: Character index, or NSNotFound if not supported
                """
                # We don't support clicking to position cursor in composition text
                return Cocoa.NSNotFound
            
            # Mouse event handlers
            
            def acceptsFirstMouse_(self, event):
                """
                Allow the view to receive mouse events even when not the key window.
                
                This method returns True to allow mouse clicks to be processed
                immediately, even if the window is not currently active.
                
                Args:
                    event: NSEvent for the mouse down event
                
                Returns:
                    bool: True to accept first mouse click
                """
                return True
            
            def mouseDown_(self, event):
                """
                Handle left mouse button down event.
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def mouseUp_(self, event):
                """
                Handle left mouse button up event.
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def rightMouseDown_(self, event):
                """
                Handle right mouse button down event.
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def rightMouseUp_(self, event):
                """
                Handle right mouse button up event.
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def otherMouseDown_(self, event):
                """
                Handle other mouse button (middle button) down event.
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def otherMouseUp_(self, event):
                """
                Handle other mouse button (middle button) up event.
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def mouseMoved_(self, event):
                """
                Handle mouse moved event (no button pressed).
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def mouseDragged_(self, event):
                """
                Handle mouse dragged event (left button pressed).
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def rightMouseDragged_(self, event):
                """
                Handle mouse dragged event (right button pressed).
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def otherMouseDragged_(self, event):
                """
                Handle mouse dragged event (other button pressed).
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)
            
            def scrollWheel_(self, event):
                """
                Handle scroll wheel event.
                
                Args:
                    event: NSEvent from macOS event system
                """
                self.backend._handle_mouse_event(event)

else:
    # Provide a dummy class when PyObjC is not available
    class TTKView:
        """Dummy TTKView class when PyObjC is not available."""
        pass
