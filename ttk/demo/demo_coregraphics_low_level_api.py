"""
Demo: CoreGraphics Backend with Low-Level API Optimization

This demo tests the optimized CoreGraphics backend that uses low-level
CoreGraphics and CoreText APIs instead of high-level NS APIs:

- CGContextFillRect instead of NSRectFill for background drawing
- CTLineDraw instead of NSAttributedString.drawAtPoint_ for text rendering
- CGContextSetRGBFillColor instead of NSColor.setFill for color setting

The low-level APIs should provide better performance by reducing overhead
from the high-level Cocoa wrapper layer.

Usage:
    python3 ttk/demo/demo_coregraphics_low_level_api.py
"""

import sys
import os

# Add parent directory to path to import ttk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.input_event import KeyCode


class DemoApp:
    """Demo application to test low-level CoreGraphics API optimization."""
    
    def __init__(self):
        """Initialize the demo application."""
        self.backend = CoreGraphicsBackend(
            window_title="CoreGraphics Low-Level API Demo",
            font_name="Menlo",
            font_size=14,
            rows=24,
            cols=80
        )
        self.running = True
        self.frame_count = 0
    
    def on_key_event(self, event):
        """Handle key events."""
        # Quit on Escape or Ctrl+C
        if event.key_code == KeyCode.ESCAPE:
            self.running = False
            return True
        
        return False
    
    def on_char_event(self, event):
        """Handle character events."""
        return False
    
    def on_system_event(self, event):
        """Handle system events."""
        pass
    
    def should_close(self):
        """Check if the application should close."""
        return not self.running
    
    def draw_test_content(self):
        """Draw test content to verify low-level API rendering."""
        # Clear screen
        self.backend.clear()
        
        # Initialize color pairs
        self.backend.init_color_pair(1, (255, 255, 255), (0, 100, 200))    # White on blue
        self.backend.init_color_pair(2, (255, 255, 0), (100, 0, 0))        # Yellow on dark red
        self.backend.init_color_pair(3, (0, 255, 0), (0, 0, 0))            # Green on black
        self.backend.init_color_pair(4, (255, 128, 0), (0, 0, 0))          # Orange on black
        
        # Draw title
        title = "CoreGraphics Low-Level API Optimization Demo"
        self.backend.draw_text(0, (80 - len(title)) // 2, title, color_pair=1)
        
        # Draw separator
        self.backend.draw_hline(1, 0, "─", 80, color_pair=1)
        
        # Draw test sections
        self.backend.draw_text(3, 2, "Testing Low-Level CoreGraphics APIs:", color_pair=3)
        
        # Test 1: Background rendering with CGContextFillRect
        self.backend.draw_text(5, 4, "1. Background Rendering (CGContextFillRect):", color_pair=4)
        self.backend.draw_text(6, 6, "This colored background uses CGContextFillRect", color_pair=2)
        self.backend.draw_text(7, 6, "instead of NSRectFill for better performance", color_pair=2)
        
        # Test 2: Text rendering with CTLineDraw
        self.backend.draw_text(9, 4, "2. Text Rendering (CTLineDraw):", color_pair=4)
        self.backend.draw_text(10, 6, "All text is rendered using CTLineDraw with", color_pair=3)
        self.backend.draw_text(11, 6, "CTLineCreateWithAttributedString for optimal", color_pair=3)
        self.backend.draw_text(12, 6, "performance and quality.", color_pair=3)
        
        # Test 3: Color setting with CGContextSetRGBFillColor
        self.backend.draw_text(14, 4, "3. Color Setting (CGContextSetRGBFillColor):", color_pair=4)
        self.backend.draw_text(15, 6, "Colors are set using CGContextSetRGBFillColor", color_pair=1)
        self.backend.draw_text(16, 6, "instead of NSColor.setFill for efficiency", color_pair=1)
        
        # Test 4: Wide character support
        self.backend.draw_text(18, 4, "4. Wide Character Support:", color_pair=4)
        self.backend.draw_text(19, 6, "日本語テスト (Japanese test)", color_pair=3)
        self.backend.draw_text(20, 6, "中文测试 (Chinese test)", color_pair=3)
        
        # Draw footer
        self.backend.draw_hline(22, 0, "─", 80, color_pair=1)
        footer = f"Frame: {self.frame_count} | Press ESC to quit"
        self.backend.draw_text(23, 2, footer, color_pair=1)
        
        # Refresh display
        self.backend.refresh()
        
        self.frame_count += 1
    
    def run(self):
        """Run the demo application."""
        # Initialize backend
        self.backend.initialize()
        
        # Set event callback
        self.backend.set_event_callback(self)
        
        # Draw initial content
        self.draw_test_content()
        
        # Run event loop
        print("CoreGraphics Low-Level API Demo")
        print("=" * 50)
        print("This demo tests the optimized CoreGraphics backend")
        print("using low-level CoreGraphics and CoreText APIs:")
        print("  - CGContextFillRect for backgrounds")
        print("  - CTLineDraw for text rendering")
        print("  - CGContextSetRGBFillColor for colors")
        print()
        print("Press ESC to quit")
        print("=" * 50)
        
        self.backend.run_event_loop()
        
        # Cleanup
        self.backend.shutdown()
        print("\nDemo completed successfully!")


def main():
    """Main entry point."""
    try:
        app = DemoApp()
        app.run()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
