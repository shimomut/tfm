#!/usr/bin/env python3
"""
Demo of the unified key bindings approach where users can configure
selection requirements for any action through the Config class.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def demo_unified_approach():
    """Demonstrate the unified key bindings approach."""
    
    print("=== Unified Key Bindings Demo ===\n")
    
    print("1. User Configuration Flexibility")
    print("   Users can now configure selection requirements for ANY action:")
    print()
    
    # Show example configuration
    example_config = """
    KEY_BINDINGS = {
        # Traditional format (defaults to 'any')
        'quit': ['q', 'Q'],
        'help': ['?'],
        
        # File operations requiring selection
        'copy_files': {'keys': ['c', 'C'], 'selection': 'required'},
        'delete_files': {'keys': ['k', 'K'], 'selection': 'required'},
        
        # User customization: make view_text require selection
        'view_text': {'keys': ['v', 'V'], 'selection': 'required'},
        
        # User customization: make create_file only work when nothing selected
        'create_file': {'keys': ['E'], 'selection': 'none'},
        
        # User customization: make search_dialog require no selection
        'search_dialog': {'keys': ['F'], 'selection': 'none'},
        
        # Explicit 'any' (works regardless of selection)
        'search': {'keys': ['f'], 'selection': 'any'},
    }
    """
    
    print("   Example user configuration:")
    print(example_config)
    
    print("\n2. Unified Implementation")
    print("   TFM now uses a single is_key_for_action() method that:")
    print("   - Automatically checks key binding")
    print("   - Automatically checks selection requirements")
    print("   - Works for ALL actions based on their configuration")
    print()
    
    # Demonstrate with actual code
    from tfm_config import ConfigManager
    
    # Create custom config for demo
    class DemoConfig:
        KEY_BINDINGS = {
            'quit': ['q', 'Q'],  # Simple format - works always
            'copy_files': {'keys': ['c', 'C'], 'selection': 'required'},
            'view_text': {'keys': ['v', 'V'], 'selection': 'required'},  # User customized
            'create_file': {'keys': ['E'], 'selection': 'none'},  # User customized
            'search': {'keys': ['f'], 'selection': 'any'},  # Explicit any
        }
    
    config_manager = ConfigManager()
    config_manager.config = DemoConfig()
    
    print("3. Live Demo with Custom Configuration")
    print()
    
    # Simulate file manager with unified method
    class DemoFileManager:
        def __init__(self, config_manager):
            self.config_manager = config_manager
            self.left_pane = {'selected_files': set()}
            self.active_pane = 'left'
        
        def get_current_pane(self):
            return self.left_pane
        
        def is_key_for_action(self, key, action):
            """Unified method - automatically respects selection requirements."""
            if 32 <= key <= 126:  # Printable ASCII
                key_char = chr(key)
                current_pane = self.get_current_pane()
                has_selection = len(current_pane['selected_files']) > 0
                return self.config_manager.is_key_bound_to_action_with_selection(key_char, action, has_selection)
            return False
    
    fm = DemoFileManager(config_manager)
    
    # Test scenarios
    scenarios = [
        ("No files selected", set()),
        ("Files selected", {'/path/file1.txt', '/path/file2.txt'})
    ]
    
    test_actions = [
        ('q', 'quit', 'Always works'),
        ('c', 'copy_files', 'Requires selection'),
        ('v', 'view_text', 'User configured to require selection'),
        ('E', 'create_file', 'User configured to require no selection'),
        ('f', 'search', 'Explicit any - always works'),
    ]
    
    for scenario_name, selected_files in scenarios:
        print(f"   Scenario: {scenario_name}")
        fm.left_pane['selected_files'] = selected_files
        
        for key_char, action, description in test_actions:
            available = fm.is_key_for_action(ord(key_char), action)
            requirement = config_manager.get_selection_requirement(action)
            status = "✓" if available else "✗"
            print(f"     '{key_char}' -> {action} [{requirement}]: {status} ({description})")
        print()
    
    print("4. Benefits of Unified Approach")
    benefits = [
        "✅ Single method handles all key binding logic",
        "✅ Users can configure ANY action with selection requirements",
        "✅ No need to manually choose between different methods",
        "✅ Automatic selection requirement enforcement",
        "✅ Backward compatible with existing configurations",
        "✅ Consistent behavior across all actions",
        "✅ Easy to understand and maintain"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print("\n5. Developer Experience")
    print("   Before (manual selection of methods):")
    print("     elif self.is_key_for_action(key, 'quit'):")
    print("     elif self.is_key_for_action_with_selection(key, 'copy_files'):")
    print("     elif self.is_key_for_action(key, 'search'):")
    print()
    print("   After (unified approach):")
    print("     elif self.is_key_for_action(key, 'quit'):")
    print("     elif self.is_key_for_action(key, 'copy_files'):")
    print("     elif self.is_key_for_action(key, 'search'):")
    print("     # All methods automatically respect selection requirements!")
    
    print("\n=== Unified Key Bindings Demo Complete ===")


if __name__ == '__main__':
    demo_unified_approach()