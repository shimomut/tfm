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
        
    def show_status_line_input(self, prompt, initial_text="", callback=None, cancel_callback=None, completer=None):
        """
        Show a status line input dialog
        
        Args:
            prompt (str): The prompt text to display
            initial_text (str): Initial text in the input field
            callback (callable): Function to call when Enter is pressed
            cancel_callback (callable): Function to call when ESC is pressed
            completer (Completer): Optional completer for TAB completion
        """
        self.is_active = True
        self.prompt_text = prompt
        self.callback = callback
        self.cancel_callback = cancel_callback
        self.content_changed = True  # Mark content as changed when showing
        
        # Create new text editor with optional completer
        self.text_editor = SingleLineTextEdit(renderer=self.renderer, completer=completer)
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
            # Handle ESC - but first check if SingleLineTextEdit wants to handle it
            # (e.g., for hiding candidate list in TAB completion)
            if event.key_code == KeyCode.ESCAPE:
                # Let SingleLineTextEdit handle ESC first if candidate list is visible
                # This allows TAB completion to intercept ESC for hiding the candidate list
                if hasattr(self.text_editor, 'candidate_list') and self.text_editor.candidate_list:
                    if self.text_editor.completion_active and self.text_editor.candidate_list.is_visible:
                        # SingleLineTextEdit will handle this ESC key for hiding candidate list
                        handled = self.text_editor.handle_key(event)
                        if handled:
                            self.content_changed = True
                        return handled
                
                # No visible candidate list - handle ESC normally (cancel and close)
                # Store callback before hiding
                cancel_callback = self.cancel_callback
                self.hide()
                # Call callback after hiding to allow new dialogs
                if cancel_callback:
                    cancel_callback()
                return True
            
            # Handle Enter - but first check if SingleLineTextEdit wants to handle it
            # (e.g., for candidate selection in TAB completion)
            elif event.key_code == KeyCode.ENTER:
                # Let SingleLineTextEdit handle Enter first if it has a focused candidate
                # This allows TAB completion to intercept Enter for candidate selection
                if hasattr(self.text_editor, 'candidate_list') and self.text_editor.candidate_list:
                    if self.text_editor.candidate_list.has_focus():
                        # SingleLineTextEdit will handle this Enter key for candidate selection
                        handled = self.text_editor.handle_key(event)
                        if handled:
                            self.content_changed = True
                        return handled
                
                # No focused candidate - handle Enter normally (confirm and close)
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
        
        # Calculate available space for the input field (prompt + text)
        # Leave some margin (4 chars total: 2 on left, 2 on right)
        margin = 4
        max_field_width = width - margin
        
        # Draw input field using SingleLineTextEdit
        # SingleLineTextEdit.draw() will set the caret position for IME
        self.text_editor.draw(
            self.renderer, status_y, 2, max_field_width,
            self.prompt_text,
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
        """Create a rename dialog configuration with simple static prompt
        
        Uses a simple "Rename to: " prompt for all rename operations.
        """
        if not current_name:
            current_name = original_name
        
        dialog.show_status_line_input(
            prompt="Rename to: ",
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