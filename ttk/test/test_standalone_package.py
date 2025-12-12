#!/usr/bin/env python3
"""
Test script to verify TTK can be used as a standalone library.

This test verifies Requirement 16.5: The library can be used independently
of TFM without any TFM-specific dependencies.
"""

def test_basic_imports():
    """Test that all main TTK components can be imported."""
    try:
        # Import main abstract classes
        from ttk import Renderer, TextAttribute, InputEvent, KeyCode, ModifierKey
        print("✓ Main classes imported successfully")
        
        # Import backends
        from ttk.backends.curses_backend import CursesBackend
        print("✓ CursesBackend imported successfully")
        
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        print("✓ CoreGraphicsBackend imported successfully")
        
        # Import serialization
        from ttk.serialization.command_serializer import (
            serialize_command,
            parse_command,
            pretty_print_command
        )
        print("✓ Serialization functions imported successfully")
        
        # Import utilities
        from ttk.utils.utils import get_recommended_backend
        print("✓ Utility functions imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_no_tfm_dependencies():
    """Verify that TTK has no dependencies on TFM code."""
    import sys
    import importlib.util
    
    # Check if any TFM modules are imported
    tfm_modules = [name for name in sys.modules if 'tfm' in name.lower() and 'ttk' not in name.lower()]
    
    if tfm_modules:
        print(f"✗ Found TFM dependencies: {tfm_modules}")
        return False
    else:
        print("✓ No TFM dependencies found")
        return True


def test_version_info():
    """Test that version information is accessible."""
    try:
        import ttk
        version = ttk.__version__
        author = ttk.__author__
        print(f"✓ TTK version {version} by {author}")
        return True
    except AttributeError as e:
        print(f"✗ Version info missing: {e}")
        return False


def test_backend_selection():
    """Test that backend selection utility works."""
    try:
        from ttk.utils.utils import get_recommended_backend
        backend = get_recommended_backend()
        print(f"✓ Recommended backend: {backend}")
        return True
    except Exception as e:
        print(f"✗ Backend selection failed: {e}")
        return False


def main():
    """Run all standalone package tests."""
    print("Testing TTK as standalone library...")
    print("=" * 60)
    
    tests = [
        ("Basic imports", test_basic_imports),
        ("No TFM dependencies", test_no_tfm_dependencies),
        ("Version information", test_version_info),
        ("Backend selection", test_backend_selection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        results.append(test_func())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ TTK can be used as a standalone library!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
