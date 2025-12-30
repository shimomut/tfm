#!/usr/bin/env python3
"""
Test that all dialogs use consistent TextAttribute values for borders.

This ensures visual consistency across all dialog types:
- Main borders (box outline) should use TextAttribute.NORMAL to avoid gaps
- Separator lines (horizontal dividers) should use TextAttribute.BOLD for emphasis
"""

import unittest
from unittest.mock import MagicMock
from ttk import TextAttribute


class TestDialogTextAttributeConsistency(unittest.TestCase):
    """Test that dialogs use consistent text attributes for borders."""
    
    def setUp(self):
        """Set up mock renderer for testing."""
        self.mock_renderer = MagicMock()
        self.mock_renderer.get_dimensions.return_value = (40, 120)
        self.mock_renderer.is_desktop_mode.return_value = False
    
    def test_info_dialog_uses_normal_for_borders(self):
        """Verify InfoDialog uses TextAttribute.NORMAL for main borders."""
        from tfm_info_dialog import InfoDialog
        from tfm_config import get_config
        
        config = get_config()
        dialog = InfoDialog(config, self.mock_renderer)
        
        # Show dialog with some content
        dialog.show("Test", ["Line 1", "Line 2"])
        dialog.draw()
        
        # Check that border drawing calls use NORMAL attribute
        border_calls = [
            call for call in self.mock_renderer.draw_text.call_args_list
            if any(char in str(call) for char in ['┌', '┐', '└', '┘', '│'])
        ]
        
        # Verify at least some border calls were made
        self.assertGreater(len(border_calls), 0, "InfoDialog should draw borders")
        
        # Check that border calls use NORMAL attribute (not BOLD)
        for call_obj in border_calls:
            if 'attributes' in call_obj.kwargs:
                attrs = call_obj.kwargs['attributes']
                # Main borders should use NORMAL
                if '│' in str(call_obj):
                    self.assertEqual(attrs, TextAttribute.NORMAL,
                                   "InfoDialog vertical borders should use NORMAL attribute")
    
    def test_batch_rename_dialog_uses_normal_for_borders(self):
        """Verify BatchRenameDialog uses TextAttribute.NORMAL for main borders."""
        from tfm_batch_rename_dialog import BatchRenameDialog
        from tfm_config import get_config
        from tfm_path import Path
        import tempfile
        
        config = get_config()
        dialog = BatchRenameDialog(config, self.mock_renderer)
        
        # Create temporary test files
        with tempfile.TemporaryDirectory() as tmpdir:
            test_files = []
            for i in range(3):
                filepath = Path(tmpdir) / f"test{i}.txt"
                filepath.touch()
                test_files.append(filepath)
            
            # Show dialog with test files
            dialog.show(test_files)
            dialog.draw()
        
        # Check that border drawing calls use NORMAL attribute
        border_calls = [
            call for call in self.mock_renderer.draw_text.call_args_list
            if any(char in str(call) for char in ['┌', '┐', '└', '┘', '│'])
        ]
        
        # Verify at least some border calls were made
        self.assertGreater(len(border_calls), 0, "BatchRenameDialog should draw borders")
        
        # Check that main border calls use NORMAL attribute
        for call_obj in border_calls:
            if 'attributes' in call_obj.kwargs:
                attrs = call_obj.kwargs['attributes']
                # Main borders should use NORMAL
                if '│' in str(call_obj):
                    self.assertEqual(attrs, TextAttribute.NORMAL,
                                   "BatchRenameDialog vertical borders should use NORMAL attribute")
    
    def test_batch_rename_dialog_uses_bold_for_separators(self):
        """Verify BatchRenameDialog uses TextAttribute.BOLD for separator lines."""
        from tfm_batch_rename_dialog import BatchRenameDialog
        from tfm_config import get_config
        from tfm_path import Path
        import tempfile
        
        config = get_config()
        dialog = BatchRenameDialog(config, self.mock_renderer)
        
        # Create temporary test files
        with tempfile.TemporaryDirectory() as tmpdir:
            test_files = []
            for i in range(3):
                filepath = Path(tmpdir) / f"test{i}.txt"
                filepath.touch()
                test_files.append(filepath)
            
            # Show dialog with test files
            dialog.show(test_files)
            dialog.draw()
        
        # Check that separator line calls use BOLD attribute
        separator_calls = [
            call for call in self.mock_renderer.draw_text.call_args_list
            if '├' in str(call) or '┤' in str(call)
        ]
        
        # Verify separator calls were made
        self.assertGreater(len(separator_calls), 0, "BatchRenameDialog should draw separator lines")
        
        # Check that separator calls use BOLD attribute
        for call_obj in separator_calls:
            if 'attributes' in call_obj.kwargs:
                attrs = call_obj.kwargs['attributes']
                self.assertEqual(attrs, TextAttribute.BOLD,
                               "BatchRenameDialog separator lines should use BOLD attribute")


if __name__ == '__main__':
    unittest.main()
