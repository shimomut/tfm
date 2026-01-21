#!/usr/bin/env python3
"""
Candidate List Overlay Component for TFM (Terminal File Manager)

This module provides a CandidateListOverlay class that displays completion
candidates in an overlay UI positioned above or below a text edit field.
The overlay automatically positions itself based on available screen space
and aligns horizontally with the completion start position.
"""

from typing import List, Optional
from ttk import TextAttribute
from ttk.wide_char_utils import get_display_width, truncate_to_width, get_safe_functions
from tfm_colors import get_status_color
from tfm_log_manager import getLogger
from tfm_scrollbar import draw_scrollbar


class CandidateListOverlay:
    """Overlay UI component for displaying completion candidates"""
    
    def __init__(self, renderer):
        """
        Initialize the candidate list overlay.
        
        Args:
            renderer: TTK Renderer instance for drawing
        """
        self.renderer = renderer
        self.logger = getLogger("CandidateList")
        
        # Candidate list state
        self.candidates = []
        self.is_visible = False
        
        # Position information
        self.text_edit_y = 0  # Y coordinate of the text edit field
        self.text_edit_x = 0  # X coordinate of the text edit field
        self.completion_start_x = 0  # X coordinate where completion starts
        self.show_above = False  # True to show above text edit, False for below
        
        # Display configuration
        self.max_visible_candidates = 10  # Maximum candidates to display
        self.border_char = "│"  # Vertical border character
        self.horizontal_border_char = "─"  # Horizontal border character
        self.corner_chars = {
            "top_left": "┌",
            "top_right": "┐",
            "bottom_left": "└",
            "bottom_right": "┘"
        }
        
        # Keyboard navigation state
        self.focused_index = None  # Index of focused candidate (None if no focus)
        self.scroll_offset = 0  # First visible candidate index
    
    def set_candidates(self, candidates: List[str], text_edit_y: int, 
                      text_edit_x: int, completion_start_x: int, show_above: bool):
        """
        Update the candidate list and position.
        
        Args:
            candidates: List of candidate strings to display
            text_edit_y: Y coordinate of the text edit field
            text_edit_x: X coordinate of the text edit field
            completion_start_x: X coordinate where completion starts (for alignment)
            show_above: True to show above text edit, False for below
        """
        self.candidates = candidates
        self.text_edit_y = text_edit_y
        self.text_edit_x = text_edit_x
        self.completion_start_x = completion_start_x
        self.show_above = show_above
    
    def show(self):
        """Make the candidate list visible"""
        self.is_visible = True
    
    def hide(self):
        """Hide the candidate list"""
        self.is_visible = False
    
    def draw(self):
        """
        Draw the candidate list overlay.
        
        Rendering:
        1. Calculate overlay position (above or below text edit)
        2. Draw border/background
        3. Draw each candidate on a separate line
        4. Truncate candidates that exceed available width
        5. Show indicator if more candidates exist than can be displayed
        6. Draw scrollbar if candidates exceed visible area
        """
        if not self.is_visible or not self.candidates:
            return
        
        # Get screen dimensions
        height, width = self.renderer.get_dimensions()
        
        # Get safe wide character functions
        safe_funcs = get_safe_functions()
        get_width = safe_funcs['get_display_width']
        truncate_text = safe_funcs['truncate_to_width']
        
        # Calculate number of candidates to display
        num_candidates = min(len(self.candidates), self.max_visible_candidates)
        
        # Calculate overlay dimensions
        # Height: candidates + top border + bottom border
        overlay_height = num_candidates + 2
        
        # Width: longest candidate + borders + padding
        max_candidate_width = max(get_width(c) for c in self.candidates[:num_candidates])
        # Add space for borders (2 chars) and padding (2 chars)
        overlay_width = max_candidate_width + 4
        
        # Ensure overlay fits on screen
        overlay_width = min(overlay_width, width - self.completion_start_x)
        
        # Calculate overlay Y position
        if self.show_above:
            # Position above text edit field
            overlay_y = self.text_edit_y - overlay_height
            # Ensure it doesn't go off top of screen
            if overlay_y < 0:
                overlay_y = 0
        else:
            # Position below text edit field
            overlay_y = self.text_edit_y + 1
            # Ensure it doesn't go off bottom of screen
            if overlay_y + overlay_height > height:
                overlay_y = height - overlay_height
        
        # Calculate overlay X position (aligned with completion start)
        # Shift left by 2 to account for left border (1) and left padding (1)
        # This aligns the candidate text with the text being edited
        overlay_x = self.completion_start_x - 2
        # Ensure it doesn't go off left edge
        if overlay_x < 0:
            overlay_x = 0
        # Ensure it doesn't go off right edge of screen
        if overlay_x + overlay_width > width:
            overlay_x = width - overlay_width
        
        # Get color and attributes for overlay
        color_pair, attributes = get_status_color()
        
        # Determine if scrollbar is needed
        show_scrollbar = len(self.candidates) > self.max_visible_candidates
        
        # Calculate available width for candidate text
        # Exclude borders (2), padding (2), and scrollbar (1 if shown)
        scrollbar_width = 1 if show_scrollbar else 0
        available_width = overlay_width - 4 - scrollbar_width
        
        # Draw top border
        if overlay_y >= 0 and overlay_y < height:
            top_border = (self.corner_chars["top_left"] + 
                         self.horizontal_border_char * (overlay_width - 2) + 
                         self.corner_chars["top_right"])
            self._safe_draw_text(overlay_y, overlay_x, top_border, color_pair, attributes)
        
        # Draw candidates
        for i in range(num_candidates):
            candidate_y = overlay_y + 1 + i
            
            if candidate_y < 0 or candidate_y >= height:
                continue
            
            # Get the actual candidate index accounting for scroll offset
            candidate_index = self.scroll_offset + i
            
            # Skip if we've scrolled past the end of the candidate list
            if candidate_index >= len(self.candidates):
                break
            
            candidate = self.candidates[candidate_index]
            
            # Truncate candidate if needed
            if get_width(candidate) > available_width:
                candidate = truncate_text(candidate, available_width, "…")
            
            # Pad candidate to fill available width
            candidate_display_width = get_width(candidate)
            padding = " " * (available_width - candidate_display_width)
            
            # Determine color based on focus state
            # Use focused color for the focused candidate, normal color for others
            if self.focused_index is not None and candidate_index == self.focused_index:
                # Import color constants for focused highlighting
                from tfm_colors import COLOR_REGULAR_FILE_FOCUSED
                candidate_color = COLOR_REGULAR_FILE_FOCUSED
                candidate_attrs = TextAttribute.NORMAL
            else:
                # Use normal status color for unfocused candidates
                candidate_color = color_pair
                candidate_attrs = attributes
            
            # Draw left border with normal color (no focused background)
            self._safe_draw_text(candidate_y, overlay_x, self.border_char, color_pair, attributes)
            
            # Draw left padding with normal color (no focused background)
            self._safe_draw_text(candidate_y, overlay_x + 1, " ", color_pair, attributes)
            
            # Draw candidate text with focused background if applicable
            self._safe_draw_text(candidate_y, overlay_x + 2, candidate + padding, candidate_color, candidate_attrs)
            
            # Draw right padding with normal color (no focused background)
            if show_scrollbar:
                # Extra space for scrollbar
                self._safe_draw_text(candidate_y, overlay_x + 2 + available_width, "  ", color_pair, attributes)
                # Right border after scrollbar space
                self._safe_draw_text(candidate_y, overlay_x + overlay_width - 1, self.border_char, color_pair, attributes)
            else:
                # Single space padding
                self._safe_draw_text(candidate_y, overlay_x + 2 + available_width, " ", color_pair, attributes)
                # Right border
                self._safe_draw_text(candidate_y, overlay_x + overlay_width - 1, self.border_char, color_pair, attributes)
        
        # Draw scrollbar if needed (inside the right border)
        if show_scrollbar:
            # Scrollbar position: right edge minus 2 (for right border and space)
            scrollbar_x = overlay_x + overlay_width - 2
            # Scrollbar starts at first candidate line
            scrollbar_start_y = overlay_y + 1
            # Scrollbar height is the number of visible candidates
            scrollbar_height = num_candidates
            
            # Draw the scrollbar
            draw_scrollbar(
                self.renderer,
                scrollbar_start_y,
                scrollbar_x,
                scrollbar_height,
                len(self.candidates),
                self.scroll_offset,
                inverted=False
            )
        
        # Draw bottom border
        bottom_y = overlay_y + 1 + num_candidates
        if bottom_y >= 0 and bottom_y < height:
            # Draw normal bottom border (scrollbar indicates if more candidates exist)
            bottom_border = (self.corner_chars["bottom_left"] + 
                           self.horizontal_border_char * (overlay_width - 2) + 
                           self.corner_chars["bottom_right"])
            
            self._safe_draw_text(bottom_y, overlay_x, bottom_border, color_pair, attributes)
    
    def _safe_draw_text(self, y: int, x: int, text: str, color_pair: int, attributes: int):
        """
        Safely draw text to screen, handling boundary conditions.
        
        Args:
            y: Y coordinate
            x: X coordinate
            text: Text to draw
            color_pair: Color pair to use
            attributes: Text attributes to use
        """
        try:
            height, width = self.renderer.get_dimensions()
            if 0 <= y < height and 0 <= x < width:
                # Get safe wide character functions
                safe_funcs = get_safe_functions()
                get_width = safe_funcs['get_display_width']
                truncate_text = safe_funcs['truncate_to_width']
                
                # Calculate available display width
                max_display_width = width - x
                
                # Truncate text if it would go beyond screen width
                if get_width(text) > max_display_width:
                    text = truncate_text(text, max_display_width, "")
                
                self.renderer.draw_text(y, x, text, color_pair=color_pair, attributes=attributes)
        except Exception as e:
            # Log rendering errors but don't crash
            self.logger.error(f"Error drawing text at ({y}, {x}): {e}")
    
    def move_focus_down(self):
        """
        Move focus to the next candidate (Down arrow key).
        
        Behavior:
        - If no focus, activate focus on first candidate
        - If focus on last candidate, wrap to first candidate
        - Otherwise, move focus to next candidate
        - Auto-scroll to keep focused candidate visible
        
        Requirements:
        - 9.1: Down arrow moves focus to next candidate
        - 9.3: Wrap from last to first candidate
        - 9.5: Activate focus on first candidate if no focus
        """
        if not self.candidates:
            return
        
        if self.focused_index is None:
            # No focus yet - activate on first candidate
            self.focused_index = 0
        elif self.focused_index >= len(self.candidates) - 1:
            # At last candidate - wrap to first
            self.focused_index = 0
        else:
            # Move to next candidate
            self.focused_index += 1
        
        # Ensure focused_index is valid
        self.focused_index = max(0, min(self.focused_index, len(self.candidates) - 1))
        
        # Auto-scroll to keep focused candidate visible
        self._ensure_focused_visible()
    
    def move_focus_up(self):
        """
        Move focus to the previous candidate (Up arrow key).
        
        Behavior:
        - If no focus, activate focus on last candidate
        - If focus on first candidate, wrap to last candidate
        - Otherwise, move focus to previous candidate
        - Auto-scroll to keep focused candidate visible
        
        Requirements:
        - 9.2: Up arrow moves focus to previous candidate
        - 9.4: Wrap from first to last candidate
        - 9.6: Activate focus on last candidate if no focus
        """
        if not self.candidates:
            return
        
        if self.focused_index is None:
            # No focus yet - activate on last candidate
            self.focused_index = len(self.candidates) - 1
        elif self.focused_index <= 0:
            # At first candidate - wrap to last
            self.focused_index = len(self.candidates) - 1
        else:
            # Move to previous candidate
            self.focused_index -= 1
        
        # Ensure focused_index is valid
        self.focused_index = max(0, min(self.focused_index, len(self.candidates) - 1))
        
        # Auto-scroll to keep focused candidate visible
        self._ensure_focused_visible()
    
    def get_focused_candidate(self) -> Optional[str]:
        """
        Get the text of the currently focused candidate.
        
        Returns:
            str: The focused candidate text, or None if no focus
        """
        if self.focused_index is None or not self.candidates:
            return None
        
        if 0 <= self.focused_index < len(self.candidates):
            return self.candidates[self.focused_index]
        
        return None
    
    def has_focus(self) -> bool:
        """
        Check if any candidate is currently focused.
        
        Returns:
            bool: True if a candidate is focused, False otherwise
        """
        return self.focused_index is not None
    
    def clear_focus(self):
        """
        Clear the focus state.
        
        This resets the focused_index to None, removing focus from all candidates.
        Called when ESC is pressed or when a candidate is selected.
        """
        self.focused_index = None
    
    def _ensure_focused_visible(self):
        """
        Ensure the focused candidate is visible by adjusting scroll_offset.
        
        This method calculates the visible range and adjusts scroll_offset
        to keep the focused candidate within the visible area.
        
        Requirements:
        - 12.4: Auto-scroll to keep focused candidate visible
        - 12.5: Scroll up when focused candidate is above visible area
        - 12.6: Scroll down when focused candidate is below visible area
        """
        if self.focused_index is None or not self.candidates:
            return
        
        # Calculate the number of visible candidates
        visible_count = min(len(self.candidates), self.max_visible_candidates)
        
        # Calculate the visible range
        first_visible = self.scroll_offset
        last_visible = self.scroll_offset + visible_count - 1
        
        # Check if focused candidate is above visible area
        if self.focused_index < first_visible:
            # Scroll up to show the focused candidate
            self.scroll_offset = self.focused_index
        
        # Check if focused candidate is below visible area
        elif self.focused_index > last_visible:
            # Scroll down to show the focused candidate
            # Position it at the bottom of the visible area
            self.scroll_offset = self.focused_index - visible_count + 1
        
        # Ensure scroll_offset is within valid bounds
        max_scroll = max(0, len(self.candidates) - visible_count)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
