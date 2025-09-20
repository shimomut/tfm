#!/usr/bin/env python3
"""
Test script to verify that the 'h' key is no longer bound to help action
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tfm_config import get_config, is_key_bound_to

def test_h_key_unassigned():
    """Test that the 'h' key is no longer bound to help action"""
    print("Testing that 'h' key is unassigned from help...")
    
    # Test that '?' is still bound to help
    is_question_bound = is_key_bound_to('?', 'help')
    print(f"Is '?' key bound to 'help'? {is_question_bound}")
    
    # Test that 'h' is no longer bound to help
    is_h_bound = is_key_bound_to('h', 'help')
    print(f"Is 'h' key bound to 'help'? {is_h_bound}")
    
    # Get the configuration to verify
    config = get_config()
    if hasattr(config, 'KEY_BINDINGS') and 'help' in config.KEY_BINDINGS:
        bound_keys = config.KEY_BINDINGS['help']
        print(f"Keys bound to 'help': {bound_keys}")
    
    # Verify the expected behavior
    assert is_question_bound, "The '?' key should still be bound to help"
    assert not is_h_bound, "The 'h' key should no longer be bound to help"
    assert bound_keys == ['?'], "Only '?' should be bound to help"
    
    print("✓ Test passed: 'h' key is no longer bound to help, only '?' key remains")

if __name__ == "__main__":
    test_h_key_unassigned()