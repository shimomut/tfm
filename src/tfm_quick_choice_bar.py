#!/usr/bin/env python3
"""
TUI File Manager - Quick Choice Bar Component
Provides quick choice dialog functionality displayed in the status bar
"""

from ttk import KeyCode, TextAttribute, KeyEvent, CharEvent
from tfm_colors import get_status_color
from tfm_string_width import reduce_width, ShorteningRegion, calculate_display_width


class QuickChoiceBar:
    """Quick choice bar component for displaying choice dialogs in the status bar"""
    
    def __init__(self, config, renderer=None):
        self.config = config
        self.renderer = renderer
        
        # Quick choice bar state
        self.is_active = False
        self.message = ""
        self.choices = []  # List of choice dictionaries: [{"text": "Yes", "key": "y", "value": True}, ...]
        self.callback = None
        self.selected = 0  # Index of currently selected choice
        self.enable_shift_modifier = False  # Whether Shift modifier is enabled for "apply to all"
        self.shortening_regions = None  # Optional list of ShorteningRegion for message shortening
        
    def show(self, message, choices, callback, enable_shift_modifier=False, shortening_regions=None):
        """Show a quick choice dialog
        
        Args:
            message: The message to display
            choices: List of choice dictionaries with format:
                     [{"text": "Yes", "key": "y", "value": True}, 
                      {"text": "No", "key": "n", "value": False},
                      {"text": "Cancel", "key": "c", "value": None}]
            callback: Function to call with the selected choice's value
            enable_shift_modifier: If True, Shift key applies choice to all remaining items
            shortening_regions: Optional list of ShorteningRegion for intelligent message shortening.
                              If None, default right abbreviation is used when message is too long.
        """
        self.is_active = True
        self.message = message
        self.choices = choices
        self.callback = callback
        self.selected = 0  # Default to first choice
        self.enable_shift_modifier = enable_shift_modifier
        self.shortening_regions = shortening_regions
        
    def exit(self):
        """Exit quick choice mode"""
        self.is_active = False
        self.message = ""
        self.choices = []
        self.callback = None
        self.selected = 0
        self.enable_shift_modifier = False
        self.shortening_regions = None
        
    def handle_input(self, event):
        """Handle input while in quick choice mode
        
        Args:
            event: KeyEvent from TTK renderer
            
        Returns:
            Tuple of (action, value, apply_to_all) where:
            - action: 'cancel', 'selection_changed', 'execute', or False
            - value: The choice value or None
            - apply_to_all: True if Shift modifier was pressed
        """
        if event.key_code == KeyCode.ESCAPE:
            return ('cancel', None, False)
            
        elif event.key_code == KeyCode.LEFT:
            # Move selection left
            if self.choices:
                self.selected = (self.selected - 1) % len(self.choices)
                return ('selection_changed', None, False)
            return (True, None, False)
            
        elif event.key_code == KeyCode.RIGHT:
            # Move selection right
            if self.choices:
                self.selected = (self.selected + 1) % len(self.choices)
                return ('selection_changed', None, False)
            return (True, None, False)
            
        elif event.key_code == KeyCode.ENTER:
            # Execute selected action
            # Check if Shift modifier is pressed (only if enabled)
            apply_to_all = False
            if self.enable_shift_modifier:
                from ttk import ModifierKey
                apply_to_all = hasattr(event, 'modifiers') and (event.modifiers & ModifierKey.SHIFT)
            
            if self.choices and 0 <= self.selected < len(self.choices):
                selected_choice = self.choices[self.selected]
                return ('execute', selected_choice["value"], apply_to_all)
            return ('execute', None, False)
            
        else:
            # Check for quick key matches with character input (only from KeyEvent)
            if isinstance(event, KeyEvent) and event.char:
                # Check if Shift modifier is pressed (only if enabled)
                apply_to_all = False
                if self.enable_shift_modifier:
                    from ttk import ModifierKey
                    apply_to_all = hasattr(event, 'modifiers') and (event.modifiers & ModifierKey.SHIFT)
                
                key_char = event.char.lower()
                for choice in self.choices:
                    if "key" in choice and choice["key"] and choice["key"].lower() == key_char:
                        # Found matching quick key
                        return ('execute', choice["value"], apply_to_all)
        
        return (False, None, False)
        
    def draw(self, status_y, width):
        """Draw the quick choice bar in the status line
        
        Args:
            status_y: Y coordinate of the status line
            width: Screen width
        """
        if not self.renderer:
            return
        
        # Get status color
        status_color_pair, status_attributes = get_status_color()
        
        # Fill entire status line with background color
        status_line = " " * width
        self.renderer.draw_text(status_y, 0, status_line, status_color_pair, status_attributes)
        
        # Calculate space needed for buttons
        # Generate help text based on available quick keys (for later use)
        quick_keys = []
        for choice in self.choices:
            if "key" in choice and choice["key"]:
                quick_keys.append(choice["key"].upper())
        
        help_parts = ["←→:select", "Enter:confirm"]
        if self.enable_shift_modifier:
            help_parts.append("Shift:all")
        if quick_keys:
            help_parts.append(f"{'/'.join(quick_keys)}:quick")
        help_parts.append("ESC:cancel")
        help_text = " ".join(help_parts)
        help_text_width = calculate_display_width(help_text)
        
        # Calculate button widths
        button_widths = []
        for i, choice in enumerate(self.choices):
            choice_text = choice["text"]
            if i == self.selected:
                button_text = f"[{choice_text}]"
            else:
                button_text = f" {choice_text} "
            button_widths.append(calculate_display_width(button_text))
        
        total_button_width = sum(button_widths) + len(button_widths) - 1  # Add spacing between buttons
        
        # Priority: Message > Buttons > Help text
        # Calculate available width for message WITHOUT reserving space for help text
        # Format: "  <message> <buttons>"
        reserved_width_without_help = 2 + 1 + total_button_width + 4
        available_message_width = max(1, width - reserved_width_without_help)
        
        # Shorten message if needed using reduce_width with optional regions
        message = self.message
        message_width = calculate_display_width(message)
        
        if message_width > available_message_width:
            if self.shortening_regions:
                # Use provided shortening regions
                message = reduce_width(message, available_message_width, regions=self.shortening_regions)
            else:
                # Use default right abbreviation
                message = reduce_width(message, available_message_width, default_position='right')
        
        # Draw message
        message_with_space = f"{message} "
        self.renderer.draw_text(status_y, 2, message_with_space, status_color_pair, status_attributes)
        
        # Calculate button start position based on actual message width
        button_start_x = 2 + calculate_display_width(message_with_space) + 2
        
        # Draw buttons
        for i, choice in enumerate(self.choices):
            choice_text = choice["text"]
            if i == self.selected:
                # Highlight selected option with bold and standout
                button_text = f"[{choice_text}]"
                self.renderer.draw_text(status_y, button_start_x, button_text, 
                                      status_color_pair, 
                                      TextAttribute.BOLD | TextAttribute.REVERSE)
            else:
                button_text = f" {choice_text} "
                self.renderer.draw_text(status_y, button_start_x, button_text, status_color_pair, status_attributes)
            
            button_start_x += button_widths[i] + 1  # Move to next button position
        
        # Now check if help text fits in the remaining space
        # Help text needs: help_text_width + 3 (spacing) + 2 (minimum gap after buttons)
        help_x = width - help_text_width - 3
        if help_x > button_start_x + 2:
            # Help text fits, draw it
            self.renderer.draw_text(status_y, help_x, help_text, 
                                  status_color_pair, status_attributes)


