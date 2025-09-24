#!/usr/bin/env python3
"""
TUI File Manager - Batch Rename Dialog Component
Provides batch file renaming functionality with regex patterns
"""

import curses
import re
from pathlib import Path
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_const import KEY_ENTER_1, KEY_ENTER_2, KEY_TAB
from tfm_colors import get_status_color, COLOR_ERROR


class BatchRenameDialog:
    """Batch rename dialog component for renaming multiple files with regex patterns"""
    
    def __init__(self, config):
        self.config = config
        
        # Batch rename dialog state
        self.mode = False
        self.regex_editor = SingleLineTextEdit()
        self.destination_editor = SingleLineTextEdit()
        self.active_field = 'regex'  # 'regex' or 'destination'
        self.files = []  # List of selected files to rename
        self.preview = []  # List of preview results
        self.scroll = 0  # Scroll offset for preview list
        self.content_changed = True  # Track if content needs redraw
        
    def show(self, selected_files):
        """Show the batch rename dialog for multiple selected files
        
        Args:
            selected_files: List of Path objects representing files to rename
        """
        if not selected_files:
            return False
            
        self.mode = True
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
        self.mode = False
        self.content_changed = True  # Mark content as changed when exiting
        self.files = []
        self.regex_editor.clear()
        self.destination_editor.clear()
        self.active_field = 'regex'
        self.preview = []
        self.scroll = 0
        
    def get_active_editor(self):
        """Get the currently active text editor"""
        return self.regex_editor if self.active_field == 'regex' else self.destination_editor
    
    def switch_field(self, field):
        """Switch to the specified field"""
        if field in ['regex', 'destination'] and field != self.active_field:
            self.active_field = field
            return True
        return False
        
    def handle_input(self, key):
        """Handle input while in batch rename mode"""
        if key == 27:  # ESC - cancel batch rename
            return ('cancel', None)
            
        elif key == KEY_TAB:  # Tab - switch between regex and destination input
            if self.active_field == 'regex':
                self.switch_field('destination')
            else:
                self.switch_field('regex')
            self.content_changed = True  # Mark content as changed when switching fields
            return ('field_switch', None)
            
        elif key == curses.KEY_UP:
            # Up arrow - move to regex field (previous field)
            if self.switch_field('regex'):
                self.content_changed = True  # Mark content as changed when switching fields
                return ('field_switch', None)
            return True
            
        elif key == curses.KEY_DOWN:
            # Down arrow - move to destination field (next field)
            if self.switch_field('destination'):
                self.content_changed = True  # Mark content as changed when switching fields
                return ('field_switch', None)
            return True
            
        elif key == curses.KEY_PPAGE:  # Page Up - scroll preview up
            if self.scroll > 0:
                self.scroll = max(0, self.scroll - 10)
                self.content_changed = True  # Mark content as changed when scrolling
                return ('scroll', None)
            return True
            
        elif key == curses.KEY_NPAGE:  # Page Down - scroll preview down
            if self.preview:
                max_scroll = max(0, len(self.preview) - 10)
                self.scroll = min(max_scroll, self.scroll + 10)
                self.content_changed = True  # Mark content as changed when scrolling
                return ('scroll', None)
            return True
            
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Enter - perform batch rename
            regex_text = self.regex_editor.get_text()
            dest_text = self.destination_editor.get_text()
            if regex_text and dest_text:
                return ('execute', None)
            else:
                return ('error', "Please enter both regex pattern and destination pattern")
            
        else:
            # Let the active editor handle other keys
            active_editor = self.get_active_editor()
            if active_editor.handle_key(key):
                # Text changed, update preview
                self.content_changed = True  # Mark content as changed when text changes
                return ('text_changed', None)
        
        # In batch rename mode, capture most other keys to prevent unintended actions
        return True
        
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
        
    def draw(self, stdscr, safe_addstr_func):
        """Draw the batch rename dialog overlay"""
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(80, int(width * 0.9))
        dialog_height = max(25, int(height * 0.9))
        
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
        title_text = f" Batch Rename ({len(self.files)} files) "
        title_x = start_x + (dialog_width - len(title_text)) // 2
        if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
            safe_addstr_func(start_y, title_x, title_text, border_color)
        
        # Content area
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Draw regex input
        regex_y = start_y + 2
        regex_label = "Regex Pattern: "
        
        if regex_y < height:
            # Draw regex input field using SingleLineTextEdit
            self.regex_editor.draw(
                stdscr, regex_y, content_start_x, content_width,
                regex_label,
                is_active=(self.active_field == 'regex')
            )
        
        # Draw destination input
        dest_y = start_y + 3
        dest_label = "Destination:   "
        
        if dest_y < height:
            # Draw destination input field using SingleLineTextEdit
            self.destination_editor.draw(
                stdscr, dest_y, content_start_x, content_width,
                dest_label,
                is_active=(self.active_field == 'destination')
            )
        
        # Draw navigation help
        nav_help_y = start_y + 4
        if nav_help_y < height:
            nav_help_text = "Navigation: ↑/↓=Switch fields, Tab=Alt switch, PgUp/PgDn=Scroll preview"
            safe_addstr_func(nav_help_y, content_start_x, nav_help_text[:content_width], get_status_color() | curses.A_DIM)
        
        # Draw help for macros
        help_y = start_y + 5
        if help_y < height:
            help_text = "Macros: \\0=full name, \\1-\\9=regex groups, \\d=index"
            safe_addstr_func(help_y, content_start_x, help_text[:content_width], get_status_color() | curses.A_DIM)
        
        # Draw separator line
        sep_y = start_y + 6
        if sep_y < height:
            sep_line = "├" + "─" * (dialog_width - 2) + "┤"
            safe_addstr_func(sep_y, start_x, sep_line[:dialog_width], border_color)
        
        # Draw preview header
        preview_header_y = start_y + 7
        if preview_header_y < height:
            header_text = "Preview:"
            safe_addstr_func(preview_header_y, content_start_x, header_text, get_status_color() | curses.A_BOLD)
        
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
                        status_color = get_status_color() | curses.A_DIM
                    elif conflict:
                        status = "CONFLICT!"
                        status_color = curses.color_pair(COLOR_ERROR) | curses.A_BOLD
                    elif not valid:
                        status = "INVALID!"
                        status_color = curses.color_pair(COLOR_ERROR) | curses.A_BOLD
                    else:
                        status = "OK"
                        status_color = get_status_color()
                    
                    # Create preview line
                    max_name_width = (content_width - 20) // 2
                    original_display = original[:max_name_width] if len(original) > max_name_width else original
                    new_display = new[:max_name_width] if len(new) > max_name_width else new
                    
                    preview_line = f"{original_display:<{max_name_width}} → {new_display:<{max_name_width}} [{status}]"
                    preview_line = preview_line[:content_width]
                    
                    safe_addstr_func(y, content_start_x, preview_line, status_color)
        else:
            # No preview available
            no_preview_y = preview_start_y + 2
            if no_preview_y < height:
                no_preview_text = "Enter regex pattern and destination to see preview"
                safe_addstr_func(no_preview_y, content_start_x, no_preview_text, get_status_color() | curses.A_DIM)
        
        # Draw help text
        help_y = start_y + dialog_height - 2
        if help_y < height:
            help_text = "Tab: Switch input | ←→: Move cursor | Home/End: Start/End | Enter: Rename | ESC: Cancel"
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                safe_addstr_func(help_y, help_x, help_text, get_status_color() | curses.A_DIM)


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
            except:
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