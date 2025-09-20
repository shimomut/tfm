#!/usr/bin/env python3
"""
General Purpose Dialog component for TFM (Terminal File Manager)

This module provides a reusable GeneralPurposeDialog class that can handle
various overlay dialog types including:
- Single-line text input dialogs (filter, rename, create file/directory, etc.)
- Status line dialogs
- Future: Multi-line dialogs, choice dialogs, etc.
"""

import curses
from tfm_single_line_text_edit import SingleLineTextEdit
from tfm_colors import get_status_color


class DialogType:
    """Constants for different dialog types"""
    STATUS_LINE_INPUT = "status_line_input"
    # Future dialog types can be added here
    # OVERLAY_INPUT = "overlay_input"
    # CHOICE_DIALOG = "choice_dialog"


class GeneralPurposeDialog:
    """A flexible dialog system for various TFM dialog needs"""
    
    def __init__(self, config=None):
        """
        Initialize the dialog system
        
        Args:
            config: TFM configuration object
        """
        self.config = config
        self.is_active = False
        self.dialog_type = None
        
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
        
        self.text_editor.set_text(initial_text)
        self.text_editor.set_cursor_pos(len(initial_text))
    
    def hide(self):
        """Hide the dialog"""
        self.is_active = False
        self.dialog_type = None
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
    
    def handle_key(self, key):
        """
        Handle key input for the dialog
        
        Args:
            key (int): The key code from curses
            
        Returns:
            bool: True if the key was handled, False otherwise
        """
        if not self.is_active:
            return False
        
        if self.dialog_type == DialogType.STATUS_LINE_INPUT:
            return self._handle_status_line_input_key(key)
        
        return False
    
    def _handle_status_line_input_key(self, key):
        """Handle key input for status line input dialog"""
        # Handle ESC - cancel
        if key == 27:  # ESC
            if self.cancel_callback:
                self.cancel_callback()
            else:
                self.hide()
            return True
        
        # Handle Enter - confirm
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            if self.callback:
                self.callback(self.text_editor.get_text())
            else:
                self.hide()
            return True
        
        # Handle text editing
        else:
            return self.text_editor.handle_key(key)
    
    def draw(self, stdscr, safe_addstr_func):
        """
        Draw the dialog
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Function to safely add strings to screen
        """
        if not self.is_active:
            return
        
        if self.dialog_type == DialogType.STATUS_LINE_INPUT:
            self._draw_status_line_input(stdscr, safe_addstr_func)
    
    def _draw_status_line_input(self, stdscr, safe_addstr_func):
        """Draw status line input dialog"""
        height, width = stdscr.getmaxyx()
        status_y = height - 1
        
        # Fill entire status line with background color
        status_line = " " * (width - 1)
        safe_addstr_func(status_y, 0, status_line, get_status_color())
        
        # Calculate available space for input
        help_space = len(self.help_text) + 6 if self.help_text else 0
        max_input_width = width - len(self.prompt_text) - help_space - 4
        
        # Draw input field using SingleLineTextEdit
        self.text_editor.draw(
            stdscr, status_y, 2, max_input_width,
            self.prompt_text,
            is_active=True
        )
        
        # Show help text on the right if there's space and help text is provided
        if self.help_text:
            input_field_width = len(self.prompt_text) + len(self.text_editor.text) + 2
            if input_field_width + len(self.help_text) + 6 < width:
                help_x = width - len(self.help_text) - 3
                if help_x > input_field_width + 4:  # Ensure no overlap
                    safe_addstr_func(status_y, help_x, self.help_text, get_status_color() | curses.A_DIM)


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