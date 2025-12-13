#!/usr/bin/env python3
"""
TFM Backend Selector

Selects the appropriate TTK backend based on command-line arguments,
configuration, and platform availability.
"""

import platform
import sys


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
    # Determine requested backend from arguments or configuration
    backend_name = _get_requested_backend(args)
    
    # Validate backend availability and fall back if necessary
    backend_name = _validate_backend_availability(backend_name)
    
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
        if hasattr(config, 'PREFERRED_BACKEND'):
            return config.PREFERRED_BACKEND
    except Exception as e:
        # If config loading fails, just use default
        print(f"Warning: Could not load configuration: {e}", file=sys.stderr)
    
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
            print("Error: CoreGraphics backend is only available on macOS", file=sys.stderr)
            print("Falling back to curses backend", file=sys.stderr)
            return 'curses'
        
        # Check if PyObjC is available
        try:
            import objc
        except ImportError:
            print("Error: PyObjC is required for CoreGraphics backend", file=sys.stderr)
            print("Install with: pip install pyobjc-framework-Cocoa", file=sys.stderr)
            print("Falling back to curses backend", file=sys.stderr)
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
        - font_name: Font to use for rendering
        - font_size: Font size in points
        - rows: Initial window height in character rows
        - cols: Initial window width in character columns
        
        Options can be customized via user configuration (DESKTOP_FONT_NAME,
        DESKTOP_FONT_SIZE, DESKTOP_WINDOW_WIDTH, DESKTOP_WINDOW_HEIGHT).
        
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
        font_name = 'Menlo'
        font_size = 14
        window_width = 1200
        window_height = 800
        
        # Try to load custom options from configuration
        try:
            from tfm_config import get_config
            config = get_config()
            
            # Override with user configuration if available
            if hasattr(config, 'DESKTOP_FONT_NAME'):
                font_name = config.DESKTOP_FONT_NAME
            
            if hasattr(config, 'DESKTOP_FONT_SIZE'):
                font_size = config.DESKTOP_FONT_SIZE
            
            if hasattr(config, 'DESKTOP_WINDOW_WIDTH'):
                window_width = config.DESKTOP_WINDOW_WIDTH
            
            if hasattr(config, 'DESKTOP_WINDOW_HEIGHT'):
                window_height = config.DESKTOP_WINDOW_HEIGHT
        
        except Exception as e:
            # If config loading fails, just use defaults
            print(f"Warning: Could not load desktop mode configuration: {e}", file=sys.stderr)
            print("Using default desktop mode options", file=sys.stderr)
        
        # Calculate approximate character dimensions from pixel dimensions
        # These are rough estimates - the backend will calculate exact dimensions
        # based on the actual font metrics
        char_width = font_size * 0.6  # Approximate width for monospace fonts
        char_height = font_size * 1.2  # Approximate height with line spacing
        
        cols = int(window_width / char_width)
        rows = int(window_height / char_height)
        
        # Return options that match CoreGraphicsBackend.__init__ parameters
        return {
            'window_title': 'TFM - TUI File Manager',
            'font_name': font_name,
            'font_size': font_size,
            'rows': rows,
            'cols': cols,
        }
    
    # Curses backend needs no special options
    return {}
