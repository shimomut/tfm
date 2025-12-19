#!/usr/bin/env python3
"""
Demo: Menu Bar Feature in Desktop Mode

This demo demonstrates the complete menu bar functionality in TFM's desktop mode.
It shows menu structure, menu selection, action execution, menu state updates,
and keyboard shortcut functionality.

Requirements:
    - macOS (CoreGraphics backend)
    - Desktop mode enabled
    - PyObjC framework installed

Usage:
    python demo/demo_menu_bar.py

Test Cases:
    1. Menu Structure:
       - File menu with New File, New Folder, Open, Delete, Rename, Quit
       - Edit menu with Copy, Cut, Paste, Select All
       - View menu with Show Hidden Files, Sort By options, Refresh
       - Go menu with Parent Directory, Home, Favorites, Recent Locations

    2. Menu Selection:
       - Click on menu items to execute actions
       - Verify actions are executed correctly
       - Check that menu closes after selection

    3. Menu State Updates:
       - Select files and verify Copy/Cut/Delete/Rename become enabled
       - Deselect files and verify they become disabled
       - Navigate to root and verify Parent Directory becomes disabled
       - Copy files and verify Paste becomes enabled

    4. Keyboard Shortcuts:
       - Cmd+N for New File
       - Cmd+Shift+N for New Folder
       - Cmd+C for Copy
       - Cmd+V for Paste
       - Cmd+A for Select All
       - Cmd+H for Toggle Hidden Files
       - Cmd+Q for Quit

Expected Behavior:
    - Menu bar appears at top of window
    - Menu items are properly enabled/disabled based on state
    - Menu selections execute corresponding actions
    - Keyboard shortcuts work without opening menus
    - Menu state updates reflect application state changes
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import KeyEvent, KeyCode, ModifierKey, MenuEvent, SystemEvent, SystemEventType
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from src.tfm_menu_manager import MenuManager
from unittest.mock import Mock
import time


def create_mock_file_manager():
    """Create a mock file manager for testing"""
    mock_fm = Mock()
    
    # Create mock pane with some test files
    mock_pane = {
        'selected_files': set(),
        'path': Path.home(),
        'files': [
            {'name': 'file1.txt', 'is_dir': False},
            {'name': 'file2.txt', 'is_dir': False},
            {'name': 'folder1', 'is_dir': True},
            {'name': '.hidden_file', 'is_dir': False},
        ]
    }
    
    mock_fm.get_current_pane.return_value = mock_pane
    mock_fm.clipboard = []
    mock_fm.show_hidden = False
    
    return mock_fm


def print_header(backend, title):
    """Print a section header"""
    backend.clear()
    backend.draw_text(0, 0, "=" * 80, color_pair=1)
    backend.draw_text(1, 0, title.center(80), color_pair=1)
    backend.draw_text(2, 0, "=" * 80, color_pair=1)
    backend.refresh()


def print_instructions(backend, instructions, start_row=4):
    """Print instructions on screen"""
    row = start_row
    for line in instructions:
        backend.draw_text(row, 2, line)
        row += 1
    backend.refresh()


def wait_for_key(backend, prompt="Press any key to continue..."):
    """Wait for user to press a key"""
    rows, cols = backend.get_size()
    backend.draw_text(rows - 2, 2, prompt, color_pair=2)
    backend.refresh()
    
    while True:
        event = backend.get_event(timeout_ms=-1)
        if isinstance(event, KeyEvent):
            break
        elif isinstance(event, SystemEvent) and event.is_close():
            return False
    
    return True


def demo_menu_structure(backend, menu_manager):
    """Demo 1: Show menu structure"""
    print_header(backend, "Demo 1: Menu Structure")
    
    instructions = [
        "The menu bar contains four menus:",
        "",
        "1. File Menu:",
        "   - New File (Cmd+N)",
        "   - New Folder (Cmd+Shift+N)",
        "   - Open (Cmd+O)",
        "   - Delete (Cmd+D)",
        "   - Rename (Cmd+R)",
        "   - Quit (Cmd+Q)",
        "",
        "2. Edit Menu:",
        "   - Copy (Cmd+C)",
        "   - Cut (Cmd+X)",
        "   - Paste (Cmd+V)",
        "   - Select All (Cmd+A)",
        "",
        "3. View Menu:",
        "   - Show Hidden Files (Cmd+H)",
        "   - Sort by Name/Size/Date/Extension",
        "   - Refresh (Cmd+R)",
        "",
        "4. Go Menu:",
        "   - Parent Directory (Cmd+Up)",
        "   - Home (Cmd+Shift+H)",
        "   - Favorites (Cmd+F)",
        "   - Recent Locations (Cmd+Shift+R)",
        "",
        "Look at the menu bar at the top of the window.",
        "Click on each menu to see the items.",
    ]
    
    print_instructions(backend, instructions)
    return wait_for_key(backend)


def demo_menu_selection(backend, menu_manager, mock_fm):
    """Demo 2: Menu selection and action execution"""
    print_header(backend, "Demo 2: Menu Selection and Action Execution")
    
    instructions = [
        "Test menu selection by clicking on menu items:",
        "",
        "1. Click 'File' menu, then 'New File'",
        "   - Should see 'New File' action message below",
        "",
        "2. Click 'Edit' menu, then 'Select All'",
        "   - Should see 'Select All' action message below",
        "",
        "3. Click 'View' menu, then 'Show Hidden Files'",
        "   - Should see 'Toggle Hidden Files' action message below",
        "",
        "4. Click 'Go' menu, then 'Home'",
        "   - Should see 'Go Home' action message below",
        "",
        "Actions will be displayed below:",
    ]
    
    print_instructions(backend, instructions)
    
    # Event loop to capture menu selections
    event_row = 20
    action_count = 0
    max_actions = 4
    
    while action_count < max_actions:
        event = backend.get_event(timeout_ms=-1)
        
        if event is None:
            continue
        
        if isinstance(event, MenuEvent):
            # Clear previous message
            backend.clear_region(event_row, 0, 2, 80)
            
            # Display action
            msg = f"Action {action_count + 1}: {event.item_id}"
            backend.draw_text(event_row, 2, msg, color_pair=2)
            
            # Show what would happen
            action_desc = ""
            if event.item_id == 'file.new_file':
                action_desc = "Would create a new file"
            elif event.item_id == 'file.new_folder':
                action_desc = "Would create a new folder"
            elif event.item_id == 'edit.select_all':
                action_desc = "Would select all files"
            elif event.item_id == 'view.show_hidden':
                mock_fm.show_hidden = not mock_fm.show_hidden
                action_desc = f"Hidden files now: {'shown' if mock_fm.show_hidden else 'hidden'}"
            elif event.item_id == 'go.home':
                action_desc = "Would navigate to home directory"
            else:
                action_desc = f"Would execute: {event.item_id}"
            
            backend.draw_text(event_row + 1, 4, action_desc, color_pair=1)
            backend.refresh()
            
            action_count += 1
            
            if action_count >= max_actions:
                break
        
        elif isinstance(event, SystemEvent) and event.is_close():
            return False
        
        elif isinstance(event, KeyEvent):
            # Allow skipping with any key
            if action_count > 0:
                break
    
    return wait_for_key(backend, "Press any key to continue to next demo...")


def demo_menu_state_updates(backend, menu_manager, mock_fm):
    """Demo 3: Menu state updates based on selection"""
    print_header(backend, "Demo 3: Menu State Updates")
    
    instructions = [
        "Menu items are enabled/disabled based on application state:",
        "",
        "Current state:",
        "  - No files selected",
        "  - Clipboard is empty",
        "  - Not at root directory",
        "",
        "Check the Edit menu:",
        "  - Copy, Cut should be DISABLED (no selection)",
        "  - Paste should be DISABLED (clipboard empty)",
        "  - Select All should be ENABLED",
        "",
        "Now we'll simulate selecting files...",
    ]
    
    print_instructions(backend, instructions)
    
    if not wait_for_key(backend, "Press any key to select files..."):
        return False
    
    # Simulate selecting files
    mock_pane = mock_fm.get_current_pane()
    mock_pane['selected_files'] = {'file1.txt', 'file2.txt'}
    
    # Update menu states
    states = menu_manager.update_menu_states()
    for item_id, enabled in states.items():
        backend.update_menu_item_state(item_id, enabled)
    
    # Show updated state
    backend.clear_region(4, 0, 20, 80)
    instructions = [
        "Files selected! State updated:",
        "",
        "Current state:",
        "  - 2 files selected",
        "  - Clipboard is empty",
        "  - Not at root directory",
        "",
        "Check the Edit menu again:",
        "  - Copy, Cut should now be ENABLED",
        "  - Paste should still be DISABLED (clipboard empty)",
        "  - Select All should be ENABLED",
        "",
        "Check the File menu:",
        "  - Delete, Rename should now be ENABLED",
    ]
    
    print_instructions(backend, instructions)
    
    if not wait_for_key(backend, "Press any key to copy files..."):
        return False
    
    # Simulate copying files
    mock_fm.clipboard = ['file1.txt', 'file2.txt']
    
    # Update menu states
    states = menu_manager.update_menu_states()
    for item_id, enabled in states.items():
        backend.update_menu_item_state(item_id, enabled)
    
    # Show updated state
    backend.clear_region(4, 0, 20, 80)
    instructions = [
        "Files copied! State updated:",
        "",
        "Current state:",
        "  - 2 files selected",
        "  - Clipboard has 2 files",
        "  - Not at root directory",
        "",
        "Check the Edit menu again:",
        "  - Copy, Cut should be ENABLED",
        "  - Paste should now be ENABLED (clipboard has files)",
        "  - Select All should be ENABLED",
    ]
    
    print_instructions(backend, instructions)
    
    if not wait_for_key(backend, "Press any key to navigate to root..."):
        return False
    
    # Simulate navigating to root
    mock_pane['path'] = Path('/')
    
    # Update menu states
    states = menu_manager.update_menu_states()
    for item_id, enabled in states.items():
        backend.update_menu_item_state(item_id, enabled)
    
    # Show updated state
    backend.clear_region(4, 0, 20, 80)
    instructions = [
        "Navigated to root! State updated:",
        "",
        "Current state:",
        "  - 2 files selected",
        "  - Clipboard has 2 files",
        "  - At root directory",
        "",
        "Check the Go menu:",
        "  - Parent Directory should now be DISABLED (at root)",
        "  - Home should be ENABLED",
        "  - Favorites should be ENABLED",
        "  - Recent Locations should be ENABLED",
    ]
    
    print_instructions(backend, instructions)
    
    return wait_for_key(backend)


def demo_keyboard_shortcuts(backend, menu_manager, mock_fm):
    """Demo 4: Keyboard shortcuts"""
    print_header(backend, "Demo 4: Keyboard Shortcuts")
    
    instructions = [
        "Keyboard shortcuts execute actions without opening menus:",
        "",
        "Try these shortcuts:",
        "  Cmd+N       - New File",
        "  Cmd+Shift+N - New Folder",
        "  Cmd+C       - Copy",
        "  Cmd+V       - Paste",
        "  Cmd+A       - Select All",
        "  Cmd+H       - Toggle Hidden Files",
        "",
        "Press any shortcut and see the action below:",
        "",
        "(Press Cmd+Q to quit when done)",
    ]
    
    print_instructions(backend, instructions)
    
    # Event loop to capture shortcuts
    event_row = 16
    
    while True:
        event = backend.get_event(timeout_ms=-1)
        
        if event is None:
            continue
        
        if isinstance(event, MenuEvent):
            # Clear previous message
            backend.clear_region(event_row, 0, 3, 80)
            
            # Display shortcut action
            shortcut_map = {
                'file.new_file': 'Cmd+N',
                'file.new_folder': 'Cmd+Shift+N',
                'file.quit': 'Cmd+Q',
                'edit.copy': 'Cmd+C',
                'edit.paste': 'Cmd+V',
                'edit.select_all': 'Cmd+A',
                'view.show_hidden': 'Cmd+H',
            }
            
            shortcut = shortcut_map.get(event.item_id, 'Unknown')
            msg = f"Shortcut pressed: {shortcut}"
            backend.draw_text(event_row, 2, msg, color_pair=2)
            
            action_desc = f"Action: {event.item_id}"
            backend.draw_text(event_row + 1, 4, action_desc, color_pair=1)
            
            # Handle quit
            if event.item_id == 'file.quit':
                backend.draw_text(event_row + 2, 4, "Quitting demo...", color_pair=1)
                backend.refresh()
                time.sleep(1)
                return True
            
            backend.refresh()
        
        elif isinstance(event, SystemEvent) and event.is_close():
            return False
        
        elif isinstance(event, KeyEvent):
            # Show key event for debugging
            if event.char and event.char.lower() == 'q' and not (event.modifiers & ModifierKey.COMMAND):
                # Regular Q key (not Cmd+Q)
                break
    
    return True


def main():
    """Main demo function"""
    print("Menu Bar Feature Demo")
    print("=" * 50)
    print()
    print("This demo demonstrates the complete menu bar functionality")
    print("in TFM's desktop mode.")
    print()
    print("The demo will show:")
    print("  1. Menu structure")
    print("  2. Menu selection and action execution")
    print("  3. Menu state updates based on application state")
    print("  4. Keyboard shortcuts")
    print()
    print("Press Enter to start the demo...")
    input()
    
    # Create backend
    backend = CoreGraphicsBackend(
        window_title="TFM - Menu Bar Demo",
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
        
        # Run demos
        if not demo_menu_structure(backend, menu_manager):
            return
        
        if not demo_menu_selection(backend, menu_manager, mock_fm):
            return
        
        if not demo_menu_state_updates(backend, menu_manager, mock_fm):
            return
        
        if not demo_keyboard_shortcuts(backend, menu_manager, mock_fm):
            return
        
        # Show completion message
        print_header(backend, "Demo Complete!")
        instructions = [
            "All menu bar features have been demonstrated:",
            "",
            "✓ Menu structure with File, Edit, View, Go menus",
            "✓ Menu selection and action execution",
            "✓ Menu state updates based on application state",
            "✓ Keyboard shortcuts for common actions",
            "",
            "The menu bar feature is fully functional and ready to use",
            "in TFM's desktop mode.",
            "",
            "To use TFM with menu bar in desktop mode:",
            "  python tfm.py --desktop",
            "",
            "Or:",
            "  python tfm.py --backend coregraphics",
        ]
        
        print_instructions(backend, instructions)
        wait_for_key(backend, "Press any key to exit...")
    
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
