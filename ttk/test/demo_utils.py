#!/usr/bin/env python3
"""
Demo script for TTK utility functions.

This script demonstrates the usage of platform detection, color conversion,
and parameter validation functions.
"""

from ttk.utils import (
    get_recommended_backend,
    rgb_to_normalized,
    normalized_to_rgb,
    rgb_to_hex,
    hex_to_rgb,
    validate_rgb,
    validate_color_pair_id,
    validate_coordinates,
    validate_dimensions,
    clamp,
    clamp_rgb,
)


def demo_platform_detection():
    """Demonstrate platform detection."""
    print("=" * 60)
    print("Platform Detection Demo")
    print("=" * 60)
    
    backend = get_recommended_backend()
    print(f"Recommended backend for this platform: {backend}")
    print()


def demo_color_conversion():
    """Demonstrate color conversion functions."""
    print("=" * 60)
    print("Color Conversion Demo")
    print("=" * 60)
    
    # RGB to normalized
    rgb = (255, 128, 0)
    normalized = rgb_to_normalized(rgb)
    print(f"RGB {rgb} -> Normalized {normalized}")
    
    # Normalized to RGB
    normalized = (1.0, 0.5, 0.0)
    rgb = normalized_to_rgb(normalized)
    print(f"Normalized {normalized} -> RGB {rgb}")
    
    # RGB to hex
    rgb = (255, 128, 0)
    hex_color = rgb_to_hex(rgb)
    print(f"RGB {rgb} -> Hex {hex_color}")
    
    # Hex to RGB
    hex_color = "#FF8000"
    rgb = hex_to_rgb(hex_color)
    print(f"Hex {hex_color} -> RGB {rgb}")
    
    # Round trip
    original = (64, 128, 192)
    hex_color = rgb_to_hex(original)
    result = hex_to_rgb(hex_color)
    print(f"Round trip: {original} -> {hex_color} -> {result}")
    print()


def demo_validation():
    """Demonstrate parameter validation functions."""
    print("=" * 60)
    print("Parameter Validation Demo")
    print("=" * 60)
    
    # Valid RGB
    try:
        validate_rgb((255, 128, 0))
        print("✓ RGB (255, 128, 0) is valid")
    except ValueError as e:
        print(f"✗ RGB validation failed: {e}")
    
    # Invalid RGB
    try:
        validate_rgb((256, 0, 0))
        print("✗ RGB (256, 0, 0) should have failed validation")
    except ValueError as e:
        print(f"✓ RGB (256, 0, 0) correctly rejected: {e}")
    
    # Valid color pair ID
    try:
        validate_color_pair_id(42)
        print("✓ Color pair ID 42 is valid")
    except ValueError as e:
        print(f"✗ Color pair ID validation failed: {e}")
    
    # Invalid color pair ID
    try:
        validate_color_pair_id(256)
        print("✗ Color pair ID 256 should have failed validation")
    except ValueError as e:
        print(f"✓ Color pair ID 256 correctly rejected: {e}")
    
    # Valid coordinates
    try:
        validate_coordinates(10, 20)
        print("✓ Coordinates (10, 20) are valid")
    except ValueError as e:
        print(f"✗ Coordinate validation failed: {e}")
    
    # Invalid coordinates
    try:
        validate_coordinates(-1, 20)
        print("✗ Coordinates (-1, 20) should have failed validation")
    except ValueError as e:
        print(f"✓ Coordinates (-1, 20) correctly rejected: {e}")
    
    # Valid dimensions
    try:
        validate_dimensions(10, 20)
        print("✓ Dimensions (10, 20) are valid")
    except ValueError as e:
        print(f"✗ Dimension validation failed: {e}")
    
    # Invalid dimensions
    try:
        validate_dimensions(0, 20)
        print("✗ Dimensions (0, 20) should have failed validation")
    except ValueError as e:
        print(f"✓ Dimensions (0, 20) correctly rejected: {e}")
    
    print()


def demo_clamping():
    """Demonstrate clamping functions."""
    print("=" * 60)
    print("Clamping Demo")
    print("=" * 60)
    
    # Clamp within range
    result = clamp(5, 0, 10)
    print(f"clamp(5, 0, 10) = {result} (unchanged)")
    
    # Clamp below range
    result = clamp(-5, 0, 10)
    print(f"clamp(-5, 0, 10) = {result} (clamped to min)")
    
    # Clamp above range
    result = clamp(15, 0, 10)
    print(f"clamp(15, 0, 10) = {result} (clamped to max)")
    
    # Clamp RGB
    rgb = (300, 128, -50)
    clamped = clamp_rgb(rgb)
    print(f"clamp_rgb({rgb}) = {clamped}")
    
    rgb = (-10, 260, 128)
    clamped = clamp_rgb(rgb)
    print(f"clamp_rgb({rgb}) = {clamped}")
    
    print()


def demo_practical_usage():
    """Demonstrate practical usage scenarios."""
    print("=" * 60)
    print("Practical Usage Examples")
    print("=" * 60)
    
    # Example 1: Backend selection
    print("Example 1: Backend Selection")
    backend = get_recommended_backend()
    print(f"  Selected backend: {backend}")
    if backend == 'metal':
        print("  -> Using Metal backend for macOS")
    else:
        print("  -> Using Curses backend for terminal")
    print()
    
    # Example 2: Color scheme conversion
    print("Example 2: Color Scheme Conversion")
    color_scheme = {
        'background': (30, 30, 30),
        'foreground': (220, 220, 220),
        'accent': (64, 128, 255),
    }
    print("  Original RGB colors:")
    for name, rgb in color_scheme.items():
        print(f"    {name}: {rgb}")
    
    print("  Converted to hex:")
    for name, rgb in color_scheme.items():
        hex_color = rgb_to_hex(rgb)
        print(f"    {name}: {hex_color}")
    print()
    
    # Example 3: Safe color operations
    print("Example 3: Safe Color Operations")
    # Simulate color calculation that might overflow
    base_color = (200, 150, 100)
    brightness_boost = 100
    
    # Without clamping (would be invalid)
    unclamped = tuple(c + brightness_boost for c in base_color)
    print(f"  Base color: {base_color}")
    print(f"  Brightness boost: +{brightness_boost}")
    print(f"  Unclamped result: {unclamped} (invalid!)")
    
    # With clamping (safe)
    clamped = clamp_rgb(unclamped)
    print(f"  Clamped result: {clamped} (valid)")
    print()
    
    # Example 4: Parameter validation in a function
    print("Example 4: Parameter Validation in Function")
    
    def draw_colored_rect(row, col, width, height, color):
        """Example function that validates parameters."""
        try:
            validate_coordinates(row, col)
            validate_dimensions(width, height)
            validate_rgb(color)
            print(f"  ✓ Drawing {width}x{height} rectangle at ({row}, {col}) with color {color}")
            return True
        except (ValueError, TypeError) as e:
            print(f"  ✗ Invalid parameters: {e}")
            return False
    
    # Valid call
    draw_colored_rect(10, 20, 30, 40, (255, 128, 0))
    
    # Invalid calls
    draw_colored_rect(-1, 20, 30, 40, (255, 128, 0))  # Negative coordinate
    draw_colored_rect(10, 20, 0, 40, (255, 128, 0))   # Zero dimension
    draw_colored_rect(10, 20, 30, 40, (256, 0, 0))    # Invalid color
    
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "TTK Utility Functions Demo" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    demo_platform_detection()
    demo_color_conversion()
    demo_validation()
    demo_clamping()
    demo_practical_usage()
    
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
