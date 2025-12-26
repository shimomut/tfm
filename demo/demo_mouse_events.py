#!/usr/bin/env python3
"""
Demo: Mouse Event Support Feature

This demo demonstrates comprehensive mouse event support in TFM across both
terminal (curses) and desktop (CoreGraphics) modes. It shows mouse event capture,
coordinate transformation, sub-cell positioning, and pane focus switching.

Requirements:
    - For desktop mode: macOS (CoreGraphics backend)
    - For terminal mode: Terminal with mouse support (most modern terminals)

Usage:
    # Desktop mode (full mouse support)
    python demo/demo_mouse_events.py --backend coregraphics
    
    # Terminal mode (limited mouse support)
    python demo/demo_mouse_events.py --backend curses

Test Cases:
    1. Mouse Event Capture:
       - Click anywhere in the window
       - Move the mouse around
       - Scroll with mouse wheel (desktop mode only)
       - Double-click (desktop mode only)

    2. Coordinate Transformation:
       - Click in different areas
       - Verify text grid coordinates are displayed
       - Verify sub-cell positioning is shown

    3. Pane Focus Switching:
       - Click in left pane to switch focus
       - Click in right pane to switch focus
       - Verify visual indicators update

    4. Backend Capabilities:
       - View supported event types for current backend
       - Compare desktop vs terminal capabilities

Expected Behavior:
    - Mouse events are captured and displayed in real-time
    - Coordinates are transformed to text grid units
    - Sub-cell positioning shows fractional position within cells
    - Pane focus switches when clicking in pane bounds
    - Visual indicators show which pane has focus
"""

import sys
import os
from pathlib import Path
import argparse
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import KeyEvent, KeyCode, MouseEvent, MouseEventType, MouseButton, SystemEvent
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.backends.curses_backend import CursesBackend
from ttk.renderer import EventCallback


