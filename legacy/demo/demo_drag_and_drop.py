#!/usr/bin/env python3
"""
Demo: Drag-and-Drop Support Feature

This demo demonstrates drag-and-drop functionality in TFM, allowing users to
drag files from the file manager to external applications on desktop platforms.
It shows gesture detection, payload building, session management, and error handling.

Requirements:
    - macOS (CoreGraphics backend) - drag-and-drop only works in desktop mode
    - External application to drop files into (Finder, TextEdit, etc.)

Usage:
    # Desktop mode (drag-and-drop supported)
    python demo/demo_drag_and_drop.py --backend coregraphics
    
    # Terminal mode (drag-and-drop not supported - graceful degradation)
    python demo/demo_drag_and_drop.py --backend curses

Test Cases:
    1. Single File Drag:
       - Click and drag on a single file
       - Drop into external application (e.g., Finder)
       - Verify file is copied/moved/opened

    2. Multi-File Drag:
       - Select multiple files (Shift+Down or Space)
       - Click and drag on any selected file
       - Drop into external application
       - Verify all selected files are transferred

    3. Error Cases:
       - Try to drag parent directory marker ("..")
       - Try to drag remote files (simulated with s3:// prefix)
       - Try to drag archive contents (simulated with ::archive:: marker)
       - Try to drag non-existent files

    4. Drag Image:
       - Single file: Shows filename
       - Multiple files: Shows "N files"

    5. Graceful Degradation:
       - Run in terminal mode (curses backend)
       - Verify drag operations are disabled with appropriate message

Expected Behavior:
    - Drag gesture detected after moving mouse 5+ pixels with button held
    - Drag image appears showing file count or filename
    - Files can be dropped into external applications
    - Error messages shown for invalid drag operations
    - Terminal mode gracefully disables drag-and-drop
"""

import sys
import os
from pathlib import Path
import argparse
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import KeyEvent, KeyCode, MouseEvent, MouseEventType, MouseButton, SystemEvent
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.backends.curses_backend import CursesBackend
from ttk.renderer import EventCallback

# Import drag-and-drop components
from tfm_drag_gesture import DragGestureDetector
from tfm_drag_payload import DragPayloadBuilder
from tfm_drag_session import DragSessionManager


class DragDropDemoCallback(EventCallback):
    """Event callback handler for drag-and-drop demo."""
    
    def __init__(self, backend):
        """Initialize the callback handler."""
        self.backend = backend
        self.running = True
        self.current_event = None
    
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


class FileListManager:
    """Simple file list manager for demo."""
    
    def __init__(self, temp_dir: Path):
        """Initialize file list manager."""
        self.temp_dir = temp_dir
        self.files = []
        self.selected_indices = set()
        self.focused_index = 0
        
        # Create demo files
        self._create_demo_files()
    
    def _create_demo_files(self):
        """Create demo files in temp directory."""
        # Create regular files
        for i in range(1, 6):
            file_path = self.temp_dir / f"file{i}.txt"
            file_path.write_text(f"This is demo file {i}\n")
            self.files.append(file_path)
        
        # Create a subdirectory with files
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        for i in range(1, 3):
            file_path = subdir / f"subfile{i}.txt"
            file_path.write_text(f"This is subdirectory file {i}\n")
            self.files.append(file_path)
        
        # Add parent directory marker
        self.files.insert(0, Path(".."))
        
        # Add simulated remote file (for error demo)
        self.files.append(Path("s3://bucket/remote-file.txt"))
        
        # Add simulated archive content (for error demo)
        self.files.append(Path("/path/to/archive.zip::archive::file.txt"))
    
    def get_files(self):
        """Get list of files."""
        return self.files
    
    def get_focused_item(self):
        """Get currently focused file."""
        if 0 <= self.focused_index < len(self.files):
            return self.files[self.focused_index]
        return None
    
    def get_selected_files(self):
        """Get list of selected files."""
        return [self.files[i] for i in sorted(self.selected_indices) if i < len(self.files)]
    
    def move_focus_up(self):
        """Move focus up."""
        if self.focused_index > 0:
            self.focused_index -= 1
    
    def move_focus_down(self):
        """Move focus down."""
        if self.focused_index < len(self.files) - 1:
            self.focused_index += 1
    
    def toggle_selection(self):
        """Toggle selection of focused item."""
        if self.focused_index in self.selected_indices:
            self.selected_indices.remove(self.focused_index)
        else:
            self.selected_indices.add(self.focused_index)
    
    def clear_selection(self):
        """Clear all selections."""
        self.selected_indices.clear()
    
    def is_point_in_file_list(self, col, row, list_bounds):
        """Check if point is in file list area."""
        return (list_bounds['x'] <= col < list_bounds['x'] + list_bounds['width'] and
                list_bounds['y'] <= row < list_bounds['y'] + list_bounds['height'])
    
    def get_file_at_row(self, row, list_bounds):
        """Get file index at given row."""
        relative_row = row - list_bounds['y']
        if 0 <= relative_row < len(self.files):
            return relative_row
        return None


