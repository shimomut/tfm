#!/usr/bin/env python3
"""
TUI File Manager - Curses Dialog Backend Implementation
Implements dialog rendering using curses library
"""

import curses
from typing import Tuple
from tfm_dialog_backend import IDialogBackend, DialogDimensions
from tfm_colors import get_status_color, COLOR_ERROR
from tfm_wide_char_utils import get_display_width, get_safe_functions


class CursesDialogBackend(IDialogBackend):
    """Curses implementation of dialog backend"""
    
    def __init__(self, stdscr, safe_addstr_func):
        """Initialize curses dialog backend
        
        Args:
            stdscr: Curses screen object
            safe_addstr_func: Safe string drawing function
        """
        self.stdscr = stdscr
        self.safe_addstr = safe_addstr_func
        self.safe_funcs = get_safe_functions()
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get current screen dimensions"""
        return self.stdscr.getmaxyx()
    
    def draw_dialog_frame(self, title: str, width_ratio: float, height_ratio: float,
                         min_width: int, min_height: int) -> DialogDimensions:
        """Draw dialog frame and return dimensions"""
        height, width = self.get_screen_size()
        
        # Calculate dialog dimensions safely
        desired_width = int(width * width_ratio)
        desired_height = int(height * height_ratio)
        
        # Apply minimum constraints, but never exceed terminal size
        dialog_width = max(min_width, desired_width)
        dialog_width = min(dialog_width, width)
        
        dialog_height = max(min_height, desired_height)
        dialog_height = min(dialog_height, height)
        
        # Calculate safe centering
        start_y = max(0, (height - dialog_height) // 2)
        start_x = max(0, (width - dialog_width) // 2)
        
        # Draw dialog background using hline for wide character safety
        for y in range(start_y, start_y + dialog_height):
            if y < height and y >= 0 and start_x >= 0 and start_x < width:
                columns_to_fill = min(dialog_width, width - start_x)
                try:
                    self.stdscr.hline(y, start_x, ' ', columns_to_fill, get_status_color())
                except curses.error:
                    try:
                        bg_line = " " * columns_to_fill
                        self.safe_addstr(y, start_x, bg_line, get_status_color())
                    except curses.error:
                        pass
        
        # Draw border
        border_color = get_status_color() | curses.A_BOLD
        
        # Top border
        if start_y >= 0 and start_y < height:
            top_line = "┌" + "─" * max(0, dialog_width - 2) + "┐"
            if start_x + len(top_line) > width:
                top_line = top_line[:width - start_x]
            if top_line:
                self.safe_addstr(start_y, start_x, top_line, border_color)
        
        # Side borders
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height and y >= 0:
                if start_x >= 0 and start_x < width:
                    self.safe_addstr(y, start_x, "│", border_color)
                right_x = start_x + dialog_width - 1
                if right_x >= 0 and right_x < width:
                    self.safe_addstr(y, right_x, "│", border_color)
        
        # Bottom border
        bottom_y = start_y + dialog_height - 1
        if bottom_y >= 0 and bottom_y < height:
            bottom_line = "└" + "─" * max(0, dialog_width - 2) + "┘"
            if start_x + len(bottom_line) > width:
                bottom_line = bottom_line[:width - start_x]
            if bottom_line:
                self.safe_addstr(bottom_y, start_x, bottom_line, border_color)
        
        # Draw title
        if title and start_y >= 0 and start_y < height:
            title_text = f" {title} "
            title_width = self.get_text_width(title_text)
            
            # Truncate title if too wide
            if title_width > dialog_width:
                title_text = self.truncate_text(title_text, dialog_width - 2, "...")
                title_width = self.get_text_width(title_text)
            
            title_x = start_x + (dialog_width - title_width) // 2
            if title_x >= 0 and title_x < width and title_x + title_width <= width:
                self.safe_addstr(start_y, title_x, title_text, border_color)
        
        # Calculate content area
        content_start_y = start_y + 2
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        content_height = dialog_height - 4
        
        return DialogDimensions(
            start_y=start_y,
            start_x=start_x,
            width=dialog_width,
            height=dialog_height,
            content_start_y=content_start_y,
            content_start_x=content_start_x,
            content_width=content_width,
            content_height=content_height
        )
    
    def draw_text_input(self, y: int, x: int, width: int, prompt: str,
                       text: str, cursor_pos: int, is_active: bool = True):
        """Draw text input field"""
        height, screen_width = self.get_screen_size()
        if y >= height:
            return
        
        # This is a simplified version - actual implementation would use SingleLineTextEdit
        # For now, just draw the prompt and text
        prompt_width = self.get_text_width(prompt)
        available_width = width - prompt_width
        
        # Draw prompt
        self.safe_addstr(y, x, prompt, get_status_color())
        
        # Draw text (truncated if needed)
        if available_width > 0:
            display_text = self.truncate_text(text, available_width, "")
            text_x = x + prompt_width
            if text_x < screen_width:
                self.safe_addstr(y, text_x, display_text, get_status_color())
    
    def draw_separator(self, y: int, x: int, width: int):
        """Draw horizontal separator line"""
        height, screen_width = self.get_screen_size()
        if y >= height:
            return
        
        border_color = get_status_color() | curses.A_BOLD
        sep_line = "├" + "─" * (width - 2) + "┤"
        self.safe_addstr(y, x, sep_line[:width], border_color)
    
    def draw_text(self, y: int, x: int, text: str, style: str = 'normal'):
        """Draw text at position with style"""
        height, width = self.get_screen_size()
        if y >= height or x >= width:
            return
        
        # Map style to curses attributes
        style_map = {
            'normal': get_status_color(),
            'bold': get_status_color() | curses.A_BOLD,
            'dim': get_status_color() | curses.A_DIM,
            'error': curses.color_pair(COLOR_ERROR) | curses.A_BOLD,
            'selected': get_status_color() | curses.A_BOLD | curses.A_STANDOUT
        }
        
        color = style_map.get(style, get_status_color())
        
        # Truncate if needed
        max_width = width - x
        if self.get_text_width(text) > max_width:
            text = self.truncate_text(text, max_width, "")
        
        self.safe_addstr(y, x, text, color)
    
    def draw_list_item(self, y: int, x: int, width: int, text: str,
                      is_selected: bool, style: str = 'normal'):
        """Draw a list item with selection indicator"""
        height, screen_width = self.get_screen_size()
        if y >= height or x >= screen_width:
            return
        
        # Truncate text if needed (account for selection indicator)
        available_width = width - 2
        if self.get_text_width(text) > available_width:
            text = self.truncate_text(text, available_width, "...")
        
        # Add selection indicator
        if is_selected:
            display_text = f"► {text}"
            color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
        else:
            display_text = f"  {text}"
            color = get_status_color()
        
        # Apply additional style
        if style == 'error':
            color = curses.color_pair(COLOR_ERROR) | curses.A_BOLD
        
        # Ensure text fits
        if self.get_text_width(display_text) > width:
            display_text = self.truncate_text(display_text, width, "")
        
        self.safe_addstr(y, x, display_text, color)
    
    def draw_scrollbar(self, start_y: int, height: int, x: int,
                      total_items: int, visible_items: int, scroll_pos: int):
        """Draw scrollbar indicator"""
        screen_height, screen_width = self.get_screen_size()
        if x >= screen_width:
            return
        
        if total_items <= visible_items:
            return  # No scrollbar needed
        
        # Calculate thumb position
        max_scroll = max(1, total_items - visible_items)
        thumb_pos = int((scroll_pos / max_scroll) * (height - 1))
        thumb_pos = max(0, min(height - 1, thumb_pos))
        
        border_color = get_status_color() | curses.A_BOLD
        for i in range(height):
            y = start_y + i
            if y < screen_height:
                if i == thumb_pos:
                    self.safe_addstr(y, x, "█", border_color)
                else:
                    self.safe_addstr(y, x, "░", get_status_color() | curses.A_DIM)
    
    def truncate_text(self, text: str, max_width: int, ellipsis: str = "...") -> str:
        """Truncate text to fit within width"""
        truncate_func = self.safe_funcs['truncate_to_width']
        return truncate_func(text, max_width, ellipsis)
    
    def get_text_width(self, text: str) -> int:
        """Get display width of text"""
        get_width_func = self.safe_funcs['get_display_width']
        return get_width_func(text)
    
    def refresh(self):
        """Refresh the display"""
        try:
            self.stdscr.refresh()
        except curses.error:
            pass
