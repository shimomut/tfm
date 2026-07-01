"""
TTK utility functions.

This module provides helper functions for platform detection, color conversion,
and parameter validation.
"""

from ttk.utils.utils import (
    get_recommended_backend,
    rgb_to_normalized,
    normalized_to_rgb,
    rgb_to_hex,
    hex_to_rgb,
    validate_rgb,
    validate_color_pair_id,
    validate_coordinates,
    validate_dimensions,
    clamp,
    clamp_rgb,
)

__all__ = [
    'get_recommended_backend',
    'rgb_to_normalized',
    'normalized_to_rgb',
    'rgb_to_hex',
    'hex_to_rgb',
    'validate_rgb',
    'validate_color_pair_id',
    'validate_coordinates',
    'validate_dimensions',
    'clamp',
    'clamp_rgb',
]
