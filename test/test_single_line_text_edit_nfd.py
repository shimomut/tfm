#!/usr/bin/env python3
"""
Test NFD/NFC normalization in SingleLineTextEdit

This test verifies that SingleLineTextEdit correctly handles NFD (decomposed)
strings from macOS filenames, normalizing them to NFC internally for editing,
and converting back to NFD when retrieving the text.
"""

import unicodedata
import pytest
from src.tfm_single_line_text_edit import SingleLineTextEdit


class TestSingleLineTextEditNFD:
    """Test NFD/NFC normalization in SingleLineTextEdit"""
    
    def test_nfd_input_returns_nfd(self):
        """Test that NFD input is converted to NFC internally and back to NFD on retrieval"""
        # Create NFD string (decomposed form, as used by macOS)
        nfd_text = unicodedata.normalize('NFD', "テストファイル_が.txt")
        
        # Verify it's actually NFD
        assert nfd_text == unicodedata.normalize('NFD', nfd_text)
        assert nfd_text != unicodedata.normalize('NFC', nfd_text)
        
        # Create editor with NFD text
        editor = SingleLineTextEdit(initial_text=nfd_text)
        
        # Internal text should be NFC
        assert editor.text == unicodedata.normalize('NFC', nfd_text)
        
        # Retrieved text should be NFD (matching original form)
        assert editor.get_text() == nfd_text
        assert editor.get_text() == unicodedata.normalize('NFD', editor.get_text())
    
    def test_nfc_input_returns_nfc(self):
        """Test that NFC input stays as NFC"""
        # Create NFC string (composed form)
        nfc_text = unicodedata.normalize('NFC', "テストファイル_が.txt")
        
        # Verify it's actually NFC
        assert nfc_text == unicodedata.normalize('NFC', nfc_text)
        
        # Create editor with NFC text
        editor = SingleLineTextEdit(initial_text=nfc_text)
        
        # Internal text should be NFC
        assert editor.text == nfc_text
        
        # Retrieved text should be NFC (matching original form)
        assert editor.get_text() == nfc_text
    
    def test_nfd_editing_preserves_nfd(self):
        """Test that editing NFD text preserves NFD form on retrieval"""
        # Create NFD string
        nfd_text = unicodedata.normalize('NFD', "が")
        
        # Create editor with NFD text
        editor = SingleLineTextEdit(initial_text=nfd_text)
        
        # Add some ASCII text
        editor.move_cursor_end()
        editor.insert_char('_')
        editor.insert_char('t')
        editor.insert_char('e')
        editor.insert_char('s')
        editor.insert_char('t')
        
        # Retrieved text should be NFD
        result = editor.get_text()
        assert result.startswith(nfd_text)
        assert result == unicodedata.normalize('NFD', result)
    
    def test_nfd_set_text_preserves_nfd(self):
        """Test that set_text with NFD preserves NFD form"""
        # Start with NFC text
        editor = SingleLineTextEdit(initial_text="test")
        
        # Set NFD text
        nfd_text = unicodedata.normalize('NFD', "がぎぐげご")
        editor.set_text(nfd_text)
        
        # Retrieved text should be NFD
        assert editor.get_text() == nfd_text
        assert editor.get_text() == unicodedata.normalize('NFD', editor.get_text())
    
    def test_nfd_insert_char_normalizes_to_nfc(self):
        """Test that inserting NFD characters normalizes them to NFC internally"""
        # Create editor with NFD text
        nfd_text = unicodedata.normalize('NFD', "が")
        editor = SingleLineTextEdit(initial_text=nfd_text)
        
        # Insert another NFD character
        nfd_char = unicodedata.normalize('NFD', "ぎ")
        editor.move_cursor_end()
        editor.insert_char(nfd_char)
        
        # Internal text should be NFC
        assert editor.text == unicodedata.normalize('NFC', editor.text)
        
        # Retrieved text should be NFD
        result = editor.get_text()
        assert result == unicodedata.normalize('NFD', result)
    
    def test_empty_string_handling(self):
        """Test that empty strings don't cause issues"""
        editor = SingleLineTextEdit(initial_text="")
        assert editor.get_text() == ""
        
        # Set to NFD text
        nfd_text = unicodedata.normalize('NFD', "が")
        editor.set_text(nfd_text)
        assert editor.get_text() == nfd_text
        
        # Clear and verify
        editor.clear()
        assert editor.get_text() == ""
    
    def test_mixed_nfd_nfc_editing(self):
        """Test editing with mixed NFD/NFC input"""
        # Start with NFD
        nfd_text = unicodedata.normalize('NFD', "が")
        editor = SingleLineTextEdit(initial_text=nfd_text)
        
        # Add NFC text
        nfc_text = unicodedata.normalize('NFC', "ぎ")
        editor.move_cursor_end()
        editor.insert_char(nfc_text)
        
        # Internal should be NFC
        assert editor.text == unicodedata.normalize('NFC', editor.text)
        
        # Retrieved should be NFD (matching original form)
        result = editor.get_text()
        assert result == unicodedata.normalize('NFD', result)
    
    def test_rename_scenario(self):
        """Test the actual rename scenario: NFD filename editing"""
        # Simulate macOS filename (NFD)
        original_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
        
        # Create editor (as done in rename dialog)
        editor = SingleLineTextEdit(initial_text=original_filename)
        
        # User edits the filename (removes extension, adds new text)
        editor.set_cursor_pos(len(editor.text) - 4)  # Before ".txt"
        editor.insert_char('_')
        editor.insert_char('2')
        
        # Get the result
        new_filename = editor.get_text()
        
        # Result should be NFD (matching original form)
        assert new_filename == unicodedata.normalize('NFD', new_filename)
        assert new_filename.endswith("_2.txt")
        
        # Verify the Japanese characters are still NFD
        assert new_filename.startswith(original_filename[:-4])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