def draw_header(backend, title):
    """Draw header section."""
    rows, cols = backend.get_size()
    backend.draw_text(0, 0, "=" * cols, color_pair=1)
    backend.draw_text(1, 0, title.center(cols), color_pair=1)
    backend.draw_text(2, 0, "=" * cols, color_pair=1)


def draw_file_list(backend, file_manager, list_bounds):
    """Draw file list with selection indicators."""
    files = file_manager.get_files()
    
    # Draw title
    backend.draw_text(list_bounds['y'] - 1, list_bounds['x'], "Files (drag to external app):", color_pair=2)
    
    # Draw files
    for i, file_path in enumerate(files):
        if i >= list_bounds['height']:
            break
        
        row = list_bounds['y'] + i
        
        # Determine display name
        if file_path.name == "..":
            display_name = ".."
        elif str(file_path).startswith("s3://"):
            display_name = f"[REMOTE] {file_path.name}"
        elif "::archive::" in str(file_path):
            display_name = f"[ARCHIVE] {file_path.name}"
        else:
            display_name = file_path.name
        
        # Determine color and prefix
        if i == file_manager.focused_index:
            prefix = ">"
            color = 2  # Yellow (focused)
        else:
            prefix = " "
            color = 1  # Light gray
        
        # Add selection indicator
        if i in file_manager.selected_indices:
            prefix = "*"
            color = 3  # Green (selected)
        
        # Draw file entry
        text = f"{prefix} {display_name}"
        backend.draw_text(row, list_bounds['x'], text[:list_bounds['width']], color_pair=color)


def draw_instructions(backend, start_row, drag_supported):
    """Draw instructions section."""
    rows, cols = backend.get_size()
    
    backend.draw_text(start_row, 2, "Instructions:", color_pair=2)
    
    if drag_supported:
        instructions = [
            "  • Use Up/Down arrows to move focus",
            "  • Press Space to select/deselect files",
            "  • Press 'c' to clear selection",
            "  • Click and drag a file to external app",
            "  • Try dragging parent dir (..) - should fail",
            "  • Try dragging [REMOTE] file - should fail",
            "  • Try dragging [ARCHIVE] file - should fail",
            "  • Press 'q' to quit"
        ]
    else:
        instructions = [
            "  • Drag-and-drop is NOT supported in terminal mode",
            "  • This is expected behavior (graceful degradation)",
            "  • Use desktop mode (--backend coregraphics) for drag support",
            "  • Press 'q' to quit"
        ]
    
    row = start_row + 1
    for instruction in instructions:
        backend.draw_text(row, 2, instruction, color_pair=1)
        row += 1


def draw_status(backend, message, is_error=False):
    """Draw status message at bottom."""
    rows, cols = backend.get_size()
    status_row = rows - 2
    
    # Clear status area
    backend.draw_text(status_row, 0, " " * cols)
    backend.draw_text(status_row + 1, 0, " " * cols)
    
    # Draw status
    backend.draw_text(status_row, 0, "-" * cols, color_pair=1)
    color = 4 if is_error else 1  # Red for errors, light gray for normal
    backend.draw_text(status_row + 1, 0, message[:cols], color_pair=color)


def draw_drag_info(backend, start_row, gesture_detector, drag_manager):
    """Draw drag operation information."""
    backend.draw_text(start_row, 2, "Drag Status:", color_pair=2)
    
    if drag_manager.is_dragging():
        status = "DRAGGING - Drop into external application!"
        color = 3  # Green
    elif gesture_detector.is_dragging():
        status = "Gesture detected, starting drag..."
        color = 2  # Yellow
    else:
        status = "Idle - Click and drag to start"
        color = 1  # Light gray
    
    backend.draw_text(start_row + 1, 4, f"Status: {status}", color_pair=color)


