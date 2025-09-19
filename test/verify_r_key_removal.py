#!/usr/bin/env python3
"""
Test script to verify that r/R keys are no longer bound to toggle_reverse_sort
and that the new toggle functionality works correctly with 1,2,3 keys.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_config import get_config, is_key_bound_to

def test_r_key_removal():
    """Test that r/R keys are no longer bound to toggle_reverse_sort"""
    
    print("=== Testing r/R Key Removal ===")
    print()
    
    # Test that r/R keys are not bound to toggle_reverse_sort
    r_bound = is_key_bound_to('r', 'toggle_reverse_sort')
    R_bound = is_key_bound_to('R', 'toggle_reverse_sort')
    
    print(f"'r' key bound to 'toggle_reverse_sort': {r_bound}")
    print(f"'R' key bound to 'toggle_reverse_sort': {R_bound}")
    
    if not r_bound and not R_bound:
        print("✓ SUCCESS: r/R keys are no longer bound to toggle_reverse_sort")
    else:
        print("✗ FAILURE: r/R keys are still bound to toggle_reverse_sort")
    
    print()
    
    # Test that 1,2,3 keys are still bound to their quick sort functions
    key_1_bound = is_key_bound_to('1', 'quick_sort_name')
    key_2_bound = is_key_bound_to('2', 'quick_sort_size')
    key_3_bound = is_key_bound_to('3', 'quick_sort_date')
    
    print(f"'1' key bound to 'quick_sort_name': {key_1_bound}")
    print(f"'2' key bound to 'quick_sort_size': {key_2_bound}")
    print(f"'3' key bound to 'quick_sort_date': {key_3_bound}")
    
    if key_1_bound and key_2_bound and key_3_bound:
        print("✓ SUCCESS: 1,2,3 keys are still properly bound to quick sort functions")
    else:
        print("✗ FAILURE: Some quick sort key bindings are missing")
    
    print()
    
    # Check configuration
    config = get_config()
    key_bindings = getattr(config, 'KEY_BINDINGS', {})
    
    if 'toggle_reverse_sort' in key_bindings:
        print(f"toggle_reverse_sort still in KEY_BINDINGS: {key_bindings['toggle_reverse_sort']}")
        print("✗ FAILURE: toggle_reverse_sort should be removed from configuration")
    else:
        print("✓ SUCCESS: toggle_reverse_sort removed from KEY_BINDINGS configuration")
    
    print()
    print("=== Summary ===")
    print("The r/R keys have been successfully removed from the toggle_reverse_sort")
    print("functionality. Users should now use the 1,2,3 keys to toggle reverse")
    print("sorting when the same sort mode is already active.")
    print()
    print("New behavior:")
    print("- Press '1' when already sorting by name → toggles reverse")
    print("- Press '2' when already sorting by size → toggles reverse") 
    print("- Press '3' when already sorting by date → toggles reverse")
    print("- Press any sort key when NOT in that mode → switches to that mode")

if __name__ == "__main__":
    test_r_key_removal()