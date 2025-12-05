#!/usr/bin/env python3
"""
TUI File Manager - Dialog Backend Interface
Provides abstraction layer for dialog rendering across different UI backends
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple


@dataclass
class DialogDimensions:
    """Dialog dimensions and positioning"""
    start_y: int
    start_x: int
    width: int
    height: int
    content_start_y: int
    content_start_x: int
    content_width: int
    content_height: int


class IDialogBackend(ABC):
    """Interface for dialog rendering backends"""
    
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """Get current screen dimensions
        
        Returns:
            Tuple of (height, width)
        """
        pass
    
    @abstractmethod
    def draw_dialog_frame(self, title: str, width_ratio: float, height_ratio: float,
                         min_width: int, min_height: int) -> DialogDimensions:
        """Draw dialog frame and return dimensions
        
        Args:
            title: Dialog title text
            width_ratio: Dialog width as ratio of screen width
            height_ratio: Dialog height as ratio of screen height
            min_width: Minimum dialog width
            min_height: Minimum dialog height
            
        Returns:
            DialogDimensions object with calculated dimensions
        """
        pass
    
    @abstractmethod
    def draw_text_input(self, y: int, x: int, width: int, prompt: str,
                       text: str, cursor_pos: int, is_active: bool = True):
        """Draw text input field
        
        Args:
            y: Y position
            x: X position
            width: Maximum width
            prompt: Prompt text
            text: Current text
            cursor_pos: Cursor position in text
            is_active: Whether input is active
        """
        pass
    
    @abstractmethod
    def draw_separator(self, y: int, x: int, width: int):
        """Draw horizontal separator line
        
        Args:
            y: Y position
            x: X position
            width: Width of separator
        """
        pass
    
    @abstractmethod
    def draw_text(self, y: int, x: int, text: str, style: str = 'normal'):
        """Draw text at position with style
        
        Args:
            y: Y position
            x: X position
            text: Text to draw
            style: Style name ('normal', 'bold', 'dim', 'error', 'selected')
        """
        pass
    
    @abstractmethod
    def draw_list_item(self, y: int, x: int, width: int, text: str,
                      is_selected: bool, style: str = 'normal'):
        """Draw a list item with selection indicator
        
        Args:
            y: Y position
            x: X position
            width: Maximum width
            text: Item text
            is_selected: Whether item is selected
            style: Style name
        """
        pass
    
    @abstractmethod
    def draw_scrollbar(self, start_y: int, height: int, x: int,
                      total_items: int, visible_items: int, scroll_pos: int):
        """Draw scrollbar indicator
        
        Args:
            start_y: Starting Y position
            height: Height of scrollbar area
            x: X position
            total_items: Total number of items
            visible_items: Number of visible items
            scroll_pos: Current scroll position
        """
        pass
    
    @abstractmethod
    def truncate_text(self, text: str, max_width: int, ellipsis: str = "...") -> str:
        """Truncate text to fit within width
        
        Args:
            text: Text to truncate
            max_width: Maximum display width
            ellipsis: Ellipsis string to append
            
        Returns:
            Truncated text
        """
        pass
    
    @abstractmethod
    def get_text_width(self, text: str) -> int:
        """Get display width of text
        
        Args:
            text: Text to measure
            
        Returns:
            Display width in columns
        """
        pass
    
    @abstractmethod
    def refresh(self):
        """Refresh the display"""
        pass


class DialogState:
    """Base class for dialog state management"""
    
    def __init__(self):
        self.is_active = False
        self.selected = 0
        self.scroll = 0
        self.content_changed = True
    
    def reset(self):
        """Reset dialog state"""
        self.is_active = False
        self.selected = 0
        self.scroll = 0
        self.content_changed = True
    
    def mark_changed(self):
        """Mark content as changed"""
        self.content_changed = True
    
    def mark_unchanged(self):
        """Mark content as unchanged"""
        self.content_changed = False
    
    def needs_redraw(self) -> bool:
        """Check if dialog needs redraw"""
        return self.content_changed
