"""
Test that "No items to show" message is properly truncated in narrow panes.

Run with: PYTHONPATH=.:src:ttk pytest test/test_empty_directory_narrow_pane.py -v
"""

from ttk.wide_char_utils import truncate_to_width, get_display_width


def test_message_truncation():
    """Test that the message is truncated correctly for narrow panes"""
    print("Testing message truncation for narrow panes...")
    
    message = "No items to show"
    
    # Test various pane widths
    test_cases = [
        {'pane_width': 20, 'expected_max_width': 18},  # usable_width = 20 - 2 = 18
        {'pane_width': 15, 'expected_max_width': 13},  # usable_width = 15 - 2 = 13
        {'pane_width': 10, 'expected_max_width': 8},   # usable_width = 10 - 2 = 8
        {'pane_width': 5, 'expected_max_width': 3},    # usable_width = 5 - 2 = 3
    ]
    
    for case in test_cases:
        pane_width = case['pane_width']
        expected_max_width = case['expected_max_width']
        
        # Simulate the truncation logic from tfm_main.py
        usable_width = pane_width - 2  # Leave 1 column margin on each side
        truncated_message = truncate_to_width(message, usable_width, ellipsis="…")
        
        # Verify truncated message fits within usable width
        actual_width = get_display_width(truncated_message)
        assert actual_width <= usable_width, \
            f"Pane width {pane_width}: truncated message width {actual_width} exceeds usable width {usable_width}"
        
        print(f"  Pane width {pane_width}: '{message}' -> '{truncated_message}' (width: {actual_width}/{usable_width})")
    
    print("✅ Message truncation test passed!")


def test_very_narrow_pane():
    """Test that very narrow panes (width < 3) are handled gracefully"""
    print("\nTesting very narrow pane handling...")
    
    message = "No items to show"
    
    # Test panes that are too narrow
    for pane_width in [1, 2]:
        usable_width = pane_width - 2
        
        # When usable_width < 1, the code should return early
        if usable_width < 1:
            print(f"  Pane width {pane_width}: too narrow, should return early")
            continue
        
        truncated_message = truncate_to_width(message, usable_width, ellipsis="…")
        actual_width = get_display_width(truncated_message)
        
        assert actual_width <= usable_width, \
            f"Pane width {pane_width}: message width {actual_width} exceeds usable width {usable_width}"
    
    print("✅ Very narrow pane test passed!")


def test_message_fits_without_truncation():
    """Test that message is not truncated when pane is wide enough"""
    print("\nTesting message without truncation...")
    
    message = "No items to show"
    message_width = get_display_width(message)
    
    # Test pane widths where message should fit without truncation
    for pane_width in [20, 30, 40, 80]:
        usable_width = pane_width - 2
        
        if usable_width >= message_width:
            truncated_message = truncate_to_width(message, usable_width, ellipsis="…")
            
            # Message should be unchanged
            assert truncated_message == message, \
                f"Pane width {pane_width}: message should not be truncated when it fits"
            
            print(f"  Pane width {pane_width}: message fits without truncation")
    
    print("✅ Message fits without truncation test passed!")


if __name__ == '__main__':
    test_message_truncation()
    test_very_narrow_pane()
    test_message_fits_without_truncation()
    print("\n✅ All tests passed!")
