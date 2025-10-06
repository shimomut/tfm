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
import warnings
from functools import lru_cache
from typing import Tuple, Optional


def safe_is_wide_character(char: str, warn_on_error: bool = None) -> bool:
    """
    Safely check if a character is a wide (double-width) character with error handling.
    
    This function provides a safe wrapper around is_wide_character() that
    handles Unicode errors gracefully by falling back to False.
    
    Args:
        char: A single Unicode character
        warn_on_error: Whether to emit warnings on Unicode errors (default: True)
        
    Returns:
        True if the character is wide (double-width), False otherwise or on error
    """
    if warn_on_error is None:
        warn_on_error = should_show_warnings()
    
    if not isinstance(char, str):
        if warn_on_error:
            warnings.warn(f"safe_is_wide_character: Expected string, got {type(char)}", UserWarning)
        return False
    
    try:
        return is_wide_character(char)
    except (UnicodeError, ValueError, TypeError) as e:
        if warn_on_error:
            safe_repr = repr(char)[:20] + ('...' if len(repr(char)) > 20 else '')
            warnings.warn(f"Unicode error in is_wide_character for {safe_repr}: {e}. "
                         f"Falling back to False.", UserWarning)
        return False
    except Exception as e:
        if warn_on_error:
            safe_repr = repr(char)[:20] + ('...' if len(repr(char)) > 20 else '')
            warnings.warn(f"Unexpected error in is_wide_character for {safe_repr}: {e}. "
                         f"Falling back to False.", UserWarning)
        return False


@lru_cache(maxsize=1024)
def _cached_is_wide_character(char: str) -> bool:
    """
    Cached version of wide character detection for performance.
    
    This function caches results to avoid repeated Unicode database lookups
    for the same characters, which is common when processing file lists.
    """
    if len(char) != 1:
        return False
    
    try:
        # Use East Asian Width property from Unicode database
        width = unicodedata.east_asian_width(char)
        # 'F' = Fullwidth, 'W' = Wide
        return width in ('F', 'W')
    except (UnicodeError, ValueError):
        # If we can't determine the width, assume it's not wide
        return False


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
    # Fast path for ASCII characters (most common case)
    if len(char) == 1 and ord(char) < 128:
        return False
    
    return _cached_is_wide_character(char)


@lru_cache(maxsize=2048)
def _cached_get_display_width(text: str) -> int:
    """
    Cached version of display width calculation for performance.
    
    This function caches results for frequently accessed strings like
    filenames that appear repeatedly in directory listings.
    """
    if not text:
        return 0
    
    width = 0
    i = 0
    
    while i < len(text):
        try:
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
        except (UnicodeError, ValueError):
            # If we can't process this character, assume it's single-width
            width += 1
        except Exception:
            # For any other unexpected error, assume single-width and continue
            width += 1
        
        i += 1
    
    return width


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
    
    # Fast path for ASCII-only strings (most common case)
    if all(ord(c) < 128 for c in text):
        return len(text)
    
    # Use cached version for non-ASCII strings
    return _cached_get_display_width(text)


def safe_get_display_width(text: str, warn_on_error: bool = None) -> int:
    """
    Safely calculate display width with fallback to character count.
    
    This function provides a safe wrapper around get_display_width() that
    handles Unicode errors gracefully by falling back to character count.
    It logs warnings for debugging while maintaining functionality.
    
    Args:
        text: The text string to measure
        warn_on_error: Whether to emit warnings on Unicode errors (default: True)
        
    Returns:
        The display width in terminal columns, or character count as fallback
    """
    if warn_on_error is None:
        warn_on_error = should_show_warnings()
    
    if not isinstance(text, str):
        if warn_on_error:
            warnings.warn(f"safe_get_display_width: Expected string, got {type(text)}", UserWarning)
        return 0
    
    # Fast path for empty strings
    if not text:
        return 0
    
    # Fast path for ASCII-only strings (most common case)
    try:
        if all(ord(c) < 128 for c in text):
            return len(text)
    except (TypeError, ValueError):
        pass  # Fall through to full Unicode processing
    
    try:
        return get_display_width(text)
    except (UnicodeError, ValueError, TypeError) as e:
        if warn_on_error:
            # Create a safe representation of the problematic text for logging
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unicode error in display width calculation for {safe_repr}: {e}. "
                         f"Falling back to character count.", UserWarning)
        # Fallback to character count if Unicode processing fails
        return len(text)
    except Exception as e:
        if warn_on_error:
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unexpected error in display width calculation for {safe_repr}: {e}. "
                         f"Falling back to character count.", UserWarning)
        # Ultimate fallback for any unexpected errors
        return len(text)


