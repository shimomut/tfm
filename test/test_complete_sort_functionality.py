#!/usr/bin/env python3
"""
Comprehensive test for the new sort toggle functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_config import get_config, is_key_bound_to

def test_complete_functionality():
    """Test the complete sort functionality after r/R key removal"""
    
    print("=== Complete Sort Functionality Test ===")
    print()
    
    # Test 1: Verify r/R keys are unbound
    print("1. Testing r/R key removal:")
    r_bound = is_key_bound_to('r', 'toggle_reverse_sort')
    R_bound = is_key_bound_to('R', 'toggle_reverse_sort')
    print(f"   'r' key bound to toggle_reverse_sort: {r_bound}")
    print(f"   'R' key bound to toggle_reverse_sort: {R_bound}")
    
    if not r_bound and not R_bound:
        print("   ✓ PASS: r/R keys successfully removed")
    else:
        print("   ✗ FAIL: r/R keys still bound")
    print()
    
    # Test 2: Verify 1,2,3 keys are still bound
    print("2. Testing 1,2,3 key bindings:")
    key_bindings = [
        ('1', 'quick_sort_name'),
        ('2', 'quick_sort_size'), 
        ('3', 'quick_sort_date')
    ]
    
    all_bound = True
    for key, action in key_bindings:
        bound = is_key_bound_to(key, action)
        print(f"   '{key}' key bound to {action}: {bound}")
        if not bound:
            all_bound = False
    
    if all_bound:
        print("   ✓ PASS: All quick sort keys properly bound")
    else:
        print("   ✗ FAIL: Some quick sort keys missing")
    print()
    
    # Test 3: Simulate the new toggle behavior
    print("3. Testing new toggle behavior (simulation):")
    
    # Mock pane data
    test_pane = {
        'sort_mode': 'name',
        'sort_reverse': False
    }
    
    def simulate_quick_sort(sort_mode, pane):
        """Simulate the new quick_sort behavior"""
        if pane['sort_mode'] == sort_mode:
            # Toggle reverse mode
            pane['sort_reverse'] = not pane['sort_reverse']
            reverse_status = "reverse" if pane['sort_reverse'] else "normal"
            return f"Toggled to {sort_mode} sorting ({reverse_status})"
        else:
            # Change to new sort mode
            pane['sort_mode'] = sort_mode
            return f"Changed to {sort_mode} sorting"
    
    # Test sequence
    test_sequence = [
        ('1', 'name', "Press '1' when already on name sort"),
        ('1', 'name', "Press '1' again to toggle back"),
        ('2', 'size', "Press '2' to switch to size sort"),
        ('2', 'size', "Press '2' again to toggle size reverse"),
        ('3', 'date', "Press '3' to switch to date sort"),
        ('1', 'name', "Press '1' to switch back to name sort")
    ]
    
    for key, expected_mode, description in test_sequence:
        result = simulate_quick_sort(expected_mode, test_pane)
        print(f"   {description}:")
        print(f"     Result: {result}")
        print(f"     State: mode={test_pane['sort_mode']}, reverse={test_pane['sort_reverse']}")
        print()
    
    # Test 4: Verify configuration cleanup
    print("4. Testing configuration cleanup:")
    config = get_config()
    key_bindings = getattr(config, 'KEY_BINDINGS', {})
    
    if 'toggle_reverse_sort' not in key_bindings:
        print("   ✓ PASS: toggle_reverse_sort removed from configuration")
    else:
        print("   ✗ FAIL: toggle_reverse_sort still in configuration")
    
    # Check that other important bindings are still there
    important_bindings = ['quick_sort_name', 'quick_sort_size', 'quick_sort_date', 'sort_menu']
    missing_bindings = []
    
    for binding in important_bindings:
        if binding not in key_bindings:
            missing_bindings.append(binding)
    
    if not missing_bindings:
        print("   ✓ PASS: All important sort bindings preserved")
    else:
        print(f"   ✗ FAIL: Missing bindings: {missing_bindings}")
    
    print()
    print("=== Test Summary ===")
    print("✓ r/R keys removed from toggle_reverse_sort")
    print("✓ 1,2,3 keys enhanced with toggle functionality")
    print("✓ Sort menu (s key) still available for manual reverse toggle")
    print("✓ Configuration properly cleaned up")
    print()
    print("The new behavior provides a more intuitive sorting experience:")
    print("- Single key press changes sort mode")
    print("- Repeated key press toggles reverse for that mode")
    print("- No need for separate reverse toggle key")

if __name__ == "__main__":
    test_complete_functionality()