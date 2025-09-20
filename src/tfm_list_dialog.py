#!/usr/bin/env python3
"""
TUI File Manager - List Dialog Component
Provides searchable list dialog functionality
"""

import curses
from pathlib import Path
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color
from tfm_config import get_favorite_directories, get_programs


class ListDialog:
    """Searchable list dialog component"""
    
    def __init__(self, config):
        self.config = config
        
        # List dialog state
        self.mode = False
        self.title = ""
        self.items = []  # List of items to choose from
        self.filtered_items = []  # Filtered items based on search
        self.selected = 0  # Index of currently selected item in filtered list
        self.scroll = 0  # Scroll offset for the list
        self.search_editor = SingleLineTextEdit()  # Search editor for list dialog
        self.callback = None  # Callback function when item is selected
        
    def show(self, title, items, callback):
        """Show a searchable list dialog
        
        Args:
            title: The title to display at the top of the dialog
            items: List of items to choose from (strings or objects with __str__ method)
            callback: Function to call with the selected item (or None if cancelled)
        """
        self.mode = True
        self.title = title
        self.items = items
        self.filtered_items = items.copy()  # Initially show all items
        self.selected = 0
        self.scroll = 0
        self.search_editor.clear()
        self.callback = callback
        
    def exit(self):
        """Exit list dialog mode"""
        self.mode = False
        self.title = ""
        self.items = []
        self.filtered_items = []
        self.selected = 0
        self.scroll = 0
        self.search_editor.clear()
        self.callback = None
        
    def handle_input(self, key):
        """Handle input while in list dialog mode"""
        if key == 27:  # ESC - cancel
            if self.callback:
                self.callback(None)
            self.exit()
            return True
        elif key == curses.KEY_UP:
            # Move selection up
            if self.filtered_items and self.selected > 0:
                self.selected -= 1
                self._adjust_scroll()
            return True
        elif key == curses.KEY_DOWN:
            # Move selection down
            if self.filtered_items and self.selected < len(self.filtered_items) - 1:
                self.selected += 1
                self._adjust_scroll()
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            if self.filtered_items:
                self.selected = max(0, self.selected - 10)
                self._adjust_scroll()
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            if self.filtered_items:
                self.selected = min(len(self.filtered_items) - 1, self.selected + 10)
                self._adjust_scroll()
            return True
        elif key == curses.KEY_HOME:  # Home - text cursor or list navigation
            # If there's text in search, let editor handle it for cursor movement
            if self.search_editor.text:
                if self.search_editor.handle_key(key):
                    return True
            else:
                # If no search text, use for list navigation
                if self.filtered_items:
                    self.selected = 0
                    self.scroll = 0
            return True
        elif key == curses.KEY_END:  # End - text cursor or list navigation
            # If there's text in search, let editor handle it for cursor movement
            if self.search_editor.text:
                if self.search_editor.handle_key(key):
                    return True
            else:
                # If no search text, use for list navigation
                if self.filtered_items:
                    self.selected = len(self.filtered_items) - 1
                    self._adjust_scroll()
            return True
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Select current item
            if self.filtered_items and 0 <= self.selected < len(self.filtered_items):
                selected_item = self.filtered_items[self.selected]
                if self.callback:
                    self.callback(selected_item)
            else:
                if self.callback:
                    self.callback(None)
            self.exit()
            return True
        elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
            # Let the editor handle cursor movement keys
            if self.search_editor.handle_key(key):
                return True
            return True
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            # Let the editor handle backspace
            if self.search_editor.handle_key(key):
                self._filter_items()
            return True
        elif 32 <= key <= 126:  # Printable characters
            # Let the editor handle printable characters
            if self.search_editor.handle_key(key):
                self._filter_items()
            return True
        return False
        
    def _filter_items(self):
        """Filter list dialog items based on current search pattern"""
        search_text = self.search_editor.text
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
        
    def _adjust_scroll(self):
        """Adjust scroll offset to keep selected item visible"""
        # Get dialog dimensions from config
        height_ratio = getattr(self.config, 'LIST_DIALOG_HEIGHT_RATIO', 0.7)
        min_height = getattr(self.config, 'LIST_DIALOG_MIN_HEIGHT', 15)
        
        # We need the screen height to calculate dialog height
        # This will be passed from the main class when drawing
        # For now, use a reasonable default
        screen_height = 24  # Default terminal height
        dialog_height = max(min_height, int(screen_height * height_ratio))
        content_height = dialog_height - 6  # Account for title, search, borders, help
        
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + content_height:
            self.scroll = self.selected - content_height + 1
            
    def draw(self, stdscr, safe_addstr_func):
        """Draw the searchable list dialog overlay"""
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions using configuration
        width_ratio = getattr(self.config, 'LIST_DIALOG_WIDTH_RATIO', 0.6)
        height_ratio = getattr(self.config, 'LIST_DIALOG_HEIGHT_RATIO', 0.7)
        min_width = getattr(self.config, 'LIST_DIALOG_MIN_WIDTH', 40)
        min_height = getattr(self.config, 'LIST_DIALOG_MIN_HEIGHT', 15)
        
        dialog_width = max(min_width, int(width * width_ratio))
        dialog_height = max(min_height, int(height * height_ratio))
        
        # Update scroll adjustment with actual screen height
        content_height = dialog_height - 6
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + content_height:
            self.scroll = self.selected - content_height + 1
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            if y < height:
                bg_line = " " * min(dialog_width, width - start_x)
                safe_addstr_func(y, start_x, bg_line, get_status_color())
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            safe_addstr_func(start_y, start_x, top_line[:dialog_width], border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                safe_addstr_func(y, start_x, "│", border_color)
                if start_x + dialog_width - 1 < width:
                    safe_addstr_func(y, start_x + dialog_width - 1, "│", border_color)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            safe_addstr_func(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], border_color)
        
        # Draw title
        if self.title and start_y >= 0:
            title_text = f" {self.title} "
            title_x = start_x + (dialog_width - len(title_text)) // 2
            if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
                safe_addstr_func(start_y, title_x, title_text, border_color)
        
        # Draw search box
        search_y = start_y + 2
        # Draw search input using SingleLineTextEdit
        if search_y < height:
            max_search_width = dialog_width - 4  # Leave some margin
            self.search_editor.draw(
                stdscr, search_y, start_x + 2, max_search_width,
                "Search: ",
                is_active=True
            )
        
        # Draw separator line
        sep_y = start_y + 3
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            safe_addstr_func(sep_y, start_x, sep_line[:dialog_width], border_color)
        
        # Calculate list area
        list_start_y = start_y + 4
        list_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = list_end_y - list_start_y + 1
        
        # Draw list items
        visible_items = self.filtered_items[self.scroll:self.scroll + content_height]
        
        for i, item in enumerate(visible_items):
            y = list_start_y + i
            if y <= list_end_y and y < height:
                item_index = self.scroll + i
                is_selected = item_index == self.selected
                
                # Format item text
                item_text = str(item)
                if len(item_text) > content_width - 2:
                    item_text = item_text[:content_width - 5] + "..."
                
                # Add selection indicator
                if is_selected:
                    display_text = f"► {item_text}"
                    item_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                else:
                    display_text = f"  {item_text}"
                    item_color = get_status_color()
                
                # Ensure text fits
                display_text = display_text[:content_width]
                safe_addstr_func(y, content_start_x, display_text, item_color)
        
        # Draw scroll indicators if needed
        if len(self.filtered_items) > content_height:
            scrollbar_x = start_x + dialog_width - 2
            scrollbar_start_y = list_start_y
            scrollbar_height = content_height
            
            # Calculate scroll thumb position
            total_items = len(self.filtered_items)
            if total_items > 0:
                thumb_pos = int((self.scroll / max(1, total_items - content_height)) * (scrollbar_height - 1))
                thumb_pos = max(0, min(scrollbar_height - 1, thumb_pos))
                
                for i in range(scrollbar_height):
                    y = scrollbar_start_y + i
                    if y < height:
                        if i == thumb_pos:
                            safe_addstr_func(y, scrollbar_x, "█", border_color)
                        else:
                            safe_addstr_func(y, scrollbar_x, "░", get_status_color() | curses.A_DIM)
        
        # Draw status info
        status_y = start_y + dialog_height - 2
        if status_y < height:
            if self.filtered_items:
                status_text = f"{self.selected + 1}/{len(self.filtered_items)} items"
                if len(self.filtered_items) != len(self.items):
                    status_text += f" (filtered from {len(self.items)})"
            else:
                status_text = "No items found"
            
            if self.search_editor.text:
                status_text += f" | Filter: '{self.search_editor.text}'"
            
            # Center the status text
            content_width = dialog_width - 4
            if len(status_text) <= content_width:
                status_x = start_x + (dialog_width - len(status_text)) // 2
                safe_addstr_func(status_y, status_x, status_text, get_status_color() | curses.A_DIM)
        
        # Draw help text at bottom
        help_text = "↑↓:select  Enter:choose  Type:search  Backspace:clear  ESC:cancel"
        help_y = start_y + dialog_height - 1
        content_width = dialog_width - 4
        if help_y < height and len(help_text) <= content_width:
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                safe_addstr_func(help_y, help_x, help_text, get_status_color() | curses.A_DIM)


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
    def show_file_type_filter(list_dialog, current_pane):
        """Show file type filter using the searchable list dialog"""
        # Get all unique file extensions in current directory
        extensions = set()
        for file_path in current_pane['files']:
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext:
                    extensions.add(ext)
                else:
                    extensions.add("(no extension)")
        
        if not extensions:
            print("No files with extensions found in current directory")
            return
        
        # Convert to sorted list
        extension_list = sorted(list(extensions))
        extension_list.insert(0, "(show all files)")  # Add option to show all
        
        def filter_callback(selected_ext):
            if selected_ext:
                if selected_ext == "(show all files)":
                    print("Showing all files")
                    # Reset any filtering (this would need additional implementation)
                else:
                    print(f"Filtering by extension: {selected_ext}")
                    # Filter files by extension (this would need additional implementation)
            else:
                print("File type filter cancelled")
        
        list_dialog.show("Filter by File Type", extension_list, filter_callback)
    
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