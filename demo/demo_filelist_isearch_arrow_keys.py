#!/usr/bin/env python3
"""
Demo: File List I-Search Arrow Key Fix

This demo demonstrates that arrow keys and other navigation keys no longer
insert unwanted characters into the I-Search pattern in the file list.

The fix ensures that only printable characters are added to the search pattern,
while navigation keys (LEFT, RIGHT, HOME, END, PAGE_UP, PAGE_DOWN, TAB, DELETE, INSERT)
are explicitly ignored.

To test manually:
1. Run TFM
2. Press '/' to enter I-Search mode in the file list
3. Type some characters (e.g., "test")
4. Press LEFT or RIGHT arrow keys
5. Verify that no unwanted characters are inserted into the search pattern
6. Press ESC to exit I-Search mode

Expected behavior:
- Only printable characters should be added to the search pattern
- Navigation keys should be ignored (no characters inserted)
- UP/DOWN arrows should navigate through matches
- BACKSPACE should remove the last character
- ESC/ENTER should exit I-Search mode

This demo verifies the fix by testing the handle_isearch_input() method directly.
"""

from unittest.mock import Mock, patch
from ttk.input_event import KeyEvent, CharEvent, KeyCode, ModifierKey


def demo_filelist_isearch_arrow_keys():
    """Demonstrate that arrow keys don't insert characters in file list I-Search"""
    from src.tfm_main import FileManager
    
    print("=" * 70)
    print("File List I-Search Arrow Key Fix Demo")
    print("=" * 70)
    print()
    
    # Create mock renderer
    mock_renderer = Mock()
    mock_renderer.get_dimensions.return_value = (24, 80)
    mock_renderer.initialize = Mock()
    mock_renderer.shutdown = Mock()
    mock_renderer.clear = Mock()
    mock_renderer.refresh = Mock()
    mock_renderer.draw_text = Mock()
    mock_renderer.draw_hline = Mock()
    mock_renderer.draw_vline = Mock()
    mock_renderer.set_cursor_visibility = Mock()
    mock_renderer.get_input = Mock()
    
    # Create FileManager with proper mocking
    with patch('tfm_main.get_config'), \
         patch('tfm_main.LogManager'), \
         patch('tfm_main.get_state_manager'), \
         patch('tfm_main.init_colors'):
        
        fm = FileManager(mock_renderer)
        fm.log_height_ratio = 0.25
        
        # Set up isearch mode
        fm.isearch_mode = True
        fm.isearch_pattern = ""
        fm.isearch_matches = []
        fm.isearch_match_index = 0
        
        # Mock methods
        mock_pane = {'focused_index': 0}
        fm.get_current_pane = Mock(return_value=mock_pane)
        fm.adjust_scroll_for_focus = Mock()
        fm.update_isearch_matches = Mock()
        fm.mark_dirty = Mock()
        fm.exit_isearch_mode = Mock()
        
        print("Test 1: Printable characters are added to search pattern")
        print("-" * 70)
        
        # Type "test"
        for char in "test":
            event = CharEvent(char)
            fm.handle_isearch_input(event)
            print(f"  Typed '{char}' -> Pattern: '{fm.isearch_pattern}'")
        
        assert fm.isearch_pattern == "test", "Pattern should be 'test'"
        print("  ✓ Printable characters work correctly")
        print()
        
        print("Test 2: Navigation keys are ignored (no characters inserted)")
        print("-" * 70)
        
        navigation_keys = [
            (KeyCode.LEFT, "LEFT"),
            (KeyCode.RIGHT, "RIGHT"),
            (KeyCode.HOME, "HOME"),
            (KeyCode.END, "END"),
            (KeyCode.PAGE_UP, "PAGE_UP"),
            (KeyCode.PAGE_DOWN, "PAGE_DOWN"),
            (KeyCode.TAB, "TAB"),
            (KeyCode.DELETE, "DELETE"),
            (KeyCode.INSERT, "INSERT"),
        ]
        
        for key_code, key_name in navigation_keys:
            event = KeyEvent(key_code, ModifierKey.NONE, None)
            fm.handle_isearch_input(event)
            print(f"  Pressed {key_name:12} -> Pattern: '{fm.isearch_pattern}'")
            assert fm.isearch_pattern == "test", f"Pattern should still be 'test' after {key_name}"
        
        print("  ✓ All navigation keys are properly ignored")
        print()
        
        print("Test 3: BACKSPACE removes last character")
        print("-" * 70)
        
        event = KeyEvent(KeyCode.BACKSPACE, ModifierKey.NONE, None)
        fm.handle_isearch_input(event)
        print(f"  Pressed BACKSPACE -> Pattern: '{fm.isearch_pattern}'")
        assert fm.isearch_pattern == "tes", "Pattern should be 'tes'"
        print("  ✓ BACKSPACE works correctly")
        print()
        
        print("Test 4: UP/DOWN navigate through matches")
        print("-" * 70)
        
        # Set up some matches
        fm.isearch_matches = [0, 5, 10]
        fm.isearch_match_index = 0
        mock_pane['focused_index'] = 0
        
        # Press DOWN
        event = KeyEvent(KeyCode.DOWN, ModifierKey.NONE, None)
        fm.handle_isearch_input(event)
        print(f"  Pressed DOWN -> Match index: {fm.isearch_match_index}, Focused: {mock_pane['focused_index']}")
        assert fm.isearch_match_index == 1, "Should move to next match"
        assert mock_pane['focused_index'] == 5, "Should focus on match at index 5"
        
        # Press UP
        event = KeyEvent(KeyCode.UP, ModifierKey.NONE, None)
        fm.handle_isearch_input(event)
        print(f"  Pressed UP   -> Match index: {fm.isearch_match_index}, Focused: {mock_pane['focused_index']}")
        assert fm.isearch_match_index == 0, "Should move to previous match"
        assert mock_pane['focused_index'] == 0, "Should focus on match at index 0"
        
        print("  ✓ UP/DOWN navigation works correctly")
        print()
        
        print("Test 5: ESC and ENTER exit I-Search mode")
        print("-" * 70)
        
        # Test ESC
        event = KeyEvent(KeyCode.ESCAPE, ModifierKey.NONE, None)
        fm.handle_isearch_input(event)
        print(f"  Pressed ESC   -> exit_isearch_mode called: {fm.exit_isearch_mode.called}")
        assert fm.exit_isearch_mode.called, "ESC should exit I-Search mode"
        
        # Reset mock
        fm.exit_isearch_mode.reset_mock()
        
        # Test ENTER
        event = KeyEvent(KeyCode.ENTER, ModifierKey.NONE, None)
        fm.handle_isearch_input(event)
        print(f"  Pressed ENTER -> exit_isearch_mode called: {fm.exit_isearch_mode.called}")
        assert fm.exit_isearch_mode.called, "ENTER should exit I-Search mode"
        
        print("  ✓ ESC and ENTER work correctly")
        print()
        
        print("=" * 70)
        print("All tests passed! ✓")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - Printable characters are added to search pattern")
        print("  - Navigation keys (LEFT, RIGHT, HOME, END, etc.) are ignored")
        print("  - UP/DOWN navigate through matches")
        print("  - BACKSPACE removes last character")
        print("  - ESC/ENTER exit I-Search mode")
        print()
        print("The fix ensures that only printable characters are treated as")
        print("search input, preventing unwanted characters from being inserted")
        print("when navigation keys are pressed.")


if __name__ == '__main__':
    demo_filelist_isearch_arrow_keys()
