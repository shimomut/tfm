#!/usr/bin/env python3
"""
Candidate List Overlay Component for TFM (Terminal File Manager)

This module provides a CandidateListOverlay class that displays completion
candidates in an overlay UI positioned above or below a text edit field.
The overlay automatically positions itself based on available screen space
and aligns horizontally with the completion start position.
"""

from typing import List
from ttk import TextAttribute
from ttk.wide_char_utils import get_display_width, truncate_to_width, get_safe_functions
from tfm_colors import get_status_color
from tfm_log_manager import getLogger


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
        overlay_x = self.completion_start_x
        # Ensure it doesn't go off right edge of screen
        if overlay_x + overlay_width > width:
            overlay_x = width - overlay_width
        # Ensure it doesn't go off left edge
        if overlay_x < 0:
            overlay_x = 0
        
        # Get color and attributes for overlay
        color_pair, attributes = get_status_color()
        
        # Calculate available width for candidate text (excluding borders and padding)
        available_width = overlay_width - 4
        
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
            
            candidate = self.candidates[i]
            
            # Truncate candidate if needed
            if get_width(candidate) > available_width:
                candidate = truncate_text(candidate, available_width, "…")
            
            # Pad candidate to fill available width
            candidate_display_width = get_width(candidate)
            padding = " " * (available_width - candidate_display_width)
            
            # Draw candidate line with borders
            line = f"{self.border_char} {candidate}{padding} {self.border_char}"
            self._safe_draw_text(candidate_y, overlay_x, line, color_pair, attributes)
        
        # Draw bottom border
        bottom_y = overlay_y + 1 + num_candidates
        if bottom_y >= 0 and bottom_y < height:
            # Check if there are more candidates than displayed
            if len(self.candidates) > num_candidates:
                # Show indicator that more candidates exist
                indicator = f" +{len(self.candidates) - num_candidates} more "
                indicator_width = get_width(indicator)
                
                # Calculate how much border to show on each side
                remaining_width = overlay_width - 2 - indicator_width
                left_border_width = remaining_width // 2
                right_border_width = remaining_width - left_border_width
                
                bottom_border = (self.corner_chars["bottom_left"] + 
                               self.horizontal_border_char * left_border_width +
                               indicator +
                               self.horizontal_border_char * right_border_width +
                               self.corner_chars["bottom_right"])
            else:
                # Normal bottom border
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
