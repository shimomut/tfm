#!/usr/bin/env python3
"""
Interactive demo for TTK clipboard support.

This demo demonstrates reading from and writing to the system clipboard
in both desktop mode (CoreGraphics) and terminal mode (Curses).

Manual Testing Instructions:
1. Run in desktop mode: python ttk/demo/demo_clipboard.py
2. Follow the on-screen prompts to test clipboard operations
3. Test reading: Copy some text to your system clipboard before running
4. Test writing: The demo will write text and you can verify by pasting elsewhere
5. Observe graceful degradation in terminal mode (if applicable)
"""

import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ttk import TtkApplication, Window, Label, Button, TextEdit, VBox, HBox


class ClipboardDemoApp(TtkApplication):
    """Interactive demo application for clipboard functionality."""
    
    def __init__(self):
        super().__init__()
        self.window = None
        self.status_label = None
        self.clipboard_content_label = None
        self.text_edit = None
        
    def setup(self):
        """Set up the demo UI."""
        # Create main window
        self.window = Window(title="Clipboard Demo", width=80, height=24)
        
        # Check clipboard support
        backend_name = self.renderer.__class__.__name__
        supports_clipboard = self.renderer.supports_clipboard()
        
        # Title and status
        title = Label("TTK Clipboard Support Demo")
        backend_info = Label(f"Backend: {backend_name}")
        support_status = Label(
            f"Clipboard Support: {'✓ Available' if supports_clipboard else '✗ Not Available (Terminal Mode)'}"
        )
        
        # Instructions
        instructions = Label("")
        if supports_clipboard:
            instructions.text = "Instructions: Use buttons below to test clipboard operations"
        else:
            instructions.text = "Note: Clipboard operations will gracefully degrade in terminal mode"
        
        # Status display
        self.status_label = Label("Status: Ready")
        
        # Clipboard content display
        self.clipboard_content_label = Label("Current clipboard: (click 'Read Clipboard' to check)")
        
        # Text input for writing to clipboard
        text_input_label = Label("Enter text to write to clipboard:")
        self.text_edit = TextEdit(width=60, height=3)
        self.text_edit.text = "Hello from TTK! 🎉\nThis text can be copied to the clipboard."
        
        # Buttons
        read_button = Button("Read Clipboard", on_click=self.on_read_clipboard)
        write_button = Button("Write to Clipboard", on_click=self.on_write_clipboard)
        clear_button = Button("Clear Clipboard", on_click=self.on_clear_clipboard)
        quit_button = Button("Quit", on_click=self.on_quit)
        
        # Layout
        button_row = HBox([read_button, write_button, clear_button, quit_button])
        
        layout = VBox([
            title,
            backend_info,
            support_status,
            instructions,
            Label(""),  # Spacer
            self.status_label,
            self.clipboard_content_label,
            Label(""),  # Spacer
            text_input_label,
            self.text_edit,
            Label(""),  # Spacer
            button_row
        ])
        
        self.window.set_content(layout)
        self.add_window(self.window)
    
    def on_read_clipboard(self):
        """Read and display clipboard content."""
        try:
            text = self.renderer.get_clipboard_text()
            
            if not self.renderer.supports_clipboard():
                self.status_label.text = "Status: Clipboard not supported (terminal mode)"
                self.clipboard_content_label.text = "Current clipboard: (not available in terminal mode)"
            elif text:
                # Truncate long text for display
                display_text = text[:100] + "..." if len(text) > 100 else text
                # Replace newlines with visible indicator
                display_text = display_text.replace('\n', '\\n')
                self.status_label.text = f"Status: Read {len(text)} characters from clipboard"
                self.clipboard_content_label.text = f"Current clipboard: {display_text}"
            else:
                self.status_label.text = "Status: Clipboard is empty"
                self.clipboard_content_label.text = "Current clipboard: (empty)"
            
            self.request_redraw()
        except Exception as e:
            self.status_label.text = f"Status: Error reading clipboard: {e}"
            self.request_redraw()
    
    def on_write_clipboard(self):
        """Write text from text edit to clipboard."""
        try:
            text = self.text_edit.text
            success = self.renderer.set_clipboard_text(text)
            
            if not self.renderer.supports_clipboard():
                self.status_label.text = "Status: Clipboard not supported (terminal mode)"
            elif success:
                self.status_label.text = f"Status: Wrote {len(text)} characters to clipboard"
                self.clipboard_content_label.text = "Current clipboard: (updated - click 'Read Clipboard' to verify)"
            else:
                self.status_label.text = "Status: Failed to write to clipboard"
            
            self.request_redraw()
        except Exception as e:
            self.status_label.text = f"Status: Error writing clipboard: {e}"
            self.request_redraw()
    
    def on_clear_clipboard(self):
        """Clear the clipboard by writing an empty string."""
        try:
            success = self.renderer.set_clipboard_text("")
            
            if not self.renderer.supports_clipboard():
                self.status_label.text = "Status: Clipboard not supported (terminal mode)"
            elif success:
                self.status_label.text = "Status: Clipboard cleared"
                self.clipboard_content_label.text = "Current clipboard: (empty)"
            else:
                self.status_label.text = "Status: Failed to clear clipboard"
            
            self.request_redraw()
        except Exception as e:
            self.status_label.text = f"Status: Error clearing clipboard: {e}"
            self.request_redraw()
    
    def on_quit(self):
        """Quit the application."""
        self.quit()


def main():
    """Run the clipboard demo application."""
    print("=" * 80)
    print("TTK Clipboard Support Demo")
    print("=" * 80)
    print()
    print("This demo shows clipboard read/write functionality in TTK.")
    print()
    print("Manual Testing Steps:")
    print("1. Before running, copy some text to your system clipboard")
    print("2. Click 'Read Clipboard' to see the current clipboard content")
    print("3. Edit the text in the text box")
    print("4. Click 'Write to Clipboard' to copy the text")
    print("5. Paste in another application to verify it worked")
    print("6. Click 'Clear Clipboard' to empty the clipboard")
    print("7. Paste in another application to verify it's empty")
    print()
    print("Note: In terminal mode (Curses), clipboard operations will gracefully")
    print("      degrade - reads return empty string, writes return False.")
    print()
    print("=" * 80)
    print()
    
    app = ClipboardDemoApp()
    app.run()


if __name__ == "__main__":
    main()
