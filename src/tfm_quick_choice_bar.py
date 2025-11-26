#!/usr/bin/env python3
"""
TUI File Manager - Quick Choice Bar Component
Provides quick choice dialog functionality displayed in the status bar
"""

import curses
from tfm_const import KEY_ENTER_1, KEY_ENTER_2
from tfm_colors import get_status_color


class QuickChoiceBar:
    """Quick choice bar component for displaying choice dialogs in the status bar"""
    
    def __init__(self, config):
        self.config = config
        
        # Quick choice bar state
        self.is_active = False
        self.message = ""
        self.choices = []  # List of choice dictionaries: [{"text": "Yes", "key": "y", "value": True}, ...]
        self.callback = None
        self.selected = 0  # Index of currently selected choice
        
    def show(self, message, choices, callback):
        """Show a quick choice dialog
        
        Args:
            message: The message to display
            choices: List of choice dictionaries with format:
                     [{"text": "Yes", "key": "y", "value": True}, 
                      {"text": "No", "key": "n", "value": False},
                      {"text": "Cancel", "key": "c", "value": None}]
            callback: Function to call with the selected choice's value
        """
        self.is_active = True
        self.message = message
        self.choices = choices
        self.callback = callback
        self.selected = 0  # Default to first choice
        
    def exit(self):
        """Exit quick choice mode"""
        self.is_active = False
        self.message = ""
        self.choices = []
        self.callback = None
        self.selected = 0
        
    def handle_input(self, key):
        """Handle input while in quick choice mode"""
        if key == 27:  # ESC - cancel
            return ('cancel', None)
            
        elif key == curses.KEY_LEFT:
            # Move selection left
            if self.choices:
                self.selected = (self.selected - 1) % len(self.choices)
                return ('selection_changed', None)
            return True
            
        elif key == curses.KEY_RIGHT:
            # Move selection right
            if self.choices:
                self.selected = (self.selected + 1) % len(self.choices)
                return ('selection_changed', None)
            return True
            
        elif key == curses.KEY_ENTER or key == KEY_ENTER_1 or key == KEY_ENTER_2:
            # Execute selected action
            if self.choices and 0 <= self.selected < len(self.choices):
                selected_choice = self.choices[self.selected]
                return ('execute', selected_choice["value"])
            return ('execute', None)
            
        else:
            # Check for quick key matches
            key_char = chr(key).lower() if 32 <= key <= 126 else None
            if key_char:
                for choice in self.choices:
                    if "key" in choice and choice["key"] and choice["key"].lower() == key_char:
                        # Found matching quick key
                        return ('execute', choice["value"])
        
        return False
        
    def draw(self, stdscr, safe_addstr_func, status_y, width):
        """Draw the quick choice bar in the status line
        
        Args:
            stdscr: The curses screen object
            safe_addstr_func: Function to safely add strings to screen
            status_y: Y coordinate of the status line
            width: Screen width
        """
        # Fill entire status line with background color
        status_line = " " * (width - 1)
        safe_addstr_func(status_y, 0, status_line, get_status_color())
        
        # Show dialog message
        message = f"{self.message} "
        safe_addstr_func(status_y, 2, message, get_status_color())
        
        button_start_x = len(message) + 4
        
        for i, choice in enumerate(self.choices):
            choice_text = choice["text"]
            if i == self.selected:
                # Highlight selected option with bold and standout
                button_color = get_status_color() | curses.A_BOLD | curses.A_STANDOUT
                button_text = f"[{choice_text}]"
            else:
                button_color = get_status_color()
                button_text = f" {choice_text} "
            
            if button_start_x + len(button_text) < width - 2:
                safe_addstr_func(status_y, button_start_x, button_text, button_color)
                button_start_x += len(button_text) + 1
        
        # Generate help text based on available quick keys
        quick_keys = []
        for choice in self.choices:
            if "key" in choice and choice["key"]:
                quick_keys.append(choice["key"].upper())
        
        help_parts = ["←→:select", "Enter:confirm"]
        if quick_keys:
            help_parts.append(f"{'/'.join(quick_keys)}:quick")
        help_parts.append("ESC:cancel")
        help_text = " ".join(help_parts)
        
        if button_start_x + len(help_text) + 6 < width:
            help_x = width - len(help_text) - 3
            if help_x > button_start_x + 4:  # Ensure no overlap
                safe_addstr_func(status_y, help_x, help_text, get_status_color() | curses.A_DIM)


