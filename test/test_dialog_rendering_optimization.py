#!/usr/bin/env python3
"""
Test script to verify dialog rendering optimization
"""

import sys
import os
import time
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_main import FileManager
from tfm_config import get_config
from ttk import KeyCode
from ttk.input_event import InputEvent


def test_dialog_rendering_optimization():
    """Test that dialogs only redraw when content changes"""
    
    # Mock curses for testing
    mock_stdscr = Mock()
    mock_stdscr.getmaxyx.return_value = (24, 80)
    mock_stdscr.getch.return_value = -1  # Timeout
    
    # Create file manager instance
    config = get_config()
    fm = FileManager(mock_stdscr)
    
    # Test 1: Check that content_changed flag is properly initialized
    assert hasattr(fm.general_dialog, 'content_changed'), "General dialog should have content_changed attribute"
    assert hasattr(fm.list_dialog, 'content_changed'), "List dialog should have content_changed attribute"
    assert hasattr(fm.info_dialog, 'content_changed'), "Info dialog should have content_changed attribute"
    assert hasattr(fm.search_dialog, 'content_changed'), "Search dialog should have content_changed attribute"
    assert hasattr(fm.jump_dialog, 'content_changed'), "Jump dialog should have content_changed attribute"
    assert hasattr(fm.batch_rename_dialog, 'content_changed'), "Batch rename dialog should have content_changed attribute"
    
    # Test 2: Check that showing a dialog marks content as changed
    fm.general_dialog.show_status_line_input("Test prompt")
    assert fm.general_dialog.content_changed == True, "Content should be marked as changed when showing dialog"
    
    # Test 3: Check that _check_dialog_content_changed works
    assert fm._check_dialog_content_changed() == True, "Should detect content change when dialog is active"
    
    # Test 4: Check that marking content as unchanged works
    fm._mark_dialog_content_unchanged()
    assert fm.general_dialog.content_changed == False, "Content should be marked as unchanged"
    assert fm._check_dialog_content_changed() == False, "Should not detect content change after marking unchanged"
    
    # Test 5: Check that text input marks content as changed
    fm.general_dialog.handle_input(InputEvent(ord('a'), 'a'))  # Type a character
    assert fm.general_dialog.content_changed == True, "Content should be marked as changed after text input"
    
    # Test 6: Check list dialog content change tracking
    fm.general_dialog.hide()
    fm.list_dialog.show("Test List", ["item1", "item2"], None)
    assert fm.list_dialog.content_changed == True, "List dialog content should be marked as changed when showing"
    
    fm._mark_dialog_content_unchanged()
    assert fm.list_dialog.content_changed == False, "List dialog content should be marked as unchanged"
    
    # Simulate navigation
    fm.list_dialog.handle_input(InputEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE))
    assert fm.list_dialog.content_changed == True, "List dialog content should be marked as changed after navigation"
    
    print("✓ All dialog rendering optimization tests passed!")
    return True


def test_performance_improvement():
    """Test that the optimization actually reduces rendering calls"""
    
    # Mock curses and track draw calls
    mock_stdscr = Mock()
    mock_stdscr.getmaxyx.return_value = (24, 80)
    mock_stdscr.getch.return_value = -1  # Timeout
    
    draw_call_count = 0
    
    def mock_draw(stdscr, safe_addstr_func):
        nonlocal draw_call_count
        draw_call_count += 1
    
    # Create file manager instance
    fm = FileManager(mock_stdscr)
    
    # Mock the dialog draw methods to count calls
    fm.general_dialog.draw = mock_draw
    
    # Show a dialog
    fm.general_dialog.show_status_line_input("Test prompt")
    
    # Reset counter
    draw_call_count = 0
    
    # Simulate multiple main loop iterations without content changes
    for i in range(10):
        fm._mark_dialog_content_unchanged()  # Mark as unchanged
        
        # Simulate the main loop dialog drawing logic
        dialog_content_changed = fm._check_dialog_content_changed()
        if dialog_content_changed or fm.needs_full_redraw:
            if fm.general_dialog.is_active:
                fm.general_dialog.draw(mock_stdscr, fm.safe_addstr)
            fm._mark_dialog_content_unchanged()
    
    # Should not have drawn since content didn't change
    assert draw_call_count == 0, f"Expected 0 draw calls, got {draw_call_count}"
    
    # Now simulate content change
    fm.general_dialog.content_changed = True
    dialog_content_changed = fm._check_dialog_content_changed()
    if dialog_content_changed or fm.needs_full_redraw:
        if fm.general_dialog.is_active:
            fm.general_dialog.draw(mock_stdscr, fm.safe_addstr)
        fm._mark_dialog_content_unchanged()
    
    # Should have drawn once since content changed
    assert draw_call_count == 1, f"Expected 1 draw call, got {draw_call_count}"
    
    print("✓ Performance improvement test passed!")
    return True


if __name__ == "__main__":
    try:
        test_dialog_rendering_optimization()
        test_performance_improvement()
        print("\n🎉 All tests passed! Dialog rendering optimization is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)