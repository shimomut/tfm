#!/usr/bin/env python3
"""
Test JumpDialog hidden files behavior
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_jump_dialog import JumpDialog
from tfm_file_operations import FileOperations


class TestJumpDialogHiddenFiles(unittest.TestCase):
    """Test JumpDialog respects show_hidden setting"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock config
        self.config = Mock()
        self.config.MAX_JUMP_DIRECTORIES = 1000
        
        # Create temporary directory structure with hidden directories
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create regular directories
        (self.temp_dir / "visible_dir1").mkdir()
        (self.temp_dir / "visible_dir2").mkdir()
        (self.temp_dir / "visible_dir1" / "subdir").mkdir()
        
        # Create hidden directories
        (self.temp_dir / ".hidden_dir1").mkdir()
        (self.temp_dir / ".hidden_dir2").mkdir()
        (self.temp_dir / "visible_dir1" / ".hidden_subdir").mkdir()
        (self.temp_dir / ".hidden_dir1" / "nested_visible").mkdir()
        
        # Create jump dialog
        self.jump_dialog = JumpDialog(self.config)
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_show_hidden_false_filters_hidden_directories(self):
        """Test that hidden directories are filtered when show_hidden is False"""
        # Create file operations with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        
        # Show dialog with file_operations reference
        self.jump_dialog.show(self.temp_dir, file_ops)
        
        # Wait for scanning to complete
        import time
        timeout = 5.0
        start_time = time.time()
        while self.jump_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Check that hidden directories are not included
        found_dirs = [str(d) for d in self.jump_dialog.directories]
        
        # Should include visible directories
        self.assertTrue(any("visible_dir1" in d for d in found_dirs))
        self.assertTrue(any("visible_dir2" in d for d in found_dirs))
        self.assertTrue(any("subdir" in d for d in found_dirs))
        
        # Should NOT include hidden directories
        self.assertFalse(any(".hidden_dir1" in d for d in found_dirs))
        self.assertFalse(any(".hidden_dir2" in d for d in found_dirs))
        self.assertFalse(any(".hidden_subdir" in d for d in found_dirs))
        self.assertFalse(any("nested_visible" in d for d in found_dirs))  # Parent is hidden
    
    def test_show_hidden_true_includes_hidden_directories(self):
        """Test that hidden directories are included when show_hidden is True"""
        # Create file operations with show_hidden = True
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = True
        
        # Show dialog with file_operations reference
        self.jump_dialog.show(self.temp_dir, file_ops)
        
        # Wait for scanning to complete
        import time
        timeout = 5.0
        start_time = time.time()
        while self.jump_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Check that hidden directories are included
        found_dirs = [str(d) for d in self.jump_dialog.directories]
        
        # Should include visible directories
        self.assertTrue(any("visible_dir1" in d for d in found_dirs))
        self.assertTrue(any("visible_dir2" in d for d in found_dirs))
        self.assertTrue(any("subdir" in d for d in found_dirs))
        
        # Should ALSO include hidden directories
        self.assertTrue(any(".hidden_dir1" in d for d in found_dirs))
        self.assertTrue(any(".hidden_dir2" in d for d in found_dirs))
        self.assertTrue(any(".hidden_subdir" in d for d in found_dirs))
        self.assertTrue(any("nested_visible" in d for d in found_dirs))
    
    def test_no_file_operations_reference_includes_all(self):
        """Test fallback behavior when no file_operations reference is provided"""
        # Show dialog without file_operations reference (old behavior)
        self.jump_dialog.show(self.temp_dir)
        
        # Wait for scanning to complete
        import time
        timeout = 5.0
        start_time = time.time()
        while self.jump_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Should include all directories (fallback behavior)
        found_dirs = [str(d) for d in self.jump_dialog.directories]
        
        # Should include both visible and hidden directories
        self.assertTrue(any("visible_dir1" in d for d in found_dirs))
        self.assertTrue(any(".hidden_dir1" in d for d in found_dirs))
    
    def test_should_include_directory_method(self):
        """Test the _should_include_directory helper method directly"""
        # Test with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        self.jump_dialog.file_operations = file_ops
        self.jump_dialog.root_directory = self.temp_dir
        
        # Visible directory should be included
        visible_dir = self.temp_dir / "visible_dir1"
        self.assertTrue(self.jump_dialog._should_include_directory(visible_dir, self.temp_dir, self.temp_dir))
        
        # Hidden directory should not be included when parent is not hidden
        hidden_dir = self.temp_dir / ".hidden_dir1"
        self.assertFalse(self.jump_dialog._should_include_directory(hidden_dir, self.temp_dir, self.temp_dir))
        
        # Test with show_hidden = True
        file_ops.show_hidden = True
        
        # All directories should be included
        self.assertTrue(self.jump_dialog._should_include_directory(visible_dir, self.temp_dir, self.temp_dir))
        self.assertTrue(self.jump_dialog._should_include_directory(hidden_dir, self.temp_dir, self.temp_dir))
    
    def test_hidden_context_behavior(self):
        """Test that directories within hidden context are included even when show_hidden=False"""
        # Test with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        self.jump_dialog.file_operations = file_ops
        
        # Test when root directory is hidden - should allow hidden subdirectories
        hidden_root = self.temp_dir / ".hidden_dir1"
        nested_visible = hidden_root / "nested_visible"
        nested_hidden = hidden_root / ".nested_hidden"
        
        # Create the nested hidden directory for testing
        nested_hidden.mkdir(exist_ok=True)
        
        self.jump_dialog.root_directory = hidden_root
        
        # When scanning from within a hidden directory, should include subdirectories
        self.assertTrue(self.jump_dialog._should_include_directory(nested_visible, hidden_root, hidden_root))
        self.assertTrue(self.jump_dialog._should_include_directory(nested_hidden, hidden_root, hidden_root))
        
        # Test when parent directory is hidden relative to non-hidden root
        self.jump_dialog.root_directory = self.temp_dir
        
        # Nested visible under hidden parent should be included when parent is already hidden
        self.assertTrue(self.jump_dialog._should_include_directory(nested_visible, hidden_root, self.temp_dir))


if __name__ == '__main__':
    unittest.main()