class MouseEventDemoCallback(EventCallback):
    """Event callback handler for mouse event demo."""
    
    def __init__(self, backend):
        """Initialize the callback handler."""
        self.backend = backend
        self.running = True
        self.current_event = None
        self.event_history = []
        self.max_history = 10
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle key events."""
        self.current_event = event
        # Quit on 'q' key
        if event.char and event.char.lower() == 'q':
            self.running = False
            return True
        return False
    
    def on_char_event(self, event) -> bool:
        """Handle character events."""
        return False
    
    def on_mouse_event(self, event: MouseEvent) -> bool:
        """Handle mouse events."""
        self.current_event = event
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        return True
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """Handle system events."""
        if event.is_close():
            self.running = False
            return True
        return False
    
    def should_close(self) -> bool:
        """Check if application should quit."""
        return not self.running
    
    def get_event(self, timeout_ms=-1):
        """Get next event."""
        self.current_event = None
        self.backend.run_event_loop_iteration(timeout_ms)
        return self.current_event


class PaneManager:
    """Simple pane manager for demo."""
    
    def __init__(self, rows, cols):
        """Initialize pane manager."""
        self.rows = rows
        self.cols = cols
        self.active_pane = 'left'  # 'left' or 'right'
        
        # Define pane bounds (split screen vertically)
        self.left_pane_bounds = {
            'x': 0,
            'y': 3,  # Below header
            'width': cols // 2 - 1,
            'height': rows - 5  # Above status bar
        }
        
        self.right_pane_bounds = {
            'x': cols // 2 + 1,
            'y': 3,
            'width': cols // 2 - 1,
            'height': rows - 5
        }
    
    def is_point_in_left_pane(self, col, row):
        """Check if point is in left pane."""
        bounds = self.left_pane_bounds
        return (bounds['x'] <= col < bounds['x'] + bounds['width'] and
                bounds['y'] <= row < bounds['y'] + bounds['height'])
    
    def is_point_in_right_pane(self, col, row):
        """Check if point is in right pane."""
        bounds = self.right_pane_bounds
        return (bounds['x'] <= col < bounds['x'] + bounds['width'] and
                bounds['y'] <= row < bounds['y'] + bounds['height'])
    
    def handle_mouse_click(self, col, row):
        """Handle mouse click for pane switching."""
        if self.is_point_in_left_pane(col, row):
            self.active_pane = 'left'
            return True
        elif self.is_point_in_right_pane(col, row):
            self.active_pane = 'right'
            return True
        return False


def draw_header(backend, title):
    """Draw header section."""
    rows, cols = backend.get_size()
    backend.draw_text(0, 0, "=" * cols, color_pair=1)
    backend.draw_text(1, 0, title.center(cols), color_pair=1)
    backend.draw_text(2, 0, "=" * cols, color_pair=1)


def draw_panes(backend, pane_manager):
    """Draw left and right panes with focus indicators."""
    rows, cols = backend.get_size()
    
    # Draw vertical separator
    separator_col = cols // 2
    for row in range(3, rows - 2):
        backend.draw_text(row, separator_col, "|", color_pair=1)
    
    # Draw left pane
    left_bounds = pane_manager.left_pane_bounds
    left_title = "LEFT PANE"
    if pane_manager.active_pane == 'left':
        left_title = f">>> {left_title} <<<"
        title_color = 2  # Highlight color
    else:
        title_color = 1
    
    backend.draw_text(
        left_bounds['y'],
        left_bounds['x'] + (left_bounds['width'] - len(left_title)) // 2,
        left_title,
        color_pair=title_color
    )
    
    # Draw left pane content
    content_row = left_bounds['y'] + 2
    backend.draw_text(content_row, left_bounds['x'] + 2, "Click here to focus", color_pair=1)
    backend.draw_text(content_row + 1, left_bounds['x'] + 2, "left pane", color_pair=1)
    
    # Draw right pane
    right_bounds = pane_manager.right_pane_bounds
    right_title = "RIGHT PANE"
    if pane_manager.active_pane == 'right':
        right_title = f">>> {right_title} <<<"
        title_color = 2  # Highlight color
    else:
        title_color = 1
    
    backend.draw_text(
        right_bounds['y'],
        right_bounds['x'] + (right_bounds['width'] - len(right_title)) // 2,
        right_title,
        color_pair=title_color
    )
    
    # Draw right pane content
    content_row = right_bounds['y'] + 2
    backend.draw_text(content_row, right_bounds['x'] + 2, "Click here to focus", color_pair=1)
    backend.draw_text(content_row + 1, right_bounds['x'] + 2, "right pane", color_pair=1)


def draw_status_bar(backend, message):
    """Draw status bar at bottom."""
    rows, cols = backend.get_size()
    status_row = rows - 2
    backend.draw_text(status_row, 0, "-" * cols, color_pair=1)
    backend.draw_text(status_row + 1, 0, message[:cols], color_pair=1)


def draw_event_info(backend, event, pane_manager):
    """Draw information about the current mouse event."""
    rows, cols = backend.get_size()
    info_start_row = rows - 12
    
    # Clear event info area
    for row in range(info_start_row, rows - 2):
        backend.draw_text(row, 0, " " * cols)
    
    if event is None:
        backend.draw_text(info_start_row, 2, "No mouse event yet. Move or click the mouse!", color_pair=1)
        return
    
    # Draw event type
    event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
    backend.draw_text(info_start_row, 2, f"Event Type: {event_type_str}", color_pair=2)
    
    # Draw coordinates
    backend.draw_text(info_start_row + 1, 2, f"Grid Position: Column {event.column}, Row {event.row}", color_pair=1)
    
    # Draw sub-cell positioning
    sub_cell_str = f"Sub-cell: ({event.sub_cell_x:.3f}, {event.sub_cell_y:.3f})"
    backend.draw_text(info_start_row + 2, 2, sub_cell_str, color_pair=1)
    
    # Draw button info
    button_str = event.button.name if hasattr(event.button, 'name') else str(event.button)
    backend.draw_text(info_start_row + 3, 2, f"Button: {button_str}", color_pair=1)
    
    # Draw scroll delta (if applicable)
    if event.scroll_delta_x != 0 or event.scroll_delta_y != 0:
        scroll_str = f"Scroll Delta: ({event.scroll_delta_x:.2f}, {event.scroll_delta_y:.2f})"
        backend.draw_text(info_start_row + 4, 2, scroll_str, color_pair=1)
    
    # Draw modifier keys
    modifiers = []
    if event.shift:
        modifiers.append("Shift")
    if event.ctrl:
        modifiers.append("Ctrl")
    if event.alt:
        modifiers.append("Alt")
    if event.meta:
        modifiers.append("Meta")
    
    if modifiers:
        mod_str = f"Modifiers: {', '.join(modifiers)}"
        backend.draw_text(info_start_row + 5, 2, mod_str, color_pair=1)
    
    # Draw pane info
    in_left = pane_manager.is_point_in_left_pane(event.column, event.row)
    in_right = pane_manager.is_point_in_right_pane(event.column, event.row)
    
    if in_left:
        pane_str = "Location: LEFT PANE"
    elif in_right:
        pane_str = "Location: RIGHT PANE"
    else:
        pane_str = "Location: Outside panes"
    
    backend.draw_text(info_start_row + 6, 2, pane_str, color_pair=2)
    
    # Draw active pane
    active_str = f"Active Pane: {pane_manager.active_pane.upper()}"
    backend.draw_text(info_start_row + 7, 2, active_str, color_pair=2)


def draw_capabilities(backend, start_row):
    """Draw backend capabilities information."""
    rows, cols = backend.get_size()
    
    backend.draw_text(start_row, 2, "Backend Capabilities:", color_pair=2)
    
    if backend.supports_mouse():
        backend.draw_text(start_row + 1, 4, "✓ Mouse events supported", color_pair=1)
        
        supported_events = backend.get_supported_mouse_events()
        backend.draw_text(start_row + 2, 4, "Supported event types:", color_pair=1)
        
        row = start_row + 3
        for event_type in MouseEventType:
            if event_type in supported_events:
                status = "✓"
                color = 2
            else:
                status = "✗"
                color = 1
            
            event_name = event_type.value if hasattr(event_type, 'value') else str(event_type)
            backend.draw_text(row, 6, f"{status} {event_name}", color_pair=color)
            row += 1
    else:
        backend.draw_text(start_row + 1, 4, "✗ Mouse events not supported", color_pair=1)


def demo_mouse_events(backend_type='coregraphics'):
    """Main demo function."""
    print(f"Mouse Event Support Demo ({backend_type} backend)")
    print("=" * 60)
    print()
    print("This demo demonstrates mouse event support in TFM.")
    print()
    print("Features demonstrated:")
    print("  • Mouse event capture (click, move, wheel, double-click)")
    print("  • Coordinate transformation to text grid")
    print("  • Sub-cell positioning within cells")
    print("  • Pane focus switching via mouse clicks")
    print("  • Backend capability detection")
    print()
    print("Instructions:")
    print("  • Move the mouse around to see coordinate updates")
    print("  • Click in left or right pane to switch focus")
    print("  • Try different mouse buttons and scroll wheel")
    print("  • Press 'q' to quit")
    print()
    print("Press Enter to start the demo...")
    input()
    
    # Create backend
    if backend_type == 'coregraphics':
        backend = CoreGraphicsBackend(
            window_title="TFM - Mouse Event Demo",
            font_name="Menlo",
            font_size=14,
            rows=30,
            cols=100
        )
    else:
        backend = CursesBackend()
    
    try:
        # Initialize backend
        backend.initialize()
        rows, cols = backend.get_size()
        
        # Initialize colors
        backend.init_color_pair(1, (200, 200, 200), (0, 0, 0))      # Light gray on black
        backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))        # Yellow on black
        backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))          # Green on black
        
        # Enable mouse events
        if backend.supports_mouse():
            if backend.enable_mouse_events():
                print(f"Mouse events enabled on {backend_type} backend")
            else:
                print(f"Failed to enable mouse events on {backend_type} backend")
                return
        else:
            print(f"Mouse events not supported on {backend_type} backend")
            return
        
        # Create pane manager
        pane_manager = PaneManager(rows, cols)
        
        # Set up event callback
        callback = MouseEventDemoCallback(backend)
        backend.set_event_callback(callback)
        
        # Initial draw
        backend.clear()
        draw_header(backend, "Mouse Event Support Demo")
        draw_panes(backend, pane_manager)
        draw_capabilities(backend, 5)
        draw_status_bar(backend, "Move mouse or click to see events | Press 'q' to quit")
        backend.refresh()
        
        # Main event loop
        last_event = None
        
        while callback.running:
            event = callback.get_event(timeout_ms=100)
            
            if event is None:
                continue
            
            if isinstance(event, MouseEvent):
                # Handle pane focus switching on button down
                if event.event_type == MouseEventType.BUTTON_DOWN:
                    if pane_manager.handle_mouse_click(event.column, event.row):
                        # Redraw panes with updated focus
                        draw_panes(backend, pane_manager)
                
                # Update event info display
                draw_event_info(backend, event, pane_manager)
                backend.refresh()
                
                last_event = event
            
            elif isinstance(event, KeyEvent):
                # Already handled in callback
                pass
            
            elif isinstance(event, SystemEvent):
                # Already handled in callback
                pass
        
        # Show completion message
        backend.clear()
        draw_header(backend, "Demo Complete!")
        
        completion_msg = [
            "",
            "Mouse event support has been demonstrated:",
            "",
            "✓ Mouse event capture across different event types",
            "✓ Coordinate transformation to text grid units",
            "✓ Sub-cell positioning within character cells",
            "✓ Pane focus switching via mouse clicks",
            "✓ Backend capability detection and reporting",
            "",
            f"Backend used: {backend_type}",
            "",
            "The mouse event system is fully functional and ready",
            "for use in TFM.",
            "",
            "Press any key to exit..."
        ]
        
        row = 4
        for line in completion_msg:
            backend.draw_text(row, 2, line, color_pair=1)
            row += 1
        
        backend.refresh()
        
        # Wait for key press
        while True:
            event = callback.get_event(timeout_ms=-1)
            if isinstance(event, KeyEvent) or isinstance(event, SystemEvent):
                break
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        backend.shutdown()
        print("\nDemo completed")


def main():
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Mouse Event Support Demo')
    parser.add_argument(
        '--backend',
        choices=['coregraphics', 'curses'],
        default='coregraphics',
        help='Backend to use (default: coregraphics)'
    )
    
    args = parser.parse_args()
    demo_mouse_events(args.backend)


if __name__ == '__main__':
    main()