class QuickChoiceBarHelpers:
    """Helper functions for common quick choice bar use cases"""
    
    @staticmethod
    def create_yes_no_cancel_choices():
        """Create standard Yes/No/Cancel choices
        
        Returns:
            List of choice dictionaries for Yes/No/Cancel
        """
        return [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False},
            {"text": "Cancel", "key": "c", "value": None}
        ]
    
    @staticmethod
    def create_ok_cancel_choices():
        """Create standard OK/Cancel choices
        
        Returns:
            List of choice dictionaries for OK/Cancel
        """
        return [
            {"text": "OK", "key": "o", "value": True},
            {"text": "Cancel", "key": "c", "value": None}
        ]
    
    @staticmethod
    def create_continue_abort_choices():
        """Create standard Continue/Abort choices
        
        Returns:
            List of choice dictionaries for Continue/Abort
        """
        return [
            {"text": "Continue", "key": "c", "value": True},
            {"text": "Abort", "key": "a", "value": False}
        ]
    
    @staticmethod
    def create_overwrite_choices():
        """Create standard file overwrite choices
        
        Returns:
            List of choice dictionaries for file overwrite scenarios
        """
        return [
            {"text": "Overwrite", "key": "o", "value": "overwrite"},
            {"text": "Skip", "key": "s", "value": "skip"},
            {"text": "Rename", "key": "r", "value": "rename"},
            {"text": "Cancel", "key": "c", "value": None}
        ]
    
    @staticmethod
    def create_delete_choices():
        """Create standard delete confirmation choices
        
        Returns:
            List of choice dictionaries for delete operations
        """
        return [
            {"text": "Delete", "key": "d", "value": True},
            {"text": "Cancel", "key": "c", "value": False}
        ]
    
    @staticmethod
    def create_custom_choices(choice_specs):
        """Create custom choices from specifications
        
        Args:
            choice_specs: List of tuples (text, key, value) or dictionaries
            
        Returns:
            List of properly formatted choice dictionaries
        """
        choices = []
        for spec in choice_specs:
            if isinstance(spec, dict):
                # Already a dictionary, validate and use
                if "text" in spec and "value" in spec:
                    choices.append(spec)
            elif isinstance(spec, (tuple, list)) and len(spec) >= 2:
                # Convert tuple/list to dictionary
                text = spec[0]
                key = spec[1] if len(spec) > 1 else None
                value = spec[2] if len(spec) > 2 else text.lower()
                choices.append({"text": text, "key": key, "value": value})
        
        return choices
    
    @staticmethod
    def show_confirmation(quick_choice_bar, message, callback):
        """Show a standard confirmation dialog
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            message: Message to display
            callback: Function to call with result (True/False/None)
        """
        choices = QuickChoiceBarHelpers.create_yes_no_cancel_choices()
        quick_choice_bar.show(message, choices, callback)
    
    @staticmethod
    def show_overwrite_dialog(quick_choice_bar, filename, callback):
        """Show a file overwrite dialog
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            filename: Name of the file that would be overwritten
            callback: Function to call with result ("overwrite"/"skip"/"rename"/None)
        """
        message = f"File '{filename}' already exists. What do you want to do?"
        choices = QuickChoiceBarHelpers.create_overwrite_choices()
        quick_choice_bar.show(message, choices, callback)
    
    @staticmethod
    def show_delete_confirmation(quick_choice_bar, items, callback):
        """Show a delete confirmation dialog
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            items: List of items to delete or count of items
            callback: Function to call with result (True/False)
        """
        if isinstance(items, (list, tuple)):
            count = len(items)
            if count == 1:
                message = f"Delete '{items[0]}'?"
            else:
                message = f"Delete {count} selected items?"
        else:
            # Assume it's a count
            message = f"Delete {items} selected items?"
        
        choices = QuickChoiceBarHelpers.create_delete_choices()
        quick_choice_bar.show(message, choices, callback)
    
    @staticmethod
    def show_error_dialog(quick_choice_bar, error_message, callback=None):
        """Show an error dialog with OK button
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            error_message: Error message to display
            callback: Optional callback function
        """
        message = f"Error: {error_message}"
        choices = [{"text": "OK", "key": "o", "value": True}]
        
        def error_callback(result):
            if callback:
                callback(result)
        
        quick_choice_bar.show(message, choices, error_callback)
    
    @staticmethod
    def show_info_dialog(quick_choice_bar, info_message, callback=None):
        """Show an info dialog with OK button
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            info_message: Info message to display
            callback: Optional callback function
        """
        choices = [{"text": "OK", "key": "o", "value": True}]
        
        def info_callback(result):
            if callback:
                callback(result)
        
        quick_choice_bar.show(info_message, choices, info_callback)