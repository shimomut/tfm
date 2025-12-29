#!/usr/bin/env python3
"""
Tests for word-level navigation and deletion in SingleLineTextEdit
"""

import pytest
from src.tfm_single_line_text_edit import SingleLineTextEdit


class TestWordNavigation:
    """Test word-level cursor movement"""
    
    def test_move_cursor_word_right_basic(self):
        """Test moving cursor right by word"""
        editor = SingleLineTextEdit("hello world test")
        editor.set_cursor_pos(0)
        
        # Move to start of "world"
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 6
        
        # Move to start of "test"
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 12
        
        # Move to end
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 16
        
        # No more words
        assert editor.move_cursor_word_right() is False
        assert editor.get_cursor_pos() == 16
    
    def test_move_cursor_word_left_basic(self):
        """Test moving cursor left by word"""
        editor = SingleLineTextEdit("hello world test")
        editor.set_cursor_pos(16)
        
        # Move to start of "test"
        assert editor.move_cursor_word_left() is True
        assert editor.get_cursor_pos() == 12
        
        # Move to start of "world"
        assert editor.move_cursor_word_left() is True
        assert editor.get_cursor_pos() == 6
        
        # Move to start
        assert editor.move_cursor_word_left() is True
        assert editor.get_cursor_pos() == 0
        
        # No more words
        assert editor.move_cursor_word_left() is False
        assert editor.get_cursor_pos() == 0
    
    def test_move_cursor_word_right_multiple_spaces(self):
        """Test word navigation with multiple spaces"""
        editor = SingleLineTextEdit("hello   world")
        editor.set_cursor_pos(0)
        
        # Should skip multiple spaces
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 8
    
    def test_move_cursor_word_left_multiple_spaces(self):
        """Test word navigation backward with multiple spaces"""
        editor = SingleLineTextEdit("hello   world")
        editor.set_cursor_pos(13)
        
        # Should move to start of "world"
        assert editor.move_cursor_word_left() is True
        assert editor.get_cursor_pos() == 8
    
    def test_move_cursor_word_right_from_middle(self):
        """Test word navigation from middle of word"""
        editor = SingleLineTextEdit("hello world")
        editor.set_cursor_pos(3)  # Middle of "hello"
        
        # Should move to start of next word
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 6
    
    def test_move_cursor_word_left_from_middle(self):
        """Test word navigation backward from middle of word"""
        editor = SingleLineTextEdit("hello world")
        editor.set_cursor_pos(8)  # Middle of "world"
        
        # Should move to start of current word
        assert editor.move_cursor_word_left() is True
        assert editor.get_cursor_pos() == 6
    
    def test_move_cursor_word_empty_text(self):
        """Test word navigation with empty text"""
        editor = SingleLineTextEdit("")
        
        assert editor.move_cursor_word_right() is False
        assert editor.move_cursor_word_left() is False
    
    def test_move_cursor_word_single_word(self):
        """Test word navigation with single word"""
        editor = SingleLineTextEdit("hello")
        editor.set_cursor_pos(0)
        
        # Move to end
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 5
        
        # Move back to start
        assert editor.move_cursor_word_left() is True
        assert editor.get_cursor_pos() == 0
    
    def test_move_cursor_word_only_spaces(self):
        """Test word navigation with only spaces"""
        editor = SingleLineTextEdit("     ")
        editor.set_cursor_pos(0)
        
        # Should move to end
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 5
        
        # Moving left from end of spaces goes to position 1 (after first space)
        assert editor.move_cursor_word_left() is True
        assert editor.get_cursor_pos() == 1


