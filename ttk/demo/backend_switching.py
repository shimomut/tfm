#!/usr/bin/env python3
"""
Backend Switching Demo

This demo application demonstrates that TTK applications can switch between
different rendering backends without any changes to the application code.
It shows that the same application logic works identically with both the
curses backend (terminal-based) and the CoreGraphics backend (native macOS).

Usage:
    python ttk/demo/backend_switching.py --backend curses
    python ttk/demo/backend_switching.py --backend coregraphics

The demo displays:
- Text with various colors and attributes
- Shapes (rectangles and lines)
- Input handling
- Window dimensions

All features work identically regardless of which backend is used.
"""

import argparse
import platform
import sys
from pathlib import Path

# Add parent directory to path for standalone execution
if __name__ == '__main__':
    parent_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(parent_dir))

from ttk.backends.curses_backend import CursesBackend
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import InputEvent, KeyCode


class BackendSwitchingDemo:
    """
    Demo application that works with any rendering backend.
    
    This class demonstrates that application code doesn't need to change
    when switching between backends. The same code works with both curses
    and CoreGraphics backends.
    """
    
    def __init__(self, renderer: Renderer):
        """
        Initialize the demo.
        
        Args:
            renderer: The rendering backend to use
        """
        self.renderer = renderer
        self.running = False
        self.frame_count = 0
        
    def initialize_colors(self):
        """Initialize color pairs used by the demo."""
        # Color pair 1: White on black (default)
        self.renderer.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Color pair 2: Red on black
        self.renderer.init_color_pair(2, (255, 0, 0), (0, 0, 0))
        
        # Color pair 3: Green on black
        self.renderer.init_color_pair(3, (0, 255, 0), (0, 0, 0))
        
        # Color pair 4: Blue on black
        self.renderer.init_color_pair(4, (0, 0, 255), (0, 0, 0))
        
        # Color pair 5: Yellow on black
        self.renderer.init_color_pair(5, (255, 255, 0), (0, 0, 0))
        
        # Color pair 6: Cyan on black
        self.renderer.init_color_pair(6, (0, 255, 255), (0, 0, 0))
        
        # Color pair 7: White on blue (header)
        self.renderer.init_color_pair(7, (255, 255, 255), (0, 0, 128))
        
        # Color pair 8: Gray on black
        self.renderer.init_color_pair(8, (128, 128, 128), (0, 0, 0))
    
    def draw_screen(self):
        """Draw the demo screen showing various rendering features."""
        # Clear screen
        self.renderer.clear()
        
        rows, cols = self.renderer.get_dimensions()
        
        # Draw header
        title = "Backend Switching Demo"
        title_x = (cols - len(title)) // 2
        self.renderer.draw_text(0, 0, " " * cols, 7)
        self.renderer.draw_text(0, title_x, title, 7, TextAttribute.BOLD)
        
        row = 2
        
        # Show instructions
        self.renderer.draw_text(row, 0, "This demo works identically with both backends!", 1, TextAttribute.BOLD)
        row += 1
        self.renderer.draw_text(row, 0, "Press 'q' to quit", 8)
        row += 2
        
        # Show window dimensions
        self.renderer.draw_text(row, 0, f"Window: {rows} rows x {cols} columns", 1)
        row += 2
        
        # Color demonstration
        self.renderer.draw_text(row, 0, "Colors:", 1, TextAttribute.BOLD)
        row += 1
        
        colors = [
            (2, "Red"),
            (3, "Green"),
            (4, "Blue"),
            (5, "Yellow"),
            (6, "Cyan"),
        ]
        
        for color_pair, name in colors:
            self.renderer.draw_text(row, 2, f"■ {name}", color_pair)
            row += 1
        
        row += 1
        
        # Text attributes demonstration
        self.renderer.draw_text(row, 0, "Text Attributes:", 1, TextAttribute.BOLD)
        row += 1
        
        self.renderer.draw_text(row, 2, "Normal text", 1, TextAttribute.NORMAL)
        row += 1
        
        self.renderer.draw_text(row, 2, "Bold text", 1, TextAttribute.BOLD)
        row += 1
        
        self.renderer.draw_text(row, 2, "Underline text", 1, TextAttribute.UNDERLINE)
        row += 1
        
        self.renderer.draw_text(row, 2, "Reverse text", 1, TextAttribute.REVERSE)
        row += 1
        
        self.renderer.draw_text(
            row, 2, "Bold + Underline", 1,
            TextAttribute.BOLD | TextAttribute.UNDERLINE
        )
        row += 1
        
        row += 1
        
        # Shape demonstration
        if row + 8 < rows and cols >= 30:
            self.renderer.draw_text(row, 0, "Shapes:", 1, TextAttribute.BOLD)
            row += 1
            
            # Outlined rectangle
            self.renderer.draw_text(row, 2, "Rectangle:", 8)
            self.renderer.draw_rect(row, 14, 3, 15, 3, filled=False)
            row += 4
            
            # Horizontal line
            self.renderer.draw_text(row, 2, "Line:", 8)
            self.renderer.draw_hline(row, 14, '-', 20, 5)
            row += 2
        
        # Frame counter
        self.renderer.draw_text(rows - 1, 0, f"Frame: {self.frame_count}", 8)
        
        # Refresh display
        self.renderer.refresh()
        
        self.frame_count += 1
    
    def handle_input(self, event: InputEvent) -> bool:
        """
        Handle input events.
        
        Args:
            event: The input event to handle
            
        Returns:
            True to continue running, False to quit
        """
        # Handle resize events
        if event.key_code == KeyCode.RESIZE:
            return True
        
        # Check for quit command
        if event.char and event.char.lower() == 'q':
            return False
        
        # Check for ESC key
        if event.key_code == KeyCode.ESCAPE:
            return False
        
        return True
    
    def run(self):
        """Run the demo main loop."""
        self.running = True
        
        try:
            # Initialize colors
            self.initialize_colors()
            
            # Draw initial screen
            self.draw_screen()
            
            # Main event loop
            while self.running:
                # Get input with timeout
                event = self.renderer.get_input(timeout_ms=100)
                
                if event is None:
                    # No input - just continue
                    continue
                
                # Handle resize event
                if event.key_code == KeyCode.RESIZE:
                    self.draw_screen()
                    continue
                
                # Handle the input
                if not self.handle_input(event):
                    self.running = False
                    break
                
                # Redraw screen
                self.draw_screen()
                
        except KeyboardInterrupt:
            self.running = False
        finally:
            self.running = False


