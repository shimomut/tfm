#!/usr/bin/env python3
"""
Wide Character Utilities for TFM (Compatibility Shim)

This module provides backward compatibility by re-exporting all functions from
the TTK wide_char_utils module. The wide character utilities have been moved to
TTK since they are a common utility feature for all TTK-based applications.

New code should import directly from ttk.wide_char_utils instead of this module.

Migration Note:
    Old: from tfm_wide_char_utils import get_display_width
    New: from ttk.wide_char_utils import get_display_width
"""

import sys
import os

# Add TTK to path if needed
ttk_path = os.path.join(os.path.dirname(__file__), '..', 'ttk')
if ttk_path not in sys.path:
    sys.path.insert(0, ttk_path)

# Re-export all public functions from TTK
from ttk.wide_char_utils import (
    # Core functions
    _is_wide_character,
    safe_is_wide_character,
    get_display_width,
    safe_get_display_width,
    truncate_to_width,
    safe_truncate_to_width,
    pad_to_width,
    safe_pad_to_width,
    split_at_width,
    safe_split_at_width,
    
    # Terminal detection
    detect_terminal_unicode_support,
    get_unicode_handling_mode,
    create_fallback_functions,
    
    # Configuration
    set_unicode_mode,
    set_unicode_mode_for_backend,
    get_current_unicode_mode,
    get_safe_functions,
    set_fallback_char,
    get_fallback_char,
    should_show_warnings,
    
    # Cache management
    clear_display_width_cache,
    get_cache_info,
    optimize_for_ascii_only,
)

# TFM-specific initialization wrapper
def initialize_from_config():
    """
    Initialize Unicode handling mode from TFM configuration.
    
    This function wraps the TTK initialize_from_config() to provide
    TFM-specific configuration loading.
    """
    try:
        from tfm_config import get_config
        from ttk.wide_char_utils import initialize_from_config as ttk_init
        
        config = get_config()
        
        # Extract configuration values
        unicode_mode = getattr(config, 'UNICODE_MODE', None)
        force_fallback = getattr(config, 'UNICODE_FORCE_FALLBACK', False)
        show_warnings = getattr(config, 'UNICODE_WARNINGS', True)
        terminal_detection = getattr(config, 'UNICODE_TERMINAL_DETECTION', True)
        fallback_char = getattr(config, 'UNICODE_FALLBACK_CHAR', '?')
        
        # Pass configuration values as arguments
        ttk_init(
            unicode_mode=unicode_mode,
            force_fallback=force_fallback,
            show_warnings=show_warnings,
            terminal_detection=terminal_detection,
            fallback_char=fallback_char
        )
        
    except ImportError:
        # Config system not available, keep current mode
        pass
    except Exception as e:
        import warnings
        warnings.warn(f"Error loading Unicode settings from TFM config: {e}. Keeping current mode.", UserWarning)


__all__ = [
    # Core functions
    '_is_wide_character',
    'safe_is_wide_character',
    'get_display_width',
    'safe_get_display_width',
    'truncate_to_width',
    'safe_truncate_to_width',
    'pad_to_width',
    'safe_pad_to_width',
    'split_at_width',
    'safe_split_at_width',
    
    # Terminal detection
    'detect_terminal_unicode_support',
    'get_unicode_handling_mode',
    'create_fallback_functions',
    
    # Configuration
    'set_unicode_mode',
    'set_unicode_mode_for_backend',
    'get_current_unicode_mode',
    'get_safe_functions',
    'initialize_from_config',
    'set_fallback_char',
    'get_fallback_char',
    'should_show_warnings',
    
    # Cache management
    'clear_display_width_cache',
    'get_cache_info',
    'optimize_for_ascii_only',
]
