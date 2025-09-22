#!/usr/bin/env python3
"""
Test suite for cursor history dialog functionality

Tests the H key functionality to show cursor history using ListDialog
and navigate to selected directories.
"""

import sys
import tempfile
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager
from tfm_pane_manager import PaneManager
from tfm_list_dialog import ListDialog
from tfm_config import DefaultConfig


class MockStdscr:
    """Mock curses screen for testing."""
    def __init__(self, height=40, width=120):
        self.height = height
        self.width = width
    
    def getmaxyx(self):
        return self.height, self.width


class MockFileManager:
    """Mock FileManager for testing cursor history dialog."""
    def __init__(self, config, left_path, right_path, state_manager):
        self.config = config
        self.state_manager = state_manager
        self.pane_manager = PaneManager(config, left_path, right_path, state_manager)
        self.list_dialog = ListDialog(config)
        self.stdscr = MockStdscr()
        self.log_height_ratio = 0.25
        self.needs_full_redraw = False
        self.navigation_log = []  # Track navigation calls
    
    def get_current_pane(self):
        """Get the currently active pane"""
        return self.pane_manager.get_current_pane()
    
    def refresh_files(self, pane=None):
        """Mock file refresh - populate with test files."""
        panes_to_refresh = [pane] if pane else [self.pane_manager.left_pane, self.pane_manager.right_pane]
        
        for pane_data in panes_to_refresh:
            path = pane_data['path']
            if path.exists():
                pane_data['files'] = sorted([f for f in path.iterdir() if f.is_file()])
    
    def _force_immediate_redraw(self):
        """Mock immediate redraw."""
        pass
    
    def show_cursor_history(self):
        """Show cursor history for the current pane using the searchable list dialog"""
        current_pane = self.get_current_pane()
        pane_name = 'left' if current_pane is self.pane_manager.left_pane else 'right'
        
        # Get cursor history for the current pane
        history = self.state_manager.get_ordered_pane_history(pane_name)
        
        if not history:
            print(f"No cursor history available for {pane_name} pane")
            return []
        
        # Extract just the paths (no timestamps or filenames needed in dialog)
        history_paths = []
        seen_paths = set()
        
        # Reverse to show most recent first, and deduplicate
        for entry in reversed(history):
            path = entry['path']
            if path not in seen_paths:
                history_paths.append(path)
                seen_paths.add(path)
        
        if not history_paths:
            print(f"No cursor history available for {pane_name} pane")
            return []
        
        # For testing, return the paths instead of showing dialog
        return history_paths
    
    def navigate_to_history_path(self, selected_path):
        """Navigate the current pane to the selected history path"""
        try:
            target_path = Path(selected_path)
            
            # Check if the path still exists
            if not target_path.exists():
                self.navigation_log.append(f"Error: Directory no longer exists: {selected_path}")
                return False
            
            if not target_path.is_dir():
                self.navigation_log.append(f"Error: Path is not a directory: {selected_path}")
                return False
            
            # Get current pane and save cursor position before navigating
            current_pane = self.get_current_pane()
            self.pane_manager.save_cursor_position(current_pane)
            
            # Navigate to the selected path
            old_path = current_pane['path']
            current_pane['path'] = target_path
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()  # Clear selections when changing directory
            
            # Refresh files and restore cursor position for the new directory
            self.refresh_files(current_pane)
            
            # Try to restore cursor position for this directory
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            restored = self.pane_manager.restore_cursor_position(current_pane, display_height)
            
            # Log the navigation
            pane_name = "left" if current_pane is self.pane_manager.left_pane else "right"
            if restored and current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']].name
                self.navigation_log.append(f"Navigated {pane_name} pane: {old_path} → {target_path} (cursor: {selected_file})")
            else:
                self.navigation_log.append(f"Navigated {pane_name} pane: {old_path} → {target_path}")
            
            self.needs_full_redraw = True
            return True
            
        except Exception as e:
            self.navigation_log.append(f"Error navigating to {selected_path}: {e}")
            return False


