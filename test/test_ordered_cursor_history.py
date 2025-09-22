#!/usr/bin/env python3
"""
Test suite for ordered cursor history functionality

Tests the new ordered cursor history implementation with configurable limits,
proper insertion/deletion behavior, and persistence across sessions.
"""

import sys
import tempfile
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager
from tfm_pane_manager import PaneManager
from tfm_config import DefaultConfig


class TestConfig(DefaultConfig):
    """Test configuration with custom cursor history limit"""
    MAX_CURSOR_HISTORY_ENTRIES = 5  # Small limit for testing


def test_ordered_cursor_history_basic():
    """Test basic ordered cursor history functionality."""
    print("Testing basic ordered cursor history...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create state manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_ordered_basic")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Test saving cursor positions in order
        paths_and_files = [
            ("/path1", "file1.txt"),
            ("/path2", "file2.py"),
            ("/path3", "file3.log"),
            ("/path1", "different_file.txt"),  # Update existing path
            ("/path4", "file4.md"),
        ]
        
        print("Saving cursor positions in sequence...")
        for i, (path, filename) in enumerate(paths_and_files):
            time.sleep(0.01)  # Small delay to ensure different timestamps
            success = state_manager.save_path_cursor_position(path, filename, max_entries=10)
            assert success
            print(f"  {i+1}. {path} -> {filename}")
        
        # Check that path1 was updated (not duplicated)
        history = state_manager.get_ordered_path_cursor_history()
        paths_in_history = [entry['path'] for entry in history]
        
        # path1 should appear only once (the most recent entry)
        assert paths_in_history.count("/path1") == 1
        
        # The order should be: path2, path3, path1 (updated), path4
        expected_order = ["/path2", "/path3", "/path1", "/path4"]
        assert paths_in_history == expected_order
        
        # Check that path1 has the updated filename
        path1_entry = next(entry for entry in history if entry['path'] == "/path1")
        assert path1_entry['filename'] == "different_file.txt"
        
        print("✓ Basic ordered cursor history works correctly")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Basic test completed\n")


def test_cursor_history_size_limit():
    """Test that cursor history respects the configured size limit."""
    print("Testing cursor history size limit...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create state manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_size_limit")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Add more entries than the limit
        max_entries = 3
        paths_and_files = [
            ("/path1", "file1.txt"),
            ("/path2", "file2.py"),
            ("/path3", "file3.log"),
            ("/path4", "file4.md"),   # This should cause path1 to be removed
            ("/path5", "file5.json"), # This should cause path2 to be removed
        ]
        
        print(f"Adding {len(paths_and_files)} entries with limit of {max_entries}...")
        for i, (path, filename) in enumerate(paths_and_files):
            time.sleep(0.01)  # Ensure different timestamps
            success = state_manager.save_path_cursor_position(path, filename, max_entries=max_entries)
            assert success
            print(f"  {i+1}. {path} -> {filename}")
        
        # Check that only the most recent entries are kept
        history = state_manager.get_ordered_path_cursor_history()
        assert len(history) == max_entries
        
        # Should contain path3, path4, path5 (the last 3)
        paths_in_history = [entry['path'] for entry in history]
        expected_paths = ["/path3", "/path4", "/path5"]
        assert paths_in_history == expected_paths
        
        print(f"✓ Size limit enforced correctly: kept {len(history)} entries")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Size limit test completed\n")


