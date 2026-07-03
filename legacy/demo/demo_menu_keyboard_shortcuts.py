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
from ttk.renderer import EventCallback
from src.tfm_menu_manager import MenuManager
from unittest.mock import Mock
from pathlib import Path


class MenuShortcutsCallback(EventCallback):
    """Event callback handler for menu shortcuts demo."""
    
    def __init__(self, backend, menu_manager, mock_fm):
        """Initialize the callback handler."""
        self.backend = backend
        self.menu_manager = menu_manager
        self.mock_fm = mock_fm
        self.running = True
        self.event_row = 12
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle key events."""
        # Clear previous event display
        self.backend.clear_region(self.event_row, 0, 1, 80)
        
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
        self.backend.draw_text(self.event_row, 2, msg)
        self.backend.refresh()
        
        # Move to next event row
        self.event_row += 1
        if self.event_row > 20:
            self.backend.clear_region(12, 0, 12, 80)
            self.event_row = 12
        
        return False
    
    def on_char_event(self, event) -> bool:
        """Handle character events."""
        return False
    
    def on_menu_event(self, event: MenuEvent) -> bool:
        """Handle menu events."""
        # Clear previous event display
        self.backend.clear_region(self.event_row, 0, 1, 80)
        
        # Display menu event
        msg = f"MenuEvent: {event.item_id}"
        self.backend.draw_text(self.event_row, 2, msg, color_pair=2)
        
        # Handle specific menu items
        if event.item_id == 'file.quit':
            self.backend.draw_text(self.event_row + 1, 2, "Quitting...", color_pair=1)
            self.backend.refresh()
            self.running = False
        elif event.item_id == 'file.new_file':
            self.backend.draw_text(self.event_row + 1, 2, "Action: Create new file", color_pair=1)
        elif event.item_id == 'file.new_folder':
            self.backend.draw_text(self.event_row + 1, 2, "Action: Create new folder", color_pair=1)
        elif event.item_id == 'view.show_hidden':
            self.backend.draw_text(self.event_row + 1, 2, "Action: Toggle hidden files", color_pair=1)
        elif event.item_id == 'edit.select_all':
            self.backend.draw_text(self.event_row + 1, 2, "Action: Select all files", color_pair=1)
        else:
            self.backend.draw_text(self.event_row + 1, 2, f"Action: {event.item_id}", color_pair=1)
        
        self.backend.refresh()
        
        # Move to next event row
        self.event_row += 3
        if self.event_row > 20:
            # Scroll up by clearing and resetting
            self.backend.clear_region(12, 0, 12, 80)
            self.event_row = 12
        
        return True
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """Handle system events."""
        if event.is_close():
            # Window close button clicked
            self.backend.clear_region(self.event_row, 0, 1, 80)
            self.backend.draw_text(self.event_row, 2, "Window close requested - quitting...", color_pair=1)
            self.backend.refresh()
            self.running = False
            return True
        return False
    
    def should_close(self) -> bool:
        """Check if application should quit."""
        return not self.running


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
        
        # Set up event callback
        callback = MenuShortcutsCallback(backend, menu_manager, mock_fm)
        backend.set_event_callback(callback)
        
        # Event loop
        while callback.running:
            # Process events (delivered via callbacks)
            backend.run_event_loop_iteration(timeout_ms=100)
    
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
