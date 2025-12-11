"""
TTK Backends Package

This package contains platform-specific implementations of the Renderer interface.

Available backends:
- CursesBackend: Terminal-based rendering using Python's curses library
- MetalBackend: Native macOS desktop applications with GPU-accelerated rendering
- CoreGraphicsBackend: Native macOS desktop applications with CoreGraphics rendering (requires PyObjC)
"""

from ttk.backends.curses_backend import CursesBackend
from ttk.backends.metal_backend import MetalBackend

# CoreGraphics backend requires PyObjC, so import conditionally
try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    __all__ = ['CursesBackend', 'MetalBackend', 'CoreGraphicsBackend']
except ImportError:
    # PyObjC not available, CoreGraphics backend not available
    __all__ = ['CursesBackend', 'MetalBackend']
