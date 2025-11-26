#!/usr/bin/env python3
"""
TUI File Manager - Info Dialog Component
Provides scrollable information dialog functionality
"""

import curses
from tfm_base_list_dialog import BaseListDialog
from tfm_colors import get_status_color
from tfm_config import config_manager
from tfm_wide_char_utils import get_display_width, get_safe_functions


class InfoDialog(BaseListDialog):
    """Scrollable information dialog component"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Info dialog specific state
        self.title = ""
        self.lines = []
        self.content_changed = True  # Track if content needs redraw
        
    def show(self, title, info_lines):
        """Show an information dialog with scrollable content
        
        Args:
            title: The title to display at the top of the dialog
            info_lines: List of strings to display in the dialog
        """
        self.is_active = True
        self.title = title
        self.lines = info_lines
        self.scroll = 0
        self.content_changed = True  # Mark content as changed when showing
        
    def exit(self):
        """Exit info dialog mode"""
        super().exit()
        self.title = ""
        self.lines = []
        self.content_changed = True  # Mark content as changed when exiting
        
    def handle_input(self, key):
        """Handle input while in info dialog mode"""
        if key == 27 or key == ord('q') or key == ord('Q'):  # ESC or Q - close
            self.exit()
            return True
        elif key == curses.KEY_UP:
            # Scroll up
            if self.scroll > 0:
                self.scroll -= 1
            # Always mark content as changed for any handled key to ensure continued rendering
            self.content_changed = True
            return True
        elif key == curses.KEY_DOWN:
            # Scroll down - calculate max scroll based on current content
            # We'll use a default content height for now, this will be refined in draw()
            content_height = 10  # Default, will be calculated properly in draw()
            max_scroll = max(0, len(self.lines) - content_height)
            if self.scroll < max_scroll:
                self.scroll += 1
            # Always mark content as changed for any handled key to ensure continued rendering
            self.content_changed = True
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            old_scroll = self.scroll
            self.scroll = max(0, self.scroll - 10)
            # Always mark content as changed for any handled key to ensure continued rendering
            self.content_changed = True
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            content_height = 10  # Default, will be calculated properly in draw()
            max_scroll = max(0, len(self.lines) - content_height)
            old_scroll = self.scroll
            self.scroll = min(max_scroll, self.scroll + 10)
            # Always mark content as changed for any handled key to ensure continued rendering
            self.content_changed = True
            return True
        elif key == curses.KEY_HOME:  # Home - go to top
            if self.scroll != 0:
                self.scroll = 0
            # Always mark content as changed for any handled key to ensure continued rendering
            self.content_changed = True
            return True
        elif key == curses.KEY_END:  # End - go to bottom
            content_height = 10  # Default, will be calculated properly in draw()
            max_scroll = max(0, len(self.lines) - content_height)
            if self.scroll != max_scroll:
                self.scroll = max_scroll
            # Always mark content as changed for any handled key to ensure continued rendering
            self.content_changed = True
            return True
        return False
        
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        return self.content_changed
    
    def draw(self, stdscr, safe_addstr_func):
        """Draw the info dialog overlay"""
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions using configuration
        width_ratio = getattr(self.config, 'INFO_DIALOG_WIDTH_RATIO', 0.8)
        height_ratio = getattr(self.config, 'INFO_DIALOG_HEIGHT_RATIO', 0.8)
        min_width = getattr(self.config, 'INFO_DIALOG_MIN_WIDTH', 20)
        min_height = getattr(self.config, 'INFO_DIALOG_MIN_HEIGHT', 10)
        
        dialog_width = max(min_width, int(width * width_ratio))
        dialog_height = max(min_height, int(height * height_ratio))
        
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
        
        # Draw title using wide character utilities
        if self.title and start_y >= 0:
            title_text = f" {self.title} "
            # Get safe wide character functions
            safe_funcs = get_safe_functions()
            get_width = safe_funcs['get_display_width']
            
            title_width = get_width(title_text)
            title_x = start_x + (dialog_width - title_width) // 2
            if title_x >= start_x and title_x + title_width <= start_x + dialog_width:
                safe_addstr_func(start_y, title_x, title_text, border_color)
        
        # Calculate content area
        content_start_y = start_y + 2
        content_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = content_end_y - content_start_y + 1
        
        # Update scroll bounds based on actual content height
        max_scroll = max(0, len(self.lines) - content_height)
        if self.scroll > max_scroll:
            self.scroll = max_scroll
        
        # Draw content lines using wide character utilities
        visible_lines = self.lines[self.scroll:self.scroll + content_height]
        
        # Get safe wide character functions
        safe_funcs = get_safe_functions()
        get_width = safe_funcs['get_display_width']
        truncate_text = safe_funcs['truncate_to_width']
        
        for i, line in enumerate(visible_lines):
            y = content_start_y + i
            if y <= content_end_y and y < height:
                # Truncate line if too wide using display width
                if get_width(line) > content_width:
                    display_line = truncate_text(line, content_width, "")
                else:
                    display_line = line
                safe_addstr_func(y, content_start_x, display_line, get_status_color())
        
        # Draw scroll indicators
        if len(self.lines) > content_height:
            # Show scroll position
            total_lines = len(self.lines)
            scroll_pos = self.scroll
            
            # Scroll bar on the right side
            scrollbar_x = start_x + dialog_width - 2
            scrollbar_start_y = content_start_y
            scrollbar_height = content_height
            
            # Calculate scroll thumb position
            if total_lines > 0:
                thumb_pos = int((scroll_pos / max(1, total_lines - content_height)) * (scrollbar_height - 1))
                thumb_pos = max(0, min(scrollbar_height - 1, thumb_pos))
                
                for i in range(scrollbar_height):
                    y = scrollbar_start_y + i
                    if y < height:
                        if i == thumb_pos:
                            safe_addstr_func(y, scrollbar_x, "█", border_color)
                        else:
                            safe_addstr_func(y, scrollbar_x, "░", get_status_color() | curses.A_DIM)
        
        # Draw help text at bottom
        help_text = "↑↓:scroll  PgUp/PgDn:page  Home/End:top/bottom  Q/ESC:close"
        help_y = start_y + dialog_height - 2
        if help_y < height:
            help_width = get_width(help_text)
            if help_width <= content_width:
                help_x = start_x + (dialog_width - help_width) // 2
                if help_x >= start_x:
                    safe_addstr_func(help_y, help_x, help_text, get_status_color() | curses.A_DIM)
            else:
                # Truncate help text if too wide
                truncated_help = truncate_text(help_text, content_width, "...")
                help_width = get_width(truncated_help)
                help_x = start_x + (dialog_width - help_width) // 2
                if help_x >= start_x:
                    safe_addstr_func(help_y, help_x, truncated_help, get_status_color() | curses.A_DIM)
        
        # Automatically mark as not needing redraw after drawing
        self.content_changed = False


class InfoDialogHelpers:
    """Helper functions for common info dialog use cases"""
    
    @staticmethod
    def _format_key_bindings(action, width=12):
        """Get formatted key bindings for an action with consistent width"""
        keys = config_manager.get_key_for_action(action)
        if not keys:
            key_str = "Not configured"
        else:
            # Replace space character with "(space)" for better readability
            formatted_keys = []
            for key in keys:
                if key == ' ':
                    formatted_keys.append('(space)')
                else:
                    formatted_keys.append(key)
            key_str = "/".join(formatted_keys)
        
        # Pad to consistent width for column alignment
        return key_str.ljust(width)
    
    @staticmethod
    def show_help_dialog(info_dialog):
        """Show the help dialog with TFM usage information"""
        help_lines = []
        help_lines.append("TFM (TUI File Manager) - Keyboard Shortcuts")
        help_lines.append("")
        
        # Navigation (non-configurable system keys)
        help_lines.append("Navigation:")
        help_lines.append(f"• {'↑↓ or j/k'.ljust(12)} Move cursor up/down")
        help_lines.append(f"• {'←→ or h/l'.ljust(12)} Switch between panes")
        help_lines.append(f"• {'Enter'.ljust(12)} Enter directory or open file")
        help_lines.append(f"• {'Backspace'.ljust(12)} Go to parent directory")
        help_lines.append(f"• {'Home/End'.ljust(12)} Go to first/last item")
        help_lines.append(f"• {'Page Up/Down'.ljust(12)} Scroll by page")
        help_lines.append(f"• {'Tab'.ljust(12)} Switch active pane")
        help_lines.append("")
        
        # File Operations (configurable)
        help_lines.append("File Operations:")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('select_file')} Toggle file selection")

        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('select_all_files')} Toggle all files selection")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('select_all_items')} Toggle all items selection")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('compare_selection')} Compare selection (select files/directories matching other pane)")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('copy_files')} Copy selected files")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('move_files')} Move selected files")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('delete_files')} Delete selected files")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('create_directory')} Create new directory")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('create_file')} Create new file")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('rename_file')} Rename file/directory")
        help_lines.append("")
        
        # View & Search (configurable)
        help_lines.append("View & Search:")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('view_file')} View file content")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('edit_file')} Edit file")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('search')} Search files (isearch)")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('filter')} Filter files by pattern")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('clear_filter')} Clear file filter")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('search_dialog')} Filename search dialog")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('jump_dialog')} Jump to directory dialog")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('search_content')} Content search dialog")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('file_details')} Show file details")
        help_lines.append("")
        
        # Pane Operations (configurable)
        help_lines.append("Pane Operations:")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('sync_current_to_other')} Sync current pane directory to other pane")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('sync_other_to_current')} Sync other pane directory to current pane")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('adjust_pane_left')} Make left pane smaller (adjust boundary left)")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('adjust_pane_right')} Make left pane larger (adjust boundary right)")
        help_lines.append(f"• {'-'.ljust(12)} Reset pane split to 50% | 50%")
        help_lines.append("")
        
        # Log Pane Controls (configurable)
        help_lines.append("Log Pane Controls:")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('adjust_log_up')} Make log pane larger")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('adjust_log_down')} Make log pane smaller")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('reset_log_height')} Reset log pane height to default")
        help_lines.append(f"• {'Shift+Up'.ljust(12)} Scroll log up (toward older messages)")
        help_lines.append(f"• {'Shift+Down'.ljust(12)} Scroll log down (toward newer messages)")
        help_lines.append(f"• {'Shift+Left'.ljust(12)} Fast scroll up (toward older messages)")
        help_lines.append(f"• {'Shift+Right'.ljust(12)} Fast scroll down (toward newer messages)")
        help_lines.append("")
        
        # Sorting (configurable)
        help_lines.append("Sorting:")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('sort_menu')} Show sort options menu")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('quick_sort_name')} Quick sort by filename")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('quick_sort_ext')} Quick sort by file extension")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('quick_sort_size')} Quick sort by file size")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('quick_sort_date')} Quick sort by modification date")
        help_lines.append("")
        
        # Other Operations (configurable)
        help_lines.append("Other Operations:")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('help')} Show this help")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('quit')} Quit TFM")
        help_lines.append(f"• {'Ctrl+R'.ljust(12)} Refresh file list")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('toggle_hidden')} Toggle visibility of hidden files")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('toggle_color_scheme')} Switch color schemes")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('favorites')} Show favorite directories")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('programs')} Show external programs menu")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('subshell')} Enter subshell (command line) mode")
        help_lines.append("")
        
        # Remote Log Monitoring
        help_lines.append("Remote Log Monitoring:")
        help_lines.append(f"• {'--remote-log-port'.ljust(12)} Start TFM with remote log monitoring")
        help_lines.append(f"• {''.ljust(12)} Example: python tfm.py --remote-log-port 8888")
        help_lines.append(f"• {''.ljust(12)} Connect with: python tools/tfm_log_client.py localhost 8888")
        help_lines.append(f"• {''.ljust(12)} Monitor logs from other terminals or remote machines")
        help_lines.append("")
        
        # Archive Operations (configurable)
        help_lines.append("Archive Operations:")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('create_archive')} Create archive from selected files")
        help_lines.append(f"• {InfoDialogHelpers._format_key_bindings('extract_archive')} Extract selected archive")
        help_lines.append(f"• {''.ljust(12)} Archive extraction creates directory with archive base name")
        
        info_dialog.show("TFM Help", help_lines)
    
    @staticmethod
    def show_file_details(info_dialog, files_to_show, current_pane):
        """Show detailed information about selected files"""
        details_lines = []
        
        for file_path in files_to_show:
            try:
                stat_info = file_path.stat()
                
                # Basic info
                details_lines.append(f"Name: {file_path.name}")
                details_lines.append(f"Path: {file_path}")
                
                # Type
                if file_path.is_dir():
                    details_lines.append("Type: Directory")
                elif file_path.is_file():
                    details_lines.append("Type: File")
                elif file_path.is_symlink():
                    details_lines.append("Type: Symbolic Link")
                else:
                    details_lines.append("Type: Other")
                
                # Size
                if file_path.is_file():
                    size = stat_info.st_size
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
                    details_lines.append(f"Size: {size_str}")
                
                # Permissions
                mode = stat_info.st_mode
                perms = []
                perms.append('r' if mode & 0o400 else '-')
                perms.append('w' if mode & 0o200 else '-')
                perms.append('x' if mode & 0o100 else '-')
                perms.append('r' if mode & 0o040 else '-')
                perms.append('w' if mode & 0o020 else '-')
                perms.append('x' if mode & 0o010 else '-')
                perms.append('r' if mode & 0o004 else '-')
                perms.append('w' if mode & 0o002 else '-')
                perms.append('x' if mode & 0o001 else '-')
                details_lines.append(f"Permissions: {''.join(perms)} ({oct(mode)[-3:]})")
                
                # Timestamps
                from datetime import datetime
                mtime = datetime.fromtimestamp(stat_info.st_mtime)
                details_lines.append(f"Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if len(files_to_show) > 1:
                    details_lines.append("")  # Separator between files
                    
            except (OSError, IOError) as e:
                details_lines.append(f"Error reading {file_path}: {e}")
                if len(files_to_show) > 1:
                    details_lines.append("")
        
        # Set title based on number of files
        if len(files_to_show) == 1:
            title = f"Details: {files_to_show[0].name}"
        else:
            title = f"Details: {len(files_to_show)} items"
        
        info_dialog.show(title, details_lines)
    
    @staticmethod
    def show_color_scheme_info(info_dialog):
        """Show information about the current color scheme"""
        info_lines = []
        info_lines.append("Color Scheme Information")
        info_lines.append("")
        info_lines.append("TFM supports different color schemes:")
        info_lines.append("• dark - Dark theme with bright text")
        info_lines.append("• light - Light theme with dark text")
        info_lines.append("• blue - Blue-based color scheme")
        info_lines.append("• green - Green-based color scheme")
        info_lines.append("")
        info_lines.append("Color scheme can be configured in:")
        info_lines.append("~/.tfm/config.py")
        info_lines.append("")
        info_lines.append("Example configuration:")
        info_lines.append("COLOR_SCHEME = 'dark'")
        
        info_dialog.show("Color Scheme Info", info_lines)