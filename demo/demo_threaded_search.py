#!/usr/bin/env python3
"""
Demo script for threaded SearchDialog functionality
Shows how the search dialog now performs searches asynchronously
"""

import sys
import curses
import time
import tempfile
import shutil
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_search_dialog import SearchDialog
from tfm_config import DefaultConfig
from tfm_colors import init_colors


class DemoConfig(DefaultConfig):
    """Demo configuration with lower search limit for demonstration"""
    MAX_SEARCH_RESULTS = 50


def create_demo_directory():
    """Create a demo directory with many files for testing"""
    temp_dir = Path(tempfile.mkdtemp(prefix="tfm_search_demo_"))
    
    print(f"Creating demo directory: {temp_dir}")
    
    # Create many files to demonstrate threading
    for i in range(200):
        file_path = temp_dir / f"file_{i:03d}.txt"
        file_path.write_text(f"This is file number {i}\nWith some searchable content\nLine 3 has test data")
    
    # Create some Python files
    for i in range(50):
        file_path = temp_dir / f"script_{i:02d}.py"
        file_path.write_text(f"#!/usr/bin/env python3\ndef function_{i}():\n    return 'test result {i}'")
    
    # Create subdirectories with more files
    for subdir_num in range(10):
        subdir = temp_dir / f"subdir_{subdir_num}"
        subdir.mkdir()
        
        for file_num in range(30):
            file_path = subdir / f"nested_{file_num}.log"
            file_path.write_text(f"Log entry {file_num} in subdir {subdir_num}\nSome test content here")
    
    print(f"Created {len(list(temp_dir.rglob('*')))} files and directories")
    return temp_dir


def safe_addstr(stdscr, y, x, text, attr=curses.A_NORMAL):
    """Safely add string to screen"""
    try:
        height, width = stdscr.getmaxyx()
        if y < 0 or y >= height or x < 0 or x >= width:
            return
        max_len = width - x - 1
        if max_len <= 0:
            return
        truncated_text = text[:max_len] if len(text) > max_len else text
        stdscr.addstr(y, x, truncated_text, attr)
    except curses.error:
        pass


def demo_threaded_search(stdscr):
    """Demonstrate threaded search functionality"""
    # Initialize colors
    init_colors('dark')
    curses.curs_set(0)
    stdscr.keypad(True)
    
    # Create demo directory
    demo_dir = create_demo_directory()
    
    try:
        # Initialize search dialog
        config = DemoConfig()
        search_dialog = SearchDialog(config)
        
        # Show instructions
        stdscr.clear()
        instructions = [
            "TFM Threaded Search Demo",
            "=" * 30,
            "",
            f"Demo directory: {demo_dir}",
            f"Files created: {len(list(demo_dir.rglob('*')))}",
            f"Search result limit: {config.MAX_SEARCH_RESULTS}",
            "",
            "This demo shows the new threaded search functionality:",
            "• Searches run in background threads",
            "• Results appear as they are found",
            "• Search can be cancelled or restarted",
            "• Navigation works while searching",
            "",
            "Press any key to start the search dialog demo...",
        ]
        
        for i, line in enumerate(instructions):
            safe_addstr(stdscr, i, 2, line)
        
        stdscr.refresh()
        stdscr.getch()
        
        # Start search dialog
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*"
        
        # Demo loop
        demo_running = True
        last_search_time = 0
        
        while demo_running:
            stdscr.clear()
            
            # Check if we need to start a search
            current_time = time.time()
            if current_time - last_search_time > 0.5:  # Restart search every 0.5 seconds for demo
                search_dialog.perform_search(demo_dir)
                last_search_time = current_time
            
            # Draw search dialog
            search_dialog.draw(stdscr, safe_addstr)
            
            # Draw demo info
            height, width = stdscr.getmaxyx()
            demo_info = [
                "",
                "Demo Controls:",
                "• ESC: Exit demo",
                "• Tab: Switch search type",
                "• Arrow keys: Navigate results",
                "• Enter: Would navigate to selected result",
                "",
                f"Search thread active: {search_dialog.searching}",
                f"Results found: {len(search_dialog.results)}",
                f"Max results: {config.MAX_SEARCH_RESULTS}",
            ]
            
            start_y = height - len(demo_info) - 2
            for i, line in enumerate(demo_info):
                safe_addstr(stdscr, start_y + i, 2, line, curses.A_DIM)
            
            stdscr.refresh()
            
            # Handle input with timeout
            stdscr.timeout(100)  # 100ms timeout
            key = stdscr.getch()
            
            if key != -1:  # Key was pressed
                if key == 27:  # ESC
                    demo_running = False
                else:
                    # Let search dialog handle the key
                    result = search_dialog.handle_input(key)
                    if result == True:
                        continue
                    elif isinstance(result, tuple) and result[0] == 'navigate':
                        # In a real application, this would navigate to the file
                        if result[1]:
                            safe_addstr(stdscr, height - 1, 2, f"Would navigate to: {result[1]['relative_path']}")
                            stdscr.refresh()
                            time.sleep(1)
                    elif isinstance(result, tuple) and result[0] == 'search':
                        # Pattern changed, search will restart automatically
                        last_search_time = 0
        
        # Clean up
        search_dialog.exit()
        
        # Show completion message
        stdscr.clear()
        completion_msg = [
            "Demo completed!",
            "",
            "The threaded search dialog provides:",
            "• Non-blocking search operations",
            "• Real-time result updates",
            "• Configurable result limits",
            "• Proper thread synchronization",
            "• Search cancellation support",
            "",
            "Press any key to exit..."
        ]
        
        for i, line in enumerate(completion_msg):
            safe_addstr(stdscr, i + 2, 2, line)
        
        stdscr.refresh()
        stdscr.getch()
        
    finally:
        # Clean up demo directory
        shutil.rmtree(demo_dir)
        print(f"Cleaned up demo directory: {demo_dir}")


def main():
    """Main entry point"""
    try:
        curses.wrapper(demo_threaded_search)
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()