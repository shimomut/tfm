#!/usr/bin/env python3
"""
TFM String Formatting Utilities

Common string formatting functions used throughout TFM.
"""


def format_size(size: int, compact: bool = False) -> str:
    """Format file size in human-readable format.
    
    Args:
        size: Size in bytes
        compact: If True, use compact format without spaces (e.g., "1.5M")
                If False, use standard format with spaces (e.g., "1.5 MB")
    
    Returns:
        str: Formatted size string
        
    Examples:
        >>> format_size(0)
        '0 B'
        >>> format_size(512)
        '512 B'
        >>> format_size(1536)
        '1.5 KB'
        >>> format_size(1536, compact=True)
        '1.5K'
        >>> format_size(1048576)
        '1.0 MB'
        >>> format_size(1073741824)
        '1.0 GB'
    """
    if size < 0:
        size = 0
    
    if compact:
        # Compact format: no space, single letter, 1 decimal place
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{int(size)}{unit}"
                else:
                    return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}P"
    else:
        # Standard format: with space, full unit name, 1 decimal place
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                if unit == 'B':
                    # Show bytes as integer without decimal
                    return f"{int(size)} {unit}"
                else:
                    return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