def demo_drag_and_drop(backend_type='coregraphics'):
    """Main demo function."""
    print(f"Drag-and-Drop Support Demo ({backend_type} backend)")
    print("=" * 60)
    print()
    print("This demo demonstrates drag-and-drop functionality in TFM.")
    print()
    print("Features demonstrated:")
    print("  • Drag gesture detection (5+ pixel movement threshold)")
    print("  • Single file drag to external applications")
    print("  • Multi-file drag with selection")
    print("  • Drag image showing file count or filename")
    print("  • Error handling for invalid drag operations:")
    print("    - Parent directory marker (..)")
    print("    - Remote files (S3, SSH)")
    print("    - Archive contents")
    print("  • Graceful degradation in terminal mode")
    print()
    
    if backend_type == 'coregraphics':
        print("Instructions:")
        print("  1. Use Up/Down arrows to navigate files")
        print("  2. Press Space to select multiple files")
        print("  3. Click and drag a file")
        print("  4. Drop into an external app (Finder, TextEdit, etc.)")
        print("  5. Try dragging special files to see error handling")
        print()
        print("Note: You need an external application open to drop files into.")
    else:
        print("Note: Drag-and-drop is not supported in terminal mode.")
        print("This demo will show graceful degradation behavior.")
    
    print()
    print("Press Enter to start the demo...")
    input()
    
    # Create temporary directory for demo files
    temp_dir = Path(tempfile.mkdtemp(prefix="tfm_drag_demo_"))
    print(f"Created demo files in: {temp_dir}")
    
    try:
        # Create backend
        if backend_type == 'coregraphics':
            backend = CoreGraphicsBackend(
                window_title="TFM - Drag-and-Drop Demo",
                font_name="Menlo",
                font_size=14,
                rows=35,
                cols=80
            )
        else:
            backend = CursesBackend()
        
        # Initialize backend
        backend.initialize()
        rows, cols = backend.get_size()
        
        # Initialize colors
        backend.init_color_pair(1, (200, 200, 200), (0, 0, 0))      # Light gray on black
        backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))        # Yellow on black
        backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))          # Green on black
        backend.init_color_pair(4, (255, 0, 0), (0, 0, 0))          # Red on black
        
        # Enable mouse events
        drag_supported = False
        if backend.supports_mouse():
            if backend.enable_mouse_events():
                drag_supported = backend.supports_drag_and_drop()
                if drag_supported:
                    print(f"Drag-and-drop enabled on {backend_type} backend")
                else:
                    print(f"Mouse events enabled but drag-and-drop not supported on {backend_type} backend")
            else:
                print(f"Failed to enable mouse events on {backend_type} backend")
        else:
            print(f"Mouse events not supported on {backend_type} backend")
        
        # Create file manager
        file_manager = FileListManager(temp_dir)
        
        # Create drag-and-drop components
        gesture_detector = DragGestureDetector()
        payload_builder = DragPayloadBuilder()
        drag_manager = DragSessionManager(backend)
        
        # Set up event callback
        callback = DragDropDemoCallback(backend)
        backend.set_event_callback(callback)
        
        # Define file list bounds
        list_bounds = {
            'x': 2,
            'y': 5,
            'width': cols - 4,
            'height': 12
        }
        
        # Drag completion callback
        def on_drag_completed(completed: bool):
            """Handle drag completion."""
            if completed:
                draw_status(backend, "Drag completed successfully! Files were dropped.", is_error=False)
            else:
                draw_status(backend, "Drag was cancelled (dropped outside valid target)", is_error=False)
            backend.refresh()
        
        # Initial draw
        backend.clear()
        draw_header(backend, "Drag-and-Drop Support Demo")
        draw_file_list(backend, file_manager, list_bounds)
        draw_instructions(backend, 18, drag_supported)
        draw_drag_info(backend, 27, gesture_detector, drag_manager)
        
        if drag_supported:
            draw_status(backend, "Ready - Click and drag a file to external application | Press 'q' to quit")
        else:
            draw_status(backend, "Drag-and-drop not supported in this mode | Press 'q' to quit")
        
        backend.refresh()
        
        # Main event loop
        while callback.running:
            event = callback.get_event(timeout_ms=100)
            
            if event is None:
                continue
            
            if isinstance(event, MouseEvent):
                # If drag in progress, ignore other events
                if drag_manager.is_dragging():
                    continue
                
                # Handle button down
                if event.event_type == MouseEventType.BUTTON_DOWN:
                    # Check if click is in file list
                    if file_manager.is_point_in_file_list(event.column, event.row, list_bounds):
                        # Update focus to clicked file
                        file_index = file_manager.get_file_at_row(event.row, list_bounds)
                        if file_index is not None:
                            file_manager.focused_index = file_index
                            draw_file_list(backend, file_manager, list_bounds)
                            backend.refresh()
                        
                        # Start tracking for potential drag
                        if drag_supported:
                            gesture_detector.handle_button_down(event.column, event.row)
                
                # Handle move - check for drag gesture
                elif event.event_type == MouseEventType.MOVE:
                    if drag_supported and gesture_detector.handle_move(event.column, event.row):
                        # Drag gesture detected - initiate drag
                        selected_files = file_manager.get_selected_files()
                        focused_item = file_manager.get_focused_item()
                        
                        # Build payload
                        urls = payload_builder.build_payload(
                            selected_files,
                            focused_item,
                            temp_dir
                        )
                        
                        if urls:
                            # Create drag image text
                            if len(urls) == 1:
                                if focused_item:
                                    drag_text = focused_item.name
                                else:
                                    drag_text = "1 file"
                            else:
                                drag_text = f"{len(urls)} files"
                            
                            # Start drag session
                            success = drag_manager.start_drag(
                                urls,
                                drag_text,
                                completion_callback=on_drag_completed
                            )
                            
                            if success:
                                draw_status(backend, f"Dragging: {drag_text} - Drop into external application!")
                                draw_drag_info(backend, 27, gesture_detector, drag_manager)
                                backend.refresh()
                            else:
                                draw_status(backend, "Failed to start drag - OS rejected the operation", is_error=True)
                                gesture_detector.reset()
                                backend.refresh()
                        else:
                            # Payload building failed - show error
                            error_msg = payload_builder.get_last_error()
                            if error_msg:
                                draw_status(backend, f"Cannot drag: {error_msg}", is_error=True)
                            else:
                                draw_status(backend, "Cannot drag this item", is_error=True)
                            gesture_detector.reset()
                            backend.refresh()
                
                # Handle button up
                elif event.event_type == MouseEventType.BUTTON_UP:
                    was_dragging = gesture_detector.handle_button_up()
                    if not was_dragging:
                        # Was a click, not a drag - already handled focus change
                        pass
                    
                    # Update drag info display
                    draw_drag_info(backend, 27, gesture_detector, drag_manager)
                    backend.refresh()
            
            elif isinstance(event, KeyEvent):
                # Handle keyboard navigation
                if event.char:
                    if event.char.lower() == 'q':
                        # Already handled in callback
                        pass
                    elif event.char == ' ':
                        # Toggle selection
                        file_manager.toggle_selection()
                        draw_file_list(backend, file_manager, list_bounds)
                        
                        selected_count = len(file_manager.selected_indices)
                        if selected_count > 0:
                            draw_status(backend, f"{selected_count} file(s) selected - Click and drag to external app")
                        else:
                            draw_status(backend, "Selection cleared")
                        backend.refresh()
                    elif event.char.lower() == 'c':
                        # Clear selection
                        file_manager.clear_selection()
                        draw_file_list(backend, file_manager, list_bounds)
                        draw_status(backend, "Selection cleared")
                        backend.refresh()
                
                # Handle arrow keys
                if event.key_code == KeyCode.UP:
                    file_manager.move_focus_up()
                    draw_file_list(backend, file_manager, list_bounds)
                    backend.refresh()
                elif event.key_code == KeyCode.DOWN:
                    file_manager.move_focus_down()
                    draw_file_list(backend, file_manager, list_bounds)
                    backend.refresh()
            
            elif isinstance(event, SystemEvent):
                # Already handled in callback
                pass
        
        # Show completion message
        backend.clear()
        draw_header(backend, "Demo Complete!")
        
        completion_msg = [
            "",
            "Drag-and-drop support has been demonstrated:",
            "",
        ]
        
        if drag_supported:
            completion_msg.extend([
                "✓ Drag gesture detection (5+ pixel threshold)",
                "✓ Single file drag to external applications",
                "✓ Multi-file drag with selection support",
                "✓ Drag image showing file count or filename",
                "✓ Error handling for invalid operations:",
                "  - Parent directory marker (..)",
                "  - Remote files (S3, SSH)",
                "  - Archive contents",
                "✓ Session lifecycle management",
                "",
                f"Backend used: {backend_type}",
                "",
                "The drag-and-drop system is fully functional and ready",
                "for use in TFM desktop mode.",
            ])
        else:
            completion_msg.extend([
                "✓ Graceful degradation in terminal mode",
                "✓ Drag-and-drop disabled with appropriate feedback",
                "",
                f"Backend used: {backend_type}",
                "",
                "Drag-and-drop is only available in desktop mode.",
                "Use --backend coregraphics to enable this feature.",
            ])
        
        completion_msg.extend([
            "",
            "Press any key to exit..."
        ])
        
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
        
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up demo files from: {temp_dir}")
        except Exception as e:
            print(f"\nWarning: Could not clean up temp directory: {e}")
        
        print("\nDemo completed")


def main():
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Drag-and-Drop Support Demo')
    parser.add_argument(
        '--backend',
        choices=['coregraphics', 'curses'],
        default='coregraphics',
        help='Backend to use (default: coregraphics)'
    )
    
    args = parser.parse_args()
    demo_drag_and_drop(args.backend)


if __name__ == '__main__':
    main()
