#!/usr/bin/env python3
"""
Debug horizontal scroll behavior
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_text_viewer import TextViewer
from tfm_path import Path
from tfm_wide_char_utils import get_display_width


def test_horizontal_scroll_logic():
    """Test the horizontal scrolling logic step by step"""
    
    # Simulate a line with syntax highlighting disabled
    # This creates a single segment: [(entire_line, color)]
    text = "0123456789" * 10  # 100 characters
    highlighted_line = [(text, 1)]  # Single segment
    
    print("Testing horizontal scroll logic:")
    print("=" * 70)
    print(f"Line: {text[:50]}...")
    print(f"Line length: {len(text)} characters")
    print(f"Highlighted line structure: {len(highlighted_line)} segment(s)")
    print()
    
    # Simulate different horizontal offsets
    for horizontal_offset in [0, 5, 10, 20, 30]:
        print(f"\nHorizontal offset: {horizontal_offset}")
        print("-" * 70)
        
        current_display_col = 0
        result_parts = []
        
        for segment_text, color in highlighted_line:
            text_display_width = get_display_width(segment_text)
            
            print(f"  Segment: '{segment_text[:30]}...' (width: {text_display_width})")
            print(f"  current_display_col: {current_display_col}")
            
            # Skip text that's before the horizontal offset
            if current_display_col + text_display_width <= horizontal_offset:
                print(f"  -> Skipping entire segment (ends at col {current_display_col + text_display_width})")
                current_display_col += text_display_width
                continue
            
            # Calculate visible portion of this text segment
            start_offset_cols = max(0, horizontal_offset - current_display_col)
            print(f"  start_offset_cols: {start_offset_cols}")
            
            # Split text to handle horizontal scrolling
            if start_offset_cols > 0:
                print(f"  -> Need to skip {start_offset_cols} columns from segment start")
                visible_text = ""
                skip_width = 0
                char_index = 0
                for char in segment_text:
                    char_width = get_display_width(char)
                    if skip_width + char_width > start_offset_cols:
                        visible_text = segment_text[char_index:]
                        print(f"     Found start at char_index {char_index}, char '{char}'")
                        break
                    skip_width += char_width
                    char_index += 1
                
                if not visible_text:
                    print(f"  -> No visible text after skipping")
                    current_display_col += text_display_width
                    continue
            else:
                visible_text = segment_text
                print(f"  -> Using entire segment (no skip needed)")
            
            print(f"  visible_text: '{visible_text[:40]}...'")
            result_parts.append(visible_text[:40])  # Limit to 40 chars for display
            
            current_display_col += text_display_width
        
        result = ''.join(result_parts)
        expected = text[horizontal_offset:horizontal_offset+40]
        
        print(f"\n  Result:   '{result}'")
        print(f"  Expected: '{expected}'")
        
        if result == expected:
            print(f"  ✓ CORRECT")
        else:
            print(f"  ✗ WRONG!")


if __name__ == '__main__':
    test_horizontal_scroll_logic()
