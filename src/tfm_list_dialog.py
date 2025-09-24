#!/usr/bin/env python3
"""
TUI File Manager - List Dialog Component
Provides searchable list dialog functionality
"""

import curses
from pathlib import Path
from tfm_base_list_dialog import BaseListDialog
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color
from tfm_config import get_favorite_directories, get_programs


class ListDialog(BaseListDialog):
    """Searchable list dialog component"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # List dialog specific state
        self.title = ""
        self.items = []  # List of items to choose from
        self.filtered_items = []  # Filtered items based on search
        self.callback = None  # Callback function when item is selected
        self.custom_key_handler = None  # Custom key handler function
        self.custom_help_text = None  # Custom help text to display at bottom
        self.content_changed = True  # Track if content needs redraw
        
    def show(self, title, items, callback, custom_key_handler=None, custom_help_text=None):
        """Show a searchable list dialog
        
        Args:
            title: The title to display at the top of the dialog
            items: List of items to choose from (strings or objects with __str__ method)
            callback: Function to call with the selected item (or None if cancelled)
            custom_key_handler: Optional function to handle custom keys (key) -> bool
            custom_help_text: Optional custom help text to display at bottom
        """
        self.mode = True
        self.title = title
        self.items = items
        self.filtered_items = items.copy()  # Initially show all items
        self.selected = 0
        self.scroll = 0
        self.text_editor.clear()
        self.callback = callback
        self.custom_key_handler = custom_key_handler
        self.custom_help_text = custom_help_text
        self.content_changed = True  # Mark content as changed when showing
        
    def exit(self):
        """Exit list dialog mode"""
        super().exit()
        self.title = ""
        self.items = []
        self.filtered_items = []
        self.callback = None
        self.custom_key_handler = None
        self.custom_help_text = None
        self.content_changed = True  # Mark content as changed when exiting
        
    def handle_input(self, key):
        """Handle input while in list dialog mode"""
        # Check custom key handler first
        if self.custom_key_handler and self.custom_key_handler(key):
            return True
            
        # Use base class navigation handling
        result = self.handle_common_navigation(key, self.filtered_items)
        
        if result == 'cancel':
            # Store callback before exiting
            callback = self.callback
            self.exit()
            # Call callback after exiting to allow new dialogs
            if callback:
                callback(None)
            return True
        elif result == 'select':
            # Select current item
            callback = self.callback
            if self.filtered_items and 0 <= self.selected < len(self.filtered_items):
                selected_item = self.filtered_items[self.selected]
                self.exit()
                # Call callback after exiting to allow new dialogs
                if callback:
                    callback(selected_item)
            else:
                self.exit()
                # Call callback after exiting to allow new dialogs
                if callback:
                    callback(None)
            return True
        elif result == 'text_changed':
            self._filter_items()
            self.content_changed = True  # Mark content as changed when filtering
            return True
        elif result:
            self.content_changed = True  # Mark content as changed for navigation
            return True
            
        return False
        
    def _filter_items(self):
        """Filter list dialog items based on current search pattern"""
        search_text = self.text_editor.text
        if not search_text:
            self.filtered_items = self.items.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_items = [
                item for item in self.items 
                if search_lower in str(item).lower()
            ]
        
        # Reset selection to top of filtered list
        self.selected = 0
        self.scroll = 0

            
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        return self.content_changed
    
    def draw(self, stdscr, safe_addstr_func):
        """Draw the searchable list dialog overlay"""
        # Get configuration values
        width_ratio = getattr(self.config, 'LIST_DIALOG_WIDTH_RATIO', 0.6)
        height_ratio = getattr(self.config, 'LIST_DIALOG_HEIGHT_RATIO', 0.7)
        min_width = getattr(self.config, 'LIST_DIALOG_MIN_WIDTH', 40)
        min_height = getattr(self.config, 'LIST_DIALOG_MIN_HEIGHT', 15)
        
        # Draw dialog frame
        start_y, start_x, dialog_width, dialog_height = self.draw_dialog_frame(
            stdscr, safe_addstr_func, self.title, width_ratio, height_ratio, min_width, min_height
        )
        
        # Draw search input
        search_y = start_y + 2
        self.draw_text_input(stdscr, safe_addstr_func, search_y, start_x, dialog_width, "Search: ")
        
        # Draw separator
        sep_y = start_y + 3
        self.draw_separator(stdscr, safe_addstr_func, sep_y, start_x, dialog_width)
        
        # Calculate list area
        list_start_y = start_y + 4
        list_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Draw list items
        self.draw_list_items(stdscr, safe_addstr_func, self.filtered_items, 
                           list_start_y, list_end_y, content_start_x, content_width)
        
        # Draw scrollbar
        scrollbar_x = start_x + dialog_width - 2
        content_height = list_end_y - list_start_y + 1
        self.draw_scrollbar(stdscr, safe_addstr_func, self.filtered_items, 
                          list_start_y, content_height, scrollbar_x)
        
        # Draw status info
        status_y = start_y + dialog_height - 2
        if status_y < stdscr.getmaxyx()[0]:
            if self.filtered_items:
                status_text = f"{self.selected + 1}/{len(self.filtered_items)} items"
                if len(self.filtered_items) != len(self.items):
                    status_text += f" (filtered from {len(self.items)})"
            else:
                status_text = "No items found"
            
            if self.text_editor.text:
                status_text += f" | Filter: '{self.text_editor.text}'"
            
            # Center the status text
            content_width = dialog_width - 4
            if len(status_text) <= content_width:
                status_x = start_x + (dialog_width - len(status_text)) // 2
                safe_addstr_func(status_y, status_x, status_text, get_status_color() | curses.A_DIM)
        
        # Draw help text
        if self.custom_help_text:
            help_text = self.custom_help_text
        else:
            help_text = "↑↓:select  Enter:choose  Type:search  Backspace:clear  ESC:cancel"
        
        help_y = start_y + dialog_height - 1
        self.draw_help_text(stdscr, safe_addstr_func, help_text, help_y, start_x, dialog_width)
        
        # Automatically mark as not needing redraw after drawing
        self.content_changed = False


class ListDialogHelpers:
    """Helper functions for common list dialog use cases"""
    
    @staticmethod
    def show_demo(list_dialog):
        """Demo function to show the searchable list dialog"""
        # Create a sample list of items
        sample_items = [
            "Apple", "Banana", "Cherry", "Date", "Elderberry", "Fig", "Grape",
            "Honeydew", "Ice cream bean", "Jackfruit", "Kiwi", "Lemon", "Mango",
            "Nectarine", "Orange", "Papaya", "Quince", "Raspberry", "Strawberry",
            "Tangerine", "Ugli fruit", "Vanilla bean", "Watermelon", "Xigua",
            "Yellow passion fruit", "Zucchini"
        ]
        
        def callback(selected_item):
            if selected_item:
                print(f"You selected: {selected_item}")
            else:
                print("Selection cancelled")
        
        list_dialog.show("Choose a Fruit", sample_items, callback)
    
    @staticmethod
    def show_favorite_directories(list_dialog, pane_manager, print_func):
        """Show favorite directories using the searchable list dialog"""
        favorites = get_favorite_directories()
        
        if not favorites:
            print_func("No favorite directories configured")
            return
        
        # Create display items with name and path
        display_items = []
        for fav in favorites:
            display_items.append(f"{fav['name']} ({fav['path']})")
        
        def favorite_callback(selected_item):
            if selected_item:
                # Extract the path from the selected item
                # Format is "Name (path)"
                try:
                    # Find the path in parentheses
                    start_paren = selected_item.rfind('(')
                    end_paren = selected_item.rfind(')')
                    if start_paren != -1 and end_paren != -1 and end_paren > start_paren:
                        selected_path = selected_item[start_paren + 1:end_paren]
                        
                        # Change current pane to selected directory
                        current_pane = pane_manager.get_current_pane()
                        target_path = Path(selected_path)
                        
                        if target_path.exists() and target_path.is_dir():
                            old_path = current_pane['path']
                            current_pane['path'] = target_path
                            current_pane['selected_index'] = 0
                            current_pane['scroll_offset'] = 0
                            current_pane['selected_files'].clear()  # Clear selections
                            
                            pane_name = "left" if pane_manager.active_pane == 'left' else "right"
                            print_func(f"Changed {pane_name} pane to favorite: {old_path} → {target_path}")
                        else:
                            print_func(f"Error: Directory no longer exists: {selected_path}")
                    else:
                        print_func("Error: Could not parse selected favorite directory")
                except Exception as e:
                    print_func(f"Error changing to favorite directory: {e}")
            else:
                print_func("Favorite directory selection cancelled")
        
        list_dialog.show("Go to Favorite Directory", display_items, favorite_callback)
    
    @staticmethod
    def show_programs_dialog(list_dialog, execute_program_func, print_func):
        """Show external programs using the searchable list dialog"""
        programs = get_programs()
        
        if not programs:
            print_func("No external programs configured")
            return
        
        # Create display items with program names
        display_items = []
        for prog in programs:
            display_items.append(prog['name'])
        
        def program_callback(selected_item):
            if selected_item:
                # Find the selected program
                selected_program = None
                for prog in programs:
                    if prog['name'] == selected_item:
                        selected_program = prog
                        break
                
                if selected_program:
                    execute_program_func(selected_program)
                else:
                    print_func(f"Error: Program not found: {selected_item}")
            else:
                print_func("Program selection cancelled")
        
        list_dialog.show("External Programs", display_items, program_callback)
    
    @staticmethod
    def show_compare_selection(list_dialog, current_pane, other_pane, print_func):
        """Show compare selection menu to select files based on comparison with other pane"""
        
        # Define comparison options
        compare_options = [
            "By filename",
            "By filename and size", 
            "By filename, size, and timestamp"
        ]
        
        def compare_callback(selected_option):
            if not selected_option:
                print_func("Compare selection cancelled")
                return
            
            # Get files from other pane for comparison
            other_files = {}
            for file_path in other_pane['files']:
                if file_path.is_file():  # Only compare files, not directories
                    name = file_path.name
                    size = file_path.stat().st_size if file_path.exists() else 0
                    mtime = file_path.stat().st_mtime if file_path.exists() else 0
                    other_files[name] = {'size': size, 'mtime': mtime, 'path': file_path}
            
            if not other_files:
                print_func("No files in other pane to compare with")
                return
            
            # Find matching files in current pane based on selected criteria
            matching_files = []
            total_files = 0
            
            for file_path in current_pane['files']:
                if file_path.is_file():  # Only compare files, not directories
                    total_files += 1
                    name = file_path.name
                    
                    if name in other_files:
                        other_file = other_files[name]
                        is_match = False
                        
                        if selected_option == "By filename":
                            # Just filename match
                            is_match = True
                            
                        elif selected_option == "By filename and size":
                            # Filename and size match
                            try:
                                current_size = file_path.stat().st_size if file_path.exists() else 0
                                is_match = current_size == other_file['size']
                            except:
                                is_match = False
                                
                        elif selected_option == "By filename, size, and timestamp":
                            # Filename, size, and timestamp match
                            try:
                                current_size = file_path.stat().st_size if file_path.exists() else 0
                                current_mtime = file_path.stat().st_mtime if file_path.exists() else 0
                                is_match = (current_size == other_file['size'] and 
                                          abs(current_mtime - other_file['mtime']) < 1.0)  # Allow 1 second difference
                            except:
                                is_match = False
                        
                        if is_match:
                            matching_files.append(str(file_path))
            
            # Select the matching files
            if matching_files:
                # Clear current selections
                current_pane['selected_files'].clear()
                
                # Add matching files to selection
                for file_path_str in matching_files:
                    current_pane['selected_files'].add(file_path_str)
                
                print_func(f"Selected {len(matching_files)} files in current pane matching {selected_option.lower()}")
                print_func(f"Criteria: {selected_option}")
            else:
                print_func(f"No files found matching {selected_option.lower()}")
        
        list_dialog.show("Compare Selection", compare_options, compare_callback)