class TestWordDeletion:
    """Test word-level deletion"""
    
    def test_delete_word_backward_basic(self):
        """Test deleting word backward"""
        editor = SingleLineTextEdit("hello world")
        editor.set_cursor_pos(11)  # End of text
        
        # Delete "world"
        assert editor.delete_word_backward() is True
        assert editor.get_text() == "hello "
        assert editor.get_cursor_pos() == 6
        
        # Delete "hello "
        assert editor.delete_word_backward() is True
        assert editor.get_text() == ""
        assert editor.get_cursor_pos() == 0
        
        # Nothing to delete
        assert editor.delete_word_backward() is False
    
    def test_delete_word_backward_from_middle(self):
        """Test deleting word backward from middle of word"""
        editor = SingleLineTextEdit("hello world test")
        editor.set_cursor_pos(8)  # Middle of "world"
        
        # Should delete "world" up to cursor
        assert editor.delete_word_backward() is True
        assert editor.get_text() == "hello rld test"
        assert editor.get_cursor_pos() == 6
    
    def test_delete_word_backward_multiple_spaces(self):
        """Test deleting word backward with multiple spaces"""
        editor = SingleLineTextEdit("hello   world")
        editor.set_cursor_pos(13)  # End of text
        
        # Should delete "world" (stops at start of word)
        assert editor.delete_word_backward() is True
        assert editor.get_text() == "hello   "
        assert editor.get_cursor_pos() == 8
    
    def test_delete_word_backward_at_start(self):
        """Test deleting word backward at start of text"""
        editor = SingleLineTextEdit("hello world")
        editor.set_cursor_pos(0)
        
        # Nothing to delete
        assert editor.delete_word_backward() is False
        assert editor.get_text() == "hello world"
        assert editor.get_cursor_pos() == 0
    
    def test_delete_word_backward_single_word(self):
        """Test deleting single word"""
        editor = SingleLineTextEdit("hello")
        editor.set_cursor_pos(5)
        
        assert editor.delete_word_backward() is True
        assert editor.get_text() == ""
        assert editor.get_cursor_pos() == 0
    
    def test_delete_word_backward_preserves_after_cursor(self):
        """Test that deletion preserves text after cursor"""
        editor = SingleLineTextEdit("hello world test")
        editor.set_cursor_pos(11)  # After "world"
        
        # Delete "world"
        assert editor.delete_word_backward() is True
        assert editor.get_text() == "hello  test"
        assert editor.get_cursor_pos() == 6
    
    def test_delete_word_backward_only_spaces(self):
        """Test deleting spaces and word"""
        editor = SingleLineTextEdit("hello     ")
        editor.set_cursor_pos(10)  # End of text
        
        # Should delete spaces and "hello"
        assert editor.delete_word_backward() is True
        assert editor.get_text() == ""
        assert editor.get_cursor_pos() == 0


class TestWordBoundaryHelpers:
    """Test word boundary helper functions"""
    
    def test_find_previous_word_boundary(self):
        """Test finding previous word boundary"""
        editor = SingleLineTextEdit("hello world test")
        
        # From end
        assert editor._find_previous_word_boundary(16) == 12
        # From middle of "test"
        assert editor._find_previous_word_boundary(14) == 12
        # From start of "test"
        assert editor._find_previous_word_boundary(12) == 6
        # From middle of "world"
        assert editor._find_previous_word_boundary(8) == 6
        # From start of "world"
        assert editor._find_previous_word_boundary(6) == 0
        # From start
        assert editor._find_previous_word_boundary(0) == 0
    
    def test_find_next_word_boundary(self):
        """Test finding next word boundary"""
        editor = SingleLineTextEdit("hello world test")
        
        # From start
        assert editor._find_next_word_boundary(0) == 6
        # From middle of "hello"
        assert editor._find_next_word_boundary(2) == 6
        # From start of "world"
        assert editor._find_next_word_boundary(6) == 12
        # From middle of "world"
        assert editor._find_next_word_boundary(8) == 12
        # From start of "test"
        assert editor._find_next_word_boundary(12) == 16
        # From end
        assert editor._find_next_word_boundary(16) == 16