def safe_truncate_to_width(text: str, max_width: int, ellipsis: str = "...", warn_on_error: bool = None) -> str:
    """
    Safely truncate text to fit within max_width display columns with error handling.
    
    This function provides a safe wrapper around truncate_to_width() that
    handles Unicode errors gracefully by falling back to character-based truncation.
    
    Args:
        text: The text string to truncate
        max_width: Maximum display width in terminal columns
        ellipsis: String to append when text is truncated (default: "...")
        warn_on_error: Whether to emit warnings on Unicode errors (default: True)
        
    Returns:
        Truncated text that fits within max_width columns
    """
    if warn_on_error is None:
        warn_on_error = should_show_warnings()
    
    if not isinstance(text, str):
        if warn_on_error:
            warnings.warn(f"safe_truncate_to_width: Expected string, got {type(text)}", UserWarning)
        return ""
    
    if not isinstance(max_width, int) or max_width < 0:
        if warn_on_error:
            warnings.warn(f"safe_truncate_to_width: Invalid max_width {max_width}, using 0", UserWarning)
        max_width = 0
    
    try:
        return truncate_to_width(text, max_width, ellipsis)
    except (UnicodeError, ValueError, TypeError) as e:
        if warn_on_error:
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unicode error in truncate_to_width for {safe_repr}: {e}. "
                         f"Falling back to character-based truncation.", UserWarning)
        # Fallback to simple character-based truncation
        if len(text) <= max_width:
            return text
        if len(ellipsis) >= max_width:
            return ellipsis[:max_width] if max_width > 0 else ""
        return text[:max_width - len(ellipsis)] + ellipsis
    except Exception as e:
        if warn_on_error:
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unexpected error in truncate_to_width for {safe_repr}: {e}. "
                         f"Falling back to character-based truncation.", UserWarning)
        # Ultimate fallback
        try:
            if len(text) <= max_width:
                return text
            return text[:max_width] if max_width > 0 else ""
        except:
            return ""


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
    
    # Fast path for ASCII-only strings (most common case)
    if all(ord(c) < 128 for c in text):
        if len(text) <= max_width:
            return text
        if len(ellipsis) >= max_width:
            return ellipsis[:max_width] if max_width > 0 else ""
        target_len = max_width - len(ellipsis)
        if target_len <= 0:
            return ellipsis[:max_width]
        return text[:target_len] + ellipsis
    
    # Full Unicode processing for non-ASCII strings
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


def safe_pad_to_width(text: str, width: int, align: str = 'left', fill_char: str = ' ', warn_on_error: bool = None) -> str:
    """
    Safely pad text to exact display width with error handling.
    
    This function provides a safe wrapper around pad_to_width() that
    handles Unicode errors gracefully by falling back to character-based padding.
    
    Args:
        text: The text string to pad
        width: Target display width in terminal columns
        align: Alignment ('left', 'right', 'center')
        fill_char: Character to use for padding (default: space)
        warn_on_error: Whether to emit warnings on Unicode errors (default: True)
        
    Returns:
        Padded text with exact display width
    """
    if warn_on_error is None:
        warn_on_error = should_show_warnings()
    
    if not isinstance(text, str):
        if warn_on_error:
            warnings.warn(f"safe_pad_to_width: Expected string, got {type(text)}", UserWarning)
        text = ""
    
    if not isinstance(width, int) or width < 0:
        if warn_on_error:
            warnings.warn(f"safe_pad_to_width: Invalid width {width}, using 0", UserWarning)
        width = 0
    
    try:
        return pad_to_width(text, width, align, fill_char)
    except (UnicodeError, ValueError, TypeError) as e:
        if warn_on_error:
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unicode error in pad_to_width for {safe_repr}: {e}. "
                         f"Falling back to character-based padding.", UserWarning)
        # Fallback to simple character-based padding
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
    except Exception as e:
        if warn_on_error:
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unexpected error in pad_to_width for {safe_repr}: {e}. "
                         f"Falling back to character-based padding.", UserWarning)
        # Ultimate fallback
        try:
            current_len = len(text)
            if current_len >= width:
                return text
            return text + (' ' * (width - current_len))
        except:
            return text


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
    
    # Fast path for ASCII-only strings with space padding (most common case)
    if fill_char == ' ' and all(ord(c) < 128 for c in text):
        current_len = len(text)
        if current_len >= width:
            return text
        
        padding_needed = width - current_len
        padding = ' ' * padding_needed
        
        if align == 'left':
            return text + padding
        elif align == 'right':
            return padding + text
        elif align == 'center':
            left_pad = padding_needed // 2
            right_pad = padding_needed - left_pad
            return (' ' * left_pad) + text + (' ' * right_pad)
        else:
            return text + padding
    
    # Full Unicode processing for non-ASCII strings or non-space padding
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


