#!/usr/bin/env python3
"""
Diagnostic tool to trace mouse event delivery through the system.

This tool monkey-patches key methods in the event delivery chain to log
when events pass through each stage. This helps identify where events
are being lost or not delivered.

Usage:
    python3 tools/diagnose_mouse_events.py

Then run TFM and try scrolling with the mouse wheel. Check the output
to see which methods are being called.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import before patching
from tfm_main import FileManager, TFMEventCallback
from tfm_log_manager import getLogger

logger = getLogger("MouseDiag")

# Patch 1: Backend _handle_mouse_event
from ttk.backends.coregraphics_backend import CoreGraphicsBackend

original_backend_handle = CoreGraphicsBackend._handle_mouse_event

def patched_backend_handle(self, event):
    event_type = event.type()
    logger.info(f"[1] Backend._handle_mouse_event: event_type={event_type}")
    return original_backend_handle(self, event)

CoreGraphicsBackend._handle_mouse_event = patched_backend_handle

# Patch 2: TFMEventCallback on_mouse_event
original_callback_handle = TFMEventCallback.on_mouse_event

def patched_callback_handle(self, event):
    logger.info(f"[2] TFMEventCallback.on_mouse_event: type={event.event_type}")
    return original_callback_handle(self, event)

TFMEventCallback.on_mouse_event = patched_callback_handle

# Patch 3: FileManager handle_mouse_event
original_fm_handle = FileManager.handle_mouse_event

def patched_fm_handle(self, event):
    logger.info(f"[3] FileManager.handle_mouse_event: type={event.event_type}, row={event.row}, col={event.column}")
    if event.event_type.name == 'WHEEL':
        logger.info(f"    Wheel: delta_x={event.scroll_delta_x}, delta_y={event.scroll_delta_y}")
    result = original_fm_handle(self, event)
    logger.info(f"    Result: {result}")
    return result

FileManager.handle_mouse_event = patched_fm_handle

logger.info("Mouse event diagnostics enabled")
logger.info("Event flow: Backend -> TFMEventCallback -> FileManager")
logger.info("Try scrolling with the mouse wheel and watch for log messages")
logger.info("")

# Run TFM
if __name__ == '__main__':
    fm = FileManager()
    fm.run()
