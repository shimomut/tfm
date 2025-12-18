#!/usr/bin/env python3
"""
Demo: Menu Bar Keyboard Shortcuts

This demo demonstrates keyboard shortcut functionality in TFM's desktop mode.
It shows that keyboard shortcuts execute menu actions without requiring the
user to open the menu.

Requirements:
    - macOS (CoreGraphics backend)
    - Desktop mode enabled

Usage:
    python demo/demo_menu_keyboard_shortcuts.py

Test Cases:
    1. Press Cmd+N - Should trigger "New File" action
    2. Press Cmd+Shift+N - Should trigger "New Folder" action
    3. Press Cmd+Q - Should quit the application
    4. Press Cmd+H - Should toggle hidden files
    5. Press Cmd+A - Should select all files

Expected Behavior:
    - Keyboard shortcuts should execute actions immediately
    - No menu needs to be opened
    - Actions should be the same as clicking the menu item
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import KeyEvent, KeyCode, ModifierKey, MenuEvent, SystemEvent, SystemEventType
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from src.tfm_menu_manager import MenuManager
from unittest.mock import Mock
from pathlib import Path


def create_mock_file_manager():
    """Create a mock file manager for testing"""
    mock_fm = Mock()
    
    # Create mock pane
    mock_pane = {
        'selected_files': set(),
        'path': Path.home()
    }
    
    mock_fm.get_current_pane.return_value = mock_pane
    mock_fm.clipboard = []
    
    return mock_fm


def main():
    """Main demo function"""
    print("Menu Bar Keyboard Shortcuts Demo")
    print("=" * 50)
    print()
    print("This demo tests keyboard shortcut functionality.")
    print("Keyboard shortcuts should execute actions without")
    print("opening menus.")
    print()
    print("Test shortcuts:")
    print("  Cmd+N       - New File")
    print("  Cmd+Shift+N - New Folder")
    print("  Cmd+H       - Toggle Hidden Files")
    print("  Cmd+A       - Select All")
    print("  Cmd+Q       - Quit")
    print()
    print("Press Cmd+Q to quit the demo.")
    print()
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="TFM - Keyboard Shortcuts Demo",
        font_name="Menlo",
        font_size=14,
        rows=24,
        cols=80
    )
    
    try:
        # Initialize backend
        backend.initialize()
        
        # Create menu manager
        mock_fm = create_mock_file_manager()
        menu_manager = MenuManager(mock_fm)
        
        # Set up menu bar
        menu_structure = menu_manager.get_menu_structure()
        backend.set_menu_bar(menu_structure)
        
        # Initialize colors
        backend.init_color_pair(1, (255, 255, 255), (0, 100, 200))  # White on blue
        backend.init_color_pair(2, (255, 255, 0), (0, 0, 0))        # Yellow on black
        
        # Draw instructions
        backend.clear()
        backend.draw_text(0, 0, "Menu Bar Keyboard Shortcuts Demo", color_pair=1)
        backend.draw_text(2, 0, "Test the following keyboard shortcuts:", color_pair=2)
        backend.draw_text(4, 2, "Cmd+N       - New File")
        backend.draw_text(5, 2, "Cmd+Shift+N - New Folder")
        backend.draw_text(6, 2, "Cmd+H       - Toggle Hidden Files")
        backend.draw_text(7, 2, "Cmd+A       - Select All")
        backend.draw_text(8, 2, "Cmd+Q       - Quit")
        backend.draw_text(10, 0, "Events will be displayed below:", color_pair=2)
        backend.refresh()
        
        # Event loop
        event_row = 12
        running = True
        
        while running:
            # Get event (block until event arrives)
            event = backend.get_event(timeout_ms=-1)
            
            if event is None:
                continue
            
            # Handle menu events
            if isinstance(event, MenuEvent):
                # Clear previous event display
                backend.clear_region(event_row, 0, 1, 80)
                
                # Display menu event
                msg = f"MenuEvent: {event.item_id}"
                backend.draw_text(event_row, 2, msg, color_pair=2)
                
                # Handle specific menu items
                if event.item_id == 'file.quit':
                    backend.draw_text(event_row + 1, 2, "Quitting...", color_pair=1)
                    backend.refresh()
                    running = False
                elif event.item_id == 'file.new_file':
                    backend.draw_text(event_row + 1, 2, "Action: Create new file", color_pair=1)
                elif event.item_id == 'file.new_folder':
                    backend.draw_text(event_row + 1, 2, "Action: Create new folder", color_pair=1)
                elif event.item_id == 'view.show_hidden':
                    backend.draw_text(event_row + 1, 2, "Action: Toggle hidden files", color_pair=1)
                elif event.item_id == 'edit.select_all':
                    backend.draw_text(event_row + 1, 2, "Action: Select all files", color_pair=1)
                else:
                    backend.draw_text(event_row + 1, 2, f"Action: {event.item_id}", color_pair=1)
                
                backend.refresh()
                
                # Move to next event row
                event_row += 3
                if event_row > 20:
                    # Scroll up by clearing and resetting
                    backend.clear_region(12, 0, 12, 80)
                    event_row = 12
            
            # Handle system events (window close, etc.)
            elif isinstance(event, SystemEvent):
                if event.is_close():
                    # Window close button clicked
                    backend.clear_region(event_row, 0, 1, 80)
                    backend.draw_text(event_row, 2, "Window close requested - quitting...", color_pair=1)
                    backend.refresh()
                    running = False
            
            # Handle keyboard events (for debugging)
            elif isinstance(event, KeyEvent):
                # Clear previous event display
                backend.clear_region(event_row, 0, 1, 80)
                
                # Display key event
                modifiers = []
                if event.modifiers & ModifierKey.COMMAND:
                    modifiers.append("Cmd")
                if event.modifiers & ModifierKey.SHIFT:
                    modifiers.append("Shift")
                if event.modifiers & ModifierKey.CONTROL:
                    modifiers.append("Ctrl")
                if event.modifiers & ModifierKey.ALT:
                    modifiers.append("Alt")
                
                mod_str = "+".join(modifiers) + "+" if modifiers else ""
                msg = f"KeyEvent: {mod_str}{event.char or event.key_code.name}"
                backend.draw_text(event_row, 2, msg)
                backend.refresh()
                
                # Move to next event row
                event_row += 1
                if event_row > 20:
                    backend.clear_region(12, 0, 12, 80)
                    event_row = 12
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        backend.shutdown()
        print("\nDemo completed")


if __name__ == '__main__':
    main()
