#!/usr/bin/env python3
"""
Verification script for CoreGraphics window creation.

This script directly tests the window creation functionality without pytest.
"""

import sys

# Check platform
if sys.platform != 'darwin':
    print("SKIP: CoreGraphics backend only available on macOS")
    sys.exit(0)

# Try to import CoreGraphics backend
try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
    import Cocoa
except ImportError as e:
    print(f"SKIP: PyObjC not available: {e}")
    sys.exit(0)

if not COCOA_AVAILABLE:
    print("SKIP: PyObjC not available")
    sys.exit(0)

print("Testing CoreGraphics window creation...")
print()

# Test 1: Basic window creation
print("Test 1: Basic window creation")
try:
    backend = CoreGraphicsBackend(window_title="Test Window")
    backend.initialize()
    
    assert backend.window is not None, "Window should be created"
    assert isinstance(backend.window, Cocoa.NSWindow), "Window should be NSWindow instance"
    print("✓ Window created successfully")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: Window title
print("\nTest 2: Window title")
try:
    title = "My Test Application"
    backend = CoreGraphicsBackend(window_title=title)
    backend.initialize()
    
    actual_title = backend.window.title()
    assert actual_title == title, f"Expected title '{title}', got '{actual_title}'"
    print(f"✓ Window title set correctly: '{actual_title}'")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 3: Window dimensions
print("\nTest 3: Window dimensions")
try:
    rows, cols = 30, 100
    backend = CoreGraphicsBackend(rows=rows, cols=cols)
    backend.initialize()
    
    content_rect = backend.window.contentView().frame()
    window_width = content_rect.size.width
    window_height = content_rect.size.height
    
    expected_width = cols * backend.char_width
    expected_height = rows * backend.char_height
    
    print(f"  Character dimensions: {backend.char_width}x{backend.char_height}")
    print(f"  Grid size: {rows}x{cols}")
    print(f"  Expected window size: {expected_width}x{expected_height}")
    print(f"  Actual window size: {window_width}x{window_height}")
    
    # Allow small rounding differences
    assert abs(window_width - expected_width) < 2, "Window width mismatch"
    assert abs(window_height - expected_height) < 2, "Window height mismatch"
    print("✓ Window dimensions calculated correctly")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 4: Window style mask
print("\nTest 4: Window style mask")
try:
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    style_mask = backend.window.styleMask()
    
    checks = [
        (Cocoa.NSWindowStyleMaskTitled, "Title bar"),
        (Cocoa.NSWindowStyleMaskClosable, "Close button"),
        (Cocoa.NSWindowStyleMaskMiniaturizable, "Minimize button"),
        (Cocoa.NSWindowStyleMaskResizable, "Resizable"),
    ]
    
    for flag, name in checks:
        if style_mask & flag:
            print(f"  ✓ {name} enabled")
        else:
            print(f"  ✗ {name} NOT enabled")
            raise AssertionError(f"{name} should be enabled")
    
    print("✓ All window controls configured correctly")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 5: get_dimensions
print("\nTest 5: get_dimensions()")
try:
    rows, cols = 25, 90
    backend = CoreGraphicsBackend(rows=rows, cols=cols)
    backend.initialize()
    
    dimensions = backend.get_dimensions()
    assert dimensions == (rows, cols), f"Expected {(rows, cols)}, got {dimensions}"
    print(f"✓ get_dimensions() returns correct values: {dimensions}")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 6: Grid initialization
print("\nTest 6: Grid initialization")
try:
    rows, cols = 24, 80
    backend = CoreGraphicsBackend(rows=rows, cols=cols)
    backend.initialize()
    
    assert backend.grid is not None, "Grid should be initialized"
    assert len(backend.grid) == rows, f"Grid should have {rows} rows"
    assert len(backend.grid[0]) == cols, f"Grid rows should have {cols} columns"
    
    # Check a few cells
    for r in range(min(3, rows)):
        for c in range(min(3, cols)):
            cell = backend.grid[r][c]
            assert isinstance(cell, tuple), "Cell should be tuple"
            assert len(cell) == 3, "Cell should have 3 elements"
            char, color_pair, attributes = cell
            assert char == ' ', "Cell should be initialized with space"
            assert color_pair == 0, "Cell should use default color pair"
            assert attributes == 0, "Cell should have no attributes"
    
    print(f"✓ Grid initialized correctly: {rows}x{cols}")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 7: Default color pair
print("\nTest 7: Default color pair")
try:
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    assert 0 in backend.color_pairs, "Default color pair (0) should be initialized"
    fg, bg = backend.color_pairs[0]
    assert fg == (255, 255, 255), f"Default foreground should be white, got {fg}"
    assert bg == (0, 0, 0), f"Default background should be black, got {bg}"
    print(f"✓ Default color pair initialized: fg={fg}, bg={bg}")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 8: Window visibility
print("\nTest 8: Window visibility")
try:
    backend = CoreGraphicsBackend()
    backend.initialize()
    
    is_visible = backend.window.isVisible()
    assert is_visible, "Window should be visible after initialization"
    print("✓ Window is visible after initialization")
    
    backend.shutdown()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("All tests passed! ✓")
print("="*60)
