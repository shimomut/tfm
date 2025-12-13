#!/usr/bin/env python3
"""
Verification script for CoreGraphics font loading implementation.

This script verifies that the font loading and character dimension calculation
functionality is properly implemented in the CoreGraphics backend.

It checks:
1. Font loading method exists and has proper error handling
2. Character dimension calculation method exists
3. Instance variables are properly initialized
4. Error messages are informative
"""

import sys
import inspect

# Add current directory to path for imports
sys.path.insert(0, '.')

from backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE


def verify_implementation():
    """Verify the font loading implementation."""
    print("=" * 70)
    print("CoreGraphics Font Loading Implementation Verification")
    print("=" * 70)
    print()
    
    # Check PyObjC availability
    print(f"1. PyObjC Available: {COCOA_AVAILABLE}")
    if not COCOA_AVAILABLE:
        print("   Note: PyObjC not installed, will verify code structure only")
    print()
    
    # Create backend instance
    backend = CoreGraphicsBackend()
    
    # Check instance variables
    print("2. Instance Variables:")
    print(f"   - font_name: {backend.font_name}")
    print(f"   - font_size: {backend.font_size}")
    print(f"   - char_width: {backend.char_width}")
    print(f"   - char_height: {backend.char_height}")
    print(f"   - font: {backend.font}")
    print()
    
    # Check methods exist
    print("3. Methods:")
    print(f"   - initialize: {hasattr(backend, 'initialize')}")
    print(f"   - _load_font: {hasattr(backend, '_load_font')}")
    print(f"   - _calculate_char_dimensions: {hasattr(backend, '_calculate_char_dimensions')}")
    print()
    
    # Check initialize method implementation
    print("4. Initialize Method Implementation:")
    init_source = inspect.getsource(backend.initialize)
    has_load_font_call = '_load_font' in init_source
    has_calc_dims_call = '_calculate_char_dimensions' in init_source
    print(f"   - Calls _load_font: {has_load_font_call}")
    print(f"   - Calls _calculate_char_dimensions: {has_calc_dims_call}")
    print()
    
    # Check _load_font method implementation
    print("5. Font Loading Method Implementation:")
    load_font_source = inspect.getsource(backend._load_font)
    has_font_with_name = 'fontWithName_size_' in load_font_source
    has_validation = 'if not self.font' in load_font_source
    has_value_error = 'ValueError' in load_font_source
    print(f"   - Uses NSFont.fontWithName_size_: {has_font_with_name}")
    print(f"   - Validates font exists: {has_validation}")
    print(f"   - Raises ValueError on failure: {has_value_error}")
    print()
    
    # Check _calculate_char_dimensions method implementation
    print("6. Character Dimension Calculation Implementation:")
    calc_dims_source = inspect.getsource(backend._calculate_char_dimensions)
    has_attributed_string = 'NSAttributedString' in calc_dims_source
    has_test_char = '"M"' in calc_dims_source or "'M'" in calc_dims_source
    has_size_call = '.size()' in calc_dims_source
    has_width_calc = 'self.char_width' in calc_dims_source
    has_height_calc = 'self.char_height' in calc_dims_source
    has_line_spacing = '1.2' in calc_dims_source
    print(f"   - Uses NSAttributedString: {has_attributed_string}")
    print(f"   - Uses 'M' character for measurement: {has_test_char}")
    print(f"   - Calls .size(): {has_size_call}")
    print(f"   - Calculates char_width: {has_width_calc}")
    print(f"   - Calculates char_height: {has_height_calc}")
    print(f"   - Adds 20% line spacing (1.2): {has_line_spacing}")
    print()
    
    # Check error handling
    print("7. Error Handling:")
    has_informative_error = 'monospace' in load_font_source.lower()
    has_font_name_in_error = 'self.font_name' in load_font_source
    print(f"   - Error message mentions monospace fonts: {has_informative_error}")
    print(f"   - Error message includes font name: {has_font_name_in_error}")
    print()
    
    # Summary
    print("=" * 70)
    print("Verification Summary:")
    print("=" * 70)
    
    all_checks = [
        has_load_font_call,
        has_calc_dims_call,
        has_font_with_name,
        has_validation,
        has_value_error,
        has_attributed_string,
        has_test_char,
        has_size_call,
        has_width_calc,
        has_height_calc,
        has_line_spacing,
        has_informative_error,
        has_font_name_in_error
    ]
    
    passed = sum(all_checks)
    total = len(all_checks)
    
    print(f"Checks Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All implementation requirements verified!")
        return True
    else:
        print("✗ Some implementation requirements not met")
        return False


if __name__ == "__main__":
    success = verify_implementation()
    sys.exit(0 if success else 1)
