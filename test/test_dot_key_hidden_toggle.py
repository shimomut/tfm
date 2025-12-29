"""
Test script to verify that the dot (.) key toggles hidden files visibility

Run with: PYTHONPATH=.:src:ttk pytest test/test_dot_key_hidden_toggle.py -v
"""

from tfm_config import get_config, is_key_bound_to

def test_dot_key_binding():
    """Test that the dot key is bound to toggle_hidden action"""
    print("Testing dot key binding for hidden files toggle...")
    
    # Test that '.' is bound to toggle_hidden
    is_bound = is_key_bound_to('.', 'toggle_hidden')
    print(f"Is '.' key bound to 'toggle_hidden'? {is_bound}")
    
    # Test that 'H' is no longer bound to toggle_hidden
    is_h_bound = is_key_bound_to('H', 'toggle_hidden')
    print(f"Is 'H' key bound to 'toggle_hidden'? {is_h_bound}")
    
    # Get the configuration to verify
    config = get_config()
    if hasattr(config, 'KEY_BINDINGS') and 'toggle_hidden' in config.KEY_BINDINGS:
        bound_keys = config.KEY_BINDINGS['toggle_hidden']
        print(f"Keys bound to 'toggle_hidden': {bound_keys}")
    
    # Verify the expected behavior
    assert is_bound, "The '.' key should be bound to toggle_hidden"
    assert not is_h_bound, "The 'H' key should no longer be bound to toggle_hidden"
    
    print("✓ Test passed: Dot key is correctly bound to toggle hidden files")
