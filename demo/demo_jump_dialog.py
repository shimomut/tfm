#!/usr/bin/env python3
"""
Demo: Jump Dialog Feature
Demonstrates the jump to directory dialog functionality
"""

import curses
import time
import tempfile
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_jump_dialog import JumpDialog, JumpDialogHelpers
from tfm_config import DefaultConfig
from tfm_colors import init_colors, get_status_color


class MockPaneManager:
    """Mock pane manager for demo"""
    
    def __init__(self):
        self.active_pane = 'left'
        self.panes = {
            'left': {
                'path': Path.cwd(),
                'selected_index': 0,
                'scroll_offset': 0,
                'selected_files': set()
            }
        }
    
    def get_current_pane(self):
        return self.panes[self.active_pane]


def create_safe_addstr(stdscr):
    """Create a safe_addstr function that captures stdscr"""
    def safe_addstr(y, x, text, attr=0):
        """Safely add string to screen, handling screen boundaries"""
        try:
            height, width = stdscr.getmaxyx()
            if 0 <= y < height and 0 <= x < width:
                # Truncate text if it would exceed screen width
                max_len = width - x
                if len(text) > max_len:
                    text = text[:max_len]
                stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass
    return safe_addstr


def create_demo_directory_structure():
    """Create a temporary directory structure for demo"""
    temp_dir = tempfile.mkdtemp(prefix="tfm_jump_demo_")
    temp_path = Path(temp_dir)
    
    # Create a more interesting directory structure
    directories = [
        "projects/web/frontend",
        "projects/web/backend", 
        "projects/mobile/ios",
        "projects/mobile/android",
        "documents/work/reports",
        "documents/personal/photos",
        "downloads/software",
        "downloads/media",
        "config/system",
        "config/user",
        "scripts/backup",
        "scripts/deployment",
        "temp/cache",
        "temp/logs"
    ]
    
    for dir_path in directories:
        (temp_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create some files to show they're ignored
    (temp_path / "README.md").write_text("Demo directory structure")
    (temp_path / "projects" / "project.txt").write_text("Project file")
    
    return temp_path


def demo_jump_dialog(stdscr):
    """Demonstrate jump dialog functionality"""
    # Initialize colors
    init_colors()
    
    # Create demo directory structure
    demo_path = create_demo_directory_structure()
    
    # Initialize components
    config = DefaultConfig()
    jump_dialog = JumpDialog(config)
    pane_manager = MockPaneManager()
    
    # Set current directory to demo path
    pane_manager.get_current_pane()['path'] = demo_path
    
    messages = []
    def demo_print(msg):
        messages.append(msg)
    
    try:
        # Clear screen
        stdscr.clear()
        
        # Show instructions
        height, width = stdscr.getmaxyx()
        
        instructions = [
            "Jump Dialog Demo",
            "================",
            "",
            f"Demo directory: {demo_path}",
            "",
            "The jump dialog will scan all subdirectories recursively.",
            "You can filter directories by typing part of their path.",
            "",
            "Controls:",
            "- Type to filter directories",
            "- ↑/↓ or Page Up/Down to navigate",
            "- Enter to jump to selected directory", 
            "- ESC to cancel",
            "",
            "Press any key to start the demo..."
        ]
        
        safe_addstr_func = create_safe_addstr(stdscr)
        
        for i, line in enumerate(instructions):
            if i < height - 1:
                safe_addstr_func(i, 2, line, get_status_color())
        
        stdscr.refresh()
        stdscr.getch()  # Wait for key press
        
        # Create safe_addstr function
        safe_addstr_func = create_safe_addstr(stdscr)
        
        # Show jump dialog
        jump_dialog.show(demo_path)
        
        # Main demo loop
        while jump_dialog.mode:
            # Clear screen
            stdscr.clear()
            
            # Draw jump dialog
            jump_dialog.draw(stdscr, safe_addstr_func)
            
            # Show additional info at bottom
            info_y = height - 3
            safe_addstr_func(info_y, 2, "Demo: Use arrow keys to navigate, type to filter, Enter to select, ESC to exit", 
                       get_status_color() | curses.A_DIM)
            
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            result = jump_dialog.handle_input(key)
            
            if isinstance(result, tuple):
                action, data = result
                if action == 'navigate' and data:
                    # Simulate navigation
                    JumpDialogHelpers.navigate_to_directory(data, pane_manager, demo_print)
                    break
            elif result == True and not jump_dialog.mode:
                # Dialog was cancelled
                break
        
        # Show results
        stdscr.clear()
        
        result_lines = [
            "Jump Dialog Demo Results",
            "========================",
            ""
        ]
        
        if messages:
            result_lines.extend([
                "Navigation result:",
                f"  {messages[-1]}",
                "",
                f"Current directory: {pane_manager.get_current_pane()['path']}",
            ])
        else:
            result_lines.extend([
                "Demo was cancelled.",
                f"Current directory: {pane_manager.get_current_pane()['path']}",
            ])
        
        result_lines.extend([
            "",
            "Key features demonstrated:",
            "- Recursive directory scanning with threading",
            "- Real-time filtering as you type",
            "- Progress animation during scanning",
            "- Thread-safe navigation and selection",
            "- Keyboard navigation (arrows, page up/down)",
            "",
            "Press any key to exit..."
        ])
        
        safe_addstr_func = create_safe_addstr(stdscr)
        
        for i, line in enumerate(result_lines):
            if i < height - 1:
                safe_addstr_func(i, 2, line, get_status_color())
        
        stdscr.refresh()
        stdscr.getch()  # Wait for key press
        
    finally:
        # Clean up
        if jump_dialog.mode:
            jump_dialog.exit()
        
        # Clean up demo directory
        import shutil
        try:
            shutil.rmtree(demo_path)
        except:
            pass


def main():
    """Main demo function"""
    try:
        curses.wrapper(demo_jump_dialog)
        print("Jump dialog demo completed successfully!")
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()