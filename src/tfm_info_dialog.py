#!/usr/bin/env python3
"""
TUI File Manager - Info Dialog Component
Provides scrollable information dialog functionality
"""

from ttk import TextAttribute, KeyCode, KeyEvent, CharEvent
from tfm_base_list_dialog import BaseListDialog
from tfm_ui_layer import UILayer
from tfm_colors import get_status_color
from tfm_config import config_manager
from tfm_wide_char_utils import get_display_width, get_safe_functions
from tfm_input_compat import ensure_input_event
from tfm_scrollbar import draw_scrollbar


class InfoDialog(UILayer, BaseListDialog):
    """Scrollable information dialog component"""
    
    def __init__(self, config, renderer=None):
        super().__init__(config, renderer)
        
        # Info dialog specific state
        self.title = ""
        self.lines = []
        self.content_changed = True  # Track if content needs redraw
        self.cached_content_height = 10  # Cached content height from last draw
        
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
        
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        return self.content_changed
    
    def draw(self):
        """Draw the info dialog overlay"""
        height, width = self.renderer.get_dimensions()
        
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
        # Use draw_hline() to properly clear wide characters underneath
        status_color_pair, status_attributes = get_status_color()
        
        for y in range(start_y, start_y + dialog_height):
            if y < height and start_x >= 0 and start_x < width:
                columns_to_fill = min(dialog_width, width - start_x)
                self.renderer.draw_hline(y, start_x, ' ', columns_to_fill, color_pair=status_color_pair)
        
        # Draw border
        border_color_pair, _ = get_status_color()
        border_attributes = TextAttribute.BOLD
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            self.renderer.draw_text(start_y, start_x, top_line[:dialog_width], 
                                   color_pair=border_color_pair, attributes=border_attributes)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height:
                self.renderer.draw_text(y, start_x, "│", 
                                       color_pair=border_color_pair, attributes=border_attributes)
                if start_x + dialog_width - 1 < width:
                    self.renderer.draw_text(y, start_x + dialog_width - 1, "│", 
                                           color_pair=border_color_pair, attributes=border_attributes)
        
        # Bottom border
        if start_y + dialog_height - 1 < height:
            bottom_line = "└" + "─" * (dialog_width - 2) + "┘"
            self.renderer.draw_text(start_y + dialog_height - 1, start_x, bottom_line[:dialog_width], 
                                   color_pair=border_color_pair, attributes=border_attributes)
        
        # Draw title using wide character utilities
        if self.title and start_y >= 0:
            title_text = f" {self.title} "
            # Get safe wide character functions
            safe_funcs = get_safe_functions()
            get_width = safe_funcs['get_display_width']
            
            title_width = get_width(title_text)
            title_x = start_x + (dialog_width - title_width) // 2
            if title_x >= start_x and title_x + title_width <= start_x + dialog_width:
                self.renderer.draw_text(start_y, title_x, title_text, 
                                       color_pair=border_color_pair, attributes=border_attributes)
        
        # Calculate content area
        content_start_y = start_y + 2
        content_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = content_end_y - content_start_y + 1
        
        # Cache content height for scroll calculations in handle_input
        self.cached_content_height = content_height
        
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
                self.renderer.draw_text(y, content_start_x, display_line, color_pair=status_color_pair)
        
        # Draw scroll indicators
        if len(self.lines) > content_height:
            # Show scroll position
            total_lines = len(self.lines)
            scroll_pos = self.scroll
            
            # Scroll bar on the right side using unified implementation
            scrollbar_x = start_x + dialog_width - 2
            draw_scrollbar(self.renderer, content_start_y, scrollbar_x, content_height,
                         total_lines, scroll_pos)
        
        # Draw help text at bottom
        help_text = "↑↓:scroll  PgUp/PgDn:page  Home/End:top/bottom  Q/ESC:close"
        help_y = start_y + dialog_height - 2
        if help_y < height:
            help_width = get_width(help_text)
            if help_width <= content_width:
                help_x = start_x + (dialog_width - help_width) // 2
                if help_x >= start_x:
                    # Note: TTK doesn't have A_DIM, using NORMAL instead
                    self.renderer.draw_text(help_y, help_x, help_text, 
                                           color_pair=status_color_pair, attributes=TextAttribute.NORMAL)
            else:
                # Truncate help text if too wide
                truncated_help = truncate_text(help_text, content_width, "…")
                help_width = get_width(truncated_help)
                help_x = start_x + (dialog_width - help_width) // 2
                if help_x >= start_x:
                    # Note: TTK doesn't have A_DIM, using NORMAL instead
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
        
        # ESC or Q - close
        if event.key_code == KeyCode.ESCAPE or (event.char and event.char.lower() == 'q'):
            self.exit()
            return True
        # Up arrow - scroll up
        elif event.key_code == KeyCode.UP:
            if self.scroll > 0:
                self.scroll -= 1
            self.content_changed = True
            return True
        # Down arrow - scroll down
        elif event.key_code == KeyCode.DOWN:
            max_scroll = max(0, len(self.lines) - self.cached_content_height)
            if self.scroll < max_scroll:
                self.scroll += 1
            self.content_changed = True
            return True
        # Page Up
        elif event.key_code == KeyCode.PAGE_UP:
            self.scroll = max(0, self.scroll - 10)
            self.content_changed = True
            return True
        # Page Down
        elif event.key_code == KeyCode.PAGE_DOWN:
            max_scroll = max(0, len(self.lines) - self.cached_content_height)
            self.scroll = min(max_scroll, self.scroll + 10)
            self.content_changed = True
            return True
        # Home - go to top
        elif event.key_code == KeyCode.HOME:
            if self.scroll != 0:
                self.scroll = 0
            self.content_changed = True
            return True
        # End - go to bottom
        elif event.key_code == KeyCode.END:
            max_scroll = max(0, len(self.lines) - self.cached_content_height)
            if self.scroll != max_scroll:
                self.scroll = max_scroll
            self.content_changed = True
            return True
        
        return False
    
    def handle_char_event(self, event: CharEvent) -> bool:
        """
        Handle a character event (UILayer interface).
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        # InfoDialog doesn't handle character events (no text input)
        return False
    
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
                # Use polymorphic metadata method - works for all storage types
                InfoDialogHelpers._add_file_details(details_lines, file_path)
                
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
    def _add_file_details(details_lines, file_path):
        """Add file details using polymorphic metadata method - works for all storage types"""
        # Common fields first
        details_lines.append(f"Name: {file_path.name}")
        details_lines.append(f"Path: {file_path}")
        
        # Get storage-specific metadata using polymorphic method
        try:
            metadata = file_path.get_extended_metadata()
            
            # Display storage-specific details
            if 'details' in metadata:
                for label, value in metadata['details']:
                    details_lines.append(f"{label}: {value}")
        except Exception as e:
            details_lines.append(f"(Error retrieving metadata: {e})")
    

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