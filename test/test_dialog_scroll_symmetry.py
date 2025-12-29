"""
Test dialog scroll symmetry - upward and downward scrolling should be symmetric

Run with: PYTHONPATH=.:src:ttk pytest test/test_dialog_scroll_symmetry.py -v
"""

import pytest
from unittest.mock import Mock
from src.tfm_search_dialog import SearchDialog


class TestDialogScrollSymmetry:
    """Test that upward and downward scrolling are symmetric"""
    
    def test_upward_scroll_positions_item_at_top(self):
        """When scrolling up, focused item should be at top of visible area"""
        config = Mock()
        config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        config.LIST_DIALOG_MIN_HEIGHT = 15
        
        renderer = Mock()
        renderer.get_dimensions.return_value = (40, 80)
        
        dialog = SearchDialog(config, renderer)
        
        # Content height = max(15, int(40 * 0.7)) - 6 = 28 - 6 = 22
        content_height = 22
        
        # Create results
        dialog.results = [{'type': 'file', 'path': f'file{i}', 'relative_path': f'file{i}', 'match_info': f'file{i}'} 
                         for i in range(50)]
        
        # Start with scroll=10, selected=10 (at top of visible area)
        dialog.scroll = 10
        dialog.selected = 10
        
        # Move up one item
        dialog.selected = 9
        dialog._adjust_scroll(len(dialog.results))
        
        # After scrolling up, selected should be at top: scroll == selected
        assert dialog.scroll == dialog.selected, \
            f"Upward scroll: selected ({dialog.selected}) should equal scroll ({dialog.scroll})"
        assert dialog.scroll == 9
        
    def test_downward_scroll_positions_item_at_bottom(self):
        """When scrolling down, focused item should be at bottom of visible area"""
        config = Mock()
        config.LIST_DIALOG_HEIGHT_RATIO = 0.7
        config.LIST_DIALOG_MIN_HEIGHT = 15
        
        renderer = Mock()
        renderer.get_dimensions.return_value = (40, 80)
        
        dialog = SearchDialog(config, renderer)
        
        # Content height based on SearchDialog layout = 20
        content_height = 20
        
        # Create results
        dialog.results = [{'type': 'file', 'path': f'file{i}', 'relative_path': f'file{i}', 'match_info': f'file{i}'} 
                         for i in range(50)]
        
        # Simulate what happens during draw - cache the content height
        dialog._last_content_height = content_height
        
        # Start with scroll=10, selected=29 (at bottom of visible area)
        # Bottom position: scroll + content_height - 1 = 10 + 20 - 1 = 29
        dialog.scroll = 10
        dialog.selected = 29
        
        # Move down one item
        dialog.selected = 30
        dialog._adjust_scroll(len(dialog.results))
        
        # After scrolling down, selected should be at bottom: selected == scroll + content_height - 1
        expected_scroll = dialog.selected - content_height + 1
        assert dialog.scroll == expected_scroll, \
            f"Downward scroll: scroll ({dialog.scroll}) should be {expected_scroll} (selected {dialog.selected} - content_height {content_height} + 1)"
        assert dialog.scroll == 11
        assert dialog.selected == dialog.scroll + content_height - 1
        
    def test_scroll_symmetry_with_different_window_sizes(self):
        """Test scroll symmetry with various window sizes"""
        test_cases = [
            (25, 80, 9),    # Small: dialog_height=17, content_height=9
            (30, 80, 13),   # Medium: dialog_height=21, content_height=13
            (40, 80, 20),   # Large: dialog_height=28, content_height=20
            (50, 100, 27),  # Extra large: dialog_height=35, content_height=27
        ]
        
        for height, width, expected_content_height in test_cases:
            config = Mock()
            config.LIST_DIALOG_HEIGHT_RATIO = 0.7
            config.LIST_DIALOG_MIN_HEIGHT = 15
            
            renderer = Mock()
            renderer.get_dimensions.return_value = (height, width)
            
            dialog = SearchDialog(config, renderer)
            
            # Create results
            dialog.results = [{'type': 'file', 'path': f'file{i}', 'relative_path': f'file{i}', 'match_info': f'file{i}'} 
                             for i in range(50)]
            
            # Simulate what happens during draw - cache the content height
            dialog._last_content_height = expected_content_height
            
            # Test upward scroll
            dialog.scroll = 10
            dialog.selected = 10
            dialog.selected = 9
            dialog._adjust_scroll(len(dialog.results))
            assert dialog.scroll == dialog.selected, \
                f"Window {height}x{width}: Upward scroll failed"
            
            # Test downward scroll
            dialog.scroll = 10
            dialog.selected = 10 + expected_content_height - 1
            dialog.selected += 1
            dialog._adjust_scroll(len(dialog.results))
            expected_scroll = dialog.selected - expected_content_height + 1
            assert dialog.scroll == expected_scroll, \
                f"Window {height}x{width}: Downward scroll failed - scroll={dialog.scroll}, expected={expected_scroll}"
            assert dialog.selected == dialog.scroll + expected_content_height - 1, \
                f"Window {height}x{width}: Selected not at bottom - selected={dialog.selected}, scroll={dialog.scroll}, content_height={expected_content_height}"
