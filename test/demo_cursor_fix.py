#!/usr/bin/env python3
"""
Demonstration of SingleLineTextEdit cursor rendering fix

This script shows how the cursor rendering issue with long text has been fixed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from unittest.mock import Mock, patch
from tfm_single_line_text_edit import SingleLineTextEdit


def simulate_text_editor_drawing(text, cursor_pos, max_width, label=""):
    """Simulate drawing a text editor and return cursor information"""
    
    editor = SingleLineTextEdit()
    editor.set_text(text)
    editor.set_cursor_pos(cursor_pos)
    
    # Mock stdscr
    mock_stdscr = Mock()
    mock_stdscr.getmaxyx.return_value = (24, 80)
    
    # Track what gets drawn
    drawn_items = []
    def mock_addstr(y, x, text, attr=0):
        drawn_items.append({
            'y': y, 'x': x, 'text': text, 'attr': attr,
            'is_cursor': bool(attr & 0x40000),  # curses.A_REVERSE
            'is_bold': bool(attr & 0x200000)    # curses.A_BOLD
        })
    
    mock_stdscr.addstr = mock_addstr
    
    with patch('tfm_single_line_text_edit.get_status_color', return_value=0):
        editor.draw(mock_stdscr, 0, 0, max_width, label, is_active=True)
    
    # Analyze results
    cursor_items = [item for item in drawn_items if item['is_cursor']]
    text_items = [item for item in drawn_items if not item['is_cursor']]
    
    # Calculate visible text
    visible_text = ""
    for item in text_items:
        if item['text'] != label:  # Skip label
            visible_text += item['text']
    
    return {
        'cursor_rendered': len(cursor_items) > 0,
        'cursor_items': cursor_items,
        'visible_text': visible_text,
        'total_items': len(drawn_items)
    }


def demonstrate_cursor_fix():
    """Demonstrate the cursor rendering fix"""
    
    print("SingleLineTextEdit Cursor Rendering Fix")
    print("=" * 40)
    print()
    
    # Test cases that previously had issues
    test_cases = [
        {
            "name": "Short text, cursor at end",
            "text": "hello.txt",
            "cursor_pos": 9,
            "max_width": 20,
            "label": "File: "
        },
        {
            "name": "Long text, cursor at end",
            "text": "very_long_filename_that_exceeds_display_width.txt",
            "cursor_pos": 49,
            "max_width": 30,
            "label": "Rename: "
        },
        {
            "name": "Long text, cursor in middle",
            "text": "very_long_filename_that_exceeds_display_width.txt",
            "cursor_pos": 25,
            "max_width": 20,
            "label": ""
        },
        {
            "name": "Text exactly fills width, cursor at end",
            "text": "exact_width_file.txt",
            "cursor_pos": 20,
            "max_width": 20,
            "label": ""
        },
        {
            "name": "Very narrow display",
            "text": "long_filename.txt",
            "cursor_pos": 17,
            "max_width": 10,
            "label": "F: "
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
        print(f"   Text: '{case['text']}' (length: {len(case['text'])})")
        print(f"   Cursor position: {case['cursor_pos']}")
        print(f"   Max width: {case['max_width']}")
        print(f"   Label: '{case['label']}'")
        
        result = simulate_text_editor_drawing(
            case['text'], case['cursor_pos'], case['max_width'], case['label']
        )
        
        status = "✓ FIXED" if result['cursor_rendered'] else "✗ BROKEN"
        print(f"   Status: {status}")
        
        if result['cursor_rendered']:
            cursor_item = result['cursor_items'][0]
            print(f"   Cursor: '{cursor_item['text']}' at x={cursor_item['x']}")
        else:
            print(f"   Cursor: NOT RENDERED")
        
        print(f"   Visible: '{result['visible_text']}'")
        print()


def demonstrate_edge_cases():
    """Demonstrate edge cases that are now handled correctly"""
    
    print("Edge Cases Now Handled Correctly")
    print("=" * 35)
    print()
    
    edge_cases = [
        ("Empty text", "", 0, 10),
        ("Single character", "a", 1, 10),
        ("Text fills exactly", "1234567890", 10, 10),
        ("Text exceeds by 1", "1234567890a", 11, 10),
        ("Very long text", "a" * 50, 50, 15),
        ("Cursor at start of long text", "a" * 30, 0, 10),
        ("Cursor in middle of long text", "a" * 30, 15, 10),
    ]
    
    for name, text, cursor_pos, max_width in edge_cases:
        result = simulate_text_editor_drawing(text, cursor_pos, max_width)
        
        status = "✓" if result['cursor_rendered'] else "✗"
        print(f"{status} {name}")
        print(f"    Text length: {len(text)}, Cursor: {cursor_pos}, Width: {max_width}")
        
        if result['cursor_rendered']:
            cursor_char = result['cursor_items'][0]['text']
            print(f"    Cursor shows: '{cursor_char}'")
        
        print()


def demonstrate_visible_window_logic():
    """Demonstrate the improved visible window calculation"""
    
    print("Visible Window Calculation")
    print("=" * 28)
    print()
    
    text = "abcdefghijklmnopqrstuvwxyz0123456789"  # 36 characters
    max_width = 15
    
    print(f"Text: '{text}' ({len(text)} chars)")
    print(f"Display width: {max_width} chars")
    print()
    
    # Test cursor at various positions
    positions = [0, 5, 10, 15, 20, 25, 30, 35, 36]
    
    for pos in positions:
        result = simulate_text_editor_drawing(text, pos, max_width)
        
        cursor_status = "✓" if result['cursor_rendered'] else "✗"
        
        print(f"Cursor at {pos:2d}: {cursor_status} Visible: '{result['visible_text']}'")
        
        if result['cursor_rendered']:
            cursor_item = result['cursor_items'][0]
            cursor_char = cursor_item['text']
            cursor_x = cursor_item['x']
            print(f"             Cursor: '{cursor_char}' at x={cursor_x}")
        
        print()


if __name__ == '__main__':
    demonstrate_cursor_fix()
    demonstrate_edge_cases()
    demonstrate_visible_window_logic()