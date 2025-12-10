"""
TTK (TUI Toolkit / Traditional app Toolkit)

A generic, reusable rendering library that supports multiple backends for
character-grid-based applications. TTK provides an abstract rendering API
that allows applications to run on different platforms without modification.

Supported backends:
- Curses: Terminal-based rendering using Python's curses library
- Metal: Native macOS desktop applications with GPU-accelerated rendering
"""

__version__ = "0.1.0"
__author__ = "TFM Development Team"

# Import main abstract classes for convenience
from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import InputEvent, KeyCode, ModifierKey

__all__ = [
    'Renderer',
    'TextAttribute',
    'InputEvent',
    'KeyCode',
    'ModifierKey',
]
