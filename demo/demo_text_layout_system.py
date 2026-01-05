#!/usr/bin/env python3
"""
Demo script for the Text Layout System.

This script demonstrates all features of the text layout system including:
- All segment types (Abbreviation, Filepath, Truncate, AllOrNothing, AsIs)
- Spacer behavior (expansion and collapse)
- Priority-based shortening and restoration
- Wide character handling (CJK, emoji)
- Color and attribute management
- Helper functions for common layouts

The demo uses TTK's curses backend to render text in a terminal window.
"""

import sys
import time
import curses

# Add src and ttk to path for imports
sys.path.insert(0, 'src')
sys.path.insert(0, 'ttk')

from ttk.ttk_curses_backend import TtkCursesBackend
from tfm_text_layout import (
    draw_text_segments,
    AbbreviationSegment,
    FilepathSegment,
    TruncateSegment,
    AllOrNothingSegment,
    AsIsSegment,
    SpacerSegment,
    create_status_bar_layout,
    create_file_list_item,
    create_dialog_prompt,
    create_three_column_layout,
    create_breadcrumb_path,
    create_key_value_pair
)
from tfm_log_manager import getLogger

# Initialize logger
logger = getLogger("LayoutDemo")


class TextLayoutDemo:
    """Demo application for text layout system."""
    
    def __init__(self, stdscr):
        """Initialize demo with curses screen."""
        self.stdscr = stdscr
        self.backend = TtkCursesBackend(stdscr)
        self.current_demo = 0
        self.demos = [
            self.demo_abbreviation_positions,
            self.demo_filepath_abbreviation,
            self.demo_truncate_segment,
            self.demo_all_or_nothing,
            self.demo_as_is_segment,
            self.demo_spacer_behavior,
            self.demo_priority_shortening,
            self.demo_wide_characters,
            self.demo_color_attributes,
            self.demo_status_bar_helper,
            self.demo_file_list_helper,
            self.demo_dialog_prompt_helper,
            self.demo_three_column_helper,
            self.demo_breadcrumb_helper,
            self.demo_key_value_helper,
            self.demo_complex_layout
        ]
        
        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)
        
        # Hide cursor
        curses.curs_set(0)
    
    def run(self):
        """Run the demo application."""
        while True:
            self.stdscr.clear()
            
            # Show current demo
            demo_func = self.demos[self.current_demo]
            demo_func()
            
            # Show navigation instructions
            height, width = self.stdscr.getmaxyx()
            nav_text = f"Demo {self.current_demo + 1}/{len(self.demos)} | SPACE: Next | Q: Quit"
            self.stdscr.addstr(height - 1, 0, nav_text[:width-1], curses.A_REVERSE)
            
            self.stdscr.refresh()
            
            # Wait for key press
            key = self.stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord(' '):
                self.current_demo = (self.current_demo + 1) % len(self.demos)
    
    def draw_title(self, row: int, title: str):
        """Draw a demo title."""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(row, 0, title, curses.A_BOLD | curses.A_UNDERLINE)
        return row + 2
    
    def draw_label(self, row: int, label: str):
        """Draw a label for a demo section."""
        self.stdscr.addstr(row, 2, label, curses.A_DIM)
        return row + 1
    
    def demo_abbreviation_positions(self):
        """Demonstrate abbreviation with different ellipsis positions."""
        row = 1
        row = self.draw_title(row, "Demo 1: Abbreviation Positions")
        
        text = "This is a very long text that needs to be abbreviated"
        
        # Right position (default)
        row = self.draw_label(row, "Right position (ellipsis at end):")
        segments = [AbbreviationSegment(text, abbrev_position='right')]
        draw_text_segments(self.backend, row, 4, segments, 30, default_color=1)
        row += 2
        
        # Middle position
        row = self.draw_label(row, "Middle position (ellipsis in center):")
        segments = [AbbreviationSegment(text, abbrev_position='middle')]
        draw_text_segments(self.backend, row, 4, segments, 30, default_color=1)
        row += 2
        
        # Left position
        row = self.draw_label(row, "Left position (ellipsis at start):")
        segments = [AbbreviationSegment(text, abbrev_position='left')]
        draw_text_segments(self.backend, row, 4, segments, 30, default_color=1)
        row += 2
        
        # Show at different widths
        row = self.draw_label(row, "Same text at different widths:")
        for width in [50, 40, 30, 20, 10]:
            segments = [AbbreviationSegment(text, abbrev_position='middle')]
            draw_text_segments(self.backend, row, 4, segments, width, default_color=2)
            row += 1
    
    def demo_filepath_abbreviation(self):
        """Demonstrate filepath abbreviation strategy."""
        row = 1
        row = self.draw_title(row, "Demo 2: Filepath Abbreviation")
        
        path = "/home/user/documents/projects/myproject/src/components/Button.tsx"
        
        row = self.draw_label(row, "Full path:")
        segments = [FilepathSegment(path)]
        draw_text_segments(self.backend, row, 4, segments, 70, default_color=1)
        row += 2
        
        row = self.draw_label(row, "Progressively shortened (removes directories):")
        for width in [70, 60, 50, 40, 30, 20]:
            segments = [FilepathSegment(path)]
            draw_text_segments(self.backend, row, 4, segments, width, default_color=3)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Windows path:")
        win_path = "C:\\Users\\John\\Documents\\Projects\\MyApp\\src\\main.py"
        for width in [60, 40, 25]:
            segments = [FilepathSegment(win_path)]
            draw_text_segments(self.backend, row, 4, segments, width, default_color=3)
            row += 1
    
    def demo_truncate_segment(self):
        """Demonstrate truncate strategy (no ellipsis)."""
        row = 1
        row = self.draw_title(row, "Demo 3: Truncate Segment (No Ellipsis)")
        
        text = "This text will be truncated without adding ellipsis"
        
        row = self.draw_label(row, "Truncate vs Abbreviation comparison:")
        
        # Truncate
        self.stdscr.addstr(row, 4, "Truncate:", curses.A_BOLD)
        row += 1
        for width in [50, 40, 30, 20]:
            segments = [TruncateSegment(text)]
            draw_text_segments(self.backend, row, 6, segments, width, default_color=4)
            row += 1
        
        row += 1
        
        # Abbreviation for comparison
        self.stdscr.addstr(row, 4, "Abbreviation:", curses.A_BOLD)
        row += 1
        for width in [50, 40, 30, 20]:
            segments = [AbbreviationSegment(text)]
            draw_text_segments(self.backend, row, 6, segments, width, default_color=2)
            row += 1
    
    def demo_all_or_nothing(self):
        """Demonstrate all-or-nothing strategy."""
        row = 1
        row = self.draw_title(row, "Demo 4: All-or-Nothing Segment")
        
        text = "This segment is either shown in full or not at all"
        
        row = self.draw_label(row, "All-or-nothing behavior:")
        
        for width in [60, 50, 40, 30]:
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            segments = [AllOrNothingSegment(text)]
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=5)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Use case: Optional status indicators")
        
        # Simulate a status bar with optional indicator
        for width in [60, 40, 30]:
            segments = [
                AbbreviationSegment("main.py", priority=0, min_length=5),
                SpacerSegment(),
                AllOrNothingSegment("[Modified]", priority=1),  # Removed first
                SpacerSegment(),
                AbbreviationSegment("1.2 KB", priority=0, min_length=4)
            ]
            self.stdscr.addstr(row, 4, f"Width {width}:")
            draw_text_segments(self.backend, row + 1, 6, segments, width, default_color=1)
            row += 2
    
    def demo_as_is_segment(self):
        """Demonstrate as-is strategy (never shortens)."""
        row = 1
        row = self.draw_title(row, "Demo 5: As-Is Segment (Never Shortens)")
        
        row = self.draw_label(row, "As-is segment always shows full text:")
        
        text = "IMPORTANT: Do not modify"
        
        for width in [40, 30, 20, 15]:
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            segments = [AsIsSegment(text)]
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=5)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Use case: Critical labels that must not be abbreviated")
        
        # Example with mixed segments
        for width in [50, 35, 25]:
            segments = [
                AsIsSegment("ERROR: ", color_pair=5, attributes=curses.A_BOLD),
                AbbreviationSegment("File not found in the specified directory", priority=0)
            ]
            self.stdscr.addstr(row, 4, f"Width {width}:")
            draw_text_segments(self.backend, row + 1, 6, segments, width, default_color=1)
            row += 2
    
    def demo_spacer_behavior(self):
        """Demonstrate spacer expansion and collapse."""
        row = 1
        row = self.draw_title(row, "Demo 6: Spacer Behavior")
        
        row = self.draw_label(row, "Spacers expand to fill available space:")
        
        # Two-column layout with spacer
        for width in [70, 60, 50, 40, 30]:
            segments = [
                AbbreviationSegment("Left text", priority=0),
                SpacerSegment(),
                AbbreviationSegment("Right text", priority=0)
            ]
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=2)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Multiple spacers distribute space equally:")
        
        # Three-column layout with two spacers
        for width in [70, 60, 50]:
            segments = [
                AbbreviationSegment("Left", priority=0),
                SpacerSegment(),
                AbbreviationSegment("Center", priority=0),
                SpacerSegment(),
                AbbreviationSegment("Right", priority=0)
            ]
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=3)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Spacers collapse when shortening is needed:")
        
        for width in [40, 30, 20]:
            segments = [
                AbbreviationSegment("Long left text", priority=0, min_length=5),
                SpacerSegment(),
                AbbreviationSegment("Long right text", priority=0, min_length=5)
            ]
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=4)
            row += 1
    
    def demo_priority_shortening(self):
        """Demonstrate priority-based shortening and restoration."""
        row = 1
        row = self.draw_title(row, "Demo 7: Priority-Based Shortening")
        
        row = self.draw_label(row, "Higher priority (2) shortened before lower priority (0):")
        
        # Three segments with different priorities
        for width in [70, 60, 50, 40, 30, 20]:
            segments = [
                AbbreviationSegment("Priority 0 (kept longest)", priority=0, min_length=8, color_pair=3),
                SpacerSegment(),
                AbbreviationSegment("Priority 1 (medium)", priority=1, min_length=6, color_pair=4),
                SpacerSegment(),
                AbbreviationSegment("Priority 2 (shortened first)", priority=2, min_length=5, color_pair=5)
            ]
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=1)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Restoration happens in reverse priority order:")
        self.stdscr.addstr(row, 4, "(Lower priority restored first when space available)")
        row += 1
    
    def demo_wide_characters(self):
        """Demonstrate wide character handling (CJK, emoji)."""
        row = 1
        row = self.draw_title(row, "Demo 8: Wide Character Support")
        
        row = self.draw_label(row, "CJK characters (2 columns each):")
        
        text_cjk = "Hello 世界 こんにちは 你好"
        for width in [30, 25, 20, 15, 10]:
            segments = [AbbreviationSegment(text_cjk, abbrev_position='middle')]
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=2)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Emoji characters:")
        
        text_emoji = "Files 📁 Documents 📄 Images 🖼️ Music 🎵"
        for width in [40, 30, 20, 15]:
            segments = [AbbreviationSegment(text_emoji, abbrev_position='middle')]
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=3)
            row += 1
        
        row += 1
        row = self.draw_label(row, "Mixed narrow and wide characters:")
        
        text_mixed = "File: 文書.txt Size: 1.2 MB 日期: 2024-01-15"
        for width in [50, 40, 30, 20]:
            segments = [AbbreviationSegment(text_mixed, abbrev_position='middle')]
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=4)
            row += 1
    
    def demo_color_attributes(self):
        """Demonstrate color and attribute management."""
        row = 1
        row = self.draw_title(row, "Demo 9: Colors and Attributes")
        
        row = self.draw_label(row, "Different colors per segment:")
        
        segments = [
            AbbreviationSegment("Red text", color_pair=5),
            SpacerSegment(),
            AbbreviationSegment("Green text", color_pair=3),
            SpacerSegment(),
            AbbreviationSegment("Cyan text", color_pair=2)
        ]
        draw_text_segments(self.backend, row, 4, segments, 60, default_color=1)
        row += 2
        
        row = self.draw_label(row, "Text attributes (bold, underline, reverse):")
        
        segments = [
            AbbreviationSegment("Bold", attributes=curses.A_BOLD),
            SpacerSegment(),
            AbbreviationSegment("Underline", attributes=curses.A_UNDERLINE),
            SpacerSegment(),
            AbbreviationSegment("Reverse", attributes=curses.A_REVERSE)
        ]
        draw_text_segments(self.backend, row, 4, segments, 60, default_color=1)
        row += 2
        
        row = self.draw_label(row, "Combined colors and attributes:")
        
        segments = [
            AbbreviationSegment("Bold Red", color_pair=5, attributes=curses.A_BOLD),
            SpacerSegment(),
            AbbreviationSegment("Underline Green", color_pair=3, attributes=curses.A_UNDERLINE),
            SpacerSegment(),
            AbbreviationSegment("Reverse Cyan", color_pair=2, attributes=curses.A_REVERSE)
        ]
        draw_text_segments(self.backend, row, 4, segments, 60, default_color=1)
        row += 2
    
    def demo_status_bar_helper(self):
        """Demonstrate status bar helper function."""
        row = 1
        row = self.draw_title(row, "Demo 10: Status Bar Helper")
        
        row = self.draw_label(row, "create_status_bar_layout() - left and right aligned text:")
        
        for width in [70, 60, 50, 40, 30]:
            segments = create_status_bar_layout(
                left_text="/home/user/documents/report.txt",
                right_text="Modified | 1.2 MB",
                left_color=2,
                right_color=4
            )
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=1)
            row += 1
    
    def demo_file_list_helper(self):
        """Demonstrate file list item helper function."""
        row = 1
        row = self.draw_title(row, "Demo 11: File List Item Helper")
        
        row = self.draw_label(row, "create_file_list_item() - filename, size, date columns:")
        
        for width in [70, 60, 50, 40, 30]:
            segments = create_file_list_item(
                filename="very_long_document_name_with_details.txt",
                size_text="1.2 MB",
                date_text="2024-01-15",
                filename_color=2,
                size_color=4,
                date_color=6
            )
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=1)
            row += 1
    
    def demo_dialog_prompt_helper(self):
        """Demonstrate dialog prompt helper function."""
        row = 1
        row = self.draw_title(row, "Demo 12: Dialog Prompt Helper")
        
        row = self.draw_label(row, "create_dialog_prompt() - prompt and input field:")
        
        for width in [60, 50, 40, 30]:
            segments = create_dialog_prompt(
                prompt_text="Enter destination path:",
                input_text="/home/user/documents/project/files/",
                prompt_attributes=curses.A_BOLD,
                prompt_color=4,
                input_color=2
            )
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=1)
            row += 1
    
    def demo_three_column_helper(self):
        """Demonstrate three-column layout helper function."""
        row = 1
        row = self.draw_title(row, "Demo 13: Three-Column Layout Helper")
        
        row = self.draw_label(row, "create_three_column_layout() - left, center, right:")
        
        for width in [70, 60, 50, 40, 30]:
            segments = create_three_column_layout(
                left_text="File",
                center_text="Terminal File Manager v1.0",
                right_text="Help: F1",
                left_color=3,
                center_color=2,
                right_color=4
            )
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=1)
            row += 1
    
    def demo_breadcrumb_helper(self):
        """Demonstrate breadcrumb path helper function."""
        row = 1
        row = self.draw_title(row, "Demo 14: Breadcrumb Path Helper")
        
        row = self.draw_label(row, "create_breadcrumb_path() - intelligent path abbreviation:")
        
        path = "/home/user/documents/projects/myproject/src/components/Button.tsx"
        
        for width in [70, 60, 50, 40, 30, 20]:
            segments = create_breadcrumb_path(path, color_pair=3)
            label = f"Width {width}: "
            self.stdscr.addstr(row, 4, label)
            draw_text_segments(self.backend, row, 4 + len(label), segments, width, default_color=1)
            row += 1
    
    def demo_key_value_helper(self):
        """Demonstrate key-value pair helper function."""
        row = 1
        row = self.draw_title(row, "Demo 15: Key-Value Pair Helper")
        
        row = self.draw_label(row, "create_key_value_pair() - labeled data:")
        
        pairs = [
            ("Size", "1,234,567 bytes"),
            ("Modified", "2024-01-15 14:30:00"),
            ("Type", "PDF Document"),
            ("Permissions", "rw-r--r--")
        ]
        
        for key, value in pairs:
            segments = create_key_value_pair(
                key=key,
                value=value,
                key_attributes=curses.A_BOLD,
                key_color=4,
                value_color=2
            )
            draw_text_segments(self.backend, row, 4, segments, 50, default_color=1)
            row += 1
        
        row += 1
        row = self.draw_label(row, "At narrow width (30 columns):")
        
        for key, value in pairs:
            segments = create_key_value_pair(
                key=key,
                value=value,
                key_attributes=curses.A_BOLD,
                key_color=4,
                value_color=2
            )
            draw_text_segments(self.backend, row, 4, segments, 30, default_color=1)
            row += 1
    
    def demo_complex_layout(self):
        """Demonstrate a complex real-world layout."""
        row = 1
        row = self.draw_title(row, "Demo 16: Complex Real-World Layout")
        
        row = self.draw_label(row, "File manager status bar with multiple elements:")
        
        # Complex status bar with many elements
        for width in [80, 70, 60, 50, 40, 30]:
            segments = [
                # Left side: current path
                FilepathSegment(
                    "/home/user/documents/projects/myproject/src",
                    priority=1,
                    min_length=15,
                    color_pair=2
                ),
                SpacerSegment(),
                
                # Middle: file count
                AbbreviationSegment(
                    "42 files",
                    priority=2,
                    min_length=5,
                    color_pair=4
                ),
                SpacerSegment(),
                
                # Right side: selection info
                AbbreviationSegment(
                    "3 selected",
                    priority=3,
                    min_length=4,
                    color_pair=3
                ),
                AsIsSegment(" | ", color_pair=1),
                AbbreviationSegment(
                    "1.2 MB",
                    priority=0,
                    min_length=4,
                    color_pair=4
                )
            ]
            
            label = f"Width {width}: "
            self.stdscr.addstr(row, 2, label)
            draw_text_segments(self.backend, row, 2 + len(label), segments, width, default_color=1)
            row += 1


def main(stdscr):
    """Main entry point for the demo."""
    try:
        demo = TextLayoutDemo(stdscr)
        demo.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Show error before exiting
        stdscr.clear()
        stdscr.addstr(0, 0, f"Error: {e}", curses.A_BOLD)
        stdscr.addstr(1, 0, "Press any key to exit...")
        stdscr.refresh()
        stdscr.getch()
        raise


if __name__ == '__main__':
    curses.wrapper(main)
