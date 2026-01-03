#!/usr/bin/env python3
"""
Tests for QuickChoiceBar ShorteningRegion support
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_quick_choice_bar import QuickChoiceBar, QuickChoiceBarHelpers
from tfm_string_width import ShorteningRegion


class TestQuickChoiceBarShortening(unittest.TestCase):
    """Test QuickChoiceBar with ShorteningRegion support"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.renderer = Mock()
        self.renderer.get_size = Mock(return_value=(24, 80))
        self.renderer.draw_text = Mock()
        self.quick_choice_bar = QuickChoiceBar(config=None, renderer=self.renderer)
    
    def test_show_accepts_shortening_regions(self):
        """Test that show() accepts shortening_regions parameter"""
        message = "This is a test message"
        choices = [{"text": "Yes", "key": "y", "value": True}]
        callback = Mock()
        
        regions = [
            ShorteningRegion(
                start=0,
                end=len(message),
                priority=1,
                strategy='abbreviate',
                abbrev_position='middle'
            )
        ]
        
        # Should not raise an exception
        self.quick_choice_bar.show(message, choices, callback, shortening_regions=regions)
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.message, message)
        self.assertEqual(self.quick_choice_bar.shortening_regions, regions)
    
    def test_show_without_shortening_regions(self):
        """Test that show() works without shortening_regions (backward compatibility)"""
        message = "Test message"
        choices = [{"text": "OK", "key": "o", "value": True}]
        callback = Mock()
        
        # Should work without shortening_regions parameter
        self.quick_choice_bar.show(message, choices, callback)
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertIsNone(self.quick_choice_bar.shortening_regions)
    
    def test_exit_clears_shortening_regions(self):
        """Test that exit() clears shortening_regions"""
        message = "Test"
        choices = [{"text": "OK", "key": "o", "value": True}]
        callback = Mock()
        regions = [ShorteningRegion(0, 4, 1, 'abbreviate')]
        
        self.quick_choice_bar.show(message, choices, callback, shortening_regions=regions)
        self.assertIsNotNone(self.quick_choice_bar.shortening_regions)
        
        self.quick_choice_bar.exit()
        self.assertIsNone(self.quick_choice_bar.shortening_regions)
    
    def test_draw_shortens_long_message_default(self):
        """Test that draw() shortens long messages using default abbreviation"""
        # Create a very long message
        long_message = "This is a very long message that should be shortened " * 5
        choices = [{"text": "Yes", "key": "y", "value": True}]
        callback = Mock()
        
        self.quick_choice_bar.show(long_message, choices, callback)
        
        # Draw with narrow width
        self.quick_choice_bar.draw(status_y=23, width=40)
        
        # Verify draw_text was called (message was rendered)
        self.assertTrue(self.renderer.draw_text.called)
        
        # Check that at least one call contains an ellipsis (message was shortened)
        calls = self.renderer.draw_text.call_args_list
        message_calls = [call for call in calls if len(call[0]) > 2 and isinstance(call[0][2], str)]
        
        # At least one call should contain the shortened message with ellipsis
        has_ellipsis = any('…' in str(call[0][2]) for call in message_calls)
        self.assertTrue(has_ellipsis, "Message should be shortened with ellipsis")
    
    def test_draw_uses_custom_shortening_regions(self):
        """Test that draw() uses custom shortening regions when provided"""
        message = "Prefix - IMPORTANT - Suffix"
        choices = [{"text": "OK", "key": "o", "value": True}]
        callback = Mock()
        
        # Create regions to preserve the important part
        regions = [
            ShorteningRegion(
                start=0,
                end=len(message),
                priority=1,
                strategy='abbreviate',
                abbrev_position='middle'
            )
        ]
        
        self.quick_choice_bar.show(message, choices, callback, shortening_regions=regions)
        
        # Draw with narrow width
        self.quick_choice_bar.draw(status_y=23, width=40)
        
        # Verify draw_text was called
        self.assertTrue(self.renderer.draw_text.called)
    
    def test_helper_show_yes_no_accepts_regions(self):
        """Test that show_yes_no_confirmation accepts shortening_regions"""
        message = "Are you sure you want to proceed?"
        callback = Mock()
        regions = [ShorteningRegion(0, len(message), 1, 'abbreviate', 'middle')]
        
        # Should not raise an exception
        QuickChoiceBarHelpers.show_yes_no_confirmation(
            self.quick_choice_bar,
            message,
            callback,
            shortening_regions=regions
        )
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.shortening_regions, regions)
    
    def test_helper_show_overwrite_accepts_regions(self):
        """Test that show_overwrite_dialog accepts shortening_regions"""
        filename = "test_file.txt"
        callback = Mock()
        regions = [ShorteningRegion(0, 10, 1, 'abbreviate')]
        
        QuickChoiceBarHelpers.show_overwrite_dialog(
            self.quick_choice_bar,
            filename,
            callback,
            shortening_regions=regions
        )
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.shortening_regions, regions)
    
    def test_helper_show_delete_accepts_regions(self):
        """Test that show_delete_confirmation accepts shortening_regions"""
        items = ["file1.txt", "file2.txt"]
        callback = Mock()
        regions = [ShorteningRegion(0, 10, 1, 'abbreviate')]
        
        QuickChoiceBarHelpers.show_delete_confirmation(
            self.quick_choice_bar,
            items,
            callback,
            shortening_regions=regions
        )
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.shortening_regions, regions)
    
    def test_helper_show_error_accepts_regions(self):
        """Test that show_error_dialog accepts shortening_regions"""
        error_message = "An error occurred"
        callback = Mock()
        regions = [ShorteningRegion(0, 10, 1, 'abbreviate')]
        
        QuickChoiceBarHelpers.show_error_dialog(
            self.quick_choice_bar,
            error_message,
            callback,
            shortening_regions=regions
        )
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.shortening_regions, regions)
    
    def test_helper_show_info_accepts_regions(self):
        """Test that show_info_dialog accepts shortening_regions"""
        info_message = "Operation completed"
        callback = Mock()
        regions = [ShorteningRegion(0, 10, 1, 'abbreviate')]
        
        QuickChoiceBarHelpers.show_info_dialog(
            self.quick_choice_bar,
            info_message,
            callback,
            shortening_regions=regions
        )
        
        self.assertTrue(self.quick_choice_bar.is_active)
        self.assertEqual(self.quick_choice_bar.shortening_regions, regions)
    
    def test_backward_compatibility_without_regions(self):
        """Test that all helpers work without shortening_regions (backward compatibility)"""
        callback = Mock()
        
        # All these should work without shortening_regions parameter
        QuickChoiceBarHelpers.show_yes_no_confirmation(
            self.quick_choice_bar, "Test?", callback
        )
        self.assertIsNone(self.quick_choice_bar.shortening_regions)
        self.quick_choice_bar.exit()
        
        QuickChoiceBarHelpers.show_overwrite_dialog(
            self.quick_choice_bar, "file.txt", callback
        )
        self.assertIsNone(self.quick_choice_bar.shortening_regions)
        self.quick_choice_bar.exit()
        
        QuickChoiceBarHelpers.show_delete_confirmation(
            self.quick_choice_bar, ["file.txt"], callback
        )
        self.assertIsNone(self.quick_choice_bar.shortening_regions)
        self.quick_choice_bar.exit()
        
        QuickChoiceBarHelpers.show_error_dialog(
            self.quick_choice_bar, "Error", callback
        )
        self.assertIsNone(self.quick_choice_bar.shortening_regions)
        self.quick_choice_bar.exit()
        
        QuickChoiceBarHelpers.show_info_dialog(
            self.quick_choice_bar, "Info", callback
        )
        self.assertIsNone(self.quick_choice_bar.shortening_regions)
    
    def test_help_text_hidden_provides_more_space(self):
        """Test that when help text is hidden, more space is available for message"""
        # Create a message that would fit without help text but not with it
        message = "This is a moderately long message"
        choices = [{"text": "Yes", "key": "y", "value": True}]
        callback = Mock()
        
        self.quick_choice_bar.show(message, choices, callback)
        
        # Draw with a narrow width where help text won't fit
        # This should give more space to the message
        self.quick_choice_bar.draw(status_y=23, width=50)
        
        # Verify draw_text was called
        self.assertTrue(self.renderer.draw_text.called)
        
        # Get all the text that was drawn
        calls = self.renderer.draw_text.call_args_list
        drawn_texts = [str(call[0][2]) for call in calls if len(call[0]) > 2]
        
        # The message should be present in some form
        # (either full or shortened, but not completely missing)
        message_found = any(
            'This' in text or 'moderately' in text or 'message' in text or '…' in text
            for text in drawn_texts
        )
        self.assertTrue(message_found, "Message should be visible even in narrow width")


if __name__ == '__main__':
    unittest.main()
