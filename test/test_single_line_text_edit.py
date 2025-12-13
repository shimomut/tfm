#!/usr/bin/env python3
"""
Test script for SingleLineTextEdit class
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_single_line_text_edit import SingleLineTextEdit
from ttk import InputEvent, KeyCode


def test_basic_functionality():
    """Test basic text editing functionality"""
    print("Testing basic functionality...")
    
    editor = SingleLineTextEdit()
    
    # Test empty initialization
    assert editor.get_text() == ""
    assert editor.get_cursor_pos() == 0
    
    # Test text insertion
    editor.insert_char('H')
    editor.insert_char('i')
    assert editor.get_text() == "Hi"
    assert editor.get_cursor_pos() == 2
    
    # Test cursor movement
    editor.move_cursor_left()
    assert editor.get_cursor_pos() == 1
    
    editor.insert_char('e')
    assert editor.get_text() == "Hei"
    assert editor.get_cursor_pos() == 2
    
    # Test backspace
    editor.backspace()
    assert editor.get_text() == "Hi"
    assert editor.get_cursor_pos() == 1
    
    # Test delete
    editor.delete_char_at_cursor()
    assert editor.get_text() == "H"
    assert editor.get_cursor_pos() == 1
    
    print("✓ Basic functionality tests passed")


def test_cursor_movement():
    """Test cursor movement operations"""
    print("Testing cursor movement...")
    
    editor = SingleLineTextEdit("Hello")
    
    # Test home/end
    editor.move_cursor_home()
    assert editor.get_cursor_pos() == 0
    
    editor.move_cursor_end()
    assert editor.get_cursor_pos() == 5
    
    # Test boundary conditions
    assert not editor.move_cursor_right()  # Can't move past end
    assert editor.get_cursor_pos() == 5
    
    editor.move_cursor_home()
    assert not editor.move_cursor_left()  # Can't move before start
    assert editor.get_cursor_pos() == 0
    
    print("✓ Cursor movement tests passed")


def test_key_handling():
    """Test key handling functionality"""
    print("Testing key handling...")
    
    editor = SingleLineTextEdit("test")
    
    # Test printable characters
    event = InputEvent(key_code=ord('X'), modifiers=0, char='X')
    result = editor.handle_key(event)
    assert result
    assert editor.get_text() == "testX"
    
    # Test cursor keys
    editor.move_cursor_home()
    event = InputEvent(key_code=KeyCode.RIGHT, modifiers=0)
    result = editor.handle_key(event)
    print(f"Debug: KEY_RIGHT returned {result}, cursor at {editor.get_cursor_pos()}")
    assert result
    assert editor.get_cursor_pos() == 1
    
    event = InputEvent(key_code=KeyCode.LEFT, modifiers=0)
    result = editor.handle_key(event)
    print(f"Debug: KEY_LEFT returned {result}, cursor at {editor.get_cursor_pos()}")
    assert result
    assert editor.get_cursor_pos() == 0
    
    # Test home/end keys
    event = InputEvent(key_code=KeyCode.END, modifiers=0)
    result = editor.handle_key(event)
    print(f"Debug: KEY_END returned {result}, cursor at {editor.get_cursor_pos()}")
    assert result
    assert editor.get_cursor_pos() == len(editor.get_text())
    
    event = InputEvent(key_code=KeyCode.HOME, modifiers=0)
    result = editor.handle_key(event)
    print(f"Debug: KEY_HOME returned {result}, cursor at {editor.get_cursor_pos()}")
    assert result
    assert editor.get_cursor_pos() == 0
    
    # Test backspace
    editor.move_cursor_right()
    original_text = editor.get_text()
    original_pos = editor.get_cursor_pos()
    event = InputEvent(key_code=KeyCode.BACKSPACE, modifiers=0)
    result = editor.handle_key(event)
    print(f"Debug: Before backspace: '{original_text}' at pos {original_pos}")
    print(f"Debug: After backspace: '{editor.get_text()}' at pos {editor.get_cursor_pos()}")
    assert result
    assert editor.get_text() == "estX"  # Should remove the 't' at position 0
    assert editor.get_cursor_pos() == 0
    
    print("✓ Key handling tests passed")


def test_max_length():
    """Test maximum length constraint"""
    print("Testing maximum length constraint...")
    
    editor = SingleLineTextEdit("", max_length=3)
    
    # Should allow up to max_length
    assert editor.insert_char('A')
    assert editor.insert_char('B')
    assert editor.insert_char('C')
    assert editor.get_text() == "ABC"
    
    # Should reject beyond max_length
    assert not editor.insert_char('D')
    assert editor.get_text() == "ABC"
    
    print("✓ Maximum length tests passed")


def test_set_operations():
    """Test set_text and related operations"""
    print("Testing set operations...")
    
    editor = SingleLineTextEdit()
    
    # Test set_text
    editor.set_text("Hello World")
    assert editor.get_text() == "Hello World"
    assert editor.get_cursor_pos() == 0  # Cursor should be adjusted
    
    # Test clear
    editor.clear()
    assert editor.get_text() == ""
    assert editor.get_cursor_pos() == 0
    
    # Test set_cursor_pos
    editor.set_text("Test")
    editor.set_cursor_pos(2)
    assert editor.get_cursor_pos() == 2
    
    # Test cursor bounds checking
    editor.set_cursor_pos(100)  # Beyond text length
    assert editor.get_cursor_pos() == 4  # Should be clamped to text length
    
    editor.set_cursor_pos(-5)  # Negative
    assert editor.get_cursor_pos() == 0  # Should be clamped to 0
    
    print("✓ Set operations tests passed")


def main():
    """Run all tests"""
    print("SingleLineTextEdit Test Suite")
    print("============================")
    
    try:
        test_basic_functionality()
        test_cursor_movement()
        test_key_handling()
        test_max_length()
        test_set_operations()
        
        print("\n🎉 All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())