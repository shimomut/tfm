"""
TTK Backends Package

This package contains platform-specific implementations of the Renderer interface.

Available backends:
- CursesBackend: Terminal-based rendering using Python's curses library
- MetalBackend: Native macOS desktop applications with GPU-accelerated rendering
"""

from ttk.backends.curses_backend import CursesBackend
from ttk.backends.metal_backend import MetalBackend

__all__ = ['CursesBackend', 'MetalBackend']
