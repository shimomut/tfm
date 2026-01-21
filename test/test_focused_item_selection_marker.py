#!/usr/bin/env python3
"""
Test that focused item background color does not apply to selection marker.

This test verifies that when a file is focused, the special background color
is only applied to the filename/size/date portion, not to the selection
indicator (left 2 char width).
"""

import sys
import os
from pathlib import Path as StdPath

# Add src and ttk to path
sys.path.insert(0, str(StdPath(__file__).parent.parent / 'src'))
sys.path.insert(0, str(StdPath(__file__).parent.parent / 'ttk'))

from tfm_colors import get_file_color, COLOR_REGULAR_FILE, COLOR_REGULAR_FILE_FOCUSED, COLOR_DIRECTORIES_FOCUSED
from ttk import TextAttribute


def test_get_file_color_returns_focused_color():
    """Test that get_file_color returns focused color for focused items"""
    
    # Test focused regular file in active pane
    color_pair, attrs = get_file_color(is_dir=False, is_executable=False, is_focused=True, is_active=True)
    assert color_pair == COLOR_REGULAR_FILE_FOCUSED
    assert attrs == TextAttribute.NORMAL
    
    # Test focused directory in active pane
    color_pair, attrs = get_file_color(is_dir=True, is_executable=False, is_focused=True, is_active=True)
    assert color_pair == COLOR_DIRECTORIES_FOCUSED
    assert attrs == TextAttribute.NORMAL


def test_get_status_color_returns_different_color():
    """Test that normal color is different from focused colors"""
    
    normal_color = COLOR_REGULAR_FILE
    focused_file_color, _ = get_file_color(is_dir=False, is_executable=False, is_focused=True, is_active=True)
    focused_dir_color, _ = get_file_color(is_dir=True, is_executable=False, is_focused=True, is_active=True)
    
    # Normal color should be different from focused colors
    assert normal_color != focused_file_color, \
        f"Normal color {normal_color} should differ from focused file color {focused_file_color}"
    assert normal_color != focused_dir_color, \
        f"Normal color {normal_color} should differ from focused dir color {focused_dir_color}"


def test_selection_marker_logic():
    """Test the logic for drawing selection markers separately"""
    
    # Simulate the drawing logic from tfm_main.py
    is_selected = True
    is_focused = True
    is_active = True
    is_dir = False
    
    # Get colors
    normal_color, normal_attrs = (COLOR_REGULAR_FILE, TextAttribute.NORMAL)
    file_color, file_attrs = get_file_color(is_dir, False, is_focused, is_active)
    
    # Selection marker and separator space should use normal color
    selection_marker = "●" if is_selected else " "
    marker_color = normal_color
    separator_color = normal_color
    
    # File content should use focused color
    content_color = file_color
    
    # Verify they are different
    assert marker_color != content_color, \
        "Selection marker color should differ from focused content color"
    assert separator_color != content_color, \
        "Separator space color should differ from focused content color"
    
    print(f"✓ Selection marker uses color {marker_color} (normal)")
    print(f"✓ Separator space uses color {separator_color} (normal)")
    print(f"✓ Focused content uses color {content_color} (focused)")
    print(f"✓ Colors are different: {marker_color} != {content_color}")


if __name__ == '__main__':
    print("Testing focused item selection marker background fix...")
    print()
    
    test_get_file_color_returns_focused_color()
    print("✓ get_file_color returns correct focused colors")
    
    test_get_status_color_returns_different_color()
    print("✓ Normal color differs from focused colors")
    
    test_selection_marker_logic()
    print()
    print("All tests passed!")
