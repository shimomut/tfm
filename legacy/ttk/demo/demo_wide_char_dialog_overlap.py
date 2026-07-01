#!/usr/bin/env python3
"""
Demo: Wide Character Dialog Overlap Fix

This demo demonstrates the fix for wide character rendering when dialog
frames overlap zenkaku characters. It shows how the fix prevents wide
characters from "bleeding through" dialog backgrounds.

The demo displays:
1. A grid with wide characters (Japanese text)
2. A simulated dialog frame that overlaps some of the wide characters
3. Visual confirmation that wide characters are properly cleared

Press any key to cycle through different overlap scenarios.
Press 'q' to quit.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import TtkApplication, KeyEvent, KeyCode


class WideCharDialogOverlapDemo(TtkApplication):
    """Demo application showing wide character dialog overlap fix."""
    
    def __init__(self):
        super().__init__()
        self.scenario = 0
        self.max_scenarios = 3
    
    def setup(self):
        """Set up the demo."""
        self.draw_scenario()
    
    def draw_scenario(self):
        """Draw the current scenario."""
        self.backend.clear()
        
        # Draw title
        title = "Wide Character Dialog Overlap Fix Demo"
        self.backend.draw_text(0, 2, title, color_pair=0)
        self.backend.draw_text(1, 2, "=" * len(title), color_pair=0)
        
        # Draw instructions
        self.backend.draw_text(3, 2, "Press any key to cycle scenarios, 'q' to quit", color_pair=0)
        
        if self.scenario == 0:
            self.draw_scenario_1()
        elif self.scenario == 1:
            self.draw_scenario_2()
        elif self.scenario == 2:
            self.draw_scenario_3()
        
        self.backend.refresh()
    
    def draw_scenario_1(self):
        """Scenario 1: Dialog overlapping single wide character."""
        self.backend.draw_text(5, 2, "Scenario 1: Dialog overlapping single wide character", color_pair=0)
        
        # Draw file list with wide characters
        self.backend.draw_text(7, 2, "File list:", color_pair=0)
        self.backend.draw_text(8, 4, "あいうえお.txt", color_pair=1)
        self.backend.draw_text(9, 4, "かきくけこ.txt", color_pair=1)
        self.backend.draw_text(10, 4, "さしすせそ.txt", color_pair=1)
        
        # Draw dialog frame overlapping the right half of characters
        # Dialog starts at column 10, which overlaps the right half of "う" (columns 8-9)
        self.backend.draw_text(12, 2, "Dialog frame (starts at column 10):", color_pair=0)
        
        # Draw dialog background using draw_hline
        for y in range(8, 11):
            self.backend.draw_hline(y, 10, ' ', 20, color_pair=2)
        
        # Draw dialog border
        self.backend.draw_text(8, 10, "┌──────────────────┐", color_pair=2)
        self.backend.draw_text(9, 10, "│  Dialog Content  │", color_pair=2)
        self.backend.draw_text(10, 10, "└──────────────────┘", color_pair=2)
        
        # Explanation
        self.backend.draw_text(14, 2, "Result: Wide characters are properly cleared where dialog overlaps", color_pair=0)
        self.backend.draw_text(15, 2, "        No 'bleeding through' of characters into dialog area", color_pair=0)
    
    def draw_scenario_2(self):
        """Scenario 2: Dialog overlapping multiple wide characters."""
        self.backend.draw_text(5, 2, "Scenario 2: Dialog overlapping multiple wide characters", color_pair=0)
        
        # Draw file list with wide characters
        self.backend.draw_text(7, 2, "File list:", color_pair=0)
        self.backend.draw_text(8, 4, "日本語ファイル名.txt", color_pair=1)
        self.backend.draw_text(9, 4, "中文文件名称.txt", color_pair=1)
        self.backend.draw_text(10, 4, "한글파일이름.txt", color_pair=1)
        
        # Draw dialog frame overlapping multiple characters
        self.backend.draw_text(12, 2, "Dialog frame (overlaps multiple characters):", color_pair=0)
        
        # Draw dialog background
        for y in range(8, 11):
            self.backend.draw_hline(y, 12, ' ', 25, color_pair=2)
        
        # Draw dialog border
        self.backend.draw_text(8, 12, "┌───────────────────────┐", color_pair=2)
        self.backend.draw_text(9, 12, "│   Larger Dialog Box   │", color_pair=2)
        self.backend.draw_text(10, 12, "└───────────────────────┘", color_pair=2)
        
        # Explanation
        self.backend.draw_text(14, 2, "Result: All overlapped wide characters are properly cleared", color_pair=0)
        self.backend.draw_text(15, 2, "        Dialog background is clean and solid", color_pair=0)
    
    def draw_scenario_3(self):
        """Scenario 3: Partial overlap with mixed content."""
        self.backend.draw_text(5, 2, "Scenario 3: Partial overlap with mixed ASCII and wide chars", color_pair=0)
        
        # Draw file list with mixed content
        self.backend.draw_text(7, 2, "File list:", color_pair=0)
        self.backend.draw_text(8, 4, "readme.txt", color_pair=1)
        self.backend.draw_text(9, 4, "設定ファイル.conf", color_pair=1)
        self.backend.draw_text(10, 4, "data.csv", color_pair=1)
        self.backend.draw_text(11, 4, "ドキュメント.pdf", color_pair=1)
        
        # Draw dialog frame with partial overlap
        self.backend.draw_text(13, 2, "Dialog frame (partial overlap):", color_pair=0)
        
        # Draw dialog background
        for y in range(9, 12):
            self.backend.draw_hline(y, 8, ' ', 22, color_pair=2)
        
        # Draw dialog border
        self.backend.draw_text(9, 8, "┌────────────────────┐", color_pair=2)
        self.backend.draw_text(10, 8, "│  Partial Overlap   │", color_pair=2)
        self.backend.draw_text(11, 8, "└────────────────────┘", color_pair=2)
        
        # Explanation
        self.backend.draw_text(15, 2, "Result: Only overlapped portions are cleared", color_pair=0)
        self.backend.draw_text(16, 2, "        Non-overlapped characters remain intact", color_pair=0)
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        """Handle keyboard input."""
        if event.key == KeyCode.CHAR and event.char == 'q':
            return False  # Quit
        
        # Any other key cycles to next scenario
        self.scenario = (self.scenario + 1) % self.max_scenarios
        self.draw_scenario()
        
        return True


def main():
    """Run the demo."""
    app = WideCharDialogOverlapDemo()
    app.run()


if __name__ == '__main__':
    main()
