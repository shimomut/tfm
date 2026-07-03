#!/usr/bin/env python3
"""
Demo: Status Bar Dynamic Key Bindings

This demo shows how the status bar help message dynamically reflects
the actual key bindings from the configuration, rather than using
hard-coded values.

The status bar displays:
- help key (default: ?)
- switch_pane key (default: TAB)
- open_item key (default: ENTER)
- quit key (default: Q)

These are now pulled from the config at runtime, so if a user customizes
their key bindings, the status bar will automatically show the correct keys.
"""

from tfm_config import get_keys_for_action, format_key_for_display


def main():
    print("Status Bar Dynamic Key Bindings Demo")
    print("=" * 60)
    print()
    
    # Show the actions displayed in the status bar
    actions = [
        ('help', 'Show help dialog'),
        ('switch_pane', 'Switch between panes'),
        ('open_item', 'Open file/directory'),
        ('quit', 'Exit application')
    ]
    
    print("Current key bindings shown in status bar:")
    print()
    
    for action, description in actions:
        keys, selection_req = get_keys_for_action(action)
        if keys:
            formatted_key = format_key_for_display(keys[0])
            print(f"  {action:20s} → {formatted_key:10s} ({description})")
        else:
            print(f"  {action:20s} → Not configured")
    
    print()
    print("Status bar message construction:")
    print()
    
    # Build the status bar message exactly as done in tfm_main.py
    help_keys, _ = get_keys_for_action('help')
    help_key = format_key_for_display(help_keys[0]) if help_keys else '?'
    
    switch_keys, _ = get_keys_for_action('switch_pane')
    switch_key = format_key_for_display(switch_keys[0]) if switch_keys else 'Tab'
    
    open_keys, _ = get_keys_for_action('open_item')
    open_key = format_key_for_display(open_keys[0]) if open_keys else 'Enter'
    
    quit_keys, _ = get_keys_for_action('quit')
    quit_key = format_key_for_display(quit_keys[0]) if quit_keys else 'q'
    
    controls = f"Press {help_key} for help  •  {switch_key}:switch panes  •  {open_key}:open  •  {quit_key}:quit"
    
    print(f"  \"{controls}\"")
    print()
    
    print("Benefits:")
    print("  ✓ Status bar automatically reflects user's custom key bindings")
    print("  ✓ No need to manually update hard-coded strings")
    print("  ✓ Consistent with the help dialog and actual behavior")
    print()


if __name__ == '__main__':
    main()
