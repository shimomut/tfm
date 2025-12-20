"""
Demo script for character drawing optimization.

This demo provides visual verification of the character drawing optimization
by displaying a full grid of characters with various attributes and allowing
interactive testing.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from ttk.renderer import TextAttribute, EventCallback
    from ttk.input_event import KeyCode, KeyEvent
    import Cocoa
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"CoreGraphics backend not available: {e}")
    BACKEND_AVAILABLE = False


class CharDrawingCallback(EventCallback):
    """Event callback handler for character drawing demo."""
    
    def __init__(self, demo):
        """Initialize the callback handler."""
        self.demo = demo
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle key events."""
        if event.char:
            key = event.char.upper()
            
            if key == 'Q':
                self.demo.running = False
            elif key == 'H':
                self.demo.current_pattern = "help"
                draw_help_screen(self.demo.backend)
            elif key == '1':
                self.demo.current_pattern = "full"
                print("\n--- Switching to Full Grid Pattern ---")
                draw_test_pattern(self.demo.backend, "full")
            elif key == '2':
                self.demo.current_pattern = "colors"
                print("\n--- Switching to Color Pairs Pattern ---")
                draw_test_pattern(self.demo.backend, "colors")
            elif key == '3':
                self.demo.current_pattern = "attributes"
                print("\n--- Switching to Attributes Pattern ---")
                draw_test_pattern(self.demo.backend, "attributes")
            elif key == '4':
                self.demo.current_pattern = "mixed"
                print("\n--- Switching to Mixed Pattern ---")
                draw_test_pattern(self.demo.backend, "mixed")
        
        return True
    
    def on_char_event(self, event) -> bool:
        """Handle character events."""
        return False
    
    def on_system_event(self, event) -> bool:
        """Handle system events."""
        return False
    
    def should_close(self) -> bool:
        """Check if application should quit."""
        return not self.demo.running


def draw_test_pattern(backend, pattern_type="full"):
    """
    Draw various test patterns to demonstrate character drawing.
    
    Args:
        backend: CoreGraphicsBackend instance
        pattern_type: Type of pattern to draw
            - "full": Full grid with all characters
            - "colors": Color gradient demonstration
            - "attributes": Attribute demonstration
            - "mixed": Mixed attributes and colors
    """
    backend.clear()
    
    if pattern_type == "full":
        # Full grid with various characters
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        for row in range(backend.rows):
            for col in range(backend.cols):
                char = chars[(row * backend.cols + col) % len(chars)]
                color_pair = (row % 5) + 1
                
                attributes = 0
                if row % 3 == 0:
                    attributes |= TextAttribute.BOLD
                if row % 4 == 0:
                    attributes |= TextAttribute.UNDERLINE
                if row % 5 == 0:
                    attributes |= TextAttribute.REVERSE
                
                backend.draw_text(row, col, char, color_pair=color_pair, attributes=attributes)
    
    elif pattern_type == "colors":
        # Color gradient demonstration
        backend.draw_text(0, 0, "Color Pairs Demonstration", color_pair=0, attributes=TextAttribute.BOLD)
        
        for i in range(1, 6):
            text = f"Color Pair {i}: " + "█" * 60
            backend.draw_text(i + 1, 2, text, color_pair=i)
    
    elif pattern_type == "attributes":
        # Attribute demonstration
        backend.draw_text(0, 0, "Text Attributes Demonstration", color_pair=0, attributes=TextAttribute.BOLD)
        
        backend.draw_text(2, 2, "Normal text", color_pair=1)
        backend.draw_text(3, 2, "Bold text", color_pair=1, attributes=TextAttribute.BOLD)
        backend.draw_text(4, 2, "Underlined text", color_pair=1, attributes=TextAttribute.UNDERLINE)
        backend.draw_text(5, 2, "Reverse video text", color_pair=1, attributes=TextAttribute.REVERSE)
        backend.draw_text(6, 2, "Bold + Underline", color_pair=1, 
                         attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE)
        backend.draw_text(7, 2, "Bold + Reverse", color_pair=1,
                         attributes=TextAttribute.BOLD | TextAttribute.REVERSE)
        backend.draw_text(8, 2, "All attributes", color_pair=1,
                         attributes=TextAttribute.BOLD | TextAttribute.UNDERLINE | TextAttribute.REVERSE)
    
    elif pattern_type == "mixed":
        # Mixed pattern with various attributes and colors
        backend.draw_text(0, 0, "Mixed Pattern - Performance Test", color_pair=0, attributes=TextAttribute.BOLD)
        
        # Create a checkerboard pattern with different attributes
        for row in range(2, backend.rows):
            for col in range(backend.cols):
                if (row + col) % 2 == 0:
                    char = "█"
                    color_pair = ((row + col) % 5) + 1
                    attributes = 0
                else:
                    char = "▓"
                    color_pair = ((row + col + 1) % 5) + 1
                    attributes = TextAttribute.BOLD
                
                backend.draw_text(row, col, char, color_pair=color_pair, attributes=attributes)
    
    backend.refresh()


