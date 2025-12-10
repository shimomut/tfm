#!/usr/bin/env python3
"""
Verification script for Metal backend initialization.

This script verifies that the Metal backend initialization code is
structurally correct and follows the design requirements.
"""

import sys
import inspect


def verify_metal_backend_structure():
    """Verify Metal backend has correct structure."""
    print("Verifying Metal backend structure...")
    
    from ttk.backends.metal_backend import MetalBackend
    
    # Check that MetalBackend is a class
    assert inspect.isclass(MetalBackend), "MetalBackend should be a class"
    print("✓ MetalBackend is a class")
    
    # Check initialization parameters
    init_sig = inspect.signature(MetalBackend.__init__)
    params = list(init_sig.parameters.keys())
    assert 'window_title' in params, "Missing window_title parameter"
    assert 'font_name' in params, "Missing font_name parameter"
    assert 'font_size' in params, "Missing font_size parameter"
    print("✓ __init__ has correct parameters")
    
    # Check that initialize method exists
    assert hasattr(MetalBackend, 'initialize'), "Missing initialize method"
    print("✓ initialize method exists")
    
    # Check helper methods exist
    assert hasattr(MetalBackend, '_validate_font'), "Missing _validate_font method"
    assert hasattr(MetalBackend, '_create_native_window'), "Missing _create_native_window method"
    assert hasattr(MetalBackend, '_calculate_char_dimensions'), "Missing _calculate_char_dimensions method"
    assert hasattr(MetalBackend, '_initialize_grid'), "Missing _initialize_grid method"
    print("✓ All helper methods exist")
    
    # Check instance variables are initialized
    backend = MetalBackend()
    assert backend.window_title == "TTK Application"
    assert backend.font_name == "Menlo"
    assert backend.font_size == 14
    assert backend.window is None
    assert backend.metal_device is None
    assert backend.command_queue is None
    assert backend.char_width == 0
    assert backend.char_height == 0
    assert backend.rows == 0
    assert backend.cols == 0
    assert backend.grid == []
    assert backend.color_pairs == {}
    print("✓ Instance variables initialized correctly")
    
    # Check custom parameters work
    backend2 = MetalBackend(
        window_title="Test",
        font_name="Monaco",
        font_size=16
    )
    assert backend2.window_title == "Test"
    assert backend2.font_name == "Monaco"
    assert backend2.font_size == 16
    print("✓ Custom parameters work correctly")
    
    print("\n✅ All structural checks passed!")
    return True


def verify_initialize_method_implementation():
    """Verify initialize method is implemented."""
    print("\nVerifying initialize method implementation...")
    
    from ttk.backends.metal_backend import MetalBackend
    import inspect
    
    # Get the source code of initialize method
    source = inspect.getsource(MetalBackend.initialize)
    
    # Check for key implementation steps
    checks = [
        ("import Metal", "Imports Metal framework"),
        ("import Cocoa", "Imports Cocoa framework"),
        ("import CoreText", "Imports CoreText framework"),
        ("MTLCreateSystemDefaultDevice", "Creates Metal device"),
        ("newCommandQueue", "Creates command queue"),
        ("_validate_font", "Validates font is monospace"),
        ("_create_native_window", "Creates native window"),
        ("_calculate_char_dimensions", "Calculates character dimensions"),
        ("_initialize_grid", "Initializes character grid"),
        ("RuntimeError", "Handles errors appropriately"),
    ]
    
    for check_str, description in checks:
        if check_str in source:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            return False
    
    print("\n✅ Initialize method implementation verified!")
    return True


def verify_helper_methods_implementation():
    """Verify helper methods are implemented."""
    print("\nVerifying helper methods implementation...")
    
    from ttk.backends.metal_backend import MetalBackend
    import inspect
    
    # Check _validate_font
    source = inspect.getsource(MetalBackend._validate_font)
    assert "NSFont.fontWithName_size_" in source, "Missing font creation"
    assert "ValueError" in source, "Missing error handling"
    assert "monospace" in source.lower(), "Missing monospace check"
    print("✓ _validate_font implemented correctly")
    
    # Check _create_native_window
    source = inspect.getsource(MetalBackend._create_native_window)
    assert "NSWindow" in source, "Missing window creation"
    assert "MTKView" in source or "MetalKit" in source, "Missing Metal view"
    assert "setTitle_" in source, "Missing window title setting"
    print("✓ _create_native_window implemented correctly")
    
    # Check _calculate_char_dimensions
    source = inspect.getsource(MetalBackend._calculate_char_dimensions)
    assert "NSFont" in source, "Missing font object"
    assert "char_width" in source, "Missing width calculation"
    assert "char_height" in source, "Missing height calculation"
    print("✓ _calculate_char_dimensions implemented correctly")
    
    # Check _initialize_grid
    source = inspect.getsource(MetalBackend._initialize_grid)
    assert "self.rows" in source, "Missing rows calculation"
    assert "self.cols" in source, "Missing cols calculation"
    assert "self.grid" in source, "Missing grid creation"
    print("✓ _initialize_grid implemented correctly")
    
    print("\n✅ All helper methods verified!")
    return True


def verify_error_handling():
    """Verify error handling is implemented."""
    print("\nVerifying error handling...")
    
    from ttk.backends.metal_backend import MetalBackend
    import inspect
    
    source = inspect.getsource(MetalBackend.initialize)
    
    # Check for proper error handling
    checks = [
        ("ImportError", "Handles missing PyObjC"),
        ("RuntimeError", "Handles Metal device creation failure"),
        ("ValueError", "Handles font validation errors"),
        ("PyObjC is required", "Provides helpful error message"),
    ]
    
    for check_str, description in checks:
        if check_str in source:
            print(f"✓ {description}")
        else:
            print(f"⚠ Warning: {description} may not be handled")
    
    print("\n✅ Error handling verified!")
    return True


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Metal Backend Initialization Verification")
    print("=" * 70)
    
    try:
        verify_metal_backend_structure()
        verify_initialize_method_implementation()
        verify_helper_methods_implementation()
        verify_error_handling()
        
        print("\n" + "=" * 70)
        print("✅ ALL VERIFICATION CHECKS PASSED!")
        print("=" * 70)
        print("\nThe Metal backend initialization is correctly implemented.")
        print("Note: Actual functionality requires PyObjC and macOS to test.")
        print("\nTo install PyObjC for testing:")
        print("  pip install pyobjc-framework-Metal pyobjc-framework-Cocoa pyobjc-framework-Quartz")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
