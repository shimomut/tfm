#!/usr/bin/env python3
"""
TFM Key Bindings Utility Module

This module provides utility functions for working with the extended KEY_BINDINGS format
that supports optional file selection status requirements.
"""

from _config import Config


class KeyBindingManager:
    """Manager for handling key bindings with selection requirements."""
    
    @staticmethod
    def get_keys_for_action(action):
        """
        Get keys for an action, handling both simple and extended formats.
        
        Args:
            action (str): The action name
            
        Returns:
            list: List of keys bound to the action, empty list if action not found
        """
        binding = Config.KEY_BINDINGS.get(action)
        if isinstance(binding, list):
            return binding
        elif isinstance(binding, dict) and 'keys' in binding:
            return binding['keys']
        return []
    
    @staticmethod
    def get_selection_requirement(action):
        """
        Get selection requirement for an action.
        
        Args:
            action (str): The action name
            
        Returns:
            str: Selection requirement ('any', 'required', 'none')
        """
        binding = Config.KEY_BINDINGS.get(action)
        if isinstance(binding, dict) and 'selection' in binding:
            return binding['selection']
        return 'any'  # default for simple format
    
    @staticmethod
    def is_action_available(action, has_selection):
        """
        Check if action is available based on current selection status.
        
        Args:
            action (str): The action name
            has_selection (bool): Whether there are currently selected items
            
        Returns:
            bool: True if action is available, False otherwise
        """
        requirement = KeyBindingManager.get_selection_requirement(action)
        if requirement == 'required':
            return has_selection
        elif requirement == 'none':
            return not has_selection
        else:  # 'any'
            return True
    
    @staticmethod
    def get_available_actions(has_selection):
        """
        Get all actions that are available based on current selection status.
        
        Args:
            has_selection (bool): Whether there are currently selected items
            
        Returns:
            list: List of available action names
        """
        available_actions = []
        for action in Config.KEY_BINDINGS.keys():
            if KeyBindingManager.is_action_available(action, has_selection):
                available_actions.append(action)
        return available_actions
    
    @staticmethod
    def get_key_to_action_mapping(has_selection=None):
        """
        Get a mapping from keys to actions, optionally filtered by selection status.
        
        Args:
            has_selection (bool, optional): Filter by selection status. 
                                          If None, includes all actions.
            
        Returns:
            dict: Mapping from key to action name
        """
        key_to_action = {}
        for action, binding in Config.KEY_BINDINGS.items():
            # Skip if not available for current selection status
            if has_selection is not None and not KeyBindingManager.is_action_available(action, has_selection):
                continue
                
            keys = KeyBindingManager.get_keys_for_action(action)
            for key in keys:
                key_to_action[key] = action
        return key_to_action
    
    @staticmethod
    def validate_key_bindings():
        """
        Validate the KEY_BINDINGS configuration.
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        valid_selections = {'any', 'required', 'none'}
        
        for action, binding in Config.KEY_BINDINGS.items():
            if isinstance(binding, list):
                # Simple format validation
                if not binding:
                    errors.append(f"Action '{action}' has empty key list")
                for key in binding:
                    if not isinstance(key, str):
                        errors.append(f"Action '{action}' has non-string key: {key}")
            elif isinstance(binding, dict):
                # Extended format validation
                if 'keys' not in binding:
                    errors.append(f"Action '{action}' missing 'keys' field")
                elif not isinstance(binding['keys'], list):
                    errors.append(f"Action '{action}' 'keys' field must be a list")
                elif not binding['keys']:
                    errors.append(f"Action '{action}' has empty keys list")
                else:
                    for key in binding['keys']:
                        if not isinstance(key, str):
                            errors.append(f"Action '{action}' has non-string key: {key}")
                
                if 'selection' not in binding:
                    errors.append(f"Action '{action}' missing 'selection' field")
                elif binding['selection'] not in valid_selections:
                    errors.append(f"Action '{action}' has invalid selection value: '{binding['selection']}'")
            else:
                errors.append(f"Action '{action}' has invalid binding format: {type(binding)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_actions_by_selection_requirement():
        """
        Group actions by their selection requirements.
        
        Returns:
            dict: Dictionary with keys 'any', 'required', 'none' containing lists of actions
        """
        groups = {'any': [], 'required': [], 'none': []}
        
        for action in Config.KEY_BINDINGS.keys():
            requirement = KeyBindingManager.get_selection_requirement(action)
            groups[requirement].append(action)
        
        return groups


# Convenience functions for backward compatibility
def get_keys_for_action(action):
    """Get keys for an action."""
    return KeyBindingManager.get_keys_for_action(action)


def is_action_available(action, has_selection):
    """Check if action is available based on selection status."""
    return KeyBindingManager.is_action_available(action, has_selection)


def get_key_to_action_mapping(has_selection=None):
    """Get key to action mapping."""
    return KeyBindingManager.get_key_to_action_mapping(has_selection)