def safe_split_at_width(text: str, width: int, warn_on_error: bool = None) -> Tuple[str, str]:
    """
    Safely split text at display width boundary with error handling.
    
    This function provides a safe wrapper around split_at_width() that
    handles Unicode errors gracefully by falling back to character-based splitting.
    
    Args:
        text: The text string to split
        width: Display width at which to split
        warn_on_error: Whether to emit warnings on Unicode errors (default: True)
        
    Returns:
        Tuple of (left_part, right_part) where left_part fits within width
    """
    if warn_on_error is None:
        warn_on_error = should_show_warnings()
    
    if not isinstance(text, str):
        if warn_on_error:
            warnings.warn(f"safe_split_at_width: Expected string, got {type(text)}", UserWarning)
        return ("", "")
    
    if not isinstance(width, int) or width < 0:
        if warn_on_error:
            warnings.warn(f"safe_split_at_width: Invalid width {width}, using 0", UserWarning)
        width = 0
    
    try:
        return split_at_width(text, width)
    except (UnicodeError, ValueError, TypeError) as e:
        if warn_on_error:
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unicode error in split_at_width for {safe_repr}: {e}. "
                         f"Falling back to character-based splitting.", UserWarning)
        # Fallback to simple character-based splitting
        if width <= 0:
            return ("", text)
        return (text[:width], text[width:])
    except Exception as e:
        if warn_on_error:
            safe_repr = repr(text)[:50] + ('...' if len(repr(text)) > 50 else '')
            warnings.warn(f"Unexpected error in split_at_width for {safe_repr}: {e}. "
                         f"Falling back to character-based splitting.", UserWarning)
        # Ultimate fallback
        try:
            if width <= 0:
                return ("", text)
            return (text[:width], text[width:])
        except:
            return ("", text)


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
    
    # Fast path for ASCII-only strings (most common case)
    if all(ord(c) < 128 for c in text):
        if width >= len(text):
            return (text, "")
        return (text[:width], text[width:])
    
    # Full Unicode processing for non-ASCII strings
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
    try:
        # Check locale settings
        locale_vars = ['LC_ALL', 'LC_CTYPE', 'LANG']
        for var in locale_vars:
            try:
                locale_value = os.environ.get(var, '').upper()
                if locale_value:
                    # Look for UTF-8 encoding in locale
                    if 'UTF-8' in locale_value or 'UTF8' in locale_value:
                        return True
                    # Some locales might not explicitly mention UTF-8 but support Unicode
                    if any(lang in locale_value for lang in ['JA_JP', 'ZH_CN', 'ZH_TW', 'KO_KR']):
                        return True
            except (KeyError, AttributeError):
                continue
        
        # Check terminal type
        try:
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
        except (KeyError, AttributeError):
            pass
        
        # Check if we're in a known Unicode-capable environment
        try:
            if os.environ.get('COLORTERM'):
                return True
        except (KeyError, AttributeError):
            pass
        
        # Check Python's default encoding
        try:
            if sys.getdefaultencoding().lower() in ['utf-8', 'utf8']:
                return True
        except (AttributeError, UnicodeError):
            pass
        
        # Test basic Unicode functionality
        try:
            test_char = 'あ'  # Japanese character
            unicodedata.east_asian_width(test_char)
            return True
        except (UnicodeError, NameError):
            pass
        
    except Exception as e:
        # If anything goes wrong, log a warning and default to False
        warnings.warn(f"Error detecting terminal Unicode support: {e}. "
                     f"Defaulting to no Unicode support.", UserWarning)
    
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
    try:
        if detect_terminal_unicode_support():
            return 'full'
        
        # Check if we can at least handle basic Unicode
        try:
            # Test if we can encode/decode Unicode
            test_text = "test unicode: café"
            test_text.encode('utf-8').decode('utf-8')
            
            # Test basic Unicode operations
            unicodedata.category('a')
            
            return 'basic'
        except (UnicodeError, LookupError, NameError, AttributeError):
            return 'ascii'
    except Exception as e:
        # If anything goes wrong, log a warning and default to ASCII
        warnings.warn(f"Error determining Unicode handling mode: {e}. "
                     f"Defaulting to ASCII mode.", UserWarning)
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
        # Use full wide character support with safe wrappers
        return {
            'get_display_width': safe_get_display_width,
            'truncate_to_width': safe_truncate_to_width,
            'pad_to_width': safe_pad_to_width,
            'split_at_width': safe_split_at_width,
            'is_wide_character': safe_is_wide_character
        }
    elif mode == 'basic':
        # Basic Unicode but treat all characters as single-width
        def basic_get_display_width(text: str) -> int:
            try:
                return len(text) if isinstance(text, str) else 0
            except Exception:
                return 0
        
        def basic_truncate_to_width(text: str, max_width: int, ellipsis: str = "...") -> str:
            try:
                if not isinstance(text, str):
                    return ""
                if not isinstance(max_width, int) or max_width < 0:
                    max_width = 0
                if len(text) <= max_width:
                    return text
                if len(ellipsis) >= max_width:
                    return ellipsis[:max_width] if max_width > 0 else ""
                return text[:max_width - len(ellipsis)] + ellipsis
            except Exception:
                return text if isinstance(text, str) else ""
        
        def basic_pad_to_width(text: str, width: int, align: str = 'left', fill_char: str = ' ') -> str:
            try:
                if not isinstance(text, str):
                    text = ""
                if not isinstance(width, int) or width < 0:
                    width = 0
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
            except Exception:
                return text if isinstance(text, str) else ""
        
        def basic_split_at_width(text: str, width: int) -> Tuple[str, str]:
            try:
                if not isinstance(text, str):
                    return ("", "")
                if not isinstance(width, int) or width <= 0:
                    return ("", text)
                return (text[:width], text[width:])
            except Exception:
                return ("", text if isinstance(text, str) else "")
        
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
            try:
                if not isinstance(text, str):
                    return 0
                # Only count ASCII printable characters
                return sum(1 for c in text if 32 <= ord(c) < 127)
            except (TypeError, ValueError):
                return 0
            except Exception:
                return len(text) if isinstance(text, str) else 0
        
        def ascii_truncate_to_width(text: str, max_width: int, ellipsis: str = "...") -> str:
            try:
                if not isinstance(text, str):
                    return ""
                if not isinstance(max_width, int) or max_width < 0:
                    max_width = 0
                # Convert to ASCII-safe representation using configurable fallback char
                fallback_char = get_fallback_char()
                safe_text = ''.join(c if 32 <= ord(c) < 127 else fallback_char for c in text)
                if len(safe_text) <= max_width:
                    return safe_text
                if len(ellipsis) >= max_width:
                    return ellipsis[:max_width] if max_width > 0 else ""
                return safe_text[:max_width - len(ellipsis)] + ellipsis
            except Exception:
                return text if isinstance(text, str) else ""
        
        def ascii_pad_to_width(text: str, width: int, align: str = 'left', fill_char: str = ' ') -> str:
            try:
                if not isinstance(text, str):
                    text = ""
                if not isinstance(width, int) or width < 0:
                    width = 0
                # Convert to ASCII-safe representation using configurable fallback char
                fallback_char = get_fallback_char()
                safe_text = ''.join(c if 32 <= ord(c) < 127 else fallback_char for c in text)
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
            except Exception:
                return text if isinstance(text, str) else ""
        
        def ascii_split_at_width(text: str, width: int) -> Tuple[str, str]:
            try:
                if not isinstance(text, str):
                    return ("", "")
                if not isinstance(width, int) or width <= 0:
                    return ("", text)
                # Convert to ASCII-safe representation using configurable fallback char
                fallback_char = get_fallback_char()
                safe_text = ''.join(c if 32 <= ord(c) < 127 else fallback_char for c in text)
                return (safe_text[:width], safe_text[width:])
            except Exception:
                return ("", text if isinstance(text, str) else "")
        
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
    
    try:
        if mode == 'auto':
            _unicode_mode = get_unicode_handling_mode()
        elif mode in ('full', 'basic', 'ascii'):
            _unicode_mode = mode
        else:
            warnings.warn(f"Invalid Unicode mode '{mode}', using 'auto'", UserWarning)
            _unicode_mode = get_unicode_handling_mode()
        
        _fallback_functions = create_fallback_functions(_unicode_mode)
    except Exception as e:
        warnings.warn(f"Error setting Unicode mode: {e}. Falling back to ASCII mode.", UserWarning)
        _unicode_mode = 'ascii'
        _fallback_functions = create_fallback_functions('ascii')


