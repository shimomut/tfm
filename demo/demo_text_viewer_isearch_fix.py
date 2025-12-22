#!/usr/bin/env python3
"""
Demo: TextViewer Incremental Search Character Input Fix

This demo verifies that character input works correctly in TextViewer's
incremental search mode. The fix ensures that:

1. When in isearch mode, KeyEvents that should generate CharEvents return False
2. CharEvents are properly handled by handle_char_event when in isearch mode
3. Characters can be typed into the search pattern

Test procedure:
1. Run the demo to open a text file
2. Press 'f' to enter isearch mode
3. Type some characters - they should appear in the search pattern
4. Press ESC to exit isearch mode
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk import KeyEvent, KeyCode, CharEvent
from src.tfm_text_viewer import TextViewer
from src.tfm_path import Path


class MockRenderer:
    """Mock renderer for testing"""
    def get_dimensions(self):
        return (24, 80)
    
    def set_cursor_visibility(self, visible):
        pass


def test_isearch_character_input():
    """Test that character input works in isearch mode"""
    
    # Create a test file
    test_file = Path("temp/test_isearch.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Line 1: Hello World\nLine 2: Python Programming\nLine 3: Test Search\n")
    
    # Create mock renderer and viewer
    renderer = MockRenderer()
    viewer = TextViewer(renderer, test_file)
    
    print("Testing TextViewer isearch character input...")
    print()
    
    # Test 1: Enter isearch mode
    print("Test 1: Entering isearch mode with 'f' key")
    key_f = KeyEvent(key_code=ord('f'), char='f', modifiers=0)
    result = viewer.handle_key_event(key_f)
    assert result == True, "Should handle 'f' key to enter isearch mode"
    assert viewer.isearch_mode == True, "Should be in isearch mode"
    print("✓ Entered isearch mode")
    print()
    
    # Test 2: Type a character - KeyEvent should return False to allow CharEvent generation
    print("Test 2: Typing 'h' character")
    key_h = KeyEvent(key_code=ord('h'), char='h', modifiers=0)
    result = viewer.handle_key_event(key_h)
    print(f"  handle_key_event returned: {result}")
    assert result == False, "Should return False to allow backend to generate CharEvent"
    
    # Simulate backend generating CharEvent
    char_h = CharEvent(char='h')
    result = viewer.handle_char_event(char_h)
    print(f"  handle_char_event returned: {result}")
    assert result == True, "Should handle CharEvent in isearch mode"
    assert viewer.isearch_pattern == "h", f"Pattern should be 'h', got '{viewer.isearch_pattern}'"
    print("✓ Character 'h' added to search pattern")
    print()
    
    # Test 3: Type another character
    print("Test 3: Typing 'e' character")
    key_e = KeyEvent(key_code=ord('e'), char='e', modifiers=0)
    result = viewer.handle_key_event(key_e)
    assert result == False, "Should return False to allow CharEvent generation"
    
    char_e = CharEvent(char='e')
    result = viewer.handle_char_event(char_e)
    assert result == True, "Should handle CharEvent"
    assert viewer.isearch_pattern == "he", f"Pattern should be 'he', got '{viewer.isearch_pattern}'"
    print("✓ Character 'e' added to search pattern")
    print()
    
    # Test 4: Type more characters to complete "hello"
    print("Test 4: Typing 'llo' to complete 'hello'")
    for char in "llo":
        key_event = KeyEvent(key_code=ord(char), char=char, modifiers=0)
        result = viewer.handle_key_event(key_event)
        assert result == False, f"Should return False for '{char}'"
        
        char_event = CharEvent(char=char)
        result = viewer.handle_char_event(char_event)
        assert result == True, f"Should handle CharEvent for '{char}'"
    
    assert viewer.isearch_pattern == "hello", f"Pattern should be 'hello', got '{viewer.isearch_pattern}'"
    assert len(viewer.isearch_matches) > 0, "Should find matches for 'hello'"
    print(f"✓ Search pattern is 'hello' with {len(viewer.isearch_matches)} match(es)")
    print()
    
    # Test 5: Backspace should work
    print("Test 5: Testing backspace")
    backspace_event = KeyEvent(key_code=KeyCode.BACKSPACE, char=None, modifiers=0)
    result = viewer.handle_key_event(backspace_event)
    assert result == True, "Should handle backspace"
    assert viewer.isearch_pattern == "hell", f"Pattern should be 'hell', got '{viewer.isearch_pattern}'"
    print("✓ Backspace removed last character")
    print()
    
    # Test 6: ESC should exit isearch mode
    print("Test 6: Exiting isearch mode with ESC")
    esc_event = KeyEvent(key_code=KeyCode.ESCAPE, char=None, modifiers=0)
    result = viewer.handle_key_event(esc_event)
    assert result == True, "Should handle ESC"
    assert viewer.isearch_mode == False, "Should exit isearch mode"
    print("✓ Exited isearch mode")
    print()
    
    # Test 7: Character events should not be handled outside isearch mode
    print("Test 7: Character events outside isearch mode")
    char_x = CharEvent(char='x')
    result = viewer.handle_char_event(char_x)
    assert result == False, "Should not handle CharEvent outside isearch mode"
    print("✓ CharEvents ignored outside isearch mode")
    print()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print()
    print("The fix ensures that:")
    print("1. KeyEvents in isearch mode return False for printable characters")
    print("2. This allows the backend to generate CharEvents")
    print("3. CharEvents are handled by handle_char_event when in isearch mode")
    print("4. Characters are properly added to the search pattern")
    
    # Cleanup
    test_file.unlink()


if __name__ == "__main__":
    test_isearch_character_input()
