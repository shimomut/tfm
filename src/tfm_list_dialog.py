#!/usr/bin/env python3
"""
TUI File Manager - List Dialog Component
Provides searchable list dialog functionality
"""

from ttk import TextAttribute, KeyEvent, CharEvent
from tfm_path import Path
from tfm_base_list_dialog import BaseListDialog
from tfm_ui_layer import UILayer
from tfm_colors import get_status_color
from tfm_config import get_favorite_directories, get_programs
from tfm_input_compat import ensure_input_event
from tfm_log_manager import getLogger


class ListDialog(UILayer, BaseListDialog):
    """Searchable list dialog component"""
    
    def __init__(self, config, renderer=None):
        super().__init__(config, renderer)
        self.logger = getLogger("ListDialog")
        
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
        self.is_active = True
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
    
    def draw(self):
        """Draw the searchable list dialog overlay"""
        # Get configuration values
        width_ratio = getattr(self.config, 'LIST_DIALOG_WIDTH_RATIO', 0.6)
        height_ratio = getattr(self.config, 'LIST_DIALOG_HEIGHT_RATIO', 0.7)
        min_width = getattr(self.config, 'LIST_DIALOG_MIN_WIDTH', 40)
        min_height = getattr(self.config, 'LIST_DIALOG_MIN_HEIGHT', 15)
        
        # Draw dialog frame
        start_y, start_x, dialog_width, dialog_height = self.draw_dialog_frame(
            self.title, width_ratio, height_ratio, min_width, min_height
        )
        
        # Draw search input
        search_y = start_y + 2
        self.draw_text_input(search_y, start_x, dialog_width, "Search: ")
        
        # Draw separator
        sep_y = start_y + 3
        self.draw_separator(sep_y, start_x, dialog_width)
        
        # Calculate list area
        list_start_y = start_y + 4
        list_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Draw list items
        self.draw_list_items(self.filtered_items, 
                           list_start_y, list_end_y, content_start_x, content_width)
        
        # Draw scrollbar
        scrollbar_x = start_x + dialog_width - 2
        content_height = list_end_y - list_start_y + 1
        self.draw_scrollbar(self.filtered_items, 
                          list_start_y, content_height, scrollbar_x)
        
        # Draw status info
        height, _ = self.renderer.get_dimensions()
        status_y = start_y + dialog_height - 2
        if status_y < height:
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
                status_color_pair, _ = get_status_color()
                # Note: TTK doesn't have A_DIM, using NORMAL instead
                self.renderer.draw_text(status_y, status_x, status_text, color_pair=status_color_pair, attributes=TextAttribute.NORMAL)
        
        # Draw help text
        if self.custom_help_text:
            help_text = self.custom_help_text
        else:
            help_text = "↑↓:select  Enter:choose  Type:search  Backspace:clear  ESC:cancel"
        
        help_y = start_y + dialog_height - 1
        self.draw_help_text(help_text, help_y, start_x, dialog_width)
        
        # Automatically mark as not needing redraw after drawing
        self.content_changed = False
    
    # UILayer interface implementation
    
    def handle_key_event(self, event) -> bool:
        """
        Handle a key event (UILayer interface).
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        # Backward compatibility: convert integer key codes to KeyEvent
        event = ensure_input_event(event)
        
        if not event or not isinstance(event, KeyEvent):
            return False
        
        # Check custom key handler first
        if self.custom_key_handler and self.custom_key_handler(event):
            return True
        
        # Use base class navigation handling
        result = self.handle_common_navigation(event, self.filtered_items)
        
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
            self.content_changed = True
            return True
        elif result:
            self.content_changed = True
            return True
        
        return False
    
    def handle_char_event(self, event) -> bool:
        """
        Handle a character event (UILayer interface).
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        # Backward compatibility: convert integer key codes to CharEvent
        event = ensure_input_event(event)
        
        if not event or not isinstance(event, CharEvent):
            return False
        
        # Pass to text editor
        if self.text_editor.handle_key(event):
            self._filter_items()
            self.content_changed = True
            return True
        
        return False
    
    def handle_system_event(self, event) -> bool:
        """
        Handle a system event (UILayer interface).
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        if event.is_resize():
            # Mark content as changed to trigger redraw with new dimensions
            self.content_changed = True
            return True
        elif event.is_close():
            # Close the dialog
            self.is_active = False
            return True
        return False
    
    def handle_mouse_event(self, event) -> bool:
        """
        Handle a mouse event (UILayer interface).
        
        Supports mouse wheel scrolling for vertical navigation.
        
        Args:
            event: MouseEvent to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        # Call BaseListDialog's wheel scrolling method directly
        result = BaseListDialog.handle_mouse_event(self, event, self.filtered_items)
        
        # Mark content as changed if scroll position changed
        if result:
            self.content_changed = True
        
        return result
    
    def render(self, renderer) -> None:
        """
        Render the layer's content (UILayer interface).
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        self.draw()
    
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen (UILayer interface).
        
        Returns:
            False - dialogs are overlays, not full-screen
        """
        return False
    
    def mark_dirty(self) -> None:
        """
        Mark this layer as needing a redraw (UILayer interface).
        """
        self.content_changed = True
    
    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after rendering (UILayer interface).
        """
        self.content_changed = False
    
    def should_close(self) -> bool:
        """
        Query if this layer wants to close (UILayer interface).
        
        Returns:
            True if the layer should be closed, False otherwise
        """
        return not self.is_active
    
    def on_activate(self) -> None:
        """
        Called when this layer becomes the top layer (UILayer interface).
        """
        self.content_changed = True  # Ensure dialog is drawn when activated
    
    def on_deactivate(self) -> None:
        """
        Called when this layer is no longer the top layer (UILayer interface).
        """
        pass


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
        
        # Create module-level logger for demo
        demo_logger = getLogger("ListDialog")
        
        def callback(selected_item):
            if selected_item:
                demo_logger.info(f"You selected: {selected_item}")
            else:
                demo_logger.info("Selection cancelled")
        
        list_dialog.show("Choose a Fruit", sample_items, callback)
    
    @staticmethod
    def show_favorite_directories(list_dialog, pane_manager, print_func):
        """Show favorite directories using the searchable list dialog
        
        Args:
            list_dialog: The ListDialog instance
            pane_manager: The PaneManager instance
            print_func: Function to print messages
        """
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
                            current_pane['focused_index'] = 0
                            current_pane['scroll_offset'] = 0
                            current_pane['selected_files'].clear()  # Clear selections
                            
                            # Refresh the file list for the current pane
                            pane_manager.refresh_files(current_pane)
                            
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
        """Show compare selection menu to select files and directories based on comparison with other pane"""
        
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
            
            # Get files and directories from other pane for comparison
            other_items = {}
            for item_path in other_pane['files']:
                name = item_path.name
                try:
                    if item_path.is_file():
                        size = item_path.stat().st_size if item_path.exists() else 0
                        mtime = item_path.stat().st_mtime if item_path.exists() else 0
                        other_items[name] = {'size': size, 'mtime': mtime, 'path': item_path, 'is_dir': False}
                    elif item_path.is_dir():
                        # For directories, use 0 as size and get mtime
                        mtime = item_path.stat().st_mtime if item_path.exists() else 0
                        other_items[name] = {'size': 0, 'mtime': mtime, 'path': item_path, 'is_dir': True}
                except (OSError, FileNotFoundError) as e:
                    logger = getLogger("ListDialog")
                    logger.warning(f"Could not get stats for {item_path}: {e}")
                    continue
                except Exception as e:
                    logger = getLogger("ListDialog")
                    logger.warning(f"Unexpected error checking {item_path}: {e}")
                    continue
            
            if not other_items:
                print_func("No items in other pane to compare with")
                return
            
            # Find matching items in current pane based on selected criteria
            matching_items = []
            total_items = 0
            
            for item_path in current_pane['files']:
                total_items += 1
                name = item_path.name
                
                if name in other_items:
                    other_item = other_items[name]
                    is_match = False
                    
                    try:
                        # Check if both items are the same type (file vs directory)
                        current_is_dir = item_path.is_dir()
                        if current_is_dir != other_item['is_dir']:
                            continue  # Skip if one is file and other is directory
                        
                        if selected_option == "By filename":
                            # Just filename match (and same type)
                            is_match = True
                            
                        elif selected_option == "By filename and size":
                            # Filename and size match
                            if current_is_dir:
                                # For directories, only match by name (size is always 0)
                                is_match = True
                            else:
                                # For files, match by size
                                current_size = item_path.stat().st_size if item_path.exists() else 0
                                is_match = current_size == other_item['size']
                                
                        elif selected_option == "By filename, size, and timestamp":
                            # Filename, size, and timestamp match
                            current_mtime = item_path.stat().st_mtime if item_path.exists() else 0
                            
                            if current_is_dir:
                                # For directories, match by name and timestamp
                                is_match = abs(current_mtime - other_item['mtime']) < 1.0  # Allow 1 second difference
                            else:
                                # For files, match by size and timestamp
                                current_size = item_path.stat().st_size if item_path.exists() else 0
                                is_match = (current_size == other_item['size'] and 
                                          abs(current_mtime - other_item['mtime']) < 1.0)  # Allow 1 second difference
                        
                        if is_match:
                            matching_items.append(str(item_path))
                            
                    except (OSError, FileNotFoundError) as e:
                        logger = getLogger("ListDialog")
                        logger.warning(f"Could not get stats for {item_path}: {e}")
                        continue
                    except Exception as e:
                        logger = getLogger("ListDialog")
                        logger.warning(f"Unexpected error checking {item_path}: {e}")
                        continue
            
            # Select the matching items
            if matching_items:
                # Clear current selections
                current_pane['selected_files'].clear()
                
                # Add matching items to selection
                for item_path_str in matching_items:
                    current_pane['selected_files'].add(item_path_str)
                
                # Count files and directories for better user feedback
                file_count = 0
                dir_count = 0
                for item_path_str in matching_items:
                    try:
                        from pathlib import Path
                        item_path = Path(item_path_str)
                        if item_path.is_dir():
                            dir_count += 1
                        else:
                            file_count += 1
                    except Exception:
                        file_count += 1  # Default to file if we can't determine
                
                # Create descriptive message
                if file_count > 0 and dir_count > 0:
                    items_desc = f"{file_count} files and {dir_count} directories"
                elif dir_count > 0:
                    items_desc = f"{dir_count} directories"
                else:
                    items_desc = f"{file_count} files"
                
                print_func(f"Selected {len(matching_items)} items ({items_desc}) matching {selected_option.lower()}")
                print_func(f"Criteria: {selected_option}")
            else:
                print_func(f"No items found matching {selected_option.lower()}")
        
        list_dialog.show("Compare Selection", compare_options, compare_callback)