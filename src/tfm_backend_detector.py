#!/usr/bin/env python3
"""
TFM Backend Detector

Provides utilities to detect which backend TFM is currently running with.
This is useful for configuration that needs to adapt based on the actual
runtime backend rather than just the preferred backend setting.
"""

import sys
import os


# Cache the backend detection result to avoid repeated checks
_cached_backend = None


def is_desktop_mode():
    """
    Detect if TFM is running in desktop mode (CoreGraphics backend).
    
    This function checks multiple indicators to determine if TFM is running
    with the CoreGraphics backend (desktop mode) or the curses backend
    (terminal mode).
    
    Detection methods (in order of priority):
    1. Check TFM_BACKEND environment variable (set by TFM at runtime)
    2. Check command-line arguments for --backend or --desktop flags
    3. Check if CoreGraphics backend modules are loaded
    4. Default to terminal mode (curses)
    
    Note: Results are cached after first detection for performance.
    
    Returns:
        bool: True if running in desktop mode, False if running in terminal mode
    
    Examples:
        >>> if is_desktop_mode():
        ...     editor = 'code'
        ... else:
        ...     editor = 'vim'
    """
    global _cached_backend
    
    # Return cached result if available
    if _cached_backend is not None:
        return _cached_backend
    
    # Method 1: Check environment variable (most reliable if set by TFM)
    backend_env = os.environ.get('TFM_BACKEND')
    if backend_env:
        _cached_backend = (backend_env == 'coregraphics')
        return _cached_backend
    
    # Method 2: Check command-line arguments
    if '--backend' in sys.argv:
        try:
            backend_idx = sys.argv.index('--backend')
            if backend_idx + 1 < len(sys.argv):
                _cached_backend = (sys.argv[backend_idx + 1] == 'coregraphics')
                return _cached_backend
        except (ValueError, IndexError):
            pass
    
    if '--desktop' in sys.argv:
        _cached_backend = True
        return _cached_backend
    
    # Method 3: Check if CoreGraphics backend modules are loaded
    # This indicates the backend is actually running
    if 'ttk.backends.coregraphics_backend' in sys.modules:
        _cached_backend = True
        return _cached_backend
    
    # Default to terminal mode (don't cache this default)
    # Note: We don't check PREFERRED_BACKEND here to avoid circular imports
    # when this is called from _config.py during config loading
    return False


def get_backend_name():
    """
    Get the name of the currently running backend.
    
    Returns:
        str: 'coregraphics' for desktop mode, 'curses' for terminal mode
    
    Examples:
        >>> backend = get_backend_name()
        >>> print(f"Running with {backend} backend")
    """
    return 'coregraphics' if is_desktop_mode() else 'curses'
