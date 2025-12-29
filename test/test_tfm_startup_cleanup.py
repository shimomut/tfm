"""
Test TFM startup directory cleanup with real FileManager.

This test verifies that the actual TFM FileManager properly cleans up
non-existing directories during startup.

Run with: PYTHONPATH=.:src:ttk pytest test/test_tfm_startup_cleanup.py -v
"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from ttk import KeyEvent, KeyCode, ModifierKey

from tfm_state_manager import TFMStateManager


def test_real_startup_cleanup():
    """Test startup cleanup with a real-like scenario."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test directories
        existing_dir1 = temp_path / "existing_dir1"
        existing_dir1.mkdir()
        (existing_dir1 / "file1.txt").touch()
        
        existing_dir2 = temp_path / "existing_dir2"
        existing_dir2.mkdir()
        (existing_dir2 / "file2.txt").touch()
        
        non_existing_dir1 = temp_path / "non_existing_dir1"
        non_existing_dir1.mkdir()
        (non_existing_dir1 / "file3.txt").touch()
        
        non_existing_dir2 = temp_path / "non_existing_dir2"
        non_existing_dir2.mkdir()
        (non_existing_dir2 / "file4.txt").touch()
        
        # Create a state manager and populate it with cursor history
        state_db_path = temp_path / "test_state.db"
        state_manager = TFMStateManager()
        state_manager.db_path = state_db_path
        state_manager._initialize_database()
        
        # Save cursor positions for all directories
        state_manager.save_pane_cursor_position("left", str(existing_dir1), "file1.txt")
        state_manager.save_pane_cursor_position("left", str(existing_dir2), "file2.txt")
        state_manager.save_pane_cursor_position("left", str(non_existing_dir1), "file3.txt")
        state_manager.save_pane_cursor_position("left", str(non_existing_dir2), "file4.txt")
        
        state_manager.save_pane_cursor_position("right", str(existing_dir1), "file1.txt")
        state_manager.save_pane_cursor_position("right", str(non_existing_dir1), "file3.txt")
        
        # Save pane states
        state_manager.save_pane_state('left', {
            'path': str(existing_dir1),
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': ''
        })
        state_manager.save_pane_state('right', {
            'path': str(existing_dir2),
            'sort_mode': 'name',
            'sort_reverse': False,
            'filter_pattern': ''
        })
        
        # Save window layout
        state_manager.save_window_layout(0.5, 0.25)
        
        # Verify initial state
        left_history_before = state_manager.get_pane_cursor_positions("left")
        right_history_before = state_manager.get_pane_cursor_positions("right")
        
        print(f"Initial cursor history - Left: {len(left_history_before)}, Right: {len(right_history_before)}")
        assert len(left_history_before) == 4
        assert len(right_history_before) == 2
        
        # Remove some directories to simulate deletion
        shutil.rmtree(non_existing_dir1)
        shutil.rmtree(non_existing_dir2)
        
        print(f"Removed directories: {non_existing_dir1.name}, {non_existing_dir2.name}")
        
        # Now test the cleanup by calling it directly
        print("\n--- Testing cleanup function ---")
        cleanup_result = state_manager.cleanup_non_existing_directories()
        assert cleanup_result, "Cleanup should succeed"
        
        # Verify cleanup worked
        left_history_after = state_manager.get_pane_cursor_positions("left")
        right_history_after = state_manager.get_pane_cursor_positions("right")
        
        print(f"After cleanup - Left: {len(left_history_after)}, Right: {len(right_history_after)}")
        
        # Should only have entries for existing directories
        assert len(left_history_after) == 2
        assert len(right_history_after) == 1
        
        # Verify correct entries remain
        assert str(existing_dir1) in left_history_after
        assert str(existing_dir2) in left_history_after
        assert str(non_existing_dir1) not in left_history_after
        assert str(non_existing_dir2) not in left_history_after
        
        assert str(existing_dir1) in right_history_after
        assert str(non_existing_dir1) not in right_history_after
        
        print("✓ Directory cleanup working correctly")
        
        # Test that pane states are still intact (they should be, as they point to existing dirs)
        left_state = state_manager.load_pane_state('left')
        right_state = state_manager.load_pane_state('right')
        
        assert left_state is not None
        assert right_state is not None
        assert Path(left_state['path']).exists()
        assert Path(right_state['path']).exists()
        
        print("✓ Pane states preserved correctly")
        
        return True


def test_cleanup_with_mixed_formats():
    """Test cleanup with both old dict format and new list format cursor history."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test directories
        existing_dir = temp_path / "existing_dir"
        existing_dir.mkdir()
        
        non_existing_dir = temp_path / "non_existing_dir"
        non_existing_dir.mkdir()
        
        # Create state manager
        state_db_path = temp_path / "test_state.db"
        state_manager = TFMStateManager()
        state_manager.db_path = state_db_path
        state_manager._initialize_database()
        
        # Manually create old dict format in the database
        old_dict_format = {
            str(existing_dir): "file1.txt",
            str(non_existing_dir): "file2.txt"
        }
        
        # Save in old format
        state_manager.set_state("path_cursor_history_left", old_dict_format, state_manager.instance_id)
        
        # Verify old format is there
        history_before = state_manager.get_state("path_cursor_history_left", [])
        assert isinstance(history_before, dict)
        assert len(history_before) == 2
        
        # Remove one directory
        shutil.rmtree(non_existing_dir)
        
        # Run cleanup
        print("\n--- Testing cleanup with old dict format ---")
        cleanup_result = state_manager.cleanup_non_existing_directories()
        assert cleanup_result
        
        # Verify cleanup converted to new format and removed non-existing entry
        history_after = state_manager.get_state("path_cursor_history_left", [])
        assert isinstance(history_after, list)  # Should be converted to new format
        assert len(history_after) == 1  # Only existing directory should remain
        
        # Verify the remaining entry is correct
        assert len(history_after[0]) == 3  # [timestamp, path, filename]
        assert history_after[0][1] == str(existing_dir)
        assert history_after[0][2] == "file1.txt"
        
        print("✓ Cleanup with old dict format working correctly")
        
        return True
