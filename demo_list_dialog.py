#!/usr/bin/env python3
"""
Demo script showing various use cases for the searchable list dialog
"""

import curses
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from tfm_main import FileManager

def demo_list_dialog(stdscr):
    """Demo the searchable list dialog with different scenarios"""
    try:
        # Initialize file manager
        fm = FileManager(stdscr)
        
        # Demo 1: File selection
        files = [
            "config.json", "main.py", "utils.py", "README.md", "LICENSE",
            "requirements.txt", "setup.py", "Makefile", ".gitignore",
            "test_file.py", "demo.py", "example.txt", "data.csv"
        ]
        
        # Demo 2: Directory selection
        directories = [
            "/home/user/Documents", "/home/user/Downloads", "/home/user/Pictures",
            "/usr/local/bin", "/var/log", "/etc/nginx", "/opt/apps",
            "/tmp/workspace", "/home/user/Projects/python", "/home/user/Desktop"
        ]
        
        # Demo 3: Command selection
        commands = [
            "ls -la", "grep -r 'pattern' .", "find . -name '*.py'",
            "git status", "git log --oneline", "docker ps", "ps aux",
            "top", "htop", "df -h", "du -sh *", "netstat -tulpn"
        ]
        
        current_demo = 0
        demos = [
            ("Select a File", files),
            ("Choose Directory", directories), 
            ("Pick Command", commands)
        ]
        
        def selection_callback(selected_item):
            nonlocal current_demo
            if selected_item:
                print(f"Demo {current_demo + 1} - Selected: {selected_item}")
            else:
                print(f"Demo {current_demo + 1} - Cancelled")
            
            # Move to next demo
            current_demo += 1
            if current_demo < len(demos):
                title, items = demos[current_demo]
                fm.show_list_dialog(title, items, selection_callback)
            else:
                # All demos completed
                fm.should_quit = True
        
        # Start first demo
        title, items = demos[current_demo]
        fm.show_list_dialog(title, items, selection_callback)
        
        # Run the file manager
        fm.run()
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("Searchable List Dialog Demo")
    print("=" * 30)
    print("This demo will show 3 different list dialogs:")
    print("1. File selection")
    print("2. Directory selection") 
    print("3. Command selection")
    print()
    print("Features to test:")
    print("- Navigation with ↑↓ arrow keys")
    print("- Page Up/Down for fast scrolling")
    print("- Home/End keys")
    print("- Isearch by typing")
    print("- Backspace to clear search")
    print("- Enter to select, ESC to cancel")
    print()
    print("Press any key to start the demo...")
    input()
    
    try:
        curses.wrapper(demo_list_dialog)
        print("\nDemo completed!")
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()