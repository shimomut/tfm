#!/usr/bin/env python3
"""
Test NFD/NFC normalization in filename abbreviation

This test verifies that filename abbreviation produces consistent results
regardless of whether the filename is in NFC or NFD form.
"""

import unicodedata
import pytest
from ttk.wide_char_utils import get_display_width, truncate_to_width, pad_to_width


class TestFilenameAbbreviationNFD:
    """Test that filename abbreviation handles NFD/NFC consistently"""
    
    def test_display_width_nfc_vs_nfd(self):
        """Test that display width is the same for NFC and NFD forms"""
        # Create test filename in both forms
        nfc_filename = unicodedata.normalize('NFC', "テストファイル_が.txt")
        nfd_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
        
        # Verify they're actually different forms
        assert nfc_filename != nfd_filename
        assert len(nfc_filename) != len(nfd_filename)
        
        # Display width should be the same
        nfc_width = get_display_width(nfc_filename)
        nfd_width = get_display_width(nfd_filename)
        
        assert nfc_width == nfd_width, \
            f"Display width should be equal: NFC={nfc_width}, NFD={nfd_width}"
    
    def test_truncate_width_nfc_vs_nfd(self):
        """Test that truncation produces same visual width for NFC and NFD"""
        # Create test filename in both forms
        nfc_filename = unicodedata.normalize('NFC', "テストファイル_が.txt")
        nfd_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
        
        # Truncate to same width
        target_width = 15
        nfc_truncated = truncate_to_width(nfc_filename, target_width)
        nfd_truncated = truncate_to_width(nfd_filename, target_width)
        
        # Display widths should be the same
        nfc_result_width = get_display_width(nfc_truncated)
        nfd_result_width = get_display_width(nfd_truncated)
        
        assert nfc_result_width == nfd_result_width, \
            f"Truncated widths should be equal: NFC={nfc_result_width}, NFD={nfd_result_width}"
        
        # Both should fit within target width
        assert nfc_result_width <= target_width
        assert nfd_result_width <= target_width
    
    def test_pad_width_nfc_vs_nfd(self):
        """Test that padding produces same visual width for NFC and NFD"""
        # Create test filename in both forms
        nfc_filename = unicodedata.normalize('NFC', "が.txt")
        nfd_filename = unicodedata.normalize('NFD', "が.txt")
        
        # Pad to same width
        target_width = 20
        nfc_padded = pad_to_width(nfc_filename, target_width)
        nfd_padded = pad_to_width(nfd_filename, target_width)
        
        # Display widths should be exactly the target width
        nfc_result_width = get_display_width(nfc_padded)
        nfd_result_width = get_display_width(nfd_padded)
        
        assert nfc_result_width == target_width, \
            f"NFC padded width should be {target_width}, got {nfc_result_width}"
        assert nfd_result_width == target_width, \
            f"NFD padded width should be {target_width}, got {nfd_result_width}"
    
    def test_multiple_japanese_characters(self):
        """Test with multiple Japanese characters"""
        test_cases = [
            "がぎぐげご",
            "テストファイル",
            "こんにちは世界",
            "日本語_ファイル名.txt"
        ]
        
        for test_str in test_cases:
            nfc_form = unicodedata.normalize('NFC', test_str)
            nfd_form = unicodedata.normalize('NFD', test_str)
            
            # Display widths should match
            nfc_width = get_display_width(nfc_form)
            nfd_width = get_display_width(nfd_form)
            
            assert nfc_width == nfd_width, \
                f"Width mismatch for '{test_str}': NFC={nfc_width}, NFD={nfd_width}"
    
    def test_mixed_ascii_and_japanese(self):
        """Test with mixed ASCII and Japanese characters"""
        test_cases = [
            "test_が_file.txt",
            "document_テスト.pdf",
            "readme_日本語.md"
        ]
        
        for test_str in test_cases:
            nfc_form = unicodedata.normalize('NFC', test_str)
            nfd_form = unicodedata.normalize('NFD', test_str)
            
            # Display widths should match
            nfc_width = get_display_width(nfc_form)
            nfd_width = get_display_width(nfd_form)
            
            assert nfc_width == nfd_width, \
                f"Width mismatch for '{test_str}': NFC={nfc_width}, NFD={nfd_width}"
    
    def test_file_list_scenario(self):
        """Test the actual file list display scenario"""
        # Simulate file list with mixed NFC/NFD filenames
        filenames = [
            unicodedata.normalize('NFC', "テストファイル_が.txt"),
            unicodedata.normalize('NFD', "テストファイル_が.txt"),
            unicodedata.normalize('NFC', "がぎぐげご.pdf"),
            unicodedata.normalize('NFD', "がぎぐげご.pdf"),
        ]
        
        # Truncate all to same width
        target_width = 15
        truncated = [truncate_to_width(f, target_width) for f in filenames]
        
        # All should have same or similar display width
        widths = [get_display_width(t) for t in truncated]
        
        # NFC and NFD versions of same filename should have same width
        assert widths[0] == widths[1], \
            f"NFC and NFD versions should have same width: {widths[0]} vs {widths[1]}"
        assert widths[2] == widths[3], \
            f"NFC and NFD versions should have same width: {widths[2]} vs {widths[3]}"
    
    def test_edge_case_single_character(self):
        """Test with single Japanese character"""
        nfc_char = unicodedata.normalize('NFC', "が")
        nfd_char = unicodedata.normalize('NFD', "が")
        
        # Verify they're different
        assert nfc_char != nfd_char
        assert len(nfc_char) == 1  # NFC: single character
        assert len(nfd_char) == 2  # NFD: base + combining mark
        
        # Display width should be the same (2 columns for wide character)
        nfc_width = get_display_width(nfc_char)
        nfd_width = get_display_width(nfd_char)
        
        assert nfc_width == nfd_width == 2, \
            f"Both should be 2 columns wide: NFC={nfc_width}, NFD={nfd_width}"
    
    def test_truncation_preserves_visual_consistency(self):
        """Test that truncation maintains visual consistency"""
        # Long filename with Japanese characters
        nfc_filename = unicodedata.normalize('NFC', "これは非常に長いファイル名です_が_test.txt")
        nfd_filename = unicodedata.normalize('NFD', "これは非常に長いファイル名です_が_test.txt")
        
        # Truncate to various widths
        for width in [10, 15, 20, 25, 30]:
            nfc_truncated = truncate_to_width(nfc_filename, width)
            nfd_truncated = truncate_to_width(nfd_filename, width)
            
            nfc_result_width = get_display_width(nfc_truncated)
            nfd_result_width = get_display_width(nfd_truncated)
            
            # Both should fit within target width
            assert nfc_result_width <= width, \
                f"NFC truncated to {width} should fit: got {nfc_result_width}"
            assert nfd_result_width <= width, \
                f"NFD truncated to {width} should fit: got {nfd_result_width}"
            
            # Widths should be equal or very close (within 1 column due to ellipsis)
            assert abs(nfc_result_width - nfd_result_width) <= 1, \
                f"Width difference too large at {width}: NFC={nfc_result_width}, NFD={nfd_result_width}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