def get_current_unicode_mode() -> str:
    """
    Get the current Unicode handling mode.
    
    Returns:
        Current Unicode handling mode string
    """
    global _unicode_mode
    try:
        if _unicode_mode is None:
            set_unicode_mode('auto')
        return _unicode_mode
    except Exception as e:
        warnings.warn(f"Error getting Unicode mode: {e}. Returning 'ascii'.", UserWarning)
        return 'ascii'


def get_safe_functions():
    """
    Get the appropriate wide character functions for the current terminal.
    
    Returns:
        Dictionary of functions appropriate for current terminal capabilities
    """
    global _fallback_functions
    try:
        if _fallback_functions is None:
            set_unicode_mode('auto')
        return _fallback_functions
    except Exception as e:
        warnings.warn(f"Error getting safe functions: {e}. Using ASCII fallback.", UserWarning)
        # Return basic ASCII-safe functions as ultimate fallback
        return {
            'get_display_width': lambda text: len(text) if isinstance(text, str) else 0,
            'truncate_to_width': lambda text, width, ellipsis="...": text[:width] if isinstance(text, str) and width > 0 else "",
            'pad_to_width': lambda text, width, align='left', fill_char=' ': text + (' ' * max(0, width - len(text))) if isinstance(text, str) else "",
            'split_at_width': lambda text, width: (text[:width], text[width:]) if isinstance(text, str) and width > 0 else ("", text),
            'is_wide_character': lambda char: False
        }


