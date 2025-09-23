#!/usr/bin/env python3
"""
End-to-End Test for Jump Dialog Feature
Tests the complete jump dialog functionality in the main TFM application
"""

import unittest
import tempfile
import time
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_config import get_config
from tfm_main import FileManager
from tfm_jump_dialog import JumpDialog


class MockStdscr:
    """Mock curses screen for testing"""
    
    def __init__(self):
        self.height = 24
        self.width = 80
        self.keys = []
        self.key_index = 0
        
    def getmaxyx(self):
        return self.height, self.width
    
    def getch(self):
        if self.key_index < len(self.keys):
            key = self.keys[self.key_index]
            self.key_index += 1
            return key
        return 27  # ESC by default
    
    def addstr(self, y, x, text, attr=0):
        pass
    
    def clear(self):
        pass
    
    def refresh(self):
        pass
    
    def set_keys(self, keys):
        self.keys = keys
        self.key_index = 0


class TestJumpDialogEndToEnd(unittest.TestCase):
    """End-to-end test cases for jump dialog feature"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_stdscr = MockStdscr()
        self.temp_dir = None
        
    def tearDown(self):
        """Clean up test environment"""
        # Clean up temp directory
        if self.temp_dir:
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def create_test_directory_structure(self):
        """Create a temporary directory structure for testing"""
        self.temp_dir = tempfile.mkdtemp(prefix="tfm_e2e_test_")
        temp_path = Path(self.temp_dir)
        
        # Create test directory structure
        directories = [
            "project1/src",
            "project1/docs", 
            "project2/src",
            "project2/tests",
            "shared/utils",
            "shared/config"
        ]
        
        for dir_path in directories:
            (temp_path / dir_path).mkdir(parents=True, exist_ok=True)
        
        return temp_path
    
    def test_jump_dialog_key_binding_recognition(self):
        """Test that the jump dialog key binding is recognized by the config system"""
        # Test with default config (which should have jump_dialog)
        from tfm_config import DefaultConfig
        default_config = DefaultConfig()
        
        # Test that jump_dialog action exists in default config
        self.assertIn('jump_dialog', default_config.KEY_BINDINGS)
        
        # Test that 'J' key is bound to jump_dialog in default config
        jump_keys = default_config.KEY_BINDINGS['jump_dialog']
        self.assertIn('J', jump_keys)
        
        # Test that favorites only uses 'j' (lowercase) now
        favorites_keys = default_config.KEY_BINDINGS['favorites']
        self.assertIn('j', favorites_keys)
        self.assertNotIn('J', favorites_keys)  # 'J' should be moved to jump_dialog
    
    def test_jump_dialog_integration_with_file_manager(self):
        """Test jump dialog integration with FileManager"""
        test_path = self.create_test_directory_structure()
        
        # Create a minimal FileManager instance for testing
        # Note: We can't fully initialize FileManager without a real curses environment
        # So we'll test the components that can be tested
        
        config = get_config()
        jump_dialog = JumpDialog(config)
        
        # Test that jump dialog can be shown with a directory
        jump_dialog.show(test_path)
        self.assertTrue(jump_dialog.mode)
        self.assertTrue(jump_dialog.searching)
        
        # Wait for scanning to start
        time.sleep(0.1)
        
        # Test that dialog can be exited
        jump_dialog.exit()
        self.assertFalse(jump_dialog.mode)
        self.assertFalse(jump_dialog.searching)
    
    def test_jump_dialog_directory_scanning_accuracy(self):
        """Test that jump dialog accurately scans directory structure"""
        test_path = self.create_test_directory_structure()
        
        config = get_config()
        jump_dialog = JumpDialog(config)
        
        # Show dialog and wait for scanning to complete
        jump_dialog.show(test_path)
        
        # Wait for scanning to complete
        max_wait = 5.0
        start_time = time.time()
        
        while jump_dialog.searching and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Get scanned directories
        with jump_dialog.scan_lock:
            directories = jump_dialog.directories.copy()
        
        # Convert to relative paths for easier testing
        relative_dirs = [str(d.relative_to(test_path)) for d in directories if d != test_path]
        relative_dirs.sort()
        
        # Expected directories (excluding root)
        expected_dirs = [
            "project1",
            "project1/docs", 
            "project1/src",
            "project2",
            "project2/src",
            "project2/tests",
            "shared",
            "shared/config",
            "shared/utils"
        ]
        expected_dirs.sort()
        
        # Check that all expected directories were found
        for expected_dir in expected_dirs:
            self.assertIn(expected_dir, relative_dirs, 
                         f"Expected directory '{expected_dir}' not found in scanned directories")
        
        # Check that root directory is included
        self.assertIn(test_path, directories)
        
        jump_dialog.exit()
    
    def test_jump_dialog_filtering_functionality(self):
        """Test jump dialog filtering functionality"""
        test_path = self.create_test_directory_structure()
        
        config = get_config()
        jump_dialog = JumpDialog(config)
        
        # Show dialog and wait for scanning to complete
        jump_dialog.show(test_path)
        
        # Wait for scanning to complete
        max_wait = 5.0
        start_time = time.time()
        
        while jump_dialog.searching and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Test filtering by "project1"
        jump_dialog.text_editor.text = "project1"
        jump_dialog._filter_directories()
        
        with jump_dialog.scan_lock:
            filtered_dirs = jump_dialog.filtered_directories.copy()
        
        # All filtered directories should contain "project1"
        for directory in filtered_dirs:
            self.assertIn("project1", str(directory).lower())
        
        # Test filtering by "src"
        jump_dialog.text_editor.text = "src"
        jump_dialog._filter_directories()
        
        with jump_dialog.scan_lock:
            filtered_dirs = jump_dialog.filtered_directories.copy()
        
        # All filtered directories should contain "src"
        for directory in filtered_dirs:
            self.assertIn("src", str(directory).lower())
        
        jump_dialog.exit()
    
    def test_jump_dialog_navigation_result(self):
        """Test jump dialog navigation result handling"""
        test_path = self.create_test_directory_structure()
        
        config = get_config()
        jump_dialog = JumpDialog(config)
        
        # Show dialog and wait for scanning to complete
        jump_dialog.show(test_path)
        
        # Wait for scanning to complete
        max_wait = 5.0
        start_time = time.time()
        
        while jump_dialog.searching and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Simulate Enter key press
        import curses
        result = jump_dialog.handle_input(curses.KEY_ENTER)
        
        # Should return navigation tuple
        self.assertIsInstance(result, tuple)
        action, data = result
        self.assertEqual(action, 'navigate')
        self.assertIsInstance(data, Path)
        self.assertTrue(data.exists())
        self.assertTrue(data.is_dir())
    
    def test_jump_dialog_thread_safety_under_load(self):
        """Test jump dialog thread safety under concurrent operations"""
        test_path = self.create_test_directory_structure()
        
        config = get_config()
        jump_dialog = JumpDialog(config)
        
        # Show dialog
        jump_dialog.show(test_path)
        
        import threading
        import curses
        
        # Perform concurrent operations
        def concurrent_filtering():
            for i in range(20):
                jump_dialog.text_editor.text = f"project{i % 2 + 1}"
                jump_dialog._filter_directories()
                time.sleep(0.01)
        
        def concurrent_navigation():
            for i in range(20):
                jump_dialog.handle_input(curses.KEY_DOWN)
                jump_dialog.handle_input(curses.KEY_UP)
                time.sleep(0.01)
        
        # Start concurrent threads
        threads = []
        for _ in range(3):
            t1 = threading.Thread(target=concurrent_filtering)
            t2 = threading.Thread(target=concurrent_navigation)
            threads.extend([t1, t2])
            t1.start()
            t2.start()
        
        # Wait for threads to complete
        for thread in threads:
            thread.join(timeout=2.0)
        
        # Dialog should still be functional
        self.assertTrue(jump_dialog.mode)
        
        # Should be able to exit cleanly
        jump_dialog.exit()
        self.assertFalse(jump_dialog.mode)


def run_end_to_end_tests():
    """Run all end-to-end tests"""
    print("Running Jump Dialog End-to-End Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJumpDialogEndToEnd)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} end-to-end tests passed!")
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
    run_end_to_end_tests()