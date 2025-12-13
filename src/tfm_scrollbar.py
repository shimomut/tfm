#!/usr/bin/env python3
"""
Unified scroll bar drawing utilities for TFM

This module provides a consistent scroll bar implementation used across
all TFM components including text viewer, log pane, and dialogs.
"""

from tfm_colors import get_scrollbar_color


def draw_scrollbar(renderer, start_y, x_pos, display_height, total_items, scroll_offset, inverted=False):
    """
    Draw a unified scroll bar for any scrollable content.
    
    This function provides a consistent scroll bar implementation used across
    all TFM components. It draws a vertical scroll bar with:
    - Track: space character (background color shows through)
    - Thumb: █ character in scroll bar color
    
    The thumb size represents the proportion of visible content, and its position
    indicates the current scroll offset.
    
    Args:
        renderer: TTK renderer object
        start_y: Starting Y position for the scroll bar
        x_pos: X position for the scroll bar (typically rightmost column)
        display_height: Height of the display area (scroll bar height)
        total_items: Total number of items/lines in the content
        scroll_offset: Current scroll position (0 = top/start, or bottom if inverted)
        inverted: If True, inverts thumb position (for bottom-up scrolling like log pane)
        
    Returns:
        None
        
    Example:
        # In a text viewer with 100 lines, showing 20 lines at a time
        draw_scrollbar(renderer, start_y=2, x_pos=79, display_height=20, 
                      total_items=100, scroll_offset=10)
        
        # In a log pane where scroll_offset=0 means bottom (newest)
        draw_scrollbar(renderer, start_y=2, x_pos=79, display_height=20,
                      total_items=100, scroll_offset=0, inverted=True)
    """
    # Don't draw scroll bar if all content fits on screen
    if total_items <= display_height:
        return
    
    # Get scroll bar color (single color pair for both track and thumb)
    scrollbar_color_pair, scrollbar_attrs = get_scrollbar_color()
    
    # Calculate scroll bar thumb position and size
    # Thumb size represents the visible portion of the document
    thumb_size = max(1, int((display_height / total_items) * display_height))
    
    # Thumb position represents current scroll position
    max_scroll = max(1, total_items - display_height)
    scroll_ratio = scroll_offset / max_scroll
    
    if inverted:
        # For inverted scrolling (log pane): scroll_offset=0 means bottom
        # So we invert the thumb position
        thumb_start = int((1 - scroll_ratio) * (display_height - thumb_size))
    else:
        # Normal scrolling: scroll_offset=0 means top
        thumb_start = int(scroll_ratio * (display_height - thumb_size))
    
    thumb_end = thumb_start + thumb_size
    
    # Draw the scroll bar using a single color pair with different characters
    for i in range(display_height):
        y = start_y + i
        if thumb_start <= i < thumb_end:
            # Draw thumb (the movable part) - solid block character
            renderer.draw_text(y, x_pos, "█", scrollbar_color_pair, scrollbar_attrs)
        else:
            # Draw track (the background) - space character (background shows through)
            renderer.draw_text(y, x_pos, " ", scrollbar_color_pair, scrollbar_attrs)


def calculate_scrollbar_width(total_items, display_height):
    """
    Calculate the width needed for a scroll bar.
    
    Args:
        total_items: Total number of items/lines in the content
        display_height: Height of the display area
        
    Returns:
        int: Width needed for scroll bar (0 if not needed, 1 if needed)
        
    Example:
        # Reserve space for scroll bar if needed
        scrollbar_width = calculate_scrollbar_width(len(items), display_height)
        content_width = total_width - scrollbar_width
    """
    return 1 if total_items > display_height else 0
