#!/usr/bin/env python3
"""
Demo script showing the extended KEY_BINDINGS format with selection requirements.

This demo shows how key bindings can be configured to work only when files are
selected, only when no files are selected, or regardless of selection status.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_key_bindings import KeyBindingManager
from _config import Config


def demo_key_bindings_selection():
    """Demonstrate the extended key bindings format."""
    
    print("=== TFM Extended Key Bindings Demo ===\n")
    
    # Show the different formats
    print("1. Key Binding Formats:")
    print("   Simple format:   'action': ['key1', 'key2']")
    print("   Extended format: 'action': {'keys': ['key1', 'key2'], 'selection': 'required|none|any'}")
    print()
    
    # Show examples of each selection requirement
    print("2. Selection Requirements:")
    groups = KeyBindingManager.get_actions_by_selection_requirement()
    
    print(f"   'any' (works regardless of selection): {len(groups['any'])} actions")
    for action in sorted(groups['any'])[:5]:  # Show first 5
        keys = KeyBindingManager.get_keys_for_action(action)
        print(f"     - {action}: {keys}")
    if len(groups['any']) > 5:
        print(f"     ... and {len(groups['any']) - 5} more")
    print()
    
    print(f"   'required' (only when files selected): {len(groups['required'])} actions")
    for action in sorted(groups['required']):
        keys = KeyBindingManager.get_keys_for_action(action)
        print(f"     - {action}: {keys}")
    print()
    
    print(f"   'none' (only when no files selected): {len(groups['none'])} actions")
    for action in sorted(groups['none']):
        keys = KeyBindingManager.get_keys_for_action(action)
        print(f"     - {action}: {keys}")
    print()
    
    # Demonstrate availability based on selection status
    print("3. Action Availability Simulation:")
    
    test_actions = ['quit', 'copy_files', 'delete_files', 'help', 'create_archive']
    
    print("\n   When NO files are selected:")
    for action in test_actions:
        available = KeyBindingManager.is_action_available(action, False)
        requirement = KeyBindingManager.get_selection_requirement(action)
        keys = KeyBindingManager.get_keys_for_action(action)
        status = "✓ Available" if available else "✗ Not available"
        print(f"     {action} ({keys}) [{requirement}]: {status}")
    
    print("\n   When files ARE selected:")
    for action in test_actions:
        available = KeyBindingManager.is_action_available(action, True)
        requirement = KeyBindingManager.get_selection_requirement(action)
        keys = KeyBindingManager.get_keys_for_action(action)
        status = "✓ Available" if available else "✗ Not available"
        print(f"     {action} ({keys}) [{requirement}]: {status}")
    
    # Show key mapping differences
    print("\n4. Key Mapping Differences:")
    
    all_keys = KeyBindingManager.get_key_to_action_mapping()
    no_selection_keys = KeyBindingManager.get_key_to_action_mapping(False)
    with_selection_keys = KeyBindingManager.get_key_to_action_mapping(True)
    
    print(f"   Total key mappings: {len(all_keys)}")
    print(f"   Available with no selection: {len(no_selection_keys)}")
    print(f"   Available with selection: {len(with_selection_keys)}")
    
    # Show keys that are only available in certain contexts
    only_with_selection = set(with_selection_keys.keys()) - set(no_selection_keys.keys())
    only_without_selection = set(no_selection_keys.keys()) - set(with_selection_keys.keys())
    
    if only_with_selection:
        print(f"\n   Keys only available WITH selection: {sorted(only_with_selection)}")
        for key in sorted(only_with_selection)[:3]:  # Show first 3
            action = with_selection_keys[key]
            print(f"     '{key}' -> {action}")
    
    if only_without_selection:
        print(f"\n   Keys only available WITHOUT selection: {sorted(only_without_selection)}")
        for key in sorted(only_without_selection)[:3]:  # Show first 3
            action = no_selection_keys[key]
            print(f"     '{key}' -> {action}")
    
    # Validate configuration
    print("\n5. Configuration Validation:")
    is_valid, errors = KeyBindingManager.validate_key_bindings()
    if is_valid:
        print("   ✓ Key bindings configuration is valid")
    else:
        print("   ✗ Key bindings configuration has errors:")
        for error in errors:
            print(f"     - {error}")
    
    print("\n=== Demo Complete ===")


if __name__ == '__main__':
    demo_key_bindings_selection()