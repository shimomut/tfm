#!/usr/bin/env python3
"""
Test that hidden files configuration is properly propagated to SearchDialog and DirectoryDiffViewer
"""

import unittest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock

from tfm_config import get_config
from tfm_search_dialog import SearchDialog
from tfm_directory_diff_viewer import DirectoryDiffViewer
from tfm_file_list_manager import FileListManager


class TestHiddenFilesPropagation(unittest.TestCase):
    """Test hidden files configuration propagation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = get_config()
        # Use tfm_path.Path instead of pathlib.Path
        from tfm_path import Path as TfmPath
        self.test_dir = TfmPath(tempfile.mkdtemp())
        
        # Create test structure with hidden files
        (self.test_dir / 'visible_file.txt').write_text('visible')
        (self.test_dir / '.hidden_file.txt').write_text('hidden')
        (self.test_dir / 'visible_dir').mkdir()
        (self.test_dir / '.hidden_dir').mkdir()
        (self.test_dir / 'visible_dir' / 'file.txt').write_text('content')
        (self.test_dir / '.hidden_dir' / 'file.txt').write_text('content')
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_search_dialog_respects_show_hidden_false(self):
        """Test SearchDialog filters hidden files when show_hidden is False"""
        file_list_manager = FileListManager(self.config)
        file_list_manager.show_hidden = False
        
        search_dialog = SearchDialog(self.config, None, file_list_manager)
        search_dialog.show('filename', self.test_dir)
        
        # Perform search for all files
        search_dialog.text_editor.text = '*'
        search_dialog.perform_search(self.test_dir)
        
        # Wait for search to complete
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        # Check results - should not include hidden files
        result_names = [r['path'].name for r in search_dialog.results]
        
        self.assertIn('visible_file.txt', result_names)
        self.assertIn('visible_dir', result_names)
        self.assertNotIn('.hidden_file.txt', result_names)
        self.assertNotIn('.hidden_dir', result_names)
        # Files in hidden directories should also be excluded
        self.assertNotIn('file.txt', [r['relative_path'] for r in search_dialog.results if '.hidden_dir' in r['relative_path']])
    
    def test_search_dialog_respects_show_hidden_true(self):
        """Test SearchDialog includes hidden files when show_hidden is True"""
        file_list_manager = FileListManager(self.config)
        file_list_manager.show_hidden = True
        
        search_dialog = SearchDialog(self.config, None, file_list_manager)
        search_dialog.show('filename', self.test_dir)
        
        # Perform search for all files
        search_dialog.text_editor.text = '*'
        search_dialog.perform_search(self.test_dir)
        
        # Wait for search to complete
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        # Check results - should include hidden files
        result_names = [r['path'].name for r in search_dialog.results]
        
        self.assertIn('visible_file.txt', result_names)
        self.assertIn('.hidden_file.txt', result_names)
        self.assertIn('visible_dir', result_names)
        self.assertIn('.hidden_dir', result_names)
    
    def test_search_dialog_content_search_respects_show_hidden(self):
        """Test SearchDialog content search filters hidden files"""
        file_list_manager = FileListManager(self.config)
        file_list_manager.show_hidden = False
        
        search_dialog = SearchDialog(self.config, None, file_list_manager)
        search_dialog.show('content', self.test_dir)
        
        # Perform content search
        search_dialog.text_editor.text = 'content'
        search_dialog.perform_search(self.test_dir)
        
        # Wait for search to complete
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        # Check results - should not include files in hidden directories
        result_paths = [r['relative_path'] for r in search_dialog.results]
        
        # Should find file in visible_dir
        self.assertTrue(any('visible_dir' in p for p in result_paths))
        # Should not find file in .hidden_dir
        self.assertFalse(any('.hidden_dir' in p for p in result_paths))
    
    def test_directory_diff_viewer_respects_show_hidden(self):
        """Test DirectoryDiffViewer filters hidden files when show_hidden is False"""
        # Create second directory for comparison
        from tfm_path import Path as TfmPath
        test_dir2 = TfmPath(tempfile.mkdtemp())
        try:
            (test_dir2 / 'visible_file.txt').write_text('visible')
            (test_dir2 / '.hidden_file.txt').write_text('hidden')
            
            file_list_manager = FileListManager(self.config)
            file_list_manager.show_hidden = False
            
            renderer = Mock()
            renderer.get_dimensions = Mock(return_value=(24, 80))
            
            diff_viewer = DirectoryDiffViewer(
                renderer, 
                self.test_dir, 
                test_dir2,
                file_list_manager=file_list_manager
            )
            
            # Wait for initial scan to complete
            if diff_viewer.scanner_thread:
                diff_viewer.scanner_thread.join(timeout=2.0)
            
            # Check that hidden files are not in the scan results
            # The scan should have filtered them out
            self.assertNotIn('.hidden_file.txt', diff_viewer.left_files)
            self.assertNotIn('.hidden_file.txt', diff_viewer.right_files)
            self.assertNotIn('.hidden_dir', diff_viewer.left_files)
            
        finally:
            shutil.rmtree(test_dir2)
    
    def test_search_dialog_without_file_list_manager(self):
        """Test SearchDialog works without file_list_manager (shows all files)"""
        search_dialog = SearchDialog(self.config, None, None)
        search_dialog.show('filename', self.test_dir)
        
        # Perform search for all files
        search_dialog.text_editor.text = '*'
        search_dialog.perform_search(self.test_dir)
        
        # Wait for search to complete
        if search_dialog.search_thread:
            search_dialog.search_thread.join(timeout=2.0)
        
        # Check results - should include all files (no filtering)
        result_names = [r['path'].name for r in search_dialog.results]
        
        self.assertIn('visible_file.txt', result_names)
        self.assertIn('.hidden_file.txt', result_names)


if __name__ == '__main__':
    unittest.main()
