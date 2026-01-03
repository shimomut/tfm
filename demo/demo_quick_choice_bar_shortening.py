#!/usr/bin/env python3
"""
Demo: QuickChoiceBar with ShorteningRegion support

This demo shows how QuickChoiceBar now uses reduce_width and ShorteningRegion
to intelligently shorten long messages while keeping choices visible.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from ttk import TtkApplication, KeyCode, KeyEvent
from tfm_quick_choice_bar import QuickChoiceBar, QuickChoiceBarHelpers
from tfm_string_width import ShorteningRegion
from tfm_colors import get_status_color


class QuickChoiceBarShorteningDemo(TtkApplication):
    """Demo application showing QuickChoiceBar message shortening"""
    
    def __init__(self):
        super().__init__()
        self.quick_choice_bar = QuickChoiceBar(config=None, renderer=self.renderer)
        self.demo_index = 0
        self.result_message = "Press 1-5 to see different shortening demos, Q to quit"
        
    def on_key_event(self, event):
        """Handle keyboard input"""
        if self.quick_choice_bar.is_active:
            # Let quick choice bar handle input
            action, value, apply_to_all = self.quick_choice_bar.handle_input(event)
            
            if action == 'cancel':
                self.quick_choice_bar.exit()
                self.result_message = "Cancelled"
                self.mark_dirty()
            elif action == 'execute':
                self.quick_choice_bar.exit()
                self.result_message = f"Selected: {value}"
                self.mark_dirty()
            elif action == 'selection_changed':
                self.mark_dirty()
            
            return True
        
        # Handle demo selection
        if event.key_code == KeyCode.CHAR and event.char:
            char = event.char.lower()
            
            if char == 'q':
                self.quit()
                return True
            elif char == '1':
                self.show_demo_1()
                return True
            elif char == '2':
                self.show_demo_2()
                return True
            elif char == '3':
                self.show_demo_3()
                return True
            elif char == '4':
                self.show_demo_4()
                return True
            elif char == '5':
                self.show_demo_5()
                return True
        
        return False
    
    def show_demo_1(self):
        """Demo 1: Default right abbreviation (no regions)"""
        message = "This is a very long message that will be shortened using default right abbreviation when the terminal is narrow"
        choices = QuickChoiceBarHelpers.create_yes_no_choices()
        
        def callback(result):
            pass
        
        self.quick_choice_bar.show(message, choices, callback)
        self.result_message = "Demo 1: Default right abbreviation"
        self.mark_dirty()
    
    def show_demo_2(self):
        """Demo 2: Middle abbreviation using ShorteningRegion"""
        message = "This is a very long message that will be shortened using middle abbreviation to preserve both ends"
        
        # Create region for middle abbreviation
        regions = [
            ShorteningRegion(
                start=0,
                end=len(message),
                priority=1,
                strategy='abbreviate',
                abbrev_position='middle'
            )
        ]
        
        choices = QuickChoiceBarHelpers.create_yes_no_choices()
        
        def callback(result):
            pass
        
        self.quick_choice_bar.show(message, choices, callback, shortening_regions=regions)
        self.result_message = "Demo 2: Middle abbreviation"
        self.mark_dirty()
    
    def show_demo_3(self):
        """Demo 3: Preserve important part with priority regions"""
        message = "Unimportant prefix - IMPORTANT MESSAGE - unimportant suffix"
        
        # Create regions: shorten prefix and suffix first (higher priority)
        # Keep important message intact (lower priority)
        regions = [
            ShorteningRegion(
                start=0,
                end=21,  # "Unimportant prefix - "
                priority=2,
                strategy='abbreviate',
                abbrev_position='right'
            ),
            ShorteningRegion(
                start=40,  # " - unimportant suffix"
                end=len(message),
                priority=2,
                strategy='abbreviate',
                abbrev_position='left'
            ),
            ShorteningRegion(
                start=21,
                end=40,  # "IMPORTANT MESSAGE"
                priority=1,
                strategy='abbreviate',
                abbrev_position='middle'
            )
        ]
        
        choices = QuickChoiceBarHelpers.create_ok_cancel_choices()
        
        def callback(result):
            pass
        
        self.quick_choice_bar.show(message, choices, callback, shortening_regions=regions)
        self.result_message = "Demo 3: Priority-based shortening"
        self.mark_dirty()
    
    def show_demo_4(self):
        """Demo 4: File path shortening"""
        message = "Delete file: /home/user/documents/projects/myproject/src/components/Button.tsx?"
        
        # Use filepath mode for intelligent path shortening
        regions = [
            ShorteningRegion(
                start=13,  # Start after "Delete file: "
                end=len(message) - 1,  # Exclude the "?"
                priority=1,
                strategy='abbreviate',
                abbrev_position='middle',
                filepath_mode=True
            )
        ]
        
        choices = QuickChoiceBarHelpers.create_delete_choices()
        
        def callback(result):
            pass
        
        self.quick_choice_bar.show(message, choices, callback, shortening_regions=regions)
        self.result_message = "Demo 4: Filepath shortening"
        self.mark_dirty()
    
    def show_demo_5(self):
        """Demo 5: Using helper with custom regions"""
        filename = "very_long_filename_that_might_need_shortening.txt"
        
        # Create regions for the filename in the message
        message = f"File '{filename}' already exists. What do you want to do?"
        filename_start = message.index(filename)
        
        regions = [
            ShorteningRegion(
                start=filename_start,
                end=filename_start + len(filename),
                priority=1,
                strategy='abbreviate',
                abbrev_position='middle'
            )
        ]
        
        def callback(result):
            pass
        
        QuickChoiceBarHelpers.show_overwrite_dialog(
            self.quick_choice_bar,
            filename,
            callback,
            shortening_regions=regions
        )
        self.result_message = "Demo 5: Helper with custom regions"
        self.mark_dirty()
    
    def draw(self):
        """Draw the demo interface"""
        height, width = self.renderer.get_size()
        
        # Clear screen
        self.renderer.clear()
        
        # Draw title
        title = "QuickChoiceBar ShorteningRegion Demo"
        self.renderer.draw_text(0, (width - len(title)) // 2, title)
        
        # Draw instructions
        instructions = [
            "",
            "This demo shows how QuickChoiceBar uses reduce_width and ShorteningRegion",
            "to intelligently shorten long messages while keeping choices visible.",
            "",
            "Press a number to see different shortening strategies:",
            "",
            "  1 - Default right abbreviation (no regions)",
            "  2 - Middle abbreviation using ShorteningRegion",
            "  3 - Priority-based shortening (preserve important parts)",
            "  4 - Filepath shortening (intelligent path abbreviation)",
            "  5 - Helper method with custom regions",
            "",
            "  Q - Quit",
            "",
            f"Last action: {self.result_message}",
            "",
            "Try resizing your terminal to see how messages adapt!",
        ]
        
        y = 2
        for line in instructions:
            if y < height - 2:
                self.renderer.draw_text(y, 2, line)
                y += 1
        
        # Draw quick choice bar if active
        if self.quick_choice_bar.is_active:
            self.quick_choice_bar.draw(height - 1, width)
        else:
            # Draw status line
            status_color_pair, status_attributes = get_status_color()
            status_line = " " * width
            self.renderer.draw_text(height - 1, 0, status_line, status_color_pair, status_attributes)
            
            help_text = "Press 1-5 for demos, Q to quit"
            self.renderer.draw_text(height - 1, 2, help_text, status_color_pair, status_attributes)
        
        self.renderer.refresh()


def main():
    """Run the demo"""
    app = QuickChoiceBarShorteningDemo()
    app.run()


if __name__ == '__main__':
    main()
