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
from tfm_string_width import reduce_width, ShorteningRegion, calculate_display_width


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
        self.shortening_regions = None  # Optional list of ShorteningRegion for prompt shortening
        self.callback = None
        self.cancel_callback = None
        
    def show_status_line_input(self, prompt, initial_text="", callback=None, cancel_callback=None, shortening_regions=None):
        """
        Show a status line input dialog
        
        Args:
            prompt (str): The prompt text to display
            initial_text (str): Initial text in the input field
            callback (callable): Function to call when Enter is pressed
            cancel_callback (callable): Function to call when ESC is pressed
            shortening_regions (list): Optional list of ShorteningRegion for intelligent prompt shortening.
                                      If None, default right abbreviation is used when prompt is too long.
        """
        self.is_active = True
        self.prompt_text = prompt
        self.shortening_regions = shortening_regions
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
        self.shortening_regions = None
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
        
        # Get safe wide character functions
        safe_funcs = get_safe_functions()
        get_width = safe_funcs['get_display_width']
        
        # Get status color and attributes
        status_color, status_attrs = get_status_color()
        
        # Fill entire status line with background color
        status_line = " " * (width - 1)
        self.renderer.draw_text(status_y, 0, status_line, 
                               color_pair=status_color, 
                               attributes=status_attrs)
        
        # Don't show help text during editing to avoid position shifts
        # caused by IME composition text width variations
        
        # Reserve minimum 40 chars for the input field
        min_input_width = 40
        # Leave some margin (4 chars total: 2 on left, 2 on right)
        margin = 4
        max_prompt_width = width - margin - min_input_width
        
        # Shorten prompt if needed using reduce_width with optional regions
        prompt = self.prompt_text
        prompt_width = calculate_display_width(prompt)
        if prompt_width > max_prompt_width and max_prompt_width > 0:
            if self.shortening_regions:
                # Use provided shortening regions
                prompt = reduce_width(prompt, max_prompt_width, regions=self.shortening_regions)
            else:
                # Use default right abbreviation
                prompt = reduce_width(prompt, max_prompt_width, default_position='right')
        
        # Calculate available space for the input field (prompt + text)
        max_field_width = width - margin
        
        # Ensure minimum width for the input field using display width
        prompt_width = calculate_display_width(prompt)
        min_field_width = prompt_width + 5  # At least 5 chars for input
        if max_field_width < min_field_width:
            max_field_width = min_field_width
        
        # Draw input field using SingleLineTextEdit
        # SingleLineTextEdit.draw() will set the caret position for IME
        self.text_editor.draw(
            self.renderer, status_y, 2, max_field_width,
            prompt,
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
        
        Uses 'all_or_nothing' strategy: either shows the full middle part or removes it entirely.
        """
        if not current_name:
            current_name = original_name
        
        # Full prompt with original name
        full_prompt = f"Rename '{original_name}' to: "
        
        # Define shortening region: " '{original_name}' to" (middle part)
        # This leaves "Rename" at start and ": " at end
        # Uses 'all_or_nothing' strategy for clean removal
        regions = [
            ShorteningRegion(
                start=6,  # After "Rename"
                end=len(full_prompt) - 2,  # Before ": "
                priority=1,
                strategy='all_or_nothing'  # Either show full or remove entirely
            )
        ]
        
        dialog.show_status_line_input(
            prompt=full_prompt,
            initial_text=current_name,
            shortening_regions=regions
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