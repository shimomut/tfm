#!/usr/bin/env python3
"""
General Purpose Dialog component for TFM (Terminal File Manager)

This module provides a reusable GeneralPurposeDialog class that can handle
various overlay dialog types including:
- Single-line text input dialogs (filter, rename, create file/directory, etc.)
- Status line dialogs
- Future: Multi-line dialogs, choice dialogs, etc.
"""

from ttk import TextAttribute, KeyCode
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_colors import get_status_color
from tfm_wide_char_utils import get_display_width, get_safe_functions
from tfm_input_compat import ensure_input_event


class DialogType:
    """Constants for different dialog types"""
    STATUS_LINE_INPUT = "status_line_input"
    # Future dialog types can be added here
    # OVERLAY_INPUT = "overlay_input"
    # CHOICE_DIALOG = "choice_dialog"


class GeneralPurposeDialog:
    """A flexible dialog system for various TFM dialog needs"""
    
    def __init__(self, config=None, renderer=None):
        """
        Initialize the dialog system
        
        Args:
            config: TFM configuration object
            renderer: TTK Renderer instance
        """
        self.config = config
        self.renderer = renderer
        self.is_active = False
        self.dialog_type = None
        self.content_changed = True  # Track if content needs redraw
        
        # Status line input dialog state
        self.text_editor = SingleLineTextEdit()
        self.prompt_text = ""
        self.help_text = ""
        self.callback = None
        self.cancel_callback = None
        
    def show_status_line_input(self, prompt, help_text="ESC:cancel Enter:confirm", 
                              initial_text="", callback=None, cancel_callback=None):
        """
        Show a status line input dialog
        
        Args:
            prompt (str): The prompt text to display
            help_text (str): Help text to show on the right side
            initial_text (str): Initial text in the input field
            callback (callable): Function to call when Enter is pressed
            cancel_callback (callable): Function to call when ESC is pressed
        """
        self.is_active = True
        self.dialog_type = DialogType.STATUS_LINE_INPUT
        self.prompt_text = prompt
        self.help_text = help_text
        self.callback = callback
        self.cancel_callback = cancel_callback
        self.content_changed = True  # Mark content as changed when showing
        
        self.text_editor.set_text(initial_text)
        self.text_editor.set_cursor_pos(len(initial_text))
    
    def hide(self):
        """Hide the dialog"""
        self.is_active = False
        self.dialog_type = None
        self.content_changed = True  # Mark content as changed when hiding
        self.text_editor.clear()
        self.prompt_text = ""
        self.help_text = ""
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
            event: InputEvent from TTK (or integer key code for backward compatibility)
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Backward compatibility: convert integer key codes to InputEvent
        event = ensure_input_event(event)
        
        if not self.is_active or not event:
            return False
        
        if self.dialog_type == DialogType.STATUS_LINE_INPUT:
            return self._handle_status_line_input(event)
        
        return False
    
    def _handle_status_line_input(self, event):
        """Handle input for status line input dialog"""
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
        
        # Handle text editing
        else:
            # Convert InputEvent to key code for SingleLineTextEdit (which hasn't been migrated yet)
            # This is a temporary workaround until task 26 migrates SingleLineTextEdit
            from tfm_input_utils import input_event_to_curses_key
            key = input_event_to_curses_key(event)
            if key is not None:
                handled = self.text_editor.handle_key(key)
                if handled:
                    self.content_changed = True  # Mark content as changed
                return handled
            return False
    
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        return self.content_changed
    
    def draw(self):
        """
        Draw the dialog using TTK renderer
        """
        if not self.is_active or not self.renderer:
            return
        
        if self.dialog_type == DialogType.STATUS_LINE_INPUT:
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
        
        # Calculate help text space and position first using display width
        help_text_width = get_width(self.help_text) if self.help_text else 0
        help_margin = 3  # Space around help text
        help_total_space = help_text_width + help_margin if self.help_text else 0
        
        # Reserve space for help text if it can fit
        reserved_help_space = 0
        show_help = False
        if self.help_text and width > help_total_space + 20:  # Need at least 20 chars for input
            reserved_help_space = help_total_space
            show_help = True
        
        # Calculate available space for the input field (prompt + text)
        # Leave some margin (4 chars) and space for help text if showing
        max_field_width = width - reserved_help_space - 4
        
        # Ensure minimum width for the input field using display width
        prompt_width = get_width(self.prompt_text)
        min_field_width = prompt_width + 5  # At least 5 chars for input
        if max_field_width < min_field_width:
            max_field_width = min_field_width
            show_help = False  # Disable help if no space
        
        # Get stdscr from renderer for SingleLineTextEdit (which hasn't been migrated yet)
        stdscr = getattr(self.renderer, 'stdscr', None)
        if stdscr:
            # Draw input field using SingleLineTextEdit
            self.text_editor.draw(
                stdscr, status_y, 2, max_field_width,
                self.prompt_text,
                is_active=True
            )
        
        # Show help text on the right if we determined it should be shown
        if show_help and self.help_text:
            help_x = width - help_text_width - 2
            # Make sure help text doesn't overlap with input field
            # Calculate input field end position using display widths
            input_text_width = get_width(self.text_editor.text)
            input_end_x = 2 + min(max_field_width, prompt_width + input_text_width + 1)
            if help_x > input_end_x + 2:  # At least 2 chars gap
                self.renderer.draw_text(status_y, help_x, self.help_text, 
                                       color_pair=status_color, 
                                       attributes=TextAttribute.DIM)


# Helper functions for common dialog patterns
class DialogHelpers:
    """Helper functions for common dialog operations"""
    
    @staticmethod
    def create_filter_dialog(dialog, current_filter=""):
        """Create a filter dialog configuration"""
        dialog.show_status_line_input(
            prompt="Filter: ",
            help_text="ESC:cancel Enter:apply (files only: *.py, test_*, *.[ch])",
            initial_text=current_filter
        )
    
    @staticmethod
    def create_rename_dialog(dialog, original_name, current_name=""):
        """Create a rename dialog configuration"""
        if not current_name:
            current_name = original_name
        dialog.show_status_line_input(
            prompt=f"Rename '{original_name}' to: ",
            help_text="ESC:cancel Enter:confirm",
            initial_text=current_name
        )
    
    @staticmethod
    def create_create_directory_dialog(dialog):
        """Create a create directory dialog configuration"""
        dialog.show_status_line_input(
            prompt="Create directory: ",
            help_text="ESC:cancel Enter:create"
        )
    
    @staticmethod
    def create_create_file_dialog(dialog):
        """Create a create file dialog configuration"""
        dialog.show_status_line_input(
            prompt="Create file: ",
            help_text="ESC:cancel Enter:create"
        )
    
    @staticmethod
    def create_create_archive_dialog(dialog):
        """Create an archive creation dialog configuration"""
        dialog.show_status_line_input(
            prompt="Archive filename: ",
            help_text="ESC:cancel Enter:create (.zip/.tar.gz/.tgz)"
        )