def create_backend(backend_name: str) -> Renderer:
    """
    Create a rendering backend instance.
    
    Args:
        backend_name: Name of backend ('curses' or 'coregraphics')
        
    Returns:
        Renderer instance
        
    Raises:
        ValueError: If backend is invalid or unavailable
    """
    if backend_name == 'curses':
        return CursesBackend()
    elif backend_name == 'coregraphics':
        # Check if we're on macOS
        if platform.system() != 'Darwin':
            raise ValueError(
                "CoreGraphics backend is only available on macOS. "
                "Use --backend curses for other platforms."
            )
        return CoreGraphicsBackend(
            window_title="Backend Switching Demo - CoreGraphics",
            font_name="Menlo",
            font_size=14
        )
    else:
        raise ValueError(
            f"Unknown backend: {backend_name}. "
            "Valid options are: curses, coregraphics"
        )


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Namespace object with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Backend Switching Demo - Demonstrates backend independence',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This demo shows that the same application code works identically with
different rendering backends. No code changes are needed to switch backends.

Examples:
  # Run with curses backend (terminal-based)
  python ttk/demo/backend_switching.py --backend curses
  
  # Run with CoreGraphics backend (native macOS window)
  python ttk/demo/backend_switching.py --backend coregraphics

The visual output and behavior will be identical regardless of which
backend is used.
        """
    )
    
    parser.add_argument(
        '--backend',
        choices=['curses', 'coregraphics'],
        required=True,
        help='Rendering backend to use'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the demo."""
    # Parse command-line arguments
    args = parse_arguments()
    
    print(f"Starting demo with {args.backend} backend...")
    
    # Create the backend
    try:
        renderer = create_backend(args.backend)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize the backend
    try:
        renderer.initialize()
        print(f"Successfully initialized {args.backend} backend")
    except Exception as e:
        print(f"Error initializing backend: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create and run the demo
    demo = BackendSwitchingDemo(renderer)
    
    try:
        demo.run()
    finally:
        # Always clean up
        renderer.shutdown()
        print(f"Successfully shut down {args.backend} backend")


if __name__ == '__main__':
    main()
