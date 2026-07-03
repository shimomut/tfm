#!/usr/bin/env python3
"""
Demo: "No items to show" message truncation in narrow panes

This demo shows how the "No items to show" message is properly truncated
when the file list pane is too narrow to display the full message.

Run with: PYTHONPATH=.:src:ttk python3 demo/demo_empty_directory_narrow_pane.py
"""

import sys
from ttk.wide_char_utils import truncate_to_width, get_display_width


def draw_pane_border(width, title):
    """Draw a simple pane border with title"""
    print("┌" + "─" * (width - 2) + "┐")
    print("│" + title.center(width - 2) + "│")
    print("├" + "─" * (width - 2) + "┤")


def draw_pane_bottom(width):
    """Draw bottom border of pane"""
    print("└" + "─" * (width - 2) + "┘")


def demo_message_in_pane(pane_width):
    """Demonstrate the message display in a pane of given width"""
    message = "No items to show"
    
    # Calculate usable width (same logic as in tfm_main.py)
    usable_width = pane_width - 2  # Leave 1 column margin on each side
    
    if usable_width < 1:
        print(f"\nPane width {pane_width}: Too narrow to display anything")
        return
    
    # Truncate message if needed
    truncated_message = truncate_to_width(message, usable_width, ellipsis="…")
    message_display_width = get_display_width(truncated_message)
    
    # Center the message horizontally
    padding_left = (pane_width - 2 - message_display_width) // 2
    padding_right = pane_width - 2 - message_display_width - padding_left
    
    # Draw the pane
    print(f"\nPane width: {pane_width} columns")
    draw_pane_border(pane_width, "Empty Directory")
    
    # Draw empty lines above message
    for _ in range(2):
        print("│" + " " * (pane_width - 2) + "│")
    
    # Draw the centered message
    print("│" + " " * padding_left + truncated_message + " " * padding_right + "│")
    
    # Draw empty lines below message
    for _ in range(2):
        print("│" + " " * (pane_width - 2) + "│")
    
    draw_pane_bottom(pane_width)
    
    # Show truncation info
    if truncated_message != message:
        print(f"  ✂️  Message truncated: '{message}' → '{truncated_message}'")
        print(f"  📏 Display width: {message_display_width}/{usable_width} columns")
    else:
        print(f"  ✓ Message fits without truncation ({message_display_width}/{usable_width} columns)")


def main():
    print("=" * 60)
    print("Demo: 'No items to show' Message Truncation")
    print("=" * 60)
    print("\nThis demo shows how the message is handled in panes of")
    print("different widths. The message is truncated with an ellipsis")
    print("when the pane is too narrow.\n")
    
    # Test various pane widths
    pane_widths = [40, 30, 20, 15, 10, 5]
    
    for width in pane_widths:
        demo_message_in_pane(width)
    
    print("\n" + "=" * 60)
    print("Key Points:")
    print("=" * 60)
    print("• Wide panes (≥20 cols): Full message displayed")
    print("• Medium panes (10-19 cols): Message truncated with ellipsis")
    print("• Narrow panes (5-9 cols): Heavily truncated but still readable")
    print("• Very narrow panes (<3 cols): Nothing displayed (too narrow)")
    print("\nThe fix ensures the message never exceeds the pane width!")


if __name__ == '__main__':
    main()
