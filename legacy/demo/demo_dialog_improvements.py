#!/usr/bin/env python3
"""
Demonstration of QuickEditBar improvements

This script shows how the dialog now handles:
1. Help text visibility in different terminal widths
2. Text editor remaining visible even in narrow terminals
3. Proper spacing and no overlapping elements
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from unittest.mock import Mock, patch
from tfm_quick_edit_bar import QuickEditBar


def simulate_dialog_drawing(width, prompt, help_text, input_text=""):
    """Simulate drawing a dialog and return the results"""
    
    dialog = QuickEditBar()
    dialog.show_status_line_input(
        prompt=prompt,
        help_text=help_text,
        initial_text=input_text
    )
    
    # Mock stdscr and safe_addstr
    mock_stdscr = Mock()
    mock_stdscr.getmaxyx.return_value = (24, width)
    
    safe_addstr_calls = []
    def mock_safe_addstr(*args):
        safe_addstr_calls.append(args)
    
    # Mock text_editor.draw to capture parameters
    draw_calls = []
    def mock_draw(*args, **kwargs):
        draw_calls.append(args)
    
    with patch('tfm_quick_edit_bar.get_status_color', return_value=0):
        dialog.text_editor.draw = mock_draw
        dialog.draw(mock_stdscr, mock_safe_addstr)
    
    # Analyze results
    text_editor_drawn = len(draw_calls) > 0
    max_field_width = draw_calls[0][3] if draw_calls else 0
    available_text_width = max_field_width - len(prompt) if max_field_width > len(prompt) else 0
    
    # Check if help text was drawn
    help_text_drawn = False
    help_text_position = None
    for call in safe_addstr_calls:
        if len(call) >= 3 and help_text in str(call[2]):
            help_text_drawn = True
            help_text_position = call[1]  # x position
            break
    
    return {
        'text_editor_drawn': text_editor_drawn,
        'max_field_width': max_field_width,
        'available_text_width': available_text_width,
        'help_text_drawn': help_text_drawn,
        'help_text_position': help_text_position
    }


def demonstrate_width_handling():
    """Demonstrate how dialog handles different terminal widths"""
    
    print("QuickEditBar Width Handling Improvements")
    print("=" * 55)
    print()
    
    prompt = "Rename file: "
    help_text = "ESC:cancel Enter:confirm"
    input_text = "document.txt"
    
    # Test different terminal widths
    widths = [30, 50, 70, 100, 120]
    
    print(f"Testing with prompt: '{prompt}' ({len(prompt)} chars)")
    print(f"Help text: '{help_text}' ({len(help_text)} chars)")
    print(f"Input text: '{input_text}' ({len(input_text)} chars)")
    print()
    
    for width in widths:
        print(f"Terminal width: {width} characters")
        print("-" * 30)
        
        result = simulate_dialog_drawing(width, prompt, help_text, input_text)
        
        print(f"✓ Text editor drawn: {result['text_editor_drawn']}")
        print(f"  Max field width: {result['max_field_width']} chars")
        print(f"  Available text width: {result['available_text_width']} chars")
        print(f"✓ Help text shown: {result['help_text_drawn']}")
        
        if result['help_text_drawn']:
            print(f"  Help text position: x={result['help_text_position']}")
            
            # Check for overlap
            input_end = 2 + min(result['max_field_width'], len(prompt) + len(input_text) + 1)
            gap = result['help_text_position'] - input_end
            print(f"  Gap between input and help: {gap} chars")
            
            if gap >= 2:
                print("  ✓ No overlap - good spacing")
            else:
                print("  ⚠ Potential overlap")
        else:
            print("  (Help text hidden to save space)")
        
        # Check if input can fit
        if result['available_text_width'] >= len(input_text):
            print(f"  ✓ Input text '{input_text}' fits completely")
        else:
            print(f"  ⚠ Input text will be scrolled/truncated")
        
        print()


def demonstrate_edge_cases():
    """Demonstrate edge cases and how they're handled"""
    
    print("Edge Case Handling")
    print("=" * 20)
    print()
    
    edge_cases = [
        {
            "name": "Very narrow terminal",
            "width": 25,
            "prompt": "File: ",
            "help_text": "ESC:cancel Enter:confirm",
            "input_text": "test.txt"
        },
        {
            "name": "Long prompt in narrow terminal",
            "width": 40,
            "prompt": "Enter new filename: ",
            "help_text": "ESC:cancel",
            "input_text": "document.pdf"
        },
        {
            "name": "No help text",
            "width": 60,
            "prompt": "Filter: ",
            "help_text": "",
            "input_text": "*.py"
        },
        {
            "name": "Very long input text",
            "width": 80,
            "prompt": "Rename: ",
            "help_text": "ESC:cancel Enter:confirm",
            "input_text": "very_long_filename_that_exceeds_normal_display_width.txt"
        }
    ]
    
    for case in edge_cases:
        print(f"Case: {case['name']}")
        print(f"  Terminal: {case['width']} chars, Prompt: '{case['prompt']}'")
        print(f"  Help: '{case['help_text']}', Input: '{case['input_text']}'")
        
        result = simulate_dialog_drawing(
            case['width'], case['prompt'], case['help_text'], case['input_text']
        )
        
        # Analyze the result
        status = "✓ GOOD" if result['text_editor_drawn'] and result['available_text_width'] > 0 else "✗ PROBLEM"
        print(f"  Status: {status}")
        
        if result['text_editor_drawn']:
            print(f"    Text editor: {result['available_text_width']} chars available")
        else:
            print(f"    Text editor: NOT DRAWN")
            
        if case['help_text']:
            if result['help_text_drawn']:
                print(f"    Help text: Shown at x={result['help_text_position']}")
            else:
                print(f"    Help text: Hidden (no space)")
        else:
            print(f"    Help text: None specified")
        
        print()


def demonstrate_improvements():
    """Show the specific improvements made"""
    
    print("Key Improvements Made")
    print("=" * 22)
    print()
    
    improvements = [
        "1. Text editor no longer disappears in narrow terminals",
        "2. Help text shows when there's adequate space (not overly restrictive)",
        "3. Help text is hidden gracefully when terminal is too narrow",
        "4. Minimum field width is guaranteed for usability",
        "5. No overlap between input field and help text",
        "6. Better space calculation prevents negative widths"
    ]
    
    for improvement in improvements:
        print(f"✓ {improvement}")
    
    print()
    print("Technical Changes:")
    print("- Improved help text space calculation and positioning logic")
    print("- Added minimum field width enforcement")
    print("- Better overlap detection and prevention")
    print("- More flexible help text display conditions")


if __name__ == '__main__':
    demonstrate_width_handling()
    demonstrate_edge_cases()
    demonstrate_improvements()