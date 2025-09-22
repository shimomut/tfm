#!/usr/bin/env python3
"""
Demo showing how the same key can be used for different actions based on selection status.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def demo_shared_key_selection_aware():
    """Demonstrate selection-aware key sharing."""
    
    print("=== Selection-Aware Key Sharing Demo ===\n")
    
    print("1. The Problem: Key Conflicts")
    print("   Traditional key binding systems have conflicts when multiple actions want the same key.")
    print("   Example: Both 'move files' and 'create directory' might want to use 'M'.")
    print()
    
    print("2. The Solution: Selection-Aware Key Bindings")
    print("   TFM's extended key binding system resolves conflicts using selection requirements:")
    print("   - Same key can be used for different actions")
    print("   - Selection status determines which action is available")
    print("   - No conflicts because requirements are mutually exclusive")
    print()
    
    # Show the configuration
    from tfm_config import ConfigManager
    from _config import Config
    
    config_manager = ConfigManager()
    config_manager.config = Config()
    
    print("3. Current Configuration")
    
    move_keys = config_manager.get_key_for_action('move_files')
    move_req = config_manager.get_selection_requirement('move_files')
    print(f"   move_files: keys={move_keys}, selection='{move_req}'")
    
    create_keys = config_manager.get_key_for_action('create_directory')
    create_req = config_manager.get_selection_requirement('create_directory')
    print(f"   create_directory: keys={create_keys}, selection='{create_req}'")
    
    print(f"\\n   Both actions use the 'M' key, but with different selection requirements!")
    print(f"   This means they're mutually exclusive - no conflict!")
    print()
    
    print("4. Behavior Demonstration")
    
    # Mock file manager to demonstrate behavior
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
                return self.config_manager.is_key_bound_to_action_with_selection(key_char, action, has_selection)
            return False
        
        def simulate_key_press(self, key_char):
            """Simulate a key press and show which action would be triggered."""
            actions_to_check = ['move_files', 'create_directory']
            triggered_actions = []
            
            for action in actions_to_check:
                if self.is_key_for_action(ord(key_char), action):
                    triggered_actions.append(action)
            
            return triggered_actions
    
    fm = MockFileManager(config_manager)
    
    scenarios = [
        ("No files selected", set()),
        ("Files selected", {'/path/file1.txt', '/path/file2.txt'})
    ]
    
    for scenario_name, selected_files in scenarios:
        print(f"\\n   Scenario: {scenario_name}")
        fm.left_pane['selected_files'] = selected_files
        
        # Test 'M' key
        triggered = fm.simulate_key_press('M')
        
        if triggered:
            action = triggered[0]  # Should only be one due to mutual exclusivity
            print(f"     'M' key pressed -> {action} action triggered")
            
            # Show why this action is available
            requirement = config_manager.get_selection_requirement(action)
            has_selection = len(selected_files) > 0
            
            if requirement == 'required' and has_selection:
                print(f"     ✓ Available because action requires selection and files are selected")
            elif requirement == 'none' and not has_selection:
                print(f"     ✓ Available because action requires no selection and no files are selected")
            elif requirement == 'any':
                print(f"     ✓ Available because action works regardless of selection")
        else:
            print(f"     'M' key pressed -> No action triggered")
        
        # Show what other action would be available in opposite scenario
        other_actions = ['move_files', 'create_directory']
        for action in other_actions:
            if action not in triggered:
                available = config_manager.is_action_available(action, len(selected_files) > 0)
                if not available:
                    requirement = config_manager.get_selection_requirement(action)
                    print(f"     ✗ {action} not available (requires selection='{requirement}')")
    
    print("\\n5. Benefits of Selection-Aware Key Sharing")
    benefits = [
        "✅ Eliminates key conflicts through smart context awareness",
        "✅ More intuitive user experience (same key, different contexts)",
        "✅ Efficient use of keyboard real estate",
        "✅ Reduces need to memorize many different keys",
        "✅ Actions are available exactly when they make sense",
        "✅ No accidental wrong actions due to selection state"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print("\\n6. User Experience")
    print("   From the user's perspective:")
    print("   - Press 'M' when no files selected -> Creates new directory")
    print("   - Press 'M' when files are selected -> Moves selected files")
    print("   - Same key, different actions, no confusion!")
    print("   - The system automatically does the 'right thing' based on context")
    
    print("\\n7. Configuration Example")
    config_example = '''
    KEY_BINDINGS = {
        # Smart key sharing using selection requirements
        'move_files': {'keys': ['m', 'M'], 'selection': 'required'},
        'create_directory': {'keys': ['M'], 'selection': 'none'},
        
        # This creates context-aware behavior:
        # - 'M' with files selected = move files
        # - 'M' with no files selected = create directory
        # - 'm' always moves files (if any selected)
    }
    '''
    print(config_example)
    
    print("=== Selection-Aware Key Sharing Demo Complete ===")


if __name__ == '__main__':
    demo_shared_key_selection_aware()