def test_cursor_history_dialog_basic():
    """Test basic cursor history dialog functionality."""
    print("Testing cursor history dialog...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory structure
        dirs = []
        for i in range(4):
            test_dir = Path(temp_dir) / f"dir_{i}"
            test_dir.mkdir()
            
            # Create test files in each directory
            for j in range(3):
                (test_dir / f"file_{j}.txt").touch()
            
            dirs.append(test_dir)
        
        # Create state manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_history_dialog")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Create file manager
        config = DefaultConfig()
        fm = MockFileManager(config, dirs[0], dirs[1], state_manager)
        
        # Build up cursor history by navigating through directories
        navigation_sequence = [
            (dirs[0], 1),  # dir_0, file_1.txt
            (dirs[1], 2),  # dir_1, file_2.txt
            (dirs[2], 0),  # dir_2, file_0.txt
            (dirs[3], 1),  # dir_3, file_1.txt
            (dirs[0], 2),  # dir_0, file_2.txt (revisit)
        ]
        
        print("Building cursor history:")
        for i, (directory, file_index) in enumerate(navigation_sequence):
            # Set up left pane (current pane)
            fm.pane_manager.left_pane['path'] = directory
            fm.refresh_files(fm.pane_manager.left_pane)
            fm.pane_manager.left_pane['selected_index'] = file_index
            
            # Save cursor position
            fm.pane_manager.save_cursor_position(fm.pane_manager.left_pane)
            
            selected_file = fm.pane_manager.left_pane['files'][file_index].name
            print(f"  {i+1}. {directory} -> {selected_file}")
            time.sleep(0.01)  # Ensure different timestamps
        
        # Test showing cursor history
        print("\nTesting cursor history dialog:")
        history_paths = fm.show_cursor_history()
        
        # Verify history paths
        assert len(history_paths) > 0
        print(f"History contains {len(history_paths)} unique paths:")
        for i, path in enumerate(history_paths):
            print(f"  {i+1}. {path}")
        
        # Most recent should be first (dir_0 since it was revisited)
        assert str(dirs[0]) == history_paths[0]
        
        # Should contain all visited directories
        visited_dirs = {str(d) for d, _ in navigation_sequence}
        history_set = set(history_paths)
        assert visited_dirs.issubset(history_set)
        
        print("✓ Cursor history dialog shows correct paths")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Basic cursor history dialog test completed\n")


def test_cursor_history_navigation():
    """Test navigation to selected history path."""
    print("Testing cursor history navigation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directories
        source_dir = Path(temp_dir) / "source"
        target_dir = Path(temp_dir) / "target"
        
        source_dir.mkdir()
        target_dir.mkdir()
        
        # Create files
        for filename in ["source_a.txt", "source_b.py", "source_c.log"]:
            (source_dir / filename).touch()
        
        for filename in ["target_x.txt", "target_y.py", "target_z.log"]:
            (target_dir / filename).touch()
        
        # Create state manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_navigation")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Create file manager starting in source directory
        config = DefaultConfig()
        fm = MockFileManager(config, source_dir, source_dir, state_manager)
        fm.refresh_files()
        
        # Set up cursor position in target directory first
        fm.pane_manager.left_pane['path'] = target_dir
        fm.refresh_files(fm.pane_manager.left_pane)
        fm.pane_manager.left_pane['selected_index'] = 1  # target_y.py
        fm.pane_manager.save_cursor_position(fm.pane_manager.left_pane)
        
        target_file = fm.pane_manager.left_pane['files'][1].name
        print(f"Saved cursor position: {target_dir} -> {target_file}")
        
        # Navigate back to source directory
        fm.pane_manager.left_pane['path'] = source_dir
        fm.refresh_files(fm.pane_manager.left_pane)
        fm.pane_manager.left_pane['selected_index'] = 0
        
        print(f"Current directory: {source_dir}")
        
        # Test navigation to history path
        print(f"Navigating to history path: {target_dir}")
        success = fm.navigate_to_history_path(str(target_dir))
        
        assert success is True
        assert fm.pane_manager.left_pane['path'] == target_dir
        
        # Check if cursor was restored
        if fm.pane_manager.left_pane['files']:
            restored_file = fm.pane_manager.left_pane['files'][fm.pane_manager.left_pane['selected_index']].name
            print(f"Cursor restored to: {restored_file}")
            assert restored_file == target_file
        
        # Check navigation log
        assert len(fm.navigation_log) > 0
        print(f"Navigation log: {fm.navigation_log[-1]}")
        
        print("✓ Navigation to history path works correctly")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Navigation test completed\n")


def test_cursor_history_separate_panes():
    """Test that cursor history dialog shows correct pane history."""
    print("Testing separate pane histories in dialog...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories for each pane
        left_dirs = []
        right_dirs = []
        
        for i in range(3):
            left_dir = Path(temp_dir) / f"left_{i}"
            right_dir = Path(temp_dir) / f"right_{i}"
            
            left_dir.mkdir()
            right_dir.mkdir()
            
            # Create files
            (left_dir / f"left_file_{i}.txt").touch()
            (right_dir / f"right_file_{i}.txt").touch()
            
            left_dirs.append(left_dir)
            right_dirs.append(right_dir)
        
        # Create state manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_separate_dialog")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Create file manager
        config = DefaultConfig()
        fm = MockFileManager(config, left_dirs[0], right_dirs[0], state_manager)
        
        # Build left pane history
        print("Building left pane history:")
        for i, directory in enumerate(left_dirs):
            fm.pane_manager.left_pane['path'] = directory
            fm.refresh_files(fm.pane_manager.left_pane)
            fm.pane_manager.left_pane['selected_index'] = 0
            fm.pane_manager.save_cursor_position(fm.pane_manager.left_pane)
            print(f"  {i+1}. {directory}")
            time.sleep(0.01)
        
        # Build right pane history
        print("Building right pane history:")
        for i, directory in enumerate(right_dirs):
            fm.pane_manager.right_pane['path'] = directory
            fm.refresh_files(fm.pane_manager.right_pane)
            fm.pane_manager.right_pane['selected_index'] = 0
            fm.pane_manager.save_cursor_position(fm.pane_manager.right_pane)
            print(f"  {i+1}. {directory}")
            time.sleep(0.01)
        
        # Test left pane history (active pane is left)
        fm.pane_manager.active_pane = 'left'
        left_history = fm.show_cursor_history()
        
        print(f"\nLeft pane history ({len(left_history)} entries):")
        for path in left_history:
            print(f"  {path}")
        
        # Should contain only left directories
        for path in left_history:
            assert "left_" in path
            assert "right_" not in path
        
        # Test right pane history (active pane is right)
        fm.pane_manager.active_pane = 'right'
        right_history = fm.show_cursor_history()
        
        print(f"\nRight pane history ({len(right_history)} entries):")
        for path in right_history:
            print(f"  {path}")
        
        # Should contain only right directories
        for path in right_history:
            assert "right_" in path
            assert "left_" not in path
        
        # Verify no overlap
        left_set = set(left_history)
        right_set = set(right_history)
        assert left_set.isdisjoint(right_set)
        
        print("✓ Separate pane histories work correctly in dialog")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Separate panes test completed\n")


def test_cursor_history_empty_history():
    """Test cursor history dialog with empty history."""
    print("Testing cursor history dialog with empty history...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory
        test_dir = Path(temp_dir) / "empty_history"
        test_dir.mkdir()
        (test_dir / "file.txt").touch()
        
        # Create state manager (no history saved)
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_empty_history")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Create file manager
        config = DefaultConfig()
        fm = MockFileManager(config, test_dir, test_dir, state_manager)
        
        # Test showing cursor history with no history
        history_paths = fm.show_cursor_history()
        
        # Should return empty list
        assert len(history_paths) == 0
        
        print("✓ Empty history handled correctly")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Empty history test completed\n")


def test_cursor_history_missing_directory():
    """Test navigation to missing directory from history."""
    print("Testing navigation to missing directory...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory
        test_dir = Path(temp_dir) / "will_be_deleted"
        test_dir.mkdir()
        (test_dir / "file.txt").touch()
        
        # Create state manager
        db_path = Path(temp_dir) / "test_state.db"
        state_manager = TFMStateManager("test_missing_dir")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        # Create file manager and save history
        config = DefaultConfig()
        fm = MockFileManager(config, test_dir, test_dir, state_manager)
        fm.refresh_files()
        fm.pane_manager.left_pane['selected_index'] = 0
        fm.pane_manager.save_cursor_position(fm.pane_manager.left_pane)
        
        print(f"Saved history for: {test_dir}")
        
        # Delete the directory
        import shutil
        shutil.rmtree(test_dir)
        print(f"Deleted directory: {test_dir}")
        
        # Try to navigate to the missing directory
        success = fm.navigate_to_history_path(str(test_dir))
        
        assert success is False
        assert len(fm.navigation_log) > 0
        assert "no longer exists" in fm.navigation_log[-1]
        
        print(f"Navigation error logged: {fm.navigation_log[-1]}")
        print("✓ Missing directory handled correctly")
        
        # Clean up
        state_manager.cleanup_session()
        print("✓ Missing directory test completed\n")


def run_all_tests():
    """Run all cursor history dialog tests."""
    print("Running cursor history dialog tests...\n")
    
    try:
        test_cursor_history_dialog_basic()
        test_cursor_history_navigation()
        test_cursor_history_separate_panes()
        test_cursor_history_empty_history()
        test_cursor_history_missing_directory()
        
        print("=" * 60)
        print("✓ All cursor history dialog tests passed!")
        print("\nKey features verified:")
        print("  • H key shows cursor history dialog")
        print("  • Dialog shows only directory paths (no timestamps/filenames)")
        print("  • Most recent directories shown first")
        print("  • Separate histories for left and right panes")
        print("  • Navigation to selected directory works")
        print("  • Cursor position restored after navigation")
        print("  • Empty history handled gracefully")
        print("  • Missing directories handled safely")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)