def draw_help_screen(backend):
    """Draw help screen with key bindings."""
    backend.clear()
    
    backend.draw_text(0, 0, "Character Drawing Optimization Demo", color_pair=0, attributes=TextAttribute.BOLD)
    backend.draw_text(1, 0, "=" * 80, color_pair=0)
    
    backend.draw_text(3, 2, "This demo demonstrates the character drawing optimization.", color_pair=1)
    backend.draw_text(4, 2, "Press keys to switch between different test patterns:", color_pair=1)
    
    backend.draw_text(6, 4, "1 - Full grid pattern (maximum workload)", color_pair=2)
    backend.draw_text(7, 4, "2 - Color pairs demonstration", color_pair=2)
    backend.draw_text(8, 4, "3 - Text attributes demonstration", color_pair=2)
    backend.draw_text(9, 4, "4 - Mixed pattern (checkerboard)", color_pair=2)
    backend.draw_text(10, 4, "H - Show this help screen", color_pair=2)
    backend.draw_text(11, 4, "Q - Quit", color_pair=2)
    
    backend.draw_text(13, 2, "Performance Information:", color_pair=1, attributes=TextAttribute.BOLD)
    backend.draw_text(14, 4, "Watch the console output for timing information (t4-t3).", color_pair=3)
    backend.draw_text(15, 4, "Baseline: ~30ms (0.03 seconds)", color_pair=3)
    backend.draw_text(16, 4, "Target after optimization: <10ms (0.01 seconds)", color_pair=3)
    
    backend.draw_text(18, 2, "Press any key to continue...", color_pair=4, attributes=TextAttribute.BOLD)
    
    backend.refresh()


def run_demo():
    """
    Run the interactive demo.
    
    This demo allows users to:
    1. View different test patterns
    2. See timing information in real-time
    3. Verify visual correctness
    4. Compare performance before/after optimization
    """
    if not BACKEND_AVAILABLE:
        print("ERROR: CoreGraphics backend not available")
        print("This demo requires macOS and PyObjC")
        return False
    
    print("=" * 70)
    print("Character Drawing Optimization Demo")
    print("=" * 70)
    print()
    print("This demo provides visual verification of character drawing.")
    print("Timing information (t4-t3) will be printed to the console.")
    print()
    print("Starting demo...")
    print()
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="Character Drawing Optimization Demo",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    
    # Create demo state object
    class DemoState:
        def __init__(self):
            self.backend = backend
            self.current_pattern = "help"
            self.running = True
    
    demo = DemoState()
    
    try:
        # Initialize backend
        backend.initialize()
        
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 255), (0, 0, 255))  # White on blue
        backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))      # Yellow on black
        backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))        # Green on black
        backend.init_color_pair(4, (255, 0, 0), (0, 0, 0))        # Red on black
        backend.init_color_pair(5, (0, 255, 255), (0, 0, 0))      # Cyan on black
        
        # Show help screen
        draw_help_screen(backend)
        
        # Set up event callback
        callback = CharDrawingCallback(demo)
        backend.set_event_callback(callback)
        
        # Main event loop
        while demo.running:
            # Process events (delivered via callbacks)
            backend.run_event_loop_iteration(timeout_ms=100)
        
        print("\nDemo complete.")
        return True
        
    finally:
        # Clean up
        backend.shutdown()


if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
