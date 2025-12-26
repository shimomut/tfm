#!/usr/bin/env python3
"""
TUI File Manager - Batch Rename Dialog Component
Provides batch file renaming functionality with regex patterns
"""

import re
from ttk import TextAttribute, KeyCode, KeyEvent, CharEvent
from tfm_path import Path
from tfm_base_list_dialog import BaseListDialog
from tfm_ui_layer import UILayer
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_colors import get_status_color, COLOR_ERROR
from tfm_wide_char_utils import get_display_width, get_safe_functions
from tfm_input_compat import ensure_input_event
from tfm_log_manager import getLogger

# Module-level logger
logger = getLogger("BatchRename")


class BatchRenameDialog(UILayer, BaseListDialog):
    """Batch rename dialog component for renaming multiple files with regex patterns"""
    
    def __init__(self, config, renderer=None):
        super().__init__(config, renderer)
        
        # Batch rename dialog specific state
        self.regex_editor = SingleLineTextEdit()
        self.destination_editor = SingleLineTextEdit()
        self.active_field = 'regex'  # 'regex' or 'destination'
        self.files = []  # List of selected files to rename
        self.preview = []  # List of preview results
        self.content_changed = True  # Track if content needs redraw
        
    def show(self, selected_files):
        """Show the batch rename dialog for multiple selected files
        
        Args:
            selected_files: List of Path objects representing files to rename
        """
        if not selected_files:
            return False
            
        self.is_active = True
        self.files = selected_files
        self.regex_editor.clear()
        self.destination_editor.clear()
        self.active_field = 'regex'
        self.preview = []
        self.scroll = 0
        self.content_changed = True  # Mark content as changed when showing
        return True
        
    def exit(self):
        """Exit batch rename mode"""
        super().exit()
        self.content_changed = True  # Mark content as changed when exiting
        self.files = []
        self.regex_editor.clear()
        self.destination_editor.clear()
        self.active_field = 'regex'
        self.preview = []
        
    def get_active_editor(self):
        """Get the currently active text editor"""
        return self.regex_editor if self.active_field == 'regex' else self.destination_editor
    
    def switch_field(self, field):
        """Switch to the specified field"""
        if field in ['regex', 'destination'] and field != self.active_field:
            self.active_field = field
            return True
        return False
        
    def update_preview(self):
        """Update the preview list for batch rename"""
        self.preview = []
        
        regex_pattern = self.regex_editor.get_text()
        destination_pattern = self.destination_editor.get_text()
        
        if not regex_pattern or not destination_pattern:
            return
        
        try:
            pattern = re.compile(regex_pattern)
        except re.error:
            # Invalid regex pattern
            return
        
        for i, file_path in enumerate(self.files):
            original_name = file_path.name
            match = pattern.search(original_name)
            
            if match:
                # Apply substitution with macro support
                new_name = destination_pattern
                
                # Replace regex groups (\1, \2, etc.)
                for group_num in range(10):  # Support up to 9 groups
                    group_placeholder = f"\\{group_num}"
                    if group_placeholder in new_name:
                        if group_num == 0:
                            # \0 = full match
                            new_name = new_name.replace(group_placeholder, match.group(0))
                        elif group_num <= len(match.groups()):
                            # \1-\9 = regex groups
                            group_value = match.group(group_num) or ""
                            new_name = new_name.replace(group_placeholder, group_value)
                        else:
                            # Group doesn't exist, replace with empty string
                            new_name = new_name.replace(group_placeholder, "")
                
                # Replace index macro (\d)
                new_name = new_name.replace("\\d", str(i + 1))
                
                # Check if new name is valid and doesn't conflict
                valid = self._is_valid_filename(new_name)
                new_path = file_path.parent / new_name
                conflict = new_path.exists() and new_path != file_path
                
                self.preview.append({
                    'original': original_name,
                    'new': new_name,
                    'valid': valid,
                    'conflict': conflict
                })
            else:
                # No match - keep original name
                self.preview.append({
                    'original': original_name,
                    'new': original_name,
                    'valid': True,
                    'conflict': False
                })
                
    def _is_valid_filename(self, filename):
        """Check if a filename is valid"""
        if not filename or filename in ['.', '..']:
            return False
        
        # Check for invalid characters (basic check)
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in filename:
                return False
        
        return True
        
    def perform_rename(self):
        """Perform the batch rename operation
        
        Returns:
            tuple: (success_count, errors) where errors is a list of error messages
        """
        if not self.preview:
            return 0, ["No rename preview available"]
        
        # Check for conflicts and invalid names
        conflicts = [p for p in self.preview if p['conflict']]
        invalid = [p for p in self.preview if not p['valid']]
        
        if conflicts:
            conflict_names = [p['new'] for p in conflicts]
            return 0, [f"Name conflicts detected: {', '.join(conflict_names)}"]
        
        if invalid:
            invalid_names = [p['new'] for p in invalid]
            return 0, [f"Invalid names detected: {', '.join(invalid_names)}"]
        
        # Perform the renames
        success_count = 0
        errors = []
        
        for i, preview in enumerate(self.preview):
            if preview['original'] != preview['new']:
                try:
                    old_path = self.files[i]
                    new_path = old_path.parent / preview['new']
                    old_path.rename(new_path)
                    success_count += 1
                except Exception as e:
                    errors.append(f"Failed to rename {preview['original']}: {str(e)}")
        
        return success_count, errors
        
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        return self.content_changed
    
    def draw(self):
        """Draw the batch rename dialog overlay"""
        if not self.renderer:
            return
            
        height, width = self.renderer.get_dimensions()
        
        # Calculate dialog dimensions safely for narrow terminals
        desired_width = int(width * 0.9)
        desired_height = int(height * 0.9)
        
        # Apply minimum constraints, but never exceed terminal size
        dialog_width = max(80, desired_width)
        dialog_width = min(dialog_width, width)  # Never exceed terminal width
        
        dialog_height = max(25, desired_height)
        dialog_height = min(dialog_height, height)  # Never exceed terminal height
        
        # Calculate safe centering
        start_y = max(0, (height - dialog_height) // 2)
        start_x = max(0, (width - dialog_width) // 2)
        
        # Draw dialog background
        # Use draw_hline() to properly clear wide characters underneath
        status_color_pair, status_attributes = get_status_color()
        
        for y in range(start_y, start_y + dialog_height):
            if y < height and y >= 0 and start_x >= 0 and start_x < width:
                columns_to_fill = min(dialog_width, width - start_x)
                try:
                    self.renderer.draw_hline(y, start_x, ' ', columns_to_fill, color_pair=status_color_pair)
                except Exception as e:
                    # Fallback to draw_text if draw_hline fails
                    try:
                        bg_line = " " * columns_to_fill
                        self.renderer.draw_text(y, start_x, bg_line, color_pair=status_color_pair)
                    except Exception:
                        pass
        
        # Draw border with safe drawing
        border_color_pair, _ = get_status_color()
        border_attributes = TextAttribute.BOLD
        
        # Top border
        if start_y >= 0 and start_y < height:
            top_line = "┌" + "─" * max(0, dialog_width - 2) + "┐"
            # Truncate if line would exceed terminal width
            if start_x + len(top_line) > width:
                top_line = top_line[:width - start_x]
            if top_line:
                self.renderer.draw_text(start_y, start_x, top_line, color_pair=border_color_pair, attributes=border_attributes)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height and y >= 0:
                # Left border
                if start_x >= 0 and start_x < width:
                    self.renderer.draw_text(y, start_x, "│", color_pair=border_color_pair, attributes=border_attributes)
                # Right border
                right_x = start_x + dialog_width - 1
                if right_x >= 0 and right_x < width:
                    self.renderer.draw_text(y, right_x, "│", color_pair=border_color_pair, attributes=border_attributes)
        
        # Bottom border
        bottom_y = start_y + dialog_height - 1
        if bottom_y >= 0 and bottom_y < height:
            bottom_line = "└" + "─" * max(0, dialog_width - 2) + "┘"
            # Truncate if line would exceed terminal width
            if start_x + len(bottom_line) > width:
                bottom_line = bottom_line[:width - start_x]
            if bottom_line:
                self.renderer.draw_text(bottom_y, start_x, bottom_line, color_pair=border_color_pair, attributes=border_attributes)
        
        # Draw title using wide character utilities with safe positioning
        title_text = f" Batch Rename ({len(self.files)} files) "
        # Get safe wide character functions
        safe_funcs = get_safe_functions()
        get_width = safe_funcs['get_display_width']
        truncate_text = safe_funcs['truncate_to_width']
        
        title_width = get_width(title_text)
        
        # Truncate title if it's too wide for the dialog
        if title_width > dialog_width:
            title_text = truncate_text(title_text, dialog_width - 2, "…")
            title_width = get_width(title_text)
        
        title_x = start_x + (dialog_width - title_width) // 2
        # Ensure title fits within terminal bounds
        if title_x >= 0 and title_x < width and title_x + title_width <= width:
            self.renderer.draw_text(start_y, title_x, title_text, color_pair=border_color_pair, attributes=border_attributes)
        
        # Content area
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Draw regex input
        regex_y = start_y + 2
        regex_label = "Regex Pattern: "
        
        if regex_y < height:
            # Draw regex input field using SingleLineTextEdit
            self.regex_editor.draw(
                self.renderer, regex_y, content_start_x, content_width,
                regex_label,
                is_active=(self.active_field == 'regex')
            )
        
        # Draw destination input
        dest_y = start_y + 3
        dest_label = "Destination:   "
        
        if dest_y < height:
            # Draw destination input field using SingleLineTextEdit
            self.destination_editor.draw(
                self.renderer, dest_y, content_start_x, content_width,
                dest_label,
                is_active=(self.active_field == 'destination')
            )
        
        # Draw navigation help
        nav_help_y = start_y + 4
        if nav_help_y < height:
            nav_help_text = "Navigation: ↑/↓=Switch fields, Tab=Alt switch, PgUp/PgDn=Scroll preview"
            status_color_pair, _ = get_status_color()
            self.renderer.draw_text(nav_help_y, content_start_x, nav_help_text[:content_width], 
                             color_pair=status_color_pair, attributes=TextAttribute.NORMAL)
        
        # Draw help for macros
        help_y = start_y + 5
        if help_y < height:
            help_text = "Macros: \\0=full name, \\1-\\9=regex groups, \\d=index"
            status_color_pair, _ = get_status_color()
            self.renderer.draw_text(help_y, content_start_x, help_text[:content_width], 
                             color_pair=status_color_pair, attributes=TextAttribute.NORMAL)
        
        # Draw separator line
        sep_y = start_y + 6
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            self.renderer.draw_text(sep_y, start_x, sep_line[:dialog_width], 
                             color_pair=border_color_pair, attributes=border_attributes)
        
        # Draw preview header
        preview_header_y = start_y + 7
        if preview_header_y < height:
            header_text = "Preview:"
            header_color_pair, _ = get_status_color()
            self.renderer.draw_text(preview_header_y, content_start_x, header_text, 
                             color_pair=header_color_pair, attributes=TextAttribute.BOLD)
        
        # Calculate preview area
        preview_start_y = start_y + 8
        preview_end_y = start_y + dialog_height - 3
        preview_height = preview_end_y - preview_start_y + 1
        
        # Draw preview list
        if self.preview:
            visible_preview = self.preview[self.scroll:self.scroll + preview_height]
            
            for i, preview in enumerate(visible_preview):
                y = preview_start_y + i
                if y <= preview_end_y and y < height:
                    original = preview['original']
                    new = preview['new']
                    conflict = preview['conflict']
                    valid = preview['valid']
                    
                    # Format preview line
                    if original == new:
                        status = "UNCHANGED"
                        status_color_pair, status_attributes = get_status_color()
                    elif conflict:
                        status = "CONFLICT!"
                        status_color_pair = COLOR_ERROR
                        status_attributes = TextAttribute.BOLD
                    elif not valid:
                        status = "INVALID!"
                        status_color_pair = COLOR_ERROR
                        status_attributes = TextAttribute.BOLD
                    else:
                        status = "OK"
                        status_color_pair, status_attributes = get_status_color()
                    
                    # Create preview line using wide character utilities
                    max_name_width = (content_width - 20) // 2
                    truncate_text = safe_funcs['truncate_to_width']
                    pad_text = safe_funcs['pad_to_width']
                    
                    if get_width(original) > max_name_width:
                        original_display = truncate_text(original, max_name_width, "")
                    else:
                        original_display = original
                        
                    if get_width(new) > max_name_width:
                        new_display = truncate_text(new, max_name_width, "")
                    else:
                        new_display = new
                    
                    # Use wide character utilities for proper alignment
                    original_padded = pad_text(original_display, max_name_width, 'left')
                    new_padded = pad_text(new_display, max_name_width, 'left')
                    
                    preview_line = f"{original_padded} → {new_padded} [{status}]"
                    
                    # Truncate the entire line if it's too long
                    if get_width(preview_line) > content_width:
                        preview_line = truncate_text(preview_line, content_width, "")
                    
                    self.renderer.draw_text(y, content_start_x, preview_line, 
                                     color_pair=status_color_pair, attributes=status_attributes)
        else:
            # No preview available
            no_preview_y = preview_start_y + 2
            if no_preview_y < height:
                no_preview_text = "Enter regex pattern and destination to see preview"
                status_color_pair, _ = get_status_color()
                self.renderer.draw_text(no_preview_y, content_start_x, no_preview_text, 
                                 color_pair=status_color_pair, attributes=TextAttribute.NORMAL)
        
        # Draw help text with safe positioning
        help_y = start_y + dialog_height - 2
        if help_y < height and help_y >= 0:
            help_text = "Tab: Switch input | ←→: Move cursor | Home/End: Start/End | Enter: Rename | ESC: Cancel"
            help_width = get_width(help_text)
            
            if help_width <= dialog_width:
                help_x = start_x + (dialog_width - help_width) // 2
                # Ensure help text fits within terminal bounds
                if help_x >= 0 and help_x < width and help_x + help_width <= width:
                    status_color_pair, _ = get_status_color()
                    self.renderer.draw_text(help_y, help_x, help_text, 
                                     color_pair=status_color_pair, attributes=TextAttribute.NORMAL)
            else:
                # Truncate help text if too wide
                truncate_text = safe_funcs['truncate_to_width']
                available_width = min(dialog_width - 4, width - start_x - 2)
                if available_width > 0:
                    truncated_help = truncate_text(help_text, available_width, "…")
                    help_width = get_width(truncated_help)
                    help_x = start_x + (dialog_width - help_width) // 2
                    # Ensure truncated help text fits within terminal bounds
                    if help_x >= 0 and help_x < width and help_x + help_width <= width:
                        status_color_pair, _ = get_status_color()
                        self.renderer.draw_text(help_y, help_x, truncated_help, 
                                         color_pair=status_color_pair, attributes=TextAttribute.NORMAL)
        
        # Automatically mark as not needing redraw after drawing
        self.content_changed = False
    
    # UILayer interface implementation
    
    def handle_key_event(self, event: KeyEvent) -> bool:
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
        
        # ESC - cancel batch rename
        if event.key_code == KeyCode.ESCAPE:
            self.exit()
            return True
            
        # Tab - switch between regex and destination input
        elif event.key_code == KeyCode.TAB:
            if self.active_field == 'regex':
                self.switch_field('destination')
            else:
                self.switch_field('regex')
            self.content_changed = True
            return True
            
        # Up arrow - move to regex field (previous field)
        elif event.key_code == KeyCode.UP:
            self.switch_field('regex')
            self.content_changed = True
            return True
            
        # Down arrow - move to destination field (next field)
        elif event.key_code == KeyCode.DOWN:
            self.switch_field('destination')
            self.content_changed = True
            return True
            
        # Page Up - scroll preview up
        elif event.key_code == KeyCode.PAGE_UP:
            if self.scroll > 0:
                self.scroll = max(0, self.scroll - 10)
            self.content_changed = True
            return True
            
        # Page Down - scroll preview down
        elif event.key_code == KeyCode.PAGE_DOWN:
            if self.preview:
                max_scroll = max(0, len(self.preview) - 10)
                self.scroll = min(max_scroll, self.scroll + 10)
            self.content_changed = True
            return True
            
        # Enter - perform batch rename
        elif event.key_code == KeyCode.ENTER:
            regex_text = self.regex_editor.get_text()
            dest_text = self.destination_editor.get_text()
            if regex_text and dest_text:
                # Don't close here - let the caller handle the execution
                return True
            else:
                # Error: missing pattern - but event was handled
                return True
            
        else:
            # Let the active editor handle other KeyEvents
            active_editor = self.get_active_editor()
            
            # Pass the KeyEvent directly to SingleLineTextEdit
            if active_editor.handle_key(event):
                # Text changed, update preview
                self.update_preview()
                self.content_changed = True
                return True
        
        # Event not handled - return False to allow CharEvent generation
        return False
    
    def handle_char_event(self, event: CharEvent) -> bool:
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
        
        # Pass to active text editor
        active_editor = self.get_active_editor()
        if active_editor.handle_key(event):
            # Text changed, update preview
            self.update_preview()
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
        result = BaseListDialog.handle_mouse_event(self, event, self.preview)
        
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
    



class BatchRenameDialogHelpers:
    """Helper functions for batch rename dialog integration"""
    
    @staticmethod
    def get_selected_files_for_rename(current_pane):
        """Get the list of selected files for batch rename
        
        Args:
            current_pane: Current pane data
            
        Returns:
            List of Path objects representing selected files, or None if invalid
        """
        if not current_pane['selected_files']:
            return None
            
        selected_files = []
        for file_path_str in current_pane['selected_files']:
            try:
                file_path = Path(file_path_str)
                if file_path.exists():
                    selected_files.append(file_path)
            except (OSError, ValueError) as e:
                logger.warning(f"Could not process selected file path '{file_path_str}': {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error processing file path: {e}")
                continue
                
        return selected_files if selected_files else None
    
    @staticmethod
    def validate_rename_operation(preview_list):
        """Validate a batch rename operation
        
        Args:
            preview_list: List of preview dictionaries
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not preview_list:
            return False, "No rename preview available"
        
        # Check for conflicts and invalid names
        conflicts = [p for p in preview_list if p['conflict']]
        invalid = [p for p in preview_list if not p['valid']]
        
        if conflicts:
            conflict_names = [p['new'] for p in conflicts]
            return False, f"Name conflicts detected: {', '.join(conflict_names)}"
        
        if invalid:
            invalid_names = [p['new'] for p in invalid]
            return False, f"Invalid names detected: {', '.join(invalid_names)}"
        
        return True, ""
    
    @staticmethod
    def format_rename_results(success_count, errors):
        """Format the results of a batch rename operation
        
        Args:
            success_count: Number of successful renames
            errors: List of error messages
            
        Returns:
            String describing the results
        """
        if errors:
            error_summary = f"Errors: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                error_summary += f" (and {len(errors) - 3} more)"
            return f"Renamed {success_count} files. {error_summary}"
        elif success_count > 0:
            return f"Successfully renamed {success_count} files"
        else:
            return "No files were renamed"