def initialize_from_config():
    """
    Initialize Unicode handling mode from TFM configuration.
    
    This function should be called after the configuration system is loaded
    to apply user-configured Unicode handling preferences.
    """
    try:
        # Try to import config - may not be available during early initialization
        from tfm_config import get_config
        config = get_config()
        
        # Get Unicode mode from config
        unicode_mode = getattr(config, 'UNICODE_MODE', 'auto')
        set_unicode_mode(unicode_mode)
        
        # Configure warning behavior
        global _show_warnings
        _show_warnings = getattr(config, 'UNICODE_WARNINGS', True)
        
    except ImportError:
        # Config system not available, use auto-detection
        set_unicode_mode('auto')
    except Exception as e:
        warnings.warn(f"Error loading Unicode settings from config: {e}. Using auto-detection.", UserWarning)
        set_unicode_mode('auto')


def get_fallback_char():
    """
    Get the fallback character for unrepresentable characters from config.
    
    Returns:
        Single character string to use as fallback
    """
    try:
        from tfm_config import get_config
        config = get_config()
        return getattr(config, 'UNICODE_FALLBACK_CHAR', '?')
    except (ImportError, Exception):
        return '?'


# Global flag for warning behavior
_show_warnings = True


def should_show_warnings():
    """Check if Unicode warnings should be shown based on configuration."""
    return _show_warnings


# Cache management functions for performance optimization
def clear_display_width_cache():
    """
    Clear the display width calculation cache.
    
    This can be useful to free memory or when Unicode handling mode changes.
    """
    try:
        _cached_get_display_width.cache_clear()
        _cached_is_wide_character.cache_clear()
    except Exception as e:
        warnings.warn(f"Error clearing display width cache: {e}", UserWarning)


def get_cache_info():
    """
    Get cache statistics for performance monitoring.
    
    Returns:
        Dictionary containing cache statistics for display width and character width functions
    """
    try:
        return {
            'display_width_cache': _cached_get_display_width.cache_info()._asdict(),
            'is_wide_char_cache': _cached_is_wide_character.cache_info()._asdict()
        }
    except Exception as e:
        warnings.warn(f"Error getting cache info: {e}", UserWarning)
        return {}


def optimize_for_ascii_only():
    """
    Optimize performance for ASCII-only environments.
    
    This function clears caches and sets up optimizations for environments
    that primarily use ASCII filenames.
    """
    try:
        clear_display_width_cache()
        # The ASCII fast paths are already built into the functions
        # This function mainly serves as a way to clear caches and
        # potentially adjust cache sizes in the future
    except Exception as e:
        warnings.warn(f"Error optimizing for ASCII: {e}", UserWarning)


# Initialize with auto-detection
try:
    set_unicode_mode('auto')
except Exception as e:
    warnings.warn(f"Error during Unicode mode initialization: {e}. Using ASCII fallback.", UserWarning)
    _unicode_mode = 'ascii'
    _fallback_functions = create_fallback_functions('ascii')