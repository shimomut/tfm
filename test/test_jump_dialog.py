#!/usr/bin/env python3
"""
Test Jump Dialog Component
"""

import unittest
import tempfile
import threading
import time
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_jump_dialog import JumpDialog, JumpDialogHelpers
from tfm_config import DefaultConfig
from tfm_pane_manager import PaneManager


class MockPaneManager:
    """Mock pane manager for testing"""
    
    def __init__(self):
        self.active_pane = 'left'
        self.panes = {
            'left': {
                'path': Path.cwd(),
                'selected_index': 0,
                'scroll_offset': 0,
                'selected_files': set()
            }
        }
    
    def get_current_pane(self):
        return self.panes[self.active_pane]


class TestJumpDialog(unittest.TestCase):
    """Test cases for JumpDialog component"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = DefaultConfig()
        self.jump_dialog = JumpDialog(self.config)
        self.temp_dir = None
        
    def tearDown(self):
        """Clean up test environment"""
        if self.jump_dialog.mode:
            self.jump_dialog.exit()
        
        # Clean up temp directory
        if self.temp_dir:
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def create_test_directory_structure(self):
        """Create a temporary directory structure for testing"""
        self.temp_dir = tempfile.mkdtemp()
        temp_path = Path(self.temp_dir)
        
        # Create test directory structure
        (temp_path / "dir1").mkdir()
        (temp_path / "dir2").mkdir()
        (temp_path / "dir1" / "subdir1").mkdir()
        (temp_path / "dir1" / "subdir2").mkdir()
        (temp_path / "dir2" / "subdir3").mkdir()
        
        # Create some files (should be ignored by jump dialog)
        (temp_path / "file1.txt").write_text("test")
        (temp_path / "dir1" / "file2.txt").write_text("test")
        
        return temp_path
    
    def test_jump_dialog_initialization(self):
        """Test jump dialog initialization"""
        self.assertFalse(self.jump_dialog.mode)
        self.assertEqual(len(self.jump_dialog.directories), 0)
        self.assertEqual(len(self.jump_dialog.filtered_directories), 0)
        self.assertEqual(self.jump_dialog.selected, 0)
        self.assertEqual(self.jump_dialog.scroll, 0)
        self.assertFalse(self.jump_dialog.searching)
    
    def test_jump_dialog_show_and_exit(self):
        """Test showing and exiting jump dialog"""
        test_path = self.create_test_directory_structure()
        
        # Show dialog
        self.jump_dialog.show(test_path)
        self.assertTrue(self.jump_dialog.mode)
        self.assertTrue(self.jump_dialog.searching)
        
        # Wait a moment for scanning to start
        time.sleep(0.1)
        
        # Exit dialog
        self.jump_dialog.exit()
        self.assertFalse(self.jump_dialog.mode)
        self.assertFalse(self.jump_dialog.searching)
        self.assertEqual(len(self.jump_dialog.directories), 0)
        self.assertEqual(len(self.jump_dialog.filtered_directories), 0)
    
    def test_directory_scanning(self):
        """Test directory scanning functionality"""
        test_path = self.create_test_directory_structure()
        
        # Show dialog and wait for scanning to complete
        self.jump_dialog.show(test_path)
        
        # Wait for scanning to complete
        max_wait = 5.0  # Maximum wait time in seconds
        start_time = time.time()
        
        while self.jump_dialog.searching and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Check that directories were found
        with self.jump_dialog.scan_lock:
            directories = self.jump_dialog.directories.copy()
            filtered_directories = self.jump_dialog.filtered_directories.copy()
        
        # Should find at least the root directory and subdirectories
        self.assertGreater(len(directories), 0)
        self.assertEqual(len(directories), len(filtered_directories))  # No filter applied
        
        # Check that root directory is included
        self.assertIn(test_path, directories)
        
        # Check that subdirectories are included
        expected_dirs = [
            test_path / "dir1",
            test_path / "dir2", 
            test_path / "dir1" / "subdir1",
            test_path / "dir1" / "subdir2",
            test_path / "dir2" / "subdir3"
        ]
        
        for expected_dir in expected_dirs:
            self.assertIn(expected_dir, directories)
    
    def test_directory_filtering(self):
        """Test directory filtering functionality"""
        test_path = self.create_test_directory_structure()
        
        # Show dialog and wait for scanning to complete
        self.jump_dialog.show(test_path)
        
        # Wait for scanning to complete
        max_wait = 5.0
        start_time = time.time()
        
        while self.jump_dialog.searching and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Apply filter
        self.jump_dialog.search_editor.text = "dir1"
        self.jump_dialog._filter_directories()
        
        with self.jump_dialog.scan_lock:
            filtered_directories = self.jump_dialog.filtered_directories.copy()
        
        # Should only show directories containing "dir1"
        for directory in filtered_directories:
            self.assertIn("dir1", str(directory).lower())
    
    def test_navigation_selection(self):
        """Test navigation selection functionality"""
        test_path = self.create_test_directory_structure()
        
        # Show dialog and wait for scanning to complete
        self.jump_dialog.show(test_path)
        
        # Wait for scanning to complete
        max_wait = 5.0
        start_time = time.time()
        
        while self.jump_dialog.searching and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Test navigation input
        import curses
        
        # Test Enter key - should return navigation result
        result = self.jump_dialog.handle_input(curses.KEY_ENTER)
        self.assertIsInstance(result, tuple)
        action, data = result
        self.assertEqual(action, 'navigate')
        self.assertIsInstance(data, Path)
        
        # Test ESC key - should exit
        self.jump_dialog.show(test_path)  # Show again
        result = self.jump_dialog.handle_input(27)  # ESC
        self.assertTrue(result)
        self.assertFalse(self.jump_dialog.mode)
    
    def test_thread_safety(self):
        """Test thread safety of jump dialog operations"""
        test_path = self.create_test_directory_structure()
        
        # Show dialog
        self.jump_dialog.show(test_path)
        
        # Perform concurrent operations
        def concurrent_filter():
            for i in range(10):
                self.jump_dialog.search_editor.text = f"test{i}"
                self.jump_dialog._filter_directories()
                time.sleep(0.01)
        
        def concurrent_navigation():
            import curses
            for i in range(10):
                self.jump_dialog.handle_input(curses.KEY_DOWN)
                time.sleep(0.01)
        
        # Start concurrent threads
        filter_thread = threading.Thread(target=concurrent_filter)
        nav_thread = threading.Thread(target=concurrent_navigation)
        
        filter_thread.start()
        nav_thread.start()
        
        # Wait for threads to complete
        filter_thread.join(timeout=2.0)
        nav_thread.join(timeout=2.0)
        
        # Dialog should still be functional
        self.assertTrue(self.jump_dialog.mode)
    
    def test_jump_dialog_helpers(self):
        """Test JumpDialogHelpers functionality"""
        test_path = self.create_test_directory_structure()
        mock_pane_manager = MockPaneManager()
        
        messages = []
        def mock_print(msg):
            messages.append(msg)
        
        # Test navigation to valid directory
        JumpDialogHelpers.navigate_to_directory(test_path, mock_pane_manager, mock_print)
        
        # Check that pane was updated
        current_pane = mock_pane_manager.get_current_pane()
        self.assertEqual(current_pane['path'], test_path)
        self.assertEqual(current_pane['selected_index'], 0)
        self.assertEqual(current_pane['scroll_offset'], 0)
        self.assertEqual(len(current_pane['selected_files']), 0)
        
        # Check that message was printed
        self.assertEqual(len(messages), 1)
        self.assertIn("Jumped to directory", messages[0])
        
        # Test navigation to invalid directory
        messages.clear()
        invalid_path = Path("/nonexistent/directory")
        JumpDialogHelpers.navigate_to_directory(invalid_path, mock_pane_manager, mock_print)
        
        # Check that error message was printed
        self.assertEqual(len(messages), 1)
        self.assertIn("Error", messages[0])
    
    def test_scan_cancellation(self):
        """Test scan cancellation functionality"""
        test_path = self.create_test_directory_structure()
        
        # Show dialog to start scanning
        self.jump_dialog.show(test_path)
        self.assertTrue(self.jump_dialog.searching)
        
        # Cancel scan immediately
        self.jump_dialog._cancel_current_scan()
        
        # Wait a moment for cancellation to take effect
        time.sleep(0.1)
        
        self.assertFalse(self.jump_dialog.searching)
    
    def test_maximum_directories_limit(self):
        """Test maximum directories limit"""
        # Set a low limit for testing
        original_limit = self.jump_dialog.max_directories
        self.jump_dialog.max_directories = 3
        
        try:
            test_path = self.create_test_directory_structure()
            
            # Show dialog and wait for scanning to complete
            self.jump_dialog.show(test_path)
            
            # Wait for scanning to complete
            max_wait = 5.0
            start_time = time.time()
            
            while self.jump_dialog.searching and (time.time() - start_time) < max_wait:
                time.sleep(0.1)
            
            with self.jump_dialog.scan_lock:
                directories = self.jump_dialog.directories.copy()
            
            # Should not exceed the limit
            self.assertLessEqual(len(directories), 3)
            
        finally:
            # Restore original limit
            self.jump_dialog.max_directories = original_limit


def run_jump_dialog_tests():
    """Run all jump dialog tests"""
    print("Running Jump Dialog Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJumpDialog)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} jump dialog tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests")
        
        for test, traceback in result.failures:
            print(f"\nFAILURE: {test}")
            print(traceback)
            
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(traceback)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_jump_dialog_tests()