def test_cursor_history_with_config():
    """Test cursor history with configuration from config class."""
    print("Testing cursor history with config...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directories
        test_dirs = []
        for i in range(7):  # More than the config limit of 5
            test_dir = Path(temp_dir) / f"test_dir_{i}"
            test_dir.mkdir()
            (test_dir / f"file_{i}.txt").touch()
            test_dirs.append(test_dir)
        
        # Create state manager and pane manager with test config
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_config")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        config = TestConfig()  # MAX_CURSOR_HISTORY_ENTRIES = 5
        pane_manager = PaneManager(config, test_dirs[0], test_dirs[1], state_manager)
        
        print(f"Config limit: {config.MAX_CURSOR_HISTORY_ENTRIES}")
        
        # Navigate through directories and save cursor positions
        for i, test_dir in enumerate(test_dirs):
            pane_manager.left_pane['path'] = test_dir
            pane_manager.left_pane['files'] = [test_dir / f"file_{i}.txt"]
            pane_manager.left_pane['selected_index'] = 0
            
            # Save cursor position
            pane_manager.save_cursor_position(pane_manager.left_pane)
            print(f"  Visited: {test_dir}")
            time.sleep(0.01)  # Ensure different timestamps
        
        # Check that only the configured number of entries are kept
        history = state_manager.get_ordered_path_cursor_history()
        assert len(history) <= config.MAX_CURSOR_HISTORY_ENTRIES
        
        # Should contain the last 5 directories
        paths_in_history = [entry['path'] for entry in history]
        expected_paths = [str(test_dirs[i]) for i in range(2, 7)]  # dirs 2-6
        assert paths_in_history == expected_paths
        
        print(f"✓ Config-based limit enforced: kept {len(history)} entries")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Config test completed\n")


def test_cursor_history_persistence_across_sessions():
    """Test that cursor history order persists across TFM sessions."""
    print("Testing cursor history persistence across sessions...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_state.db"
        
        # === Session 1: Create ordered history ===
        print("--- Session 1: Creating ordered history ---")
        state_manager1 = TFMStateManager("session1")
        state_manager1.db_path = db_path
        state_manager1._initialize_database()
        
        # Add entries in a specific order
        session1_entries = [
            ("/home/user", "document.txt"),
            ("/tmp", "temp_file.log"),
            ("/var/log", "system.log"),
            ("/home/user/projects", "main.py"),
        ]
        
        for i, (path, filename) in enumerate(session1_entries):
            time.sleep(0.01)
            state_manager1.save_path_cursor_position(path, filename, max_entries=10)
            print(f"  {i+1}. {path} -> {filename}")
        
        # Get the order from session 1
        history1 = state_manager1.get_ordered_path_cursor_history()
        paths1 = [entry['path'] for entry in history1]
        
        # Clean up session 1
        state_manager1.cleanup_session()
        print("Session 1 ended")
        
        # === Session 2: Verify order is preserved ===
        print("\n--- Session 2: Verifying preserved order ---")
        state_manager2 = TFMStateManager("session2")
        state_manager2.db_path = db_path
        
        # Load history from session 2
        history2 = state_manager2.get_ordered_path_cursor_history()
        paths2 = [entry['path'] for entry in history2]
        
        # Order should be preserved
        assert paths1 == paths2
        print(f"✓ Order preserved across sessions: {paths2}")
        
        # Add a new entry in session 2
        state_manager2.save_path_cursor_position("/new/path", "new_file.txt", max_entries=10)
        
        # Update an existing entry
        state_manager2.save_path_cursor_position("/home/user", "updated_document.txt", max_entries=10)
        
        # Check final order
        history_final = state_manager2.get_ordered_path_cursor_history()
        paths_final = [entry['path'] for entry in history_final]
        
        # Should be: /tmp, /var/log, /home/user/projects, /new/path, /home/user (updated)
        expected_final = ["/tmp", "/var/log", "/home/user/projects", "/new/path", "/home/user"]
        assert paths_final == expected_final
        
        # Check that /home/user has the updated filename
        user_entry = next(entry for entry in history_final if entry['path'] == "/home/user")
        assert user_entry['filename'] == "updated_document.txt"
        
        print(f"✓ Final order after updates: {paths_final}")
        
        # Clean up session 2
        state_manager2.cleanup_session()
        print("Session 2 ended")
        
        print("✓ Persistence across sessions test completed\n")


def test_backward_compatibility():
    """Test backward compatibility with old dict-based cursor history."""
    print("Testing backward compatibility...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_compat")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Simulate old dict-based format
        old_format = {
            "/old/path1": "old_file1.txt",
            "/old/path2": "old_file2.py",
            "/old/path3": "old_file3.log"
        }
        
        # Save in old format
        state_manager.set_state("path_cursor_history", old_format)
        print("Saved cursor history in old dict format")
        
        # Test loading with new methods
        filename1 = state_manager.load_path_cursor_position("/old/path1")
        assert filename1 == "old_file1.txt"
        
        all_positions = state_manager.get_all_path_cursor_positions()
        assert all_positions == old_format
        
        ordered_history = state_manager.get_ordered_path_cursor_history()
        assert len(ordered_history) == 3
        
        print("✓ Old format can be read with new methods")
        
        # Add a new entry (should convert to new format)
        state_manager.save_path_cursor_position("/new/path", "new_file.txt", max_entries=10)
        
        # Verify it's now in new format and old data is preserved
        final_history = state_manager.get_ordered_path_cursor_history()
        assert len(final_history) == 4  # 3 old + 1 new
        
        # Check that new entry is at the end
        assert final_history[-1]['path'] == "/new/path"
        assert final_history[-1]['filename'] == "new_file.txt"
        
        print("✓ Automatic conversion to new format works")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Backward compatibility test completed\n")


def test_pane_manager_integration():
    """Test PaneManager integration with ordered cursor history."""
    print("Testing PaneManager integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory structure
        test_dirs = []
        for i in range(3):
            test_dir = Path(temp_dir) / f"dir_{i}"
            test_dir.mkdir()
            
            # Create multiple files in each directory
            for j in range(5):
                (test_dir / f"file_{j}.txt").touch()
            
            test_dirs.append(test_dir)
        
        # Create state manager and pane manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_pane_integration")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        config = TestConfig()  # MAX_CURSOR_HISTORY_ENTRIES = 5
        pane_manager = PaneManager(config, test_dirs[0], test_dirs[1], state_manager)
        
        # Navigate through directories and set different cursor positions
        navigation_sequence = [
            (test_dirs[0], 2),  # file_2.txt
            (test_dirs[1], 4),  # file_4.txt
            (test_dirs[2], 1),  # file_1.txt
            (test_dirs[0], 3),  # file_3.txt (update dir_0)
        ]
        
        print("Navigation sequence:")
        for i, (directory, file_index) in enumerate(navigation_sequence):
            # Set up pane
            pane_manager.left_pane['path'] = directory
            pane_manager.left_pane['files'] = [directory / f"file_{j}.txt" for j in range(5)]
            pane_manager.left_pane['selected_index'] = file_index
            
            # Save cursor position
            pane_manager.save_cursor_position(pane_manager.left_pane)
            
            selected_file = pane_manager.left_pane['files'][file_index].name
            print(f"  {i+1}. {directory} -> {selected_file}")
            time.sleep(0.01)
        
        # Test restoration
        print("\nTesting cursor restoration:")
        for directory, expected_file_index in [(test_dirs[1], 4), (test_dirs[2], 1), (test_dirs[0], 3)]:
            # Navigate to directory
            pane_manager.left_pane['path'] = directory
            pane_manager.left_pane['files'] = [directory / f"file_{j}.txt" for j in range(5)]
            pane_manager.left_pane['selected_index'] = 0  # Start at first file
            
            # Restore cursor position
            restored = pane_manager.restore_cursor_position(pane_manager.left_pane, 20)
            
            assert restored is True
            assert pane_manager.left_pane['selected_index'] == expected_file_index
            
            restored_file = pane_manager.left_pane['files'][expected_file_index].name
            print(f"  ✓ {directory} -> {restored_file} (index {expected_file_index})")
        
        # Check final order in history
        history = state_manager.get_ordered_path_cursor_history()
        paths_in_order = [entry['path'] for entry in history]
        
        # Should be: dir_1, dir_2, dir_0 (updated last)
        expected_order = [str(test_dirs[1]), str(test_dirs[2]), str(test_dirs[0])]
        assert paths_in_order == expected_order
        
        print(f"✓ Final history order: {[Path(p).name for p in paths_in_order]}")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ PaneManager integration test completed\n")


def run_all_tests():
    """Run all ordered cursor history tests."""
    print("Running ordered cursor history tests...\n")
    
    try:
        test_ordered_cursor_history_basic()
        test_cursor_history_size_limit()
        test_cursor_history_with_config()
        test_cursor_history_persistence_across_sessions()
        test_backward_compatibility()
        test_pane_manager_integration()
        
        print("=" * 60)
        print("✓ All ordered cursor history tests passed!")
        print("\nKey features verified:")
        print("  • Proper chronological ordering maintained")
        print("  • Configurable size limits respected")
        print("  • Duplicate path handling (update in place)")
        print("  • Persistence across TFM sessions")
        print("  • Backward compatibility with old format")
        print("  • PaneManager integration")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)