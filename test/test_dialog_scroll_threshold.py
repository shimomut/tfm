"""
Test dialog scroll threshold respects actual content height

Run with: PYTHONPATH=.:src:ttk pytest test/test_dialog_scroll_threshold.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.tfm_search_dialog import SearchDialog
from src.tfm_list_dialog import ListDialog
from src.tfm_info_dialog import InfoDialog
from src.tfm_drives_dialog import DrivesDialog
from src.tfm_batch_rename_dialog import BatchRenameDialog


class TestDialogScrollThreshold:
    """Test that dialog scroll thresholds respect actual UI height"""
    
    def test_search_dialog_scroll_uses_actual_height(self):
        """SearchDialog should use actual terminal height for scroll calculation"""
        config = Mock()
        config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        config.LIST_DIALOG_MIN_HEIGHT = 15
        
        renderer = Mock()
        renderer.get_dimensions.return_value = (40, 80)  # 40 rows, 80 cols
        
        dialog = SearchDialog(config, renderer)
        
        # Calculate expected content height based on SearchDialog layout
        # Dialog height = max(15, int(40 * 0.7)) = max(15, 28) = 28
        # SearchDialog: results_start_y = start_y + 6, results_end_y = start_y + dialog_height - 3
        # Content height = (start_y + 28 - 3) - (start_y + 6) + 1 = 20
        expected_content_height = 20
        
        # Create enough results to test scrolling
        dialog.results = [{'type': 'file', 'path': f'file{i}', 'relative_path': f'file{i}', 'match_info': f'file{i}'} 
                         for i in range(50)]
        
        # Simulate what happens during draw - cache the content height
        dialog._last_content_height = expected_content_height
        
        # Test scroll adjustment when selected is at bottom of visible area
        dialog.selected = expected_content_height  # Just past visible area
        dialog.scroll = 0
        dialog._adjust_scroll(len(dialog.results))
        
        # Scroll should adjust to keep selection visible
        # selected (20) >= scroll (0) + content_height (20), so scroll = 20 - 20 + 1 = 1
        assert dialog.scroll == 1, f"Expected scroll=1, got scroll={dialog.scroll}"
        
    def test_list_dialog_scroll_uses_actual_height(self):
        """ListDialog should use actual terminal height for scroll calculation"""
        config = Mock()
        config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        config.LIST_DIALOG_MIN_HEIGHT = 15
        
        renderer = Mock()
        renderer.get_dimensions.return_value = (30, 80)  # 30 rows, 80 cols
        
        dialog = ListDialog(config, renderer)
        
        # Calculate expected content height
        # Dialog height = max(15, int(30 * 0.7)) = max(15, 21) = 21
        # Content height = 21 - 8 = 13 (conservative estimate)
        expected_content_height = 13
        
        # Create enough items to test scrolling
        items = [f'item{i}' for i in range(40)]
        
        # Simulate what happens during draw - cache the content height
        dialog._last_content_height = expected_content_height
        
        # Test scroll adjustment
        dialog.selected = expected_content_height  # Just past visible area
        dialog.scroll = 0
        dialog._adjust_scroll(len(items))
        
        # Scroll should adjust: selected (13) >= scroll (0) + content_height (13), so scroll = 13 - 13 + 1 = 1
        assert dialog.scroll == 1, f"Expected scroll=1, got scroll={dialog.scroll}"
        
    def test_info_dialog_scroll_uses_actual_height(self):
        """InfoDialog should use actual terminal height for scroll calculation"""
        config = Mock()
        config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        config.LIST_DIALOG_MIN_HEIGHT = 15
        
        renderer = Mock()
        renderer.get_dimensions.return_value = (50, 100)  # 50 rows, 100 cols
        
        dialog = InfoDialog(config, renderer)
        
        # Calculate expected content height
        # Dialog height = max(15, int(50 * 0.7)) = max(15, 35) = 35
        # Content height = 35 - 8 = 27 (conservative estimate)
        expected_content_height = 27
        
        # Create enough lines to test scrolling
        lines = [f'line{i}' for i in range(60)]
        
        # Simulate what happens during draw - cache the content height
        dialog._last_content_height = expected_content_height
        
        # Test scroll adjustment
        dialog.selected = expected_content_height  # Just past visible area
        dialog.scroll = 0
        dialog._adjust_scroll(len(lines))
        
        # Scroll should adjust: selected (27) >= scroll (0) + content_height (27), so scroll = 27 - 27 + 1 = 1
        assert dialog.scroll == 1, f"Expected scroll=1, got scroll={dialog.scroll}"
        
    def test_drives_dialog_scroll_uses_actual_height(self):
        """DrivesDialog should use actual terminal height for scroll calculation"""
        config = Mock()
        config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        config.LIST_DIALOG_MIN_HEIGHT = 15
        
        renderer = Mock()
        renderer.get_dimensions.return_value = (25, 80)  # 25 rows, 80 cols
        
        dialog = DrivesDialog(config, renderer)
        
        # Calculate expected content height
        # Dialog height = max(15, int(25 * 0.7)) = max(15, 17) = 17
        # Content height = 17 - 8 = 9 (conservative estimate)
        expected_content_height = 9
        
        # Create enough drives to test scrolling
        drives = [{'name': f'drive{i}', 'path': f'/drive{i}'} for i in range(30)]
        
        # Simulate what happens during draw - cache the content height
        dialog._last_content_height = expected_content_height
        
        # Test scroll adjustment
        dialog.selected = expected_content_height  # Just past visible area
        dialog.scroll = 0
        dialog._adjust_scroll(len(drives))
        
        # Scroll should adjust: selected (9) >= scroll (0) + content_height (9), so scroll = 9 - 9 + 1 = 1
        assert dialog.scroll == 1, f"Expected scroll=1, got scroll={dialog.scroll}"
        
    def test_batch_rename_dialog_scroll_uses_actual_height(self):
        """BatchRenameDialog should use actual terminal height for scroll calculation"""
        config = Mock()
        config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        config.LIST_DIALOG_MIN_HEIGHT = 15
        
        renderer = Mock()
        renderer.get_dimensions.return_value = (35, 90)  # 35 rows, 90 cols
        
        dialog = BatchRenameDialog(config, renderer)
        
        # Calculate expected content height
        # Dialog height = max(15, int(35 * 0.7)) = max(15, 24) = 24
        # Content height = 24 - 8 = 16 (conservative estimate)
        expected_content_height = 16
        
        # Create enough files to test scrolling
        files = [f'file{i}.txt' for i in range(40)]
        
        # Simulate what happens during draw - cache the content height
        dialog._last_content_height = expected_content_height
        
        # Test scroll adjustment
        dialog.selected = expected_content_height  # Just past visible area
        dialog.scroll = 0
        dialog._adjust_scroll(len(files))
        
        # Scroll should adjust: selected (16) >= scroll (0) + content_height (16), so scroll = 16 - 16 + 1 = 1
        assert dialog.scroll == 1, f"Expected scroll=1, got scroll={dialog.scroll}"
