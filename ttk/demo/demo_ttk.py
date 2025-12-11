#!/usr/bin/env python3
"""
TTK Demo Application

This demo application demonstrates the TTK library's rendering capabilities
with both curses and Metal backends. It provides a test interface to verify
that both backends work correctly and produce equivalent output.

Usage:
    python ttk/demo/demo_ttk.py [--backend {curses|metal}]
    python -m ttk.demo.demo_ttk [--backend {curses|metal}]

Options:
    --backend    Choose rendering backend (default: auto-detect)
                 - curses: Terminal-based rendering
                 - metal: Native macOS desktop rendering (macOS only)
                 - auto: Automatically select best backend for platform
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
from ttk.backends.metal_backend import MetalBackend
from ttk.utils.utils import get_recommended_backend
from ttk.renderer import Renderer
from ttk.demo.test_interface import create_test_interface


class DemoApplication:
    """Main demo application class."""
    
    def __init__(self, backend_name: str = 'auto'):
        """
        Initialize the demo application.
        
        Args:
            backend_name: Name of backend to use ('curses', 'metal', or 'auto')
        """
        self.backend_name = backend_name
        self.renderer: Renderer = None
        self.running = False
        
    def select_backend(self) -> Renderer:
        """
        Select and create the appropriate rendering backend.
        
        Returns:
            Renderer instance for the selected backend
            
        Raises:
            ValueError: If backend selection fails or backend is unavailable
        """
        # Auto-detect backend if requested
        if self.backend_name == 'auto':
            self.backend_name = get_recommended_backend()
            print(f"Auto-detected backend: {self.backend_name}")
        
        # Create backend instance
        if self.backend_name == 'curses':
            return CursesBackend()
        elif self.backend_name == 'metal':
            # Check if we're on macOS
            if platform.system() != 'Darwin':
                raise ValueError(
                    "Metal backend is only available on macOS. "
                    "Use --backend curses for other platforms."
                )
            return MetalBackend(
                window_title="TTK Demo Application",
                font_name="Monaco",
                font_size=14
            )
        else:
            raise ValueError(
                f"Unknown backend: {self.backend_name}. "
                "Valid options are: curses, metal, auto"
            )
    
    def initialize(self):
        """Initialize the demo application and rendering backend."""
        try:
            # Select and create backend
            self.renderer = self.select_backend()
            
            # Initialize the backend
            self.renderer.initialize()
            
            print(f"Successfully initialized {self.backend_name} backend")
            self.running = True
            
        except Exception as e:
            print(f"Error initializing backend: {e}", file=sys.stderr)
            raise
    
    def shutdown(self):
        """Shutdown the demo application and clean up resources."""
        if self.renderer:
            try:
                self.renderer.shutdown()
                print(f"Successfully shut down {self.backend_name} backend")
            except Exception as e:
                print(f"Error during shutdown: {e}", file=sys.stderr)
        
        self.running = False
    
    def run(self):
        """
        Run the main application loop with the test interface.
        
        This creates and runs the comprehensive test interface that demonstrates
        all TTK rendering capabilities including colors, attributes, shapes,
        input handling, and coordinate system information.
        """
        if not self.running:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        
        try:
            # Create the test interface
            test_interface = create_test_interface(self.renderer)
            
            # Run the test interface
            test_interface.run()
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error in main loop: {e}", file=sys.stderr)
            raise


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Namespace object with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='TTK Demo Application - Test rendering backends',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect best backend for platform
  python ttk/demo/demo_ttk.py
  
  # Use curses backend explicitly
  python ttk/demo/demo_ttk.py --backend curses
  
  # Use Metal backend (macOS only)
  python ttk/demo/demo_ttk.py --backend metal
        """
    )
    
    parser.add_argument(
        '--backend',
        choices=['curses', 'metal', 'auto'],
        default='auto',
        help='Rendering backend to use (default: auto)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the demo application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Create demo application
    app = DemoApplication(backend_name=args.backend)
    
    try:
        # Initialize the application
        app.initialize()
        
        # Run the main loop
        app.run()
        
    finally:
        # Always clean up
        app.shutdown()


if __name__ == '__main__':
    main()
