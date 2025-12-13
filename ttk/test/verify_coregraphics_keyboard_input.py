#!/usr/bin/env python3
"""
Verification script for CoreGraphics backend keyboard input handling.

This script creates a simple interactive application that displays
keyboard input events, allowing manual verification of:
- Key code translation
- Modifier key detection
- Timeout modes (blocking, non-blocking, timed)
- Special key handling (arrows, function keys, etc.)

Usage:
    python verify_coregraphics_keyboard_input.py

Controls:
    - Type any key to see its event details
    - Press ESC to exit
"""

import sys

# Check if we're on macOS
if sys.platform != 'darwin':
    print("This verification script requires macOS")
    sys.exit(1)

try:
    import Cocoa
    import objc
except ImportError:
    print("PyObjC is required. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import KeyCode, ModifierKey


def format_modifiers(modifiers):
    """Format modifier flags as a readable string."""
    parts = []
    if modifiers & ModifierKey.SHIFT:
        parts.append("Shift")
    if modifiers & ModifierKey.CONTROL:
        parts.append("Control")
    if modifiers & ModifierKey.ALT:
        parts.append("Alt")
    if modifiers & ModifierKey.COMMAND:
        parts.append("Command")
    
    return " + ".join(parts) if parts else "None"


def format_key_code(key_code):
    """Format key code as a readable string."""
    # Check for special keys
    special_keys = {
        KeyCode.UP: "UP",
        KeyCode.DOWN: "DOWN",
        KeyCode.LEFT: "LEFT",
        KeyCode.RIGHT: "RIGHT",
        KeyCode.HOME: "HOME",
        KeyCode.END: "END",
        KeyCode.PAGE_UP: "PAGE_UP",
        KeyCode.PAGE_DOWN: "PAGE_DOWN",
        KeyCode.DELETE: "DELETE",
        KeyCode.BACKSPACE: "BACKSPACE",
        KeyCode.ENTER: "ENTER",
        KeyCode.ESCAPE: "ESCAPE",
        KeyCode.TAB: "TAB",
        KeyCode.F1: "F1",
        KeyCode.F2: "F2",
        KeyCode.F3: "F3",
        KeyCode.F4: "F4",
        KeyCode.F5: "F5",
        KeyCode.F6: "F6",
        KeyCode.F7: "F7",
        KeyCode.F8: "F8",
        KeyCode.F9: "F9",
        KeyCode.F10: "F10",
        KeyCode.F11: "F11",
        KeyCode.F12: "F12",
    }
    
    if key_code in special_keys:
        return special_keys[key_code]
    
    # Printable character
    if 32 <= key_code <= 126:
        return f"'{chr(key_code)}' (ASCII {key_code})"
    
    return f"Code {key_code}"


def main():
    """Run the keyboard input verification."""
    print("CoreGraphics Backend Keyboard Input Verification")
    print("=" * 60)
    print()
    print("This script will display keyboard input events.")
    print("Press ESC to exit.")
    print()
    print("-" * 60)
    
    # Create and initialize backend
    backend = CoreGraphicsBackend(
        window_title="Keyboard Input Test",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    
    try:
        backend.initialize()
        
        # Draw instructions on the window
        backend.clear()
        backend.draw_text(0, 0, "Keyboard Input Test", color_pair=0)
        backend.draw_text(2, 0, "Press any key to see event details", color_pair=0)
        backend.draw_text(3, 0, "Press ESC to exit", color_pair=0)
        backend.draw_text(5, 0, "-" * 60, color_pair=0)
        backend.refresh()
        
        row = 7
        event_count = 0
        
        # Event loop
        while True:
            # Get input with blocking mode (wait indefinitely)
            event = backend.get_input(timeout_ms=-1)
            
            if event is None:
                continue
            
            event_count += 1
            
            # Check for ESC to exit
            if event.key_code == KeyCode.ESCAPE:
                print("\nESC pressed - exiting")
                break
            
            # Format event details
            key_str = format_key_code(event.key_code)
            mod_str = format_modifiers(event.modifiers)
            char_str = f"'{event.char}'" if event.char else "None"
            
            # Display event details in terminal
            print(f"Event #{event_count}:")
            print(f"  Key: {key_str}")
            print(f"  Modifiers: {mod_str}")
            print(f"  Character: {char_str}")
            print()
            
            # Display event details in window
            if row >= 23:
                # Clear old events and reset
                backend.clear_region(7, 0, 16, 80)
                row = 7
            
            event_text = f"Event #{event_count}: {key_str}"
            if event.modifiers != ModifierKey.NONE:
                event_text += f" ({mod_str})"
            
            backend.draw_text(row, 0, event_text, color_pair=0)
            row += 1
            
            backend.refresh()
        
        print(f"\nTotal events processed: {event_count}")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        backend.shutdown()
        print("Backend shut down")


if __name__ == '__main__':
    main()