class QuickChoiceBarHelpers:
    """Helper functions for common quick choice bar use cases"""
    
    @staticmethod
    def create_yes_no_choices():
        """Create standard Yes/No choices (ESC to cancel)
        
        Returns:
            List of choice dictionaries for Yes/No
        """
        return [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False}
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
    def show_yes_no_confirmation(quick_choice_bar, message, callback, shortening_regions=None):
        """Show a Yes/No confirmation dialog (ESC to cancel)
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            message: Message to display
            callback: Function to call with result (True/False/None)
                     - True: User selected Yes
                     - False: User selected No
                     - None: User pressed ESC to cancel
            shortening_regions: Optional list of ShorteningRegion for intelligent message shortening
        """
        choices = QuickChoiceBarHelpers.create_yes_no_choices()
        quick_choice_bar.show(message, choices, callback, shortening_regions=shortening_regions)
    
    @staticmethod
    def show_overwrite_dialog(quick_choice_bar, filename, callback, shortening_regions=None):
        """Show a file overwrite dialog
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            filename: Name of the file that would be overwritten
            callback: Function to call with result ("overwrite"/"skip"/"rename"/None)
            shortening_regions: Optional list of ShorteningRegion for intelligent message shortening
        """
        message = f"File '{filename}' already exists. What do you want to do?"
        choices = QuickChoiceBarHelpers.create_overwrite_choices()
        quick_choice_bar.show(message, choices, callback, shortening_regions=shortening_regions)
    
    @staticmethod
    def show_delete_confirmation(quick_choice_bar, items, callback, shortening_regions=None):
        """Show a delete confirmation dialog
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            items: List of items to delete or count of items
            callback: Function to call with result (True/False)
            shortening_regions: Optional list of ShorteningRegion for intelligent message shortening
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
        quick_choice_bar.show(message, choices, callback, shortening_regions=shortening_regions)
    
    @staticmethod
    def show_error_dialog(quick_choice_bar, error_message, callback=None, shortening_regions=None):
        """Show an error dialog with OK button
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            error_message: Error message to display
            callback: Optional callback function
            shortening_regions: Optional list of ShorteningRegion for intelligent message shortening
        """
        message = f"Error: {error_message}"
        choices = [{"text": "OK", "key": "o", "value": True}]
        
        def error_callback(result):
            if callback:
                callback(result)
        
        quick_choice_bar.show(message, choices, error_callback, shortening_regions=shortening_regions)
    
    @staticmethod
    def show_info_dialog(quick_choice_bar, info_message, callback=None, shortening_regions=None):
        """Show an info dialog with OK button
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            info_message: Info message to display
            callback: Optional callback function
            shortening_regions: Optional list of ShorteningRegion for intelligent message shortening
        """
        choices = [{"text": "OK", "key": "o", "value": True}]
        
        def info_callback(result):
            if callback:
                callback(result)
        
        quick_choice_bar.show(info_message, choices, info_callback, shortening_regions=shortening_regions)