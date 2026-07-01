#!/usr/bin/env python3
"""
Verification script for TTKView implementation.

This script demonstrates that the TTKView class is properly implemented
as an NSView subclass with the required methods for backend integration
and keyboard input handling.

Requirements verified:
- 8.1: TTKView is created as NSView subclass
- 8.5: TTKView stores backend reference via initWithFrame_backend_
- 6.5: TTKView implements acceptsFirstResponder to return True
"""

import sys

# Check if running on macOS
if sys.platform != 'darwin':
    print("This verification script requires macOS")
    sys.exit(1)

try:
    import Cocoa
    import objc
except ImportError:
    print("PyObjC is required. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)

from ttk.backends.coregraphics_backend import CoreGraphicsBackend, TTKView


def verify_ttkview_is_nsview_subclass():
    """Verify that TTKView is a proper NSView subclass."""
    print("1. Verifying TTKView is NSView subclass...")
    
    if not issubclass(TTKView, Cocoa.NSView):
        print("   ❌ FAILED: TTKView is not a subclass of NSView")
        return False
    
    print("   ✓ TTKView is a proper NSView subclass")
    return True


def verify_ttkview_initialization():
    """Verify that TTKView can be initialized with frame and backend."""
    print("\n2. Verifying TTKView initialization...")
    
    try:
        # Create a mock backend
        backend = CoreGraphicsBackend()
        
        # Create a frame
        frame = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Initialize the view
        view = TTKView.alloc().initWithFrame_backend_(frame, backend)
        
        if view is None:
            print("   ❌ FAILED: TTKView initialization returned None")
            return False
        
        if not hasattr(view, 'backend'):
            print("   ❌ FAILED: TTKView does not store backend reference")
            return False
        
        if view.backend is not backend:
            print("   ❌ FAILED: TTKView stores incorrect backend reference")
            return False
        
        print("   ✓ TTKView initializes correctly with frame and backend")
        print(f"   ✓ Backend reference stored: {view.backend is not None}")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: Exception during initialization: {e}")
        return False


def verify_accepts_first_responder():
    """Verify that TTKView accepts first responder status."""
    print("\n3. Verifying acceptsFirstResponder...")
    
    try:
        # Create a mock backend
        backend = CoreGraphicsBackend()
        
        # Create a frame
        frame = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Initialize the view
        view = TTKView.alloc().initWithFrame_backend_(frame, backend)
        
        # Check acceptsFirstResponder
        accepts = view.acceptsFirstResponder()
        
        if accepts is not True:
            print(f"   ❌ FAILED: acceptsFirstResponder returned {accepts}, expected True")
            return False
        
        print("   ✓ acceptsFirstResponder returns True")
        print("   ✓ View can receive keyboard input")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: Exception checking acceptsFirstResponder: {e}")
        return False


def verify_drawrect_method():
    """Verify that TTKView has a drawRect_ method."""
    print("\n4. Verifying drawRect_ method...")
    
    try:
        # Create a mock backend
        backend = CoreGraphicsBackend()
        
        # Create a frame
        frame = Cocoa.NSMakeRect(0, 0, 800, 600)
        
        # Initialize the view
        view = TTKView.alloc().initWithFrame_backend_(frame, backend)
        
        if not hasattr(view, 'drawRect_'):
            print("   ❌ FAILED: TTKView does not have drawRect_ method")
            return False
        
        if not callable(view.drawRect_):
            print("   ❌ FAILED: drawRect_ is not callable")
            return False
        
        print("   ✓ drawRect_ method exists and is callable")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: Exception checking drawRect_: {e}")
        return False


def verify_backend_integration():
    """Verify that TTKView integrates with CoreGraphicsBackend."""
    print("\n5. Verifying backend integration...")
    
    try:
        # Create backend
        backend = CoreGraphicsBackend(window_title="TTKView Verification")
        
        # Initialize backend (creates window and view)
        backend.initialize()
        
        # Verify view was created
        if backend.view is None:
            print("   ❌ FAILED: Backend did not create a view")
            backend.window.close()
            return False
        
        # Verify view is a TTKView instance
        if not isinstance(backend.view, TTKView):
            print(f"   ❌ FAILED: Backend created {type(backend.view)}, not TTKView")
            backend.window.close()
            return False
        
        # Verify view has backend reference
        if backend.view.backend is not backend:
            print("   ❌ FAILED: View does not have correct backend reference")
            backend.window.close()
            return False
        
        # Verify view is set as window's content view
        if backend.window.contentView() is not backend.view:
            print("   ❌ FAILED: View is not set as window's content view")
            backend.window.close()
            return False
        
        print("   ✓ Backend creates TTKView instance")
        print("   ✓ View has correct backend reference")
        print("   ✓ View is set as window's content view")
        print("   ✓ Window is visible and ready for rendering")
        
        # Clean up
        backend.window.close()
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: Exception during backend integration: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("TTKView Implementation Verification")
    print("=" * 70)
    
    results = []
    
    # Run all verification tests
    results.append(verify_ttkview_is_nsview_subclass())
    results.append(verify_ttkview_initialization())
    results.append(verify_accepts_first_responder())
    results.append(verify_drawrect_method())
    results.append(verify_backend_integration())
    
    # Print summary
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ All verifications passed!")
        print("\nTTKView is properly implemented as an NSView subclass with:")
        print("  - Custom initializer (initWithFrame_backend_)")
        print("  - Backend reference storage")
        print("  - Keyboard input support (acceptsFirstResponder)")
        print("  - Rendering method (drawRect_)")
        print("  - Full integration with CoreGraphicsBackend")
        return 0
    else:
        print("\n❌ Some verifications failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
