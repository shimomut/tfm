#!/usr/bin/env python3
"""
TFM Wide Character Utilities - Compatibility Shim

This module provides TFM-specific wrappers around TTK's wide character utilities.
All core wide character detection and manipulation functions have been moved to
ttk.wide_char_utils for reuse across TTK-based applications.

This shim provides:
1. Configuration integration - initialize_from_config() reads TFM config
2. Backend-specific mode setting - set_unicode_mode_for_backend() handles backend names

For direct access to wide character utilities, import from ttk.wide_char_utils:
    from ttk.wide_char_utils import get_display_width, truncate_to_width, etc.

Migration Status:
- Core functions moved to TTK: ✓
- TFM files updated to import from TTK: ✓
- This shim provides only TFM-specific wrappers: ✓
"""

from ttk.wide_char_utils import initialize_from_config as ttk_initialize


def initialize_from_config():
    """
    Initialize wide character utilities from TFM configuration.
    
    This is a TFM-specific wrapper that reads configuration values and
    passes them to TTK's initialize_from_config() function.
    
    Configuration values read from tfm_config:
    - UNICODE_MODE: 'full', 'basic', or 'ascii'
    """
    from tfm_config import config_manager
    
    # Get configuration value
    unicode_mode = getattr(config_manager.config, 'UNICODE_MODE', 'full')
    
    # Call TTK's initialize_from_config with explicit parameter
    ttk_initialize(unicode_mode=unicode_mode)


def set_unicode_mode_for_backend(backend_name):
    """
    Set Unicode mode based on backend name.
    
    This is a TFM-specific function that maps backend names to Unicode modes.
    TTK should not know about specific backend names like 'coregraphics' or 'curses'.
    
    Desktop backends (CoreGraphics) always use full Unicode support.
    Terminal backends (Curses) respect the configured Unicode mode.
    
    Args:
        backend_name: Name of the backend ('coregraphics', 'curses', etc.)
    """
    from tfm_config import config_manager
    
    # Desktop backends always use full Unicode
    if backend_name == 'coregraphics':
        ttk_initialize(unicode_mode='full')
    else:
        # Terminal backends use configured mode
        unicode_mode = getattr(config_manager.config, 'UNICODE_MODE', 'full')
        ttk_initialize(unicode_mode=unicode_mode)


# Note: All other functions are available by importing directly from ttk.wide_char_utils
# Example:
#   from ttk.wide_char_utils import get_display_width, truncate_to_width
#
# This shim only provides TFM-specific configuration wrappers.
