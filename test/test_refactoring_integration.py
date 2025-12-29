"""
Test that the BaseListDialog refactoring doesn't break TFM integration

Run with: PYTHONPATH=.:src:ttk pytest test/test_refactoring_integration.py -v
"""

import unittest
from unittest.mock import Mock
import tempfile
import shutil

from tfm_search_dialog import SearchDialog
from tfm_list_dialog import ListDialog

from _config import Config

class TestRefactoringIntegration(unittest.TestCase):
    """Test that refactoring doesn't break integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create some test files
        (self.temp_dir / "test1.txt").write_text("test content 1")
        (self.temp_dir / "test2.py").write_text("print('hello')")
        (self.temp_dir / "subdir").mkdir()
        (self.temp_dir / "subdir" / "test3.txt").write_text("test content 3")
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
        
    def test_search_dialog_integration(self):
        """Test SearchDialog integration after refactoring"""
        search_dialog = SearchDialog(self.config)
        
        # Test that it can be shown
        search_dialog.show('filename')
        self.assertTrue(search_dialog.mode)
        self.assertEqual(search_dialog.search_type, 'filename')
        
        # Test that text_editor works
        search_dialog.text_editor.text = "*.txt"
        self.assertEqual(search_dialog.text_editor.text, "*.txt")
        
        # Test search functionality
        search_dialog.perform_search(self.temp_dir)
        
        # Wait a moment for search to start
        import time
        time.sleep(0.1)
        
        # Should have started searching
        self.assertTrue(search_dialog.searching or len(search_dialog.results) > 0)
        
        search_dialog.exit()
        self.assertFalse(search_dialog.mode)
        
    def test_list_dialog_integration(self):
        """Test ListDialog integration after refactoring"""
        list_dialog = ListDialog(self.config)
        
        items = ["apple", "banana", "cherry"]
        callback_result = None
        
        def test_callback(item):
            nonlocal callback_result
            callback_result = item
            
        # Test show functionality
        list_dialog.show("Test Items", items, test_callback)
        self.assertTrue(list_dialog.mode)
        self.assertEqual(list_dialog.items, items)
        self.assertEqual(list_dialog.filtered_items, items)
        
        # Test filtering
        list_dialog.text_editor.text = "ap"
        list_dialog._filter_items()
        self.assertEqual(list_dialog.filtered_items, ["apple"])
        
        # Test selection
        list_dialog.selected = 0
        result = list_dialog.handle_input(10)  # ENTER key
        self.assertTrue(result)
        self.assertFalse(list_dialog.mode)  # Should exit
        self.assertEqual(callback_result, "apple")
        
    def test_jump_dialog_integration(self):
        """Test JumpDialog integration after refactoring"""
        jump_dialog = JumpDialog(self.config)
        
        # Test show functionality
        jump_dialog.show(self.temp_dir)
        self.assertTrue(jump_dialog.mode)
        
        # Wait for scanning to complete
        import time
        max_wait = 2.0
        start_time = time.time()
        
        while jump_dialog.searching and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
            
        # Should have found directories
        with jump_dialog.scan_lock:
            self.assertGreater(len(jump_dialog.directories), 0)
            self.assertGreater(len(jump_dialog.filtered_directories), 0)
            
        # Test filtering
        jump_dialog.text_editor.text = "subdir"
        jump_dialog._filter_directories()
        
        with jump_dialog.scan_lock:
            filtered_names = [str(d.name) for d in jump_dialog.filtered_directories]
            self.assertIn("subdir", filtered_names)
            
        jump_dialog.exit()
        self.assertFalse(jump_dialog.mode)
        
    def test_common_navigation_works(self):
        """Test that common navigation works across all dialogs"""
        dialogs = [
            ListDialog(self.config),
            SearchDialog(self.config)(self.config)
        ]
        
        for dialog in dialogs:
            # Test UP/DOWN navigation
            items = ["item1", "item2", "item3"]
            
            # Test DOWN key
            dialog.selected = 0
            result = dialog.handle_common_navigation(258, items)  # KEY_DOWN
            self.assertTrue(result)
            self.assertEqual(dialog.selected, 1)
            
            # Test UP key
            result = dialog.handle_common_navigation(259, items)  # KEY_UP
            self.assertTrue(result)
            self.assertEqual(dialog.selected, 0)
            
            # Test ESC key
            result = dialog.handle_common_navigation(27, items)  # ESC
            self.assertEqual(result, 'cancel')
            
            # Test ENTER key
            result = dialog.handle_common_navigation(10, items)  # ENTER
            self.assertEqual(result, 'select')
