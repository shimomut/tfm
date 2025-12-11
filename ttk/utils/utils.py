"""
Utility functions for the TTK library.

This module provides helper functions for platform detection, color conversion,
and parameter validation.
"""

import platform
from typing import Tuple


def get_recommended_backend() -> str:
    """
    Get the recommended rendering backend for the current platform.
    
    Returns:
        str: 'metal' for macOS, 'curses' for all other platforms
        
    Example:
        >>> backend_name = get_recommended_backend()
        >>> if backend_name == 'metal':
        ...     from ttk.backends.metal_backend import MetalBackend
        ...     renderer = MetalBackend()
        ... else:
        ...     from ttk.backends.curses_backend import CursesBackend
        ...     renderer = CursesBackend()
    """
    if platform.system() == 'Darwin':
        return 'metal'
    return 'curses'


def rgb_to_normalized(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """
    Convert RGB color values from 0-255 range to normalized 0.0-1.0 range.
    
    This is useful for graphics APIs that expect normalized color values.
    
    Args:
        rgb: Tuple of (R, G, B) values in range 0-255
        
    Returns:
        Tuple of (R, G, B) values in range 0.0-1.0
        
    Raises:
        ValueError: If any RGB component is outside 0-255 range
        
    Example:
        >>> rgb_to_normalized((255, 128, 0))
        (1.0, 0.5019607843137255, 0.0)
    """
    r, g, b = rgb
    validate_rgb(rgb)
    return (r / 255.0, g / 255.0, b / 255.0)


def normalized_to_rgb(normalized: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """
    Convert normalized color values from 0.0-1.0 range to RGB 0-255 range.
    
    Args:
        normalized: Tuple of (R, G, B) values in range 0.0-1.0
        
    Returns:
        Tuple of (R, G, B) values in range 0-255
        
    Raises:
        ValueError: If any component is outside 0.0-1.0 range
        
    Example:
        >>> normalized_to_rgb((1.0, 0.5, 0.0))
        (255, 127, 0)
    """
    r, g, b = normalized
    if not (0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0):
        raise ValueError(f"Normalized RGB values must be in range 0.0-1.0, got ({r}, {g}, {b})")
    return (int(r * 255), int(g * 255), int(b * 255))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Convert RGB color to hexadecimal string representation.
    
    Args:
        rgb: Tuple of (R, G, B) values in range 0-255
        
    Returns:
        Hexadecimal color string in format '#RRGGBB'
        
    Raises:
        ValueError: If any RGB component is outside 0-255 range
        
    Example:
        >>> rgb_to_hex((255, 128, 0))
        '#FF8000'
    """
    r, g, b = rgb
    validate_rgb(rgb)
    return f'#{r:02X}{g:02X}{b:02X}'


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hexadecimal color string to RGB tuple.
    
    Args:
        hex_color: Hexadecimal color string in format '#RRGGBB' or 'RRGGBB'
        
    Returns:
        Tuple of (R, G, B) values in range 0-255
        
    Raises:
        ValueError: If hex_color is not a valid hexadecimal color string
        
    Example:
        >>> hex_to_rgb('#FF8000')
        (255, 128, 0)
        >>> hex_to_rgb('FF8000')
        (255, 128, 0)
    """
    # Remove '#' prefix if present
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) != 6:
        raise ValueError(f"Hex color must be 6 characters (RRGGBB), got '{hex_color}'")
    
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError as e:
        raise ValueError(f"Invalid hexadecimal color string '{hex_color}': {e}")


def validate_rgb(rgb: Tuple[int, int, int]) -> None:
    """
    Validate that RGB color values are in the valid range 0-255.
    
    Args:
        rgb: Tuple of (R, G, B) values to validate
        
    Raises:
        ValueError: If any RGB component is outside 0-255 range
        TypeError: If rgb is not a tuple of three integers
        
    Example:
        >>> validate_rgb((255, 128, 0))  # Valid, no exception
        >>> validate_rgb((256, 0, 0))  # Raises ValueError
        Traceback (most recent call last):
        ...
        ValueError: RGB values must be in range 0-255, got (256, 0, 0)
    """
    if not isinstance(rgb, tuple) or len(rgb) != 3:
        raise TypeError(f"RGB must be a tuple of 3 integers, got {type(rgb).__name__}")
    
    r, g, b = rgb
    
    if not all(isinstance(c, int) for c in rgb):
        raise TypeError(f"RGB components must be integers, got ({type(r).__name__}, {type(g).__name__}, {type(b).__name__})")
    
    if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
        raise ValueError(f"RGB values must be in range 0-255, got ({r}, {g}, {b})")


def validate_color_pair_id(pair_id: int) -> None:
    """
    Validate that a color pair ID is in the valid range.
    
    Color pair IDs must be in range 0-255, where 0 is reserved for default colors.
    
    Args:
        pair_id: Color pair ID to validate
        
    Raises:
        ValueError: If pair_id is outside 0-255 range
        TypeError: If pair_id is not an integer
        
    Example:
        >>> validate_color_pair_id(42)  # Valid, no exception
        >>> validate_color_pair_id(256)  # Raises ValueError
        Traceback (most recent call last):
        ...
        ValueError: Color pair ID must be in range 0-255, got 256
    """
    if not isinstance(pair_id, int):
        raise TypeError(f"Color pair ID must be an integer, got {type(pair_id).__name__}")
    
    if not (0 <= pair_id <= 255):
        raise ValueError(f"Color pair ID must be in range 0-255, got {pair_id}")


def validate_coordinates(row: int, col: int) -> None:
    """
    Validate that coordinates are non-negative integers.
    
    Args:
        row: Row coordinate to validate
        col: Column coordinate to validate
        
    Raises:
        ValueError: If row or col is negative
        TypeError: If row or col is not an integer
        
    Example:
        >>> validate_coordinates(10, 20)  # Valid, no exception
        >>> validate_coordinates(-1, 20)  # Raises ValueError
        Traceback (most recent call last):
        ...
        ValueError: Coordinates must be non-negative, got row=-1, col=20
    """
    if not isinstance(row, int):
        raise TypeError(f"Row must be an integer, got {type(row).__name__}")
    if not isinstance(col, int):
        raise TypeError(f"Column must be an integer, got {type(col).__name__}")
    
    if row < 0 or col < 0:
        raise ValueError(f"Coordinates must be non-negative, got row={row}, col={col}")


def validate_dimensions(width: int, height: int) -> None:
    """
    Validate that dimensions are positive integers.
    
    Args:
        width: Width to validate
        height: Height to validate
        
    Raises:
        ValueError: If width or height is not positive
        TypeError: If width or height is not an integer
        
    Example:
        >>> validate_dimensions(10, 20)  # Valid, no exception
        >>> validate_dimensions(0, 20)  # Raises ValueError
        Traceback (most recent call last):
        ...
        ValueError: Dimensions must be positive, got width=0, height=20
    """
    if not isinstance(width, int):
        raise TypeError(f"Width must be an integer, got {type(width).__name__}")
    if not isinstance(height, int):
        raise TypeError(f"Height must be an integer, got {type(height).__name__}")
    
    if width <= 0 or height <= 0:
        raise ValueError(f"Dimensions must be positive, got width={width}, height={height}")


def clamp(value: int, min_value: int, max_value: int) -> int:
    """
    Clamp a value to be within a specified range.
    
    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Clamped value within [min_value, max_value]
        
    Example:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(-5, 0, 10)
        0
        >>> clamp(15, 0, 10)
        10
    """
    return max(min_value, min(value, max_value))


def clamp_rgb(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """
    Clamp RGB values to valid 0-255 range.
    
    This is useful when performing color calculations that might produce
    out-of-range values.
    
    Args:
        rgb: Tuple of (R, G, B) values (may be outside 0-255 range)
        
    Returns:
        Tuple of (R, G, B) values clamped to 0-255 range
        
    Example:
        >>> clamp_rgb((300, 128, -50))
        (255, 128, 0)
    """
    r, g, b = rgb
    return (clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))
