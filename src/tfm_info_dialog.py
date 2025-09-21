#!/usr/bin/env python3
"""
TUI File Manager - Info Dialog Component
Provides scrollable information dialog functionality
"""

import curses
from tfm_colors import get_status_color


class InfoDialog:
    """Scrollable information dialog component"""
    
    def __init__(self, config):
        self.config = config
        
        # Info dialog state
        self.mode = False
        self.title = ""
        self.lines = []
        self.scroll = 0
        
    def show(self, title, info_lines):
        """Show an information dialog with scrollable content
        
        Args:
            title: The title to display at the top of the dialog
            info_lines: List of strings to display in the dialog
        """
        self.mode = True
        self.title = title
        self.lines = info_lines
        self.scroll = 0
        
    def exit(self):
        """Exit info dialog mode"""
        self.mode = False
        self.title = ""
        self.lines = []
        self.scroll = 0
        
    def handle_input(self, key):
        """Handle input while in info dialog mode"""
        if key == 27 or key == ord('q') or key == ord('Q'):  # ESC or Q - close
            self.exit()
            return True
        elif key == curses.KEY_UP:
            # Scroll up
            if self.scroll > 0:
                self.scroll -= 1
            return True
        elif key == curses.KEY_DOWN:
            # Scroll down - calculate max scroll based on current content
            # We'll use a default content height for now, this will be refined in draw()
            content_height = 10  # Default, will be calculated properly in draw()
            max_scroll = max(0, len(self.lines) - content_height)
            if self.scroll < max_scroll:
                self.scroll += 1
            return True
        elif key == curses.KEY_PPAGE:  # Page Up
            self.scroll = max(0, self.scroll - 10)
            return True
        elif key == curses.KEY_NPAGE:  # Page Down
            content_height = 10  # Default, will be calculated properly in draw()
            max_scroll = max(0, len(self.lines) - content_height)
            self.scroll = min(max_scroll, self.scroll + 10)
            return True
        elif key == curses.KEY_HOME:  # Home - go to top
            self.scroll = 0
            return True
        elif key == curses.KEY_END:  # End - go to bottom
            content_height = 10  # Default, will be calculated properly in draw()
            max_scroll = max(0, len(self.lines) - content_height)
            self.scroll = max_scroll
            return True
        return False
        
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
        
        # Draw title
        if self.title and start_y >= 0:
            title_text = f" {self.title} "
            title_x = start_x + (dialog_width - len(title_text)) // 2
            if title_x >= start_x and title_x + len(title_text) <= start_x + dialog_width:
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
        
        # Draw content lines
        visible_lines = self.lines[self.scroll:self.scroll + content_height]
        
        for i, line in enumerate(visible_lines):
            y = content_start_y + i
            if y <= content_end_y and y < height:
                # Truncate line if too long
                display_line = line[:content_width] if len(line) > content_width else line
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
        if help_y < height and len(help_text) <= content_width:
            help_x = start_x + (dialog_width - len(help_text)) // 2
            if help_x >= start_x:
                safe_addstr_func(help_y, help_x, help_text, get_status_color() | curses.A_DIM)


class InfoDialogHelpers:
    """Helper functions for common info dialog use cases"""
    
    @staticmethod
    def show_help_dialog(info_dialog):
        """Show the help dialog with TFM usage information"""
        help_lines = []
        help_lines.append("TFM (TUI File Manager) - Keyboard Shortcuts")
        help_lines.append("")
        help_lines.append("Navigation:")
        help_lines.append("• ↑↓ or j/k: Move cursor up/down")
        help_lines.append("• ←→ or h/l: Switch between panes")
        help_lines.append("• Enter: Enter directory or open file")
        help_lines.append("• Backspace: Go to parent directory")
        help_lines.append("• Home/End: Go to first/last item")
        help_lines.append("• Page Up/Down: Scroll by page")
        help_lines.append("")
        help_lines.append("File Operations:")
        help_lines.append("• Space: Toggle file selection")
        help_lines.append("• Shift+Space: Toggle selection and move up")
        help_lines.append("• Ctrl+A: Toggle all files selection")
        help_lines.append("• Shift+Ctrl+A: Toggle all items selection")
        help_lines.append("• W: Compare selection (select files matching other pane)")
        help_lines.append("• F5: Copy selected files")
        help_lines.append("• F6: Move selected files")
        help_lines.append("• F8/Delete: Delete selected files")
        help_lines.append("• F7: Create new directory")
        help_lines.append("• Shift+F4: Create new file")
        help_lines.append("• F2: Rename file/directory")
        help_lines.append("")
        help_lines.append("View & Search:")
        help_lines.append("• F3: View file content")
        help_lines.append("• F4: Edit file")
        help_lines.append("• /: Search files (isearch)")
        help_lines.append("• Ctrl+F: Filter files by pattern")
        help_lines.append("• Ctrl+S: Advanced search dialog")
        help_lines.append("")
        help_lines.append("Pane Operations:")
        help_lines.append("• Tab: Switch active pane")
        help_lines.append("• Ctrl+U: Swap pane directories")
        help_lines.append("• Ctrl+O: Sync pane directories")
        help_lines.append("• Ctrl+→: Sync other pane to current")
        help_lines.append("• Ctrl+←: Sync current pane to other")
        help_lines.append("• <: Make left pane smaller (adjust boundary left)")
        help_lines.append("• >: Make left pane larger (adjust boundary right)")
        help_lines.append("• -: Reset pane split to 50% | 50%")
        help_lines.append("")
        help_lines.append("Log Pane Controls:")
        help_lines.append("• Ctrl+U: Make log pane smaller")
        help_lines.append("• Ctrl+D: Make log pane larger")
        help_lines.append("• {: Make log pane larger")
        help_lines.append("• }: Make log pane smaller")
        help_lines.append("• Ctrl+K: Scroll log up")
        help_lines.append("• Ctrl+L: Scroll log down")
        help_lines.append("• Shift+Up: Scroll log up (toward older messages)")
        help_lines.append("• Shift+Down: Scroll log down (toward newer messages)")
        help_lines.append("• Shift+Left: Fast scroll up (toward older messages)")
        help_lines.append("• Shift+Right: Fast scroll down (toward newer messages)")
        help_lines.append("")
        help_lines.append("Other:")
        help_lines.append("• F1: Show this help")
        help_lines.append("• F10/Ctrl+Q: Quit")
        help_lines.append("• Ctrl+R: Refresh file list")
        help_lines.append("")
        help_lines.append("Archive Operations:")
        help_lines.append("• Ctrl+A on archive: Create archive from selected files")
        help_lines.append("• Enter on archive: Extract archive contents")
        help_lines.append("• Archive extraction creates directory with archive base name")
        
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