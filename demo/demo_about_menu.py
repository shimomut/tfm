#!/usr/bin/env python3
"""
Demo: About Dialog with Matrix-style Animation

This demo showcases the AboutDialog feature which displays:
- TFM ASCII art logo
- Version number
- GitHub URL
- Matrix-style falling green characters in the background

The Matrix effect creates an animated background with falling characters
similar to the iconic "Matrix" movie visual effect.

Usage:
    PYTHONPATH=.:src:ttk python demo/demo_about_menu.py

Controls:
    - Press any key to close the About dialog
    - Press 'q' to quit the demo
"""

import sys
import os

# Add src and ttk directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from ttk import TtkApplication, KeyCode
from tfm_about_dialog import AboutDialog
from tfm_config import get_config
from tfm_log_manager import getLogger


class AboutDialogDemo(TtkApplication):
    """Demo application showing the About dialog with Matrix animation"""
    
    def __init__(self):
        super().__init__()
        self.logger = getLogger("AboutDemo")
        self.config = get_config()
        self.about_dialog = None
        self.running = True
        
    def on_start(self):
        """Called when application starts"""
        self.logger.info("About Dialog Demo started")
        
        # Create and show the about dialog
        self.about_dialog = AboutDialog(self.config, self.renderer)
        self.about_dialog.show()
        
        # Draw initial frame
        self.mark_dirty()
        
    def on_render(self):
        """Called when rendering is needed"""
        if self.about_dialog and self.about_dialog.is_active:
            self.about_dialog.render(self.renderer)
            # Keep marking dirty for continuous animation
            self.mark_dirty()
        else:
            # Dialog closed, show exit message
            height, width = self.renderer.get_dimensions()
            msg = "About dialog closed. Press 'q' to quit."
            x = (width - len(msg)) // 2
            y = height // 2
            self.renderer.draw_text(y, x, msg)
    
    def on_key_event(self, event):
        """Handle key events"""
        if self.about_dialog and self.about_dialog.is_active:
            # Let dialog handle the event
            consumed = self.about_dialog.handle_key_event(event)
            if consumed:
                self.mark_dirty()
                return True
        
        # Handle quit
        if event.key_code == KeyCode.ESCAPE or (event.char and event.char.lower() == 'q'):
            self.logger.info("Quitting demo")
            self.running = False
            self.quit()
            return True
        
        return False
    
    def on_char_event(self, event):
        """Handle character events"""
        if self.about_dialog and self.about_dialog.is_active:
            consumed = self.about_dialog.handle_char_event(event)
            if consumed:
                self.mark_dirty()
                return True
        return False
    
    def on_system_event(self, event):
        """Handle system events"""
        if self.about_dialog and self.about_dialog.is_active:
            consumed = self.about_dialog.handle_system_event(event)
            if consumed:
                self.mark_dirty()
                return True
        return False
    
    def on_mouse_event(self, event):
        """Handle mouse events"""
        if self.about_dialog and self.about_dialog.is_active:
            consumed = self.about_dialog.handle_mouse_event(event)
            if consumed:
                self.mark_dirty()
                return True
        return False


def main():
    """Run the demo"""
    demo = AboutDialogDemo()
    demo.run()


if __name__ == '__main__':
    main()
