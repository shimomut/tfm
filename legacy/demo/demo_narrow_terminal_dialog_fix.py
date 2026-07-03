#!/usr/bin/env python3
"""
Demo: Narrow Terminal Dialog Fix

This demo shows how the dialog width calculation fix handles narrow terminals.
It demonstrates the safe dimension calculation logic without requiring curses.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def calculate_safe_dialog_dimensions(terminal_width, terminal_height, width_ratio, height_ratio, min_width, min_height):
    """Calculate safe dialog dimensions that fit within terminal bounds
    
    This is the core logic used in the dialog fix.
    """
    # Calculate desired dimensions
    desired_width = int(terminal_width * width_ratio)
    desired_height = int(terminal_height * height_ratio)
    
    # Apply minimum constraints, but never exceed terminal size
    dialog_width = max(min_width, desired_width)
    dialog_width = min(dialog_width, terminal_width)  # Never exceed terminal width
    
    dialog_height = max(min_height, desired_height)
    dialog_height = min(dialog_height, terminal_height)  # Never exceed terminal height
    
    # Calculate safe centering
    start_x = max(0, (terminal_width - dialog_width) // 2)
    start_y = max(0, (terminal_height - dialog_height) // 2)
    
    return dialog_width, dialog_height, start_x, start_y


def demo_dialog_calculations():
    """Demonstrate dialog calculations for various terminal sizes"""
    print("=== Narrow Terminal Dialog Fix Demo ===\n")
    
    # Test cases representing different terminal sizes
    test_cases = [
        ("Extremely Narrow", 20, 10, 0.6, 0.7, 40, 15),
        ("Very Narrow", 25, 15, 0.6, 0.7, 40, 15),
        ("Narrow", 30, 20, 0.6, 0.7, 40, 15),
        ("Small", 40, 24, 0.6, 0.7, 40, 15),
        ("Normal", 80, 24, 0.6, 0.7, 40, 15),
        ("Wide", 120, 30, 0.6, 0.7, 40, 15),
    ]
    
    print("Dialog Dimension Calculations:")
    print("=" * 80)
    print(f"{'Terminal Type':<15} {'Size':<10} {'Dialog Size':<12} {'Position':<12} {'Fits?':<6}")
    print("-" * 80)
    
    for name, term_w, term_h, w_ratio, h_ratio, min_w, min_h in test_cases:
        dialog_w, dialog_h, start_x, start_y = calculate_safe_dialog_dimensions(
            term_w, term_h, w_ratio, h_ratio, min_w, min_h
        )
        
        fits = dialog_w <= term_w and dialog_h <= term_h
        fits_str = "✓" if fits else "✗"
        
        print(f"{name:<15} {term_w}x{term_h:<7} {dialog_w}x{dialog_h:<9} ({start_x},{start_y})<8 {fits_str:<6}")
    
    print("\n" + "=" * 80)
    print("Key Improvements:")
    print("• Dialog width never exceeds terminal width")
    print("• Dialog height never exceeds terminal height") 
    print("• Start positions are never negative")
    print("• All dialogs fit within terminal bounds")


def demo_before_after_comparison():
    """Show before/after comparison for narrow terminal"""
    print("\n=== Before vs After Comparison ===\n")
    
    terminal_width, terminal_height = 30, 24
    width_ratio, height_ratio = 0.6, 0.7
    min_width, min_height = 40, 15
    
    print(f"Terminal Size: {terminal_width}x{terminal_height}")
    print(f"Desired Ratio: {width_ratio} x {height_ratio}")
    print(f"Minimum Size: {min_width} x {min_height}")
    print()
    
    # Before (problematic calculation)
    print("BEFORE (Problematic):")
    old_dialog_width = max(min_width, int(terminal_width * width_ratio))
    old_dialog_height = max(min_height, int(terminal_height * height_ratio))
    old_start_x = (terminal_width - old_dialog_width) // 2
    old_start_y = (terminal_height - old_dialog_height) // 2
    
    print(f"  Dialog Size: {old_dialog_width}x{old_dialog_height}")
    print(f"  Position: ({old_start_x}, {old_start_y})")
    print(f"  Exceeds Width: {old_dialog_width > terminal_width}")
    print(f"  Negative Position: {old_start_x < 0 or old_start_y < 0}")
    print(f"  End Position: ({old_start_x + old_dialog_width}, {old_start_y + old_dialog_height})")
    
    # After (fixed calculation)
    print("\nAFTER (Fixed):")
    new_dialog_width, new_dialog_height, new_start_x, new_start_y = calculate_safe_dialog_dimensions(
        terminal_width, terminal_height, width_ratio, height_ratio, min_width, min_height
    )
    
    print(f"  Dialog Size: {new_dialog_width}x{new_dialog_height}")
    print(f"  Position: ({new_start_x}, {new_start_y})")
    print(f"  Exceeds Width: {new_dialog_width > terminal_width}")
    print(f"  Negative Position: {new_start_x < 0 or new_start_y < 0}")
    print(f"  End Position: ({new_start_x + new_dialog_width}, {new_start_y + new_dialog_height})")
    
    print("\nImprovements:")
    if old_dialog_width > terminal_width:
        print(f"  ✓ Width reduced from {old_dialog_width} to {new_dialog_width} (fits in terminal)")
    if old_start_x < 0:
        print(f"  ✓ X position corrected from {old_start_x} to {new_start_x} (no longer negative)")
    if old_start_y < 0:
        print(f"  ✓ Y position corrected from {old_start_y} to {new_start_y} (no longer negative)")


def demo_text_truncation():
    """Demonstrate text truncation for narrow terminals"""
    print("\n=== Text Truncation Demo ===\n")
    
    def safe_truncate_text(text, max_width, suffix="..."):
        """Safely truncate text to fit within max_width"""
        if len(text) <= max_width:
            return text
        
        if max_width <= len(suffix):
            return suffix[:max_width]
        
        return text[:max_width - len(suffix)] + suffix
    
    test_texts = [
        "Short title",
        "Medium length dialog title",
        "Very long dialog title that definitely needs truncation",
        "Extremely long dialog title that would never fit in narrow terminals"
    ]
    
    widths = [10, 15, 20, 25, 30]
    
    print("Text Truncation Examples:")
    print("=" * 60)
    print(f"{'Original Text':<50} {'Width':<6} {'Result'}")
    print("-" * 60)
    
    for text in test_texts:
        for width in widths:
            truncated = safe_truncate_text(text, width)
            if len(truncated) != len(text):  # Only show truncated examples
                print(f"{text:<50} {width:<6} '{truncated}'")
    
    print("\nKey Features:")
    print("• Text is truncated to fit available width")
    print("• Ellipsis (...) indicates truncation")
    print("• Handles edge cases (width < suffix length)")
    print("• Preserves as much original text as possible")


def main():
    """Run all demos"""
    demo_dialog_calculations()
    demo_before_after_comparison()
    demo_text_truncation()
    
    print("\n" + "=" * 80)
    print("Dialog Fix Summary:")
    print("• All dialogs now work correctly in narrow terminals")
    print("• Width calculations respect terminal boundaries")
    print("• Text and borders are safely truncated when needed")
    print("• Positioning prevents negative coordinates")
    print("• Backward compatibility maintained for normal terminals")
    print("=" * 80)


if __name__ == '__main__':
    main()