#!/usr/bin/env python3
"""
TFM Backend Selector

Selects the appropriate TTK backend based on command-line arguments,
configuration, and platform availability.
"""

import platform
import sys
from tfm_log_manager import getLogger

# Module-level logger
logger = getLogger("BackendSel")


def select_backend(args):
    """
    Select appropriate TTK backend based on arguments and platform.
    
    This function determines which TTK backend to use by checking:
    1. Command-line arguments (--backend or --desktop)
    2. User configuration (PREFERRED_BACKEND)
    3. Platform availability (macOS for CoreGraphics)
    4. PyObjC availability (required for CoreGraphics)
    
    Args:
        args: Parsed command-line arguments with optional 'backend' and 'desktop' attributes
    
    Returns:
        Tuple of (backend_name, backend_options) where:
        - backend_name: 'curses' or 'coregraphics'
        - backend_options: Dict of backend-specific configuration options
    
    Examples:
        >>> # Default to curses backend
        >>> backend_name, options = select_backend(args)
        >>> # backend_name == 'curses', options == {}
        
        >>> # Request CoreGraphics backend on macOS
        >>> args.backend = 'coregraphics'
        >>> backend_name, options = select_backend(args)
        >>> # backend_name == 'coregraphics', options == {'window_title': ..., 'font_name': ..., ...}
    """
    import os
    
    # Determine requested backend from arguments or configuration
    backend_name = _get_requested_backend(args)
    
    # Validate backend availability and fall back if necessary
    backend_name = _validate_backend_availability(backend_name)
    
    # Set environment variable so other modules can detect the actual backend
    os.environ['TFM_BACKEND'] = backend_name
    
    # Prepare backend-specific options
    backend_options = _get_backend_options(backend_name, args)
    
    return backend_name, backend_options


def _get_requested_backend(args):
    """
    Determine which backend was requested via arguments or configuration.
    
    Priority order:
    1. --backend command-line argument
    2. --desktop command-line flag (shorthand for coregraphics)
    3. PREFERRED_BACKEND from user configuration
    4. Default to 'curses'
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Requested backend name as string ('curses' or 'coregraphics')
    """
    # Check command-line arguments first
    if hasattr(args, 'backend') and args.backend:
        return args.backend
    
    if hasattr(args, 'desktop') and args.desktop:
        return 'coregraphics'
    
    # Check user configuration
    try:
        from tfm_config import get_config
        config = get_config()
        return config.PREFERRED_BACKEND
    except Exception as e:
        # If config loading fails, just use default
        logger.warning(f"Could not load configuration: {e}")
    
    # Default to curses backend
    return 'curses'


def _validate_backend_availability(backend_name):
    """
    Validate that the requested backend is available on this platform.
    
    Checks:
    - CoreGraphics backend requires macOS (Darwin platform)
    - CoreGraphics backend requires PyObjC to be installed
    
    Falls back to curses backend with informative error messages if
    the requested backend is not available.
    
    Args:
        backend_name: Requested backend name ('curses' or 'coregraphics')
    
    Returns:
        Validated backend name (may fall back to 'curses')
    """
    if backend_name == 'coregraphics':
        # Check if running on macOS
        if platform.system() != 'Darwin':
            logger.error("CoreGraphics backend is only available on macOS")
            logger.info("Falling back to curses backend")
            return 'curses'
        
        # Check if PyObjC is available
        try:
            import objc
        except ImportError:
            logger.error("PyObjC is required for CoreGraphics backend")
            logger.info("Install with: pip install pyobjc-framework-Cocoa")
            logger.info("Falling back to curses backend")
            return 'curses'
    
    return backend_name


def _get_backend_options(backend_name, args):
    """
    Get backend-specific configuration options.
    
    For curses backend:
        Returns empty dict (no special options needed)
    
    For coregraphics backend:
        Returns dict with window configuration:
        - window_title: Application window title
        - font_name: Font to use for rendering (selected from DESKTOP_FONT_NAME list)
        - font_size: Font size in points
        - rows: Initial window height in character rows
        - cols: Initial window width in character columns
        
        Options can be customized via user configuration:
        - DESKTOP_FONT_NAME: String or list of font names (tries in order)
        - DESKTOP_FONT_SIZE: Font size in points
        - DESKTOP_WINDOW_WIDTH: Window width in pixels
        - DESKTOP_WINDOW_HEIGHT: Window height in pixels
        
        Window dimensions in pixels are converted to character dimensions
        using approximate character size calculations based on font size.
    
    Args:
        backend_name: Name of the backend ('curses' or 'coregraphics')
        args: Parsed command-line arguments (for future extensibility)
    
    Returns:
        Dict of backend-specific options
    """
    if backend_name == 'coregraphics':
        # Default CoreGraphics options
        font_names = ['Menlo', 'Monaco', 'Courier']  # Default font list with fallbacks
        font_size = 14
        window_width = 1200
        window_height = 800
        
        # Try to load custom options from configuration
        try:
            from tfm_config import get_config
            config = get_config()
            
            # Support both string (single font) and list (with fallbacks)
            if isinstance(config.DESKTOP_FONT_NAME, str):
                font_names = [config.DESKTOP_FONT_NAME]
            elif isinstance(config.DESKTOP_FONT_NAME, list):
                font_names = config.DESKTOP_FONT_NAME
            
            font_size = config.DESKTOP_FONT_SIZE
            window_width = config.DESKTOP_WINDOW_WIDTH
            window_height = config.DESKTOP_WINDOW_HEIGHT
        
        except Exception as e:
            # If config loading fails, just use defaults
            logger.warning(f"Could not load desktop mode configuration: {e}")
            logger.info("Using default desktop mode options")
        
        # Calculate approximate character dimensions from pixel dimensions
        # These are rough estimates - the backend will calculate exact dimensions
        # based on the actual font metrics
        char_width = font_size * 0.6  # Approximate width for monospace fonts
        char_height = font_size * 1.2  # Approximate height with line spacing
        
        cols = int(window_width / char_width)
        rows = int(window_height / char_height)
        
        # Check if performance logging is enabled via command-line argument
        enable_perf_logging = getattr(args, 'perf_logging', False)
        
        # Return options that match CoreGraphicsBackend.__init__ parameters
        return {
            'window_title': 'TFM - TUI File Manager',
            'font_names': font_names,     # Full list: first=primary, rest=cascade
            'font_size': font_size,
            'rows': rows,
            'cols': cols,
            'frame_autosave_name': 'TFMMainWindow',
            'enable_perf_logging': enable_perf_logging,
        }
    
    # Curses backend needs no special options
    return {}
