#!/usr/bin/env python3
"""
TUI File Manager - About Dialog Component
Displays TFM logo, version, and GitHub URL with Matrix-style background animation
"""

import random
import time
from ttk import TextAttribute, KeyCode, KeyEvent, CharEvent
from ttk.wide_char_utils import get_display_width

from tfm_ui_layer import UILayer
from tfm_colors import (get_status_color, COLOR_MATRIX_BRIGHT, COLOR_MATRIX_MEDIUM, COLOR_MATRIX_DIM)
from tfm_const import VERSION, GITHUB_URL
from tfm_log_manager import getLogger


class MatrixColumn:
    """Represents a single column of falling Matrix-style characters"""
    
    def __init__(self, x, height):
        """Initialize a Matrix column
        
        Args:
            x: Column x position
            height: Screen height
        """
        self.x = x
        self.height = height
        self.y = random.randint(-height, 0)  # Start above screen
        self.speed = random.uniform(0.3, 1.0)  # Characters per frame
        self.length = random.randint(25, 75)  # Trail length (5x longer: was 5-15, now 25-75)
        
        # Generate fixed characters for each grid position (authentic Matrix effect)
        # Use zenkaku katakana characters for authentic Matrix look
        # Full-width katakana range: U+30A0 to U+30FF
        katakana_chars = [chr(i) for i in range(0x30A0, 0x30FF)]
        self.grid_chars = [random.choice(katakana_chars) for _ in range(height)]
    
    def update(self, dt):
        """Update column position
        
        Args:
            dt: Time delta since last update
        """
        self.y += self.speed
        
        # Reset when column goes off screen
        if self.y - self.length > self.height:
            self.y = random.randint(-self.height // 2, 0)
            self.speed = random.uniform(0.3, 1.0)
            self.length = random.randint(25, 75)  # Trail length (5x longer)
    
    def get_brightness_map(self):
        """Get brightness value and index for each grid position
        
        Returns:
            Dict mapping y_pos to (index, brightness) tuple
        """
        brightness_map = {}
        for i in range(self.length):
            y_pos = int(self.y - i)
            if 0 <= y_pos < self.height:
                # Brightness increases toward the head (bottom)
                # i=0 is the head (brightest), i=length-1 is the tail (dimmest)
                if i == 0:
                    brightness = 1.0  # Only the head gets exactly 1.0
                else:
                    brightness = 1.0 - (i / self.length)
                
                brightness_map[y_pos] = (i, brightness)
        return brightness_map


class AboutDialog(UILayer):
    """About dialog with Matrix-style background animation"""
    
    def __init__(self, config, renderer=None):
        # UILayer is an ABC with no __init__, so we don't call super().__init__()
        self.config = config
        self.renderer = renderer
        self.logger = getLogger("AboutDlg")
        
        # Dialog state
        self.is_active = False
        self.content_changed = True
        
        # Matrix animation state
        self.matrix_columns = []
        self.last_update_time = 0
        self.animation_enabled = True
        self.previous_drawn_positions = set()  # Track positions that were drawn in previous frame
        
    def show(self):
        """Show the about dialog"""
        self.is_active = True
        self.content_changed = True
        self.last_update_time = time.time()
        
        # Initialize Matrix columns based on screen width
        height, width = self.renderer.get_dimensions()
        self.matrix_columns = []
        # Create columns at every other position for zenkaku (full-width) characters
        # Zenkaku katakana characters take 2 columns of screen space
        for x in range(0, width, 2):
            self.matrix_columns.append(MatrixColumn(x, height))
        
        self.logger.info("About dialog opened")
        
    def exit(self):
        """Exit about dialog"""
        self.is_active = False
        self.content_changed = True
        self.matrix_columns = []
        self.logger.info("About dialog closed")
        
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        # Always redraw when active for animation
        return self.is_active or self.content_changed
    
    def _draw_matrix_background(self, height, width):
        """Draw Matrix-style falling characters in background
        
        Args:
            height: Screen height
            width: Screen width
        """
        # Update animation
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update all columns
        for column in self.matrix_columns:
            column.update(dt)
        
        # Track which positions are drawn in this frame
        current_drawn_positions = set()
        
        # Draw all grid characters with brightness based on falling trails
        # In authentic Matrix effect, characters are fixed per grid position,
        # and only brightness changes as trails pass through
        
        for column in self.matrix_columns:
            brightness_map = column.get_brightness_map()
            
            # Draw all grid positions for this column
            for y in range(height):
                if 0 <= column.x < width:
                    char = column.grid_chars[y]
                    
                    # Check if this position is part of a trail
                    if y in brightness_map:
                        i, brightness = brightness_map[y]
                        
                        # Use index-based logic for color selection:
                        # i=0: white (head, 1 char)
                        # i=1 to length-3: green (main trail)
                        # i=length-2 to length-1: dim green (tail, 2 chars)
                        # After trail: invisible (don't draw)
                        
                        if i == 0:
                            # Head - single white character
                            color_pair = COLOR_MATRIX_BRIGHT
                        elif i < column.length - 2:
                            # Main trail - bright green
                            color_pair = COLOR_MATRIX_MEDIUM
                        else:
                            # Tail (last 2 characters) - dim green
                            color_pair = COLOR_MATRIX_DIM
                        
                        try:
                            self.renderer.draw_text(y, column.x, char, 
                                                  color_pair=color_pair, 
                                                  attributes=TextAttribute.NORMAL)
                            current_drawn_positions.add((column.x, y))
                        except Exception:
                            pass  # Ignore drawing errors at screen edges
        
        # Clear positions that were drawn in previous frame but not in current frame
        # This ensures the tail properly disappears
        positions_to_clear = self.previous_drawn_positions - current_drawn_positions
        for x, y in positions_to_clear:
            if 0 <= y < height and 0 <= x < width:
                try:
                    # Draw a space to clear the position
                    self.renderer.draw_text(y, x, ' ', 
                                          color_pair=0,  # Default color
                                          attributes=TextAttribute.NORMAL)
                except Exception:
                    pass
        
        # Update previous positions for next frame
        self.previous_drawn_positions = current_drawn_positions
    
    def draw(self):
        """Draw the about dialog"""
        height, width = self.renderer.get_dimensions()
        
        # Draw Matrix background animation
        if self.animation_enabled:
            self._draw_matrix_background(height, width)
        
        # Calculate dialog dimensions
        dialog_width = min(60, width - 4)
        dialog_height = min(20, height - 4)
        
        # Center the dialog
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw semi-transparent dialog background
        # Use black background to let Matrix show through at edges
        status_color_pair, status_attributes = get_status_color()
        
        # Draw dialog box with border
        border_color_pair, _ = get_status_color()
        border_attributes = TextAttribute.NORMAL
        
        # Top border
        if start_y >= 0:
            top_line = "┌" + "─" * (dialog_width - 2) + "┐"
            self.renderer.draw_text(start_y, start_x, top_line[:dialog_width], 
                                   color_pair=border_color_pair, attributes=border_attributes)
        
        # Content area with solid background
        for y in range(start_y + 1, start_y + dialog_height - 1):
            if y < height and start_x >= 0 and start_x < width:
                # Draw solid background for content area
                columns_to_fill = min(dialog_width - 2, width - start_x - 1)
                self.renderer.draw_hline(y, start_x + 1, ' ', columns_to_fill, 
                                        color_pair=status_color_pair)
                
                # Draw side borders
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
        
        # Draw content
        content_y = start_y + 2
        content_x = start_x + 2
        content_width = dialog_width - 4
        
        # ASCII art logo
        logo = [
            "████████╗███████╗███╗   ███╗",
            "╚══██╔══╝██╔════╝████╗ ████║",
            "   ██║   █████╗  ██╔████╔██║",
            "   ██║   ██╔══╝  ██║╚██╔╝██║",
            "   ██║   ██║     ██║ ╚═╝ ██║",
            "   ╚═╝   ╚═╝     ╚═╝     ╚═╝"
        ]
        
        # Draw logo centered
        for i, line in enumerate(logo):
            y = content_y + i
            if y < start_y + dialog_height - 2:
                line_width = get_display_width(line)
                x = content_x + (content_width - line_width) // 2
                if x >= content_x and x + line_width <= start_x + dialog_width - 2:
                    self.renderer.draw_text(y, x, line, 
                                           color_pair=status_color_pair, 
                                           attributes=TextAttribute.BOLD)
        
        # Draw version and info
        info_y = content_y + len(logo) + 2
        
        info_lines = [
            f"Version {VERSION}",
            "",
            "Terminal File Manager",
            "",
            GITHUB_URL,
            "",
            "Press any key to close"
        ]
        
        for i, line in enumerate(info_lines):
            y = info_y + i
            if y < start_y + dialog_height - 2:
                line_width = get_display_width(line)
                x = content_x + (content_width - line_width) // 2
                if x >= content_x:
                    # Highlight GitHub URL
                    if line == GITHUB_URL:
                        attr = TextAttribute.UNDERLINE
                    else:
                        attr = TextAttribute.NORMAL
                    
                    self.renderer.draw_text(y, x, line, 
                                           color_pair=status_color_pair, 
                                           attributes=attr)
        
        self.content_changed = False
    
    # UILayer interface implementation
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        """Handle a key event (UILayer interface)
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed
        """
        if not event or not isinstance(event, KeyEvent):
            return False
        
        # Any key closes the dialog
        self.exit()
        return True
    
    def handle_char_event(self, event: CharEvent) -> bool:
        """Handle a character event (UILayer interface)
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed
        """
        # Any character closes the dialog
        self.exit()
        return True
    
    def handle_system_event(self, event) -> bool:
        """Handle a system event (UILayer interface)
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if event was handled
        """
        if event.is_resize():
            # Reinitialize Matrix columns for new dimensions
            height, width = self.renderer.get_dimensions()
            self.matrix_columns = []
            # Create columns at every other position for zenkaku (full-width) characters
            for x in range(0, width, 2):
                self.matrix_columns.append(MatrixColumn(x, height))
            self.content_changed = True
            return True
        elif event.is_close():
            self.is_active = False
            return True
        return False
    
    def handle_mouse_event(self, event) -> bool:
        """Handle a mouse event (UILayer interface)
        
        Args:
            event: MouseEvent to handle
        
        Returns:
            True if event was handled
        """
        # Any mouse button down closes the dialog
        from ttk.ttk_mouse_event import MouseEventType
        if event.event_type == MouseEventType.BUTTON_DOWN:
            self.exit()
            return True
        return False
    
    def render(self, renderer) -> None:
        """Render the layer's content (UILayer interface)
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        self.draw()
    
    def is_full_screen(self) -> bool:
        """Query if this layer occupies the full screen (UILayer interface)
        
        Returns:
            True - about dialog covers full screen with animation
        """
        return True
    
    def mark_dirty(self) -> None:
        """Mark this layer as needing a redraw (UILayer interface)"""
        self.content_changed = True
    
    def clear_dirty(self) -> None:
        """Clear the dirty flag after rendering (UILayer interface)"""
        self.content_changed = False
    
    def should_close(self) -> bool:
        """Query if this layer wants to close (UILayer interface)
        
        Returns:
            True if the layer should be closed
        """
        return not self.is_active
    
    def on_activate(self) -> None:
        """Called when this layer becomes the top layer (UILayer interface)"""
        self.content_changed = True
    
    def on_deactivate(self) -> None:
        """Called when this layer is no longer the top layer (UILayer interface)"""
        pass
