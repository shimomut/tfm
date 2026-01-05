#!/usr/bin/env python3
"""
TUI File Manager - Quick Choice Bar Component
Provides quick choice dialog functionality displayed in the status bar
"""

from ttk import KeyCode, TextAttribute, KeyEvent, CharEvent
from tfm_colors import get_status_color
from tfm_text_layout import (
    draw_text_segments, AbbreviationSegment, AsIsSegment, SpacerSegment, 
    AllOrNothingSegment, TextSegment
)
from typing import Union, List


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
        self.shortening_regions = None  # Deprecated: kept for backward compatibility
        
    def show(self, message, choices, callback, enable_shift_modifier=False, shortening_regions=None):
        """Show a quick choice dialog
        
        Args:
            message: The message to display. Can be either:
                    - str: Plain text message (will be converted to AbbreviationSegment)
                    - List[TextSegment]: List of text segments for advanced formatting
            choices: List of choice dictionaries with format:
                     [{"text": "Yes", "key": "y", "value": True}, 
                      {"text": "No", "key": "n", "value": False},
                      {"text": "Cancel", "key": "c", "value": None}]
            callback: Function to call with the selected choice's value
            enable_shift_modifier: If True, Shift key applies choice to all remaining items
            shortening_regions: Deprecated parameter, kept for backward compatibility.
                              Message shortening is now handled automatically by the text layout system.
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
        
        # Build segments list for the entire status bar
        segments = []
        
        # Add leading spaces
        segments.append(AsIsSegment("  "))
        
        # Add message segment(s)
        # Message can be either a string or a list of TextSegment objects
        if isinstance(self.message, str):
            # String message: convert to AbbreviationSegment with priority-based shortening
            # If shortening_regions provided, use middle abbreviation
            # Otherwise, use right abbreviation
            if self.shortening_regions:
                # Note: shortening_regions is legacy API, we'll use middle abbreviation
                # as a reasonable default for messages with regions
                segments.append(AbbreviationSegment(
                    self.message,
                    priority=0,  # Lower priority than help text (preserved more)
                    min_length=10,
                    abbrev_position='middle'
                ))
            else:
                segments.append(AbbreviationSegment(
                    self.message,
                    priority=0,  # Lower priority than help text (preserved more)
                    min_length=10,
                    abbrev_position='right'
                ))
        elif isinstance(self.message, list):
            # List of TextSegment objects: use them directly
            segments.extend(self.message)
        else:
            # Fallback: convert to string and use as AbbreviationSegment
            segments.append(AbbreviationSegment(
                str(self.message),
                priority=0,
                min_length=10,
                abbrev_position='right'
            ))
        
        # Add space after message
        segments.append(AsIsSegment(" "))
        
        # Add spacer before buttons
        segments.append(SpacerSegment())
        
        # Add button segments
        for i, choice in enumerate(self.choices):
            choice_text = choice["text"]
            
            if i == self.selected:
                # Selected button with brackets and highlighting
                button_text = f"[{choice_text}]"
                segments.append(AsIsSegment(
                    button_text,
                    color_pair=status_color_pair,
                    attributes=TextAttribute.BOLD | TextAttribute.REVERSE
                ))
            else:
                # Unselected button with spaces
                button_text = f" {choice_text} "
                segments.append(AsIsSegment(button_text))
            
            # Add space between buttons (except after last button)
            if i < len(self.choices) - 1:
                segments.append(AsIsSegment(" "))
        
        # Add spacer before help text
        segments.append(SpacerSegment())
        
        # Generate help text based on available quick keys
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
        
        # Add help text segment with all-or-nothing strategy (shown in full or not at all)
        segments.append(AllOrNothingSegment(
            help_text,
            priority=1  # Higher priority, removed before message
        ))
        
        # Add trailing spaces
        segments.append(AsIsSegment("   "))
        
        # Use text layout system to render all segments
        draw_text_segments(
            self.renderer,
            row=status_y,
            col=0,
            segments=segments,
            rendering_width=width,
            default_color=status_color_pair,
            default_attributes=status_attributes
        )


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
    def show_yes_no_confirmation(quick_choice_bar, message, callback):
        """Show a Yes/No confirmation dialog (ESC to cancel)
        
        Args:
            quick_choice_bar: QuickChoiceBar instance
            message: Message to display. Can be either:
                    - str: Plain text message
                    - List[TextSegment]: List of text segments for advanced formatting
            callback: Function to call with result (True/False/None)
                     - True: User selected Yes
                     - False: User selected No
                     - None: User pressed ESC to cancel
        """
        choices = QuickChoiceBarHelpers.create_yes_no_choices()
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