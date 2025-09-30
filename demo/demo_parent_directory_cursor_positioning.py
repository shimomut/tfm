#!/usr/bin/env python3
"""
Demo: Parent Directory Cursor Positioning

This demo showcases the improved parent directory navigation behavior where
the cursor is automatically positioned on the child directory we just came from
when navigating to the parent directory using the Backspace key.

Features demonstrated:
1. Navigate to child directory using Enter
2. Navigate to parent directory using Backspace
3. Cursor automatically positions on the child directory we came from
4. Easy navigation back to child directory by pressing Enter again

Usage:
    python demo/demo_parent_directory_cursor_positioning.py

Navigation:
    - Use arrow keys to move cursor
    - Press Enter to enter a directory
    - Press Backspace to go to parent directory
    - Press 'q' to quit
"""

import curses
import os
import sys
import tempfile
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_path import Path as TFMPath


class ParentNavigationDemo:
    """Demo class for parent directory cursor positioning"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.current_path = None
        self.files = []
        self.selected_index = 0
        self.scroll_offset = 0
        
        # Set up demo directory structure
        self.setup_demo_directories()
        
        # Configure curses
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)
        
        # Initialize colors if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Selected
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Directory
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # File
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Header
    
    def setup_demo_directories(self):
        """Create demo directory structure"""
        self.temp_dir = tempfile.mkdtemp(prefix="tfm_demo_")
        
        # Create directory structure:
        # demo_root/
        #   ├── documents/
        #   │   ├── reports/
        #   │   │   ├── 2023_report.txt
        #   │   │   └── 2024_report.txt
        #   │   ├── letters/
        #   │   │   ├── letter1.txt
        #   │   │   └── letter2.txt
        #   │   └── readme.txt
        #   ├── projects/
        #   │   ├── project_a/
        #   │   │   └── main.py
        #   │   ├── project_b/
        #   │   │   └── app.py
        #   │   └── notes.txt
        #   └── media/
        #       ├── images/
        #       │   ├── photo1.jpg
        #       │   └── photo2.jpg
        #       └── videos/
        #           └── demo.mp4
        
        base = Path(self.temp_dir)
        
        # Create directories
        (base / "documents").mkdir()
        (base / "documents" / "reports").mkdir()
        (base / "documents" / "letters").mkdir()
        (base / "projects").mkdir()
        (base / "projects" / "project_a").mkdir()
        (base / "projects" / "project_b").mkdir()
        (base / "media").mkdir()
        (base / "media" / "images").mkdir()
        (base / "media" / "videos").mkdir()
        
        # Create files
        (base / "documents" / "reports" / "2023_report.txt").write_text("2023 Annual Report")
        (base / "documents" / "reports" / "2024_report.txt").write_text("2024 Annual Report")
        (base / "documents" / "letters" / "letter1.txt").write_text("Dear Sir/Madam...")
        (base / "documents" / "letters" / "letter2.txt").write_text("Follow-up letter...")
        (base / "documents" / "readme.txt").write_text("Documents folder readme")
        (base / "projects" / "project_a" / "main.py").write_text("print('Project A')")
        (base / "projects" / "project_b" / "app.py").write_text("print('Project B')")
        (base / "projects" / "notes.txt").write_text("Project notes")
        (base / "media" / "images" / "photo1.jpg").write_text("JPEG data")
        (base / "media" / "images" / "photo2.jpg").write_text("JPEG data")
        (base / "media" / "videos" / "demo.mp4").write_text("MP4 data")
        
        # Start in the root directory
        self.current_path = TFMPath(self.temp_dir)
        self.refresh_files()
    
    def cleanup_demo_directories(self):
        """Clean up demo directories"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def refresh_files(self):
        """Refresh file list for current directory"""
        try:
            self.files = []
            if self.current_path.exists() and self.current_path.is_dir():
                for item in sorted(self.current_path.iterdir()):
                    self.files.append(TFMPath(item))
            
            # Ensure selected index is valid
            if self.selected_index >= len(self.files):
                self.selected_index = max(0, len(self.files) - 1)
                
        except Exception as e:
            self.files = []
            self.selected_index = 0
    
    def draw_screen(self):
        """Draw the demo screen"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Draw header
        header = f"Parent Directory Navigation Demo - Current: {self.current_path}"
        if len(header) > width - 1:
            header = "..." + header[-(width-4):]
        
        try:
            if curses.has_colors():
                self.stdscr.addstr(0, 0, header[:width-1], curses.color_pair(4))
            else:
                self.stdscr.addstr(0, 0, header[:width-1], curses.A_BOLD)
        except curses.error:
            pass
        
        # Draw instructions
        instructions = [
            "Instructions:",
            "  ↑/↓ - Move cursor",
            "  Enter - Enter directory",
            "  Backspace - Go to parent (cursor will be on child directory)",
            "  q - Quit demo"
        ]
        
        start_y = 2
        for i, instruction in enumerate(instructions):
            try:
                self.stdscr.addstr(start_y + i, 2, instruction[:width-3])
            except curses.error:
                pass
        
        # Draw file list
        list_start_y = start_y + len(instructions) + 1
        display_height = height - list_start_y - 2
        
        # Calculate scroll offset
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + display_height:
            self.scroll_offset = self.selected_index - display_height + 1
        
        # Draw files
        for i in range(display_height):
            file_index = i + self.scroll_offset
            y = list_start_y + i
            
            if file_index >= len(self.files):
                break
            
            file_path = self.files[file_index]
            is_selected = file_index == self.selected_index
            is_dir = file_path.is_dir()
            
            # Prepare display text
            display_name = file_path.name
            if is_dir:
                display_name += "/"
            
            # Truncate if too long
            max_width = width - 6
            if len(display_name) > max_width:
                display_name = display_name[:max_width-3] + "..."
            
            # Choose color and attributes
            if is_selected:
                if curses.has_colors():
                    attr = curses.color_pair(1) | curses.A_BOLD
                else:
                    attr = curses.A_REVERSE
            elif is_dir:
                if curses.has_colors():
                    attr = curses.color_pair(2)
                else:
                    attr = curses.A_BOLD
            else:
                if curses.has_colors():
                    attr = curses.color_pair(3)
                else:
                    attr = curses.A_NORMAL
            
            try:
                self.stdscr.addstr(y, 4, display_name, attr)
            except curses.error:
                pass
        
        # Draw status
        status = f"Files: {len(self.files)} | Selected: {self.selected_index + 1 if self.files else 0}"
        try:
            self.stdscr.addstr(height - 1, 2, status[:width-3])
        except curses.error:
            pass
        
        self.stdscr.refresh()
    
    def handle_enter_directory(self):
        """Handle entering a directory"""
        if not self.files or self.selected_index >= len(self.files):
            return
        
        selected_file = self.files[self.selected_index]
        if selected_file.is_dir():
            # Navigate to directory
            self.current_path = selected_file
            self.selected_index = 0
            self.scroll_offset = 0
            self.refresh_files()
    
    def handle_parent_directory(self):
        """Handle navigating to parent directory with cursor positioning"""
        if self.current_path == self.current_path.parent:
            return  # Already at root
        
        # Remember the child directory name we're leaving
        child_directory_name = self.current_path.name
        
        # Navigate to parent
        self.current_path = self.current_path.parent
        self.selected_index = 0
        self.scroll_offset = 0
        self.refresh_files()
        
        # Try to set cursor to the child directory we just came from
        for i, file_path in enumerate(self.files):
            if file_path.name == child_directory_name and file_path.is_dir():
                self.selected_index = i
                break
    
    def run(self):
        """Run the demo"""
        try:
            while True:
                self.draw_screen()
                
                key = self.stdscr.getch()
                
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == curses.KEY_UP:
                    if self.selected_index > 0:
                        self.selected_index -= 1
                elif key == curses.KEY_DOWN:
                    if self.selected_index < len(self.files) - 1:
                        self.selected_index += 1
                elif key == ord('\n') or key == curses.KEY_ENTER or key == 10:
                    self.handle_enter_directory()
                elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                    self.handle_parent_directory()
        
        finally:
            self.cleanup_demo_directories()


def main(stdscr):
    """Main demo function"""
    demo = ParentNavigationDemo(stdscr)
    demo.run()


if __name__ == '__main__':
    print("Starting Parent Directory Navigation Demo...")
    print("This demo will create temporary directories for demonstration.")
    print("Press any key to continue...")
    input()
    
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo error: {e}")
    
    print("Demo completed. Temporary directories have been cleaned up.")