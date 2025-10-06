#!/usr/bin/env python3
"""
Wide Character Utilities for TFM

This module provides utilities for handling wide characters (particularly Japanese Zenkaku
characters) in terminal display contexts. It includes functions for calculating display
width, text truncation, padding, and terminal capability detection.

The module addresses layout issues that occur when filenames contain wide Unicode characters
by providing proper display width calculations and text manipulation functions.
"""

import os
import sys
import unicodedata
from typing import Tuple, Optional


def is_wide_character(char: str) -> bool:
    """
    Check if a character is a wide (double-width) character.
    
    Wide characters typically take up 2 display columns in terminal output,
    including most East Asian characters (Chinese, Japanese, Korean).
    
    Args:
        char: A single Unicode character
        
    Returns:
        True if the character is wide (double-width), False otherwise
        
    Examples:
        >>> is_wide_character('A')
        False
        >>> is_wide_character('あ')
        True
        >>> is_wide_character('中')
        True
    """
    if len(char) != 1:
        return False
    
    # Use East Asian Width property from Unicode database
    width = unicodedata.east_asian_width(char)
    # 'F' = Fullwidth, 'W' = Wide
    return width in ('F', 'W')


def get_display_width(text: str) -> int:
    """
    Calculate the display width of a string, accounting for wide characters.
    
    This function properly measures the visual width that text will occupy
    in a terminal, where wide characters take 2 columns and combining
    characters take 0 columns.
    
    Args:
        text: The text string to measure
        
    Returns:
        The display width in terminal columns
        
    Examples:
        >>> get_display_width("hello")
        5
        >>> get_display_width("こんにちは")
        10
        >>> get_display_width("hello世界")
        9
    """
    if not text:
        return 0
    
    width = 0
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Handle combining characters (they don't add width)
        if unicodedata.combining(char):
            # Combining characters don't add to display width
            pass
        elif is_wide_character(char):
            # Wide characters take 2 columns
            width += 2
        else:
            # Regular characters take 1 column
            width += 1
        
        i += 1
    
    return width


def safe_get_display_width(text: str) -> int:
    """
    Safely calculate display width with fallback to character count.
    
    This function provides a safe wrapper around get_display_width() that
    handles Unicode errors gracefully by falling back to character count.
    
    Args:
        text: The text string to measure
        
    Returns:
        The display width in terminal columns, or character count as fallback
    """
    try:
        return get_display_width(text)
    except (UnicodeError, ValueError):
        # Fallback to character count if Unicode processing fails
        return len(text)


def truncate_to_width(text: str, max_width: int, ellipsis: str = "...") -> str:
    """
    Truncate text to fit within max_width display columns, preserving character boundaries.
    
    This function ensures that wide characters are not split and that the resulting
    text fits within the specified display width. If truncation is needed, an ellipsis
    is added to indicate the text was cut off.
    
    Args:
        text: The text string to truncate
        max_width: Maximum display width in terminal columns
        ellipsis: String to append when text is truncated (default: "...")
        
    Returns:
        Truncated text that fits within max_width columns
        
    Examples:
        >>> truncate_to_width("hello world", 8)
        'hello...'
        >>> truncate_to_width("こんにちは", 6)
        'こん...'
        >>> truncate_to_width("short", 10)
        'short'
    """
    if not text:
        return text
    
    current_width = get_display_width(text)
    if current_width <= max_width:
        return text
    
    ellipsis_width = get_display_width(ellipsis)
    if ellipsis_width >= max_width:
        # If ellipsis is too long, truncate it or return empty
        if max_width <= 0:
            return ""
        return ellipsis[:max_width]
    
    target_width = max_width - ellipsis_width
    if target_width <= 0:
        return ellipsis[:max_width]
    
    result = ""
    current_width = 0
    
    for char in text:
        char_width = get_display_width(char)
        if current_width + char_width > target_width:
            break
        result += char
        current_width += char_width
    
    return result + ellipsis


def pad_to_width(text: str, width: int, align: str = 'left', fill_char: str = ' ') -> str:
    """
    Pad text to exact display width, accounting for wide characters.
    
    This function ensures proper column alignment by padding text to a specific
    display width, taking into account that wide characters occupy 2 columns.
    
    Args:
        text: The text string to pad
        width: Target display width in terminal columns
        align: Alignment ('left', 'right', 'center')
        fill_char: Character to use for padding (default: space)
        
    Returns:
        Padded text with exact display width
        
    Examples:
        >>> pad_to_width("hello", 10)
        'hello     '
        >>> pad_to_width("こんにちは", 12)
        'こんにちは  '
        >>> pad_to_width("test", 10, align='right')
        '      test'
    """
    if not text:
        text = ""
    
    current_width = get_display_width(text)
    
    if current_width >= width:
        # Text is already at or exceeds target width
        return text
    
    padding_needed = width - current_width
    fill_width = get_display_width(fill_char)
    
    if fill_width == 0:
        # Can't pad with zero-width characters
        return text
    
    padding_chars = padding_needed // fill_width
    padding = fill_char * padding_chars
    
    if align == 'left':
        return text + padding
    elif align == 'right':
        return padding + text
    elif align == 'center':
        left_padding = padding_chars // 2
        right_padding = padding_chars - left_padding
        return (fill_char * left_padding) + text + (fill_char * right_padding)
    else:
        # Default to left alignment for unknown alignment
        return text + padding


def split_at_width(text: str, width: int) -> Tuple[str, str]:
    """
    Split text at display width boundary, preserving character integrity.
    
    This function splits text at the specified display width without breaking
    wide characters. It's useful for text wrapping in terminal applications.
    
    Args:
        text: The text string to split
        width: Display width at which to split
        
    Returns:
        Tuple of (left_part, right_part) where left_part fits within width
        
    Examples:
        >>> split_at_width("hello world", 6)
        ('hello ', 'world')
        >>> split_at_width("こんにちは世界", 8)
        ('こんにちは', '世界')
    """
    if not text or width <= 0:
        return ("", text)
    
    current_width = 0
    split_index = 0
    
    for i, char in enumerate(text):
        char_width = get_display_width(char)
        if current_width + char_width > width:
            break
        current_width += char_width
        split_index = i + 1
    
    return (text[:split_index], text[split_index:])


def detect_terminal_unicode_support() -> bool:
    """
    Detect if the terminal supports Unicode wide characters properly.
    
    This function attempts to determine if the current terminal environment
    can properly display wide Unicode characters. It checks various environment
    variables and system properties to make this determination.
    
    Returns:
        True if terminal likely supports Unicode wide characters, False otherwise
        
    Note:
        This is a best-effort detection. Some terminals may not be detected
        correctly, so fallback mechanisms should always be available.
    """
    # Check locale settings
    locale_vars = ['LC_ALL', 'LC_CTYPE', 'LANG']
    for var in locale_vars:
        locale_value = os.environ.get(var, '').upper()
        if locale_value:
            # Look for UTF-8 encoding in locale
            if 'UTF-8' in locale_value or 'UTF8' in locale_value:
                return True
            # Some locales might not explicitly mention UTF-8 but support Unicode
            if any(lang in locale_value for lang in ['JA_JP', 'ZH_CN', 'ZH_TW', 'KO_KR']):
                return True
    
    # Check terminal type
    term = os.environ.get('TERM', '').lower()
    if term:
        # Modern terminals that typically support Unicode
        unicode_terminals = [
            'xterm-256color', 'screen-256color', 'tmux-256color',
            'alacritty', 'kitty', 'iterm2', 'gnome-terminal',
            'konsole', 'terminator', 'tilix'
        ]
        if any(terminal in term for terminal in unicode_terminals):
            return True
    
    # Check if we're in a known Unicode-capable environment
    if os.environ.get('COLORTERM'):
        return True
    
    # Check Python's default encoding
    if sys.getdefaultencoding().lower() in ['utf-8', 'utf8']:
        return True
    
    # Default to False for safety - better to have ASCII fallback
    # than broken display
    return False


def get_unicode_handling_mode() -> str:
    """
    Determine the appropriate Unicode handling mode for the current environment.
    
    Returns:
        String indicating the Unicode handling mode:
        - 'full': Full Unicode support with wide character handling
        - 'basic': Basic Unicode support, treat all characters as single-width
        - 'ascii': ASCII-only fallback mode
    """
    if detect_terminal_unicode_support():
        return 'full'
    
    # Check if we can at least handle basic Unicode
    try:
        # Test if we can encode/decode Unicode
        test_text = "test unicode: café"
        test_text.encode('utf-8').decode('utf-8')
        return 'basic'
    except (UnicodeError, LookupError):
        return 'ascii'


def create_fallback_functions(mode: str = None):
    """
    Create fallback versions of wide character functions based on terminal capabilities.
    
    This function returns a dictionary of functions that are appropriate for the
    current terminal's Unicode support level.
    
    Args:
        mode: Override the detected mode ('full', 'basic', 'ascii')
        
    Returns:
        Dictionary containing appropriate functions for the terminal capabilities
    """
    if mode is None:
        mode = get_unicode_handling_mode()
    
    if mode == 'full':
        # Use full wide character support
        return {
            'get_display_width': get_display_width,
            'truncate_to_width': truncate_to_width,
            'pad_to_width': pad_to_width,
            'split_at_width': split_at_width,
            'is_wide_character': is_wide_character
        }
    elif mode == 'basic':
        # Basic Unicode but treat all characters as single-width
        def basic_get_display_width(text: str) -> int:
            return len(text)
        
        def basic_truncate_to_width(text: str, max_width: int, ellipsis: str = "...") -> str:
            if len(text) <= max_width:
                return text
            if len(ellipsis) >= max_width:
                return ellipsis[:max_width]
            return text[:max_width - len(ellipsis)] + ellipsis
        
        def basic_pad_to_width(text: str, width: int, align: str = 'left', fill_char: str = ' ') -> str:
            current_len = len(text)
            if current_len >= width:
                return text
            padding = fill_char * (width - current_len)
            if align == 'right':
                return padding + text
            elif align == 'center':
                left_pad = (width - current_len) // 2
                right_pad = width - current_len - left_pad
                return (fill_char * left_pad) + text + (fill_char * right_pad)
            else:
                return text + padding
        
        def basic_split_at_width(text: str, width: int) -> Tuple[str, str]:
            if width <= 0:
                return ("", text)
            return (text[:width], text[width:])
        
        def basic_is_wide_character(char: str) -> bool:
            return False
        
        return {
            'get_display_width': basic_get_display_width,
            'truncate_to_width': basic_truncate_to_width,
            'pad_to_width': basic_pad_to_width,
            'split_at_width': basic_split_at_width,
            'is_wide_character': basic_is_wide_character
        }
    else:  # ascii mode
        # ASCII-safe fallback functions
        def ascii_get_display_width(text: str) -> int:
            # Only count ASCII printable characters
            return sum(1 for c in text if ord(c) >= 32 and ord(c) < 127)
        
        def ascii_truncate_to_width(text: str, max_width: int, ellipsis: str = "...") -> str:
            # Convert to ASCII-safe representation
            safe_text = ''.join(c if ord(c) >= 32 and ord(c) < 127 else '?' for c in text)
            if len(safe_text) <= max_width:
                return safe_text
            if len(ellipsis) >= max_width:
                return ellipsis[:max_width]
            return safe_text[:max_width - len(ellipsis)] + ellipsis
        
        def ascii_pad_to_width(text: str, width: int, align: str = 'left', fill_char: str = ' ') -> str:
            safe_text = ''.join(c if ord(c) >= 32 and ord(c) < 127 else '?' for c in text)
            current_len = len(safe_text)
            if current_len >= width:
                return safe_text
            padding = fill_char * (width - current_len)
            if align == 'right':
                return padding + safe_text
            elif align == 'center':
                left_pad = (width - current_len) // 2
                right_pad = width - current_len - left_pad
                return (fill_char * left_pad) + safe_text + (fill_char * right_pad)
            else:
                return safe_text + padding
        
        def ascii_split_at_width(text: str, width: int) -> Tuple[str, str]:
            safe_text = ''.join(c if ord(c) >= 32 and ord(c) < 127 else '?' for c in text)
            if width <= 0:
                return ("", safe_text)
            return (safe_text[:width], safe_text[width:])
        
        def ascii_is_wide_character(char: str) -> bool:
            return False
        
        return {
            'get_display_width': ascii_get_display_width,
            'truncate_to_width': ascii_truncate_to_width,
            'pad_to_width': ascii_pad_to_width,
            'split_at_width': ascii_split_at_width,
            'is_wide_character': ascii_is_wide_character
        }


# Global configuration for Unicode handling mode
_unicode_mode = None
_fallback_functions = None


def set_unicode_mode(mode: str):
    """
    Set the Unicode handling mode for the application.
    
    Args:
        mode: Unicode handling mode ('full', 'basic', 'ascii', or 'auto')
    """
    global _unicode_mode, _fallback_functions
    
    if mode == 'auto':
        _unicode_mode = get_unicode_handling_mode()
    else:
        _unicode_mode = mode
    
    _fallback_functions = create_fallback_functions(_unicode_mode)


def get_current_unicode_mode() -> str:
    """
    Get the current Unicode handling mode.
    
    Returns:
        Current Unicode handling mode string
    """
    global _unicode_mode
    if _unicode_mode is None:
        set_unicode_mode('auto')
    return _unicode_mode


def get_safe_functions():
    """
    Get the appropriate wide character functions for the current terminal.
    
    Returns:
        Dictionary of functions appropriate for current terminal capabilities
    """
    global _fallback_functions
    if _fallback_functions is None:
        set_unicode_mode('auto')
    return _fallback_functions


# Initialize with auto-detection
set_unicode_mode('auto')