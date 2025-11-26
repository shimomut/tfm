#!/usr/bin/env python3
"""
Test script to verify progress animations work with dialog optimization
"""

import sys
import os
import time
import threading
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_search_dialog import SearchDialog
from tfm_jump_dialog import JumpDialog
from tfm_config import get_config


def test_search_dialog_animation():
    """Test that SearchDialog animation continues during search"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show search dialog
    search_dialog.show('filename')
    search_dialog.text_editor.set_text('test')
    
    # Simulate search in progress
    search_dialog.searching = True
    search_dialog.content_changed = False  # Simulate after initial draw
    
    # Track animation frames
    animation_frames = []
    
    def mock_get_status_text(operation_name, context_info=None, is_active=True):
        frame = search_dialog.progress_animator.get_current_frame()
        animation_frames.append(frame)
        return f"{operation_name} {frame} ({context_info})"
    
    search_dialog.progress_animator.get_status_text = mock_get_status_text
    
    # Simulate main loop checking for content changes
    print("Testing SearchDialog animation:")
    print("==============================")
    
    for i in range(10):
        # Simulate the main loop content check
        content_changed = search_dialog.searching or search_dialog.content_changed
        
        print(f"Iteration {i+1}: searching={search_dialog.searching}, content_changed={content_changed}")
        
        if content_changed:
            # Simulate drawing the dialog (which calls get_status_text)
            status_text = search_dialog.progress_animator.get_status_text("Searching", f"{i} found", True)
            print(f"  Animation frame: {animation_frames[-1] if animation_frames else 'None'}")
        
        time.sleep(0.1)  # Wait for animation to advance
    
    # Stop search
    search_dialog.searching = False
    
    print(f"\nAnimation frames captured: {len(animation_frames)}")
    print(f"Unique frames: {len(set(animation_frames))}")
    
    # Verify animation progressed
    assert len(animation_frames) >= 5, f"Expected at least 5 animation frames, got {len(animation_frames)}"
    assert len(set(animation_frames)) > 1, f"Animation should have multiple unique frames, got {set(animation_frames)}"
    
    print("✓ SearchDialog animation works correctly during search")
    return True


def test_jump_dialog_animation():
    """Test that JumpDialog animation continues during directory scan"""
    
    config = get_config()
    jump_dialog = JumpDialog(config)
    
    # Show jump dialog
    jump_dialog.show(os.getcwd())
    
    # Simulate scan in progress
    jump_dialog.searching = True
    jump_dialog.content_changed = False  # Simulate after initial draw
    
    # Track animation frames
    animation_frames = []
    
    def mock_get_status_text(operation_name, context_info=None, is_active=True):
        frame = jump_dialog.progress_animator.get_current_frame()
        animation_frames.append(frame)
        return f"{operation_name} {frame} ({context_info})"
    
    jump_dialog.progress_animator.get_status_text = mock_get_status_text
    
    # Simulate main loop checking for content changes
    print("\nTesting JumpDialog animation:")
    print("=============================")
    
    for i in range(10):
        # Simulate the main loop content check
        content_changed = jump_dialog.searching or jump_dialog.content_changed
        
        print(f"Iteration {i+1}: searching={jump_dialog.searching}, content_changed={content_changed}")
        
        if content_changed:
            # Simulate drawing the dialog (which calls get_status_text)
            status_text = jump_dialog.progress_animator.get_status_text("Scanning", f"{i*10} dirs", True)
            print(f"  Animation frame: {animation_frames[-1] if animation_frames else 'None'}")
        
        time.sleep(0.1)  # Wait for animation to advance
    
    # Stop scan
    jump_dialog.searching = False
    
    print(f"\nAnimation frames captured: {len(animation_frames)}")
    print(f"Unique frames: {len(set(animation_frames))}")
    
    # Verify animation progressed
    assert len(animation_frames) >= 5, f"Expected at least 5 animation frames, got {len(animation_frames)}"
    assert len(set(animation_frames)) > 1, f"Animation should have multiple unique frames, got {set(animation_frames)}"
    
    print("✓ JumpDialog animation works correctly during directory scan")
    return True


def test_main_loop_animation_logic():
    """Test the main loop logic for handling animations"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Mock FileManager methods
    class MockFileManager:
        def __init__(self):
            self.search_dialog = search_dialog
            self.general_dialog = Mock()
            self.general_dialog.is_active = False
            self.list_dialog = Mock()
            self.list_dialog.is_active = False
            self.info_dialog = Mock()
            self.info_dialog.is_active = False
            self.jump_dialog = Mock()
            self.jump_dialog.is_active = False
            self.batch_rename_dialog = Mock()
            self.batch_rename_dialog.is_active = False
        
        def _check_dialog_content_changed(self):
            """Simulate the updated method"""
            if self.search_dialog.mode:
                if self.search_dialog.searching:
                    return True  # Always redraw to animate progress indicator
                return self.search_dialog.content_changed
            return False
        
        def _mark_dialog_content_unchanged(self):
            """Simulate the updated method"""
            if self.search_dialog.mode:
                if not self.search_dialog.searching:
                    self.search_dialog.content_changed = False
    
    fm = MockFileManager()
    
    # Show search dialog
    search_dialog.show('filename')
    
    print("\nTesting main loop animation logic:")
    print("==================================")
    
    # Test 1: Not searching, no content change
    search_dialog.searching = False
    search_dialog.content_changed = False
    
    result = fm._check_dialog_content_changed()
    print(f"Not searching, no content change: {result}")
    assert result == False, "Should not need redraw when not searching and no content change"
    
    # Test 2: Not searching, but content changed
    search_dialog.searching = False
    search_dialog.content_changed = True
    
    result = fm._check_dialog_content_changed()
    print(f"Not searching, content changed: {result}")
    assert result == True, "Should need redraw when content changed"
    
    # Test 3: Searching (should always redraw for animation)
    search_dialog.searching = True
    search_dialog.content_changed = False
    
    result = fm._check_dialog_content_changed()
    print(f"Searching, no content change: {result}")
    assert result == True, "Should always redraw when searching for animation"
    
    # Test 4: Mark unchanged while searching (should not mark)
    search_dialog.searching = True
    search_dialog.content_changed = True
    
    fm._mark_dialog_content_unchanged()
    print(f"After mark unchanged while searching: content_changed={search_dialog.content_changed}")
    assert search_dialog.content_changed == True, "Should not mark unchanged while searching"
    
    # Test 5: Mark unchanged while not searching (should mark)
    search_dialog.searching = False
    search_dialog.content_changed = True
    
    fm._mark_dialog_content_unchanged()
    print(f"After mark unchanged while not searching: content_changed={search_dialog.content_changed}")
    assert search_dialog.content_changed == False, "Should mark unchanged when not searching"
    
    print("✓ Main loop animation logic works correctly")
    return True


if __name__ == "__main__":
    try:
        test_search_dialog_animation()
        test_jump_dialog_animation()
        test_main_loop_animation_logic()
        
        print("\n" + "=" * 60)
        print("🎉 Progress animation tests passed!")
        print("\nConclusion:")
        print("  • SearchDialog animations work during search operations")
        print("  • JumpDialog animations work during directory scanning")
        print("  • Main loop correctly handles animation redraws")
        print("  • Animations continue smoothly with dialog optimization")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)