#!/usr/bin/env python3
"""
Demo: QuickEditBar Prompt Shortening

This demo shows how QuickEditBar intelligently shortens prompts using ShorteningRegion
to ensure adequate space for text input, especially in the rename dialog.

The rename dialog uses the format: "Rename '{original_name}' to: "
When space is limited, the " '{original_name}' to" part is automatically hidden,
leaving just "Rename: " to ensure at least 40 chars for the input field.

Run with: PYTHONPATH=.:src:ttk python demo/demo_quick_edit_bar_shortening.py
"""

import sys
from pathlib import Path

# Add src and ttk to path
src_path = Path(__file__).parent.parent / 'src'
ttk_path = Path(__file__).parent.parent / 'ttk'
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(ttk_path))

from ttk import TtkApplication, KeyCode, KeyEvent, ModifierKey
from tfm_quick_edit_bar import QuickEditBar, QuickEditBarHelpers


class QuickEditBarShorteningDemo(TtkApplication):
    """Demo application showing QuickEditBar prompt shortening"""
    
    def __init__(self):
        super().__init__()
        self.dialog = QuickEditBar(renderer=self.renderer)
        self.current_demo = 0
        self.demos = [
            ("Wide terminal - full prompt", 120, "very_long_filename_that_takes_up_space.txt"),
            ("Medium terminal - shortened prompt", 80, "another_long_filename_example.txt"),
            ("Narrow terminal - minimal prompt", 60, "extremely_long_filename_that_would_overflow.txt"),
            ("Very narrow - just 'Rename: '", 50, "super_long_name_with_many_characters.txt"),
        ]
        self.result_text = None
        self.show_next_demo()
    
    def show_next_demo(self):
        """Show the next demo scenario"""
        if self.current_demo >= len(self.demos):
            self.current_demo = 0
        
        demo_name, width, filename = self.demos[self.current_demo]
        
        # Simulate terminal width by setting it in the demo info
        self.demo_info = f"Demo {self.current_demo + 1}/{len(self.demos)}: {demo_name} (width={width})"
        self.demo_width = width
        self.result_text = None
        
        # Show rename dialog
        QuickEditBarHelpers.create_rename_dialog(
            self.dialog,
            original_name=filename,
            current_name=filename
        )
        
        # Set callback to capture result
        original_callback = self.dialog.callback
        def callback_wrapper(text):
            self.result_text = f"Renamed to: {text}"
            if original_callback:
                original_callback(text)
        self.dialog.callback = callback_wrapper
        
        self.dialog.is_active = True
    
    def handle_input(self, event):
        """Handle keyboard input"""
        if not event:
            return False
        
        # Let dialog handle input first
        if self.dialog.is_active:
            handled = self.dialog.handle_input(event)
            if handled:
                return True
        
        # Handle demo navigation
        if isinstance(event, KeyEvent):
            if event.key_code == KeyCode.TAB:
                # Next demo
                self.current_demo += 1
                self.show_next_demo()
                return True
            elif event.key_code == KeyCode.F10:
                # Quit
                return False
        
        return False
    
    def draw(self):
        """Draw the demo"""
        height, width = self.renderer.get_dimensions()
        
        # Clear screen
        self.renderer.clear()
        
        # Draw title
        title = "QuickEditBar Prompt Shortening Demo"
        self.renderer.draw_text(0, (width - len(title)) // 2, title)
        
        # Draw instructions
        instructions = [
            "",
            "This demo shows how rename dialog prompts are intelligently shortened",
            "to ensure adequate space for text input (minimum 40 chars).",
            "",
            f"Current: {self.demo_info}",
            "",
            "The prompt format is: \"Rename '{original_name}' to: \"",
            "When space is limited, the \" '{original_name}' to\" part is hidden.",
            "",
            "Try typing in the input field below.",
            "",
            "Keys:",
            "  TAB       - Next demo scenario",
            "  Enter     - Confirm rename",
            "  ESC       - Cancel",
            "  F10       - Quit demo",
        ]
        
        y = 2
        for line in instructions:
            if y < height - 3:
                self.renderer.draw_text(y, 2, line)
                y += 1
        
        # Show result if available
        if self.result_text:
            y += 1
            self.renderer.draw_text(y, 2, self.result_text)
        
        # Simulate narrow terminal by only drawing in limited width
        # (In real usage, the terminal width would be naturally limited)
        # For demo purposes, we show what it would look like
        demo_width_info = f"[Simulating terminal width: {self.demo_width} chars]"
        self.renderer.draw_text(height - 3, 2, demo_width_info)
        
        # Draw the dialog (it will appear in the status line)
        if self.dialog.is_active:
            # Temporarily override renderer dimensions for demo
            original_get_dimensions = self.renderer.get_dimensions
            self.renderer.get_dimensions = lambda: (height, self.demo_width)
            
            self.dialog.draw()
            
            # Restore original dimensions
            self.renderer.get_dimensions = original_get_dimensions
        
        self.renderer.refresh()


def main():
    """Run the demo"""
    demo = QuickEditBarShorteningDemo()
    demo.run()


if __name__ == '__main__':
    main()