class TestPunctuationWordBoundaries:
    """Test word boundaries with punctuation and special characters"""
    
    def test_is_word_char(self):
        """Test word character detection"""
        editor = SingleLineTextEdit("")
        
        # Word characters
        assert editor._is_word_char('a') is True
        assert editor._is_word_char('Z') is True
        assert editor._is_word_char('0') is True
        assert editor._is_word_char('9') is True
        assert editor._is_word_char('_') is True
        
        # Non-word characters
        assert editor._is_word_char(' ') is False
        assert editor._is_word_char('-') is False
        assert editor._is_word_char('~') is False
        assert editor._is_word_char('`') is False
        assert editor._is_word_char('[') is False
        assert editor._is_word_char(']') is False
        assert editor._is_word_char('=') is False
        assert editor._is_word_char('|') is False
        assert editor._is_word_char('\\') is False
        assert editor._is_word_char('/') is False
        assert editor._is_word_char('.') is False
        assert editor._is_word_char(',') is False
    
    def test_word_navigation_with_hyphens(self):
        """Test word navigation with hyphenated text"""
        editor = SingleLineTextEdit("hello-world-test")
        editor.set_cursor_pos(0)
        
        # Should skip over hyphens and stop at next word
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 6  # Start of "world"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 12  # Start of "test"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 16  # End
    
    def test_word_navigation_with_brackets(self):
        """Test word navigation with brackets"""
        editor = SingleLineTextEdit("func[index]")
        editor.set_cursor_pos(0)
        
        # Should skip over brackets
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 5  # Start of "index"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 11  # End
    
    def test_word_navigation_with_path(self):
        """Test word navigation with file path"""
        editor = SingleLineTextEdit("/usr/local/bin")
        editor.set_cursor_pos(0)
        
        # Should skip over slashes
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 1  # Start of "usr"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 5  # Start of "local"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 11  # Start of "bin"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 14  # End
    
    def test_word_navigation_with_equals(self):
        """Test word navigation with equals sign"""
        editor = SingleLineTextEdit("key=value")
        editor.set_cursor_pos(0)
        
        # Should skip over equals sign
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 4  # Start of "value"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 9  # End
    
    def test_word_navigation_with_multiple_punctuation(self):
        """Test word navigation with multiple punctuation marks"""
        editor = SingleLineTextEdit("hello...world")
        editor.set_cursor_pos(0)
        
        # Should skip over all punctuation
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 8  # Start of "world"
        
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 13  # End
    
    def test_delete_word_with_punctuation(self):
        """Test deleting words with punctuation"""
        editor = SingleLineTextEdit("hello-world")
        editor.set_cursor_pos(11)  # End
        
        # Delete "world"
        assert editor.delete_word_backward() is True
        assert editor.get_text() == "hello-"
        assert editor.get_cursor_pos() == 6
        
        # Delete "-" and "hello" (punctuation is skipped, deletes previous word)
        assert editor.delete_word_backward() is True
        assert editor.get_text() == ""
        assert editor.get_cursor_pos() == 0
    
    def test_delete_word_with_path(self):
        """Test deleting words in file path"""
        editor = SingleLineTextEdit("/usr/local/bin")
        editor.set_cursor_pos(14)  # End
        
        # Delete "bin"
        assert editor.delete_word_backward() is True
        assert editor.get_text() == "/usr/local/"
        assert editor.get_cursor_pos() == 11
        
        # Delete "/" and "local"
        assert editor.delete_word_backward() is True
        assert editor.get_text() == "/usr/"
        assert editor.get_cursor_pos() == 5
    
    def test_underscore_is_word_char(self):
        """Test that underscore is treated as word character"""
        editor = SingleLineTextEdit("hello_world_test")
        editor.set_cursor_pos(0)
        
        # Should treat entire string as one word
        assert editor.move_cursor_word_right() is True
        assert editor.get_cursor_pos() == 16  # End
        
        # Delete entire word
        assert editor.delete_word_backward() is True
        assert editor.get_text() == ""
        assert editor.get_cursor_pos() == 0
