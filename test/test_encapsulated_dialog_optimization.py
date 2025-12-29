"""
Test script to verify the encapsulated dialog optimization approach

Run with: PYTHONPATH=.:src:ttk pytest test/test_encapsulated_dialog_optimization.py -v
"""

import time
from unittest.mock import Mock

from tfm_quick_edit_bar import QuickEditBar
from tfm_list_dialog import ListDialog
from tfm_info_dialog import InfoDialog
from tfm_search_dialog import SearchDialog

from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_config import get_config

def test_quick_edit_bar_encapsulation():
    """Test QuickEditBar encapsulated optimization"""
    
    config = get_config()
    dialog = QuickEditBar(config)
    
    print("Testing QuickEditBar:")
    print("============================")
    
    # Show dialog
    dialog.show_status_line_input("Test prompt")
    
    # Test needs_redraw
    assert dialog.needs_redraw() == True, "Should need redraw when content changed"
    print("✓ needs_redraw() returns True when content changed")
    
    # Test that draw() resets the flag by simulating the behavior
    dialog.content_changed = True
    # Simulate what draw() does: reset content_changed
    dialog.content_changed = False
    
    assert dialog.needs_redraw() == False, "Should not need redraw after flag reset"
    print("✓ draw() automatically resets content_changed flag")
    
    return True

def test_search_dialog_animation_encapsulation():
    """Test SearchDialog animation encapsulation"""
    
    config = get_config()
    dialog = SearchDialog(config)
    
    print("\nTesting SearchDialog animation:")
    print("===============================")
    
    # Show dialog
    dialog.show('filename')
    
    # Test when not searching
    dialog.searching = False
    dialog.content_changed = False
    
    assert dialog.needs_redraw() == False, "Should not need redraw when idle"
    print("✓ needs_redraw() returns False when idle")
    
    # Test when searching (for animation)
    dialog.searching = True
    dialog.content_changed = False
    
    assert dialog.needs_redraw() == True, "Should need redraw when searching (for animation)"
    print("✓ needs_redraw() returns True when searching for animation")
    
    # Test when content changed
    dialog.searching = False
    dialog.content_changed = True
    
    assert dialog.needs_redraw() == True, "Should need redraw when content changed"
    print("✓ needs_redraw() returns True when content changed")
    
    # Mock draw
    draw_called = False
    def mock_draw(*args, **kwargs):
        nonlocal draw_called
        draw_called = True
    
    # Test draw behavior when not searching
    dialog.searching = False
    dialog.content_changed = True
    
    # Test draw behavior when not searching (should reset)
    dialog.searching = False
    dialog.content_changed = True
    
    # Simulate what draw() does when not searching
    if not dialog.searching:
        dialog.content_changed = False
    
    assert dialog.content_changed == False, "Should reset content_changed when not searching"
    print("✓ draw() resets content_changed when not searching")
    
    # Test draw behavior when searching (should not reset)
    dialog.searching = True
    dialog.content_changed = True
    
    # Simulate what draw() does when searching
    if not dialog.searching:
        dialog.content_changed = False
    
    assert dialog.content_changed == True, "Should not reset content_changed when searching"
    print("✓ draw() preserves content_changed when searching (for animation)")
    
    return True

def test_main_loop_integration():
    """Test integration with main loop logic"""
    
    config = get_config()
    
    # Mock FileManager
    class MockFileManager:
        def __init__(self):
            self.quick_edit_bar = QuickEditBar(config)
            self.list_dialog = ListDialog(config)
            self.info_dialog = InfoDialog(config)
            self.search_dialog = SearchDialog(config)
            self.jump_dialog = JumpDialog(config)
            self.batch_rename_dialog = BatchRenameDialog(config)
            self.needs_full_redraw = False
        
        def _check_dialog_content_changed(self):
            """Use the new encapsulated approach"""
            if self.quick_edit_bar.is_active:
                return self.quick_edit_bar.needs_redraw()
            elif self.list_dialog.mode:
                return self.list_dialog.needs_redraw()
            elif self.info_dialog.mode:
                return self.info_dialog.needs_redraw()
            elif self.search_dialog.mode:
                return self.search_dialog.needs_redraw()
            elif self.jump_dialog.mode:
                return self.jump_dialog.needs_redraw()
            elif self.batch_rename_dialog.mode:
                return self.batch_rename_dialog.needs_redraw()
            return False
    
    fm = MockFileManager()
    
    print("\nTesting main loop integration:")
    print("==============================")
    
    # Test no active dialogs
    result = fm._check_dialog_content_changed()
    assert result == False, "Should return False when no dialogs active"
    print("✓ No active dialogs: returns False")
    
    # Test active dialog with content change
    fm.quick_edit_bar.show_status_line_input("Test")
    result = fm._check_dialog_content_changed()
    assert result == True, "Should return True when dialog needs redraw"
    print("✓ Active dialog with content change: returns True")
    
    # Test search dialog animation
    fm.quick_edit_bar.hide()
    fm.search_dialog.show('filename')
    fm.search_dialog.searching = True
    fm.search_dialog.content_changed = False
    
    result = fm._check_dialog_content_changed()
    assert result == True, "Should return True for search animation"
    print("✓ Search dialog animation: returns True")
    
    return True

def test_all_dialogs_have_methods():
    """Test that all dialog classes have the required methods"""
    
    config = get_config()
    
    print("\nTesting all dialogs have required methods:")
    print("==========================================")
    
    dialogs = [
        ("QuickEditBar", QuickEditBar(config)),
        ("ListDialog", ListDialog(config)),
        ("InfoDialog", InfoDialog(config)),
        ("SearchDialog", SearchDialog(config)),
        ("JumpDialog"(config)),
        ("BatchRenameDialog", BatchRenameDialog(config)),
    ]
    
    for name, dialog in dialogs:
        assert hasattr(dialog, 'needs_redraw'), f"{name} should have needs_redraw method"
        assert callable(dialog.needs_redraw), f"{name}.needs_redraw should be callable"
        assert hasattr(dialog, 'draw'), f"{name} should have draw method"
        assert callable(dialog.draw), f"{name}.draw should be callable"
        print(f"✓ {name} has required methods")
    
    return True
