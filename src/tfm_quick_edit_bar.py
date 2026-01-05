#!/usr/bin/env python3
"""
Quick Edit Bar component for TFM (Terminal File Manager)

This module provides a reusable QuickEditBar class for single-line text input
in the status bar area (filter, rename, create file/directory, etc.)
"""

from ttk import TextAttribute, KeyCode
from ttk.input_event import KeyEvent
from ttk.wide_char_utils import get_display_width, get_safe_functions

from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_colors import get_status_color
from tfm_text_layout import (
    draw_text_segments, AbbreviationSegment, AsIsSegment, AllOrNothingSegment, 
    TextSegment, calculate_display_width
)
from typing import Union, List


class QuickEditBar:
    """A quick edit bar for single-line text input in the status bar"""
    
    def __init__(self, config=None, renderer=None):
        """
        Initialize the quick edit bar
        
        Args:
            config: TFM configuration object
            renderer: TTK Renderer instance
        """
        self.config = config
        self.renderer = renderer
        self.is_active = False
        self.content_changed = True  # Track if content needs redraw
        
        # Status line input dialog state
        self.text_editor = SingleLineTextEdit(renderer=renderer)
        self.prompt_text = ""
        self.callback = None
        self.cancel_callback = None
        
    def show_status_line_input(self, prompt, initial_text="", callback=None, cancel_callback=None):
        """
        Show a status line input dialog
        
        Args:
            prompt: The prompt text to display. Can be either:
                   - str: Plain text prompt (will be converted to AbbreviationSegment)
                   - List[TextSegment]: List of text segments for advanced formatting
            initial_text (str): Initial text in the input field
            callback (callable): Function to call when Enter is pressed
            cancel_callback (callable): Function to call when ESC is pressed
        """
        self.is_active = True
        self.prompt_text = prompt
        self.callback = callback
        self.cancel_callback = cancel_callback
        self.content_changed = True  # Mark content as changed when showing
        
        self.text_editor.set_text(initial_text)
        self.text_editor.set_cursor_pos(len(initial_text))
    
    def hide(self):
        """Hide the dialog"""
        self.is_active = False
        self.content_changed = True  # Mark content as changed when hiding
        self.text_editor.clear()
        self.prompt_text = ""
        self.callback = None
        self.cancel_callback = None
    
    def get_text(self):
        """Get the current text from the input field"""
        return self.text_editor.get_text()
    
    def set_text(self, text):
        """Set the text in the input field"""
        self.text_editor.set_text(text)
    
    def handle_input(self, event):
        """
        Handle input for the dialog
        
        Args:
            event: KeyEvent from TTK (or integer key code for backward compatibility)
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if not self.is_active or not event:
            return False
        
        return self._handle_status_line_input(event)
    
    def _handle_status_line_input(self, event):
        """Handle input for status line input dialog"""
        # Check if it's a KeyEvent first
        if isinstance(event, KeyEvent):
            # Handle ESC - cancel
            if event.key_code == KeyCode.ESCAPE:
                # Store callback before hiding
                cancel_callback = self.cancel_callback
                self.hide()
                # Call callback after hiding to allow new dialogs
                if cancel_callback:
                    cancel_callback()
                return True
            
            # Handle Enter - confirm
            elif event.key_code == KeyCode.ENTER:
                # Store callback and text before hiding
                callback = self.callback
                text = self.text_editor.get_text()
                self.hide()
                # Call callback after hiding to allow new dialogs
                if callback:
                    callback(text)
                return True
        
        # Handle text editing (both KeyEvent and CharEvent)
        # Pass event directly to SingleLineTextEdit
        # SingleLineTextEdit handles both KeyEvent and CharEvent
        handled = self.text_editor.handle_key(event)
        if handled:
            self.content_changed = True  # Mark content as changed
        return handled
    
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        return self.content_changed
    
    def draw(self):
        """
        Draw the dialog using TTK renderer
        """
        if not self.is_active or not self.renderer:
            return
        
        self._draw_status_line_input()
        
        # Automatically mark as not needing redraw after drawing
        self.content_changed = False
    
    def _draw_status_line_input(self):
        """Draw status line input dialog with wide character support"""
        height, width = self.renderer.get_dimensions()
        status_y = height - 1
        
        # Get status color and attributes
        status_color, status_attrs = get_status_color()
        
        # Fill entire status line with background color
        status_line = " " * (width - 1)
        self.renderer.draw_text(status_y, 0, status_line, 
                               color_pair=status_color, 
                               attributes=status_attrs)
        
        # Don't show help text during editing to avoid position shifts
        # caused by IME composition text width variations
        
        # Build segments list for the prompt
        segments = []
        
        # Add leading spaces
        segments.append(AsIsSegment("  "))
        
        # Add prompt segment(s)
        # Prompt can be either a string or a list of TextSegment objects
        if isinstance(self.prompt_text, str):
            # String prompt: convert to AbbreviationSegment with priority-based shortening
            segments.append(AbbreviationSegment(
                self.prompt_text,
                priority=0,
                min_length=10,
                abbrev_position='right'
            ))
        elif isinstance(self.prompt_text, list):
            # List of TextSegment objects: use them directly
            segments.extend(self.prompt_text)
        else:
            # Fallback: convert to string and use as AbbreviationSegment
            segments.append(AbbreviationSegment(
                str(self.prompt_text),
                priority=0,
                min_length=10,
                abbrev_position='right'
            ))
        
        # Calculate the prompt width after layout
        # We need to know how much space the prompt takes to position the input field
        # Reserve minimum 40 chars for the input field
        min_input_width = 40
        margin = 4  # Total margin (2 on left, 2 on right)
        max_prompt_width = width - margin - min_input_width
        
        # Calculate available space for the input field (prompt + text)
        max_field_width = width - margin
        
        # Draw input field using SingleLineTextEdit
        # SingleLineTextEdit.draw() will render both prompt and input field
        # and set the caret position for IME
        # We need to extract just the prompt text for SingleLineTextEdit
        if isinstance(self.prompt_text, str):
            prompt_for_editor = self.prompt_text
        elif isinstance(self.prompt_text, list):
            # Concatenate text from all segments
            prompt_for_editor = "".join(seg.text for seg in self.prompt_text if hasattr(seg, 'text'))
        else:
            prompt_for_editor = str(self.prompt_text)
        
        # For list of segments with AllOrNothingSegment, we need to handle shortening properly
        # If the full prompt doesn't fit, check if any AllOrNothingSegment should be removed
        if isinstance(self.prompt_text, list) and max_prompt_width > 0:
            full_width = calculate_display_width(prompt_for_editor)
            if full_width > max_prompt_width:
                # Need to shorten - remove AllOrNothingSegment segments
                shortened_segments = []
                for seg in self.prompt_text:
                    if isinstance(seg, AllOrNothingSegment):
                        # Skip this segment (all-or-nothing: remove entirely)
                        continue
                    else:
                        shortened_segments.append(seg)
                
                # Recalculate prompt text without AllOrNothingSegment segments
                prompt_for_editor = "".join(seg.text for seg in shortened_segments if hasattr(seg, 'text'))
                
                # If still too long, use simple right abbreviation
                if calculate_display_width(prompt_for_editor) > max_prompt_width:
                    # Truncate from right with ellipsis
                    prompt_for_editor = prompt_for_editor[:max_prompt_width-1] + "…"
        elif calculate_display_width(prompt_for_editor) > max_prompt_width and max_prompt_width > 0:
            # Simple string prompt - use right abbreviation
            prompt_for_editor = prompt_for_editor[:max_prompt_width-1] + "…"
        
        # Ensure minimum width for the input field
        prompt_width = calculate_display_width(prompt_for_editor)
        min_field_width = prompt_width + 5  # At least 5 chars for input
        if max_field_width < min_field_width:
            max_field_width = min_field_width
        
        self.text_editor.draw(
            self.renderer, status_y, 2, max_field_width,
            prompt_for_editor,
            is_active=True
        )
        
        # Note: Don't call renderer.refresh() here - UILayerStack will do it
        # after rendering all layers


# Helper functions for common dialog patterns
class QuickEditBarHelpers:
    """Helper functions for common dialog operations"""
    
    @staticmethod
    def create_filter_dialog(dialog, current_filter=""):
        """Create a filter dialog configuration"""
        dialog.show_status_line_input(
            prompt="Filter: ",
            initial_text=current_filter
        )
    
    @staticmethod
    def create_rename_dialog(dialog, original_name, current_name=""):
        """Create a rename dialog configuration with intelligent prompt shortening
        
        The prompt format is: "Rename '{original_name}' to: "
        When space is limited (less than 40 chars for input + full prompt),
        it falls back to just "Rename: " to ensure adequate input space.
        
        Uses all-or-nothing strategy: either shows the full middle part or removes it entirely.
        """
        if not current_name:
            current_name = original_name
        
        # Build prompt as a list of TextSegment objects
        # The middle part (original filename) uses AllOrNothingSegment
        # so it's either shown in full or removed entirely
        prompt_segments = [
            AsIsSegment("Rename"),
            AllOrNothingSegment(
                f" '{original_name}' to",
                priority=1  # Higher priority, removed first when space is limited
            ),
            AsIsSegment(": ")
        ]
        
        dialog.show_status_line_input(
            prompt=prompt_segments,
            initial_text=current_name
        )
    
    @staticmethod
    def create_create_directory_dialog(dialog):
        """Create a create directory dialog configuration"""
        dialog.show_status_line_input(
            prompt="Create directory: "
        )
    
    @staticmethod
    def create_create_file_dialog(dialog):
        """Create a create file dialog configuration"""
        dialog.show_status_line_input(
            prompt="Create file: "
        )
    
    @staticmethod
    def create_create_archive_dialog(dialog):
        """Create an archive creation dialog configuration"""
        dialog.show_status_line_input(
            prompt="Archive filename: "
        )