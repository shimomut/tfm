#!/usr/bin/env python3
"""
Simple Standalone Application Using TTK

This demonstrates that TTK can be used completely independently of TFM
to create a simple text-based application.

This is a minimal example showing:
- Backend initialization
- Text rendering
- Input handling
- Color management
- Window management

No TFM-specific code or concepts are used.
"""

import argparse
import platform
import sys
from ttk import Renderer, KeyEvent, KeyCode, ModifierKey, TextAttribute
from ttk.backends.curses_backend import CursesBackend
from ttk.utils import get_recommended_backend


class SimpleTextApp:
    """A simple text-based application using TTK."""
    
    def __init__(self, backend: Renderer):
        self.backend = backend
        self.running = False
        self.message = "Hello from TTK!"
        self.counter = 0
        
    def initialize(self):
        """Initialize the application."""
        self.backend.initialize()
        
        # Initialize some color pairs
        self.backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))      # White on black
        self.backend.init_color_pair(2, (0, 255, 0), (0, 0, 0))          # Green on black
        self.backend.init_color_pair(3, (255, 255, 0), (0, 0, 0))        # Yellow on black
        self.backend.init_color_pair(4, (255, 0, 0), (0, 0, 0))          # Red on black
        
    def draw(self):
        """Draw the application UI."""
        rows, cols = self.backend.get_dimensions()
        
        # Clear screen
        self.backend.clear()
        
        # Draw title
        title = "TTK Standalone Application Demo"
        title_col = (cols - len(title)) // 2
        self.backend.draw_text(0, title_col, title, color_pair=2, 
                              attributes=TextAttribute.BOLD)
        
        # Draw separator
        self.backend.draw_hline(1, 0, '-', cols, color_pair=1)
        
        # Draw message
        msg_row = rows // 2 - 2
        msg_col = (cols - len(self.message)) // 2
        self.backend.draw_text(msg_row, msg_col, self.message, 
                              color_pair=3, attributes=TextAttribute.BOLD)
        
        # Draw counter
        counter_text = f"Counter: {self.counter}"
        counter_col = (cols - len(counter_text)) // 2
        self.backend.draw_text(msg_row + 2, counter_col, counter_text, 
                              color_pair=2)
        
        # Draw instructions
        instructions = [
            "Press SPACE to increment counter",
            "Press 'r' to reset counter",
            "Press 'q' or ESC to quit"
        ]
        
        start_row = rows - len(instructions) - 2
        for i, instruction in enumerate(instructions):
            inst_col = (cols - len(instruction)) // 2
            self.backend.draw_text(start_row + i, inst_col, instruction, 
                                  color_pair=1)
        
        # Draw window dimensions
        dim_text = f"Window: {rows}x{cols}"
        self.backend.draw_text(rows - 1, 0, dim_text, color_pair=1)
        
        # Refresh display
        self.backend.refresh()
        
    def handle_input(self, event: KeyEvent) -> bool:
        """
        Handle input event.
        
        Returns:
            True to continue running, False to quit
        """
        if event.key_code == KeyCode.ESCAPE:
            return False
        
        if event.char == 'q' or event.char == 'Q':
            return False
        
        if event.char == ' ':
            self.counter += 1
            return True
        
        if event.char == 'r' or event.char == 'R':
            self.counter = 0
            return True
        
        if event.key_code == KeyCode.RESIZE:
            # Window was resized, just redraw
            return True
        
        return True
    
    def run(self):
        """Run the application main loop."""
        self.running = True
        
        try:
            while self.running:
                # Draw UI
                self.draw()
                
                # Get input with timeout
                event = self.backend.get_input(timeout_ms=100)
                
                if event:
                    self.running = self.handle_input(event)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.backend.shutdown()
    
    def shutdown(self):
        """Shutdown the application."""
        self.backend.shutdown()


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Namespace object with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='TTK Standalone Application - Demonstrates TTK independence from TFM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect best backend for platform
  python ttk/demo/standalone_app.py
  
  # Use curses backend explicitly
  python ttk/demo/standalone_app.py --backend curses
  
  # Use CoreGraphics backend (macOS only)
  python ttk/demo/standalone_app.py --backend coregraphics
        """
    )
    
    parser.add_argument(
        '--backend',
        choices=['curses', 'coregraphics', 'auto'],
        default='auto',
        help='Rendering backend to use (default: auto)'
    )
    
    return parser.parse_args()


def create_backend(backend_name: str) -> Renderer:
    """
    Create the appropriate rendering backend.
    
    Args:
        backend_name: Name of backend to create ('curses', 'coregraphics', or 'auto')
        
    Returns:
        Renderer instance for the selected backend
        
    Raises:
        ValueError: If backend selection fails or backend is unavailable
    """
    # Auto-detect backend if requested
    if backend_name == 'auto':
        backend_name = get_recommended_backend()
        print(f"Auto-detected backend: {backend_name}")
    
    # Create backend instance
    if backend_name == 'curses':
        return CursesBackend()
    elif backend_name == 'coregraphics':
        # Check if we're on macOS
        if platform.system() != 'Darwin':
            raise ValueError(
                "CoreGraphics backend is only available on macOS. "
                "Use --backend curses for other platforms."
            )
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        return CoreGraphicsBackend(
            window_title="TTK Standalone Application",
            font_name="Menlo",
            font_size=12
        )
    else:
        raise ValueError(
            f"Unknown backend: {backend_name}. "
            "Valid options are: curses, coregraphics, auto"
        )


def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_arguments()
    
    print("Starting TTK Standalone Application...")
    print("This demonstrates TTK can be used without TFM.")
    print()
    
    try:
        # Create backend
        backend = create_backend(args.backend)
        print(f"Using backend: {args.backend}")
        
        # Create and run application
        app = SimpleTextApp(backend)
        
        try:
            app.initialize()
            app.run()
        except Exception as e:
            print(f"Error running application: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        print("\nApplication exited successfully.")
        print("This demonstrates TTK is fully independent from TFM!")
        return 0
        
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
