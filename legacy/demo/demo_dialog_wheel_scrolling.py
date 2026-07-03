#!/usr/bin/env python3
"""
Demo: Dialog Wheel Scrolling Support

Demonstrates mouse wheel scrolling in InfoDialog and list-based dialogs.
Shows how users can scroll through long content using the mouse wheel.
"""

import sys
import os

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from ttk import TtkApplication, KeyEvent, KeyCode
from tfm_info_dialog import InfoDialog
from tfm_list_dialog import ListDialog


class DialogWheelScrollingDemo(TtkApplication):
    """Demo application showing wheel scrolling in dialogs"""
    
    def __init__(self):
        super().__init__()
        self.info_dialog = InfoDialog(None, self.backend)
        self.list_dialog = ListDialog(None, self.backend)
        self.current_dialog = None
        self.show_instructions = True
        
    def handle_key_event(self, event: KeyEvent) -> bool:
        """Handle keyboard input"""
        # If a dialog is active, let it handle the event
        if self.current_dialog and self.current_dialog.is_active:
            result = self.current_dialog.handle_key_event(event)
            if not self.current_dialog.is_active:
                self.current_dialog = None
            return result
        
        # Main menu keys
        if event.char and event.char.lower() == 'i':
            self._show_info_dialog()
            return True
        elif event.char and event.char.lower() == 'l':
            self._show_list_dialog()
            return True
        elif event.char and event.char.lower() == 'q':
            self.quit()
            return True
        
        return False
    
    def handle_mouse_event(self, event) -> bool:
        """Handle mouse events"""
        # If a dialog is active, let it handle the event
        if self.current_dialog and self.current_dialog.is_active:
            return self.current_dialog.handle_mouse_event(event)
        return False
    
    def _show_info_dialog(self):
        """Show InfoDialog with many lines"""
        lines = []
        lines.append("InfoDialog Wheel Scrolling Demo")
        lines.append("")
        lines.append("This dialog demonstrates mouse wheel scrolling support.")
        lines.append("")
        lines.append("Try scrolling with your mouse wheel:")
        lines.append("• Scroll up to move toward the top")
        lines.append("• Scroll down to move toward the bottom")
        lines.append("")
        lines.append("You can also use keyboard navigation:")
        lines.append("• ↑↓ - Move one line at a time")
        lines.append("• Page Up/Down - Move by page")
        lines.append("• Home/End - Jump to top/bottom")
        lines.append("")
        
        # Add many lines to demonstrate scrolling
        for i in range(1, 51):
            lines.append(f"Line {i}: This is sample content to demonstrate scrolling.")
            if i % 10 == 0:
                lines.append("")
                lines.append(f"--- Section {i // 10} ---")
                lines.append("")
        
        lines.append("")
        lines.append("End of content. Press Q or ESC to close.")
        
        self.info_dialog.show("InfoDialog Wheel Scrolling", lines)
        self.current_dialog = self.info_dialog
        self.show_instructions = False
    
    def _show_list_dialog(self):
        """Show ListDialog with many items"""
        items = []
        
        # Add many items to demonstrate scrolling
        for i in range(1, 101):
            items.append(f"Item {i:03d}: Sample list item for wheel scrolling demo")
        
        self.list_dialog.show(
            title="ListDialog Wheel Scrolling",
            items=items,
            prompt="Filter: ",
            on_select=self._on_list_select
        )
        self.current_dialog = self.list_dialog
        self.show_instructions = False
    
    def _on_list_select(self, selected_item):
        """Handle list item selection"""
        # Show selected item in info dialog
        lines = [
            "You selected:",
            "",
            selected_item,
            "",
            "Press Q or ESC to close."
        ]
        self.info_dialog.show("Selection", lines)
        self.current_dialog = self.info_dialog
    
    def draw(self):
        """Draw the demo interface"""
        height, width = self.backend.get_dimensions()
        
        # Clear screen
        for y in range(height):
            self.backend.draw_text(y, 0, " " * width)
        
        if self.show_instructions:
            # Draw instructions
            title = "Dialog Wheel Scrolling Demo"
            self.backend.draw_text(2, (width - len(title)) // 2, title)
            
            instructions = [
                "",
                "This demo shows mouse wheel scrolling support in dialogs.",
                "",
                "Press a key to open a dialog:",
                "",
                "  I - InfoDialog with scrollable content",
                "  L - ListDialog with many items",
                "",
                "Once a dialog is open:",
                "  • Use mouse wheel to scroll up/down",
                "  • Use arrow keys for keyboard navigation",
                "  • Press Q or ESC to close the dialog",
                "",
                "Press Q to quit the demo.",
            ]
            
            start_y = 5
            for i, line in enumerate(instructions):
                if start_y + i < height:
                    x = (width - len(line)) // 2
                    self.backend.draw_text(start_y + i, x, line)
        
        # Draw active dialog if present
        if self.current_dialog and self.current_dialog.is_active:
            self.current_dialog.draw()


def main():
    """Run the demo"""
    demo = DialogWheelScrollingDemo()
    demo.run()


if __name__ == '__main__':
    main()
