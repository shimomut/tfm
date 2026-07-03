#!/usr/bin/env python3
"""
Demo: Dialog Scroll Threshold Fix

This demo verifies that dialogs now correctly respect the actual terminal
height when calculating scroll thresholds, instead of using a hardcoded value.

The issue was that BaseListDialog._adjust_scroll() used screen_height = 24
instead of getting the actual terminal dimensions from the renderer.

Test this by:
1. Resize your terminal to different heights
2. Open the search dialog (Ctrl+F)
3. Enter a search pattern that returns many results
4. Use arrow keys to navigate - scroll should adjust correctly based on
   the actual visible area, not a hardcoded threshold
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ttk import TtkApplication, KeyCode
from tfm_config import Config
from tfm_search_dialog import SearchDialog
from tfm_path import Path


class DialogScrollThresholdDemo(TtkApplication):
    """Demo application showing dialog scroll threshold fix"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.search_dialog = SearchDialog(self.config, self.renderer)
        self.message = "Press 'S' to open search dialog, 'Q' to quit"
        self.test_results = []
        
        # Create test directory with many files
        self.test_dir = Path.cwd()
        
    def draw(self):
        """Draw the demo interface"""
        height, width = self.renderer.get_dimensions()
        
        # Clear screen
        self.renderer.clear()
        
        # Draw title
        title = "Dialog Scroll Threshold Fix Demo"
        self.renderer.draw_text(0, (width - len(title)) // 2, title)
        
        # Draw instructions
        instructions = [
            "",
            "This demo verifies that dialogs respect actual terminal height",
            "for scroll calculations instead of using hardcoded values.",
            "",
            "Instructions:",
            "1. Resize your terminal to different heights",
            "2. Press 'S' to open search dialog",
            "3. Enter a search pattern (e.g., '*.py')",
            "4. Use arrow keys to navigate through results",
            "5. Observe that scrolling adjusts correctly based on visible area",
            "",
            f"Current terminal size: {height} rows x {width} columns",
            f"Expected dialog height: {max(15, int(height * 0.7))} rows",
            f"Expected content height: {max(15, int(height * 0.7)) - 6} rows",
            "",
            self.message,
        ]
        
        y = 2
        for line in instructions:
            if y < height:
                self.renderer.draw_text(y, 2, line[:width-4])
                y += 1
        
        # Draw search dialog if active
        if self.search_dialog.is_active:
            self.search_dialog.draw()
        
        self.renderer.refresh()
        
    def handle_key(self, key_code):
        """Handle keyboard input"""
        # Let search dialog handle keys if active
        if self.search_dialog.is_active:
            from ttk import KeyEvent
            event = KeyEvent(key_code)
            if self.search_dialog.handle_key_event(event):
                return True
        
        # Handle demo keys
        if key_code == ord('q') or key_code == ord('Q'):
            return False
        elif key_code == ord('s') or key_code == ord('S'):
            self.search_dialog.show('filename', self.test_dir, self._on_search_result)
            self.message = "Search dialog opened - enter pattern and navigate with arrows"
        
        return True
    
    def _on_search_result(self, result):
        """Callback when search result is selected"""
        if result:
            self.message = f"Selected: {result['relative_path']}"
        else:
            self.message = "Search cancelled - Press 'S' to search again, 'Q' to quit"


def main():
    """Run the demo"""
    print("Starting Dialog Scroll Threshold Fix Demo...")
    print("Resize your terminal to test different heights!")
    print()
    
    app = DialogScrollThresholdDemo()
    app.run()


if __name__ == '__main__':
    main()
