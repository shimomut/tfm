#!/usr/bin/env python3
"""
Demo showing the migration from hardcoded directory creation to proper key bindings.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def demo_create_directory_migration():
    """Demonstrate the create_directory key binding migration."""
    
    print("=== Create Directory Key Binding Migration Demo ===\n")
    
    print("1. Problem: Hardcoded Directory Creation")
    print("   Before this change:")
    print("   - F7 was mentioned in help but not in KEY_BINDINGS")
    print("   - Directory creation was hardcoded in move_selected_files()")
    print("   - When no files selected, 'm' would create directory instead of moving")
    print("   - Users couldn't customize the key binding")
    print()
    
    print("   Old move_selected_files() behavior:")
    old_code = '''
    def move_selected_files(self):
        """Move selected files to the opposite pane's directory, or create new directory if no files selected"""
        if not current_pane['selected_files']:
            # No files selected - create new directory instead
            self.enter_create_directory_mode()
            return
    '''
    print(old_code)
    
    print("2. Solution: Proper Key Binding System")
    print("   After this change:")
    print("   - create_directory is now a proper action in KEY_BINDINGS")
    print("   - Users can customize the key binding (default: 'D')")
    print("   - move_files now properly requires selection")
    print("   - Separation of concerns: move vs create are different actions")
    print()
    
    # Demonstrate with actual configuration
    from tfm_config import ConfigManager
    from _config import Config
    
    config_manager = ConfigManager()
    config_manager.config = Config()
    
    print("3. Current Configuration")
    
    # Show move_files configuration
    move_keys = config_manager.get_key_for_action('move_files')
    move_req = config_manager.get_selection_requirement('move_files')
    print(f"   move_files: keys={move_keys}, selection={move_req}")
    
    # Show create_directory configuration
    create_keys = config_manager.get_key_for_action('create_directory')
    create_req = config_manager.get_selection_requirement('create_directory')
    print(f"   create_directory: keys={create_keys}, selection={create_req}")
    
    print()
    print("4. Behavior Demonstration")
    
    # Mock file manager to show behavior
    class MockFileManager:
        def __init__(self, config_manager):
            self.config_manager = config_manager
            self.left_pane = {'selected_files': set()}
            self.active_pane = 'left'
        
        def get_current_pane(self):
            return self.left_pane
        
        def is_key_for_action(self, key, action):
            """Unified method that respects selection requirements."""
            if 32 <= key <= 126:  # Printable ASCII
                key_char = chr(key)
                current_pane = self.get_current_pane()
                has_selection = len(current_pane['selected_files']) > 0
                
                # Use the new API: find_action_for_event
                from ttk import KeyEvent, ModifierKey
                event = KeyEvent(key_code=key, modifiers=ModifierKey.NONE, char=key_char)
                
                from tfm_config import find_action_for_event
                found_action = find_action_for_event(event, has_selection)
                
                return found_action == action
            return False
    
    fm = MockFileManager(config_manager)
    
    scenarios = [
        ("No files selected", set()),
        ("Files selected", {'/path/file1.txt', '/path/file2.txt'})
    ]
    
    actions = [
        ('m', 'move_files', 'Move selected files'),
        ('M', 'move_files', 'Move selected files (uppercase)'),
        ('D', 'create_directory', 'Create new directory'),
    ]
    
    for scenario_name, selected_files in scenarios:
        print(f"\n   Scenario: {scenario_name}")
        fm.left_pane['selected_files'] = selected_files
        
        for key_char, action, description in actions:
            available = fm.is_key_for_action(ord(key_char), action)
            requirement = config_manager.get_selection_requirement(action)
            status = "✓ Available" if available else "✗ Not available"
            print(f"     '{key_char}' -> {action} [{requirement}]: {status}")
    
    print("\n5. Benefits of the Change")
    benefits = [
        "✅ Proper separation of move and create actions",
        "✅ Users can customize create_directory key binding",
        "✅ Consistent with KEY_BINDINGS system design",
        "✅ move_files now has clear, predictable behavior",
        "✅ Help dialog shows actual key binding",
        "✅ No more hidden/hardcoded functionality"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print("\n6. User Customization Example")
    print("   Users can now customize the create_directory key:")
    customization_example = '''
    KEY_BINDINGS = {
        # Use F7-like key (if supported by terminal)
        'create_directory': ['7'],
        
        # Or use a different key entirely
        'create_directory': ['N'],  # 'N' for New directory
        
        # Or even require no selection (only when nothing selected)
        'create_directory': {'keys': ['D'], 'selection': 'none'},
    }
    '''
    print(customization_example)
    
    print("=== Create Directory Migration Demo Complete ===")


if __name__ == '__main__':
    demo_create_directory_migration()