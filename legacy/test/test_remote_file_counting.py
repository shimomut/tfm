#!/usr/bin/env python3
"""
Test for remote file counting fix - ensures S3/SSH directories are counted correctly
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from tfm_path import Path
from tfm_file_operation_executor import FileOperationExecutor


class TestRemoteFileCounting(unittest.TestCase):
    """Test that file counting works correctly for remote storage (S3/SSH)"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock file manager
        self.file_manager = Mock()
        self.file_manager.progress_manager = Mock()
        self.file_manager.cache_manager = Mock()
        
        # Create executor
        self.executor = FileOperationExecutor(self.file_manager)
    
    def test_count_files_with_s3_directory(self):
        """Test that S3 directories are counted correctly using rglob()"""
        # Create mock S3 paths
        mock_file1 = Mock(spec=Path)
        mock_file1.is_file.return_value = True
        mock_file1.is_symlink.return_value = False
        mock_file1.is_dir.return_value = False
        
        mock_dir = Mock(spec=Path)
        mock_dir.is_file.return_value = False
        mock_dir.is_symlink.return_value = False
        mock_dir.is_dir.return_value = True
        
        # Mock rglob to return 3 files inside the directory
        mock_file_in_dir1 = Mock(spec=Path)
        mock_file_in_dir1.is_file.return_value = True
        mock_file_in_dir1.is_symlink.return_value = False
        
        mock_file_in_dir2 = Mock(spec=Path)
        mock_file_in_dir2.is_file.return_value = True
        mock_file_in_dir2.is_symlink.return_value = False
        
        mock_file_in_dir3 = Mock(spec=Path)
        mock_file_in_dir3.is_file.return_value = True
        mock_file_in_dir3.is_symlink.return_value = False
        
        mock_dir.rglob.return_value = [mock_file_in_dir1, mock_file_in_dir2, mock_file_in_dir3]
        
        # Count files: 1 file + 1 directory with 3 files = 4 total
        paths = [mock_file1, mock_dir]
        count = self.executor._count_files_recursively(paths)
        
        # Verify rglob was called (polymorphic traversal)
        mock_dir.rglob.assert_called_once_with('*')
        
        # Verify count is correct
        self.assertEqual(count, 4, "Should count 1 file + 3 files in directory = 4 total")
    
    def test_count_files_with_ssh_directory(self):
        """Test that SSH directories are counted correctly using rglob()"""
        # Create mock SSH paths
        mock_file1 = Mock(spec=Path)
        mock_file1.is_file.return_value = True
        mock_file1.is_symlink.return_value = False
        mock_file1.is_dir.return_value = False
        
        mock_file2 = Mock(spec=Path)
        mock_file2.is_file.return_value = True
        mock_file2.is_symlink.return_value = False
        mock_file2.is_dir.return_value = False
        
        mock_dir1 = Mock(spec=Path)
        mock_dir1.is_file.return_value = False
        mock_dir1.is_symlink.return_value = False
        mock_dir1.is_dir.return_value = True
        
        mock_dir2 = Mock(spec=Path)
        mock_dir2.is_file.return_value = False
        mock_dir2.is_symlink.return_value = False
        mock_dir2.is_dir.return_value = True
        
        # Mock rglob to return files inside directories
        # dir1 has 2 files
        mock_file_in_dir1_1 = Mock(spec=Path)
        mock_file_in_dir1_1.is_file.return_value = True
        mock_file_in_dir1_1.is_symlink.return_value = False
        
        mock_file_in_dir1_2 = Mock(spec=Path)
        mock_file_in_dir1_2.is_file.return_value = True
        mock_file_in_dir1_2.is_symlink.return_value = False
        
        mock_dir1.rglob.return_value = [mock_file_in_dir1_1, mock_file_in_dir1_2]
        
        # dir2 has 3 files
        mock_file_in_dir2_1 = Mock(spec=Path)
        mock_file_in_dir2_1.is_file.return_value = True
        mock_file_in_dir2_1.is_symlink.return_value = False
        
        mock_file_in_dir2_2 = Mock(spec=Path)
        mock_file_in_dir2_2.is_file.return_value = True
        mock_file_in_dir2_2.is_symlink.return_value = False
        
        mock_file_in_dir2_3 = Mock(spec=Path)
        mock_file_in_dir2_3.is_file.return_value = True
        mock_file_in_dir2_3.is_symlink.return_value = False
        
        mock_dir2.rglob.return_value = [mock_file_in_dir2_1, mock_file_in_dir2_2, mock_file_in_dir2_3]
        
        # Count files: 2 files + dir1(2 files) + dir2(3 files) = 7 total
        paths = [mock_file1, mock_file2, mock_dir1, mock_dir2]
        count = self.executor._count_files_recursively(paths)
        
        # Verify rglob was called for both directories
        mock_dir1.rglob.assert_called_once_with('*')
        mock_dir2.rglob.assert_called_once_with('*')
        
        # Verify count is correct
        self.assertEqual(count, 7, "Should count 2 files + 2 files in dir1 + 3 files in dir2 = 7 total")
    
    def test_count_files_with_symlinks(self):
        """Test that symlinks are counted correctly"""
        # Create mock paths with symlinks
        mock_file = Mock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.is_symlink.return_value = False
        mock_file.is_dir.return_value = False
        
        mock_symlink = Mock(spec=Path)
        mock_symlink.is_file.return_value = False
        mock_symlink.is_symlink.return_value = True
        mock_symlink.is_dir.return_value = False
        
        mock_dir = Mock(spec=Path)
        mock_dir.is_file.return_value = False
        mock_dir.is_symlink.return_value = False
        mock_dir.is_dir.return_value = True
        
        # Directory contains 1 file and 1 symlink
        mock_file_in_dir = Mock(spec=Path)
        mock_file_in_dir.is_file.return_value = True
        mock_file_in_dir.is_symlink.return_value = False
        
        mock_symlink_in_dir = Mock(spec=Path)
        mock_symlink_in_dir.is_file.return_value = False
        mock_symlink_in_dir.is_symlink.return_value = True
        
        mock_dir.rglob.return_value = [mock_file_in_dir, mock_symlink_in_dir]
        
        # Count: 1 file + 1 symlink + dir(1 file + 1 symlink) = 4 total
        paths = [mock_file, mock_symlink, mock_dir]
        count = self.executor._count_files_recursively(paths)
        
        self.assertEqual(count, 4, "Should count files and symlinks correctly")
    
    def test_count_files_with_permission_error(self):
        """Test that permission errors are handled gracefully"""
        # Create mock directory that raises PermissionError on rglob
        mock_dir = Mock(spec=Path)
        mock_dir.is_file.return_value = False
        mock_dir.is_symlink.return_value = False
        mock_dir.is_dir.return_value = True
        mock_dir.rglob.side_effect = PermissionError("Access denied")
        
        # Should count as 1 item when we can't traverse
        paths = [mock_dir]
        count = self.executor._count_files_recursively(paths)
        
        self.assertEqual(count, 1, "Should count inaccessible directory as 1 item")


if __name__ == '__main__':
    unittest.main()
